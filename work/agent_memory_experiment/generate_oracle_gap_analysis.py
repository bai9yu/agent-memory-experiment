#!/usr/bin/env python3
"""Generate oracle-gap and remaining-headroom analysis for reranker results."""

from __future__ import annotations

import argparse
import csv
import json
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


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def f(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: Any, digits: int = 4) -> str:
    return f"{float(value):+.{digits}f}"


def gap_row(
    scenario: str,
    metric_name: str,
    baseline: dict[str, str],
    method: dict[str, str],
    oracle: dict[str, str],
    notes: str,
) -> dict[str, Any]:
    key = f"{metric_name}_mean"
    baseline_value = float(baseline[key])
    method_value = float(method[key])
    oracle_value = float(oracle[key])
    total_gap = oracle_value - baseline_value
    closed_gap = method_value - baseline_value
    remaining_gap = oracle_value - method_value
    closure_rate = closed_gap / total_gap if total_gap > 0 else 0.0
    return {
        "scenario": scenario,
        "metric": metric_name,
        "baseline_method": baseline["method"],
        "candidate_method": method["method"],
        "oracle_method": oracle["method"],
        "baseline": baseline_value,
        "candidate": method_value,
        "oracle": oracle_value,
        "closed_gap": closed_gap,
        "remaining_gap": remaining_gap,
        "total_oracle_gap": total_gap,
        "closure_rate": closure_rate,
        "notes": notes,
    }


def coverage_gap_row(
    scenario: str,
    metric_name: str,
    baseline: dict[str, str],
    method: dict[str, str],
    oracle: dict[str, str],
    notes: str,
) -> dict[str, Any]:
    baseline_value = float(baseline[metric_name])
    method_value = float(method[metric_name])
    oracle_value = float(oracle[metric_name])
    total_gap = oracle_value - baseline_value
    closed_gap = method_value - baseline_value
    remaining_gap = oracle_value - method_value
    closure_rate = closed_gap / total_gap if total_gap > 0 else 0.0
    return {
        "scenario": scenario,
        "metric": metric_name,
        "baseline_method": baseline["method"],
        "candidate_method": method["method"],
        "oracle_method": oracle["method"],
        "baseline": baseline_value,
        "candidate": method_value,
        "oracle": oracle_value,
        "closed_gap": closed_gap,
        "remaining_gap": remaining_gap,
        "total_oracle_gap": total_gap,
        "closure_rate": closure_rate,
        "notes": notes,
    }


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    heldout = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    type3_summary = read_csv(outputs / "agent_memory_type3_supervised_set_selector_rwn002_summary.csv")
    type3_coverage = read_csv(outputs / "agent_memory_type3_supervised_set_selector_rwn002_coverage_summary.csv")

    heldout_baseline = lookup(heldout, method="type_aware")
    heldout_intrinsic = lookup(heldout, method="ablation_intrinsic_only")
    heldout_oracle = lookup(heldout, method="candidate_oracle")
    loco_baseline = lookup(loco, method="type_aware")
    loco_intrinsic = lookup(loco, method="intrinsic_reranker_loco")
    loco_oracle = lookup(loco, method="candidate_oracle")
    type3_baseline = lookup(type3_summary, method="type_aware")
    type3_selector = lookup(type3_summary, method="supervised_set_selector")
    type3_oracle = lookup(type3_summary, method="candidate_oracle")
    type3_cov_baseline = lookup(type3_coverage, method="type_aware")
    type3_cov_selector = lookup(type3_coverage, method="supervised_set_selector")
    type3_cov_oracle = lookup(type3_coverage, method="candidate_oracle")

    rows: list[dict[str, Any]] = []
    for metric_name in ("mrr", "recall@5"):
        rows.append(gap_row(
            "heldout_intrinsic",
            metric_name,
            heldout_baseline,
            heldout_intrinsic,
            heldout_oracle,
            "Held-out query split; tests how much intrinsic reranker closes candidate-oracle headroom.",
        ))
        rows.append(gap_row(
            "loco_intrinsic",
            metric_name,
            loco_baseline,
            loco_intrinsic,
            loco_oracle,
            "Leave-one-conversation-out split; tests cross-conversation oracle-gap closure.",
        ))
        rows.append(gap_row(
            "type3_set_selector",
            metric_name,
            type3_baseline,
            type3_selector,
            type3_oracle,
            "Type 3 only; tests whether supervised set selector closes oracle headroom.",
        ))
    for metric_name in ("coverage_ratio@5", "full_coverage@5", "coverage_ratio@20", "full_coverage@20"):
        rows.append(coverage_gap_row(
            "type3_set_coverage",
            metric_name,
            type3_cov_baseline,
            type3_cov_selector,
            type3_cov_oracle,
            "Type 3 set-level evidence coverage; oracle shows candidate-pool headroom.",
        ))
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    heldout_mrr = lookup_any(rows, scenario="heldout_intrinsic", metric="mrr")
    heldout_r5 = lookup_any(rows, scenario="heldout_intrinsic", metric="recall@5")
    loco_mrr = lookup_any(rows, scenario="loco_intrinsic", metric="mrr")
    type3_cov5 = lookup_any(rows, scenario="type3_set_coverage", metric="coverage_ratio@5")
    type3_cov20 = lookup_any(rows, scenario="type3_set_coverage", metric="coverage_ratio@20")
    table_rows = [
        [
            row["scenario"],
            row["metric"],
            f(row["baseline"]),
            f(row["candidate"]),
            f(row["oracle"]),
            signed(row["closed_gap"]),
            signed(row["remaining_gap"]),
            f(row["closure_rate"], 3),
        ]
        for row in rows
    ]
    lines = [
        "# Candidate Oracle Gap 与剩余上界分析",
        "",
        "本报告把主方法、固定 baseline 与 candidate oracle 放在同一张表中，量化当前方法关闭了多少候选池上界差距，以及剩余空间更可能来自排序学习、集合选择还是候选召回。candidate oracle 不是可部署方法，只用于诊断候选池内是否存在可利用证据。",
        "",
        "## 总览",
        "",
        f"- Held-out intrinsic MRR oracle-gap closure: {f(heldout_mrr['closure_rate'], 3)}；remaining gap={signed(heldout_mrr['remaining_gap'])}。",
        f"- Held-out intrinsic Recall@5 oracle-gap closure: {f(heldout_r5['closure_rate'], 3)}；remaining gap={signed(heldout_r5['remaining_gap'])}。",
        f"- LOCO intrinsic MRR oracle-gap closure: {f(loco_mrr['closure_rate'], 3)}；remaining gap={signed(loco_mrr['remaining_gap'])}。",
        f"- Type 3 set selector Coverage@5 closure: {f(type3_cov5['closure_rate'], 3)}；Type 3 oracle Coverage@5={f(type3_cov5['oracle'])}。",
        f"- Type 3 set selector Coverage@20 closure: {f(type3_cov20['closure_rate'], 3)}；Type 3 oracle Coverage@20={f(type3_cov20['oracle'])}。",
        "",
        "## Oracle Gap 表",
        "",
        markdown_table(
            ["Scenario", "Metric", "Baseline", "Candidate", "Oracle", "Closed Gap", "Remaining Gap", "Closure Rate"],
            table_rows,
        ),
        "",
        "## 解释",
        "",
        "- `heldout_intrinsic` 和 `loco_intrinsic` 的 closure rate 为正，说明 intrinsic reranker 确实关闭了一部分 candidate-oracle 上界差距，但距离 oracle 仍有较大空间。",
        "- Type 3 set selector 的 Coverage@5 closure 为负，说明当前 set-level 修复没有把候选池中的可用证据提前到 Top-5。",
        "- Type 3 oracle Coverage@20 明显高于 fixed method，说明候选池中仍有可利用证据；真正瓶颈更像是多证据集合选择目标，而不是完全没有候选。",
        "- 论文中可以把该结果写成“主方法有效但未穷尽候选池上界；Type 3 需要 listwise/setwise objective 或更强 query decomposition”。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def lookup_any(rows: list[dict[str, Any]], **keys: str) -> dict[str, Any]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate candidate-oracle gap analysis.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    heldout = lookup_any(rows, scenario="heldout_intrinsic", metric="mrr")
    type3 = lookup_any(rows, scenario="type3_set_coverage", metric="coverage_ratio@5")
    print(json.dumps({
        "output_report": str(args.output_report),
        "rows": len(rows),
        "heldout_mrr_closure_rate": heldout["closure_rate"],
        "type3_coverage5_closure_rate": type3["closure_rate"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
