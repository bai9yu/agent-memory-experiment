#!/usr/bin/env python3
"""Generate status report for external embedding baselines."""

from __future__ import annotations

import argparse
import csv
import json
import os
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


def summary_metric(summary_path: Path, method: str) -> dict[str, str] | None:
    if not summary_path.exists():
        return None
    for row in read_csv(summary_path):
        if row.get("method") == method:
            return row
    return None


def status_row(
    label: str,
    provider: str,
    model: str,
    key_env: str,
    result_dir: Path,
    method: str,
) -> dict[str, Any]:
    summary_path = result_dir / "summary.csv"
    metric = summary_metric(summary_path, method)
    key_available = bool(os.environ.get(key_env, ""))
    if metric:
        status = "completed"
        evidence = f"summary.csv found; {method} MRR={float(metric['mrr']):.4f}, R@5={float(metric['recall@5']):.4f}"
    elif key_available:
        status = "ready_to_run"
        evidence = f"{key_env} is available; summary.csv not found"
    else:
        status = "pending_api_key"
        evidence = f"{key_env} is not set; summary.csv not found"
    return {
        "label": label,
        "provider": provider,
        "model": model,
        "key_env": key_env,
        "key_available": key_available,
        "status": status,
        "method": method,
        "result_dir": str(result_dir),
        "summary_exists": summary_path.exists(),
        "evidence": evidence,
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    table_rows = [
        [
            row["label"],
            row["provider"],
            row["model"],
            row["key_env"],
            str(row["key_available"]),
            row["status"],
            row["method"],
            row["evidence"],
        ]
        for row in rows
    ]
    lines = [
        "# 外部 Embedding Baseline 状态",
        "",
        "本文件记录外部 embedding baseline 的接入与运行状态。它只检查环境变量是否存在，不读取、不打印 API key。",
        "",
        markdown_table(["Label", "Provider", "Model", "Key Env", "Key Available", "Status", "Method", "Evidence"], table_rows),
        "",
        "## 跑前规模预估",
        "",
        "- `outputs/agent_memory_api_embedding_run_estimate_zh.md` 记录当前 LoCoMo10 外部 embedding baseline 的文本数量、近似 token、批次数和缓存状态。",
        "",
        "## 推荐运行命令",
        "",
        "```bash",
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \\",
        "  --memories work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl \\",
        "  --queries work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl \\",
        "  --output-dir work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004 \\",
        "  --semantic-backend api \\",
        "  --api-embedding-model text-embedding-3-small \\",
        "  --api-embedding-base-url https://api.openai.com/v1 \\",
        "  --api-key-env OPENAI_API_KEY \\",
        "  --api-embedding-batch-size 128 \\",
        "  --embedding-cache-dir work/agent_memory_experiment/cache/embeddings \\",
        "  --half-life-days 30 \\",
        "  --persona-boost-weight 0.04 \\",
        "  --persona-boost-query-types 1,2,3 \\",
        "  --importance-weight 0.06 \\",
        "  --type-awareness-weight 0.04 \\",
        "  --rank-output-k 20",
        "```",
        "",
        "## 论文使用判断",
        "",
    ]
    if any(row["status"] == "completed" for row in rows):
        lines.append("- 可以把已完成的外部 embedding baseline 与 BGE-M3 主结果放在同一张对照表中。")
    else:
        lines.append("- 当前只能说明外部 embedding baseline 已具备接入和缓存框架；在实际跑完前，不能作为实验结果写入主表。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external embedding baseline status.")
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument(
        "--openai-result-dir",
        type=Path,
        default=Path("work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004"),
    )
    args = parser.parse_args()

    rows = [
        status_row(
            label="OpenAI text-embedding-3-small",
            provider="OpenAI-compatible embeddings API",
            model="text-embedding-3-small",
            key_env="OPENAI_API_KEY",
            result_dir=args.openai_result_dir,
            method="type_aware",
        )
    ]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "baselines": len(rows),
        "statuses": {row["label"]: row["status"] for row in rows},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
