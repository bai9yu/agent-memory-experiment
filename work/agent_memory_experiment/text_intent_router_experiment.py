#!/usr/bin/env python3
"""Evaluate a deployable text-intent router from existing per-query metrics."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from query_type_router_experiment import aggregate, as_float, fixed_method_rows, metric, write_csv


TEMPORAL_RE = re.compile(r"\b(when|how long|what year|which year|date|time)\b", re.IGNORECASE)
KEYWORD_HEAVY_RE = re.compile(
    r"\b(what kind|what kinds|which kind|which kinds|what type|which type|what .* issue|what .* device|"
    r"what .* car|what .* recipe|what .* recipes|what .* project|what .* projects)\b",
    re.IGNORECASE,
)
IDENTITY_PROFILE_RE = re.compile(
    r"\b(identity|relationship status|who is|who was|where did|where has|move from|activities|activity|"
    r"career path|fields|pursue|planning|plan|like|likes|favorite|prefer)\b",
    re.IGNORECASE,
)
CAUSAL_COUNTERFACTUAL_RE = re.compile(
    r"\b(why|how does|how did|would .* if|if .* had|because|challenge|support|motivated|value of)\b",
    re.IGNORECASE,
)


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


def predict_method(query_text: str) -> tuple[str, str]:
    text = query_text.strip()
    if KEYWORD_HEAVY_RE.search(text):
        return "keyword", "keyword_heavy"
    if TEMPORAL_RE.search(text):
        return "type_aware", "temporal_type_aware"
    if CAUSAL_COUNTERFACTUAL_RE.search(text):
        return "type_aware", "causal_type_aware"
    if IDENTITY_PROFILE_RE.search(text):
        return "vector", "identity_profile_vector"
    return "type_aware", "default_type_aware"


def select_router_rows(per_query_rows: list[dict[str, str]], queries: dict[str, dict[str, Any]], default_method: str) -> list[dict[str, Any]]:
    by_query_method = {
        (row["query_id"], row["method"]): row
        for row in per_query_rows
    }
    query_types = {}
    for row in per_query_rows:
        query_types[row["query_id"]] = row["query_type"]

    selected = []
    for query_id in sorted(query_types):
        query = queries.get(query_id, {})
        method, intent = predict_method(str(query.get("query", "")))
        row = by_query_method.get((query_id, method))
        if row is None:
            method = default_method
            intent = "fallback_default"
            row = by_query_method[(query_id, default_method)]
        selected.append({
            "query_id": query_id,
            "query_type": query_types[query_id],
            "query": query.get("query", ""),
            "method": "text_intent_router",
            "selected_method": method,
            "predicted_intent": intent,
            "mrr": as_float(row, "mrr"),
            "recall@1": as_float(row, "recall@1"),
            "recall@3": as_float(row, "recall@3"),
            "recall@5": as_float(row, "recall@5"),
            "first_rank": row.get("first_rank", ""),
        })
    return selected


def route_distribution(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((row["selected_method"], row["predicted_intent"]) for row in rows)
    total = len(rows)
    return [
        {
            "selected_method": method,
            "predicted_intent": intent,
            "num_queries": count,
            "share": count / total if total else 0.0,
        }
        for (method, intent), count in sorted(counts.items())
    ]


def aggregate_by_intent(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["predicted_intent"]].append(row)
    result = []
    for intent in sorted(buckets):
        bucket = buckets[intent]
        result.append({
            "predicted_intent": intent,
            "selected_method": bucket[0]["selected_method"],
            "num_queries": len(bucket),
            "mrr": sum(row["mrr"] for row in bucket) / len(bucket),
            "recall@1": sum(row["recall@1"] for row in bucket) / len(bucket),
            "recall@3": sum(row["recall@3"] for row in bucket) / len(bucket),
            "recall@5": sum(row["recall@5"] for row in bucket) / len(bucket),
        })
    return result


def write_report(path: Path, summary_rows: list[dict[str, Any]], by_intent_rows: list[dict[str, Any]], distribution_rows: list[dict[str, Any]]) -> None:
    overall = {row["method"]: row for row in summary_rows}
    baseline = overall["type_aware"]
    router = overall["text_intent_router"]
    lines = [
        "# Text-Intent Router Experiment",
        "",
        "本实验只使用 query 文本规则预测 route，不使用 LoCoMo 标注 type，因此比 query-type router 更接近可部署设置。",
        "",
        "## Overall Result",
        "",
        "| Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
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
        "## Route Distribution",
        "",
        "| Selected Method | Predicted Intent | Queries | Share |",
        "|---|---|---:|---:|",
    ])
    for row in distribution_rows:
        lines.append(
            f"| {row['selected_method']} | {row['predicted_intent']} | {row['num_queries']} | {row['share']:.3f} |"
        )
    lines.extend([
        "",
        "## By Predicted Intent",
        "",
        "| Predicted Intent | Selected Method | Queries | Recall@1 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in by_intent_rows:
        lines.append(
            f"| {row['predicted_intent']} | {row['selected_method']} | {row['num_queries']} | "
            f"{metric(row['recall@1'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- 该规则版 router 是可部署 baseline，但仍然很粗糙，可能把大量问题路由到不合适的方法。",
        "- 若它弱于 fixed `type_aware`，说明需要更强的 query intent classifier，而不是简单关键词规则。",
        "- 若它接近 query-type router，则可以继续把规则替换为小模型或 LLM classifier，并在 validation split 上调参。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate text-intent routing from per-query metrics.")
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--default-method", default="type_aware")
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-by-intent", type=Path, required=True)
    parser.add_argument("--output-distribution", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    per_query_rows = read_csv(args.per_query)
    queries = read_queries(args.queries)
    router_rows = select_router_rows(per_query_rows, queries, args.default_method)
    fixed_rows = fixed_method_rows(per_query_rows, args.default_method)
    for row in fixed_rows:
        query = queries.get(row["query_id"], {})
        row["query"] = query.get("query", "")
        row["predicted_intent"] = "fixed_baseline"
    summary = aggregate(fixed_rows, args.default_method, group_by_type=False) + aggregate(router_rows, "text_intent_router", group_by_type=False)
    by_intent = aggregate_by_intent(router_rows)
    distribution = route_distribution(router_rows)

    write_csv(args.output_selected, router_rows)
    write_csv(args.output_comparison, fixed_rows + router_rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_by_intent, by_intent)
    write_csv(args.output_distribution, distribution)
    write_report(args.output_report, summary, by_intent, distribution)


if __name__ == "__main__":
    main()
