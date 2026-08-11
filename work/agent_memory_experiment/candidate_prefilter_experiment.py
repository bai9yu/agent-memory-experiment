#!/usr/bin/env python3
"""Evaluate semantic top-N candidate prefiltering before reranking."""

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
    limits = []
    for item in value.split(","):
        item = item.strip()
        if item:
            limits.append(int(item))
    return sorted(set(limits))


def prefilter_candidates(query, memories, semantic_scorer, limit: int):
    if limit <= 0 or limit >= len(memories):
        return memories
    scores = semantic_scorer.score(query, memories)
    top_ids = {
        memory_id
        for memory_id, _ in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    }
    return [memory for memory in memories if memory.id in top_ids]


def evaluate_limit(
    *,
    candidate_limit: int,
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

    for query in queries:
        candidates = prefilter_candidates(query, memories, semantic_scorer, candidate_limit)
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
        "seconds": seconds,
        "milliseconds_per_query": seconds * 1000 / max(len(queries), 1),
    }
    return query_metric_rows, meta


def write_report(path: Path, summary_rows: list[dict[str, Any]], meta_rows: list[dict[str, Any]], full_baseline_seconds: float | None) -> None:
    by_limit_method = {(row["candidate_limit"], row["method"]): row for row in summary_rows}
    lines = [
        "# Candidate Prefilter Experiment",
        "",
        "本实验先用 semantic top-N 取候选，再在候选集合上执行 keyword / hybrid / time-aware / type-aware 重排。",
        "",
        "## Runtime",
        "",
        "| Candidate Limit | Avg Candidates | Seconds | ms / Query | Speedup vs Full Ranking |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in meta_rows:
        speedup = ""
        if full_baseline_seconds and row["seconds"] > 0:
            speedup = f"{full_baseline_seconds / row['seconds']:.2f}x"
        lines.append(
            f"| {row['candidate_limit']} | {row['avg_candidates']:.1f} | {row['seconds']:.4f} | "
            f"{row['milliseconds_per_query']:.2f} | {speedup} |"
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
        "## 结论提示",
        "",
        "- 如果小 candidate limit 的 Recall@5 明显下降，说明正确记忆未进入候选集，必须改进召回。",
        "- 如果耗时显著下降但 MRR 接近 full ranking，则该 candidate limit 可作为线上系统默认候选规模。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run semantic top-N candidate prefilter experiments.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--candidate-limits", default="50,100,200,500")
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
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
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = load_queries(args.queries)
    semantic_scorer = build_semantic_scorer(args, memories)
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    methods = ("keyword", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)

    summary_rows = []
    meta_rows = []
    for limit in parse_candidate_limits(args.candidate_limits):
        query_metric_rows, meta = evaluate_limit(
            candidate_limit=limit,
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

    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_meta, meta_rows)
    write_report(args.output_report, summary_rows, meta_rows, args.full_baseline_seconds)
    print(json.dumps({
        "output_summary": str(args.output_summary),
        "output_meta": str(args.output_meta),
        "output_report": str(args.output_report),
        "candidate_limits": parse_candidate_limits(args.candidate_limits),
    }, indent=2))


if __name__ == "__main__":
    main()
