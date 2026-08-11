#!/usr/bin/env python3
"""Evaluate a heuristic query-decomposition retrieval baseline for Type-3 queries."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from memory_eval import (
    Memory,
    Query,
    bm25_score,
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    entity_overlap,
    load_memories,
    load_queries,
    memory_type_score,
    normalize,
    persona_score,
    query_intent_type_weights,
    query_personas,
    tokenize,
)
from query_type_router_experiment import metric, write_csv


STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "at", "be", "been", "besides",
    "based", "by", "cause", "considered", "did", "does", "do", "for", "from",
    "had", "has", "have", "her", "his", "if", "in", "is", "it", "likely",
    "might", "more", "of", "on", "or", "own", "person", "say", "still",
    "than", "that", "the", "their", "to", "use", "was", "were", "what",
    "when", "where", "which", "who", "why", "with", "would",
}
SPLIT_RE = re.compile(r"\b(?:and|or|if|after|besides|based on|as|because|than)\b", re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def known_personas(memories: list[Memory]) -> set[str]:
    return {memory.agent_id.lower() for memory in memories if memory.agent_id}


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        key = " ".join(tokenize(item))
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def decompose_query(query: Query, persona_names: set[str], max_facets: int) -> list[str]:
    personas = [name for name in persona_names if name in query.query.lower()]
    persona_prefix = " ".join(personas)
    tokens = content_tokens(query.query)
    facets = [query.query]
    stripped = " ".join(tokens)
    if stripped:
        facets.append(f"{persona_prefix} {stripped}".strip())

    for part in SPLIT_RE.split(query.query):
        part_tokens = content_tokens(part)
        if part_tokens:
            facets.append(f"{persona_prefix} {' '.join(part_tokens)}".strip())

    for n in (2, 3, 4):
        for idx in range(0, max(0, len(tokens) - n + 1)):
            window = tokens[idx : idx + n]
            if window:
                facets.append(f"{persona_prefix} {' '.join(window)}".strip())

    if personas:
        for token in tokens:
            facets.append(f"{persona_prefix} {token}".strip())
    return dedupe(facets)[:max_facets]


def load_type_aware_ranked(rankings_path: Path, max_k: int) -> dict[str, list[str]]:
    ranked: dict[str, list[str]] = defaultdict(list)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if len(ranked[row["query_id"]]) < max_k:
                ranked[row["query_id"]].append(row["memory_id"])
    return ranked


def load_type_aware_ranked_rows(rankings_path: Path, max_k: int) -> dict[str, list[dict[str, Any]]]:
    ranked: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if len(ranked[row["query_id"]]) < max_k:
                ranked[row["query_id"]].append({
                    "memory_id": row["memory_id"],
                    "memory_text": row["memory_text"],
                    "memory_type": row["memory_type"],
                    "final_score": float(row["final_score"]),
                    "is_relevant": row["is_relevant"] == "True",
                })
    return ranked


def load_baseline_metrics(per_query_path: Path, method: str) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in read_csv(per_query_path):
        if row["method"] == method:
            rows[row["query_id"]] = {
                "mrr": float(row["mrr"]),
                "recall@1": float(row["recall@1"]),
                "recall@3": float(row["recall@3"]),
                "recall@5": float(row["recall@5"]),
                "first_rank": row.get("first_rank", ""),
            }
    return rows


def coverage_for_ids(ranked_ids: list[str], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    out = {}
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def ranking_metrics(ranked_ids: list[str], gold_ids: set[str]) -> dict[str, Any]:
    first_rank = 0
    for rank, memory_id in enumerate(ranked_ids, start=1):
        if memory_id in gold_ids:
            first_rank = rank
            break
    return {
        "mrr": 1.0 / first_rank if first_rank else 0.0,
        "recall@1": 1.0 if first_rank and first_rank <= 1 else 0.0,
        "recall@3": 1.0 if first_rank and first_rank <= 3 else 0.0,
        "recall@5": 1.0 if first_rank and first_rank <= 5 else 0.0,
        "first_rank": first_rank,
    }


def fuse_rankings(
    type_aware_rows: list[dict[str, Any]],
    decomp_rows: list[dict[str, Any]],
    type_weight: float,
    decomp_weight: float,
) -> list[dict[str, Any]]:
    by_memory: dict[str, dict[str, Any]] = {}
    for rank, row in enumerate(type_aware_rows, start=1):
        item = by_memory.setdefault(row["memory_id"], dict(row))
        item["type_aware_rank"] = rank
        item["type_aware_rrf"] = 1.0 / (60.0 + rank)
        item["decomp_rrf"] = item.get("decomp_rrf", 0.0)
    for rank, row in enumerate(decomp_rows, start=1):
        item = by_memory.setdefault(row["memory_id"], dict(row))
        item["decomp_rank"] = rank
        item["decomp_rrf"] = 1.0 / (60.0 + rank)
        item["type_aware_rrf"] = item.get("type_aware_rrf", 0.0)
    fused = []
    for memory_id, row in by_memory.items():
        fused_score = type_weight * row.get("type_aware_rrf", 0.0) + decomp_weight * row.get("decomp_rrf", 0.0)
        fused.append({**row, "memory_id": memory_id, "final_score": fused_score})
    fused.sort(key=lambda row: row["final_score"], reverse=True)
    return fused


def rank_decomposed(
    query: Query,
    memories: list[Memory],
    memory_tokens: dict[str, list[str]],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    max_facets: int,
    facet_top_k: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    persona_names = query_personas(query, personas)
    facets = decompose_query(query, persona_names, max_facets)
    query_type_weights = query_intent_type_weights(query)
    query_token_set = set(tokenize(query.query))
    per_memory: dict[str, dict[str, Any]] = {}
    memory_by_id = {memory.id: memory for memory in memories}
    for facet_idx, facet in enumerate(facets):
        facet_tokens = tokenize(facet)
        raw_scores = {
            memory.id: bm25_score(facet_tokens, memory_tokens[memory.id], idf, avg_len)
            for memory in memories
        }
        norm_scores = normalize(raw_scores)
        ranked_ids = sorted(norm_scores, key=lambda memory_id: norm_scores[memory_id], reverse=True)
        for rank, memory_id in enumerate(ranked_ids[:facet_top_k], start=1):
            memory = memory_by_id[memory_id]
            row = per_memory.setdefault(
                memory_id,
                {
                    "memory": memory,
                    "max_facet_score": 0.0,
                    "rrf_score": 0.0,
                    "facet_hits": 0,
                    "best_facet": "",
                    "best_facet_rank": 0,
                },
            )
            score = norm_scores[memory_id]
            row["facet_hits"] += 1
            row["rrf_score"] += 1.0 / (60.0 + rank)
            if score > row["max_facet_score"]:
                row["max_facet_score"] = score
                row["best_facet"] = facet
                row["best_facet_rank"] = rank

    ranked = []
    for memory_id, row in per_memory.items():
        memory = row["memory"]
        persona = persona_score(memory, persona_names)
        entity = entity_overlap(query_token_set, memory.entities)
        type_match = memory_type_score(memory, query_type_weights)
        importance = importance_scores[memory_id]
        final = (
            0.62 * row["max_facet_score"]
            + 10.0 * row["rrf_score"]
            + 0.06 * entity
            + 0.04 * type_match
            + 0.04 * max(persona, 0.0)
            + 0.03 * importance
            + 0.02 * min(row["facet_hits"], 5)
        )
        ranked.append({
            "query_id": query.id,
            "query_type": query.type,
            "memory_id": memory_id,
            "memory_text": memory.text,
            "memory_type": memory.memory_type,
            "final_score": final,
            "max_facet_score": row["max_facet_score"],
            "rrf_score": row["rrf_score"],
            "facet_hits": row["facet_hits"],
            "best_facet": row["best_facet"],
            "best_facet_rank": row["best_facet_rank"],
            "is_relevant": memory_id in query.answer_memory_ids,
        })
    ranked.sort(key=lambda row: row["final_score"], reverse=True)
    return ranked, facets


def aggregate(rows: list[dict[str, Any]], methods: list[str], ks: list[int]) -> list[dict[str, Any]]:
    output = []
    for method in methods:
        bucket = [row for row in rows if row["method"] == method]
        if not bucket:
            continue
        item = {
            "method": method,
            "num_queries": len(bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
            "mrr": statistics.mean(row["mrr"] for row in bucket),
            "recall@1": statistics.mean(row["recall@1"] for row in bucket),
            "recall@3": statistics.mean(row["recall@3"] for row in bucket),
            "recall@5": statistics.mean(row["recall@5"] for row in bucket),
        }
        for k in ks:
            for metric_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                item[metric_name] = statistics.mean(row[metric_name] for row in bucket)
        output.append(item)
    return output


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    example_rows: list[dict[str, Any]],
    max_facets: int,
    facet_top_k: int,
    type_weight: float,
    decomp_weight: float,
) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    lines = [
        "# Type 3 Query Decomposition 检索基线",
        "",
        "本实验针对 LoCoMo Type 3 推理/多证据问题，使用无训练的 query decomposition：从原 query 中抽取人物名、内容关键词和短窗口 facet query，分别做 BM25 召回，再用 RRF 与轻量 persona/type/importance 特征合并候选。",
        "",
        f"参数：max_facets=`{max_facets}`，facet_top_k=`{facet_top_k}`，fusion type_weight=`{type_weight}`，decomp_weight=`{decomp_weight}`。该方法不使用 gold evidence 调参。",
        "",
        "## Type 3 全量结果",
        "",
        "| 方法 | Queries | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("type_aware", "query_decomposition", "type_aware_plus_decomposition"):
        row = by_method.get(method)
        if not row:
            continue
        lines.append(
            f"| {method} | {row['num_queries']} | {metric(row['mrr'])} | {metric(row['recall@1'])} | "
            f"{metric(row['recall@3'])} | {metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | "
            f"{metric(row['full_coverage@5'])} | {metric(row['coverage_ratio@20'])} | {metric(row['full_coverage@20'])} |"
        )
    if "type_aware" in by_method and "type_aware_plus_decomposition" in by_method:
        base = by_method["type_aware"]
        cand = by_method["type_aware_plus_decomposition"]
        lines.extend([
            "",
            "## 融合方法相比 Type-Aware 的变化",
            "",
            f"- MRR delta：`{cand['mrr'] - base['mrr']:.4f}`",
            f"- Recall@5 delta：`{cand['recall@5'] - base['recall@5']:.4f}`",
            f"- Coverage@5 delta：`{cand['coverage_ratio@5'] - base['coverage_ratio@5']:.4f}`",
            f"- Coverage@20 delta：`{cand['coverage_ratio@20'] - base['coverage_ratio@20']:.4f}`",
        ])
    lines.extend([
        "",
        "## 代表性拆解示例",
        "",
        "| Query | Facets | First Relevant Rank | Coverage@5 |",
        "|---|---|---:|---:|",
    ])
    for row in example_rows[:10]:
        query = row["query"].replace("|", "/")
        facets = row["facets"].replace("|", "/")
        lines.append(f"| {query} | {facets} | {row['first_rank']} | {metric(row['coverage_ratio@5'])} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果纯拆解低于 `type_aware` 但融合方法提升，说明 decomposition 可作为辅助召回信号。",
        "- 如果融合方法也低于 `type_aware`，说明关键词式拆解噪声过大，需要 LLM/规则更准确地生成子问题。",
        "- 该实验是 query decomposition 的弱基线，主要用于判断是否值得继续投入更强的拆解模型。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3 query decomposition retrieval baseline.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,10,20")
    parser.add_argument("--max-facets", type=int, default=12)
    parser.add_argument("--facet-top-k", type=int, default=80)
    parser.add_argument("--fusion-type-weight", type=float, default=4.0)
    parser.add_argument("--fusion-decomp-weight", type=float, default=1.0)
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-facets", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = [query for query in load_queries(args.queries) if query.type == "3"]
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    memory_tokens = build_memory_tokens(memories)
    idf = build_idf(memories)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    personas = known_personas(memories)
    importance_scores = build_importance_scores(memories)
    type_aware_ranked = load_type_aware_ranked(args.rankings, max(ks))
    type_aware_ranked_rows = load_type_aware_ranked_rows(args.rankings, 100)
    baseline_metrics = load_baseline_metrics(args.per_query, args.baseline_method)

    per_query_rows = []
    ranked_rows = []
    facet_rows = []
    for query in queries:
        gold_ids = set(query.answer_memory_ids)
        ranked, facets = rank_decomposed(
            query,
            memories,
            memory_tokens,
            idf,
            avg_len,
            personas,
            importance_scores,
            args.max_facets,
            args.facet_top_k,
        )
        ranked_ids = [row["memory_id"] for row in ranked]
        fused = fuse_rankings(
            type_aware_ranked_rows.get(query.id, []),
            ranked,
            args.fusion_type_weight,
            args.fusion_decomp_weight,
        )
        fused_ids = [row["memory_id"] for row in fused]
        decomp_metrics = ranking_metrics(ranked_ids, gold_ids)
        decomp_cov = coverage_for_ids(ranked_ids, gold_ids, ks)
        fused_metrics = ranking_metrics(fused_ids, gold_ids)
        fused_cov = coverage_for_ids(fused_ids, gold_ids, ks)
        base_ranked_ids = type_aware_ranked.get(query.id, [])
        base_cov = coverage_for_ids(base_ranked_ids, gold_ids, ks)
        base_metrics = baseline_metrics.get(query.id, ranking_metrics(base_ranked_ids, gold_ids))
        for method, metrics, coverage in (
            ("type_aware", base_metrics, base_cov),
            ("query_decomposition", decomp_metrics, decomp_cov),
            ("type_aware_plus_decomposition", fused_metrics, fused_cov),
        ):
            per_query_rows.append({
                "query_id": query.id,
                "query_type": query.type,
                "query": query.query,
                "method": method,
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                **metrics,
                **coverage,
            })
        for rank, row in enumerate(ranked[: max(ks)], start=1):
            ranked_rows.append({
                "query_id": query.id,
                "query_type": query.type,
                "method": "query_decomposition",
                "rank": rank,
                "memory_id": row["memory_id"],
                "memory_type": row["memory_type"],
                "final_score": row["final_score"],
                "facet_hits": row["facet_hits"],
                "best_facet": row["best_facet"],
                "best_facet_rank": row["best_facet_rank"],
                "is_relevant": row["is_relevant"],
                "memory_text": row["memory_text"],
            })
        for rank, row in enumerate(fused[: max(ks)], start=1):
            ranked_rows.append({
                "query_id": query.id,
                "query_type": query.type,
                "method": "type_aware_plus_decomposition",
                "rank": rank,
                "memory_id": row["memory_id"],
                "memory_type": row["memory_type"],
                "final_score": row["final_score"],
                "facet_hits": row.get("facet_hits", 0),
                "best_facet": row.get("best_facet", ""),
                "best_facet_rank": row.get("best_facet_rank", 0),
                "is_relevant": row["is_relevant"],
                "memory_text": row["memory_text"],
            })
        facet_rows.append({
            "query_id": query.id,
            "query": query.query,
            "num_facets": len(facets),
            "facets": " || ".join(facets),
            **decomp_metrics,
            **decomp_cov,
        })

    summary_rows = aggregate(per_query_rows, ["type_aware", "query_decomposition", "type_aware_plus_decomposition"], ks)
    examples = sorted(facet_rows, key=lambda row: (row["coverage_ratio@5"], row["mrr"]), reverse=True)
    write_csv(args.output_per_query, per_query_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_csv(args.output_facets, facet_rows)
    write_report(
        args.output_report,
        summary_rows,
        examples,
        args.max_facets,
        args.facet_top_k,
        args.fusion_type_weight,
        args.fusion_decomp_weight,
    )
    print(json.dumps({
        "num_type3_queries": len(queries),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
