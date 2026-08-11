#!/usr/bin/env python3
"""Evaluate a query-type router from existing per-query metrics."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_ROUTE = {
    "1": "vector",
    "2": "type_aware",
    "3": "type_aware",
    "4": "type_aware",
    "5": "keyword",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_route(value: str) -> dict[str, str]:
    route = dict(DEFAULT_ROUTE)
    if not value:
        return route
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        query_type, method = item.split(":", 1)
        route[query_type.strip()] = method.strip()
    return route


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def aggregate(rows: list[dict[str, Any]], method_name: str, group_by_type: bool) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = row["query_type"] if group_by_type else "all"
        buckets[key].append(row)
    result = []
    for key in sorted(buckets):
        bucket = buckets[key]
        out = {
            "method": method_name,
            "num_queries": len(bucket),
            "mrr": sum(row["mrr"] for row in bucket) / len(bucket),
            "recall@1": sum(row["recall@1"] for row in bucket) / len(bucket),
            "recall@3": sum(row["recall@3"] for row in bucket) / len(bucket),
            "recall@5": sum(row["recall@5"] for row in bucket) / len(bucket),
        }
        if group_by_type:
            out["query_type"] = key
        result.append(out)
    return result


def select_router_rows(per_query_rows: list[dict[str, str]], route: dict[str, str], default_method: str) -> list[dict[str, Any]]:
    by_query_method = {
        (row["query_id"], row["method"]): row
        for row in per_query_rows
    }
    query_types = {}
    for row in per_query_rows:
        query_types[row["query_id"]] = row["query_type"]

    selected = []
    for query_id in sorted(query_types):
        query_type = query_types[query_id]
        method = route.get(query_type, default_method)
        row = by_query_method.get((query_id, method))
        if row is None:
            row = by_query_method[(query_id, default_method)]
            method = default_method
        selected.append({
            "query_id": query_id,
            "query_type": query_type,
            "method": "query_type_router",
            "selected_method": method,
            "mrr": as_float(row, "mrr"),
            "recall@1": as_float(row, "recall@1"),
            "recall@3": as_float(row, "recall@3"),
            "recall@5": as_float(row, "recall@5"),
            "first_rank": row.get("first_rank", ""),
        })
    return selected


def fixed_method_rows(per_query_rows: list[dict[str, str]], method: str) -> list[dict[str, Any]]:
    return [
        {
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
        for row in per_query_rows
        if row["method"] == method
    ]


def metric(value: float) -> str:
    return f"{value:.3f}"


def write_report(path: Path, route: dict[str, str], overall_rows: list[dict[str, Any]], by_type_rows: list[dict[str, Any]]) -> None:
    overall_by_method = {row["method"]: row for row in overall_rows}
    router = overall_by_method["query_type_router"]
    baseline = overall_by_method["type_aware"]
    lines = [
        "# Query-Type Router Experiment",
        "",
        "本实验不重新运行检索，而是基于已有 per-query metrics 做离线 routing：不同 LoCoMo query type 选择不同检索方法。",
        "",
        "## Routing Rule",
        "",
        "| Query Type | Selected Method |",
        "|---|---|",
    ]
    for query_type in sorted(route):
        lines.append(f"| Type {query_type} | {route[query_type]} |")
    lines.extend([
        "",
        "## Overall Result",
        "",
        "| Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in overall_rows:
        lines.append(
            f"| {row['method']} | {row['num_queries']} | {metric(row['recall@1'])} | "
            f"{metric(row['recall@3'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## Router Gain Over Fixed Type-Aware",
        "",
        f"- Delta Recall@1: `{router['recall@1'] - baseline['recall@1']:.4f}`",
        f"- Delta Recall@5: `{router['recall@5'] - baseline['recall@5']:.4f}`",
        f"- Delta MRR: `{router['mrr'] - baseline['mrr']:.4f}`",
        "",
        "## By-Type Router Result",
        "",
        "| Query Type | Queries | Selected Method | Recall@1 | Recall@5 | MRR |",
        "|---|---:|---|---:|---:|---:|",
    ])
    method_by_type = route
    for row in by_type_rows:
        lines.append(
            f"| Type {row['query_type']} | {row['num_queries']} | {method_by_type.get(row['query_type'], '')} | "
            f"{metric(row['recall@1'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- 该 router 是 oracle-light 版本：它使用 LoCoMo 已知 query type，不使用测试标签答案，因此适合作为后续 query-intent router 的上界启发。",
        "- 如果 router 超过固定 `type_aware`，说明统一打分公式仍有改进空间。",
        "- 真正可部署版本需要用规则或小模型从 query 文本预测 route，而不能依赖数据集标注的 type。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate query-type routing from per-query metrics.")
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--route", default="")
    parser.add_argument("--default-method", default="type_aware")
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-by-type", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    route = parse_route(args.route)
    per_query_rows = read_csv(args.per_query)
    router_rows = select_router_rows(per_query_rows, route, args.default_method)
    fixed_rows = fixed_method_rows(per_query_rows, args.default_method)

    summary = aggregate(fixed_rows, args.default_method, group_by_type=False) + aggregate(router_rows, "query_type_router", group_by_type=False)
    by_type = aggregate(router_rows, "query_type_router", group_by_type=True)

    write_csv(args.output_selected, router_rows)
    write_csv(args.output_comparison, fixed_rows + router_rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_by_type, by_type)
    write_report(args.output_report, route, summary, by_type)


if __name__ == "__main__":
    main()
