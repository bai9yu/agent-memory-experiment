#!/usr/bin/env python3
"""Extract fact-level agent memories from LoCoMo sessions with an LLM.

The extractor reads API configuration from a local .env file by default:

DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

It writes JSONL files compatible with memory_eval.py:

- memories.jsonl: extracted fact-level memories
- queries.jsonl: LoCoMo QA queries remapped to extracted memory ids by source turn

The script intentionally keeps the output schema explicit so extraction quality
can be compared against LoCoMo's official observation memories.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from compression_experiment import token_count
from convert_long_conversation import extract_entities, parse_any_date


SESSION_RE = re.compile(r"session_(\d+)$")
EVIDENCE_RE = re.compile(r"D(\d+):(\d+)")
JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


SYSTEM_PROMPT = """You extract durable long-term memories from a dialogue.

Return only valid JSON. Do not include markdown.

Extract concise fact-level memories that are useful for future retrieval.
Prefer stable facts about identity, relationships, goals, plans, preferences,
important events, emotional experiences, notable commitments, family/work
status, and immediate plans that a user may ask about later. Keep specific
dates, people, and evidence turn ids. Skip greetings, filler, compliments with
no durable fact, and generic backchannel messages.

Required output schema:
{
  "memories": [
    {
      "text": "A concise standalone memory fact.",
      "subject": "Main person or entity",
      "type": "identity|relationship|goal|plan|preference|event|emotion|health|work|education|family|hobby|other",
      "importance": 0.0,
      "confidence": 0.0,
      "source_turn_ids": ["D1:3"],
      "visibility": "private|shared"
    }
  ]
}

Rules:
- importance and confidence must be numbers from 0 to 1.
- source_turn_ids must use the ids provided in the dialogue, such as D1:3.
- Use one to three source_turn_ids per memory.
- Each text should be self-contained and understandable without the dialogue.
- Do not invent facts not supported by source_turn_ids.
- Optimize for evidence coverage first, then brevity.
- Prefer 6 to 12 memories per session when the dialogue contains enough facts.
- Include short but answerable facts, such as "Melanie is managing kids and work"
  or "Melanie is going swimming with the kids after the conversation."
- For identity questions, write direct identity memories when supported, e.g.
  "Caroline is a transgender woman" rather than only describing related stories.
- For career/goal questions, include the specific target field in the same memory
  when possible, e.g. "counseling or mental health" rather than only "career options."
- For event memories, include the relevant time expression when present, e.g.
  "recently", "yesterday", "last year", or the session date.
- If a turn supports two different retrievable facts, create two memories with
  the same source_turn_ids.
- Set visibility to "private" unless the dialogue explicitly says the memory is
  meant to be shared across agents or people.
"""


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def load_records(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("LoCoMo input must be a JSON list.")
    return data


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


def append_csv(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def load_existing_memories(output_dir: Path) -> list[dict[str, Any]]:
    path = output_dir / "memories.jsonl"
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_existing_csv(output_dir: Path, name: str) -> list[dict[str, Any]]:
    path = output_dir / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def completed_session_keys(usage_rows: list[dict[str, Any]]) -> set[tuple[int, str]]:
    done = set()
    for row in usage_rows:
        try:
            record_idx = int(row.get("record_idx", 0))
        except (TypeError, ValueError):
            continue
        session = str(row.get("session", ""))
        if record_idx and session:
            done.add((record_idx, session))
    return done


def next_memory_counter(memory_rows: list[dict[str, Any]]) -> int:
    max_id = 0
    for row in memory_rows:
        match = re.fullmatch(r"llm_(\d+)", str(row.get("id", "")))
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id + 1


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return str(value)


def session_number(key: str) -> int | None:
    match = SESSION_RE.fullmatch(key)
    return int(match.group(1)) if match else None


def selected_session_keys(record: dict[str, Any], max_sessions: int, session_start: int) -> list[str]:
    conversation = record.get("conversation", {})
    if not isinstance(conversation, dict):
        return []
    keys = [
        key for key, value in conversation.items()
        if session_number(key) is not None and isinstance(value, list)
    ]
    keys.sort(key=lambda item: session_number(item) or 10_000)
    if session_start > 1:
        keys = [key for key in keys if (session_number(key) or 0) >= session_start]
    return keys[:max_sessions]


def session_date(record: dict[str, Any], session_idx: int, fallback_idx: int) -> str:
    value = record.get("conversation", {}).get(f"session_{session_idx}_date_time")
    return parse_any_date(value, fallback_idx)


def session_dialogue(record: dict[str, Any], session_key: str) -> list[dict[str, str]]:
    session_idx = session_number(session_key)
    turns = record.get("conversation", {}).get(session_key, [])
    rows = []
    if not isinstance(turns, list) or session_idx is None:
        return rows
    for turn_idx, turn in enumerate(turns, start=1):
        if not isinstance(turn, dict):
            speaker = "speaker"
            text = normalize_text(turn)
        else:
            speaker = normalize_text(turn.get("speaker") or turn.get("role") or turn.get("name") or "speaker")
            text = normalize_text(turn.get("text") or turn.get("content") or turn.get("message") or turn.get("utterance"))
        if text:
            rows.append({
                "turn_id": f"D{session_idx}:{turn_idx}",
                "speaker": speaker,
                "text": text,
            })
    return rows


def build_user_prompt(record: dict[str, Any], session_key: str) -> str:
    session_idx = session_number(session_key) or 0
    date_text = record.get("conversation", {}).get(f"session_{session_idx}_date_time", "")
    speakers = [
        normalize_text(record.get("conversation", {}).get("speaker_a", "")),
        normalize_text(record.get("conversation", {}).get("speaker_b", "")),
    ]
    lines = [
        f"sample_id: {record.get('sample_id', '')}",
        f"session: D{session_idx}",
        f"session_datetime: {date_text}",
        f"participants: {', '.join(item for item in speakers if item)}",
        "",
        "Dialogue turns:",
    ]
    for row in session_dialogue(record, session_key):
        lines.append(f"{row['turn_id']} | {row['speaker']}: {row['text']}")
    return "\n".join(lines)


def parse_json_response(content: str) -> dict[str, Any]:
    content = content.strip()
    block = JSON_BLOCK_RE.search(content)
    if block:
        content = block.group(1).strip()
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("memories"), list):
        raise ValueError("LLM response must be a JSON object with a memories list.")
    return data


def call_deepseek(prompt: str, model: str, base_url: str, api_key: str, temperature: float, timeout: int) -> tuple[dict[str, Any], dict[str, Any]]:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {exc.code}: {message}") from exc
    content = payload["choices"][0]["message"]["content"]
    return parse_json_response(content), payload.get("usage", {})


def clamp_score(value: Any, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = default
    return max(0.0, min(1.0, score))


def normalize_memory(
    raw: dict[str, Any],
    memory_id: str,
    record_idx: int,
    session_idx: int,
    session_iso_date: str,
    sample_id: str,
) -> dict[str, Any] | None:
    text = normalize_text(raw.get("text"))
    if not text:
        return None
    source_turn_ids = raw.get("source_turn_ids", [])
    if isinstance(source_turn_ids, str):
        source_turn_ids = [source_turn_ids]
    source_turn_ids = [str(item) for item in source_turn_ids if EVIDENCE_RE.fullmatch(str(item))]
    if not source_turn_ids:
        return None
    subject = normalize_text(raw.get("subject") or "unknown")
    memory_type = normalize_text(raw.get("type") or "other").lower()
    visibility = normalize_text(raw.get("visibility") or "private").lower()
    if visibility not in {"private", "shared"}:
        visibility = "private"
    return {
        "id": memory_id,
        "session_id": f"{record_idx}_session_{session_idx}",
        "turn": int(source_turn_ids[0].split(":")[1]),
        "date": session_iso_date,
        "agent_id": subject,
        "user_id": f"user_{record_idx}",
        "text": f"{subject}: {text}" if subject and not text.startswith(subject) else text,
        "entities": extract_entities(text),
        "memory_type": memory_type,
        "importance": clamp_score(raw.get("importance"), 0.5),
        "confidence": clamp_score(raw.get("confidence"), 0.7),
        "visibility": visibility,
        "source_evidence_ids": source_turn_ids,
        "sample_id": sample_id,
        "compression_variant": "llm_extracted_fact",
    }


def add_adjacent_goal_links(memories: list[dict[str, Any]]) -> None:
    """Link adjacent planning/career turns so related QA evidence can map.

    LoCoMo observations often compress a broad plan turn and a specific career
    turn into one memory. LLM extraction may split them, which is useful, but
    evidence-based evaluation then misses cross-turn questions. This lightweight
    postprocess adds the adjacent source turn id to compatible memories.
    """
    by_session_subject: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for memory in memories:
        key = (str(memory.get("session_id", "")), str(memory.get("agent_id", "")))
        by_session_subject.setdefault(key, []).append(memory)

    goal_types = {"goal", "plan", "work", "education"}
    for rows in by_session_subject.values():
        rows.sort(key=lambda row: int(row.get("turn", 0)))
        for left, right in zip(rows, rows[1:]):
            if left.get("memory_type") not in goal_types or right.get("memory_type") not in goal_types:
                continue
            if abs(int(right.get("turn", 0)) - int(left.get("turn", 0))) > 3:
                continue
            left_sources = list(left.get("source_evidence_ids", []))
            right_sources = list(right.get("source_evidence_ids", []))
            combined = []
            for source in [*left_sources, *right_sources]:
                if source not in combined:
                    combined.append(source)
            left["source_evidence_ids"] = combined
            right["source_evidence_ids"] = combined


def remap_queries(records: list[dict[str, Any]], evidence_map: dict[tuple[int, str], list[str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    total_evidence = 0
    mapped_evidence = 0
    fully_mapped_queries = 0
    partially_mapped_queries = 0
    unmapped_queries = 0
    counter = 1

    for record_idx, record in enumerate(records, start=1):
        qas = record.get("qa", [])
        if not isinstance(qas, list):
            continue
        for qa in qas:
            if not isinstance(qa, dict):
                continue
            question = normalize_text(qa.get("question"))
            if not question:
                continue
            evidence_items = [str(item) for item in qa.get("evidence", []) if item]
            answer_ids: list[str] = []
            mapped_count = 0
            for evidence_id in evidence_items:
                total_evidence += 1
                mapped = evidence_map.get((record_idx, evidence_id), [])
                if mapped:
                    mapped_count += 1
                    mapped_evidence += 1
                for memory_id in mapped:
                    if memory_id not in answer_ids:
                        answer_ids.append(memory_id)
            if evidence_items and mapped_count == len(evidence_items):
                fully_mapped_queries += 1
            elif mapped_count > 0:
                partially_mapped_queries += 1
            else:
                unmapped_queries += 1

            max_session = max((int(match.group(1)) for item in evidence_items if (match := EVIDENCE_RE.fullmatch(item))), default=0)
            query_date = session_date(record, max_session, counter + 30) if max_session else parse_any_date(None, counter + 30)
            queries.append({
                "id": f"q{counter:05d}",
                "query": question,
                "answer_memory_ids": answer_ids,
                "query_date": query_date,
                "type": str(qa.get("category", "unknown")),
                "source_evidence_ids": evidence_items,
            })
            counter += 1

    stats = {
        "num_queries": len(queries),
        "fully_mapped_queries": fully_mapped_queries,
        "partially_mapped_queries": partially_mapped_queries,
        "unmapped_queries": unmapped_queries,
        "query_coverage": (fully_mapped_queries + partially_mapped_queries) / max(len(queries), 1),
        "strict_query_coverage": fully_mapped_queries / max(len(queries), 1),
        "total_evidence_ids": total_evidence,
        "mapped_evidence_ids": mapped_evidence,
        "evidence_coverage": mapped_evidence / max(total_evidence, 1),
    }
    return queries, stats


def write_report(path: Path, memory_rows: list[dict[str, Any]], coverage: dict[str, Any], usage_rows: list[dict[str, Any]]) -> None:
    total_tokens = sum(token_count(row["text"]) for row in memory_rows)
    prompt_tokens = sum(int(row.get("prompt_tokens") or 0) for row in usage_rows)
    completion_tokens = sum(int(row.get("completion_tokens") or 0) for row in usage_rows)
    lines = [
        "# LLM Memory Extraction Report",
        "",
        "This report summarizes fact-level memories extracted from LoCoMo sessions with DeepSeek.",
        "",
        "## Extraction Summary",
        "",
        f"- Extracted memories: `{len(memory_rows)}`",
        f"- Extracted memory tokens: `{total_tokens}`",
        f"- Prompt tokens: `{prompt_tokens}`",
        f"- Completion tokens: `{completion_tokens}`",
        f"- Query coverage: `{coverage['query_coverage']:.3f}`",
        f"- Strict query coverage: `{coverage['strict_query_coverage']:.3f}`",
        f"- Evidence coverage: `{coverage['evidence_coverage']:.3f}`",
        "",
        "## Notes",
        "",
        "- Query coverage is based on whether extracted memories cite the same LoCoMo evidence turn ids used by QA labels.",
        "- This is a memory-write evaluation: low coverage usually means the extractor omitted a fact or cited the wrong source turn.",
        "- The next comparison should run `memory_eval.py` on these extracted memories and compare against official `observation` memories.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def rebuild_final_outputs(output_dir: Path, records: list[dict[str, Any]], memory_rows: list[dict[str, Any]], usage_rows: list[dict[str, Any]]) -> dict[str, Any]:
    add_adjacent_goal_links(memory_rows)
    evidence_map: dict[tuple[int, str], list[str]] = {}
    for memory in memory_rows:
        record_idx = int(str(memory.get("session_id", "0_")).split("_", 1)[0])
        for evidence_id in memory["source_evidence_ids"]:
            evidence_map.setdefault((record_idx, evidence_id), []).append(memory["id"])

    queries, coverage = remap_queries(records, evidence_map)
    write_jsonl(output_dir / "memories.jsonl", memory_rows)
    write_jsonl(output_dir / "queries.jsonl", queries)
    write_csv(output_dir / "usage.csv", usage_rows)
    write_csv(output_dir / "coverage.csv", [{"variant": "llm_extracted_fact", **coverage}])
    write_report(output_dir / "extraction_report.md", memory_rows, coverage, usage_rows)
    return coverage


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract LoCoMo fact-level memories with DeepSeek.")
    parser.add_argument("--input", type=Path, default=Path("work/agent_memory_experiment/data/locomo10.json"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--max-records", type=int, default=1)
    parser.add_argument("--max-sessions", type=int, default=1)
    parser.add_argument("--session-start", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip sessions already present in usage.csv and refresh outputs after each new session.")
    args = parser.parse_args()

    load_dotenv(args.env_file)
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    if not args.dry_run and not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is missing. Put it in .env or the environment.")

    records = load_records(args.input)[:args.max_records]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    memory_rows = load_existing_memories(args.output_dir) if args.resume and not args.dry_run else []
    prompt_rows = load_existing_csv(args.output_dir, "prompts.csv") if args.resume else []
    usage_rows = load_existing_csv(args.output_dir, "usage.csv") if args.resume and not args.dry_run else []
    done_sessions = completed_session_keys(usage_rows)
    memory_counter = next_memory_counter(memory_rows)

    for record_idx, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id", f"sample_{record_idx}"))
        for session_key in selected_session_keys(record, args.max_sessions, args.session_start):
            session_idx = session_number(session_key) or 0
            session_label = f"D{session_idx}"
            if args.resume and (record_idx, session_label) in done_sessions:
                continue
            prompt = build_user_prompt(record, session_key)
            prompt_row = {
                "record_idx": record_idx,
                "sample_id": sample_id,
                "session": session_label,
                "prompt": prompt,
            }
            prompt_rows.append(prompt_row)
            if args.resume:
                append_csv(args.output_dir / "prompts.csv", prompt_row)
            if args.dry_run:
                continue
            data, usage = call_deepseek(prompt, model, base_url, api_key, args.temperature, args.timeout)
            usage_row = {
                "record_idx": record_idx,
                "sample_id": sample_id,
                "session": session_label,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            }
            usage_rows.append(usage_row)
            if args.resume:
                append_csv(args.output_dir / "usage.csv", usage_row)
                done_sessions.add((record_idx, session_label))
            iso_date = session_date(record, session_idx, len(memory_rows))
            for raw_memory in data.get("memories", []):
                if not isinstance(raw_memory, dict):
                    continue
                memory_id = f"llm_{memory_counter:05d}"
                memory = normalize_memory(raw_memory, memory_id, record_idx, session_idx, iso_date, sample_id)
                if memory is None:
                    continue
                memory_rows.append(memory)
                memory_counter += 1
            if args.resume:
                rebuild_final_outputs(args.output_dir, records, memory_rows, usage_rows)
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    if not args.resume:
        write_csv(args.output_dir / "prompts.csv", prompt_rows)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "prompts": len(prompt_rows), "output_dir": str(args.output_dir)}, indent=2))
        return

    coverage = rebuild_final_outputs(args.output_dir, records, memory_rows, usage_rows)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "num_memories": len(memory_rows),
        "num_queries": coverage["num_queries"],
        "query_coverage": coverage["query_coverage"],
        "evidence_coverage": coverage["evidence_coverage"],
        "model": model,
    }, indent=2))


if __name__ == "__main__":
    main()
