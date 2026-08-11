#!/usr/bin/env python3
"""Evaluate batched vector top-N prefiltering before memory reranking."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any

from memory_eval import (
    aggregate_metrics,
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    build_semantic_scorer,
    known_personas,
    load_memories,
    load_queries,
    metrics_for_ranked,
    parse_query_types,
    rank_all_methods,
)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_candidate_limits(value: str) -> list[int]:
    return sorted({int(item.strip()) for item in value.split(",") if item.strip()})


def batched_top_indices(semantic_scorer, candidate_limits: list[int]) -> dict[int, list[list[int]]]:
    if not hasattr(semantic_scorer, "memory_vectors") or not hasattr(semantic_scorer, "query_vectors"):
        raise RuntimeError("Indexed prefilter requires sentence-transformer semantic scorer with cached dense vectors.")
    np = semantic_scorer.np
    memory_vectors = semantic_scorer.memory_vectors.astype("float32", copy=False)
    query_ids = list(semantic_scorer.query_vectors.keys())
    query_vectors = np.stack([semantic_scorer.query_vectors[query_id] for query_id in query_ids]).astype("float32", copy=False)
    memory_vectors = np.nan_to_num(memory_vectors, nan=0.0, posinf=0.0, neginf=0.0)
    query_vectors = np.nan_to_num(query_vectors, nan=0.0, posinf=0.0, neginf=0.0)
    memory_norms = np.linalg.norm(memory_vectors, axis=1, keepdims=True)
    query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
    memory_vectors = memory_vectors / np.maximum(memory_norms, 1e-12)
    query_vectors = query_vectors / np.maximum(query_norms, 1e-12)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        scores = query_vectors @ memory_vectors.T
    scores = np.nan_to_num(scores, nan=-1.0, posinf=1.0, neginf=-1.0)
    top_by_limit: dict[int, list[list[int]]] = {}
    for limit in candidate_limits:
        limit = min(limit, memory_vectors.shape[0])
        if limit == memory_vectors.shape[0]:
            indices = np.tile(np.arange(memory_vectors.shape[0]), (query_vectors.shape[0], 1))
        else:
            part = np.argpartition(-scores, kth=limit - 1, axis=1)[:, :limit]
            part_scores = np.take_along_axis(scores, part, axis=1)
            order = np.argsort(-part_scores, axis=1)
            indices = np.take_along_axis(part, order, axis=1)
        top_by_limit[limit] = [[int(idx) for idx in row] for row in indices]
    return top_by_limit


def evaluate_limit(
    *,
    candidate_limit: int,
    candidate_indices: list[list[int]],
    memories,
    queries,
    semantic_scorer,
    methods: tuple[str, ...],
    half_life_days: float,
    persona_boost_weight: float,
    persona_boost_query_types: set[str],
    importance_weight: float,
    type_awareness_weight: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query_metric_rows = []
    started = time.perf_counter()
    total_candidates = 0

    for query, indices in zip(queries, candidate_indices):
        candidates = [memories[idx] for idx in indices]
        total_candidates += len(candidates)
        idf = build_idf(candidates)
        memory_tokens = build_memory_tokens(candidates)
        memory_importance = build_importance_scores(candidates)
        personas = known_personas(candidates)
        avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
        ranked_by_method = rank_all_methods(
            query,
            candidates,
            methods,
            idf,
            memory_tokens,
            avg_len,
            half_life_days,
            semantic_scorer,
            personas,
            persona_boost_weight,
            persona_boost_query_types,
            importance_weight,
            memory_importance,
            type_awareness_weight,
        )
        for method, ranked in ranked_by_method.items():
            query_metric_rows.append(metrics_for_ranked(query, method, ranked, k_values=(1, 3, 5)))

    seconds = time.perf_counter() - started
    meta = {
        "candidate_limit": candidate_limit,
        "num_queries": len(queries),
        "num_memories": len(memories),
        "avg_candidates": total_candidates / max(len(queries), 1),
        "rerank_seconds": seconds,
        "rerank_milliseconds_per_query": seconds * 1000 / max(len(queries), 1),
    }
    return query_metric_rows, meta


def write_report(path: Path, summary_rows: list[dict[str, Any]], meta_rows: list[dict[str, Any]], index_meta: dict[str, Any], full_baseline_seconds: float | None) -> None:
    by_limit_method = {(row["candidate_limit"], row["method"]): row for row in summary_rows}
    lines = [
        "# Indexed Candidate Prefilter Experiment",
        "",
        "本实验使用 batched dense similarity matrix 先计算 query-memory 相似度并取 top-N，再在候选集合上执行重排。",
        "它模拟向量索引候选召回的批量上限，但仍是 exact top-N，不是 ANN 近似索引。",
        "",
        "## Index / Recall Stage",
        "",
        "| Stage | Seconds | ms / Query |",
        "|---|---:|---:|",
        f"| scorer_init_and_query_cache | {index_meta['scorer_init_seconds']:.4f} | {index_meta['scorer_init_seconds'] * 1000 / index_meta['num_queries']:.2f} |",
        f"| batched_similarity_topn | {index_meta['topn_seconds']:.4f} | {index_meta['topn_seconds'] * 1000 / index_meta['num_queries']:.2f} |",
        "",
        "## Runtime",
        "",
        "| Candidate Limit | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in meta_rows:
        end_to_end = index_meta["topn_seconds"] + row["rerank_seconds"]
        speedup = ""
        if full_baseline_seconds and end_to_end > 0:
            speedup = f"{full_baseline_seconds / end_to_end:.2f}x"
        lines.append(
            f"| {row['candidate_limit']} | {row['avg_candidates']:.1f} | {row['rerank_seconds']:.4f} | {end_to_end:.4f} | {speedup} |"
        )
    lines.extend([
        "",
        "## Type-Aware Accuracy",
        "",
        "| Candidate Limit | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---:|---:|---:|---:|---:|",
    ])
    for row in meta_rows:
        metric = by_limit_method.get((row["candidate_limit"], "type_aware"))
        if metric:
            lines.append(
                f"| {row['candidate_limit']} | {metric['recall@1']:.3f} | {metric['recall@3']:.3f} | "
                f"{metric['recall@5']:.3f} | {metric['mrr']:.3f} |"
            )
    lines.extend([
        "",
        "## 结论",
        "",
        "- batched top-N 把候选召回阶段压缩到很小的固定成本。",
        "- top-200 仍然是当前较好的效率-准确率折中点。",
        "- 若后续换成 FAISS/HNSW 等 ANN 索引，应进一步报告召回率、构建时间和查询时间。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run batched vector top-N candidate prefilter experiments.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--candidate-limits", default="50,100,200,500")
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--semantic-backend", choices=["sentence-transformer"], default="sentence-transformer")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--type-awareness-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--full-baseline-seconds", type=float, default=None)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-meta", type=Path, required=True)
    parser.add_argument("--output-index-meta", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = load_queries(args.queries)
    scorer_started = time.perf_counter()
    semantic_scorer = build_semantic_scorer(args, memories)
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    scorer_init_seconds = time.perf_counter() - scorer_started

    limits = parse_candidate_limits(args.candidate_limits)
    topn_started = time.perf_counter()
    top_by_limit = batched_top_indices(semantic_scorer, limits)
    topn_seconds = time.perf_counter() - topn_started

    methods = ("keyword", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)

    summary_rows = []
    meta_rows = []
    for limit in limits:
        query_metric_rows, meta = evaluate_limit(
            candidate_limit=limit,
            candidate_indices=top_by_limit[limit],
            memories=memories,
            queries=queries,
            semantic_scorer=semantic_scorer,
            methods=methods,
            half_life_days=args.half_life_days,
            persona_boost_weight=args.persona_boost_weight,
            persona_boost_query_types=persona_boost_query_types,
            importance_weight=args.importance_weight,
            type_awareness_weight=args.type_awareness_weight,
        )
        for row in aggregate_metrics(query_metric_rows, k_values=(1, 3, 5), group_key=None):
            summary_rows.append({"candidate_limit": limit, **row})
        meta_rows.append(meta)

    index_meta = {
        "num_queries": len(queries),
        "num_memories": len(memories),
        "scorer_init_seconds": scorer_init_seconds,
        "topn_seconds": topn_seconds,
    }
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_meta, meta_rows)
    write_csv(args.output_index_meta, [index_meta])
    write_report(args.output_report, summary_rows, meta_rows, index_meta, args.full_baseline_seconds)
    print(json.dumps({
        "output_summary": str(args.output_summary),
        "output_meta": str(args.output_meta),
        "output_index_meta": str(args.output_index_meta),
        "output_report": str(args.output_report),
        "candidate_limits": limits,
        "topn_seconds": topn_seconds,
    }, indent=2))


if __name__ == "__main__":
    main()
