#!/usr/bin/env python3
"""Compare BGE-M3 against offline hash/keyword retrieval baselines."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


METRICS = ["mrr", "recall@1", "recall@3", "recall@5"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def row_by_method(rows: list[dict[str, str]], method: str) -> dict[str, str]:
    for row in rows:
        if row.get("method") == method:
            return row
    raise RuntimeError(f"Missing method `{method}`")


def f(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def signed(value: float) -> str:
    return f"{value:+.3f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def build_rows(bge_summary: Path, hash_summary: Path) -> list[dict[str, Any]]:
    bge_rows = read_csv(bge_summary)
    hash_rows = read_csv(hash_summary)
    rows: list[dict[str, Any]] = []
    comparisons = [
        ("BGE-M3 vector", "bge_m3", row_by_method(bge_rows, "vector"), "semantic_vector"),
        ("BGE-M3 hybrid", "bge_m3", row_by_method(bge_rows, "hybrid"), "semantic_plus_keyword"),
        ("BGE-M3 type-aware", "bge_m3", row_by_method(bge_rows, "type_aware"), "main_retrieval_baseline"),
        ("Hash vector", "hash", row_by_method(hash_rows, "vector"), "offline_semantic_floor"),
        ("Hash hybrid", "hash", row_by_method(hash_rows, "hybrid"), "offline_hybrid_floor"),
        ("Hash type-aware", "hash", row_by_method(hash_rows, "type_aware"), "offline_type_aware_floor"),
        ("BM25 keyword", "lexical", row_by_method(bge_rows, "keyword"), "lexical_baseline"),
    ]
    bge_type = row_by_method(bge_rows, "type_aware")
    hash_type = row_by_method(hash_rows, "type_aware")
    keyword = row_by_method(bge_rows, "keyword")
    bge_hybrid = row_by_method(bge_rows, "hybrid")
    hash_hybrid = row_by_method(hash_rows, "hybrid")

    for label, encoder, source, role in comparisons:
        row: dict[str, Any] = {
            "label": label,
            "encoder": encoder,
            "role": role,
            "num_queries": int(source["num_queries"]),
        }
        for metric in METRICS:
            row[metric] = float(source[metric])
            row[f"delta_vs_bge_type_aware_{metric}"] = float(source[metric]) - float(bge_type[metric])
        rows.append(row)

    diagnostics = [
        ("bge_type_minus_hash_type", bge_type, hash_type),
        ("bge_type_minus_keyword", bge_type, keyword),
        ("bge_hybrid_minus_hash_hybrid", bge_hybrid, hash_hybrid),
    ]
    for label, left, right in diagnostics:
        row = {
            "label": label,
            "encoder": "delta",
            "role": "diagnostic_delta",
            "num_queries": int(left["num_queries"]),
        }
        for metric in METRICS:
            row[metric] = float(left[metric]) - float(right[metric])
            row[f"delta_vs_bge_type_aware_{metric}"] = ""
        rows.append(row)
    return rows


def write_report(path: Path, rows: list[dict[str, Any]], bge_summary: Path, hash_summary: Path) -> None:
    display_rows = []
    for row in rows:
        if row["encoder"] == "delta":
            continue
        display_rows.append([
            row["label"],
            row["role"],
            str(row["num_queries"]),
            f(row["mrr"]),
            f(row["recall@1"]),
            f(row["recall@3"]),
            f(row["recall@5"]),
            signed(row["delta_vs_bge_type_aware_mrr"]),
            signed(row["delta_vs_bge_type_aware_recall@5"]),
        ])

    delta_rows = [
        [
            row["label"],
            signed(row["mrr"]),
            signed(row["recall@1"]),
            signed(row["recall@3"]),
            signed(row["recall@5"]),
        ]
        for row in rows
        if row["encoder"] == "delta"
    ]

    bge_type = next(row for row in rows if row["label"] == "BGE-M3 type-aware")
    hash_type = next(row for row in rows if row["label"] == "Hash type-aware")
    keyword = next(row for row in rows if row["label"] == "BM25 keyword")

    lines = [
        "# Offline Embedding Sensitivity",
        "",
        "本报告比较主实验使用的 BGE-M3 检索与完全离线的 hash vector / BM25 keyword 下界。它不调用外部 API，因此不能替代最终的 OpenAI/Cohere/Jina 等外部 embedding baseline；它的作用是证明当前结论不是只来自单一排序公式，并给出 lexical 与弱语义编码器的可复现下界。",
        "",
        "## 数据与输入",
        "",
        f"- BGE-M3 summary: `{bge_summary}`",
        f"- Hash summary: `{hash_summary}`",
        f"- Query 数：{int(bge_type['num_queries'])}",
        "",
        "## 主表",
        "",
        markdown_table(
            ["Baseline", "Role", "N", "MRR", "R@1", "R@3", "R@5", "ΔMRR vs BGE type-aware", "ΔR@5 vs BGE type-aware"],
            display_rows,
        ),
        "",
        "## 关键差值",
        "",
        markdown_table(["Delta", "MRR", "R@1", "R@3", "R@5"], delta_rows),
        "",
        "## 论文解释",
        "",
        f"- BGE-M3 type-aware 的 MRR/R@5 为 {f(bge_type['mrr'])}/{f(bge_type['recall@5'])}，hash type-aware 为 {f(hash_type['mrr'])}/{f(hash_type['recall@5'])}，说明真实语义 encoder 带来 {signed(bge_type['mrr'] - hash_type['mrr'])} MRR 和 {signed(bge_type['recall@5'] - hash_type['recall@5'])} R@5 的增量。",
        f"- BM25 keyword 的 MRR/R@5 为 {f(keyword['mrr'])}/{f(keyword['recall@5'])}，高于 hash vector，但低于 BGE-M3 type-aware；这说明 lexical matching 是强下界，语义编码与 type-aware reranking 仍有额外收益。",
        "- 当前仍不能写成外部 embedding 泛化已经完成；最终投稿前仍需至少一个真实 API embedding baseline。",
        "",
        "## 写法边界",
        "",
        "- 可以写：我们报告了 BGE-M3、BM25 keyword 和 hash-vector 离线下界，验证主方法相对弱语义/词面检索的收益。",
        "- 应谨慎：hash vector 不是主流 embedding model，只能作为工程下界和 pipeline sanity check。",
        "- 不能写：该结果替代了 OpenAI/Cohere/Jina 等外部 embedding baseline。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate offline embedding sensitivity report.")
    parser.add_argument("--bge-summary", type=Path, required=True)
    parser.add_argument("--hash-summary", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_offline_embedding_sensitivity.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_offline_embedding_sensitivity_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.bge_summary, args.hash_summary)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, args.bge_summary, args.hash_summary)
    print({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "rows": len(rows),
    })


if __name__ == "__main__":
    main()
