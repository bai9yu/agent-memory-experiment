#!/usr/bin/env python3
"""Validate that the environment snapshot matches the source state at generation time."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Any


def run_text(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def value(rows: list[dict[str, str]], key: str) -> str:
    for row in rows:
        if row.get("key") == key:
            return row.get("value", "")
    return ""


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def build_rows(root: Path, system_csv: Path) -> list[dict[str, Any]]:
    system_rows = read_csv(system_csv)
    snapshot_commit = value(system_rows, "git_commit")
    snapshot_branch = value(system_rows, "git_branch_status")
    current_commit = run_text(["git", "rev-parse", "--short", "HEAD"], root)
    current_branch = run_text(["git", "status", "--short", "--branch"], root).splitlines()[0]
    distance = run_text(["git", "rev-list", "--count", f"{snapshot_commit}..HEAD"], root) if snapshot_commit else "unavailable"
    same_commit = snapshot_commit == current_commit
    same_branch = snapshot_branch == current_branch
    return [
        {
            "check": "snapshot_system_csv_exists",
            "pass": str(system_csv.exists()),
            "observed": str(system_csv),
            "expected": "existing environment system CSV",
            "severity": "required",
        },
        {
            "check": "git_commit_matches_generation_head",
            "pass": str(same_commit),
            "observed": snapshot_commit,
            "expected": current_commit,
            "severity": "advisory_after_commit",
        },
        {
            "check": "git_branch_status_matches_generation_status",
            "pass": str(same_branch),
            "observed": snapshot_branch,
            "expected": current_branch,
            "severity": "advisory_after_commit",
        },
        {
            "check": "commits_since_snapshot_generation",
            "pass": str(distance in {"0", "1"}),
            "observed": distance,
            "expected": "0 during generation; 1 is normal after committing the refreshed snapshot",
            "severity": "advisory_after_commit",
        },
    ]


def write_report(path: Path, rows: list[dict[str, Any]], system_csv: Path) -> None:
    failures = [row for row in rows if row["pass"] != "True" and row["severity"] == "required"]
    advisory = [row for row in rows if row["pass"] != "True" and row["severity"] != "required"]
    table_rows = [
        [row["check"], row["pass"], row["severity"], row["observed"], row["expected"]]
        for row in rows
    ]
    lines = [
        "# Environment Snapshot Freshness Audit",
        "",
        "本文件检查环境快照是否对应当前实验源状态。由于环境快照被提交后，最终提交号会天然比生成时的 HEAD 晚一个提交，所以 commit/branch 匹配项标为 advisory；真正的 required gate 是环境 system CSV 存在且字段可读。",
        "",
        "## 总览",
        "",
        f"- Required failures: {len(failures)}",
        f"- Advisory mismatches: {len(advisory)}",
        f"- System CSV: `{system_csv}`",
        "",
        "## 检查项",
        "",
        markdown_table(["Check", "Pass", "Severity", "Observed", "Expected"], table_rows),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：环境快照记录了生成报告时的 Python/package/cache/Git source state。",
        "- 应谨慎：提交后的 Git commit 可能比快照中的 generation commit 晚一个提交。",
        "- 不能写：环境快照中的 commit 必然等于包含该快照文件的最终 commit。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate environment snapshot freshness.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--system-csv", type=Path, default=Path("outputs/agent_memory_environment_system.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_environment_freshness_audit.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_environment_freshness_audit_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.system_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.system_csv)
    print({
        "output_report": str(args.output_report),
        "required_failures": sum(1 for row in rows if row["pass"] != "True" and row["severity"] == "required"),
        "advisory_mismatches": sum(1 for row in rows if row["pass"] != "True" and row["severity"] != "required"),
    })


if __name__ == "__main__":
    main()
