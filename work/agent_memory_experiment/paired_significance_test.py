#!/usr/bin/env python3
"""Paired significance tests for memory retrieval methods."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def paired_values(rows: list[dict[str, str]], baseline: str, candidate: str, metric: str) -> list[tuple[float, float]]:
    by_key = {(row["query_id"], row["method"]): row for row in rows}
    query_ids = sorted({row["query_id"] for row in rows})
    pairs = []
    for query_id in query_ids:
        left = by_key.get((query_id, baseline))
        right = by_key.get((query_id, candidate))
        if left is None or right is None:
            continue
        pairs.append((float(left[metric]), float(right[metric])))
    return pairs


def bootstrap_ci(deltas: list[float], iterations: int, rng: random.Random) -> tuple[float, float]:
    if not deltas:
        return 0.0, 0.0
    means = []
    n = len(deltas)
    for _ in range(iterations):
        sample = [deltas[rng.randrange(n)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    low_idx = max(0, int(0.025 * iterations))
    high_idx = min(iterations - 1, int(0.975 * iterations))
    return means[low_idx], means[high_idx]


def permutation_p_value(deltas: list[float], iterations: int, rng: random.Random) -> float:
    if not deltas:
        return 1.0
    observed = abs(statistics.mean(deltas))
    count = 0
    for _ in range(iterations):
        mean = statistics.mean(delta if rng.random() < 0.5 else -delta for delta in deltas)
        if abs(mean) >= observed:
            count += 1
    return (count + 1) / (iterations + 1)


def summarize_metric(rows: list[dict[str, str]], baseline: str, candidate: str, metric: str, iterations: int, seed: int) -> dict[str, float | int | str]:
    rng = random.Random(seed)
    pairs = paired_values(rows, baseline, candidate, metric)
    baseline_values = [left for left, _ in pairs]
    candidate_values = [right for _, right in pairs]
    deltas = [right - left for left, right in pairs]
    mean_delta = statistics.mean(deltas) if deltas else 0.0
    ci_low, ci_high = bootstrap_ci(deltas, iterations, rng)
    p_value = permutation_p_value(deltas, iterations, rng)
    improved = sum(1 for delta in deltas if delta > 0)
    worsened = sum(1 for delta in deltas if delta < 0)
    tied = sum(1 for delta in deltas if delta == 0)
    return {
        "metric": metric,
        "baseline": baseline,
        "candidate": candidate,
        "num_queries": len(pairs),
        "baseline_mean": statistics.mean(baseline_values) if baseline_values else 0.0,
        "candidate_mean": statistics.mean(candidate_values) if candidate_values else 0.0,
        "mean_delta": mean_delta,
        "bootstrap_ci_low": ci_low,
        "bootstrap_ci_high": ci_high,
        "permutation_p_value": p_value,
        "improved_queries": improved,
        "worsened_queries": worsened,
        "tied_queries": tied,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict]) -> None:
    lines = [
        "# 配对显著性检验",
        "",
        "| 指标 | Baseline | Candidate | Delta | 95% Bootstrap CI | Permutation p-value | 改善 | 变差 | 持平 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {row['baseline']} | {row['candidate']} | "
            f"{row['mean_delta']:.6f} | [{row['bootstrap_ci_low']:.6f}, {row['bootstrap_ci_high']:.6f}] | "
            f"{row['permutation_p_value']:.4f} | {row['improved_queries']} | {row['worsened_queries']} | {row['tied_queries']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paired bootstrap and permutation tests for retrieval metrics.")
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--baseline", default="time_aware")
    parser.add_argument("--candidate", default="type_aware")
    parser.add_argument("--metrics", default="mrr,recall@1,recall@3,recall@5")
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_rows(args.per_query)
    metrics = [item.strip() for item in args.metrics.split(",") if item.strip()]
    summaries = [
        summarize_metric(rows, args.baseline, args.candidate, metric, args.iterations, args.seed + idx)
        for idx, metric in enumerate(metrics)
    ]
    write_csv(args.output_csv, summaries)
    write_report(args.output_report, summaries)
    print(json.dumps({"output_csv": str(args.output_csv), "output_report": str(args.output_report), "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
