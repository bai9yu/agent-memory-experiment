#!/usr/bin/env python3
"""Generate dataset and slice-profile diagnostics for LoCoMo memory experiments."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def f(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def memory_group(row: dict[str, Any]) -> str:
    return str(row.get("sample_id") or row.get("session_id", "").split("_session_")[0] or "unknown")


def query_group(row: dict[str, Any], memory_by_id: dict[str, dict[str, Any]]) -> str:
    for memory_id in row.get("answer_memory_ids", []):
        memory = memory_by_id.get(memory_id)
        if memory:
            return memory_group(memory)
    return "unknown"


def summarize_variant(
    label: str,
    memories: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    raw_query_count: int | None = None,
) -> dict[str, Any]:
    memory_by_id = {str(row["id"]): row for row in memories if row.get("id")}
    memory_groups = Counter(memory_group(row) for row in memories)
    query_groups = Counter(query_group(row, memory_by_id) for row in queries)
    query_types = Counter(str(row.get("type", "unknown")) for row in queries)
    memory_types = Counter(str(row.get("memory_type", "raw_turn")) for row in memories)
    gold_counts = [len(row.get("answer_memory_ids", [])) for row in queries]
    source_counts = [len(row.get("source_evidence_ids", [])) for row in queries]
    memory_dates = [item for item in (parse_date(row.get("date")) for row in memories) if item]
    query_dates = [item for item in (parse_date(row.get("query_date")) for row in queries) if item]
    groups = sorted(set(memory_groups) | set(query_groups))
    memory_per_group = [memory_groups[group] for group in groups]
    query_per_group = [query_groups[group] for group in groups]
    answerable_share = len(queries) / raw_query_count if raw_query_count else 1.0
    return {
        "label": label,
        "memories": len(memories),
        "queries": len(queries),
        "raw_query_count": raw_query_count or len(queries),
        "answerable_share": answerable_share,
        "groups": len(groups),
        "sessions": len({row.get("session_id", "") for row in memories if row.get("session_id")}),
        "agents": len({row.get("agent_id", "") for row in memories if row.get("agent_id")}),
        "memory_types": len(memory_types),
        "mean_memories_per_group": mean([float(item) for item in memory_per_group]),
        "median_memories_per_group": median([float(item) for item in memory_per_group]),
        "mean_queries_per_group": mean([float(item) for item in query_per_group]),
        "median_queries_per_group": median([float(item) for item in query_per_group]),
        "mean_gold_memories_per_query": mean([float(item) for item in gold_counts]),
        "median_gold_memories_per_query": median([float(item) for item in gold_counts]),
        "multi_gold_query_share": sum(1 for item in gold_counts if item > 1) / len(gold_counts) if gold_counts else 0.0,
        "mean_source_evidence_per_query": mean([float(item) for item in source_counts]),
        "memory_start_date": min(memory_dates).isoformat() if memory_dates else "",
        "memory_end_date": max(memory_dates).isoformat() if memory_dates else "",
        "query_start_date": min(query_dates).isoformat() if query_dates else "",
        "query_end_date": max(query_dates).isoformat() if query_dates else "",
        "query_type_distribution": json.dumps(dict(sorted(query_types.items())), ensure_ascii=False),
        "memory_type_distribution": json.dumps(dict(memory_types.most_common()), ensure_ascii=False),
    }


def distribution_rows(
    label: str,
    memories: list[dict[str, Any]],
    queries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    memory_by_id = {str(row["id"]): row for row in memories if row.get("id")}
    counters = {
        "query_type": Counter(str(row.get("type", "unknown")) for row in queries),
        "memory_type": Counter(str(row.get("memory_type", "raw_turn")) for row in memories),
        "agent": Counter(str(row.get("agent_id", "unknown")) for row in memories),
        "group_memory": Counter(memory_group(row) for row in memories),
        "group_query": Counter(query_group(row, memory_by_id) for row in queries),
        "gold_count": Counter(str(len(row.get("answer_memory_ids", []))) for row in queries),
    }
    totals = {
        "query_type": len(queries),
        "memory_type": len(memories),
        "agent": len(memories),
        "group_memory": len(memories),
        "group_query": len(queries),
        "gold_count": len(queries),
    }
    for kind, counter in counters.items():
        for value, count in counter.most_common():
            rows.append({
                "variant": label,
                "kind": kind,
                "value": value,
                "count": count,
                "share": count / totals[kind] if totals[kind] else 0.0,
            })
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, summary_rows: list[dict[str, Any]], dist_rows: list[dict[str, Any]]) -> None:
    by_variant = {row["label"]: row for row in summary_rows}
    fact = by_variant["llm_extracted_fact_answerable"]
    raw = by_variant["raw_turn_full"]
    observation = by_variant.get("locomo_observation_answerable")
    lines = [
        "# LoCoMo 数据集切片画像",
        "",
        "本报告描述当前论文实验使用的 LoCoMo10 数据范围、answerable slice 比例、query type 分布、gold evidence 数量和 memory bank 结构。它用于支撑论文的数据集小节，并明确哪些结论只适用于当前 slice。",
        "",
        "## 总览",
        "",
        markdown_table(
            [
                "Variant",
                "Memories",
                "Queries",
                "Raw Query Count",
                "Answerable Share",
                "Groups",
                "Sessions",
                "Agents",
                "Mean Gold/query",
                "Multi-gold Share",
            ],
            [
                [
                    row["label"],
                    str(row["memories"]),
                    str(row["queries"]),
                    str(row["raw_query_count"]),
                    pct(float(row["answerable_share"])),
                    str(row["groups"]),
                    str(row["sessions"]),
                    str(row["agents"]),
                    f(float(row["mean_gold_memories_per_query"])),
                    pct(float(row["multi_gold_query_share"])),
                ]
                for row in summary_rows
            ],
        ),
        "",
        "## 当前主实验切片",
        "",
        f"- 主实验使用 `llm_extracted_fact_answerable`：{fact['memories']} 条 fact memories，{fact['queries']} 条 answerable queries。",
        f"- 相比 raw LoCoMo query 数 {raw['queries']}，answerable 覆盖率为 {pct(float(fact['answerable_share']))}。",
        f"- 覆盖 group/conversation 数：{fact['groups']}；session 数：{fact['sessions']}；agent 数：{fact['agents']}。",
        f"- 平均 gold memory 数：{f(float(fact['mean_gold_memories_per_query']))}；多 gold query 占比：{pct(float(fact['multi_gold_query_share']))}。",
        f"- Memory 时间范围：{fact['memory_start_date']} 到 {fact['memory_end_date']}；Query 时间范围：{fact['query_start_date']} 到 {fact['query_end_date']}。",
        "",
    ]
    if observation:
        lines.extend([
            "## Observation 对照切片",
            "",
            f"- `locomo_observation_answerable` 含 {observation['memories']} 条 observation memories 和 {observation['queries']} 条 answerable queries。",
            f"- observation memory 数约为 LLM fact memory 的 {f(float(observation['memories']) / float(fact['memories']))} 倍。",
            f"- 两个 answerable slice 的 query 数差异为 {int(fact['queries']) - int(observation['queries'])}，论文中不应把二者视为完全相同的标注空间。",
            "",
        ])
    for variant in ["llm_extracted_fact_answerable", "raw_turn_full", "locomo_observation_answerable"]:
        if variant not in by_variant:
            continue
        variant_rows = [
            row for row in dist_rows
            if row["variant"] == variant and row["kind"] in {"query_type", "gold_count", "memory_type"}
        ]
        lines.extend([
            f"## {variant} 分布",
            "",
        ])
        for kind in ["query_type", "gold_count", "memory_type"]:
            kind_rows = [row for row in variant_rows if row["kind"] == kind][:12]
            lines.extend([
                f"### {kind}",
                "",
                markdown_table(
                    ["Value", "Count", "Share"],
                    [[row["value"], str(row["count"]), pct(float(row["share"]))] for row in kind_rows],
                ),
                "",
            ])
    lines.extend([
        "## 论文写法边界",
        "",
        "- 可以写：当前主结果覆盖 LoCoMo10 中可映射到 LLM fact memory 的 answerable slice，且保留了多 query type、多个 conversation/group、跨 session 的时间跨度。",
        "- 应谨慎：answerable slice 不是 LoCoMo 所有原始问题；无法映射到 fact memory 的问题会被排除，因此外部有效性仍需更多数据集或更大 slice 验证。",
        "- 不能写：当前结果已经代表所有长对话智能体记忆任务，或已经完成跨数据集泛化。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LoCoMo dataset slice profile.")
    parser.add_argument("--raw-memories", type=Path, required=True)
    parser.add_argument("--raw-queries", type=Path, required=True)
    parser.add_argument("--fact-memories", type=Path, required=True)
    parser.add_argument("--fact-queries", type=Path, required=True)
    parser.add_argument("--observation-memories", type=Path)
    parser.add_argument("--observation-queries", type=Path)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-distribution", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    raw_memories = read_jsonl(args.raw_memories)
    raw_queries = read_jsonl(args.raw_queries)
    fact_memories = read_jsonl(args.fact_memories)
    fact_queries = read_jsonl(args.fact_queries)
    variants: list[tuple[str, list[dict[str, Any]], list[dict[str, Any]], int | None]] = [
        ("raw_turn_full", raw_memories, raw_queries, len(raw_queries)),
        ("llm_extracted_fact_answerable", fact_memories, fact_queries, len(raw_queries)),
    ]
    if args.observation_memories and args.observation_queries and args.observation_memories.exists() and args.observation_queries.exists():
        variants.append((
            "locomo_observation_answerable",
            read_jsonl(args.observation_memories),
            read_jsonl(args.observation_queries),
            len(raw_queries),
        ))
    summary_rows = [summarize_variant(label, memories, queries, raw_count) for label, memories, queries, raw_count in variants]
    dist_rows: list[dict[str, Any]] = []
    for label, memories, queries, _ in variants:
        dist_rows.extend(distribution_rows(label, memories, queries))
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_distribution, dist_rows)
    write_report(args.output_report, summary_rows, dist_rows)
    fact = next(row for row in summary_rows if row["label"] == "llm_extracted_fact_answerable")
    print(json.dumps({
        "output_report": str(args.output_report),
        "variants": len(summary_rows),
        "fact_memories": fact["memories"],
        "fact_queries": fact["queries"],
        "answerable_share": fact["answerable_share"],
        "groups": fact["groups"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
