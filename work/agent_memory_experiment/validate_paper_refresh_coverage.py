#!/usr/bin/env python3
"""Validate coverage of the offline paper artifact refresh pipeline."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


REQUIRED_STEPS = [
    ("offline_embedding_sensitivity", "encoder sensitivity diagnostic"),
    ("human_audit_execution_plan", "human audit execution plan"),
    ("human_audit_annotation_codebook", "human audit codebook with label rules and agreement formulas"),
    ("human_audit_sample_qc", "human audit sample coverage and progress QC"),
    ("human_audit_labeling_dashboard", "human audit per-row labeling progress dashboard"),
    ("human_audit_annotation_interface", "offline human audit HTML annotation interface"),
    ("human_audit_annotation_interface_validation", "human audit annotation interface safety validation"),
    ("human_audit_annotation_import_readiness", "human audit annotation export import readiness check"),
    ("human_audit_paper_claim_upgrade", "human audit paper-claim upgrade gate"),
    ("human_audit_blind_review_leakage", "human audit blind review schema and leakage audit"),
    ("human_audit_protocol_compliance", "human audit protocol compliance and closure audit"),
    ("type3_coverage_aware_reranker", "Type3 coverage-aware reranking negative-result diagnostic"),
    ("type3_intent_fusion_reranker", "Type3 intent-facet conservative window-reranking diagnostic"),
    ("type3_rescue_space_analysis", "Type3 Top-20 rescue-space and recall-missing diagnostic"),
    ("type3_supervised_window_reranker", "Type3 supervised conservative window-reranking diagnostic"),
    ("type3_recall_expansion_analysis", "Type3 offline recall-expansion diagnostic"),
    ("type3_expanded_pool_selector", "Type3 expanded-pool Top-5 evidence selector diagnostic"),
    ("type3_learned_expanded_selector", "Type3 learned expanded-pool selector diagnostic"),
    ("embedding_baseline_status", "external embedding status without network calls"),
    ("embedding_provider_profiles", "provider-specific external embedding command profiles"),
    ("api_embedding_preflight", "paid/API embedding preflight"),
    ("api_embedding_run_estimate", "API embedding cost/cache estimate"),
    ("writer_cost_boundary", "one-time memory-write cost vs reusable storage-token boundary"),
    ("api_embedding_execution_runbook", "external API embedding execution and acceptance runbook"),
    ("embedding_baseline_comparison", "BGE-M3 vs API embedding comparison status"),
    ("api_embedding_postrun_gate", "API embedding post-run completeness gate"),
    ("api_embedding_paper_acceptance", "strict API embedding paper acceptance gate"),
    ("external_embedding_blocker_audit", "external embedding blocker audit"),
    ("embedding_paper_claim_upgrade", "embedding baseline paper-claim upgrade gate"),
    ("submission_blocker_closure_plan", "submission blocker closure path"),
    ("submission_closure_consistency", "submission closure artifact consistency audit"),
    ("submission_package_index", "paper package index"),
    ("supplementary_package_manifest", "supplementary package manifest and anonymization audit"),
    ("submission_package_consistency", "submission package index and manifest consistency audit"),
    ("anonymous_submission_readiness", "anonymous submission package readiness audit"),
    ("paper_table_consistency", "paper table consistency audit"),
    ("untracked_artifact_audit", "untracked artifact hygiene audit"),
    ("large_intermediate_provenance", "large local intermediate provenance audit"),
    ("artifact_path_portability", "paper-facing artifact path portability audit"),
    ("public_release_readiness", "public release readiness gate"),
    ("reproducibility_checklist", "artifact and metric gates"),
    ("artifact_integrity_manifest", "artifact integrity manifest"),
    ("evidence_matrix", "claim/evidence/gap matrix"),
    ("submission_gap_analysis", "reviewer risk matrix"),
    ("submission_readiness", "final submission gates"),
    ("final_submission_checklist", "action-oriented final submission checklist"),
    ("reviewer_response_prep", "reviewer response prep"),
    ("paper_manuscript", "manuscript draft"),
    ("manuscript_claim_check", "manuscript claim check"),
    ("manuscript_numeric_claim_check", "manuscript numeric claim consistency check"),
    ("paper_scope_claim_audit", "paper-facing scope and generalization claim audit"),
    ("evidence_freshness", "stale evidence audit"),
    ("submission_entrypoint_consistency", "submission readiness entrypoint consistency audit"),
]

EXCLUDED_BY_DESIGN = [
    ("external_api_embedding_run", "requires paid/network API key"),
    ("human_label_filling", "requires human judgment"),
    ("full80_adjudication", "requires independent annotators/adjudication"),
]


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


def build_rows(refresh_csv: Path) -> list[dict[str, Any]]:
    refresh_rows = read_csv(refresh_csv)
    by_step = {row.get("step", ""): row for row in refresh_rows}
    rows: list[dict[str, Any]] = []
    for step, purpose in REQUIRED_STEPS:
        row = by_step.get(step, {})
        rows.append({
            "group": "required_offline_step",
            "item": step,
            "purpose": purpose,
            "present": str(bool(row)),
            "pass": str(bool(row) and row.get("status") == "pass"),
            "evidence": row.get("status", "missing"),
            "action": "Keep in refresh_paper_artifacts.py and rerun after relevant artifacts change.",
        })
    for step, purpose in EXCLUDED_BY_DESIGN:
        rows.append({
            "group": "excluded_by_design",
            "item": step,
            "purpose": purpose,
            "present": "False",
            "pass": "True",
            "evidence": "intentionally excluded from offline refresh pipeline",
            "action": "Run manually only after external input is available.",
        })
    return rows


def write_report(path: Path, rows: list[dict[str, Any]], refresh_csv: Path) -> None:
    required = [row for row in rows if row["group"] == "required_offline_step"]
    missing = [row for row in required if row["present"] != "True"]
    failing = [row for row in required if row["pass"] != "True"]
    table = [
        [row["group"], row["item"], row["pass"], row["purpose"], row["evidence"], row["action"]]
        for row in rows
    ]
    lines = [
        "# Paper Refresh Coverage Audit",
        "",
        "本文件检查离线论文 artifact 刷新流水线是否覆盖关键报告。它只验证本地缓存/离线报告刷新，不把真实外部 embedding API 或人工标注纳入自动流水线。",
        "",
        "## 总览",
        "",
        f"- Refresh CSV: `{refresh_csv}`",
        f"- Required offline steps: {len(required)}",
        f"- Missing required steps: {len(missing)}",
        f"- Failing required steps: {len(failing)}",
        "",
        "## 覆盖检查",
        "",
        markdown_table(["Group", "Item", "Pass", "Purpose", "Evidence", "Action"], table),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：paper artifact refresh pipeline 已覆盖当前离线报告闭环。",
        "- 应谨慎：coverage audit 只保证刷新脚本覆盖报告，不保证 blocker 已解除。",
        "- 不能写：外部 embedding baseline 或人工审计已由该流水线自动完成。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate paper refresh pipeline coverage.")
    parser.add_argument("--refresh-csv", type=Path, default=Path("outputs/agent_memory_paper_artifact_refresh_run.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_paper_refresh_coverage_audit.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_paper_refresh_coverage_audit_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.refresh_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.refresh_csv)
    required = [row for row in rows if row["group"] == "required_offline_step"]
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "required_steps": len(required),
        "missing": sum(1 for row in required if row["present"] != "True"),
        "failing": sum(1 for row in required if row["pass"] != "True"),
    })


if __name__ == "__main__":
    main()
