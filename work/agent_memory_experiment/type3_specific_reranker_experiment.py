#!/usr/bin/env python3
"""Evaluate a Type-3-specific candidate reranker for multi-evidence queries."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from candidate_reranker_experiment import (
    aggregate,
    candidate_oracle_rows,
    load_baseline,
    load_candidates,
    score_ranked_query,
    summarize_across_splits,
    train_predict,
)
from query_type_router_experiment import metric, write_csv


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def coverage_for_ranked(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    ranked_ids = [row["memory_id"] for row in rows]
    out = {}
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def load_type_aware_ranked(rankings_path: Path, max_k: int) -> dict[str, list[str]]:
    ranked: dict[str, list[str]] = defaultdict(list)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if len(ranked[row["query_id"]]) < max_k:
                ranked[row["query_id"]].append(row["memory_id"])
    return ranked


def score_ranked_ids(ranked_ids: list[str], candidates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ranked_rows = [candidates[memory_id] for memory_id in ranked_ids if memory_id in candidates]
    return score_ranked_query(ranked_rows)


def evaluate_method_rows(
    seed: int,
    query_ids: list[str],
    method: str,
    ranked_by_query: dict[str, list[dict[str, Any]]],
    queries: dict[str, dict[str, Any]],
    ks: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metric_rows = []
    coverage_rows = []
    for query_id in query_ids:
        ranked = ranked_by_query[query_id]
        scored = score_ranked_query(ranked)
        gold_ids = set(queries[query_id].get("answer_memory_ids", []))
        metric_rows.append({
            "split_seed": seed,
            "query_id": query_id,
            "query_type": queries[query_id].get("type", ""),
            "method": method,
            **scored,
        })
        coverage_rows.append({
            "split_seed": seed,
            "query_id": query_id,
            "query_type": queries[query_id].get("type", ""),
            "method": method,
            "num_gold": len(gold_ids),
            "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            **coverage_for_ranked(ranked, gold_ids, ks),
        })
    return metric_rows, coverage_rows


def aggregate_coverage(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    summary = []
    for method, bucket in sorted(buckets.items()):
        out = {
            "method": method,
            "num_rows": len(bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
        }
        for k in ks:
            for metric_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[metric_name] = statistics.mean(row[metric_name] for row in bucket)
        summary.append(out)
    return summary


def summarize_features(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    by_feature: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_feature[row["feature"]].append(float(row["importance"]))
    summary = []
    for feature, values in by_feature.items():
        summary.append({
            "feature": feature,
            "splits": len(values),
            "importance_mean": statistics.mean(values),
            "importance_stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        })
    summary.sort(key=lambda row: row["importance_mean"], reverse=True)
    return summary[:top_n]


def evaluate_split(
    seed: int,
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    queries: dict[str, dict[str, Any]],
    type_aware_ranked_ids: dict[str, list[str]],
    methods: list[str],
    train_fraction: float,
    ks: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(query_ids)
    rng.shuffle(shuffled)
    train_size = int(len(shuffled) * train_fraction)
    train_ids = sorted(shuffled[:train_size])
    test_ids = sorted(shuffled[train_size:])
    type3_test_ids = [query_id for query_id in test_ids if queries[query_id].get("type") == "3"]

    global_train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    type3_train_rows = [
        row
        for query_id in train_ids
        if queries[query_id].get("type") == "3"
        for row in candidates[query_id].values()
    ]
    type3_test_rows = [row for query_id in type3_test_ids for row in candidates[query_id].values()]

    global_scores, global_features = train_predict(global_train_rows, type3_test_rows, methods)
    type3_scores, type3_features = train_predict(type3_train_rows, type3_test_rows, methods)
    for row in global_features:
        row["split_seed"] = seed
        row["model"] = "global_candidate_reranker"
    for row in type3_features:
        row["split_seed"] = seed
        row["model"] = "type3_specific_reranker"

    scored_by_query: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row, global_score, type3_score in zip(type3_test_rows, global_scores, type3_scores):
        global_row = {**row, "learned_score": global_score}
        type3_row = {**row, "learned_score": type3_score}
        scored_by_query[row["query_id"]]["global_candidate_reranker"].append(global_row)
        scored_by_query[row["query_id"]]["type3_specific_reranker"].append(type3_row)

    ranked_by_method: dict[str, dict[str, list[dict[str, Any]]]] = {
        "type_aware": {},
        "global_candidate_reranker": {},
        "type3_specific_reranker": {},
        "candidate_oracle": {},
    }
    ranked_output_rows = []
    for query_id in type3_test_ids:
        query_candidates = candidates[query_id]
        type_aware_ranked = [
            query_candidates[memory_id]
            for memory_id in type_aware_ranked_ids.get(query_id, [])
            if memory_id in query_candidates
        ]
        global_ranked = sorted(scored_by_query[query_id]["global_candidate_reranker"], key=lambda row: row["learned_score"], reverse=True)
        type3_ranked = sorted(scored_by_query[query_id]["type3_specific_reranker"], key=lambda row: row["learned_score"], reverse=True)
        oracle_ranked = sorted(query_candidates.values(), key=lambda row: row["is_relevant"], reverse=True)
        ranked_by_method["type_aware"][query_id] = type_aware_ranked
        ranked_by_method["global_candidate_reranker"][query_id] = global_ranked
        ranked_by_method["type3_specific_reranker"][query_id] = type3_ranked
        ranked_by_method["candidate_oracle"][query_id] = oracle_ranked
        for method, ranked in (
            ("global_candidate_reranker", global_ranked),
            ("type3_specific_reranker", type3_ranked),
        ):
            for rank, row in enumerate(ranked[:max(ks)], start=1):
                ranked_output_rows.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "query_type": "3",
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "learned_score": row["learned_score"],
                    "is_relevant": row["is_relevant"],
                    "memory_text": row["memory_text"],
                })

    per_query_rows = []
    coverage_rows = []
    split_summary_rows = []
    for method, ranked in ranked_by_method.items():
        method_metric_rows, method_coverage_rows = evaluate_method_rows(seed, type3_test_ids, method, ranked, queries, ks)
        per_query_rows.extend(method_metric_rows)
        coverage_rows.extend(method_coverage_rows)
        split_summary_rows.append(aggregate(method_metric_rows, method, seed))

    comparison_rows = []
    for row in per_query_rows:
        comparison_rows.append({
            "query_id": f"{seed}:{row['query_id']}",
            "original_query_id": row["query_id"],
            "split_seed": seed,
            "query_type": row["query_type"],
            "method": row["method"],
            "mrr": row["mrr"],
            "recall@1": row["recall@1"],
            "recall@3": row["recall@3"],
            "recall@5": row["recall@5"],
            "first_rank": row["first_rank"],
        })

    return (
        split_summary_rows,
        per_query_rows,
        comparison_rows,
        coverage_rows,
        global_features + type3_features,
        ranked_output_rows,
    )


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    coverage_summary_rows: list[dict[str, Any]],
    feature_rows: list[dict[str, Any]],
    ks: list[int],
) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    coverage_by_method = {row["method"]: row for row in coverage_summary_rows}
    primary_k = 5 if 5 in ks else max(ks)
    lines = [
        "# Type 3 专用监督重排实验",
        "",
        "本实验只在 LoCoMo Type 3 多证据/推理类问题上评估候选级学习重排。训练时使用相同随机 query-level 划分，避免同一 query 的候选同时进入训练和测试。",
        "",
        "对比方法：",
        "",
        "- `type_aware`：固定公式检索基线。",
        "- `global_candidate_reranker`：使用所有 query type 的训练候选学习，然后只在 Type 3 测试集评估。",
        "- `type3_specific_reranker`：只使用训练集中的 Type 3 候选学习，再在 Type 3 测试集评估。",
        "- `candidate_oracle`：候选池上限，用于判断瓶颈在候选召回还是重排。",
        "",
        "## Type 3 Held-Out 排序指标",
        "",
        "| 方法 | 划分数 | 平均 Query 数 | MRR | Recall@1 | Recall@3 | Recall@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("type_aware", "global_candidate_reranker", "type3_specific_reranker", "candidate_oracle"):
        row = by_method.get(method)
        if not row:
            continue
        lines.append(
            f"| {method} | {row['splits']} | {row['mean_queries']:.1f} | {metric(row['mrr_mean'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@3_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    if "type_aware" in by_method:
        base = by_method["type_aware"]
        lines.extend(["", "## 相比 Type-Aware 的变化", ""])
        for method in ("global_candidate_reranker", "type3_specific_reranker"):
            row = by_method.get(method)
            if row:
                lines.append(
                    f"- `{method}`：MRR `{row['mrr_mean'] - base['mrr_mean']:.4f}`，"
                    f"Recall@5 `{row['recall@5_mean'] - base['recall@5_mean']:.4f}`。"
                )
    lines.extend([
        "",
        f"## Type 3 多证据覆盖 @{primary_k}",
        "",
        "| 方法 | Rows | Mean Gold | Multi-Evidence Share | Any | Full | Coverage Ratio |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for method in ("type_aware", "global_candidate_reranker", "type3_specific_reranker", "candidate_oracle"):
        row = coverage_by_method.get(method)
        if not row:
            continue
        lines.append(
            f"| {method} | {row['num_rows']} | {row['mean_gold']:.2f} | {row['multi_evidence_share']:.3f} | "
            f"{metric(row[f'any_hit@{primary_k}'])} | {metric(row[f'full_coverage@{primary_k}'])} | "
            f"{metric(row[f'coverage_ratio@{primary_k}'])} |"
        )
    if feature_rows:
        lines.extend([
            "",
            "## Type3-Specific Top Feature Importance",
            "",
            "| Feature | Importance Mean | Importance Std |",
            "|---|---:|---:|",
        ])
        shown = 0
        for row in feature_rows:
            if row.get("model") != "type3_specific_reranker":
                continue
            lines.append(f"| {row['feature']} | {row['importance_mean']:.4f} | {row['importance_stdev']:.4f} |")
            shown += 1
            if shown >= 12:
                break
    lines.extend([
        "",
        "## 结论",
        "",
        "- 如果 Type3 专用模型没有超过 global reranker，说明目前 Type3 训练样本规模或特征表达不足，单独建模会过拟合。",
        "- 如果 candidate oracle 明显高于学习器，后续应优先做 query decomposition 或 supervised set selector，而不是继续只优化 Top1 排名。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3-specific reranker experiment.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--ks", default="1,3,5,10,20")
    parser.add_argument("--feature-top-n", type=int, default=30)
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-coverage", type=Path, required=True)
    parser.add_argument("--output-coverage-summary", type=Path, required=True)
    parser.add_argument("--output-feature-importance", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    queries = read_jsonl(args.queries)
    type_aware_ranked_ids = load_type_aware_ranked(args.rankings, max(ks))
    query_ids = sorted(query_id for query_id in candidates if query_id in baseline_rows and query_id in queries)

    split_rows = []
    per_query_rows = []
    comparison_rows = []
    coverage_rows = []
    feature_rows = []
    ranked_rows = []
    for seed in seeds:
        (
            split_summary_rows,
            split_per_query_rows,
            split_comparison_rows,
            split_coverage_rows,
            split_feature_rows,
            split_ranked_rows,
        ) = evaluate_split(
            seed,
            query_ids,
            candidates,
            baseline_rows,
            queries,
            type_aware_ranked_ids,
            methods,
            args.train_fraction,
            ks,
        )
        split_rows.extend(split_summary_rows)
        per_query_rows.extend(split_per_query_rows)
        comparison_rows.extend(split_comparison_rows)
        coverage_rows.extend(split_coverage_rows)
        feature_rows.extend(split_feature_rows)
        ranked_rows.extend(split_ranked_rows)

    summary_rows = summarize_across_splits(split_rows)
    coverage_summary_rows = aggregate_coverage(coverage_rows, ks)
    feature_summary_rows = []
    for model in ("global_candidate_reranker", "type3_specific_reranker"):
        model_features = [{key: value for key, value in row.items() if key != "model"} for row in feature_rows if row.get("model") == model]
        for row in summarize_features(model_features, args.feature_top_n):
            row["model"] = model
            feature_summary_rows.append(row)

    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_per_query, per_query_rows)
    write_csv(args.output_comparison, comparison_rows)
    write_csv(args.output_coverage, coverage_rows)
    write_csv(args.output_coverage_summary, coverage_summary_rows)
    write_csv(args.output_feature_importance, feature_summary_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_report(args.output_report, summary_rows, coverage_summary_rows, feature_summary_rows, ks)
    print(json.dumps({
        "type3_test_rows": len(per_query_rows),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
