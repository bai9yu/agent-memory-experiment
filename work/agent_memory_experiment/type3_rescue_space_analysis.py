#!/usr/bin/env python3
"""Analyze Type-3 evidence rescue space inside cached ranked candidates."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from query_type_router_experiment import metric, write_csv


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_queries(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    return rows


def load_ranked(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row.get("memory_type", ""),
            "memory_text": row.get("memory_text", ""),
            "learned_score": float(row.get("learned_score", "0") or 0),
            "is_relevant": row.get("is_relevant") == "True",
        })
    for rows in groups.values():
        rows.sort(key=lambda row: row["rank"])
    return groups


def coverage(ids: list[str], gold_ids: set[str]) -> float:
    return len(set(ids) & gold_ids) / len(gold_ids) if gold_ids else 0.0


def full(ids: list[str], gold_ids: set[str]) -> float:
    return 1.0 if gold_ids and gold_ids.issubset(set(ids)) else 0.0


def first_rank(ids: list[str], gold_ids: set[str]) -> int:
    for rank, memory_id in enumerate(ids, start=1):
        if memory_id in gold_ids:
            return rank
    return 0


def classify_query(top5: list[str], top20: list[str], gold_ids: set[str]) -> str:
    top5_cov = coverage(top5, gold_ids)
    top20_cov = coverage(top20, gold_ids)
    if full(top5, gold_ids):
        return "top5_already_full"
    if top5_cov == 0 and top20_cov == 0:
        return "candidate_missing_all_gold"
    if top20_cov > top5_cov:
        return "rerank_rescuable_from_top20"
    if top20_cov == top5_cov and top20_cov > 0:
        return "partial_but_not_improvable_within_top20"
    return "candidate_missing_required_gold"


def oracle_top5(ids: list[str], gold_ids: set[str]) -> list[str]:
    relevant = [memory_id for memory_id in ids if memory_id in gold_ids]
    non_relevant = [memory_id for memory_id in ids if memory_id not in gold_ids]
    return (relevant + non_relevant)[:5]


def build_rows(groups: dict[tuple[str, str], list[dict[str, Any]]], queries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for (seed, query_id), rows in sorted(groups.items()):
        query = queries.get(query_id)
        if not query or str(query.get("type")) != "3":
            continue
        gold_ids = set(query.get("answer_memory_ids", []))
        ids = [row["memory_id"] for row in rows]
        top5 = ids[:5]
        top20 = ids[:20]
        oracle5 = oracle_top5(top20, gold_ids)
        top5_rank = first_rank(top5, gold_ids)
        oracle_rank = first_rank(oracle5, gold_ids)
        out.append({
            "split_seed": seed,
            "query_id": query_id,
            "query": query.get("query", ""),
            "num_gold": len(gold_ids),
            "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
            "class": classify_query(top5, top20, gold_ids),
            "top5_coverage": coverage(top5, gold_ids),
            "top5_full": full(top5, gold_ids),
            "top20_coverage": coverage(top20, gold_ids),
            "top20_full": full(top20, gold_ids),
            "oracle_top5_coverage": coverage(oracle5, gold_ids),
            "oracle_top5_full": full(oracle5, gold_ids),
            "top5_mrr": 1.0 / top5_rank if top5_rank else 0.0,
            "oracle_top5_mrr": 1.0 / oracle_rank if oracle_rank else 0.0,
            "coverage_rescue_gap": coverage(oracle5, gold_ids) - coverage(top5, gold_ids),
            "full_rescue_gap": full(oracle5, gold_ids) - full(top5, gold_ids),
        })
    return out


def aggregate(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    total = len(rows)
    classes = Counter(row["class"] for row in rows)
    class_rows = []
    for name, count in sorted(classes.items()):
        bucket = [row for row in rows if row["class"] == name]
        class_rows.append({
            "class": name,
            "rows": count,
            "share": count / total if total else 0.0,
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
            "top5_coverage": statistics.mean(row["top5_coverage"] for row in bucket),
            "top20_coverage": statistics.mean(row["top20_coverage"] for row in bucket),
            "oracle_top5_coverage": statistics.mean(row["oracle_top5_coverage"] for row in bucket),
            "coverage_rescue_gap": statistics.mean(row["coverage_rescue_gap"] for row in bucket),
            "full_rescue_gap": statistics.mean(row["full_rescue_gap"] for row in bucket),
        })
    summary = [{
        "scope": "all_type3_candidate_reranker_top20",
        "rows": total,
        "mean_gold": statistics.mean(row["num_gold"] for row in rows),
        "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in rows),
        "top5_mrr": statistics.mean(row["top5_mrr"] for row in rows),
        "oracle_top5_mrr": statistics.mean(row["oracle_top5_mrr"] for row in rows),
        "top5_coverage": statistics.mean(row["top5_coverage"] for row in rows),
        "top5_full": statistics.mean(row["top5_full"] for row in rows),
        "top20_coverage": statistics.mean(row["top20_coverage"] for row in rows),
        "top20_full": statistics.mean(row["top20_full"] for row in rows),
        "oracle_top5_coverage": statistics.mean(row["oracle_top5_coverage"] for row in rows),
        "oracle_top5_full": statistics.mean(row["oracle_top5_full"] for row in rows),
        "coverage_rescue_gap": statistics.mean(row["coverage_rescue_gap"] for row in rows),
        "full_rescue_gap": statistics.mean(row["full_rescue_gap"] for row in rows),
        "rerank_rescuable_share": classes["rerank_rescuable_from_top20"] / total if total else 0.0,
        "candidate_missing_all_gold_share": classes["candidate_missing_all_gold"] / total if total else 0.0,
    }]
    return summary, class_rows


def write_report(path: Path, summary: list[dict[str, Any]], class_rows: list[dict[str, Any]], examples: list[dict[str, Any]]) -> None:
    row = summary[0]
    lines = [
        "# Type 3 Top-20 救回空间分析",
        "",
        "本分析不作为实际检索方法，而是诊断 Type 3 多证据问题的优化空间：在 candidate reranker 已落盘的 Top-20 候选里，检查有多少问题可以通过更好的集合/列表重排把证据救回 Top-5。",
        "",
        "## 总体上限",
        "",
        "| 指标 | 当前 Top-5 | Top-20 覆盖 | Oracle Top-5 | 可救回空间 |",
        "|---|---:|---:|---:|---:|",
        f"| MRR | {metric(row['top5_mrr'])} | - | {metric(row['oracle_top5_mrr'])} | {row['oracle_top5_mrr'] - row['top5_mrr']:+.4f} |",
        f"| Coverage | {metric(row['top5_coverage'])} | {metric(row['top20_coverage'])} | {metric(row['oracle_top5_coverage'])} | {row['coverage_rescue_gap']:+.4f} |",
        f"| Full Coverage | {metric(row['top5_full'])} | {metric(row['top20_full'])} | {metric(row['oracle_top5_full'])} | {row['full_rescue_gap']:+.4f} |",
        "",
        "## 问题分型",
        "",
        "| 类型 | Rows | Share | Top5 Coverage | Top20 Coverage | Oracle Top5 Coverage | Coverage Gap | Full Gap |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in class_rows:
        lines.append(
            f"| {item['class']} | {item['rows']} | {metric(item['share'])} | {metric(item['top5_coverage'])} | "
            f"{metric(item['top20_coverage'])} | {metric(item['oracle_top5_coverage'])} | "
            f"{item['coverage_rescue_gap']:+.4f} | {item['full_rescue_gap']:+.4f} |"
        )
    lines.extend([
        "",
        "## 代表性可救回问题",
        "",
        "| Query | Gold 数 | Top5 Coverage | Top20 Coverage | Oracle Top5 Coverage |",
        "|---|---:|---:|---:|---:|",
    ])
    for item in examples[:10]:
        lines.append(
            f"| {item['query'].replace('|', '/')} | {item['num_gold']} | {metric(item['top5_coverage'])} | "
            f"{metric(item['top20_coverage'])} | {metric(item['oracle_top5_coverage'])} |"
        )
    lines.extend([
        "",
        "## 结论",
        "",
        "- 如果 `rerank_rescuable_from_top20` 占比较高，下一步应做学习式 listwise/setwise 重排。",
        "- 如果 `candidate_missing_all_gold` 占比较高，下一步应先增强召回，例如 LLM 子问题生成、真实 embedding 或更大的候选池。",
        "- 该分析使用 gold evidence 计算上限，不可作为实际部署方法，只用于确定优化方向。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Type-3 rescue space from ranked candidates.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-classes", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    groups = load_ranked(args.candidate_ranked)
    queries = read_queries(args.queries)
    rows = build_rows(groups, queries)
    summary, class_rows = aggregate(rows)
    examples = sorted(
        [row for row in rows if row["class"] == "rerank_rescuable_from_top20"],
        key=lambda row: (row["coverage_rescue_gap"], row["full_rescue_gap"], row["num_gold"]),
        reverse=True,
    )
    write_csv(args.output_per_query, rows)
    write_csv(args.output_summary, summary)
    write_csv(args.output_classes, class_rows)
    write_report(args.output_report, summary, class_rows, examples)
    print(json.dumps({
        "rows": len(rows),
        "output_report": str(args.output_report),
        "rerank_rescuable_share": summary[0]["rerank_rescuable_share"],
        "candidate_missing_all_gold_share": summary[0]["candidate_missing_all_gold_share"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
