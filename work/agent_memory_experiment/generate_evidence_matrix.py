#!/usr/bin/env python3
"""Generate a paper-readiness evidence matrix from cached experiment outputs."""

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


def pct(value: Any, digits: int = 1) -> str:
    return f"{100.0 * float(value):.{digits}f}%"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_rows(outputs: Path) -> list[dict[str, str]]:
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    storage = read_csv(outputs / "agent_memory_cost_storage_locomo10.csv")
    type_sig = read_csv(outputs / "agent_memory_type_aware_significance_results.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    reranker_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    query_type = read_csv(outputs / "agent_memory_query_type_locomo10_best_methods.csv")
    coverage = read_csv(outputs / "agent_memory_multi_evidence_coverage_summary.csv")
    type3_sig = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    sklearn = read_csv(outputs / "agent_memory_sklearn_nn_prefilter_locomo10_summary.csv")
    faiss_scale = read_csv(outputs / "agent_memory_faiss_scale_100k_locomo10.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    audit_sample = read_csv(outputs / "agent_memory_human_audit_sample_type_aware.csv")
    audit_summary = read_csv(outputs / "agent_memory_human_audit_summary.csv")
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    embedding_estimate = read_csv(outputs / "agent_memory_api_embedding_run_estimate.csv")
    embedding_comparison = read_csv(outputs / "agent_memory_embedding_baseline_comparison.csv")
    writer_stability = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")

    fact_type_aware = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    observation_type_aware = lookup(baseline, variant="locomo_observation", method="type_aware")
    fact_storage = lookup(storage, variant="llm_extracted_fact")
    observation_storage = lookup(storage, variant="locomo_observation")
    time_aware = lookup(baseline, variant="llm_extracted_fact", method="time_aware")
    type_sig_mrr = lookup(type_sig, metric="mrr")
    type_sig_r5 = lookup(type_sig, metric="recall@5")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    reranker_sig_mrr = lookup(reranker_sig, metric="mrr")
    reranker_sig_r5 = lookup(reranker_sig, metric="recall@5")
    type3_row = lookup(query_type, variant="llm_extracted_fact", query_type="3")
    type5_row = lookup(query_type, variant="llm_extracted_fact", query_type="5")
    cov_type3 = lookup(coverage, query_type="3", method="type_aware")
    cov_type5 = lookup(coverage, query_type="5", method="type_aware")
    type3_selector_sig = lookup(type3_sig, experiment="supervised_set_selector", metric="coverage_ratio@5")
    sklearn_200 = lookup(sklearn, candidate_limit="200", method="type_aware")
    faiss_flat = lookup(faiss_scale, memory_bank_size="100000", index_type="flat", top_k="200")
    faiss_ivf4 = lookup(faiss_scale, memory_bank_size="100000", index_type="ivf", nprobe="4", top_k="200")

    artifact_pass = sum(1 for row in repro_artifacts if row["exists"] == "True")
    metric_pass = sum(1 for row in repro_metrics if row["pass"] == "True")
    audit_labeled = sum(int(row["count"]) for row in audit_summary if row["group"] == "auto_reason")
    embedding_completed = sum(1 for row in embedding_status if row["status"] == "completed")
    embedding_ready = sum(1 for row in embedding_status if row["status"] in {"completed", "ready_to_run"})
    embedding_items = sum(int(row["items"]) for row in embedding_estimate)
    embedding_tokens = sum(int(row["approx_tokens"]) for row in embedding_estimate)
    embedding_batches = sum(0 if row["cache_exists"] == "True" else int(row["api_batches_if_uncached"]) for row in embedding_estimate)
    embedding_comparison_done = all(row["status"] == "completed" for row in embedding_comparison)
    writer_completed = max(int(row["completed_runs"]) for row in writer_stability)

    storage_ratio = float(fact_storage["memory_tokens"]) / float(observation_storage["memory_tokens"])
    sklearn_delta = float(sklearn_200["mrr"]) - float(fact_type_aware["mrr"])

    rows = [
        {
            "claim": "DeepSeek 抽取的事实级记忆在 LoCoMo10 上具备竞争力。",
            "status": "main_result",
            "evidence": (
                f"DeepSeek fact + type-aware: MRR {f(fact_type_aware['mrr'])}, R@5 {f(fact_type_aware['recall@5'])}; "
                f"LoCoMo observation + type-aware: MRR {f(observation_type_aware['mrr'])}, R@5 {f(observation_type_aware['recall@5'])}."
            ),
            "support_level": "strong_cached",
            "primary_artifacts": "agent_memory_baseline_comparison_locomo10.csv; agent_memory_llm_extraction_locomo10_comparison_zh.md",
            "paper_use": "可以作为记忆形态对比主结果，但需要说明当前仍是 LoCoMo10 切片。",
            "remaining_gap": "需要做多 seed / temperature 的 DeepSeek 重复抽取，才能宣称 memory writer 稳定性。",
        },
        {
            "claim": "事实级记忆相比 LoCoMo observation memory 能减少存储 token。",
            "status": "main_result",
            "evidence": (
                f"Fact memory tokens {fact_storage['memory_tokens']} vs observation {observation_storage['memory_tokens']}; "
                f"ratio {f(storage_ratio)}, saving about {pct(1.0 - storage_ratio)}."
            ),
            "support_level": "strong_cached",
            "primary_artifacts": "agent_memory_baseline_comparison_locomo10.csv; agent_memory_cost_latency_locomo10_zh.md",
            "paper_use": "可以支撑 memory compression / storage efficiency 动机。",
            "remaining_gap": "需要把抽取 API 成本和检索阶段存储成本分开报告，并补充重复抽取方差。",
        },
        {
            "claim": "type-aware 重排相比 time-aware 重排有小幅但统计可靠的提升。",
            "status": "ablation_result",
            "evidence": (
                f"MRR {f(time_aware['mrr'])} -> {f(fact_type_aware['mrr'])}, delta {signed(type_sig_mrr['mean_delta'])}, "
                f"p={f(type_sig_mrr['permutation_p_value'], 4)}; R@5 delta {signed(type_sig_r5['mean_delta'])}, "
                f"p={f(type_sig_r5['permutation_p_value'], 4)}."
            ),
            "support_level": "statistically_supported_small_effect",
            "primary_artifacts": "agent_memory_type_aware_significance_results.csv; agent_memory_type_aware_significance_zh.md",
            "paper_use": "可以写成一个有用但幅度有限的打分组件。",
            "remaining_gap": "不要夸大 Recall@1 / Recall@3，因为它们没有通过显著性检验。",
        },
        {
            "claim": "候选级学习重排是当前最强的方法贡献。",
            "status": "main_method",
            "evidence": (
                f"Held-out type-aware MRR {f(reranker_base['mrr_mean'])}, R@5 {f(reranker_base['recall@5_mean'])}; "
                f"candidate reranker MRR {f(reranker_row['mrr_mean'])}, R@5 {f(reranker_row['recall@5_mean'])}; "
                f"MRR delta {signed(reranker_sig_mrr['mean_delta'])}, p={f(reranker_sig_mrr['permutation_p_value'], 4)}; "
                f"R@5 delta {signed(reranker_sig_r5['mean_delta'])}, p={f(reranker_sig_r5['permutation_p_value'], 4)}."
            ),
            "support_level": "strong_heldout_statistical",
            "primary_artifacts": "agent_memory_candidate_reranker_locomo10_summary.csv; agent_memory_candidate_reranker_significance_results.csv",
            "paper_use": "应作为当前论文方法增量的核心结果。",
            "remaining_gap": "需要加入外部数据集或更大的 LoCoMo split，才能宣称广泛泛化。",
        },
        {
            "claim": "Type 3 多证据问题仍是当前方法边界。",
            "status": "negative_result",
            "evidence": (
                f"Type 3 best method {type3_row['best_method']} with MRR {f(type3_row['mrr'])}, R@5 {f(type3_row['recall@5'])}; "
                f"mean gold evidence {f(cov_type3['mean_gold'])}, multi-evidence share {pct(cov_type3['multi_evidence_share'])}; "
                f"Type 5 multi-evidence share is only {pct(cov_type5['multi_evidence_share'])}."
            ),
            "support_level": "strong_diagnostic",
            "primary_artifacts": "agent_memory_query_type_locomo10_best_methods.csv; agent_memory_multi_evidence_coverage_summary.csv",
            "paper_use": "可以作为 limitations 和下一步研究问题的主要依据。",
            "remaining_gap": "需要更强的 listwise / setwise objective 或 LLM decomposition，不能宣称已解决 Type 3。",
        },
        {
            "claim": "浅层 Type 3 修复方法无法解决多证据检索。",
            "status": "negative_result",
            "evidence": (
                f"Supervised set selector Coverage@5 delta {signed(type3_selector_sig['mean_delta'])}, "
                f"p={f(type3_selector_sig['permutation_p_value'], 4)}; Type3-specific reranker and keyword decomposition also reduce Coverage@5."
            ),
            "support_level": "statistically_supported_negative",
            "primary_artifacts": "agent_memory_type3_coverage_significance_summary.csv; agent_memory_type3_coverage_significance_zh.md",
            "paper_use": "适合作为边界/负结果消融，而不是作为改进方法。",
            "remaining_gap": "下一步应尝试 LLM 子问题生成或真正的 setwise objective。",
        },
        {
            "claim": "向量候选预筛选可以在不损害质量的情况下提升检索速度。",
            "status": "efficiency_result",
            "evidence": (
                f"Sklearn exact NN top-200 + type-aware MRR {f(sklearn_200['mrr'])}, R@5 {f(sklearn_200['recall@5'])}; "
                f"delta vs full type-aware MRR {signed(sklearn_delta)}."
            ),
            "support_level": "strong_cached_efficiency",
            "primary_artifacts": "agent_memory_sklearn_nn_prefilter_locomo10_summary.csv; agent_memory_sklearn_nn_prefilter_locomo10_zh.md",
            "paper_use": "可以支撑论文效率实验章节。",
            "remaining_gap": "需要统一报告 wall-clock 设置，并在更大的真实 memory bank 上验证。",
        },
        {
            "claim": "100k 记忆规模下 ANN 的速度-质量权衡并非天然占优。",
            "status": "efficiency_boundary",
            "evidence": (
                f"100k Flat candidate gold recall {f(faiss_flat['candidate_gold_recall'])}, query {f(faiss_flat['query_seconds'])}s; "
                f"IVF nprobe=4 recall {f(faiss_ivf4['candidate_gold_recall'])}, query {f(faiss_ivf4['query_seconds'])}s."
            ),
            "support_level": "synthetic_scale_diagnostic",
            "primary_artifacts": "agent_memory_faiss_scale_100k_locomo10.csv; agent_memory_faiss_scale_100k_locomo10_zh.md",
            "paper_use": "可以作为扩展性诊断，但必须标注为 synthetic distractor stress test。",
            "remaining_gap": "需要真实的大规模 conversation memory bank 才能形成更强系统结论。",
        },
        {
            "claim": "当前仓库已经具备可复现的缓存实验包。",
            "status": "reproducibility",
            "evidence": f"Reproducibility artifact gate {artifact_pass}/{len(repro_artifacts)} and metric gate {metric_pass}/{len(repro_metrics)}.",
            "support_level": "artifact_checked",
            "primary_artifacts": "agent_memory_reproducibility_checklist_zh.md; agent_memory_environment_snapshot_zh.md",
            "paper_use": "可以用于论文 appendix 和内部复现实验。",
            "remaining_gap": "全新 clone 仍需要按文档准备模型/embedding cache，因为大缓存不进入 Git。",
        },
        {
            "claim": "自动错误分析已经具备人工复核入口，但人工标注尚未完成。",
            "status": "reliability_protocol",
            "evidence": f"已从 type-aware Top-1 错误中分层抽样 {len(audit_sample)} 条；当前已汇总人工标注 {audit_labeled} 条。",
            "support_level": "protocol_ready_unlabeled",
            "primary_artifacts": "agent_memory_human_audit_sample_type_aware.csv; agent_memory_human_audit_protocol_zh.md; agent_memory_human_audit_summary_zh.md",
            "paper_use": "可以说明已有复核流程；在人工标注完成前，不能把自动错误分类当作已验证结论。",
            "remaining_gap": "需要人工填写 manual_reason / auto_reason_correct，并统计一致性或准确率。",
        },
        {
            "claim": "DeepSeek memory writer 稳定性分析框架已经准备好，但重复抽取尚未完成。",
            "status": "stability_protocol",
            "evidence": f"稳定性 manifest 登记 3 次抽取，目前 completed runs={writer_completed}；少于 3 次，不能报告方差。",
            "support_level": "protocol_ready_pending_runs",
            "primary_artifacts": "agent_memory_writer_stability_zh.md; deepseek_writer_stability_manifest.csv",
            "paper_use": "可以作为重复抽取实验入口；在 run2/run3 完成前，不应宣称 memory writer 稳定。",
            "remaining_gap": "需要补齐至少 2 次 DeepSeek 重复抽取，并重新生成均值/标准差。",
        },
        {
            "claim": "外部 embedding baseline 已经具备 API 接入与缓存框架，但尚未形成实验结果。",
            "status": "baseline_protocol",
            "evidence": f"已登记 {len(embedding_status)} 个外部 embedding baseline；completed={embedding_completed}, ready_or_completed={embedding_ready}；预计文本 {embedding_items} 条、约 {embedding_tokens} tokens、未缓存批次 {embedding_batches}；对比表完成={embedding_comparison_done}。",
            "support_level": "protocol_ready_pending_run",
            "primary_artifacts": "agent_memory_embedding_baseline_status_zh.md; agent_memory_api_embedding_run_estimate_zh.md; agent_memory_embedding_baseline_comparison_zh.md; memory_eval.py",
            "paper_use": "可以作为复现实验入口；在 summary.csv 生成前，不能写入主结果表。",
            "remaining_gap": "需要提供 API key 并实际运行 text-embedding-3-small 等外部 embedding 对照。",
        },
        {
            "claim": "完整项目距离最终投稿仍需要额外验证。",
            "status": "open_gap",
            "evidence": "剩余缺口包括完成多 seed DeepSeek 抽取、实际完成更强 embedding/API baseline、更大真实 memory bank 效率实验，以及人工错误复核标注结果。",
            "support_level": "gap_analysis",
            "primary_artifacts": "agent_memory_paper_experiment_status_zh.md; agent_memory_reproducibility_checklist_zh.md",
            "paper_use": "作为下一步 checklist，而不是论文主张。",
            "remaining_gap": "投稿前至少补齐一个强 baseline 家族，以及一个稳定性/可靠性检查。",
        },
    ]
    return rows


def write_report(path: Path, rows: list[dict[str, str]]) -> None:
    headers = ["状态", "主张", "证据", "证据强度", "论文写法", "剩余缺口"]
    table_rows = [
        [
            row["status"],
            row["claim"],
            row["evidence"],
            row["support_level"],
            row["paper_use"],
            row["remaining_gap"],
        ]
        for row in rows
    ]
    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["status"]] = status_counts.get(row["status"], 0) + 1

    lines = [
        "# 论文实验证据矩阵",
        "",
        "本文件把当前实验结果整理为“可写入论文的主张-证据-缺口”矩阵。它用于区分主结果、消融结果、负结果、效率结果和仍不能宣称的开放缺口。",
        "",
        "## 状态汇总",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"| {status} | {count} |")
    lines.extend([
        "",
        "## Evidence Matrix",
        "",
        markdown_table(headers, table_rows),
        "",
        "## 投稿前最低补强建议",
        "",
        "1. 对 DeepSeek memory writer 做至少 3 个 seed / temperature 的重复抽取，报告 retrieval 指标均值和方差。",
        "2. 加入至少一个强 embedding/API baseline，避免结果只依赖 BGE-M3。",
        "3. 对 candidate reranker 增加外部数据或更大 LoCoMo split 的验证。",
        "4. 对错误分析做人工抽样复核，报告自动错误分类的可信度。",
        "5. Type 3 暂按负结果和边界分析书写，不应宣称已经解决多证据检索。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate evidence matrix for paper readiness.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "claims": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
