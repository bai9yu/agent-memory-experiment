#!/usr/bin/env python3
"""Audit untracked files that should not accidentally enter the public artifact package."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path
from typing import Any


def run_git_status(root: Path) -> list[str]:
    result = subprocess.run(["git", "status", "--porcelain=v1"], cwd=root, check=True, capture_output=True, text=True)
    return [line[3:] for line in result.stdout.splitlines() if line.startswith("?? ")]


def classify(path: str) -> tuple[str, str, str]:
    if path in {
        "work/agent_memory_experiment/audit_untracked_artifacts.py",
        "work/agent_memory_experiment/validate_api_embedding_postrun.py",
        "outputs/agent_memory_untracked_artifact_audit.csv",
        "outputs/agent_memory_untracked_artifact_audit_zh.md",
        "outputs/agent_memory_api_embedding_postrun_gate.csv",
        "outputs/agent_memory_api_embedding_postrun_gate_zh.md",
    }:
        return ("release_audit_artifact", "track_as_paper_artifact", "New public-release audit support file; track with the paper artifact package.")
    if path.startswith("work/agent_memory_experiment/data/deepseek_smoke_test/"):
        return ("local_smoke_test_data", "keep_untracked", "DeepSeek smoke-test cache/output should stay local unless explicitly anonymized and documented.")
    if path.startswith("work/agent_memory_experiment/data/llm_extracted_locomo_1s_v2"):
        return ("intermediate_llm_extraction_slice", "keep_untracked", "Intermediate one-session extraction slice; not part of current LoCoMo10 paper package.")
    if path.startswith("work/agent_memory_experiment/data/locomo_observation"):
        return ("intermediate_observation_slice", "keep_untracked", "Intermediate observation conversion slice; not part of tracked paper artifact set.")
    if path.startswith("outputs/agent_memory_candidate_reranker_") or path.startswith("outputs/agent_memory_set_selection"):
        return ("exploratory_candidate_output", "review_before_tracking", "Exploratory ranking/selection output; add only if promoted to a named paper artifact and indexed.")
    if path.startswith("outputs/agent_memory_error_analysis_") or path.startswith("outputs/agent_memory_multi_evidence_"):
        return ("exploratory_error_analysis_output", "review_before_tracking", "Exploratory error/coverage output; add only with provenance, generator command, and claim boundary.")
    return ("unknown_untracked", "review_before_tracking", "Classify before committing or releasing.")


def file_size(root: Path, rel: str) -> int:
    path = root / rel
    if path.is_dir():
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    if path.exists():
        return path.stat().st_size
    return 0


def build_rows(root: Path) -> list[dict[str, Any]]:
    rows = []
    for rel in run_git_status(root):
        category, recommendation, reason = classify(rel)
        rows.append({
            "path": rel,
            "category": category,
            "recommendation": recommendation,
            "size_bytes": file_size(root, rel),
            "reason": reason,
        })
    rows.sort(key=lambda row: (row["category"], row["path"]))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["path", "category", "recommendation", "size_bytes", "reason"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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
    review = [row for row in rows if row["recommendation"] == "review_before_tracking"]
    keep_local = [row for row in rows if row["recommendation"] == "keep_untracked"]
    track = [row for row in rows if row["recommendation"] == "track_as_paper_artifact"]
    table_rows = [
        [row["path"], row["category"], row["recommendation"], str(row["size_bytes"]), row["reason"]]
        for row in rows
    ]
    lines = [
        "# Untracked Artifact Audit",
        "",
        "本文件审计当前工作树中的未跟踪文件，防止探索性输出、临时数据切片或 API smoke-test 结果误进入公开仓库或论文 artifact 包。它不删除文件，也不把这些文件自动加入 Git。",
        "",
        "## 总览",
        "",
        f"- Untracked entries: {len(rows)}",
        f"- Track as paper artifact: {len(track)}",
        f"- Review before tracking: {len(review)}",
        f"- Keep untracked/local: {len(keep_local)}",
        "",
        "## 明细",
        "",
        markdown_table(["Path", "Category", "Recommendation", "Size Bytes", "Reason"], table_rows) if rows else "当前没有未跟踪文件。",
        "",
        "## 使用边界",
        "",
        "- 可以写：公开发布前已经审计未跟踪文件，避免把本地临时数据误作为论文 artifact。",
        "- 可以写：`track_as_paper_artifact` 文件属于本轮新增的公开发布审计支撑文件，提交后不再计入未跟踪风险。",
        "- 应谨慎：`review_before_tracking` 并不表示文件有问题，只表示需要补 generator/provenance/index 后再纳入论文包。",
        "- 不能写：这些未跟踪输出已经全部通过论文质量门禁或人工验证。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit untracked local artifacts.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_untracked_artifact_audit.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_untracked_artifact_audit_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "untracked_entries": len(rows),
        "track_as_paper_artifact": sum(1 for row in rows if row["recommendation"] == "track_as_paper_artifact"),
        "review_before_tracking": sum(1 for row in rows if row["recommendation"] == "review_before_tracking"),
        "keep_untracked": sum(1 for row in rows if row["recommendation"] == "keep_untracked"),
    })


if __name__ == "__main__":
    main()
