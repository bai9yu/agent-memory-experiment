#!/usr/bin/env python3
"""Validate anonymous-submission readiness for current paper package candidates."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


IDENTITY_PATTERNS = (
    ("absolute_user_path", re.compile(r"/Users/[^/\s`]+")),
    ("github_repository_identity", re.compile(r"github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")),
    ("email_like", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("api_key_assignment", re.compile(r"\b(?:OPENAI|DEEPSEEK|EXTERNAL_EMBEDDING)_API_KEY\s*=")),
    ("codex_local_thread_path", re.compile(r"Documents/Codex/\d{4}-\d{2}-\d{2}")),
)


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


def as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def scan_file(path: Path) -> list[str]:
    if not path.exists() or not path.is_file():
        return ["missing_file"]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    for label, pattern in IDENTITY_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


def check_row(check: str, category: str, passed: bool, evidence: str, action: str) -> dict[str, Any]:
    return {
        "check": check,
        "category": category,
        "pass": passed,
        "status": "pass" if passed else "blocker",
        "evidence": evidence,
        "action": action,
    }


def build_rows(root: Path, manifest_csv: Path) -> list[dict[str, Any]]:
    manifest_rows = read_csv(manifest_csv)
    include_rows = [row for row in manifest_rows if as_bool(row.get("include_in_current_supplement"))]
    blocked_included = [
        row for row in manifest_rows
        if row.get("package_bucket") == "exclude_until_blocker_closed" and as_bool(row.get("include_in_current_supplement"))
    ]
    file_findings: list[tuple[str, list[str]]] = []
    for row in include_rows:
        artifact = row.get("artifact", "")
        findings = scan_file(root / artifact)
        if findings:
            file_findings.append((artifact, findings))
    internal_gate_included = [
        row for row in include_rows
        if row.get("package_bucket") == "internal_review_gate"
    ]
    return [
        check_row(
            "manifest_exists",
            "input",
            bool(manifest_rows),
            f"manifest_rows={len(manifest_rows)}, include_rows={len(include_rows)}",
            "先生成 supplementary package manifest。",
        ),
        check_row(
            "blocked_artifacts_excluded",
            "claim_boundary",
            not blocked_included,
            f"blocked_artifacts_included={len(blocked_included)}",
            "关闭外部 embedding / 人审 blocker 前，不要把 blocked artifact 放入 supplement。",
        ),
        check_row(
            "internal_gates_not_in_supplement",
            "packaging_boundary",
            not internal_gate_included,
            f"internal_gate_artifacts_included={len(internal_gate_included)}",
            "将 internal_review_gate 保留在仓库/rebuttal 材料中，不作为匿名 supplement 主包。",
        ),
        check_row(
            "included_files_exist",
            "file_integrity",
            not any("missing_file" in findings for _, findings in file_findings),
            "missing=" + ";".join(artifact for artifact, findings in file_findings if "missing_file" in findings),
            "修复 manifest 中指向的缺失 artifact。",
        ),
        check_row(
            "included_files_anonymous",
            "anonymization",
            not [item for item in file_findings if item[1] != ["missing_file"]],
            "; ".join(f"{artifact}:{','.join(findings)}" for artifact, findings in file_findings if findings != ["missing_file"]) or "no identity-like findings in included artifacts",
            "匿名投稿前移除作者路径、仓库 URL、邮箱、API key 赋值和本地 Codex 路径。",
        ),
    ]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], manifest_csv: Path) -> None:
    blockers = [row for row in rows if row["status"] == "blocker"]
    table_rows = [
        [row["check"], row["category"], row["status"], row["evidence"], row["action"]]
        for row in rows
    ]
    lines = [
        "# Anonymous Submission Readiness Audit",
        "",
        "本文件检查当前补充材料候选是否适合匿名投稿。它只扫描 supplementary package manifest 中 `include_in_current_supplement=True` 的 artifact，不扫描内部审查 gate 或本地中间文件。",
        "",
        "## 总览",
        "",
        f"- Manifest source: `{manifest_csv}`",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Anonymous package ready: {len(blockers) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Check", "Category", "Status", "Evidence", "Action"], table_rows),
        "",
        "## 使用边界",
        "",
        "- 该审计只能检查当前 artifact 文本中常见身份线索；最终仍需按目标会议模板检查作者栏、致谢、补充材料封面和文件元数据。",
        "- `Anonymous package ready=True` 不代表实验 blocker 已解除，只代表当前可纳入 supplement 的文件未发现常见身份泄露。",
        "- 若目标会议允许非匿名仓库，本审计仍可作为公开发布前的路径/身份卫生检查。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate anonymous-submission readiness for supplement candidates.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--manifest-csv", type=Path, default=Path("outputs/agent_memory_supplementary_package_manifest.csv"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.manifest_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.manifest_csv)
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "blockers": sum(1 for row in rows if row["status"] == "blocker"),
        "anonymous_package_ready": all(row["status"] == "pass" for row in rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
