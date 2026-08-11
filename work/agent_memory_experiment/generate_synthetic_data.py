#!/usr/bin/env python3
"""Generate deterministic synthetic agent-memory datasets.

The generated data is intentionally simple enough to inspect, but it includes
temporal updates, compression cues, and cross-agent reuse cases so retrieval
methods can be compared beyond toy exact matching.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path


USERS = ["Alice", "Bo", "Chen", "Dana", "Eli", "Faye", "Gita", "Hugo"]
PROJECTS = ["LoCoMo", "MemoryOS", "mem0", "Graphiti", "AutoGen", "LongMemEval"]
BACKENDS = ["Chroma", "Qdrant", "FAISS", "Neo4j", "SQLite", "Redis"]
LANGUAGES = ["Python", "TypeScript", "Java", "Go"]
METRICS = ["Recall@1", "Recall@3", "MRR", "temporal accuracy", "context token cost", "latency"]
AGENTS = ["planner", "retriever", "compressor", "shared_memory", "systems"]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def make_memory(memory_id: int, session_id: int, turn: int, day_offset: int, agent_id: str, user: str, text: str, entities: list[str]) -> dict:
    return {
        "id": f"m{memory_id:05d}",
        "session_id": f"s{session_id:04d}",
        "turn": turn,
        "date": (date(2026, 1, 1) + timedelta(days=day_offset)).isoformat(),
        "agent_id": agent_id,
        "user_id": user.lower(),
        "text": text,
        "entities": entities,
    }


def make_query(query_id: int, query: str, answer_ids: list[str], query_type: str) -> dict:
    return {
        "id": f"q{query_id:05d}",
        "query": query,
        "answer_memory_ids": answer_ids,
        "query_date": date(2026, 12, 31).isoformat(),
        "type": query_type,
    }


def generate(num_memories: int, seed: int) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    memories: list[dict] = []
    queries: list[dict] = []
    memory_id = 1
    query_id = 1
    session_id = 1

    while memory_id <= num_memories:
        user = rng.choice(USERS)
        project = rng.choice(PROJECTS)
        agent = rng.choice(AGENTS)
        pattern = (memory_id - 1) % 5

        if pattern == 0 and memory_id + 1 <= num_memories:
            old_backend, new_backend = rng.sample(BACKENDS, 2)
            old = make_memory(
                memory_id,
                session_id,
                1,
                rng.randint(1, 80),
                "retriever",
                user,
                f"{user}'s current memory backend preference for the {project} experiment is {old_backend}.",
                [user, project, old_backend, "memory backend"],
            )
            new = make_memory(
                memory_id + 1,
                session_id,
                2,
                rng.randint(160, 260),
                "retriever",
                user,
                f"{user}'s current memory backend preference for the {project} experiment is {new_backend}.",
                [user, project, new_backend, "memory backend"],
            )
            memories.extend([old, new])
            queries.append(
                make_query(
                    query_id,
                    f"What is {user}'s current memory backend preference for the {project} experiment?",
                    [new["id"]],
                    "temporal-update",
                )
            )
            memory_id += 2
            query_id += 1

        elif pattern == 2:
            language = rng.choice(LANGUAGES)
            memory = make_memory(
                memory_id,
                session_id,
                1,
                rng.randint(30, 300),
                "planner",
                user,
                f"{user} prefers {language} code examples when studying {project} agent memory experiments.",
                [user, language, project, "code examples"],
            )
            memories.append(memory)
            queries.append(
                make_query(
                    query_id,
                    f"Which programming language does {user} prefer for {project} memory experiments?",
                    [memory["id"]],
                    "single-hop",
                )
            )
            memory_id += 1
            query_id += 1

        elif pattern == 3:
            metric_a, metric_b = rng.sample(METRICS, 2)
            memory = make_memory(
                memory_id,
                session_id,
                1,
                rng.randint(60, 320),
                "analyst",
                user,
                f"The {project} validation run should report {metric_a} and {metric_b} for every retrieval method.",
                [project, metric_a, metric_b, "evaluation"],
            )
            memories.append(memory)
            queries.append(
                make_query(
                    query_id,
                    f"Which metrics should be reported for the {project} validation run?",
                    [memory["id"]],
                    "evaluation",
                )
            )
            memory_id += 1
            query_id += 1

        elif pattern == 4:
            memory = make_memory(
                memory_id,
                session_id,
                1,
                rng.randint(90, 340),
                "compressor",
                user,
                f"In {project}, old conversation turns should be summarized once access heat is high and raw token cost becomes expensive.",
                [project, "summary compression", "access heat", "token cost"],
            )
            memories.append(memory)
            queries.append(
                make_query(
                    query_id,
                    f"When should old conversation turns be compressed in {project}?",
                    [memory["id"]],
                    "compression",
                )
            )
            memory_id += 1
            query_id += 1

        else:
            memory = make_memory(
                memory_id,
                session_id,
                1,
                rng.randint(100, 340),
                "shared_memory",
                user,
                f"Cross-agent reuse for {project} is verified when agent A stores a useful fact and agent B retrieves it with permission checks.",
                [project, "cross-agent reuse", "agent A", "agent B", "permission checks"],
            )
            memories.append(memory)
            queries.append(
                make_query(
                    query_id,
                    f"How is cross-agent reuse verified for {project}?",
                    [memory["id"]],
                    "multi-agent",
                )
            )
            memory_id += 1
            query_id += 1

        session_id += 1

    return memories[:num_memories], queries


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic agent-memory JSONL data.")
    parser.add_argument("--num-memories", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()

    memories, queries = generate(args.num_memories, args.seed)
    memory_path = args.output_dir / f"synthetic_{args.num_memories}_memories.jsonl"
    query_path = args.output_dir / f"synthetic_{args.num_memories}_queries.jsonl"
    write_jsonl(memory_path, memories)
    write_jsonl(query_path, queries)
    print(json.dumps({"memories": str(memory_path), "queries": str(query_path), "num_queries": len(queries)}, indent=2))


if __name__ == "__main__":
    main()
