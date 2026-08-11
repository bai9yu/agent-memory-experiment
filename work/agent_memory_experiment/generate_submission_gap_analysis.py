#!/usr/bin/env python3
"""Generate a submission-readiness gap and reviewer-risk analysis."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def find_contains(rows: list[dict[str, str]], field: str, text: str) -> dict[str, str]:
    for row in rows:
        if text in row.get(field, ""):
            return row
    raise KeyError({field: text})


def count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    evidence = read_csv(outputs / "agent_memory_paper_evidence_matrix.csv")
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    agreement = read_csv(outputs / "agent_memory_human_llm_audit_agreement.csv")
    priority_agreement = read_csv(outputs / "agent_memory_human_llm_audit_priority20_agreement.csv")
    human_gate = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    checklist_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    checklist_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")

    artifact_pass = count(checklist_artifacts, "exists", "True")
    metric_pass = count(checklist_metrics, "pass", "True")
    confirmed = int(lookup(agreement, group="overview", label="confirmed_samples")["count"])
    invalid_labels = int(lookup(agreement, group="overview", label="validation_errors")["count"])
    priority_samples = int(lookup(priority_agreement, group="overview", label="samples")["count"])
    priority_confirmed = int(lookup(priority_agreement, group="overview", label="confirmed_samples")["count"])
    human_gate_priority = lookup(human_gate, label="priority20")
    human_gate_full = lookup(human_gate, label="full80")
    embedding_completed = count(embedding_status, "status", "completed")
    embedding_ready = sum(1 for row in embedding_status if row.get("status") in {"ready_to_run", "completed"})

    main_retrieval = find_contains(evidence, "claim", "事实级记忆在 LoCoMo10")
    main_method = lookup(evidence, status="main_method")
    type3 = find_contains(evidence, "claim", "Type 3 多证据问题")
    efficiency = lookup(evidence, status="efficiency_result")
    stability = lookup(evidence, status="stability_result")
    reproducibility = lookup(evidence, status="reproducibility")

    rows = [
        {
            "priority": 1,
            "risk_level": "blocker",
            "reviewer_question": "是否只在单一 embedding / 单一检索编码器上有效？",
            "current_evidence": f"外部 embedding baseline completed={embedding_completed}, ready_or_completed={embedding_ready}。",
            "why_it_matters": "没有强外部 embedding 对照时，审稿人可能认为提升来自 BGE-M3 或缓存设置，而不是记忆/重排方法本身。",
            "minimum_action": "运行至少一个主流 API embedding baseline，并自动生成与 BGE-M3 的 delta 表。",
            "paper_wording_now": "只能说 API baseline 接口已经准备好，不能把它写入主结果。",
            "target_artifact": "agent_memory_embedding_baseline_comparison_zh.md",
            "owner": "needs_api_key",
        },
        {
            "priority": 2,
            "risk_level": "blocker",
            "reviewer_question": "错误分析是否经过人工确认？",
            "current_evidence": (
                f"Human/LLM 确认表 80 条，人工确认 {confirmed} 条，非法标签 {invalid_labels}；"
                f"priority20 快速抽查包 {priority_samples} 条，agreement confirmed={priority_confirmed}；"
                f"readiness gate priority20={human_gate_priority['confirmed_samples']}/{human_gate_priority['min_required']}, "
                f"full80={human_gate_full['confirmed_samples']}/{human_gate_full['min_required']}。"
            ),
            "why_it_matters": "自动错误类型如果没有人工或一致性证据，只能作为诊断脚本输出，难以支撑论文中的错误分析结论。",
            "minimum_action": "优先填写 priority20 confirmation CSV 的 human_* 字段，先报告 quick-review exact agreement 与 Cohen's kappa；投稿前再扩展到 80 条。",
            "paper_wording_now": "可以写 LLM-assisted audit draft 和人工确认流程，不能写 human-verified error analysis。",
            "target_artifact": "agent_memory_human_audit_readiness_gate_zh.md; agent_memory_human_llm_audit_priority20_agreement_zh.md; agent_memory_human_llm_audit_agreement_zh.md",
            "owner": "needs_human_labels",
        },
        {
            "priority": 3,
            "risk_level": "major",
            "reviewer_question": "LoCoMo10 slice 是否足以支撑泛化结论？",
            "current_evidence": main_retrieval["evidence"],
            "why_it_matters": "当前主结果强，但数据范围仍是 LoCoMo10 answerable slice；过度宣称会被质疑外部有效性。",
            "minimum_action": "扩大 LoCoMo slice 或加入第二个长对话/agent memory 数据集；若时间有限，论文标题和结论限制在系统性实证研究。",
            "paper_wording_now": "可以写 LoCoMo10 上有效，不能写一般智能体记忆场景均有效。",
            "target_artifact": "agent_memory_paper_draft_outline_zh.md",
            "owner": "experiment_design",
        },
        {
            "priority": 4,
            "risk_level": "major",
            "reviewer_question": "候选级重排是否真的跨 conversation 泛化？",
            "current_evidence": main_method["evidence"],
            "why_it_matters": "学习式方法容易被质疑过拟合；LOCO 已缓解该风险，但仍应把 split 设置写清楚。",
            "minimum_action": "在方法和实验设置中突出 leave-one-conversation-out split，并保留 paired permutation test。",
            "paper_wording_now": "可以作为核心方法贡献，但需要避免跨数据集泛化措辞。",
            "target_artifact": "agent_memory_candidate_reranker_loco_zh.md",
            "owner": "paper_writing",
        },
        {
            "priority": 5,
            "risk_level": "major",
            "reviewer_question": "Type 3 多证据失败是否削弱方法贡献？",
            "current_evidence": type3["evidence"],
            "why_it_matters": "如果不主动承认边界，审稿人会把 Type 3 失败视作方法缺陷；主动报告负结果反而能提升可信度。",
            "minimum_action": "把 Type 3 写成系统边界和未来工作，避免把浅层修复方法包装为有效贡献。",
            "paper_wording_now": "可以写负结果、边界分析和后续 setwise/listwise 方向。",
            "target_artifact": "agent_memory_type3_coverage_significance_zh.md",
            "owner": "paper_writing",
        },
        {
            "priority": 6,
            "risk_level": "moderate",
            "reviewer_question": "效率实验是否只反映小规模缓存条件？",
            "current_evidence": efficiency["evidence"],
            "why_it_matters": "当前 exact NN 和 synthetic 100k 诊断有价值，但真实大规模 memory bank 证据仍不足。",
            "minimum_action": "统一报告硬件、wall-clock 设置、候选数和 synthetic distractor 限制；更高目标再补真实大规模 memory bank。",
            "paper_wording_now": "可以写效率诊断，不能写真实生产规模结论。",
            "target_artifact": "agent_memory_sklearn_nn_prefilter_locomo10_zh.md",
            "owner": "paper_writing",
        },
        {
            "priority": 7,
            "risk_level": "moderate",
            "reviewer_question": "memory writer 的随机性是否影响主结论？",
            "current_evidence": stability["evidence"],
            "why_it_matters": "LLM 写记忆天然有随机性；已有 3 次稳定性结果，但需要在论文中说明范围和温度设置。",
            "minimum_action": "在实验设置中报告 3-run mean/std，并说明仍是 LoCoMo10 范围内稳定性。",
            "paper_wording_now": "可以写 LoCoMo10 重复抽取稳定，不宜写跨模型稳定。",
            "target_artifact": "agent_memory_writer_stability_zh.md",
            "owner": "paper_writing",
        },
        {
            "priority": 8,
            "risk_level": "moderate",
            "reviewer_question": "复现实验是否足够完整？",
            "current_evidence": f"{reproducibility['evidence']} Current checklist artifacts={artifact_pass}, metrics={metric_pass}.",
            "why_it_matters": "复现清单完整能降低审稿人对工程实验的疑虑，但大模型输出和 embedding cache 不能全部进 Git。",
            "minimum_action": "在 appendix 写清楚数据准备、模型缓存、API key 不入库、重型结果由 CSV 缓存复现。",
            "paper_wording_now": "可以写 artifact-checked reproducibility package。",
            "target_artifact": "agent_memory_reproducibility_checklist_zh.md",
            "owner": "paper_writing",
        },
    ]
    return rows


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    severity_counts = Counter(row["risk_level"] for row in rows)
    blockers = [row for row in rows if row["risk_level"] == "blocker"]
    major = [row for row in rows if row["risk_level"] == "major"]
    moderate = [row for row in rows if row["risk_level"] == "moderate"]
    table_rows = [
        [
            str(row["priority"]),
            row["risk_level"],
            row["reviewer_question"],
            row["minimum_action"],
            row["target_artifact"],
        ]
        for row in rows
    ]
    lines = [
        "# 投稿前差距与审稿风险矩阵",
        "",
        "本文件从审稿视角整理当前实验包的主要风险、已有证据、最低补救动作和论文当前可用措辞。它用于决定下一轮实验优先级，不把尚未完成的事项写成已完成结论。",
        "",
        "## 总览",
        "",
        f"- Blocker：{severity_counts['blocker']}",
        f"- Major：{severity_counts['major']}",
        f"- Moderate：{severity_counts['moderate']}",
        "",
        "## 最小投稿前动作",
        "",
    ]
    for row in blockers:
        lines.append(f"- P{row['priority']} `{row['risk_level']}`：{row['minimum_action']}")
    lines.extend([
        "",
        "## 风险矩阵",
        "",
        markdown_table(["Priority", "Risk", "Reviewer Question", "Minimum Action", "Target Artifact"], table_rows),
        "",
        "## 论文写作边界",
        "",
    ])
    for row in rows:
        lines.extend([
            f"### P{row['priority']} {row['reviewer_question']}",
            "",
            f"- 风险等级：`{row['risk_level']}`",
            f"- 当前证据：{row['current_evidence']}",
            f"- 重要性：{row['why_it_matters']}",
            f"- 当前可写：{row['paper_wording_now']}",
            f"- 最小动作：{row['minimum_action']}",
            f"- 目标 artifact：`{row['target_artifact']}`",
            f"- 依赖：`{row['owner']}`",
            "",
        ])
    lines.extend([
        "## 优先级建议",
        "",
        "- 先补 blocker：外部 embedding baseline 与 Human/LLM 人工确认。这两项直接决定论文能否从“完整实验包”进入“可投稿实验”。",
        "- 再补 major：泛化措辞、LOCO split 说明和 Type 3 负结果写法。这些更多影响审稿观感和论证边界。",
        "- Moderate 项主要靠论文写法和 appendix 补足；不用阻塞下一轮核心实验。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate submission gap and reviewer-risk analysis.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "risks": len(rows),
        "blockers": sum(1 for row in rows if row["risk_level"] == "blocker"),
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
