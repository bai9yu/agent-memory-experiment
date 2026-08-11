#!/usr/bin/env python3
"""Aggregate cross-agent memory reuse result folders."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_size(name: str) -> int:
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else 0


def fmt(value: str | float) -> str:
    return f"{float(value):.3f}"


def load_result(result_dir: Path) -> dict:
    return {
        "name": result_dir.name,
        "size": run_size(result_dir.name),
        "metrics": read_csv(result_dir / "cross_agent_metrics.csv"),
    }


def write_flat_csv(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for result in results:
        for row in result["metrics"]:
            rows.append({
                "run": result["name"],
                "size": result["size"],
                **row,
            })
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(results: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Cross-Agent Memory Reuse Analysis",
        "",
        "This report tests whether agent B can answer questions using memories shared by agent A, and how retrieval behaves when private same-topic distractors are present.",
        "",
        "## Time-Aware Retrieval",
        "",
        "| Run | Strategy | Memories | Tokens | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        for row in result["metrics"]:
            if row["method"] == "time_aware":
                lines.append(
                    f"| {result['name']} | {row['strategy']} | {row['num_memories']} | {row['total_tokens']} | "
                    f"{fmt(row['recall@1'])} | {fmt(row['recall@3'])} | {fmt(row['recall@5'])} | {fmt(row['mrr'])} |"
                )

    lines.extend([
        "",
        "## Shared Memory Gain",
        "",
        "| Run | Private Recall@1 | Shared Recall@1 | Mixed Recall@1 | Unfiltered Recall@1 | Shared Gain | Mixed Drop | Permission Drop |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for result in results:
        rows = {(row["strategy"], row["method"]): row for row in result["metrics"]}
        private = rows[("private_only", "time_aware")]
        shared = rows[("shared_allowed", "time_aware")]
        mixed = rows[("shared_plus_private_noise", "time_aware")]
        unfiltered = rows[("unfiltered_private_first", "time_aware")]
        shared_gain = float(shared["recall@1"]) - float(private["recall@1"])
        mixed_drop = float(shared["recall@1"]) - float(mixed["recall@1"])
        permission_drop = float(shared["recall@1"]) - float(unfiltered["recall@1"])
        lines.append(
            f"| {result['name']} | {fmt(private['recall@1'])} | {fmt(shared['recall@1'])} | "
            f"{fmt(mixed['recall@1'])} | {fmt(unfiltered['recall@1'])} | "
            f"{shared_gain:.3f} | {mixed_drop:.3f} | {permission_drop:.3f} |"
        )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `private_only` should remain near zero because agent B cannot see the answer memories from agent A.",
        "- `shared_allowed` measures the positive value of cross-agent reusable knowledge.",
        "- `shared_plus_private_noise` is the more realistic condition: authorized shared facts compete with private same-topic memories.",
        "- `unfiltered_private_first` is a risk control showing that retrieval should filter by permission scope before ranking, deduplication, or KV-cache reuse.",
        "- A useful next implementation step is adding a permission gate before retrieval and a second score term for source-agent trust/KV-cache reuse cost.",
    ])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate cross-agent memory reuse result folders.")
    parser.add_argument("result_dirs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()
    results = [load_result(path) for path in args.result_dirs]
    results.sort(key=lambda result: result["size"])
    write_report(results, args.output)
    write_flat_csv(results, args.csv_output)
    print(str(args.output))
    print(str(args.csv_output))


if __name__ == "__main__":
    main()
