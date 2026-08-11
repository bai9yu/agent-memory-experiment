#!/usr/bin/env python3
"""Estimate scale, cache status, and optional cost for an API embedding run."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
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
    # Conservative tokenizer-free approximation for short English LoCoMo facts/questions.
    return max(1, math.ceil(len(text) / 4))


def summarize(kind: str, items: list[tuple[str, str]], batch_size: int, cache_file: Path, price_per_million: float) -> dict[str, Any]:
    total_chars = sum(len(text) for _, text in items)
    total_tokens = sum(approx_tokens(text) for _, text in items)
    return {
        "kind": kind,
        "items": len(items),
        "total_chars": total_chars,
        "approx_tokens": total_tokens,
        "batch_size": batch_size,
        "api_batches_if_uncached": math.ceil(len(items) / batch_size) if items else 0,
        "cache_exists": cache_file.exists(),
        "cache_path": str(cache_file),
        "estimated_cost": total_tokens * price_per_million / 1_000_000.0 if price_per_million else 0.0,
    }


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
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], model: str, base_url: str, price_per_million: float) -> None:
    total_items = sum(int(row["items"]) for row in rows)
    total_tokens = sum(int(row["approx_tokens"]) for row in rows)
    total_batches = sum(0 if row["cache_exists"] else int(row["api_batches_if_uncached"]) for row in rows)
    total_cost = sum(float(row["estimated_cost"]) for row in rows if not row["cache_exists"])
    table_rows = [
        [
            row["kind"],
            str(row["items"]),
            str(row["approx_tokens"]),
            str(row["api_batches_if_uncached"]),
            str(row["cache_exists"]),
            f"${float(row['estimated_cost']):.6f}" if price_per_million else "price_not_set",
        ]
        for row in rows
    ]
    lines = [
        "# API Embedding Baseline 运行预估",
        "",
        "本文件在不联网、不读取 API key 的情况下，预估外部 embedding baseline 的请求规模、缓存状态和可选费用。",
        "",
        "## 总览",
        "",
        f"- Model: `{model}`",
        f"- Base URL: `{base_url.rstrip('/')}`",
        f"- Total items: {total_items}",
        f"- Approx tokens: {total_tokens}",
        f"- API batches still needed if current cache is unchanged: {total_batches}",
        f"- Price per 1M tokens: {price_per_million if price_per_million else 'not_set'}",
        f"- Estimated uncached cost: ${total_cost:.6f}" if price_per_million else "- Estimated uncached cost: `price_not_set`",
        "",
        "## 明细",
        "",
        markdown_table(["Kind", "Items", "Approx Tokens", "Batches", "Cache Exists", "Estimated Cost"], table_rows),
        "",
        "## 使用说明",
        "",
        "- 如果 `cache_exists=True`，对应 memories 或 queries embedding 已经缓存，重复运行通常不会再次调用 API。",
        "- `approx_tokens` 是 tokenizer-free 估计值，用于跑前预算，不应作为论文中的精确 token 计数。",
        "- 如果需要费用估算，请通过 `--price-per-million-tokens` 手动传入当前 provider 单价。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate API embedding run scale and optional cost.")
    parser.add_argument("--memories", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--model", default="text-embedding-3-small")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    parser.add_argument("--dimensions", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--price-per-million-tokens", type=float, default=0.0)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    memories = read_jsonl(args.memories)
    queries = read_jsonl(args.queries)
    memory_items = [(row["id"], row["text"]) for row in memories]
    query_items = [(row["id"], row["query"]) for row in queries]
    rows = [
        summarize(
            "memories",
            memory_items,
            args.batch_size,
            cache_path(args.embedding_cache_dir, "memories", args.base_url, args.model, args.dimensions, memory_items),
            args.price_per_million_tokens,
        ),
        summarize(
            "queries",
            query_items,
            args.batch_size,
            cache_path(args.embedding_cache_dir, "queries", args.base_url, args.model, args.dimensions, query_items),
            args.price_per_million_tokens,
        ),
    ]
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.model, args.base_url, args.price_per_million_tokens)
    print(json.dumps({
        "output_report": str(args.output_report),
        "total_items": sum(row["items"] for row in rows),
        "approx_tokens": sum(row["approx_tokens"] for row in rows),
        "uncached_batches": sum(0 if row["cache_exists"] else row["api_batches_if_uncached"] for row in rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
