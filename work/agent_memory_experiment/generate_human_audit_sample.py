#!/usr/bin/env python3
"""Generate a human-audit sample for retrieval error analysis."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


AUDIT_FIELDS = [
    "audit_id",
    "query_id",
    "query",
    "query_type",
    "auto_reason",
    "first_rank",
    "top_memory_id",
    "top_memory_type",
    "top_memory_text",
    "gold_memory_ids",
    "gold_memory_types",
    "gold_memory_texts",
    "manual_reason",
    "auto_reason_correct",
    "top_memory_relevant",
    "gold_memory_sufficient",
    "auditor_notes",
]


REASON_DEFINITIONS = {
    "memory_type_mismatch": "Top-1 记忆主题相关但 memory type 与问题所需类型不匹配。",
    "gold_below_top20": "正确 gold evidence 没有进入 Top-20，主要是候选召回失败。",
    "identity_neighbor": "Top-1 与人物身份相关，但身份属性或目标人物不对。",
    "semantic_neighbor": "Top-1 与问题语义相近，但回答的是相邻事实而非目标事实。",
    "temporal_neighbor": "Top-1 涉及相近事件或人物，但时间点不对。",
    "persona_confusion": "Top-1 混淆了说话人、人物身份或关系主体。",
    "activity_neighbor": "Top-1 与活动/经历相近，但不是问题要问的活动。",
    "preference_neighbor": "Top-1 与偏好相近，但不是问题要问的偏好。",
    "career_education_neighbor": "Top-1 与职业/教育相关，但不是目标事实。",
    "location_neighbor": "Top-1 与地点相关，但地点或事件不对。",
    "relationship_neighbor": "Top-1 与关系相关，但关系类型、对象或状态不对。",
    "other": "以上类别都不准确，或需要人工补充新的错误原因。",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def stratified_sample(rows: list[dict[str, str]], total: int, per_reason_min: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["reason"]].append(row)

    selected: list[dict[str, str]] = []
    selected_ids: set[str] = set()
    for reason in sorted(groups):
        bucket = groups[reason][:]
        rng.shuffle(bucket)
        take = min(per_reason_min, len(bucket))
        for row in bucket[:take]:
            selected.append(row)
            selected_ids.add(row["query_id"])

    remaining = [row for row in rows if row["query_id"] not in selected_ids]
    rng.shuffle(remaining)
    selected.extend(remaining[: max(0, total - len(selected))])
    selected = selected[:total]
    selected.sort(key=lambda row: (row["reason"], row["query_id"]))
    return selected


def to_audit_rows(sample: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for idx, row in enumerate(sample, start=1):
        rows.append({
            "audit_id": f"audit_{idx:03d}",
            "query_id": row["query_id"],
            "query": row["query"],
            "query_type": row["query_type"],
            "auto_reason": row["reason"],
            "first_rank": row["first_rank"],
            "top_memory_id": row["top_memory_id"],
            "top_memory_type": row["top_memory_type"],
            "top_memory_text": row["top_memory_text"],
            "gold_memory_ids": row["gold_memory_ids"],
            "gold_memory_types": row["gold_memory_types"],
            "gold_memory_texts": row["gold_memory_texts"],
            "manual_reason": "",
            "auto_reason_correct": "",
            "top_memory_relevant": "",
            "gold_memory_sufficient": "",
            "auditor_notes": "",
        })
    return rows


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return counts


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, source_rows: list[dict[str, str]], audit_rows: list[dict[str, str]], seed: int, per_reason_min: int) -> None:
    reason_counts = count_by(audit_rows, "auto_reason")
    type_counts = count_by(audit_rows, "query_type")
    reason_rows = [[reason, str(reason_counts[reason]), REASON_DEFINITIONS.get(reason, "待人工定义。")] for reason in sorted(reason_counts)]
    type_rows = [[query_type, str(type_counts[query_type])] for query_type in sorted(type_counts, key=lambda item: int(item))]
    lines = [
        "# 人工错误复核抽样包",
        "",
        "本文件用于对自动错误分析结果做人工抽样复核。目标不是重新跑实验，而是检查自动错误类别是否可信，并为论文中的错误分析提供人工可靠性证据。",
        "",
        "## 抽样设置",
        "",
        f"- 来源错误样本数：{len(source_rows)}",
        f"- 人工复核样本数：{len(audit_rows)}",
        f"- 随机种子：{seed}",
        f"- 每个自动错误类型最低抽样数：{per_reason_min}",
        "",
        "## 样本分布：自动错误类型",
        "",
        markdown_table(["Auto Reason", "Sample Count", "判定说明"], reason_rows),
        "",
        "## 样本分布：Query Type",
        "",
        markdown_table(["Query Type", "Sample Count"], type_rows),
        "",
        "## 标注字段说明",
        "",
        "- `manual_reason`：人工认为最合适的错误类型；可以沿用自动 reason，也可以填写新的类别。",
        "- `auto_reason_correct`：填写 `yes` / `no` / `partial`，表示自动 reason 是否正确。",
        "- `top_memory_relevant`：填写 `yes` / `no` / `partial`，表示 Top-1 memory 是否与问题有关。",
        "- `gold_memory_sufficient`：填写 `yes` / `no` / `unclear`，表示 gold memory 是否足以回答问题。",
        "- `auditor_notes`：记录判断依据、歧义点或新增错误类型。",
        "",
        "## 论文使用方式",
        "",
        "完成标注后，可以统计 `auto_reason_correct` 的 yes / partial / no 比例，作为自动错误分析可靠性的补充证据。如果 `gold_memory_sufficient=no` 的比例较高，需要在论文中说明该数据集标注本身存在证据不充分问题。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate human audit sample for retrieval errors.")
    parser.add_argument("--errors", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=80)
    parser.add_argument("--per-reason-min", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260811)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    errors = read_csv(args.errors)
    sample = stratified_sample(errors, args.sample_size, args.per_reason_min, args.seed)
    audit_rows = to_audit_rows(sample)
    write_csv(args.output_csv, audit_rows, AUDIT_FIELDS)
    write_report(args.output_report, errors, audit_rows, args.seed, args.per_reason_min)
    print(json.dumps({
        "source_errors": len(errors),
        "audit_samples": len(audit_rows),
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
