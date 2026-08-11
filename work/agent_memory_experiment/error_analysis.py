#!/usr/bin/env python3
"""Analyze top-1 retrieval errors for agent-memory experiments."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


INTENT_PATTERNS = (
    ("identity", re.compile(r"\b(identity|identify|transgender|who is|who was)\b", re.IGNORECASE)),
    ("relationship", re.compile(r"\b(relationship|status|married|husband|wife|partner|single|dating|family)\b", re.IGNORECASE)),
    ("temporal", re.compile(r"\b(when|date|time|how long|last|yesterday|today|recently|summer)\b", re.IGNORECASE)),
    ("activity", re.compile(r"\b(activity|activities|hobby|hobbies|instrument|play|playing|run|running|race|camp|camping|swim|swimming|music|paint|painting|workout|yoga)\b", re.IGNORECASE)),
    ("preference", re.compile(r"\b(like|likes|enjoy|favorite|prefer|love|value)\b", re.IGNORECASE)),
    ("career_education", re.compile(r"\b(career|field|fields|pursue|education|educaton|study|school|class|job|work)\b", re.IGNORECASE)),
    ("location", re.compile(r"\b(where|move|moved|from|place|location)\b", re.IGNORECASE)),
    ("causal_emotion", re.compile(r"\b(why|how did|feel|feels|realize|realized|learn|learned|support|supported)\b", re.IGNORECASE)),
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def classify_intent(query: str) -> str:
    for label, pattern in INTENT_PATTERNS:
        if pattern.search(query):
            return label
    return "other"


def query_person_names(query: str, memories: list[dict[str, Any]]) -> set[str]:
    names = {str(row.get("agent_id", "")).strip() for row in memories if row.get("agent_id")}
    lowered = {name.lower(): name for name in names}
    query_lower = query.lower()
    return {name for key, name in lowered.items() if key and re.search(rf"\b{re.escape(key)}\b", query_lower)}


def has_person(memory: dict[str, Any] | None, names: set[str]) -> bool:
    if not memory or not names:
        return True
    text = str(memory.get("text", "")).lower()
    speaker = str(memory.get("agent_id", "")).lower()
    return any(name.lower() == speaker or name.lower() in text for name in names)


def primary_reason(
    query: dict[str, Any],
    top_row: dict[str, str] | None,
    top_memory: dict[str, Any] | None,
    gold_memories: list[dict[str, Any]],
    first_rank: int,
    all_memories: list[dict[str, Any]],
) -> str:
    if first_rank == 0:
        return "gold_not_retrieved"
    if first_rank > 20:
        return "gold_below_top20"
    names = query_person_names(str(query.get("query", "")), all_memories)
    if names and not has_person(top_memory, names):
        return "persona_confusion"

    top_type = str((top_memory or {}).get("memory_type", "unknown"))
    gold_types = {str(memory.get("memory_type", "unknown")) for memory in gold_memories}
    if gold_types and top_type not in gold_types:
        return "memory_type_mismatch"

    intent = classify_intent(str(query.get("query", "")))
    if intent == "temporal":
        return "temporal_neighbor"
    if intent in {"activity", "preference", "career_education", "relationship", "identity"}:
        return f"{intent}_neighbor"
    if top_row and float(top_row.get("semantic_score", 0.0) or 0.0) > 0.75:
        return "semantic_neighbor"
    return "other"


def build_top_rows(rankings: list[dict[str, str]], method: str) -> dict[str, dict[str, str]]:
    top_rows = {}
    for row in rankings:
        if row.get("method") != method:
            continue
        query_id = row["query_id"]
        if query_id not in top_rows:
            top_rows[query_id] = row
    return top_rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify top-1 retrieval errors.")
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--method", default="type_aware")
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--summary-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    queries = {row["id"]: row for row in read_jsonl(args.queries)}
    memories = {row["id"]: row for row in read_jsonl(args.memories)}
    all_memories = list(memories.values())
    rankings = read_csv(args.rankings)
    metrics = [row for row in read_csv(args.per_query) if row.get("method") == args.method]
    top_rows = build_top_rows(rankings, args.method)

    error_rows = []
    for metric in metrics:
        if float(metric.get("recall@1", "0") or 0) >= 1.0:
            continue
        query = queries[metric["query_id"]]
        top_row = top_rows.get(metric["query_id"])
        top_memory = memories.get(top_row["memory_id"]) if top_row else None
        gold_memories = [memories[memory_id] for memory_id in query.get("answer_memory_ids", []) if memory_id in memories]
        first_rank = int(float(metric.get("first_rank", "0") or 0))
        reason = primary_reason(query, top_row, top_memory, gold_memories, first_rank, all_memories)
        error_rows.append({
            "query_id": metric["query_id"],
            "query": query["query"],
            "query_type": query.get("type", "unknown"),
            "intent": classify_intent(query["query"]),
            "first_rank": first_rank,
            "reason": reason,
            "top_memory_id": "" if top_row is None else top_row["memory_id"],
            "top_memory_type": "" if top_memory is None else top_memory.get("memory_type", "unknown"),
            "top_memory_text": "" if top_memory is None else top_memory.get("text", ""),
            "gold_memory_ids": "|".join(query.get("answer_memory_ids", [])),
            "gold_memory_types": "|".join(sorted({memory.get("memory_type", "unknown") for memory in gold_memories})),
            "gold_memory_texts": " || ".join(memory.get("text", "") for memory in gold_memories[:3]),
        })

    total_queries = len(metrics)
    miss_count = len(error_rows)
    counters = {
        "reason": Counter(row["reason"] for row in error_rows),
        "intent": Counter(row["intent"] for row in error_rows),
        "query_type": Counter(row["query_type"] for row in error_rows),
        "top_memory_type": Counter(row["top_memory_type"] for row in error_rows),
        "gold_memory_types": Counter(row["gold_memory_types"] for row in error_rows),
    }
    summary_rows = []
    for group, counter in counters.items():
        for label, count in counter.most_common():
            summary_rows.append({
                "group": group,
                "label": label,
                "count": count,
                "share_of_errors": count / max(miss_count, 1),
                "share_of_queries": count / max(total_queries, 1),
            })

    write_csv(args.output_csv, error_rows)
    write_csv(args.summary_csv, summary_rows)

    lines = [
        "# Retrieval Error Analysis",
        "",
        f"- Method: `{args.method}`",
        f"- Queries: `{total_queries}`",
        f"- Top-1 errors: `{miss_count}`",
        f"- Top-1 error rate: `{miss_count / max(total_queries, 1):.3f}`",
        "",
        "## Error Reasons",
        "",
        "| Reason | Count | Share of Errors | Share of Queries |",
        "|---|---:|---:|---:|",
    ]
    for row in [item for item in summary_rows if item["group"] == "reason"]:
        lines.append(f"| {row['label']} | {row['count']} | {row['share_of_errors']:.3f} | {row['share_of_queries']:.3f} |")

    lines.extend([
        "",
        "## Query Intents",
        "",
        "| Intent | Count | Share of Errors | Share of Queries |",
        "|---|---:|---:|---:|",
    ])
    for row in [item for item in summary_rows if item["group"] == "intent"]:
        lines.append(f"| {row['label']} | {row['count']} | {row['share_of_errors']:.3f} | {row['share_of_queries']:.3f} |")

    lines.extend(["", "## Representative Errors", ""])
    for row in error_rows[:12]:
        lines.append(
            f"- `{row['query_id']}` / `{row['intent']}` / `{row['reason']}`: {row['query']} -> "
            f"`{row['top_memory_id']}` ({row['top_memory_type']})"
        )
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "method": args.method,
        "total_queries": total_queries,
        "top1_errors": miss_count,
        "output_csv": str(args.output_csv),
        "summary_csv": str(args.summary_csv),
        "output_report": str(args.output_report),
    }, indent=2))


if __name__ == "__main__":
    main()
