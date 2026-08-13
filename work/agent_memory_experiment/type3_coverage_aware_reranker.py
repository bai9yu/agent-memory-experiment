#!/usr/bin/env python3
"""Coverage-aware Type-3 reranking over cached candidate-reranker Top-20 rows."""

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
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "did", "do", "does",
    "for", "from", "had", "has", "have", "he", "her", "his", "how", "in",
    "is", "it", "kind", "of", "on", "or", "she", "that", "the", "their",
    "to", "was", "were", "what", "when", "where", "which", "who", "why",
    "with", "would",
}


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


def tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(text)
        if token.lower() not in STOPWORDS and len(token) > 2
    }


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def normalize_scores(rows: list[dict[str, Any]]) -> None:
    scores = [row["learned_score"] for row in rows]
    lo = min(scores)
    hi = max(scores)
    for row in rows:
        row["norm_score"] = (row["learned_score"] - lo) / (hi - lo) if hi > lo else 0.0


def load_ranked(path: Path, memories: dict[str, dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_csv(path):
        memory = memories.get(row["memory_id"], {})
        memory_text = row.get("memory_text", "")
        query_type = row.get("query_type", "")
        groups[(row["split_seed"], row["query_id"])].append({
            "split_seed": row["split_seed"],
            "query_id": row["query_id"],
            "query_type": query_type,
            "rank": int(row["rank"]),
            "memory_id": row["memory_id"],
            "memory_type": row.get("memory_type", memory.get("memory_type", "")),
            "memory_text": memory_text,
            "learned_score": float(row.get("learned_score", "0") or 0),
            "is_relevant": row.get("is_relevant") == "True",
            "tokens": tokens(memory_text),
            "entities": {str(item).lower() for item in memory.get("entities", [])},
            "source_session": str(memory.get("session_id", "")),
            "agent_id": str(memory.get("agent_id", "")),
        })
    for rows in groups.values():
        rows.sort(key=lambda item: item["rank"])
        normalize_scores(rows)
    return groups


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
        "first_rank": rank,
    }


def coverage_metrics(rows: list[dict[str, Any]], gold_ids: set[str], ks: list[int]) -> dict[str, float]:
    out = {}
    ranked_ids = [row["memory_id"] for row in rows]
    for k in ks:
        top_ids = set(ranked_ids[:k])
        covered = top_ids & gold_ids
        out[f"any_hit@{k}"] = 1.0 if covered else 0.0
        out[f"full_coverage@{k}"] = 1.0 if gold_ids and gold_ids.issubset(top_ids) else 0.0
        out[f"coverage_ratio@{k}"] = len(covered) / len(gold_ids) if gold_ids else 0.0
    return out


def row_gain(
    row: dict[str, Any],
    selected: list[dict[str, Any]],
    query_tokens: set[str],
    query_entities: set[str],
    params: dict[str, float],
) -> float:
    selected_tokens = set().union(*(item["tokens"] for item in selected)) if selected else set()
    selected_entities = set().union(*(item["entities"] for item in selected)) if selected else set()
    selected_types = {item["memory_type"] for item in selected}
    selected_sessions = {item["source_session"] for item in selected}
    selected_agents = {item["agent_id"] for item in selected}

    new_query_tokens = len((row["tokens"] & query_tokens) - selected_tokens) / max(len(query_tokens), 1)
    new_entities = len((row["entities"] & query_entities) - selected_entities) / max(len(query_entities), 1)
    type_novelty = 0.0 if row["memory_type"] in selected_types else 1.0
    session_novelty = 0.0 if row["source_session"] in selected_sessions else 1.0
    agent_novelty = 0.0 if row["agent_id"] in selected_agents else 1.0
    redundancy = max((jaccard(row["tokens"], item["tokens"]) for item in selected), default=0.0)
    rank_prior = 1.0 / max(row["rank"], 1)

    return (
        params["score"] * row["norm_score"]
        + params["query_coverage"] * new_query_tokens
        + params["entity_coverage"] * new_entities
        + params["type_novelty"] * type_novelty
        + params["session_novelty"] * session_novelty
        + params["agent_novelty"] * agent_novelty
        + params["rank_prior"] * rank_prior
        - params["redundancy"] * redundancy
    )


def coverage_aware_select(
    rows: list[dict[str, Any]],
    query: dict[str, Any],
    params: dict[str, float],
    select_k: int,
    keep_top1: bool,
) -> list[dict[str, Any]]:
    remaining = list(rows)
    selected: list[dict[str, Any]] = []
    if keep_top1 and remaining:
        selected.append(remaining.pop(0))
    query_tokens = tokens(query.get("query", ""))
    query_entities = {token for token in query_tokens if token[:1].isupper()}
    # The tokenizer lower-cases tokens, so use entities from memory overlap as a soft signal.
    query_entities = {token for token in query_tokens if token in {entity for row in rows for entity in row["entities"]}}
    while remaining and len(selected) < select_k:
        best_idx = 0
        best_score = float("-inf")
        for idx, row in enumerate(remaining):
            score = row_gain(row, selected, query_tokens, query_entities, params)
            if score > best_score:
                best_idx = idx
                best_score = score
        chosen = dict(remaining.pop(best_idx))
        chosen["coverage_aware_score"] = best_score
        selected.append(chosen)
    selected_ids = {row["memory_id"] for row in selected}
    selected.extend([row for row in rows if row["memory_id"] not in selected_ids])
    return selected


def build_rows(
    groups: dict[tuple[str, str], list[dict[str, Any]]],
    queries: dict[str, dict[str, Any]],
    params: dict[str, float],
    ks: list[int],
    select_k: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_query = []
    ranked_rows = []
    for (seed, query_id), original in sorted(groups.items()):
        query = queries.get(query_id)
        if not query or str(query.get("type")) != "3":
            continue
        gold_ids = set(query.get("answer_memory_ids", []))
        methods = {
            "candidate_reranker": original,
            "coverage_aware_keep_top1": coverage_aware_select(original, query, params, select_k, keep_top1=True),
            "coverage_aware_free": coverage_aware_select(original, query, params, select_k, keep_top1=False),
        }
        for method, rows in methods.items():
            metric_row = {
                "split_seed": seed,
                "query_id": query_id,
                "query_type": "3",
                "query": query.get("query", ""),
                "method": method,
                "num_gold": len(gold_ids),
                "is_multi_evidence": 1 if len(gold_ids) > 1 else 0,
                **ranking_metrics(rows),
                **coverage_metrics(rows, gold_ids, ks),
            }
            per_query.append(metric_row)
            for rank, row in enumerate(rows[:max(ks)], start=1):
                ranked_rows.append({
                    "split_seed": seed,
                    "query_id": query_id,
                    "method": method,
                    "rank": rank,
                    "memory_id": row["memory_id"],
                    "memory_type": row["memory_type"],
                    "is_relevant": row["is_relevant"],
                    "learned_score": row["learned_score"],
                    "coverage_aware_score": row.get("coverage_aware_score", ""),
                })
    return per_query, ranked_rows


def aggregate(rows: list[dict[str, Any]], ks: list[int]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[row["method"]].append(row)
    out_rows = []
    for method, bucket in sorted(buckets.items()):
        out = {
            "method": method,
            "num_rows": len(bucket),
            "mean_gold": statistics.mean(row["num_gold"] for row in bucket),
            "multi_evidence_share": statistics.mean(row["is_multi_evidence"] for row in bucket),
            "mrr": statistics.mean(row["mrr"] for row in bucket),
            "recall@1": statistics.mean(row["recall@1"] for row in bucket),
            "recall@3": statistics.mean(row["recall@3"] for row in bucket),
            "recall@5": statistics.mean(row["recall@5"] for row in bucket),
        }
        for k in ks:
            for name in (f"any_hit@{k}", f"full_coverage@{k}", f"coverage_ratio@{k}"):
                out[name] = statistics.mean(row[name] for row in bucket)
        out_rows.append(out)
    return out_rows


def delta_rows(summary: list[dict[str, Any]], baseline_method: str) -> list[dict[str, Any]]:
    by_method = {row["method"]: row for row in summary}
    base = by_method[baseline_method]
    out = []
    for method, row in by_method.items():
        if method == baseline_method:
            continue
        out.append({
            "baseline": baseline_method,
            "method": method,
            "delta_mrr": row["mrr"] - base["mrr"],
            "delta_recall@5": row["recall@5"] - base["recall@5"],
            "delta_coverage_ratio@5": row["coverage_ratio@5"] - base["coverage_ratio@5"],
            "delta_full_coverage@5": row["full_coverage@5"] - base["full_coverage@5"],
            "delta_coverage_ratio@20": row["coverage_ratio@20"] - base.get("coverage_ratio@20", 0.0),
            "delta_full_coverage@20": row["full_coverage@20"] - base.get("full_coverage@20", 0.0),
        })
    return out


def fmt(value: float) -> str:
    return f"{value:.3f}"


def write_report(path: Path, summary: list[dict[str, Any]], deltas: list[dict[str, Any]], params: dict[str, float]) -> None:
    lines = [
        "# Type 3 Coverage-Aware Reranking",
        "",
        "本实验针对 Type 3 多证据问题，在已缓存的 candidate reranker Top-20 候选上做无监督 coverage-aware 选择。打分只使用候选分数、query token 覆盖、实体覆盖、memory type/session/agent 新颖性和文本冗余惩罚，不使用 gold evidence 调参。",
        "",
        "## 参数",
        "",
        "| Parameter | Value |",
        "|---|---:|",
    ]
    for key, value in params.items():
        lines.append(f"| {key} | {value} |")
    lines.extend([
        "",
        "## Type 3 结果",
        "",
        "| Method | Rows | MRR | R@5 | Coverage@5 | Full@5 | Coverage@20 | Full@20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in summary:
        lines.append(
            f"| {row['method']} | {row['num_rows']} | {fmt(row['mrr'])} | {fmt(row['recall@5'])} | "
            f"{fmt(row['coverage_ratio@5'])} | {fmt(row['full_coverage@5'])} | "
            f"{fmt(row['coverage_ratio@20'])} | {fmt(row['full_coverage@20'])} |"
        )
    lines.extend([
        "",
        "## 相比 Candidate Reranker 的变化",
        "",
        "| Method | ΔMRR | ΔR@5 | ΔCoverage@5 | ΔFull@5 | ΔCoverage@20 | ΔFull@20 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in deltas:
        lines.append(
            f"| {row['method']} | {row['delta_mrr']:.4f} | {row['delta_recall@5']:.4f} | "
            f"{row['delta_coverage_ratio@5']:.4f} | {row['delta_full_coverage@5']:.4f} | "
            f"{row['delta_coverage_ratio@20']:.4f} | {row['delta_full_coverage@20']:.4f} |"
        )
    best_cov5 = max(summary, key=lambda row: row["coverage_ratio@5"])
    best_mrr = max(summary, key=lambda row: row["mrr"])
    lines.extend([
        "",
        "## 解释",
        "",
        f"- Coverage@5 最好的方法是 `{best_cov5['method']}`，Coverage@5=`{fmt(best_cov5['coverage_ratio@5'])}`。",
        f"- MRR 最好的方法是 `{best_mrr['method']}`，MRR=`{fmt(best_mrr['mrr'])}`。",
        "- 如果 coverage-aware 方法仍不能提升 Coverage@5，说明仅凭无监督多样性和 query 覆盖信号不足以解决 Type 3，需要真正的 listwise/setwise 学习目标或更强 LLM 子问题分解。",
        "- 如果它提升 Coverage@5 但损害 MRR，则可作为 recall/coverage-oriented reranking 的系统折中，而不是替代主排序器。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Type-3 coverage-aware reranking over Top-20 candidates.")
    parser.add_argument("--candidate-ranked", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--ks", default="1,3,5,20")
    parser.add_argument("--select-k", type=int, default=20)
    parser.add_argument("--score", type=float, default=1.0)
    parser.add_argument("--query-coverage", type=float, default=0.35)
    parser.add_argument("--entity-coverage", type=float, default=0.25)
    parser.add_argument("--type-novelty", type=float, default=0.08)
    parser.add_argument("--session-novelty", type=float, default=0.04)
    parser.add_argument("--agent-novelty", type=float, default=0.02)
    parser.add_argument("--rank-prior", type=float, default=0.10)
    parser.add_argument("--redundancy", type=float, default=0.30)
    parser.add_argument("--output-per-query", type=Path, required=True)
    parser.add_argument("--output-ranked", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-deltas", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    ks = [int(item) for item in args.ks.split(",") if item.strip()]
    params = {
        "score": args.score,
        "query_coverage": args.query_coverage,
        "entity_coverage": args.entity_coverage,
        "type_novelty": args.type_novelty,
        "session_novelty": args.session_novelty,
        "agent_novelty": args.agent_novelty,
        "rank_prior": args.rank_prior,
        "redundancy": args.redundancy,
    }
    queries = read_jsonl(args.queries)
    memories = read_jsonl(args.memories)
    groups = load_ranked(args.candidate_ranked, memories)
    per_query, ranked = build_rows(groups, queries, params, ks, args.select_k)
    summary = aggregate(per_query, ks)
    deltas = delta_rows(summary, "candidate_reranker")
    write_csv(args.output_per_query, per_query)
    write_csv(args.output_ranked, ranked)
    write_csv(args.output_summary, summary)
    write_csv(args.output_deltas, deltas)
    write_report(args.output_report, summary, deltas, params)
    print(json.dumps({
        "output_report": str(args.output_report),
        "num_queries": len({row["query_id"] for row in per_query}),
        "methods": sorted({row["method"] for row in per_query}),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
