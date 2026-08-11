#!/usr/bin/env python3
"""Generate a checksum manifest for paper experiment artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return sum(1 for _ in f)
    except UnicodeDecodeError:
        return -1


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_rows(project_root: Path, artifact_csv: Path) -> list[dict[str, Any]]:
    artifacts = read_csv(artifact_csv)
    rows = []
    for artifact in artifacts:
        rel_path = artifact["path"]
        path = project_root / rel_path
        exists = path.exists()
        rows.append({
            "label": artifact["label"],
            "path": rel_path,
            "exists": exists,
            "size_bytes": path.stat().st_size if exists else 0,
            "line_count": line_count(path) if exists else 0,
            "sha256": sha256_file(path) if exists else "",
        })
    return rows


def write_report(path: Path, rows: list[dict[str, Any]], artifact_csv: Path) -> None:
    existing = [row for row in rows if row["exists"]]
    missing = [row for row in rows if not row["exists"]]
    total_bytes = sum(int(row["size_bytes"]) for row in existing)
    table_rows = [
        [
            row["label"],
            str(row["exists"]),
            str(row["size_bytes"]),
            str(row["line_count"]),
            str(row["sha256"])[:12],
            row["path"],
        ]
        for row in rows[:20]
    ]
    lines = [
        "# Artifact Integrity Manifest",
        "",
        "本文件为论文复现清单中的关键 artifact 生成 sha256、大小和行数，便于审稿复现、归档和后续检查结果文件是否被意外改动。",
        "",
        "## 总览",
        "",
        f"- Source artifact list: `{artifact_csv}`",
        f"- Artifacts covered: {len(existing)}/{len(rows)}",
        f"- Missing artifacts: {len(missing)}",
        f"- Total bytes: {total_bytes}",
        "",
        "## 前 20 个 Artifact",
        "",
        markdown_table(["Label", "Exists", "Bytes", "Lines", "SHA256 Prefix", "Path"], table_rows),
        "",
        "## 使用说明",
        "",
        "- 完整 sha256 位于 `outputs/agent_memory_artifact_integrity_manifest.csv`。",
        "- 若重新生成实验结果，预期相关 artifact 的 sha256 会变化；应同时更新复现清单、证据矩阵和论文声明检查。",
        "- 若没有重新运行实验而 sha256 变化，应检查是否存在非预期编辑或文件损坏。",
    ]
    if missing:
        lines.extend(["", "## 缺失 Artifact", ""])
        lines.extend([f"- `{row['path']}`" for row in missing])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sha256 manifest for reproducibility artifacts.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--artifact-csv", type=Path, default=Path("outputs/agent_memory_reproducibility_artifacts.csv"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.artifact_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.artifact_csv)
    print(json.dumps({
        "output_report": str(args.output_report),
        "artifacts": f"{sum(1 for row in rows if row['exists'])}/{len(rows)}",
        "missing": sum(1 for row in rows if not row["exists"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
