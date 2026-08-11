#!/usr/bin/env python3
"""Validate which paper claims are unlocked by current human-audit evidence."""

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
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    return {}


def as_int(value: str | int | None) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def readiness_summary(rows: list[dict[str, str]], label: str) -> dict[str, Any]:
    row = lookup(rows, label=label)
    return {
        "samples": as_int(row.get("samples")),
        "min_required": as_int(row.get("min_required")),
        "confirmed": as_int(row.get("confirmed_samples")),
        "missing": as_int(row.get("missing_human_fields")),
        "invalid": as_int(row.get("invalid_labels")),
        "status": row.get("status", "missing"),
    }


def agreement_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    samples = lookup(rows, group="overview", label="samples", value="total")
    confirmed = lookup(rows, group="overview", label="confirmed_samples", value="fully_confirmed")
    invalid = lookup(rows, group="overview", label="validation_errors", value="invalid_labels")
    fields = []
    for label in ("auto_reason_correct", "top_memory_relevant", "gold_memory_sufficient"):
        exact = lookup(rows, group="agreement", label=label, value="exact")
        fields.append(f"{label}: exact={float(exact.get('share', 0) or 0):.3f}, kappa={exact.get('kappa', '')}")
    return {
        "samples": as_int(samples.get("count")),
        "confirmed": as_int(confirmed.get("count")),
        "invalid": as_int(invalid.get("count")),
        "field_summary": "; ".join(fields),
    }


def dual_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    samples = lookup(rows, group="overview", label="samples", value="total")
    both = lookup(rows, group="overview", label="both_labeled", value="complete_a_b")
    adjudicated = lookup(rows, group="overview", label="adjudicated", value="complete_adjudication")
    invalid = lookup(rows, group="overview", label="validation_errors", value="invalid_labels")
    fields = []
    for label in ("auto_reason_correct", "top_memory_relevant", "gold_memory_sufficient"):
        exact = lookup(rows, group="inter_annotator", label=label, value="exact")
        fields.append(f"{label}: exact={float(exact.get('share', 0) or 0):.3f}, kappa={exact.get('kappa', '')}")
    return {
        "samples": as_int(samples.get("count")),
        "both_labeled": as_int(both.get("count")),
        "adjudicated": as_int(adjudicated.get("count")),
        "invalid": as_int(invalid.get("count")),
        "field_summary": "; ".join(fields),
    }


def gate_row(
    tier: str,
    required_evidence: str,
    passed: bool,
    evidence: str,
    allowed_claim: str,
    forbidden_claim: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "tier": tier,
        "required_evidence": required_evidence,
        "pass": passed,
        "status": "pass" if passed else "pending",
        "evidence": evidence,
        "allowed_paper_claim": allowed_claim,
        "forbidden_paper_claim": forbidden_claim,
        "next_action": next_action,
    }


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    readiness = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    priority = readiness_summary(readiness, "priority20")
    full = readiness_summary(readiness, "full80")
    priority_agreement = agreement_summary(read_csv(outputs / "agent_memory_human_llm_audit_priority20_agreement.csv"))
    full_agreement = agreement_summary(read_csv(outputs / "agent_memory_human_llm_audit_agreement.csv"))
    priority_dual = dual_summary(read_csv(outputs / "agent_memory_human_audit_priority20_dual_agreement.csv"))
    full_dual = dual_summary(read_csv(outputs / "agent_memory_human_audit_full80_dual_agreement.csv"))

    priority_single_pass = priority["confirmed"] >= 20 and priority["invalid"] == 0 and priority_agreement["confirmed"] >= 20
    full_single_pass = full["confirmed"] >= 80 and full["invalid"] == 0 and full_agreement["confirmed"] >= 80
    priority_dual_pass = priority_dual["both_labeled"] >= 20 and priority_dual["invalid"] == 0
    full_dual_pass = full_dual["both_labeled"] >= 80 and full_dual["invalid"] == 0
    full_adjudicated_pass = full_dual["adjudicated"] >= 80 and full_dual["invalid"] == 0

    rows = [
        gate_row(
            "protocol_only",
            "Blind review sheets, codebook, annotation interface, and import checks exist.",
            True,
            "annotation interface and import readiness artifacts are tracked in the reproducibility package",
            "可以写：已准备 human-confirmation protocol、blind review sheets 和回填验收脚本。",
            "不能写：human-verified error analysis 或人工一致性结果已经完成。",
            "填写 priority20 single-blind human_* 字段。",
        ),
        gate_row(
            "priority20_quick_review",
            "20/20 priority samples have valid single-human labels and Human/LLM agreement is recomputed.",
            priority_single_pass,
            f"priority20 confirmed={priority['confirmed']}/20, invalid={priority['invalid']}; agreement confirmed={priority_agreement['confirmed']}/20",
            "可以写：priority20 quick-review Human/LLM agreement，并把它作为小样本人工抽查。",
            "不能写：完整错误分析已经 human-verified。",
            "完成 full80 single-blind labels；若追求更强证据，再完成 priority20 dual A/B。",
        ),
        gate_row(
            "priority20_dual_review",
            "20/20 priority samples have two independent annotators; optional adjudication is reported if complete.",
            priority_dual_pass,
            f"priority20 A/B both_labeled={priority_dual['both_labeled']}/20, adjudicated={priority_dual['adjudicated']}/20, invalid={priority_dual['invalid']}",
            "可以写：priority20 inter-annotator agreement，作为错误分析标注可靠性的快速证据。",
            "不能写：full80 人工错误分析已完成。",
            "扩展 full80 single-blind 或 full80 dual labels。",
        ),
        gate_row(
            "full80_single_review",
            "80/80 full samples have valid single-human labels and Human/LLM agreement is recomputed.",
            full_single_pass,
            f"full80 confirmed={full['confirmed']}/80, invalid={full['invalid']}; agreement confirmed={full_agreement['confirmed']}/80",
            "可以写：full80 Human/LLM error-audit agreement，支撑完整人工确认的错误分析。",
            "不能写：双人一致性或仲裁完成，除非 dual gate 也通过。",
            "完成 full80 dual A/B labels 或在论文中明确 single-review limitation。",
        ),
        gate_row(
            "full80_dual_review",
            "80/80 full samples have two independent annotators.",
            full_dual_pass,
            f"full80 A/B both_labeled={full_dual['both_labeled']}/80, adjudicated={full_dual['adjudicated']}/80, invalid={full_dual['invalid']}",
            "可以写：full80 inter-annotator agreement，并报告 exact agreement 与 Cohen's kappa。",
            "不能写：已使用仲裁标签作为最终分布，除非 adjudication gate 也通过。",
            "对 A/B 冲突样本填写 adjudicated_* 字段。",
        ),
        gate_row(
            "human_verified_ready",
            "80/80 full samples have two independent labels and adjudicated labels.",
            full_dual_pass and full_adjudicated_pass,
            f"full80 adjudicated={full_dual['adjudicated']}/80, invalid={full_dual['invalid']}",
            "可以写：human-verified error analysis，并以 adjudicated labels 作为论文错误类型分布。",
            "不能写：跨数据集人工可靠性，除非新增第二数据集标注。",
            "刷新 gap analysis、reviewer response、manuscript、claim checks 和 submission readiness。",
        ),
    ]
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
    passed = [row for row in rows if row["pass"]]
    highest = passed[-1]["tier"] if passed else "none"
    table_rows = [
        [
            row["tier"],
            row["status"],
            row["evidence"],
            row["allowed_paper_claim"],
            row["next_action"],
        ]
        for row in rows
    ]
    lines = [
        "# Human Audit Paper-Claim Upgrade Gate",
        "",
        "本文件把人工审计从“协议已准备”到“可写入论文的人工可靠性证据”分成多个门槛。它不会自动填写人工标签，也不会把 LLM-assisted 预标注当成人工结果。",
        "",
        "## 总览",
        "",
        f"- Claim tiers: {len(rows)}",
        f"- Passed tiers: {len(passed)}/{len(rows)}",
        f"- Highest unlocked tier: `{highest}`",
        "",
        "## 门槛明细",
        "",
        markdown_table(["Tier", "Status", "Evidence", "Allowed Paper Claim", "Next Action"], table_rows),
        "",
        "## 使用边界",
        "",
        "- 可以把本报告作为人工标注后的验收入口，决定论文中能升级到哪一种表述。",
        "- 在 `priority20_quick_review` 之前，只能写 protocol-ready，不能写人工一致性结果。",
        "- 在 `full80_single_review` 之前，不建议把错误分析写成完整 human-confirmed evidence。",
        "- 只有 `human_verified_ready` 通过后，才适合写强版本的 human-verified error analysis。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate human-audit paper-claim upgrade tiers.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "passed_tiers": f"{sum(1 for row in rows if row['pass'])}/{len(rows)}",
        "highest_unlocked_tier": [row["tier"] for row in rows if row["pass"]][-1],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
