#!/usr/bin/env python3
"""Summarize Top-K depth effects for multi-evidence coverage."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


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


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def metric(value: float) -> str:
    return f"{value:.3f}"


def build_depth_rows(delta_rows: list[dict[str, str]], ks: list[int]) -> list[dict[str, Any]]:
    rows = []
    for row in delta_rows:
        query_type = row["query_type"]
        for k in ks:
            rows.append({
                "query_type": query_type,
                "k": k,
                "mean_gold": as_float(row, "mean_gold"),
                "multi_evidence_share": as_float(row, "multi_evidence_share"),
                "baseline_coverage_ratio": as_float(row, f"baseline_coverage_ratio@{k}"),
                "candidate_coverage_ratio": as_float(row, f"candidate_coverage_ratio@{k}"),
                "delta_coverage_ratio": as_float(row, f"delta_coverage_ratio@{k}"),
                "baseline_full_coverage": as_float(row, f"baseline_full_coverage@{k}"),
                "candidate_full_coverage": as_float(row, f"candidate_full_coverage@{k}"),
                "delta_full_coverage": as_float(row, f"delta_full_coverage@{k}"),
            })
    return rows


def write_report(path: Path, depth_rows: list[dict[str, Any]]) -> None:
    type3_rows = [row for row in depth_rows if row["query_type"] == "3"]
    lines = [
        "# Candidate Depth Analysis",
        "",
        "本报告比较不同 Top-K 深度下的 evidence coverage，用于判断 Type 3 是候选池不足还是排序/集合选择不足。",
        "",
        "## Type 3 Depth Curve",
        "",
        "| K | Base Coverage | Reranker Coverage | Delta Coverage | Base Full | Reranker Full | Delta Full |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in type3_rows:
        lines.append(
            f"| {row['k']} | {metric(row['baseline_coverage_ratio'])} | {metric(row['candidate_coverage_ratio'])} | "
            f"{row['delta_coverage_ratio']:.4f} | {metric(row['baseline_full_coverage'])} | "
            f"{metric(row['candidate_full_coverage'])} | {row['delta_full_coverage']:.4f} |"
        )
    lines.extend([
        "",
        "## All Query Types @20",
        "",
        "| Query Type | Base Coverage@20 | Reranker Coverage@20 | Delta | Base Full@20 | Reranker Full@20 | Delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in [item for item in depth_rows if item["k"] == 20]:
        lines.append(
            f"| Type {row['query_type']} | {metric(row['baseline_coverage_ratio'])} | "
            f"{metric(row['candidate_coverage_ratio'])} | {row['delta_coverage_ratio']:.4f} | "
            f"{metric(row['baseline_full_coverage'])} | {metric(row['candidate_full_coverage'])} | "
            f"{row['delta_full_coverage']:.4f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Type 3 在 Top-5 上没有改善，但在 Top-20 上 candidate reranker 的 coverage ratio 明显超过 fixed `type_aware`。",
        "- 这说明相关 evidence 并非完全缺失，而是常落在较深候选位置；下一步应扩大候选召回并做 set-level selection。",
        "- 简单 Top-10 MMR 失败并不否定集合选择方向，它说明需要在更深候选池和更明确的覆盖目标上做集合选择。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize evidence coverage depth curves.")
    parser.add_argument("--delta-by-type", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,10,20")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    depth_rows = build_depth_rows(read_csv(args.delta_by_type), ks)
    write_csv(args.output_csv, depth_rows)
    write_report(args.output_report, depth_rows)


if __name__ == "__main__":
    main()
