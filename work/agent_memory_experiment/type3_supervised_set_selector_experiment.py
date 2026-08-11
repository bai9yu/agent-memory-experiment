#!/usr/bin/env python3
"""Evaluate a supervised greedy set selector for Type-3 multi-evidence queries."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from candidate_reranker_experiment import (
    aggregate,
    feature_dict,
    load_baseline,
    load_candidates,
    score_ranked_query,
    summarize_across_splits,
    train_predict,
)
from query_type_router_experiment import metric, write_csv


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "he", "her", "his", "in", "is", "it", "of", "on", "or", "she",
    "that", "the", "their", "to", "was", "were", "what", "when", "where",
    "which", "who", "why", "with", "would",
}


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def text_tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in STOPWORDS and len(token) > 2}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def enrich_tokens(candidates: dict[str, dict[str, dict[str, Any]]]) -> None:
    for query_candidates in candidates.values():
        for row in query_candidates.values():
            row["tokens"] = text_tokens(row.get("memory_text", ""))


def load_type_aware_ranked(rankings_path: Path, max_k: int) -> dict[str, list[str]]:
    ranked: dict[str, list[str]] = defaultdict(list)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if len(ranked[row["query_id"]]) < max_k:
                ranked[row["query_id"]].append(row["memory_id"])
    return ranked


def coverage_for_ranked(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    ranked_ids = [row["memory_id"] for row in rows]
    out = {}
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def context_features(row: dict[str, Any], selected: list[dict[str, Any]], methods: list[str]) -> dict[str, float]:
    features = feature_dict(row, methods)
    features["selected_count"] = float(len(selected))
    if not selected:
        features["selected_max_jaccard"] = 0.0
        features["selected_mean_jaccard"] = 0.0
        features["selected_same_type"] = 0.0
        features["selected_type_coverage"] = 0.0
        return features
    sims = [jaccard(row["tokens"], chosen["tokens"]) for chosen in selected]
    selected_types = {chosen["memory_type"] for chosen in selected}
    features["selected_max_jaccard"] = max(sims)
    features["selected_mean_jaccard"] = statistics.mean(sims)
    features["selected_same_type"] = 1.0 if row["memory_type"] in selected_types else 0.0
    features["selected_type_coverage"] = float(len(selected_types))
    return features


def rank_by_global_model(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    methods: list[str],
) -> None:
    scores, _ = train_predict(train_rows, test_rows, methods)
    for row, score in zip(test_rows, scores):
        row["global_learned_score"] = score


def rank_by_type3_model(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    methods: list[str],
) -> None:
    scores, _ = train_predict(train_rows, test_rows, methods)
    for row, score in zip(test_rows, scores):
        row["type3_learned_score"] = score


def build_set_training_examples(
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    methods: list[str],
    max_steps: int,
    max_rows_per_step: int,
) -> tuple[list[dict[str, float]], list[int]]:
    x_rows: list[dict[str, float]] = []
    y_rows: list[int] = []
    for query_id in query_ids:
        remaining = sorted(candidates[query_id].values(), key=lambda row: row.get("type3_learned_score", 0.0), reverse=True)
        selected: list[dict[str, Any]] = []
        for _ in range(min(max_steps, len(remaining))):
            sampled = remaining[:max_rows_per_step]
            for row in sampled:
                x_rows.append(context_features(row, selected, methods))
                y_rows.append(1 if row["is_relevant"] else 0)
            relevant = [row for row in remaining if row["is_relevant"]]
            if relevant:
                chosen = max(relevant, key=lambda row: row.get("type3_learned_score", 0.0))
            else:
                chosen = remaining[0]
            selected.append(chosen)
            remaining = [row for row in remaining if row["memory_id"] != chosen["memory_id"]]
            if not relevant:
                break
    return x_rows, y_rows


def train_set_selector(x_rows: list[dict[str, float]], y_rows: list[int]):
    from sklearn.feature_extraction import DictVectorizer
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import make_pipeline

    if len(set(y_rows)) < 2:
        return None
    model = make_pipeline(
        DictVectorizer(sparse=False),
        RandomForestClassifier(
            n_estimators=80,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            random_state=0,
            n_jobs=1,
        ),
    )
    model.fit(x_rows, y_rows)
    return model


def greedy_select(
    rows: list[dict[str, Any]],
    model: Any,
    methods: list[str],
    output_k: int,
    base_score_key: str,
    redundancy_weight: float,
) -> list[dict[str, Any]]:
    remaining = list(rows)
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < output_k:
        feature_rows = [context_features(row, selected, methods) for row in remaining]
        if model is None:
            gains = [float(row.get(base_score_key, 0.0)) for row in remaining]
        else:
            gains = [float(value) for value in model.predict_proba(feature_rows)[:, 1]]
        scored = [
            (gain - redundancy_weight * features["selected_max_jaccard"], row)
            for gain, features, row in zip(gains, feature_rows, remaining)
        ]
        best_score, chosen = max(scored, key=lambda item: item[0])
        chosen = {**chosen, "set_selector_score": best_score}
        selected.append(chosen)
        remaining = [row for row in remaining if row["memory_id"] != chosen["memory_id"]]
    selected_ids = {row["memory_id"] for row in selected}
    selected.extend([row for row in rows if row["memory_id"] not in selected_ids])
    return selected


def evaluate_method(
    seed: int,
    query_ids: list[str],
    method: str,
    ranked_by_query: dict[str, list[dict[str, Any]]],
    queries: dict[str, dict[str, Any]],
    ks: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metric_rows = []
    coverage_rows = []
    for query_id in query_ids:
        ranked = ranked_by_query[query_id]
        scored = score_ranked_query(ranked)
        gold_ids = set(queries[query_id].get("answer_memory_ids", []))
        metric_rows.append({
            "split_seed": seed,
            "query_id": query_id,
            "query_type": "3",
            "method": method,
            **scored,
        })
        coverage_rows.append({
            "split_seed": seed,
            "query_id": query_id,
            "query_type": "3",
            "method": method,
            "num_gold": len(gold_ids),
            "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            **coverage_for_ranked(ranked, gold_ids, ks),
        })
    return metric_rows, coverage_rows


def aggregate_coverage(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    summary = []
    for method, bucket in sorted(buckets.items()):
        out = {
            "method": method,
            "num_rows": len(bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
        }
        for k in ks:
            for metric_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[metric_name] = statistics.mean(row[metric_name] for row in bucket)
        summary.append(out)
    return summary


def evaluate_split(
    seed: int,
    query_ids: list[str],
    candidates: dict[str, dict[str, dict[str, Any]]],
    queries: dict[str, dict[str, Any]],
    type_aware_ranked_ids: dict[str, list[str]],
    methods: list[str],
    train_fraction: float,
    ks: list[int],
    max_rows_per_step: int,
    redundancy_weight: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    shuffled = list(query_ids)
    rng.shuffle(shuffled)
    train_size = int(len(shuffled) * train_fraction)
    train_ids = sorted(shuffled[:train_size])
    test_ids = sorted(shuffled[train_size:])
    type3_train_ids = [query_id for query_id in train_ids if queries[query_id].get("type") == "3"]
    type3_test_ids = [query_id for query_id in test_ids if queries[query_id].get("type") == "3"]

    global_train_rows = [row for query_id in train_ids for row in candidates[query_id].values()]
    type3_train_rows = [row for query_id in type3_train_ids for row in candidates[query_id].values()]
    type3_test_rows = [row for query_id in type3_test_ids for row in candidates[query_id].values()]
    rank_by_global_model(global_train_rows, type3_test_rows, methods)
    rank_by_type3_model(type3_train_rows, type3_train_rows + type3_test_rows, methods)

    x_set, y_set = build_set_training_examples(type3_train_ids, candidates, methods, max(ks), max_rows_per_step)
    set_model = train_set_selector(x_set, y_set)

    ranked_by_method: dict[str, dict[str, list[dict[str, Any]]]] = {
        "type_aware": {},
        "global_candidate_reranker": {},
        "type3_specific_reranker": {},
        "supervised_set_selector": {},
        "candidate_oracle": {},
    }
    ranked_output_rows = []
    for query_id in type3_test_ids:
        query_candidates = candidates[query_id]
        type_aware_rows = [
            query_candidates[memory_id]
            for memory_id in type_aware_ranked_ids.get(query_id, [])
            if memory_id in query_candidates
        ]
        global_rows = sorted(query_candidates.values(), key=lambda row: row.get("global_learned_score", 0.0), reverse=True)
        type3_rows = sorted(query_candidates.values(), key=lambda row: row.get("type3_learned_score", 0.0), reverse=True)
        set_rows = greedy_select(
            type3_rows,
            set_model,
            methods,
            max(ks),
            "type3_learned_score",
            redundancy_weight,
        )
        oracle_rows = sorted(query_candidates.values(), key=lambda row: row["is_relevant"], reverse=True)
        ranked_by_method["type_aware"][query_id] = type_aware_rows
        ranked_by_method["global_candidate_reranker"][query_id] = global_rows
        ranked_by_method["type3_specific_reranker"][query_id] = type3_rows
        ranked_by_method["supervised_set_selector"][query_id] = set_rows
        ranked_by_method["candidate_oracle"][query_id] = oracle_rows
        for method, rows in (
            ("type3_specific_reranker", type3_rows),
            ("supervised_set_selector", set_rows),
        ):
            for rank, row in enumerate(rows[:max(ks)], start=1):
                ranked_output_rows.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "query_type": "3",
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "score": row.get("set_selector_score", row.get("type3_learned_score", 0.0)),
                    "is_relevant": row["is_relevant"],
                    "memory_text": row["memory_text"],
                })

    metric_rows = []
    coverage_rows = []
    split_rows = []
    for method, ranked in ranked_by_method.items():
        method_metrics, method_coverage = evaluate_method(seed, type3_test_ids, method, ranked, queries, ks)
        metric_rows.extend(method_metrics)
        coverage_rows.extend(method_coverage)
        split_rows.append(aggregate(method_metrics, method, seed))

    comparison_rows = []
    for row in metric_rows:
        comparison_rows.append({
            "query_id": f"{seed}:{row['query_id']}",
            "original_query_id": row["query_id"],
            "split_seed": seed,
            "query_type": "3",
            "method": row["method"],
            "mrr": row["mrr"],
            "recall@1": row["recall@1"],
            "recall@3": row["recall@3"],
            "recall@5": row["recall@5"],
            "first_rank": row["first_rank"],
        })
    return split_rows, metric_rows, comparison_rows, coverage_rows, ranked_output_rows


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    coverage_rows: list[dict[str, Any]],
    ks: list[int],
    redundancy_weight: float,
) -> None:
    by_method = {row["method"]: row for row in summary_rows}
    coverage_by_method = {row["method"]: row for row in coverage_rows}
    primary_k = 5 if 5 in ks else max(ks)
    lines = [
        "# Type 3 监督式集合选择实验",
        "",
        "本实验针对 LoCoMo Type 3 多证据问题，训练一个 greedy set-level selector。模型在每一步选择候选时，不只看单条 memory 的相关性，还加入已选集合带来的文本冗余、memory type 覆盖等上下文特征。",
        "",
        f"当前 redundancy weight 为 `{redundancy_weight}`。训练和测试仍使用 query-level held-out split，避免同一 query 的候选泄漏。",
        "",
        "## Type 3 Held-Out 排序指标",
        "",
        "| 方法 | 划分数 | 平均 Query 数 | MRR | R@1 | R@3 | R@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("type_aware", "global_candidate_reranker", "type3_specific_reranker", "supervised_set_selector", "candidate_oracle"):
        row = by_method.get(method)
        if not row:
            continue
        lines.append(
            f"| {method} | {row['splits']} | {row['mean_queries']:.1f} | {metric(row['mrr_mean'])} | "
            f"{metric(row['recall@1_mean'])} | {metric(row['recall@3_mean'])} | {metric(row['recall@5_mean'])} |"
        )
    lines.extend([
        "",
        f"## Type 3 多证据覆盖 @{primary_k}",
        "",
        "| 方法 | Rows | Mean Gold | Multi-Evidence Share | Any | Full | Coverage Ratio |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for method in ("type_aware", "global_candidate_reranker", "type3_specific_reranker", "supervised_set_selector", "candidate_oracle"):
        row = coverage_by_method.get(method)
        if not row:
            continue
        lines.append(
            f"| {method} | {row['num_rows']} | {row['mean_gold']:.2f} | {row['multi_evidence_share']:.3f} | "
            f"{metric(row[f'any_hit@{primary_k}'])} | {metric(row[f'full_coverage@{primary_k}'])} | "
            f"{metric(row[f'coverage_ratio@{primary_k}'])} |"
        )
    if "supervised_set_selector" in by_method and "type_aware" in by_method:
        cand = by_method["supervised_set_selector"]
        base = by_method["type_aware"]
        cand_cov = coverage_by_method["supervised_set_selector"]
        base_cov = coverage_by_method["type_aware"]
        lines.extend([
            "",
            "## 相比 Type-Aware 的变化",
            "",
            f"- MRR delta：`{cand['mrr_mean'] - base['mrr_mean']:.4f}`",
            f"- Recall@5 delta：`{cand['recall@5_mean'] - base['recall@5_mean']:.4f}`",
            f"- Coverage@{primary_k} delta：`{cand_cov[f'coverage_ratio@{primary_k}'] - base_cov[f'coverage_ratio@{primary_k}']:.4f}`",
            f"- Full@{primary_k} delta：`{cand_cov[f'full_coverage@{primary_k}'] - base_cov[f'full_coverage@{primary_k}']:.4f}`",
        ])
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果该方法提升 Coverage@5 但降低 MRR，说明集合覆盖目标有效，但会牺牲第一个证据的排序。",
        "- 如果仍未超过 `type_aware`，说明仅用候选上下文特征还不足，需要显式 query decomposition 或更强的 listwise/setwise 学习目标。",
        "- Candidate oracle 是候选池上限，用于判断剩余空间是否来自候选召回还是集合选择。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3 supervised set selector experiment.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--methods", default="keyword,vector,hybrid,time_aware,type_aware")
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--ks", default="1,3,5,10,20")
    parser.add_argument("--max-rows-per-step", type=int, default=40)
    parser.add_argument("--redundancy-weight", type=float, default=0.0)
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-comparison", type=Path, required=True)
    parser.add_argument("--output-coverage", type=Path, required=True)
    parser.add_argument("--output-coverage-summary", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    enrich_tokens(candidates)
    queries = read_jsonl(args.queries)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    query_ids = sorted(query_id for query_id in candidates if query_id in baseline_rows and query_id in queries)
    type_aware_ranked_ids = load_type_aware_ranked(args.rankings, max(ks))

    split_rows = []
    per_query_rows = []
    comparison_rows = []
    coverage_rows = []
    ranked_rows = []
    for seed in seeds:
        split_summary, split_per_query, split_comparison, split_coverage, split_ranked = evaluate_split(
            seed,
            query_ids,
            candidates,
            queries,
            type_aware_ranked_ids,
            methods,
            args.train_fraction,
            ks,
            args.max_rows_per_step,
            args.redundancy_weight,
        )
        split_rows.extend(split_summary)
        per_query_rows.extend(split_per_query)
        comparison_rows.extend(split_comparison)
        coverage_rows.extend(split_coverage)
        ranked_rows.extend(split_ranked)

    summary_rows = summarize_across_splits(split_rows)
    coverage_summary_rows = aggregate_coverage(coverage_rows, ks)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_per_query, per_query_rows)
    write_csv(args.output_comparison, comparison_rows)
    write_csv(args.output_coverage, coverage_rows)
    write_csv(args.output_coverage_summary, coverage_summary_rows)
    write_csv(args.output_ranked, ranked_rows)
    write_report(args.output_report, summary_rows, coverage_summary_rows, ks, args.redundancy_weight)
    print(json.dumps({
        "per_query_rows": len(per_query_rows),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
