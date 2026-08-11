#!/usr/bin/env python3
"""Generate a Chinese manuscript draft from cached agent-memory experiments."""

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


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def f(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: Any, digits: int = 4) -> str:
    return f"{float(value):+.{digits}f}"


def pct(value: Any, digits: int = 1) -> str:
    return f"{100 * float(value):.{digits}f}%"


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

    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    storage = read_csv(outputs / "agent_memory_cost_storage_locomo10.csv")
    type_sig = read_csv(outputs / "agent_memory_type_aware_significance_results.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    reranker_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    feature_ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    seed_stability = read_csv(outputs / "agent_memory_candidate_reranker_seed_stability.csv")
    train_fraction_sensitivity = read_csv(outputs / "agent_memory_candidate_reranker_train_fraction_sensitivity.csv")
    effect_size = read_csv(outputs / "agent_memory_candidate_reranker_paired_effect_size.csv")
    oracle_gap = read_csv(outputs / "agent_memory_candidate_oracle_gap_analysis.csv")
    bootstrap_ci = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")
    loco = read_csv(outputs / "agent_memory_candidate_reranker_loco_summary.csv")
    intrinsic_loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    loco_sig = read_csv(outputs / "agent_memory_candidate_reranker_loco_significance_results.csv")
    type3 = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    writer = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    agreement = read_csv(outputs / "agent_memory_human_llm_audit_priority20_agreement.csv")
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    threats = read_csv(outputs / "agent_memory_threats_to_validity.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")

    fact_type = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    fact_time = lookup(baseline, variant="llm_extracted_fact", method="time_aware")
    fact_hybrid = lookup(baseline, variant="llm_extracted_fact", method="hybrid")
    obs_type = lookup(baseline, variant="locomo_observation", method="type_aware")
    fact_storage = lookup(storage, variant="llm_extracted_fact")
    obs_storage = lookup(storage, variant="locomo_observation")
    type_mrr = lookup(type_sig, metric="mrr")
    type_r5 = lookup(type_sig, metric="recall@5")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    reranker_mrr = lookup(reranker_sig, metric="mrr")
    reranker_r5 = lookup(reranker_sig, metric="recall@5")
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
    intrinsic_loco_mrr = lookup(bootstrap_ci, scenario="candidate_reranker_intrinsic_loco", metric="mrr")
    intrinsic_loco_r5 = lookup(bootstrap_ci, scenario="candidate_reranker_intrinsic_loco", metric="recall@5")
    loco_row = lookup(loco, method="candidate_reranker_loco")
    loco_base = lookup(loco, method="type_aware")
    loco_mrr = lookup(loco_sig, metric="mrr")
    loco_r5 = lookup(loco_sig, metric="recall@5")
    type3_cov = lookup(type3, experiment="supervised_set_selector", metric="coverage_ratio@5")
    writer_mrr = lookup(writer, metric="mrr")
    writer_r5 = lookup(writer, metric="recall@5")
    priority_samples = lookup(agreement, group="overview", label="samples")["count"]
    priority_confirmed = lookup(agreement, group="overview", label="confirmed_samples")["count"]
    embedding_completed = sum(1 for row in embedding_status if row["status"] == "completed")
    threat_blockers = [row for row in threats if row.get("status") == "blocker"]
    threat_categories = sorted({row.get("category", "") for row in threats if row.get("category")})
    artifact_pass = sum(1 for row in repro_artifacts if row["exists"] == "True")
    metric_pass = sum(1 for row in repro_metrics if row["pass"] == "True")

    memories = data / "llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
    queries = data / "llm_extracted_locomo10_all_v3_answerable_queries.jsonl"
    memory_count = count_jsonl(memories) if memories.exists() else 0
    query_count = count_jsonl(queries) if queries.exists() else 0
    storage_ratio = float(fact_storage["memory_tokens"]) / float(obs_storage["memory_tokens"])

    main_rows = [
        ["hybrid", f(fact_hybrid["mrr"]), f(fact_hybrid["recall@5"])],
        ["time-aware", f(fact_time["mrr"]), f(fact_time["recall@5"])],
        ["type-aware", f(fact_type["mrr"]), f(fact_type["recall@5"])],
        ["candidate reranker", f(reranker_row["mrr_mean"]), f(reranker_row["recall@5_mean"])],
        ["intrinsic feature reranker", f(intrinsic_row["mrr_mean"]), f(intrinsic_row["recall@5_mean"])],
        ["intrinsic feature reranker LOCO", f(intrinsic_loco_row["mrr_mean"]), f(intrinsic_loco_row["recall@5_mean"])],
        ["candidate reranker LOCO", f(loco_row["mrr_mean"]), f(loco_row["recall@5_mean"])],
    ]
    lines = [
        "# 面向长对话智能体的事实级记忆写入与候选级学习重排",
        "",
        "> 当前状态：论文正文初稿。本文稿已经可用于组会、开题/中期汇报或继续扩写，但在外部 embedding baseline 和人工一致性确认完成前，不应作为最终投稿稿。",
        "",
        "## 摘要",
        "",
        (
            "长对话智能体需要在不断增长的交互历史中检索与当前任务相关的个体事实、事件、偏好和计划。"
            "本文围绕 agent memory 的写入、检索、压缩和重排过程构建一套可复现实验框架，并在 LoCoMo10 answerable slice 上比较 "
            "LLM-written fact memory、LoCoMo observation memory、BGE-M3 embedding 检索、BM25 混合检索、时间感知重排、type-aware 重排和候选级学习重排。"
            f"实验显示，DeepSeek fact memory + type-aware reranking 达到 MRR {f(fact_type['mrr'])}、Recall@5 {f(fact_type['recall@5'])}，"
            f"高于 LoCoMo observation memory + type-aware 的 MRR {f(obs_type['mrr'])}、Recall@5 {f(obs_type['recall@5'])}。"
            f"候选级学习重排进一步将 held-out MRR 从 {f(reranker_base['mrr_mean'])} 提升至 {f(reranker_row['mrr_mean'])}，"
            f"而 feature ablation 显示更简洁的 intrinsic feature reranker 可达到 MRR {f(intrinsic_row['mrr_mean'])}、Recall@5 {f(intrinsic_row['recall@5_mean'])}，"
            f"并在 leave-one-conversation-out split 中达到 MRR {f(intrinsic_loco_row['mrr_mean'])}、Recall@5 {f(intrinsic_loco_row['recall@5_mean'])}。"
            f"同时，事实级记忆将 memory token 降至 observation memory 的 {pct(storage_ratio)}，DeepSeek memory writer 三次运行的 MRR 标准差为 {f(writer_mrr['stdev'])}。"
            "负结果表明，Type 3 多证据问题仍是主要边界，浅层单候选重排和简单 query decomposition 不能有效提高覆盖率。"
            "本文还给出复现清单、审稿风险矩阵和人工复核流程，用于后续补齐外部 embedding baseline 与人工一致性证据。"
        ),
        "",
        "## 1 引言",
        "",
        "长对话智能体的记忆模块通常同时承担三个目标：保留长期个人事实，控制存储与检索成本，并在新任务中快速找到可用证据。直接保留原始对话虽然信息完整，但会带来上下文窗口、检索噪声和隐私控制问题；过度压缩的 session summary 又可能丢失细粒度事实。因此，一个可投稿的 agent memory 实验需要同时回答：记忆写入是否有效，检索/重排是否带来增益，多证据问题是否被解决，以及这些结论是否可复现。",
        "",
        "本文的核心观察是：将长对话写成结构化 fact-level memory 后，固定检索器已经能获得强基线；真正明显的性能增量来自候选级学习重排，而不是简单的时间或类型启发式。与此同时，Type 3 多证据问题对当前方法仍然困难，说明未来需要 listwise/setwise objective 或更强的 LLM 子问题分解。",
        "",
        "本文贡献如下：",
        "",
        "1. 构建一套覆盖 memory writing、retrieval、reranking、compression、efficiency diagnostics 和 error audit 的 agent memory 实验框架。",
        "2. 在 LoCoMo10 answerable slice 上验证 DeepSeek fact-level memory 相比 observation memory 具有更好的检索表现和更低 token 存储成本。",
        "3. 提出并验证 candidate-level learned reranking，并通过 feature-group ablation 发现更简洁的 intrinsic feature reranker；held-out、bootstrap CI 和 LOCO split 均支持该类方法优于 type-aware reranking。",
        "4. 系统报告 Type 3 multi-evidence retrieval 的负结果，明确当前方法边界。",
        "5. 提供论文级 artifact：复现清单、实验协议、审稿风险矩阵、LLM-assisted audit、盲审人工复核表和 priority20 人工确认包。",
        "",
        "## 2 任务定义",
        "",
        r"给定查询 \(q\) 和记忆库 \(M=\{m_i\}_{i=1}^{N}\)，每个查询对应一个或多个 gold memory \(G_q\subset M\)。系统目标是在 Top-K 返回集合中覆盖至少一个或尽可能多的 gold memory。本文主要使用 Recall@K、MRR 和多证据 Coverage@K：",
        "",
        r"\[Recall@K=\frac{1}{|Q|}\sum_{q\in Q}\mathbf{1}[\exists g\in G_q, rank_q(g)\le K]\]",
        "",
        r"\[MRR=\frac{1}{|Q|}\sum_{q\in Q}\frac{1}{\min_{g\in G_q}rank_q(g)}\]",
        "",
        r"\[Coverage@K=\frac{1}{|Q|}\sum_{q\in Q}\frac{|G_q\cap TopK(q)|}{|G_q|}\]",
        "",
        "## 3 方法",
        "",
        "### 3.1 Fact-Level Memory Writing",
        "",
        "本文使用 DeepSeek API 从 LoCoMo 长对话中抽取事实级记忆。每条记忆包含文本、记忆类型、日期、实体、重要性和 source evidence。形式化地，记忆可表示为：",
        "",
        r"\[m_i=(text_i,type_i,date_i,entities_i,importance_i,source_i)\]",
        "",
        "与 session summary 或 observation memory 相比，fact-level memory 的目标是将检索单元压缩到可直接回答问题的事实粒度，从而降低检索噪声和存储 token。",
        "",
        "### 3.2 固定检索与 Type-Aware Reranking",
        "",
        "基础检索包括 keyword、vector 和 hybrid。hybrid score 组合语义相似度、BM25 和实体匹配：",
        "",
        r"\[S_{hybrid}=0.65s_{sem}+0.30s_{bm25}+0.05s_{entity}\]",
        "",
        "time-aware 与 type-aware reranking 在 hybrid 的基础上进一步加入时间、人物、重要性和 query-intent 与 memory type 的匹配项：",
        "",
        r"\[S_{type}=0.70s_{sem}+0.30s_{bm25}+0.08g(q)d(q,m_i)+\gamma p(q,m_i)+\eta I(m_i)+\lambda T(q,m_i)\]",
        "",
        "其中 \(g(q)\) 是 recency gate，\(d(q,m_i)\) 是时间衰减，\(p(q,m_i)\) 是 persona match，\(I(m_i)\) 是重要性 proxy，\(T(q,m_i)\) 表示 query-intent 与 memory type 的匹配。",
        "",
        "### 3.3 Intrinsic Candidate-Level Learned Reranking",
        "",
        "候选级学习重排从 keyword、vector、hybrid、time-aware 和 type-aware 的 Top-K 并集中构造候选集，并为每个候选抽取语义、关键词、时间、人物、memory type、importance 和交互特征。完整版本也可使用各检索器的 method-level score/rank，但 feature-group ablation 显示，只使用候选自身 intrinsic features 的变体更稳定。模型学习候选是否为 gold memory 的相关性分数：",
        "",
        r"\[\hat{y}_{q,i}=f_{\theta}(s_{sem},s_{bm25},d(q,m_i),p(q,m_i),T(q,m_i),type_i,I_i,\phi(q,m_i))\]",
        "",
        "其中 \(\phi(q,m_i)\) 表示语义-关键词、persona-type、recency-decay 等交互项。最终按照 \(\hat{y}_{q,i}\) 对候选重新排序。该方法不重新生成记忆，而是在已有检索结果上学习更稳健的排序函数。",
        "",
        "## 4 实验设置",
        "",
        f"数据使用 LoCoMo10 answerable slice，包含 {memory_count} 条 fact memory 和 {query_count} 条可评估查询。主结果使用本地 BGE-M3 embedding cache。评估指标为 Recall@1/3/5、MRR，以及 Type 3 多证据问题的 Coverage@K。显著性检验采用 paired bootstrap 置信区间和 paired permutation test。",
        "",
        "候选级重排使用四类稳定性检查：held-out query split 用于基础泛化检查，20-seed split sweep 用于排除单一随机划分偶然性，train-fraction sensitivity 用于检查训练比例依赖，leave-one-conversation-out split 用于验证模型是否跨 conversation 泛化。intrinsic feature reranker 同时报告 held-out、multi-seed、train-fraction 和 LOCO 结果。所有可复现入口记录在 `outputs/agent_memory_reproducibility_checklist_zh.md`。",
        "",
        "## 5 结果",
        "",
        "### 5.1 主检索结果",
        "",
        markdown_table(["Method", "MRR", "Recall@5"], main_rows),
        "",
        f"fact memory + type-aware 的 MRR 为 {f(fact_type['mrr'])}，Recall@5 为 {f(fact_type['recall@5'])}，高于 observation memory + type-aware 的 MRR {f(obs_type['mrr'])} 和 Recall@5 {f(obs_type['recall@5'])}。这说明将长对话写成事实级记忆可以作为有效的 memory representation。",
        "",
        "### 5.2 Type-Aware Reranking 的作用",
        "",
        f"type-aware 相比 time-aware 的 MRR delta 为 {signed(type_mrr['mean_delta'])}，p={f(type_mrr['permutation_p_value'], 4)}；Recall@5 delta 为 {signed(type_r5['mean_delta'])}，p={f(type_r5['permutation_p_value'], 4)}。该增益幅度不大，但在 MRR 和 Recall@5 上具有统计支持，因此适合写作一个有用的固定打分组件。",
        "",
        "### 5.3 Intrinsic Candidate-Level Reranking 是主要收益来源",
        "",
        f"在 held-out split 下，full candidate reranker 将 MRR 从 {f(reranker_base['mrr_mean'])} 提升到 {f(reranker_row['mrr_mean'])}，MRR delta 为 {signed(reranker_mrr['mean_delta'])}，p={f(reranker_mrr['permutation_p_value'], 4)}；Recall@5 delta 为 {signed(reranker_r5['mean_delta'])}。进一步的 feature-group ablation 显示，intrinsic feature reranker 达到 MRR {f(intrinsic_row['mrr_mean'])}、Recall@5 {f(intrinsic_row['recall@5_mean'])}，相对 type-aware 的 MRR delta 为 {signed(intrinsic_vs_type_mrr['delta_mean'])}，95% CI=[{f(intrinsic_vs_type_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_type_mrr['delta_ci_high'], 4)}]；相对 full reranker 的 MRR delta 为 {signed(intrinsic_vs_full_mrr['delta_mean'])}，95% CI=[{f(intrinsic_vs_full_mrr['delta_ci_low'], 4)}, {f(intrinsic_vs_full_mrr['delta_ci_high'], 4)}]。oracle-gap 分析显示，intrinsic reranker 在 held-out MRR 上关闭 candidate-oracle gap 的 {f(heldout_oracle_mrr['closure_rate'], 3)}，Recall@5 closure 为 {f(heldout_oracle_r5['closure_rate'], 3)}；LOCO MRR closure 为 {f(loco_oracle_mrr['closure_rate'], 3)}，说明当前方法有效但仍未穷尽候选池上界。paired outcome 分析显示，MRR improved/worsened/tied 为 {intrinsic_effect_mrr['improved_pairs']}/{intrinsic_effect_mrr['worsened_pairs']}/{intrinsic_effect_mrr['tied_pairs']}，Cohen dz={f(intrinsic_effect_mrr['cohen_dz'], 4)}；Recall@5 improved/worsened/tied 为 {intrinsic_effect_r5['improved_pairs']}/{intrinsic_effect_r5['worsened_pairs']}/{intrinsic_effect_r5['tied_pairs']}，但 Type 3 Recall@5 delta 为 {signed(intrinsic_effect_type3_r5['mean_delta'])}，Type 3 set Coverage@5 oracle-gap closure 为 {signed(type3_oracle_cov5['closure_rate'])}，说明收益并不覆盖多证据问题。扩展 20-seed stability 检查显示，intrinsic reranker 在 {intrinsic_seed['mrr_positive_seeds']}/{intrinsic_seed['seeds']} 个随机划分上 MRR 均高于 type-aware，平均 ΔMRR={signed(intrinsic_seed['mrr_delta_mean'])}，最小 ΔMRR={signed(intrinsic_seed['mrr_delta_min'])}。训练比例敏感性实验进一步显示，在 train fraction 0.5/0.6/0.7/0.8 下，intrinsic reranker 的最低 MRR win rate={f(intrinsic_fraction_min_win_rate, 2)}，最小 seed-level ΔMRR={signed(intrinsic_fraction_min_delta)}，平均 fraction-level ΔMRR={signed(intrinsic_fraction_mean_delta)}。在 LOCO split 下，intrinsic feature reranker 的 MRR 为 {f(intrinsic_loco_row['mrr_mean'])}、Recall@5 为 {f(intrinsic_loco_row['recall@5_mean'])}，相对 type-aware 的 MRR delta 为 {signed(intrinsic_loco_mrr['delta_mean'])}，95% CI=[{f(intrinsic_loco_mrr['delta_ci_low'], 4)}, {f(intrinsic_loco_mrr['delta_ci_high'], 4)}]，Recall@5 delta 为 {signed(intrinsic_loco_r5['delta_mean'])}，95% CI=[{f(intrinsic_loco_r5['delta_ci_low'], 4)}, {f(intrinsic_loco_r5['delta_ci_high'], 4)}]。这支持将 intrinsic candidate-level learned reranking 作为本文最主要的方法贡献，同时把 method-level rank/score 特征视为可能带来噪声的消融发现。",
        "",
        "### 5.4 存储效率与 Writer 稳定性",
        "",
        f"fact memory 使用 {fact_storage['memory_tokens']} 个 memory tokens，而 observation memory 使用 {obs_storage['memory_tokens']} 个 tokens，fact/observation token ratio 为 {f(storage_ratio)}。DeepSeek writer 三次运行的 MRR mean={f(writer_mrr['mean'])}, stdev={f(writer_mrr['stdev'])}；Recall@5 mean={f(writer_r5['mean'])}, stdev={f(writer_r5['stdev'])}。这些结果说明当前 LoCoMo10 范围内 writer 输出对主指标影响较小，但仍需要在更大切片或第二数据集上复验。",
        "",
        "### 5.5 Type 3 多证据负结果",
        "",
        f"Type 3 supervised set selector 的 Coverage@5 delta 为 {signed(type3_cov['mean_delta'])}，p={f(type3_cov['permutation_p_value'], 4)}，说明浅层 set selector 不但没有解决多证据检索，反而降低了覆盖率。本文因此将 Type 3 写作方法边界，而不是已解决问题。",
        "",
        "## 6 错误分析与可靠性",
        "",
        f"当前已有 80 条 LLM-assisted audit 初稿，并生成 priority20 快速人工确认包和盲审人工复核表。priority20 包包含 {priority_samples} 条样本，当前人工确认 {priority_confirmed} 条。该流程适合先在不暴露 LLM 预标注的条件下完成 quick-review，再回填 confirmation 表并报告 exact agreement 与 Cohen's kappa；完整投稿前仍应扩展到 80 条。",
        "",
        "## 7 Threats to Validity 与限制",
        "",
        (
            f"本文当前有效性威胁附录覆盖 {len(threats)} 项风险，类别包括 {', '.join(threat_categories)}；"
            f"其中仍有 {len(threat_blockers)} 项会阻止最终投稿。"
            f"第一，外部 embedding baseline completed={embedding_completed}，因此目前不能把外部 API embedding 对照写入主结果。"
            "第二，Human/LLM 人工确认尚未完成，不能宣称 human-verified error analysis。"
            "第三，主结果仍限定在 LoCoMo10 answerable slice；LOCO split 支持跨 conversation 泛化，但不等同于跨数据集泛化。"
            "第四，MRR/Recall@K 只衡量 memory retrieval，不等价于端到端 agent task success。"
            "第五，100k 扩展性实验包含 synthetic distractor，只能作为效率诊断，不能直接代表真实生产规模。"
            "完整有效性威胁、缓解措施和论文声明边界见 `outputs/agent_memory_threats_to_validity_zh.md`。"
        ),
        "",
        "## 8 结论",
        "",
        "本文给出一套面向长对话智能体记忆的可复现实验框架。结果显示，LLM-written fact memory 是紧凑且有效的记忆表示，intrinsic candidate-level learned reranking 是当前最强的排序改进，而 Type 3 多证据检索仍是关键未解问题。后续最小补强是完成一个外部 embedding baseline，并通过盲审表填写 priority20/80 Human/LLM confirmation 以形成可靠性证据。",
        "",
        "## Appendix A 复现状态",
        "",
        f"- Artifact gate：{artifact_pass}/{len(repro_artifacts)}",
        f"- Metric gate：{metric_pass}/{len(repro_metrics)}",
        "- 关键文档：`outputs/agent_memory_experiment_protocol_zh.md`、`outputs/agent_memory_submission_gap_analysis_zh.md`、`outputs/agent_memory_reproducibility_checklist_zh.md`、`outputs/agent_memory_manuscript_claim_check_zh.md`、`outputs/agent_memory_threats_to_validity_zh.md`、`outputs/agent_memory_human_audit_readiness_gate_zh.md`。",
        "",
        "## Appendix B 投稿前 TODO",
        "",
        "- 运行外部 embedding baseline，生成 `agent_memory_embedding_baseline_comparison_zh.md` 的 completed 版本。",
        "- 填写 `agent_memory_human_audit_priority20_blind_review.csv` 的 human_* 字段，回填 confirmation 后生成 quick-review agreement。",
        "- 若目标为更高等级会议/期刊，继续扩展 LoCoMo slice 或加入第二数据集。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Chinese manuscript draft.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    write_report(args.output_report, args.project_root)
    print(json.dumps({"output_report": str(args.output_report)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
