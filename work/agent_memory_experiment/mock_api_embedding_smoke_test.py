#!/usr/bin/env python3
"""Run an offline smoke test for the API embedding backend.

This uses a localhost OpenAI-compatible `/v1/embeddings` mock server. It proves
the API backend, result writer, and embedding cache path without spending API
credits or requiring a real provider key.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


class EmbeddingMockHandler(BaseHTTPRequestHandler):
    request_count = 0
    input_count = 0
    dims = 32

    def log_message(self, format: str, *args: object) -> None:
        return

    @classmethod
    def reset_counts(cls) -> None:
        cls.request_count = 0
        cls.input_count = 0

    @staticmethod
    def embed(text: str, dims: int) -> list[float]:
        values = []
        for idx in range(dims):
            digest = hashlib.sha256(f"{idx}\t{text}".encode("utf-8")).digest()
            raw = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
            values.append((raw * 2.0) - 1.0)
        return values

    def do_POST(self) -> None:
        if self.path != "/v1/embeddings":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        inputs = payload.get("input", [])
        if isinstance(inputs, str):
            inputs = [inputs]
        EmbeddingMockHandler.request_count += 1
        EmbeddingMockHandler.input_count += len(inputs)
        data = [
            {
                "object": "embedding",
                "index": idx,
                "embedding": self.embed(str(text), self.dims),
            }
            for idx, text in enumerate(inputs)
        ]
        body = json.dumps({
            "object": "list",
            "model": payload.get("model", "mock-embedding-small"),
            "data": data,
            "usage": {"prompt_tokens": 0, "total_tokens": 0},
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


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


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def run_memory_eval(args: argparse.Namespace, base_url: str, cache_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AGENT_MEMORY_MOCK_API_KEY"] = "mock_key_for_local_smoke_test"
    command = [
        sys.executable,
        str(args.memory_eval),
        "--memories",
        str(args.memories),
        "--queries",
        str(args.queries),
        "--output-dir",
        str(args.output_dir),
        "--semantic-backend",
        "api",
        "--api-embedding-model",
        "mock-embedding-small",
        "--api-embedding-base-url",
        base_url,
        "--api-key-env",
        "AGENT_MEMORY_MOCK_API_KEY",
        "--api-embedding-batch-size",
        str(args.batch_size),
        "--embedding-cache-dir",
        str(cache_dir),
        "--half-life-days",
        "30",
        "--persona-boost-weight",
        "0.04",
        "--persona-boost-query-types",
        "1,2,3",
        "--importance-weight",
        "0.06",
        "--type-awareness-weight",
        "0.04",
        "--rank-output-k",
        "5",
    ]
    return subprocess.run(command, check=True, capture_output=True, text=True, env=env)


def write_report(path: Path, rows: list[dict[str, Any]], summary_rows: list[dict[str, str]], output_dir: Path) -> None:
    type_aware = next((row for row in summary_rows if row.get("method") == "type_aware"), {})
    lines = [
        "# Mock API Embedding Smoke Test",
        "",
        "本文件记录 API embedding backend 的离线 smoke test。测试使用 localhost mock server，不访问外网、不使用真实 API key、不产生费用。",
        "",
        "## 结论",
        "",
        f"- Output dir: `{output_dir}`",
        f"- First run API requests: {rows[0]['requests']}",
        f"- Second run API requests: {rows[1]['requests']}",
        f"- Cache hit verified: {rows[1]['requests'] == 0}",
        f"- Summary has type_aware: {bool(type_aware)}",
    ]
    if type_aware:
        lines.extend([
            f"- Mock type_aware MRR: {float(type_aware['mrr']):.4f}",
            f"- Mock type_aware Recall@5: {float(type_aware['recall@5']):.4f}",
        ])
    lines.extend([
        "",
        "## 运行明细",
        "",
        markdown_table(
            ["Run", "Requests", "Inputs", "Summary Exists", "Rankings Exists"],
            [
                [
                    str(row["run"]),
                    str(row["requests"]),
                    str(row["inputs"]),
                    str(row["summary_exists"]),
                    str(row["rankings_exists"]),
                ]
                for row in rows
            ],
        ),
        "",
        "## 论文使用判断",
        "",
        "- 该 smoke test 只能证明 API embedding backend、缓存和结果写入通路可运行，不能替代真实外部 embedding baseline。",
        "- 投稿主结果仍需要真实 provider summary.csv，并与 BGE-M3 生成 delta 对比。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Run offline API embedding backend smoke test.")
    parser.add_argument("--memory-eval", type=Path, default=base / "memory_eval.py")
    parser.add_argument("--memories", type=Path, default=base / "data" / "sample_10.jsonl")
    parser.add_argument("--queries", type=Path, default=base / "data" / "queries_10.jsonl")
    parser.add_argument("--output-dir", type=Path, default=base / "results" / "api_embedding_mock_smoke_test")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", 0), EmbeddingMockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}/v1"

    rows = []
    try:
        with tempfile.TemporaryDirectory(prefix="agent_memory_mock_api_cache_") as tmp:
            cache_dir = Path(tmp)
            for run_idx in (1, 2):
                EmbeddingMockHandler.reset_counts()
                result = run_memory_eval(args, base_url, cache_dir)
                summary_exists = (args.output_dir / "summary.csv").exists()
                rankings_exists = (args.output_dir / "rankings.csv").exists()
                rows.append({
                    "run": run_idx,
                    "requests": EmbeddingMockHandler.request_count,
                    "inputs": EmbeddingMockHandler.input_count,
                    "summary_exists": summary_exists,
                    "rankings_exists": rankings_exists,
                    "returncode": result.returncode,
                })
    finally:
        server.shutdown()
        server.server_close()

    summary_rows = read_csv(args.output_dir / "summary.csv")
    if not summary_rows:
        raise RuntimeError("summary.csv is empty after mock API smoke test.")
    if not any(row.get("method") == "type_aware" for row in summary_rows):
        raise RuntimeError("type_aware summary row missing after mock API smoke test.")
    if rows[0]["requests"] <= 0:
        raise RuntimeError("first run did not call the mock embedding API.")
    if rows[1]["requests"] != 0:
        raise RuntimeError("second run did not hit the embedding cache.")

    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, summary_rows, args.output_dir)
    print(json.dumps({
        "output_report": str(args.output_report),
        "first_run_requests": rows[0]["requests"],
        "second_run_requests": rows[1]["requests"],
        "cache_hit_verified": rows[1]["requests"] == 0,
        "summary_methods": len(summary_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
