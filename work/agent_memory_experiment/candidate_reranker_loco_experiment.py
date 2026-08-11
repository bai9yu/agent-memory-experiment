#!/usr/bin/env python3
"""Evaluate candidate reranking with leave-one-conversation-out splits."""

from __future__ import annotations

import argparse
import csv
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
    train_predict,
)
from query_type_router_experiment import metric, write_csv


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_query_group_map(locomo_path: Path) -> dict[str, dict[str, str]]:
    records = read_json(locomo_path)
    mapping: dict[str, dict[str, str]] = {}
    counter = 1
    for record_idx, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id", f"record_{record_idx}"))
        for qa in record.get("qa", []):
            if not isinstance(qa, dict) or not str(qa.get("question", "")).strip():
                continue
            query_id = f"q{counter:05d}"
            mapping[query_id] = {
                "conversation_id": f"record_{record_idx:02d}",
                "sample_id": sample_id,
            }
            counter += 1
    return mapping


def evaluate_group(
    group_id: str,
    test_ids: list[str],
    train_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    methods: list[str],
    rank_output_k: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    test_rows = [row for query_id in test_ids for row in candidates[query_id].values()]
    scores, feature_rows = train_predict(train_rows, test_rows, methods)
    for row in feature_rows:
        row["split_id"] = group_id
    for row, score in zip(test_rows, scores):
        row["learned_score"] = score

    selected_rows = []
    comparison_rows = []
    ranked_rows = []
    for query_id in test_ids:
        ranked = sorted(candidates[query_id].values(), key=lambda row: row.get("learned_score", 0.0), reverse=True)
        scored = score_ranked_query(ranked)
        top = ranked[0] if ranked else {}
        selected_row = {
            "split_id": group_id,
            "query_id": query_id,
            "query_type": top.get("query_type", ""),
            "query": top.get("query", ""),
            "method": "candidate_reranker",
            "selected_method": "candidate_reranker",
            "top_memory_id": top.get("memory_id", ""),
            "top_memory_type": top.get("memory_type", ""),
            "top_score": top.get("learned_score", 0.0),
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
            "method": "candidate_reranker_loco",
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
                "rank": rank,
                "memory_id": row["memory_id"],
                "is_relevant": row["is_relevant"],
                "learned_score": row.get("learned_score", 0.0),
                "memory_type": row["memory_type"],
                "memory_text": row["memory_text"],
            })

    baseline_split = [{**baseline_rows[query_id], "split_seed": group_id} for query_id in test_ids]
    oracle_split = candidate_oracle_rows(test_ids, candidates)
    for row in oracle_split:
        row["split_seed"] = group_id
    split_rows = [
        aggregate(baseline_split, "type_aware", group_id),
        aggregate(selected_rows, "candidate_reranker_loco", group_id),
        aggregate(oracle_split, "candidate_oracle", group_id),
    ]
    return split_rows, selected_rows, comparison_rows, feature_rows, ranked_rows


def delta_rows(summary_rows: list[dict[str, Any]], baseline: str, candidate: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary_rows}
    base = by_method[baseline]
    cand = by_method[candidate]
    rows = []
    for metric_name in ("mrr", "recall@1", "recall@3", "recall@5"):
        rows.append({
            "metric": metric_name,
            "baseline_mean": base[f"{metric_name}_mean"],
            "candidate_mean": cand[f"{metric_name}_mean"],
            "delta": cand[f"{metric_name}_mean"] - base[f"{metric_name}_mean"],
        })
    return rows


def write_report(path: Path, summary_rows: list[dict[str, Any]], split_rows: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    cand = by_method["candidate_reranker_loco"]
    base = by_method["type_aware"]
    lines = [
        "# Candidate Reranker Leave-One-Conversation-Out 验证",
        "",
        "本实验把 LoCoMo10 的每个 conversation 轮流作为测试集，其余 conversation 作为训练集。它比随机 query-level split 更严格，用于检查 candidate-level reranker 是否跨 conversation 保持收益。",
        "",
        "## 总览",
        "",
        f"- Splits: {int(cand['splits'])}",
        f"- Type-aware MRR: {metric(base['mrr_mean'])}",
        f"- LOCO candidate reranker MRR: {metric(cand['mrr_mean'])}",
        f"- MRR delta: {metric(cand['mrr_mean'] - base['mrr_mean'])}",
        f"- Recall@5 delta: {metric(cand['recall@5_mean'] - base['recall@5_mean'])}",
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
        "| Metric | Baseline | LOCO Reranker | Delta |",
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
        "- 如果 LOCO reranker 仍显著高于 type-aware，可把它写成跨 conversation 的泛化证据。",
        "- 如果提升变小，应如实说明 candidate-level reranker 在更严格 split 下仍有收益，但泛化幅度弱于随机 query split。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run leave-one-conversation-out candidate reranker experiment.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--locomo", type=Path, required=True)
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--rank-output-k", type=int, default=10)
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-feature-importance", type=Path, required=True)
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
    feature_rows = []
    ranked_rows = []
    for group_id in sorted(groups):
        test_ids = sorted(groups[group_id])
        train_ids = sorted(query_id for query_id in query_ids if query_id not in set(test_ids))
        group_split, group_selected, group_comparison, group_feature, group_ranked = evaluate_group(
            group_id,
            test_ids,
            train_ids,
            candidates,
            baseline_rows,
            methods,
            args.rank_output_k,
        )
        split_rows.extend(group_split)
        selected_rows.extend(group_selected)
        comparison_rows.extend(group_comparison)
        feature_rows.extend(group_feature)
        ranked_rows.extend(group_ranked)

    summary_rows = summarize_across_splits(split_rows)
    deltas = delta_rows(summary_rows, "type_aware", "candidate_reranker_loco")
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_deltas, deltas)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_comparison, comparison_rows)
    write_csv(args.output_feature_importance, feature_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_report(args.output_report, summary_rows, split_rows, deltas)
    print(json.dumps({
        "output_report": str(args.output_report),
        "splits": len(groups),
        "queries": len(query_ids),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
