#!/usr/bin/env python3
"""Generate a paper appendix for the intrinsic candidate reranker."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


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


def feature_rows() -> list[dict[str, str]]:
    return [
        {
            "group": "semantic_keyword",
            "features": "semantic_score, keyword_score, entity_score, semantic_x_keyword",
            "included_intrinsic": "yes",
            "notes": "候选自身与 query 的语义、关键词和实体匹配信号。",
        },
        {
            "group": "temporal",
            "features": "time_decay, recency_gate, recency_x_decay",
            "included_intrinsic": "yes",
            "notes": "记忆时间与 query 时间需求之间的时效性特征。",
        },
        {
            "group": "persona_type",
            "features": "persona_score, persona_weight, memory_type_score, persona_x_type",
            "included_intrinsic": "yes",
            "notes": "人物匹配、query intent 与 memory type 的匹配及其交互。",
        },
        {
            "group": "categorical",
            "features": "query_type one-hot, memory_type one-hot",
            "included_intrinsic": "yes",
            "notes": "显式类型特征，帮助模型学习不同 query 和 memory type 的排序偏好。",
        },
        {
            "group": "importance",
            "features": "importance_score",
            "included_intrinsic": "yes",
            "notes": "记忆重要性 proxy；作为弱先验而不是主排序依据。",
        },
        {
            "group": "method_level",
            "features": "retriever_score, retriever_rank, retriever_present, reciprocal_rank",
            "included_intrinsic": "no",
            "notes": "仅用于 full reranker ablation；intrinsic-only 主方法排除此组，以降低对固定检索器排名的依赖。",
        },
    ]


def write_report(report_path: Path, feature_csv_path: Path, root: Path) -> None:
    outputs = root / "outputs"
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    feature_ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    intrinsic_loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    bootstrap = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")

    type_aware = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    full_reranker = lookup(reranker, method="candidate_reranker")
    intrinsic_heldout = lookup(feature_ablation, method="ablation_intrinsic_only")
    intrinsic_loco_row = lookup(intrinsic_loco, method="intrinsic_reranker_loco")
    candidate_oracle = lookup(feature_ablation, method="candidate_oracle")

    heldout_vs_type = lookup(
        bootstrap,
        scenario="candidate_reranker_intrinsic_ablation_vs_type_aware",
        metric="mrr",
    )
    heldout_vs_full = lookup(
        bootstrap,
        scenario="candidate_reranker_intrinsic_ablation_vs_full",
        metric="mrr",
    )
    loco_vs_type_mrr = lookup(bootstrap, scenario="candidate_reranker_intrinsic_loco", metric="mrr")
    loco_vs_type_r5 = lookup(bootstrap, scenario="candidate_reranker_intrinsic_loco", metric="recall@5")

    rows = feature_rows()
    write_csv(feature_csv_path, rows)

    feature_table = [
        [row["group"], row["features"], row["included_intrinsic"], row["notes"]]
        for row in rows
    ]
    result_table = [
        ["fixed type-aware", f(type_aware["mrr"]), f(type_aware["recall@5"]), "固定公式主基线"],
        ["full candidate reranker", f(full_reranker["mrr_mean"]), f(full_reranker["recall@5_mean"]), "含 method-level 特征的学习重排"],
        ["intrinsic feature reranker", f(intrinsic_heldout["mrr_mean"]), f(intrinsic_heldout["recall@5_mean"]), "held-out query split 主方法候选"],
        ["intrinsic feature reranker LOCO", f(intrinsic_loco_row["mrr_mean"]), f(intrinsic_loco_row["recall@5_mean"]), "leave-one-conversation-out 泛化检查"],
        ["candidate oracle", f(candidate_oracle["mrr_mean"]), f(candidate_oracle["recall@5_mean"]), "候选池上界，仅作诊断"],
    ]
    ci_table = [
        [
            "intrinsic vs type-aware held-out",
            "MRR",
            signed(heldout_vs_type["delta_mean"]),
            f(heldout_vs_type["delta_ci_low"], 4),
            f(heldout_vs_type["delta_ci_high"], 4),
            heldout_vs_type["delta_ci_excludes_zero"],
        ],
        [
            "intrinsic vs full held-out",
            "MRR",
            signed(heldout_vs_full["delta_mean"]),
            f(heldout_vs_full["delta_ci_low"], 4),
            f(heldout_vs_full["delta_ci_high"], 4),
            heldout_vs_full["delta_ci_excludes_zero"],
        ],
        [
            "intrinsic LOCO vs type-aware",
            "MRR",
            signed(loco_vs_type_mrr["delta_mean"]),
            f(loco_vs_type_mrr["delta_ci_low"], 4),
            f(loco_vs_type_mrr["delta_ci_high"], 4),
            loco_vs_type_mrr["delta_ci_excludes_zero"],
        ],
        [
            "intrinsic LOCO vs type-aware",
            "Recall@5",
            signed(loco_vs_type_r5["delta_mean"]),
            f(loco_vs_type_r5["delta_ci_low"], 4),
            f(loco_vs_type_r5["delta_ci_high"], 4),
            loco_vs_type_r5["delta_ci_excludes_zero"],
        ],
    ]

    lines = [
        "# Intrinsic Feature Reranker 方法附录",
        "",
        "本附录把当前论文主方法候选 `intrinsic feature reranker` 的输入、特征边界、训练协议、验证方式和复现命令集中写清楚，避免只报告结果而缺少可复查的方法细节。",
        "",
        "## 1. 问题设置",
        "",
        r"对每个 query \(q\)，先从 `keyword`、`vector`、`hybrid`、`time-aware`、`type-aware` 的 Top-K 结果取并集，得到候选池 \(C_q\subset M\)。学习式重排器对每个候选 \(m_i\in C_q\) 预测相关性分数 \(\hat{y}_{q,i}\)，并按该分数重新排序。",
        "",
        r"\[\hat{y}_{q,i}=f_{\theta}(x(q,m_i))\]",
        "",
        r"\[rank(q)=argsort_{m_i\in C_q}(-\hat{y}_{q,i})\]",
        "",
        "训练标签来自 LoCoMo10 answerable slice 中已有的 gold memory id：若候选属于 query 的 gold memory set，则标记为 1，否则为 0。模型不调用大模型生成答案，也不改写记忆，只学习候选级排序。",
        "",
        "## 2. 特征边界",
        "",
        "intrinsic-only 版本只使用候选自身和 query-memory 关系特征；不使用“某个固定检索器把该候选排第几名/打多少分”这类 method-level 特征。这样做的原因是 feature-group ablation 显示 method-level rank/score 可能带来噪声，而 intrinsic 特征更简洁、泛化边界也更清楚。",
        "",
        markdown_table(["Feature Group", "Features", "Used", "Notes"], feature_table),
        "",
        "## 3. 模型与训练协议",
        "",
        "- 模型：`RandomForestClassifier`。",
        "- 超参数：`n_estimators=120`、`min_samples_leaf=4`、`class_weight=balanced_subsample`、`random_state=0`、`n_jobs=1`。",
        "- 特征编码：`DictVectorizer(sparse=False)`，连续特征和 one-hot 类型特征共同输入。",
        "- held-out query split：seeds=`13,17,23,29,31`，`train_fraction=0.7`，按 query 划分训练/测试。",
        "- LOCO split：10 个 LoCoMo conversation 轮流作为测试集，其余 conversation 作为训练集。",
        "- 评价指标：MRR、Recall@1/3/5；核心对比使用 query-level paired bootstrap 置信区间。",
        "",
        "## 4. 当前结果",
        "",
        markdown_table(["Method", "MRR", "Recall@5", "Role"], result_table),
        "",
        markdown_table(["Comparison", "Metric", "Delta", "CI Low", "CI High", "CI Excludes 0"], ci_table),
        "",
        "结果说明：intrinsic feature reranker 在 held-out query split 上高于 fixed type-aware，也略高于 full candidate reranker；在更严格的 LOCO split 中仍高于 fixed type-aware。因此当前可以把它作为论文主方法候选，而把 full reranker 写作消融对照。",
        "",
        "## 5. 可复现命令",
        "",
        "```bash",
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/candidate_reranker_feature_ablation.py \\",
        "  --rankings work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/rankings.csv \\",
        "  --per-query work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/per_query_metrics.csv \\",
        "  --output-split-summary outputs/agent_memory_candidate_reranker_feature_ablation_split_summary.csv \\",
        "  --output-summary outputs/agent_memory_candidate_reranker_feature_ablation_summary.csv \\",
        "  --output-deltas outputs/agent_memory_candidate_reranker_feature_ablation_deltas.csv \\",
        "  --output-comparison outputs/agent_memory_candidate_reranker_feature_ablation_comparison_per_query.csv \\",
        "  --output-report outputs/agent_memory_candidate_reranker_feature_ablation_zh.md",
        "```",
        "",
        "```bash",
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/candidate_reranker_intrinsic_loco_experiment.py \\",
        "  --rankings work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/rankings.csv \\",
        "  --per-query work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/per_query_metrics.csv \\",
        "  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \\",
        "  --locomo work/agent_memory_experiment/data/locomo10.json \\",
        "  --output-split-summary outputs/agent_memory_candidate_reranker_intrinsic_loco_split_summary.csv \\",
        "  --output-summary outputs/agent_memory_candidate_reranker_intrinsic_loco_summary.csv \\",
        "  --output-deltas outputs/agent_memory_candidate_reranker_intrinsic_loco_deltas.csv \\",
        "  --output-selected outputs/agent_memory_candidate_reranker_intrinsic_loco_selected.csv \\",
        "  --output-comparison outputs/agent_memory_candidate_reranker_intrinsic_loco_comparison_per_query.csv \\",
        "  --output-ranked outputs/agent_memory_candidate_reranker_intrinsic_loco_ranked_top20.csv \\",
        "  --output-report outputs/agent_memory_candidate_reranker_intrinsic_loco_zh.md",
        "```",
        "",
        "```bash",
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/bootstrap_metric_ci.py \\",
        "  --output-csv outputs/agent_memory_bootstrap_metric_ci.csv \\",
        "  --output-report outputs/agent_memory_bootstrap_metric_ci_zh.md",
        "```",
        "",
        "## 6. 论文表述边界",
        "",
        "- 可以写：在 LoCoMo10 answerable slice 上，intrinsic feature reranker 在 held-out query split 和 LOCO split 中均稳定优于 fixed type-aware。",
        "- 可以写：method-level rank/score 特征不是当前主要收益来源；intrinsic-only 版本更适合作为简洁主方法。",
        "- 暂不能写：跨数据集泛化、真实外部 embedding API 对比已经完成、人工错误分析已经 human-verified。",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate intrinsic reranker method appendix.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-features", type=Path, required=True)
    args = parser.parse_args()

    write_report(args.output_report, args.output_features, args.project_root)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_features": str(args.output_features),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
