#!/usr/bin/env python3
"""Export and merge blinded human-audit labels.

The blinded sheet hides LLM-assisted labels while keeping the retrieval context
needed for a human reviewer to judge the error analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any


AUDIT_FIELDS = (
    "auto_reason_correct",
    "top_memory_relevant",
    "gold_memory_sufficient",
)

HUMAN_FIELDS = (
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
)

BLIND_FIELDS = (
    "review_order",
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
    *HUMAN_FIELDS,
)

ALLOWED = {
    "auto_reason_correct": ("yes", "partial", "no"),
    "top_memory_relevant": ("yes", "partial", "no"),
    "gold_memory_sufficient": ("yes", "no", "unclear"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: tuple[str, ...] | list[str] | None = None) -> None:
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


def is_confirmed(row: dict[str, str]) -> bool:
    return all(norm(row.get(f"human_{field}", "")) for field in AUDIT_FIELDS)


def validation_errors(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        audit_id = row.get("audit_id", "unknown")
        for field in AUDIT_FIELDS:
            key = f"human_{field}"
            value = norm(row.get(key, ""))
            if value and value not in ALLOWED[field]:
                allowed = ", ".join(ALLOWED[field])
                errors.append(f"{audit_id}: {key}=`{row.get(key, '')}`; allowed: {allowed}")
    return errors


def export_rows(rows: list[dict[str, str]], seed: int, keep_order: bool) -> list[dict[str, str]]:
    out = []
    for row in rows:
        item = {field: row.get(field, "") for field in BLIND_FIELDS}
        out.append(item)
    if not keep_order:
        rng = random.Random(seed)
        rng.shuffle(out)
    for idx, row in enumerate(out, start=1):
        row["review_order"] = str(idx)
    return out


def merge_rows(source_rows: list[dict[str, str]], blind_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    blind_by_id = {row["audit_id"]: row for row in blind_rows if row.get("audit_id")}
    merged = []
    missing = []
    for row in source_rows:
        audit_id = row.get("audit_id", "")
        new_row = dict(row)
        blind_row = blind_by_id.get(audit_id)
        if blind_row is None:
            missing.append(audit_id)
        else:
            for field in HUMAN_FIELDS:
                new_row[field] = blind_row.get(field, row.get(field, ""))
        merged.append(new_row)
    if missing:
        raise RuntimeError(f"Blinded sheet is missing audit ids from source: {missing[:10]}")
    return merged


def write_report(path: Path, scope: str, mode: str, rows: list[dict[str, str]], errors: list[str], extra: dict[str, Any]) -> None:
    confirmed = [row for row in rows if is_confirmed(row)]
    lines = [
        "# Blinded Human Audit Sheet",
        "",
        "本文件记录盲审人工复核表的导出/回填状态。盲审表隐藏 LLM-assisted 预标注，只保留 query、top memory、gold memory 和待填写的 human_* 字段，用于降低人工审核被 LLM 标签锚定的风险。",
        "",
        "## 状态",
        "",
        f"- Scope: `{scope}`",
        f"- Mode: `{mode}`",
        f"- Samples: {len(rows)}",
        f"- Fully confirmed: {len(confirmed)}",
        f"- Validation errors: {len(errors)}",
    ]
    for key, value in extra.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## 盲审填写说明",
        "",
        "- 只填写 `human_manual_reason`、`human_auto_reason_correct`、`human_top_memory_relevant`、`human_gold_memory_sufficient`、`human_auditor_notes`。",
        "- `human_auto_reason_correct` / `human_top_memory_relevant` 允许：`yes`、`partial`、`no`。",
        "- `human_gold_memory_sufficient` 允许：`yes`、`no`、`unclear`。",
        "- 填完盲审表后用 `merge` 模式回填确认表，再运行 agreement 和 readiness gate。",
        "",
        "## 论文使用判断",
        "",
        "- 盲审流程可以写入实验协议，说明人工复核不直接暴露 LLM 预标注。",
        "- 在人工字段未完成前，仍不能宣称 human-verified error analysis。",
    ])
    if errors:
        lines.extend(["", "## 非法标签", ""])
        lines.extend([f"- {item}" for item in errors])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_export(args: argparse.Namespace) -> None:
    source_rows = read_csv(args.confirmation_csv)
    blind_rows = export_rows(source_rows, seed=args.seed, keep_order=args.keep_order)
    errors = validation_errors(blind_rows)
    write_csv(args.output_blind_csv, blind_rows, BLIND_FIELDS)
    write_report(
        args.output_report,
        args.scope,
        "export",
        blind_rows,
        errors,
        {
            "blind_csv": args.output_blind_csv,
            "source_confirmation": args.confirmation_csv,
            "seed": args.seed,
            "keep_order": args.keep_order,
        },
    )
    print(json.dumps({
        "mode": "export",
        "scope": args.scope,
        "samples": len(blind_rows),
        "output_blind_csv": str(args.output_blind_csv),
        "output_report": str(args.output_report),
        "validation_errors": len(errors),
    }, ensure_ascii=False, indent=2))


def run_merge(args: argparse.Namespace) -> None:
    source_rows = read_csv(args.confirmation_csv)
    blind_rows = read_csv(args.blind_csv)
    merged_rows = merge_rows(source_rows, blind_rows)
    errors = validation_errors(merged_rows)
    source_fieldnames = list(read_csv_header(args.confirmation_csv))
    write_csv(args.output_confirmation_csv, merged_rows, source_fieldnames)
    write_report(
        args.output_report,
        args.scope,
        "merge",
        merged_rows,
        errors,
        {
            "blind_csv": args.blind_csv,
            "source_confirmation": args.confirmation_csv,
            "output_confirmation": args.output_confirmation_csv,
        },
    )
    print(json.dumps({
        "mode": "merge",
        "scope": args.scope,
        "samples": len(merged_rows),
        "confirmed_samples": sum(1 for row in merged_rows if is_confirmed(row)),
        "output_confirmation_csv": str(args.output_confirmation_csv),
        "output_report": str(args.output_report),
        "validation_errors": len(errors),
    }, ensure_ascii=False, indent=2))


def read_csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return next(reader)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export or merge blinded human-audit labels.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--scope", required=True)
    export_parser.add_argument("--confirmation-csv", type=Path, required=True)
    export_parser.add_argument("--output-blind-csv", type=Path, required=True)
    export_parser.add_argument("--output-report", type=Path, required=True)
    export_parser.add_argument("--seed", type=int, default=20260811)
    export_parser.add_argument("--keep-order", action="store_true")
    export_parser.set_defaults(func=run_export)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--scope", required=True)
    merge_parser.add_argument("--confirmation-csv", type=Path, required=True)
    merge_parser.add_argument("--blind-csv", type=Path, required=True)
    merge_parser.add_argument("--output-confirmation-csv", type=Path, required=True)
    merge_parser.add_argument("--output-report", type=Path, required=True)
    merge_parser.set_defaults(func=run_merge)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
