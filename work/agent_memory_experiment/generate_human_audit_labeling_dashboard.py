#!/usr/bin/env python3
"""Generate a progress dashboard for human-audit labeling sheets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_HUMAN_FIELDS = (
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
)

OPTIONAL_HUMAN_FIELDS = (
    "human_manual_reason",
    "human_auditor_notes",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def norm(value: str) -> str:
    return value.strip()


def rank_bucket(value: str) -> str:
    try:
        rank = int(float(value))
    except ValueError:
        return "unknown"
    if rank <= 1:
        return "rank_1"
    if rank <= 5:
        return "rank_2_5"
    if rank <= 10:
        return "rank_6_10"
    if rank <= 20:
        return "rank_11_20"
    return "rank_gt_20"


def missing_required_fields(row: dict[str, str]) -> list[str]:
    return [field for field in REQUIRED_HUMAN_FIELDS if not norm(row.get(field, ""))]


def missing_optional_fields(row: dict[str, str]) -> list[str]:
    return [field for field in OPTIONAL_HUMAN_FIELDS if not norm(row.get(field, ""))]


def row_status(row: dict[str, str]) -> str:
    missing = missing_required_fields(row)
    if not missing:
        return "complete_required"
    filled = len(REQUIRED_HUMAN_FIELDS) - len(missing)
    if filled:
        return "partial_required"
    return "not_started"


def build_item_rows(scope: str, rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        missing_required = missing_required_fields(row)
        missing_optional = missing_optional_fields(row)
        out.append({
            "row_type": "item",
            "scope": scope,
            "review_order": row.get("review_order", ""),
            "audit_id": row.get("audit_id", ""),
            "query_id": row.get("query_id", ""),
            "query_type": row.get("query_type", ""),
            "auto_reason": row.get("auto_reason", ""),
            "first_rank": row.get("first_rank", ""),
            "first_rank_bucket": rank_bucket(row.get("first_rank", "")),
            "top_memory_type": row.get("top_memory_type", ""),
            "status": row_status(row),
            "missing_required_count": len(missing_required),
            "missing_required_fields": ";".join(missing_required),
            "missing_optional_fields": ";".join(missing_optional),
            "query": row.get("query", ""),
        })
    return out


def build_summary_rows(scope: str, item_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = len(item_rows)
    status_counts = Counter(row["status"] for row in item_rows)
    missing_total = sum(int(row["missing_required_count"]) for row in item_rows)
    summary_rows: list[dict[str, Any]] = [
        {
            "row_type": "summary",
            "scope": scope,
            "group": "progress",
            "value": "samples",
            "count": total,
            "total": total,
            "share": 1.0 if total else 0.0,
            "evidence": "blind review rows",
        },
        {
            "row_type": "summary",
            "scope": scope,
            "group": "progress",
            "value": "complete_required",
            "count": status_counts["complete_required"],
            "total": total,
            "share": status_counts["complete_required"] / total if total else 0.0,
            "evidence": "all required human_* fields filled",
        },
        {
            "row_type": "summary",
            "scope": scope,
            "group": "progress",
            "value": "partial_required",
            "count": status_counts["partial_required"],
            "total": total,
            "share": status_counts["partial_required"] / total if total else 0.0,
            "evidence": "some required human_* fields filled",
        },
        {
            "row_type": "summary",
            "scope": scope,
            "group": "progress",
            "value": "not_started",
            "count": status_counts["not_started"],
            "total": total,
            "share": status_counts["not_started"] / total if total else 0.0,
            "evidence": "no required human_* fields filled",
        },
        {
            "row_type": "summary",
            "scope": scope,
            "group": "progress",
            "value": "missing_required_fields",
            "count": missing_total,
            "total": total * len(REQUIRED_HUMAN_FIELDS),
            "share": missing_total / (total * len(REQUIRED_HUMAN_FIELDS)) if total else 0.0,
            "evidence": ";".join(REQUIRED_HUMAN_FIELDS),
        },
    ]
    for group, key in (
        ("auto_reason_distribution", "auto_reason"),
        ("query_type_distribution", "query_type"),
        ("rank_bucket_distribution", "first_rank_bucket"),
    ):
        counts = Counter(str(row[key]) or "missing" for row in item_rows)
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            summary_rows.append({
                "row_type": "summary",
                "scope": scope,
                "group": group,
                "value": value,
                "count": count,
                "total": total,
                "share": count / total if total else 0.0,
                "evidence": key,
            })
    return summary_rows


def build_rows(priority_csv: Path, full_csv: Path) -> list[dict[str, Any]]:
    priority_items = build_item_rows("priority20", read_csv(priority_csv))
    full_items = build_item_rows("full80", read_csv(full_csv))
    rows: list[dict[str, Any]] = []
    rows.extend(build_summary_rows("priority20", priority_items))
    rows.extend(build_summary_rows("full80", full_items))
    rows.extend(priority_items)
    rows.extend(full_items)
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_report(path: Path, rows: list[dict[str, Any]], priority_csv: Path, full_csv: Path, item_limit: int) -> None:
    summaries = [row for row in rows if row.get("row_type") == "summary" and row.get("group") == "progress"]
    items = [row for row in rows if row.get("row_type") == "item"]
    next_items = [row for row in items if row["status"] != "complete_required"][:item_limit]
    progress_table = [
        [row["scope"], row["value"], str(row["count"]), str(row["total"]), fmt(row["share"]), row["evidence"]]
        for row in summaries
    ]
    next_table = [
        [
            row["scope"],
            row["review_order"],
            row["audit_id"],
            row["query_type"],
            row["auto_reason"],
            row["first_rank_bucket"],
            str(row["missing_required_count"]),
            row["missing_required_fields"],
        ]
        for row in next_items
    ]
    complete_priority = next((row for row in summaries if row["scope"] == "priority20" and row["value"] == "complete_required"), {})
    complete_full = next((row for row in summaries if row["scope"] == "full80" and row["value"] == "complete_required"), {})
    lines = [
        "# Human Audit Labeling Dashboard",
        "",
        "本文件把 priority20/full80 盲审表的人工填写进度展开成可执行面板。它只读取 human_* 字段是否填写，不替代人工判断，也不使用 LLM-assisted 标签作为人工结果。",
        "",
        "## 总览",
        "",
        f"- Priority CSV: `{priority_csv}`",
        f"- Full CSV: `{full_csv}`",
        f"- priority20 complete required: {complete_priority.get('count', 0)}/{complete_priority.get('total', 0)}",
        f"- full80 complete required: {complete_full.get('count', 0)}/{complete_full.get('total', 0)}",
        f"- Next item preview limit: {item_limit}",
        "",
        "## Progress Summary",
        "",
        markdown_table(["Scope", "Value", "Count", "Total", "Share", "Evidence"], progress_table),
        "",
        "## Next Items To Label",
        "",
        markdown_table(["Scope", "Review Order", "Audit ID", "Query Type", "Auto Reason", "Rank Bucket", "Missing Required", "Missing Fields"], next_table) if next_table else "所有 required human_* 字段均已填写。",
        "",
        "## 使用方式",
        "",
        "1. 标注者打开 priority20 或 full80 blind review CSV。",
        "2. 优先从 `Next Items To Label` 中的 review_order 开始填写。",
        "3. 每条至少填写 `human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`。",
        "4. 建议同时填写 `human_manual_reason` 和 `human_auditor_notes`，便于后续错误分析复盘。",
        "",
        "## 论文使用边界",
        "",
        "- 可以写：人工标注进度有独立 dashboard，可复现记录每轮完成度。",
        "- 不能写：dashboard 通过就等于人工审计完成；真正完成仍以 agreement/readiness gate 为准。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate human-audit labeling dashboard.")
    parser.add_argument("--priority-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--full-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--next-item-limit", type=int, default=30)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.priority_csv, args.full_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.priority_csv, args.full_csv, args.next_item_limit)
    item_rows = [row for row in rows if row.get("row_type") == "item"]
    complete = sum(1 for row in item_rows if row.get("status") == "complete_required")
    print(json.dumps({
        "output_report": str(args.output_report),
        "rows": len(rows),
        "item_rows": len(item_rows),
        "complete_required": complete,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
