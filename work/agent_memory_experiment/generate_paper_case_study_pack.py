#!/usr/bin/env python3
"""Build a compact paper-facing qualitative case-study pack."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


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


def safe_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def truncate(text: str, limit: int = 260) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def select_examples(rows: list[dict[str, str]], per_bucket: int) -> list[dict[str, Any]]:
    buckets = [
        ("success_large_gain", lambda row: row["case"] == "improved"),
        ("failure_large_regression", lambda row: row["case"] == "worsened"),
        ("stable_already_correct", lambda row: row["case"] == "tied"),
    ]
    selected: list[dict[str, Any]] = []
    seen_queries: set[str] = set()
    for bucket, predicate in buckets:
        candidates = [row for row in rows if predicate(row)]
        candidates.sort(key=lambda row: abs(safe_float(row["delta_mrr"])), reverse=True)
        used = 0
        for row in candidates:
            if used >= per_bucket:
                break
            if row["query_id"] in seen_queries and bucket != "stable_already_correct":
                continue
            seen_queries.add(row["query_id"])
            selected.append({
                "case_bucket": bucket,
                "query_id": row["query_id"],
                "query_type": row["query_type"],
                "query": row["query"],
                "delta_mrr": safe_float(row["delta_mrr"]),
                "baseline_first_rank": row["baseline_first_rank"],
                "candidate_first_rank": row["candidate_first_rank"],
                "baseline_top_memory_type": row["baseline_top_memory_type"],
                "baseline_top_memory_text": row["baseline_top_memory_text"],
                "candidate_top_memory_type": row["candidate_top_memory_type"],
                "candidate_top_memory_text": row["candidate_top_memory_text"],
                "gold_memory_types": row["gold_memory_types"],
                "gold_memory_texts": row["gold_memory_texts"],
                "paper_takeaway": takeaway(bucket, row),
            })
            used += 1
    return selected


def takeaway(bucket: str, row: dict[str, str]) -> str:
    if bucket == "success_large_gain":
        return (
            "重排器把更具体、答案承载更强的记忆提前，说明 intrinsic candidate features "
            "可以纠正 fixed type-aware 的主题邻近但答案不足问题。"
        )
    if bucket == "failure_large_regression":
        return (
            "重排器有时会把语义/实体相邻但答案不足的记忆提前，说明方法仍需更强的 "
            "multi-evidence 或 answer-aware objective。"
        )
    return "两种方法都已把 gold memory 排到首位，说明部分 query 主要受候选池质量而非重排策略限制。"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", " ") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    by_bucket: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_bucket.setdefault(row["case_bucket"], []).append(row)

    lines = [
        "# 论文 Case Study Pack",
        "",
        "本文件从已缓存的 candidate reranker 代表性案例中抽取少量可放入论文 qualitative analysis 的成功、失败和稳定案例。它用于帮助解释主表指标背后的具体排序行为；这些案例仍是自动抽取，不能替代人工错误复核。",
        "",
        "## 摘要表",
        "",
        markdown_table(
            ["Bucket", "Query", "Type", "ΔMRR", "Base Rank", "Rerank Rank", "Takeaway"],
            [
                [
                    row["case_bucket"],
                    row["query_id"],
                    row["query_type"],
                    f"{row['delta_mrr']:.4f}",
                    str(row["baseline_first_rank"]),
                    str(row["candidate_first_rank"]),
                    row["paper_takeaway"],
                ]
                for row in rows
            ],
        ),
        "",
    ]
    for bucket in ("success_large_gain", "failure_large_regression", "stable_already_correct"):
        bucket_rows = by_bucket.get(bucket, [])
        lines.extend([f"## {bucket}", ""])
        for row in bucket_rows:
            lines.extend([
                f"### `{row['query_id']}` / Type {row['query_type']} / ΔMRR {row['delta_mrr']:.4f}",
                "",
                f"- Query: {row['query']}",
                f"- Baseline top ({row['baseline_top_memory_type']}, rank {row['baseline_first_rank']}): {truncate(row['baseline_top_memory_text'])}",
                f"- Reranker top ({row['candidate_top_memory_type']}, rank {row['candidate_first_rank']}): {truncate(row['candidate_top_memory_text'])}",
                f"- Gold ({row['gold_memory_types']}): {truncate(row['gold_memory_texts'], 360)}",
                f"- Paper takeaway: {row['paper_takeaway']}",
                "",
            ])
    lines.extend([
        "## 论文写法边界",
        "",
        "- 可以写：这些案例展示了 intrinsic reranker 的典型成功模式和失败边界。",
        "- 应谨慎：案例由脚本自动抽取，未经过人工确认；论文中应称为 illustrative examples，而不是 human-verified error analysis。",
        "- 不能写：这些案例已经证明错误分析经过人工验证，或 Type 3 多证据问题已经解决。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a compact paper case-study pack.")
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--per-bucket", type=int, default=3)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = select_examples(read_csv(args.examples), args.per_bucket)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "case_studies": len(rows),
        "buckets": sorted({row["case_bucket"] for row in rows}),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
