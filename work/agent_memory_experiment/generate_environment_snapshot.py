#!/usr/bin/env python3
"""Generate an environment snapshot for reproducible paper experiments."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


KEY_PACKAGES = (
    "numpy",
    "scikit-learn",
    "scipy",
    "sentence-transformers",
    "transformers",
    "torch",
    "faiss-cpu",
    "huggingface-hub",
    "tokenizers",
)


def run_text(args: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def package_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not_installed"


def cache_status(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "num_files": sum(1 for item in path.rglob("*") if item.is_file()) if path.exists() else 0,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, system_rows: list[dict[str, str]], package_rows: list[dict[str, str]], cache_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# 实验环境快照",
        "",
        "本文件记录复现实验所需的运行环境。它不包含任何 API key，也不读取 `.env`。",
        "",
        "## System",
        "",
        "| Key | Value |",
        "|---|---|",
    ]
    for row in system_rows:
        lines.append(f"| {row['key']} | `{row['value']}` |")
    lines.extend([
        "",
        "## Python Packages",
        "",
        "| Package | Version |",
        "|---|---:|",
    ])
    for row in package_rows:
        lines.append(f"| {row['package']} | `{row['version']}` |")
    lines.extend([
        "",
        "## Local Caches",
        "",
        "| Cache | Exists | Files | Path |",
        "|---|---:|---:|---|",
    ])
    for row in cache_rows:
        lines.append(f"| {row['cache']} | {row['exists']} | {row['num_files']} | `{row['path']}` |")
    lines.extend([
        "",
        "## Notes",
        "",
        "- 主 LoCoMo 实验使用本地 `BAAI/bge-m3` sentence-transformer 缓存。",
        "- 默认检索和重排实验不需要在线 embedding API。",
        "- DeepSeek API 仅用于 memory write / fact extraction；复现已缓存检索结果不需要再次调用 API。",
        "- `.venv`、模型缓存和 embedding 缓存不进入 Git，需要在本地按 README 准备。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate environment snapshot.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-packages", type=Path, required=True)
    parser.add_argument("--output-system", type=Path, required=True)
    args = parser.parse_args()

    root = args.project_root
    cache_root = root / "work" / "agent_memory_experiment" / "cache"
    system_rows = [
        {"key": "git_commit", "value": run_text(["git", "rev-parse", "--short", "HEAD"], root)},
        {"key": "git_branch_status", "value": run_text(["git", "status", "--short", "--branch"], root).splitlines()[0]},
        {"key": "python_version", "value": sys.version.split()[0]},
        {"key": "platform", "value": platform.platform()},
        {"key": "machine", "value": platform.machine()},
        {"key": "processor", "value": platform.processor() or "unknown"},
    ]
    package_rows = [
        {"package": package, "version": package_version(package)}
        for package in KEY_PACKAGES
    ]
    cache_rows = [
        {"cache": "sentence_transformers_bge_m3", **cache_status(cache_root / "sentence_transformers" / "models--BAAI--bge-m3")},
        {"cache": "embedding_cache_bge_m3", **cache_status(cache_root / "embeddings" / "sentence_transformer" / "BAAI_bge-m3")},
        {"cache": "huggingface_cache", **cache_status(cache_root / "huggingface")},
    ]
    write_csv(args.output_system, system_rows)
    write_csv(args.output_packages, package_rows)
    write_report(args.output_report, system_rows, package_rows, cache_rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "packages": len(package_rows),
        "caches": cache_rows,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
