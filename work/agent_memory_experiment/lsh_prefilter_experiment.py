#!/usr/bin/env python3
"""Evaluate dependency-free LSH candidate prefiltering before reranking."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from memory_eval import (
    HashSemanticScorer,
    aggregate_metrics,
    build_idf,
    build_importance_scores,
    build_memory_tokens,
    cosine,
    hashed_vector,
    known_personas,
    load_memories,
    load_queries,
    metrics_for_ranked,
    parse_query_types,
    rank_all_methods,
    tokenize,
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


def projection_sign(dim: str, table_idx: int, bit_idx: int) -> int:
    digest = hashlib.blake2b(f"{dim}:{table_idx}:{bit_idx}".encode("utf-8"), digest_size=1).digest()
    return 1 if digest[0] & 1 else -1


def lsh_signature(vector: Counter[str], table_idx: int, num_bits: int) -> int:
    signature = 0
    for bit_idx in range(num_bits):
        score = 0.0
        for dim, value in vector.items():
            score += value * projection_sign(dim, table_idx, bit_idx)
        if score >= 0:
            signature |= 1 << bit_idx
    return signature


def hamming_neighbors(signature: int, num_bits: int, radius: int) -> list[int]:
    if radius <= 0:
        return [signature]
    neighbors = [signature]
    if radius >= 1:
        neighbors.extend(signature ^ (1 << bit_idx) for bit_idx in range(num_bits))
    if radius >= 2:
        for left in range(num_bits):
            for right in range(left + 1, num_bits):
                neighbors.append(signature ^ (1 << left) ^ (1 << right))
    return neighbors


class RandomHyperplaneLSH:
    def __init__(self, memory_vectors: list[Counter[str]], num_tables: int, num_bits: int):
        self.memory_vectors = memory_vectors
        self.num_tables = num_tables
        self.num_bits = num_bits
        self.tables: list[dict[int, list[int]]] = []
        for table_idx in range(num_tables):
            buckets: dict[int, list[int]] = defaultdict(list)
            for memory_idx, vector in enumerate(memory_vectors):
                buckets[lsh_signature(vector, table_idx, num_bits)].append(memory_idx)
            self.tables.append(dict(buckets))

    def query_pool(self, query_vector: Counter[str], probe_radius: int) -> list[int]:
        candidates: set[int] = set()
        for table_idx, buckets in enumerate(self.tables):
            signature = lsh_signature(query_vector, table_idx, self.num_bits)
            for neighbor in hamming_neighbors(signature, self.num_bits, probe_radius):
                candidates.update(buckets.get(neighbor, ()))
        return list(candidates)


def ranked_candidate_indices(
    *,
    lsh_index: RandomHyperplaneLSH,
    memory_vectors: list[Counter[str]],
    query_vector: Counter[str],
    candidate_limit: int,
    probe_radius: int,
) -> tuple[list[int], int]:
    pool = lsh_index.query_pool(query_vector, probe_radius)
    scored = [(idx, cosine(query_vector, memory_vectors[idx])) for idx in pool]
    scored.sort(key=lambda item: item[1], reverse=True)
    return [idx for idx, _ in scored[:candidate_limit]], len(pool)


def evaluate_limit(
    *,
    candidate_limit: int,
    candidate_indices: list[list[int]],
    raw_pool_sizes: list[int],
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
        if not candidates:
            for method in methods:
                query_metric_rows.append(metrics_for_ranked(query, method, [], k_values=(1, 3, 5)))
            continue
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
        "avg_lsh_pool": statistics.mean(raw_pool_sizes) if raw_pool_sizes else 0.0,
        "avg_candidates": total_candidates / max(len(queries), 1),
        "empty_candidate_queries": sum(1 for indices in candidate_indices if not indices),
        "rerank_seconds": seconds,
        "rerank_milliseconds_per_query": seconds * 1000 / max(len(queries), 1),
    }
    return query_metric_rows, meta


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    meta_rows: list[dict[str, Any]],
    index_meta: dict[str, Any],
    full_baseline_seconds: float | None,
) -> None:
    by_limit_method = {(row["candidate_limit"], row["method"]): row for row in summary_rows}
    lines = [
        "# LSH Candidate Prefilter Experiment",
        "",
        "本实验使用 dependency-free hash embedding + random-hyperplane LSH 先做近似候选召回，再在候选集合上执行重排。",
        "它是一个可复现的 ANN-style 索引基线，用于补充效率实验；由于 embedding 不是 BGE-M3，不能直接替代 BGE 主结果。",
        "",
        "## Index Setting",
        "",
        f"- Tables: `{index_meta['num_tables']}`",
        f"- Bits per table: `{index_meta['num_bits']}`",
        f"- Probe radius: `{index_meta['probe_radius']}`",
        f"- Memories: `{index_meta['num_memories']}`",
        f"- Queries: `{index_meta['num_queries']}`",
        "",
        "## Index / Recall Stage",
        "",
        "| Stage | Seconds | ms / Query |",
        "|---|---:|---:|",
        f"| vectorize_memories | {index_meta['vectorize_memories_seconds']:.4f} | - |",
        f"| build_lsh_index | {index_meta['build_index_seconds']:.4f} | - |",
        f"| query_lsh_and_rank_pool | {index_meta['query_index_seconds']:.4f} | {index_meta['query_index_seconds'] * 1000 / index_meta['num_queries']:.2f} |",
        "",
        "## Runtime",
        "",
        "| Candidate Limit | Avg LSH Pool | Avg Candidates | Empty Queries | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in meta_rows:
        end_to_end = index_meta["query_index_seconds"] + row["rerank_seconds"]
        speedup = ""
        if full_baseline_seconds and end_to_end > 0:
            speedup = f"{full_baseline_seconds / end_to_end:.2f}x"
        lines.append(
            f"| {row['candidate_limit']} | {row['avg_lsh_pool']:.1f} | {row['avg_candidates']:.1f} | "
            f"{row['empty_candidate_queries']} | {row['rerank_seconds']:.4f} | {end_to_end:.4f} | {speedup} |"
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
        "- LSH 给出了一个无需安装 FAISS/sklearn 的近似索引实验入口。",
        "- 如果 LSH 准确率低于 BGE exact top-N，说明当前主要瓶颈不是索引结构，而是近似召回 embedding 的表达能力。",
        "- 论文版建议继续加入 BGE-M3 + FAISS/HNSW，并报告 ANN recall、构建时间、查询时间和端到端 MRR。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LSH ANN-style candidate prefilter experiments.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--candidate-limits", default="50,100,200,500")
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--num-tables", type=int, default=12)
    parser.add_argument("--num-bits", type=int, default=8)
    parser.add_argument("--probe-radius", type=int, default=1)
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--type-awareness-weight", type=float, default=0.0)
    parser.add_argument("--full-baseline-seconds", type=float, default=None)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-meta", type=Path, required=True)
    parser.add_argument("--output-index-meta", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = load_queries(args.queries)

    vectorize_started = time.perf_counter()
    memory_vectors = [hashed_vector(tokenize(memory.text)) for memory in memories]
    query_vectors = [hashed_vector(tokenize(query.query)) for query in queries]
    vectorize_memories_seconds = time.perf_counter() - vectorize_started

    build_started = time.perf_counter()
    lsh_index = RandomHyperplaneLSH(memory_vectors, args.num_tables, args.num_bits)
    build_index_seconds = time.perf_counter() - build_started

    limits = parse_candidate_limits(args.candidate_limits)
    max_limit = max(limits)
    query_started = time.perf_counter()
    top_indices: list[list[int]] = []
    raw_pool_sizes: list[int] = []
    for query_vector in query_vectors:
        indices, pool_size = ranked_candidate_indices(
            lsh_index=lsh_index,
            memory_vectors=memory_vectors,
            query_vector=query_vector,
            candidate_limit=max_limit,
            probe_radius=args.probe_radius,
        )
        top_indices.append(indices)
        raw_pool_sizes.append(pool_size)
    query_index_seconds = time.perf_counter() - query_started

    semantic_scorer = HashSemanticScorer(memories)
    methods = ("keyword", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)

    summary_rows = []
    meta_rows = []
    for limit in limits:
        limited_indices = [indices[:limit] for indices in top_indices]
        query_metric_rows, meta = evaluate_limit(
            candidate_limit=limit,
            candidate_indices=limited_indices,
            raw_pool_sizes=raw_pool_sizes,
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
        "num_tables": args.num_tables,
        "num_bits": args.num_bits,
        "probe_radius": args.probe_radius,
        "vectorize_memories_seconds": vectorize_memories_seconds,
        "build_index_seconds": build_index_seconds,
        "query_index_seconds": query_index_seconds,
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
        "index": "random_hyperplane_lsh_hash_embedding",
    }, indent=2))


if __name__ == "__main__":
    main()
