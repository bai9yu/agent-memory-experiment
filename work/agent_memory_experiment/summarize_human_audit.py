#!/usr/bin/env python3
"""Summarize completed human-audit labels for retrieval error analysis."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


LABEL_FIELDS = ("auto_reason_correct", "top_memory_relevant", "gold_memory_sufficient")
ALLOWED = {
    "auto_reason_correct": {"yes", "no", "partial", ""},
    "top_memory_relevant": {"yes", "no", "partial", ""},
    "gold_memory_sufficient": {"yes", "no", "unclear", ""},
}


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


def norm(value: str) -> str:
    return value.strip().lower()


def is_labeled(row: dict[str, str]) -> bool:
    return any(norm(row.get(field, "")) for field in LABEL_FIELDS)


def validate_labels(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        audit_id = row.get("audit_id", "unknown")
        for field in LABEL_FIELDS:
            value = norm(row.get(field, ""))
            if value not in ALLOWED[field]:
                allowed = ", ".join(sorted(item or "<blank>" for item in ALLOWED[field]))
                errors.append(f"{audit_id}: field {field} has invalid value `{row.get(field, '')}`; allowed: {allowed}")
    return errors


def summarize_field(rows: list[dict[str, str]], field: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        value = norm(row.get(field, ""))
        if not value:
            continue
        counts[value] = counts.get(value, 0) + 1
    total = sum(counts.values())
    ordered = ["yes", "partial", "no", "unclear"]
    out = []
    for label in ordered:
        if label not in counts:
            continue
        out.append({
            "group": "field",
            "label": field,
            "value": label,
            "count": counts[label],
            "share": counts[label] / total if total else 0.0,
        })
    return out


def summarize_by_reason(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[row.get("auto_reason", "unknown")].append(row)

    out = []
    for reason in sorted(buckets):
        bucket = buckets[reason]
        labeled = [row for row in bucket if norm(row.get("auto_reason_correct", ""))]
        yes = sum(1 for row in labeled if norm(row.get("auto_reason_correct", "")) == "yes")
        partial = sum(1 for row in labeled if norm(row.get("auto_reason_correct", "")) == "partial")
        no = sum(1 for row in labeled if norm(row.get("auto_reason_correct", "")) == "no")
        out.append({
            "group": "auto_reason",
            "label": reason,
            "value": "auto_reason_correct",
            "count": len(labeled),
            "share": (yes + 0.5 * partial) / len(labeled) if labeled else 0.0,
            "yes": yes,
            "partial": partial,
            "no": no,
            "unlabeled": len(bucket) - len(labeled),
        })
    return out


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def fmt(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def write_report(path: Path, rows: list[dict[str, str]], summary_rows: list[dict[str, Any]], validation_errors: list[str]) -> None:
    labeled_rows = [row for row in rows if is_labeled(row)]
    fully_labeled = [
        row for row in rows
        if all(norm(row.get(field, "")) for field in LABEL_FIELDS)
    ]
    status = "ready_for_paper" if len(fully_labeled) == len(rows) and not validation_errors else "pending_labels"

    field_rows = [row for row in summary_rows if row["group"] == "field"]
    reason_rows = [row for row in summary_rows if row["group"] == "auto_reason"]
    field_table = [
        [row["label"], row["value"], str(row["count"]), fmt(row["share"])]
        for row in field_rows
    ]
    reason_table = [
        [
            row["label"],
            str(row["count"]),
            str(row["yes"]),
            str(row["partial"]),
            str(row["no"]),
            str(row["unlabeled"]),
            fmt(row["share"]),
        ]
        for row in reason_rows
    ]

    lines = [
        "# 人工错误复核统计",
        "",
        "本文件汇总人工复核表中的标注结果，用于判断自动错误分析是否足以写入论文。未完成标注时，本文件会明确显示 pending 状态。",
        "",
        "## 总览",
        "",
        f"- 状态：`{status}`",
        f"- 样本数：{len(rows)}",
        f"- 至少填写一个人工字段的样本数：{len(labeled_rows)}",
        f"- 三个人工字段均已填写的样本数：{len(fully_labeled)}",
        f"- 非法标签数：{len(validation_errors)}",
        "",
        "## 字段分布",
        "",
        markdown_table(["Field", "Value", "Count", "Share"], field_table) if field_table else "暂无人工标注。",
        "",
        "## 按自动错误类型统计",
        "",
        markdown_table(["Auto Reason", "Labeled", "Yes", "Partial", "No", "Unlabeled", "Weighted Correct"], reason_table),
        "",
        "## 论文使用判断",
        "",
    ]
    if status == "ready_for_paper":
        lines.extend([
            "- 可以报告 `auto_reason_correct` 的 yes / partial / no 比例作为自动错误分类可靠性。",
            "- 可以报告 `gold_memory_sufficient`，说明失败是否来自检索器还是 gold evidence 不充分。",
        ])
    else:
        lines.extend([
            "- 当前只能说明人工复核流程已经准备好，不能宣称自动错误分类已被人工验证。",
            "- 需要填写 `manual_reason`、`auto_reason_correct`、`top_memory_relevant`、`gold_memory_sufficient` 后重新运行本脚本。",
        ])
    if validation_errors:
        lines.extend(["", "## 非法标签", ""])
        lines.extend([f"- {item}" for item in validation_errors])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize human audit labels.")
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_csv(args.audit_csv)
    validation_errors = validate_labels(rows)
    summary_rows: list[dict[str, Any]] = []
    labeled_rows = [row for row in rows if is_labeled(row)]
    for field in LABEL_FIELDS:
        summary_rows.extend(summarize_field(labeled_rows, field))
    summary_rows.extend(summarize_by_reason(rows))
    write_csv(args.output_csv, summary_rows)
    write_report(args.output_report, rows, summary_rows, validation_errors)
    print(json.dumps({
        "audit_samples": len(rows),
        "labeled_samples": len(labeled_rows),
        "validation_errors": len(validation_errors),
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
