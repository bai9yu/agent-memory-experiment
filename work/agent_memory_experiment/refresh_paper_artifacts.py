#!/usr/bin/env python3
"""Refresh paper-facing artifacts from cached/offline experiment outputs."""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Step:
    name: str
    args: list[str]
    notes: str


def py(script: str, *args: str) -> list[str]:
    return [sys.executable, f"work/agent_memory_experiment/{script}", *args]


def build_steps(include_environment: bool) -> list[Step]:
    steps = [
        Step(
            "offline_embedding_sensitivity",
            py(
                "generate_offline_embedding_sensitivity.py",
                "--bge-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv",
                "--hash-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_hash_type_004_with_keyword/summary.csv",
                "--output-csv",
                "outputs/agent_memory_offline_embedding_sensitivity.csv",
                "--output-report",
                "outputs/agent_memory_offline_embedding_sensitivity_zh.md",
            ),
            "Refreshes offline hash/BM25 vs BGE-M3 encoder-sensitivity diagnostics.",
        ),
        Step(
            "human_audit_execution_plan",
            py(
                "generate_human_audit_execution_plan.py",
                "--outputs-dir",
                "outputs",
                "--output-report",
                "outputs/agent_memory_human_audit_execution_plan_zh.md",
                "--output-csv",
                "outputs/agent_memory_human_audit_execution_plan.csv",
            ),
            "Refreshes the human-audit labeling execution plan from current gates.",
        ),
        Step(
            "submission_blocker_closure_plan",
            py(
                "generate_submission_blocker_closure_plan.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_submission_blocker_closure_plan.csv",
                "--output-report",
                "outputs/agent_memory_submission_blocker_closure_plan_zh.md",
            ),
            "Refreshes the ordered closure path for final-submission blockers.",
        ),
        Step(
            "submission_package_index",
            py(
                "generate_submission_package_index.py",
                "--project-root",
                ".",
                "--output-report",
                "outputs/agent_memory_submission_package_index_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_package_index.csv",
            ),
            "Refreshes the index of manuscript, tables, appendices, gates, and packaging actions.",
        ),
    ]
    if include_environment:
        steps.extend([
            Step(
                "environment_snapshot",
                py(
                    "generate_environment_snapshot.py",
                    "--project-root",
                    ".",
                    "--output-report",
                    "outputs/agent_memory_environment_snapshot_zh.md",
                    "--output-packages",
                    "outputs/agent_memory_environment_packages.csv",
                    "--output-system",
                    "outputs/agent_memory_environment_system.csv",
                ),
                "Refreshes Python/package/cache/Git environment snapshot using the current Python executable.",
            ),
            Step(
                "environment_freshness",
                py(
                    "validate_environment_snapshot_freshness.py",
                    "--project-root",
                    ".",
                    "--system-csv",
                    "outputs/agent_memory_environment_system.csv",
                    "--output-csv",
                    "outputs/agent_memory_environment_freshness_audit.csv",
                    "--output-report",
                    "outputs/agent_memory_environment_freshness_audit_zh.md",
                ),
                "Checks generation-time environment snapshot freshness.",
            ),
        ])
    steps.extend([
        Step(
            "reproducibility_checklist",
            py(
                "generate_reproducibility_checklist.py",
                "--output-report",
                "outputs/agent_memory_reproducibility_checklist_zh.md",
                "--output-artifacts",
                "outputs/agent_memory_reproducibility_artifacts.csv",
                "--output-metrics",
                "outputs/agent_memory_reproducibility_metrics.csv",
            ),
            "Refreshes artifact and metric gates.",
        ),
        Step(
            "artifact_integrity_manifest",
            py(
                "generate_artifact_integrity_manifest.py",
                "--output-report",
                "outputs/agent_memory_artifact_integrity_manifest_zh.md",
                "--output-csv",
                "outputs/agent_memory_artifact_integrity_manifest.csv",
                "--artifact-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
            ),
            "Refreshes artifact sha256/size/line-count manifest.",
        ),
        Step(
            "evidence_matrix",
            py(
                "generate_evidence_matrix.py",
                "--output-report",
                "outputs/agent_memory_paper_evidence_matrix_zh.md",
                "--output-csv",
                "outputs/agent_memory_paper_evidence_matrix.csv",
            ),
            "Refreshes paper claim/evidence/gap matrix.",
        ),
        Step(
            "submission_gap_analysis",
            py(
                "generate_submission_gap_analysis.py",
                "--output-report",
                "outputs/agent_memory_submission_gap_analysis_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_gap_analysis.csv",
            ),
            "Refreshes reviewer-facing risk matrix.",
        ),
        Step(
            "submission_readiness",
            py(
                "validate_submission_readiness.py",
                "--output-report",
                "outputs/agent_memory_submission_readiness_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_readiness.csv",
            ),
            "Refreshes final-submission gates.",
        ),
        Step(
            "reviewer_response_prep",
            py(
                "generate_reviewer_response_prep.py",
                "--output-report",
                "outputs/agent_memory_reviewer_response_prep_zh.md",
                "--output-csv",
                "outputs/agent_memory_reviewer_response_prep.csv",
            ),
            "Refreshes reviewer question/answer preparation matrix.",
        ),
        Step(
            "paper_manuscript",
            py(
                "generate_paper_manuscript.py",
                "--project-root",
                ".",
                "--output-report",
                "outputs/agent_memory_manuscript_draft_zh.md",
            ),
            "Refreshes Chinese manuscript draft from current evidence.",
        ),
        Step(
            "manuscript_claim_check",
            py(
                "validate_manuscript_claims.py",
                "--manuscript",
                "outputs/agent_memory_manuscript_draft_zh.md",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_manuscript_claim_check.csv",
                "--output-report",
                "outputs/agent_memory_manuscript_claim_check_zh.md",
            ),
            "Checks that manuscript does not overclaim pending baselines/audits.",
        ),
        Step(
            "evidence_freshness",
            py(
                "validate_evidence_freshness.py",
                "--output-csv",
                "outputs/agent_memory_evidence_freshness_audit.csv",
                "--output-report",
                "outputs/agent_memory_evidence_freshness_audit_zh.md",
            ),
            "Checks stale artifact/metric/integrity gate counts.",
        ),
        Step(
            "artifact_integrity_manifest_final",
            py(
                "generate_artifact_integrity_manifest.py",
                "--output-report",
                "outputs/agent_memory_artifact_integrity_manifest_zh.md",
                "--output-csv",
                "outputs/agent_memory_artifact_integrity_manifest.csv",
                "--artifact-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
            ),
            "Final manifest refresh after freshness audit changes.",
        ),
        Step(
            "submission_readiness_final",
            py(
                "validate_submission_readiness.py",
                "--output-report",
                "outputs/agent_memory_submission_readiness_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_readiness.csv",
            ),
            "Final submission gate refresh after manifest changes.",
        ),
    ])
    return steps


def command_string(args: list[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in args)


def run_step(step: Step, cwd: Path, dry_run: bool) -> dict[str, Any]:
    start = time.time()
    row: dict[str, Any] = {
        "step": step.name,
        "command": command_string(step.args),
        "notes": step.notes,
        "status": "dry_run" if dry_run else "pending",
        "returncode": "",
        "duration_sec": "0.000",
    }
    if dry_run:
        return row
    result = subprocess.run(step.args, cwd=cwd, text=True, capture_output=True)
    row["returncode"] = result.returncode
    row["duration_sec"] = f"{time.time() - start:.3f}"
    row["status"] = "pass" if result.returncode == 0 else "fail"
    if result.stdout.strip():
        row["stdout_tail"] = result.stdout.strip().splitlines()[-1][:500]
    else:
        row["stdout_tail"] = ""
    if result.stderr.strip():
        row["stderr_tail"] = result.stderr.strip().splitlines()[-1][:500]
    else:
        row["stderr_tail"] = ""
    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {step.name}\n{result.stderr}\n{result.stdout}")
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step", "status", "returncode", "duration_sec", "notes", "command", "stdout_tail", "stderr_tail"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], include_environment: bool, dry_run: bool) -> None:
    failures = [row for row in rows if row["status"] == "fail"]
    table = [
        [row["step"], row["status"], str(row.get("returncode", "")), str(row["duration_sec"]), row["notes"]]
        for row in rows
    ]
    lines = [
        "# Paper Artifact Refresh Run",
        "",
        "本文件记录一次论文 artifact 离线刷新流水线的执行结果。该流水线只调用本地已缓存结果和无网络脚本；不会运行真实外部 embedding API，也不会自动填写人工标签。",
        "",
        "## 总览",
        "",
        f"- Dry run: {dry_run}",
        f"- Include environment snapshot: {include_environment}",
        f"- Steps: {len(rows)}",
        f"- Failures: {len(failures)}",
        "",
        "## Step Results",
        "",
        markdown_table(["Step", "Status", "Return Code", "Duration Sec", "Notes"], table),
        "",
        "## 使用边界",
        "",
        "- 可以用于补完 API baseline 或人工标签后的最终报告刷新。",
        "- 不能替代真实外部 embedding baseline，也不能替代人工审计填写。",
        "- 如果刷新后 artifact 数变化，应再次运行 freshness audit 并检查 submission readiness。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh paper-facing artifacts from cached/offline outputs.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--include-environment", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_paper_artifact_refresh_run.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_paper_artifact_refresh_run_zh.md"))
    args = parser.parse_args()

    rows = []
    for step in build_steps(args.include_environment):
        rows.append(run_step(step, args.project_root, args.dry_run))
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.include_environment, args.dry_run)
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "steps": len(rows),
        "failures": sum(1 for row in rows if row["status"] == "fail"),
        "dry_run": args.dry_run,
    })


if __name__ == "__main__":
    main()
