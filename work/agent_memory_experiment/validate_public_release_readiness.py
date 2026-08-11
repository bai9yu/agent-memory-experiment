#!/usr/bin/env python3
"""Validate public-release hygiene for the experiment repository."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{12,}"),
    re.compile(r"Bearer [A-Za-z0-9_-]{20,}"),
    re.compile(r"OPENAI_API_KEY=[A-Za-z0-9]"),
    re.compile(r"DEEPSEEK_API_KEY=[A-Za-z0-9]"),
    re.compile(r"EXTERNAL_EMBEDDING_API_KEY=[A-Za-z0-9]"),
)
ALLOWED_PLACEHOLDERS = {
    "your_deepseek_api_key_here",
    "your_openai_api_key_here",
    "your_embedding_provider_key_here",
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def git_files(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True)
    return [line for line in result.stdout.splitlines() if line.strip()]


def file_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None


def tracked_secret_hits(root: Path, files: list[str]) -> list[str]:
    hits = []
    for rel in files:
        text = file_text(root / rel)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(token in line for token in ALLOWED_PLACEHOLDERS):
                continue
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                hits.append(f"{rel}:{line_no}:{line[:160]}")
                if len(hits) >= 20:
                    return hits
    return hits


def check_row(check: str, category: str, passed: bool, severity: str, evidence: str, next_action: str) -> dict[str, Any]:
    return {
        "check": check,
        "category": category,
        "pass": passed,
        "severity": severity,
        "status": "pass" if passed else severity,
        "evidence": evidence,
        "next_action": next_action,
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_rows(root: Path) -> list[dict[str, Any]]:
    files = git_files(root)
    file_set = set(files)
    gitignore = file_text(root / ".gitignore") or ""
    env_example = file_text(root / ".env.example") or ""
    readme = file_text(root / "README.md") or ""
    untracked_audit = read_csv(root / "outputs" / "agent_memory_untracked_artifact_audit.csv")
    path_portability = read_csv(root / "outputs" / "agent_memory_artifact_path_portability.csv")
    secret_hits = tracked_secret_hits(root, files)
    license_files = [name for name in files if Path(name).name.lower() in {"license", "license.md", "license.txt"}]
    untracked_review = sum(1 for row in untracked_audit if row.get("recommendation") == "review_before_tracking")
    untracked_keep_local = sum(1 for row in untracked_audit if row.get("recommendation") == "keep_untracked")
    path_findings = sum(1 for row in path_portability if row.get("status") == "finding")

    rows = [
        check_row(
            "tracked_secret_scan",
            "security",
            not secret_hits,
            "blocker",
            "no tracked secret-like lines found" if not secret_hits else "; ".join(secret_hits[:5]),
            "移除真实 API key 或 bearer token，轮换泄露 key，并重写 Git 历史后再公开。",
        ),
        check_row(
            "env_file_not_tracked",
            "security",
            ".env" not in file_set,
            "blocker",
            ".env tracked=False",
            "确保 `.env` 不进入 Git；只提交 `.env.example`。",
        ),
        check_row(
            "gitignore_covers_env",
            "security",
            any(line.strip() == ".env" for line in gitignore.splitlines()),
            "major",
            ".gitignore contains `.env`" if ".env" in gitignore else ".gitignore missing `.env`",
            "在 `.gitignore` 中加入 `.env`，避免后续误提交 key。",
        ),
        check_row(
            "env_example_uses_placeholders",
            "reproducibility",
            "your_deepseek_api_key_here" in env_example and "your_openai_api_key_here" in env_example,
            "major",
            ".env.example has provider placeholders",
            "保留 DeepSeek/OpenAI key 的占位说明，不能写真实 key。",
        ),
        check_row(
            "readme_links_submission_gate",
            "paper_artifact",
            "agent_memory_submission_readiness_zh.md" in readme,
            "major",
            "README links submission readiness gate",
            "在 README 的论文报告列表中加入最终投稿门禁。",
        ),
        check_row(
            "untracked_artifact_audit_present",
            "paper_artifact",
            bool(untracked_audit),
            "major",
            f"untracked audit rows={len(untracked_audit)}, review_before_tracking={untracked_review}, keep_untracked={untracked_keep_local}",
            "运行 audit_untracked_artifacts.py，并确认 keep_untracked/local 项仍不属于论文正式 artifact。",
        ),
        check_row(
            "artifact_paths_portable",
            "paper_artifact",
            bool(path_portability) and path_findings == 0,
            "major",
            f"path portability rows={len(path_portability)}, findings={path_findings}",
            "运行 validate_artifact_path_portability.py，并把公开报告中的本机绝对路径改为仓库相对路径。",
        ),
        check_row(
            "license_file_present",
            "open_source",
            bool(license_files),
            "minor",
            f"license files={license_files if license_files else 'none'}",
            "正式开源前补充 LICENSE；内部实验仓库可暂缓。",
        ),
    ]
    return rows


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [row for row in rows if row["status"] == "blocker"]
    majors = [row for row in rows if row["status"] == "major"]
    minors = [row for row in rows if row["status"] == "minor"]
    table_rows = [
        [row["check"], row["category"], row["severity"], str(row["pass"]), row["status"], row["evidence"]]
        for row in rows
    ]
    lines = [
        "# Public Release Readiness Gate",
        "",
        "本文件检查仓库公开发布和论文 artifact 附件的基础卫生状态，重点是 API key 泄露、`.env` 管理、复现入口和开源元数据。它只扫描 Git 已跟踪文件，不读取或打印 `.env` 内容。",
        "",
        "## 总览",
        "",
        f"- Blockers: {len(blockers)}",
        f"- Major warnings: {len(majors)}",
        f"- Minor warnings: {len(minors)}",
        f"- Safe for public artifact release: {len(blockers) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Check", "Category", "Severity", "Pass", "Status", "Evidence"], table_rows),
        "",
        "## 当前动作",
        "",
    ]
    pending = blockers + majors + minors
    if pending:
        for row in pending:
            lines.append(f"- `{row['check']}`：{row['next_action']}")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 论文使用判断",
        "",
        "- 若 blocker=0，可以把当前仓库作为内部复现 artifact 或公开仓库继续整理。",
        "- 若要匿名投稿，仍需要根据会议要求移除作者、账号、仓库 URL 等身份信息；该检查不自动匿名化论文文本。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate public-release hygiene for tracked repository files.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    blockers = sum(1 for row in rows if row["status"] == "blocker")
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "blockers": blockers,
        "safe_for_public_artifact_release": blockers == 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
