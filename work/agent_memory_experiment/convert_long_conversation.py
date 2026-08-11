#!/usr/bin/env python3
"""Convert LoCoMo-like long-conversation data into the local JSONL format.

The converter is intentionally permissive because public long-memory datasets
often use slightly different field names across releases or mirrors. It accepts
JSON or JSONL input and tries common keys for conversations, sessions, messages,
questions, answers, and evidence turn identifiers.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


ENTITY_RE = re.compile(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b")
ENTITY_STOPWORDS = {
    "The",
    "This",
    "That",
    "Update",
    "User",
    "Assistant",
    "I",
}


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    for key in ("data", "records", "conversations", "examples"):
        if isinstance(data.get(key), list):
            return data[key]
    return [data]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def first_value(obj: dict[str, Any], keys: tuple[str, ...], default: Any = None) -> Any:
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return default


def parse_any_date(value: Any, fallback_day: int) -> str:
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value[:19], fmt).date().isoformat()
            except ValueError:
                pass
        match = re.search(r"(\d{1,2})\s+([A-Za-z]+),\s+(\d{4})", value)
        if match:
            day, month, year = match.groups()
            try:
                return datetime.strptime(f"{day} {month} {year}", "%d %B %Y").date().isoformat()
            except ValueError:
                pass
    if isinstance(value, (int, float)) and value > 10_000:
        try:
            return datetime.fromtimestamp(value).date().isoformat()
        except (OSError, ValueError):
            pass
    return (date(2026, 1, 1) + timedelta(days=fallback_day)).isoformat()


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, list):
        return " ".join(normalize_text(item) for item in value if item)
    if isinstance(value, dict):
        return normalize_text(first_value(value, ("text", "content", "message", "utterance", "value"), ""))
    return str(value)


def extract_entities(text: str, limit: int = 8) -> list[str]:
    seen = set()
    entities = []
    for item in ENTITY_RE.findall(text):
        if item in ENTITY_STOPWORDS:
            continue
        if item not in seen:
            seen.add(item)
            entities.append(item)
        if len(entities) >= limit:
            break
    return entities


def next_day(iso_date: str) -> str:
    return (datetime.strptime(iso_date, "%Y-%m-%d").date() + timedelta(days=1)).isoformat()


def iter_sessions(record: dict[str, Any]) -> list[dict[str, Any]]:
    sessions = first_value(record, ("sessions", "session", "conversation_sessions"), None)
    if isinstance(sessions, list):
        return [session if isinstance(session, dict) else {"messages": session} for session in sessions]

    conversation = record.get("conversation")
    if isinstance(conversation, dict):
        out = []
        session_keys = sorted(
            [key for key, value in conversation.items() if re.fullmatch(r"session_\d+", key) and isinstance(value, list)],
            key=lambda item: int(item.split("_")[1]),
        )
        for key in session_keys:
            out.append({
                "session_id": key,
                "date": conversation.get(f"{key}_date_time"),
                "messages": conversation[key],
            })
        if out:
            return out

    for key in ("conversation", "dialogue", "dialog", "messages", "turns", "chat"):
        value = record.get(key)
        if isinstance(value, list):
            return [{"session_id": first_value(record, ("id", "conversation_id", "sample_id"), "sample"), "messages": value}]
    return []


def iter_messages(session: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("messages", "conversation", "dialogue", "dialog", "turns", "chat"):
        value = session.get(key)
        if isinstance(value, list):
            return [message if isinstance(message, dict) else {"content": message} for message in value]
    return []


def iter_questions(record: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("qa", "qas", "questions", "qa_pairs", "evaluation"):
        value = record.get(key)
        if isinstance(value, list):
            return [question if isinstance(question, dict) else {"question": question} for question in value]
    return []


def evidence_ids_from_question(question: dict[str, Any], local_to_global: dict[str, str], fallback_ids: list[str]) -> list[str]:
    raw = first_value(
        question,
        ("answer_memory_ids", "evidence_memory_ids", "evidence_ids", "evidence", "evidence_turns", "supporting_turns"),
        [],
    )
    if isinstance(raw, (str, int)):
        raw_items = [raw]
    elif isinstance(raw, list):
        raw_items = raw
    else:
        raw_items = []

    answer_ids = []
    for item in raw_items:
        if isinstance(item, dict):
            item = first_value(item, ("memory_id", "turn_id", "id", "message_id", "index"), None)
        if item is None:
            continue
        key = str(item)
        answer_ids.append(local_to_global.get(key, key))

    valid_ids = [memory_id for memory_id in answer_ids if memory_id.startswith("m")]
    if valid_ids:
        return valid_ids
    return fallback_ids[-1:] if fallback_ids else []


def convert(records: list[dict[str, Any]], max_records: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    memories: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    memory_counter = 1
    query_counter = 1

    for record_idx, record in enumerate(records[:max_records] if max_records else records, start=1):
        user_id = str(first_value(record, ("user_id", "user", "speaker", "participant"), f"user_{record_idx}"))
        local_to_global: dict[str, str] = {}
        record_memory_ids: list[str] = []
        record_dates: list[str] = []

        for session_idx, session in enumerate(iter_sessions(record), start=1):
            raw_session_id = first_value(session, ("session_id", "id", "date"), f"r{record_idx}_s{session_idx}")
            session_id = f"{record_idx}_{raw_session_id}"
            for turn_idx, message in enumerate(iter_messages(session), start=1):
                speaker = str(first_value(message, ("speaker", "role", "agent_id", "name"), "speaker"))
                content = normalize_text(first_value(message, ("content", "text", "message", "utterance"), message))
                if not content:
                    continue
                local_id = str(first_value(message, ("dia_id", "id", "turn_id", "message_id", "index"), f"{session_idx}:{turn_idx}"))
                global_id = f"m{memory_counter:05d}"
                memory_counter += 1
                memory = {
                    "id": global_id,
                    "session_id": str(session_id),
                    "turn": turn_idx,
                    "date": parse_any_date(first_value(message, ("date", "timestamp", "time"), session.get("date")), len(memories)),
                    "agent_id": speaker,
                    "user_id": user_id,
                    "text": f"{speaker}: {content}",
                    "entities": extract_entities(content),
                }
                memories.append(memory)
                record_memory_ids.append(global_id)
                record_dates.append(memory["date"])
                local_to_global[local_id] = global_id
                local_to_global[str(turn_idx)] = global_id
                local_to_global[f"D{session_idx}:{turn_idx}"] = global_id

        for question in iter_questions(record):
            query_text = normalize_text(first_value(question, ("query", "question", "q"), ""))
            if not query_text:
                continue
            query_type = str(first_value(question, ("type", "category", "question_type"), "unknown"))
            fallback_query_date = next_day(max(record_dates)) if record_dates else parse_any_date(None, len(memories) + 30)
            query = {
                "id": f"q{query_counter:05d}",
                "query": query_text,
                "answer_memory_ids": evidence_ids_from_question(question, local_to_global, record_memory_ids),
                "query_date": parse_any_date(first_value(question, ("query_date", "date", "timestamp"), None), len(memories) + 30)
                if first_value(question, ("query_date", "date", "timestamp"), None)
                else fallback_query_date,
                "type": query_type,
            }
            queries.append(query)
            query_counter += 1

    return memories, queries


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert long-conversation datasets to experiment JSONL files.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--max-records", type=int, default=None)
    args = parser.parse_args()

    memories, queries = convert(load_records(args.input), max_records=args.max_records)
    memory_path = args.output_prefix.with_name(args.output_prefix.name + "_memories.jsonl")
    query_path = args.output_prefix.with_name(args.output_prefix.name + "_queries.jsonl")
    write_jsonl(memory_path, memories)
    write_jsonl(query_path, queries)
    print(json.dumps({"memories": str(memory_path), "queries": str(query_path), "num_memories": len(memories), "num_queries": len(queries)}, indent=2))


if __name__ == "__main__":
    main()
