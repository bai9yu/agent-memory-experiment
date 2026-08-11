#!/usr/bin/env python3
"""Run the full offline agent-memory experiment pipeline."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def run_cmd(args: list[str], cwd: Path) -> None:
    print("+ " + " ".join(args))
    subprocess.run(args, cwd=str(cwd), check=True)


def read_summary(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_trend_csv(result_dirs: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for result_dir in result_dirs:
        for row in read_summary(result_dir / "summary.csv"):
            rows.append({
                "run": result_dir.name,
                "method": row["method"],
                "num_queries": row["num_queries"],
                "recall@1": row["recall@1"],
                "recall@3": row["recall@3"],
                "recall@5": row["recall@5"],
                "mrr": row["mrr"],
            })
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all first-stage memory experiments.")
    parser.add_argument("--sizes", type=int, nargs="*", default=[100, 300, 500])
    parser.add_argument("--seeds", type=int, nargs="*", default=[7, 11, 17])
    parser.add_argument("--analysis-output", type=Path, default=Path("outputs/agent_memory_experiment_analysis.md"))
    parser.add_argument("--trend-output", type=Path, default=Path("outputs/agent_memory_experiment_trends.csv"))
    parser.add_argument("--visualization-output", type=Path, default=Path("outputs/agent_memory_experiment_visualization.html"))
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--long-conversation-input", type=Path, default=None)
    parser.add_argument("--long-conversation-name", default="long_conversation")
    parser.add_argument("--max-long-records", type=int, default=None)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    experiment_dir = repo_root / "work" / "agent_memory_experiment"
    python = sys.executable

    if len(args.seeds) < len(args.sizes):
        raise ValueError("Provide at least as many seeds as sizes.")

    result_dirs = [experiment_dir / "results" / "sample_10"]

    backend_args = [
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
    ]
    if args.no_embedding_cache:
        backend_args.append("--no-embedding-cache")
    if args.local_files_only:
        backend_args.append("--local-files-only")

    run_cmd([python, str(experiment_dir / "memory_eval.py"), *backend_args], cwd=repo_root)

    for size, seed in zip(args.sizes, args.seeds):
        run_cmd(
            [
                python,
                str(experiment_dir / "generate_synthetic_data.py"),
                "--num-memories",
                str(size),
                "--seed",
                str(seed),
            ],
            cwd=repo_root,
        )
        memory_path = experiment_dir / "data" / f"synthetic_{size}_memories.jsonl"
        query_path = experiment_dir / "data" / f"synthetic_{size}_queries.jsonl"
        result_dir = experiment_dir / "results" / f"synthetic_{size}"
        result_dirs.append(result_dir)
        run_cmd(
            [
                python,
                str(experiment_dir / "memory_eval.py"),
                "--memories",
                str(memory_path),
                "--queries",
                str(query_path),
                "--output-dir",
                str(result_dir),
                *backend_args,
            ],
            cwd=repo_root,
        )

    if args.long_conversation_input:
        converted_prefix = experiment_dir / "data" / args.long_conversation_name
        convert_cmd = [
            python,
            str(experiment_dir / "convert_long_conversation.py"),
            "--input",
            str(args.long_conversation_input),
            "--output-prefix",
            str(converted_prefix),
        ]
        if args.max_long_records is not None:
            convert_cmd.extend(["--max-records", str(args.max_long_records)])
        run_cmd(convert_cmd, cwd=repo_root)

        memory_path = converted_prefix.with_name(converted_prefix.name + "_memories.jsonl")
        query_path = converted_prefix.with_name(converted_prefix.name + "_queries.jsonl")
        result_dir = experiment_dir / "results" / args.long_conversation_name
        result_dirs.append(result_dir)
        run_cmd(
            [
                python,
                str(experiment_dir / "memory_eval.py"),
                "--memories",
                str(memory_path),
                "--queries",
                str(query_path),
                "--output-dir",
                str(result_dir),
                *backend_args,
            ],
            cwd=repo_root,
        )

    run_cmd(
        [
            python,
            str(experiment_dir / "compare_results.py"),
            *[str(path) for path in result_dirs],
            "--output",
            str(repo_root / args.analysis_output),
        ],
        cwd=repo_root,
    )
    write_trend_csv(result_dirs, repo_root / args.trend_output)
    print(f"Wrote {repo_root / args.trend_output}")
    run_cmd(
        [
            python,
            str(experiment_dir / "visualize_results.py"),
            "--trend-csv",
            str(repo_root / args.trend_output),
            "--result-dirs",
            *[str(path) for path in result_dirs],
            "--output",
            str(repo_root / args.visualization_output),
        ],
        cwd=repo_root,
    )


if __name__ == "__main__":
    main()
