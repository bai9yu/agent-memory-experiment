#!/usr/bin/env python3
"""Validate HTML-exported human-audit CSVs before merging into confirmation sheets."""

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

HUMAN_FIELDS = (
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
)

ALLOWED = {
    "auto_reason_correct": ("yes", "partial", "no"),
    "top_memory_relevant": ("yes", "partial", "no"),
    "gold_memory_sufficient": ("yes", "no", "unclear"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader, [])


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


def is_complete(row: dict[str, str]) -> bool:
    return all(norm(row.get(f"human_{field}", "")) for field in AUDIT_FIELDS)


def invalid_labels(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        audit_id = row.get("audit_id", "unknown")
        for field in AUDIT_FIELDS:
            key = f"human_{field}"
            value = norm(row.get(key, ""))
            if value and value not in ALLOWED[field]:
                errors.append(f"{audit_id}: {key}={row.get(key, '')}")
    return errors


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def check_scope(scope: str, source_csv: Path, export_csv: Path, confirmation_csv: Path) -> dict[str, Any]:
    source_rows = read_csv(source_csv)
    export_rows = read_csv(export_csv)
    export_header = read_header(export_csv)
    source_ids = [row.get("audit_id", "") for row in source_rows]
    export_ids = [row.get("audit_id", "") for row in export_rows]
    missing_human_cols = [field for field in HUMAN_FIELDS if field not in export_header]
    extra_missing_ids = [audit_id for audit_id in source_ids if audit_id not in set(export_ids)]
    unexpected_ids = [audit_id for audit_id in export_ids if audit_id not in set(source_ids)]
    duplicates = duplicate_values([audit_id for audit_id in export_ids if audit_id])
    invalid = invalid_labels(export_rows)
    complete_count = sum(1 for row in export_rows if is_complete(row))
    rows_match = source_ids == export_ids
    status = "ready_to_merge" if (
        export_rows
        and len(export_rows) == len(source_rows)
        and rows_match
        and not missing_human_cols
        and not duplicates
        and not invalid
        and complete_count == len(export_rows)
    ) else "pending_or_invalid"
    if export_rows and complete_count < len(export_rows) and not invalid:
        status = "pending_human_labels"
    return {
        "scope": scope,
        "source_csv": str(source_csv),
        "export_csv": str(export_csv),
        "confirmation_csv": str(confirmation_csv),
        "export_exists": export_csv.exists(),
        "source_rows": len(source_rows),
        "export_rows": len(export_rows),
        "row_count_match": len(source_rows) == len(export_rows),
        "audit_id_order_match": rows_match,
        "missing_human_columns": ";".join(missing_human_cols),
        "missing_audit_ids": ";".join(extra_missing_ids[:20]),
        "unexpected_audit_ids": ";".join(unexpected_ids[:20]),
        "duplicate_audit_ids": ";".join(duplicates[:20]),
        "complete_labels": complete_count,
        "invalid_labels": len(invalid),
        "invalid_examples": ";".join(invalid[:20]),
        "status": status,
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    ready = [row for row in rows if row["status"] == "ready_to_merge"]
    table = [
        [
            row["scope"],
            str(row["export_exists"]),
            f"{row['export_rows']}/{row['source_rows']}",
            str(row["audit_id_order_match"]),
            str(row["complete_labels"]),
            str(row["invalid_labels"]),
            row["status"],
        ]
        for row in rows
    ]
    lines = [
        "# Human Audit Annotation Import Readiness",
        "",
        "本文件检查 HTML 标注界面导出的 CSV 是否可以安全回填到 Human/LLM confirmation 表。它不自动生成或伪造人工标签；当前若 human_* 仍为空，会明确显示为 pending。",
        "",
        "## 总览",
        "",
        f"- Scopes: {len(rows)}",
        f"- Ready to merge: {len(ready)}",
        f"- Pending or invalid: {len(rows) - len(ready)}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Scope", "Export Exists", "Rows", "Audit ID Order Match", "Complete Labels", "Invalid Labels", "Status"], table),
        "",
        "## 回填命令",
        "",
        "priority20 完成后：",
        "",
        "```bash",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/blind_human_audit_labels.py merge \\",
        "  --scope priority20 \\",
        "  --confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \\",
        "  --blind-csv outputs/agent_memory_human_audit_priority20_blind_review.csv \\",
        "  --output-confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \\",
        "  --output-report outputs/agent_memory_human_audit_priority20_blind_review_zh.md",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/confirm_llm_audit_labels.py \\",
        "  --llm-audit-csv outputs/agent_memory_llm_audit_sample_type_aware.csv \\",
        "  --audit-id-csv outputs/agent_memory_human_llm_audit_priority20_ids.csv \\",
        "  --confirmation-csv outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \\",
        "  --output-summary-csv outputs/agent_memory_human_llm_audit_priority20_agreement.csv \\",
        "  --output-report outputs/agent_memory_human_llm_audit_priority20_agreement_zh.md",
        "```",
        "",
        "full80 完成后使用同一流程，替换为 full80 对应 confirmation / blind review / agreement 文件。最后运行：",
        "",
        "```bash",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_human_audit_readiness.py \\",
        "  --full-confirmation outputs/agent_memory_human_llm_audit_confirmation.csv \\",
        "  --priority-confirmation outputs/agent_memory_human_llm_audit_priority20_confirmation.csv \\",
        "  --output-csv outputs/agent_memory_human_audit_readiness_gate.csv \\",
        "  --output-report outputs/agent_memory_human_audit_readiness_gate_zh.md",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_submission_readiness.py \\",
        "  --output-report outputs/agent_memory_submission_readiness_zh.md \\",
        "  --output-csv outputs/agent_memory_submission_readiness.csv",
        "```",
        "",
        "## 使用边界",
        "",
        "- 可以写：人工标注结果回填前有 schema、audit_id 顺序、合法标签和完成度检查。",
        "- 不能写：import readiness 通过前或人工字段为空时，错误分析已经 human-verified。",
    ]
    for row in rows:
        if row["invalid_examples"] or row["missing_audit_ids"] or row["unexpected_audit_ids"]:
            lines.extend(["", f"### {row['scope']} details", ""])
            for key in ("missing_human_columns", "missing_audit_ids", "unexpected_audit_ids", "duplicate_audit_ids", "invalid_examples"):
                if row[key]:
                    lines.append(f"- {key}: `{row[key]}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate HTML-exported human audit CSVs before merge.")
    parser.add_argument("--priority-source-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--priority-export-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--priority-confirmation-csv", type=Path, default=Path("outputs/agent_memory_human_llm_audit_priority20_confirmation.csv"))
    parser.add_argument("--full-source-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--full-export-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--full-confirmation-csv", type=Path, default=Path("outputs/agent_memory_human_llm_audit_confirmation.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_import_readiness.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_import_readiness_zh.md"))
    args = parser.parse_args()

    rows = [
        check_scope("priority20", args.priority_source_csv, args.priority_export_csv, args.priority_confirmation_csv),
        check_scope("full80", args.full_source_csv, args.full_export_csv, args.full_confirmation_csv),
    ]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "ready_to_merge": sum(1 for row in rows if row["status"] == "ready_to_merge"),
        "statuses": {row["scope"]: row["status"] for row in rows},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
