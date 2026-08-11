#!/usr/bin/env python3
"""Measure coarse-grained runtime breakdown for memory retrieval."""

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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def elapsed_since(start: float) -> tuple[float, float]:
    now = time.perf_counter()
    return now, now - start


def benchmark(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    stages: list[dict[str, Any]] = []
    started = time.perf_counter()

    stage_started = time.perf_counter()
    memories = load_memories(args.memories)
    queries = load_queries(args.queries)
    _, seconds = elapsed_since(stage_started)
    stages.append({"variant": args.variant, "stage": "load_data", "seconds": seconds})

    stage_started = time.perf_counter()
    idf = build_idf(memories)
    memory_tokens = build_memory_tokens(memories)
    memory_importance = build_importance_scores(memories)
    personas = known_personas(memories)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)
    avg_len = statistics.mean(len(tokens) for tokens in memory_tokens.values())
    _, seconds = elapsed_since(stage_started)
    stages.append({"variant": args.variant, "stage": "feature_prep", "seconds": seconds})

    stage_started = time.perf_counter()
    semantic_scorer = build_semantic_scorer(args, memories)
    _, seconds = elapsed_since(stage_started)
    stages.append({"variant": args.variant, "stage": "semantic_scorer_init", "seconds": seconds})

    stage_started = time.perf_counter()
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    _, seconds = elapsed_since(stage_started)
    stages.append({"variant": args.variant, "stage": "query_encoding", "seconds": seconds})

    methods = ("vector", "keyword", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)

    query_metric_rows = []
    stage_started = time.perf_counter()
    for query in queries:
        ranked_by_method = rank_all_methods(
            query,
            memories,
            methods,
            idf,
            memory_tokens,
            avg_len,
            args.half_life_days,
            semantic_scorer,
            personas,
            args.persona_boost_weight,
            persona_boost_query_types,
            args.importance_weight,
            memory_importance,
            args.type_awareness_weight,
        )
        for method, ranked in ranked_by_method.items():
            query_metric_rows.append(metrics_for_ranked(query, method, ranked, k_values=(1, 3, 5)))
    _, seconds = elapsed_since(stage_started)
    stages.append({"variant": args.variant, "stage": "ranking_and_metrics", "seconds": seconds})

    total_seconds = time.perf_counter() - started
    stages.append({"variant": args.variant, "stage": "total", "seconds": total_seconds})

    summary = aggregate_metrics(query_metric_rows, k_values=(1, 3, 5), group_key=None)
    meta = [{
        "variant": args.variant,
        "num_memories": len(memories),
        "num_queries": len(queries),
        "num_methods": len(methods),
        "semantic_backend": semantic_scorer.name,
        "total_seconds": total_seconds,
        "milliseconds_per_query": total_seconds * 1000 / max(len(queries), 1),
        "milliseconds_per_query_method": total_seconds * 1000 / max(len(queries) * len(methods), 1),
    }]
    for row in stages:
        row["share_of_total"] = row["seconds"] / max(total_seconds, 1e-9)
        row["milliseconds_per_query"] = row["seconds"] * 1000 / max(len(queries), 1)
    return stages, meta, summary


def write_report(path: Path, stages: list[dict[str, Any]], meta: list[dict[str, Any]], summary: list[dict[str, Any]]) -> None:
    lines = [
        "# Retrieval Latency Breakdown",
        "",
        "## Run Meta",
        "",
        "| Variant | Memories | Queries | Methods | Total Seconds | ms / Query | ms / Query-Method |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in meta:
        lines.append(
            f"| {row['variant']} | {row['num_memories']} | {row['num_queries']} | {row['num_methods']} | "
            f"{row['total_seconds']:.4f} | {row['milliseconds_per_query']:.2f} | {row['milliseconds_per_query_method']:.2f} |"
        )
    lines.extend([
        "",
        "## Stage Breakdown",
        "",
        "| Variant | Stage | Seconds | Share | ms / Query |",
        "|---|---|---:|---:|---:|",
    ])
    for row in stages:
        lines.append(
            f"| {row['variant']} | {row['stage']} | {row['seconds']:.4f} | {row['share_of_total']:.3f} | {row['milliseconds_per_query']:.2f} |"
        )
    lines.extend([
        "",
        "## Metrics Sanity Check",
        "",
        "| Method | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in summary:
        lines.append(
            f"| {row['method']} | {row['recall@1']:.3f} | {row['recall@3']:.3f} | {row['recall@5']:.3f} | {row['mrr']:.3f} |"
        )
    lines.extend([
        "",
        "说明：该报告测量离线评测链路的粗粒度耗时，包括本地 embedding cache 读取、query 编码、全量 memory 排序与指标计算。",
        "它不是线上服务的严格单请求 latency，但可用于论文中的可复现实验效率分析。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure runtime breakdown for memory retrieval.")
    parser.add_argument("--variant", required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
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
    parser.add_argument("--output-stages", type=Path, required=True)
    parser.add_argument("--output-meta", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    stages, meta, summary = benchmark(args)
    write_csv(args.output_stages, stages)
    write_csv(args.output_meta, meta)
    write_csv(args.output_summary, summary)
    write_report(args.output_report, stages, meta, summary)
    print(json.dumps({
        "variant": args.variant,
        "output_stages": str(args.output_stages),
        "output_meta": str(args.output_meta),
        "output_summary": str(args.output_summary),
        "output_report": str(args.output_report),
        "total_seconds": meta[0]["total_seconds"],
    }, indent=2))


if __name__ == "__main__":
    main()
