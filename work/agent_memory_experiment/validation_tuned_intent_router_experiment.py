#!/usr/bin/env python3
"""Evaluate a validation-tuned text-intent router for retrieval method selection."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from query_type_router_experiment import as_float, metric, write_csv
from text_intent_router_experiment import predict_method


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


def rows_by_query_method(per_query_rows: list[dict[str, str]], methods: set[str]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["query_id"], row["method"]): row
        for row in per_query_rows
        if row["method"] in methods
    }


def query_ids_with_all_methods(per_query_rows: list[dict[str, str]], methods: set[str]) -> list[str]:
    seen: dict[str, set[str]] = defaultdict(set)
    for row in per_query_rows:
        if row["method"] in methods:
            seen[row["query_id"]].add(row["method"])
    return sorted(query_id for query_id, available in seen.items() if methods.issubset(available))


def query_intents(query_ids: list[str], queries: dict[str, dict[str, Any]]) -> dict[str, str]:
    intents = {}
    for query_id in query_ids:
        _, intent = predict_method(str(queries.get(query_id, {}).get("query", "")))
        intents[query_id] = intent
    return intents


def tune_route(
    train_ids: list[str],
    intents: dict[str, str],
    row_lookup: dict[tuple[str, str], dict[str, str]],
    methods: set[str],
    metric_name: str,
    default_method: str,
) -> dict[str, str]:
    by_intent: dict[str, list[str]] = defaultdict(list)
    for query_id in train_ids:
        by_intent[intents[query_id]].append(query_id)

    route = {}
    for intent, ids in by_intent.items():
        method_scores = []
        for method in sorted(methods):
            values = [as_float(row_lookup[(query_id, method)], metric_name) for query_id in ids]
            method_scores.append((statistics.mean(values), method))
        best_score, best_method = max(method_scores)
        if best_score <= 0 and default_method in methods:
            best_method = default_method
        route[intent] = best_method
    return route


def select_rows(
    query_ids: list[str],
    route: dict[str, str],
    intents: dict[str, str],
    row_lookup: dict[tuple[str, str], dict[str, str]],
    output_method: str,
    queries: dict[str, dict[str, Any]],
    default_method: str,
) -> list[dict[str, Any]]:
    selected = []
    for query_id in query_ids:
        intent = intents[query_id]
        selected_method = route.get(intent, default_method)
        row = row_lookup[(query_id, selected_method)]
        selected.append({
            "query_id": query_id,
            "query_type": row["query_type"],
            "query": queries.get(query_id, {}).get("query", ""),
            "method": output_method,
            "selected_method": selected_method,
            "predicted_intent": intent,
            "mrr": as_float(row, "mrr"),
            "recall@1": as_float(row, "recall@1"),
            "recall@3": as_float(row, "recall@3"),
            "recall@5": as_float(row, "recall@5"),
            "first_rank": row.get("first_rank", ""),
        })
    return selected


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


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
    route_counts: dict[tuple[str, str], int],
) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    tuned = by_method.get("validation_tuned_intent_router", {})
    baseline = by_method.get("type_aware", {})
    oracle = by_method.get("oracle_best_method", {})
    lines = [
        "# 验证集调参 Text-Intent Router 实验",
        "",
        "本实验保留 text-intent router 的 query 文本规则，只在训练集上为每个 predicted intent 自动选择平均 MRR 最好的检索方法。",
        "测试集仅使用 query 文本得到 intent，再套用训练集学到的 intent-to-method route；不使用测试集 query type 或答案选择 route。",
        "",
        "## Held-Out 多划分结果",
        "",
        "| 方法 | 划分数 | MRR 均值 | MRR 标准差 | Recall@1 均值 | Recall@5 均值 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['method']} | {row['splits']} | {metric(row['mrr_mean'])} | {metric(row['mrr_stdev'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    if tuned and baseline:
        lines.extend([
            "",
            "## 相比固定 Type-Aware 的变化",
            "",
            f"- MRR 变化：`{tuned['mrr_mean'] - baseline['mrr_mean']:.4f}`",
            f"- Recall@1 变化：`{tuned['recall@1_mean'] - baseline['recall@1_mean']:.4f}`",
            f"- Recall@5 变化：`{tuned['recall@5_mean'] - baseline['recall@5_mean']:.4f}`",
        ])
    if tuned and oracle:
        lines.extend([
            "",
            "## 距离 Oracle Best 的差距",
            "",
            f"- Oracle MRR 差距：`{oracle['mrr_mean'] - tuned['mrr_mean']:.4f}`",
            f"- Oracle Recall@5 差距：`{oracle['recall@5_mean'] - tuned['recall@5_mean']:.4f}`",
        ])
    lines.extend([
        "",
        "## 学到的 Route 分布",
        "",
        "| Predicted Intent | Selected Method | Splits |",
        "|---|---|---:|",
    ])
    for (intent, method), count in sorted(route_counts.items()):
        lines.append(f"| {intent} | {method} | {count} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 该实验比固定手写 route 更稳健，因为 intent 到检索器的映射来自训练集表现。",
        "- 如果它仍低于 fixed `type_aware`，说明当前 intent 颗粒度不足，无法稳定区分检索策略。",
        "- 如果它接近或超过 fixed `type_aware`，可以继续把 intent detector 从规则替换为 LLM 或小模型分类器。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run held-out validation-tuned text-intent router experiment.")
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
    parser.add_argument("--output-routes", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = {item.strip() for item in args.methods.split(",") if item.strip()}
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    per_query_rows = read_csv(args.per_query)
    queries = read_queries(args.queries)
    query_ids = [query_id for query_id in query_ids_with_all_methods(per_query_rows, methods) if query_id in queries]
    row_lookup = rows_by_query_method(per_query_rows, methods)
    labels = best_label_by_query(per_query_rows, methods, args.label_metric)
    intents = query_intents(query_ids, queries)

    split_rows = []
    selected_rows = []
    route_rows = []
    route_counts: Counter[tuple[str, str]] = Counter()
    for seed in seeds:
        rng = random.Random(seed)
        shuffled = list(query_ids)
        rng.shuffle(shuffled)
        train_size = int(len(shuffled) * args.train_fraction)
        train_ids = sorted(shuffled[:train_size])
        test_ids = sorted(shuffled[train_size:])
        route = tune_route(train_ids, intents, row_lookup, methods, args.label_metric, args.baseline_method)
        route_counts.update((intent, method) for intent, method in route.items())
        for intent, method in sorted(route.items()):
            route_rows.append({"split_seed": seed, "predicted_intent": intent, "selected_method": method})

        baseline_route = {intent: args.baseline_method for intent in set(intents.values())}
        oracle_route = {query_id: labels[query_id] for query_id in test_ids}

        baseline_rows = select_rows(test_ids, baseline_route, intents, row_lookup, args.baseline_method, queries, args.baseline_method)
        tuned_rows = select_rows(test_ids, route, intents, row_lookup, "validation_tuned_intent_router", queries, args.baseline_method)
        oracle_rows = select_rows(test_ids, oracle_route, {query_id: query_id for query_id in test_ids}, row_lookup, "oracle_best_method", queries, args.baseline_method)
        for rows, method in (
            (baseline_rows, args.baseline_method),
            (tuned_rows, "validation_tuned_intent_router"),
            (oracle_rows, "oracle_best_method"),
        ):
            split_rows.append(aggregate_metric(rows, method, seed))
        for row in tuned_rows:
            selected_rows.append({"split_seed": seed, **row})

    summary_rows = summarize_across_splits(split_rows)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_routes, route_rows)
    write_report(args.output_report, summary_rows, route_rows, dict(route_counts))


if __name__ == "__main__":
    main()
