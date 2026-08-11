#!/usr/bin/env python3
"""Validate that submission-readiness entrypoints point to the current gate artifact."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


CURRENT_REPORT = "outputs/agent_memory_submission_readiness_zh.md"
CURRENT_CSV = "outputs/agent_memory_submission_readiness.csv"
LEGACY_REPORT = "outputs/agent_memory_submission_readiness_gate_zh.md"
LEGACY_CSV = "outputs/agent_memory_submission_readiness_gate.csv"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def check_row(check: str, passed: bool, severity: str, evidence: str, action: str) -> dict[str, Any]:
    return {
        "check": check,
        "pass": passed,
        "severity": severity,
        "status": "pass" if passed else severity,
        "evidence": evidence,
        "action": action,
    }


def extract_summary(report_text: str) -> tuple[str, str]:
    gates = ""
    blockers = ""
    for line in report_text.splitlines():
        if line.startswith("- Required gates passed:"):
            gates = line.split(":", 1)[1].strip()
        if line.startswith("- Blockers:"):
            blockers = line.split(":", 1)[1].strip()
    return gates, blockers


def legacy_refs(root: Path) -> list[str]:
    files = [
        root / "README.md",
        root / "work" / "agent_memory_experiment" / "README.md",
        root / "outputs" / "agent_memory_submission_package_index_zh.md",
        root / "outputs" / "agent_memory_submission_package_index.csv",
        root / "outputs" / "agent_memory_reproducibility_checklist_zh.md",
        root / "outputs" / "agent_memory_reproducibility_artifacts.csv",
        root / "outputs" / "agent_memory_reviewer_response_prep_zh.md",
        root / "outputs" / "agent_memory_reviewer_response_prep.csv",
    ]
    hits: list[str] = []
    pattern = re.compile(r"agent_memory_submission_readiness_gate(?:_zh\.md|\.csv)")
    for path in files:
        text = read_text(path)
        for line_no, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{path.relative_to(root)}:{line_no}:{line.strip()}")
    return hits


def build_rows(root: Path) -> list[dict[str, Any]]:
    outputs = root / "outputs"
    current_report = root / CURRENT_REPORT
    current_csv = root / CURRENT_CSV
    report_text = read_text(current_report)
    gate_rows = read_csv(current_csv)
    gates, blockers = extract_summary(report_text)
    blockers_from_csv = sum(1 for row in gate_rows if row.get("status") == "blocker")
    legacy_hits = legacy_refs(root)
    rows = [
        check_row(
            "current_report_exists",
            current_report.exists(),
            "blocker",
            CURRENT_REPORT,
            "Regenerate validate_submission_readiness.py with --output-report outputs/agent_memory_submission_readiness_zh.md.",
        ),
        check_row(
            "current_csv_exists",
            current_csv.exists(),
            "blocker",
            CURRENT_CSV,
            "Regenerate validate_submission_readiness.py with --output-csv outputs/agent_memory_submission_readiness.csv.",
        ),
        check_row(
            "legacy_report_absent",
            not (root / LEGACY_REPORT).exists(),
            "major",
            LEGACY_REPORT,
            "Remove stale legacy readiness report from tracked artifacts.",
        ),
        check_row(
            "legacy_csv_absent",
            not (root / LEGACY_CSV).exists(),
            "major",
            LEGACY_CSV,
            "Remove stale legacy readiness CSV from tracked artifacts.",
        ),
        check_row(
            "readme_links_current_report",
            CURRENT_REPORT in read_text(root / "README.md"),
            "major",
            "README.md",
            "Update the root README paper artifact list to point to the current readiness report.",
        ),
        check_row(
            "work_readme_links_current_report",
            CURRENT_REPORT in read_text(root / "work" / "agent_memory_experiment" / "README.md"),
            "major",
            "work/agent_memory_experiment/README.md",
            "Update the experiment README submission command and artifact list.",
        ),
        check_row(
            "no_legacy_entrypoint_refs",
            not legacy_hits,
            "major",
            "; ".join(legacy_hits[:5]) if legacy_hits else "no legacy references found",
            "Replace legacy submission_readiness_gate references with submission_readiness references.",
        ),
        check_row(
            "report_csv_blocker_count_consistent",
            bool(blockers) and blockers == str(blockers_from_csv),
            "blocker",
            f"report_blockers={blockers or 'missing'}, csv_blockers={blockers_from_csv}",
            "Regenerate submission readiness report and CSV together.",
        ),
        check_row(
            "report_required_gate_count_present",
            bool(gates),
            "major",
            f"required_gates={gates or 'missing'}",
            "Ensure submission readiness report contains Required gates passed summary.",
        ),
    ]
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    failures = [row for row in rows if row["status"] != "pass"]
    table_rows = [[row["check"], str(row["pass"]), row["severity"], row["evidence"], row["action"]] for row in rows]
    lines = [
        "# Submission Entrypoint Consistency Audit",
        "",
        "本文件检查最终投稿门禁的入口是否唯一且指向当前 artifact，避免旧的 `submission_readiness_gate` 报告与当前 `submission_readiness` 报告并存造成读者误读。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Failures: {len(failures)}",
        f"- Entrypoints consistent: {len(failures) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Check", "Pass", "Severity", "Evidence", "Action"], table_rows),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：最终投稿门禁入口已统一到当前 readiness artifact。",
        "- 不能写：该检查解除外部 embedding 或人工审计 blocker；它只处理入口一致性。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate submission readiness entrypoint consistency.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "failures": sum(1 for row in rows if row["status"] != "pass"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
