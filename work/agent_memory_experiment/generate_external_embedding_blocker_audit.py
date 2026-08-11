#!/usr/bin/env python3
"""Generate an actionable blocker audit for external embedding baselines."""

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
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def build_action_rows(outputs: Path) -> list[dict[str, Any]]:
    status_rows = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    preflight_rows = read_csv(outputs / "agent_memory_api_embedding_preflight.csv")
    estimate_rows = read_csv(outputs / "agent_memory_api_embedding_run_estimate.csv")
    comparison_rows = read_csv(outputs / "agent_memory_embedding_baseline_comparison.csv")
    readiness_rows = read_csv(outputs / "agent_memory_submission_readiness_gate.csv")

    openai_status = find_row(status_rows, "label", "OpenAI text-embedding-3-small")
    generic_status = find_row(status_rows, "label", "Generic OpenAI-compatible embedding")
    api_key_check = find_row(preflight_rows, "check", "api key available")
    completed_gate = find_row(readiness_rows, "gate", "external_embedding_completed")
    preflight_gate = find_row(readiness_rows, "gate", "api_embedding_preflight")

    total_items = ""
    approx_tokens = ""
    uncached_batches = ""
    if estimate_rows and "kind" in estimate_rows[0]:
        total_items = str(sum(int(row.get("items", "0") or 0) for row in estimate_rows))
        approx_tokens = str(sum(int(row.get("approx_tokens", "0") or 0) for row in estimate_rows))
        uncached_batches = str(sum(int(row.get("api_batches_if_uncached", "0") or 0) for row in estimate_rows if row.get("cache_exists") != "True"))
    else:
        for row in estimate_rows:
            metric = row.get("metric", "")
            if metric == "total_items":
                total_items = row.get("value", "")
            elif metric == "approx_tokens":
                approx_tokens = row.get("value", "")
            elif metric == "uncached_batches":
                uncached_batches = row.get("value", "")
        if not total_items and estimate_rows:
            total_items = estimate_rows[0].get("total_items", "")
            approx_tokens = estimate_rows[0].get("approx_tokens", "")
            uncached_batches = estimate_rows[0].get("uncached_batches", "")

    comparison_ready = any(row.get("status") == "completed" for row in comparison_rows)

    rows: list[dict[str, Any]] = [
        {
            "item": "default_openai_key",
            "status": "pass" if openai_status and openai_status.get("key_available") == "True" else "blocker",
            "evidence": openai_status.get("evidence", "status row missing") if openai_status else "OpenAI status row missing",
            "required_action": "Set OPENAI_API_KEY in .env or shell, then rerun preflight.",
            "unblocks": "api_embedding_preflight",
        },
        {
            "item": "generic_provider_key",
            "status": "pass" if generic_status and generic_status.get("key_available") == "True" else "alternative_missing",
            "evidence": generic_status.get("evidence", "status row missing") if generic_status else "Generic provider status row missing",
            "required_action": "Alternatively set EXTERNAL_EMBEDDING_API_KEY, EXTERNAL_EMBEDDING_MODEL, and EXTERNAL_EMBEDDING_BASE_URL.",
            "unblocks": "api_embedding_preflight",
        },
        {
            "item": "preflight_required_checks",
            "status": "pass" if preflight_gate and preflight_gate.get("pass") == "True" else "blocker",
            "evidence": preflight_gate.get("evidence", "preflight gate missing") if preflight_gate else "preflight gate missing",
            "required_action": "Run preflight_api_embedding_baseline.py after configuring an embedding provider key.",
            "unblocks": "safe paid/API run",
        },
        {
            "item": "run_scale_known",
            "status": "pass" if total_items or approx_tokens else "needs_refresh",
            "evidence": f"items={total_items or 'unknown'}, approx_tokens={approx_tokens or 'unknown'}, uncached_batches={uncached_batches or 'unknown'}",
            "required_action": "Rerun estimate_api_embedding_run.py if memories or queries change.",
            "unblocks": "cost/risk planning",
        },
        {
            "item": "external_summary_completed",
            "status": "pass" if completed_gate and completed_gate.get("pass") == "True" else "blocker",
            "evidence": completed_gate.get("evidence", "completed gate missing") if completed_gate else "completed gate missing",
            "required_action": "Run memory_eval.py with semantic-backend api and generate summary.csv.",
            "unblocks": "external_embedding_completed",
        },
        {
            "item": "comparison_table_completed",
            "status": "pass" if comparison_ready else "pending_summary",
            "evidence": "completed API/BGE delta exists" if comparison_ready else "API summary not available; comparison remains pending",
            "required_action": "Run compare_embedding_baselines.py after API summary.csv exists.",
            "unblocks": "paper embedding baseline table",
        },
    ]
    return rows


def write_report(path: Path, rows: list[dict[str, Any]], outputs: Path) -> None:
    blocker_count = sum(1 for row in rows if row["status"] == "blocker")
    table_rows = [
        [row["item"], row["status"], row["evidence"], row["required_action"], row["unblocks"]]
        for row in rows
    ]
    lines = [
        "# External Embedding Baseline Blocker Audit",
        "",
        "本文件把外部 embedding baseline 的投稿 blocker 拆成可执行检查项。它不读取、不打印 API key，也不发起网络请求；只汇总当前本地证据，说明为什么还不能把外部 embedding 写进论文主结果。",
        "",
        "## 总览",
        "",
        f"- Blocker count: {blocker_count}",
        f"- Status source: `{outputs / 'agent_memory_embedding_baseline_status.csv'}`",
        f"- Preflight source: `{outputs / 'agent_memory_api_embedding_preflight.csv'}`",
        f"- Estimate source: `{outputs / 'agent_memory_api_embedding_run_estimate.csv'}`",
        f"- Readiness source: `{outputs / 'agent_memory_submission_readiness_gate.csv'}`",
        "",
        markdown_table(["Item", "Status", "Evidence", "Required Action", "Unblocks"], table_rows),
        "",
        "## 结论",
        "",
    ]
    if blocker_count:
        lines.extend([
            "- 当前不能启动真实外部 embedding baseline，也不能把外部 embedding 对照写成已完成实验。",
            "- 当前 `.env` 中的 DeepSeek key 可用于 LLM memory writer / LLM-assisted audit，但不能解除 embedding baseline blocker。",
            "- 最小解除路径：配置 `OPENAI_API_KEY`，或配置 `EXTERNAL_EMBEDDING_API_KEY` + `EXTERNAL_EMBEDDING_MODEL` + `EXTERNAL_EMBEDDING_BASE_URL`，然后按 README 的 preflight -> memory_eval -> compare 顺序运行。",
        ])
    else:
        lines.extend([
            "- 外部 embedding blocker 已解除，可以把 API embedding baseline 与 BGE-M3 主结果进行对比。",
            "- 投稿前仍需确认生成的 comparison table 已纳入论文表格和 evidence matrix。",
        ])
    lines.extend([
        "",
        "## 复现实验命令顺序",
        "",
        "1. `generate_embedding_baseline_status.py`：确认 key 是否存在以及 summary 是否已完成。",
        "2. `preflight_api_embedding_baseline.py`：确认输入、key、缓存和输出路径。",
        "3. `estimate_api_embedding_run.py`：确认文本数量、近似 token 和未缓存批次数。",
        "4. `memory_eval.py --semantic-backend api`：执行真实外部 embedding baseline。",
        "5. `compare_embedding_baselines.py`：生成相对 BGE-M3 的 delta 表。",
        "6. `validate_submission_readiness.py`：确认 `api_embedding_preflight` 与 `external_embedding_completed` 门禁是否解除。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external embedding blocker audit.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    rows = build_action_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.outputs_dir)
    print(json.dumps({
        "output_report": str(args.output_report),
        "blockers": sum(1 for row in rows if row["status"] == "blocker"),
        "rows": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
