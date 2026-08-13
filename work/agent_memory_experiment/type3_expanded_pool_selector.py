#!/usr/bin/env python3
"""Select Type-3 evidence from an expanded offline candidate pool."""

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
    compact = " ".join(tokens)
    facets = [query.query]
    if compact:
        facets.append(f"{prefix} {compact}".strip())
    for pattern, text in INTENT_PATTERNS:
        if pattern.search(query.query):
            facets.append(f"{prefix} {text}".strip())
            if compact:
                facets.append(f"{prefix} {text} {compact}".strip())
    return dedupe(facets)[:max_facets]


def load_candidate_rows(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row.get("memory_type", ""),
            "memory_text": row.get("memory_text", ""),
            "learned_score": float(row.get("learned_score", "0") or 0.0),
            "is_relevant": row.get("is_relevant") == "True",
        })
    for rows in groups.values():
        rows.sort(key=lambda row: row["rank"])
        norm = normalize({row["memory_id"]: row["learned_score"] for row in rows})
        for row in rows:
            row["candidate_rank"] = row["rank"]
            row["candidate_norm"] = norm[row["memory_id"]]
            row["candidate_rrf"] = 1.0 / (60.0 + row["rank"])
    return groups


def score_all_memories(
    query: Query,
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    half_life_days: float,
) -> dict[str, dict[str, float]]:
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
    out = {}
    for memory in memories:
        out[memory.id] = {
            "bm25_norm": bm25_norm[memory.id],
            "semantic_norm": semantic_norm[memory.id],
            "entity_overlap": entity_overlap(query_set, memory.entities),
            "memory_type_score": memory_type_score(memory, query_type_weights),
            "persona_score": max(persona_score(memory, query_persona_names), 0.0),
            "importance_score": importance_scores[memory.id],
            "recency_score": query_recency_gate * time_decay(memory.date, query.query_date, half_life_days),
        }
    return out


def facet_rankings(
    query: Query,
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    max_facets: int,
) -> dict[str, dict[str, float]]:
    scores: dict[str, dict[str, float]] = defaultdict(lambda: {"facet_rrf": 0.0, "facet_hits": 0.0})
    for facet in query_facets(query, personas, max_facets):
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
        for rank, memory_id in enumerate(sorted(combined, key=combined.get, reverse=True), start=1):
            scores[memory_id]["facet_rrf"] += 1.0 / (60.0 + rank)
            if rank <= 50:
                scores[memory_id]["facet_hits"] += 1.0
    return scores


def build_pool(
    candidate_rows: list[dict[str, Any]],
    offline_scores: dict[str, dict[str, float]],
    facet_scores: dict[str, dict[str, float]],
    memory_by_id: dict[str, Memory],
    offline_k: int,
    facet_k: int,
) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in candidate_rows[:20]:
        by_id[row["memory_id"]] = {
            **row,
            "source_candidate": 1.0,
            "source_offline": 0.0,
            "source_facet": 0.0,
        }
    offline_ranking = sorted(
        offline_scores,
        key=lambda memory_id: (
            offline_scores[memory_id]["bm25_norm"]
            + offline_scores[memory_id]["semantic_norm"]
            + offline_scores[memory_id]["entity_overlap"]
            + offline_scores[memory_id]["memory_type_score"]
        ),
        reverse=True,
    )
    facet_ranking = sorted(facet_scores, key=lambda memory_id: facet_scores[memory_id]["facet_rrf"], reverse=True)
    for source, ranking, limit in (("source_offline", offline_ranking, offline_k), ("source_facet", facet_ranking, facet_k)):
        for rank, memory_id in enumerate(ranking[:limit], start=1):
            memory = memory_by_id[memory_id]
            item = by_id.setdefault(
                memory_id,
                {
                    "memory_id": memory_id,
                    "memory_type": memory.memory_type,
                    "memory_text": memory.text,
                    "learned_score": 0.0,
                    "candidate_rank": 999,
                    "candidate_norm": 0.0,
                    "candidate_rrf": 0.0,
                    "source_candidate": 0.0,
                    "source_offline": 0.0,
                    "source_facet": 0.0,
                },
            )
            item[source] = 1.0
            item[f"{source}_rank"] = rank
    pool = []
    for memory_id, row in by_id.items():
        features = offline_scores.get(memory_id, {})
        facet = facet_scores.get(memory_id, {})
        pool.append({
            **row,
            **features,
            "facet_rrf": facet.get("facet_rrf", 0.0),
            "facet_hits": facet.get("facet_hits", 0.0),
        })
    return pool


def redundancy(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_tokens = set(tokenize(left["memory_text"]))
    right_tokens = set(tokenize(right["memory_text"]))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def base_score(row: dict[str, Any]) -> float:
    return (
        0.34 * row.get("candidate_norm", 0.0)
        + 0.24 * row.get("bm25_norm", 0.0)
        + 0.14 * row.get("semantic_norm", 0.0)
        + 0.08 * row.get("entity_overlap", 0.0)
        + 0.06 * row.get("memory_type_score", 0.0)
        + 0.04 * row.get("persona_score", 0.0)
        + 0.04 * row.get("importance_score", 0.0)
        + 0.03 * row.get("recency_score", 0.0)
        + 1.15 * row.get("facet_rrf", 0.0)
        + 0.015 * min(row.get("facet_hits", 0.0), 4.0)
        + 0.02 * row.get("source_offline", 0.0)
        + 0.02 * row.get("source_facet", 0.0)
    )


def greedy_select(pool: list[dict[str, Any]], select_k: int, keep_top1: bool, redundancy_weight: float) -> list[dict[str, Any]]:
    remaining = [dict(row, selector_base_score=base_score(row)) for row in pool]
    selected = []
    if keep_top1:
        candidate_rows = [row for row in remaining if row.get("candidate_rank") == 1]
        if candidate_rows:
            selected.append(candidate_rows[0])
            remaining = [row for row in remaining if row["memory_id"] != selected[0]["memory_id"]]
    while remaining and len(selected) < select_k:
        best = None
        best_score = float("-inf")
        for row in remaining:
            max_redundancy = max((redundancy(row, chosen) for chosen in selected), default=0.0)
            score = row["selector_base_score"] - redundancy_weight * max_redundancy
            if score > best_score:
                best = row
                best_score = score
        chosen = dict(best, selector_score=best_score)
        selected.append(chosen)
        remaining = [row for row in remaining if row["memory_id"] != chosen["memory_id"]]
    selected_ids = {row["memory_id"] for row in selected}
    tail = sorted(
        [row for row in remaining if row["memory_id"] not in selected_ids],
        key=lambda row: row["selector_base_score"],
        reverse=True,
    )
    return selected + tail


def append_expansion_after_candidate(candidate_rows: list[dict[str, Any]], pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_ids = {row["memory_id"] for row in candidate_rows[:20]}
    appended = sorted(
        [row for row in pool if row["memory_id"] not in candidate_ids],
        key=lambda row: base_score(row),
        reverse=True,
    )
    enriched_candidate = []
    by_pool_id = {row["memory_id"]: row for row in pool}
    for row in candidate_rows[:20]:
        enriched = dict(by_pool_id.get(row["memory_id"], row))
        enriched["is_relevant"] = row.get("is_relevant", False)
        enriched_candidate.append(enriched)
    return enriched_candidate + appended


def oracle_select(pool: list[dict[str, Any]], gold_ids: set[str], select_k: int) -> list[dict[str, Any]]:
    relevant = [row for row in pool if row["memory_id"] in gold_ids]
    non_relevant = [row for row in pool if row["memory_id"] not in gold_ids]
    relevant.sort(key=lambda row: base_score(row), reverse=True)
    non_relevant.sort(key=lambda row: base_score(row), reverse=True)
    return relevant[:select_k] + non_relevant


def first_rank(rows: list[dict[str, Any]]) -> int:
    for rank, row in enumerate(rows, start=1):
        if row["is_relevant"]:
            return rank
    return 0


def metrics(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    rank = first_rank(rows)
    out = {
        "mrr": 1.0 / rank if rank else 0.0,
        "recall@1": 1.0 if rank and rank <= 1 else 0.0,
        "recall@3": 1.0 if rank and rank <= 3 else 0.0,
        "recall@5": 1.0 if rank and rank <= 5 else 0.0,
        "first_rank": rank,
    }
    ranked_ids = [row["memory_id"] for row in rows]
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
    return out


def build_rows(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    queries: dict[str, Query],
    memories: list[Memory],
    memory_by_id: dict[str, Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_query = []
    ranked_rows = []
    cache: dict[str, tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]] = {}
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    for (seed, query_id), candidate_rows in sorted(groups.items()):
        query = queries.get(query_id)
        if not query or query.type != "3":
            continue
        gold_ids = set(query.answer_memory_ids)
        if query_id not in cache:
            cache[query_id] = (
                score_all_memories(
                    query,
                    memories,
                    memory_tokens,
                    memory_vectors,
                    idf,
                    avg_len,
                    personas,
                    importance_scores,
                    args.half_life_days,
                ),
                facet_rankings(
                    query,
                    memories,
                    memory_tokens,
                    memory_vectors,
                    idf,
                    avg_len,
                    personas,
                    args.max_facets,
                ),
            )
        offline_scores, facet_scores = cache[query_id]
        pool = build_pool(
            candidate_rows,
            offline_scores,
            facet_scores,
            memory_by_id,
            args.offline_k,
            args.facet_k,
        )
        original = []
        for row in candidate_rows:
            enriched = dict(row)
            enriched["is_relevant"] = row["memory_id"] in gold_ids
            original.append(enriched)
        selected = greedy_select(pool, args.select_k, args.keep_top1, args.redundancy_weight)
        for row in selected:
            row["is_relevant"] = row["memory_id"] in gold_ids
        appended = append_expansion_after_candidate(original, pool)
        for row in appended:
            row["is_relevant"] = row["memory_id"] in gold_ids
        oracle = oracle_select(pool, gold_ids, args.select_k)
        for row in oracle:
            row["is_relevant"] = row["memory_id"] in gold_ids
        methods = {
            "candidate_reranker": original,
            "candidate20_then_expansion": appended,
            "expanded_pool_selector": selected,
            "expanded_pool_oracle_top5": oracle,
        }
        for method, rows in methods.items():
            per_query.append({
                "split_seed": seed,
                "query_id": query_id,
                "query": query.query,
                "method": method,
                "pool_size": len(rows),
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                **metrics(rows, gold_ids, ks),
            })
            for rank, row in enumerate(rows[: max(ks)], start=1):
                ranked_rows.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row.get("memory_type", ""),
                    "is_relevant": row.get("is_relevant", False),
                    "selector_score": row.get("selector_score", ""),
                    "selector_base_score": row.get("selector_base_score", ""),
                    "candidate_norm": row.get("candidate_norm", ""),
                    "bm25_norm": row.get("bm25_norm", ""),
                    "semantic_norm": row.get("semantic_norm", ""),
                    "facet_rrf": row.get("facet_rrf", ""),
                    "source_candidate": row.get("source_candidate", ""),
                    "source_offline": row.get("source_offline", ""),
                    "source_facet": row.get("source_facet", ""),
                    "memory_text": row.get("memory_text", ""),
                })
    return per_query, ranked_rows


def aggregate(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
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
            "mrr": statistics.mean(row["mrr"] for row in bucket),
            "recall@1": statistics.mean(row["recall@1"] for row in bucket),
            "recall@3": statistics.mean(row["recall@3"] for row in bucket),
            "recall@5": statistics.mean(row["recall@5"] for row in bucket),
        }
        for k in ks:
            item[f"coverage_ratio@{k}"] = statistics.mean(row[f"coverage_ratio@{k}"] for row in bucket)
            item[f"full_coverage@{k}"] = statistics.mean(row[f"full_coverage@{k}"] for row in bucket)
        out.append(item)
    return out


def deltas(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method["candidate_reranker"]
    rows = []
    for method, row in by_method.items():
        if method == "candidate_reranker":
            continue
        out = {"baseline": "candidate_reranker", "method": method}
        for name in (
            "mrr",
            "recall@1",
            "recall@3",
            "recall@5",
            "coverage_ratio@5",
            "full_coverage@5",
            "coverage_ratio@20",
            "full_coverage@20",
            "coverage_ratio@50",
            "full_coverage@50",
            "coverage_ratio@100",
            "full_coverage@100",
        ):
            out[f"delta_{name}"] = row[name] - base[name]
        rows.append(out)
    return rows


def write_report(path: Path, summary: list[dict[str, Any]], delta_rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    by_method = {row["method"]: row for row in summary}
    lines = [
        "# Type 3 扩展候选池证据选择实验",
        "",
        "本实验把上一轮召回增强的候选池接入实际 Top-5 证据选择：候选池由 candidate Top-20、offline Top-K 和 intent-facet Top-K 合并得到，然后用无监督多信号打分与冗余惩罚选择证据。排序阶段不使用 gold evidence。",
        "",
        "## 参数",
        "",
        f"- offline_k：`{args.offline_k}`",
        f"- facet_k：`{args.facet_k}`",
        f"- select_k：`{args.select_k}`",
        f"- keep_top1：`{args.keep_top1}`",
        f"- redundancy_weight：`{args.redundancy_weight}`",
        "",
        "## 结果",
        "",
        "| 方法 | Rows | Pool | MRR | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 | Coverage@100 | Full@100 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("candidate_reranker", "candidate20_then_expansion", "expanded_pool_selector", "expanded_pool_oracle_top5"):
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['rows']} | {row['mean_pool_size']:.1f} | {metric(row['mrr'])} | "
                f"{metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | {metric(row['full_coverage@5'])} | "
                f"{metric(row['coverage_ratio@20'])} | {metric(row['full_coverage@20'])} | "
                f"{metric(row['coverage_ratio@100'])} | {metric(row['full_coverage@100'])} |"
            )
    lines.extend(["", "## 相比 Candidate Reranker 的变化", ""])
    for row in delta_rows:
        lines.append(
            f"- `{row['method']}`：MRR `{row['delta_mrr']:+.4f}`，R@5 `{row['delta_recall@5']:+.4f}`，"
            f"Coverage@5 `{row['delta_coverage_ratio@5']:+.4f}`，Full@5 `{row['delta_full_coverage@5']:+.4f}`，"
            f"Coverage@100 `{row['delta_coverage_ratio@100']:+.4f}`，Full@100 `{row['delta_full_coverage@100']:+.4f}`。"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果 Coverage@5/Full@5 提升，说明召回增强已经能转化为端到端证据选择收益。",
        "- `candidate20_then_expansion` 不改变原始 Top-20，只把扩展证据追加到后面，用来检验候选池收益是否可保守保留。",
        "- `expanded_pool_oracle_top5` 使用 gold evidence 构造上限，只用于诊断，不是可部署方法。",
        "- 如果 oracle 明显提升但 selector 不提升，说明候选池变好了，但 Top-5 selector 还不够强。",
        "- 如果 MRR 下降明显，说明扩展候选带来噪声，需要学习式 listwise/setwise 目标控制排序。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type3 expanded-pool evidence selector.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--offline-k", type=int, default=50)
    parser.add_argument("--facet-k", type=int, default=50)
    parser.add_argument("--select-k", type=int, default=5)
    parser.add_argument("--max-facets", type=int, default=6)
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--redundancy-weight", type=float, default=0.08)
    parser.add_argument("--keep-top1", action="store_true")
    parser.add_argument("--ks", default="1,3,5,20,50,100")
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = {query.id: query for query in load_queries(args.queries)}
    memory_by_id = {memory.id: memory for memory in memories}
    memory_tokens = build_memory_tokens(memories)
    memory_vectors = {memory.id: hashed_vector(memory_tokens[memory.id]) for memory in memories}
    idf = build_idf(memories)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    personas = known_personas(memories)
    importance_scores = build_importance_scores(memories)
    groups = load_candidate_rows(args.candidate_ranked)
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]

    per_query, ranked_rows = build_rows(
        groups,
        queries,
        memories,
        memory_by_id,
        memory_tokens,
        memory_vectors,
        idf,
        avg_len,
        personas,
        importance_scores,
        args,
    )
    summary = aggregate(per_query, ks)
    delta_rows = deltas(summary)
    write_csv(args.output_per_query, per_query)
    write_csv(args.output_ranked, ranked_rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, delta_rows)
    write_report(args.output_report, summary, delta_rows, args)
    print(json.dumps({
        "rows": len(per_query),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
