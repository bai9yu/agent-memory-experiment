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
    writer_ready: bool,
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
        "- DeepSeek 抽取重复实验已具备 3 个 completed run；后续可在额外数据集或更大 slice 上复验稳定性。" if writer_ready else "- DeepSeek 抽取重复实验仍需多 seed/temperature 版本，以报告 memory writer 方差。",
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
        ("Writer stability report", outputs / "agent_memory_writer_stability_zh.md"),
        ("Writer stability aggregate", outputs / "agent_memory_writer_stability_aggregate.csv"),
        ("Writer stability runs", outputs / "agent_memory_writer_stability_runs.csv"),
        ("Candidate reranker report", outputs / "agent_memory_candidate_reranker_locomo10_zh.md"),
        ("Candidate reranker significance", outputs / "agent_memory_candidate_reranker_significance_zh.md"),
        ("Candidate reranker feature ablation report", outputs / "agent_memory_candidate_reranker_feature_ablation_zh.md"),
        ("Candidate reranker feature ablation summary", outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv"),
        ("Candidate reranker feature ablation split summary", outputs / "agent_memory_candidate_reranker_feature_ablation_split_summary.csv"),
        ("Candidate reranker feature ablation deltas", outputs / "agent_memory_candidate_reranker_feature_ablation_deltas.csv"),
        ("Candidate reranker feature ablation comparison", outputs / "agent_memory_candidate_reranker_feature_ablation_comparison_per_query.csv"),
        ("Bootstrap metric CI report", outputs / "agent_memory_bootstrap_metric_ci_zh.md"),
        ("Bootstrap metric CI CSV", outputs / "agent_memory_bootstrap_metric_ci.csv"),
        ("Validation-tuned router comparison", outputs / "agent_memory_validation_tuned_router_locomo10_comparison_per_query.csv"),
        ("Candidate reranker LOCO report", outputs / "agent_memory_candidate_reranker_loco_zh.md"),
        ("Candidate reranker LOCO summary", outputs / "agent_memory_candidate_reranker_loco_summary.csv"),
        ("Candidate reranker LOCO significance", outputs / "agent_memory_candidate_reranker_loco_significance_zh.md"),
        ("Candidate reranker LOCO comparison", outputs / "agent_memory_candidate_reranker_loco_comparison_per_query.csv"),
        ("Intrinsic candidate reranker LOCO report", outputs / "agent_memory_candidate_reranker_intrinsic_loco_zh.md"),
        ("Intrinsic candidate reranker LOCO summary", outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv"),
        ("Intrinsic candidate reranker LOCO split summary", outputs / "agent_memory_candidate_reranker_intrinsic_loco_split_summary.csv"),
        ("Intrinsic candidate reranker LOCO deltas", outputs / "agent_memory_candidate_reranker_intrinsic_loco_deltas.csv"),
        ("Intrinsic candidate reranker LOCO comparison", outputs / "agent_memory_candidate_reranker_intrinsic_loco_comparison_per_query.csv"),
        ("Intrinsic reranker method appendix", outputs / "agent_memory_intrinsic_reranker_method_appendix_zh.md"),
        ("Intrinsic reranker feature groups", outputs / "agent_memory_intrinsic_reranker_feature_groups.csv"),
        ("Type3 coverage significance", outputs / "agent_memory_type3_coverage_significance_zh.md"),
        ("Type3 query decomposition fusion4 report", outputs / "agent_memory_type3_query_decomposition_fusion4_zh.md"),
        ("Type3 query decomposition fusion4 summary", outputs / "agent_memory_type3_query_decomposition_fusion4_summary.csv"),
        ("Type3 query decomposition fusion4 per-query", outputs / "agent_memory_type3_query_decomposition_fusion4_per_query.csv"),
        ("Type3 query decomposition fusion4 facets", outputs / "agent_memory_type3_query_decomposition_fusion4_facets.csv"),
        ("Type3 query decomposition fusion4 ranked top20", outputs / "agent_memory_type3_query_decomposition_fusion4_ranked_top20.csv"),
        ("Type3 supervised selector rw0 report", outputs / "agent_memory_type3_supervised_set_selector_rw0_zh.md"),
        ("Type3 supervised selector rw0 split summary", outputs / "agent_memory_type3_supervised_set_selector_rw0_split_summary.csv"),
        ("Type3 supervised selector rw0 summary", outputs / "agent_memory_type3_supervised_set_selector_rw0_summary.csv"),
        ("Type3 supervised selector rw0 coverage summary", outputs / "agent_memory_type3_supervised_set_selector_rw0_coverage_summary.csv"),
        ("Type3 supervised selector rw0 per-query", outputs / "agent_memory_type3_supervised_set_selector_rw0_per_query.csv"),
        ("Type3 supervised selector rw0 coverage", outputs / "agent_memory_type3_supervised_set_selector_rw0_coverage.csv"),
        ("Type3 supervised selector rw0 comparison", outputs / "agent_memory_type3_supervised_set_selector_rw0_comparison_per_query.csv"),
        ("Type3 supervised selector rw0 ranked top20", outputs / "agent_memory_type3_supervised_set_selector_rw0_ranked_top20.csv"),
        ("Type3 supervised selector rwn002 report", outputs / "agent_memory_type3_supervised_set_selector_rwn002_zh.md"),
        ("Type3 supervised selector rwn002 split summary", outputs / "agent_memory_type3_supervised_set_selector_rwn002_split_summary.csv"),
        ("Type3 supervised selector rwn002 summary", outputs / "agent_memory_type3_supervised_set_selector_rwn002_summary.csv"),
        ("Type3 supervised selector rwn002 coverage summary", outputs / "agent_memory_type3_supervised_set_selector_rwn002_coverage_summary.csv"),
        ("Type3 supervised selector rwn002 per-query", outputs / "agent_memory_type3_supervised_set_selector_rwn002_per_query.csv"),
        ("Type3 supervised selector rwn002 coverage", outputs / "agent_memory_type3_supervised_set_selector_rwn002_coverage.csv"),
        ("Type3 supervised selector rwn002 comparison", outputs / "agent_memory_type3_supervised_set_selector_rwn002_comparison_per_query.csv"),
        ("Type3 supervised selector rwn002 ranked top20", outputs / "agent_memory_type3_supervised_set_selector_rwn002_ranked_top20.csv"),
        ("Paper tables Markdown", outputs / "agent_memory_paper_tables_zh.md"),
        ("Paper tables LaTeX", outputs / "agent_memory_paper_tables.tex"),
        ("Paper evidence matrix", outputs / "agent_memory_paper_evidence_matrix_zh.md"),
        ("Paper draft outline", outputs / "agent_memory_paper_draft_outline_zh.md"),
        ("Paper manuscript draft", outputs / "agent_memory_manuscript_draft_zh.md"),
        ("Paper manuscript claim check", outputs / "agent_memory_manuscript_claim_check_zh.md"),
        ("Paper manuscript claim check CSV", outputs / "agent_memory_manuscript_claim_check.csv"),
        ("Submission readiness gate", outputs / "agent_memory_submission_readiness_gate_zh.md"),
        ("Submission readiness gate CSV", outputs / "agent_memory_submission_readiness_gate.csv"),
        ("Public release readiness gate", outputs / "agent_memory_public_release_readiness_zh.md"),
        ("Public release readiness gate CSV", outputs / "agent_memory_public_release_readiness.csv"),
        ("Artifact integrity manifest", outputs / "agent_memory_artifact_integrity_manifest_zh.md"),
        ("Artifact integrity manifest CSV", outputs / "agent_memory_artifact_integrity_manifest.csv"),
        ("Submission gap analysis", outputs / "agent_memory_submission_gap_analysis_zh.md"),
        ("Submission gap analysis CSV", outputs / "agent_memory_submission_gap_analysis.csv"),
        ("Experiment protocol", outputs / "agent_memory_experiment_protocol_zh.md"),
        ("Embedding baseline status", outputs / "agent_memory_embedding_baseline_status_zh.md"),
        ("Embedding baseline status CSV", outputs / "agent_memory_embedding_baseline_status.csv"),
        ("Embedding provider profiles", outputs / "agent_memory_embedding_provider_profiles_zh.md"),
        ("Embedding provider profiles CSV", outputs / "agent_memory_embedding_provider_profiles.csv"),
        ("API embedding preflight", outputs / "agent_memory_api_embedding_preflight_zh.md"),
        ("API embedding preflight CSV", outputs / "agent_memory_api_embedding_preflight.csv"),
        ("Mock API embedding smoke test", outputs / "agent_memory_mock_api_embedding_smoke_test_zh.md"),
        ("Mock API embedding smoke test CSV", outputs / "agent_memory_mock_api_embedding_smoke_test.csv"),
        ("API embedding run estimate", outputs / "agent_memory_api_embedding_run_estimate_zh.md"),
        ("API embedding run estimate CSV", outputs / "agent_memory_api_embedding_run_estimate.csv"),
        ("Embedding baseline comparison", outputs / "agent_memory_embedding_baseline_comparison_zh.md"),
        ("Embedding baseline comparison CSV", outputs / "agent_memory_embedding_baseline_comparison.csv"),
        ("Human audit protocol", outputs / "agent_memory_human_audit_protocol_zh.md"),
        ("Human audit sample", outputs / "agent_memory_human_audit_sample_type_aware.csv"),
        ("Human audit summary", outputs / "agent_memory_human_audit_summary_zh.md"),
        ("Human audit summary CSV", outputs / "agent_memory_human_audit_summary.csv"),
        ("LLM-assisted audit report", outputs / "agent_memory_llm_audit_report_zh.md"),
        ("LLM-assisted audit summary", outputs / "agent_memory_llm_audit_summary_zh.md"),
        ("LLM-assisted audit summary CSV", outputs / "agent_memory_llm_audit_summary.csv"),
        ("LLM-assisted audit usage", outputs / "agent_memory_llm_audit_usage.csv"),
        ("Human/LLM audit confirmation", outputs / "agent_memory_human_llm_audit_confirmation.csv"),
        ("Human/LLM audit agreement", outputs / "agent_memory_human_llm_audit_agreement_zh.md"),
        ("Human/LLM audit agreement CSV", outputs / "agent_memory_human_llm_audit_agreement.csv"),
        ("Human/LLM priority20 audit ids", outputs / "agent_memory_human_llm_audit_priority20_ids.csv"),
        ("Human/LLM priority20 audit guide", outputs / "agent_memory_human_llm_audit_priority20_guide_zh.md"),
        ("Human/LLM priority20 audit confirmation", outputs / "agent_memory_human_llm_audit_priority20_confirmation.csv"),
        ("Human/LLM priority20 audit agreement", outputs / "agent_memory_human_llm_audit_priority20_agreement_zh.md"),
        ("Human/LLM priority20 audit agreement CSV", outputs / "agent_memory_human_llm_audit_priority20_agreement.csv"),
        ("Human audit priority20 blind review", outputs / "agent_memory_human_audit_priority20_blind_review_zh.md"),
        ("Human audit priority20 blind review CSV", outputs / "agent_memory_human_audit_priority20_blind_review.csv"),
        ("Human audit priority20 review packet", outputs / "agent_memory_human_audit_priority20_review_packet_zh.md"),
        ("Human audit priority20 dual review CSV", outputs / "agent_memory_human_audit_priority20_dual_review.csv"),
        ("Human audit priority20 dual agreement", outputs / "agent_memory_human_audit_priority20_dual_agreement_zh.md"),
        ("Human audit priority20 dual agreement CSV", outputs / "agent_memory_human_audit_priority20_dual_agreement.csv"),
        ("Human audit full80 blind review", outputs / "agent_memory_human_audit_full80_blind_review_zh.md"),
        ("Human audit full80 blind review CSV", outputs / "agent_memory_human_audit_full80_blind_review.csv"),
        ("Human audit full80 review packet", outputs / "agent_memory_human_audit_full80_review_packet_zh.md"),
        ("Human audit full80 dual review CSV", outputs / "agent_memory_human_audit_full80_dual_review.csv"),
        ("Human audit full80 dual agreement", outputs / "agent_memory_human_audit_full80_dual_agreement_zh.md"),
        ("Human audit full80 dual agreement CSV", outputs / "agent_memory_human_audit_full80_dual_agreement.csv"),
        ("Human audit readiness gate", outputs / "agent_memory_human_audit_readiness_gate_zh.md"),
        ("Human audit readiness gate CSV", outputs / "agent_memory_human_audit_readiness_gate.csv"),
        ("Paper experiment status", outputs / "agent_memory_paper_experiment_status_zh.md"),
        ("Experiment retro", outputs / "agent_memory_experiment_retro_zh.md"),
        ("Environment snapshot", outputs / "agent_memory_environment_snapshot_zh.md"),
    ]
    artifact_rows = [exists_row(label, path) for label, path in artifact_specs]

    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    type_aware = metric_lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    reranker = metric_lookup(read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv"), method="candidate_reranker")
    intrinsic_reranker = metric_lookup(
        read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv"),
        method="ablation_intrinsic_only",
    )
    intrinsic_loco = metric_lookup(
        read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv"),
        method="intrinsic_reranker_loco",
    )
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
        metric_row("Intrinsic-only candidate reranker MRR", float(intrinsic_reranker["mrr_mean"]), 0.67),
        metric_row("Intrinsic-only candidate reranker Recall@5", float(intrinsic_reranker["recall@5_mean"]), 0.80),
        metric_row("Intrinsic-only LOCO candidate reranker MRR", float(intrinsic_loco["mrr_mean"]), 0.66),
        metric_row("Intrinsic-only LOCO candidate reranker Recall@5", float(intrinsic_loco["recall@5_mean"]), 0.79),
        metric_row("Type3 supervised selector Coverage@5 delta is negative", -float(coverage["mean_delta"]), 0.05),
    ]
    writer_ready = False
    writer_aggregate_path = outputs / "agent_memory_writer_stability_aggregate.csv"
    if writer_aggregate_path.exists():
        writer_rows = read_csv(writer_aggregate_path)
        writer_ready = any(
            row.get("metric") == "mrr"
            and int(row.get("completed_runs", "0") or 0) >= 3
            and row.get("status") == "ready_for_variance"
            for row in writer_rows
        )

    command_rows = [
        {
            "stage": "Main LoCoMo retrieval",
            "command": "work/agent_memory_experiment/README.md#recommended-locomo-run",
            "notes": "Requires local BGE-M3 cache; no online embedding API.",
        },
        {
            "stage": "Writer stability",
            "command": "work/agent_memory_experiment/summarize_writer_stability.py",
            "notes": "Summarizes repeated DeepSeek memory-writer runs from a local manifest.",
        },
        {
            "stage": "Candidate reranker",
            "command": "work/agent_memory_experiment/candidate_reranker_experiment.py",
            "notes": "Uses cached rankings.csv; held-out query split.",
        },
        {
            "stage": "Candidate reranker feature ablation",
            "command": "work/agent_memory_experiment/candidate_reranker_feature_ablation.py",
            "notes": "Tests feature-group ablations and compares intrinsic-only reranker against full reranker and fixed type-aware.",
        },
        {
            "stage": "Candidate reranker LOCO",
            "command": "work/agent_memory_experiment/candidate_reranker_loco_experiment.py",
            "notes": "Uses cached rankings.csv; leave-one-conversation-out split.",
        },
        {
            "stage": "Intrinsic candidate reranker LOCO",
            "command": "work/agent_memory_experiment/candidate_reranker_intrinsic_loco_experiment.py",
            "notes": "Reuses leave-one-conversation-out split with intrinsic-only candidate features.",
        },
        {
            "stage": "Intrinsic reranker method appendix",
            "command": "work/agent_memory_experiment/generate_intrinsic_reranker_method_appendix.py",
            "notes": "Builds a paper appendix with feature definitions, model hyperparameters, validation protocol, and reproducible commands.",
        },
        {
            "stage": "Bootstrap metric CI",
            "command": "work/agent_memory_experiment/bootstrap_metric_ci.py",
            "notes": "Computes query-level bootstrap confidence intervals for main, LOCO, router, and Type3 paired results.",
        },
        {
            "stage": "Type3 diagnostics",
            "command": "work/agent_memory_experiment/type3_coverage_significance_analysis.py",
            "notes": "Aggregates Type3 coverage significance tests.",
        },
        {
            "stage": "Type3 query decomposition fusion4",
            "command": "work/agent_memory_experiment/type3_query_decomposition_experiment.py",
            "notes": "Records the stronger keyword-facet decomposition fusion variant and its negative result.",
        },
        {
            "stage": "Type3 supervised set selector variants",
            "command": "work/agent_memory_experiment/type3_supervised_set_selector_experiment.py",
            "notes": "Records rw=0 and rw=-0.02 greedy set-selector variants for Type3 negative-result analysis.",
        },
        {
            "stage": "Embedding baseline status",
            "command": "work/agent_memory_experiment/generate_embedding_baseline_status.py",
            "notes": "Tracks API embedding baseline readiness without reading or printing keys.",
        },
        {
            "stage": "Embedding provider profiles",
            "command": "work/agent_memory_experiment/generate_embedding_provider_profiles.py",
            "notes": "Lists OpenAI and generic OpenAI-compatible provider commands for preflight, estimate, run, and compare.",
        },
        {
            "stage": "API embedding preflight",
            "command": "work/agent_memory_experiment/preflight_api_embedding_baseline.py",
            "notes": "Checks inputs, key availability, cache paths, and result summary before paid/API embedding runs.",
        },
        {
            "stage": "Mock API embedding smoke test",
            "command": "work/agent_memory_experiment/mock_api_embedding_smoke_test.py",
            "notes": "Runs the API embedding backend against a localhost OpenAI-compatible mock and verifies cache hits.",
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
            "stage": "LLM-assisted audit",
            "command": "work/agent_memory_experiment/llm_audit_retrieval_errors.py",
            "notes": "Uses DeepSeek to draft audit labels for human review; does not replace human audit.",
        },
        {
            "stage": "Human/LLM audit confirmation",
            "command": "work/agent_memory_experiment/confirm_llm_audit_labels.py",
            "notes": "Creates a human-confirmation sheet and summarizes agreement after manual labels are filled.",
        },
        {
            "stage": "Human/LLM priority20 audit",
            "command": "work/agent_memory_experiment/generate_priority_audit_subset.py",
            "notes": "Selects a 20-sample quick-review subset and reuses the agreement workflow.",
        },
        {
            "stage": "Blinded human audit sheets",
            "command": "work/agent_memory_experiment/blind_human_audit_labels.py",
            "notes": "Exports blind review sheets that hide LLM-assisted labels and can merge human labels back.",
        },
        {
            "stage": "Human audit review packet",
            "command": "work/agent_memory_experiment/generate_human_audit_review_packet.py",
            "notes": "Renders a readable Markdown review packet from the blinded priority20 sheet without exposing LLM-assisted labels.",
        },
        {
            "stage": "Dual human audit agreement",
            "command": "work/agent_memory_experiment/dual_human_audit_agreement.py",
            "notes": "Prepares two-annotator review sheets and reports exact agreement, partial-credit agreement, and Cohen's kappa.",
        },
        {
            "stage": "Human audit readiness gate",
            "command": "work/agent_memory_experiment/validate_human_audit_readiness.py",
            "notes": "Checks whether priority20/full80 human confirmations can support paper claims.",
        },
        {
            "stage": "Evidence matrix",
            "command": "work/agent_memory_experiment/generate_evidence_matrix.py",
            "notes": "Summarizes paper claims, evidence strength, and remaining gaps.",
        },
        {
            "stage": "Paper draft outline",
            "command": "work/agent_memory_experiment/generate_paper_draft_outline.py",
            "notes": "Builds a Chinese paper skeleton from current evidence, formulas, and result tables.",
        },
        {
            "stage": "Paper manuscript draft",
            "command": "work/agent_memory_experiment/generate_paper_manuscript.py",
            "notes": "Generates an editable Chinese manuscript draft from cached experiment outputs.",
        },
        {
            "stage": "Paper manuscript claim check",
            "command": "work/agent_memory_experiment/validate_manuscript_claims.py",
            "notes": "Checks that the draft does not overclaim pending embedding or human-audit results.",
        },
        {
            "stage": "Submission readiness gate",
            "command": "work/agent_memory_experiment/validate_submission_readiness.py",
            "notes": "Aggregates reproducibility, baseline, human-audit, and reviewer-risk gates before final submission.",
        },
        {
            "stage": "Public release readiness gate",
            "command": "work/agent_memory_experiment/validate_public_release_readiness.py",
            "notes": "Scans tracked files for secret-like strings, .env hygiene, release metadata, and artifact links.",
        },
        {
            "stage": "Artifact integrity manifest",
            "command": "work/agent_memory_experiment/generate_artifact_integrity_manifest.py",
            "notes": "Writes sha256, size, and line-count metadata for all reproducibility artifacts.",
        },
        {
            "stage": "Submission gap analysis",
            "command": "work/agent_memory_experiment/generate_submission_gap_analysis.py",
            "notes": "Ranks reviewer-facing risks and minimum actions before submission.",
        },
        {
            "stage": "Experiment protocol",
            "command": "work/agent_memory_experiment/generate_experiment_protocol.py",
            "notes": "Builds a paper appendix-style protocol from cached metrics and artifacts.",
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
    write_report(args.output_report, artifact_rows, metric_rows, command_rows, data_rows, env_rows, writer_ready)
    print(json.dumps({
        "output_report": str(args.output_report),
        "artifacts": f"{sum(1 for row in artifact_rows if row['exists'])}/{len(artifact_rows)}",
        "metrics": f"{sum(1 for row in metric_rows if row['pass'])}/{len(metric_rows)}",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
