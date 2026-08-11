#!/usr/bin/env python3
"""Convert and evaluate the real LoCoMo dataset with the local memory pipeline."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def run_cmd(args: list[str], cwd: Path) -> None:
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=str(cwd), check=True)


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(value: str | float) -> str:
    return f"{float(value):.3f}"


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def write_report(result_dir: Path, output: Path, memories_path: Path, queries_path: Path, repo_root: Path) -> None:
    summary = read_csv(result_dir / "summary.csv")
    by_type = read_csv(result_dir / "summary_by_type.csv")

    lines = [
        "# LoCoMo 真实数据接入实验报告",
        "",
        "## 数据与转换",
        "",
        f"- Memory 文件：`{display_path(memories_path, repo_root)}`",
        f"- Query 文件：`{display_path(queries_path, repo_root)}`",
        f"- 评测结果目录：`{display_path(result_dir, repo_root)}`",
        "",
        "LoCoMo 原始数据包含多 session 长对话、时间戳、QA 标注和 evidence。当前转换器把对话 turn 转为 memory，把 QA question 转为 query，并把 `D1:3` 这类 evidence id 映射到本地 `mxxxxx` memory id。",
        "",
        "## 总体指标",
        "",
        "| Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['method']} | {fmt(row['recall@1'])} | {fmt(row['recall@3'])} | "
            f"{fmt(row['recall@5'])} | {fmt(row['mrr'])} | {row['num_queries']} |"
        )

    lines.extend([
        "",
        "## 按问题类别",
        "",
        "| Category | Method | Recall@1 | Recall@3 | Recall@5 | MRR | Queries |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in by_type:
        lines.append(
            f"| {row['query_type']} | {row['method']} | {fmt(row['recall@1'])} | "
            f"{fmt(row['recall@3'])} | {fmt(row['recall@5'])} | {fmt(row['mrr'])} | {row['num_queries']} |"
        )

    lines.extend([
        "",
        "## 初步解释",
        "",
        "- 真实 LoCoMo 比合成数据更难：问题存在转述、跨 session、多证据、时间推理和隐含推理。",
        "- 当前 hash embedding 只是离线基线，语义能力弱，因此真实数据上 `vector` 表现较低。",
        "- `hybrid` 在全量 LoCoMo 上优于纯向量和当前 time-aware，说明真实数据里关键词和实体匹配很重要。",
        "- 当前 time-aware 的半衰期和权重来自合成数据验证，真实 LoCoMo 需要重新调参；并不是所有问题都应偏向最近记忆。",
        "",
        "## 下一步",
        "",
        "1. 接入真实 embedding：当前路线使用本地 `sentence-transformers` + BGE，先用 `BAAI/bge-small-en-v1.5` 验证，再切到 `BAAI/bge-m3`。",
        "2. 按 LoCoMo category 分别调权重：事实类、时间类、多跳推理类不应共用同一套时间衰减。",
        "3. 加入 session/persona/entity 过滤，减少跨人物和跨样本干扰。",
        "4. 用 `observation` 和 `session_summary` 做真实压缩对照。",
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LoCoMo real-data conversion and retrieval evaluation.")
    parser.add_argument("--input", type=Path, default=Path("work/agent_memory_experiment/data/locomo10.json"))
    parser.add_argument("--name", default="locomo_real_all")
    parser.add_argument("--max-records", type=int)
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--rank-output-k", type=int, default=100)
    parser.add_argument("--report-output", type=Path, default=Path("outputs/agent_memory_locomo_real_report_zh.md"))
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    experiment_dir = repo_root / "work" / "agent_memory_experiment"
    python = sys.executable
    output_prefix = experiment_dir / "data" / args.name
    result_dir = experiment_dir / "results" / args.name

    convert_cmd = [
        python,
        str(experiment_dir / "convert_long_conversation.py"),
        "--input",
        str(repo_root / args.input if not args.input.is_absolute() else args.input),
        "--output-prefix",
        str(output_prefix),
    ]
    if args.max_records is not None:
        convert_cmd.extend(["--max-records", str(args.max_records)])
    run_cmd(convert_cmd, cwd=repo_root)

    memories_path = output_prefix.with_name(output_prefix.name + "_memories.jsonl")
    queries_path = output_prefix.with_name(output_prefix.name + "_queries.jsonl")
    eval_cmd = [
        python,
        str(experiment_dir / "memory_eval.py"),
        "--memories",
        str(memories_path),
        "--queries",
        str(queries_path),
        "--output-dir",
        str(result_dir),
        "--semantic-backend",
        args.semantic_backend,
        "--embedding-model",
        args.embedding_model,
        "--embedding-batch-size",
        str(args.embedding_batch_size),
        "--embedding-cache-dir",
        str(args.embedding_cache_dir),
        "--persona-boost-weight",
        str(args.persona_boost_weight),
        "--persona-boost-query-types",
        args.persona_boost_query_types,
        "--importance-weight",
        str(args.importance_weight),
        "--rank-output-k",
        str(args.rank_output_k),
    ]
    if args.no_embedding_cache:
        eval_cmd.append("--no-embedding-cache")
    if args.local_files_only:
        eval_cmd.append("--local-files-only")
    run_cmd(eval_cmd, cwd=repo_root)
    write_report(result_dir, repo_root / args.report_output, memories_path, queries_path, repo_root)


if __name__ == "__main__":
    main()
