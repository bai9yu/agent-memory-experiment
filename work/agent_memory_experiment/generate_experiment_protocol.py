#!/usr/bin/env python3
"""Generate a paper-ready experiment protocol appendix."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def f(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: Any, digits: int = 4) -> str:
    return f"{float(value):+.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, root: Path) -> None:
    outputs = root / "outputs"
    data = root / "work" / "agent_memory_experiment" / "data"
    memories = data / "llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
    queries = data / "llm_extracted_locomo10_all_v3_answerable_queries.jsonl"

    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    type_sig = read_csv(outputs / "agent_memory_type_aware_significance_results.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    reranker_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    loco = read_csv(outputs / "agent_memory_candidate_reranker_loco_summary.csv")
    loco_sig = read_csv(outputs / "agent_memory_candidate_reranker_loco_significance_results.csv")
    type3 = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    writer = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    gap = read_csv(outputs / "agent_memory_submission_gap_analysis.csv")
    priority_agreement = read_csv(outputs / "agent_memory_human_llm_audit_priority20_agreement.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")

    fact_type = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    obs_type = lookup(baseline, variant="locomo_observation", method="type_aware")
    time_aware = lookup(baseline, variant="llm_extracted_fact", method="time_aware")
    type_mrr = lookup(type_sig, metric="mrr")
    type_r5 = lookup(type_sig, metric="recall@5")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    reranker_mrr = lookup(reranker_sig, metric="mrr")
    reranker_r5 = lookup(reranker_sig, metric="recall@5")
    loco_row = lookup(loco, method="candidate_reranker_loco")
    loco_base = lookup(loco, method="type_aware")
    loco_mrr = lookup(loco_sig, metric="mrr")
    loco_r5 = lookup(loco_sig, metric="recall@5")
    writer_mrr = lookup(writer, metric="mrr")
    writer_r5 = lookup(writer, metric="recall@5")
    type3_cov = lookup(type3, experiment="supervised_set_selector", metric="coverage_ratio@5")
    artifact_pass = sum(1 for row in repro_artifacts if row["exists"] == "True")
    metric_pass = sum(1 for row in repro_metrics if row["pass"] == "True")
    blocker_count = sum(1 for row in gap if row["risk_level"] == "blocker")
    priority_samples = lookup(priority_agreement, group="overview", label="samples")["count"]
    priority_confirmed = lookup(priority_agreement, group="overview", label="confirmed_samples")["count"]

    main_table = [
        ["Fact memory + time-aware", f(time_aware["mrr"]), f(time_aware["recall@5"]), "fixed reranking baseline"],
        ["Fact memory + type-aware", f(fact_type["mrr"]), f(fact_type["recall@5"]), "main fixed reranker"],
        ["Observation + type-aware", f(obs_type["mrr"]), f(obs_type["recall@5"]), "memory-form baseline"],
        ["Candidate reranker", f(reranker_row["mrr_mean"]), f(reranker_row["recall@5_mean"]), "held-out learned reranker"],
        ["Candidate reranker LOCO", f(loco_row["mrr_mean"]), f(loco_row["recall@5_mean"]), "leave-one-conversation-out"],
    ]
    sig_table = [
        ["type-aware vs time-aware", "MRR", signed(type_mrr["mean_delta"]), f(type_mrr["permutation_p_value"], 4), f(type_mrr["bootstrap_ci_low"]), f(type_mrr["bootstrap_ci_high"])],
        ["type-aware vs time-aware", "Recall@5", signed(type_r5["mean_delta"]), f(type_r5["permutation_p_value"], 4), f(type_r5["bootstrap_ci_low"]), f(type_r5["bootstrap_ci_high"])],
        ["candidate reranker vs type-aware", "MRR", signed(reranker_mrr["mean_delta"]), f(reranker_mrr["permutation_p_value"], 4), f(reranker_mrr["bootstrap_ci_low"]), f(reranker_mrr["bootstrap_ci_high"])],
        ["candidate reranker vs type-aware", "Recall@5", signed(reranker_r5["mean_delta"]), f(reranker_r5["permutation_p_value"], 4), f(reranker_r5["bootstrap_ci_low"]), f(reranker_r5["bootstrap_ci_high"])],
        ["LOCO candidate reranker vs type-aware", "MRR", signed(loco_mrr["mean_delta"]), f(loco_mrr["permutation_p_value"], 4), f(loco_mrr["bootstrap_ci_low"]), f(loco_mrr["bootstrap_ci_high"])],
        ["LOCO candidate reranker vs type-aware", "Recall@5", signed(loco_r5["mean_delta"]), f(loco_r5["permutation_p_value"], 4), f(loco_r5["bootstrap_ci_low"]), f(loco_r5["bootstrap_ci_high"])],
    ]
    lines = [
        "# 论文实验协议与审稿复核清单",
        "",
        "本文件把当前 agent memory 实验整理为论文 appendix 可用的实验协议。它强调数据范围、模型组件、评价指标、显著性检验、复现入口和不能过度宣称的边界。",
        "",
        "## 1. 数据与切片",
        "",
        f"- 数据源：LoCoMo10 answerable slice。",
        f"- 事实级记忆数：{count_jsonl(memories) if memories.exists() else 0}",
        f"- 可评估查询数：{count_jsonl(queries) if queries.exists() else 0}",
        "- 主要实验单位：query-memory retrieval；每个 query 有一个或多个 gold memory ids。",
        "- 论文写法：所有主结论默认限定在 LoCoMo10 answerable slice，除 LOCO split 外不宣称跨数据集泛化。",
        "",
        "## 2. 记忆写入与检索组件",
        "",
        "- Memory writer：DeepSeek API 抽取 fact-level memory，字段包括 text、type、date、entities、importance、source evidence。",
        "- Memory baseline：LoCoMo 官方 observation memory。",
        "- Embedding：本地主结果使用 BGE-M3 缓存；外部 API embedding baseline 当前仍是投稿 blocker。",
        "- 检索方法：keyword、vector、hybrid、time-aware、type-aware、candidate-level learned reranker。",
        "- 学习式重排：从多个检索器 Top-K 并集构造候选，使用候选级特征预测相关性分数，再重新排序。",
        "",
        "## 3. 指标与公式",
        "",
        r"- Recall@K：\(\frac{1}{|Q|}\sum_{q\in Q}\mathbf{1}[\exists g\in G_q, rank_q(g)\le K]\)。",
        r"- MRR：\(\frac{1}{|Q|}\sum_{q\in Q}\frac{1}{\min_{g\in G_q} rank_q(g)}\)。",
        r"- 多证据 Coverage@K：\(\frac{1}{|Q|}\sum_{q\in Q}\frac{|G_q\cap TopK(q)|}{|G_q|}\)。",
        r"- type-aware score：\(S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\gamma p(q,m_i)+\eta I(m_i)+\lambda T(q,m_i)\)。",
        "- 显著性：paired bootstrap 置信区间 + paired permutation p-value；报告 improved / worsened / tied queries。",
        "",
        "## 4. 主结果摘要",
        "",
        markdown_table(["Method", "MRR", "Recall@5", "Role"], main_table),
        "",
        "## 5. 显著性与泛化检查",
        "",
        markdown_table(["Comparison", "Metric", "Delta", "Permutation p", "CI Low", "CI High"], sig_table),
        "",
        "## 6. 稳定性与负结果",
        "",
        f"- DeepSeek memory writer 三次运行：MRR mean={f(writer_mrr['mean'])}, stdev={f(writer_mrr['stdev'])}; Recall@5 mean={f(writer_r5['mean'])}, stdev={f(writer_r5['stdev'])}。",
        f"- Type 3 supervised set selector Coverage@5 delta={signed(type3_cov['mean_delta'])}, p={f(type3_cov['permutation_p_value'], 4)}；该结果应写为负结果和边界分析。",
        f"- Human/LLM 错误复核：已有 80 条确认表、priority20 快速抽查包 {priority_samples} 条和盲审人工复核表；当前人工确认 {priority_confirmed} 条；不能写作 human-verified error analysis。",
        "",
        "## 7. 复现与审稿风险",
        "",
        f"- 复现清单：artifact gate {artifact_pass}/{len(repro_artifacts)}，metric gate {metric_pass}/{len(repro_metrics)}。",
        f"- 投稿风险矩阵：{len(gap)} 个风险，其中 blocker={blocker_count}。",
        "- 两个 blocker：外部 embedding baseline 未实际完成；Human/LLM 人工确认未完成。",
        "",
        "## 8. 论文写法边界",
        "",
        "- 可以写：fact-level memory 在 LoCoMo10 上有效且更紧凑；candidate-level reranker 在 held-out 和 LOCO split 下稳定优于 type-aware。",
        "- 可以写：Type 3 multi-evidence retrieval 是当前方法边界，浅层修复方法为负结果。",
        "- 暂不能写：跨数据集泛化、生产规模 ANN 结论、human-verified error analysis、外部 embedding baseline 主结果。",
        "",
        "## 9. 最小投稿前检查",
        "",
        "- 完成至少一个外部 embedding baseline 并生成 delta。",
        "- 优先填写 priority20 blind review CSV 的 human_* 字段，回填 confirmation 后报告 quick-review exact agreement 和 Cohen's kappa；投稿前再扩展到完整 80 条。",
        "- 在论文实验设置中显式写出 LoCoMo10 slice、BGE-M3 cache、DeepSeek writer、LOCO split、paired significance test。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate experiment protocol appendix.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    write_report(args.output_report, args.project_root)
    print(json.dumps({
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
