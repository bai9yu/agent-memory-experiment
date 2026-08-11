#!/usr/bin/env python3
"""Prepare and summarize dual-human audit agreement sheets."""

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
    "review_order",
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

DUAL_FIELDS = (
    *CONTEXT_FIELDS,
    "annotator_a_manual_reason",
    "annotator_a_auto_reason_correct",
    "annotator_a_top_memory_relevant",
    "annotator_a_gold_memory_sufficient",
    "annotator_a_notes",
    "annotator_b_manual_reason",
    "annotator_b_auto_reason_correct",
    "annotator_b_top_memory_relevant",
    "annotator_b_gold_memory_sufficient",
    "annotator_b_notes",
    "adjudicated_manual_reason",
    "adjudicated_auto_reason_correct",
    "adjudicated_top_memory_relevant",
    "adjudicated_gold_memory_sufficient",
    "adjudicator_notes",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...] = DUAL_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str) -> str:
    return value.strip().lower()


def prepare_rows(blind_rows: list[dict[str, str]], existing_rows: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    old_by_id = {row["audit_id"]: row for row in existing_rows or [] if row.get("audit_id")}
    out: list[dict[str, str]] = []
    for row in blind_rows:
        old = old_by_id.get(row.get("audit_id", ""), {})
        new_row: dict[str, str] = {}
        for field in CONTEXT_FIELDS:
            new_row[field] = row.get(field, "")
        for field in DUAL_FIELDS:
            if field in CONTEXT_FIELDS:
                continue
            new_row[field] = old.get(field, "")
        out.append(new_row)
    return out


def label_key(prefix: str, field: str) -> str:
    return f"{prefix}_{field}"


def has_all_labels(row: dict[str, str], prefix: str) -> bool:
    return all(norm(row.get(label_key(prefix, field), "")) for field in AUDIT_FIELDS)


def invalid_labels(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        audit_id = row.get("audit_id", "unknown")
        for prefix in ("annotator_a", "annotator_b", "adjudicated"):
            for field in AUDIT_FIELDS:
                key = label_key(prefix, field)
                value = norm(row.get(key, ""))
                if not value:
                    continue
                if value not in ALLOWED[field]:
                    errors.append(f"{audit_id}: {key}=`{row.get(key, '')}`; allowed={','.join(ALLOWED[field])}")
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


def summarize(rows: list[dict[str, str]], errors: list[str]) -> list[dict[str, Any]]:
    both_labeled = [row for row in rows if has_all_labels(row, "annotator_a") and has_all_labels(row, "annotator_b")]
    adjudicated = [row for row in rows if has_all_labels(row, "adjudicated")]
    summary: list[dict[str, Any]] = [
        {"group": "overview", "label": "samples", "value": "total", "count": len(rows), "total": len(rows), "share": 1.0 if rows else 0.0, "kappa": ""},
        {"group": "overview", "label": "both_labeled", "value": "complete_a_b", "count": len(both_labeled), "total": len(rows), "share": len(both_labeled) / len(rows) if rows else 0.0, "kappa": ""},
        {"group": "overview", "label": "adjudicated", "value": "complete_adjudication", "count": len(adjudicated), "total": len(rows), "share": len(adjudicated) / len(rows) if rows else 0.0, "kappa": ""},
        {"group": "overview", "label": "validation_errors", "value": "invalid_labels", "count": len(errors), "total": len(rows), "share": 0.0, "kappa": ""},
    ]
    for field in AUDIT_FIELDS:
        pairs = [(norm(row[label_key("annotator_a", field)]), norm(row[label_key("annotator_b", field)])) for row in both_labeled]
        exact = sum(1 for left, right in pairs if left == right)
        partial_credit = 0.0
        conflicts = 0
        for left, right in pairs:
            if left == right:
                partial_credit += 1.0
            else:
                conflicts += 1
                if "partial" in {left, right}:
                    partial_credit += 0.5
        summary.append({
            "group": "inter_annotator",
            "label": field,
            "value": "exact",
            "count": exact,
            "total": len(pairs),
            "share": exact / len(pairs) if pairs else 0.0,
            "kappa": cohen_kappa(pairs, ALLOWED[field]),
        })
        summary.append({
            "group": "inter_annotator",
            "label": field,
            "value": "partial_credit",
            "count": partial_credit,
            "total": len(pairs),
            "share": partial_credit / len(pairs) if pairs else 0.0,
            "kappa": "",
        })
        summary.append({
            "group": "inter_annotator",
            "label": field,
            "value": "conflict",
            "count": conflicts,
            "total": len(pairs),
            "share": conflicts / len(pairs) if pairs else 0.0,
            "kappa": "",
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


def fmt(value: Any) -> str:
    if value in ("", None):
        return ""
    return f"{float(value):.3f}"


def missing_examples(rows: list[dict[str, str]], prefix: str, limit: int = 20) -> list[str]:
    examples: list[str] = []
    for row in rows:
        missing = [label_key(prefix, field) for field in AUDIT_FIELDS if not norm(row.get(label_key(prefix, field), ""))]
        if missing:
            examples.append(f"{row.get('audit_id', 'unknown')}({','.join(missing)})")
        if len(examples) >= limit:
            break
    return examples


def write_report(path: Path, rows: list[dict[str, str]], summary: list[dict[str, Any]], errors: list[str], scope: str) -> None:
    both = next(row for row in summary if row["group"] == "overview" and row["label"] == "both_labeled")
    adjudicated = next(row for row in summary if row["group"] == "overview" and row["label"] == "adjudicated")
    status = "ready_for_inter_annotator_analysis" if both["count"] == len(rows) and rows and not errors else "pending_dual_human_labels"
    if status == "ready_for_inter_annotator_analysis" and adjudicated["count"] == len(rows):
        status = "ready_with_adjudication"
    agreement_rows = [row for row in summary if row["group"] == "inter_annotator"]
    lines = [
        f"# {scope} 双人 Human Audit Agreement",
        "",
        "本文件用于把 retrieval error audit 从单人确认升级为双人独立标注与仲裁流程。它只统计人工字段，不使用 LLM-assisted 预标注作为人工结果。",
        "",
        "## 状态",
        "",
        f"- 状态：`{status}`",
        f"- 样本数：{len(rows)}",
        f"- A/B 均完成的样本数：{both['count']}/{len(rows)}",
        f"- 已仲裁样本数：{adjudicated['count']}/{len(rows)}",
        f"- 非法标签数：{len(errors)}",
        "",
        "## A/B 一致性指标",
        "",
        markdown_table(
            ["Field", "Metric", "Count", "Total", "Rate", "Cohen Kappa"],
            [[row["label"], row["value"], str(row["count"]), str(row["total"]), fmt(row["share"]), fmt(row["kappa"])] for row in agreement_rows],
        ),
        "",
        "## 标注规则",
        "",
        "- `annotator_a_*` 与 `annotator_b_*` 由两名标注者独立填写，不参考彼此结果。",
        "- `auto_reason_correct` / `top_memory_relevant` 允许：`yes`、`partial`、`no`。",
        "- `gold_memory_sufficient` 允许：`yes`、`no`、`unclear`。",
        "- A/B 冲突样本再填写 `adjudicated_*` 字段；论文主错误类型分布优先使用 adjudicated labels。",
        "",
        "## 待填写样例",
        "",
        "### Annotator A",
    ]
    a_missing = missing_examples(rows, "annotator_a")
    lines.extend([f"- {item}" for item in a_missing] if a_missing else ["- 无缺失。"])
    lines.extend(["", "### Annotator B"])
    b_missing = missing_examples(rows, "annotator_b")
    lines.extend([f"- {item}" for item in b_missing] if b_missing else ["- 无缺失。"])
    if errors:
        lines.extend(["", "## 非法标签样例"])
        lines.extend([f"- {item}" for item in errors[:20]])
    lines.extend([
        "",
        "## 论文使用判断",
        "",
        "- A/B 均完成后，可以报告 inter-annotator exact agreement 与 Cohen's kappa。",
        "- 仲裁完成后，可以把 adjudicated labels 作为论文错误分析的人工确认结果。",
        "- 在人工字段未完成前，本文件只能证明双人标注流程已准备好，不能宣称人工一致性已完成。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare and summarize dual-human audit agreement sheets.")
    parser.add_argument("--scope", required=True)
    parser.add_argument("--blind-csv", type=Path, required=True)
    parser.add_argument("--dual-csv", type=Path, required=True)
    parser.add_argument("--summary-csv", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    blind_rows = read_csv(args.blind_csv)
    existing_rows = read_csv(args.dual_csv) if args.dual_csv.exists() else []
    rows = prepare_rows(blind_rows, existing_rows)
    errors = invalid_labels(rows)
    summary = summarize(rows, errors)
    write_csv(args.dual_csv, rows)
    write_csv(args.summary_csv, summary, fieldnames=("group", "label", "value", "count", "total", "share", "kappa"))
    write_report(args.report, rows, summary, errors, args.scope)
    both = next(row for row in summary if row["group"] == "overview" and row["label"] == "both_labeled")
    print(json.dumps({
        "scope": args.scope,
        "samples": len(rows),
        "both_labeled": both["count"],
        "validation_errors": len(errors),
        "dual_csv": str(args.dual_csv),
        "report": str(args.report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
