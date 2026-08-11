#!/usr/bin/env python3
"""Evaluate intrinsic-only candidate reranking with leave-one-conversation-out splits."""

from __future__ import annotations

import argparse
import json
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
)
from candidate_reranker_feature_ablation import train_predict
from candidate_reranker_loco_experiment import build_query_group_map, read_jsonl
from query_type_router_experiment import metric, write_csv


def evaluate_group(
    group_id: str,
    test_ids: list[str],
    train_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    methods: list[str],
    variant: str,
    rank_output_k: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    test_rows = [row for query_id in test_ids for row in candidates[query_id].values()]
    scores = train_predict(train_rows, test_rows, methods, variant)
    for row, score in zip(test_rows, scores):
        row["intrinsic_loco_score"] = score

    selected_rows = []
    comparison_rows = []
    ranked_rows = []
    for query_id in test_ids:
        ranked = sorted(candidates[query_id].values(), key=lambda row: row.get("intrinsic_loco_score", 0.0), reverse=True)
        scored = score_ranked_query(ranked)
        top = ranked[0] if ranked else {}
        selected_row = {
            "split_id": group_id,
            "query_id": query_id,
            "query_type": top.get("query_type", ""),
            "query": top.get("query", ""),
            "method": "intrinsic_reranker_loco",
            "selected_method": "intrinsic_reranker_loco",
            "top_memory_id": top.get("memory_id", ""),
            "top_memory_type": top.get("memory_type", ""),
            "top_score": top.get("intrinsic_loco_score", 0.0),
            **scored,
        }
        selected_rows.append(selected_row)
        pair_query_id = f"{group_id}:{query_id}"
        baseline_row = baseline_rows[query_id]
        comparison_rows.append({
            "query_id": pair_query_id,
            "original_query_id": query_id,
            "split_id": group_id,
            "split_seed": group_id,
            "query_type": baseline_row["query_type"],
            "method": "type_aware",
            "mrr": baseline_row["mrr"],
            "recall@1": baseline_row["recall@1"],
            "recall@3": baseline_row["recall@3"],
            "recall@5": baseline_row["recall@5"],
            "first_rank": baseline_row["first_rank"],
        })
        comparison_rows.append({
            "query_id": pair_query_id,
            "original_query_id": query_id,
            "split_id": group_id,
            "split_seed": group_id,
            "query_type": selected_row["query_type"],
            "method": "intrinsic_reranker_loco",
            "mrr": selected_row["mrr"],
            "recall@1": selected_row["recall@1"],
            "recall@3": selected_row["recall@3"],
            "recall@5": selected_row["recall@5"],
            "first_rank": selected_row["first_rank"],
        })
        for rank, row in enumerate(ranked[:rank_output_k], start=1):
            ranked_rows.append({
                "split_id": group_id,
                "query_id": query_id,
                "query_type": row["query_type"],
                "rank": rank,
                "memory_id": row["memory_id"],
                "is_relevant": row["is_relevant"],
                "intrinsic_loco_score": row.get("intrinsic_loco_score", 0.0),
                "memory_type": row["memory_type"],
                "memory_text": row["memory_text"],
            })

    baseline_split = [{**baseline_rows[query_id], "split_seed": group_id} for query_id in test_ids]
    oracle_split = candidate_oracle_rows(test_ids, candidates)
    for row in oracle_split:
        row["split_seed"] = group_id
    split_rows = [
        aggregate(baseline_split, "type_aware", group_id),
        aggregate(selected_rows, "intrinsic_reranker_loco", group_id),
        aggregate(oracle_split, "candidate_oracle", group_id),
    ]
    return split_rows, selected_rows, comparison_rows, ranked_rows


def delta_rows(summary_rows: list[dict[str, Any]], baseline: str, candidate: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary_rows}
    base = by_method[baseline]
    cand = by_method[candidate]
    return [
        {
            "metric": metric_name,
            "baseline_mean": base[f"{metric_name}_mean"],
            "candidate_mean": cand[f"{metric_name}_mean"],
            "delta": cand[f"{metric_name}_mean"] - base[f"{metric_name}_mean"],
        }
        for metric_name in ("mrr", "recall@1", "recall@3", "recall@5")
    ]


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    split_rows: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    variant: str,
) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    cand = by_method["intrinsic_reranker_loco"]
    base = by_method["type_aware"]
    oracle = by_method["candidate_oracle"]
    lines = [
        "# Intrinsic Candidate Reranker LOCO 验证",
        "",
        "本实验把 LoCoMo10 的每个 conversation 轮流作为测试集，其余 conversation 作为训练集。与 full LOCO reranker 不同，本实验只使用 feature ablation 中表现最好的 intrinsic-only 特征组，检验该简化主方法是否跨 conversation 保持收益。",
        "",
        "## 总览",
        "",
        f"- Feature variant: `{variant}`",
        f"- Splits: {int(cand['splits'])}",
        f"- Type-aware MRR: {metric(base['mrr_mean'])}",
        f"- Intrinsic LOCO MRR: {metric(cand['mrr_mean'])}",
        f"- MRR delta: {metric(cand['mrr_mean'] - base['mrr_mean'])}",
        f"- Recall@5 delta: {metric(cand['recall@5_mean'] - base['recall@5_mean'])}",
        f"- Candidate oracle MRR gap: {metric(oracle['mrr_mean'] - cand['mrr_mean'])}",
        "",
        "## 方法汇总",
        "",
        "| Method | Splits | Mean Queries | MRR | MRR Stdev | R@1 | R@3 | R@5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {int(row['splits'])} | {metric(row['mean_queries'])} | "
            f"{metric(row['mrr_mean'])} | {metric(row['mrr_stdev'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@3_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    lines.extend([
        "",
        "## Delta",
        "",
        "| Metric | Baseline | Intrinsic LOCO | Delta |",
        "|---|---:|---:|---:|",
    ])
    for row in deltas:
        lines.append(f"| {row['metric']} | {metric(row['baseline_mean'])} | {metric(row['candidate_mean'])} | {metric(row['delta'])} |")
    lines.extend([
        "",
        "## Split 明细",
        "",
        "| Split | Method | Queries | MRR | R@1 | R@3 | R@5 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in split_rows:
        lines.append(
            f"| {row['split_seed']} | {row['method']} | {int(row['num_queries'])} | "
            f"{metric(row['mrr'])} | {metric(row['recall@1'])} | {metric(row['recall@3'])} | {metric(row['recall@5'])} |"
        )
    lines.extend([
        "",
        "## 论文使用判断",
        "",
        "- 如果 intrinsic LOCO 仍稳定高于 type-aware，可以把 intrinsic feature reranker 写成随机 held-out 与 LOCO 均支持的主方法。",
        "- 如果 intrinsic LOCO 弱于 full LOCO，应写为：intrinsic-only 是 held-out 最强简化版本，full feature reranker 是当前更稳的跨 conversation 版本。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run intrinsic-only LOCO candidate reranker experiment.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--locomo", type=Path, required=True)
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--variant", default="intrinsic_only")
    parser.add_argument("--rank-output-k", type=int, default=20)
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    query_group_map = build_query_group_map(args.locomo)
    answerable_query_ids = [row["id"] for row in read_jsonl(args.queries)]
    query_ids = sorted(query_id for query_id in answerable_query_ids if query_id in candidates and query_id in baseline_rows)
    groups: dict[str, list[str]] = defaultdict(list)
    for query_id in query_ids:
        groups[query_group_map[query_id]["conversation_id"]].append(query_id)

    split_rows = []
    selected_rows = []
    comparison_rows = []
    ranked_rows = []
    for group_id in sorted(groups):
        test_ids = sorted(groups[group_id])
        test_set = set(test_ids)
        train_ids = sorted(query_id for query_id in query_ids if query_id not in test_set)
        group_split, group_selected, group_comparison, group_ranked = evaluate_group(
            group_id,
            test_ids,
            train_ids,
            candidates,
            baseline_rows,
            methods,
            args.variant,
            args.rank_output_k,
        )
        split_rows.extend(group_split)
        selected_rows.extend(group_selected)
        comparison_rows.extend(group_comparison)
        ranked_rows.extend(group_ranked)

    summary_rows = summarize_across_splits(split_rows)
    summary_rows.sort(key=lambda row: row["mrr_mean"], reverse=True)
    deltas = delta_rows(summary_rows, "type_aware", "intrinsic_reranker_loco")
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_deltas, deltas)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_comparison, comparison_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_report(args.output_report, summary_rows, split_rows, deltas, args.variant)
    print(json.dumps({
        "output_report": str(args.output_report),
        "splits": len(groups),
        "queries": len(query_ids),
        "variant": args.variant,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
