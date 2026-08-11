#!/usr/bin/env python3
"""Prepare and summarize human confirmation of LLM-assisted audit labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
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

CONTEXT_FIELDS = (
    "audit_id",
    "query_id",
    "query",
    "query_type",
    "auto_reason",
    "first_rank",
    "top_memory_id",
    "top_memory_type",
    "top_memory_text",
    "gold_memory_ids",
    "gold_memory_types",
    "gold_memory_texts",
)

CONFIRMATION_FIELDS = (
    *CONTEXT_FIELDS,
    "llm_manual_reason",
    "llm_auto_reason_correct",
    "llm_top_memory_relevant",
    "llm_gold_memory_sufficient",
    "llm_auditor_notes",
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def filter_by_audit_ids(rows: list[dict[str, str]], id_csv: Path | None) -> list[dict[str, str]]:
    if id_csv is None:
        return rows
    id_rows = read_csv(id_csv)
    ordered_ids = [row["audit_id"] for row in id_rows if row.get("audit_id")]
    row_by_id = {row["audit_id"]: row for row in rows if row.get("audit_id")}
    missing = [audit_id for audit_id in ordered_ids if audit_id not in row_by_id]
    if missing:
        raise RuntimeError(f"Missing audit ids in LLM audit CSV: {missing[:5]}")
    return [row_by_id[audit_id] for audit_id in ordered_ids]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | tuple[str, ...] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str) -> str:
    return value.strip().lower()


def is_confirmed(row: dict[str, str]) -> bool:
    return all(norm(row.get(f"human_{field}", "")) for field in AUDIT_FIELDS)


def prepare_rows(llm_rows: list[dict[str, str]], existing_rows: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    existing_by_id = {row["audit_id"]: row for row in existing_rows or [] if row.get("audit_id")}
    out: list[dict[str, str]] = []
    for row in llm_rows:
        old = existing_by_id.get(row["audit_id"], {})
        new_row: dict[str, str] = {}
        for field in CONTEXT_FIELDS:
            new_row[field] = row.get(field, "")
        new_row["llm_manual_reason"] = row.get("manual_reason", "")
        for field in AUDIT_FIELDS:
            new_row[f"llm_{field}"] = norm(row.get(field, ""))
        new_row["llm_auditor_notes"] = row.get("auditor_notes", "")
        new_row["human_manual_reason"] = old.get("human_manual_reason", "")
        for field in AUDIT_FIELDS:
            new_row[f"human_{field}"] = norm(old.get(f"human_{field}", ""))
        new_row["human_auditor_notes"] = old.get("human_auditor_notes", "")
        out.append(new_row)
    return out


def validate_rows(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        audit_id = row.get("audit_id", "unknown")
        for source in ("llm", "human"):
            for field in AUDIT_FIELDS:
                key = f"{source}_{field}"
                value = norm(row.get(key, ""))
                if source == "human" and not value:
                    continue
                if value not in ALLOWED[field]:
                    allowed = ", ".join(ALLOWED[field])
                    errors.append(f"{audit_id}: {key}=`{row.get(key, '')}`; allowed: {allowed}")
    return errors


def cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> float | None:
    if not pairs:
        return None
    total = len(pairs)
    observed = sum(1 for left, right in pairs if left == right) / total
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum((left_counts[label] / total) * (right_counts[label] / total) for label in labels)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else None
    return (observed - expected) / (1.0 - expected)


def summarize(rows: list[dict[str, str]], validation_errors: list[str]) -> list[dict[str, Any]]:
    confirmed = [row for row in rows if is_confirmed(row)]
    summary: list[dict[str, Any]] = [
        {
            "group": "overview",
            "label": "samples",
            "value": "total",
            "count": len(rows),
            "share": 1.0 if rows else 0.0,
        },
        {
            "group": "overview",
            "label": "confirmed_samples",
            "value": "fully_confirmed",
            "count": len(confirmed),
            "share": len(confirmed) / len(rows) if rows else 0.0,
        },
        {
            "group": "overview",
            "label": "validation_errors",
            "value": "invalid_labels",
            "count": len(validation_errors),
            "share": 0.0,
        },
    ]
    for field in AUDIT_FIELDS:
        pairs = [(norm(row[f"llm_{field}"]), norm(row[f"human_{field}"])) for row in confirmed]
        exact = sum(1 for llm, human in pairs if llm == human)
        partial_credit = 0.0
        for llm, human in pairs:
            if llm == human:
                partial_credit += 1.0
            elif "partial" in {llm, human}:
                partial_credit += 0.5
        summary.append({
            "group": "agreement",
            "label": field,
            "value": "exact",
            "count": exact,
            "total": len(pairs),
            "share": exact / len(pairs) if pairs else 0.0,
            "kappa": cohen_kappa(pairs, ALLOWED[field]),
        })
        summary.append({
            "group": "agreement",
            "label": field,
            "value": "partial_credit",
            "count": partial_credit,
            "total": len(pairs),
            "share": partial_credit / len(pairs) if pairs else 0.0,
            "kappa": "",
        })
    for field in AUDIT_FIELDS:
        for value in ALLOWED[field]:
            count = sum(1 for row in confirmed if norm(row.get(f"human_{field}", "")) == value)
            summary.append({
                "group": "human_distribution",
                "label": field,
                "value": value,
                "count": count,
                "share": count / len(confirmed) if confirmed else 0.0,
            })
    return summary


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def fmt(value: Any, digits: int = 3) -> str:
    if value in ("", None):
        return ""
    return f"{float(value):.{digits}f}"


def write_report(path: Path, rows: list[dict[str, str]], summary: list[dict[str, Any]], validation_errors: list[str]) -> None:
    confirmed = [row for row in rows if is_confirmed(row)]
    status = "ready_for_agreement_analysis" if len(confirmed) == len(rows) and rows and not validation_errors else "pending_human_confirmation"
    agreement_rows = [row for row in summary if row["group"] == "agreement" and row["value"] == "exact"]
    distribution_rows = [row for row in summary if row["group"] == "human_distribution"]
    lines = [
        "# Human/LLM 错误复核一致性报告",
        "",
        "本文件用于跟踪人工确认 LLM-assisted 错误复核初稿的进度，并在人工字段填写后统计 Human/LLM 一致性。当前报告不会把 LLM 预标注等同于人工标注。",
        "",
        "## 状态",
        "",
        f"- 状态：`{status}`",
        f"- 样本数：{len(rows)}",
        f"- 三个人工字段均已确认的样本数：{len(confirmed)}",
        f"- 非法标签数：{len(validation_errors)}",
        "",
        "## 一致性指标",
        "",
        markdown_table(
            ["Field", "Exact Agree", "Total", "Exact Rate", "Cohen Kappa"],
            [[row["label"], str(row["count"]), str(row["total"]), fmt(row["share"]), fmt(row["kappa"])] for row in agreement_rows],
        ),
        "",
        "## 人工标签分布",
        "",
        markdown_table(
            ["Field", "Value", "Count", "Share"],
            [[row["label"], row["value"], str(row["count"]), fmt(row["share"])] for row in distribution_rows],
        ),
        "",
        "## 人工填写说明",
        "",
        "- 在确认表中填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。",
        "- 允许标签：`auto_reason_correct` 和 `top_memory_relevant` 使用 `yes` / `partial` / `no`；`gold_memory_sufficient` 使用 `yes` / `no` / `unclear`。",
        "- 完成人工确认后重新运行本脚本，即可得到可写入论文的 Human/LLM 一致性统计。",
        "",
        "## 论文使用判断",
        "",
    ]
    if status == "ready_for_agreement_analysis":
        lines.extend([
            "- 可以报告 Human/LLM exact agreement 与 Cohen's kappa，作为错误复核过程可靠性的补充证据。",
            "- 同时应报告人工标签分布，避免只展示一致性而忽略错误类型本身的质量。",
        ])
    else:
        lines.extend([
            "- 当前只能说明确认流程已准备好；在人工字段完成前，不能宣称错误分析已经被人工验证。",
            "- 若时间有限，建议至少人工确认 20 条高歧义样本，再单独报告抽样一致性。",
        ])
    if validation_errors:
        lines.extend(["", "## 非法标签", ""])
        lines.extend([f"- {item}" for item in validation_errors])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and summarize human confirmation for LLM-assisted audit labels.")
    parser.add_argument("--llm-audit-csv", type=Path, required=True)
    parser.add_argument("--audit-id-csv", type=Path)
    parser.add_argument("--confirmation-csv", type=Path, required=True)
    parser.add_argument("--output-summary-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    llm_rows = filter_by_audit_ids(read_csv(args.llm_audit_csv), args.audit_id_csv)
    existing_rows = read_csv(args.confirmation_csv) if args.confirmation_csv.exists() else None
    confirmation_rows = prepare_rows(llm_rows, existing_rows)
    validation_errors = validate_rows(confirmation_rows)
    summary = summarize(confirmation_rows, validation_errors)
    write_csv(args.confirmation_csv, confirmation_rows, CONFIRMATION_FIELDS)
    write_csv(args.output_summary_csv, summary)
    write_report(args.output_report, confirmation_rows, summary, validation_errors)
    confirmed = [row for row in confirmation_rows if is_confirmed(row)]
    print(json.dumps({
        "samples": len(confirmation_rows),
        "confirmed_samples": len(confirmed),
        "validation_errors": len(validation_errors),
        "confirmation_csv": str(args.confirmation_csv),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
