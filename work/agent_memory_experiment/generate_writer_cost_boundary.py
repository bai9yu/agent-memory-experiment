#!/usr/bin/env python3
"""Separate one-time memory-write API tokens from reusable memory storage savings."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

from compression_experiment import token_count


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def usage_stats(path: Path) -> dict[str, Any]:
    rows = read_csv(path)
    return {
        "api_sessions": len(rows),
        "prompt_tokens": sum(int(float(row.get("prompt_tokens", "0") or 0)) for row in rows),
        "completion_tokens": sum(int(float(row.get("completion_tokens", "0") or 0)) for row in rows),
        "total_tokens": sum(int(float(row.get("total_tokens", "0") or 0)) for row in rows),
    }


def memory_tokens(path: Path) -> tuple[int, int, float]:
    rows = read_jsonl(path)
    total = sum(token_count(row.get("text", "")) for row in rows)
    return len(rows), total, total / max(len(rows), 1)


def maybe_writer_variance(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    rows = read_csv(path)
    return {row["metric"]: row for row in rows}


def build_rows(
    usage: dict[str, Any],
    fact_memories: Path,
    observation_memories: Path,
    writer_aggregate: Path,
) -> list[dict[str, Any]]:
    fact_count, fact_tokens, fact_avg = memory_tokens(fact_memories)
    obs_count, obs_tokens, obs_avg = memory_tokens(observation_memories)
    storage_ratio = fact_tokens / max(obs_tokens, 1)
    storage_saving = 1.0 - storage_ratio
    write_to_storage_ratio = usage["total_tokens"] / max(fact_tokens, 1)
    break_even_reuses = usage["total_tokens"] / max(obs_tokens - fact_tokens, 1)
    variance = maybe_writer_variance(writer_aggregate)
    mrr = variance.get("mrr", {})
    recall5 = variance.get("recall@5", {})

    return [
        {
            "item": "memory_write_api_tokens",
            "value": usage["total_tokens"],
            "unit": "tokens",
            "scope": f"{usage['api_sessions']} DeepSeek memory-write sessions",
            "paper_boundary": "one_time_generation_cost_not_online_retrieval_storage",
        },
        {
            "item": "memory_write_prompt_tokens",
            "value": usage["prompt_tokens"],
            "unit": "tokens",
            "scope": "DeepSeek memory writer input",
            "paper_boundary": "report_separately_from_stored_memory_tokens",
        },
        {
            "item": "memory_write_completion_tokens",
            "value": usage["completion_tokens"],
            "unit": "tokens",
            "scope": "DeepSeek memory writer output",
            "paper_boundary": "report_separately_from_stored_memory_tokens",
        },
        {
            "item": "fact_memory_storage_tokens",
            "value": fact_tokens,
            "unit": "tokens",
            "scope": f"{fact_count} fact memories, avg={fact_avg:.2f}",
            "paper_boundary": "reused_by_downstream_retrieval_runs",
        },
        {
            "item": "observation_memory_storage_tokens",
            "value": obs_tokens,
            "unit": "tokens",
            "scope": f"{obs_count} LoCoMo observation memories, avg={obs_avg:.2f}",
            "paper_boundary": "comparison_storage_baseline",
        },
        {
            "item": "fact_vs_observation_storage_ratio",
            "value": f"{storage_ratio:.6f}",
            "unit": "ratio",
            "scope": "fact tokens / observation tokens",
            "paper_boundary": "storage_efficiency_claim",
        },
        {
            "item": "fact_vs_observation_storage_saving",
            "value": f"{storage_saving:.6f}",
            "unit": "ratio",
            "scope": "1 - storage ratio",
            "paper_boundary": "storage_efficiency_claim",
        },
        {
            "item": "write_tokens_per_fact_storage_token",
            "value": f"{write_to_storage_ratio:.6f}",
            "unit": "ratio",
            "scope": "one-time API tokens / stored fact-memory tokens",
            "paper_boundary": "do_not_describe_storage_saving_as_free_extraction",
        },
        {
            "item": "storage_break_even_reuses",
            "value": f"{break_even_reuses:.6f}",
            "unit": "retrieval_passes",
            "scope": "one-time API tokens / per-pass storage-token saving",
            "paper_boundary": "token_only_diagnostic_not_monetary_cost_model",
        },
        {
            "item": "writer_stability_mrr",
            "value": mrr.get("mean", ""),
            "unit": "mean",
            "scope": f"completed_runs={mrr.get('completed_runs', '')}, stdev={mrr.get('stdev', '')}",
            "paper_boundary": "supports_stability_but_not_human_faithfulness",
        },
        {
            "item": "writer_stability_recall5",
            "value": recall5.get("mean", ""),
            "unit": "mean",
            "scope": f"completed_runs={recall5.get('completed_runs', '')}, stdev={recall5.get('stdev', '')}",
            "paper_boundary": "supports_stability_but_not_human_faithfulness",
        },
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    by_item = {row["item"]: row for row in rows}
    total_write = int(by_item["memory_write_api_tokens"]["value"])
    prompt = int(by_item["memory_write_prompt_tokens"]["value"])
    completion = int(by_item["memory_write_completion_tokens"]["value"])
    fact_tokens = int(by_item["fact_memory_storage_tokens"]["value"])
    obs_tokens = int(by_item["observation_memory_storage_tokens"]["value"])
    saving = float(by_item["fact_vs_observation_storage_saving"]["value"])
    write_per_storage = float(by_item["write_tokens_per_fact_storage_token"]["value"])
    break_even = float(by_item["storage_break_even_reuses"]["value"])
    mrr_row = by_item["writer_stability_mrr"]
    recall5_row = by_item["writer_stability_recall5"]

    lines = [
        "# Memory Writer 成本边界报告",
        "",
        "本报告把 LLM memory write 的一次性 API token 成本，与后续检索阶段可复用的 memory storage token 分开。它用于避免把“存储 token 节省”误写成“没有抽取成本”。",
        "",
        "## 总览",
        "",
        f"- 一次性 memory-write API tokens：`{total_write}`，其中 prompt `{prompt}`，completion `{completion}`。",
        f"- 存储后的 fact memory tokens：`{fact_tokens}`。",
        f"- 对照 LoCoMo observation memory tokens：`{obs_tokens}`。",
        f"- fact memory 相比 observation memory 的存储节省：`{saving:.1%}`。",
        f"- 一次性写入 token / fact 存储 token：`{write_per_storage:.2f}x`。",
        f"- 仅从 token 数看，若每次检索都需要扫描/携带完整 memory，约 `{break_even:.1f}` 次复用后，累计存储 token 节省可抵消一次性写入 token；该值不是货币成本模型。",
        "",
        "## 明细",
        "",
        "| Item | Value | Unit | Scope | Paper Boundary |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item']} | {row['value']} | {row['unit']} | {row['scope']} | {row['paper_boundary']} |"
        )
    lines.extend([
        "",
        "## 可写入论文的边界",
        "",
        "- 可以写：fact-level memory 在检索阶段的存储 token 低于 LoCoMo observation memory，并在当前 LoCoMo10 slice 上保持更高检索指标。",
        "- 可以写：memory writer 有一次性 API token 成本，后续检索复用的是已写入的短 fact memory。",
        "- 应谨慎：`storage_break_even_reuses` 只是 token 口径诊断，不等同于真实费用、延迟或能耗 break-even。",
        "- 不能写：事实级记忆压缩没有成本；也不能在人工复核前宣称所有抽取事实完全忠实。",
    ])
    if mrr_row["value"] and recall5_row["value"]:
        lines.extend([
            "",
            "## Writer 稳定性引用",
            "",
            f"- MRR mean=`{float(mrr_row['value']):.3f}`，{mrr_row['scope']}。",
            f"- Recall@5 mean=`{float(recall5_row['value']):.3f}`，{recall5_row['scope']}。",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate memory-writer cost boundary report.")
    parser.add_argument("--usage", type=Path, required=True)
    parser.add_argument("--fact-memories", type=Path, required=True)
    parser.add_argument("--observation-memories", type=Path, required=True)
    parser.add_argument("--writer-aggregate", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(usage_stats(args.usage), args.fact_memories, args.observation_memories, args.writer_aggregate)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print({
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
        "rows": len(rows),
    })


if __name__ == "__main__":
    main()
