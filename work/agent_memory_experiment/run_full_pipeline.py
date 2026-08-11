#!/usr/bin/env python3
"""Run retrieval, compression, and cross-agent memory experiments end to end."""

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


def row_for(rows: list[dict], **matches: str) -> dict:
    for row in rows:
        if all(row.get(key) == value for key, value in matches.items()):
            return row
    raise KeyError(f"Missing row matching {matches}")


def write_final_report(repo_root: Path, sizes: list[int]) -> None:
    trend_rows = read_csv(repo_root / "outputs" / "agent_memory_experiment_trends.csv")
    compression_rows = read_csv(repo_root / "outputs" / "agent_memory_compression_results.csv")
    cross_rows = read_csv(repo_root / "outputs" / "agent_memory_cross_agent_results.csv")

    largest = max(sizes)
    sample_best = row_for(trend_rows, run="sample_10", method="time_aware")
    largest_vector = row_for(trend_rows, run=f"synthetic_{largest}", method="vector")
    largest_time = row_for(trend_rows, run=f"synthetic_{largest}", method="time_aware")
    raw_comp = row_for(compression_rows, run=f"compression_{largest}", variant="raw", method="time_aware")
    fact_comp = row_for(compression_rows, run=f"compression_{largest}", variant="fact", method="time_aware")
    summary_comp = row_for(compression_rows, run=f"compression_{largest}", variant="summary", method="time_aware")
    cross_private = row_for(cross_rows, run=f"cross_agent_{largest}", strategy="private_only", method="time_aware")
    cross_shared = row_for(cross_rows, run=f"cross_agent_{largest}", strategy="shared_allowed", method="time_aware")
    cross_unfiltered = row_for(cross_rows, run=f"cross_agent_{largest}", strategy="unfiltered_private_first", method="time_aware")

    lines = [
        "# Agent Memory Full Pipeline Report",
        "",
        "This is the consolidated first-stage evidence for the memory module.",
        "",
        "## What Was Verified",
        "",
        "- Retrieval baselines from 10 hand-checkable records to several hundred synthetic memories.",
        "- Recency-aware reranking for memory token freshness / temporal validity.",
        "- Fact-level and grouped-summary compression tradeoffs.",
        "- Cross-agent shared memory reuse and the risk of skipping permission filtering before ranking.",
        "",
        "## Key Numbers",
        "",
        "| Check | Result |",
        "|---|---:|",
        f"| 10-row sanity check, time-aware Recall@1 | {fmt(sample_best['recall@1'])} |",
        f"| {largest}-memory vector Recall@1 | {fmt(largest_vector['recall@1'])} |",
        f"| {largest}-memory time-aware Recall@1 | {fmt(largest_time['recall@1'])} |",
        f"| {largest}-memory raw time-aware Recall@1 | {fmt(raw_comp['recall@1'])} |",
        f"| {largest}-memory fact-compressed time-aware Recall@1 | {fmt(fact_comp['recall@1'])} |",
        f"| {largest}-memory summary-compressed time-aware Recall@1 | {fmt(summary_comp['recall@1'])} |",
        f"| {largest}-memory cross-agent private-only Recall@1 | {fmt(cross_private['recall@1'])} |",
        f"| {largest}-memory cross-agent shared Recall@1 | {fmt(cross_shared['recall@1'])} |",
        f"| {largest}-memory unfiltered private-first Recall@1 | {fmt(cross_unfiltered['recall@1'])} |",
        "",
        "## Interpretation",
        "",
        "- The first-stage pipeline is easy to reproduce and inspect, because it starts from 10 records and scales to 100/300/500 records with identical metrics.",
        "- Recency-aware scoring is the strongest simple baseline when repeated memories contain old and new versions of similar facts.",
        "- Fact-level compression is the safer first compression target: it reduces token cost strongly while preserving more retrieval quality than grouped summaries.",
        "- Cross-agent reuse should be implemented as `permission filter -> retrieval/reranking -> optional KV-cache reuse`; the risk control shows that ranking before filtering can put unauthorized copies in the top result.",
        "",
        "## Output Index",
        "",
        "- Retrieval analysis: `outputs/agent_memory_experiment_analysis.md`",
        "- Trend table: `outputs/agent_memory_experiment_trends.csv`",
        "- Visualization: `outputs/agent_memory_experiment_visualization.html`",
        "- Compression analysis: `outputs/agent_memory_compression_analysis.md`",
        "- Compression table: `outputs/agent_memory_compression_results.csv`",
        "- Cross-agent analysis: `outputs/agent_memory_cross_agent_analysis.md`",
        "- Cross-agent table: `outputs/agent_memory_cross_agent_results.csv`",
    ]
    output = repo_root / "outputs" / "agent_memory_full_pipeline_report.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all first-stage agent-memory experiments and reports.")
    parser.add_argument("--sizes", type=int, nargs="*", default=[100, 300, 500])
    parser.add_argument("--seeds", type=int, nargs="*", default=[7, 11, 17])
    parser.add_argument("--semantic-backend", choices=["hash", "sentence-transformer"], default="hash")
    parser.add_argument("--embedding-model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--embedding-batch-size", type=int, default=32)
    parser.add_argument("--embedding-cache-dir", type=Path, default=Path("work/agent_memory_experiment/cache/embeddings"))
    parser.add_argument("--no-embedding-cache", action="store_true")
    parser.add_argument("--persona-boost-weight", type=float, default=0.0)
    parser.add_argument("--persona-boost-query-types", default="")
    parser.add_argument("--importance-weight", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    experiment_dir = repo_root / "work" / "agent_memory_experiment"
    python = sys.executable

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

    run_cmd([
        python,
        str(experiment_dir / "run_experiments.py"),
        "--sizes",
        *[str(size) for size in args.sizes],
        "--seeds",
        *[str(seed) for seed in args.seeds],
        *backend_args,
    ], cwd=repo_root)

    compression_dirs = []
    cross_agent_dirs = []
    for size in args.sizes:
        memories = experiment_dir / "data" / f"synthetic_{size}_memories.jsonl"
        queries = experiment_dir / "data" / f"synthetic_{size}_queries.jsonl"
        compression_dir = experiment_dir / "results" / f"compression_{size}"
        cross_agent_dir = experiment_dir / "results" / f"cross_agent_{size}"
        compression_dirs.append(compression_dir)
        cross_agent_dirs.append(cross_agent_dir)

        run_cmd([
            python,
            str(experiment_dir / "compression_experiment.py"),
            "--memories",
            str(memories),
            "--queries",
            str(queries),
            "--output-dir",
            str(compression_dir),
            *backend_args,
        ], cwd=repo_root)

        run_cmd([
            python,
            str(experiment_dir / "cross_agent_experiment.py"),
            "--memories",
            str(memories),
            "--output-dir",
            str(cross_agent_dir),
            *backend_args,
        ], cwd=repo_root)

    run_cmd([
        python,
        str(experiment_dir / "compare_compression_results.py"),
        *[str(path) for path in compression_dirs],
        "--output",
        str(repo_root / "outputs" / "agent_memory_compression_analysis.md"),
        "--csv-output",
        str(repo_root / "outputs" / "agent_memory_compression_results.csv"),
    ], cwd=repo_root)

    run_cmd([
        python,
        str(experiment_dir / "compare_cross_agent_results.py"),
        *[str(path) for path in cross_agent_dirs],
        "--output",
        str(repo_root / "outputs" / "agent_memory_cross_agent_analysis.md"),
        "--csv-output",
        str(repo_root / "outputs" / "agent_memory_cross_agent_results.csv"),
    ], cwd=repo_root)

    write_final_report(repo_root, args.sizes)


if __name__ == "__main__":
    main()
