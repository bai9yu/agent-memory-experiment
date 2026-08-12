#!/usr/bin/env python3
"""Validate which embedding-baseline paper claims are unlocked."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def as_int(value: str | int | None) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def required_preflight_pass(rows: list[dict[str, str]]) -> tuple[int, int]:
    required = [row for row in rows if row.get("severity") == "required"]
    passed = [row for row in required if as_bool(row.get("pass"))]
    return len(passed), len(required)


def completed_status(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("status") == "completed")


def ready_status(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("status") in {"ready_to_run", "completed"})


def postrun_completed(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if as_bool(row.get("postrun_pass")))


def acceptance_completed(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if as_bool(row.get("paper_acceptance_pass")))


def comparison_completed(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(row.get("status") == "completed" for row in rows)


def comparison_delta_summary(rows: list[dict[str, str]]) -> str:
    if not comparison_completed(rows):
        return "pending comparison deltas"
    parts = []
    for row in rows:
        metric = row.get("metric", "")
        delta = row.get("delta_api_minus_bge", "")
        try:
            parts.append(f"{metric}={float(delta):+.4f}")
        except ValueError:
            parts.append(f"{metric}=pending")
    return "; ".join(parts)


def gate_row(
    tier: str,
    required_evidence: str,
    passed: bool,
    evidence: str,
    allowed_claim: str,
    forbidden_claim: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "tier": tier,
        "required_evidence": required_evidence,
        "pass": passed,
        "status": "pass" if passed else "pending",
        "evidence": evidence,
        "allowed_paper_claim": allowed_claim,
        "forbidden_paper_claim": forbidden_claim,
        "next_action": next_action,
    }


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    preflight = read_csv(outputs / "agent_memory_api_embedding_preflight.csv")
    status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    comparison = read_csv(outputs / "agent_memory_embedding_baseline_comparison.csv")
    postrun = read_csv(outputs / "agent_memory_api_embedding_postrun_gate.csv")
    acceptance = read_csv(outputs / "agent_memory_api_embedding_paper_acceptance.csv")
    estimate = read_csv(outputs / "agent_memory_api_embedding_run_estimate.csv")

    required_pass, required_total = required_preflight_pass(preflight)
    ready = ready_status(status)
    completed = completed_status(status)
    postrun_pass = postrun_completed(postrun)
    acceptance_pass = acceptance_completed(acceptance)
    comparison_ok = comparison_completed(comparison)
    estimated_items = sum(as_int(row.get("items")) for row in estimate)
    estimated_tokens = sum(as_int(row.get("approx_tokens")) for row in estimate)
    uncached_batches = sum(as_int(row.get("uncached_batches")) for row in estimate)

    preflight_ok = required_total > 0 and required_pass == required_total
    run_ready = preflight_ok and ready >= 1
    result_completed = completed >= 1
    paper_ready = postrun_pass >= 1 and acceptance_pass >= 1 and comparison_ok

    return [
        gate_row(
            "protocol_ready",
            "Provider profiles, preflight, run estimate, comparison skeleton, and post-run gate exist.",
            bool(preflight and status and comparison and postrun),
            f"preflight_rows={len(preflight)}, status_rows={len(status)}, comparison_rows={len(comparison)}, postrun_rows={len(postrun)}",
            "可以写：外部 embedding baseline 的接入、费用预估、缓存和跑后验收协议已经准备。",
            "不能写：外部 embedding baseline 已完成或支持主结论。",
            "配置 OpenAI 或 OpenAI-compatible embedding provider key。",
        ),
        gate_row(
            "preflight_ready",
            "All required preflight checks pass and at least one provider is ready_to_run or completed.",
            run_ready,
            f"required_preflight={required_pass}/{required_total}, ready_or_completed_providers={ready}",
            "可以写：外部 embedding baseline 已通过跑前门禁，可以执行真实 API run。",
            "不能写：已获得外部 embedding 指标。",
            "运行真实 API embedding baseline，生成 summary/per-query/ranking 文件。",
        ),
        gate_row(
            "cost_cache_reviewed",
            "Run scale and cache estimate are available before paid/network calls.",
            bool(estimate) and estimated_items > 0,
            f"items={estimated_items}, approx_tokens={estimated_tokens}, uncached_batches={uncached_batches}",
            "可以写：真实 API baseline 的文本规模、近似 token 和缓存批次数已在运行前估算。",
            "不能写：费用估算等同于实验完成。",
            "确认预算后执行真实 API run；若数据变动，先重跑 estimate。",
        ),
        gate_row(
            "api_result_completed",
            "At least one external embedding status row is completed.",
            result_completed,
            f"completed_status_rows={completed}",
            "可以写：至少一个外部 embedding provider 已产生本地 summary 指标。",
            "不能写：可进入论文主表，除非 comparison 和 postrun gate 也通过。",
            "运行 compare_embedding_baselines.py 和 validate_api_embedding_postrun.py。",
        ),
        gate_row(
            "comparison_completed",
            "Embedding comparison table has completed deltas for all core metrics.",
            comparison_ok,
            comparison_delta_summary(comparison),
            "可以写：外部 embedding 与 BGE-M3 的 Recall/MRR delta 已可报告。",
            "不能写：post-run 文件完整性已通过，除非 postrun gate 也通过。",
            "检查 summary_by_type、per_query_metrics、rankings 并刷新 postrun gate。",
        ),
        gate_row(
            "paper_claim_ready",
            "Post-run gate and strict paper-acceptance gate have at least one completed provider, and comparison is complete.",
            paper_ready,
            f"postrun_pass={postrun_pass}, paper_acceptance_pass={acceptance_pass}, comparison_completed={comparison_ok}",
            "可以写：外部 embedding baseline 已完成，可作为论文 embedding 稳健性对照。",
            "不能写：跨所有 embedding provider 均稳健，除非新增多个 provider 并通过同一门禁。",
            "刷新 evidence matrix、manuscript、claim checks、reproducibility、freshness 和 submission readiness。",
        ),
    ]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    passed = [row for row in rows if row["pass"]]
    highest = passed[-1]["tier"] if passed else "none"
    table_rows = [
        [
            row["tier"],
            row["status"],
            row["evidence"],
            row["allowed_paper_claim"],
            row["next_action"],
        ]
        for row in rows
    ]
    lines = [
        "# Embedding Baseline Paper-Claim Upgrade Gate",
        "",
        "本文件把外部 embedding baseline 从“接入协议已准备”到“可写入论文主结果/稳健性对照”分成多个门槛。它不联网、不调用 API，也不读取或打印 key。",
        "",
        "## 总览",
        "",
        f"- Claim tiers: {len(rows)}",
        f"- Passed tiers: {len(passed)}/{len(rows)}",
        f"- Highest unlocked tier: `{highest}`",
        "",
        "## 门槛明细",
        "",
        markdown_table(["Tier", "Status", "Evidence", "Allowed Paper Claim", "Next Action"], table_rows),
        "",
        "## 使用边界",
        "",
        "- 在 `preflight_ready` 之前，只能写外部 embedding baseline 的接入协议准备好。",
        "- 在 `api_result_completed` 之前，不能写任何外部 embedding 指标。",
        "- 在 `paper_claim_ready` 之前，不能把外部 embedding baseline 写入论文主结果或稳健性结论。",
        "- 通过 `paper_claim_ready` 需要 postrun gate、strict paper-acceptance gate 和 comparison 同时通过；若要写跨 provider 稳健性，需要多个 provider 均完成并单独报告。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate embedding-baseline paper-claim upgrade tiers.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "passed_tiers": f"{sum(1 for row in rows if row['pass'])}/{len(rows)}",
        "highest_unlocked_tier": [row["tier"] for row in rows if row["pass"]][-1],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
