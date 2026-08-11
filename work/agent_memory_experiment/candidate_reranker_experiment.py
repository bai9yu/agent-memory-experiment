#!/usr/bin/env python3
"""Evaluate a held-out candidate-level reranker from cached rankings features."""

from __future__ import annotations

import argparse
import csv
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from query_type_router_experiment import as_float, metric, write_csv


NUMERIC_FEATURES = (
    "semantic_score",
    "keyword_score",
    "entity_score",
    "time_decay",
    "recency_gate",
    "persona_score",
    "persona_weight",
    "importance_score",
    "memory_type_score",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_candidates(rankings_path: Path) -> dict[str, dict[str, dict[str, Any]]]:
    by_query: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    rank_by_method: dict[tuple[str, str], int] = defaultdict(int)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            query_id = row["query_id"]
            memory_id = row["memory_id"]
            method = row["method"]
            rank_by_method[(query_id, method)] += 1
            rank = rank_by_method[(query_id, method)]
            candidate = by_query[query_id].setdefault(
                memory_id,
                {
                    "query_id": query_id,
                    "query": row["query"],
                    "query_type": row["query_type"],
                    "memory_id": memory_id,
                    "memory_text": row["memory_text"],
                    "memory_type": row["memory_type"],
                    "is_relevant": False,
                    "method_scores": {},
                    "method_rr": {},
                },
            )
            for feature in NUMERIC_FEATURES:
                candidate[feature] = as_float(row, feature)
            candidate["is_relevant"] = candidate["is_relevant"] or row["is_relevant"] == "True"
            candidate["method_scores"][method] = as_float(row, "final_score")
            candidate["method_rr"][method] = 1.0 / rank
    return by_query


def load_baseline(per_query_path: Path, method: str) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in read_csv(per_query_path):
        if row["method"] == method:
            rows[row["query_id"]] = {
                "query_id": row["query_id"],
                "query_type": row["query_type"],
                "method": method,
                "selected_method": method,
                "mrr": as_float(row, "mrr"),
                "recall@1": as_float(row, "recall@1"),
                "recall@3": as_float(row, "recall@3"),
                "recall@5": as_float(row, "recall@5"),
                "first_rank": row.get("first_rank", ""),
            }
    return rows


def feature_dict(candidate: dict[str, Any], methods: list[str]) -> dict[str, float]:
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


def train_predict(train_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]], methods: list[str]) -> tuple[list[float], list[dict[str, Any]]]:
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import make_pipeline

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
    x_train = [feature_dict(row, methods) for row in train_rows]
    y_train = [1 if row["is_relevant"] else 0 for row in train_rows]
    x_test = [feature_dict(row, methods) for row in test_rows]
    if len(set(y_train)) < 2:
        return [0.0 for _ in test_rows], []
    model.fit(x_train, y_train)
    vectorizer = model.named_steps["dictvectorizer"]
    classifier = model.named_steps["randomforestclassifier"]
    feature_rows = [
        {"feature": feature, "importance": float(importance)}
        for feature, importance in zip(vectorizer.get_feature_names_out(), classifier.feature_importances_)
    ]
    return [float(value) for value in model.predict_proba(x_test)[:, 1]], feature_rows


def score_ranked_query(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first_rank = 0
    first_memory = ""
    for rank, row in enumerate(rows, start=1):
        if row["is_relevant"]:
            first_rank = rank
            first_memory = row["memory_id"]
            break
    return {
        "mrr": 1.0 / first_rank if first_rank else 0.0,
        "recall@1": 1.0 if first_rank and first_rank <= 1 else 0.0,
        "recall@3": 1.0 if first_rank and first_rank <= 3 else 0.0,
        "recall@5": 1.0 if first_rank and first_rank <= 5 else 0.0,
        "first_rank": first_rank,
        "first_relevant_memory_id": first_memory,
    }


def aggregate(rows: list[dict[str, Any]], method: str, split_seed: int) -> dict[str, Any]:
    return {
        "split_seed": split_seed,
        "method": method,
        "num_queries": len(rows),
        "mrr": statistics.mean(row["mrr"] for row in rows),
        "recall@1": statistics.mean(row["recall@1"] for row in rows),
        "recall@3": statistics.mean(row["recall@3"] for row in rows),
        "recall@5": statistics.mean(row["recall@5"] for row in rows),
    }


def summarize_across_splits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_method[row["method"]].append(row)
    summary = []
    for method in sorted(by_method):
        bucket = by_method[method]
        out = {
            "method": method,
            "splits": len(bucket),
            "mean_queries": statistics.mean(row["num_queries"] for row in bucket),
        }
        for metric_name in ("mrr", "recall@1", "recall@3", "recall@5"):
            values = [row[metric_name] for row in bucket]
            out[f"{metric_name}_mean"] = statistics.mean(values)
            out[f"{metric_name}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
        summary.append(out)
    return summary


def candidate_oracle_rows(query_ids: list[str], candidates: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows = []
    for query_id in query_ids:
        query_candidates = list(candidates[query_id].values())
        ranked = sorted(query_candidates, key=lambda row: row["is_relevant"], reverse=True)
        scored = score_ranked_query(ranked)
        rows.append({
            "query_id": query_id,
            "query_type": query_candidates[0]["query_type"],
            "method": "candidate_oracle",
            "selected_method": "candidate_oracle",
            **scored,
        })
    return rows


def evaluate_split(
    seed: int,
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    baseline_rows: dict[str, dict[str, Any]],
    methods: list[str],
    train_fraction: float,
    rank_output_k: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(query_ids)
    rng.shuffle(shuffled)
    train_size = int(len(shuffled) * train_fraction)
    train_ids = sorted(shuffled[:train_size])
    test_ids = sorted(shuffled[train_size:])

    train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    test_rows = [row for query_id in test_ids for row in candidates[query_id].values()]
    scores, feature_rows = train_predict(train_rows, test_rows, methods)
    for row in feature_rows:
        row["split_seed"] = seed
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
            "split_seed": seed,
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
        pair_query_id = f"{seed}:{query_id}"
        baseline_row = baseline_rows[query_id]
        comparison_rows.append({
            "query_id": pair_query_id,
            "original_query_id": query_id,
            "split_seed": seed,
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
            "split_seed": seed,
            "query_type": selected_row["query_type"],
            "method": "candidate_reranker",
            "mrr": selected_row["mrr"],
            "recall@1": selected_row["recall@1"],
            "recall@3": selected_row["recall@3"],
            "recall@5": selected_row["recall@5"],
            "first_rank": selected_row["first_rank"],
        })
        for rank, row in enumerate(ranked[:rank_output_k], start=1):
            ranked_rows.append({
                "split_seed": seed,
                "query_id": query_id,
                "query_type": row["query_type"],
                "rank": rank,
                "memory_id": row["memory_id"],
                "memory_type": row["memory_type"],
                "memory_text": row["memory_text"],
                "learned_score": row.get("learned_score", 0.0),
                "is_relevant": row["is_relevant"],
            })

    split_metric_rows = []
    baseline_split = [{**baseline_rows[query_id], "split_seed": seed} for query_id in test_ids]
    oracle_split = candidate_oracle_rows(test_ids, candidates)
    split_metric_rows.append(aggregate(baseline_split, "type_aware", seed))
    split_metric_rows.append(aggregate(selected_rows, "candidate_reranker", seed))
    split_metric_rows.append(aggregate(oracle_split, "candidate_oracle", seed))
    return split_metric_rows, selected_rows, comparison_rows, feature_rows, ranked_rows


def summarize_feature_importance(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
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


def write_report(path: Path, summary_rows: list[dict[str, Any]], label_counts: dict[str, int], feature_rows: list[dict[str, Any]]) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    reranker = by_method.get("candidate_reranker", {})
    baseline = by_method.get("type_aware", {})
    oracle = by_method.get("candidate_oracle", {})
    lines = [
        "# 候选级学习重排实验",
        "",
        "本实验使用 `rankings.csv` 中各检索器 Top-K 候选的并集作为候选池，在训练 query 上学习 candidate-level relevance classifier，并在 held-out query 上重排候选记忆。",
        "当前学习器为轻量随机森林分类器。它不重新计算 embedding，也不使用测试 query 的答案来训练；候选池受原始 Top-K 落盘范围限制。",
        "",
        "## 候选标签分布",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label, count in sorted(label_counts.items()):
        lines.append(f"| {label} | {count} |")
    lines.extend([
        "",
        "## Held-Out 多划分结果",
        "",
        "| 方法 | 划分数 | MRR 均值 | MRR 标准差 | Recall@1 均值 | Recall@5 均值 |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['splits']} | {metric(row['mrr_mean'])} | {metric(row['mrr_stdev'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    if reranker and baseline:
        lines.extend([
            "",
            "## 相比固定 Type-Aware 的变化",
            "",
            f"- MRR 变化：`{reranker['mrr_mean'] - baseline['mrr_mean']:.4f}`",
            f"- Recall@1 变化：`{reranker['recall@1_mean'] - baseline['recall@1_mean']:.4f}`",
            f"- Recall@5 变化：`{reranker['recall@5_mean'] - baseline['recall@5_mean']:.4f}`",
        ])
    if reranker and oracle:
        lines.extend([
            "",
            "## 候选池 Oracle 差距",
            "",
            f"- Candidate Oracle MRR 差距：`{oracle['mrr_mean'] - reranker['mrr_mean']:.4f}`",
            f"- Candidate Oracle Recall@5 差距：`{oracle['recall@5_mean'] - reranker['recall@5_mean']:.4f}`",
        ])
    if feature_rows:
        lines.extend([
            "",
            "## Top Feature Importance",
            "",
            "| Feature | Importance Mean | Importance Std |",
            "|---|---:|---:|",
        ])
        for row in feature_rows[:12]:
            lines.append(f"| {row['feature']} | {row['importance_mean']:.4f} | {row['importance_stdev']:.4f} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 该实验检验的是：给定多个检索器已经召回的候选并集，轻量学习器能否学到比固定公式更好的排序。",
        "- 如果低于 fixed `type_aware`，说明当前特征或训练标签不足以支撑学习式重排，固定加权公式仍更稳。",
        "- 如果接近 candidate oracle 但不超过 full baseline，则主要瓶颈在候选召回；如果远低于 candidate oracle，则主要瓶颈在重排学习。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run held-out candidate-level reranker experiment.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-feature-importance", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--rank-output-k", type=int, default=10)
    parser.add_argument("--feature-top-n", type=int, default=40)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    query_ids = sorted(query_id for query_id in candidates if query_id in baseline_rows)
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]

    all_candidates = [row for query_id in query_ids for row in candidates[query_id].values()]
    label_counts = Counter("relevant" if row["is_relevant"] else "non_relevant" for row in all_candidates)
    split_rows = []
    selected_rows = []
    comparison_rows = []
    feature_rows = []
    ranked_rows = []
    for seed in seeds:
        split_metric_rows, split_selected_rows, split_comparison_rows, split_feature_rows, split_ranked_rows = evaluate_split(
            seed,
            query_ids,
            candidates,
            baseline_rows,
            methods,
            args.train_fraction,
            args.rank_output_k,
        )
        split_rows.extend(split_metric_rows)
        selected_rows.extend(split_selected_rows)
        comparison_rows.extend(split_comparison_rows)
        feature_rows.extend(split_feature_rows)
        ranked_rows.extend(split_ranked_rows)

    summary_rows = summarize_across_splits(split_rows)
    feature_summary_rows = summarize_feature_importance(feature_rows, args.feature_top_n)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_comparison, comparison_rows)
    write_csv(args.output_feature_importance, feature_summary_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_report(args.output_report, summary_rows, dict(label_counts), feature_summary_rows)


if __name__ == "__main__":
    main()
