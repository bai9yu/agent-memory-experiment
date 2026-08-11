#!/usr/bin/env python3
"""Evaluate a held-out supervised text router for retrieval method selection."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_queries(path: Path) -> dict[str, dict[str, Any]]:
    queries = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                queries[row["id"]] = row
    return queries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def metric(value: float) -> str:
    return f"{value:.3f}"


def best_label_by_query(per_query_rows: list[dict[str, str]], methods: set[str], metric_name: str) -> dict[str, str]:
    by_query: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in per_query_rows:
        if row["method"] in methods:
            by_query[row["query_id"]].append(row)
    labels = {}
    for query_id, rows in by_query.items():
        best = max(rows, key=lambda row: (as_float(row, metric_name), row["method"] == "type_aware"))
        labels[query_id] = best["method"]
    return labels


def rows_by_query_method(per_query_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["query_id"], row["method"]): row
        for row in per_query_rows
    }


def query_ids_with_all_methods(per_query_rows: list[dict[str, str]], methods: set[str]) -> list[str]:
    seen: dict[str, set[str]] = defaultdict(set)
    for row in per_query_rows:
        if row["method"] in methods:
            seen[row["query_id"]].add(row["method"])
    return sorted(query_id for query_id, available in seen.items() if methods.issubset(available))


def aggregate_metric(rows: list[dict[str, Any]], method: str, split_seed: int) -> dict[str, Any]:
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


def select_rows(query_ids: list[str], selected_methods: dict[str, str], row_lookup: dict[tuple[str, str], dict[str, str]], output_method: str, queries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    selected = []
    for query_id in query_ids:
        method = selected_methods[query_id]
        row = row_lookup[(query_id, method)]
        selected.append({
            "query_id": query_id,
            "query_type": row["query_type"],
            "query": queries.get(query_id, {}).get("query", ""),
            "method": output_method,
            "selected_method": method,
            "mrr": as_float(row, "mrr"),
            "recall@1": as_float(row, "recall@1"),
            "recall@3": as_float(row, "recall@3"),
            "recall@5": as_float(row, "recall@5"),
            "first_rank": row.get("first_rank", ""),
        })
    return selected


def train_predict(train_texts: list[str], train_labels: list[str], test_texts: list[str]) -> list[str]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=3000),
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=0),
    )
    model.fit(train_texts, train_labels)
    return list(model.predict(test_texts))


def write_report(path: Path, summary_rows: list[dict[str, Any]], label_counts: dict[str, int], prediction_counts: dict[str, int]) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    learned = by_method.get("supervised_text_router", {})
    baseline = by_method.get("type_aware", {})
    oracle = by_method.get("oracle_best_method", {})
    lines = [
        "# 监督式 Query-Text Router 实验",
        "",
        "本实验使用 held-out split 验证可部署 query-text router：训练集用 per-query metrics 派生的最佳方法作为标签，测试集只根据 query 文本预测 route。",
        "它不使用测试集 query type 标注，也不使用测试答案来选择 route。",
        "",
        "## 训练标签分布",
        "",
        "| 最优方法标签 | 数量 |",
        "|---|---:|",
    ]
    for label, count in sorted(label_counts.items()):
        lines.append(f"| {label} | {count} |")
    lines.extend([
        "",
        "## 预测路由分布",
        "",
        "| 预测方法 | 数量 |",
        "|---|---:|",
    ])
    for label, count in sorted(prediction_counts.items()):
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
    if learned and baseline:
        lines.extend([
            "",
            "## 相比固定 Type-Aware 的变化",
            "",
            f"- MRR 变化：`{learned['mrr_mean'] - baseline['mrr_mean']:.4f}`",
            f"- Recall@1 变化：`{learned['recall@1_mean'] - baseline['recall@1_mean']:.4f}`",
            f"- Recall@5 变化：`{learned['recall@5_mean'] - baseline['recall@5_mean']:.4f}`",
        ])
    if learned and oracle:
        lines.extend([
            "",
            "## 距离 Oracle Best 的差距",
            "",
            f"- Oracle MRR 差距：`{oracle['mrr_mean'] - learned['mrr_mean']:.4f}`",
            f"- Oracle Recall@5 差距：`{oracle['recall@5_mean'] - learned['recall@5_mean']:.4f}`",
        ])
    lines.extend([
        "",
        "## 解释",
        "",
        "- supervised router 是比手写 text-intent rules 更合理的可部署 baseline，因为 route 从 query 文本学习得到。",
        "- 当前 held-out 结果低于 fixed `type_aware`，说明 per-query oracle labels 噪声较大，或者 query text 本身不足以可靠选择检索器。",
        "- 这不是最终路由方案，而是一个负结果基线：后续需要 validation-tuned classifier、LLM few-shot classifier，或将 query intent 作为显式中间变量建模。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run held-out supervised query-text router experiment.")
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--label-metric", default="mrr")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = {item.strip() for item in args.methods.split(",") if item.strip()}
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    per_query_rows = read_csv(args.per_query)
    queries = read_queries(args.queries)
    labels = best_label_by_query(per_query_rows, methods, args.label_metric)
    row_lookup = rows_by_query_method(per_query_rows)
    query_ids = [query_id for query_id in query_ids_with_all_methods(per_query_rows, methods) if query_id in queries and query_id in labels]

    split_rows = []
    selected_rows = []
    prediction_counts: Counter[str] = Counter()
    for seed in seeds:
        rng = random.Random(seed)
        shuffled = list(query_ids)
        rng.shuffle(shuffled)
        train_size = int(len(shuffled) * args.train_fraction)
        train_ids = sorted(shuffled[:train_size])
        test_ids = sorted(shuffled[train_size:])
        train_texts = [queries[query_id]["query"] for query_id in train_ids]
        train_labels = [labels[query_id] for query_id in train_ids]
        test_texts = [queries[query_id]["query"] for query_id in test_ids]
        predictions = train_predict(train_texts, train_labels, test_texts)
        predicted_methods = {query_id: method for query_id, method in zip(test_ids, predictions)}
        prediction_counts.update(predicted_methods.values())

        baseline_methods = {query_id: args.baseline_method for query_id in test_ids}
        oracle_methods = {query_id: labels[query_id] for query_id in test_ids}

        baseline_rows = select_rows(test_ids, baseline_methods, row_lookup, args.baseline_method, queries)
        learned_rows = select_rows(test_ids, predicted_methods, row_lookup, "supervised_text_router", queries)
        oracle_rows = select_rows(test_ids, oracle_methods, row_lookup, "oracle_best_method", queries)
        for rows, method in (
            (baseline_rows, args.baseline_method),
            (learned_rows, "supervised_text_router"),
            (oracle_rows, "oracle_best_method"),
        ):
            split_rows.append(aggregate_metric(rows, method, seed))
        for row in learned_rows:
            selected_rows.append({"split_seed": seed, **row})

    summary_rows = summarize_across_splits(split_rows)
    label_counts = Counter(labels[query_id] for query_id in query_ids)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_selected, selected_rows)
    write_report(args.output_report, summary_rows, dict(label_counts), dict(prediction_counts))


if __name__ == "__main__":
    main()
