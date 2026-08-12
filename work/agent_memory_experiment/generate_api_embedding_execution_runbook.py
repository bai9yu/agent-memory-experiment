#!/usr/bin/env python3
"""Generate a paper-safe execution runbook for external API embedding baselines."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


MEMORIES = "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_memories.jsonl"
QUERIES = "work/agent_memory_experiment/data/llm_extracted_locomo10_all_v3_answerable_queries.jsonl"
BGE_SUMMARY = "work/agent_memory_experiment/results/llm_extracted_locomo10_all_v3_answerable_bge_m3_type_004_with_keyword/summary.csv"
CACHE_DIR = "work/agent_memory_experiment/cache/embeddings"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def slug(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "provider"


def line_join(parts: list[str]) -> str:
    return " \\\n  ".join(parts)


def preflight_command(profile: dict[str, str], output_prefix: str) -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/preflight_api_embedding_baseline.py",
        f"--memories {MEMORIES}",
        f"--queries {QUERIES}",
        f"--result-dir {profile['result_dir']}",
        "--method type_aware",
        f"--provider-label \"{profile['label']}\"",
        f"--model \"{profile['model']}\"",
        f"--base-url \"{profile['base_url']}\"",
        f"--dimensions {profile.get('dimensions', '0')}",
        f"--batch-size {profile.get('batch_size', '128')}",
        f"--embedding-cache-dir {CACHE_DIR}",
        f"--api-key-env {profile['key_env']}",
        "--env-file .env",
        f"--output-csv outputs/{output_prefix}_preflight.csv",
        f"--output-report outputs/{output_prefix}_preflight_zh.md",
    ])


def estimate_command(profile: dict[str, str], output_prefix: str) -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/estimate_api_embedding_run.py",
        f"--memories {MEMORIES}",
        f"--queries {QUERIES}",
        f"--model \"{profile['model']}\"",
        f"--base-url \"{profile['base_url']}\"",
        f"--dimensions {profile.get('dimensions', '0')}",
        f"--batch-size {profile.get('batch_size', '128')}",
        f"--embedding-cache-dir {CACHE_DIR}",
        f"--output-csv outputs/{output_prefix}_run_estimate.csv",
        f"--output-report outputs/{output_prefix}_run_estimate_zh.md",
    ])


def run_command(profile: dict[str, str]) -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/memory_eval.py",
        f"--memories {MEMORIES}",
        f"--queries {QUERIES}",
        f"--output-dir {profile['result_dir']}",
        "--semantic-backend api",
        f"--api-embedding-model \"{profile['model']}\"",
        f"--api-embedding-base-url \"{profile['base_url']}\"",
        f"--api-key-env {profile['key_env']}",
        "--env-file .env",
        f"--api-embedding-batch-size {profile.get('batch_size', '128')}",
        f"--api-embedding-dimensions {profile.get('dimensions', '0')}",
        f"--embedding-cache-dir {CACHE_DIR}",
        "--half-life-days 30",
        "--persona-boost-weight 0.04",
        "--persona-boost-query-types 1,2,3",
        "--importance-weight 0.06",
        "--type-awareness-weight 0.04",
        "--rank-output-k 20",
    ])


def compare_command(profile: dict[str, str], output_prefix: str) -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/compare_embedding_baselines.py",
        f"--bge-summary {BGE_SUMMARY}",
        f"--api-summary {profile['summary_path']}",
        "--method type_aware",
        f"--api-label \"{profile['label']}\"",
        f"--output-csv outputs/{output_prefix}_comparison.csv",
        f"--output-report outputs/{output_prefix}_comparison_zh.md",
    ])


def postrun_command() -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/validate_api_embedding_postrun.py",
        "--profile-csv outputs/agent_memory_embedding_provider_profiles.csv",
        "--outputs-dir outputs",
        "--output-csv outputs/agent_memory_api_embedding_postrun_gate.csv",
        "--output-report outputs/agent_memory_api_embedding_postrun_gate_zh.md",
    ])


def refresh_command() -> str:
    return line_join([
        "work/agent_memory_experiment/.venv/bin/python work/agent_memory_experiment/refresh_paper_artifacts.py",
        "--project-root .",
        "--output-csv outputs/agent_memory_paper_artifact_refresh_run.csv",
        "--output-report outputs/agent_memory_paper_artifact_refresh_run_zh.md",
    ])


def build_rows(profile_csv: Path, preflight_csv: Path, estimate_csv: Path, postrun_csv: Path) -> list[dict[str, Any]]:
    profiles = read_csv(profile_csv)
    preflight_rows = read_csv(preflight_csv)
    estimate_rows = read_csv(estimate_csv)
    postrun_rows = read_csv(postrun_csv)
    ready_preflight = sum(1 for row in preflight_rows if row.get("severity") == "required" and row.get("pass") == "True")
    required_preflight = sum(1 for row in preflight_rows if row.get("severity") == "required")
    estimate_evidence = "; ".join(
        (
            f"{row.get('kind', 'unknown')}: items={row.get('items', '')}, "
            f"tokens={row.get('approx_tokens', '')}, "
            f"batches={row.get('api_batches_if_uncached', '')}, "
            f"cache_exists={row.get('cache_exists', '')}"
        )
        for row in estimate_rows
    )
    postrun_completed = sum(1 for row in postrun_rows if row.get("postrun_pass") == "True")
    rows: list[dict[str, Any]] = []
    for idx, profile in enumerate(profiles, start=1):
        prefix = f"agent_memory_api_embedding_{idx}_{slug(profile.get('label', 'provider'))}"
        key_ready = profile.get("key_available") == "True"
        row_common = {
            "provider_label": profile.get("label", ""),
            "model": profile.get("model", ""),
            "base_url": profile.get("base_url", ""),
            "key_env": profile.get("key_env", ""),
            "result_dir": profile.get("result_dir", ""),
        }
        steps = [
            (
                "1_configure_key",
                "manual",
                key_ready,
                f"{profile.get('key_env', '')} available={key_ready}",
                "Store the provider key in .env or shell; never commit the key.",
                f"Set the {profile.get('key_env', '')} environment variable in .env or shell.",
            ),
            (
                "2_preflight",
                "offline_check",
                required_preflight > 0 and ready_preflight == required_preflight and key_ready,
                f"default preflight required={ready_preflight}/{required_preflight}; provider key available={key_ready}",
                "All required preflight checks pass before any paid/network API call.",
                preflight_command(profile, prefix),
            ),
            (
                "3_cost_and_cache_estimate",
                "offline_check",
                bool(estimate_rows),
                estimate_evidence or "estimate missing",
                "Review item count, approximate tokens, uncached batches, and expected cache reuse.",
                estimate_command(profile, prefix),
            ),
            (
                "4_real_api_run",
                "network_paid_run",
                False,
                "intentionally not run by offline refresh",
                "Run only after preflight passes and expected cost/cache behavior is acceptable.",
                run_command(profile),
            ),
            (
                "5_compare_with_bge_m3",
                "offline_after_run",
                False,
                "requires provider summary.csv from real API run",
                "Generate numeric delta table versus BGE-M3 after summary.csv exists.",
                compare_command(profile, prefix),
            ),
            (
                "6_postrun_gate",
                "offline_after_run",
                postrun_completed > 0,
                f"completed_for_paper={postrun_completed}",
                "Post-run gate and paper acceptance gate must report at least one provider completed/accepted for paper.",
                postrun_command(),
            ),
            (
                "7_final_refresh",
                "offline_after_run",
                False,
                "run after external baseline and comparison are complete",
                "Refresh evidence matrix, manuscript, claim checks, reproducibility, freshness, and submission readiness.",
                refresh_command(),
            ),
        ]
        for order, phase, current_pass, evidence, acceptance, command in steps:
            rows.append({
                **row_common,
                "step": order,
                "phase": phase,
                "current_pass": current_pass,
                "evidence": evidence,
                "acceptance": acceptance,
                "command": command,
            })
    if not rows:
        rows.append({
            "provider_label": "no_profiles",
            "model": "",
            "base_url": "",
            "key_env": "",
            "result_dir": "",
            "step": "profile_missing",
            "phase": "offline_check",
            "current_pass": False,
            "evidence": str(profile_csv),
            "acceptance": "Regenerate provider profiles before running an external baseline.",
            "command": "work/agent_memory_experiment/generate_embedding_provider_profiles.py",
        })
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    providers = list(dict.fromkeys(row["provider_label"] for row in rows))
    paid_steps = [row for row in rows if row["phase"] == "network_paid_run"]
    completed = [row for row in rows if row["step"] == "6_postrun_gate" and row["current_pass"]]
    table = [
        [
            row["provider_label"],
            row["step"],
            row["phase"],
            str(row["current_pass"]),
            row["evidence"],
            row["acceptance"],
        ]
        for row in rows
    ]
    lines = [
        "# API Embedding Execution Runbook",
        "",
        "本文件把外部 API embedding baseline 的真实运行路径整理成可执行 runbook。它不联网、不读取 API key 内容，也不会自动启动付费调用；目标是在拿到 key 后按同一顺序关闭 external embedding blocker。",
        "",
        "## 总览",
        "",
        f"- Providers: {len(providers)}",
        f"- Paid/network steps listed: {len(paid_steps)}",
        f"- Providers completed for paper: {len(completed)}",
        f"- Offline refresh starts paid run: False",
        "",
        "## Step Matrix",
        "",
        markdown_table(["Provider", "Step", "Phase", "Current Pass", "Evidence", "Acceptance"], table),
        "",
        "## 使用方式",
        "",
        "1. 选择一个 provider。",
        "2. 完成 `1_configure_key`，确保 key 只在 `.env` 或 shell 中，不进入 Git。",
        "3. 运行 `2_preflight` 和 `3_cost_and_cache_estimate`。",
        "4. 只有 preflight 全部通过、费用/缓存可接受时，才运行 `4_real_api_run`。",
        "5. 跑完后依次运行 compare、postrun gate、paper acceptance gate 和 final refresh。",
        "",
        "## 论文使用边界",
        "",
        "- 可以写：外部 embedding baseline 的真实运行和验收路径已经固定，且离线刷新不会误触发付费 API。",
        "- 不能写：runbook 生成完成就等于外部 embedding baseline 已完成；最终仍以 postrun gate completed_for_paper 和 paper acceptance accepted_for_paper 为准。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external API embedding execution runbook.")
    parser.add_argument("--profile-csv", type=Path, default=Path("outputs/agent_memory_embedding_provider_profiles.csv"))
    parser.add_argument("--preflight-csv", type=Path, default=Path("outputs/agent_memory_api_embedding_preflight.csv"))
    parser.add_argument("--estimate-csv", type=Path, default=Path("outputs/agent_memory_api_embedding_run_estimate.csv"))
    parser.add_argument("--postrun-csv", type=Path, default=Path("outputs/agent_memory_api_embedding_postrun_gate.csv"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_api_embedding_execution_runbook.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_api_embedding_execution_runbook_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.profile_csv, args.preflight_csv, args.estimate_csv, args.postrun_csv)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "providers": len(set(row["provider_label"] for row in rows)),
        "paid_steps": sum(1 for row in rows if row["phase"] == "network_paid_run"),
        "completed_for_paper": sum(1 for row in rows if row["step"] == "6_postrun_gate" and row["current_pass"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
