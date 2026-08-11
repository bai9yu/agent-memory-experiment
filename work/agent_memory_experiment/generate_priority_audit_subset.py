#!/usr/bin/env python3
"""Select a small high-value Human/LLM audit subset for quick manual review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def norm(value: str) -> str:
    return value.strip().lower()


def priority_score(row: dict[str, str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    auto_correct = norm(row.get("llm_auto_reason_correct", ""))
    top_relevant = norm(row.get("llm_top_memory_relevant", ""))
    gold_sufficient = norm(row.get("llm_gold_memory_sufficient", ""))
    auto_reason = row.get("auto_reason", "")
    first_rank = int(row.get("first_rank") or 0)
    query_type = row.get("query_type", "")

    if auto_correct == "no":
        score += 5
        reasons.append("LLM 认为自动错误类型不正确")
    elif auto_correct == "partial":
        score += 3
        reasons.append("LLM 认为自动错误类型只有部分正确")
    if top_relevant == "no":
        score += 3
        reasons.append("Top memory 被判为不相关")
    elif top_relevant == "partial":
        score += 1
        reasons.append("Top memory 只有部分相关")
    if gold_sufficient in {"no", "unclear"}:
        score += 4
        reasons.append("gold evidence 充分性存疑")
    if auto_reason in {"persona_confusion", "relationship_neighbor", "other", "temporal_neighbor"}:
        score += 2
        reasons.append(f"覆盖高歧义错误类型 {auto_reason}")
    if query_type == "3":
        score += 2
        reasons.append("覆盖 Type 3 多证据问题")
    if first_rank > 20:
        score += 2
        reasons.append("gold evidence 排名较低")
    elif first_rank > 5:
        score += 1
        reasons.append("gold evidence 未进入 Top-5")
    return score, reasons


def select_subset(rows: list[dict[str, str]], size: int) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        score, reasons = priority_score(row)
        enriched.append({
            "audit_id": row["audit_id"],
            "query_id": row["query_id"],
            "query_type": row["query_type"],
            "auto_reason": row["auto_reason"],
            "first_rank": row["first_rank"],
            "llm_auto_reason_correct": row["llm_auto_reason_correct"],
            "llm_top_memory_relevant": row["llm_top_memory_relevant"],
            "llm_gold_memory_sufficient": row["llm_gold_memory_sufficient"],
            "priority_score": score,
            "selection_reason": "; ".join(reasons),
        })
    enriched.sort(key=lambda row: (-int(row["priority_score"]), row["auto_reason"], row["audit_id"]))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    # Ensure the quick-review pack is not only "hard negatives"; cover every LLM label family first.
    for field, values in (
        ("llm_auto_reason_correct", ("no", "partial", "yes")),
        ("llm_gold_memory_sufficient", ("no", "unclear")),
        ("query_type", ("3",)),
    ):
        for value in values:
            for row in enriched:
                if row["audit_id"] not in selected_ids and row[field] == value:
                    selected.append(row)
                    selected_ids.add(row["audit_id"])
                    break
    for row in enriched:
        if len(selected) >= size:
            break
        if row["audit_id"] not in selected_ids:
            selected.append(row)
            selected_ids.add(row["audit_id"])
    selected.sort(key=lambda row: row["audit_id"])
    return selected


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, selected: list[dict[str, Any]]) -> None:
    reason_counts = Counter(row["auto_reason"] for row in selected)
    label_counts = Counter(row["llm_auto_reason_correct"] for row in selected)
    lines = [
        "# Human/LLM 优先人工抽查包",
        "",
        "本文件从 80 条 Human/LLM 确认样本中选出 20 条优先人工抽查样本。目标是先用较小标注成本检查 LLM-assisted 预标注和自动错误分类是否可靠；它不能替代完整 80 条人工确认。",
        "",
        "## 抽样原则",
        "",
        "- 优先选择 LLM 认为 `auto_reason_correct=no/partial` 的样本。",
        "- 优先选择 `gold_memory_sufficient=no/unclear`、Top memory 不相关、persona/relationship/temporal/other 等高歧义类型。",
        "- 保留部分 `yes` 样本作为 sanity check，避免只看困难样本。",
        "- 抽样结果写入 id 文件后，可以复用 `confirm_llm_audit_labels.py --audit-id-csv` 生成独立一致性报告。",
        "",
        "## 分布",
        "",
        markdown_table(["Auto Reason", "Count"], [[key, str(reason_counts[key])] for key in sorted(reason_counts)]),
        "",
        markdown_table(["LLM auto_reason_correct", "Count"], [[key, str(label_counts[key])] for key in sorted(label_counts)]),
        "",
        "## 样本列表",
        "",
        markdown_table(
            ["Audit ID", "Query ID", "Type", "Auto Reason", "LLM Label", "Score", "Selection Reason"],
            [
                [
                    row["audit_id"],
                    row["query_id"],
                    row["query_type"],
                    row["auto_reason"],
                    row["llm_auto_reason_correct"],
                    str(row["priority_score"]),
                    row["selection_reason"],
                ]
                for row in selected
            ],
        ),
        "",
        "## 人工填写指南",
        "",
        "- 打开 `outputs/agent_memory_human_llm_audit_priority20_confirmation.csv`。",
        "- 只填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。",
        "- 完成后重新运行 priority20 agreement 命令，得到 quick-review exact agreement 和 Cohen's kappa。",
        "- 论文中可写为抽样人工确认；若要写完整 human audit，仍需填写 80 条确认表。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate priority Human/LLM audit subset.")
    parser.add_argument("--confirmation-csv", type=Path, required=True)
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--output-id-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_csv(args.confirmation_csv)
    selected = select_subset(rows, args.sample_size)
    write_csv(args.output_id_csv, selected, [
        "audit_id",
        "query_id",
        "query_type",
        "auto_reason",
        "first_rank",
        "llm_auto_reason_correct",
        "llm_top_memory_relevant",
        "llm_gold_memory_sufficient",
        "priority_score",
        "selection_reason",
    ])
    write_report(args.output_report, selected)
    print(json.dumps({
        "selected": len(selected),
        "output_id_csv": str(args.output_id_csv),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
