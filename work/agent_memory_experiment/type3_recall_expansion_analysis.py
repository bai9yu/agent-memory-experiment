#!/usr/bin/env python3
"""Analyze Type-3 candidate recall expansion with offline retrievers."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from memory_eval import (
    Memory,
    Query,
    bm25_score,
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    cosine,
    entity_overlap,
    hashed_vector,
    load_memories,
    load_queries,
    memory_type_score,
    normalize,
    persona_score,
    query_intent_type_weights,
    query_personas,
    recency_gate,
    time_decay,
    tokenize,
)
from query_type_router_experiment import metric, write_csv


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "did", "do", "does",
    "for", "from", "had", "has", "have", "he", "her", "his", "how", "if", "in",
    "is", "it", "likely", "might", "of", "on", "or", "she", "that", "the",
    "their", "to", "was", "were", "what", "when", "where", "which", "who", "why",
    "with", "would",
}
INTENT_PATTERNS = (
    (re.compile(r"\bwhy|because|reason|decide|decided|cause\b", re.IGNORECASE), "reason motive cause decision"),
    (re.compile(r"\bwhen|date|time|recent|recently|last\b", re.IGNORECASE), "time date event recent"),
    (re.compile(r"\bwhere|country|state|city|place|location|live|moved?\b", re.IGNORECASE), "place location live move"),
    (re.compile(r"\bwho|friend|mother|father|partner|husband|wife|family\b", re.IGNORECASE), "person relationship family identity"),
    (re.compile(r"\bcareer|field|education|school|study|job|work|pursue\b", re.IGNORECASE), "career education work goal plan"),
    (re.compile(r"\blike|enjoy|favorite|prefer|love|hobby|activity\b", re.IGNORECASE), "preference hobby enjoy"),
    (re.compile(r"\bfeel|support|realize|learned|experience|worry|happy|sad\b", re.IGNORECASE), "emotion support experience"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def known_personas(memories: list[Memory]) -> set[str]:
    return {memory.agent_id.lower() for memory in memories if memory.agent_id}


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]


def dedupe(values: list[str]) -> list[str]:
    seen = set()
    out = []
    for value in values:
        key = " ".join(tokenize(value))
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def query_facets(query: Query, personas: set[str], max_facets: int) -> list[str]:
    persona_names = sorted(query_personas(query, personas))
    prefix = " ".join(persona_names)
    tokens = content_tokens(query.query)
    facets = [query.query]
    compact = " ".join(tokens)
    if compact:
        facets.append(f"{prefix} {compact}".strip())
    for pattern, text in INTENT_PATTERNS:
        if pattern.search(query.query):
            facets.append(f"{prefix} {text}".strip())
            if compact:
                facets.append(f"{prefix} {text} {compact}".strip())
    return dedupe(facets)[:max_facets]


def build_offline_ranking(
    query: Query,
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    half_life_days: float,
) -> list[str]:
    query_tokens = tokenize(query.query)
    query_set = set(query_tokens)
    query_vector = hashed_vector(query_tokens)
    query_persona_names = query_personas(query, personas)
    query_type_weights = query_intent_type_weights(query)
    query_recency_gate = recency_gate(query)
    bm25_raw = {
        memory.id: bm25_score(query_tokens, memory_tokens[memory.id], idf, avg_len)
        for memory in memories
    }
    semantic_raw = {
        memory.id: cosine(query_vector, memory_vectors[memory.id])
        for memory in memories
    }
    bm25_norm = normalize(bm25_raw)
    semantic_norm = normalize(semantic_raw)
    scores = {}
    for memory in memories:
        scores[memory.id] = (
            0.46 * bm25_norm[memory.id]
            + 0.25 * semantic_norm[memory.id]
            + 0.08 * entity_overlap(query_set, memory.entities)
            + 0.07 * memory_type_score(memory, query_type_weights)
            + 0.05 * max(persona_score(memory, query_persona_names), 0.0)
            + 0.05 * importance_scores[memory.id]
            + 0.04 * query_recency_gate * time_decay(memory.date, query.query_date, half_life_days)
        )
    return sorted(scores, key=scores.get, reverse=True)


def build_facet_pool(
    query: Query,
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    facet_top_k: int,
    max_facets: int,
) -> list[str]:
    scores: dict[str, float] = defaultdict(float)
    facets = query_facets(query, personas, max_facets)
    for facet in facets:
        facet_tokens = tokenize(facet)
        facet_vector = hashed_vector(facet_tokens)
        bm25_raw = {
            memory.id: bm25_score(facet_tokens, memory_tokens[memory.id], idf, avg_len)
            for memory in memories
        }
        semantic_raw = {
            memory.id: cosine(facet_vector, memory_vectors[memory.id])
            for memory in memories
        }
        bm25_norm = normalize(bm25_raw)
        semantic_norm = normalize(semantic_raw)
        combined = {
            memory.id: 0.68 * bm25_norm[memory.id] + 0.32 * semantic_norm[memory.id]
            for memory in memories
        }
        for rank, memory_id in enumerate(sorted(combined, key=combined.get, reverse=True)[:facet_top_k], start=1):
            scores[memory_id] += 1.0 / (60.0 + rank)
    return sorted(scores, key=scores.get, reverse=True)


def load_candidate_ranked(path: Path) -> dict[tuple[str, str], list[str]]:
    groups: dict[tuple[str, str], list[tuple[int, str]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append((int(row["rank"]), row["memory_id"]))
    return {
        key: [memory_id for _rank, memory_id in sorted(rows)]
        for key, rows in groups.items()
    }


def merge_unique(*rankings: list[str]) -> list[str]:
    seen = set()
    out = []
    for ranking in rankings:
        for memory_id in ranking:
            if memory_id not in seen:
                seen.add(memory_id)
                out.append(memory_id)
    return out


def coverage(ids: list[str], gold_ids: set[str], k: int) -> float:
    return len(set(ids[:k]) & gold_ids) / len(gold_ids) if gold_ids else 0.0


def full(ids: list[str], gold_ids: set[str], k: int) -> float:
    return 1.0 if gold_ids and gold_ids.issubset(set(ids[:k])) else 0.0


def any_hit(ids: list[str], gold_ids: set[str], k: int) -> float:
    return 1.0 if set(ids[:k]) & gold_ids else 0.0


def build_rows(
    candidate_ranked: dict[tuple[str, str], list[str]],
    queries: dict[str, Query],
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    candidate_ks: list[int],
    expansion_ks: list[int],
    facet_top_k: int,
    max_facets: int,
    half_life_days: float,
) -> list[dict[str, Any]]:
    by_query_offline: dict[str, list[str]] = {}
    by_query_facet: dict[str, list[str]] = {}
    per_query = []
    for (seed, query_id), candidate_ids in sorted(candidate_ranked.items()):
        query = queries.get(query_id)
        if not query or query.type != "3":
            continue
        gold_ids = set(query.answer_memory_ids)
        if query_id not in by_query_offline:
            by_query_offline[query_id] = build_offline_ranking(
                query,
                memories,
                memory_tokens,
                memory_vectors,
                idf,
                avg_len,
                personas,
                importance_scores,
                half_life_days,
            )
            by_query_facet[query_id] = build_facet_pool(
                query,
                memories,
                memory_tokens,
                memory_vectors,
                idf,
                avg_len,
                personas,
                facet_top_k,
                max_facets,
            )
        offline_ids = by_query_offline[query_id]
        facet_ids = by_query_facet[query_id]
        methods = {}
        for k in candidate_ks:
            methods[f"candidate_top{k}"] = candidate_ids[:k]
        for k in expansion_ks:
            methods[f"offline_top{k}"] = offline_ids[:k]
            methods[f"facet_top{k}"] = facet_ids[:k]
            methods[f"candidate20_plus_offline{k}"] = merge_unique(candidate_ids[:20], offline_ids[:k])
            methods[f"candidate20_plus_facet{k}"] = merge_unique(candidate_ids[:20], facet_ids[:k])
            methods[f"candidate20_plus_offline{k}_facet{k}"] = merge_unique(candidate_ids[:20], offline_ids[:k], facet_ids[:k])
        for method, ids in methods.items():
            row = {
                "split_seed": seed,
                "query_id": query_id,
                "query": query.query,
                "method": method,
                "pool_size": len(ids),
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            }
            for k in (5, 20, 50, 100):
                row[f"any_hit@{k}"] = any_hit(ids, gold_ids, k)
                row[f"coverage_ratio@{k}"] = coverage(ids, gold_ids, k)
                row[f"full_coverage@{k}"] = full(ids, gold_ids, k)
            row["missing_all_gold"] = 1.0 if coverage(ids, gold_ids, min(len(ids), 100)) == 0.0 else 0.0
            per_query.append(row)
    return per_query


def aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    out = []
    for method, bucket in sorted(buckets.items()):
        item = {
            "method": method,
            "rows": len(bucket),
            "mean_pool_size": statistics.mean(row["pool_size"] for row in bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
            "missing_all_gold_share": statistics.mean(row["missing_all_gold"] for row in bucket),
        }
        for k in (5, 20, 50, 100):
            item[f"any_hit@{k}"] = statistics.mean(row[f"any_hit@{k}"] for row in bucket)
            item[f"coverage_ratio@{k}"] = statistics.mean(row[f"coverage_ratio@{k}"] for row in bucket)
            item[f"full_coverage@{k}"] = statistics.mean(row[f"full_coverage@{k}"] for row in bucket)
        out.append(item)
    return out


def deltas(summary: list[dict[str, Any]], baseline_method: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method[baseline_method]
    rows = []
    for method, row in sorted(by_method.items()):
        if method == baseline_method:
            continue
        rows.append({
            "baseline": baseline_method,
            "method": method,
            "delta_missing_all_gold_share": row["missing_all_gold_share"] - base["missing_all_gold_share"],
            "delta_coverage_ratio@20": row["coverage_ratio@20"] - base["coverage_ratio@20"],
            "delta_full_coverage@20": row["full_coverage@20"] - base["full_coverage@20"],
            "delta_coverage_ratio@50": row["coverage_ratio@50"] - base["coverage_ratio@50"],
            "delta_full_coverage@50": row["full_coverage@50"] - base["full_coverage@50"],
            "delta_coverage_ratio@100": row["coverage_ratio@100"] - base["coverage_ratio@100"],
            "delta_full_coverage@100": row["full_coverage@100"] - base["full_coverage@100"],
        })
    return rows


def write_report(path: Path, summary: list[dict[str, Any]], delta_rows: list[dict[str, Any]], baseline_method: str) -> None:
    by_method = {row["method"]: row for row in summary}
    candidate20 = by_method[baseline_method]
    selected_methods = [
        baseline_method,
        "candidate_top50",
        "candidate_top100",
        "offline_top50",
        "facet_top50",
        "candidate20_plus_offline50",
        "candidate20_plus_facet50",
        "candidate20_plus_offline50_facet50",
    ]
    lines = [
        "# Type 3 召回扩展分析",
        "",
        "本实验针对 Type 3 中 Top-20 候选缺失 gold evidence 的问题，比较扩大候选池、离线多信号检索和意图 facet 检索能否提升证据召回。该实验只评估候选池覆盖，不作为最终排序方法。",
        "",
        "## 主要结果",
        "",
        "| 方法 | Pool | Missing-All | Coverage@20 | Full@20 | Coverage@50 | Full@50 | Coverage@100 | Full@100 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in selected_methods:
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['mean_pool_size']:.1f} | {metric(row['missing_all_gold_share'])} | "
                f"{metric(row['coverage_ratio@20'])} | {metric(row['full_coverage@20'])} | "
                f"{metric(row['coverage_ratio@50'])} | {metric(row['full_coverage@50'])} | "
                f"{metric(row['coverage_ratio@100'])} | {metric(row['full_coverage@100'])} |"
            )
    lines.extend([
        "",
        "## 相比 Candidate Top-20 的变化",
        "",
    ])
    for row in delta_rows:
        if row["method"] not in set(selected_methods):
            continue
        lines.append(
            f"- `{row['method']}`：Missing-All `{row['delta_missing_all_gold_share']:+.4f}`，"
            f"Coverage@50 `{row['delta_coverage_ratio@50']:+.4f}`，Full@50 `{row['delta_full_coverage@50']:+.4f}`。"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        f"- Candidate Top-20 的 Missing-All 为 `{candidate20['missing_all_gold_share']:.3f}`；该值越高，说明重排无法解决的问题越多。",
        "- 如果扩大候选池显著降低 Missing-All，下一步应把候选池扩大后接 listwise/setwise 重排。",
        "- 如果离线检索或 facet 检索优于简单扩大 candidate，则说明 query decomposition / 多路召回值得继续投入。",
        "- 如果所有离线召回仍不足，下一步应接真实 embedding 或 LLM 子问题生成。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Type3 recall expansion.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--candidate-ks", default="20,50,100")
    parser.add_argument("--expansion-ks", default="20,50,100")
    parser.add_argument("--facet-top-k", type=int, default=50)
    parser.add_argument("--max-facets", type=int, default=6)
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--baseline-method", default="candidate_top20")
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = {query.id: query for query in load_queries(args.queries)}
    memory_tokens = build_memory_tokens(memories)
    memory_vectors = {memory.id: hashed_vector(memory_tokens[memory.id]) for memory in memories}
    idf = build_idf(memories)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    personas = known_personas(memories)
    importance_scores = build_importance_scores(memories)
    candidate_ranked = load_candidate_ranked(args.candidate_ranked)
    candidate_ks = [int(item.strip()) for item in args.candidate_ks.split(",") if item.strip()]
    expansion_ks = [int(item.strip()) for item in args.expansion_ks.split(",") if item.strip()]

    rows = build_rows(
        candidate_ranked,
        queries,
        memories,
        memory_tokens,
        memory_vectors,
        idf,
        avg_len,
        personas,
        importance_scores,
        candidate_ks,
        expansion_ks,
        args.facet_top_k,
        args.max_facets,
        args.half_life_days,
    )
    summary = aggregate(rows)
    delta_rows = deltas(summary, args.baseline_method)
    write_csv(args.output_per_query, rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, delta_rows)
    write_report(args.output_report, summary, delta_rows, args.baseline_method)
    best_missing = min(summary, key=lambda row: row["missing_all_gold_share"])
    print(json.dumps({
        "rows": len(rows),
        "baseline_method": args.baseline_method,
        "best_missing_method": best_missing["method"],
        "best_missing_all_gold_share": best_missing["missing_all_gold_share"],
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
