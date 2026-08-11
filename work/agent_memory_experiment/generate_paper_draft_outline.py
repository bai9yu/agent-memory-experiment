#!/usr/bin/env python3
"""Generate a Chinese paper draft outline from current experiment artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def f(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: Any, digits: int = 4) -> str:
    return f"{float(value):+.{digits}f}"


def write_report(path: Path, outputs: Path) -> None:
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    reranker_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    feature_ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    bootstrap_ci = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")
    reranker_loco = read_csv(outputs / "agent_memory_candidate_reranker_loco_summary.csv")
    reranker_loco_sig = read_csv(outputs / "agent_memory_candidate_reranker_loco_significance_results.csv")
    type3_cov = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    evidence = read_csv(outputs / "agent_memory_paper_evidence_matrix.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    writer_aggregate = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    llm_audit_summary = read_csv(outputs / "agent_memory_llm_audit_summary.csv")

    type_aware = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    observation = lookup(baseline, variant="locomo_observation", method="type_aware")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    reranker_mrr = lookup(reranker_sig, metric="mrr")
    reranker_r5 = lookup(reranker_sig, metric="recall@5")
    intrinsic_row = lookup(feature_ablation, method="ablation_intrinsic_only")
    intrinsic_vs_type_mrr = lookup(
        bootstrap_ci,
        scenario="candidate_reranker_intrinsic_ablation_vs_type_aware",
        metric="mrr",
    )
    intrinsic_vs_full_mrr = lookup(
        bootstrap_ci,
        scenario="candidate_reranker_intrinsic_ablation_vs_full",
        metric="mrr",
    )
    reranker_loco_row = lookup(reranker_loco, method="candidate_reranker_loco")
    reranker_loco_base = lookup(reranker_loco, method="type_aware")
    reranker_loco_mrr = lookup(reranker_loco_sig, metric="mrr")
    reranker_loco_r5 = lookup(reranker_loco_sig, metric="recall@5")
    type3_selector = lookup(type3_cov, experiment="supervised_set_selector", metric="coverage_ratio@5")
    writer_mrr = lookup(writer_aggregate, metric="mrr")
    writer_r5 = lookup(writer_aggregate, metric="recall@5")
    artifact_pass = sum(1 for row in repro_artifacts if row["exists"] == "True")
    metric_pass = sum(1 for row in repro_metrics if row["pass"] == "True")
    writer_completed = int(writer_mrr["completed_runs"])
    writer_ready = writer_completed >= 3
    llm_audit_yes = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="yes")
    llm_audit_partial = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="partial")
    llm_audit_no = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="no")
    gap_rows = read_csv(outputs / "agent_memory_submission_gap_analysis.csv")
    blocker_count = sum(1 for row in gap_rows if row["risk_level"] == "blocker")
    open_gaps = [row for row in evidence if row["status"] in {"open_gap", "baseline_protocol", "stability_protocol", "reliability_protocol"}]

    lines = [
        "# Agent Memory 论文草稿骨架",
        "",
        "本文件面向论文写作，不是最终论文。它把当前实验结果组织成可投稿论文的章节结构，并明确哪些结论已有证据、哪些只能写为限制或未来工作。",
        "",
        "## 题目候选",
        "",
        "1. 面向长对话智能体的事实级记忆写入与候选级学习重排",
        "2. Agent Memory Retrieval with LLM-Written Facts and Candidate-Level Reranking",
        "3. From Memory Writing to Retrieval: A Reproducible Study on Long-Conversation Agent Memory",
        "",
        "## 摘要草稿",
        "",
        (
            "长对话智能体需要在大量历史交互中高效检索与当前任务相关的事实记忆。"
            "本文构建了一个基于 LoCoMo 长对话数据的可复现实验框架，比较 DeepSeek 抽取的 fact-level memory、"
            "LoCoMo 官方 observation memory、本地 BGE-M3 embedding 检索、BM25 混合检索、时间感知重排、type-aware 重排以及候选级学习重排。"
            f"在 LoCoMo10 answerable slice 上，DeepSeek fact memory + type-aware reranking 取得 MRR {f(type_aware['mrr'])} 和 Recall@5 {f(type_aware['recall@5'])}，"
            f"高于 LoCoMo observation memory 的 MRR {f(observation['mrr'])} 和 Recall@5 {f(observation['recall@5'])}。"
            f"进一步地，候选级学习重排在 held-out split 上将 MRR 从 {f(reranker_base['mrr_mean'])} 提升到 {f(reranker_row['mrr_mean'])}，"
            f"MRR delta 为 {signed(reranker_mrr['mean_delta'])}，permutation p={f(reranker_mrr['permutation_p_value'], 4)}；"
            f"feature ablation 中 intrinsic-only reranker 进一步达到 MRR {f(intrinsic_row['mrr_mean'])} 和 Recall@5 {f(intrinsic_row['recall@5_mean'])}。"
            f"在更严格的 leave-one-conversation-out split 下，candidate reranker 的 MRR 为 {f(reranker_loco_row['mrr_mean'])}，"
            f"高于 type-aware 的 {f(reranker_loco_base['mrr_mean'])}，加权 MRR delta 为 {signed(reranker_loco_mrr['mean_delta'])}。"
            f"DeepSeek memory writer 三次运行的 MRR 均值为 {f(writer_mrr['mean'])}，标准差为 {f(writer_mrr['stdev'])}，"
            f"Recall@5 均值为 {f(writer_r5['mean'])}，标准差为 {f(writer_r5['stdev'])}。"
            f"错误分析方面，80 条 LLM-assisted audit 初稿中 auto_reason_correct 的 yes/partial/no 为 "
            f"{llm_audit_yes['count']}/{llm_audit_partial['count']}/{llm_audit_no['count']}，并已生成 Human/LLM 确认表，可作为人工复核前的预标注材料。"
            "同时，Type 3 多证据问题仍是主要边界，浅层 set selector 和关键词式 decomposition 未能改善 Coverage@5。"
            "本文给出主结果、负结果、稳定性、效率诊断和复现清单，并指出外部 embedding baseline 和人工错误复核仍需补齐后才能作为完整投稿版本。"
        ),
        "",
        "## 贡献点写法",
        "",
        "- 构建一套面向 agent memory 的可复现实验框架，覆盖 memory write、retrieval、reranking、compression、cross-agent reuse 和 error analysis。",
        "- 证明 fact-level LLM-written memory 在 LoCoMo10 上可以作为紧凑且有效的记忆形态，同时节省存储 token。",
        "- 提出并验证 candidate-level learned reranking；feature-group ablation 发现 intrinsic-only reranker 高于 full reranker，说明 method-level rank/score 特征可能带来噪声。",
        "- 系统报告 Type 3 multi-evidence retrieval 的负结果，说明浅层单候选重排和简单 query decomposition 不足以解决多证据覆盖。",
        "- 提供复现实验包、环境快照、证据矩阵、人工复核协议、writer stability 框架和 API embedding baseline 框架。",
        "",
        "## 方法章节结构",
        "",
        "### Problem Setup",
        "",
        "给定查询 \\(q\\) 和记忆库 \\(M=\\{m_i\\}_{i=1}^{N}\\)，目标是在 Top-K 中召回答案证据记忆 \\(G_q\\subset M\\)。主要指标为 Recall@K 和 MRR。",
        "",
        "### Memory Writing",
        "",
        "使用 DeepSeek 将长对话 session/turn 抽取为结构化 fact-level memory：",
        "",
        "\\[m_i=(text_i, type_i, date_i, entities_i, importance_i, source_i)\\]",
        "",
        (
            f"当前稳定性框架已登记 3 次 LoCoMo10 抽取，completed runs={writer_completed}。"
            if writer_ready
            else f"当前稳定性框架已登记 3 次 LoCoMo10 抽取，completed runs={writer_completed}，暂不能报告方差。"
        ),
        "",
        "### Retrieval Scoring",
        "",
        "语义分数：",
        "",
        "\\[s_{sem}(q,m_i)=\\cos(e(q), e(m_i))\\]",
        "",
        "混合检索：",
        "",
        "\\[S_{hybrid}=0.65s_{sem}+0.30s_{bm25}+0.05s_{entity}\\]",
        "",
        "time-aware / type-aware 重排：",
        "",
        "\\[S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\\gamma p(q,m_i)+\\eta I(m_i)+\\lambda T(q,m_i)\\]",
        "",
        "其中 \\(g(q)\\) 为 recency gate，\\(d\\) 为时间衰减，\\(p\\) 为 persona match，\\(I\\) 为 importance proxy，\\(T\\) 为 query-intent 与 memory type 的匹配分。",
        "",
        "### Intrinsic Candidate-Level Learned Reranking",
        "",
        "从 keyword/vector/hybrid/time-aware/type-aware 的 Top-K 并集构造候选集合，用候选级特征学习相关性：",
        "",
        "\\[\\hat{y}_{q,i}=f_{\\theta}(s_{sem},s_{bm25},d(q,m_i),p(q,m_i),T(q,m_i),type_i,I_i,\\phi(q,m_i))\\]",
        "",
        "最终按 \\(\\hat{y}_{q,i}\\) 重新排序候选。当前 intrinsic-only 变体是 held-out split 上最强方法贡献；full reranker 和 LOCO reranker 作为消融与跨 conversation 泛化证据。",
        "",
        "## 实验章节结构",
        "",
        "### RQ1: LLM-written fact memory 是否有效？",
        "",
        f"- 主表：fact memory type-aware MRR {f(type_aware['mrr'])}, Recall@5 {f(type_aware['recall@5'])}；observation MRR {f(observation['mrr'])}, Recall@5 {f(observation['recall@5'])}。",
        "- 写法：可以作为 memory-form comparison；必须说明 LoCoMo10 slice 限制，并把 writer stability 作为 LoCoMo10 范围内证据。",
        "",
        "### RQ2: 固定重排组件是否有用？",
        "",
        "- 表格：paper tables 中的 LoCoMo10 主检索结果和 type-aware 显著性。",
        "- 写法：type-aware 是小幅但可靠提升，不要夸大 Recall@1/3。",
        "",
        "### RQ3: 学习式候选重排是否带来主要收益？",
        "",
        f"- 结果：full candidate reranker MRR {f(reranker_row['mrr_mean'])} vs type-aware {f(reranker_base['mrr_mean'])}；MRR delta {signed(reranker_mrr['mean_delta'])}，Recall@5 delta {signed(reranker_r5['mean_delta'])}。",
        f"- 特征组消融：intrinsic-only reranker MRR {f(intrinsic_row['mrr_mean'])}，Recall@5 {f(intrinsic_row['recall@5_mean'])}；相对 type-aware MRR delta {signed(intrinsic_vs_type_mrr['delta_mean'])}，95% CI [{f(intrinsic_vs_type_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_type_mrr['delta_ci_high'], 4)}]；相对 full reranker MRR delta {signed(intrinsic_vs_full_mrr['delta_mean'])}，95% CI [{f(intrinsic_vs_full_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_full_mrr['delta_ci_high'], 4)}]。",
        f"- LOCO 验证：candidate reranker MRR {f(reranker_loco_row['mrr_mean'])} vs type-aware {f(reranker_loco_base['mrr_mean'])}；加权 MRR delta {signed(reranker_loco_mrr['mean_delta'])}，Recall@5 delta {signed(reranker_loco_r5['mean_delta'])}。",
        "- 写法：intrinsic-only 是 held-out 最强版本；LOCO 已支持 candidate-level reranking 方向跨 conversation 泛化，但 intrinsic-only 版本可作为后续补充 LOCO 复验。",
        "",
        "### RQ4: Type 3 多证据问题是否解决？",
        "",
        f"- 结果：supervised set selector Coverage@5 delta {signed(type3_selector['mean_delta'])}，p={f(type3_selector['permutation_p_value'], 4)}。",
        "- 写法：作为负结果和 limitation；不能宣称解决 Type 3。",
        "",
        "### RQ5: 效率与扩展性如何？",
        "",
        "- 写法：sklearn exact NN / FAISS / LSH 作为效率与索引诊断；100k synthetic distractor 必须标注 synthetic。",
        "",
        "## 当前不可写为主结果的内容",
        "",
    ]
    for row in open_gaps:
        lines.append(f"- `{row['status']}`：{row['claim']}；缺口：{row['remaining_gap']}")
    lines.extend([
        "",
        "## 投稿前最小完成条件",
        "",
        f"投稿风险矩阵当前列出 {len(gap_rows)} 个审稿风险，其中 {blocker_count} 个 blocker。完整清单见 `outputs/agent_memory_submission_gap_analysis_zh.md`。",
        "",
        "1. 至少完成一个外部 embedding baseline，并自动生成与 BGE-M3 的 delta 对比。",
        "2. 优先在盲审人工复核表中填写 human_* 字段，回填 Human/LLM 确认表后报告 exact agreement 与 Cohen's kappa。",
        "3. 若不补外部数据集，需要在论文中明确本工作是 LoCoMo10 slice 的系统性实验，而非广泛泛化结论。",
        "",
        "## 复现状态",
        "",
        f"- Artifact gate: {artifact_pass}/{len(repro_artifacts)}",
        f"- Metric gate: {metric_pass}/{len(repro_metrics)}",
        "- 关键入口：`outputs/agent_memory_reproducibility_checklist_zh.md`、`outputs/agent_memory_paper_evidence_matrix_zh.md`、`outputs/agent_memory_paper_tables_zh.md`、`outputs/agent_memory_experiment_protocol_zh.md`、`outputs/agent_memory_manuscript_draft_zh.md`。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper draft outline.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    write_report(args.output_report, args.outputs_dir)
    print(json.dumps({"output_report": str(args.output_report)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
