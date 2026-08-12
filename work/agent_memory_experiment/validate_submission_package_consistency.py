#!/usr/bin/env python3
"""Validate consistency across paper package index and packaging artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


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


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def rel_exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def bool_str(value: str) -> bool:
    return value == "True"


def check_row(check: str, passed: bool, severity: str, evidence: str, action: str) -> dict[str, Any]:
    return {
        "check": check,
        "pass": passed,
        "severity": severity,
        "status": "pass" if passed else severity,
        "evidence": evidence,
        "action": action,
    }


def build_rows(
    root: Path,
    package_index: Path,
    supplement_manifest: Path,
    reproducibility_artifacts: Path,
    integrity_manifest: Path,
) -> list[dict[str, Any]]:
    index_rows = read_csv(package_index)
    supplement_rows = read_csv(supplement_manifest)
    repro_rows = read_csv(reproducibility_artifacts)
    integrity_rows = read_csv(integrity_manifest)

    index_paths = {row.get("artifact", "") for row in index_rows if row.get("artifact")}
    self_referential_paths = {"outputs/agent_memory_reproducibility_checklist_zh.md"}
    supplement_paths = {row.get("artifact", "") for row in supplement_rows if row.get("artifact")}
    repro_paths = {row.get("path", "") for row in repro_rows if row.get("path")}
    integrity_paths = {row.get("path", "") for row in integrity_rows if row.get("path")}

    missing_index_files = sorted(path for path in index_paths if not rel_exists(root, path))
    missing_from_supplement = sorted(index_paths - supplement_paths)
    extra_in_supplement = sorted(supplement_paths - index_paths)
    missing_from_repro = sorted(index_paths - repro_paths - self_referential_paths)
    missing_from_integrity = sorted(index_paths - integrity_paths - self_referential_paths)
    supplement_missing_files = sorted(
        row.get("artifact", "")
        for row in supplement_rows
        if row.get("artifact") and not bool_str(row.get("exists", "False"))
    )
    supplement_untracked = sorted(
        row.get("artifact", "")
        for row in supplement_rows
        if row.get("artifact") and not bool_str(row.get("tracked_in_reproducibility", "False"))
        and row.get("artifact") not in self_referential_paths
    )
    supplement_anonymization = sorted(
        row.get("artifact", "")
        for row in supplement_rows
        if row.get("anonymization_findings", "")
    )

    return [
        check_row(
            "package_index_exists",
            package_index.exists() and len(index_rows) > 0,
            "blocker",
            f"path={package_index}, rows={len(index_rows)}",
            "Regenerate the submission package index.",
        ),
        check_row(
            "indexed_artifacts_exist",
            not missing_index_files,
            "blocker",
            "all indexed artifacts exist" if not missing_index_files else "; ".join(missing_index_files[:20]),
            "Regenerate missing artifacts or remove stale rows from the package index.",
        ),
        check_row(
            "supplement_manifest_covers_index",
            not missing_from_supplement,
            "blocker",
            f"missing_from_supplement={missing_from_supplement[:20]}",
            "Regenerate the supplementary package manifest from the current package index.",
        ),
        check_row(
            "supplement_manifest_has_no_extra_artifacts",
            not extra_in_supplement,
            "major",
            f"extra_in_supplement={extra_in_supplement[:20]}",
            "Regenerate the supplementary package manifest so it mirrors the package index.",
        ),
        check_row(
            "indexed_artifacts_tracked_in_reproducibility",
            not missing_from_repro,
            "blocker",
            f"missing_from_reproducibility={missing_from_repro[:20]}",
            "Add indexed artifacts to generate_reproducibility_checklist.py or remove stale package-index rows.",
        ),
        check_row(
            "indexed_artifacts_in_integrity_manifest",
            not missing_from_integrity,
            "blocker",
            f"missing_from_integrity={missing_from_integrity[:20]}",
            "Regenerate reproducibility checklist and artifact integrity manifest after package-index changes.",
        ),
        check_row(
            "supplement_manifest_file_flags_match_disk",
            not supplement_missing_files,
            "blocker",
            f"supplement_missing_files={supplement_missing_files[:20]}",
            "Regenerate missing files or update the package index before packaging.",
        ),
        check_row(
            "supplement_manifest_repro_flags_match_repro_list",
            not supplement_untracked,
            "major",
            f"supplement_untracked={supplement_untracked[:20]}",
            "Ensure package artifacts are tracked in the reproducibility artifact list.",
        ),
        check_row(
            "supplement_manifest_anonymization_clean",
            not supplement_anonymization,
            "blocker",
            f"anonymization_findings={supplement_anonymization[:20]}",
            "Resolve anonymization findings before treating current supplement candidates as anonymous-submission ready.",
        ),
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [row for row in rows if row["status"] == "blocker"]
    major = [row for row in rows if row["status"] == "major"]
    table = [[row["check"], str(row["pass"]), row["status"], row["evidence"], row["action"]] for row in rows]
    lines = [
        "# Submission Package Consistency Audit",
        "",
        "本文件检查 submission package index、supplementary package manifest、reproducibility artifact list 和 integrity manifest 是否互相覆盖。它用于防止投稿打包时漏掉索引文件、把过期文件误放进 supplement，或让索引 artifact 脱离 sha256 manifest。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major issues: {len(major)}",
        f"- Package artifacts consistent: {not blockers and not major}",
        "",
        "## 明细",
        "",
        markdown_table(["Check", "Pass", "Status", "Evidence", "Action"], table),
        "",
        "## 使用边界",
        "",
        "- 可以写：当前 package index 中的 artifact 均存在，并由 supplement manifest、reproducibility checklist 和 integrity manifest 覆盖。",
        "- 不能写：package consistency 通过就代表实验 blocker 已解除；它只证明打包索引和复现清单没有互相脱节。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate submission package artifact consistency.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--package-index-csv", type=Path, default=Path("outputs/agent_memory_submission_package_index.csv"))
    parser.add_argument("--supplement-manifest-csv", type=Path, default=Path("outputs/agent_memory_supplementary_package_manifest.csv"))
    parser.add_argument("--reproducibility-csv", type=Path, default=Path("outputs/agent_memory_reproducibility_artifacts.csv"))
    parser.add_argument("--integrity-csv", type=Path, default=Path("outputs/agent_memory_artifact_integrity_manifest.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_submission_package_consistency.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_submission_package_consistency_zh.md"))
    args = parser.parse_args()

    rows = build_rows(
        args.project_root,
        args.package_index_csv,
        args.supplement_manifest_csv,
        args.reproducibility_csv,
        args.integrity_csv,
    )
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
