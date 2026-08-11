#!/usr/bin/env python3
"""Validate blinded human-audit review sheets before manual labeling."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


EXPECTED_COLUMNS = (
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
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
)

HUMAN_LABEL_COLUMNS = (
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        return [], []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str) -> str:
    return value.strip()


def audit_ids(rows: list[dict[str, str]]) -> list[str]:
    return [row.get("audit_id", "") for row in rows]


def review_orders(rows: list[dict[str, str]]) -> list[int]:
    orders: list[int] = []
    for row in rows:
        try:
            orders.append(int(row.get("review_order", "")))
        except ValueError:
            return []
    return orders


def filled_human_label_cells(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows for col in HUMAN_LABEL_COLUMNS if norm(row.get(col, "")))


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def check_scope(scope: str, path: Path, expected_rows: int) -> tuple[list[dict[str, Any]], set[str]]:
    header, rows = read_csv(path)
    ids = audit_ids(rows)
    orders = review_orders(rows)
    expected_orders = list(range(1, len(rows) + 1))
    leaked_columns = [col for col in header if col.startswith("llm_")]
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in header]
    extra_columns = [col for col in header if col not in EXPECTED_COLUMNS]
    duplicates = duplicate_values([item for item in ids if item])
    blank_ids = sum(1 for item in ids if not item)
    label_cells = filled_human_label_cells(rows)
    checks = [
        {
            "scope": scope,
            "check": "file_exists",
            "pass": path.exists(),
            "severity": "blocker",
            "evidence": str(path),
            "action": "Regenerate the blind review CSV from the confirmation sheet.",
        },
        {
            "scope": scope,
            "check": "expected_row_count",
            "pass": len(rows) == expected_rows,
            "severity": "blocker",
            "evidence": f"rows={len(rows)}, expected={expected_rows}",
            "action": "Regenerate the blind review sample with the expected scope size.",
        },
        {
            "scope": scope,
            "check": "no_llm_label_columns",
            "pass": not leaked_columns,
            "severity": "blocker",
            "evidence": ";".join(leaked_columns) if leaked_columns else "no llm_* columns",
            "action": "Remove llm_* fields from the blind review sheet before labeling.",
        },
        {
            "scope": scope,
            "check": "expected_columns_present",
            "pass": not missing_columns,
            "severity": "blocker",
            "evidence": ";".join(missing_columns) if missing_columns else "all expected columns present",
            "action": "Regenerate the blind review sheet with the standard schema.",
        },
        {
            "scope": scope,
            "check": "no_extra_columns",
            "pass": not extra_columns,
            "severity": "major",
            "evidence": ";".join(extra_columns) if extra_columns else "no extra columns",
            "action": "Remove non-protocol columns or document why they are needed.",
        },
        {
            "scope": scope,
            "check": "audit_id_unique_nonempty",
            "pass": not duplicates and blank_ids == 0,
            "severity": "blocker",
            "evidence": f"duplicates={duplicates[:10]}, blank_ids={blank_ids}",
            "action": "Regenerate the sheet so every row has one unique audit_id.",
        },
        {
            "scope": scope,
            "check": "review_order_contiguous",
            "pass": orders == expected_orders,
            "severity": "major",
            "evidence": f"first_orders={orders[:5]}, expected_len={len(expected_orders)}",
            "action": "Regenerate or sort the sheet so review_order is 1..N.",
        },
        {
            "scope": scope,
            "check": "human_labels_not_prefilled",
            "pass": label_cells == 0,
            "severity": "info",
            "evidence": f"filled_required_human_label_cells={label_cells}",
            "action": "If labels are already filled, this is not a leakage issue; run merge/agreement/readiness next.",
        },
    ]
    for row in checks:
        row["status"] = "pass" if row["pass"] else row["severity"]
    return checks, set(ids)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [row for row in rows if row["status"] == "blocker"]
    major = [row for row in rows if row["status"] == "major"]
    table_rows = [
        [row["scope"], row["check"], str(row["pass"]), row["severity"], row["evidence"], row["action"]]
        for row in rows
    ]
    lines = [
        "# Human Audit Blind Review Leakage Audit",
        "",
        "本文件检查 priority20/full80 盲审标注表是否适合交给人工标注者。它只验证表结构和泄露风险，不自动填写人工标签，也不把未标注样本写成人工结果。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major issues: {len(major)}",
        f"- Blind-review protocol safe: {len(blockers) == 0 and len(major) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Scope", "Check", "Pass", "Severity", "Evidence", "Action"], table_rows),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：人工复核使用不含 LLM 预标注列的盲审表，降低标注者被 LLM 标签锚定的风险。",
        "- 不能写：该检查等同于人工复核完成；最终仍以 agreement/readiness gate 为准。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate blinded human-audit sheets for leakage and schema issues.")
    parser.add_argument("--priority-csv", type=Path, required=True)
    parser.add_argument("--full-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    priority_rows, priority_ids = check_scope("priority20", args.priority_csv, expected_rows=20)
    full_rows, full_ids = check_scope("full80", args.full_csv, expected_rows=80)
    subset_check = {
        "scope": "cross_scope",
        "check": "priority20_subset_of_full80",
        "pass": priority_ids.issubset(full_ids),
        "severity": "major",
        "evidence": "missing=" + ";".join(sorted(priority_ids - full_ids)[:20]) if not priority_ids.issubset(full_ids) else "priority20 ids are included in full80",
        "action": "Regenerate priority20 from the full80 audit pool or explain the separate sample design.",
    }
    subset_check["status"] = "pass" if subset_check["pass"] else subset_check["severity"]
    rows = [*priority_rows, *full_rows, subset_check]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "blockers": sum(1 for row in rows if row["status"] == "blocker"),
        "major": sum(1 for row in rows if row["status"] == "major"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
