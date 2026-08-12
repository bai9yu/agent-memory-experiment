#!/usr/bin/env python3
"""Generate a concrete closure plan for remaining final-submission blockers."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
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


def by_key(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    readiness = read_csv(outputs / "agent_memory_submission_readiness.csv")
    external = read_csv(outputs / "agent_memory_external_embedding_blocker_audit.csv")
    human = read_csv(outputs / "agent_memory_human_audit_execution_plan.csv")

    api_gate = by_key(readiness, "gate", "api_embedding_preflight")
    external_gate = by_key(readiness, "gate", "external_embedding_completed")
    priority_gate = by_key(readiness, "gate", "priority20_human_audit")
    full_gate = by_key(readiness, "gate", "full80_human_audit")
    reviewer_gate = by_key(readiness, "gate", "reviewer_risk_blockers")

    external_key = by_key(external, "item", "default_openai_key")
    external_summary = by_key(external, "item", "external_summary_completed")
    external_acceptance = by_key(external, "item", "api_embedding_paper_acceptance")
    priority_step = by_key(human, "stage", "priority20 single blind labeling")
    full_step = by_key(human, "stage", "full80 single blind labeling")

    return [
        {
            "order": 1,
            "blocker_group": "external_embedding_preflight",
            "current_gate": api_gate.get("evidence", ""),
            "minimum_action": external_key.get("required_action", "Set an external embedding key and rerun preflight."),
            "acceptance_criterion": "api_embedding_preflight pass=True; no key value is written to Git.",
            "primary_command": "preflight_api_embedding_baseline.py",
            "paper_upgrade": "API baseline can move from pending protocol to safe-to-run experiment.",
            "depends_on": "embedding API key or OpenAI-compatible provider key",
        },
        {
            "order": 2,
            "blocker_group": "external_embedding_completed",
            "current_gate": external_gate.get("evidence", ""),
            "minimum_action": external_summary.get("required_action", "Run memory_eval.py with semantic-backend api.") + " Then run compare, postrun gate, and strict paper acceptance.",
            "acceptance_criterion": "summary/per-query/rankings/summary_by_type exist; compare_embedding_baselines.py reports numeric deltas; validate_api_embedding_postrun.py passes; validate_api_embedding_paper_acceptance.py reports paper_acceptance_pass=1.",
            "primary_command": "memory_eval.py --semantic-backend api; compare_embedding_baselines.py; validate_api_embedding_postrun.py; validate_api_embedding_paper_acceptance.py",
            "paper_upgrade": "External embedding baseline can be added to the embedding comparison table only after strict paper acceptance passes.",
            "depends_on": "external_embedding_preflight",
            "secondary_evidence": external_acceptance.get("evidence", ""),
        },
        {
            "order": 3,
            "blocker_group": "priority20_human_audit",
            "current_gate": priority_gate.get("evidence", ""),
            "minimum_action": priority_step.get("required_action", "Fill priority20 human_* fields."),
            "acceptance_criterion": priority_step.get("pass_condition", "20/20 samples have valid labels."),
            "primary_command": "blind_human_audit_labels.py merge; confirm_llm_audit_labels.py; validate_human_audit_readiness.py",
            "paper_upgrade": priority_step.get("paper_claim_enabled", "quick-review agreement can be reported."),
            "depends_on": "human annotation time",
        },
        {
            "order": 4,
            "blocker_group": "full80_human_audit",
            "current_gate": full_gate.get("evidence", ""),
            "minimum_action": full_step.get("required_action", "Fill full80 human_* fields."),
            "acceptance_criterion": full_step.get("pass_condition", "80/80 samples have valid labels."),
            "primary_command": "blind_human_audit_labels.py merge; confirm_llm_audit_labels.py; validate_human_audit_readiness.py",
            "paper_upgrade": full_step.get("paper_claim_enabled", "full Human/LLM audit agreement can be reported."),
            "depends_on": "priority20 protocol stable; human annotation time",
        },
        {
            "order": 5,
            "blocker_group": "reviewer_risk_blockers",
            "current_gate": reviewer_gate.get("evidence", ""),
            "minimum_action": "Regenerate reviewer response prep and submission gap analysis after external embedding and human audit gates pass.",
            "acceptance_criterion": "reviewer_risk_blockers pass=True and blocker risks=0.",
            "primary_command": "generate_submission_gap_analysis.py; generate_reviewer_response_prep.py; validate_submission_readiness.py",
            "paper_upgrade": "The manuscript can move from internal draft to final-submission candidate.",
            "depends_on": "external_embedding_completed; priority20/full80_human_audit",
        },
        {
            "order": 6,
            "blocker_group": "final_consistency_refresh",
            "current_gate": "freshness/integrity/claim checks must remain synchronized",
            "minimum_action": "Run evidence matrix, manuscript, claim check, reproducibility checklist, artifact manifest, freshness audit, and submission readiness after blocker closure.",
            "acceptance_criterion": "claim failures=0; stale_count_findings=0; artifact gate passes; final submission readiness=True.",
            "primary_command": "generate_evidence_matrix.py; generate_paper_manuscript.py; validate_manuscript_claims.py; validate_evidence_freshness.py",
            "paper_upgrade": "Final paper claims and appendix evidence are aligned with completed experiments.",
            "depends_on": "all required blockers closed",
        },
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    table_rows = [
        [
            str(row["order"]),
            row["blocker_group"],
            row["current_gate"],
            row["minimum_action"],
            row["acceptance_criterion"],
            row["paper_upgrade"],
        ]
        for row in rows
    ]
    lines = [
        "# Submission Blocker Closure Plan",
        "",
        "本文件把最终投稿前仍未通过的 gate 串成最短关闭路线。它不会把 pending 项写成完成结果；它的作用是说明下一次拿到 API key 或人工标签后，应该按什么顺序执行、用什么证据判断通过，以及论文措辞可以如何升级。",
        "",
        "## 总览",
        "",
        f"- Closure steps: {len(rows)}",
        "- Hard external input: embedding API key; human labels for priority20/full80.",
        "- Current status: protocol-ready, not final-submission ready.",
        "",
        "## 关闭路线",
        "",
        markdown_table(
            ["Order", "Blocker Group", "Current Gate", "Minimum Action", "Acceptance Criterion", "Paper Upgrade"],
            table_rows,
        ),
        "",
        "## 依赖图",
        "",
        "```mermaid",
        "flowchart TD",
        "  A[\"Embedding API key\"] --> B[\"API preflight pass\"]",
        "  B --> C[\"External embedding summary.csv\"]",
        "  C --> D[\"Embedding comparison delta table\"]",
        "  D --> D2[\"Postrun + paper acceptance pass\"]",
        "  E[\"priority20 human labels\"] --> F[\"quick-review agreement\"]",
        "  F --> G[\"full80 human labels\"]",
        "  G --> H[\"full human audit agreement\"]",
        "  D2 --> I[\"Reviewer blocker risks = 0\"]",
        "  H --> I",
        "  I --> J[\"Final consistency refresh\"]",
        "  J --> K[\"Submission readiness = True\"]",
        "```",
        "",
        "## 执行边界",
        "",
        "- 可以先关闭 priority20，形成小样本 quick-review evidence；但最终投稿仍需要 full80 或在论文中明确写成 limited audit。",
        "- 可以先跑一个外部 embedding provider；不必同时跑 OpenAI 和 generic provider。",
        "- 每关闭一个 blocker 后都必须刷新 submission gap、reviewer response、manuscript claim check 和 freshness audit。",
        "- 在 external_embedding_completed 和 human audit gates 通过前，正文仍应保留 pending/limitation 措辞。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate submission blocker closure plan.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_submission_blocker_closure_plan.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_submission_blocker_closure_plan_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "steps": len(rows),
    })


if __name__ == "__main__":
    main()
