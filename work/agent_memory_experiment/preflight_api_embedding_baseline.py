#!/usr/bin/env python3
"""Preflight checks for the external API embedding baseline.

The script does not call the provider and never prints API-key values. It checks
that the local inputs, key name, cache paths, and expected outputs are coherent
before the paid/networked baseline run starts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def load_dotenv(path: Path) -> list[str]:
    loaded_keys = []
    if not path.exists():
        return loaded_keys
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        loaded_keys.append(key)
        if key not in os.environ:
            os.environ[key] = value
    return loaded_keys


def safe_cache_name(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def embedding_cache_key(kind: str, model_name: str, items: list[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    digest.update(kind.encode("utf-8"))
    digest.update(b"\n")
    digest.update(model_name.encode("utf-8"))
    for item_id, text in items:
        digest.update(b"\n")
        digest.update(item_id.encode("utf-8"))
        digest.update(b"\t")
        digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def cache_model_name(base_url: str, model: str, dimensions: int) -> str:
    dims = f":dim{dimensions}" if dimensions else ""
    return f"{base_url.rstrip('/')}:{model}{dims}"


def cache_path(cache_dir: Path, kind: str, base_url: str, model: str, dimensions: int, items: list[tuple[str, str]]) -> Path:
    key = embedding_cache_key(kind, cache_model_name(base_url, model, dimensions), items)
    return cache_dir / "api" / safe_cache_name(model) / f"{kind}_{key}.npz"


def approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def summary_has_method(path: Path, method: str) -> bool:
    if not path.exists():
        return False
    return any(row.get("method") == method for row in read_csv(path))


def check_row(name: str, passed: bool, evidence: str, severity: str = "required") -> dict[str, Any]:
    return {
        "check": name,
        "pass": passed,
        "severity": severity,
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


def write_report(
    path: Path,
    rows: list[dict[str, Any]],
    args: argparse.Namespace,
    loaded_env_keys: list[str],
    total_items: int,
    total_tokens: int,
    uncached_batches: int,
) -> None:
    required_rows = [row for row in rows if row["severity"] == "required"]
    required_pass = sum(1 for row in required_rows if row["pass"])
    all_required_pass = required_pass == len(required_rows)
    table_rows = [
        [row["check"], str(row["pass"]), row["severity"], row["evidence"]]
        for row in rows
    ]
    lines = [
        "# API Embedding Baseline Preflight",
        "",
        "本文件是外部 embedding baseline 的跑前门禁。它不联网、不调用 provider、不打印 API key，只检查本地输入、环境变量、缓存和目标结果是否处于可运行状态。",
        "",
        "## 总览",
        "",
        f"- Provider label: `{args.provider_label}`",
        f"- Model: `{args.model}`",
        f"- Base URL: `{args.base_url.rstrip('/')}`",
        f"- Required checks: {required_pass}/{len(required_rows)}",
        f"- Ready to run paid/API baseline: {all_required_pass}",
        f"- Input items: {total_items}",
        f"- Approx tokens: {total_tokens}",
        f"- API batches still needed if cache is unchanged: {uncached_batches}",
        f"- Existing result summary satisfies method: {summary_has_method(args.result_dir / 'summary.csv', args.method)}",
        "",
        "## 环境",
        "",
        f"- Env file: `{args.env_file}`",
        f"- Env file exists: {args.env_file.exists()}",
        f"- Loaded key names: {', '.join(loaded_env_keys) if loaded_env_keys else 'none'}",
        f"- Required key name: `{args.api_key_env}`",
        "",
        "## 检查明细",
        "",
        markdown_table(["Check", "Pass", "Severity", "Evidence"], table_rows),
        "",
        "## 下一步",
        "",
    ]
    if all_required_pass:
        lines.append("- 可以运行 README 中的 API embedding baseline 命令；若缓存不存在，会产生真实 API 调用和费用。")
    else:
        lines.append("- 先修复未通过的 required check；当前不建议启动付费/API baseline。")
    if uncached_batches:
        lines.append("- 首次运行后会写入 embedding cache；之后重复实验应优先命中缓存。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight API embedding baseline without network calls.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--method", default="type_aware")
    parser.add_argument("--provider-label", default="OpenAI text-embedding-3-small")
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--dimensions", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    loaded_env_keys = load_dotenv(args.env_file)
    memories = read_jsonl(args.memories) if args.memories.exists() else []
    queries = read_jsonl(args.queries) if args.queries.exists() else []
    memory_items = [(row.get("id", ""), row.get("text", "")) for row in memories]
    query_items = [(row.get("id", ""), row.get("query", "")) for row in queries]
    memory_cache = cache_path(args.embedding_cache_dir, "memories", args.base_url, args.model, args.dimensions, memory_items)
    query_cache = cache_path(args.embedding_cache_dir, "queries", args.base_url, args.model, args.dimensions, query_items)
    summary_path = args.result_dir / "summary.csv"
    total_items = len(memory_items) + len(query_items)
    total_tokens = sum(approx_tokens(text) for _, text in memory_items + query_items)
    uncached_batches = (
        (0 if memory_cache.exists() else math.ceil(len(memory_items) / max(args.batch_size, 1)))
        + (0 if query_cache.exists() else math.ceil(len(query_items) / max(args.batch_size, 1)))
    )

    rows = [
        check_row("memories file exists", args.memories.exists(), str(args.memories)),
        check_row("queries file exists", args.queries.exists(), str(args.queries)),
        check_row("memory rows available", len(memory_items) > 0, str(len(memory_items))),
        check_row("query rows available", len(query_items) > 0, str(len(query_items))),
        check_row("api key available", bool(os.environ.get(args.api_key_env, "")), f"{args.api_key_env} set={bool(os.environ.get(args.api_key_env, ''))}"),
        check_row("embedding cache dir parent exists", args.embedding_cache_dir.exists(), str(args.embedding_cache_dir), "optional"),
        check_row("memory cache exists", memory_cache.exists(), str(memory_cache), "optional"),
        check_row("query cache exists", query_cache.exists(), str(query_cache), "optional"),
        check_row("result summary exists", summary_path.exists(), str(summary_path), "optional"),
        check_row("result summary has method", summary_has_method(summary_path, args.method), args.method, "optional"),
    ]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args, loaded_env_keys, total_items, total_tokens, uncached_batches)
    required_rows = [row for row in rows if row["severity"] == "required"]
    print(json.dumps({
        "output_report": str(args.output_report),
        "required_checks": f"{sum(1 for row in required_rows if row['pass'])}/{len(required_rows)}",
        "ready_to_run": all(row["pass"] for row in required_rows),
        "uncached_batches": uncached_batches,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
