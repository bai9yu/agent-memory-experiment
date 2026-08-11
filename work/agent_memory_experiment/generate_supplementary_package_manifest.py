#!/usr/bin/env python3
"""Generate a supplementary-material packaging manifest for paper artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


IDENTITY_PATTERNS = (
    ("absolute_user_path", re.compile(r"/Users/[^/\s`]+")),
    ("github_identity_url", re.compile(r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")),
    ("email_like", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("api_key_assignment", re.compile(r"\b(?:OPENAI|DEEPSEEK|EXTERNAL_EMBEDDING)_API_KEY\s*=")),
)

INCLUDE_STATUSES = {
    "ready",
    "ready_diagnostic",
    "ready_for_internal_review",
    "ready_with_blockers_declared",
    "pass",
    "classified",
}

PROTOCOL_ONLY_STATUSES = {
    "ready_for_labeling",
    "ready_qc",
    "ready_with_external_inputs",
}

BLOCKED_STATUSES = {
    "blocked",
    "blocked_until_api_run",
    "not_ready",
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


def rel_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def file_size(root: Path, rel: str) -> int:
    path = root / rel
    return path.stat().st_size if path.exists() and path.is_file() else 0


def scan_identity(root: Path, rel: str) -> list[str]:
    path = root / rel
    if not path.exists() or not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    for label, pattern in IDENTITY_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def package_bucket(section: str, status: str) -> str:
    if status in BLOCKED_STATUSES:
        return "exclude_until_blocker_closed"
    if section in {"Submission Gate", "Reproducibility", "Evidence Matrix", "Reviewer Prep"}:
        return "internal_review_gate"
    if status in PROTOCOL_ONLY_STATUSES:
        return "protocol_appendix_candidate"
    if section in {"Manuscript", "Main Tables"}:
        return "main_paper_candidate"
    if section in {"Method Appendix", "Experiment Protocol", "Threats to Validity", "Paper Tables"}:
        return "supplement_candidate"
    if section in {"External Embedding", "Human Audit"}:
        return "protocol_or_diagnostic_candidate"
    if status in INCLUDE_STATUSES:
        return "supplement_candidate"
    return "review_before_packaging"


def include_now(bucket: str, status: str, anonymization_findings: list[str]) -> bool:
    if anonymization_findings:
        return False
    if bucket in {"main_paper_candidate", "supplement_candidate", "protocol_or_diagnostic_candidate"}:
        return status not in BLOCKED_STATUSES
    return False


def build_rows(root: Path, package_index: Path, reproducibility_csv: Path) -> list[dict[str, Any]]:
    package_rows = read_csv(package_index)
    repro_paths = {row.get("path", "") for row in read_csv(reproducibility_csv)}
    rows: list[dict[str, Any]] = []
    for row in package_rows:
        artifact = row.get("artifact", "")
        status = row.get("status", "")
        section = row.get("section", "")
        findings = scan_identity(root, artifact)
        bucket = package_bucket(section, status)
        exists = rel_exists(root, artifact)
        rows.append({
            "section": section,
            "artifact": artifact,
            "package_bucket": bucket,
            "include_in_current_supplement": include_now(bucket, status, findings),
            "exists": exists,
            "status": status,
            "tracked_in_reproducibility": artifact in repro_paths,
            "size_bytes": file_size(root, artifact),
            "anonymization_findings": ";".join(findings),
            "role": row.get("role", ""),
            "next_action": row.get("next_action", ""),
        })
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], readiness_rows: list[dict[str, str]]) -> None:
    include_rows = [row for row in rows if row["include_in_current_supplement"]]
    blocked_rows = [row for row in rows if row["package_bucket"] == "exclude_until_blocker_closed"]
    findings = [row for row in rows if row["anonymization_findings"]]
    missing = [row for row in rows if not row["exists"]]
    blockers = [row for row in readiness_rows if row.get("status") == "blocker"]
    table_rows = [
        [
            row["section"],
            row["artifact"],
            row["package_bucket"],
            str(row["include_in_current_supplement"]),
            row["status"],
            row["anonymization_findings"] or "none",
        ]
        for row in rows
    ]
    lines = [
        "# Supplementary Package Manifest",
        "",
        "本文件把当前论文提交包索引转成补充材料打包清单。它区分可进入当前 supplement 的 artifact、只供内部审查的 gate、因 blocker 暂缓的实验报告，并扫描匿名投稿前常见身份/本地路径风险。",
        "",
        "## 总览",
        "",
        f"- Indexed artifacts: {len(rows)}",
        f"- Include in current supplement: {len(include_rows)}",
        f"- Internal/review gates or protocol-only artifacts: {len(rows) - len(include_rows) - len(blocked_rows)}",
        f"- Exclude until blocker closed: {len(blocked_rows)}",
        f"- Missing indexed artifacts: {len(missing)}",
        f"- Anonymization findings: {len(findings)}",
        f"- Submission blockers still open: {len(blockers)}",
        "",
        "## 打包明细",
        "",
        markdown_table(["Section", "Artifact", "Bucket", "Include Now", "Status", "Anonymization Findings"], table_rows),
        "",
        "## 使用边界",
        "",
        "- `include_in_current_supplement=True` 表示当前内部/非匿名补充材料候选；最终匿名投稿仍要按会议模板去除作者信息。",
        "- `internal_review_gate` 适合留在仓库或 rebuttal 准备材料中，不一定适合提交为 supplement。",
        "- `exclude_until_blocker_closed` 在外部 embedding 或人工审计完成前不应作为已完成实验结果进入 supplement。",
        "- 该 manifest 不压缩文件、不复制文件，只提供可复现打包决策。",
    ]
    if findings:
        lines.extend(["", "## 匿名化发现", ""])
        for row in findings:
            lines.append(f"- `{row['artifact']}`: {row['anonymization_findings']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate supplementary packaging manifest.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--package-index-csv", type=Path, default=Path("outputs/agent_memory_submission_package_index.csv"))
    parser.add_argument("--reproducibility-csv", type=Path, default=Path("outputs/agent_memory_reproducibility_artifacts.csv"))
    parser.add_argument("--readiness-csv", type=Path, default=Path("outputs/agent_memory_submission_readiness.csv"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.package_index_csv, args.reproducibility_csv)
    readiness_rows = read_csv(args.readiness_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, readiness_rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "indexed_artifacts": len(rows),
        "include_in_current_supplement": sum(1 for row in rows if row["include_in_current_supplement"]),
        "anonymization_findings": sum(1 for row in rows if row["anonymization_findings"]),
        "missing": sum(1 for row in rows if not row["exists"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
