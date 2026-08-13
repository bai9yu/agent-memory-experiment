#!/usr/bin/env python3
"""Train a dependency-free Type-3 selector over expanded candidate pools."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from memory_eval import (
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    hashed_vector,
    load_memories,
    load_queries,
)
from query_type_router_experiment import metric, write_csv
from type3_expanded_pool_selector import (
    append_expansion_after_candidate,
    build_pool,
    facet_rankings,
    known_personas,
    load_candidate_rows,
    metrics,
    score_all_memories,
)


NUMERIC_FEATURES = (
    "candidate_norm",
    "candidate_rrf",
    "bm25_norm",
    "semantic_norm",
    "entity_overlap",
    "memory_type_score",
    "persona_score",
    "importance_score",
    "recency_score",
    "facet_rrf",
    "facet_hits",
    "source_candidate",
    "source_offline",
    "source_facet",
)


def feature_dict(row: dict[str, Any]) -> dict[str, float]:
    features = {name: float(row.get(name, 0.0) or 0.0) for name in NUMERIC_FEATURES}
    features["candidate_rank_inv"] = 1.0 / max(float(row.get("candidate_rank", 999) or 999), 1.0)
    features[f"memory_type={row.get('memory_type', '')}"] = 1.0
    return features


def learn_weights(rows: list[dict[str, Any]], l2: float) -> dict[str, float]:
    positives = [feature_dict(row) for row in rows if row["is_relevant"]]
    negatives = [feature_dict(row) for row in rows if not row["is_relevant"]]
    feature_names = sorted({name for row in positives + negatives for name in row})
    weights = {}
    for name in feature_names:
        pos_values = [row.get(name, 0.0) for row in positives]
        neg_values = [row.get(name, 0.0) for row in negatives]
        pos_mean = statistics.mean(pos_values) if pos_values else 0.0
        neg_mean = statistics.mean(neg_values) if neg_values else 0.0
        spread_values = pos_values + neg_values
        spread = statistics.pstdev(spread_values) if len(spread_values) > 1 else 0.0
        weights[name] = (pos_mean - neg_mean) / (spread + l2)
    return weights


def learned_score(row: dict[str, Any], weights: dict[str, float], mix: float) -> float:
    features = feature_dict(row)
    raw = sum(weights.get(name, 0.0) * value for name, value in features.items())
    model_score = 1.0 / (1.0 + math.exp(-max(min(raw, 20.0), -20.0)))
    candidate_prior = float(row.get("candidate_norm", 0.0) or 0.0)
    return mix * model_score + (1.0 - mix) * candidate_prior


def redundancy(left: dict[str, Any], right: dict[str, Any]) -> float:
    left_tokens = set(str(left.get("memory_text", "")).lower().split())
    right_tokens = set(str(right.get("memory_text", "")).lower().split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def select_rows(
    pool: list[dict[str, Any]],
    weights: dict[str, float],
    mix: float,
    redundancy_weight: float,
    keep_top1: bool,
    select_k: int,
) -> list[dict[str, Any]]:
    remaining = [dict(row) for row in pool]
    selected = []
    if keep_top1:
        top1 = [row for row in remaining if row.get("candidate_rank") == 1]
        if top1:
            top = dict(top1[0])
            top["learned_selector_score"] = learned_score(top, weights, mix)
            selected.append(top)
            remaining = [row for row in remaining if row["memory_id"] != top["memory_id"]]
    while remaining and len(selected) < select_k:
        best = None
        best_score = float("-inf")
        for row in remaining:
            score = learned_score(row, weights, mix)
            score -= redundancy_weight * max((redundancy(row, chosen) for chosen in selected), default=0.0)
            if score > best_score:
                best = row
                best_score = score
        chosen = dict(best)
        chosen["learned_selector_score"] = best_score
        selected.append(chosen)
        remaining = [row for row in remaining if row["memory_id"] != chosen["memory_id"]]
    selected_ids = {row["memory_id"] for row in selected}
    tail = [
        dict(row, learned_selector_score=learned_score(row, weights, mix))
        for row in remaining
        if row["memory_id"] not in selected_ids
    ]
    tail.sort(key=lambda row: row["learned_selector_score"], reverse=True)
    return selected + tail


def prepare_pools(args: argparse.Namespace) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], dict[str, Any]]:
    memories = load_memories(args.memories)
    queries = {query.id: query for query in load_queries(args.queries)}
    memory_by_id = {memory.id: memory for memory in memories}
    memory_tokens = build_memory_tokens(memories)
    memory_vectors = {memory.id: hashed_vector(memory_tokens[memory.id]) for memory in memories}
    idf = build_idf(memories)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    personas = known_personas(memories)
    importance_scores = build_importance_scores(memories)
    groups = load_candidate_rows(args.candidate_ranked)
    cache: dict[str, tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]] = {}
    pools: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for (seed, query_id), candidate_rows in sorted(groups.items()):
        query = queries.get(query_id)
        if not query or query.type != "3":
            continue
        if query_id not in cache:
            cache[query_id] = (
                score_all_memories(
                    query,
                    memories,
                    memory_tokens,
                    memory_vectors,
                    idf,
                    avg_len,
                    personas,
                    importance_scores,
                    args.half_life_days,
                ),
                facet_rankings(
                    query,
                    memories,
                    memory_tokens,
                    memory_vectors,
                    idf,
                    avg_len,
                    personas,
                    args.max_facets,
                ),
            )
        offline_scores, facet_scores = cache[query_id]
        gold_ids = set(query.answer_memory_ids)
        pool = build_pool(candidate_rows, offline_scores, facet_scores, memory_by_id, args.offline_k, args.facet_k)
        for row in pool:
            row["split_seed"] = seed
            row["query_id"] = query_id
            row["query"] = query.query
            row["is_relevant"] = row["memory_id"] in gold_ids
            row["num_gold"] = len(gold_ids)
            row["is_multi_evidence"] = 1 if len(gold_ids) > 1 else 0
        pools[seed][query_id] = pool
    return pools, queries


def score_method(
    seed: str,
    query_ids: list[str],
    pools_for_seed: dict[str, list[dict[str, Any]]],
    queries: dict[str, Any],
    method: str,
    ks: list[int],
    weights: dict[str, float] | None = None,
    mix: float = 0.5,
    redundancy_weight: float = 0.0,
    keep_top1: bool = True,
    select_k: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_query = []
    ranked_rows = []
    for query_id in query_ids:
        pool = pools_for_seed[query_id]
        query = queries[query_id]
        gold_ids = set(query.answer_memory_ids)
        if method == "candidate20_then_expansion":
            candidate_rows = sorted(
                [row for row in pool if row.get("source_candidate")],
                key=lambda row: row.get("candidate_rank", 999),
            )
            rows = append_expansion_after_candidate(candidate_rows, pool)
        elif method == "expanded_pool_oracle_top5":
            relevant = [row for row in pool if row["is_relevant"]]
            non_relevant = [row for row in pool if not row["is_relevant"]]
            relevant.sort(key=lambda row: row.get("candidate_norm", 0.0), reverse=True)
            non_relevant.sort(key=lambda row: row.get("candidate_norm", 0.0), reverse=True)
            rows = relevant[:select_k] + non_relevant
        else:
            rows = select_rows(pool, weights or {}, mix, redundancy_weight, keep_top1, select_k)
        for row in rows:
            row["is_relevant"] = row["memory_id"] in gold_ids
        row_metrics = metrics(rows, gold_ids, ks)
        per_query.append({
            "split_seed": seed,
            "query_id": query_id,
            "query": query.query,
            "method": method,
            "pool_size": len(rows),
            "num_gold": len(gold_ids),
            "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            **row_metrics,
        })
        for rank, row in enumerate(rows[: max(ks)], start=1):
            ranked_rows.append({
                "split_seed": seed,
                "query_id": query_id,
                "method": method,
                "rank": rank,
                "memory_id": row["memory_id"],
                "memory_type": row.get("memory_type", ""),
                "is_relevant": row.get("is_relevant", False),
                "learned_selector_score": row.get("learned_selector_score", ""),
                "candidate_norm": row.get("candidate_norm", ""),
                "bm25_norm": row.get("bm25_norm", ""),
                "semantic_norm": row.get("semantic_norm", ""),
                "facet_rrf": row.get("facet_rrf", ""),
                "source_candidate": row.get("source_candidate", ""),
                "source_offline": row.get("source_offline", ""),
                "source_facet": row.get("source_facet", ""),
                "memory_text": row.get("memory_text", ""),
            })
    return per_query, ranked_rows


def objective(rows: list[dict[str, Any]], objective_name: str) -> float:
    if not rows:
        return 0.0
    mrr = statistics.mean(row["mrr"] for row in rows)
    r5 = statistics.mean(row["recall@5"] for row in rows)
    cov5 = statistics.mean(row["coverage_ratio@5"] for row in rows)
    full5 = statistics.mean(row["full_coverage@5"] for row in rows)
    if objective_name == "coverage":
        return cov5 + 0.4 * full5 + 0.1 * r5
    if objective_name == "mrr":
        return mrr
    return mrr + 0.35 * cov5 + 0.2 * full5


def tune_params(
    validation_seed: str,
    validation_ids: list[str],
    pools_for_validation: dict[str, list[dict[str, Any]]],
    queries: dict[str, Any],
    weights: dict[str, float],
    mixes: list[float],
    redundancy_weights: list[float],
    keep_top1_options: list[bool],
    objective_name: str,
    ks: list[int],
    select_k: int,
) -> dict[str, Any]:
    baseline_rows, _ = score_method(validation_seed, validation_ids, pools_for_validation, queries, "candidate20_then_expansion", ks)
    baseline_cov5 = statistics.mean(row["coverage_ratio@5"] for row in baseline_rows)
    baseline_full5 = statistics.mean(row["full_coverage@5"] for row in baseline_rows)
    best = {
        "mix": 0.0,
        "redundancy_weight": 0.0,
        "keep_top1": True,
        "validation_objective": objective(baseline_rows, objective_name),
        "validation_coverage@5": baseline_cov5,
        "validation_full@5": baseline_full5,
    }
    for mix in mixes:
        for redundancy_weight in redundancy_weights:
            for keep_top1 in keep_top1_options:
                rows, _ = score_method(
                    validation_seed,
                    validation_ids,
                    pools_for_validation,
                    queries,
                    "learned_expanded_selector",
                    ks,
                    weights,
                    mix,
                    redundancy_weight,
                    keep_top1,
                    select_k,
                )
                cov5 = statistics.mean(row["coverage_ratio@5"] for row in rows)
                full5 = statistics.mean(row["full_coverage@5"] for row in rows)
                if cov5 + 1e-12 < baseline_cov5 or full5 + 1e-12 < baseline_full5:
                    continue
                score = objective(rows, objective_name)
                if score > best["validation_objective"]:
                    best = {
                        "mix": mix,
                        "redundancy_weight": redundancy_weight,
                        "keep_top1": keep_top1,
                        "validation_objective": score,
                        "validation_coverage@5": cov5,
                        "validation_full@5": full5,
                    }
    return best


def aggregate(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    out = []
    for method, bucket in sorted(buckets.items()):
        item = {
            "method": method,
            "rows": len(bucket),
            "mean_pool_size": statistics.mean(row["pool_size"] for row in bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
            "mrr": statistics.mean(row["mrr"] for row in bucket),
            "recall@1": statistics.mean(row["recall@1"] for row in bucket),
            "recall@3": statistics.mean(row["recall@3"] for row in bucket),
            "recall@5": statistics.mean(row["recall@5"] for row in bucket),
        }
        for k in ks:
            item[f"coverage_ratio@{k}"] = statistics.mean(row[f"coverage_ratio@{k}"] for row in bucket)
            item[f"full_coverage@{k}"] = statistics.mean(row[f"full_coverage@{k}"] for row in bucket)
        out.append(item)
    return out


def deltas(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method["candidate20_then_expansion"]
    rows = []
    for method, row in by_method.items():
        if method == "candidate20_then_expansion":
            continue
        out = {"baseline": "candidate20_then_expansion", "method": method}
        for name in ("mrr", "recall@5", "coverage_ratio@5", "full_coverage@5", "coverage_ratio@100", "full_coverage@100"):
            out[f"delta_{name}"] = row[name] - base[name]
        rows.append(out)
    return rows


def summarize_weights(weight_rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    by_feature: dict[str, list[float]] = defaultdict(list)
    for row in weight_rows:
        by_feature[row["feature"]].append(float(row["weight"]))
    out = []
    for feature, values in by_feature.items():
        out.append({
            "feature": feature,
            "mean_abs_weight": statistics.mean(abs(value) for value in values),
            "mean_weight": statistics.mean(values),
            "stdev_weight": statistics.stdev(values) if len(values) > 1 else 0.0,
        })
    out.sort(key=lambda row: row["mean_abs_weight"], reverse=True)
    return out[:top_n]


def write_report(
    path: Path,
    summary: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    selected_params: list[dict[str, Any]],
    weights: list[dict[str, Any]],
    objective_name: str,
) -> None:
    by_method = {row["method"]: row for row in summary}
    lines = [
        "# Type 3 学习式扩展池证据选择实验",
        "",
        "本实验在扩展候选池上训练无依赖的轻量选择器：用训练 query 的相关/不相关候选特征均值差学习权重，在 validation seed 上选择 mix/redundancy/keep_top1，再在 held-out seed 上评估。",
        "",
        f"优化目标：`{objective_name}`。测试 query 的 gold evidence 不参与训练或调参。",
        "",
        "## Held-Out 结果",
        "",
        "| 方法 | Rows | Pool | MRR | R@5 | Coverage@5 | Full@5 | Coverage@100 | Full@100 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("candidate20_then_expansion", "learned_expanded_selector", "expanded_pool_oracle_top5"):
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['rows']} | {row['mean_pool_size']:.1f} | {metric(row['mrr'])} | "
                f"{metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | {metric(row['full_coverage@5'])} | "
                f"{metric(row['coverage_ratio@100'])} | {metric(row['full_coverage@100'])} |"
            )
    lines.extend(["", "## 相比 Candidate20 Then Expansion 的变化", ""])
    for row in delta_rows:
        lines.append(
            f"- `{row['method']}`：MRR `{row['delta_mrr']:+.4f}`，R@5 `{row['delta_recall@5']:+.4f}`，"
            f"Coverage@5 `{row['delta_coverage_ratio@5']:+.4f}`，Full@5 `{row['delta_full_coverage@5']:+.4f}`。"
        )
    lines.extend([
        "",
        "## Validation 选择参数",
        "",
        "| Seed | Mix | Redundancy | Keep Top1 | Validation Coverage@5 | Validation Full@5 |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for row in selected_params:
        lines.append(
            f"| {row['split_seed']} | {row['mix']} | {row['redundancy_weight']} | {row['keep_top1']} | "
            f"{metric(row['validation_coverage@5'])} | {metric(row['validation_full@5'])} |"
        )
    if weights:
        lines.extend([
            "",
            "## Top Learned Weights",
            "",
            "| Feature | Mean Abs Weight | Mean Weight | Std |",
            "|---|---:|---:|---:|",
        ])
        for row in weights[:12]:
            lines.append(
                f"| {row['feature']} | {float(row['mean_abs_weight']):.4f} | "
                f"{float(row['mean_weight']):.4f} | {float(row['stdev_weight']):.4f} |"
            )
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果学习式选择器提升 Coverage@5/Full@5，说明扩展池收益已能转成最终证据选择收益。",
        "- 如果仍低于 oracle，说明需要更强的 listwise/setwise 模型或 LLM 子问题标签。",
        "- 如果与保守追加基线持平，说明当前无依赖特征学习不足，但扩展池本身仍有价值。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run learned Type3 expanded-pool selector.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--offline-k", type=int, default=50)
    parser.add_argument("--facet-k", type=int, default=50)
    parser.add_argument("--select-k", type=int, default=5)
    parser.add_argument("--max-facets", type=int, default=6)
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--mixes", default="0.1,0.2,0.35,0.5,0.65,0.8")
    parser.add_argument("--redundancy-weights", default="0.0,0.02,0.05,0.08")
    parser.add_argument("--objective", choices=("mrr", "coverage", "balanced"), default="coverage")
    parser.add_argument("--l2", type=float, default=0.05)
    parser.add_argument("--ks", default="1,3,5,20,50,100")
    parser.add_argument("--feature-top-n", type=int, default=40)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-weights", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    pools, queries = prepare_pools(args)
    seeds = sorted(pools)
    mixes = [float(item.strip()) for item in args.mixes.split(",") if item.strip()]
    redundancy_weights = [float(item.strip()) for item in args.redundancy_weights.split(",") if item.strip()]
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    all_per_query = []
    all_ranked = []
    selected_rows = []
    weight_rows = []
    for seed in seeds:
        test_ids = sorted(pools[seed])
        other_seeds = [item for item in seeds if item != seed]
        validation_seed = other_seeds[0]
        validation_ids = sorted(pools[validation_seed])
        validation_id_set = set(validation_ids)
        train_rows = [
            row
            for other_seed in other_seeds[1:]
            for query_id, rows in pools[other_seed].items()
            if query_id not in validation_id_set
            for row in rows
        ]
        weights = learn_weights(train_rows, args.l2)
        for feature, weight in weights.items():
            weight_rows.append({"split_seed": seed, "feature": feature, "weight": weight})
        best = tune_params(
            validation_seed,
            validation_ids,
            pools[validation_seed],
            queries,
            weights,
            mixes,
            redundancy_weights,
            [True, False],
            args.objective,
            ks,
            args.select_k,
        )
        selected_rows.append({"split_seed": seed, **best, "train_candidates": len(train_rows), "validation_queries": len(validation_ids), "test_queries": len(test_ids)})
        for method in ("candidate20_then_expansion", "learned_expanded_selector", "expanded_pool_oracle_top5"):
            per_query, ranked = score_method(
                seed,
                test_ids,
                pools[seed],
                queries,
                method,
                ks,
                weights,
                best["mix"],
                best["redundancy_weight"],
                bool(best["keep_top1"]),
                args.select_k,
            )
            all_per_query.extend(per_query)
            all_ranked.extend(ranked)

    summary = aggregate(all_per_query, ks)
    delta_rows = deltas(summary)
    weight_summary = summarize_weights(weight_rows, args.feature_top_n)
    write_csv(args.output_per_query, all_per_query)
    write_csv(args.output_ranked, all_ranked)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, delta_rows)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_weights, weight_summary)
    write_report(args.output_report, summary, delta_rows, selected_rows, weight_summary, args.objective)
    print(json.dumps({
        "rows": len(all_per_query),
        "seeds": seeds,
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
