#!/usr/bin/env python3
"""Audit large local intermediate artifacts and their tracked downstream evidence."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


INTERMEDIATES = [
    {
        "path": "outputs/agent_memory_candidate_reranker_loco_ranked_top20.csv",
        "role": "LOCO candidate reranker ranked Top-20 intermediate",
        "generator": "work/agent_memory_experiment/candidate_reranker_intrinsic_loco_experiment.py",
        "downstream": "outputs/agent_memory_candidate_reranker_intrinsic_loco_zh.md;outputs/agent_memory_candidate_depth_analysis_zh.md",
        "policy": "keep_untracked_regenerable",
    },
    {
        "path": "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
        "role": "held-out candidate reranker ranked Top-20 intermediate",
        "generator": "work/agent_memory_experiment/candidate_reranker_experiment.py",
        "downstream": "outputs/agent_memory_set_selection_top20_zh.md;outputs/agent_memory_multi_evidence_coverage_top20_zh.md;outputs/agent_memory_candidate_depth_analysis_zh.md",
        "policy": "keep_untracked_regenerable",
    },
    {
        "path": "outputs/agent_memory_set_selection_ranked.csv",
        "role": "Top-10 set-level selector full ranked intermediate",
        "generator": "work/agent_memory_experiment/set_level_selection_experiment.py",
        "downstream": "outputs/agent_memory_set_selection_zh.md;outputs/agent_memory_set_selection_overall.csv;outputs/agent_memory_set_selection_by_type.csv",
        "policy": "keep_untracked_regenerable",
    },
    {
        "path": "outputs/agent_memory_set_selection_top20_ranked.csv",
        "role": "Top-20 set-level selector full ranked intermediate",
        "generator": "work/agent_memory_experiment/set_level_selection_experiment.py",
        "downstream": "outputs/agent_memory_set_selection_top20_zh.md;outputs/agent_memory_set_selection_top20_overall.csv;outputs/agent_memory_set_selection_top20_by_type.csv",
        "policy": "keep_untracked_regenerable",
    },
    {
        "path": "outputs/agent_memory_multi_evidence_coverage_top20_per_query.csv",
        "role": "Top-20 multi-evidence per-query diagnostic",
        "generator": "work/agent_memory_experiment/multi_evidence_coverage_analysis.py",
        "downstream": "outputs/agent_memory_multi_evidence_coverage_top20_zh.md;outputs/agent_memory_multi_evidence_coverage_top20_summary.csv;outputs/agent_memory_multi_evidence_coverage_top20_delta_by_type.csv;outputs/agent_memory_candidate_depth_analysis_zh.md",
        "policy": "optional_track_or_keep_untracked",
    },
]


def git_tracked(root: Path, rel: str) -> bool:
    result = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=root, capture_output=True, text=True)
    return result.returncode == 0


def file_size(root: Path, rel: str) -> int:
    path = root / rel
    return path.stat().st_size if path.exists() and path.is_file() else 0


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def downstream_status(root: Path, downstream: str) -> tuple[int, int, str]:
    items = [item for item in downstream.split(";") if item]
    existing = [item for item in items if (root / item).exists()]
    tracked = [item for item in items if git_tracked(root, item)]
    missing = [item for item in items if not (root / item).exists()]
    detail = f"existing={len(existing)}/{len(items)}, tracked={len(tracked)}/{len(items)}"
    if missing:
        detail += "; missing=" + ";".join(missing[:5])
    return len(existing), len(tracked), detail


def build_rows(root: Path) -> list[dict[str, Any]]:
    readme = read_text(root / "work" / "agent_memory_experiment" / "README.md")
    rows = []
    for spec in INTERMEDIATES:
        rel = spec["path"]
        exists = (root / rel).exists()
        tracked = git_tracked(root, rel)
        generator_exists = (root / spec["generator"]).exists()
        readme_mentions = rel in readme and spec["generator"] in readme
        downstream_existing, downstream_tracked, downstream_detail = downstream_status(root, spec["downstream"])
        policy = spec["policy"]
        if policy == "keep_untracked_regenerable":
            passed = exists and not tracked and generator_exists and readme_mentions and downstream_existing == downstream_tracked
            status = "pass" if passed else "major"
            action = "Keep the large ranked intermediate local; rely on tracked downstream summaries and README regeneration commands."
        elif policy == "optional_track_or_keep_untracked":
            passed = exists and generator_exists and readme_mentions and downstream_existing == downstream_tracked
            status = "pass" if passed else "major"
            action = "Either track this moderate-size per-query diagnostic or keep it local with tracked summary/delta artifacts."
        else:
            passed = exists and generator_exists
            status = "review" if passed else "major"
            action = "Promote only after adding a named paper claim, tracked downstream summary, and README command."
        rows.append({
            "path": rel,
            "role": spec["role"],
            "policy": policy,
            "exists": exists,
            "tracked": tracked,
            "size_bytes": file_size(root, rel),
            "generator": spec["generator"],
            "generator_exists": generator_exists,
            "readme_mentions_command": readme_mentions,
            "downstream": spec["downstream"] or "none",
            "downstream_status": downstream_detail if spec["downstream"] else "no tracked downstream artifact declared",
            "status": status,
            "action": action,
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
    major = [row for row in rows if row["status"] == "major"]
    review = [row for row in rows if row["status"] == "review"]
    table_rows = [
        [
            row["path"],
            row["policy"],
            row["status"],
            str(row["tracked"]),
            str(row["size_bytes"]),
            row["generator"],
            str(row["readme_mentions_command"]),
            row["downstream_status"],
        ]
        for row in rows
    ]
    lines = [
        "# Large Intermediate Provenance Audit",
        "",
        "本文件审计较大的本地中间文件是否有清晰生成来源、README 命令和已入库的下游小报告。它用于解释为什么部分 ranked/per-query 明细保持未跟踪，而不是误以为复现包遗漏证据。",
        "",
        "## 总览",
        "",
        f"- Audited intermediates: {len(rows)}",
        f"- Major issues: {len(major)}",
        f"- Review-only items: {len(review)}",
        f"- Provenance acceptable: {len(major) == 0}",
        "",
        "## 明细",
        "",
        markdown_table(
            ["Path", "Policy", "Status", "Tracked", "Size Bytes", "Generator", "README Command", "Downstream Status"],
            table_rows,
        ),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：大 ranked/per-query 中间文件有生成命令和下游已跟踪 summary/report 支撑，公开仓库优先保留小型可审阅 artifact。",
        "- 应谨慎：`review_before_tracking` 项不能作为论文主证据，除非补齐正式 summary、claim boundary 和复现索引。",
        "- 不能写：未跟踪的大中间文件已经等同于公开复现包的一部分。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit large local intermediates and tracked downstream provenance.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "intermediates": len(rows),
        "major": sum(1 for row in rows if row["status"] == "major"),
        "review": sum(1 for row in rows if row["status"] == "review"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
