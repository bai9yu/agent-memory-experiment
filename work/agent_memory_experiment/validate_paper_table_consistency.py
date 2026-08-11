#!/usr/bin/env python3
"""Validate that paper table artifacts match cached metric CSV sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SOURCE_FILES = (
    "agent_memory_baseline_comparison_locomo10.csv",
    "agent_memory_candidate_reranker_locomo10_summary.csv",
    "agent_memory_candidate_reranker_significance_results.csv",
    "agent_memory_candidate_reranker_loco_summary.csv",
    "agent_memory_candidate_reranker_loco_significance_results.csv",
    "agent_memory_candidate_reranker_intrinsic_loco_summary.csv",
    "agent_memory_candidate_reranker_feature_ablation_deltas.csv",
    "agent_memory_type3_specific_reranker_summary.csv",
    "agent_memory_type3_supervised_set_selector_summary.csv",
    "agent_memory_type3_query_decomposition_summary.csv",
    "agent_memory_type3_coverage_significance_summary.csv",
    "agent_memory_sklearn_nn_prefilter_locomo10_summary.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_markdown_tables(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("| ") and " |" in line and "---" not in line)


def count_latex_tables(text: str) -> int:
    return text.count(r"\begin{table}")


def latex_labels(text: str) -> list[str]:
    labels: list[str] = []
    marker = r"\label{"
    for part in text.split(marker)[1:]:
        labels.append(part.split("}", 1)[0])
    return labels


def run_regeneration(project_root: Path, outputs_dir: Path, tmp_dir: Path) -> tuple[Path, Path]:
    expected_md = tmp_dir / "expected_tables.md"
    expected_tex = tmp_dir / "expected_tables.tex"
    script = project_root / "work" / "agent_memory_experiment" / "generate_paper_tables.py"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--outputs-dir",
            str(outputs_dir),
            "--output-markdown",
            str(expected_md),
            "--output-latex",
            str(expected_tex),
        ],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return expected_md, expected_tex


def file_row(kind: str, current: Path, expected: Path) -> dict[str, Any]:
    current_exists = current.exists()
    expected_exists = expected.exists()
    current_text = current.read_text(encoding="utf-8") if current_exists else ""
    expected_text = expected.read_text(encoding="utf-8") if expected_exists else ""
    return {
        "check": f"{kind}_matches_regenerated",
        "kind": kind,
        "pass": current_exists and expected_exists and current_text == expected_text,
        "current_path": str(current),
        "expected_sha256": sha256(expected) if expected_exists else "",
        "current_sha256": sha256(current) if current_exists else "",
        "current_size_bytes": current.stat().st_size if current_exists else 0,
        "expected_size_bytes": expected.stat().st_size if expected_exists else 0,
        "evidence": "byte-identical to regenerated table artifact" if current_text == expected_text else "current table artifact differs from regenerated source output",
    }


def build_rows(project_root: Path, outputs_dir: Path, markdown: Path, latex: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in SOURCE_FILES:
        path = outputs_dir / source
        rows.append({
            "check": f"source_exists:{source}",
            "kind": "source",
            "pass": path.exists(),
            "current_path": str(path),
            "expected_sha256": "",
            "current_sha256": sha256(path) if path.exists() else "",
            "current_size_bytes": path.stat().st_size if path.exists() else 0,
            "expected_size_bytes": "",
            "evidence": "source CSV exists" if path.exists() else "source CSV missing",
        })
    with tempfile.TemporaryDirectory(prefix="paper_table_consistency_") as tmp:
        expected_md, expected_tex = run_regeneration(project_root, outputs_dir, Path(tmp))
        rows.append(file_row("markdown", markdown, expected_md))
        rows.append(file_row("latex", latex, expected_tex))

    md_text = markdown.read_text(encoding="utf-8") if markdown.exists() else ""
    tex_text = latex.read_text(encoding="utf-8") if latex.exists() else ""
    labels = latex_labels(tex_text)
    rows.extend([
        {
            "check": "markdown_table_sections_present",
            "kind": "structure",
            "pass": md_text.count("## ") >= 11,
            "current_path": str(markdown),
            "expected_sha256": "",
            "current_sha256": "",
            "current_size_bytes": "",
            "expected_size_bytes": "",
            "evidence": f"markdown sections={md_text.count('## ')}",
        },
        {
            "check": "latex_table_count",
            "kind": "structure",
            "pass": count_latex_tables(tex_text) == 11,
            "current_path": str(latex),
            "expected_sha256": "",
            "current_sha256": "",
            "current_size_bytes": "",
            "expected_size_bytes": "",
            "evidence": f"latex tables={count_latex_tables(tex_text)}",
        },
        {
            "check": "latex_labels_unique",
            "kind": "structure",
            "pass": len(labels) == len(set(labels)) == 11,
            "current_path": str(latex),
            "expected_sha256": "",
            "current_sha256": "",
            "current_size_bytes": "",
            "expected_size_bytes": "",
            "evidence": f"labels={len(labels)}, unique={len(set(labels))}",
        },
    ])
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    failures = [row for row in rows if not row["pass"]]
    table_rows = [
        [row["check"], row["kind"], str(row["pass"]), row["current_path"], row["evidence"]]
        for row in rows
    ]
    lines = [
        "# Paper Table Consistency Audit",
        "",
        "本文件检查论文表格 artifact 是否仍与缓存实验 CSV 一致。它会在临时目录中重新运行 `generate_paper_tables.py`，再把当前 Markdown/LaTeX 表格与重新生成结果做字节级比较。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Failures: {len(failures)}",
        f"- Table artifacts match regenerated outputs: {len(failures) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Check", "Kind", "Pass", "Path", "Evidence"], table_rows),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：当前论文表格由缓存 CSV 生成，并通过独立一致性审计。",
        "- 应谨慎：该审计只证明表格和 CSV 一致，不证明实验设计本身已解除外部 embedding 或人工审计 blocker。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate paper table artifacts against regenerated outputs.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--markdown", type=Path, default=Path("outputs/agent_memory_paper_tables_zh.md"))
    parser.add_argument("--latex", type=Path, default=Path("outputs/agent_memory_paper_tables.tex"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.outputs_dir, args.markdown, args.latex)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "failures": sum(1 for row in rows if not row["pass"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
