#!/usr/bin/env python3
"""Compare BGE-M3 baseline with optional API embedding baseline results."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


METRICS = ("recall@1", "recall@3", "recall@5", "mrr")


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


def metric_row(path: Path, method: str) -> dict[str, str] | None:
    if not path.exists():
        return None
    for row in read_csv(path):
        if row.get("method") == method:
            return row
    return None


def build_rows(bge_summary: Path, api_summary: Path, method: str, api_label: str) -> list[dict[str, Any]]:
    bge = metric_row(bge_summary, method)
    if bge is None:
        raise RuntimeError(f"BGE summary row not found: method={method}, path={bge_summary}")
    api = metric_row(api_summary, method)
    rows = []
    for metric in METRICS:
        bge_value = float(bge[metric])
        if api is None:
            rows.append({
                "metric": metric,
                "bge_m3": bge_value,
                "api_embedding": "",
                "delta_api_minus_bge": "",
                "status": "pending_api_result",
                "api_label": api_label,
            })
        else:
            api_value = float(api[metric])
            rows.append({
                "metric": metric,
                "bge_m3": bge_value,
                "api_embedding": api_value,
                "delta_api_minus_bge": api_value - bge_value,
                "status": "completed",
                "api_label": api_label,
            })
    return rows


def fmt(value: Any) -> str:
    if value == "":
        return "pending"
    return f"{float(value):.4f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], bge_summary: Path, api_summary: Path, method: str) -> None:
    completed = all(row["status"] == "completed" for row in rows)
    table_rows = [
        [
            row["metric"],
            fmt(row["bge_m3"]),
            fmt(row["api_embedding"]),
            fmt(row["delta_api_minus_bge"]),
            row["status"],
        ]
        for row in rows
    ]
    lines = [
        "# Embedding Baseline 对比报告",
        "",
        "本文件用于比较本地 BGE-M3 主结果与外部 API embedding baseline。它只读取本地 summary.csv，不发起网络请求。",
        "",
        "## 输入",
        "",
        f"- BGE-M3 summary: `{bge_summary}`",
        f"- API embedding summary: `{api_summary}`",
        f"- Method: `{method}`",
        "",
        "## 指标对比",
        "",
        markdown_table(["Metric", "BGE-M3", "API Embedding", "Delta", "Status"], table_rows),
        "",
        "## 论文使用判断",
        "",
    ]
    if completed:
        lines.append("- API embedding baseline 已完成，可以把该表加入 embedding 对照实验。")
    else:
        lines.append("- API embedding baseline 尚未生成 summary.csv；当前只能说明对比框架已准备好，不能写入主结果。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare BGE and API embedding baseline summaries.")
    parser.add_argument("--bge-summary", type=Path, required=True)
    parser.add_argument("--api-summary", type=Path, required=True)
    parser.add_argument("--method", default="type_aware")
    parser.add_argument("--api-label", default="OpenAI text-embedding-3-small")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.bge_summary, args.api_summary, args.method, args.api_label)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.bge_summary, args.api_summary, args.method)
    print(json.dumps({
        "output_report": str(args.output_report),
        "status": "completed" if all(row["status"] == "completed" for row in rows) else "pending_api_result",
        "metrics": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
