#!/usr/bin/env python3
"""Generate a readable human-audit review packet from a blinded audit CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


AUDIT_FIELDS = (
    ("human_auto_reason_correct", "自动错误类型是否正确", "yes / partial / no"),
    ("human_top_memory_relevant", "Top memory 是否回答或部分回答 query", "yes / partial / no"),
    ("human_gold_memory_sufficient", "Gold memory 是否足以支持答案判断", "yes / no / unclear"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def norm(value: str) -> str:
    return value.strip()


def is_confirmed(row: dict[str, str]) -> bool:
    return all(norm(row.get(field, "")) for field, _, _ in AUDIT_FIELDS)


def md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def split_gold_items(ids: str, types: str, texts: str) -> list[tuple[str, str, str]]:
    id_items = [item.strip() for item in ids.split("|") if item.strip()]
    type_items = [item.strip() for item in types.split("|") if item.strip()]
    text_items = [item.strip() for item in texts.split(" || ") if item.strip()]
    n = max(len(id_items), len(type_items), len(text_items))
    out = []
    for idx in range(n):
        out.append((
            id_items[idx] if idx < len(id_items) else "",
            type_items[idx] if idx < len(type_items) else "",
            text_items[idx] if idx < len(text_items) else "",
        ))
    return out


def write_packet(path: Path, rows: list[dict[str, str]], source_csv: Path, scope: str) -> None:
    confirmed = sum(1 for row in rows if is_confirmed(row))
    lines = [
        f"# {scope} 人工复核阅读包",
        "",
        "本阅读包由盲审 CSV 自动生成，只展示人工判断所需的 query、自动错误类型、Top memory 和 gold memory；不展示 LLM-assisted 预标注，避免人工复核被模型标签锚定。",
        "",
        "## 使用方式",
        "",
        f"- 源盲审表：`{source_csv}`",
        f"- 样本数：{len(rows)}",
        f"- 已完整填写：{confirmed}/{len(rows)}",
        "- 阅读每个样本后，把判断结果回填到源 CSV 的 `human_*` 字段。",
        "- 完成后运行 merge/agreement/readiness 脚本，生成 Human/LLM agreement 和门禁结果。",
        "",
        "## 字段取值",
        "",
        "| 字段 | 判断问题 | 允许取值 |",
        "|---|---|---|",
    ]
    for field, question, allowed in AUDIT_FIELDS:
        lines.append(f"| `{field}` | {question} | `{allowed}` |")
    lines.extend([
        "",
        "## 快速填写表",
        "",
        "| Review | Audit ID | Query ID | auto_reason_correct | top_memory_relevant | gold_memory_sufficient | Notes |",
        "|---:|---|---|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row.get('review_order', '')} | {row.get('audit_id', '')} | {row.get('query_id', '')} |  |  |  |  |"
        )
    lines.extend(["", "## 样本卡片", ""])
    for row in rows:
        lines.extend([
            f"### {row.get('review_order', '')}. {row.get('audit_id', '')} / {row.get('query_id', '')}",
            "",
            "| 项目 | 内容 |",
            "|---|---|",
            f"| Query type | {md_escape(row.get('query_type', ''))} |",
            f"| Query | {md_escape(row.get('query', ''))} |",
            f"| 自动错误类型 | `{md_escape(row.get('auto_reason', ''))}` |",
            f"| First rank | {md_escape(row.get('first_rank', ''))} |",
            f"| Top memory | `{md_escape(row.get('top_memory_id', ''))}` / `{md_escape(row.get('top_memory_type', ''))}`：{md_escape(row.get('top_memory_text', ''))} |",
            "",
            "**Gold memory**",
            "",
            "| Gold ID | Type | Text |",
            "|---|---|---|",
        ])
        for gold_id, gold_type, gold_text in split_gold_items(
            row.get("gold_memory_ids", ""),
            row.get("gold_memory_types", ""),
            row.get("gold_memory_texts", ""),
        ):
            lines.append(f"| `{md_escape(gold_id)}` | `{md_escape(gold_type)}` | {md_escape(gold_text)} |")
        lines.extend([
            "",
            "**待填写**",
            "",
            "- `human_auto_reason_correct`: ",
            "- `human_top_memory_relevant`: ",
            "- `human_gold_memory_sufficient`: ",
            "- `human_manual_reason`: ",
            "- `human_auditor_notes`: ",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a readable blinded human-audit review packet.")
    parser.add_argument("--scope", default="priority20")
    parser.add_argument("--blind-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_csv(args.blind_csv)
    write_packet(args.output_report, rows, args.blind_csv, args.scope)
    print(json.dumps({
        "scope": args.scope,
        "samples": len(rows),
        "confirmed": sum(1 for row in rows if is_confirmed(row)),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
