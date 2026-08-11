#!/usr/bin/env python3
"""Generate a paper-facing execution plan for human audit completion."""

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


def lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(k) == v for k, v in filters.items()):
            return row
    return {}


def count_rows(path: Path) -> int:
    return len(read_csv(path))


def build_steps(outputs: Path) -> list[dict[str, Any]]:
    readiness = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    priority = lookup(readiness, label="priority20")
    full = lookup(readiness, label="full80")
    priority_dual = read_csv(outputs / "agent_memory_human_audit_priority20_dual_agreement.csv")
    full_dual = read_csv(outputs / "agent_memory_human_audit_full80_dual_agreement.csv")

    priority_both = lookup(priority_dual, group="overview", label="both_labeled")
    priority_adj = lookup(priority_dual, group="overview", label="adjudicated")
    full_both = lookup(full_dual, group="overview", label="both_labeled")
    full_adj = lookup(full_dual, group="overview", label="adjudicated")

    return [
        {
            "step": "1",
            "stage": "priority20 single blind labeling",
            "status": "pending" if priority.get("status") != "pass" else "pass",
            "artifact_to_edit": "outputs/agent_memory_human_audit_priority20_blind_review.csv",
            "required_action": "Fill human_manual_reason, human_auto_reason_correct, human_top_memory_relevant, human_gold_memory_sufficient, and human_auditor_notes for all 20 rows.",
            "current_evidence": f"confirmed={priority.get('confirmed_samples', '0')}/{priority.get('min_required', '20')}; missing_fields={priority.get('missing_human_fields', '')}; invalid={priority.get('invalid_labels', '')}",
            "pass_condition": "20/20 samples have valid human_* labels after merge and agreement recomputation.",
            "paper_claim_enabled": "quick-review Human/LLM agreement can be reported.",
        },
        {
            "step": "2",
            "stage": "priority20 dual independent labeling",
            "status": "pending" if priority_both.get("count") != "20" else "pass",
            "artifact_to_edit": "outputs/agent_memory_human_audit_priority20_dual_review.csv",
            "required_action": "Annotator A and B independently fill their own columns; do not copy LLM-assisted labels or each other's labels.",
            "current_evidence": f"both_labeled={priority_both.get('count', '0')}/20; adjudicated={priority_adj.get('count', '0')}/20",
            "pass_condition": "Both annotators complete 20 rows; conflicts are adjudicated when needed.",
            "paper_claim_enabled": "inter-annotator exact agreement, partial-credit agreement, and Cohen's kappa can be reported for priority20.",
        },
        {
            "step": "3",
            "stage": "full80 single blind labeling",
            "status": "pending" if full.get("status") != "pass" else "pass",
            "artifact_to_edit": "outputs/agent_memory_human_audit_full80_blind_review.csv",
            "required_action": "Complete the same human_* fields for all 80 rows after priority20 labels are stable.",
            "current_evidence": f"confirmed={full.get('confirmed_samples', '0')}/{full.get('min_required', '80')}; missing_fields={full.get('missing_human_fields', '')}; invalid={full.get('invalid_labels', '')}",
            "pass_condition": "80/80 samples have valid human_* labels after merge and agreement recomputation.",
            "paper_claim_enabled": "full Human/LLM audit agreement can be reported.",
        },
        {
            "step": "4",
            "stage": "full80 dual independent labeling",
            "status": "pending" if full_both.get("count") != "80" else "pass",
            "artifact_to_edit": "outputs/agent_memory_human_audit_full80_dual_review.csv",
            "required_action": "Annotator A and B fill full80 independently; adjudicator resolves disagreements.",
            "current_evidence": f"both_labeled={full_both.get('count', '0')}/80; adjudicated={full_adj.get('count', '0')}/80",
            "pass_condition": "Both annotators complete 80 rows and adjudication is complete.",
            "paper_claim_enabled": "human-verified error analysis can be written with stronger reliability evidence.",
        },
        {
            "step": "5",
            "stage": "paper refresh after human labels",
            "status": "waiting_on_labels",
            "artifact_to_edit": "generated reports",
            "required_action": "Regenerate agreement, human readiness, submission gap/readiness, evidence matrix, manuscript, claim check, reproducibility checklist, and manifest.",
            "current_evidence": "Current paper-facing reports correctly state human audit is pending.",
            "pass_condition": "No stale evidence findings; manuscript claim check has 0 failures; submission readiness human gates pass.",
            "paper_claim_enabled": "Upgrade wording from protocol-only to measured human-audit reliability.",
        },
    ]


def write_report(path: Path, outputs: Path, rows: list[dict[str, Any]]) -> None:
    pending = sum(1 for row in rows if row["status"] != "pass")
    priority_n = count_rows(outputs / "agent_memory_human_audit_priority20_blind_review.csv")
    full_n = count_rows(outputs / "agent_memory_human_audit_full80_blind_review.csv")

    table = [
        [
            row["step"],
            row["stage"],
            row["status"],
            row["artifact_to_edit"],
            row["current_evidence"],
            row["pass_condition"],
        ]
        for row in rows
    ]

    lines = [
        "# Human Audit Execution Plan",
        "",
        "本文件把人工复核 blocker 拆成可执行步骤，用于从当前 protocol-ready 状态推进到论文可报告的人类一致性证据。它不自动填写人工标签，也不把 LLM-assisted 预标注当成人工结果。",
        "",
        "## 总览",
        "",
        f"- Pending execution steps: {pending}/{len(rows)}",
        f"- priority20 blind samples: {priority_n}",
        f"- full80 blind samples: {full_n}",
        "- 当前论文边界：未完成人工标签前，只能写 human confirmation protocol，不能写 human-verified error analysis。",
        "",
        "## 执行步骤",
        "",
        markdown_table(["Step", "Stage", "Status", "Artifact To Edit", "Current Evidence", "Pass Condition"], table),
        "",
        "## 标注字段",
        "",
        "- `human_auto_reason_correct`: yes / partial / no，用于判断自动错误类型是否合理。",
        "- `human_top_memory_relevant`: yes / partial / no，用于判断 top memory 是否支持 query。",
        "- `human_gold_memory_sufficient`: yes / no / unclear，用于判断 gold memory 是否足够。",
        "- `human_manual_reason`: 推荐短标签，如 gold_below_top20、memory_type_mismatch、temporal_neighbor、entity_confusion、multi_evidence_missing、gold_insufficient、other。",
        "- `human_auditor_notes`: 写出触发判断的关键词、时间线、人物或冲突证据。",
        "",
        "## 一致性指标公式",
        "",
        "令第 `i` 个样本在某字段上的人工标签为 `h_i`，LLM-assisted 标签为 `l_i`：",
        "",
        "- Exact agreement: `A_exact = (1/N) * sum_i 1[h_i = l_i]`。",
        "- Partial-credit agreement: 对 yes/partial/no，可设 `s(yes, partial)=0.5`、`s(no, partial)=0.5`、完全一致为 1、yes/no 冲突为 0，然后 `A_partial = (1/N) * sum_i s(h_i, l_i)`。",
        "- Cohen's kappa: `kappa = (p_o - p_e) / (1 - p_e)`，其中 `p_o` 是观测一致率，`p_e` 是按边际分布计算的随机一致率。",
        "",
        "## 推荐执行顺序",
        "",
        "1. 先填 `outputs/agent_memory_human_audit_priority20_blind_review.csv`，形成 quick-review 结果。",
        "2. 再填 `outputs/agent_memory_human_audit_priority20_dual_review.csv`，若只有一位标注者，可先跳过双人一致性，但论文措辞要更保守。",
        "3. priority20 通过后扩展到 full80；最终投稿建议至少完成 full80 single blind labeling。",
        "4. 每次人工字段更新后，重新运行 codebook 中的 merge/agreement/readiness 命令，并刷新 submission readiness。",
        "",
        "## 论文写法门槛",
        "",
        "- 0/20：只能写“人工复核协议与盲审表已准备”。",
        "- 20/20：可以写“priority20 quick-review agreement”，但不能代表完整错误分析。",
        "- 80/80：可以写“full80 Human/LLM audit agreement”。",
        "- 80/80 + 双人/仲裁完成：可以更稳健地写“human-verified error analysis”。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate human audit execution plan.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_human_audit_execution_plan_zh.md"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_human_audit_execution_plan.csv"))
    args = parser.parse_args()

    rows = build_steps(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, args.outputs_dir, rows)
    print(
        {
            "output_report": str(args.output_report),
            "output_csv": str(args.output_csv),
            "steps": len(rows),
            "pending": sum(1 for row in rows if row["status"] != "pass"),
        }
    )


if __name__ == "__main__":
    main()
