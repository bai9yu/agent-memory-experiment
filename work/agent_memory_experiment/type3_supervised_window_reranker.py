#!/usr/bin/env python3
"""Held-out supervised conservative window reranker for Type-3 queries."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from memory_eval import (
    Memory,
    Query,
    bm25_score,
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    cosine,
    entity_overlap,
    hashed_vector,
    load_memories,
    load_queries,
    memory_type_score,
    normalize,
    persona_score,
    query_intent_type_weights,
    query_personas,
    recency_gate,
    time_decay,
    tokenize,
)
from query_type_router_experiment import metric, write_csv


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def known_personas(memories: list[Memory]) -> set[str]:
    return {memory.agent_id.lower() for memory in memories if memory.agent_id}


def load_ranked(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "query_type": row.get("query_type", ""),
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row.get("memory_type", ""),
            "memory_text": row.get("memory_text", ""),
            "learned_score": float(row.get("learned_score", "0") or 0.0),
            "is_relevant": row.get("is_relevant") == "True",
        })
    for rows in groups.values():
        rows.sort(key=lambda row: row["rank"])
        scores = {row["memory_id"]: row["learned_score"] for row in rows}
        normalized = normalize(scores)
        for row in rows:
            row["candidate_norm"] = normalized[row["memory_id"]]
            row["candidate_rr"] = 1.0 / row["rank"]
            row["candidate_rrf"] = 1.0 / (60.0 + row["rank"])
    return groups


def enrich_rows(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    queries: dict[str, Query],
    memory_by_id: dict[str, Memory],
    memory_tokens: dict[str, list[str]],
    memory_vectors: dict[str, Any],
    idf: dict[str, float],
    avg_len: float,
    personas: set[str],
    importance_scores: dict[str, float],
    half_life_days: float,
) -> None:
    for (_seed, query_id), rows in groups.items():
        query = queries.get(query_id)
        if not query:
            continue
        query_tokens = tokenize(query.query)
        query_token_set = set(query_tokens)
        query_vector = hashed_vector(query_tokens)
        query_persona_names = query_personas(query, personas)
        query_type_weights = query_intent_type_weights(query)
        query_recency_gate = recency_gate(query)
        bm25_raw = {}
        semantic_raw = {}
        for row in rows:
            memory = memory_by_id[row["memory_id"]]
            bm25_raw[row["memory_id"]] = bm25_score(query_tokens, memory_tokens[memory.id], idf, avg_len)
            semantic_raw[row["memory_id"]] = cosine(query_vector, memory_vectors[memory.id])
        bm25_norm = normalize(bm25_raw)
        semantic_norm = normalize(semantic_raw)
        for row in rows:
            memory = memory_by_id[row["memory_id"]]
            memory_token_set = set(memory_tokens[memory.id])
            row["bm25_norm"] = bm25_norm[row["memory_id"]]
            row["semantic_norm"] = semantic_norm[row["memory_id"]]
            row["entity_overlap"] = entity_overlap(query_token_set, memory.entities)
            row["memory_type_score"] = memory_type_score(memory, query_type_weights)
            row["persona_score"] = persona_score(memory, query_persona_names)
            row["importance_score"] = importance_scores[memory.id]
            row["time_decay"] = time_decay(memory.date, query.query_date, half_life_days)
            row["recency_score"] = query_recency_gate * row["time_decay"]
            row["query_token_coverage"] = len(query_token_set & memory_token_set) / max(len(query_token_set), 1)
            row["text_len"] = len(memory_tokens[memory.id])


def feature_dict(row: dict[str, Any]) -> dict[str, float]:
    return {
        "candidate_norm": float(row.get("candidate_norm", 0.0)),
        "candidate_rr": float(row.get("candidate_rr", 0.0)),
        "candidate_rrf": float(row.get("candidate_rrf", 0.0)),
        "bm25_norm": float(row.get("bm25_norm", 0.0)),
        "semantic_norm": float(row.get("semantic_norm", 0.0)),
        "entity_overlap": float(row.get("entity_overlap", 0.0)),
        "memory_type_score": float(row.get("memory_type_score", 0.0)),
        "persona_score": max(float(row.get("persona_score", 0.0)), 0.0),
        "importance_score": float(row.get("importance_score", 0.0)),
        "recency_score": float(row.get("recency_score", 0.0)),
        "query_token_coverage": float(row.get("query_token_coverage", 0.0)),
        "text_len_log": min(float(row.get("text_len", 0.0)), 80.0) / 80.0,
        f"memory_type={row.get('memory_type', '')}": 1.0,
    }


def train_predict(train_rows: list[dict[str, Any]], test_rows: list[dict[str, Any]]) -> tuple[list[float], list[dict[str, Any]]]:
    if len({row["is_relevant"] for row in train_rows}) < 2:
        return [0.0 for _ in test_rows], []
    train_features = [feature_dict(row) for row in train_rows]
    feature_names = sorted({name for features in train_features for name in features})
    positives = [features for row, features in zip(train_rows, train_features) if row["is_relevant"]]
    negatives = [features for row, features in zip(train_rows, train_features) if not row["is_relevant"]]
    weights = {}
    for name in feature_names:
        pos_values = [features.get(name, 0.0) for features in positives]
        neg_values = [features.get(name, 0.0) for features in negatives]
        pos_mean = statistics.mean(pos_values) if pos_values else 0.0
        neg_mean = statistics.mean(neg_values) if neg_values else 0.0
        spread_values = pos_values + neg_values
        spread = statistics.pstdev(spread_values) if len(spread_values) > 1 else 0.0
        weights[name] = (pos_mean - neg_mean) / max(spread, 1e-6)

    def score(row: dict[str, Any]) -> float:
        features = feature_dict(row)
        raw = sum(weights.get(name, 0.0) * features.get(name, 0.0) for name in feature_names)
        return 1.0 / (1.0 + pow(2.718281828, -max(min(raw, 20.0), -20.0)))

    scores = [score(row) for row in test_rows]
    feature_rows = [
        {"feature": name, "importance": abs(weight)}
        for name, weight in weights.items()
    ]
    return scores, feature_rows


def first_rank(rows: list[dict[str, Any]]) -> int:
    for rank, row in enumerate(rows, start=1):
        if row["is_relevant"]:
            return rank
    return 0


def ranking_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rank = first_rank(rows)
    return {
        "mrr": 1.0 / rank if rank else 0.0,
        "recall@1": 1.0 if rank and rank <= 1 else 0.0,
        "recall@3": 1.0 if rank and rank <= 3 else 0.0,
        "recall@5": 1.0 if rank and rank <= 5 else 0.0,
        "first_rank": rank,
    }


def coverage_metrics(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    ranked_ids = [row["memory_id"] for row in rows]
    out = {}
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def rerank_window(rows: list[dict[str, Any]], alpha: float, window_k: int, keep_top1: bool) -> list[dict[str, Any]]:
    rows = [dict(row) for row in rows]
    head = rows[:window_k]
    tail = rows[window_k:]
    for row in head:
        row["window_score"] = alpha * row.get("model_score", 0.0) + (1.0 - alpha) * row.get("candidate_norm", 0.0)
    pinned = []
    if keep_top1 and head:
        pinned = [head[0]]
        head = head[1:]
    head.sort(key=lambda row: row["window_score"], reverse=True)
    return pinned + head + tail


def score_queries(
    query_ids: list[str],
    groups_for_seed: dict[str, list[dict[str, Any]]],
    queries: dict[str, Query],
    method: str,
    alpha: float,
    window_k: int,
    keep_top1: bool,
    ks: list[int],
) -> list[dict[str, Any]]:
    rows = []
    for query_id in query_ids:
        query = queries[query_id]
        ranked = groups_for_seed[query_id]
        if method != "candidate_reranker":
            ranked = rerank_window(ranked, alpha, window_k, keep_top1)
        gold_ids = set(query.answer_memory_ids)
        rows.append({
            "query_id": query_id,
            "query_type": query.type,
            "method": method,
            "alpha": alpha,
            "window_k": window_k,
            "keep_top1": int(keep_top1),
            "num_gold": len(gold_ids),
            "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            **ranking_metrics(ranked),
            **coverage_metrics(ranked, gold_ids, ks),
        })
    return rows


def aggregate_metric(rows: list[dict[str, Any]], objective: str) -> float:
    if not rows:
        return 0.0
    mrr = statistics.mean(row["mrr"] for row in rows)
    cov5 = statistics.mean(row["coverage_ratio@5"] for row in rows)
    full5 = statistics.mean(row["full_coverage@5"] for row in rows)
    r5 = statistics.mean(row["recall@5"] for row in rows)
    if objective == "mrr":
        return mrr
    if objective == "coverage":
        return cov5 + 0.25 * full5 + 0.10 * r5
    return mrr + 0.35 * cov5 + 0.15 * full5


def aggregate(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    out = []
    for method, bucket in sorted(buckets.items()):
        item = {
            "method": method,
            "num_rows": len(bucket),
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


def summarize_features(rows: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    by_feature: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_feature[row["feature"]].append(float(row["importance"]))
    out = []
    for feature, values in by_feature.items():
        out.append({
            "feature": feature,
            "splits": len(values),
            "importance_mean": statistics.mean(values),
            "importance_stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        })
    out.sort(key=lambda row: row["importance_mean"], reverse=True)
    return out[:top_n]


def tune_params(
    train_ids: list[str],
    groups_for_seed: dict[str, list[dict[str, Any]]],
    queries: dict[str, Query],
    alphas: list[float],
    windows: list[int],
    objective: str,
    ks: list[int],
) -> dict[str, Any]:
    baseline = score_queries(train_ids, groups_for_seed, queries, "candidate_reranker", 0.0, 5, False, ks)
    baseline_cov5 = statistics.mean(row["coverage_ratio@5"] for row in baseline)
    baseline_full5 = statistics.mean(row["full_coverage@5"] for row in baseline)
    best = {
        "alpha": 0.0,
        "window_k": 5,
        "keep_top1": True,
        "objective_score": aggregate_metric(baseline, objective),
        "train_cov5": baseline_cov5,
        "train_full5": baseline_full5,
    }
    for alpha in alphas:
        for window_k in windows:
            for keep_top1 in (True, False):
                rows = score_queries(
                    train_ids,
                    groups_for_seed,
                    queries,
                    "supervised_window_reranker",
                    alpha,
                    window_k,
                    keep_top1,
                    ks,
                )
                cov5 = statistics.mean(row["coverage_ratio@5"] for row in rows)
                full5 = statistics.mean(row["full_coverage@5"] for row in rows)
                if cov5 + 1e-12 < baseline_cov5 or full5 + 1e-12 < baseline_full5:
                    continue
                objective_score = aggregate_metric(rows, objective)
                if objective_score > best["objective_score"]:
                    best = {
                        "alpha": alpha,
                        "window_k": window_k,
                        "keep_top1": keep_top1,
                        "objective_score": objective_score,
                        "train_cov5": cov5,
                        "train_full5": full5,
                    }
    return best


def evaluate_split(
    seed: int,
    groups_by_seed: dict[str, dict[str, list[dict[str, Any]]]],
    queries: dict[str, Query],
    alphas: list[float],
    windows: list[int],
    objective: str,
    ks: list[int],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    seed_key = str(seed)
    groups_for_seed = groups_by_seed[seed_key]
    test_ids = sorted(groups_for_seed)
    train_ids = sorted({
        query_id
        for other_seed, group in groups_by_seed.items()
        if other_seed != seed_key
        for query_id in group
        if query_id not in groups_for_seed
    })
    train_rows = [
        row
        for other_seed, group in groups_by_seed.items()
        if other_seed != seed_key
        for query_id, rows in group.items()
        if query_id in train_ids
        for row in rows
    ]
    test_rows = [row for query_id in test_ids for row in groups_for_seed[query_id]]
    model_scores, feature_rows = train_predict(train_rows, test_rows)
    for row, score in zip(test_rows, model_scores):
        row["model_score"] = score
    for row in feature_rows:
        row["split_seed"] = seed

    tuning_seed = next(other_seed for other_seed in sorted(groups_by_seed) if other_seed != seed_key)
    tuning_group = {
        query_id: rows
        for query_id, rows in groups_by_seed[tuning_seed].items()
        if query_id in train_ids
    }
    tune_ids = sorted(tuning_group)
    best = tune_params(tune_ids, tuning_group, queries, alphas, windows, objective, ks)
    selected = [{
        "split_seed": seed,
        **best,
        "train_ids": len(train_ids),
        "test_ids": len(test_ids),
    }]
    per_query = []
    ranked_rows = []
    for method, alpha, window_k, keep_top1 in (
        ("candidate_reranker", 0.0, 5, False),
        ("supervised_window_reranker", best["alpha"], int(best["window_k"]), bool(best["keep_top1"])),
    ):
        scored = score_queries(test_ids, groups_for_seed, queries, method, alpha, window_k, keep_top1, ks)
        for row in scored:
            row["split_seed"] = seed
        per_query.extend(scored)
        for query_id in test_ids:
            ranked = groups_for_seed[query_id]
            if method != "candidate_reranker":
                ranked = rerank_window(ranked, alpha, window_k, keep_top1)
            for rank, row in enumerate(ranked[: max(ks)], start=1):
                ranked_rows.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "is_relevant": row["is_relevant"],
                    "candidate_norm": row.get("candidate_norm", 0.0),
                    "model_score": row.get("model_score", 0.0),
                    "window_score": row.get("window_score", ""),
                    "memory_text": row["memory_text"],
                })
    return per_query, ranked_rows, selected, feature_rows


def deltas(summary: list[dict[str, Any]], baseline: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method[baseline]
    rows = []
    for method, row in by_method.items():
        if method == baseline:
            continue
        out = {"baseline": baseline, "method": method}
        for name in ("mrr", "recall@1", "recall@3", "recall@5", "coverage_ratio@5", "full_coverage@5", "coverage_ratio@20", "full_coverage@20"):
            out[f"delta_{name}"] = row[name] - base[name]
        rows.append(out)
    return rows


def write_report(
    path: Path,
    summary: list[dict[str, Any]],
    delta_rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    features: list[dict[str, Any]],
    objective: str,
) -> None:
    by_method = {row["method"]: row for row in summary}
    lines = [
        "# Type 3 监督式窗口重排实验",
        "",
        "本实验针对 rescue-space 分析中发现的 Top-20 可救回空间，训练一个轻量监督模型预测候选记忆相关性，并只在 Top-K 窗口内做保守重排。参数 `alpha/window_k/keep_top1` 只在训练 query 上选择，测试 query 不参与调参。",
        "",
        f"优化目标：`{objective}`。该实验不调用外部大模型，也不使用测试 query 的 gold evidence 进行排序。",
        "",
        "## Held-Out 结果",
        "",
        "| 方法 | Rows | MRR | R@1 | R@3 | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("candidate_reranker", "supervised_window_reranker"):
        row = by_method.get(method)
        if row:
            lines.append(
                f"| {method} | {row['num_rows']} | {metric(row['mrr'])} | {metric(row['recall@1'])} | "
                f"{metric(row['recall@3'])} | {metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | "
                f"{metric(row['full_coverage@5'])} | {metric(row['coverage_ratio@20'])} | {metric(row['full_coverage@20'])} |"
            )
    lines.extend(["", "## 相比 Candidate Reranker 的变化", ""])
    for row in delta_rows:
        lines.append(
            f"- `{row['method']}`：MRR `{row['delta_mrr']:+.4f}`，R@5 `{row['delta_recall@5']:+.4f}`，"
            f"Coverage@5 `{row['delta_coverage_ratio@5']:+.4f}`，Full@5 `{row['delta_full_coverage@5']:+.4f}`。"
        )
    lines.extend([
        "",
        "## 训练集选择的参数",
        "",
        "| Seed | Alpha | Window K | Keep Top1 | Train Coverage@5 | Train Full@5 |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for row in selected:
        lines.append(
            f"| {row['split_seed']} | {row['alpha']} | {row['window_k']} | {row['keep_top1']} | "
            f"{metric(row['train_cov5'])} | {metric(row['train_full5'])} |"
        )
    if features:
        lines.extend([
            "",
            "## Top Feature Importance",
            "",
            "| Feature | Importance Mean | Importance Std |",
            "|---|---:|---:|",
        ])
        for row in features[:12]:
            lines.append(f"| {row['feature']} | {float(row['importance_mean']):.4f} | {float(row['importance_stdev']):.4f} |")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果该方法提升 MRR 且不降低 Coverage@5/Full@5，说明保守窗口重排能利用 Top-20 可救回空间。",
        "- 如果 Coverage@5 仍没有提升，说明需要真正的 set/listwise 覆盖目标，而非单候选相关性模型。",
        "- 如果指标下降，说明当前 Type 3 训练样本或特征不足，应优先增强召回或引入 LLM 子问题标签。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run held-out Type3 supervised conservative window reranker.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--seeds", default="13,17,23,29,31")
    parser.add_argument("--alphas", default="0.1,0.2,0.35,0.5,0.65,0.8")
    parser.add_argument("--windows", default="3,5,10")
    parser.add_argument("--objective", choices=("mrr", "coverage", "balanced"), default="balanced")
    parser.add_argument("--ks", default="1,3,5,20")
    parser.add_argument("--half-life-days", type=float, default=30.0)
    parser.add_argument("--feature-top-n", type=int, default=40)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-selected", type=Path, required=True)
    parser.add_argument("--output-feature-importance", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = {query.id: query for query in load_queries(args.queries)}
    type3_query_ids = sorted(query.id for query in queries.values() if query.type == "3")
    memory_by_id = {memory.id: memory for memory in memories}
    memory_tokens = build_memory_tokens(memories)
    memory_vectors = {memory.id: hashed_vector(memory_tokens[memory.id]) for memory in memories}
    idf = build_idf(memories)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    personas = known_personas(memories)
    importance_scores = build_importance_scores(memories)
    groups = load_ranked(args.candidate_ranked)
    enrich_rows(
        groups,
        queries,
        memory_by_id,
        memory_tokens,
        memory_vectors,
        idf,
        avg_len,
        personas,
        importance_scores,
        args.half_life_days,
    )
    groups_by_seed: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(dict)
    for (seed, query_id), rows in groups.items():
        if query_id in type3_query_ids:
            groups_by_seed[seed][query_id] = rows
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    alphas = [float(item.strip()) for item in args.alphas.split(",") if item.strip()]
    windows = [int(item.strip()) for item in args.windows.split(",") if item.strip()]
    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]

    per_query = []
    ranked_rows = []
    selected_rows = []
    feature_rows = []
    for seed in seeds:
        split_per_query, split_ranked, split_selected, split_features = evaluate_split(
            seed,
            groups_by_seed,
            queries,
            alphas,
            windows,
            args.objective,
            ks,
        )
        per_query.extend(split_per_query)
        ranked_rows.extend(split_ranked)
        selected_rows.extend(split_selected)
        feature_rows.extend(split_features)

    summary = aggregate(per_query, ks)
    delta_rows = deltas(summary, "candidate_reranker")
    feature_summary = summarize_features(feature_rows, args.feature_top_n)
    write_csv(args.output_per_query, per_query)
    write_csv(args.output_ranked, ranked_rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, delta_rows)
    write_csv(args.output_selected, selected_rows)
    write_csv(args.output_feature_importance, feature_summary)
    write_report(args.output_report, summary, delta_rows, selected_rows, feature_summary, args.objective)
    print(json.dumps({
        "num_type3_query_splits": len(per_query) // 2,
        "num_per_query_rows": len(per_query),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
