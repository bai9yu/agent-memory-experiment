#!/usr/bin/env python3
"""Run feature-group ablations for the candidate-level reranker."""

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
    NUMERIC_FEATURES,
    aggregate,
    candidate_oracle_rows,
    load_baseline,
    load_candidates,
    score_ranked_query,
    summarize_across_splits,
)
from query_type_router_experiment import metric, write_csv


METHODS = ("keyword", "vector", "hybrid", "time_aware", "type_aware")
VARIANTS = (
    "full",
    "retrieval_rank_only",
    "intrinsic_only",
    "no_time_features",
    "no_type_persona_features",
    "no_keyword_features",
    "no_semantic_features",
    "type_aware_score_only",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def keep_feature(name: str, variant: str) -> bool:
    if variant == "full":
        return True
    if variant == "retrieval_rank_only":
        return name.endswith("_score") or name.endswith("_rr") or name.endswith("_present")
    if variant == "intrinsic_only":
        return not any(name.startswith(f"{method}_") for method in METHODS)
    if variant == "no_time_features":
        banned = ("time_decay", "recency_gate", "recency_x_decay")
        return not (
            name in banned
            or name.startswith("time_aware_")
        )
    if variant == "no_type_persona_features":
        return not (
            name.startswith("query_type=")
            or name.startswith("memory_type=")
            or name in {"persona_score", "persona_weight", "memory_type_score", "persona_x_type"}
            or name.startswith("type_aware_")
        )
    if variant == "no_keyword_features":
        return not (
            name in {"keyword_score", "semantic_x_keyword"}
            or name.startswith("keyword_")
        )
    if variant == "no_semantic_features":
        return not (
            name == "semantic_score"
            or name.startswith("vector_")
            or name == "semantic_x_keyword"
        )
    if variant == "type_aware_score_only":
        return name in {"type_aware_score", "type_aware_rr", "type_aware_present"}
    raise ValueError(f"Unknown variant: {variant}")


def all_features(candidate: dict[str, Any], methods: list[str]) -> dict[str, float]:
    features = {name: float(candidate.get(name, 0.0)) for name in NUMERIC_FEATURES}
    features[f"query_type={candidate['query_type']}"] = 1.0
    features[f"memory_type={candidate['memory_type']}"] = 1.0
    for method in methods:
        features[f"{method}_score"] = float(candidate["method_scores"].get(method, 0.0))
        features[f"{method}_rr"] = float(candidate["method_rr"].get(method, 0.0))
        features[f"{method}_present"] = 1.0 if method in candidate["method_scores"] else 0.0
    features["semantic_x_keyword"] = features["semantic_score"] * features["keyword_score"]
    features["persona_x_type"] = features["persona_score"] * features["memory_type_score"]
    features["recency_x_decay"] = features["recency_gate"] * features["time_decay"]
    return features


def feature_dict(candidate: dict[str, Any], methods: list[str], variant: str) -> dict[str, float]:
    return {key: value for key, value in all_features(candidate, methods).items() if keep_feature(key, variant)}


def train_predict(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    methods: list[str],
    variant: str,
) -> list[float]:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.pipeline import make_pipeline

    x_train = [feature_dict(row, methods, variant) for row in train_rows]
    y_train = [1 if row["is_relevant"] else 0 for row in train_rows]
    x_test = [feature_dict(row, methods, variant) for row in test_rows]
    if len(set(y_train)) < 2:
        return [0.0 for _ in test_rows]
    model = make_pipeline(
        DictVectorizer(sparse=False),
        RandomForestClassifier(
            n_estimators=120,
            min_samples_leaf=4,
            class_weight="balanced_subsample",
            random_state=0,
            n_jobs=1,
        ),
    )
    model.fit(x_train, y_train)
    return [float(value) for value in model.predict_proba(x_test)[:, 1]]


def evaluate_variant(
    seed: int,
    variant: str,
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    methods: list[str],
    train_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(query_ids)
    rng.shuffle(shuffled)
    train_size = int(len(shuffled) * train_fraction)
    train_ids = sorted(shuffled[:train_size])
    test_ids = sorted(shuffled[train_size:])

    train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    test_rows = [row for query_id in test_ids for row in candidates[query_id].values()]
    scores = train_predict(train_rows, test_rows, methods, variant)
    for row, score in zip(test_rows, scores):
        row[f"{variant}_score"] = score

    selected_rows = []
    comparison_rows = []
    method_name = f"ablation_{variant}"
    for query_id in test_ids:
        ranked = sorted(candidates[query_id].values(), key=lambda row: row.get(f"{variant}_score", 0.0), reverse=True)
        scored = score_ranked_query(ranked)
        top = ranked[0] if ranked else {}
        selected = {
            "split_seed": seed,
            "query_id": query_id,
            "query_type": top.get("query_type", ""),
            "method": method_name,
            "selected_method": method_name,
            "top_memory_id": top.get("memory_id", ""),
            "top_memory_type": top.get("memory_type", ""),
            **scored,
        }
        selected_rows.append(selected)
        pair_query_id = f"{seed}:{query_id}"
        comparison_rows.append({
            "query_id": pair_query_id,
            "original_query_id": query_id,
            "split_seed": seed,
            "query_type": selected["query_type"],
            "method": method_name,
            "mrr": selected["mrr"],
            "recall@1": selected["recall@1"],
            "recall@3": selected["recall@3"],
            "recall@5": selected["recall@5"],
            "first_rank": selected["first_rank"],
        })
    return [aggregate(selected_rows, method_name, seed)], comparison_rows


def add_reference_rows(
    seed: int,
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    train_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(query_ids)
    rng.shuffle(shuffled)
    train_size = int(len(shuffled) * train_fraction)
    test_ids = sorted(shuffled[train_size:])
    baseline_split = [{**baseline_rows[query_id], "split_seed": seed} for query_id in test_ids]
    oracle_split = candidate_oracle_rows(test_ids, candidates)
    metric_rows = [
        aggregate(baseline_split, "type_aware", seed),
        aggregate(oracle_split, "candidate_oracle", seed),
    ]
    comparison_rows = []
    for query_id in test_ids:
        pair_query_id = f"{seed}:{query_id}"
        base = baseline_rows[query_id]
        comparison_rows.append({
            "query_id": pair_query_id,
            "original_query_id": query_id,
            "split_seed": seed,
            "query_type": base["query_type"],
            "method": "type_aware",
            "mrr": base["mrr"],
            "recall@1": base["recall@1"],
            "recall@3": base["recall@3"],
            "recall@5": base["recall@5"],
            "first_rank": base["first_rank"],
        })
    return metric_rows, comparison_rows


def delta_rows(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary_rows}
    full = by_method["ablation_full"]
    baseline = by_method["type_aware"]
    out = []
    for row in summary_rows:
        if row["method"] in {"candidate_oracle"}:
            continue
        out.append({
            "method": row["method"],
            "mrr_mean": row["mrr_mean"],
            "recall@5_mean": row["recall@5_mean"],
            "mrr_delta_vs_type_aware": row["mrr_mean"] - baseline["mrr_mean"],
            "recall@5_delta_vs_type_aware": row["recall@5_mean"] - baseline["recall@5_mean"],
            "mrr_delta_vs_full_reranker": row["mrr_mean"] - full["mrr_mean"],
            "recall@5_delta_vs_full_reranker": row["recall@5_mean"] - full["recall@5_mean"],
        })
    out.sort(key=lambda row: row["mrr_mean"], reverse=True)
    return out


def write_report(path: Path, summary_rows: list[dict[str, Any]], deltas: list[dict[str, Any]], variants: list[str]) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    full = by_method["ablation_full"]
    baseline = by_method["type_aware"]
    oracle = by_method["candidate_oracle"]
    lines = [
        "# Candidate Reranker 特征组消融",
        "",
        "本实验复用已落盘的 `rankings.csv` 候选池，不重新计算 embedding。它检查 candidate-level reranker 的提升是否依赖某一类特征，或是否来自多检索器候选信号融合。",
        "",
        "## 消融设置",
        "",
        "| Variant | Meaning |",
        "|---|---|",
        "| `full` | 原始 candidate reranker 全特征。 |",
        "| `retrieval_rank_only` | 只保留各检索器的 score/rank/present 特征。 |",
        "| `intrinsic_only` | 去掉各检索器 method-level 特征，只保留 candidate 自身分数、query type、memory type 和交互项。 |",
        "| `no_time_features` | 去掉 time decay / recency / time-aware method 特征。 |",
        "| `no_type_persona_features` | 去掉 query type、memory type、persona 和 type-aware method 特征。 |",
        "| `no_keyword_features` | 去掉 keyword score、keyword method 和 semantic-keyword 交互。 |",
        "| `no_semantic_features` | 去掉 semantic score、vector method 和 semantic-keyword 交互。 |",
        "| `type_aware_score_only` | 只保留 fixed type-aware score/rank/present。 |",
        "",
        "## 多划分结果",
        "",
        "| Method | Splits | MRR | Recall@1 | Recall@3 | Recall@5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['splits']} | {metric(row['mrr_mean'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@3_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    lines.extend([
        "",
        "## 相对变化",
        "",
        "| Method | MRR | ΔMRR vs Type-Aware | ΔMRR vs Full | R@5 | ΔR@5 vs Type-Aware | ΔR@5 vs Full |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in deltas:
        lines.append(
            f"| {row['method']} | {metric(row['mrr_mean'])} | {row['mrr_delta_vs_type_aware']:.4f} | "
            f"{row['mrr_delta_vs_full_reranker']:.4f} | {metric(row['recall@5_mean'])} | "
            f"{row['recall@5_delta_vs_type_aware']:.4f} | {row['recall@5_delta_vs_full_reranker']:.4f} |"
        )
    lines.extend([
        "",
        "## 主要结论",
        "",
        f"- Full reranker 相比 fixed `type_aware` 的 MRR 提升为 `{full['mrr_mean'] - baseline['mrr_mean']:.4f}`，Recall@5 提升为 `{full['recall@5_mean'] - baseline['recall@5_mean']:.4f}`。",
        f"- Candidate oracle 相比 full reranker 仍有 MRR `{oracle['mrr_mean'] - full['mrr_mean']:.4f}` 的空间，说明候选池内仍存在未充分利用的相关证据。",
        "- 如果某个去除特征组后的结果接近 full，说明该特征组不是主要增益来源；如果明显下降，说明该特征组对学习重排必要。",
        "- 本实验与主 reranker 共享同一 train/test seed 和候选池，因此适合作为论文中的 ablation table。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run candidate reranker feature-group ablations.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--variants", default=",".join(VARIANTS))
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    variants = [item.strip() for item in args.variants.split(",") if item.strip()]
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    query_ids = sorted(query_id for query_id in candidates if query_id in baseline_rows)

    split_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    for seed in seeds:
        reference_metrics, reference_comparison = add_reference_rows(seed, query_ids, candidates, baseline_rows, args.train_fraction)
        split_rows.extend(reference_metrics)
        comparison_rows.extend(reference_comparison)
        for variant in variants:
            metric_rows, variant_comparison = evaluate_variant(
                seed,
                variant,
                query_ids,
                candidates,
                baseline_rows,
                methods,
                args.train_fraction,
            )
            split_rows.extend(metric_rows)
            comparison_rows.extend(variant_comparison)

    summary_rows = summarize_across_splits(split_rows)
    summary_rows.sort(key=lambda row: row["mrr_mean"], reverse=True)
    deltas = delta_rows(summary_rows)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_deltas, deltas)
    write_csv(args.output_comparison, comparison_rows)
    write_report(args.output_report, summary_rows, deltas, variants)
    print(json.dumps({
        "output_report": str(args.output_report),
        "methods": len(summary_rows),
        "variants": variants,
        "splits": len(seeds),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
