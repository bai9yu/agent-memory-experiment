#!/usr/bin/env python3
"""Strict paper-acceptance gate for completed API embedding baselines."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


CORE_METRICS = ("recall@1", "recall@3", "recall@5", "mrr")
REQUIRED_FILES = ("summary.csv", "summary_by_type.csv", "per_query_metrics.csv", "rankings.csv")
EXPECTED_QUERY_TYPES = {"1", "2", "3", "4", "5"}
EXPECTED_METHODS = {"vector", "keyword", "hybrid", "time_aware", "type_aware"}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_values_ok(row: dict[str, str] | None) -> bool:
    if row is None:
        return False
    for metric in CORE_METRICS:
        value = as_float(row.get(metric, ""))
        if value is None or value < 0.0 or value > 1.0:
            return False
    return True


def method_row(rows: list[dict[str, str]], method: str) -> dict[str, str] | None:
    for row in rows:
        if row.get("method") == method:
            return row
    return None


def comparison_status(outputs: Path, label: str) -> tuple[bool, str]:
    candidates = [outputs / "agent_memory_embedding_baseline_comparison.csv"]
    candidates.extend(sorted(outputs.glob("agent_memory_api_embedding_*_comparison.csv")))
    evidence = []
    for path in candidates:
        rows = read_csv(path)
        if not rows:
            evidence.append(f"{path}:empty_or_missing")
            continue
        label_matches = any(row.get("api_label", label) == label for row in rows)
        metric_set = {row.get("metric", "") for row in rows}
        statuses = {row.get("status", "") for row in rows}
        deltas_ok = all(row.get("delta_api_minus_bge", "") != "" for row in rows)
        ok = label_matches and metric_set >= set(CORE_METRICS) and statuses == {"completed"} and deltas_ok
        evidence.append(f"{path}:label={label_matches}, metrics={len(metric_set & set(CORE_METRICS))}/4, statuses={statuses}, deltas_ok={deltas_ok}")
        if ok:
            return True, evidence[-1]
    return False, "; ".join(evidence[:4])


def method_count(rows: list[dict[str, str]], method: str) -> int:
    return sum(1 for row in rows if row.get("method") == method)


def target_query_types(rows: list[dict[str, str]], method: str) -> set[str]:
    return {row.get("query_type", "") for row in rows if row.get("method") == method}


def build_provider_row(profile: dict[str, str], queries: Path, outputs: Path, rank_output_k: int) -> dict[str, Any]:
    label = profile.get("label", "")
    method = profile.get("method", "type_aware")
    result_dir = Path(profile.get("result_dir", ""))
    expected_queries = count_jsonl(queries)
    paths = {name: result_dir / name for name in REQUIRED_FILES}
    existing = [name for name, path in paths.items() if path.exists() and path.stat().st_size > 0]
    missing = [name for name in REQUIRED_FILES if name not in existing]
    summary_rows = read_csv(paths["summary.csv"])
    by_type_rows = read_csv(paths["summary_by_type.csv"])
    per_query_rows = read_csv(paths["per_query_metrics.csv"])
    ranking_rows = read_csv(paths["rankings.csv"])
    summary = method_row(summary_rows, method)
    summary_num_queries = int(float(summary.get("num_queries", "0"))) if summary and summary.get("num_queries", "") else 0
    by_type_target = [row for row in by_type_rows if row.get("method") == method]
    per_query_target_count = method_count(per_query_rows, method)
    ranking_target_count = method_count(ranking_rows, method)
    semantic_backends = {row.get("semantic_backend", "") for row in ranking_rows if row.get("method") == method}
    comparison_ok, comparison_evidence = comparison_status(outputs, label)
    methods_present = {row.get("method", "") for row in summary_rows}
    by_type_query_types = target_query_types(by_type_rows, method)
    expected_ranking_rows = expected_queries * rank_output_k
    acceptance_pass = (
        not missing
        and expected_queries > 0
        and summary_num_queries == expected_queries
        and metric_values_ok(summary)
        and per_query_target_count == expected_queries
        and ranking_target_count == expected_ranking_rows
        and by_type_query_types >= EXPECTED_QUERY_TYPES
        and methods_present >= EXPECTED_METHODS
        and comparison_ok
    )
    if acceptance_pass:
        status = "accepted_for_paper"
    elif paths["summary.csv"].exists():
        status = "partial_or_failed_acceptance"
    else:
        status = "pending_api_run"
    return {
        "label": label,
        "model": profile.get("model", ""),
        "method": method,
        "status": status,
        "paper_acceptance_pass": acceptance_pass,
        "expected_queries": expected_queries,
        "summary_num_queries": summary_num_queries,
        "summary_metrics_ok": metric_values_ok(summary),
        "per_query_target_rows": per_query_target_count,
        "expected_per_query_rows": expected_queries,
        "ranking_target_rows": ranking_target_count,
        "expected_ranking_rows": expected_ranking_rows,
        "summary_by_type_query_types": ";".join(sorted(by_type_query_types)),
        "expected_query_types": ";".join(sorted(EXPECTED_QUERY_TYPES)),
        "summary_methods_present": ";".join(sorted(methods_present)),
        "semantic_backends": ";".join(sorted(semantic_backends)),
        "comparison_completed": comparison_ok,
        "comparison_evidence": comparison_evidence,
        "existing_files": ";".join(existing),
        "missing_files": ";".join(missing),
        "result_dir": str(result_dir),
    }


def build_rows(profile_csv: Path, queries: Path, outputs: Path, rank_output_k: int) -> list[dict[str, Any]]:
    profiles = read_csv(profile_csv)
    if not profiles:
        return [{
            "label": "no_provider_profiles",
            "model": "",
            "method": "",
            "status": "profile_missing",
            "paper_acceptance_pass": False,
            "expected_queries": count_jsonl(queries),
            "summary_num_queries": 0,
            "summary_metrics_ok": False,
            "per_query_target_rows": 0,
            "expected_per_query_rows": count_jsonl(queries),
            "ranking_target_rows": 0,
            "expected_ranking_rows": 0,
            "summary_by_type_query_types": "",
            "expected_query_types": ";".join(sorted(EXPECTED_QUERY_TYPES)),
            "summary_methods_present": "",
            "semantic_backends": "",
            "comparison_completed": False,
            "comparison_evidence": "provider profile csv missing or empty",
            "existing_files": "",
            "missing_files": ";".join(REQUIRED_FILES),
            "result_dir": "",
        }]
    return [build_provider_row(profile, queries, outputs, rank_output_k) for profile in profiles]


def write_report(path: Path, rows: list[dict[str, Any]], profile_csv: Path, queries: Path, rank_output_k: int) -> None:
    accepted = [row for row in rows if row["paper_acceptance_pass"]]
    partial = [row for row in rows if row["status"] == "partial_or_failed_acceptance"]
    table = [
        [
            row["label"],
            row["status"],
            str(row["summary_num_queries"]) + "/" + str(row["expected_queries"]),
            str(row["summary_metrics_ok"]),
            str(row["per_query_target_rows"]) + "/" + str(row["expected_per_query_rows"]),
            str(row["ranking_target_rows"]) + "/" + str(row["expected_ranking_rows"]),
            str(row["comparison_completed"]),
            row["missing_files"] or "none",
        ]
        for row in rows
    ]
    lines = [
        "# API Embedding Paper Acceptance Gate",
        "",
        "本文件是外部 API embedding baseline 的严格论文引用门禁。它不联网、不调用 provider、也不读取 API key；只检查真实运行后落到本地的结果是否覆盖完整 LoCoMo10 answerable slice，并且是否已生成与 BGE-M3 的完整 delta 表。",
        "",
        "## 总览",
        "",
        f"- Provider profile source: `{profile_csv}`",
        f"- Query source: `{queries}`",
        f"- Expected rank_output_k: {rank_output_k}",
        f"- Providers checked: {len(rows)}",
        f"- Accepted for paper: {len(accepted)}",
        f"- Partial/failed local results: {len(partial)}",
        f"- Ready to cite external embedding baseline: {bool(accepted)}",
        "",
        "## 明细",
        "",
        markdown_table(["Label", "Status", "Summary Queries", "Metrics OK", "Per-Query Rows", "Ranking Rows", "Comparison", "Missing Files"], table),
        "",
        "## Acceptance Rules",
        "",
        "- `summary.csv` 必须包含目标 method，且 `num_queries` 等于当前 answerable query 数。",
        "- `recall@1/3/5` 和 `mrr` 必须能解析为 `[0, 1]` 区间内的数值。",
        "- `per_query_metrics.csv` 中目标 method 的行数必须等于 query 数。",
        "- `rankings.csv` 中目标 method 的行数必须等于 `query 数 * rank_output_k`。",
        "- `summary_by_type.csv` 必须覆盖 LoCoMo query type 1-5。",
        "- `summary.csv` 必须保留 vector/keyword/hybrid/time_aware/type_aware 方法，防止只跑单一不完整配置。",
        "- comparison 表必须包含 4 个核心指标且状态为 completed。",
        "",
        "## 论文使用边界",
        "",
    ]
    if accepted:
        lines.append("- 可以把 accepted provider 写入外部 embedding baseline 对照实验。")
    else:
        lines.append("- 当前没有 provider 通过严格论文引用门禁；只能写接入协议、费用估计和跑后验收流程已经准备好。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate strict paper acceptance for API embedding baselines.")
    parser.add_argument("--profile-csv", type=Path, default=Path("outputs/agent_memory_embedding_provider_profiles.csv"))
    parser.add_argument("--queries", type=Path, default=Path("work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl"))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--rank-output-k", type=int, default=20)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.profile_csv, args.queries, args.outputs_dir, args.rank_output_k)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.profile_csv, args.queries, args.rank_output_k)
    print(json.dumps({
        "output_report": str(args.output_report),
        "providers": len(rows),
        "accepted_for_paper": sum(1 for row in rows if row["paper_acceptance_pass"]),
        "partial_or_failed": sum(1 for row in rows if row["status"] == "partial_or_failed_acceptance"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
