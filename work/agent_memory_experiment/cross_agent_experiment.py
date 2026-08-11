#!/usr/bin/env python3
"""Evaluate cross-agent memory reuse with permission-scoped memory pools."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def token_count(text: str) -> int:
    return len(text.split())


def build_query_text(memory: dict) -> str:
    entities = [entity for entity in memory.get("entities", []) if entity]
    topic = ", ".join(entities[:3]) if entities else memory.get("session_id", "the prior task")
    return f"What useful fact can agent B reuse from agent A about {topic}?"


def build_cross_agent_dataset(memories: list[dict], max_queries: int | None) -> tuple[list[dict], list[dict], list[dict]]:
    source = memories[:max_queries] if max_queries else memories
    shared = []
    private_noise = []
    queries = []

    for index, memory in enumerate(source, start=1):
        shared_id = f"shared_{memory['id']}"
        private_id = f"private_noise_{memory['id']}"
        shared_text = (
            f"Agent A shared with agent B: {memory['text']} "
            "This fact is marked reusable for cross-agent task transfer."
        )
        private_text = shared_text
        shared_entities = list(dict.fromkeys([*memory.get("entities", []), "agent A", "agent B", "shared memory"]))

        shared.append({
            **memory,
            "id": shared_id,
            "agent_id": "agent_a",
            "text": shared_text,
            "entities": shared_entities,
            "visibility": "shared",
            "source_memory_id": memory["id"],
        })
        private_noise.append({
            **memory,
            "id": private_id,
            "agent_id": "agent_b",
            "text": private_text,
            "entities": shared_entities,
            "visibility": "private",
            "source_memory_id": memory["id"],
        })
        queries.append({
            "id": f"cross_q{index:05d}",
            "query": build_query_text(memory),
            "answer_memory_ids": [shared_id],
            "query_date": memory["date"],
            "type": "cross-agent-reuse",
            "requesting_agent_id": "agent_b",
        })

    return shared, private_noise, queries


def run_eval(
    eval_script: Path,
    memories_path: Path,
    queries_path: Path,
    output_dir: Path,
    half_life_days: float,
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
    command = [
        sys.executable,
        str(eval_script),
        "--memories",
        str(memories_path),
        "--queries",
        str(queries_path),
        "--output-dir",
        str(output_dir),
        "--half-life-days",
        str(half_life_days),
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
        command.append("--no-embedding-cache")
    if local_files_only:
        command.append("--local-files-only")
    subprocess.run(command, check=True)


def load_strategy_metrics(strategy: str, result_dir: Path, num_memories: int, total_tokens: int) -> list[dict]:
    rows = []
    for row in read_csv(result_dir / "summary.csv"):
        rows.append({
            "strategy": strategy,
            "method": row["method"],
            "num_memories": num_memories,
            "total_tokens": total_tokens,
            "recall@1": row["recall@1"],
            "recall@3": row["recall@3"],
            "recall@5": row["recall@5"],
            "mrr": row["mrr"],
        })
    return rows


def fmt(value: str | float) -> str:
    return f"{float(value):.3f}"


def write_report(path: Path, metrics: list[dict], num_queries: int) -> None:
    lines = [
        "# Cross-Agent Memory Reuse Report",
        "",
        f"Queries: {num_queries}",
        "",
        "## Strategy Meaning",
        "",
        "- `private_only`: agent B only sees its private memory pool; relevant agent A memories are unavailable.",
        "- `shared_allowed`: agent B can retrieve authorized memories shared by agent A.",
        "- `shared_plus_private_noise`: authorized shared memories are retrieved with same-topic private distractors present.",
        "- `unfiltered_private_first`: same memories as mixed retrieval, but private distractors are ranked first on ties to simulate missing permission filtering.",
        "",
        "## Metrics",
        "",
        "| Strategy | Method | Memories | Tokens | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metrics:
        lines.append(
            f"| {row['strategy']} | {row['method']} | {row['num_memories']} | {row['total_tokens']} | "
            f"{fmt(row['recall@1'])} | {fmt(row['recall@3'])} | {fmt(row['recall@5'])} | {fmt(row['mrr'])} |"
        )

    by_key = {(row["strategy"], row["method"]): row for row in metrics}
    private = by_key.get(("private_only", "time_aware"))
    shared = by_key.get(("shared_allowed", "time_aware"))
    mixed = by_key.get(("shared_plus_private_noise", "time_aware"))
    unfiltered = by_key.get(("unfiltered_private_first", "time_aware"))
    lines.extend(["", "## Interpretation", ""])
    if private and shared and mixed:
        gain = float(shared["recall@1"]) - float(private["recall@1"])
        noise_drop = float(shared["recall@1"]) - float(mixed["recall@1"])
        lines.append(f"- Shared access improves time-aware Recall@1 by {gain:.3f} over private-only retrieval.")
        lines.append(f"- Adding same-topic private noise changes time-aware Recall@1 by {-noise_drop:.3f} versus shared-only retrieval.")
    if shared and unfiltered:
        permission_drop = float(shared["recall@1"]) - float(unfiltered["recall@1"])
        lines.append(f"- The unfiltered private-first condition loses {permission_drop:.3f} time-aware Recall@1, showing why permission filtering must happen before ranking.")
    lines.append("- This isolates the project question: cross-agent reuse is useful only when the memory layer enforces an explicit shared/authorized scope.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    base = Path(__file__).resolve().parent
    eval_script = base / "memory_eval.py"
    source_memories = read_jsonl(args.memories)
    shared, private_noise, queries = build_cross_agent_dataset(source_memories, args.max_queries)
    if not shared:
        raise ValueError("No source memories were available for cross-agent evaluation.")

    datasets_dir = args.output_dir / "datasets"
    strategies = {
        "private_only": private_noise,
        "shared_allowed": shared,
        "shared_plus_private_noise": shared + private_noise,
        "unfiltered_private_first": private_noise + shared,
    }
    queries_path = datasets_dir / "cross_agent_queries.jsonl"
    write_jsonl(queries_path, queries)

    all_metrics = []
    for strategy, strategy_memories in strategies.items():
        memories_path = datasets_dir / f"{strategy}_memories.jsonl"
        result_dir = args.output_dir / strategy
        write_jsonl(memories_path, strategy_memories)
        run_eval(
            eval_script,
            memories_path,
            queries_path,
            result_dir,
            args.half_life_days,
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
        all_metrics.extend(load_strategy_metrics(
            strategy,
            result_dir,
            len(strategy_memories),
            sum(token_count(row["text"]) for row in strategy_memories),
        ))

    write_csv(args.output_dir / "cross_agent_metrics.csv", all_metrics)
    write_report(args.output_dir / "cross_agent_report.md", all_metrics, len(queries))
    print(str(args.output_dir / "cross_agent_report.md"))


def build_parser() -> argparse.ArgumentParser:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run cross-agent memory reuse evaluation.")
    parser.add_argument("--memories", type=Path, default=base / "data" / "synthetic_100_memories.jsonl")
    parser.add_argument("--output-dir", type=Path, default=base / "results" / "cross_agent_100")
    parser.add_argument("--max-queries", type=int)
    parser.add_argument("--half-life-days", type=float, default=45.0)
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    return parser


if __name__ == "__main__":
    run(build_parser().parse_args())
