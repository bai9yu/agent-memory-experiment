#!/usr/bin/env python3
"""Validate the human-audit protocol package before manual labels are filled."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


BLIND_REQUIRED_FIELDS = {
    "review_order",
    "audit_id",
    "query_id",
    "query",
    "query_type",
    "auto_reason",
    "first_rank",
    "top_memory_id",
    "top_memory_type",
    "top_memory_text",
    "gold_memory_ids",
    "gold_memory_types",
    "gold_memory_texts",
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
}

DUAL_REQUIRED_FIELDS = {
    "review_order",
    "audit_id",
    "query_id",
    "query",
    "query_type",
    "auto_reason",
    "first_rank",
    "top_memory_id",
    "top_memory_text",
    "gold_memory_ids",
    "gold_memory_texts",
    "annotator_a_manual_reason",
    "annotator_a_auto_reason_correct",
    "annotator_a_top_memory_relevant",
    "annotator_a_gold_memory_sufficient",
    "annotator_a_notes",
    "annotator_b_manual_reason",
    "annotator_b_auto_reason_correct",
    "annotator_b_top_memory_relevant",
    "annotator_b_gold_memory_sufficient",
    "annotator_b_notes",
    "adjudicated_manual_reason",
    "adjudicated_auto_reason_correct",
    "adjudicated_top_memory_relevant",
    "adjudicated_gold_memory_sufficient",
    "adjudicator_notes",
}

CODEBOOK_TOKENS = {
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "gold_below_top20",
    "memory_type_mismatch",
    "temporal_neighbor",
    "entity_confusion",
    "multi_evidence_missing",
    "gold_insufficient",
    "Cohen's kappa",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_header(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return next(csv.reader(f), [])


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


def row(
    group: str,
    item: str,
    passed: bool,
    severity: str,
    evidence: str,
    action: str,
) -> dict[str, Any]:
    return {
        "group": group,
        "item": item,
        "pass": passed,
        "severity": severity,
        "status": "pass" if passed else severity,
        "evidence": evidence,
        "action": action,
    }


def duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def check_expected_csv(scope: str, path: Path, expected_rows: int, required_fields: set[str], group: str) -> list[dict[str, Any]]:
    rows = read_csv(path)
    header = set(read_header(path))
    audit_ids = [r.get("audit_id", "") for r in rows]
    missing_fields = sorted(required_fields - header)
    duplicates = duplicate_values([audit_id for audit_id in audit_ids if audit_id])
    blank_ids = sum(1 for audit_id in audit_ids if not audit_id)
    return [
        row(
            group,
            f"{scope}_exists",
            path.exists() and path.stat().st_size > 0,
            "blocker",
            f"{path}, rows={len(rows)}",
            "Regenerate the human-audit CSV from the current audit sample.",
        ),
        row(
            group,
            f"{scope}_row_count",
            len(rows) == expected_rows,
            "blocker",
            f"rows={len(rows)}, expected={expected_rows}",
            "Regenerate the scope with the expected sample size.",
        ),
        row(
            group,
            f"{scope}_schema",
            not missing_fields,
            "blocker",
            "missing=" + (";".join(missing_fields) if missing_fields else "none"),
            "Regenerate the CSV with the standard human-audit schema.",
        ),
        row(
            group,
            f"{scope}_audit_ids_unique",
            not duplicates and blank_ids == 0,
            "blocker",
            f"duplicates={duplicates[:10]}, blank_ids={blank_ids}",
            "Regenerate the CSV so each row has one stable non-empty audit_id.",
        ),
    ]


def lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    for r in rows:
        if all(r.get(k) == v for k, v in filters.items()):
            return r
    return {}


def check_codebook(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    missing = sorted(token for token in CODEBOOK_TOKENS if token not in text)
    has_flow = "flowchart TD" in text
    has_commands = "blind_human_audit_labels.py merge" in text and "confirm_llm_audit_labels.py" in text
    return [
        row(
            "protocol_documentation",
            "codebook_exists",
            path.exists() and path.stat().st_size > 0,
            "blocker",
            f"{path}, size={path.stat().st_size if path.exists() else 0}",
            "Regenerate the human-audit annotation codebook.",
        ),
        row(
            "protocol_documentation",
            "codebook_fields_and_labels",
            not missing,
            "major",
            "missing=" + (";".join(missing) if missing else "none"),
            "Add required fields, reason labels, and agreement terminology to the codebook.",
        ),
        row(
            "protocol_documentation",
            "codebook_decision_flow",
            has_flow,
            "major",
            "flowchart TD present" if has_flow else "decision flow missing",
            "Add a decision flow so annotators follow a stable order.",
        ),
        row(
            "protocol_documentation",
            "codebook_recompute_commands",
            has_commands,
            "major",
            "merge/agreement commands present" if has_commands else "merge/agreement commands missing",
            "Add merge and agreement recomputation commands to the codebook.",
        ),
    ]


def check_existing_gate_csv(name: str, path: Path, allowed_problem_statuses: set[str]) -> list[dict[str, Any]]:
    rows = read_csv(path)
    statuses = [r.get("status", "") for r in rows]
    bad_statuses = sorted({s for s in statuses if s and s not in {"pass", "info", *allowed_problem_statuses}})
    blockers = sum(1 for r in rows if r.get("status") == "blocker")
    major = sum(1 for r in rows if r.get("status") == "major")
    return [
        row(
            "upstream_validation",
            f"{name}_exists",
            path.exists() and len(rows) > 0,
            "blocker",
            f"{path}, rows={len(rows)}",
            "Regenerate the upstream human-audit validation artifact.",
        ),
        row(
            "upstream_validation",
            f"{name}_no_protocol_blockers",
            blockers == 0 and major == 0 and not bad_statuses,
            "blocker",
            f"blockers={blockers}, major={major}, other_problem_statuses={bad_statuses}",
            "Fix protocol/schema/interface problems before sending the packet to annotators.",
        ),
    ]


def check_import_readiness(path: Path) -> list[dict[str, Any]]:
    rows = read_csv(path)
    statuses = {r.get("scope", ""): r.get("status", "") for r in rows}
    allowed = {"pending_human_labels", "ready_to_merge"}
    bad = {scope: status for scope, status in statuses.items() if status not in allowed}
    return [
        row(
            "upstream_validation",
            "annotation_import_readiness_exists",
            path.exists() and len(rows) == 2,
            "blocker",
            f"{path}, scopes={sorted(statuses)}",
            "Regenerate annotation import readiness for priority20 and full80.",
        ),
        row(
            "upstream_validation",
            "annotation_import_pending_or_ready",
            not bad,
            "blocker",
            f"statuses={statuses}",
            "Fix invalid exported labels, row order, duplicate audit IDs, or schema mismatch before merge.",
        ),
    ]


def check_sample_qc(path: Path) -> list[dict[str, Any]]:
    rows = read_csv(path)
    sample_priority = lookup(rows, scope="priority20", group="overview", value="sample_count")
    sample_full = lookup(rows, scope="full80", group="overview", value="sample_count")
    duplicate_priority = lookup(rows, scope="priority20", group="overview", value="duplicate_audit_ids")
    duplicate_full = lookup(rows, scope="full80", group="overview", value="duplicate_audit_ids")
    coverage_rows = [r for r in rows if r.get("group") == "coverage"]
    coverage_failed = [r for r in coverage_rows if r.get("status") != "pass"]
    return [
        row(
            "sample_design",
            "sample_counts",
            sample_priority.get("status") == "pass" and sample_full.get("status") == "pass",
            "blocker",
            f"priority20={sample_priority.get('count', 'missing')}/20; full80={sample_full.get('count', 'missing')}/80",
            "Regenerate priority20/full80 samples with expected row counts.",
        ),
        row(
            "sample_design",
            "sample_unique_ids",
            duplicate_priority.get("status") == "pass" and duplicate_full.get("status") == "pass",
            "blocker",
            f"priority20_duplicates={duplicate_priority.get('count', 'missing')}; full80_duplicates={duplicate_full.get('count', 'missing')}",
            "Regenerate audit IDs before collecting labels.",
        ),
        row(
            "sample_design",
            "sample_coverage",
            not coverage_failed,
            "major",
            f"failed_coverage_checks={len(coverage_failed)}",
            "Check auto-reason, query-type, and rank-bucket coverage before labeling.",
        ),
    ]


def check_human_label_gates(readiness_csv: Path, claim_csv: Path) -> list[dict[str, Any]]:
    readiness = read_csv(readiness_csv)
    priority = lookup(readiness, label="priority20")
    full = lookup(readiness, label="full80")
    claim_rows = read_csv(claim_csv)
    protocol = lookup(claim_rows, tier="protocol_only")
    quick = lookup(claim_rows, tier="priority20_quick_review")
    full_single = lookup(claim_rows, tier="full80_single_review")
    return [
        row(
            "human_label_gate",
            "protocol_only_claim_unlocked",
            protocol.get("status") == "pass",
            "blocker",
            protocol.get("evidence", "missing"),
            "Regenerate protocol artifacts before discussing human-audit protocol in the paper.",
        ),
        row(
            "human_label_gate",
            "priority20_labels_pending",
            priority.get("confirmed_samples") == "0" and quick.get("status") == "pending",
            "info",
            f"priority20 confirmed={priority.get('confirmed_samples', 'missing')}/20; claim_tier={quick.get('status', 'missing')}",
            "Fill priority20 human_* fields to unlock quick-review agreement.",
        ),
        row(
            "human_label_gate",
            "full80_labels_pending",
            full.get("confirmed_samples") == "0" and full_single.get("status") == "pending",
            "info",
            f"full80 confirmed={full.get('confirmed_samples', 'missing')}/80; claim_tier={full_single.get('status', 'missing')}",
            "Fill full80 human_* fields to unlock full Human/LLM audit agreement.",
        ),
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [r for r in rows if r["status"] == "blocker"]
    major = [r for r in rows if r["status"] == "major"]
    protocol_rows = [r for r in rows if r["group"] != "human_label_gate"]
    protocol_ready = not [r for r in protocol_rows if r["status"] in {"blocker", "major"}]
    table = [[r["group"], r["item"], str(r["pass"]), r["status"], r["evidence"], r["action"]] for r in rows]
    lines = [
        "# Human Audit Protocol Compliance",
        "",
        "本文件检查人工审计流程是否已经具备论文级可执行性：样本、盲审隔离、标注字段、HTML 标注入口、导入检查、协议文档和 claim tier 都必须闭环。它不填写人工标签，也不把 protocol-ready 误写成人工审计完成。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major issues: {len(major)}",
        f"- Protocol ready for human labeling: {protocol_ready}",
        "- Human labels completed: False",
        "",
        "## 检查明细",
        "",
        markdown_table(["Group", "Item", "Pass", "Status", "Evidence", "Action"], table),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：人工审计协议、盲审材料、标注界面、回填检查和 claim gate 已形成可复现闭环。",
        "- 可以写：当前人审 blocker 是外部人工标签尚未填写，而不是协议或工程入口缺失。",
        "- 不能写：human-verified error analysis、priority20 agreement 或 full80 agreement 已完成，除非相应 human_* 字段填写并重算 agreement。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.extend(check_codebook(outputs / "agent_memory_human_audit_annotation_codebook_zh.md"))
    rows.extend(check_sample_qc(outputs / "agent_memory_human_audit_sample_qc.csv"))
    rows.extend(check_expected_csv("priority20_blind", outputs / "agent_memory_human_audit_priority20_blind_review.csv", 20, BLIND_REQUIRED_FIELDS, "blind_review_schema"))
    rows.extend(check_expected_csv("full80_blind", outputs / "agent_memory_human_audit_full80_blind_review.csv", 80, BLIND_REQUIRED_FIELDS, "blind_review_schema"))
    rows.extend(check_expected_csv("priority20_dual", outputs / "agent_memory_human_audit_priority20_dual_review.csv", 20, DUAL_REQUIRED_FIELDS, "dual_review_schema"))
    rows.extend(check_expected_csv("full80_dual", outputs / "agent_memory_human_audit_full80_dual_review.csv", 80, DUAL_REQUIRED_FIELDS, "dual_review_schema"))
    rows.extend(check_existing_gate_csv("blind_review_leakage", outputs / "agent_memory_human_audit_blind_review_leakage.csv", set()))
    rows.extend(check_existing_gate_csv("annotation_interface_validation", outputs / "agent_memory_human_audit_annotation_interface_validation.csv", set()))
    rows.extend(check_import_readiness(outputs / "agent_memory_human_audit_annotation_import_readiness.csv"))
    rows.extend(check_human_label_gates(outputs / "agent_memory_human_audit_readiness_gate.csv", outputs / "agent_memory_human_audit_paper_claim_upgrade.csv"))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate human-audit protocol compliance.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_human_audit_protocol_compliance.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_human_audit_protocol_compliance_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    protocol_rows = [r for r in rows if r["group"] != "human_label_gate"]
    blockers = sum(1 for r in rows if r["status"] == "blocker")
    major = sum(1 for r in rows if r["status"] == "major")
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "checks": len(rows),
        "blockers": blockers,
        "major": major,
        "protocol_ready_for_human_labeling": not [r for r in protocol_rows if r["status"] in {"blocker", "major"}],
        "human_labels_completed": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
