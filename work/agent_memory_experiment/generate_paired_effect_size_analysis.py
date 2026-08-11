#!/usr/bin/env python3
"""Generate paired outcome and effect-size diagnostics for reranker comparisons."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


METRICS = ("mrr", "recall@1", "recall@3", "recall@5")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def paired_rows(rows: list[dict[str, str]], baseline: str, candidate: str) -> list[tuple[str, dict[str, str], dict[str, str]]]:
    by_query: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        query_id = row.get("query_id", "")
        method = row.get("method", "")
        if query_id and method:
            by_query[query_id][method] = row
    pairs = []
    for query_id in sorted(by_query):
        left = by_query[query_id].get(baseline)
        right = by_query[query_id].get(candidate)
        if left and right:
            pairs.append((query_id, left, right))
    return pairs


def safe_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "0")
    try:
        return float(value)
    except ValueError:
        return 0.0


def paired_effect_row(
    comparison: str,
    group: str,
    group_value: str,
    metric: str,
    pairs: list[tuple[str, dict[str, str], dict[str, str]]],
) -> dict[str, Any]:
    deltas = [safe_float(right, metric) - safe_float(left, metric) for _, left, right in pairs]
    n = len(deltas)
    improved = sum(1 for delta in deltas if delta > 0.0)
    worsened = sum(1 for delta in deltas if delta < 0.0)
    tied = n - improved - worsened
    mean_delta = statistics.mean(deltas) if deltas else 0.0
    stdev_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
    cohen_dz = mean_delta / stdev_delta if stdev_delta else 0.0
    win_loss_ratio = improved / worsened if worsened else math.inf if improved else 0.0
    positive_rate = improved / n if n else 0.0
    negative_rate = worsened / n if n else 0.0
    tie_rate = tied / n if n else 0.0
    net_positive_rate = (improved - worsened) / n if n else 0.0
    return {
        "comparison": comparison,
        "group": group,
        "group_value": group_value,
        "metric": metric,
        "pairs": n,
        "baseline_mean": statistics.mean(safe_float(left, metric) for _, left, _ in pairs) if pairs else 0.0,
        "candidate_mean": statistics.mean(safe_float(right, metric) for _, _, right in pairs) if pairs else 0.0,
        "mean_delta": mean_delta,
        "stdev_delta": stdev_delta,
        "cohen_dz": cohen_dz,
        "improved_pairs": improved,
        "worsened_pairs": worsened,
        "tied_pairs": tied,
        "positive_rate": positive_rate,
        "negative_rate": negative_rate,
        "tie_rate": tie_rate,
        "net_positive_rate": net_positive_rate,
        "win_loss_ratio": win_loss_ratio,
    }


def summarize_comparison(
    comparison: str,
    pairs: list[tuple[str, dict[str, str], dict[str, str]]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for metric in METRICS:
        rows.append(paired_effect_row(comparison, "all", "all", metric, pairs))
    by_type: dict[str, list[tuple[str, dict[str, str], dict[str, str]]]] = defaultdict(list)
    for pair in pairs:
        _, left, right = pair
        query_type = right.get("query_type") or left.get("query_type") or "unknown"
        by_type[query_type].append(pair)
    for query_type in sorted(by_type, key=lambda value: (value == "unknown", value)):
        for metric in METRICS:
            rows.append(paired_effect_row(comparison, "query_type", query_type, metric, by_type[query_type]))
    return rows


def fmt(value: Any, digits: int = 4) -> str:
    if value == math.inf:
        return "inf"
    return f"{float(value):.{digits}f}"


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    by_comparison: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_comparison[row["comparison"]].append(row)

    lines = [
        "# Paired Outcome 与效应量分析",
        "",
        "本报告补充 bootstrap CI 之外的效应解释：同一 query/seed 配对中，候选方法相对 baseline 到底有多少样本变好、变差或不变，并给出 paired Cohen's dz。它用于回答“平均提升是否由少数样本拉动”以及“收益集中在哪些 query type”。",
        "",
    ]
    for comparison, comp_rows in by_comparison.items():
        overall = {row["metric"]: row for row in comp_rows if row["group"] == "all"}
        mrr = overall["mrr"]
        r5 = overall["recall@5"]
        lines.extend([
            f"## {comparison}",
            "",
            "### Overall",
            "",
            "| Metric | Baseline | Candidate | ΔMean | Cohen dz | Improved/Worse/Tie | Net Positive Rate | Win/Loss |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for metric in METRICS:
            row = overall[metric]
            lines.append(
                f"| {metric} | {fmt(row['baseline_mean'])} | {fmt(row['candidate_mean'])} | "
                f"{fmt(row['mean_delta'])} | {fmt(row['cohen_dz'])} | "
                f"{row['improved_pairs']}/{row['worsened_pairs']}/{row['tied_pairs']} | "
                f"{fmt(row['net_positive_rate'])} | {fmt(row['win_loss_ratio'])} |"
            )
        lines.extend([
            "",
            "### Query Type Breakdown",
            "",
            "| Query Type | Metric | Pairs | ΔMean | Cohen dz | Improved/Worse/Tie | Net Positive Rate |",
            "|---|---|---:|---:|---:|---:|---:|",
        ])
        type_rows = [row for row in comp_rows if row["group"] == "query_type" and row["metric"] in {"mrr", "recall@5"}]
        for row in sorted(type_rows, key=lambda item: (item["group_value"], item["metric"])):
            lines.append(
                f"| {row['group_value']} | {row['metric']} | {row['pairs']} | {fmt(row['mean_delta'])} | "
                f"{fmt(row['cohen_dz'])} | {row['improved_pairs']}/{row['worsened_pairs']}/{row['tied_pairs']} | "
                f"{fmt(row['net_positive_rate'])} |"
            )
        lines.extend([
            "",
            "### Interpretation",
            "",
            (
                f"- MRR: improved/worse/tie={mrr['improved_pairs']}/{mrr['worsened_pairs']}/{mrr['tied_pairs']}，"
                f"net positive rate={fmt(mrr['net_positive_rate'])}，Cohen dz={fmt(mrr['cohen_dz'])}。"
            ),
            (
                f"- Recall@5: improved/worse/tie={r5['improved_pairs']}/{r5['worsened_pairs']}/{r5['tied_pairs']}，"
                f"net positive rate={fmt(r5['net_positive_rate'])}，Cohen dz={fmt(r5['cohen_dz'])}。"
            ),
            "- 该分析仍基于 LoCoMo10 answerable slice，不能替代外部数据集泛化或人工复核。",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paired outcome/effect-size diagnostics.")
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--baseline", default="type_aware")
    parser.add_argument("--candidate", default="ablation_intrinsic_only")
    parser.add_argument("--comparison-name", default="intrinsic_only_vs_type_aware")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_csv(args.comparison)
    pairs = paired_rows(rows, args.baseline, args.candidate)
    effect_rows = summarize_comparison(args.comparison_name, pairs)
    write_csv(args.output_csv, effect_rows)
    write_report(args.output_report, effect_rows)
    overall_mrr = next(
        row for row in effect_rows
        if row["comparison"] == args.comparison_name and row["group"] == "all" and row["metric"] == "mrr"
    )
    print(json.dumps({
        "output_report": str(args.output_report),
        "pairs": overall_mrr["pairs"],
        "mrr_improved": overall_mrr["improved_pairs"],
        "mrr_worsened": overall_mrr["worsened_pairs"],
        "mrr_tied": overall_mrr["tied_pairs"],
        "mrr_cohen_dz": overall_mrr["cohen_dz"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
