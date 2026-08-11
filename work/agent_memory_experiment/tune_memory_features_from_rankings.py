#!/usr/bin/env python3
"""Tune memory feature weights from a rankings.csv feature cache.

This reuses the candidate rows produced by memory_eval.py. The file already
contains semantic, BM25, decay, recency gate, persona score, and importance
score, so tuning does not need to reload BGE-M3 or recompute BM25.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_candidates(path: Path) -> list[list[dict]]:
    by_query: dict[str, dict[str, dict]] = defaultdict(dict)
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["method"] != "time_aware":
                continue
            by_query[row["query_id"]][row["memory_id"]] = {
                "query_type": row["query_type"],
                "semantic": float(row["semantic_score"]),
                "keyword": float(row["keyword_score"]),
                "decay": float(row["time_decay"]),
                "recency_gate": float(row.get("recency_gate", 0.0)),
                "persona": float(row.get("persona_score", 0.0)),
                "persona_weight": float(row.get("persona_weight", 0.0)),
                "importance": float(row.get("importance_score", 0.0)),
                "is_relevant": row["is_relevant"] == "True",
            }
    return [list(rows.values()) for rows in by_query.values()]


def evaluate(candidates: list[list[dict]], importance_weight: float, persona_weight: float | None) -> dict:
    hits = {1: 0, 3: 0, 5: 0}
    mrr = 0.0
    for rows in candidates:
        ranked = sorted(
            rows,
            key=lambda row: (
                0.70 * row["semantic"]
                + 0.30 * row["keyword"]
                + 0.08 * row["recency_gate"] * row["decay"]
                + (row["persona_weight"] if persona_weight is None else persona_weight) * row["persona"]
                + importance_weight * row["importance"]
            ),
            reverse=True,
        )
        first_rank = 0
        for rank, row in enumerate(ranked, start=1):
            if row["is_relevant"]:
                first_rank = rank
                break
        if first_rank:
            mrr += 1.0 / first_rank
            for k in hits:
                hits[k] += int(first_rank <= k)
    n = len(candidates)
    return {
        "num_queries": n,
        "importance_weight": importance_weight,
        "persona_weight": "" if persona_weight is None else persona_weight,
        "recall@1": hits[1] / n,
        "recall@3": hits[3] / n,
        "recall@5": hits[5] / n,
        "mrr": mrr / n,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, rows: list[dict]) -> None:
    best = rows[0]
    lines = [
        "# Memory Feature 参数搜索报告",
        "",
        "## 输入",
        "",
        "使用 `memory_eval.py` 生成的 `rankings.csv` 作为特征缓存，直接重排候选集合。",
        "",
        "## 最优结果",
        "",
        "| Importance weight | Persona weight | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {best['importance_weight']} | {best['persona_weight']} | {best['recall@1']:.3f} | {best['recall@3']:.3f} | {best['recall@5']:.3f} | {best['mrr']:.3f} |",
        "",
        "## Top Candidates",
        "",
        "| Importance weight | Persona weight | Recall@1 | Recall@3 | Recall@5 | MRR |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows[:12]:
        lines.append(
            f"| {row['importance_weight']} | {row['persona_weight']} | {row['recall@1']:.3f} | "
            f"{row['recall@3']:.3f} | {row['recall@5']:.3f} | {row['mrr']:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tune cached memory feature weights from rankings.csv.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--top-n", type=int, default=40)
    args = parser.parse_args()

    candidates = read_candidates(args.rankings)
    rows = []
    for importance_weight in (0.0, 0.005, 0.01, 0.015, 0.02, 0.03, 0.04, 0.06, 0.08):
        rows.append(evaluate(candidates, importance_weight, None))
        for persona_weight in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05):
            rows.append(evaluate(candidates, importance_weight, persona_weight))
    rows.sort(key=lambda row: (row["recall@1"], row["mrr"], row["recall@5"]), reverse=True)
    best_rows = rows[:args.top_n]
    write_csv(args.output_csv, best_rows)
    write_report(args.output_report, best_rows)
    print(json.dumps({"best": best_rows[0]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
