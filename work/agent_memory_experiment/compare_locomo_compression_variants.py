#!/usr/bin/env python3
"""Aggregate LoCoMo raw, observation, and session-summary compression results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def metric_row(path: Path, variant: str, method: str = "time_aware") -> dict[str, Any]:
    for row in read_csv(path):
        if row["method"] == method:
            return {"variant": variant, **row}
    raise ValueError(f"Missing method {method} in {path}")


def by_variant(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["variant"]: row for row in rows}


def fmt(value: Any) -> str:
    return f"{float(value):.3f}"


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# LoCoMo 真实压缩对照实验报告",
        "",
        "本实验比较三种记忆形态：原始 turn-level memory、LoCoMo 官方 observation fact、LoCoMo 官方 session summary。评测使用同一套 BGE-M3 embedding、adaptive time-aware、persona gate 和 importance proxy。",
        "",
        "## 总体结果",
        "",
        "| Variant | Memories | Token Ratio | Evidence Coverage | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['num_memories']} | {fmt(row['token_ratio_vs_raw'])} | "
            f"{fmt(row['evidence_coverage'])} | {fmt(row['recall@1'])} | {fmt(row['recall@3'])} | "
            f"{fmt(row['recall@5'])} | {fmt(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## 关键解释",
        "",
        "- `raw_turn` 是原始对话 turn 级记忆，粒度最细，但 token 成本最高，闲聊噪声也最多。",
        "- `observation` 是 LoCoMo 官方抽取的事实级记忆，只保留约 28% token。它的 Recall@1 高于 raw，说明高质量事实抽取能显著减少检索噪声；但 evidence 覆盖率约 78%，部分 QA 在 observation 中已经没有可召回证据。",
        "- `session_summary` 只保留约 20% token，覆盖率接近完整，检索指标最高。但它把一个 session 压成一个大块，gold target 也变成 session 级，因此指标会比 turn/fact 级更容易；真实 Agent 回答时还需要在摘要内部定位具体事实。",
        "",
        "## 当前结论",
        "",
        "第一阶段已经可以证明：记忆压缩不是简单越短越好。更合理的结构是两层记忆：",
        "",
        "1. 在线检索层：以 observation/fact-level memory 为主，保留较细粒度，适合直接召回事实。",
        "2. 归档回溯层：以 session_summary 为主，保留完整上下文，适合做二次检索或回答补充。",
        "",
        "下一步若要继续提升 observation 覆盖率和质量，就需要接入大模型做 memory write：从原始对话中自动抽取事实、重要性、主体、时间、置信度和权限字段。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate LoCoMo compression variant results.")
    parser.add_argument("--build-dir", type=Path, required=True)
    parser.add_argument("--raw-summary", type=Path, required=True)
    parser.add_argument("--observation-summary", type=Path, required=True)
    parser.add_argument("--session-summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--csv-output", type=Path, required=True)
    args = parser.parse_args()

    storage = by_variant(read_csv(args.build_dir / "locomo_compression_storage.csv"))
    coverage = by_variant(read_csv(args.build_dir / "locomo_compression_coverage.csv"))
    raw_metrics = metric_row(args.raw_summary, "raw_turn")
    observation_metrics = metric_row(args.observation_summary, "observation")
    session_metrics = metric_row(args.session_summary, "session_summary")

    raw_row = {
        "variant": "raw_turn",
        "num_memories": 5882,
        "token_ratio_vs_raw": 1.0,
        "evidence_coverage": 1.0,
        **{key: raw_metrics[key] for key in ("recall@1", "recall@3", "recall@5", "mrr")},
    }
    rows = [raw_row]
    for variant, metrics in (("observation", observation_metrics), ("session_summary", session_metrics)):
        rows.append({
            "variant": variant,
            "num_memories": storage[variant]["num_memories"],
            "token_ratio_vs_raw": storage[variant]["token_ratio_vs_raw"],
            "evidence_coverage": coverage[variant]["evidence_coverage"],
            **{key: metrics[key] for key in ("recall@1", "recall@3", "recall@5", "mrr")},
        })

    write_csv(args.csv_output, rows)
    write_report(args.output, rows)
    print({"output": str(args.output), "csv_output": str(args.csv_output), "variants": [row["variant"] for row in rows]})


if __name__ == "__main__":
    main()
