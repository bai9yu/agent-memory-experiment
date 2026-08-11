#!/usr/bin/env python3
"""Analyze Top-K evidence-set coverage for reranked memory candidates."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def metric(value: float) -> str:
    return f"{value:.3f}"


def load_type_aware_ranked(rankings_path: Path, max_k: int) -> dict[str, list[str]]:
    ranked: dict[str, list[str]] = defaultdict(list)
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if len(ranked[row["query_id"]]) < max_k:
                ranked[row["query_id"]].append(row["memory_id"])
    return ranked


def load_candidate_ranked(path: Path, max_k: int) -> dict[tuple[str, str], list[str]]:
    ranked: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in read_csv(path):
        key = (row["split_seed"], row["query_id"])
        if len(ranked[key]) < max_k:
            ranked[key].append(row["memory_id"])
    return ranked


def coverage_for_ids(ranked_ids: list[str], gold_ids: set[str], k: int) -> dict[str, float]:
    top_ids = set(ranked_ids[:k])
    covered = top_ids & gold_ids
    return {
        f"any_hit@{k}": 1.0 if covered else 0.0,
        f"full_coverage@{k}": 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0,
        f"coverage_ratio@{k}": len(covered) / len(gold_ids) if gold_ids else 0.0,
    }


def build_rows(
    queries: dict[str, dict[str, Any]],
    type_aware_ranked: dict[str, list[str]],
    candidate_ranked: dict[tuple[str, str], list[str]],
    ks: list[int],
) -> list[dict[str, Any]]:
    rows = []
    for (seed, query_id), ranked_ids in sorted(candidate_ranked.items()):
        query = queries.get(query_id)
        if not query:
            continue
        gold_ids = set(query.get("answer_memory_ids", []))
        if not gold_ids:
            continue
        for method, ids in (
            ("type_aware", type_aware_ranked.get(query_id, [])),
            ("candidate_reranker", ranked_ids),
        ):
            row = {
                "split_seed": seed,
                "query_id": query_id,
                "query_type": query.get("type", "unknown"),
                "query": query.get("query", ""),
                "method": method,
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            }
            for k in ks:
                row.update(coverage_for_ids(ids, gold_ids, k))
            rows.append(row)
    return rows


def aggregate(rows: list[dict[str, Any]], ks: list[int], group_keys: list[str]) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[tuple(row[key] for key in group_keys)].append(row)
    summary = []
    for key, bucket in sorted(buckets.items()):
        out = {name: value for name, value in zip(group_keys, key)}
        out["num_rows"] = len(bucket)
        out["mean_gold"] = statistics.mean(row["num_gold"] for row in bucket)
        out["multi_evidence_share"] = statistics.mean(row["is_multi_evidence"] for row in bucket)
        for k in ks:
            for metric_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[metric_name] = statistics.mean(row[metric_name] for row in bucket)
        summary.append(out)
    return summary


def delta_by_type(summary_rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    by_key = {(row["query_type"], row["method"]): row for row in summary_rows}
    query_types = sorted({row["query_type"] for row in summary_rows}, key=lambda value: int(value) if str(value).isdigit() else 999)
    rows = []
    for query_type in query_types:
        base = by_key.get((query_type, "type_aware"))
        cand = by_key.get((query_type, "candidate_reranker"))
        if not base or not cand:
            continue
        out = {
            "query_type": query_type,
            "num_rows": cand["num_rows"],
            "mean_gold": cand["mean_gold"],
            "multi_evidence_share": cand["multi_evidence_share"],
        }
        for k in ks:
            for metric_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[f"baseline_{metric_name}"] = base[metric_name]
                out[f"candidate_{metric_name}"] = cand[metric_name]
                out[f"delta_{metric_name}"] = cand[metric_name] - base[metric_name]
        rows.append(out)
    return rows


def representative_type3(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        if row["query_type"] != "3":
            continue
        by_pair[(row["split_seed"], row["query_id"])][row["method"]] = row
    examples = []
    for (seed, query_id), methods in sorted(by_pair.items()):
        base = methods.get("type_aware")
        cand = methods.get("candidate_reranker")
        if not base or not cand:
            continue
        delta_full = cand["full_coverage@5"] - base["full_coverage@5"]
        delta_ratio = cand["coverage_ratio@5"] - base["coverage_ratio@5"]
        if delta_full == 0 and delta_ratio == 0:
            continue
        examples.append({
            "split_seed": seed,
            "query_id": query_id,
            "query": cand["query"],
            "num_gold": cand["num_gold"],
            "baseline_full@5": base["full_coverage@5"],
            "candidate_full@5": cand["full_coverage@5"],
            "delta_full@5": delta_full,
            "baseline_ratio@5": base["coverage_ratio@5"],
            "candidate_ratio@5": cand["coverage_ratio@5"],
            "delta_ratio@5": delta_ratio,
        })
    examples.sort(key=lambda row: (row["delta_full@5"], row["delta_ratio@5"]), reverse=True)
    return examples[:20]


def write_report(path: Path, delta_rows: list[dict[str, Any]], type3_examples: list[dict[str, Any]], ks: list[int]) -> None:
    primary_k = 5 if 5 in ks else max(ks)
    lines = [
        "# 多证据覆盖分析",
        "",
        "本报告评估 Top-K 候选集合对答案 evidence set 的覆盖情况，特别用于分析 Type 3 多证据/推理类 query。",
        "",
        f"## 按 Query Type 统计 @ {primary_k}",
        "",
        "| Query Type | Rows | Mean Gold | Multi-Evidence Share | Base Any | Reranker Any | Base Full | Reranker Full | Base Ratio | Reranker Ratio | Delta Ratio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in delta_rows:
        lines.append(
            f"| Type {row['query_type']} | {row['num_rows']} | {row['mean_gold']:.2f} | "
            f"{row['multi_evidence_share']:.3f} | {metric(row[f'baseline_any_hit@{primary_k}'])} | "
            f"{metric(row[f'candidate_any_hit@{primary_k}'])} | {metric(row[f'baseline_full_coverage@{primary_k}'])} | "
            f"{metric(row[f'candidate_full_coverage@{primary_k}'])} | {metric(row[f'baseline_coverage_ratio@{primary_k}'])} | "
            f"{metric(row[f'candidate_coverage_ratio@{primary_k}'])} | {row[f'delta_coverage_ratio@{primary_k}']:.4f} |"
        )
    lines.extend([
        "",
        "## Type 3 覆盖变化案例",
        "",
        "| Query | Gold | Base Full@5 | Reranker Full@5 | Base Ratio@5 | Reranker Ratio@5 | Delta Ratio@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in type3_examples[:12]:
        query = row["query"].replace("|", "/")
        lines.append(
            f"| {query} | {row['num_gold']} | {metric(row['baseline_full@5'])} | {metric(row['candidate_full@5'])} | "
            f"{metric(row['baseline_ratio@5'])} | {metric(row['candidate_ratio@5'])} | {row['delta_ratio@5']:.4f} |"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        "- `Any` 表示 Top-K 至少命中一条 evidence；`Full` 表示 Top-K 覆盖该 query 的全部 evidence；`Ratio` 表示覆盖比例。",
        "- 如果 Type 3 的 Full/Ratio 没有提升，即使总体 MRR 上升，也说明单候选重排没有解决多证据聚合。",
        "- 下一步应在 candidate reranker 之后增加 set-level selection 或 query decomposition，而不是只继续优化 Top-1。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Top-K evidence coverage for reranked candidates.")
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,10")
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-delta", type=Path, required=True)
    parser.add_argument("--output-type3-examples", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    max_k = max(ks)
    queries = read_jsonl(args.queries)
    type_aware_ranked = load_type_aware_ranked(args.rankings, max_k)
    candidate_ranked = load_candidate_ranked(args.candidate_ranked, max_k)
    rows = build_rows(queries, type_aware_ranked, candidate_ranked, ks)
    summary_rows = aggregate(rows, ks, ["query_type", "method"])
    delta_rows = delta_by_type(summary_rows, ks)
    type3_examples = representative_type3(rows)

    write_csv(args.output_per_query, rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_delta, delta_rows)
    write_csv(args.output_type3_examples, type3_examples)
    write_report(args.output_report, delta_rows, type3_examples, ks)
    print(json.dumps({
        "num_rows": len(rows),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
