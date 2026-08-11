#!/usr/bin/env python3
"""Summarize paired significance tests for Type-3 evidence coverage metrics."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path
from typing import Any


DEFAULT_METRICS = (
    "coverage_ratio@5",
    "full_coverage@5",
    "coverage_ratio@20",
    "full_coverage@20",
)


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


def row_key(row: dict[str, str]) -> str:
    split_seed = row.get("split_seed", "")
    if split_seed:
        return f"{split_seed}:{row['query_id']}"
    return row["query_id"]


def paired_deltas(rows: list[dict[str, str]], baseline: str, candidate: str, metric: str) -> tuple[list[float], list[float], list[float]]:
    by_key = {(row_key(row), row["method"]): row for row in rows}
    keys = sorted({row_key(row) for row in rows})
    baseline_values = []
    candidate_values = []
    deltas = []
    for key in keys:
        base = by_key.get((key, baseline))
        cand = by_key.get((key, candidate))
        if not base or not cand:
            continue
        left = float(base[metric])
        right = float(cand[metric])
        baseline_values.append(left)
        candidate_values.append(right)
        deltas.append(right - left)
    return baseline_values, candidate_values, deltas


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


def summarize(
    experiment: str,
    rows: list[dict[str, str]],
    baseline: str,
    candidate: str,
    metrics: list[str],
    iterations: int,
    seed: int,
) -> list[dict[str, Any]]:
    output = []
    for idx, metric in enumerate(metrics):
        rng = random.Random(seed + idx)
        baseline_values, candidate_values, deltas = paired_deltas(rows, baseline, candidate, metric)
        ci_low, ci_high = bootstrap_ci(deltas, iterations, rng)
        p_value = permutation_p_value(deltas, iterations, rng)
        output.append({
            "experiment": experiment,
            "baseline": baseline,
            "candidate": candidate,
            "metric": metric,
            "num_pairs": len(deltas),
            "baseline_mean": statistics.mean(baseline_values) if baseline_values else 0.0,
            "candidate_mean": statistics.mean(candidate_values) if candidate_values else 0.0,
            "mean_delta": statistics.mean(deltas) if deltas else 0.0,
            "bootstrap_ci_low": ci_low,
            "bootstrap_ci_high": ci_high,
            "permutation_p_value": p_value,
            "improved_pairs": sum(1 for delta in deltas if delta > 0),
            "worsened_pairs": sum(1 for delta in deltas if delta < 0),
            "tied_pairs": sum(1 for delta in deltas if delta == 0),
        })
    return output


def parse_experiment(value: str) -> tuple[str, Path, str, str]:
    parts = value.split(":")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "Experiment must be label:path:baseline:candidate"
        )
    label, path, baseline, candidate = parts
    return label, Path(path), baseline, candidate


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Type 3 Evidence Coverage 显著性汇总",
        "",
        "本报告只检验 evidence coverage 指标，用于补充 MRR/Recall 的显著性分析。所有检验均为 paired bootstrap CI 和 paired permutation test。",
        "",
        "| Experiment | Candidate | Metric | Baseline | Candidate Mean | Delta | 95% Bootstrap CI | p-value | 改善 | 变差 | 持平 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['experiment']} | {row['candidate']} | {row['metric']} | "
            f"{row['baseline_mean']:.4f} | {row['candidate_mean']:.4f} | {row['mean_delta']:.4f} | "
            f"[{row['bootstrap_ci_low']:.4f}, {row['bootstrap_ci_high']:.4f}] | "
            f"{row['permutation_p_value']:.4f} | {row['improved_pairs']} | {row['worsened_pairs']} | {row['tied_pairs']} |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        "- 如果 Coverage@5 显著下降，说明方法不仅排序变差，也没有改善多证据前排覆盖。",
        "- 如果 Coverage@20 持平但 Coverage@5 下降，说明候选空间没有扩大，或者扩大的信号没有被排到前面。",
        "- 当前 Type 3 后续应优先考虑更强 query decomposition 或 listwise/setwise objective，而不是继续堆浅层候选上下文特征。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3 evidence coverage significance summary.")
    parser.add_argument("--experiment", action="append", type=parse_experiment, required=True)
    parser.add_argument("--metrics", default=",".join(DEFAULT_METRICS))
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    metrics = [item.strip() for item in args.metrics.split(",") if item.strip()]
    all_rows = []
    for idx, (label, path, baseline, candidate) in enumerate(args.experiment):
        rows = read_csv(path)
        all_rows.extend(summarize(label, rows, baseline, candidate, metrics, args.iterations, args.seed + idx * 100))
    write_csv(args.output_csv, all_rows)
    write_report(args.output_report, all_rows)
    print(json.dumps({
        "num_rows": len(all_rows),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
