#!/usr/bin/env python3
"""Validate human-audit readiness for paper-facing reliability claims."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


AUDIT_FIELDS = (
    "auto_reason_correct",
    "top_memory_relevant",
    "gold_memory_sufficient",
)

ALLOWED = {
    "auto_reason_correct": ("yes", "partial", "no"),
    "top_memory_relevant": ("yes", "partial", "no"),
    "gold_memory_sufficient": ("yes", "no", "unclear"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str) -> str:
    return value.strip().lower()


def is_confirmed(row: dict[str, str]) -> bool:
    return all(norm(row.get(f"human_{field}", "")) for field in AUDIT_FIELDS)


def missing_fields(row: dict[str, str]) -> list[str]:
    return [
        f"human_{field}"
        for field in AUDIT_FIELDS
        if not norm(row.get(f"human_{field}", ""))
    ]


def invalid_labels(row: dict[str, str]) -> list[str]:
    errors = []
    audit_id = row.get("audit_id", "unknown")
    for field in AUDIT_FIELDS:
        value = norm(row.get(f"human_{field}", ""))
        if value and value not in ALLOWED[field]:
            errors.append(f"{audit_id}: human_{field}={row.get(f'human_{field}', '')}")
    return errors


def summarize_one(label: str, path: Path, min_required: int) -> dict[str, Any]:
    rows = read_csv(path) if path.exists() else []
    confirmed = [row for row in rows if is_confirmed(row)]
    invalid = []
    missing_total = 0
    incomplete_ids = []
    for row in rows:
        invalid.extend(invalid_labels(row))
        missing = missing_fields(row)
        missing_total += len(missing)
        if missing and len(incomplete_ids) < 20:
            incomplete_ids.append(f"{row.get('audit_id', 'unknown')}({','.join(missing)})")
    status = "paper_ready" if len(confirmed) >= min_required and not invalid else "pending_human_confirmation"
    if rows and len(confirmed) == len(rows) and not invalid:
        status = "complete"
    return {
        "label": label,
        "path": str(path),
        "exists": path.exists(),
        "samples": len(rows),
        "min_required": min_required,
        "confirmed_samples": len(confirmed),
        "missing_human_fields": missing_total,
        "invalid_labels": len(invalid),
        "status": status,
        "completion_rate": len(confirmed) / len(rows) if rows else 0.0,
        "incomplete_examples": "; ".join(incomplete_ids),
        "invalid_examples": "; ".join(invalid[:20]),
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    full = next(row for row in rows if row["label"] == "full80")
    priority = next(row for row in rows if row["label"] == "priority20")
    blockers = []
    if priority["confirmed_samples"] < priority["min_required"] or priority["invalid_labels"]:
        blockers.append("priority20 人工抽查尚未达到最小可报告阈值。")
    if full["confirmed_samples"] < full["min_required"] or full["invalid_labels"]:
        blockers.append("full80 完整人工确认尚未达到完整 human-verified error analysis 阈值。")

    table_rows = [
        [
            row["label"],
            str(row["exists"]),
            str(row["samples"]),
            str(row["confirmed_samples"]),
            str(row["min_required"]),
            f"{float(row['completion_rate']):.3f}",
            str(row["missing_human_fields"]),
            str(row["invalid_labels"]),
            row["status"],
        ]
        for row in rows
    ]
    lines = [
        "# Human Audit Readiness 门禁",
        "",
        "本文件检查 Human/LLM 确认表是否已经足以支撑论文中的人工复核声明。它不自动填写人工标签，也不把 LLM-assisted 预标注当成人工结果。",
        "",
        "## 总览",
        "",
        f"- blocker 数：{len(blockers)}",
        f"- priority20 confirmed：{priority['confirmed_samples']}/{priority['min_required']}",
        f"- full80 confirmed：{full['confirmed_samples']}/{full['min_required']}",
        "",
        markdown_table(
            ["Scope", "Exists", "Samples", "Confirmed", "Required", "Rate", "Missing Fields", "Invalid Labels", "Status"],
            table_rows,
        ),
        "",
        "## 论文声明门槛",
        "",
        "- `priority20` 达到 20/20 且无非法标签后，可以写为小样本人工抽查或 quick-review agreement。",
        "- `full80` 达到 80/80 且无非法标签后，才可以写为完整 Human/LLM error-audit agreement。",
        "- 在任一门槛未达成前，论文只能写 LLM-assisted audit draft / human confirmation protocol。",
        "",
        "## 当前 blocker",
        "",
    ]
    if blockers:
        lines.extend([f"- {item}" for item in blockers])
    else:
        lines.append("- 无。人工复核门禁已通过。")
    lines.extend(["", "## 待填写样例", ""])
    for row in rows:
        lines.append(f"### {row['label']}")
        if row["incomplete_examples"]:
            for item in str(row["incomplete_examples"]).split("; ")[:20]:
                lines.append(f"- {item}")
        else:
            lines.append("- 无缺失人工字段。")
        if row["invalid_examples"]:
            lines.append("")
            lines.append("非法标签样例：")
            for item in str(row["invalid_examples"]).split("; ")[:20]:
                lines.append(f"- {item}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate human-audit readiness for paper claims.")
    parser.add_argument("--full-confirmation", type=Path, required=True)
    parser.add_argument("--priority-confirmation", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = [
        summarize_one("priority20", args.priority_confirmation, min_required=20),
        summarize_one("full80", args.full_confirmation, min_required=80),
    ]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "blockers": sum(1 for row in rows if row["status"] == "pending_human_confirmation"),
        "confirmed": {row["label"]: row["confirmed_samples"] for row in rows},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
