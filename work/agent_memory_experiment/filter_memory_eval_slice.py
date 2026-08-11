#!/usr/bin/env python3
"""Filter memory_eval JSONL files to an evidence-session slice.

This is useful for evaluating a small LLM extraction run, such as only D1,
without counting QA items from sessions that were never extracted.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


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


def evidence_ids(row: dict[str, Any]) -> list[str]:
    values = row.get("source_evidence_ids", [])
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, list):
        return []
    return [str(item) for item in values]


def in_slice(evidence: list[str], prefixes: tuple[str, ...], require_all: bool) -> bool:
    if not evidence:
        return False
    matches = [any(item.startswith(prefix + ":") or item == prefix for prefix in prefixes) for item in evidence]
    return all(matches) if require_all else any(matches)


def query_number(query_id: str) -> int | None:
    if len(query_id) < 2 or not query_id[1:].isdigit():
        return None
    return int(query_id[1:])


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter memory_eval files to selected LoCoMo evidence sessions.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--sessions", default="D1", help="Comma-separated session ids such as D1,D2.")
    parser.add_argument("--require-all-evidence-in-slice", action="store_true")
    parser.add_argument("--require-answer", action="store_true")
    parser.add_argument("--query-id-min", type=int, default=None)
    parser.add_argument("--query-id-max", type=int, default=None)
    parser.add_argument("--sample-id", default=None)
    args = parser.parse_args()

    prefixes = tuple(item.strip() for item in args.sessions.split(",") if item.strip())
    memories = read_jsonl(args.memories)
    queries = read_jsonl(args.queries)

    kept_memories = []
    for row in memories:
        if args.sample_id and str(row.get("sample_id", "")) != args.sample_id:
            continue
        if in_slice(evidence_ids(row), prefixes, require_all=False):
            kept_memories.append(row)
    kept_memory_ids = {row["id"] for row in kept_memories}
    kept_queries = []
    for query in queries:
        number = query_number(str(query.get("id", "")))
        if args.query_id_min is not None and (number is None or number < args.query_id_min):
            continue
        if args.query_id_max is not None and (number is None or number > args.query_id_max):
            continue
        if not in_slice(evidence_ids(query), prefixes, args.require_all_evidence_in_slice):
            continue
        row = dict(query)
        row["answer_memory_ids"] = [
            memory_id for memory_id in row.get("answer_memory_ids", [])
            if memory_id in kept_memory_ids
        ]
        if args.require_answer and not row["answer_memory_ids"]:
            continue
        kept_queries.append(row)

    memory_path = args.output_prefix.with_name(args.output_prefix.name + "_memories.jsonl")
    query_path = args.output_prefix.with_name(args.output_prefix.name + "_queries.jsonl")
    write_jsonl(memory_path, kept_memories)
    write_jsonl(query_path, kept_queries)
    print(json.dumps({
        "memories": str(memory_path),
        "queries": str(query_path),
        "num_memories": len(kept_memories),
        "num_queries": len(kept_queries),
        "sessions": prefixes,
    }, indent=2))


if __name__ == "__main__":
    main()
