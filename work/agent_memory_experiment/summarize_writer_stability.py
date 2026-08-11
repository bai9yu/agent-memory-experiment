#!/usr/bin/env python3
"""Summarize DeepSeek memory-writer stability across repeated extraction runs."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

from compression_experiment import token_count

METRICS = ("num_memories", "memory_tokens", "prompt_tokens", "completion_tokens", "total_tokens", "num_queries", "recall@1", "recall@3", "recall@5", "mrr")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def usage_totals(path: Path | None) -> dict[str, int]:
    if path is None or not path.exists():
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    rows = read_csv(path)
    return {
        "prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
    }


def summary_metric(path: Path | None, method: str) -> dict[str, float]:
    if path is None or not path.exists():
        return {"num_queries": 0, "recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "mrr": 0.0}
    for row in read_csv(path):
        if row.get("method") == method:
            return {
                "num_queries": int(row["num_queries"]),
                "recall@1": float(row["recall@1"]),
                "recall@3": float(row["recall@3"]),
                "recall@5": float(row["recall@5"]),
                "mrr": float(row["mrr"]),
            }
    raise RuntimeError(f"Method {method} not found in {path}")


def path_or_none(value: str) -> Path | None:
    value = value.strip()
    return Path(value) if value else None


def run_row(manifest_row: dict[str, str]) -> dict[str, Any]:
    method = manifest_row.get("method") or "type_aware"
    memories_path = path_or_none(manifest_row.get("memories", ""))
    usage_path = path_or_none(manifest_row.get("usage", ""))
    summary_path = path_or_none(manifest_row.get("summary", ""))
    completed = manifest_row.get("status") == "completed" and memories_path is not None and memories_path.exists() and summary_path is not None and summary_path.exists()
    if completed:
        memories = read_jsonl(memories_path)
        memory_tokens = sum(token_count(row.get("text", "")) for row in memories)
        usage = usage_totals(usage_path)
        metrics = summary_metric(summary_path, method)
        evidence = "completed"
    else:
        memories = []
        memory_tokens = 0
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        metrics = {"num_queries": 0, "recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "mrr": 0.0}
        evidence = "pending_or_missing_files"
    return {
        "run_id": manifest_row["run_id"],
        "temperature": manifest_row.get("temperature", ""),
        "seed": manifest_row.get("seed", ""),
        "status": "completed" if completed else "pending",
        "num_memories": len(memories),
        "memory_tokens": memory_tokens,
        **usage,
        **metrics,
        "method": method,
        "evidence": evidence,
        "notes": manifest_row.get("notes", ""),
    }


def aggregate_rows(run_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    completed = [row for row in run_rows if row["status"] == "completed"]
    out = []
    for metric in METRICS:
        values = [float(row[metric]) for row in completed]
        out.append({
            "metric": metric,
            "completed_runs": len(completed),
            "mean": statistics.mean(values) if values else 0.0,
            "stdev": statistics.stdev(values) if len(values) >= 2 else 0.0,
            "min": min(values) if values else 0.0,
            "max": max(values) if values else 0.0,
            "status": "ready_for_variance" if len(values) >= 3 else "pending_more_runs",
        })
    return out


def fmt(value: Any) -> str:
    return f"{float(value):.4f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, run_rows: list[dict[str, Any]], aggregate: list[dict[str, Any]]) -> None:
    completed = [row for row in run_rows if row["status"] == "completed"]
    run_table = [
        [
            row["run_id"],
            row["status"],
            str(row["temperature"]),
            str(row["seed"]),
            str(row["num_memories"]),
            str(row["memory_tokens"]),
            str(row["total_tokens"]),
            fmt(row["mrr"]),
            fmt(row["recall@5"]),
        ]
        for row in run_rows
    ]
    aggregate_table = [
        [
            row["metric"],
            str(row["completed_runs"]),
            fmt(row["mean"]),
            fmt(row["stdev"]),
            fmt(row["min"]),
            fmt(row["max"]),
            row["status"],
        ]
        for row in aggregate
    ]
    lines = [
        "# DeepSeek Memory Writer 稳定性报告",
        "",
        "本文件汇总 DeepSeek memory writer 多次抽取实验的规模、API 用量和检索指标方差。当前只读取本地 manifest 和结果文件，不调用 API。",
        "",
        "## 总览",
        "",
        f"- Manifest runs: {len(run_rows)}",
        f"- Completed runs: {len(completed)}",
        f"- 状态：`{'ready_for_variance' if len(completed) >= 3 else 'pending_more_runs'}`",
        "",
        "## Run 明细",
        "",
        markdown_table(["Run", "Status", "Temp", "Seed", "Memories", "Memory Tokens", "API Tokens", "MRR", "R@5"], run_table),
        "",
        "## 聚合统计",
        "",
        markdown_table(["Metric", "Runs", "Mean", "Stdev", "Min", "Max", "Status"], aggregate_table),
        "",
        "## 论文使用判断",
        "",
    ]
    if len(completed) >= 3:
        lines.append("- 可以报告 memory writer 的均值和标准差，作为抽取稳定性证据。")
    else:
        lines.append("- 当前 completed run 少于 3 个，只能说明稳定性分析框架已准备好，不能宣称 memory writer 方差已验证。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize DeepSeek writer stability runs.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-runs", type=Path, required=True)
    parser.add_argument("--output-aggregate", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    manifest_rows = read_csv(args.manifest)
    run_rows = [run_row(row) for row in manifest_rows]
    aggregate = aggregate_rows(run_rows)
    write_csv(args.output_runs, run_rows)
    write_csv(args.output_aggregate, aggregate)
    write_report(args.output_report, run_rows, aggregate)
    print(json.dumps({
        "output_report": str(args.output_report),
        "runs": len(run_rows),
        "completed_runs": sum(1 for row in run_rows if row["status"] == "completed"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
