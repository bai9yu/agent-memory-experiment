#!/usr/bin/env python3
"""Validate generated human-audit annotation HTML interfaces."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


HUMAN_FIELDS = {
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
}

FORBIDDEN_TOKENS = {
    "llm_manual_reason",
    "llm_auto_reason_correct",
    "llm_top_memory_relevant",
    "llm_gold_memory_sufficient",
    "llm_auditor_notes",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def extract_embedded_rows(html_text: str) -> list[dict[str, Any]]:
    match = re.search(r"const rows = (\[.*?\]);\n\s+const outputFilename", html_text, flags=re.S)
    if not match:
        return []
    return json.loads(match.group(1))


def check_interface(scope: str, source_csv: Path, html_path: Path) -> list[dict[str, Any]]:
    source_rows = read_csv(source_csv)
    html_text = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
    embedded_rows = extract_embedded_rows(html_text) if html_text else []
    source_ids = [row.get("audit_id", "") for row in source_rows]
    embedded_ids = [str(row.get("audit_id", "")) for row in embedded_rows]
    forbidden_hits = sorted(token for token in FORBIDDEN_TOKENS if token in html_text)
    missing_human_fields = sorted(field for field in HUMAN_FIELDS if field not in html_text)
    checks = [
        {
            "scope": scope,
            "check": "html_exists",
            "pass": html_path.exists() and html_path.stat().st_size > 0,
            "severity": "blocker",
            "evidence": f"{html_path}, size={html_path.stat().st_size if html_path.exists() else 0}",
            "action": "Regenerate annotation interface HTML.",
        },
        {
            "scope": scope,
            "check": "embedded_rows_parseable",
            "pass": bool(embedded_rows),
            "severity": "blocker",
            "evidence": f"embedded_rows={len(embedded_rows)}",
            "action": "Fix HTML generator so embedded row JSON is parseable.",
        },
        {
            "scope": scope,
            "check": "row_count_matches_source",
            "pass": len(source_rows) == len(embedded_rows),
            "severity": "blocker",
            "evidence": f"source_rows={len(source_rows)}, embedded_rows={len(embedded_rows)}",
            "action": "Regenerate HTML from the current blind review CSV.",
        },
        {
            "scope": scope,
            "check": "audit_id_order_matches_source",
            "pass": source_ids == embedded_ids,
            "severity": "major",
            "evidence": f"first_source_ids={source_ids[:3]}, first_embedded_ids={embedded_ids[:3]}",
            "action": "Regenerate HTML without reordering or dropping review rows.",
        },
        {
            "scope": scope,
            "check": "no_llm_assisted_label_tokens",
            "pass": not forbidden_hits,
            "severity": "blocker",
            "evidence": ";".join(forbidden_hits) if forbidden_hits else "no forbidden llm label tokens",
            "action": "Remove LLM-assisted label fields from the annotation interface.",
        },
        {
            "scope": scope,
            "check": "human_fields_present",
            "pass": not missing_human_fields,
            "severity": "blocker",
            "evidence": ";".join(missing_human_fields) if missing_human_fields else "all human fields present",
            "action": "Regenerate HTML with all required human_* form fields.",
        },
        {
            "scope": scope,
            "check": "download_button_present",
            "pass": "downloadCsv()" in html_text and "导出 CSV" in html_text,
            "severity": "major",
            "evidence": "downloadCsv and export button present" if "downloadCsv()" in html_text else "download control missing",
            "action": "Regenerate HTML with an export/download control.",
        },
    ]
    for row in checks:
        row["status"] = "pass" if row["pass"] else row["severity"]
    return checks


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
    table = [
        [row["scope"], row["check"], str(row["pass"]), row["severity"], row["evidence"], row["action"]]
        for row in rows
    ]
    lines = [
        "# Human Audit Annotation Interface Validation",
        "",
        "本文件检查离线 HTML 标注界面是否和盲审 CSV 同步，是否保留必要 human_* 字段，以及是否没有泄漏 LLM-assisted 预标注字段。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major issues: {len(major)}",
        f"- Annotation interface safe: {len(blockers) == 0 and len(major) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Scope", "Check", "Pass", "Severity", "Evidence", "Action"], table),
        "",
        "## 使用边界",
        "",
        "- 可以写：HTML 标注界面与当前盲审表同步，且未暴露 LLM-assisted 预标注字段。",
        "- 不能写：该校验通过就表示人工标注已完成；它只证明标注入口可用。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate generated human audit annotation interfaces.")
    parser.add_argument("--priority-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--full-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--priority-html", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_annotation.html"))
    parser.add_argument("--full-html", type=Path, default=Path("outputs/agent_memory_human_audit_full80_annotation.html"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_interface_validation.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_interface_validation_zh.md"))
    args = parser.parse_args()

    rows = []
    rows.extend(check_interface("priority20", args.priority_csv, args.priority_html))
    rows.extend(check_interface("full80", args.full_csv, args.full_html))
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    blockers = sum(1 for row in rows if row["status"] == "blocker")
    major = sum(1 for row in rows if row["status"] == "major")
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "checks": len(rows),
        "blockers": blockers,
        "major": major,
        "safe": blockers == 0 and major == 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
