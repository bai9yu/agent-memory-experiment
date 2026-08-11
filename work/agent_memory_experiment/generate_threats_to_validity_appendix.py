#!/usr/bin/env python3
"""Generate a Chinese threats-to-validity appendix from cached paper gates."""

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


def lookup(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_rows(root: Path) -> list[dict[str, Any]]:
    outputs = root / "outputs"
    data = root / "work" / "agent_memory_experiment" / "data"
    submission = read_csv(outputs / "agent_memory_submission_readiness_gate.csv")
    embedding = read_csv(outputs / "agent_memory_external_embedding_blocker_audit.csv")
    human = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    claims = read_csv(outputs / "agent_memory_manuscript_claim_check.csv")
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    memories = data / "llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
    queries = data / "llm_extracted_locomo10_all_v3_answerable_queries.jsonl"

    type_aware = next(
        (
            row
            for row in baseline
            if row.get("variant") == "llm_extracted_fact" and row.get("method") == "type_aware"
        ),
        {},
    )
    api_gate = lookup(submission, "gate", "api_embedding_preflight")
    external_gate = lookup(submission, "gate", "external_embedding_completed")
    priority_gate = lookup(submission, "gate", "priority20_human_audit")
    full_gate = lookup(submission, "gate", "full80_human_audit")
    artifact_gate = lookup(submission, "gate", "reproducibility_artifacts")
    metric_gate = lookup(submission, "gate", "reproducibility_metrics")
    claim_gate = lookup(submission, "gate", "manuscript_claim_check")
    embedding_key = lookup(embedding, "item", "default_openai_key")
    embedding_summary = lookup(embedding, "item", "external_summary_completed")
    priority = lookup(human, "label", "priority20")
    full = lookup(human, "label", "full80")
    cross_claim = lookup(claims, "rule_id", "cross_dataset_overclaim")
    scale_claim = lookup(claims, "rule_id", "production_scale_overclaim")

    return [
        {
            "category": "internal_validity",
            "threat": "LLM memory writer 可能产生抽取偏差或遗漏事实。",
            "current_evidence": "DeepSeek writer 已有三次运行稳定性统计；正文仍限定为 LoCoMo10 范围。",
            "mitigation": "报告 writer stability 均值/方差；保留 source evidence；后续扩展第二数据集或人工抽查 writer 输出。",
            "paper_claim_boundary": "可以说 LoCoMo10 中 fact memory 有效，不能泛化到所有长对话记忆写入场景。",
            "status": "partially_mitigated",
        },
        {
            "category": "construct_validity",
            "threat": "MRR/Recall@K 只衡量 memory retrieval，不等价于完整 agent task success。",
            "current_evidence": f"type-aware MRR={type_aware.get('mrr', 'unknown')}, Recall@5={type_aware.get('recall@5', 'unknown')}; 评估对象是 query-memory retrieval。",
            "mitigation": "在任务定义中明确 retrieval-only；后续加入 answer generation 或 downstream agent task success。",
            "paper_claim_boundary": "不能宣称端到端 agent 性能提升，只能宣称记忆检索和重排性能提升。",
            "status": "bounded_claim",
        },
        {
            "category": "external_validity",
            "threat": "主实验只有 LoCoMo10 answerable slice。",
            "current_evidence": f"fact memories={count_jsonl(memories)}, queries={count_jsonl(queries)}; claim check: {cross_claim.get('status', 'unknown')}",
            "mitigation": "使用 held-out query split 和 LOCO split 检查跨 conversation 泛化；正文显式禁止跨数据集宣称。",
            "paper_claim_boundary": "可以写跨 LoCoMo conversation 泛化，不可写跨数据集泛化。",
            "status": "open_until_second_dataset",
        },
        {
            "category": "external_validity",
            "threat": "外部 embedding baseline 尚未完成，BGE-M3 结果可能依赖本地 embedding 选择。",
            "current_evidence": f"{api_gate.get('evidence', 'missing api gate')}; {external_gate.get('evidence', 'missing external gate')}; {embedding_key.get('evidence', 'missing key row')}; {embedding_summary.get('evidence', 'missing summary row')}",
            "mitigation": "已准备 OpenAI/default 与 generic OpenAI-compatible provider 的 preflight、estimate、run、compare 和 blocker audit。",
            "paper_claim_boundary": "外部 API embedding 对照只能写为 pending/protocol，不能写为完成结果。",
            "status": "blocker",
        },
        {
            "category": "reliability",
            "threat": "错误分析仍缺人工确认，LLM-assisted 标签可能带来判断偏差。",
            "current_evidence": f"{priority_gate.get('evidence', 'missing priority gate')}; {full_gate.get('evidence', 'missing full gate')}; priority status={priority.get('status', 'unknown')}; full status={full.get('status', 'unknown')}",
            "mitigation": "已生成盲审 CSV、阅读包、双人标注表、annotation codebook、agreement/readiness gate。",
            "paper_claim_boundary": "不能宣称 human-verified error analysis；只能写人工复核流程已准备。",
            "status": "blocker",
        },
        {
            "category": "statistical_conclusion_validity",
            "threat": "随机划分或单一指标可能导致偶然提升。",
            "current_evidence": "已使用 5 seeds held-out split、LOCO split、paired bootstrap CI、permutation test，并报告负结果。",
            "mitigation": "继续保留 query-level paired tests；新增数据集后重复所有显著性检验。",
            "paper_claim_boundary": "当前统计结论限定于 LoCoMo10 answerable slice 和现有检索任务。",
            "status": "mitigated_in_scope",
        },
        {
            "category": "scalability_validity",
            "threat": "100k distractor scale test 含 synthetic memory，不能代表真实生产规模。",
            "current_evidence": f"claim check: {scale_claim.get('status', 'unknown')}",
            "mitigation": "正文把 FAISS/LSH 大规模实验写成效率诊断；后续加入真实大规模 memory bank。",
            "paper_claim_boundary": "不能写生产规模结论，只能写 synthetic stress-test 诊断。",
            "status": "bounded_claim",
        },
        {
            "category": "reproducibility",
            "threat": "多脚本、多 artifact 可能导致结果漂移或遗漏。",
            "current_evidence": f"{artifact_gate.get('evidence', 'missing artifact gate')}; {metric_gate.get('evidence', 'missing metric gate')}; {claim_gate.get('evidence', 'missing claim gate')}",
            "mitigation": "复现清单、artifact integrity manifest、submission readiness gate 和 claim checker 随每次结果更新重跑。",
            "paper_claim_boundary": "可以写当前 artifact 自洽；不能替代外部独立复现。",
            "status": "mitigated_in_scope",
        },
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blocker_rows = [row for row in rows if row["status"] == "blocker"]
    table_rows = [
        [
            row["category"],
            row["threat"],
            row["current_evidence"],
            row["mitigation"],
            row["paper_claim_boundary"],
            row["status"],
        ]
        for row in rows
    ]
    lines = [
        "# Threats to Validity 与论文声明边界",
        "",
        "本附录把当前实验的有效性威胁、已有缓解措施和论文可写边界集中列出。它的作用不是美化未完成工作，而是防止论文把 LoCoMo10 范围内的检索结果过度扩展到跨数据集、端到端 agent 或生产规模结论。",
        "",
        "## 总览",
        "",
        f"- Threat items: {len(rows)}",
        f"- Submission blockers reflected here: {len(blocker_rows)}",
        "- 两个仍会阻止最终投稿的方向：外部 embedding baseline 未完成；人工错误复核标签未填写。",
        "",
        markdown_table(
            ["Category", "Threat", "Current Evidence", "Mitigation", "Paper Claim Boundary", "Status"],
            table_rows,
        ),
        "",
        "## 推荐写入论文的限制段落",
        "",
        "本文的结论主要限定在 LoCoMo10 answerable slice 的 memory retrieval setting。虽然 held-out query split 和 leave-one-conversation-out split 均支持 intrinsic feature reranker 相比 fixed type-aware reranking 的稳定提升，但这仍不等价于跨数据集泛化或端到端 agent task success。当前主结果使用本地 BGE-M3 embedding cache，外部 API embedding baseline 尚未完成，因此不能将外部 embedding 对照写入主结果。错误分析部分已经准备 LLM-assisted draft、盲审 CSV、双人标注表和 annotation codebook，但在 priority20/full80 人工确认完成前，不能宣称 human-verified error analysis。大规模检索部分包含 synthetic distractor stress test，只能作为效率诊断，不能直接代表真实生产规模部署。",
        "",
        "## 投稿前必须解除的声明风险",
        "",
    ]
    if blocker_rows:
        for row in blocker_rows:
            lines.append(f"- {row['category']}：{row['threat']} -> {row['mitigation']}")
    else:
        lines.append("- 无 blocker。")
    lines.extend([
        "",
        "## 审稿问答准备",
        "",
        "- 如果审稿人问为什么没有外部 embedding：回答为当前版本中该实验仍是 blocker，代码已具备 provider 接入、preflight、cache、estimate 和 compare，但未配置真实 embedding provider key，因此不写入主结果。",
        "- 如果审稿人问错误分析是否人工验证：回答为当前仅有 LLM-assisted draft 和人工复核流程，priority20/full80 未填写前不声称 human-verified。",
        "- 如果审稿人问是否适用于所有 agent memory：回答为当前证据支持 LoCoMo10 answerable slice 的长期对话 memory retrieval，后续需要第二数据集和端到端任务验证。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate threats-to-validity appendix.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "threats": len(rows),
        "blockers": sum(1 for row in rows if row["status"] == "blocker"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
