#!/usr/bin/env python3
"""Generate a paper-readiness evidence matrix from cached experiment outputs."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
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
    writer_cost = read_csv(outputs / "agent_memory_writer_cost_boundary.csv")
    type_sig = read_csv(outputs / "agent_memory_type_aware_significance_results.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    reranker_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    feature_ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    seed_stability = read_csv(outputs / "agent_memory_candidate_reranker_seed_stability.csv")
    train_fraction_sensitivity = read_csv(outputs / "agent_memory_candidate_reranker_train_fraction_sensitivity.csv")
    effect_size = read_csv(outputs / "agent_memory_candidate_reranker_paired_effect_size.csv")
    statistical_power = read_csv(outputs / "agent_memory_candidate_reranker_statistical_power.csv")
    oracle_gap = read_csv(outputs / "agent_memory_candidate_oracle_gap_analysis.csv")
    bootstrap_ci = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")
    reranker_loco = read_csv(outputs / "agent_memory_candidate_reranker_loco_summary.csv")
    intrinsic_loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    reranker_loco_sig = read_csv(outputs / "agent_memory_candidate_reranker_loco_significance_results.csv")
    query_type = read_csv(outputs / "agent_memory_query_type_locomo10_best_methods.csv")
    coverage = read_csv(outputs / "agent_memory_multi_evidence_coverage_summary.csv")
    type3_sig = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    type3_coverage_aware = read_csv(outputs / "agent_memory_type3_coverage_aware_deltas.csv")
    type3_intent_fusion = read_csv(outputs / "agent_memory_type3_intent_fusion_deltas.csv")
    type3_rescue_space = read_csv(outputs / "agent_memory_type3_rescue_space_summary.csv")
    type3_supervised_window = read_csv(outputs / "agent_memory_type3_supervised_window_deltas.csv")
    type3_recall_expansion = read_csv(outputs / "agent_memory_type3_recall_expansion_summary.csv")
    type3_recall_expansion_deltas = read_csv(outputs / "agent_memory_type3_recall_expansion_deltas.csv")
    type3_expanded_selector = read_csv(outputs / "agent_memory_type3_expanded_pool_selector_deltas.csv")
    type3_learned_expanded_selector = read_csv(outputs / "agent_memory_type3_learned_expanded_selector_deltas.csv")
    type3_cluster_coverage_selector = read_csv(outputs / "agent_memory_type3_cluster_coverage_selector_deltas.csv")
    sklearn = read_csv(outputs / "agent_memory_sklearn_nn_prefilter_locomo10_summary.csv")
    faiss_scale = read_csv(outputs / "agent_memory_faiss_scale_100k_locomo10.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    audit_sample = read_csv(outputs / "agent_memory_human_audit_sample_type_aware.csv")
    audit_summary = read_csv(outputs / "agent_memory_human_audit_summary.csv")
    llm_audit_summary = read_csv(outputs / "agent_memory_llm_audit_summary.csv")
    agreement_summary = read_csv(outputs / "agent_memory_human_llm_audit_agreement.csv")
    human_gate = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    embedding_preflight = read_csv(outputs / "agent_memory_api_embedding_preflight.csv")
    embedding_estimate = read_csv(outputs / "agent_memory_api_embedding_run_estimate.csv")
    embedding_comparison = read_csv(outputs / "agent_memory_embedding_baseline_comparison.csv")
    writer_stability = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    dataset_profile = read_csv(outputs / "agent_memory_dataset_slice_profile_summary.csv")

    fact_type_aware = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    observation_type_aware = lookup(baseline, variant="locomo_observation", method="type_aware")
    fact_slice = lookup(dataset_profile, label="llm_extracted_fact_answerable")
    fact_storage = lookup(storage, variant="llm_extracted_fact")
    observation_storage = lookup(storage, variant="locomo_observation")
    writer_api_tokens = lookup(writer_cost, item="memory_write_api_tokens")
    break_even_reuses = lookup(writer_cost, item="storage_break_even_reuses")
    time_aware = lookup(baseline, variant="llm_extracted_fact", method="time_aware")
    type_sig_mrr = lookup(type_sig, metric="mrr")
    type_sig_r5 = lookup(type_sig, metric="recall@5")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    reranker_sig_mrr = lookup(reranker_sig, metric="mrr")
    reranker_sig_r5 = lookup(reranker_sig, metric="recall@5")
    intrinsic_row = lookup(feature_ablation, method="ablation_intrinsic_only")
    intrinsic_seed = lookup(seed_stability, method="ablation_intrinsic_only")
    intrinsic_fraction_rows = [
        row for row in train_fraction_sensitivity
        if row.get("method") == "ablation_intrinsic_only"
    ]
    intrinsic_fraction_min_win_rate = min(float(row["mrr_win_rate"]) for row in intrinsic_fraction_rows)
    intrinsic_fraction_min_delta = min(float(row["mrr_delta_min"]) for row in intrinsic_fraction_rows)
    intrinsic_fraction_mean_delta = statistics.mean(float(row["mrr_delta_mean"]) for row in intrinsic_fraction_rows)
    intrinsic_effect_mrr = lookup(
        effect_size,
        comparison="intrinsic_only_vs_type_aware",
        group="all",
        group_value="all",
        metric="mrr",
    )
    intrinsic_effect_r5 = lookup(
        effect_size,
        comparison="intrinsic_only_vs_type_aware",
        group="all",
        group_value="all",
        metric="recall@5",
    )
    intrinsic_effect_type3_r5 = lookup(
        effect_size,
        comparison="intrinsic_only_vs_type_aware",
        group="query_type",
        group_value="3",
        metric="recall@5",
    )
    intrinsic_power_mrr = lookup(
        statistical_power,
        comparison="intrinsic_only_vs_type_aware",
        metric="mrr",
        sample_size="2760",
    )
    intrinsic_power_r5 = lookup(
        statistical_power,
        comparison="intrinsic_only_vs_type_aware",
        metric="recall@5",
        sample_size="2760",
    )
    heldout_oracle_mrr = lookup(oracle_gap, scenario="heldout_intrinsic", metric="mrr")
    heldout_oracle_r5 = lookup(oracle_gap, scenario="heldout_intrinsic", metric="recall@5")
    loco_oracle_mrr = lookup(oracle_gap, scenario="loco_intrinsic", metric="mrr")
    type3_oracle_cov5 = lookup(oracle_gap, scenario="type3_set_coverage", metric="coverage_ratio@5")
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
    intrinsic_loco_row = lookup(intrinsic_loco, method="intrinsic_reranker_loco")
    intrinsic_loco_mrr = lookup(
        bootstrap_ci,
        scenario="candidate_reranker_intrinsic_loco",
        metric="mrr",
    )
    intrinsic_loco_r5 = lookup(
        bootstrap_ci,
        scenario="candidate_reranker_intrinsic_loco",
        metric="recall@5",
    )
    reranker_loco_row = lookup(reranker_loco, method="candidate_reranker_loco")
    reranker_loco_base = lookup(reranker_loco, method="type_aware")
    reranker_loco_sig_mrr = lookup(reranker_loco_sig, metric="mrr")
    reranker_loco_sig_r5 = lookup(reranker_loco_sig, metric="recall@5")
    type3_row = lookup(query_type, variant="llm_extracted_fact", query_type="3")
    type5_row = lookup(query_type, variant="llm_extracted_fact", query_type="5")
    cov_type3 = lookup(coverage, query_type="3", method="type_aware")
    cov_type5 = lookup(coverage, query_type="5", method="type_aware")
    type3_selector_sig = lookup(type3_sig, experiment="supervised_set_selector", metric="coverage_ratio@5")
    type3_coverage_aware_free = lookup(type3_coverage_aware, method="coverage_aware_free")
    type3_intent_top5 = lookup(type3_intent_fusion, method="intent_fusion_top5_window_keep_top1")
    type3_rescue = lookup(type3_rescue_space, scope="all_type3_candidate_reranker_top20")
    type3_window = lookup(type3_supervised_window, method="supervised_window_reranker")
    type3_recall_best = lookup(type3_recall_expansion, method="candidate20_plus_offline50_facet50")
    type3_recall_best_delta = lookup(type3_recall_expansion_deltas, method="candidate20_plus_offline50_facet50")
    type3_expanded_append = lookup(type3_expanded_selector, method="candidate20_then_expansion")
    type3_expanded_selector_row = lookup(type3_expanded_selector, method="expanded_pool_selector")
    type3_expanded_oracle = lookup(type3_expanded_selector, method="expanded_pool_oracle_top5")
    type3_learned_expanded = lookup(type3_learned_expanded_selector, method="learned_expanded_selector")
    type3_learned_oracle = lookup(type3_learned_expanded_selector, method="expanded_pool_oracle_top5")
    type3_cluster_coverage = lookup(type3_cluster_coverage_selector, method="cluster_coverage_selector")
    type3_cluster_oracle = lookup(type3_cluster_coverage_selector, method="expanded_pool_oracle_top5")
    sklearn_200 = lookup(sklearn, candidate_limit="200", method="type_aware")
    faiss_flat = lookup(faiss_scale, memory_bank_size="100000", index_type="flat", top_k="200")
    faiss_ivf4 = lookup(faiss_scale, memory_bank_size="100000", index_type="ivf", nprobe="4", top_k="200")

    artifact_pass = sum(1 for row in repro_artifacts if row["exists"] == "True")
    metric_pass = sum(1 for row in repro_metrics if row["pass"] == "True")
    audit_labeled = sum(int(row["count"]) for row in audit_summary if row["group"] == "auto_reason")
    llm_audit_labeled = sum(int(row["count"]) for row in llm_audit_summary if row["group"] == "auto_reason")
    llm_audit_correct = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="yes")
    llm_audit_partial = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="partial")
    llm_audit_no = lookup(llm_audit_summary, group="field", label="auto_reason_correct", value="no")
    agreement_confirmed = lookup(agreement_summary, group="overview", label="confirmed_samples")
    agreement_errors = lookup(agreement_summary, group="overview", label="validation_errors")
    human_gate_priority = lookup(human_gate, label="priority20")
    human_gate_full = lookup(human_gate, label="full80")
    embedding_completed = sum(1 for row in embedding_status if row["status"] == "completed")
    embedding_ready = sum(1 for row in embedding_status if row["status"] in {"completed", "ready_to_run"})
    preflight_required_pass = sum(
        1 for row in embedding_preflight
        if row["severity"] == "required" and row["pass"] == "True"
    )
    preflight_required_total = sum(1 for row in embedding_preflight if row["severity"] == "required")
    embedding_items = sum(int(row["items"]) for row in embedding_estimate)
    embedding_tokens = sum(int(row["approx_tokens"]) for row in embedding_estimate)
    embedding_batches = sum(0 if row["cache_exists"] == "True" else int(row["api_batches_if_uncached"]) for row in embedding_estimate)
    embedding_comparison_done = all(row["status"] == "completed" for row in embedding_comparison)
    writer_completed = max(int(row["completed_runs"]) for row in writer_stability)
    writer_ready = writer_completed >= 3

    storage_ratio = float(fact_storage["memory_tokens"]) / float(observation_storage["memory_tokens"])
    sklearn_delta = float(sklearn_200["mrr"]) - float(fact_type_aware["mrr"])

    rows = [
        {
            "claim": "DeepSeek 抽取的事实级记忆在 LoCoMo10 上具备竞争力。",
            "status": "main_result",
            "evidence": (
                f"DeepSeek fact + type-aware: MRR {f(fact_type_aware['mrr'])}, R@5 {f(fact_type_aware['recall@5'])}; "
                f"LoCoMo observation + type-aware: MRR {f(observation_type_aware['mrr'])}, R@5 {f(observation_type_aware['recall@5'])}. "
                f"Dataset slice: {fact_slice['queries']}/{fact_slice['raw_query_count']} raw queries answerable ({pct(fact_slice['answerable_share'])}), "
                f"{fact_slice['groups']} groups, {fact_slice['sessions']} sessions, multi-gold query share {pct(fact_slice['multi_gold_query_share'])}."
            ),
            "support_level": "strong_cached",
            "primary_artifacts": "agent_memory_baseline_comparison_locomo10.csv; agent_memory_llm_extraction_locomo10_comparison_zh.md; agent_memory_dataset_slice_profile_zh.md",
            "paper_use": "可以作为记忆形态对比主结果，但需要说明当前仍是 LoCoMo10 切片。",
            "remaining_gap": "仍需在 LoCoMo10 之外补外部数据或更大真实 memory bank，才能宣称广泛泛化。",
        },
        {
            "claim": "事实级记忆相比 LoCoMo observation memory 能减少存储 token。",
            "status": "main_result",
            "evidence": (
                f"Fact memory tokens {fact_storage['memory_tokens']} vs observation {observation_storage['memory_tokens']}; "
                f"ratio {f(storage_ratio)}, saving about {pct(1.0 - storage_ratio)}. "
                f"One-time writer API tokens are reported separately: {writer_api_tokens['value']}; "
                f"token-only storage break-even diagnostic is {f(break_even_reuses['value'])} retrieval passes."
            ),
            "support_level": "strong_cached",
            "primary_artifacts": "agent_memory_baseline_comparison_locomo10.csv; agent_memory_cost_latency_locomo10_zh.md; agent_memory_writer_cost_boundary_zh.md",
            "paper_use": "可以支撑 memory compression / storage efficiency 动机。",
            "remaining_gap": "若要报告货币成本，需要按目标 provider 的实时 input/output 单价换算；token-only break-even 不应写成费用或能耗结论。",
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
            "claim": "Intrinsic 候选级学习重排是当前最强的方法贡献。",
            "status": "main_method",
            "evidence": (
                f"Held-out type-aware MRR {f(reranker_base['mrr_mean'])}, R@5 {f(reranker_base['recall@5_mean'])}; "
                f"full candidate reranker MRR {f(reranker_row['mrr_mean'])}, R@5 {f(reranker_row['recall@5_mean'])}; "
                f"MRR delta {signed(reranker_sig_mrr['mean_delta'])}, p={f(reranker_sig_mrr['permutation_p_value'], 4)}; "
                f"R@5 delta {signed(reranker_sig_r5['mean_delta'])}, p={f(reranker_sig_r5['permutation_p_value'], 4)}. "
                f"Intrinsic-only reranker MRR {f(intrinsic_row['mrr_mean'])}, R@5 {f(intrinsic_row['recall@5_mean'])}; "
                f"delta vs type-aware {signed(intrinsic_vs_type_mrr['delta_mean'])}, 95% CI [{f(intrinsic_vs_type_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_type_mrr['delta_ci_high'], 4)}]; "
                f"delta vs full {signed(intrinsic_vs_full_mrr['delta_mean'])}, 95% CI [{f(intrinsic_vs_full_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_full_mrr['delta_ci_high'], 4)}]. "
                f"20-seed stability: positive seeds {intrinsic_seed['mrr_positive_seeds']}/{intrinsic_seed['seeds']}, "
                f"mean MRR delta {signed(intrinsic_seed['mrr_delta_mean'])}, min MRR delta {signed(intrinsic_seed['mrr_delta_min'])}. "
                f"Train-fraction sensitivity: fractions 0.5/0.6/0.7/0.8, min win rate {f(intrinsic_fraction_min_win_rate, 2)}, "
                f"min MRR delta {signed(intrinsic_fraction_min_delta)}, mean fraction-level MRR delta {signed(intrinsic_fraction_mean_delta)}. "
                f"Oracle-gap closure: held-out MRR {f(heldout_oracle_mrr['closure_rate'], 3)}, held-out R@5 {f(heldout_oracle_r5['closure_rate'], 3)}, "
                f"LOCO MRR {f(loco_oracle_mrr['closure_rate'], 3)}. "
                f"Statistical power: full-sample MRR CI half-width {f(intrinsic_power_mrr['bootstrap_ci_half_width'], 4)}, "
                f"R@5 CI half-width {f(intrinsic_power_r5['bootstrap_ci_half_width'], 4)}. "
                f"Paired outcome: MRR improved/worsened/tied {intrinsic_effect_mrr['improved_pairs']}/{intrinsic_effect_mrr['worsened_pairs']}/{intrinsic_effect_mrr['tied_pairs']}, "
                f"Cohen dz {f(intrinsic_effect_mrr['cohen_dz'], 4)}; R@5 improved/worsened/tied {intrinsic_effect_r5['improved_pairs']}/{intrinsic_effect_r5['worsened_pairs']}/{intrinsic_effect_r5['tied_pairs']}; "
                f"Type 3 R@5 delta {signed(intrinsic_effect_type3_r5['mean_delta'])}; Type 3 Coverage@5 oracle-gap closure {signed(type3_oracle_cov5['closure_rate'])}. "
                f"LOCO split: type-aware MRR {f(reranker_loco_base['mrr_mean'])}, candidate reranker MRR {f(reranker_loco_row['mrr_mean'])}; "
                f"weighted MRR delta {signed(reranker_loco_sig_mrr['mean_delta'])}, p={f(reranker_loco_sig_mrr['permutation_p_value'], 4)}; "
                f"weighted R@5 delta {signed(reranker_loco_sig_r5['mean_delta'])}, p={f(reranker_loco_sig_r5['permutation_p_value'], 4)}. "
                f"Intrinsic LOCO MRR {f(intrinsic_loco_row['mrr_mean'])}, R@5 {f(intrinsic_loco_row['recall@5_mean'])}; "
                f"MRR delta {signed(intrinsic_loco_mrr['delta_mean'])}, 95% CI [{f(intrinsic_loco_mrr['delta_ci_low'], 4)}, {f(intrinsic_loco_mrr['delta_ci_high'], 4)}]; "
                f"R@5 delta {signed(intrinsic_loco_r5['delta_mean'])}, 95% CI [{f(intrinsic_loco_r5['delta_ci_low'], 4)}, {f(intrinsic_loco_r5['delta_ci_high'], 4)}]."
            ),
            "support_level": "strong_heldout_and_loco_statistical",
            "primary_artifacts": "agent_memory_candidate_reranker_feature_ablation_summary.csv; agent_memory_candidate_reranker_feature_ablation_zh.md; agent_memory_candidate_reranker_paired_effect_size_zh.md; agent_memory_candidate_reranker_statistical_power_zh.md; agent_memory_paper_case_study_pack_zh.md; agent_memory_candidate_reranker_seed_stability_zh.md; agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md; agent_memory_candidate_oracle_gap_analysis_zh.md; agent_memory_candidate_reranker_intrinsic_loco_summary.csv; agent_memory_candidate_reranker_intrinsic_loco_zh.md; agent_memory_bootstrap_metric_ci_zh.md",
            "paper_use": "应作为当前论文方法增量的核心结果；full reranker 保留为消融对照。",
            "remaining_gap": "Held-out 和 LOCO 已支持跨 LoCoMo conversation 泛化；若要宣称跨数据集泛化，仍需外部数据集验证。",
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
                f"p={f(type3_selector_sig['permutation_p_value'], 4)}; Type3-specific reranker and keyword decomposition also reduce Coverage@5. "
                f"Top-20 coverage-aware unsupervised reranking also reduces Coverage@5 by {signed(type3_coverage_aware_free['delta_coverage_ratio@5'])} "
                f"and Full@5 by {signed(type3_coverage_aware_free['delta_full_coverage@5'])}."
            ),
            "support_level": "statistically_supported_negative",
            "primary_artifacts": "agent_memory_type3_coverage_significance_summary.csv; agent_memory_type3_coverage_significance_zh.md; agent_memory_type3_coverage_aware_zh.md",
            "paper_use": "适合作为边界/负结果消融，而不是作为改进方法。",
            "remaining_gap": "无监督 coverage/diversity 信号已不足；下一步应尝试 LLM 子问题生成或真正的 listwise/setwise objective。",
        },
        {
            "claim": "保守的 Type 3 意图窗口重排可以微调首个证据位置，但不足以解决多证据覆盖。",
            "status": "limited_positive",
            "evidence": (
                f"Intent-facet Top-5 window reranking changes MRR by {signed(type3_intent_top5['delta_mrr'])} while keeping "
                f"Recall@5, Coverage@5, Full@5, Coverage@20, and Full@20 unchanged "
                f"({signed(type3_intent_top5['delta_recall@5'])}, {signed(type3_intent_top5['delta_coverage_ratio@5'])}, "
                f"{signed(type3_intent_top5['delta_full_coverage@5'])})."
            ),
            "support_level": "small_clean_diagnostic",
            "primary_artifacts": "agent_memory_type3_intent_fusion_zh.md; agent_memory_type3_intent_fusion_summary.csv; agent_memory_type3_intent_fusion_deltas.csv",
            "paper_use": "可作为轻量优化尝试或消融边界：保守窗口重排不会破坏 Top-5 证据集合，但收益很小。",
            "remaining_gap": "需要学习式 set/listwise 目标来真正提升 Coverage@5 和 Full@5。",
        },
        {
            "claim": "Type 3 错误同时包含重排可救回空间和候选召回缺失。",
            "status": "diagnostic",
            "evidence": (
                f"Within candidate-reranker Top-20, {pct(type3_rescue['rerank_rescuable_share'])} of Type3 query-splits are rerank-rescuable; "
                f"{pct(type3_rescue['candidate_missing_all_gold_share'])} miss all gold evidence. "
                f"Oracle Top-5 coverage can rise from {f(type3_rescue['top5_coverage'])} to {f(type3_rescue['oracle_top5_coverage'])}, "
                f"with Full@5 rising from {f(type3_rescue['top5_full'])} to {f(type3_rescue['oracle_top5_full'])}."
            ),
            "support_level": "strong_diagnostic",
            "primary_artifacts": "agent_memory_type3_rescue_space_zh.md; agent_memory_type3_rescue_space_summary.csv; agent_memory_type3_rescue_space_classes.csv",
            "paper_use": "用于解释为什么下一步需要双线优化：listwise/setwise 重排负责可救回样本，召回增强负责候选缺失样本。",
            "remaining_gap": "该结果是 oracle 上限分析，不能作为实际方法指标；实际算法仍需在 held-out query 上验证。",
        },
        {
            "claim": "单候选监督窗口重排不足以利用 Type 3 的 Top-20 可救回空间。",
            "status": "negative_result",
            "evidence": (
                f"Dependency-free supervised window reranking changes MRR by {signed(type3_window['delta_mrr'])}; "
                f"Recall@5, Coverage@5, and Full@5 change by {signed(type3_window['delta_recall@5'])}, "
                f"{signed(type3_window['delta_coverage_ratio@5'])}, and {signed(type3_window['delta_full_coverage@5'])}."
            ),
            "support_level": "heldout_negative",
            "primary_artifacts": "agent_memory_type3_supervised_window_zh.md; agent_memory_type3_supervised_window_summary.csv; agent_memory_type3_supervised_window_deltas.csv",
            "paper_use": "可作为方法选择的负结果：仅学习单条候选相关性不能解决多证据集合覆盖。",
            "remaining_gap": "需要直接优化集合覆盖的 listwise/setwise 目标，或引入 LLM 子问题生成提高候选召回。",
        },
        {
            "claim": "多路离线召回扩展可以显著减少 Type 3 候选池缺证据问题。",
            "status": "positive_diagnostic",
            "evidence": (
                f"Merging candidate Top-20 with offline Top-50 and intent-facet Top-50 lowers Missing-All from "
                f"{f(lookup(type3_recall_expansion, method='candidate_top20')['missing_all_gold_share'])} to "
                f"{f(type3_recall_best['missing_all_gold_share'])} "
                f"({signed(type3_recall_best_delta['delta_missing_all_gold_share'])}); "
                f"Coverage@100 rises by {signed(type3_recall_best_delta['delta_coverage_ratio@100'])} and "
                f"Full@100 rises by {signed(type3_recall_best_delta['delta_full_coverage@100'])}."
            ),
            "support_level": "strong_candidate_pool_diagnostic",
            "primary_artifacts": "agent_memory_type3_recall_expansion_zh.md; agent_memory_type3_recall_expansion_summary.csv; agent_memory_type3_recall_expansion_deltas.csv",
            "paper_use": "可作为下一版主方法的动机：先扩展候选池，再做 listwise/setwise 证据选择。",
            "remaining_gap": "该实验只评价候选池覆盖，不评价最终排序；需要接后续重排器验证端到端 MRR/Coverage@5。",
        },
        {
            "claim": "扩展候选池的收益尚未被无监督 Top-5 选择器充分转化。",
            "status": "diagnostic_boundary",
            "evidence": (
                f"Appending expansion after candidate Top-20 preserves Top-5 while improving Coverage@100 by "
                f"{signed(type3_expanded_append['delta_coverage_ratio@100'])} and Full@100 by "
                f"{signed(type3_expanded_append['delta_full_coverage@100'])}. "
                f"The unsupervised expanded-pool selector changes Coverage@5 by "
                f"{signed(type3_expanded_selector_row['delta_coverage_ratio@5'])}, while oracle Top-5 on the expanded pool could improve "
                f"Coverage@5 by {signed(type3_expanded_oracle['delta_coverage_ratio@5'])} and Full@5 by "
                f"{signed(type3_expanded_oracle['delta_full_coverage@5'])}."
            ),
            "support_level": "strong_oracle_gap_diagnostic",
            "primary_artifacts": "agent_memory_type3_expanded_pool_selector_zh.md; agent_memory_type3_expanded_pool_selector_summary.csv; agent_memory_type3_expanded_pool_selector_deltas.csv",
            "paper_use": "用于支撑下一版主方法：扩展召回池已经有证据，但必须设计学习式 listwise/setwise 选择器才能把收益前移到 Top-5。",
            "remaining_gap": "当前 selector 是无监督启发式，不能作为最终改进；需要训练或 LLM 辅助标签来学习集合级选择。",
        },
        {
            "claim": "轻量学习式扩展池选择器仍不足以转化 Type 3 oracle 空间。",
            "status": "heldout_negative_with_oracle_gap",
            "evidence": (
                f"With train/validation/test separation, the learned expanded selector changes MRR by "
                f"{signed(type3_learned_expanded['delta_mrr'])}, Coverage@5 by "
                f"{signed(type3_learned_expanded['delta_coverage_ratio@5'])}, and Full@5 by "
                f"{signed(type3_learned_expanded['delta_full_coverage@5'])}. "
                f"Oracle Top-5 on the same expanded pool could still improve Coverage@5 by "
                f"{signed(type3_learned_oracle['delta_coverage_ratio@5'])} and Full@5 by "
                f"{signed(type3_learned_oracle['delta_full_coverage@5'])}."
            ),
            "support_level": "heldout_negative_with_oracle_gap",
            "primary_artifacts": "agent_memory_type3_learned_expanded_selector_zh.md; agent_memory_type3_learned_expanded_selector_summary.csv; agent_memory_type3_learned_expanded_selector_deltas.csv; agent_memory_type3_learned_expanded_selector_weights.csv",
            "paper_use": "可以作为方法演进证据：候选扩展有效，但简单点式学习/均值差权重不足，需要更强的 listwise/setwise 训练目标或 LLM 子问题标签。",
            "remaining_gap": "下一步需要引入真正的集合级监督信号，评价是否能同时提升 MRR、Coverage@5 与 Full@5。",
        },
        {
            "claim": "无监督簇多样性不能直接替代答案证据覆盖目标。",
            "status": "negative_setwise_diagnostic",
            "evidence": (
                f"Cluster coverage selection changes Top-5 cluster count by "
                f"{signed(type3_cluster_coverage['delta_top5_cluster_count'])}, but changes Coverage@5 by "
                f"{signed(type3_cluster_coverage['delta_coverage_ratio@5'])} and Full@5 by "
                f"{signed(type3_cluster_coverage['delta_full_coverage@5'])}. "
                f"The oracle gap on the same pool remains Coverage@5 "
                f"{signed(type3_cluster_oracle['delta_coverage_ratio@5'])} and Full@5 "
                f"{signed(type3_cluster_oracle['delta_full_coverage@5'])}."
            ),
            "support_level": "negative_setwise_diagnostic_with_oracle_gap",
            "primary_artifacts": "agent_memory_type3_cluster_coverage_selector_zh.md; agent_memory_type3_cluster_coverage_selector_summary.csv; agent_memory_type3_cluster_coverage_selector_deltas.csv",
            "paper_use": "可作为消融结论：集合级目标是必要的，但简单无监督多样性与 gold evidence coverage 不对齐。",
            "remaining_gap": "需要用监督式 listwise/setwise 目标、子问题覆盖标签，或 LLM 生成的 query decomposition 来对齐证据覆盖。",
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
            "claim": "自动错误分析已经具备人工复核入口，并已有 LLM-assisted 预标注。",
            "status": "reliability_protocol",
            "evidence": (
                f"已从 type-aware Top-1 错误中分层抽样 {len(audit_sample)} 条；当前已汇总人工标注 {audit_labeled} 条；"
                f"LLM-assisted 预标注 {llm_audit_labeled} 条，auto_reason_correct yes/partial/no="
                f"{llm_audit_correct['count']}/{llm_audit_partial['count']}/{llm_audit_no['count']}；"
                f"Human/LLM 确认表已生成，人工确认 {agreement_confirmed['count']} 条，非法标签 {agreement_errors['count']}；"
                f"readiness gate: priority20 {human_gate_priority['confirmed_samples']}/{human_gate_priority['min_required']}, "
                f"full80 {human_gate_full['confirmed_samples']}/{human_gate_full['min_required']}。"
            ),
            "support_level": "llm_assisted_protocol_ready",
            "primary_artifacts": "agent_memory_human_audit_sample_type_aware.csv; agent_memory_human_audit_protocol_zh.md; agent_memory_llm_audit_summary_zh.md; agent_memory_llm_audit_report_zh.md; agent_memory_human_llm_audit_confirmation.csv; agent_memory_human_llm_audit_agreement_zh.md; agent_memory_human_audit_readiness_gate_zh.md",
            "paper_use": "可以说明已有 LLM-assisted 预复核流程；在人工确认前，不能把它写成人工验证结论。",
            "remaining_gap": "需要在 confirmation CSV 中填写 human_* 字段，并重新运行一致性脚本，得到 exact agreement 与 Cohen's kappa。",
        },
        {
            "claim": "DeepSeek memory writer 在 LoCoMo10 重复抽取中具有可报告的稳定性。",
            "status": "stability_result" if writer_ready else "stability_protocol",
            "evidence": (
                f"稳定性 manifest 登记 3 次抽取，目前 completed runs={writer_completed}；"
                f"{'已可报告均值和标准差。' if writer_ready else '少于 3 次，不能报告方差。'}"
            ),
            "support_level": "variance_ready" if writer_ready else "protocol_ready_pending_runs",
            "primary_artifacts": "agent_memory_writer_stability_zh.md; deepseek_writer_stability_manifest.csv",
            "paper_use": "可以作为 memory writer stability 小节；需要说明 temperature 设置和 LoCoMo10 slice 范围。",
            "remaining_gap": "若投稿目标更高，需要在额外数据集或更大 LoCoMo slice 上复验。",
        },
        {
            "claim": "外部 embedding baseline 已经具备 API 接入与缓存框架，但尚未形成实验结果。",
            "status": "baseline_protocol",
            "evidence": f"已登记 {len(embedding_status)} 个外部 embedding baseline；completed={embedding_completed}, ready_or_completed={embedding_ready}；preflight required={preflight_required_pass}/{preflight_required_total}；预计文本 {embedding_items} 条、约 {embedding_tokens} tokens、未缓存批次 {embedding_batches}；对比表完成={embedding_comparison_done}。",
            "support_level": "protocol_ready_pending_run",
            "primary_artifacts": "agent_memory_embedding_baseline_status_zh.md; agent_memory_api_embedding_preflight_zh.md; agent_memory_api_embedding_run_estimate_zh.md; agent_memory_embedding_baseline_comparison_zh.md; agent_memory_offline_embedding_sensitivity_zh.md; memory_eval.py",
            "paper_use": "可以作为复现实验入口；离线 hash/BM25 敏感性可写为下界诊断，但外部 API summary.csv 生成前不能写入外部 embedding 主结果表。",
            "remaining_gap": "需要提供 OpenAI 或其他 OpenAI-compatible provider 的 embedding API key，并实际运行至少一个外部 embedding 对照；hash baseline 不能替代真实外部 embedding。",
        },
        {
            "claim": "完整项目距离最终投稿仍需要额外验证。",
            "status": "open_gap",
            "evidence": "剩余缺口包括实际完成更强 embedding/API baseline、更大真实 memory bank 效率实验，以及人工错误复核标注结果。",
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
        "1. 加入至少一个强 embedding/API baseline，避免结果只依赖 BGE-M3。",
        "2. 对错误分析做人工抽样复核，报告自动错误分类的可信度。",
        "3. Type 3 暂按负结果和边界分析书写，不应宣称已经解决多证据检索。",
        "4. 若目标期刊/会议要求更强泛化，应在额外数据集或更大真实 memory bank 上复验 writer stability 和 candidate reranker。",
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
