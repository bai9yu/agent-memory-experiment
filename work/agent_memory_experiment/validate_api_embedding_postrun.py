#!/usr/bin/env python3
"""Validate that an external API embedding run is complete enough for paper use."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_RESULT_FILES = ("summary.csv", "summary_by_type.csv", "per_query_metrics.csv", "rankings.csv")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def method_row(summary: Path, method: str) -> dict[str, str] | None:
    for row in read_csv(summary):
        if row.get("method") == method:
            return row
    return None


def comparison_completed(outputs: Path, label: str) -> bool:
    candidates = [outputs / "agent_memory_embedding_baseline_comparison.csv"]
    candidates.extend(sorted(outputs.glob("agent_memory_api_embedding_*_comparison.csv")))
    for path in candidates:
        rows = read_csv(path)
        if not rows:
            continue
        label_matches = any(row.get("api_label", label) == label for row in rows)
        all_completed = rows and all(row.get("status") == "completed" for row in rows)
        if label_matches and all_completed:
            return True
    return False


def numeric_metric_ready(row: dict[str, str] | None) -> bool:
    if row is None:
        return False
    for metric in ("recall@1", "recall@3", "recall@5", "mrr"):
        try:
            float(row.get(metric, ""))
        except ValueError:
            return False
    return True


def build_rows(profile_csv: Path, outputs: Path) -> list[dict[str, Any]]:
    profiles = read_csv(profile_csv)
    rows: list[dict[str, Any]] = []
    for profile in profiles:
        label = profile.get("label", "")
        method = profile.get("method", "type_aware")
        result_dir = Path(profile.get("result_dir", ""))
        summary = result_dir / "summary.csv"
        summary_row = method_row(summary, method)
        existing_files = [name for name in REQUIRED_RESULT_FILES if (result_dir / name).exists()]
        missing_files = [name for name in REQUIRED_RESULT_FILES if name not in existing_files]
        comparison_ok = comparison_completed(outputs, label)
        summary_metrics_ok = numeric_metric_ready(summary_row)
        result_files_ok = not missing_files
        postrun_pass = summary_metrics_ok and result_files_ok and comparison_ok
        if postrun_pass:
            status = "completed_for_paper"
        elif summary.exists():
            status = "partial_result"
        else:
            status = "pending_api_run"
        rows.append({
            "label": label,
            "model": profile.get("model", ""),
            "base_url": profile.get("base_url", ""),
            "dimensions": profile.get("dimensions", "0"),
            "method": method,
            "status": status,
            "postrun_pass": postrun_pass,
            "summary_exists": summary.exists(),
            "summary_method_exists": summary_row is not None,
            "summary_metrics_ok": summary_metrics_ok,
            "result_files_ok": result_files_ok,
            "comparison_completed": comparison_ok,
            "existing_result_files": ";".join(existing_files),
            "missing_result_files": ";".join(missing_files),
            "summary_path": str(summary),
        })
    if not rows:
        rows.append({
            "label": "no_provider_profiles",
            "model": "",
            "base_url": "",
            "dimensions": "0",
            "method": "",
            "status": "profile_missing",
            "postrun_pass": False,
            "summary_exists": False,
            "summary_method_exists": False,
            "summary_metrics_ok": False,
            "result_files_ok": False,
            "comparison_completed": False,
            "existing_result_files": "",
            "missing_result_files": "",
            "summary_path": "",
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


def write_report(path: Path, rows: list[dict[str, Any]], profile_csv: Path) -> None:
    completed = [row for row in rows if row["postrun_pass"]]
    partial = [row for row in rows if row["status"] == "partial_result"]
    table_rows = [
        [
            row["label"],
            row["model"],
            str(row["dimensions"]),
            row["status"],
            str(row["summary_metrics_ok"]),
            str(row["result_files_ok"]),
            str(row["comparison_completed"]),
            row["missing_result_files"] or "none",
        ]
        for row in rows
    ]
    lines = [
        "# API Embedding Post-Run Gate",
        "",
        "本文件检查外部 API embedding baseline 跑完之后，结果是否足够进入论文对照表。它不联网、不调用 provider，也不读取 API key；只检查本地结果文件和 comparison 表。",
        "",
        "## 总览",
        "",
        f"- Provider profile source: `{profile_csv}`",
        f"- Provider profiles checked: {len(rows)}",
        f"- Completed for paper: {len(completed)}",
        f"- Partial results: {len(partial)}",
        f"- Ready to cite external embedding baseline: {bool(completed)}",
        "",
        "## 明细",
        "",
        markdown_table(["Label", "Model", "Dimensions", "Status", "Summary Metrics OK", "Result Files OK", "Comparison Completed", "Missing Files"], table_rows),
        "",
        "## 判定规则",
        "",
        "- `summary.csv` 中必须存在目标 method，并且 `recall@1/3/5`、`mrr` 可以解析为数值。",
        "- `summary.csv`、`summary_by_type.csv`、`per_query_metrics.csv`、`rankings.csv` 必须同时存在。",
        "- 必须已经生成相对 BGE-M3 的 completed comparison 表。",
        "",
        "## 论文使用边界",
        "",
    ]
    if completed:
        lines.append("- 可以把 completed provider 写入外部 embedding baseline 对照实验。")
    else:
        lines.append("- 当前还不能把外部 embedding baseline 写成已完成结果；只能写接入链路和跑后验收门禁已经准备好。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate API embedding result completeness after a real run.")
    parser.add_argument("--profile-csv", type=Path, default=Path("outputs/agent_memory_embedding_provider_profiles.csv"))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.profile_csv, args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.profile_csv)
    print(json.dumps({
        "output_report": str(args.output_report),
        "profiles": len(rows),
        "completed_for_paper": sum(1 for row in rows if row["postrun_pass"]),
        "partial_results": sum(1 for row in rows if row["status"] == "partial_result"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
