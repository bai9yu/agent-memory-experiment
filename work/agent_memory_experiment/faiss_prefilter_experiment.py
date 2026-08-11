#!/usr/bin/env python3
"""Evaluate FAISS candidate prefiltering before memory reranking."""

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


def normalized_dense_vectors(semantic_scorer):
    if not hasattr(semantic_scorer, "memory_vectors") or not hasattr(semantic_scorer, "query_vectors"):
        raise RuntimeError("FAISS prefilter requires sentence-transformer semantic scorer with dense vectors.")
    np = semantic_scorer.np
    memory_vectors = semantic_scorer.memory_vectors.astype("float32", copy=False)
    query_vectors = np.stack(list(semantic_scorer.query_vectors.values())).astype("float32", copy=False)
    memory_vectors = np.nan_to_num(memory_vectors, nan=0.0, posinf=0.0, neginf=0.0)
    query_vectors = np.nan_to_num(query_vectors, nan=0.0, posinf=0.0, neginf=0.0)
    memory_norms = np.linalg.norm(memory_vectors, axis=1, keepdims=True)
    query_norms = np.linalg.norm(query_vectors, axis=1, keepdims=True)
    memory_vectors = memory_vectors / np.maximum(memory_norms, 1e-12)
    query_vectors = query_vectors / np.maximum(query_norms, 1e-12)
    return memory_vectors.astype("float32"), query_vectors.astype("float32")


def build_faiss_index(memory_vectors, index_type: str, nlist: int, nprobe: int):
    import faiss

    dimension = memory_vectors.shape[1]
    if index_type == "flat":
        index = faiss.IndexFlatIP(dimension)
        train_seconds = 0.0
    elif index_type == "ivf":
        quantizer = faiss.IndexFlatIP(dimension)
        nlist = max(1, min(nlist, memory_vectors.shape[0]))
        index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
        train_started = time.perf_counter()
        index.train(memory_vectors)
        train_seconds = time.perf_counter() - train_started
        index.nprobe = max(1, min(nprobe, nlist))
    else:
        raise ValueError(f"Unsupported FAISS index type: {index_type}")

    add_started = time.perf_counter()
    index.add(memory_vectors)
    add_seconds = time.perf_counter() - add_started
    return index, train_seconds, add_seconds


def query_faiss_index(index, query_vectors, max_limit: int):
    limit = min(max_limit, index.ntotal)
    query_started = time.perf_counter()
    _, indices = index.search(query_vectors, limit)
    query_seconds = time.perf_counter() - query_started
    candidate_indices = [
        [int(idx) for idx in row if idx >= 0]
        for row in indices
    ]
    return candidate_indices, query_seconds


def candidate_recall_at_pool(candidate_indices: list[list[int]], memories, queries) -> dict[str, float]:
    id_to_index = {memory.id: idx for idx, memory in enumerate(memories)}
    recall_hits = 0
    answerable = 0
    for indices, query in zip(candidate_indices, queries):
        gold_indices = {id_to_index[memory_id] for memory_id in query.answer_memory_ids if memory_id in id_to_index}
        if not gold_indices:
            continue
        answerable += 1
        if gold_indices.intersection(indices):
            recall_hits += 1
    return {
        "candidate_pool_gold_recall": recall_hits / answerable if answerable else 0.0,
        "candidate_pool_answerable_queries": answerable,
    }


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
        candidates = [memories[idx] for idx in indices[:candidate_limit]]
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
        **candidate_recall_at_pool([indices[:candidate_limit] for indices in candidate_indices], memories, queries),
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
        "# FAISS Candidate Prefilter Experiment",
        "",
        "本实验使用 BGE-M3 embedding + FAISS 先做向量候选召回，再在候选集合上执行 type-aware 重排。",
        "`flat` 是 exact inner-product index；`ivf` 是 ANN inverted-file index，可通过 `nlist/nprobe` 控制速度与召回折中。",
        "",
        "## Index Setting",
        "",
        f"- Backend: `{index_meta['semantic_backend']}`",
        f"- Embedding model: `{index_meta['embedding_model']}`",
        f"- FAISS index: `{index_meta['index_type']}`",
        f"- Metric: `inner_product_on_l2_normalized_vectors`",
        f"- nlist: `{index_meta['nlist']}`",
        f"- nprobe: `{index_meta['nprobe']}`",
        f"- Memories: `{index_meta['num_memories']}`",
        f"- Queries: `{index_meta['num_queries']}`",
        "",
        "## Index / Recall Stage",
        "",
        "| Stage | Seconds | ms / Query |",
        "|---|---:|---:|",
        f"| scorer_init_and_query_cache | {index_meta['scorer_init_seconds']:.4f} | {index_meta['scorer_init_seconds'] * 1000 / index_meta['num_queries']:.2f} |",
        f"| train_index | {index_meta['train_index_seconds']:.4f} | - |",
        f"| add_vectors | {index_meta['add_vectors_seconds']:.4f} | - |",
        f"| query_index | {index_meta['query_index_seconds']:.4f} | {index_meta['query_index_seconds'] * 1000 / index_meta['num_queries']:.2f} |",
        "",
        "## Runtime And Candidate Recall",
        "",
        "| Candidate Limit | Candidate Gold Recall | Avg Candidates | Rerank Seconds | End-to-End Seconds | Speedup vs Full Ranking |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in meta_rows:
        end_to_end = index_meta["query_index_seconds"] + row["rerank_seconds"]
        speedup = ""
        if full_baseline_seconds and end_to_end > 0:
            speedup = f"{full_baseline_seconds / end_to_end:.2f}x"
        lines.append(
            f"| {row['candidate_limit']} | {row['candidate_pool_gold_recall']:.3f} | {row['avg_candidates']:.1f} | "
            f"{row['rerank_seconds']:.4f} | {end_to_end:.4f} | {speedup} |"
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
        "- FAISS 使候选召回具备标准向量索引实现，适合写入论文效率实验。",
        "- `flat` 可作为 exact upper-bound；`ivf` 用于报告 ANN 速度-召回折中。",
        "- 如果 IVF 的 candidate gold recall 明显下降，需要提高 `nprobe` 或增大候选池。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FAISS candidate prefilter experiments.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--candidate-limits", default="50,100,200,500")
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--semantic-backend", choices=["sentence-transformer"], default="sentence-transformer")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--index-type", choices=["flat", "ivf"], default="ivf")
    parser.add_argument("--nlist", type=int, default=64)
    parser.add_argument("--nprobe", type=int, default=8)
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
    scorer_started = time.perf_counter()
    semantic_scorer = build_semantic_scorer(args, memories)
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    scorer_init_seconds = time.perf_counter() - scorer_started

    memory_vectors, query_vectors = normalized_dense_vectors(semantic_scorer)
    limits = parse_candidate_limits(args.candidate_limits)
    index, train_index_seconds, add_vectors_seconds = build_faiss_index(memory_vectors, args.index_type, args.nlist, args.nprobe)
    candidate_indices, query_index_seconds = query_faiss_index(index, query_vectors, max(limits))

    methods = ("keyword", "hybrid", "time_aware")
    if args.type_awareness_weight > 0:
        methods = methods + ("type_aware",)
    persona_boost_query_types = parse_query_types(args.persona_boost_query_types)

    summary_rows = []
    meta_rows = []
    for limit in limits:
        query_metric_rows, meta = evaluate_limit(
            candidate_limit=limit,
            candidate_indices=candidate_indices,
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
        "semantic_backend": semantic_scorer.name,
        "embedding_model": args.embedding_model,
        "index_type": args.index_type,
        "nlist": args.nlist,
        "nprobe": args.nprobe,
        "num_queries": len(queries),
        "num_memories": len(memories),
        "scorer_init_seconds": scorer_init_seconds,
        "train_index_seconds": train_index_seconds,
        "add_vectors_seconds": add_vectors_seconds,
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
        "index": f"faiss_{args.index_type}",
    }, indent=2))


if __name__ == "__main__":
    main()
