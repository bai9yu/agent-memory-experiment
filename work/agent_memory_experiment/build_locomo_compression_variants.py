#!/usr/bin/env python3
"""Build LoCoMo observation and session-summary memory variants.

LoCoMo QA evidence points to dialogue turns such as D1:3. This script remaps
those turn-level evidence ids to compressed memories:

- observation: one memory per LoCoMo observation fact, using the cited turn id.
- session_summary: one memory per session summary, mapping all turns in that
  session to the same summary memory.

The observation variant uses strict evidence mapping. If a QA evidence turn was
not represented by an observation fact, that query keeps only the mapped
evidence ids it can support. Coverage statistics show how often this happens.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from convert_long_conversation import extract_entities, parse_any_date
from compression_experiment import token_count


SESSION_KEY_RE = re.compile(r"session_(\d+)")
EVIDENCE_RE = re.compile(r"D(\d+):(\d+)")


def load_json(path: Path) -> list[dict[str, Any]]:
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


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return str(value)


def session_number(key: str) -> int | None:
    match = SESSION_KEY_RE.search(key)
    return int(match.group(1)) if match else None


def evidence_session_id(evidence_id: str) -> int | None:
    match = EVIDENCE_RE.fullmatch(str(evidence_id))
    return int(match.group(1)) if match else None


def session_date(record: dict[str, Any], session_idx: int, fallback_idx: int) -> str:
    value = record.get("conversation", {}).get(f"session_{session_idx}_date_time")
    return parse_any_date(value, fallback_idx)


def max_turn_for_session(record: dict[str, Any], session_idx: int) -> int:
    turns = record.get("conversation", {}).get(f"session_{session_idx}", [])
    return len(turns) if isinstance(turns, list) else 0


def build_observation_variant(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[tuple[int, str], list[str]]]:
    memories: list[dict[str, Any]] = []
    evidence_map: dict[tuple[int, str], list[str]] = {}
    counter = 1

    for record_idx, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id", f"sample_{record_idx}"))
        observations = record.get("observation", {})
        if not isinstance(observations, dict):
            continue
        for key in sorted(observations, key=lambda item: session_number(item) or 10_000):
            session_idx = session_number(key)
            if session_idx is None:
                continue
            session_obs = observations.get(key)
            if not isinstance(session_obs, dict):
                continue
            for speaker, facts in session_obs.items():
                if not isinstance(facts, list):
                    continue
                for fact in facts:
                    if not isinstance(fact, list) or not fact:
                        continue
                    text = normalize_text(fact[0])
                    if not text:
                        continue
                    cited = [str(item) for item in fact[1:] if item]
                    memory_id = f"obs_{counter:05d}"
                    counter += 1
                    memory = {
                        "id": memory_id,
                        "session_id": f"{record_idx}_session_{session_idx}",
                        "turn": len(memories) + 1,
                        "date": session_date(record, session_idx, len(memories)),
                        "agent_id": str(speaker),
                        "user_id": f"user_{record_idx}",
                        "text": f"{speaker}: {text}",
                        "entities": extract_entities(text),
                        "compression_variant": "locomo_observation",
                        "source_evidence_ids": cited,
                        "sample_id": sample_id,
                    }
                    memories.append(memory)
                    for evidence_id in cited:
                        evidence_map.setdefault((record_idx, evidence_id), []).append(memory_id)
    return memories, evidence_map


def build_session_summary_variant(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[tuple[int, str], list[str]]]:
    memories: list[dict[str, Any]] = []
    evidence_map: dict[tuple[int, str], list[str]] = {}
    counter = 1

    for record_idx, record in enumerate(records, start=1):
        sample_id = str(record.get("sample_id", f"sample_{record_idx}"))
        summaries = record.get("session_summary", {})
        if not isinstance(summaries, dict):
            continue
        for key in sorted(summaries, key=lambda item: session_number(item) or 10_000):
            session_idx = session_number(key)
            if session_idx is None:
                continue
            text = normalize_text(summaries.get(key))
            if not text:
                continue
            memory_id = f"summ_{counter:05d}"
            counter += 1
            max_turn = max_turn_for_session(record, session_idx)
            memory = {
                "id": memory_id,
                "session_id": f"{record_idx}_session_{session_idx}",
                "turn": 1,
                "date": session_date(record, session_idx, len(memories)),
                "agent_id": "session_summary",
                "user_id": f"user_{record_idx}",
                "text": text,
                "entities": extract_entities(text),
                "compression_variant": "locomo_session_summary",
                "source_session": f"D{session_idx}",
                "sample_id": sample_id,
            }
            memories.append(memory)
            for turn_idx in range(1, max_turn + 1):
                evidence_map[(record_idx, f"D{session_idx}:{turn_idx}")] = [memory_id]
    return memories, evidence_map


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

            max_session = max((evidence_session_id(item) or 0 for item in evidence_items), default=0)
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


def storage_stats(memories: list[dict[str, Any]], raw_tokens: int, variant: str) -> dict[str, Any]:
    total_tokens = sum(token_count(memory["text"]) for memory in memories)
    return {
        "variant": variant,
        "num_memories": len(memories),
        "total_tokens": total_tokens,
        "avg_tokens_per_memory": total_tokens / max(len(memories), 1),
        "token_ratio_vs_raw": total_tokens / max(raw_tokens, 1),
    }


def write_report(path: Path, storage_rows: list[dict[str, Any]], coverage_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# LoCoMo 真实压缩数据构建报告",
        "",
        "本文档记录从 LoCoMo 原始字段构建 `observation` 与 `session_summary` 两种真实压缩记忆的结果。",
        "",
        "## 存储规模",
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
        "## Evidence 覆盖率",
        "",
        "| Variant | Queries | Full Query Coverage | Partial Query Coverage | Unmapped Queries | Evidence Coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for row in coverage_rows:
        partial = row["query_coverage"] - row["strict_query_coverage"]
        lines.append(
            f"| {row['variant']} | {row['num_queries']} | {row['strict_query_coverage']:.3f} | "
            f"{partial:.3f} | {row['unmapped_queries']} | {row['evidence_coverage']:.3f} |"
        )
    lines.extend([
        "",
        "## 评测口径",
        "",
        "- `observation` 使用严格 evidence 映射：只有 observation fact 明确引用的 `Dsession:turn` 才会成为 gold memory。",
        "- `session_summary` 把同一 session 的所有 turn 映射到该 session summary，因此覆盖率通常更高，但检索粒度更粗。",
        "- 如果压缩版本没有覆盖某个 QA 的 evidence，该 query 在该版本中会自然记为无法召回；这能反映压缩是否丢失事实。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build LoCoMo observation/session-summary compression variants.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--raw-memories", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    records = load_json(args.input)
    raw_tokens = 0
    with args.raw_memories.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                raw_tokens += token_count(json.loads(line)["text"])

    observation_memories, observation_map = build_observation_variant(records)
    observation_queries, observation_stats = remap_queries(records, observation_map)
    summary_memories, summary_map = build_session_summary_variant(records)
    summary_queries, summary_stats = remap_queries(records, summary_map)

    variants = {
        "observation": (observation_memories, observation_queries, observation_stats),
        "session_summary": (summary_memories, summary_queries, summary_stats),
    }

    storage_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    for variant, (memories, queries, stats) in variants.items():
        variant_dir = args.output_dir / variant
        write_jsonl(variant_dir / "memories.jsonl", memories)
        write_jsonl(variant_dir / "queries.jsonl", queries)
        storage_rows.append(storage_stats(memories, raw_tokens, variant))
        coverage_row = {"variant": variant, **stats}
        coverage_rows.append(coverage_row)

    write_csv(args.output_dir / "locomo_compression_storage.csv", storage_rows)
    write_csv(args.output_dir / "locomo_compression_coverage.csv", coverage_rows)
    write_report(args.output_dir / "locomo_compression_build_report_zh.md", storage_rows, coverage_rows)
    print(json.dumps({
        "output_dir": str(args.output_dir),
        "storage": storage_rows,
        "coverage": coverage_rows,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
