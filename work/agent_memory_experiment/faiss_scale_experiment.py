#!/usr/bin/env python3
"""Run FAISS index-only scale stress tests with expanded memory banks."""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from faiss_prefilter_experiment import build_faiss_index, normalized_dense_vectors
from memory_eval import build_semantic_scorer, load_memories, load_queries


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_ints(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def expand_vectors(base_vectors, target_size: int, noise: float, seed: int):
    np = __import__("numpy")
    if target_size <= base_vectors.shape[0]:
        return base_vectors[:target_size].astype("float32", copy=True)

    rng = np.random.default_rng(seed)
    vectors = [base_vectors.astype("float32", copy=True)]
    remaining = target_size - base_vectors.shape[0]
    while remaining > 0:
        take = min(remaining, base_vectors.shape[0])
        source_indices = rng.integers(0, base_vectors.shape[0], size=take)
        distractors = base_vectors[source_indices].astype("float32", copy=True)
        if noise > 0:
            distractors = distractors + rng.normal(0.0, noise, size=distractors.shape).astype("float32")
        norms = np.linalg.norm(distractors, axis=1, keepdims=True)
        distractors = distractors / np.maximum(norms, 1e-12)
        vectors.append(distractors.astype("float32", copy=False))
        remaining -= take
    return np.concatenate(vectors, axis=0).astype("float32", copy=False)


def gold_index_sets(memories, queries) -> list[set[int]]:
    id_to_index = {memory.id: idx for idx, memory in enumerate(memories)}
    return [
        {id_to_index[memory_id] for memory_id in query.answer_memory_ids if memory_id in id_to_index}
        for query in queries
    ]


def candidate_recall(indices, gold_sets: list[set[int]]) -> float:
    answerable = 0
    hits = 0
    for row, gold in zip(indices, gold_sets):
        if not gold:
            continue
        answerable += 1
        if gold.intersection(int(idx) for idx in row if idx >= 0):
            hits += 1
    return hits / answerable if answerable else 0.0


def search_index(index, query_vectors, top_k: int):
    started = time.perf_counter()
    _, indices = index.search(query_vectors, top_k)
    seconds = time.perf_counter() - started
    return indices, seconds


def run_one(memory_vectors, query_vectors, gold_sets, *, index_type: str, nlist: int, nprobe: int, top_k: int):
    index, train_seconds, add_seconds = build_faiss_index(memory_vectors, index_type, nlist, nprobe)
    indices, query_seconds = search_index(index, query_vectors, top_k)
    recall = candidate_recall(indices, gold_sets)
    return {
        "index_type": index_type,
        "nlist": nlist if index_type == "ivf" else 0,
        "nprobe": nprobe if index_type == "ivf" else 0,
        "top_k": top_k,
        "train_seconds": train_seconds,
        "add_seconds": add_seconds,
        "query_seconds": query_seconds,
        "query_ms_per_query": query_seconds * 1000 / max(query_vectors.shape[0], 1),
        "candidate_gold_recall": recall,
    }


def write_report(path: Path, rows: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    lines = [
        "# FAISS Scale Stress Test",
        "",
        "本实验是 index-only stress test：在 LoCoMo10 的真实 BGE-M3 memory/query embedding 基础上，加入轻微扰动的 synthetic distractor vectors 扩展 memory bank，比较 FAISS Flat 与 IVF 的候选召回速度和 gold recall。",
        "该实验不重新执行 type-aware reranking，因此用于支持论文中的索引扩展性分析，不替代主检索准确率实验。",
        "",
        "## Setting",
        "",
        f"- Base memories: `{meta['base_memories']}`",
        f"- Queries: `{meta['num_queries']}`",
        f"- Embedding model: `{meta['embedding_model']}`",
        f"- Target memory sizes: `{meta['target_sizes']}`",
        f"- Top-k: `{meta['top_k']}`",
        f"- Distractor noise std: `{meta['noise']}`",
        "",
        "## Results",
        "",
        "| Memory Bank | Index | nlist | nprobe | Query Seconds | ms / Query | Candidate Gold Recall | Train Seconds | Add Seconds |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['memory_bank_size']} | {row['index_type']} | {row['nlist']} | {row['nprobe']} | "
            f"{row['query_seconds']:.4f} | {row['query_ms_per_query']:.3f} | {row['candidate_gold_recall']:.3f} | "
            f"{row['train_seconds']:.4f} | {row['add_seconds']:.4f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Flat index 是 exact upper-bound，candidate gold recall 通常最高，但查询成本随 memory bank 线性增长。",
        "- IVF 是真正 ANN；在更大 memory bank 中应优先观察 query seconds 是否低于 Flat，以及 candidate gold recall 是否保持在可接受范围。",
        "- 如果 IVF recall 明显下降，应提高 `nprobe`、增大 candidate top-k，或换 HNSW/IVF-PQ 等索引配置。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run FAISS index-only scale stress tests.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--target-sizes", default="2517,10000,25000,50000")
    parser.add_argument("--top-k", type=int, default=200)
    parser.add_argument("--nlist", type=int, default=128)
    parser.add_argument("--nprobes", default="8,32")
    parser.add_argument("--noise", type=float, default=0.03)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--semantic-backend", choices=["sentence-transformer"], default="sentence-transformer")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = load_memories(args.memories)
    queries = load_queries(args.queries)
    scorer_started = time.perf_counter()
    semantic_scorer = build_semantic_scorer(args, memories)
    prepare_queries = getattr(semantic_scorer, "prepare_queries", None)
    if callable(prepare_queries):
        prepare_queries(queries)
    scorer_seconds = time.perf_counter() - scorer_started
    base_memory_vectors, query_vectors = normalized_dense_vectors(semantic_scorer)
    gold_sets = gold_index_sets(memories, queries)

    rows: list[dict[str, Any]] = []
    for target_size in parse_ints(args.target_sizes):
        expanded = expand_vectors(base_memory_vectors, target_size, args.noise, args.seed + target_size)
        for index_type in ("flat", "ivf"):
            if index_type == "flat":
                row = run_one(expanded, query_vectors, gold_sets, index_type="flat", nlist=args.nlist, nprobe=0, top_k=args.top_k)
                rows.append({"memory_bank_size": expanded.shape[0], "scorer_seconds": scorer_seconds, **row})
            else:
                for nprobe in parse_ints(args.nprobes):
                    row = run_one(expanded, query_vectors, gold_sets, index_type="ivf", nlist=args.nlist, nprobe=nprobe, top_k=args.top_k)
                    rows.append({"memory_bank_size": expanded.shape[0], "scorer_seconds": scorer_seconds, **row})

    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, {
        "base_memories": len(memories),
        "num_queries": len(queries),
        "embedding_model": args.embedding_model,
        "target_sizes": args.target_sizes,
        "top_k": args.top_k,
        "noise": args.noise,
    })
    print(json.dumps({
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
        "rows": len(rows),
    }, indent=2))


if __name__ == "__main__":
    main()
