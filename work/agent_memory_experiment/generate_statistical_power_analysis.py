#!/usr/bin/env python3
"""Estimate paired-sample precision for reranker metric deltas."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


METRICS = ("mrr", "recall@1", "recall@3", "recall@5")
DEFAULT_SAMPLE_SIZES = (100, 250, 500, 1000, 1500, 2760)


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


def safe_float(row: dict[str, str], key: str) -> float:
    try:
        return float(row.get(key, "0"))
    except ValueError:
        return 0.0


def paired_deltas(
    rows: list[dict[str, str]],
    baseline: str,
    candidate: str,
) -> dict[str, list[float]]:
    by_query: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        query_id = row.get("query_id", "")
        method = row.get("method", "")
        if query_id and method:
            by_query[query_id][method] = row

    deltas: dict[str, list[float]] = {metric: [] for metric in METRICS}
    for query_id in sorted(by_query):
        left = by_query[query_id].get(baseline)
        right = by_query[query_id].get(candidate)
        if not left or not right:
            continue
        for metric in METRICS:
            deltas[metric].append(safe_float(right, metric) - safe_float(left, metric))
    return deltas


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = q * (len(ordered) - 1)
    lower = int(pos)
    upper = min(lower + 1, len(ordered) - 1)
    weight = pos - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def bootstrap_means(values: list[float], sample_size: int, draws: int, rng: random.Random) -> list[float]:
    if not values:
        return []
    n = min(sample_size, len(values))
    means: list[float] = []
    for _ in range(draws):
        sample = [values[rng.randrange(len(values))] for _ in range(n)]
        means.append(statistics.mean(sample))
    return means


def summarize_metric(
    comparison: str,
    metric: str,
    values: list[float],
    sample_sizes: list[int],
    draws: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    observed_mean = statistics.mean(values) if values else 0.0
    observed_sd = statistics.stdev(values) if len(values) > 1 else 0.0
    for sample_size in sample_sizes:
        n = min(sample_size, len(values))
        means = bootstrap_means(values, n, draws, rng)
        ci_low = percentile(means, 0.025)
        ci_high = percentile(means, 0.975)
        half_width = (ci_high - ci_low) / 2.0
        analytic_half_width = 1.96 * observed_sd / (n ** 0.5) if n else 0.0
        rows.append({
            "comparison": comparison,
            "metric": metric,
            "sample_size": n,
            "available_pairs": len(values),
            "observed_mean_delta": observed_mean,
            "paired_delta_sd": observed_sd,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "bootstrap_ci_half_width": half_width,
            "analytic_95ci_half_width": analytic_half_width,
            "ci_excludes_zero": ci_low > 0 or ci_high < 0,
            "observed_delta_exceeds_ci_half_width": abs(observed_mean) > half_width,
            "draws": draws,
        })
    return rows


def fmt(value: Any, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    by_metric: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_metric[row["metric"]].append(row)

    lines = [
        "# 统计功效与最小可检测效应分析",
        "",
        "本报告用 paired query-level delta 估计当前样本量下的均值提升精度。它回答两个问题：第一，主方法的提升在较小子样本下是否仍稳定可检测；第二，当前实验规模大约能检测多小的平均提升。该分析不替代外部数据集或人工复核，但可以支撑论文中的统计可靠性说明。",
        "",
        "## 方法",
        "",
        "- 输入：同一 query/seed 下 baseline 与 candidate 的配对指标。",
        "- 对每个样本量进行 bootstrap resampling，记录均值 delta 的 95% CI。",
        "- `bootstrap_ci_half_width` 可近似理解为该样本量下的最小可分辨平均提升尺度；越小代表统计精度越高。",
        "- `ci_excludes_zero=True` 表示该样本量下 bootstrap CI 不跨 0。",
        "",
    ]
    for metric in METRICS:
        metric_rows = sorted(by_metric[metric], key=lambda row: int(row["sample_size"]))
        full = metric_rows[-1]
        first_stable = next((row for row in metric_rows if row["ci_excludes_zero"]), None)
        lines.extend([
            f"## {metric}",
            "",
            "| Sample Size | Mean Δ | 95% CI | CI Half Width | Excludes 0 |",
            "|---:|---:|---:|---:|---|",
        ])
        for row in metric_rows:
            lines.append(
                f"| {row['sample_size']} | {fmt(row['observed_mean_delta'])} | "
                f"[{fmt(row['bootstrap_ci_low'])}, {fmt(row['bootstrap_ci_high'])}] | "
                f"{fmt(row['bootstrap_ci_half_width'])} | {row['ci_excludes_zero']} |"
            )
        lines.extend([
            "",
            f"- 全量 paired samples：{full['available_pairs']}；观察均值提升：{fmt(full['observed_mean_delta'])}。",
            f"- 全量 bootstrap 95% CI：[{fmt(full['bootstrap_ci_low'])}, {fmt(full['bootstrap_ci_high'])}]，半宽 {fmt(full['bootstrap_ci_half_width'])}。",
        ])
        if first_stable:
            lines.append(f"- 在当前抽样网格中，最小稳定样本量为 {first_stable['sample_size']}，其 CI 已不跨 0。")
        else:
            lines.append("- 在当前抽样网格中，CI 仍跨 0；该指标不适合做强结论。")
        lines.append("")
    lines.extend([
        "## 论文使用边界",
        "",
        "- 可以写：主指标在 paired bootstrap 下具有较窄置信区间，观察提升不是由单一小样本偶然性驱动。",
        "- 不能写：该结果已经证明跨数据集泛化；外部 embedding baseline 和人工错误复核仍是最终投稿 blocker。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paired statistical power diagnostics.")
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--baseline", default="type_aware")
    parser.add_argument("--candidate", default="ablation_intrinsic_only")
    parser.add_argument("--comparison-name", default="intrinsic_only_vs_type_aware")
    parser.add_argument("--sample-sizes", default=",".join(str(item) for item in DEFAULT_SAMPLE_SIZES))
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260812)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    sample_sizes = [int(item) for item in args.sample_sizes.split(",") if item.strip()]
    deltas = paired_deltas(read_csv(args.comparison), args.baseline, args.candidate)
    rng = random.Random(args.seed)
    rows: list[dict[str, Any]] = []
    for metric in METRICS:
        rows.extend(summarize_metric(args.comparison_name, metric, deltas[metric], sample_sizes, args.draws, rng))
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    mrr_full = next(row for row in rows if row["metric"] == "mrr" and row["sample_size"] == max(row["sample_size"] for row in rows if row["metric"] == "mrr"))
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "metrics": len(METRICS),
        "draws": args.draws,
        "mrr_full_ci": [mrr_full["bootstrap_ci_low"], mrr_full["bootstrap_ci_high"]],
        "mrr_full_half_width": mrr_full["bootstrap_ci_half_width"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
