#!/usr/bin/env python3
"""Generate provider profiles and commands for external embedding baselines."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any

from generate_embedding_baseline_status import load_dotenv


MEMORIES = "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
QUERIES = "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl"
BGE_SUMMARY = "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv"
CACHE_DIR = "work/agent_memory_experiment/cache/embeddings"


def safe_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value.strip()) or "custom"


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


def profile_row(
    label: str,
    provider: str,
    model: str,
    base_url: str,
    key_env: str,
    result_dir: str,
    batch_size: int,
) -> dict[str, Any]:
    return {
        "label": label,
        "provider": provider,
        "model": model,
        "base_url": base_url.rstrip("/"),
        "key_env": key_env,
        "key_available": bool(os.environ.get(key_env, "")),
        "result_dir": result_dir,
        "summary_path": f"{result_dir}/summary.csv",
        "batch_size": batch_size,
        "method": "type_aware",
        "status": "ready_to_run" if os.environ.get(key_env, "") else "pending_api_key",
    }


def build_profiles(batch_size: int) -> list[dict[str, Any]]:
    custom_model = os.environ.get("EXTERNAL_EMBEDDING_MODEL", "provider_embedding_model")
    custom_base_url = os.environ.get("EXTERNAL_EMBEDDING_BASE_URL", "https://provider.example/v1")
    return [
        profile_row(
            "OpenAI text-embedding-3-small",
            "OpenAI",
            "text-embedding-3-small",
            "https://api.openai.com/v1",
            "OPENAI_API_KEY",
            "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_openai_text_embedding_3_small_type_004",
            batch_size,
        ),
        profile_row(
            "Generic OpenAI-compatible embedding",
            "OpenAI-compatible provider",
            custom_model,
            custom_base_url,
            "EXTERNAL_EMBEDDING_API_KEY",
            f"work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_{safe_name(custom_model)}_type_004",
            batch_size,
        ),
    ]


def command_block(lines: list[str]) -> str:
    return "```bash\n" + "\n".join(lines) + "\n```"


def preflight_command(row: dict[str, Any], output_prefix: str) -> list[str]:
    return [
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/preflight_api_embedding_baseline.py \\",
        f"  --memories {MEMORIES} \\",
        f"  --queries {QUERIES} \\",
        f"  --result-dir {row['result_dir']} \\",
        "  --method type_aware \\",
        f"  --provider-label \"{row['label']}\" \\",
        f"  --model \"{row['model']}\" \\",
        f"  --base-url \"{row['base_url']}\" \\",
        f"  --batch-size {row['batch_size']} \\",
        f"  --embedding-cache-dir {CACHE_DIR} \\",
        f"  --api-key-env {row['key_env']} \\",
        "  --env-file .env \\",
        f"  --output-csv outputs/{output_prefix}_preflight.csv \\",
        f"  --output-report outputs/{output_prefix}_preflight_zh.md",
    ]


def run_command(row: dict[str, Any]) -> list[str]:
    return [
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py \\",
        f"  --memories {MEMORIES} \\",
        f"  --queries {QUERIES} \\",
        f"  --output-dir {row['result_dir']} \\",
        "  --semantic-backend api \\",
        f"  --api-embedding-model \"{row['model']}\" \\",
        f"  --api-embedding-base-url \"{row['base_url']}\" \\",
        f"  --api-key-env {row['key_env']} \\",
        "  --env-file .env \\",
        f"  --api-embedding-batch-size {row['batch_size']} \\",
        f"  --embedding-cache-dir {CACHE_DIR} \\",
        "  --half-life-days 30 \\",
        "  --persona-boost-weight 0.04 \\",
        "  --persona-boost-query-types 1,2,3 \\",
        "  --importance-weight 0.06 \\",
        "  --type-awareness-weight 0.04 \\",
        "  --rank-output-k 20",
    ]


def estimate_command(row: dict[str, Any], output_prefix: str) -> list[str]:
    return [
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py \\",
        f"  --memories {MEMORIES} \\",
        f"  --queries {QUERIES} \\",
        f"  --model \"{row['model']}\" \\",
        f"  --base-url \"{row['base_url']}\" \\",
        f"  --batch-size {row['batch_size']} \\",
        f"  --embedding-cache-dir {CACHE_DIR} \\",
        f"  --output-csv outputs/{output_prefix}_run_estimate.csv \\",
        f"  --output-report outputs/{output_prefix}_run_estimate_zh.md",
    ]


def compare_command(row: dict[str, Any], output_prefix: str) -> list[str]:
    return [
        "PYTHONPYCACHEPREFIX=/private/tmp/agent_memory_pycache \\",
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py \\",
        f"  --bge-summary {BGE_SUMMARY} \\",
        f"  --api-summary {row['summary_path']} \\",
        "  --method type_aware \\",
        f"  --api-label \"{row['label']}\" \\",
        f"  --output-csv outputs/{output_prefix}_comparison.csv \\",
        f"  --output-report outputs/{output_prefix}_comparison_zh.md",
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# 外部 Embedding Provider Profiles",
        "",
        "本文件把外部 embedding baseline 的 provider 配置、跑前检查、真实运行和结果对比命令集中到一处。它不联网、不读取 API key 内容，只根据环境变量是否存在给出可执行状态。",
        "",
        "## Provider 概览",
        "",
        "| Label | Model | Base URL | Key Env | Key Available | Status | Result Dir |",
        "|---|---|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | `{row['model']}` | `{row['base_url']}` | `{row['key_env']}` | {row['key_available']} | {row['status']} | `{row['result_dir']}` |"
        )
    lines.extend([
        "",
        "## 使用顺序",
        "",
        "1. 在 `.env` 中配置其中一个 provider 的 key/model/base URL。",
        "2. 先运行该 provider 的 preflight，确认 required checks 全部通过。",
        "3. 运行真实 API embedding baseline；首次运行会产生外部 API 调用和费用，之后应命中 embedding cache。",
        "4. 运行 compare 命令，生成相对 BGE-M3 的 delta 表，再重跑 evidence/readiness gate。",
        "",
    ])
    for idx, row in enumerate(rows, start=1):
        output_prefix = f"agent_memory_api_embedding_{idx}_{safe_name(row['label']).lower()}"
        lines.extend([
            f"## {idx}. {row['label']}",
            "",
            "### Preflight",
            "",
            command_block(preflight_command(row, output_prefix)),
            "",
            "### Estimate",
            "",
            command_block(estimate_command(row, output_prefix)),
            "",
            "### Run",
            "",
            command_block(run_command(row)),
            "",
            "### Compare With BGE-M3",
            "",
            command_block(compare_command(row, output_prefix)),
            "",
        ])
    lines.extend([
        "## 论文使用判断",
        "",
        "- 只要任一 provider 生成 `summary.csv` 并完成 compare，就可以作为外部 embedding baseline 写入对照实验。",
        "- 在 summary 生成前，本文件只能证明 provider 接入路径清楚，不能替代真实 baseline 结果。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external embedding provider profiles and run commands.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    loaded_env_keys = load_dotenv(args.env_file)
    rows = build_profiles(args.batch_size)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
        "profiles": len(rows),
        "loaded_env_keys": loaded_env_keys,
        "ready_profiles": sum(1 for row in rows if row["status"] == "ready_to_run"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
