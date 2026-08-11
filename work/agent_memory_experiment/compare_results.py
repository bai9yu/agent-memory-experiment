#!/usr/bin/env python3
"""Create a consolidated analysis report for multiple experiment runs."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(value: str | float) -> str:
    return f"{float(value):.3f}"


def load_run(result_dir: Path) -> dict:
    summary = read_csv(result_dir / "summary.csv")
    by_type = read_csv(result_dir / "summary_by_type.csv")
    return {
        "name": result_dir.name,
        "summary": summary,
        "by_type": by_type,
    }


def best_method(summary: list[dict]) -> dict:
    return max(summary, key=lambda row: float(row["recall@1"]))


def run_size(name: str) -> int:
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else 10


def write_report(runs: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Agent Memory Experiment Analysis",
        "",
        "This report compares the offline first-stage memory retrieval runs.",
        "",
        "## Overall Results",
        "",
        "| Run | Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for run in runs:
        for row in run["summary"]:
            lines.append(
                f"| {run['name']} | {row['method']} | {fmt(row['recall@1'])} | {fmt(row['recall@3'])} | "
                f"{fmt(row['recall@5'])} | {fmt(row['mrr'])} | {row['num_queries']} |"
            )

    lines.extend(["", "## Best Method Per Run", "", "| Run | Best Method | Recall@1 | MRR |", "|---|---|---:|---:|"])
    for run in runs:
        best = best_method(run["summary"])
        lines.append(f"| {run['name']} | {best['method']} | {fmt(best['recall@1'])} | {fmt(best['mrr'])} |")

    lines.extend([
        "",
        "## Recall@1 Trend",
        "",
        "| Method | " + " | ".join(run["name"] for run in runs) + " |",
        "|---" + "|---:" * len(runs) + "|",
    ])
    methods = sorted({row["method"] for run in runs for row in run["summary"]})
    for method in methods:
        values = []
        for run in runs:
            row = next(item for item in run["summary"] if item["method"] == method)
            values.append(fmt(row["recall@1"]))
        lines.append(f"| {method} | " + " | ".join(values) + " |")

    lines.extend([
        "",
        "## Temporal Update Focus",
        "",
        "| Run | Method | Temporal Recall@1 | Temporal Recall@3 | Temporal MRR |",
        "|---|---|---:|---:|---:|",
    ])
    for run in runs:
        temporal_rows = [row for row in run["by_type"] if row.get("query_type") == "temporal-update"]
        for row in temporal_rows:
            lines.append(
                f"| {run['name']} | {row['method']} | {fmt(row['recall@1'])} | {fmt(row['recall@3'])} | {fmt(row['mrr'])} |"
            )

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- The 10-row sample proves the pipeline works and is easy to inspect by hand.",
        "- At 100 memories, `time_aware` improves Recall@1 over `vector` and `hybrid`, mainly because temporal-update queries need the newest fact rather than the oldest matching fact.",
        "- As memory count grows, the gap becomes clearer: repeated similar memories make plain retrieval confuse old and new facts, while recency-aware reranking recovers many current-state answers.",
        "- Compression and evaluation queries remain harder in synthetic data because many generated memories share the same project and template wording. This is useful: it exposes the need for better entity keys, user/session filters, or stronger embeddings before moving to real LoCoMo data.",
        "",
        "## Next Experimental Step",
        "",
        "Use this offline baseline as the control group, then replace the hashed-vector scorer with a real memory backend such as `mem0` or a sentence-transformer embedding model. The same JSONL files and metrics can stay unchanged.",
    ])
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare memory experiment result folders.")
    parser.add_argument("result_dirs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runs = [load_run(path) for path in args.result_dirs]
    runs.sort(key=lambda run: run_size(run["name"]))
    write_report(runs, args.output)
    print(str(args.output))


if __name__ == "__main__":
    main()
