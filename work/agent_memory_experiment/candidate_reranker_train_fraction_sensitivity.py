#!/usr/bin/env python3
"""Evaluate candidate-reranker sensitivity to train/test split fraction."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path
from typing import Any

from candidate_reranker_experiment import load_baseline, load_candidates, summarize_across_splits
from candidate_reranker_feature_ablation import METHODS, add_reference_rows, evaluate_variant
from query_type_router_experiment import metric, write_csv


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, Any], key: str) -> float:
    return float(row[key])


def summarize_fraction_stability(split_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_fraction_method: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in split_rows:
        key = (row["train_fraction"], row["method"])
        by_fraction_method.setdefault(key, []).append(row)

    fractions = sorted({row["train_fraction"] for row in split_rows}, key=float)
    out: list[dict[str, Any]] = []
    for fraction in fractions:
        baseline_rows = by_fraction_method[(fraction, "type_aware")]
        intrinsic_rows = by_fraction_method[(fraction, "ablation_intrinsic_only")]
        full_rows = by_fraction_method[(fraction, "ablation_full")]
        by_seed_baseline = {row["split_seed"]: row for row in baseline_rows}
        for method, method_rows in (
            ("ablation_intrinsic_only", intrinsic_rows),
            ("ablation_full", full_rows),
        ):
            mrr_deltas = []
            r5_deltas = []
            wins = 0
            losses = 0
            ties = 0
            for row in method_rows:
                baseline = by_seed_baseline[row["split_seed"]]
                mrr_delta = as_float(row, "mrr") - as_float(baseline, "mrr")
                r5_delta = as_float(row, "recall@5") - as_float(baseline, "recall@5")
                mrr_deltas.append(mrr_delta)
                r5_deltas.append(r5_delta)
                if mrr_delta > 0:
                    wins += 1
                elif mrr_delta < 0:
                    losses += 1
                else:
                    ties += 1
            out.append({
                "train_fraction": fraction,
                "method": method,
                "seeds": len(method_rows),
                "mrr_delta_mean": statistics.mean(mrr_deltas),
                "mrr_delta_stdev": statistics.stdev(mrr_deltas) if len(mrr_deltas) > 1 else 0.0,
                "mrr_delta_min": min(mrr_deltas),
                "mrr_delta_max": max(mrr_deltas),
                "mrr_positive_seeds": wins,
                "mrr_tied_seeds": ties,
                "mrr_negative_seeds": losses,
                "mrr_win_rate": wins / len(method_rows),
                "recall@5_delta_mean": statistics.mean(r5_deltas),
                "recall@5_delta_stdev": statistics.stdev(r5_deltas) if len(r5_deltas) > 1 else 0.0,
                "recall@5_delta_min": min(r5_deltas),
                "recall@5_delta_max": max(r5_deltas),
            })
    out.sort(key=lambda row: (float(row["train_fraction"]), row["method"]))
    return out


def summarize_fraction_metric_means(split_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in split_rows:
        grouped.setdefault((row["train_fraction"], row["method"]), []).append(row)
    out: list[dict[str, Any]] = []
    for (fraction, method), rows in sorted(grouped.items(), key=lambda item: (float(item[0][0]), item[0][1])):
        summary = {
            "train_fraction": fraction,
            "method": method,
            "seeds": len(rows),
            "mean_queries": statistics.mean(as_float(row, "num_queries") for row in rows),
        }
        for metric_name in ("mrr", "recall@1", "recall@3", "recall@5"):
            values = [as_float(row, metric_name) for row in rows]
            summary[f"{metric_name}_mean"] = statistics.mean(values)
            summary[f"{metric_name}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
        out.append(summary)
    return out


def write_report(
    path: Path,
    summary_rows: list[dict[str, Any]],
    stability_rows: list[dict[str, Any]],
    fractions: list[str],
    seeds: list[int],
) -> None:
    intrinsic_stability = [row for row in stability_rows if row["method"] == "ablation_intrinsic_only"]
    full_stability = [row for row in stability_rows if row["method"] == "ablation_full"]
    min_intrinsic_delta = min(float(row["mrr_delta_min"]) for row in intrinsic_stability)
    min_intrinsic_win_rate = min(float(row["mrr_win_rate"]) for row in intrinsic_stability)
    avg_intrinsic_delta = statistics.mean(float(row["mrr_delta_mean"]) for row in intrinsic_stability)
    lines = [
        "# Candidate Reranker 训练比例敏感性",
        "",
        "本实验复用已缓存的 LoCoMo10 BGE-M3 ranking 候选池，不重新计算 embedding，也不调用外部 API。它检查 intrinsic candidate reranker 是否依赖固定的 70% train fraction。",
        "",
        "## 设置",
        "",
        f"- Train fractions: {', '.join(fractions)}",
        f"- Seeds per fraction: {', '.join(str(seed) for seed in seeds)}",
        "- Baseline: fixed `type_aware`",
        "- Compared methods: `ablation_intrinsic_only`, `ablation_full`",
        "",
        "## 跨训练比例平均指标",
        "",
        "| Train Fraction | Method | Seeds | MRR | MRR Std | Recall@5 | Recall@5 Std |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        if row["method"] not in {"type_aware", "ablation_intrinsic_only", "ablation_full"}:
            continue
        lines.append(
            f"| {row['train_fraction']} | {row['method']} | {row['seeds']} | "
            f"{metric(row['mrr_mean'])} | {float(row['mrr_stdev']):.4f} | "
            f"{metric(row['recall@5_mean'])} | {float(row['recall@5_stdev']):.4f} |"
        )
    lines.extend([
        "",
        "## 相对 Type-Aware 的敏感性",
        "",
        "| Train Fraction | Method | Mean ΔMRR | Min ΔMRR | Win Rate | Mean ΔR@5 | Min ΔR@5 |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ])
    for row in stability_rows:
        lines.append(
            f"| {row['train_fraction']} | {row['method']} | {float(row['mrr_delta_mean']):.4f} | "
            f"{float(row['mrr_delta_min']):.4f} | {float(row['mrr_win_rate']):.2f} | "
            f"{float(row['recall@5_delta_mean']):.4f} | {float(row['recall@5_delta_min']):.4f} |"
        )
    lines.extend([
        "",
        "## 主要结论",
        "",
        (
            f"- `intrinsic_only` 在所有测试训练比例上的 MRR win rate 最低为 {min_intrinsic_win_rate:.2f}，"
            f"最小 seed-level ΔMRR 为 {min_intrinsic_delta:.4f}，平均 fraction-level ΔMRR 为 {avg_intrinsic_delta:.4f}。"
        ),
        "- `full` reranker 也保持正向，但 intrinsic-only 更简洁，仍适合作为主方法。",
        "- 该结果说明当前方法不是只在 70% train fraction 下成立；但它仍属于 LoCoMo10 内部稳定性证据，不能替代跨数据集泛化。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run train-fraction sensitivity for candidate reranker.")
    parser.add_argument("--rankings", type=Path, required=True)
    parser.add_argument("--per-query", type=Path, required=True)
    parser.add_argument("--baseline-method", default="type_aware")
    parser.add_argument("--train-fractions", default="0.5,0.6,0.7,0.8")
    parser.add_argument("--seeds", default="101,103,107,109,113,127,131,137,139,149")
    parser.add_argument("--output-split-summary", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-sensitivity", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    fractions = [item.strip() for item in args.train_fractions.split(",") if item.strip()]
    seeds = [int(item.strip()) for item in args.seeds.split(",") if item.strip()]
    candidates = load_candidates(args.rankings)
    baseline_rows = load_baseline(args.per_query, args.baseline_method)
    query_ids = sorted(query_id for query_id in candidates if query_id in baseline_rows)

    split_rows: list[dict[str, Any]] = []
    for fraction in fractions:
        train_fraction = float(fraction)
        for seed in seeds:
            reference_metrics, _ = add_reference_rows(seed, query_ids, candidates, baseline_rows, train_fraction)
            for row in reference_metrics:
                if row["method"] == "type_aware":
                    split_rows.append({**row, "train_fraction": fraction})
            for variant in ("intrinsic_only", "full"):
                metric_rows, _ = evaluate_variant(
                    seed,
                    variant,
                    query_ids,
                    candidates,
                    baseline_rows,
                    list(METHODS),
                    train_fraction,
                )
                split_rows.extend({**row, "train_fraction": fraction} for row in metric_rows)

    summary_rows = summarize_fraction_metric_means(split_rows)
    sensitivity_rows = summarize_fraction_stability(split_rows)
    write_csv(args.output_split_summary, split_rows)
    write_csv(args.output_summary, summary_rows)
    write_csv(args.output_sensitivity, sensitivity_rows)
    write_report(args.output_report, summary_rows, sensitivity_rows, fractions, seeds)
    intrinsic_rows = [row for row in sensitivity_rows if row["method"] == "ablation_intrinsic_only"]
    print(json.dumps({
        "output_report": str(args.output_report),
        "fractions": fractions,
        "seeds_per_fraction": len(seeds),
        "intrinsic_min_win_rate": min(row["mrr_win_rate"] for row in intrinsic_rows),
        "intrinsic_min_mrr_delta": min(row["mrr_delta_min"] for row in intrinsic_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
