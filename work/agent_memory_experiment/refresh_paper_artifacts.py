#!/usr/bin/env python3
"""Refresh paper-facing artifacts from cached/offline experiment outputs."""

from __future__ import annotations

import argparse
import csv
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Step:
    name: str
    args: list[str]
    notes: str


def py(script: str, *args: str) -> list[str]:
    return [sys.executable, f"work/agent_memory_experiment/{script}", *args]


def build_steps(include_environment: bool) -> list[Step]:
    steps = [
        Step(
            "offline_embedding_sensitivity",
            py(
                "generate_offline_embedding_sensitivity.py",
                "--bge-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv",
                "--hash-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_hash_type_004_with_keyword/summary.csv",
                "--output-csv",
                "outputs/agent_memory_offline_embedding_sensitivity.csv",
                "--output-report",
                "outputs/agent_memory_offline_embedding_sensitivity_zh.md",
            ),
            "Refreshes offline hash/BM25 vs BGE-M3 encoder-sensitivity diagnostics.",
        ),
        Step(
            "human_audit_execution_plan",
            py(
                "generate_human_audit_execution_plan.py",
                "--outputs-dir",
                "outputs",
                "--output-report",
                "outputs/agent_memory_human_audit_execution_plan_zh.md",
                "--output-csv",
                "outputs/agent_memory_human_audit_execution_plan.csv",
            ),
            "Refreshes the human-audit labeling execution plan from current gates.",
        ),
        Step(
            "human_audit_annotation_codebook",
            py(
                "generate_human_audit_annotation_codebook.py",
                "--project-root",
                ".",
                "--output-report",
                "outputs/agent_memory_human_audit_annotation_codebook_zh.md",
                "--output-schema",
                "outputs/agent_memory_human_audit_annotation_schema.csv",
            ),
            "Refreshes the human-audit annotation codebook, allowed labels, formulas, and recomputation commands.",
        ),
        Step(
            "human_audit_sample_qc",
            py(
                "validate_human_audit_sample_qc.py",
                "--priority-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--full-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--output-csv",
                "outputs/agent_memory_human_audit_sample_qc.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_sample_qc_zh.md",
            ),
            "Checks priority20/full80 human-audit sample size, uniqueness, coverage, and labeling progress.",
        ),
        Step(
            "human_audit_labeling_dashboard",
            py(
                "generate_human_audit_labeling_dashboard.py",
                "--priority-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--full-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--output-csv",
                "outputs/agent_memory_human_audit_labeling_dashboard.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_labeling_dashboard_zh.md",
            ),
            "Refreshes per-row human-audit labeling progress and next-item dashboard.",
        ),
        Step(
            "human_audit_annotation_interface",
            py(
                "generate_human_audit_annotation_interface.py",
                "--priority-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--full-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--priority-html",
                "outputs/agent_memory_human_audit_priority20_annotation.html",
                "--full-html",
                "outputs/agent_memory_human_audit_full80_annotation.html",
                "--output-csv",
                "outputs/agent_memory_human_audit_annotation_interface.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_annotation_interface_zh.md",
            ),
            "Generates offline HTML annotation interfaces for priority20/full80 blind-review sheets.",
        ),
        Step(
            "human_audit_annotation_interface_validation",
            py(
                "validate_human_audit_annotation_interface.py",
                "--priority-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--full-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--priority-html",
                "outputs/agent_memory_human_audit_priority20_annotation.html",
                "--full-html",
                "outputs/agent_memory_human_audit_full80_annotation.html",
                "--output-csv",
                "outputs/agent_memory_human_audit_annotation_interface_validation.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_annotation_interface_validation_zh.md",
            ),
            "Validates that generated annotation HTML matches blind CSVs and hides LLM-assisted labels.",
        ),
        Step(
            "human_audit_annotation_import_readiness",
            py(
                "validate_human_audit_annotation_import.py",
                "--priority-source-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--priority-export-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--priority-confirmation-csv",
                "outputs/agent_memory_human_llm_audit_priority20_confirmation.csv",
                "--full-source-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--full-export-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--full-confirmation-csv",
                "outputs/agent_memory_human_llm_audit_confirmation.csv",
                "--output-csv",
                "outputs/agent_memory_human_audit_annotation_import_readiness.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_annotation_import_readiness_zh.md",
            ),
            "Checks whether HTML-exported human labels are ready to merge into confirmation sheets.",
        ),
        Step(
            "human_audit_paper_claim_upgrade",
            py(
                "validate_human_audit_paper_claim_upgrade.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_human_audit_paper_claim_upgrade.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_paper_claim_upgrade_zh.md",
            ),
            "Checks which paper-facing human-audit claim tier is currently unlocked.",
        ),
        Step(
            "human_audit_blind_review_leakage",
            py(
                "validate_human_audit_blind_review.py",
                "--priority-csv",
                "outputs/agent_memory_human_audit_priority20_blind_review.csv",
                "--full-csv",
                "outputs/agent_memory_human_audit_full80_blind_review.csv",
                "--output-csv",
                "outputs/agent_memory_human_audit_blind_review_leakage.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_blind_review_leakage_zh.md",
            ),
            "Checks that blinded human-audit review sheets do not expose LLM-assisted labels and follow the expected schema.",
        ),
        Step(
            "human_audit_protocol_compliance",
            py(
                "validate_human_audit_protocol_compliance.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_human_audit_protocol_compliance.csv",
                "--output-report",
                "outputs/agent_memory_human_audit_protocol_compliance_zh.md",
            ),
            "Checks that human-audit samples, schemas, codebook, interfaces, import checks, and claim gates form a protocol-ready package.",
        ),
        Step(
            "type3_coverage_aware_reranker",
            py(
                "type3_coverage_aware_reranker.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--ks",
                "1,3,5,20",
                "--output-per-query",
                "outputs/agent_memory_type3_coverage_aware_per_query.csv",
                "--output-ranked",
                "outputs/agent_memory_type3_coverage_aware_ranked_top20.csv",
                "--output-summary",
                "outputs/agent_memory_type3_coverage_aware_summary.csv",
                "--output-deltas",
                "outputs/agent_memory_type3_coverage_aware_deltas.csv",
                "--output-report",
                "outputs/agent_memory_type3_coverage_aware_zh.md",
            ),
            "Tests unsupervised coverage-aware Type3 reranking over cached Top-20 candidates.",
        ),
        Step(
            "type3_intent_fusion_reranker",
            py(
                "type3_intent_fusion_reranker.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--ks",
                "1,3,5,20",
                "--facet-weight",
                "0.35",
                "--facet-hit-weight",
                "0.002",
                "--output-per-query",
                "outputs/agent_memory_type3_intent_fusion_per_query.csv",
                "--output-ranked",
                "outputs/agent_memory_type3_intent_fusion_ranked_top20.csv",
                "--output-summary",
                "outputs/agent_memory_type3_intent_fusion_summary.csv",
                "--output-deltas",
                "outputs/agent_memory_type3_intent_fusion_deltas.csv",
                "--output-facets",
                "outputs/agent_memory_type3_intent_fusion_facets.csv",
                "--output-report",
                "outputs/agent_memory_type3_intent_fusion_zh.md",
            ),
            "Tests conservative Type3 intent-facet window reranking without changing Top-5 evidence membership.",
        ),
        Step(
            "type3_rescue_space_analysis",
            py(
                "type3_rescue_space_analysis.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--output-per-query",
                "outputs/agent_memory_type3_rescue_space_per_query.csv",
                "--output-summary",
                "outputs/agent_memory_type3_rescue_space_summary.csv",
                "--output-classes",
                "outputs/agent_memory_type3_rescue_space_classes.csv",
                "--output-report",
                "outputs/agent_memory_type3_rescue_space_zh.md",
            ),
            "Classifies Type3 errors into Top-20 rerank-rescuable and candidate-recall-missing cases.",
        ),
        Step(
            "type3_supervised_window_reranker",
            py(
                "type3_supervised_window_reranker.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--output-per-query",
                "outputs/agent_memory_type3_supervised_window_per_query.csv",
                "--output-ranked",
                "outputs/agent_memory_type3_supervised_window_ranked_top20.csv",
                "--output-summary",
                "outputs/agent_memory_type3_supervised_window_summary.csv",
                "--output-deltas",
                "outputs/agent_memory_type3_supervised_window_deltas.csv",
                "--output-selected",
                "outputs/agent_memory_type3_supervised_window_selected_params.csv",
                "--output-feature-importance",
                "outputs/agent_memory_type3_supervised_window_feature_importance.csv",
                "--output-report",
                "outputs/agent_memory_type3_supervised_window_zh.md",
            ),
            "Tests dependency-free supervised Type3 window reranking with held-out query splits.",
        ),
        Step(
            "type3_recall_expansion_analysis",
            py(
                "type3_recall_expansion_analysis.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--output-per-query",
                "outputs/agent_memory_type3_recall_expansion_per_query.csv",
                "--output-summary",
                "outputs/agent_memory_type3_recall_expansion_summary.csv",
                "--output-deltas",
                "outputs/agent_memory_type3_recall_expansion_deltas.csv",
                "--output-report",
                "outputs/agent_memory_type3_recall_expansion_zh.md",
            ),
            "Tests offline Type3 recall expansion by merging candidate Top-20 with multi-signal and intent-facet retrieval pools.",
        ),
        Step(
            "type3_expanded_pool_selector",
            py(
                "type3_expanded_pool_selector.py",
                "--candidate-ranked",
                "outputs/agent_memory_candidate_reranker_locomo10_ranked_top20.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--keep-top1",
                "--redundancy-weight",
                "0.02",
                "--output-per-query",
                "outputs/agent_memory_type3_expanded_pool_selector_per_query.csv",
                "--output-ranked",
                "outputs/agent_memory_type3_expanded_pool_selector_ranked_top20.csv",
                "--output-summary",
                "outputs/agent_memory_type3_expanded_pool_selector_summary.csv",
                "--output-deltas",
                "outputs/agent_memory_type3_expanded_pool_selector_deltas.csv",
                "--output-report",
                "outputs/agent_memory_type3_expanded_pool_selector_zh.md",
            ),
            "Tests whether expanded Type3 candidate pools can be converted into Top-5 evidence selection gains.",
        ),
        Step(
            "embedding_baseline_status",
            py(
                "generate_embedding_baseline_status.py",
                "--output-report",
                "outputs/agent_memory_embedding_baseline_status_zh.md",
                "--output-csv",
                "outputs/agent_memory_embedding_baseline_status.csv",
                "--env-file",
                ".env",
            ),
            "Refreshes external embedding key/result status without printing keys.",
        ),
        Step(
            "embedding_provider_profiles",
            py(
                "generate_embedding_provider_profiles.py",
                "--env-file",
                ".env",
                "--output-csv",
                "outputs/agent_memory_embedding_provider_profiles.csv",
                "--output-report",
                "outputs/agent_memory_embedding_provider_profiles_zh.md",
            ),
            "Refreshes provider-specific preflight, estimate, run, and compare commands.",
        ),
        Step(
            "api_embedding_preflight",
            py(
                "preflight_api_embedding_baseline.py",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--result-dir",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004",
                "--method",
                "type_aware",
                "--provider-label",
                "OpenAI text-embedding-3-small",
                "--model",
                "text-embedding-3-small",
                "--base-url",
                "https://api.openai.com/v1",
                "--batch-size",
                "128",
                "--embedding-cache-dir",
                "work/agent_memory_experiment/cache/embeddings",
                "--api-key-env",
                "OPENAI_API_KEY",
                "--env-file",
                ".env",
                "--output-csv",
                "outputs/agent_memory_api_embedding_preflight.csv",
                "--output-report",
                "outputs/agent_memory_api_embedding_preflight_zh.md",
            ),
            "Refreshes paid/API embedding preflight without network calls.",
        ),
        Step(
            "api_embedding_run_estimate",
            py(
                "estimate_api_embedding_run.py",
                "--memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--model",
                "text-embedding-3-small",
                "--base-url",
                "https://api.openai.com/v1",
                "--batch-size",
                "128",
                "--embedding-cache-dir",
                "work/agent_memory_experiment/cache/embeddings",
                "--output-csv",
                "outputs/agent_memory_api_embedding_run_estimate.csv",
                "--output-report",
                "outputs/agent_memory_api_embedding_run_estimate_zh.md",
            ),
            "Refreshes API embedding item/token/batch estimate without network calls.",
        ),
        Step(
            "writer_cost_boundary",
            py(
                "generate_writer_cost_boundary.py",
                "--usage",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3/usage.csv",
                "--fact-memories",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl",
                "--observation-memories",
                "work/agent_memory_experiment/data/locomo_observation_all_answerable_memories.jsonl",
                "--writer-aggregate",
                "outputs/agent_memory_writer_stability_aggregate.csv",
                "--output-csv",
                "outputs/agent_memory_writer_cost_boundary.csv",
                "--output-report",
                "outputs/agent_memory_writer_cost_boundary_zh.md",
            ),
            "Separates one-time LLM memory-write API tokens from reusable retrieval-time storage tokens.",
        ),
        Step(
            "api_embedding_execution_runbook",
            py(
                "generate_api_embedding_execution_runbook.py",
                "--profile-csv",
                "outputs/agent_memory_embedding_provider_profiles.csv",
                "--preflight-csv",
                "outputs/agent_memory_api_embedding_preflight.csv",
                "--estimate-csv",
                "outputs/agent_memory_api_embedding_run_estimate.csv",
                "--postrun-csv",
                "outputs/agent_memory_api_embedding_postrun_gate.csv",
                "--output-csv",
                "outputs/agent_memory_api_embedding_execution_runbook.csv",
                "--output-report",
                "outputs/agent_memory_api_embedding_execution_runbook_zh.md",
            ),
            "Generates the external API embedding baseline runbook without starting paid/network calls.",
        ),
        Step(
            "embedding_baseline_comparison",
            py(
                "compare_embedding_baselines.py",
                "--bge-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv",
                "--api-summary",
                "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004/summary.csv",
                "--method",
                "type_aware",
                "--api-label",
                "OpenAI text-embedding-3-small",
                "--output-csv",
                "outputs/agent_memory_embedding_baseline_comparison.csv",
                "--output-report",
                "outputs/agent_memory_embedding_baseline_comparison_zh.md",
            ),
            "Refreshes BGE-M3 vs API embedding comparison status from local summaries.",
        ),
        Step(
            "api_embedding_postrun_gate",
            py(
                "validate_api_embedding_postrun.py",
                "--profile-csv",
                "outputs/agent_memory_embedding_provider_profiles.csv",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_api_embedding_postrun_gate.csv",
                "--output-report",
                "outputs/agent_memory_api_embedding_postrun_gate_zh.md",
            ),
            "Checks whether any API embedding run has complete paper-ready local outputs.",
        ),
        Step(
            "api_embedding_paper_acceptance",
            py(
                "validate_api_embedding_paper_acceptance.py",
                "--profile-csv",
                "outputs/agent_memory_embedding_provider_profiles.csv",
                "--queries",
                "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl",
                "--outputs-dir",
                "outputs",
                "--rank-output-k",
                "20",
                "--output-csv",
                "outputs/agent_memory_api_embedding_paper_acceptance.csv",
                "--output-report",
                "outputs/agent_memory_api_embedding_paper_acceptance_zh.md",
            ),
            "Strictly checks API embedding result scale, metrics, per-query rows, rankings, by-type coverage, and comparison deltas before paper citation.",
        ),
        Step(
            "external_embedding_blocker_audit",
            py(
                "generate_external_embedding_blocker_audit.py",
                "--outputs-dir",
                "outputs",
                "--output-report",
                "outputs/agent_memory_external_embedding_blocker_audit_zh.md",
                "--output-csv",
                "outputs/agent_memory_external_embedding_blocker_audit.csv",
            ),
            "Refreshes actionable blocker audit for external embedding baselines.",
        ),
        Step(
            "embedding_paper_claim_upgrade",
            py(
                "validate_embedding_paper_claim_upgrade.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_embedding_paper_claim_upgrade.csv",
                "--output-report",
                "outputs/agent_memory_embedding_paper_claim_upgrade_zh.md",
            ),
            "Checks which paper-facing embedding-baseline claim tier is currently unlocked.",
        ),
        Step(
            "submission_blocker_closure_plan",
            py(
                "generate_submission_blocker_closure_plan.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_submission_blocker_closure_plan.csv",
                "--output-report",
                "outputs/agent_memory_submission_blocker_closure_plan_zh.md",
            ),
            "Refreshes the ordered closure path for final-submission blockers.",
        ),
        Step(
            "submission_closure_consistency",
            py(
                "validate_submission_closure_consistency.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_submission_closure_consistency.csv",
                "--output-report",
                "outputs/agent_memory_submission_closure_consistency_zh.md",
            ),
            "Checks closure plan, final checklist, readiness, reviewer prep, and strict API acceptance for consistent blocker standards.",
        ),
        Step(
            "submission_package_index",
            py(
                "generate_submission_package_index.py",
                "--project-root",
                ".",
                "--output-report",
                "outputs/agent_memory_submission_package_index_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_package_index.csv",
            ),
            "Refreshes the index of manuscript, tables, appendices, gates, and packaging actions.",
        ),
        Step(
            "supplementary_package_manifest",
            py(
                "generate_supplementary_package_manifest.py",
                "--project-root",
                ".",
                "--package-index-csv",
                "outputs/agent_memory_submission_package_index.csv",
                "--reproducibility-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
                "--readiness-csv",
                "outputs/agent_memory_submission_readiness.csv",
                "--output-csv",
                "outputs/agent_memory_supplementary_package_manifest.csv",
                "--output-report",
                "outputs/agent_memory_supplementary_package_manifest_zh.md",
            ),
            "Builds a supplement packaging manifest with blocker and anonymization checks.",
        ),
        Step(
            "submission_package_consistency",
            py(
                "validate_submission_package_consistency.py",
                "--project-root",
                ".",
                "--package-index-csv",
                "outputs/agent_memory_submission_package_index.csv",
                "--supplement-manifest-csv",
                "outputs/agent_memory_supplementary_package_manifest.csv",
                "--reproducibility-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
                "--integrity-csv",
                "outputs/agent_memory_artifact_integrity_manifest.csv",
                "--output-csv",
                "outputs/agent_memory_submission_package_consistency.csv",
                "--output-report",
                "outputs/agent_memory_submission_package_consistency_zh.md",
            ),
            "Checks package index coverage across supplement manifest, reproducibility list, and integrity manifest.",
        ),
        Step(
            "anonymous_submission_readiness",
            py(
                "validate_anonymous_submission_readiness.py",
                "--project-root",
                ".",
                "--manifest-csv",
                "outputs/agent_memory_supplementary_package_manifest.csv",
                "--output-csv",
                "outputs/agent_memory_anonymous_submission_readiness.csv",
                "--output-report",
                "outputs/agent_memory_anonymous_submission_readiness_zh.md",
            ),
            "Checks anonymous-submission readiness for current supplement candidates.",
        ),
        Step(
            "paper_table_consistency",
            py(
                "validate_paper_table_consistency.py",
                "--project-root",
                ".",
                "--outputs-dir",
                "outputs",
                "--markdown",
                "outputs/agent_memory_paper_tables_zh.md",
                "--latex",
                "outputs/agent_memory_paper_tables.tex",
                "--output-csv",
                "outputs/agent_memory_paper_table_consistency.csv",
                "--output-report",
                "outputs/agent_memory_paper_table_consistency_zh.md",
            ),
            "Checks that paper Markdown/LaTeX tables are byte-identical to regenerated CSV-derived outputs.",
        ),
        Step(
            "untracked_artifact_audit",
            py(
                "audit_untracked_artifacts.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_untracked_artifact_audit.csv",
                "--output-report",
                "outputs/agent_memory_untracked_artifact_audit_zh.md",
            ),
            "Classifies untracked local outputs before public artifact packaging.",
        ),
        Step(
            "large_intermediate_provenance",
            py(
                "validate_large_intermediate_provenance.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_large_intermediate_provenance.csv",
                "--output-report",
                "outputs/agent_memory_large_intermediate_provenance_zh.md",
            ),
            "Audits large local ranked/per-query intermediates against README commands and tracked downstream summaries.",
        ),
        Step(
            "artifact_path_portability",
            py(
                "validate_artifact_path_portability.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_artifact_path_portability.csv",
                "--output-report",
                "outputs/agent_memory_artifact_path_portability_zh.md",
            ),
            "Checks tracked paper-facing reports for machine-local absolute paths before artifact sharing.",
        ),
        Step(
            "public_release_readiness",
            py(
                "validate_public_release_readiness.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_public_release_readiness.csv",
                "--output-report",
                "outputs/agent_memory_public_release_readiness_zh.md",
            ),
            "Refreshes tracked-file release hygiene checks after untracked artifact audit.",
        ),
    ]
    if include_environment:
        steps.extend([
            Step(
                "environment_snapshot",
                py(
                    "generate_environment_snapshot.py",
                    "--project-root",
                    ".",
                    "--output-report",
                    "outputs/agent_memory_environment_snapshot_zh.md",
                    "--output-packages",
                    "outputs/agent_memory_environment_packages.csv",
                    "--output-system",
                    "outputs/agent_memory_environment_system.csv",
                ),
                "Refreshes Python/package/cache/Git environment snapshot using the current Python executable.",
            ),
            Step(
                "environment_freshness",
                py(
                    "validate_environment_snapshot_freshness.py",
                    "--project-root",
                    ".",
                    "--system-csv",
                    "outputs/agent_memory_environment_system.csv",
                    "--output-csv",
                    "outputs/agent_memory_environment_freshness_audit.csv",
                    "--output-report",
                    "outputs/agent_memory_environment_freshness_audit_zh.md",
                ),
                "Checks generation-time environment snapshot freshness.",
            ),
        ])
    steps.extend([
        Step(
            "reproducibility_checklist",
            py(
                "generate_reproducibility_checklist.py",
                "--output-report",
                "outputs/agent_memory_reproducibility_checklist_zh.md",
                "--output-artifacts",
                "outputs/agent_memory_reproducibility_artifacts.csv",
                "--output-metrics",
                "outputs/agent_memory_reproducibility_metrics.csv",
            ),
            "Refreshes artifact and metric gates.",
        ),
        Step(
            "artifact_integrity_manifest",
            py(
                "generate_artifact_integrity_manifest.py",
                "--output-report",
                "outputs/agent_memory_artifact_integrity_manifest_zh.md",
                "--output-csv",
                "outputs/agent_memory_artifact_integrity_manifest.csv",
                "--artifact-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
            ),
            "Refreshes artifact sha256/size/line-count manifest.",
        ),
        Step(
            "evidence_matrix",
            py(
                "generate_evidence_matrix.py",
                "--output-report",
                "outputs/agent_memory_paper_evidence_matrix_zh.md",
                "--output-csv",
                "outputs/agent_memory_paper_evidence_matrix.csv",
            ),
            "Refreshes paper claim/evidence/gap matrix.",
        ),
        Step(
            "submission_gap_analysis",
            py(
                "generate_submission_gap_analysis.py",
                "--output-report",
                "outputs/agent_memory_submission_gap_analysis_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_gap_analysis.csv",
            ),
            "Refreshes reviewer-facing risk matrix.",
        ),
        Step(
            "submission_readiness",
            py(
                "validate_submission_readiness.py",
                "--output-report",
                "outputs/agent_memory_submission_readiness_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_readiness.csv",
            ),
            "Refreshes final-submission gates.",
        ),
        Step(
            "final_submission_checklist",
            py(
                "generate_final_submission_checklist.py",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_final_submission_checklist.csv",
                "--output-report",
                "outputs/agent_memory_final_submission_checklist_zh.md",
            ),
            "Refreshes the action-oriented final-submission checklist.",
        ),
        Step(
            "reviewer_response_prep",
            py(
                "generate_reviewer_response_prep.py",
                "--output-report",
                "outputs/agent_memory_reviewer_response_prep_zh.md",
                "--output-csv",
                "outputs/agent_memory_reviewer_response_prep.csv",
            ),
            "Refreshes reviewer question/answer preparation matrix.",
        ),
        Step(
            "paper_manuscript",
            py(
                "generate_paper_manuscript.py",
                "--project-root",
                ".",
                "--output-report",
                "outputs/agent_memory_manuscript_draft_zh.md",
            ),
            "Refreshes Chinese manuscript draft from current evidence.",
        ),
        Step(
            "manuscript_claim_check",
            py(
                "validate_manuscript_claims.py",
                "--manuscript",
                "outputs/agent_memory_manuscript_draft_zh.md",
                "--outputs-dir",
                "outputs",
                "--output-csv",
                "outputs/agent_memory_manuscript_claim_check.csv",
                "--output-report",
                "outputs/agent_memory_manuscript_claim_check_zh.md",
            ),
            "Checks that manuscript does not overclaim pending baselines/audits.",
        ),
        Step(
            "manuscript_numeric_claim_check",
            py(
                "validate_manuscript_numeric_claims.py",
                "--project-root",
                ".",
                "--outputs-dir",
                "outputs",
                "--manuscript",
                "outputs/agent_memory_manuscript_draft_zh.md",
                "--output-csv",
                "outputs/agent_memory_manuscript_numeric_claim_check.csv",
                "--output-report",
                "outputs/agent_memory_manuscript_numeric_claim_check_zh.md",
            ),
            "Checks that key numeric manuscript claims match current paper artifacts.",
        ),
        Step(
            "paper_scope_claim_audit",
            py(
                "validate_paper_scope_claims.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_paper_scope_claim_audit.csv",
                "--output-report",
                "outputs/agent_memory_paper_scope_claim_audit_zh.md",
            ),
            "Audits paper-facing documents for scope and generalization overclaims.",
        ),
        Step(
            "evidence_freshness",
            py(
                "validate_evidence_freshness.py",
                "--output-csv",
                "outputs/agent_memory_evidence_freshness_audit.csv",
                "--output-report",
                "outputs/agent_memory_evidence_freshness_audit_zh.md",
            ),
            "Checks stale artifact/metric/integrity gate counts.",
        ),
        Step(
            "submission_entrypoint_consistency",
            py(
                "validate_submission_entrypoint_consistency.py",
                "--project-root",
                ".",
                "--output-csv",
                "outputs/agent_memory_submission_entrypoint_consistency.csv",
                "--output-report",
                "outputs/agent_memory_submission_entrypoint_consistency_zh.md",
            ),
            "Checks that README/package/reproducibility entrypoints point to the current submission readiness artifact.",
        ),
        Step(
            "paper_refresh_coverage",
            py(
                "validate_paper_refresh_coverage.py",
                "--refresh-csv",
                "outputs/agent_memory_paper_artifact_refresh_run.csv",
                "--output-csv",
                "outputs/agent_memory_paper_refresh_coverage_audit.csv",
                "--output-report",
                "outputs/agent_memory_paper_refresh_coverage_audit_zh.md",
            ),
            "Checks that the offline refresh run covers all required paper-facing reports.",
        ),
        Step(
            "artifact_integrity_manifest_final",
            py(
                "generate_artifact_integrity_manifest.py",
                "--output-report",
                "outputs/agent_memory_artifact_integrity_manifest_zh.md",
                "--output-csv",
                "outputs/agent_memory_artifact_integrity_manifest.csv",
                "--artifact-csv",
                "outputs/agent_memory_reproducibility_artifacts.csv",
            ),
            "Final manifest refresh after freshness audit changes.",
        ),
        Step(
            "submission_readiness_final",
            py(
                "validate_submission_readiness.py",
                "--output-report",
                "outputs/agent_memory_submission_readiness_zh.md",
                "--output-csv",
                "outputs/agent_memory_submission_readiness.csv",
            ),
            "Final submission gate refresh after manifest changes.",
        ),
    ])
    return steps


def portable_arg(arg: str, cwd: Path) -> str:
    path = Path(arg)
    if path.is_absolute():
        try:
            return str(path.relative_to(cwd.resolve()))
        except ValueError:
            return arg
    return arg


def command_string(args: list[str], cwd: Path) -> str:
    return " ".join(shlex.quote(portable_arg(arg, cwd)) for arg in args)


def run_step(step: Step, cwd: Path, dry_run: bool) -> dict[str, Any]:
    start = time.time()
    row: dict[str, Any] = {
        "step": step.name,
        "command": command_string(step.args, cwd),
        "notes": step.notes,
        "status": "dry_run" if dry_run else "pending",
        "returncode": "",
        "duration_sec": "0.000",
    }
    if dry_run:
        return row
    result = subprocess.run(step.args, cwd=cwd, text=True, capture_output=True)
    row["returncode"] = result.returncode
    row["duration_sec"] = f"{time.time() - start:.3f}"
    row["status"] = "pass" if result.returncode == 0 else "fail"
    if result.stdout.strip():
        row["stdout_tail"] = result.stdout.strip().splitlines()[-1][:500]
    else:
        row["stdout_tail"] = ""
    if result.stderr.strip():
        row["stderr_tail"] = result.stderr.strip().splitlines()[-1][:500]
    else:
        row["stderr_tail"] = ""
    if result.returncode != 0:
        raise RuntimeError(f"Step failed: {step.name}\n{result.stderr}\n{result.stdout}")
    return row


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step", "status", "returncode", "duration_sec", "notes", "command", "stdout_tail", "stderr_tail"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], include_environment: bool, dry_run: bool) -> None:
    failures = [row for row in rows if row["status"] == "fail"]
    table = [
        [row["step"], row["status"], str(row.get("returncode", "")), str(row["duration_sec"]), row["notes"]]
        for row in rows
    ]
    lines = [
        "# Paper Artifact Refresh Run",
        "",
        "本文件记录一次论文 artifact 离线刷新流水线的执行结果。该流水线只调用本地已缓存结果和无网络脚本；不会运行真实外部 embedding API，也不会自动填写人工标签。",
        "",
        "## 总览",
        "",
        f"- Dry run: {dry_run}",
        f"- Include environment snapshot: {include_environment}",
        f"- Steps: {len(rows)}",
        f"- Failures: {len(failures)}",
        "",
        "## Step Results",
        "",
        markdown_table(["Step", "Status", "Return Code", "Duration Sec", "Notes"], table),
        "",
        "## 使用边界",
        "",
        "- 可以用于补完 API baseline 或人工标签后的最终报告刷新。",
        "- 不能替代真实外部 embedding baseline，也不能替代人工审计填写。",
        "- 如果刷新后 artifact 数变化，应再次运行 freshness audit 并检查 submission readiness。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh paper-facing artifacts from cached/offline outputs.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--include-environment", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_paper_artifact_refresh_run.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_paper_artifact_refresh_run_zh.md"))
    args = parser.parse_args()

    rows = []
    for step in build_steps(args.include_environment):
        rows.append(run_step(step, args.project_root, args.dry_run))
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.include_environment, args.dry_run)
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "steps": len(rows),
        "failures": sum(1 for row in rows if row["status"] == "fail"),
        "dry_run": args.dry_run,
    })


if __name__ == "__main__":
    main()
