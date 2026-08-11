#!/usr/bin/env python3
"""Summarize token cost, storage cost, and runtime for LoCoMo experiments."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from compression_experiment import token_count


RUNTIME_RE = re.compile(r"^Runtime seconds:\s*([0-9.]+)\s*$", re.MULTILINE)


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def memory_stats(path: Path, variant: str) -> dict[str, Any]:
    rows = read_jsonl(path)
    total_tokens = sum(token_count(row.get("text", "")) for row in rows)
    return {
        "variant": variant,
        "num_memories": len(rows),
        "memory_tokens": total_tokens,
        "avg_tokens_per_memory": total_tokens / max(len(rows), 1),
    }


def usage_stats(path: Path, input_price_per_million: float, output_price_per_million: float) -> dict[str, Any]:
    rows = read_csv(path)
    prompt_tokens = sum(int(float(row.get("prompt_tokens", 0) or 0)) for row in rows)
    completion_tokens = sum(int(float(row.get("completion_tokens", 0) or 0)) for row in rows)
    total_tokens = sum(int(float(row.get("total_tokens", 0) or 0)) for row in rows)
    estimated_cost = (
        prompt_tokens / 1_000_000 * input_price_per_million
        + completion_tokens / 1_000_000 * output_price_per_million
    )
    return {
        "api_sessions": len(rows),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "input_price_per_million": input_price_per_million,
        "output_price_per_million": output_price_per_million,
        "estimated_api_cost": estimated_cost,
    }


def runtime_seconds(report_path: Path) -> float:
    text = report_path.read_text(encoding="utf-8")
    match = RUNTIME_RE.search(text)
    if not match:
        return 0.0
    return float(match.group(1))


def runtime_stats(report_path: Path, variant: str, num_memories: int, num_queries: int, num_methods: int) -> dict[str, Any]:
    seconds = runtime_seconds(report_path)
    return {
        "variant": variant,
        "runtime_seconds": seconds,
        "num_memories": num_memories,
        "num_queries": num_queries,
        "num_methods": num_methods,
        "milliseconds_per_query": seconds * 1000 / max(num_queries, 1),
        "milliseconds_per_query_method": seconds * 1000 / max(num_queries * num_methods, 1),
        "candidate_pairs_per_method": num_memories * num_queries,
    }


def best_rows(baseline_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    wanted = {"keyword", "vector", "hybrid", "time_aware", "type_aware"}
    return [row for row in baseline_rows if row["method"] in wanted]


def write_report(path: Path, storage_rows: list[dict[str, Any]], runtime_rows: list[dict[str, Any]], usage: dict[str, Any], baseline_rows: list[dict[str, str]]) -> None:
    llm = next(row for row in storage_rows if row["variant"] == "llm_extracted_fact")
    obs = next(row for row in storage_rows if row["variant"] == "locomo_observation")
    token_ratio = llm["memory_tokens"] / max(obs["memory_tokens"], 1)
    token_saving = 1.0 - token_ratio
    cost_line = "未计算货币成本；如需估算，请传入 input/output 每百万 token 单价。"
    if usage["input_price_per_million"] or usage["output_price_per_million"]:
        cost_line = (
            f"按 input={usage['input_price_per_million']}、output={usage['output_price_per_million']} 每百万 token 估算，"
            f"API 成本为 `{usage['estimated_api_cost']:.6f}`。"
        )

    lines = [
        "# LoCoMo10 成本与延迟分析",
        "",
        "## API Token 成本",
        "",
        f"- API sessions：`{usage['api_sessions']}`",
        f"- Prompt tokens：`{usage['prompt_tokens']}`",
        f"- Completion tokens：`{usage['completion_tokens']}`",
        f"- Total tokens：`{usage['total_tokens']}`",
        f"- 货币成本：{cost_line}",
        "",
        "## Memory Storage",
        "",
        "| Variant | Memories | Memory Tokens | Avg Tokens / Memory |",
        "|---|---:|---:|---:|",
    ]
    for row in storage_rows:
        lines.append(
            f"| {row['variant']} | {row['num_memories']} | {row['memory_tokens']} | {row['avg_tokens_per_memory']:.2f} |"
        )
    lines.extend([
        "",
        f"DeepSeek extracted fact 的 memory token 是 LoCoMo observation 的 `{token_ratio:.3f}`，约节省 `{token_saving:.1%}` memory storage tokens。",
        "",
        "## Runtime",
        "",
        "| Variant | Runtime Seconds | Queries | Memories | Methods | ms / Query | ms / Query-Method |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in runtime_rows:
        lines.append(
            f"| {row['variant']} | {row['runtime_seconds']:.4f} | {row['num_queries']} | {row['num_memories']} | "
            f"{row['num_methods']} | {row['milliseconds_per_query']:.2f} | {row['milliseconds_per_query_method']:.2f} |"
        )
    lines.extend([
        "",
        "说明：runtime 是 `memory_eval.py` 的端到端离线评测时间，包含本地模型/缓存读取、编码、排序和写出结果，不等同于线上服务单 query latency。",
        "",
        "## Accuracy-Cost Tradeoff",
        "",
        "| Variant | Method | Recall@1 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|",
    ])
    for row in best_rows(baseline_rows):
        lines.append(
            f"| {row['variant']} | {row['method']} | {float(row['recall@1']):.3f} | "
            f"{float(row['recall@5']):.3f} | {float(row['mrr']):.3f} |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        "- DeepSeek 抽取带来一次性 API 成本，但生成的 fact-level memory 比 observation 更短。",
        "- type-aware 的准确率最高，但 runtime 与 time-aware 基本同阶，因为只增加轻量规则匹配。",
        "- keyword/vector 单独使用成本低但准确率明显弱于 hybrid/time-aware/type-aware。",
        "- 若面向在线系统，应进一步拆分 embedding 编码时间、候选召回时间和重排时间。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize LoCoMo10 memory cost and runtime.")
    parser.add_argument("--llm-memories", type=Path, required=True)
    parser.add_argument("--observation-memories", type=Path, required=True)
    parser.add_argument("--usage", type=Path, required=True)
    parser.add_argument("--llm-report", type=Path, required=True)
    parser.add_argument("--observation-report", type=Path, required=True)
    parser.add_argument("--baseline-csv", type=Path, required=True)
    parser.add_argument("--input-price-per-million", type=float, default=0.0)
    parser.add_argument("--output-price-per-million", type=float, default=0.0)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--runtime-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    storage_rows = [
        memory_stats(args.llm_memories, "llm_extracted_fact"),
        memory_stats(args.observation_memories, "locomo_observation"),
    ]
    usage = usage_stats(args.usage, args.input_price_per_million, args.output_price_per_million)
    baseline_rows = read_csv(args.baseline_csv)
    llm_row = next(row for row in storage_rows if row["variant"] == "llm_extracted_fact")
    obs_row = next(row for row in storage_rows if row["variant"] == "locomo_observation")
    llm_queries = int(next(row["num_queries"] for row in baseline_rows if row["variant"] == "llm_extracted_fact"))
    obs_queries = int(next(row["num_queries"] for row in baseline_rows if row["variant"] == "locomo_observation"))
    num_methods = len({row["method"] for row in baseline_rows if row["variant"] == "llm_extracted_fact"})
    runtime_rows = [
        runtime_stats(args.llm_report, "llm_extracted_fact", llm_row["num_memories"], llm_queries, num_methods),
        runtime_stats(args.observation_report, "locomo_observation", obs_row["num_memories"], obs_queries, num_methods),
    ]
    cost_rows = []
    for row in storage_rows:
        if row["variant"] == "llm_extracted_fact":
            usage_part = usage
        else:
            usage_part = {
                "api_sessions": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "input_price_per_million": usage["input_price_per_million"],
                "output_price_per_million": usage["output_price_per_million"],
                "estimated_api_cost": 0.0,
            }
        cost_rows.append({**row, **usage_part})
    write_csv(args.output_csv, cost_rows)
    write_csv(args.runtime_csv, runtime_rows)
    write_report(args.output_report, storage_rows, runtime_rows, usage, baseline_rows)
    print(json.dumps({
        "output_csv": str(args.output_csv),
        "runtime_csv": str(args.runtime_csv),
        "output_report": str(args.output_report),
        "usage": usage,
    }, indent=2))


if __name__ == "__main__":
    main()
