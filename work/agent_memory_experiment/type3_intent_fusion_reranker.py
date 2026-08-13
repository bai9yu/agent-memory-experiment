#!/usr/bin/env python3
"""Conservative Type-3 intent-facet fusion over candidate-reranker rows."""

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
    "is", "it", "kind", "likely", "might", "of", "on", "or", "she", "still",
    "that", "the", "their", "to", "was", "were", "what", "when", "where", "which",
    "who", "why", "with", "would",
}
CONNECTOR_RE = re.compile(r"\b(?:and|or|because|after|before|if|while|but|besides|based on|as)\b", re.IGNORECASE)
INTENT_PATTERNS = (
    (re.compile(r"\bwhy|because|reason|decide|decided|cause\b", re.IGNORECASE), "reason motive cause decision"),
    (re.compile(r"\bwhen|date|time|how long|recent|recently|last\b", re.IGNORECASE), "time date event recent"),
    (re.compile(r"\bwhere|country|state|city|place|location|live|moved?\b", re.IGNORECASE), "place location live move"),
    (re.compile(r"\bwho|friend|mother|father|partner|husband|wife|family\b", re.IGNORECASE), "person relationship family identity"),
    (re.compile(r"\bcareer|field|education|school|study|job|work|pursue\b", re.IGNORECASE), "career education work goal plan"),
    (re.compile(r"\blike|enjoy|favorite|prefer|love|hobby|activity\b", re.IGNORECASE), "preference hobby enjoy"),
    (re.compile(r"\bfeel|support|realize|learned|experience|worry|happy|sad\b", re.IGNORECASE), "emotion support experience"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def known_personas(memories: list[Memory]) -> set[str]:
    return {memory.agent_id.lower() for memory in memories if memory.agent_id}


def build_facets(query: Query, personas: set[str], max_facets: int) -> list[dict[str, str]]:
    query_people = sorted(query_personas(query, personas))
    person_prefix = " ".join(query_people)
    tokens = content_tokens(query.query)
    facets: list[dict[str, str]] = [{"facet_type": "original", "facet": query.query}]
    compact = " ".join(tokens)
    if compact and compact != query.query.lower():
        facets.append({"facet_type": "content", "facet": f"{person_prefix} {compact}".strip()})
    for part in CONNECTOR_RE.split(query.query):
        part_tokens = content_tokens(part)
        if len(part_tokens) >= 2:
            facets.append({"facet_type": "clause", "facet": f"{person_prefix} {' '.join(part_tokens)}".strip()})
    for pattern, intent_text in INTENT_PATTERNS:
        if pattern.search(query.query):
            facets.append({"facet_type": "intent", "facet": f"{person_prefix} {intent_text}".strip()})
            if compact:
                facets.append({"facet_type": "intent_content", "facet": f"{person_prefix} {intent_text} {compact}".strip()})
    deduped = []
    for facet in facets:
        for value in dedupe([facet["facet"]]):
            deduped.append({"facet_type": facet["facet_type"], "facet": value})
    return dedupe_facets(deduped)[:max_facets]


def dedupe_facets(facets: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out = []
    for row in facets:
        key = " ".join(tokenize(row["facet"]))
        if key and key not in seen:
            seen.add(key)
            out.append(row)
    return out


def load_candidate_rows(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "query_type": row.get("query_type", ""),
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row.get("memory_type", ""),
            "memory_text": row.get("memory_text", ""),
            "learned_score": float(row.get("learned_score", "0") or 0),
            "is_relevant": row.get("is_relevant") == "True",
            "source": "candidate",
        })
    for rows in groups.values():
        rows.sort(key=lambda row: row["rank"])
        scores = {row["memory_id"]: row["learned_score"] for row in rows}
        norm = normalize(scores)
        for row in rows:
            row["candidate_norm"] = norm[row["memory_id"]]
            row["candidate_rrf"] = 1.0 / (60.0 + row["rank"])
    return groups


def facet_retrieve(
    query: Query,
    facets: list[dict[str, str]],
    memories: list[Memory],
    memory_by_id: dict[str, Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    facet_top_k: int,
    half_life_days: float,
) -> dict[str, dict[str, Any]]:
    query_type_weights = query_intent_type_weights(query)
    query_persona_names = query_personas(query, personas)
    query_token_set = set(tokenize(query.query))
    query_recency_gate = recency_gate(query)
    per_memory: dict[str, dict[str, Any]] = {}
    for facet_index, facet_row in enumerate(facets):
        facet = facet_row["facet"]
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
        scores = {}
        for memory in memories:
            persona = persona_score(memory, query_persona_names)
            entity = entity_overlap(query_token_set, memory.entities)
            type_match = memory_type_score(memory, query_type_weights)
            recency = query_recency_gate * time_decay(memory.date, query.query_date, half_life_days)
            importance = importance_scores[memory.id]
            scores[memory.id] = (
                0.50 * bm25_norm[memory.id]
                + 0.22 * semantic_norm[memory.id]
                + 0.08 * entity
                + 0.07 * type_match
                + 0.05 * max(persona, 0.0)
                + 0.05 * importance
                + 0.03 * recency
            )
        for rank, memory_id in enumerate(sorted(scores, key=scores.get, reverse=True)[:facet_top_k], start=1):
            memory = memory_by_id[memory_id]
            row = per_memory.setdefault(
                memory_id,
                {
                    "memory_id": memory_id,
                    "memory_type": memory.memory_type,
                    "memory_text": memory.text,
                    "facet_rrf": 0.0,
                    "facet_hits": 0,
                    "best_facet": "",
                    "best_facet_type": "",
                    "best_facet_rank": 0,
                    "best_facet_score": 0.0,
                },
            )
            weighted_rrf = (1.25 if facet_index == 0 else 1.0) / (60.0 + rank)
            row["facet_rrf"] += weighted_rrf
            row["facet_hits"] += 1
            if scores[memory_id] > row["best_facet_score"]:
                row["best_facet_score"] = scores[memory_id]
                row["best_facet"] = facet
                row["best_facet_type"] = facet_row["facet_type"]
                row["best_facet_rank"] = rank
    return per_memory


def first_rank(rows: list[dict[str, Any]]) -> int:
    for rank, row in enumerate(rows, start=1):
        if row["is_relevant"]:
            return rank
    return 0


def ranking_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rank = first_rank(rows)
    return {
        "mrr": 1.0 / rank if rank else 0.0,
        "recall@1": 1.0 if rank and rank <= 1 else 0.0,
        "recall@3": 1.0 if rank and rank <= 3 else 0.0,
        "recall@5": 1.0 if rank and rank <= 5 else 0.0,
        "first_rank": rank,
    }


def coverage_metrics(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    out = {}
    ranked_ids = [row["memory_id"] for row in rows]
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def fuse_rows(
    candidate_rows: list[dict[str, Any]],
    facet_rows: dict[str, dict[str, Any]],
    memory_by_id: dict[str, Memory],
    gold_ids: set[str],
    candidate_weight: float,
    facet_weight: float,
    facet_hit_weight: float,
    keep_top1: bool,
    candidate_only: bool,
) -> list[dict[str, Any]]:
    by_memory: dict[str, dict[str, Any]] = {}
    for row in candidate_rows:
        item = by_memory.setdefault(row["memory_id"], dict(row))
        item["candidate_rrf"] = row.get("candidate_rrf", 0.0)
        item["candidate_norm"] = row.get("candidate_norm", 0.0)
        item["facet_rrf"] = 0.0
        item["facet_hits"] = 0
        item["best_facet"] = ""
        item["best_facet_type"] = ""
        item["best_facet_rank"] = 0
    candidate_ids = {row["memory_id"] for row in candidate_rows}
    for memory_id, row in facet_rows.items():
        if candidate_only and memory_id not in candidate_ids:
            continue
        memory = memory_by_id[memory_id]
        item = by_memory.setdefault(
            memory_id,
            {
                "split_seed": candidate_rows[0]["split_seed"] if candidate_rows else "",
                "query_id": candidate_rows[0]["query_id"] if candidate_rows else "",
                "query_type": "3",
                "rank": 999,
                "memory_id": memory_id,
                "memory_type": memory.memory_type,
                "memory_text": memory.text,
                "learned_score": 0.0,
                "candidate_norm": 0.0,
                "candidate_rrf": 0.0,
                "is_relevant": memory_id in gold_ids,
                "source": "facet",
            },
        )
        item["facet_rrf"] = row["facet_rrf"]
        item["facet_hits"] = row["facet_hits"]
        item["best_facet"] = row["best_facet"]
        item["best_facet_type"] = row["best_facet_type"]
        item["best_facet_rank"] = row["best_facet_rank"]
    fused = []
    for row in by_memory.values():
        score = (
            candidate_weight * row.get("candidate_rrf", 0.0)
            + 0.20 * row.get("candidate_norm", 0.0)
            + facet_weight * row.get("facet_rrf", 0.0)
            + facet_hit_weight * min(row.get("facet_hits", 0), 4)
        )
        fused.append({**row, "intent_fusion_score": score})
    pinned = []
    if keep_top1 and candidate_rows:
        top_id = candidate_rows[0]["memory_id"]
        pinned = [row for row in fused if row["memory_id"] == top_id]
        fused = [row for row in fused if row["memory_id"] != top_id]
    fused.sort(key=lambda row: row["intent_fusion_score"], reverse=True)
    return pinned + fused


def window_rerank(
    candidate_rows: list[dict[str, Any]],
    facet_rows: dict[str, dict[str, Any]],
    window_k: int,
    facet_weight: float,
    facet_hit_weight: float,
    keep_top1: bool,
) -> list[dict[str, Any]]:
    head = [dict(row) for row in candidate_rows[:window_k]]
    tail = [dict(row) for row in candidate_rows[window_k:]]
    for row in head:
        facet = facet_rows.get(row["memory_id"], {})
        row["facet_rrf"] = facet.get("facet_rrf", 0.0)
        row["facet_hits"] = facet.get("facet_hits", 0)
        row["best_facet"] = facet.get("best_facet", "")
        row["best_facet_type"] = facet.get("best_facet_type", "")
        row["best_facet_rank"] = facet.get("best_facet_rank", "")
        row["intent_fusion_score"] = (
            row.get("candidate_rrf", 0.0)
            + 0.20 * row.get("candidate_norm", 0.0)
            + facet_weight * row["facet_rrf"]
            + facet_hit_weight * min(row["facet_hits"], 4)
        )
    pinned = []
    if keep_top1 and head:
        pinned = [head[0]]
        head = head[1:]
    head.sort(key=lambda row: row["intent_fusion_score"], reverse=True)
    return pinned + head + tail


def aggregate(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    out = []
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_method[row["method"]].append(row)
    for method, bucket in sorted(by_method.items()):
        item = {
            "method": method,
            "num_rows": len(bucket),
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


def deltas(summary: list[dict[str, Any]], baseline: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method[baseline]
    rows = []
    for method, row in by_method.items():
        if method == baseline:
            continue
        out = {"baseline": baseline, "method": method}
        for name in ("mrr", "recall@1", "recall@3", "recall@5", "coverage_ratio@5", "full_coverage@5", "coverage_ratio@20", "full_coverage@20"):
            out[f"delta_{name}"] = row[name] - base[name]
        rows.append(out)
    return rows


def write_report(path: Path, summary: list[dict[str, Any]], delta_rows: list[dict[str, Any]], facets: list[dict[str, Any]], args: argparse.Namespace) -> None:
    by_method = {row["method"]: row for row in summary}
    lines = [
        "# Type 3 Intent-Facet Fusion 优化实验",
        "",
        "本实验针对 Type 3 多证据问题做保守优化：不替换已有 candidate reranker，而是为每个问题生成少量高置信度检索意图 facet，从全量记忆库补充候选，再用 RRF、候选分数和 facet 命中次数融合排序。",
        "",
        "该方法不调用大模型，也不使用 gold evidence 参与打分；gold evidence 只用于最终评估。",
        "",
        "## 参数",
        "",
        f"- max_facets：`{args.max_facets}`",
        f"- facet_top_k：`{args.facet_top_k}`",
        f"- candidate_weight：`{args.candidate_weight}`",
        f"- facet_weight：`{args.facet_weight}`",
        f"- facet_hit_weight：`{args.facet_hit_weight}`",
        "",
        "## 结果",
        "",
        "| 方法 | Rows | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in (
        "candidate_reranker",
        "intent_fusion_top5_window_keep_top1",
        "intent_fusion_top5_window_free",
        "intent_fusion_candidate_only_keep_top1",
        "intent_fusion_candidate_only_free",
        "intent_fusion_keep_top1",
        "intent_fusion_free",
    ):
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['num_rows']} | {metric(row['mrr'])} | {metric(row['recall@1'])} | "
                f"{metric(row['recall@3'])} | {metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | "
                f"{metric(row['full_coverage@5'])} | {metric(row['coverage_ratio@20'])} | {metric(row['full_coverage@20'])} |"
            )
    lines.extend(["", "## 相比 Candidate Reranker 的变化", ""])
    for row in delta_rows:
        lines.append(
            f"- `{row['method']}`：MRR `{row['delta_mrr']:+.4f}`，R@5 `{row['delta_recall@5']:+.4f}`，"
            f"Coverage@5 `{row['delta_coverage_ratio@5']:+.4f}`，Full@5 `{row['delta_full_coverage@5']:+.4f}`。"
        )
    lines.extend([
        "",
        "## Facet 示例",
        "",
        "| Query | Facets |",
        "|---|---|",
    ])
    for row in facets[:10]:
        lines.append(f"| {row['query'].replace('|', '/')} | {row['facets'].replace('|', '/')} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果 `intent_fusion_keep_top1` 提升，说明保留强首位证据后，意图补召回有助于增加多证据覆盖。",
        "- 如果 `intent_fusion_free` 提升但 MRR 下降，说明它更偏向集合覆盖，可能适合作为生成回答前的证据包选择器。",
        "- 如果两者仍下降，说明 Type 3 的主要瓶颈不是候选补召回，而是需要学习式 set/listwise 目标或更强的 LLM 子问题生成。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3 intent-facet fusion reranker.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,20")
    parser.add_argument("--max-facets", type=int, default=6)
    parser.add_argument("--facet-top-k", type=int, default=40)
    parser.add_argument("--candidate-weight", type=float, default=4.0)
    parser.add_argument("--facet-weight", type=float, default=1.6)
    parser.add_argument("--facet-hit-weight", type=float, default=0.012)
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-facets", type=Path, required=True)
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
    candidate_groups = load_candidate_rows(args.candidate_ranked)
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]

    per_query = []
    ranked_out = []
    facet_out = []
    for (seed, query_id), candidate_rows in sorted(candidate_groups.items()):
        query = queries.get(query_id)
        if not query or query.type != "3":
            continue
        gold_ids = set(query.answer_memory_ids)
        facets = build_facets(query, personas, args.max_facets)
        facet_rows = facet_retrieve(
            query,
            facets,
            memories,
            memory_by_id,
            memory_tokens,
            memory_vectors,
            idf,
            avg_len,
            personas,
            importance_scores,
            args.facet_top_k,
            args.half_life_days,
        )
        methods = {
            "candidate_reranker": candidate_rows,
            "intent_fusion_top5_window_keep_top1": window_rerank(
                candidate_rows,
                facet_rows,
                window_k=5,
                facet_weight=args.facet_weight,
                facet_hit_weight=args.facet_hit_weight,
                keep_top1=True,
            ),
            "intent_fusion_top5_window_free": window_rerank(
                candidate_rows,
                facet_rows,
                window_k=5,
                facet_weight=args.facet_weight,
                facet_hit_weight=args.facet_hit_weight,
                keep_top1=False,
            ),
            "intent_fusion_candidate_only_keep_top1": fuse_rows(
                candidate_rows,
                facet_rows,
                memory_by_id,
                gold_ids,
                args.candidate_weight,
                args.facet_weight,
                args.facet_hit_weight,
                keep_top1=True,
                candidate_only=True,
            ),
            "intent_fusion_candidate_only_free": fuse_rows(
                candidate_rows,
                facet_rows,
                memory_by_id,
                gold_ids,
                args.candidate_weight,
                args.facet_weight,
                args.facet_hit_weight,
                keep_top1=False,
                candidate_only=True,
            ),
            "intent_fusion_keep_top1": fuse_rows(
                candidate_rows,
                facet_rows,
                memory_by_id,
                gold_ids,
                args.candidate_weight,
                args.facet_weight,
                args.facet_hit_weight,
                keep_top1=True,
                candidate_only=False,
            ),
            "intent_fusion_free": fuse_rows(
                candidate_rows,
                facet_rows,
                memory_by_id,
                gold_ids,
                args.candidate_weight,
                args.facet_weight,
                args.facet_hit_weight,
                keep_top1=False,
                candidate_only=False,
            ),
        }
        facet_out.append({
            "split_seed": seed,
            "query_id": query_id,
            "query": query.query,
            "num_facets": len(facets),
            "facets": " || ".join(f"{row['facet_type']}:{row['facet']}" for row in facets),
            "num_facet_candidates": len(facet_rows),
            "num_gold": len(gold_ids),
        })
        for method, rows in methods.items():
            per_query.append({
                "split_seed": seed,
                "query_id": query_id,
                "query_type": query.type,
                "query": query.query,
                "method": method,
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                **ranking_metrics(rows),
                **coverage_metrics(rows, gold_ids, ks),
            })
            for rank, row in enumerate(rows[: max(ks)], start=1):
                ranked_out.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "is_relevant": row["is_relevant"],
                    "candidate_rrf": row.get("candidate_rrf", 0.0),
                    "facet_rrf": row.get("facet_rrf", 0.0),
                    "facet_hits": row.get("facet_hits", 0),
                    "intent_fusion_score": row.get("intent_fusion_score", ""),
                    "best_facet_type": row.get("best_facet_type", ""),
                    "best_facet_rank": row.get("best_facet_rank", ""),
                    "memory_text": row["memory_text"],
                })

    summary = aggregate(per_query, ks)
    delta_rows = deltas(summary, "candidate_reranker")
    write_csv(args.output_per_query, per_query)
    write_csv(args.output_ranked, ranked_out)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, delta_rows)
    write_csv(args.output_facets, facet_out)
    write_report(args.output_report, summary, delta_rows, facet_out, args)
    print(json.dumps({
        "num_rows": len(per_query),
        "num_type3_query_splits": len(facet_out),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
