#!/usr/bin/env python3
"""Bootstrap confidence intervals for paper-facing retrieval metrics."""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SCENARIOS = [
    {
        "scenario": "candidate_reranker_heldout",
        "path": "outputs/agent_memory_candidate_reranker_locomo10_comparison_per_query.csv",
        "baseline": "type_aware",
        "candidate": "candidate_reranker",
        "description": "LoCoMo10 held-out query split：学习式 candidate reranker 相对 type-aware 的主结果稳定性。",
    },
    {
        "scenario": "candidate_reranker_loco",
        "path": "outputs/agent_memory_candidate_reranker_loco_comparison_per_query.csv",
        "baseline": "type_aware",
        "candidate": "candidate_reranker_loco",
        "description": "Leave-one-conversation-out split：检验 candidate reranker 是否能跨 conversation 泛化。",
    },
    {
        "scenario": "validation_tuned_router",
        "path": "outputs/agent_memory_validation_tuned_router_locomo10_comparison_per_query.csv",
        "baseline": "type_aware",
        "candidate": "validation_tuned_intent_router",
        "description": "Validation-tuned intent router：可部署路由 baseline 相对固定 type-aware 的负/弱结果。",
    },
    {
        "scenario": "text_intent_router",
        "path": "outputs/agent_memory_text_intent_router_locomo10_comparison_per_query.csv",
        "baseline": "type_aware",
        "candidate": "text_intent_router",
        "description": "规则文本 intent router：不使用验证集调参的可解释路由 baseline。",
    },
    {
        "scenario": "type3_query_decomposition_fusion4",
        "path": "outputs/agent_memory_type3_query_decomposition_fusion4_per_query.csv",
        "baseline": "type_aware",
        "candidate": "type_aware_plus_decomposition",
        "description": "Type 3 query decomposition fusion4：多证据问题上的关键词式分解负结果。",
    },
]


METRICS = ["mrr", "recall@1", "recall@3", "recall@5"]


def read_csv(path: Path) -> list[dict[str, str]]:
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


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    position = q * (len(values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def bootstrap_mean_ci(values: list[float], iterations: int, rng: random.Random) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    n = len(values)
    boot_means = []
    for _ in range(iterations):
        boot_means.append(statistics.mean(values[rng.randrange(n)] for _ in range(n)))
    boot_means.sort()
    return percentile(boot_means, 0.025), percentile(boot_means, 0.975)


def normalize_query_id(row: dict[str, str]) -> str:
    return row.get("query_id") or row.get("original_query_id") or row.get("audit_id") or ""


def paired_method_rows(rows: list[dict[str, str]], baseline: str, candidate: str) -> list[tuple[str, dict[str, str], dict[str, str]]]:
    by_query: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        query_id = normalize_query_id(row)
        method = row.get("method", "")
        if query_id and method:
            by_query[query_id][method] = row
    pairs = []
    for query_id in sorted(by_query):
        left = by_query[query_id].get(baseline)
        right = by_query[query_id].get(candidate)
        if left and right:
            pairs.append((query_id, left, right))
    return pairs


def summarize_scenario(
    project_root: Path,
    scenario: dict[str, str],
    scenario_idx: int,
    metrics: list[str],
    iterations: int,
    seed: int,
) -> list[dict[str, Any]]:
    path = project_root / scenario["path"]
    if not path.exists():
        return [{
            "scenario": scenario["scenario"],
            "description": scenario["description"],
            "metric": "",
            "baseline": scenario["baseline"],
            "candidate": scenario["candidate"],
            "status": "missing_input",
            "num_queries": 0,
            "baseline_mean": 0.0,
            "baseline_ci_low": 0.0,
            "baseline_ci_high": 0.0,
            "candidate_mean": 0.0,
            "candidate_ci_low": 0.0,
            "candidate_ci_high": 0.0,
            "delta_mean": 0.0,
            "delta_ci_low": 0.0,
            "delta_ci_high": 0.0,
            "delta_ci_excludes_zero": False,
            "improved_queries": 0,
            "worsened_queries": 0,
            "tied_queries": 0,
        }]

    rows = read_csv(path)
    pairs = paired_method_rows(rows, scenario["baseline"], scenario["candidate"])
    output_rows = []
    for metric_idx, metric in enumerate(metrics):
        rng = random.Random(seed + 1009 * metric_idx + 100_003 * scenario_idx)
        metric_pairs = [
            (float(left[metric]), float(right[metric]))
            for _, left, right in pairs
            if metric in left and metric in right
        ]
        baseline_values = [left for left, _ in metric_pairs]
        candidate_values = [right for _, right in metric_pairs]
        deltas = [right - left for left, right in metric_pairs]
        baseline_low, baseline_high = bootstrap_mean_ci(baseline_values, iterations, rng)
        candidate_low, candidate_high = bootstrap_mean_ci(candidate_values, iterations, rng)
        delta_low, delta_high = bootstrap_mean_ci(deltas, iterations, rng)
        output_rows.append({
            "scenario": scenario["scenario"],
            "description": scenario["description"],
            "metric": metric,
            "baseline": scenario["baseline"],
            "candidate": scenario["candidate"],
            "status": "ok" if pairs else "missing_pairs",
            "num_queries": len(metric_pairs),
            "baseline_mean": statistics.mean(baseline_values) if baseline_values else 0.0,
            "baseline_ci_low": baseline_low,
            "baseline_ci_high": baseline_high,
            "candidate_mean": statistics.mean(candidate_values) if candidate_values else 0.0,
            "candidate_ci_low": candidate_low,
            "candidate_ci_high": candidate_high,
            "delta_mean": statistics.mean(deltas) if deltas else 0.0,
            "delta_ci_low": delta_low,
            "delta_ci_high": delta_high,
            "delta_ci_excludes_zero": delta_low > 0.0 or delta_high < 0.0,
            "improved_queries": sum(1 for delta in deltas if delta > 0.0),
            "worsened_queries": sum(1 for delta in deltas if delta < 0.0),
            "tied_queries": sum(1 for delta in deltas if delta == 0.0),
        })
    return output_rows


def fmt(value: Any) -> str:
    return f"{float(value):.4f}"


def write_report(path: Path, rows: list[dict[str, Any]], iterations: int, seed: int) -> None:
    scenario_order = []
    by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        scenario = row["scenario"]
        if scenario not in by_scenario:
            scenario_order.append(scenario)
        by_scenario[scenario].append(row)

    lines = [
        "# Bootstrap 置信区间报告",
        "",
        "本报告对论文中最容易被审稿人追问的 per-query 检索结果做非参数 bootstrap 置信区间。每次 bootstrap 以 query 为重采样单位，避免只报告单个点估计。",
        "",
        "## 设置",
        "",
        f"- Bootstrap iterations: `{iterations}`",
        f"- Random seed: `{seed}`",
        "- Confidence level: `95%`",
        "- Metrics: `MRR`、`Recall@1`、`Recall@3`、`Recall@5`",
        "",
        "## 主要结论",
        "",
    ]
    for scenario in scenario_order:
        scenario_rows = by_scenario[scenario]
        mrr = next((row for row in scenario_rows if row["metric"] == "mrr"), scenario_rows[0])
        if mrr["status"] != "ok":
            lines.append(f"- `{scenario}`：输入或配对结果缺失，当前不能报告 CI。")
            continue
        if mrr["delta_ci_low"] > 0.0:
            verdict = "CI 不跨 0，提升较稳定"
        elif mrr["delta_ci_high"] < 0.0:
            verdict = "CI 不跨 0，但方向为下降，应作为负结果表述"
        else:
            verdict = "CI 跨 0，应作为弱结果或不确定结果谨慎表述"
        lines.append(
            f"- `{scenario}`：MRR delta={fmt(mrr['delta_mean'])}，95% CI=[{fmt(mrr['delta_ci_low'])}, {fmt(mrr['delta_ci_high'])}]，{verdict}。"
        )

    lines.extend([
        "",
        "## 明细表",
        "",
        "| Scenario | Metric | Baseline Mean [95% CI] | Candidate Mean [95% CI] | Delta [95% CI] | Improved/Worse/Tie |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for row in rows:
        if row["status"] != "ok":
            lines.append(f"| {row['scenario']} | {row['metric']} | missing | missing | missing | 0/0/0 |")
            continue
        lines.append(
            f"| {row['scenario']} | {row['metric']} | "
            f"{fmt(row['baseline_mean'])} [{fmt(row['baseline_ci_low'])}, {fmt(row['baseline_ci_high'])}] | "
            f"{fmt(row['candidate_mean'])} [{fmt(row['candidate_ci_low'])}, {fmt(row['candidate_ci_high'])}] | "
            f"{fmt(row['delta_mean'])} [{fmt(row['delta_ci_low'])}, {fmt(row['delta_ci_high'])}] | "
            f"{row['improved_queries']}/{row['worsened_queries']}/{row['tied_queries']} |"
        )

    lines.extend([
        "",
        "## 论文写法建议",
        "",
        "- 对 `candidate_reranker_heldout` 和 `candidate_reranker_loco`，若 MRR delta 的 CI 不跨 0，可以作为主方法稳定提升证据。",
        "- 对 CI 跨 0 的 router/decomposition 结果，应写成对照或负结果，避免包装成有效方法。",
        "- 本报告不能替代外部 embedding baseline 或人工复核；它补强的是统计不确定性，而不是外部有效性和人工可靠性。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate bootstrap CIs for paper-facing retrieval metrics.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--metrics", default=",".join(METRICS))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    metrics = [item.strip() for item in args.metrics.split(",") if item.strip()]
    rows: list[dict[str, Any]] = []
    for scenario_idx, scenario in enumerate(DEFAULT_SCENARIOS):
        rows.extend(summarize_scenario(args.project_root, scenario, scenario_idx, metrics, args.iterations, args.seed))

    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.iterations, args.seed)
    print(json.dumps({
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
        "rows": len(rows),
        "scenarios": len(DEFAULT_SCENARIOS),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
