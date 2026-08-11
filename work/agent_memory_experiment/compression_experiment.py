#!/usr/bin/env python3
"""Build and evaluate compressed memory variants.

Variants:
- raw: original memory granularity.
- fact: one shorter fact-style record per original memory.
- summary: grouped memory blocks with query evidence ids remapped to block ids.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def token_count(text: str) -> int:
    return len(tokenize(text))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def fact_text(memory: dict[str, Any]) -> str:
    text = memory["text"]
    entities = memory.get("entities", [])
    if "current memory backend preference" in text and len(entities) >= 3:
        return f"{entities[0]} {entities[1]} backend {entities[2]}"
    if "prefers" in text and "code examples" in text and len(entities) >= 3:
        return f"{entities[0]} prefers {entities[1]} for {entities[2]}"
    if "validation run should report" in text and len(entities) >= 3:
        return f"{entities[0]} metrics {entities[1]} {entities[2]}"
    if "old conversation turns should be summarized" in text and entities:
        return f"{entities[0]} compress old turns when heat and token cost are high"
    if "Cross-agent reuse" in text and entities:
        return f"{entities[0]} cross-agent reuse needs agent A agent B permission checks"
    return " ".join(tokenize(text)[:12])


def build_fact_variant(memories: list[dict[str, Any]], queries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    id_map = {}
    out_memories = []
    for idx, memory in enumerate(memories, start=1):
        new_id = f"fact_{idx:05d}"
        id_map[memory["id"]] = new_id
        row = dict(memory)
        row["id"] = new_id
        row["text"] = fact_text(memory)
        row["compression_variant"] = "fact"
        row["source_memory_ids"] = [memory["id"]]
        out_memories.append(row)
    return out_memories, remap_queries(queries, id_map), id_map


def build_summary_variant(memories: list[dict[str, Any]], queries: list[dict[str, Any]], group_size: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    id_map = {}
    out_memories = []
    sorted_memories = sorted(memories, key=lambda row: (row.get("session_id", ""), int(row.get("turn", 0)), row.get("id", "")))
    for group_idx, start in enumerate(range(0, len(sorted_memories), group_size), start=1):
        group = sorted_memories[start:start + group_size]
        new_id = f"summary_{group_idx:05d}"
        for memory in group:
            id_map[memory["id"]] = new_id
        entity_items = []
        for memory in group:
            entity_items.extend(memory.get("entities", []))
        entities = sorted(set(entity_items))
        snippets = [fact_text(memory) for memory in group]
        row = {
            "id": new_id,
            "session_id": f"summary_group_{group_idx:05d}",
            "turn": 1,
            "date": max(memory["date"] for memory in group),
            "agent_id": "summary_compressor",
            "user_id": "mixed",
            "text": " | ".join(snippets),
            "entities": entities,
            "compression_variant": "summary",
            "source_memory_ids": [memory["id"] for memory in group],
        }
        out_memories.append(row)
    return out_memories, remap_queries(queries, id_map), id_map


def remap_queries(queries: list[dict[str, Any]], id_map: dict[str, str]) -> list[dict[str, Any]]:
    out_queries = []
    for query in queries:
        row = dict(query)
        remapped = []
        for memory_id in query["answer_memory_ids"]:
            new_id = id_map.get(memory_id)
            if new_id and new_id not in remapped:
                remapped.append(new_id)
        row["answer_memory_ids"] = remapped
        out_queries.append(row)
    return out_queries


def storage_stats(memories: list[dict[str, Any]], raw_tokens: int, variant: str) -> dict[str, Any]:
    total_tokens = sum(token_count(memory["text"]) for memory in memories)
    return {
        "variant": variant,
        "num_memories": len(memories),
        "total_tokens": total_tokens,
        "avg_tokens_per_memory": total_tokens / max(len(memories), 1),
        "token_ratio_vs_raw": total_tokens / max(raw_tokens, 1),
    }


def run_eval(
    memory_path: Path,
    query_path: Path,
    output_dir: Path,
    semantic_backend: str,
    embedding_model: str,
    embedding_batch_size: int,
    embedding_cache_dir: Path,
    no_embedding_cache: bool,
    persona_boost_weight: float,
    persona_boost_query_types: str,
    importance_weight: float,
    local_files_only: bool,
) -> None:
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "memory_eval.py"),
        "--memories",
        str(memory_path),
        "--queries",
        str(query_path),
        "--output-dir",
        str(output_dir),
        "--semantic-backend",
        semantic_backend,
        "--embedding-model",
        embedding_model,
        "--embedding-batch-size",
        str(embedding_batch_size),
        "--embedding-cache-dir",
        str(embedding_cache_dir),
        "--persona-boost-weight",
        str(persona_boost_weight),
        "--persona-boost-query-types",
        persona_boost_query_types,
        "--importance-weight",
        str(importance_weight),
    ]
    if no_embedding_cache:
        cmd.append("--no-embedding-cache")
    if local_files_only:
        cmd.append("--local-files-only")
    subprocess.run(cmd, check=True)


def read_summary(path: Path, variant: str) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row["variant"] = variant
            rows.append(row)
    return rows


def write_report(path: Path, storage_rows: list[dict[str, Any]], metric_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Memory Compression Experiment",
        "",
        "This report compares retrieval quality and storage cost across raw, fact, and summary memory variants.",
        "",
        "## Storage Cost",
        "",
        "| Variant | Memories | Total Tokens | Avg Tokens/Memory | Token Ratio vs Raw |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in storage_rows:
        lines.append(
            f"| {row['variant']} | {row['num_memories']} | {row['total_tokens']} | "
            f"{row['avg_tokens_per_memory']:.2f} | {row['token_ratio_vs_raw']:.3f} |"
        )
    lines.extend([
        "",
        "## Retrieval Metrics",
        "",
        "| Variant | Method | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in metric_rows:
        lines.append(
            f"| {row['variant']} | {row['method']} | {float(row['recall@1']):.3f} | "
            f"{float(row['recall@3']):.3f} | {float(row['recall@5']):.3f} | {float(row['mrr']):.3f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `fact` keeps memory granularity but shortens each record, so it tests whether compact factual memory can preserve retrieval quality while reducing token cost.",
        "- `summary` merges several memories into one block, so it tests a more aggressive compression tradeoff: fewer memory items and fewer tokens, but less precise retrieval targets.",
        "- A useful compression method should reduce `token_ratio_vs_raw` while keeping `Recall@3` and `MRR` close to the raw baseline.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run raw/fact/summary memory compression experiments.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--summary-group-size", type=int, default=5)
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    raw_memories = read_jsonl(args.memories)
    raw_queries = read_jsonl(args.queries)
    raw_tokens = sum(token_count(memory["text"]) for memory in raw_memories)

    variants = {
        "raw": (raw_memories, raw_queries),
    }
    fact_memories, fact_queries, _ = build_fact_variant(raw_memories, raw_queries)
    summary_memories, summary_queries, _ = build_summary_variant(raw_memories, raw_queries, args.summary_group_size)
    variants["fact"] = (fact_memories, fact_queries)
    variants["summary"] = (summary_memories, summary_queries)

    storage_rows = []
    metric_rows = []
    for variant, (memories, queries) in variants.items():
        variant_dir = args.output_dir / variant
        memory_path = variant_dir / "memories.jsonl"
        query_path = variant_dir / "queries.jsonl"
        write_jsonl(memory_path, memories)
        write_jsonl(query_path, queries)
        storage_rows.append(storage_stats(memories, raw_tokens, variant))
        run_eval(
            memory_path,
            query_path,
            variant_dir / "eval",
            args.semantic_backend,
            args.embedding_model,
            args.embedding_batch_size,
            args.embedding_cache_dir,
            args.no_embedding_cache,
            args.persona_boost_weight,
            args.persona_boost_query_types,
            args.importance_weight,
            args.local_files_only,
        )
        metric_rows.extend(read_summary(variant_dir / "eval" / "summary.csv", variant))

    write_csv(args.output_dir / "compression_storage.csv", storage_rows)
    write_csv(args.output_dir / "compression_metrics.csv", metric_rows)
    write_report(args.output_dir / "compression_report.md", storage_rows, metric_rows)
    print(json.dumps({"output_dir": str(args.output_dir), "variants": sorted(variants)}, indent=2))


if __name__ == "__main__":
    main()
