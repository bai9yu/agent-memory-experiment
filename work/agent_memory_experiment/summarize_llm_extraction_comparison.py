#!/usr/bin/env python3
"""Summarize LLM memory extraction against LoCoMo observation memories."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from compression_experiment import token_count


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def summary_for(path: Path, method: str) -> dict[str, Any]:
    rows = read_csv(path)
    for row in rows:
        if row["method"] == method:
            return row
    raise ValueError(f"Method {method} not found in {path}")


def memory_stats(path: Path) -> dict[str, Any]:
    rows = read_jsonl(path)
    total_tokens = sum(token_count(row.get("text", "")) for row in rows)
    type_counts: dict[str, int] = {}
    for row in rows:
        memory_type = str(row.get("memory_type") or row.get("compression_variant") or "unknown")
        type_counts[memory_type] = type_counts.get(memory_type, 0) + 1
    return {
        "num_memories": len(rows),
        "memory_tokens": total_tokens,
        "avg_tokens_per_memory": total_tokens / max(len(rows), 1),
        "type_counts": type_counts,
    }


def usage_stats(path: Path | None) -> dict[str, int]:
    if path is None or not path.exists():
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    rows = read_csv(path)
    return {
        "prompt_tokens": sum(int(row.get("prompt_tokens") or 0) for row in rows),
        "completion_tokens": sum(int(row.get("completion_tokens") or 0) for row in rows),
        "total_tokens": sum(int(row.get("total_tokens") or 0) for row in rows),
    }


def top1_errors(rankings_path: Path, method: str, limit: int = 8) -> list[dict[str, Any]]:
    errors = []
    seen = set()
    for row in read_csv(rankings_path):
        if row["method"] != method or row["query_id"] in seen:
            continue
        seen.add(row["query_id"])
        if row["is_relevant"] == "True":
            continue
        errors.append({
            "query_id": row["query_id"],
            "query": row["query"],
            "top_memory_id": row["memory_id"],
            "top_memory_text": row["memory_text"],
            "top_score": row["final_score"],
        })
        if len(errors) >= limit:
            break
    return errors


def fmt(value: Any) -> str:
    return f"{float(value):.3f}"


def write_report(path: Path, rows: list[dict[str, Any]], llm_errors: list[dict[str, Any]], obs_errors: list[dict[str, Any]]) -> None:
    lines = [
        "# LLM Memory Extraction 对比报告",
        "",
        "本报告比较 DeepSeek 抽取的 fact-level memory 与 LoCoMo 官方 observation memory，在同一 conversation/session slice 下的覆盖率、token 成本和 BGE-M3 检索效果。",
        "",
        "## 主结果",
        "",
        "| Variant | Memories | Memory Tokens | Answerable Queries | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['num_memories']} | {row['memory_tokens']} | {row['num_queries']} | "
            f"{fmt(row['recall@1'])} | {fmt(row['recall@3'])} | {fmt(row['recall@5'])} | {fmt(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## API 用量",
        "",
        "| Variant | Prompt Tokens | Completion Tokens | Total Tokens |",
        "|---|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['prompt_tokens']} | {row['completion_tokens']} | {row['total_tokens']} |"
        )
    lines.extend([
        "",
        "## Top-1 错误样例",
        "",
        "### LLM Extracted Fact",
        "",
    ])
    if llm_errors:
        for error in llm_errors:
            lines.append(f"- `{error['query_id']}` {error['query']} -> `{error['top_memory_id']}`: {error['top_memory_text']}")
    else:
        lines.append("- 无 Top-1 错误。")
    lines.extend([
        "",
        "### LoCoMo Observation",
        "",
    ])
    if obs_errors:
        for error in obs_errors:
            lines.append(f"- `{error['query_id']}` {error['query']} -> `{error['top_memory_id']}`: {error['top_memory_text']}")
    else:
        lines.append("- 无 Top-1 错误。")
    lines.extend([
        "",
        "## 解释",
        "",
        "- 如果 LLM 的 answerable query 数接近 observation，说明 extraction 的 evidence 覆盖率已经接近官方事实记忆。",
        "- 如果 LLM 的 Recall@1/MRR 低于 observation，说明抽取文本措辞或 memory type 与查询表达仍有差距。",
        "- 如果 LLM 的 Recall@3/5 较高但 Recall@1 较低，下一步优先考虑 reranking 或 memory-type-aware scoring。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize LLM extraction vs observation retrieval results.")
    parser.add_argument("--llm-memories", type=Path, required=True)
    parser.add_argument("--llm-summary", type=Path, required=True)
    parser.add_argument("--llm-rankings", type=Path, required=True)
    parser.add_argument("--llm-usage", type=Path, default=None)
    parser.add_argument("--observation-memories", type=Path, required=True)
    parser.add_argument("--observation-summary", type=Path, required=True)
    parser.add_argument("--observation-rankings", type=Path, required=True)
    parser.add_argument("--method", default="hybrid")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()

    llm_metrics = summary_for(args.llm_summary, args.method)
    obs_metrics = summary_for(args.observation_summary, args.method)
    llm_mem = memory_stats(args.llm_memories)
    obs_mem = memory_stats(args.observation_memories)
    llm_usage = usage_stats(args.llm_usage)

    rows = [
        {
            "variant": "llm_extracted_fact",
            **{key: llm_mem[key] for key in ("num_memories", "memory_tokens", "avg_tokens_per_memory")},
            **llm_usage,
            **{key: llm_metrics[key] for key in ("num_queries", "recall@1", "recall@3", "recall@5", "mrr")},
        },
        {
            "variant": "locomo_observation",
            **{key: obs_mem[key] for key in ("num_memories", "memory_tokens", "avg_tokens_per_memory")},
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            **{key: obs_metrics[key] for key in ("num_queries", "recall@1", "recall@3", "recall@5", "mrr")},
        },
    ]
    write_csv(args.csv_output, rows)
    write_report(
        args.output,
        rows,
        top1_errors(args.llm_rankings, args.method),
        top1_errors(args.observation_rankings, args.method),
    )
    print(json.dumps({"output": str(args.output), "csv_output": str(args.csv_output), "method": args.method}, indent=2))


if __name__ == "__main__":
    main()
