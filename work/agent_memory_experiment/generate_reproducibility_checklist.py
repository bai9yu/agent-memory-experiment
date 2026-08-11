#!/usr/bin/env python3
"""Generate a reproducibility checklist for the agent-memory paper experiments."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def count_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def exists_row(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def metric_row(label: str, observed: float, expected_min: float) -> dict[str, Any]:
    return {
        "label": label,
        "observed": observed,
        "expected_min": expected_min,
        "pass": observed >= expected_min,
    }


def metric_lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(
    path: Path,
    artifact_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    command_rows: list[dict[str, str]],
    data_rows: list[dict[str, Any]],
    env_rows: list[dict[str, str]],
) -> None:
    artifact_pass = sum(1 for row in artifact_rows if row["exists"])
    metric_pass = sum(1 for row in metric_rows if row["pass"])
    lines = [
        "# 论文实验复现清单",
        "",
        "本清单用于检查当前仓库是否具备复现实验和写论文的关键 artifact。它不重新运行重型实验，只核对数据、结果文件、核心指标和复现命令入口。",
        "",
        "## 总览",
        "",
        f"- Artifact 存在性：{artifact_pass}/{len(artifact_rows)}",
        f"- 关键指标阈值：{metric_pass}/{len(metric_rows)}",
        "",
        "## 环境快照",
        "",
        "| Key | Value |",
        "|---|---|",
    ]
    for row in env_rows:
        lines.append(f"| {row['key']} | `{row['value']}` |")
    lines.extend([
        "",
        "## 数据文件",
        "",
        "| Label | Path | Count/Status |",
        "|---|---|---:|",
    ])
    for row in data_rows:
        lines.append(f"| {row['label']} | `{row['path']}` | {row['count']} |")
    lines.extend([
        "",
        "## 关键 Artifact",
        "",
        "| Label | Exists | Size | Path |",
        "|---|---:|---:|---|",
    ])
    for row in artifact_rows:
        lines.append(f"| {row['label']} | {row['exists']} | {row['size_bytes']} | `{row['path']}` |")
    lines.extend([
        "",
        "## 核心指标检查",
        "",
        "| Metric | Observed | Expected Min | Pass |",
        "|---|---:|---:|---:|",
    ])
    for row in metric_rows:
        lines.append(f"| {row['label']} | {row['observed']:.4f} | {row['expected_min']:.4f} | {row['pass']} |")
    lines.extend([
        "",
        "## 复现命令入口",
        "",
        "| Stage | Command / Document | Notes |",
        "|---|---|---|",
    ])
    for row in command_rows:
        lines.append(f"| {row['stage']} | `{row['command']}` | {row['notes']} |")
    lines.extend([
        "",
        "## 仍需补强",
        "",
        "- DeepSeek 抽取重复实验仍需多 seed/temperature 版本，以报告 memory writer 方差。",
        "- 跨智能体/KV cache 仍需要真实或半真实 multi-agent trace。",
        "- Type 3 需要更强 LLM 子问题生成或 listwise/setwise objective；当前浅层方法均为负结果。",
        "- 如果投稿，需要把实验环境写成固定版本，包括 Python、sentence-transformers、FAISS/sklearn 版本和 BGE-M3 缓存来源。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_text(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducibility checklist.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-artifacts", type=Path, required=True)
    parser.add_argument("--output-metrics", type=Path, required=True)
    args = parser.parse_args()

    root = args.project_root
    outputs = root / "outputs"
    work = root / "work" / "agent_memory_experiment"
    data = work / "data"
    env_rows = [
        {"key": "git_commit", "value": run_text(["git", "rev-parse", "--short", "HEAD"], root)},
        {"key": "git_branch_status", "value": run_text(["git", "status", "--short", "--branch"], root).splitlines()[0]},
        {"key": "python", "value": sys.version.split()[0]},
    ]

    memories = data / "llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
    queries = data / "llm_extracted_locomo10_all_v3_answerable_queries.jsonl"
    data_rows = [
        {"label": "LLM fact memories", "path": str(memories), "count": count_jsonl(memories) if memories.exists() else 0},
        {"label": "Answerable queries", "path": str(queries), "count": count_jsonl(queries) if queries.exists() else 0},
    ]

    artifact_specs = [
        ("Main baseline CSV", outputs / "agent_memory_baseline_comparison_locomo10.csv"),
        ("LLM extraction report", outputs / "agent_memory_llm_extraction_locomo10_comparison_zh.md"),
        ("Candidate reranker report", outputs / "agent_memory_candidate_reranker_locomo10_zh.md"),
        ("Candidate reranker significance", outputs / "agent_memory_candidate_reranker_significance_zh.md"),
        ("Type3 coverage significance", outputs / "agent_memory_type3_coverage_significance_zh.md"),
        ("Paper tables Markdown", outputs / "agent_memory_paper_tables_zh.md"),
        ("Paper tables LaTeX", outputs / "agent_memory_paper_tables.tex"),
        ("Paper evidence matrix", outputs / "agent_memory_paper_evidence_matrix_zh.md"),
        ("Embedding baseline status", outputs / "agent_memory_embedding_baseline_status_zh.md"),
        ("Embedding baseline status CSV", outputs / "agent_memory_embedding_baseline_status.csv"),
        ("API embedding run estimate", outputs / "agent_memory_api_embedding_run_estimate_zh.md"),
        ("API embedding run estimate CSV", outputs / "agent_memory_api_embedding_run_estimate.csv"),
        ("Embedding baseline comparison", outputs / "agent_memory_embedding_baseline_comparison_zh.md"),
        ("Embedding baseline comparison CSV", outputs / "agent_memory_embedding_baseline_comparison.csv"),
        ("Human audit protocol", outputs / "agent_memory_human_audit_protocol_zh.md"),
        ("Human audit sample", outputs / "agent_memory_human_audit_sample_type_aware.csv"),
        ("Human audit summary", outputs / "agent_memory_human_audit_summary_zh.md"),
        ("Human audit summary CSV", outputs / "agent_memory_human_audit_summary.csv"),
        ("Paper experiment status", outputs / "agent_memory_paper_experiment_status_zh.md"),
        ("Experiment retro", outputs / "agent_memory_experiment_retro_zh.md"),
        ("Environment snapshot", outputs / "agent_memory_environment_snapshot_zh.md"),
    ]
    artifact_rows = [exists_row(label, path) for label, path in artifact_specs]

    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    type_aware = metric_lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    reranker = metric_lookup(read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv"), method="candidate_reranker")
    coverage = metric_lookup(
        read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv"),
        experiment="supervised_set_selector",
        metric="coverage_ratio@5",
    )
    metric_rows = [
        metric_row("LoCoMo10 type_aware MRR", float(type_aware["mrr"]), 0.60),
        metric_row("LoCoMo10 type_aware Recall@5", float(type_aware["recall@5"]), 0.73),
        metric_row("Candidate reranker MRR", float(reranker["mrr_mean"]), 0.65),
        metric_row("Candidate reranker Recall@5", float(reranker["recall@5_mean"]), 0.79),
        metric_row("Type3 supervised selector Coverage@5 delta is negative", -float(coverage["mean_delta"]), 0.05),
    ]

    command_rows = [
        {
            "stage": "Main LoCoMo retrieval",
            "command": "work/agent_memory_experiment/README.md#recommended-locomo-run",
            "notes": "Requires local BGE-M3 cache; no online embedding API.",
        },
        {
            "stage": "Candidate reranker",
            "command": "work/agent_memory_experiment/candidate_reranker_experiment.py",
            "notes": "Uses cached rankings.csv; held-out query split.",
        },
        {
            "stage": "Type3 diagnostics",
            "command": "work/agent_memory_experiment/type3_coverage_significance_analysis.py",
            "notes": "Aggregates Type3 coverage significance tests.",
        },
        {
            "stage": "Embedding baseline status",
            "command": "work/agent_memory_experiment/generate_embedding_baseline_status.py",
            "notes": "Tracks API embedding baseline readiness without reading or printing keys.",
        },
        {
            "stage": "API embedding run estimate",
            "command": "work/agent_memory_experiment/estimate_api_embedding_run.py",
            "notes": "Estimates API embedding item count, approximate tokens, batches, and cache status without network.",
        },
        {
            "stage": "Embedding baseline comparison",
            "command": "work/agent_memory_experiment/compare_embedding_baselines.py",
            "notes": "Compares API embedding summary against BGE-M3 when the API run exists.",
        },
        {
            "stage": "Human audit sample",
            "command": "work/agent_memory_experiment/generate_human_audit_sample.py",
            "notes": "Creates stratified manual-review sample for error-analysis reliability.",
        },
        {
            "stage": "Human audit summary",
            "command": "work/agent_memory_experiment/summarize_human_audit.py",
            "notes": "Summarizes manual labels once the audit CSV is filled.",
        },
        {
            "stage": "Evidence matrix",
            "command": "work/agent_memory_experiment/generate_evidence_matrix.py",
            "notes": "Summarizes paper claims, evidence strength, and remaining gaps.",
        },
        {
            "stage": "Environment snapshot",
            "command": "work/agent_memory_experiment/generate_environment_snapshot.py",
            "notes": "Records Python/package/cache/Git environment; does not read .env.",
        },
        {
            "stage": "Paper tables",
            "command": "work/agent_memory_experiment/generate_paper_tables.py",
            "notes": "Generates Markdown and LaTeX tables from cached CSVs.",
        },
    ]

    write_csv(args.output_artifacts, artifact_rows)
    write_csv(args.output_metrics, metric_rows)
    write_report(args.output_report, artifact_rows, metric_rows, command_rows, data_rows, env_rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "artifacts": f"{sum(1 for row in artifact_rows if row['exists'])}/{len(artifact_rows)}",
        "metrics": f"{sum(1 for row in metric_rows if row['pass'])}/{len(metric_rows)}",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
