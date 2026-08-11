#!/usr/bin/env python3
"""Analyze candidate reranker gains and failures by query type."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


METRICS = ("mrr", "recall@1", "recall@3", "recall@5")


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


def as_float(row: dict[str, str], key: str) -> float:
    return float(row.get(key, "0") or 0)


def metric(value: float) -> str:
    return f"{value:.3f}"


def paired_rows(comparison_rows: list[dict[str, str]], baseline: str, candidate: str) -> list[dict[str, Any]]:
    by_query: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in comparison_rows:
        by_query[row["query_id"]][row["method"]] = row

    pairs = []
    for split_query_id, methods in sorted(by_query.items()):
        if baseline not in methods or candidate not in methods:
            continue
        left = methods[baseline]
        right = methods[candidate]
        pair = {
            "query_id": split_query_id,
            "original_query_id": left.get("original_query_id", split_query_id.split(":", 1)[-1]),
            "split_seed": left.get("split_seed", ""),
            "query_type": left.get("query_type", right.get("query_type", "")),
            "baseline_first_rank": left.get("first_rank", ""),
            "candidate_first_rank": right.get("first_rank", ""),
        }
        for metric_name in METRICS:
            base_value = as_float(left, metric_name)
            cand_value = as_float(right, metric_name)
            pair[f"baseline_{metric_name}"] = base_value
            pair[f"candidate_{metric_name}"] = cand_value
            pair[f"delta_{metric_name}"] = cand_value - base_value
        pairs.append(pair)
    return pairs


def by_type_summary(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        buckets[str(row["query_type"])].append(row)

    rows = []
    for query_type in sorted(buckets, key=lambda value: int(value) if value.isdigit() else 999):
        bucket = buckets[query_type]
        out = {
            "query_type": query_type,
            "num_pairs": len(bucket),
            "improved_mrr": sum(1 for row in bucket if row["delta_mrr"] > 0),
            "worsened_mrr": sum(1 for row in bucket if row["delta_mrr"] < 0),
            "tied_mrr": sum(1 for row in bucket if row["delta_mrr"] == 0),
        }
        for metric_name in METRICS:
            out[f"baseline_{metric_name}"] = statistics.mean(row[f"baseline_{metric_name}"] for row in bucket)
            out[f"candidate_{metric_name}"] = statistics.mean(row[f"candidate_{metric_name}"] for row in bucket)
            out[f"delta_{metric_name}"] = statistics.mean(row[f"delta_{metric_name}"] for row in bucket)
        rows.append(out)
    return rows


def selected_lookup(selected_rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    return {
        (row["split_seed"], row["query_id"]): row
        for row in selected_rows
    }


def load_type_aware_top(rankings_path: Path) -> dict[str, dict[str, str]]:
    top_rows = {}
    with rankings_path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "type_aware":
                continue
            if row["query_id"] not in top_rows:
                top_rows[row["query_id"]] = row
    return top_rows


def classify_pair(delta_mrr: float) -> str:
    if delta_mrr > 0:
        return "improved"
    if delta_mrr < 0:
        return "worsened"
    return "tied"


def example_rows(
    pairs: list[dict[str, Any]],
    queries: dict[str, dict[str, Any]],
    memories: dict[str, dict[str, Any]],
    selected: dict[tuple[str, str], dict[str, str]],
    type_aware_top: dict[str, dict[str, str]],
    per_group: int,
) -> list[dict[str, Any]]:
    candidates = sorted(pairs, key=lambda row: abs(row["delta_mrr"]), reverse=True)
    counts: Counter[tuple[str, str]] = Counter()
    examples = []
    for pair in candidates:
        label = classify_pair(pair["delta_mrr"])
        key = (str(pair["query_type"]), label)
        if counts[key] >= per_group:
            continue
        original_query_id = pair["original_query_id"]
        selected_row = selected.get((str(pair["split_seed"]), original_query_id), {})
        baseline_top = type_aware_top.get(original_query_id, {})
        candidate_memory = memories.get(selected_row.get("top_memory_id", ""), {})
        baseline_memory = memories.get(baseline_top.get("memory_id", ""), {})
        query = queries.get(original_query_id, {})
        gold_ids = query.get("answer_memory_ids", [])
        gold_memories = [memories[memory_id] for memory_id in gold_ids if memory_id in memories]
        examples.append({
            "case": label,
            "query_type": pair["query_type"],
            "split_seed": pair["split_seed"],
            "query_id": original_query_id,
            "query": query.get("query", ""),
            "delta_mrr": pair["delta_mrr"],
            "baseline_first_rank": pair["baseline_first_rank"],
            "candidate_first_rank": pair["candidate_first_rank"],
            "baseline_top_memory_id": baseline_top.get("memory_id", ""),
            "baseline_top_memory_type": baseline_top.get("memory_type", ""),
            "baseline_top_memory_text": baseline_top.get("memory_text", ""),
            "candidate_top_memory_id": selected_row.get("top_memory_id", ""),
            "candidate_top_memory_type": selected_row.get("top_memory_type", ""),
            "candidate_top_memory_text": candidate_memory.get("text", ""),
            "gold_memory_ids": "|".join(gold_ids),
            "gold_memory_types": "|".join(sorted({memory.get("memory_type", "unknown") for memory in gold_memories})),
            "gold_memory_texts": " || ".join(memory.get("text", "") for memory in gold_memories[:3]),
        })
        counts[key] += 1
    return examples


def write_report(path: Path, summary_rows: list[dict[str, Any]], examples: list[dict[str, Any]]) -> None:
    lines = [
        "# Candidate Reranker 按 Query Type 分析",
        "",
        "本报告基于 held-out split 的 paired comparison，分析 candidate reranker 相比 fixed `type_aware` 在不同 LoCoMo query type 上的收益和失败案例。",
        "",
        "## By Query Type",
        "",
        "| Query Type | Pairs | Base MRR | Reranker MRR | Delta MRR | Base R@1 | Reranker R@1 | Base R@5 | Reranker R@5 | Improved | Worsened | Tied |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| Type {row['query_type']} | {row['num_pairs']} | {metric(row['baseline_mrr'])} | "
            f"{metric(row['candidate_mrr'])} | {row['delta_mrr']:.4f} | "
            f"{metric(row['baseline_recall@1'])} | {metric(row['candidate_recall@1'])} | "
            f"{metric(row['baseline_recall@5'])} | {metric(row['candidate_recall@5'])} | "
            f"{row['improved_mrr']} | {row['worsened_mrr']} | {row['tied_mrr']} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- 若某类 query 的 Delta MRR 明显为正，说明 candidate-level reranker 能从多检索器候选中学到比固定公式更细的排序边界。",
        "- 若某类 query 的 Worsened 数量较高，需要重点检查 top memory 是否过度依赖某个检索器分数，或 gold memory 是否没有进入候选池。",
        "- 这些结果可用于论文中的细粒度分析表和失败案例小节。",
        "",
        "## Representative Cases",
        "",
    ])
    for row in examples[:24]:
        lines.extend([
            f"### {row['case']} / Type {row['query_type']} / `{row['query_id']}` / seed {row['split_seed']}",
            "",
            f"- Query: {row['query']}",
            f"- Delta MRR: `{row['delta_mrr']:.4f}`; baseline rank `{row['baseline_first_rank']}`, reranker rank `{row['candidate_first_rank']}`",
            f"- Baseline top: `{row['baseline_top_memory_id']}` ({row['baseline_top_memory_type']}) {row['baseline_top_memory_text']}",
            f"- Reranker top: `{row['candidate_top_memory_id']}` ({row['candidate_top_memory_type']}) {row['candidate_top_memory_text']}",
            f"- Gold: {row['gold_memory_texts']}",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze candidate reranker gains by query type.")
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--selected", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--baseline", default="type_aware")
    parser.add_argument("--candidate", default="candidate_reranker")
    parser.add_argument("--examples-per-group", type=int, default=2)
    parser.add_argument("--output-by-type", type=Path, required=True)
    parser.add_argument("--output-examples", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    pairs = paired_rows(read_csv(args.comparison), args.baseline, args.candidate)
    summary_rows = by_type_summary(pairs)
    queries = read_jsonl(args.queries)
    memories = read_jsonl(args.memories)
    selected = selected_lookup(read_csv(args.selected))
    type_aware_top = load_type_aware_top(args.rankings)
    examples = example_rows(
        pairs,
        queries,
        memories,
        selected,
        type_aware_top,
        args.examples_per_group,
    )

    write_csv(args.output_by_type, summary_rows)
    write_csv(args.output_examples, examples)
    write_report(args.output_report, summary_rows, examples)
    print(json.dumps({
        "num_pairs": len(pairs),
        "output_by_type": str(args.output_by_type),
        "output_examples": str(args.output_examples),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
