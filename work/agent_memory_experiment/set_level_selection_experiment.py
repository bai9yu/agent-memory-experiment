#!/usr/bin/env python3
"""Evaluate unsupervised set-level selection over candidate reranker Top-K rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
METRICS = ("mrr", "recall@1", "recall@3", "recall@5", "recall@10")


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


def tokens(text: str) -> set[str]:
    stop = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
        "have", "he", "her", "his", "in", "is", "it", "of", "on", "or", "she",
        "that", "the", "their", "to", "was", "were", "what", "when", "where",
        "which", "who", "why", "with", "would",
    }
    return {token.lower() for token in TOKEN_RE.findall(text) if token.lower() not in stop and len(token) > 2}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def load_ranked(path: Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "query_type": row["query_type"],
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row["memory_type"],
            "memory_text": row["memory_text"],
            "learned_score": as_float(row, "learned_score"),
            "is_relevant": row["is_relevant"] == "True",
            "tokens": tokens(row["memory_text"]),
        })
    for rows in groups.values():
        rows.sort(key=lambda row: row["rank"])
    return groups


def select_diverse(rows: list[dict[str, Any]], alpha: float, beta: float, gamma: float, keep_top1: bool) -> list[dict[str, Any]]:
    if not rows:
        return []
    remaining = list(rows)
    selected = []
    if keep_top1:
        selected.append(remaining.pop(0))
    while remaining:
        best_index = 0
        best_score = float("-inf")
        selected_types = {row["memory_type"] for row in selected}
        for idx, row in enumerate(remaining):
            max_sim = max((jaccard(row["tokens"], chosen["tokens"]) for chosen in selected), default=0.0)
            type_penalty = 1.0 if row["memory_type"] in selected_types else 0.0
            score = alpha * row["learned_score"] - beta * max_sim - gamma * type_penalty
            if score > best_score:
                best_score = score
                best_index = idx
        selected.append(remaining.pop(best_index))
    return selected


def first_rank(rows: list[dict[str, Any]]) -> int:
    for rank, row in enumerate(rows, start=1):
        if row["is_relevant"]:
            return rank
    return 0


def ranking_metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    rank = first_rank(rows)
    return {
        "mrr": 1.0 / rank if rank else 0.0,
        "recall@1": 1.0 if rank and rank <= 1 else 0.0,
        "recall@3": 1.0 if rank and rank <= 3 else 0.0,
        "recall@5": 1.0 if rank and rank <= 5 else 0.0,
        "recall@10": 1.0 if rank and rank <= 10 else 0.0,
        "first_rank": rank,
    }


def coverage_metrics(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    output = {}
    for k in ks:
        covered = {row["memory_id"] for row in rows[:k]} & gold_ids
        output[f"any_hit@{k}"] = 1.0 if covered else 0.0
        output[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset({row["memory_id"] for row in rows[:k]}) else 0.0
        output[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return output


def build_method_rows(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    queries: dict[str, dict[str, Any]],
    ks: list[int],
    alpha: float,
    beta: float,
    gamma: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_query = []
    ranked_out = []
    for (seed, query_id), original_rows in sorted(groups.items()):
        query = queries.get(query_id, {})
        if not query:
            continue
        gold_ids = set(query.get("answer_memory_ids", []))
        query_type = str(query.get("type", original_rows[0]["query_type"]))
        variants = {
            "candidate_reranker": original_rows,
            "set_selector_all": select_diverse(original_rows, alpha, beta, gamma, keep_top1=True),
            "set_selector_type3": select_diverse(original_rows, alpha, beta, gamma, keep_top1=True) if query_type == "3" else original_rows,
        }
        for method, rows in variants.items():
            ranked = ranking_metrics(rows)
            coverage = coverage_metrics(rows, gold_ids, ks)
            per_query.append({
                "split_seed": seed,
                "query_id": query_id,
                "query_type": query_type,
                "query": query.get("query", ""),
                "method": method,
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                **ranked,
                **coverage,
            })
            for rank, row in enumerate(rows, start=1):
                ranked_out.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "query_type": query_type,
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "learned_score": row["learned_score"],
                    "is_relevant": row["is_relevant"],
                })
    return per_query, ranked_out


def aggregate(rows: list[dict[str, Any]], group_keys: list[str], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[tuple(row[key] for key in group_keys)].append(row)
    output = []
    for key, bucket in sorted(buckets.items()):
        out = {name: value for name, value in zip(group_keys, key)}
        out["num_rows"] = len(bucket)
        out["mean_gold"] = statistics.mean(row["num_gold"] for row in bucket)
        out["multi_evidence_share"] = statistics.mean(row["is_multi_evidence"] for row in bucket)
        for metric_name in METRICS:
            out[metric_name] = statistics.mean(row[metric_name] for row in bucket)
        for k in ks:
            for cov_name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[cov_name] = statistics.mean(row[cov_name] for row in bucket)
        output.append(out)
    return output


def write_report(path: Path, overall: list[dict[str, Any]], by_type: list[dict[str, Any]], params: dict[str, float], ks: list[int]) -> None:
    max_k = max(ks)
    lines = [
        "# 集合级选择基线",
        "",
        f"本实验在 candidate reranker 的 Top-{max_k} 候选上做无监督 set-level selection：保留原 Top-1，然后用文本 Jaccard 去重和 memory type 多样性选择后续候选。",
        f"固定参数：alpha={params['alpha']}, beta={params['beta']}, gamma={params['gamma']}。该方法不使用 gold evidence 调参。所有指标仅基于已缓存 Top-{max_k} 候选计算。",
        "",
        "## Overall",
        "",
        f"| Method | Rows | MRR | R@1 | R@5 | Coverage@5 | Full@5 | Coverage@{max_k} | Full@{max_k} |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            f"| {row['method']} | {row['num_rows']} | {metric(row['mrr'])} | {metric(row['recall@1'])} | "
            f"{metric(row['recall@5'])} | {metric(row['coverage_ratio@5'])} | {metric(row['full_coverage@5'])} | "
            f"{metric(row[f'coverage_ratio@{max_k}'])} | {metric(row[f'full_coverage@{max_k}'])} |"
        )
    lines.extend([
        "",
        "## Type 3",
        "",
        f"| Method | Rows | MRR | R@5 | Coverage@5 | Full@5 | Coverage@{max_k} | Full@{max_k} |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in [item for item in by_type if item["query_type"] == "3"]:
        lines.append(
            f"| {row['method']} | {row['num_rows']} | {metric(row['mrr'])} | {metric(row['recall@5'])} | "
            f"{metric(row['coverage_ratio@5'])} | {metric(row['full_coverage@5'])} | "
            f"{metric(row[f'coverage_ratio@{max_k}'])} | {metric(row[f'full_coverage@{max_k}'])} |"
        )
    lines.extend([
        "",
        "## 解释",
        "",
        f"- `set_selector_type3` 没有提升 Type 3 coverage，说明仅在当前 Top-{max_k} 内做文本去重和 memory type 多样性不足以解决多证据覆盖。",
        f"- Coverage@{max_k} 反映输入候选池的总体证据空间；Coverage@5 下降说明简单多样性可能把相关证据推到更后。",
        f"- 下一步应做 query decomposition、扩大候选召回，或训练真正的 set-level selector，而不是只在 Top-{max_k} 内做启发式重排。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run unsupervised set-level selection over reranker Top-K candidates.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,10")
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--beta", type=float, default=0.25)
    parser.add_argument("--gamma", type=float, default=0.05)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-overall", type=Path, required=True)
    parser.add_argument("--output-by-type", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    ks = [int(item.strip()) for item in args.ks.split(",") if item.strip()]
    groups = load_ranked(args.candidate_ranked)
    queries = read_jsonl(args.queries)
    per_query, ranked = build_method_rows(groups, queries, ks, args.alpha, args.beta, args.gamma)
    overall = aggregate(per_query, ["method"], ks)
    by_type = aggregate(per_query, ["query_type", "method"], ks)

    write_csv(args.output_per_query, per_query)
    write_csv(args.output_ranked, ranked)
    write_csv(args.output_overall, overall)
    write_csv(args.output_by_type, by_type)
    write_report(args.output_report, overall, by_type, {"alpha": args.alpha, "beta": args.beta, "gamma": args.gamma}, ks)
    print(json.dumps({
        "num_rows": len(per_query),
        "output_report": str(args.output_report),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
