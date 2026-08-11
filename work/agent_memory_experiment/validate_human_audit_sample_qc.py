#!/usr/bin/env python3
"""Validate sample coverage and labeling readiness for human-audit sheets."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_HUMAN_FIELDS = (
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def norm(value: str) -> str:
    return value.strip()


def rank_bucket(value: str) -> str:
    try:
        rank = int(float(value))
    except ValueError:
        return "unknown"
    if rank <= 1:
        return "rank_1"
    if rank <= 5:
        return "rank_2_5"
    if rank <= 10:
        return "rank_6_10"
    if rank <= 20:
        return "rank_11_20"
    return "rank_gt_20"


def is_confirmed(row: dict[str, str]) -> bool:
    return all(norm(row.get(field, "")) for field in REQUIRED_HUMAN_FIELDS)


def count_values(rows: list[dict[str, str]], key: str) -> Counter[str]:
    values: Counter[str] = Counter()
    for row in rows:
        value = norm(row.get(key, "")) or "missing"
        values[value] += 1
    return values


def distribution_rows(scope: str, rows: list[dict[str, str]], key: str, label: str) -> list[dict[str, Any]]:
    counts = count_values(rows, key)
    total = len(rows)
    return [
        {
            "scope": scope,
            "group": label,
            "value": value,
            "count": count,
            "total": total,
            "share": count / total if total else 0.0,
            "status": "info",
            "evidence": f"{label}={value}",
        }
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def missing_field_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows for field in REQUIRED_HUMAN_FIELDS if not norm(row.get(field, "")))


def sample_summary(scope: str, rows: list[dict[str, str]], expected: int) -> list[dict[str, Any]]:
    audit_ids = [row.get("audit_id", "") for row in rows]
    duplicate_ids = len(audit_ids) - len(set(audit_ids))
    confirmed = sum(1 for row in rows if is_confirmed(row))
    reason_count = len(count_values(rows, "auto_reason"))
    type_count = len(count_values(rows, "query_type"))
    rank_buckets = Counter(rank_bucket(row.get("first_rank", "")) for row in rows)
    return [
        {
            "scope": scope,
            "group": "overview",
            "value": "sample_count",
            "count": len(rows),
            "total": expected,
            "share": len(rows) / expected if expected else 0.0,
            "status": "pass" if len(rows) == expected else "fail",
            "evidence": f"expected={expected}",
        },
        {
            "scope": scope,
            "group": "overview",
            "value": "duplicate_audit_ids",
            "count": duplicate_ids,
            "total": len(rows),
            "share": duplicate_ids / len(rows) if rows else 0.0,
            "status": "pass" if duplicate_ids == 0 else "fail",
            "evidence": "audit_id should be unique within scope",
        },
        {
            "scope": scope,
            "group": "overview",
            "value": "confirmed_samples",
            "count": confirmed,
            "total": len(rows),
            "share": confirmed / len(rows) if rows else 0.0,
            "status": "pending_human_labels" if confirmed < len(rows) else "pass",
            "evidence": "not required for sample QC; tracked for labeling progress",
        },
        {
            "scope": scope,
            "group": "overview",
            "value": "missing_required_human_fields",
            "count": missing_field_count(rows),
            "total": len(rows) * len(REQUIRED_HUMAN_FIELDS),
            "share": missing_field_count(rows) / (len(rows) * len(REQUIRED_HUMAN_FIELDS)) if rows else 0.0,
            "status": "pending_human_labels" if missing_field_count(rows) else "pass",
            "evidence": ",".join(REQUIRED_HUMAN_FIELDS),
        },
        {
            "scope": scope,
            "group": "coverage",
            "value": "auto_reason_types",
            "count": reason_count,
            "total": reason_count,
            "share": 1.0 if reason_count else 0.0,
            "status": "pass" if reason_count >= 3 else "warning",
            "evidence": "sample should cover multiple automatic error categories",
        },
        {
            "scope": scope,
            "group": "coverage",
            "value": "query_types",
            "count": type_count,
            "total": type_count,
            "share": 1.0 if type_count else 0.0,
            "status": "pass" if type_count >= 3 else "warning",
            "evidence": "sample should cover multiple LoCoMo query types",
        },
        {
            "scope": scope,
            "group": "coverage",
            "value": "rank_buckets",
            "count": len(rank_buckets),
            "total": len(rank_buckets),
            "share": 1.0 if rank_buckets else 0.0,
            "status": "pass" if len(rank_buckets) >= 3 else "warning",
            "evidence": ";".join(f"{key}={value}" for key, value in sorted(rank_buckets.items())),
        },
    ]


def overlap_rows(priority: list[dict[str, str]], full: list[dict[str, str]]) -> list[dict[str, Any]]:
    priority_qids = {row.get("query_id", "") for row in priority}
    full_qids = {row.get("query_id", "") for row in full}
    overlap = len(priority_qids & full_qids)
    return [{
        "scope": "priority20_vs_full80",
        "group": "overlap",
        "value": "priority_queries_in_full80",
        "count": overlap,
        "total": len(priority_qids),
        "share": overlap / len(priority_qids) if priority_qids else 0.0,
        "status": "pass" if overlap == len(priority_qids) else "warning",
        "evidence": "priority20 is expected to be a focused subset or compatible slice of full80",
    }]


def build_rows(priority_csv: Path, full_csv: Path) -> list[dict[str, Any]]:
    priority = read_csv(priority_csv)
    full = read_csv(full_csv)
    rows: list[dict[str, Any]] = []
    rows.extend(sample_summary("priority20", priority, expected=20))
    rows.extend(sample_summary("full80", full, expected=80))
    rows.extend(overlap_rows(priority, full))
    for scope, sample_rows in (("priority20", priority), ("full80", full)):
        rows.extend(distribution_rows(scope, sample_rows, "auto_reason", "auto_reason_distribution"))
        rows.extend(distribution_rows(scope, sample_rows, "query_type", "query_type_distribution"))
        bucketed = [dict(row, first_rank_bucket=rank_bucket(row.get("first_rank", ""))) for row in sample_rows]
        rows.extend(distribution_rows(scope, bucketed, "first_rank_bucket", "first_rank_bucket_distribution"))
        rows.extend(distribution_rows(scope, sample_rows, "top_memory_type", "top_memory_type_distribution"))
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_report(path: Path, rows: list[dict[str, Any]], priority_csv: Path, full_csv: Path) -> None:
    overview = [row for row in rows if row["group"] in {"overview", "coverage", "overlap"}]
    failures = [row for row in overview if row["status"] == "fail"]
    warnings = [row for row in overview if row["status"] == "warning"]
    pending = [row for row in overview if row["status"] == "pending_human_labels"]
    dist = [row for row in rows if row["group"].endswith("_distribution")]
    overview_table = [
        [row["scope"], row["group"], row["value"], str(row["count"]), str(row["total"]), fmt(row["share"]), row["status"], row["evidence"]]
        for row in overview
    ]
    dist_table = [
        [row["scope"], row["group"], row["value"], str(row["count"]), fmt(row["share"])]
        for row in dist
    ]
    lines = [
        "# Human Audit Sample QC",
        "",
        "本文件检查 priority20/full80 人工复核样本的结构质量：样本数、重复、错误类型覆盖、query type 覆盖、rank 区间覆盖和标注完成进度。它不自动填写人工标签，也不把空白标注当作已完成结果。",
        "",
        "## 总览",
        "",
        f"- Priority CSV: `{priority_csv}`",
        f"- Full CSV: `{full_csv}`",
        f"- Blocking QC failures: {len(failures)}",
        f"- Coverage warnings: {len(warnings)}",
        f"- Pending human-label progress rows: {len(pending)}",
        f"- Sample QC pass: {len(failures) == 0}",
        "",
        "## QC 明细",
        "",
        markdown_table(["Scope", "Group", "Value", "Count", "Total", "Share", "Status", "Evidence"], overview_table),
        "",
        "## 分布明细",
        "",
        markdown_table(["Scope", "Group", "Value", "Count", "Share"], dist_table),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：人工复核样本已经通过样本数、去重和覆盖性 QC，适合进入人工标注。",
        "- 可以写：priority20/full80 的错误类型、query type 和 first-rank 区间分布可复现记录。",
        "- 不能写：人工标注已经完成或错误分析已经 human-verified；这仍取决于 human_* 字段是否填写并通过 agreement/readiness gate。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate human audit sample coverage and labeling progress.")
    parser.add_argument("--priority-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--full-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.priority_csv, args.full_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.priority_csv, args.full_csv)
    failures = sum(1 for row in rows if row["group"] in {"overview", "coverage", "overlap"} and row["status"] == "fail")
    warnings = sum(1 for row in rows if row["group"] in {"overview", "coverage", "overlap"} and row["status"] == "warning")
    print(json.dumps({
        "output_report": str(args.output_report),
        "rows": len(rows),
        "blocking_qc_failures": failures,
        "coverage_warnings": warnings,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
