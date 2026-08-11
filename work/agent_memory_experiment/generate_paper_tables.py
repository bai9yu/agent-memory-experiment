#!/usr/bin/env python3
"""Generate paper-ready Markdown and LaTeX tables from cached experiment outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt(value: Any, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def pct_delta(value: Any, digits: int = 4) -> str:
    number = float(value)
    return f"{number:+.{digits}f}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def latex_table(headers: list[str], rows: list[list[str]], caption: str, label: str) -> str:
    colspec = "l" + "r" * (len(headers) - 1)
    safe_headers = [latex_escape(item) for item in headers]
    safe_rows = [[latex_escape(item) for item in row] for row in rows]
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{colspec}}}",
        r"\toprule",
        " & ".join(safe_headers) + r" \\",
        r"\midrule",
    ]
    for row in safe_rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
    ])
    return "\n".join(lines)


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
        "$": r"\$",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in text)


def main_results_rows(path: Path) -> list[list[str]]:
    rows = read_csv(path)
    selected = [
        row for row in rows
        if row["variant"] == "llm_extracted_fact" and row["method"] in {"keyword", "vector", "hybrid", "time_aware", "type_aware"}
    ]
    order = {"keyword": 0, "vector": 1, "hybrid": 2, "time_aware": 3, "type_aware": 4}
    selected.sort(key=lambda row: order[row["method"]])
    return [
        [row["method"], row["num_queries"], fmt(row["recall@1"]), fmt(row["recall@3"]), fmt(row["recall@5"]), fmt(row["mrr"])]
        for row in selected
    ]


def memory_form_rows(path: Path) -> list[list[str]]:
    rows = read_csv(path)
    selected = [
        row for row in rows
        if row["method"] == "type_aware" and row["variant"] in {"llm_extracted_fact", "locomo_observation"}
    ]
    order = {"llm_extracted_fact": 0, "locomo_observation": 1}
    selected.sort(key=lambda row: order[row["variant"]])
    return [
        [row["variant"], row["num_queries"], fmt(row["recall@1"]), fmt(row["recall@3"]), fmt(row["recall@5"]), fmt(row["mrr"])]
        for row in selected
    ]


def candidate_reranker_rows(summary_path: Path, significance_path: Path) -> tuple[list[list[str]], list[list[str]]]:
    rows = read_csv(summary_path)
    order = {"type_aware": 0, "candidate_reranker": 1, "candidate_oracle": 2}
    selected = sorted(rows, key=lambda row: order.get(row["method"], 99))
    metric_rows = [
        [row["method"], row["splits"], fmt(row["recall@1_mean"]), fmt(row["recall@3_mean"]), fmt(row["recall@5_mean"]), fmt(row["mrr_mean"])]
        for row in selected
    ]
    sig_rows = [
        [row["metric"], pct_delta(row["mean_delta"]), f"[{fmt(row['bootstrap_ci_low'], 4)}, {fmt(row['bootstrap_ci_high'], 4)}]", fmt(row["permutation_p_value"], 4)]
        for row in read_csv(significance_path)
        if row["metric"] in {"mrr", "recall@5"}
    ]
    return metric_rows, sig_rows


def candidate_loco_rows(summary_path: Path, significance_path: Path) -> tuple[list[list[str]], list[list[str]]]:
    rows = read_csv(summary_path)
    order = {"type_aware": 0, "candidate_reranker_loco": 1, "candidate_oracle": 2}
    selected = sorted(rows, key=lambda row: order.get(row["method"], 99))
    metric_rows = [
        [row["method"], row["splits"], fmt(row["recall@1_mean"]), fmt(row["recall@3_mean"]), fmt(row["recall@5_mean"]), fmt(row["mrr_mean"])]
        for row in selected
    ]
    sig_rows = [
        [row["metric"], pct_delta(row["mean_delta"]), f"[{fmt(row['bootstrap_ci_low'], 4)}, {fmt(row['bootstrap_ci_high'], 4)}]", fmt(row["permutation_p_value"], 4)]
        for row in read_csv(significance_path)
        if row["metric"] in {"mrr", "recall@5"}
    ]
    return metric_rows, sig_rows


def type3_rows(
    specific_path: Path,
    set_selector_path: Path,
    decomp_path: Path,
    coverage_sig_path: Path,
) -> tuple[list[list[str]], list[list[str]]]:
    specific = {row["method"]: row for row in read_csv(specific_path)}
    selector = {row["method"]: row for row in read_csv(set_selector_path)}
    decomp = {row["method"]: row for row in read_csv(decomp_path)}
    rows = []
    for method, source in (
        ("type_aware", specific),
        ("type3_specific_reranker", specific),
        ("supervised_set_selector", selector),
        ("query_decomposition", decomp),
        ("type_aware_plus_decomposition", decomp),
        ("candidate_oracle", specific),
    ):
        row = source[method]
        if "mrr_mean" in row:
            rows.append([method, fmt(row["recall@1_mean"]), fmt(row["recall@3_mean"]), fmt(row["recall@5_mean"]), fmt(row["mrr_mean"])])
        else:
            rows.append([method, fmt(row["recall@1"]), fmt(row["recall@3"]), fmt(row["recall@5"]), fmt(row["mrr"])])

    cov_rows = []
    for row in read_csv(coverage_sig_path):
        if row["metric"] != "coverage_ratio@5":
            continue
        cov_rows.append([
            row["experiment"],
            row["candidate"],
            fmt(row["baseline_mean"]),
            fmt(row["candidate_mean"]),
            pct_delta(row["mean_delta"]),
            fmt(row["permutation_p_value"], 4),
        ])
    return rows, cov_rows


def prefilter_rows(path: Path) -> list[list[str]]:
    rows = read_csv(path)
    selected = [row for row in rows if row["method"] == "type_aware" and row["candidate_limit"] in {"50", "100", "200", "500"}]
    selected.sort(key=lambda row: int(row["candidate_limit"]))
    return [
        [row["candidate_limit"], fmt(row["recall@1"]), fmt(row["recall@3"]), fmt(row["recall@5"]), fmt(row["mrr"])]
        for row in selected
    ]


def write_outputs(markdown_path: Path, latex_path: Path, sections: list[tuple[str, list[str], list[list[str]], str, str]]) -> None:
    md_lines = [
        "# 论文表格汇总",
        "",
        "该文件由 `generate_paper_tables.py` 从缓存实验结果生成，用于写论文时复制主结果表、消融表和 Type 3 失败分析表。",
        "",
    ]
    tex_blocks = []
    for title, headers, rows, caption, label in sections:
        md_lines.extend([
            f"## {title}",
            "",
            markdown_table(headers, rows),
            "",
        ])
        tex_blocks.append(latex_table(headers, rows, caption, label))
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    latex_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(md_lines), encoding="utf-8")
    latex_path.write_text("\n\n".join(tex_blocks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate paper-ready tables.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-markdown", type=Path, required=True)
    parser.add_argument("--output-latex", type=Path, required=True)
    args = parser.parse_args()

    out = args.outputs_dir
    main_rows = main_results_rows(out / "agent_memory_baseline_comparison_locomo10.csv")
    memory_rows = memory_form_rows(out / "agent_memory_baseline_comparison_locomo10.csv")
    reranker_rows, reranker_sig_rows = candidate_reranker_rows(
        out / "agent_memory_candidate_reranker_locomo10_summary.csv",
        out / "agent_memory_candidate_reranker_significance_results.csv",
    )
    reranker_loco_rows, reranker_loco_sig_rows = candidate_loco_rows(
        out / "agent_memory_candidate_reranker_loco_summary.csv",
        out / "agent_memory_candidate_reranker_loco_significance_results.csv",
    )
    type3_metric_rows, type3_coverage_rows = type3_rows(
        out / "agent_memory_type3_specific_reranker_summary.csv",
        out / "agent_memory_type3_supervised_set_selector_summary.csv",
        out / "agent_memory_type3_query_decomposition_summary.csv",
        out / "agent_memory_type3_coverage_significance_summary.csv",
    )
    prefilter = prefilter_rows(out / "agent_memory_sklearn_nn_prefilter_locomo10_summary.csv")

    sections = [
        (
            "LoCoMo10 主检索结果",
            ["Method", "Queries", "R@1", "R@3", "R@5", "MRR"],
            main_rows,
            "Main retrieval results on LoCoMo10 with LLM-extracted fact memories.",
            "tab:main_retrieval",
        ),
        (
            "记忆形态对比",
            ["Memory", "Queries", "R@1", "R@3", "R@5", "MRR"],
            memory_rows,
            "Comparison between LLM-extracted fact memory and LoCoMo observation memory.",
            "tab:memory_forms",
        ),
        (
            "候选级学习重排",
            ["Method", "Splits", "R@1", "R@3", "R@5", "MRR"],
            reranker_rows,
            "Held-out candidate-level reranking results.",
            "tab:candidate_reranker",
        ),
        (
            "候选级重排显著性",
            ["Metric", "Delta", "95% CI", "p-value"],
            reranker_sig_rows,
            "Paired significance tests for candidate-level reranking.",
            "tab:candidate_reranker_sig",
        ),
        (
            "候选级重排 LOCO 验证",
            ["Method", "Splits", "R@1", "R@3", "R@5", "MRR"],
            reranker_loco_rows,
            "Leave-one-conversation-out candidate-level reranking results.",
            "tab:candidate_reranker_loco",
        ),
        (
            "候选级重排 LOCO 显著性",
            ["Metric", "Delta", "95% CI", "p-value"],
            reranker_loco_sig_rows,
            "Paired significance tests for leave-one-conversation-out candidate reranking.",
            "tab:candidate_reranker_loco_sig",
        ),
        (
            "Type 3 方法边界",
            ["Method", "R@1", "R@3", "R@5", "MRR"],
            type3_metric_rows,
            "Type-3 multi-evidence diagnostic results.",
            "tab:type3_boundary",
        ),
        (
            "Type 3 覆盖显著性",
            ["Experiment", "Candidate", "Base Cov@5", "Cand Cov@5", "Delta", "p-value"],
            type3_coverage_rows,
            "Paired evidence-coverage significance tests for Type-3 diagnostics.",
            "tab:type3_coverage_sig",
        ),
        (
            "向量候选预筛选",
            ["Candidate K", "R@1", "R@3", "R@5", "MRR"],
            prefilter,
            "Type-aware retrieval quality under vector candidate prefiltering.",
            "tab:prefilter",
        ),
    ]
    write_outputs(args.output_markdown, args.output_latex, sections)
    print(f"wrote {args.output_markdown}")
    print(f"wrote {args.output_latex}")


if __name__ == "__main__":
    main()
