#!/usr/bin/env python3
"""Create paper-ready query-type analysis tables from LoCoMo result summaries."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
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


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def load_summary_by_type(path: Path, variant: str) -> list[dict[str, Any]]:
    rows = []
    for row in read_csv(path):
        rows.append({
            "variant": variant,
            "query_type": row["query_type"],
            "method": row["method"],
            "num_queries": int(float(row["num_queries"])),
            "mrr": as_float(row, "mrr"),
            "recall@1": as_float(row, "recall@1"),
            "recall@3": as_float(row, "recall@3"),
            "recall@5": as_float(row, "recall@5"),
        })
    return sorted(rows, key=lambda item: (item["variant"], item["query_type"], item["method"]))


def delta_rows(rows: list[dict[str, Any]], variant: str, baseline: str, improved: str) -> list[dict[str, Any]]:
    by_key = {
        (row["variant"], row["query_type"], row["method"]): row
        for row in rows
    }
    deltas = []
    query_types = sorted({row["query_type"] for row in rows if row["variant"] == variant})
    for query_type in query_types:
        base = by_key.get((variant, query_type, baseline))
        new = by_key.get((variant, query_type, improved))
        if not base or not new:
            continue
        deltas.append({
            "variant": variant,
            "query_type": query_type,
            "num_queries": new["num_queries"],
            "baseline": baseline,
            "improved": improved,
            "delta_mrr": new["mrr"] - base["mrr"],
            "delta_recall@1": new["recall@1"] - base["recall@1"],
            "delta_recall@3": new["recall@3"] - base["recall@3"],
            "delta_recall@5": new["recall@5"] - base["recall@5"],
        })
    return deltas


def best_method_rows(rows: list[dict[str, Any]], variant: str, metric: str) -> list[dict[str, Any]]:
    result = []
    for query_type in sorted({row["query_type"] for row in rows if row["variant"] == variant}):
        candidates = [row for row in rows if row["variant"] == variant and row["query_type"] == query_type]
        if not candidates:
            continue
        best = max(candidates, key=lambda row: row[metric])
        result.append({
            "variant": variant,
            "query_type": query_type,
            "num_queries": best["num_queries"],
            "best_method": best["method"],
            f"best_{metric}": best[metric],
            "recall@1": best["recall@1"],
            "recall@5": best["recall@5"],
            "mrr": best["mrr"],
        })
    return result


def metric(value: float) -> str:
    return f"{value:.3f}"


def write_report(path: Path, rows: list[dict[str, Any]], deltas: list[dict[str, Any]], best_rows: list[dict[str, Any]]) -> None:
    llm_type_rows = [
        row for row in rows
        if row["variant"] == "llm_extracted_fact" and row["method"] in {"keyword", "vector", "hybrid", "time_aware", "type_aware"}
    ]
    observation_type_rows = [
        row for row in rows
        if row["variant"] == "locomo_observation" and row["method"] in {"keyword", "vector", "hybrid", "time_aware", "type_aware"}
    ]
    delta_by_type = {row["query_type"]: row for row in deltas if row["variant"] == "llm_extracted_fact"}
    best_by_variant = {}
    for row in best_rows:
        best_by_variant.setdefault(row["variant"], []).append(row)

    lines = [
        "# LoCoMo10 Query-Type Analysis",
        "",
        "本报告基于已完成的 LoCoMo10 answerable slice 实验，按原始 LoCoMo query type 统计检索表现。",
        "由于本地数据只保留 type 编号，以下使用 `Type 1` 到 `Type 5` 的数字标签，不强行解释语义类别。",
        "",
        "## DeepSeek Extracted Fact Memory",
        "",
        "| Query Type | Method | Queries | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in llm_type_rows:
        lines.append(
            f"| Type {row['query_type']} | {row['method']} | {row['num_queries']} | "
            f"{metric(row['recall@1'])} | {metric(row['recall@3'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## Type-Aware Gain Over Time-Aware",
        "",
        "| Query Type | Queries | Delta Recall@1 | Delta Recall@3 | Delta Recall@5 | Delta MRR |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for query_type in sorted(delta_by_type):
        row = delta_by_type[query_type]
        lines.append(
            f"| Type {query_type} | {row['num_queries']} | {metric(row['delta_recall@1'])} | "
            f"{metric(row['delta_recall@3'])} | {metric(row['delta_recall@5'])} | {metric(row['delta_mrr'])} |"
        )
    lines.extend([
        "",
        "## Best Method By Query Type",
        "",
        "| Variant | Query Type | Queries | Best Method | Recall@1 | Recall@5 | MRR |",
        "|---|---|---:|---|---:|---:|---:|",
    ])
    for variant in sorted(best_by_variant):
        for row in best_by_variant[variant]:
            lines.append(
                f"| {variant} | Type {row['query_type']} | {row['num_queries']} | {row['best_method']} | "
                f"{metric(row['recall@1'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
            )
    lines.extend([
        "",
        "## LoCoMo Observation Memory Reference",
        "",
        "| Query Type | Method | Queries | Recall@1 | Recall@5 | MRR |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in observation_type_rows:
        lines.append(
            f"| Type {row['query_type']} | {row['method']} | {row['num_queries']} | "
            f"{metric(row['recall@1'])} | {metric(row['recall@5'])} | {metric(row['mrr'])} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- DeepSeek extracted fact memory 在 Type 2 和 Type 4 上表现最高，说明当前 fact-level memory write 与 time/type-aware reranking 对这些问题较友好。",
        "- Type 3 是最困难类别，所有方法的 MRR 明显低于其他类型；后续应优先检查该类 query 的证据粒度、意图解析和 memory type 映射。",
        "- `type_aware` 相比 `time_aware` 的增益主要来自 Type 1、Type 2、Type 3 和 Type 5，Type 4 基本持平；这解释了总体显著但幅度较小的原因。",
        "- LoCoMo observation memory 在 Type 5 上弱于 DeepSeek extracted fact，说明 LLM fact extraction 对部分复杂/跨证据问题可能保留了更可检索的细节。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build query-type analysis from summary_by_type CSVs.")
    parser.add_argument("--llm-summary-by-type", type=Path, required=True)
    parser.add_argument("--observation-summary-by-type", type=Path, required=True)
    parser.add_argument("--output-combined-csv", type=Path, required=True)
    parser.add_argument("--output-delta-csv", type=Path, required=True)
    parser.add_argument("--output-best-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = []
    rows.extend(load_summary_by_type(args.llm_summary_by_type, "llm_extracted_fact"))
    rows.extend(load_summary_by_type(args.observation_summary_by_type, "locomo_observation"))
    deltas = delta_rows(rows, "llm_extracted_fact", "time_aware", "type_aware")
    best_rows = []
    best_rows.extend(best_method_rows(rows, "llm_extracted_fact", "mrr"))
    best_rows.extend(best_method_rows(rows, "locomo_observation", "mrr"))

    write_csv(args.output_combined_csv, rows)
    write_csv(args.output_delta_csv, deltas)
    write_csv(args.output_best_csv, best_rows)
    write_report(args.output_report, rows, deltas, best_rows)


if __name__ == "__main__":
    main()
