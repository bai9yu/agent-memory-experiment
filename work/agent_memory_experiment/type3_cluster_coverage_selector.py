#!/usr/bin/env python3
"""Select Type-3 evidence with cluster-coverage rewards over expanded pools."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from memory_eval import build_idf, build_importance_scores, build_memory_tokens, hashed_vector, load_memories, load_queries, tokenize
from query_type_router_experiment import metric, write_csv
from type3_expanded_pool_selector import (
    append_expansion_after_candidate,
    base_score,
    build_pool,
    facet_rankings,
    known_personas,
    load_candidate_rows,
    metrics,
    oracle_select,
    score_all_memories,
)


STOPWORDS = {
    "about", "after", "again", "also", "because", "before", "being", "between", "could", "during",
    "early", "first", "from", "have", "into", "just", "like", "more", "most", "much", "only",
    "other", "over", "same", "some", "still", "than", "that", "their", "them", "then", "there",
    "these", "they", "this", "through", "when", "where", "which", "while", "with", "would",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def content_terms(text: str) -> list[str]:
    return [token for token in tokenize(text) if len(token) > 2 and token not in STOPWORDS]


def top_terms(text: str, limit: int) -> tuple[str, ...]:
    counts = Counter(content_terms(text))
    return tuple(term for term, _ in counts.most_common(limit))


def cluster_key(row: dict[str, Any], term_limit: int) -> str:
    memory_type = row.get("memory_type", "")
    terms = top_terms(str(row.get("memory_text", "")), term_limit)
    if terms:
        return f"{memory_type}:{' '.join(terms)}"
    return f"{memory_type}:{row.get('memory_id', '')}"


def cluster_similarity(left: str, right: str) -> float:
    left_type, _, left_terms = left.partition(":")
    right_type, _, right_terms = right.partition(":")
    left_set = set(left_terms.split())
    right_set = set(right_terms.split())
    if not left_set or not right_set:
        return 0.0
    overlap = len(left_set & right_set) / len(left_set | right_set)
    if left_type and left_type == right_type:
        overlap += 0.05
    return min(overlap, 1.0)


def build_query_pool(
    query: Any,
    candidate_rows: list[dict[str, Any]],
    memories: list[Any],
    memory_by_id: dict[str, Any],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    offline_scores = score_all_memories(
        query,
        memories,
        memory_tokens,
        memory_vectors,
        idf,
        avg_len,
        personas,
        importance_scores,
        args.half_life_days,
    )
    facet_scores = facet_rankings(
        query,
        memories,
        memory_tokens,
        memory_vectors,
        idf,
        avg_len,
        personas,
        args.max_facets,
    )
    pool = build_pool(candidate_rows, offline_scores, facet_scores, memory_by_id, args.offline_k, args.facet_k)
    for row in pool:
        row["cluster_key"] = cluster_key(row, args.cluster_terms)
        row["selector_base_score"] = base_score(row)
    return pool


def cluster_coverage_select(
    pool: list[dict[str, Any]],
    select_k: int,
    keep_top1: bool,
    cluster_bonus: float,
    near_duplicate_penalty: float,
) -> list[dict[str, Any]]:
    remaining = [dict(row) for row in pool]
    selected: list[dict[str, Any]] = []
    covered_clusters: set[str] = set()
    if keep_top1:
        top1 = [row for row in remaining if row.get("candidate_rank") == 1]
        if top1:
            row = dict(top1[0])
            row["cluster_selector_score"] = row["selector_base_score"]
            selected.append(row)
            covered_clusters.add(row["cluster_key"])
            remaining = [item for item in remaining if item["memory_id"] != row["memory_id"]]
    while remaining and len(selected) < select_k:
        best = None
        best_score = float("-inf")
        for row in remaining:
            cluster = row["cluster_key"]
            novelty = 1.0 if cluster not in covered_clusters else 0.0
            max_cluster_similarity = max((cluster_similarity(cluster, chosen["cluster_key"]) for chosen in selected), default=0.0)
            score = row["selector_base_score"] + cluster_bonus * novelty - near_duplicate_penalty * max_cluster_similarity
            if score > best_score:
                best = row
                best_score = score
        chosen = dict(best)
        chosen["cluster_selector_score"] = best_score
        selected.append(chosen)
        covered_clusters.add(chosen["cluster_key"])
        remaining = [row for row in remaining if row["memory_id"] != chosen["memory_id"]]
    selected_ids = {row["memory_id"] for row in selected}
    tail = [
        dict(row, cluster_selector_score=row["selector_base_score"])
        for row in remaining
        if row["memory_id"] not in selected_ids
    ]
    tail.sort(key=lambda row: row["selector_base_score"], reverse=True)
    return selected + tail


def score_methods(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
    per_query = []
    ranked_rows = []
    for (seed, query_id), candidate_rows in sorted(groups.items()):
        query = queries.get(query_id)
        if not query or query.type != "3":
            continue
        gold_ids = set(query.answer_memory_ids)
        pool = build_query_pool(
            query,
            candidate_rows,
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
        for row in pool:
            row["is_relevant"] = row["memory_id"] in gold_ids
        original = []
        by_pool_id = {row["memory_id"]: row for row in pool}
        for row in candidate_rows:
            enriched = dict(by_pool_id.get(row["memory_id"], row))
            enriched["is_relevant"] = row["memory_id"] in gold_ids
            original.append(enriched)
        appended = append_expansion_after_candidate(original, pool)
        selected = cluster_coverage_select(
            pool,
            args.select_k,
            args.keep_top1,
            args.cluster_bonus,
            args.near_duplicate_penalty,
        )
        oracle = oracle_select(pool, gold_ids, args.select_k)
        methods = {
            "candidate20_then_expansion": appended,
            "cluster_coverage_selector": selected,
            "expanded_pool_oracle_top5": oracle,
        }
        for method, rows in methods.items():
            for row in rows:
                row["is_relevant"] = row["memory_id"] in gold_ids
            per_query.append({
                "split_seed": seed,
                "query_id": query_id,
                "query": query.query,
                "method": method,
                "pool_size": len(rows),
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                "top5_cluster_count": len({row.get("cluster_key", "") for row in rows[:5]}),
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
                    "cluster_key": row.get("cluster_key", ""),
                    "is_relevant": row.get("is_relevant", False),
                    "cluster_selector_score": row.get("cluster_selector_score", ""),
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
            "top5_cluster_count": statistics.mean(row["top5_cluster_count"] for row in bucket),
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
    base = by_method["candidate20_then_expansion"]
    rows = []
    for method, row in by_method.items():
        if method == "candidate20_then_expansion":
            continue
        out = {"baseline": "candidate20_then_expansion", "method": method}
        for name in ("mrr", "recall@5", "coverage_ratio@5", "full_coverage@5", "top5_cluster_count", "coverage_ratio@100", "full_coverage@100"):
            out[f"delta_{name}"] = row[name] - base[name]
        rows.append(out)
    return rows


def write_report(path: Path, summary: list[dict[str, Any]], delta_rows: list[dict[str, Any]], args: argparse.Namespace) -> None:
    by_method = {row["method"]: row for row in summary}
    lines = [
        "# Type 3 集合级覆盖簇选择实验",
        "",
        "本实验验证一个更接近多证据检索目标的选择策略：在扩展候选池上进行 Top-5 选择时，不只看单条候选分数，还奖励覆盖新的文本关键词簇，并惩罚与已选证据高度相似的候选。排序阶段不使用 gold evidence。",
        "",
        "## 参数",
        "",
        f"- cluster_terms：`{args.cluster_terms}`",
        f"- cluster_bonus：`{args.cluster_bonus}`",
        f"- near_duplicate_penalty：`{args.near_duplicate_penalty}`",
        f"- keep_top1：`{args.keep_top1}`",
        "",
        "## 结果",
        "",
        "| 方法 | Rows | Pool | Top5 Clusters | MRR | R@5 | Coverage@5 | Full@5 | Coverage@100 | Full@100 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("candidate20_then_expansion", "cluster_coverage_selector", "expanded_pool_oracle_top5"):
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['rows']} | {row['mean_pool_size']:.1f} | {row['top5_cluster_count']:.2f} | "
                f"{metric(row['mrr'])} | {metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | "
                f"{metric(row['full_coverage@5'])} | {metric(row['coverage_ratio@100'])} | {metric(row['full_coverage@100'])} |"
            )
    lines.extend(["", "## 相比 Candidate20 Then Expansion 的变化", ""])
    for row in delta_rows:
        lines.append(
            f"- `{row['method']}`：MRR `{row['delta_mrr']:+.4f}`，R@5 `{row['delta_recall@5']:+.4f}`，"
            f"Coverage@5 `{row['delta_coverage_ratio@5']:+.4f}`，Full@5 `{row['delta_full_coverage@5']:+.4f}`，"
            f"Top5 cluster count `{row['delta_top5_cluster_count']:+.4f}`。"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果 Top5 cluster count 上升但 Coverage@5 不升，说明表面多样性没有对齐 gold evidence。",
        "- 如果 Coverage@5/Full@5 上升，说明集合级覆盖信号可以把扩展候选池收益转化为最终证据选择收益。",
        "- 如果仍低于 oracle，下一步应从无监督簇覆盖转向监督式 setwise/listwise 选择。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type3 cluster coverage selector over expanded pools.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--offline-k", type=int, default=50)
    parser.add_argument("--facet-k", type=int, default=50)
    parser.add_argument("--select-k", type=int, default=5)
    parser.add_argument("--max-facets", type=int, default=6)
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--cluster-terms", type=int, default=4)
    parser.add_argument("--cluster-bonus", type=float, default=0.035)
    parser.add_argument("--near-duplicate-penalty", type=float, default=0.04)
    parser.add_argument("--keep-top1", action="store_true")
    parser.add_argument("--ks", default="1,3,5,20,50,100")
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    per_query, ranked_rows = score_methods(args)
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
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
