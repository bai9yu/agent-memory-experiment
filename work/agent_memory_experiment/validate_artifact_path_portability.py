#!/usr/bin/env python3
"""Audit paper-facing artifacts for machine-local absolute paths."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any


LOCAL_PATH_PATTERNS = (
    re.compile(r"/Users/[^`\s,;\")]+"),
    re.compile(r"/private/var/[^`\s,;\")]+"),
    re.compile(r"/var/folders/[^`\s,;\")]+"),
    re.compile(r"Documents/Codex"),
    re.compile(r"referenced-chatgpt-conversation-this-is-an"),
)

SCAN_SUFFIXES = {".md", ".csv", ".tex"}
SCAN_ROOTS = ("outputs/", "README.md", "work/agent_memory_experiment/README.md")
EXCLUDED_FILES = {
    # This file is produced at the end of refresh_paper_artifacts.py; command
    # portability is handled directly by that generator.
    "outputs/agent_memory_paper_artifact_refresh_run.csv",
}


def git_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def should_scan(rel: str) -> bool:
    if rel in EXCLUDED_FILES:
        return False
    path = Path(rel)
    if path.suffix not in SCAN_SUFFIXES:
        return False
    return rel.startswith(SCAN_ROOTS)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None


def build_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rel in git_files(root):
        if not should_scan(rel):
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            hits = [pattern.pattern for pattern in LOCAL_PATH_PATTERNS if pattern.search(line)]
            if hits:
                rows.append({
                    "status": "finding",
                    "path": rel,
                    "line": line_no,
                    "matched_patterns": ";".join(hits),
                    "evidence": line[:240],
                    "action": "Replace machine-local absolute path with a repository-relative path or a documented placeholder.",
                })
    if not rows:
        rows.append({
            "status": "pass",
            "path": "",
            "line": "",
            "matched_patterns": "",
            "evidence": "No machine-local absolute paths found in scanned tracked paper-facing artifacts.",
            "action": "Keep this audit in the refresh pipeline before sharing public artifacts.",
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    findings = [row for row in rows if row["status"] == "finding"]
    table = [
        [row["status"], row["path"], str(row["line"]), row["evidence"], row["action"]]
        for row in rows
    ]
    lines = [
        "# Artifact Path Portability Audit",
        "",
        "本文件检查论文和复现相关公开 artifact 中是否残留本机绝对路径。目标是让报告可以公开分享，并让他人在不同机器上按相对路径复现。",
        "",
        "## 总览",
        "",
        f"- Findings: {len(findings)}",
        f"- Portable: {len(findings) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Status", "Path", "Line", "Evidence", "Action"], table),
        "",
        "## 论文使用判断",
        "",
        "- findings=0 时，可以说明当前公开 artifact 没有暴露本机工作目录。",
        "- 该检查不扫描 `.env`，密钥泄露仍由 public release readiness gate 单独负责。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit tracked paper-facing artifacts for local absolute paths.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_artifact_path_portability.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_artifact_path_portability_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    findings = sum(1 for row in rows if row["status"] == "finding")
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "findings": findings,
        "portable": findings == 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
