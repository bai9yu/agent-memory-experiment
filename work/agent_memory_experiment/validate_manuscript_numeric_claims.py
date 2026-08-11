#!/usr/bin/env python3
"""Validate key numeric manuscript claims against paper artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Claim:
    claim_id: str
    group: str
    source_path: str
    source_pattern: str
    manuscript_pattern: str
    severity: str
    guidance: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def f(value: str | float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def signed(value: str | float, digits: int = 4) -> str:
    number = float(value)
    return f"{number:+.{digits}f}"


def regex_fragment(text: str) -> str:
    return r"\s+".join(re.escape(part) for part in text.split())


def md_row_fragment(cells: list[str]) -> str:
    return regex_fragment("| " + " | ".join(cells) + " |")


def metric_rows(outputs: Path) -> dict[str, dict[str, str]]:
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    extraction = read_csv(outputs / "agent_memory_llm_extraction_locomo10_comparison.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_deltas.csv")
    intrinsic_loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    type_sig = read_csv(outputs / "agent_memory_type_aware_significance_results.csv")
    candidate_sig = read_csv(outputs / "agent_memory_candidate_reranker_significance_results.csv")
    bootstrap = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")
    oracle_gap = read_csv(outputs / "agent_memory_candidate_oracle_gap_analysis.csv")
    paired = read_csv(outputs / "agent_memory_candidate_reranker_paired_effect_size.csv")
    seed = read_csv(outputs / "agent_memory_candidate_reranker_seed_stability.csv")
    fractions = [
        row for row in read_csv(outputs / "agent_memory_candidate_reranker_train_fraction_sensitivity.csv")
        if row.get("method") == "ablation_intrinsic_only"
    ]
    storage = read_csv(outputs / "agent_memory_cost_storage_locomo10.csv")
    writer = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    type3_cov = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")

    fact = lookup(extraction, variant="llm_extracted_fact")
    obs = lookup(extraction, variant="locomo_observation")
    fact_tokens = float(fact["memory_tokens"])
    obs_tokens = float(obs["memory_tokens"])
    fraction_mean_delta = sum(float(row["mrr_delta_mean"]) for row in fractions) / len(fractions)
    return {
        "fact_type": fact,
        "obs_type": obs,
        "baseline_type_aware": lookup(baseline, variant="llm_extracted_fact", method="type_aware"),
        "baseline_time_aware": lookup(baseline, variant="llm_extracted_fact", method="time_aware"),
        "candidate_type_aware": lookup(reranker, method="type_aware"),
        "candidate_reranker": lookup(reranker, method="candidate_reranker"),
        "intrinsic": lookup(ablation, method="ablation_intrinsic_only"),
        "full": lookup(ablation, method="ablation_full"),
        "intrinsic_loco": lookup(intrinsic_loco, method="intrinsic_reranker_loco"),
        "type_sig_mrr": lookup(type_sig, metric="mrr"),
        "type_sig_r5": lookup(type_sig, metric="recall@5"),
        "candidate_sig_mrr": lookup(candidate_sig, metric="mrr"),
        "candidate_sig_r5": lookup(candidate_sig, metric="recall@5"),
        "intrinsic_vs_type_mrr": lookup(bootstrap, scenario="candidate_reranker_intrinsic_ablation_vs_type_aware", metric="mrr"),
        "intrinsic_vs_full_mrr": lookup(bootstrap, scenario="candidate_reranker_intrinsic_ablation_vs_full", metric="mrr"),
        "intrinsic_loco_mrr": lookup(bootstrap, scenario="candidate_reranker_intrinsic_loco", metric="mrr"),
        "intrinsic_loco_r5": lookup(bootstrap, scenario="candidate_reranker_intrinsic_loco", metric="recall@5"),
        "heldout_oracle_mrr": lookup(oracle_gap, scenario="heldout_intrinsic", metric="mrr"),
        "heldout_oracle_r5": lookup(oracle_gap, scenario="heldout_intrinsic", metric="recall@5"),
        "loco_oracle_mrr": lookup(oracle_gap, scenario="loco_intrinsic", metric="mrr"),
        "type3_oracle_cov5": lookup(oracle_gap, scenario="type3_set_coverage", metric="coverage_ratio@5"),
        "paired_mrr": lookup(paired, comparison="intrinsic_only_vs_type_aware", group="all", group_value="all", metric="mrr"),
        "paired_r5": lookup(paired, comparison="intrinsic_only_vs_type_aware", group="all", group_value="all", metric="recall@5"),
        "paired_type3_r5": lookup(paired, comparison="intrinsic_only_vs_type_aware", group="query_type", group_value="3", metric="recall@5"),
        "seed_intrinsic": lookup(seed, method="ablation_intrinsic_only"),
        "fraction_summary": {
            "min_win_rate": str(min(float(row["mrr_win_rate"]) for row in fractions)),
            "min_delta": str(min(float(row["mrr_delta_min"]) for row in fractions)),
            "mean_delta": str(fraction_mean_delta),
        },
        "storage_fact": lookup(storage, variant="llm_extracted_fact"),
        "storage_obs": lookup(storage, variant="locomo_observation"),
        "storage_ratio": {"ratio": str(fact_tokens / obs_tokens)},
        "writer_mrr": lookup(writer, metric="mrr"),
        "writer_r5": lookup(writer, metric="recall@5"),
        "type3_cov": lookup(type3_cov, experiment="supervised_set_selector", metric="coverage_ratio@5"),
    }


def build_claims(outputs: Path) -> list[Claim]:
    rows = metric_rows(outputs)
    fact = rows["fact_type"]
    obs = rows["obs_type"]
    candidate_base = rows["candidate_type_aware"]
    reranker = rows["candidate_reranker"]
    intrinsic = rows["intrinsic"]
    intrinsic_loco = rows["intrinsic_loco"]
    storage_ratio = float(rows["storage_ratio"]["ratio"])
    fraction = rows["fraction_summary"]

    return [
        Claim(
            "fact_type_aware_main",
            "main_result",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["type_aware", "1838", "0.503", "0.670", f(fact["recall@5"]), f(fact["mrr"])]),
            regex_fragment(f"MRR {f(fact['mrr'])}、Recall@5 {f(fact['recall@5'])}"),
            "critical",
            "更新正文主结果或重新生成 paper tables。",
        ),
        Claim(
            "observation_type_aware_main",
            "main_result",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["locomo_observation", "1638", "0.483", "0.639", f(obs["recall@5"]), f(obs["mrr"])]),
            regex_fragment(f"MRR {f(obs['mrr'])}、Recall@5 {f(obs['recall@5'])}"),
            "critical",
            "确认 observation memory 口径后更新正文。",
        ),
        Claim(
            "candidate_reranker_heldout",
            "reranker",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["candidate_reranker", "5", "0.556", "0.732", f(reranker["recall@5_mean"]), f(reranker["mrr_mean"])]),
            regex_fragment(f"MRR 从 {f(candidate_base['mrr_mean'])} 提升到 {f(reranker['mrr_mean'])}"),
            "critical",
            "同步 held-out candidate reranker 主指标。",
        ),
        Claim(
            "intrinsic_reranker_heldout",
            "reranker",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["ablation_intrinsic_only", f(intrinsic["mrr_mean"]), signed(intrinsic["mrr_delta_vs_type_aware"]), signed(intrinsic["mrr_delta_vs_full_reranker"]), f(intrinsic["recall@5_mean"]), signed(intrinsic["recall@5_delta_vs_type_aware"])]),
            regex_fragment(f"intrinsic feature reranker 达到 MRR {f(intrinsic['mrr_mean'])}、Recall@5 {f(intrinsic['recall@5_mean'])}"),
            "critical",
            "同步 intrinsic-only ablation 主指标。",
        ),
        Claim(
            "intrinsic_reranker_loco",
            "reranker",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["intrinsic_reranker_loco", "10", "0.559", "0.742", f(intrinsic_loco["recall@5_mean"]), f(intrinsic_loco["mrr_mean"])]),
            regex_fragment(f"MRR 为 {f(intrinsic_loco['mrr_mean'])}、Recall@5 为 {f(intrinsic_loco['recall@5_mean'])}"),
            "critical",
            "同步 LOCO intrinsic reranker 指标。",
        ),
        Claim(
            "type_aware_significance",
            "significance",
            "outputs/agent_memory_type_aware_significance_zh.md",
            regex_fragment(f"| mrr | time_aware | type_aware | {float(rows['type_sig_mrr']['mean_delta']):.6f}"),
            regex_fragment(f"MRR delta 为 {signed(rows['type_sig_mrr']['mean_delta'])}，p={f(rows['type_sig_mrr']['permutation_p_value'], 4)}；Recall@5 delta 为 {signed(rows['type_sig_r5']['mean_delta'])}，p={f(rows['type_sig_r5']['permutation_p_value'], 4)}"),
            "major",
            "同步 type-aware vs time-aware 显著性表述。",
        ),
        Claim(
            "candidate_significance",
            "significance",
            "outputs/agent_memory_paper_tables_zh.md",
            md_row_fragment(["mrr", signed(rows["candidate_sig_mrr"]["mean_delta"]), "[0.0462, 0.0619]", f(rows["candidate_sig_mrr"]["permutation_p_value"], 4)]),
            regex_fragment(f"MRR delta 为 {signed(rows['candidate_sig_mrr']['mean_delta'])}，p={f(rows['candidate_sig_mrr']['permutation_p_value'], 4)}；Recall@5 delta 为 {signed(rows['candidate_sig_r5']['mean_delta'])}"),
            "critical",
            "同步 full candidate reranker 显著性。",
        ),
        Claim(
            "intrinsic_ci_claims",
            "significance",
            "outputs/agent_memory_bootstrap_metric_ci_zh.md",
            regex_fragment(f"candidate_reranker_intrinsic_ablation_vs_type_aware`：MRR delta={f(rows['intrinsic_vs_type_mrr']['delta_mean'], 4)}，95% CI=[{f(rows['intrinsic_vs_type_mrr']['delta_ci_low'], 4)}, {f(rows['intrinsic_vs_type_mrr']['delta_ci_high'], 4)}]"),
            regex_fragment(f"MRR delta 为 {signed(rows['intrinsic_vs_type_mrr']['delta_mean'])}，95% CI=[{f(rows['intrinsic_vs_type_mrr']['delta_ci_low'], 4)}, {f(rows['intrinsic_vs_type_mrr']['delta_ci_high'], 4)}]；相对 full reranker 的 MRR delta 为 {signed(rows['intrinsic_vs_full_mrr']['delta_mean'])}，95% CI=[{f(rows['intrinsic_vs_full_mrr']['delta_ci_low'], 4)}, {f(rows['intrinsic_vs_full_mrr']['delta_ci_high'], 4)}]"),
            "critical",
            "同步 intrinsic reranker bootstrap CI。",
        ),
        Claim(
            "oracle_gap_claims",
            "oracle_gap",
            "outputs/agent_memory_candidate_oracle_gap_analysis_zh.md",
            regex_fragment(f"Held-out intrinsic MRR oracle-gap closure: {f(rows['heldout_oracle_mrr']['closure_rate'], 3)}"),
            regex_fragment(f"held-out MRR 上关闭 candidate-oracle gap 的 {f(rows['heldout_oracle_mrr']['closure_rate'], 3)}，Recall@5 closure 为 {f(rows['heldout_oracle_r5']['closure_rate'], 3)}；LOCO MRR closure 为 {f(rows['loco_oracle_mrr']['closure_rate'], 3)}"),
            "major",
            "同步 oracle-gap closure 口径。",
        ),
        Claim(
            "paired_outcome_claims",
            "paired_effect",
            "outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md",
            regex_fragment(f"MRR: improved/worse/tie={rows['paired_mrr']['improved_pairs']}/{rows['paired_mrr']['worsened_pairs']}/{rows['paired_mrr']['tied_pairs']}"),
            regex_fragment(f"MRR improved/worsened/tied 为 {rows['paired_mrr']['improved_pairs']}/{rows['paired_mrr']['worsened_pairs']}/{rows['paired_mrr']['tied_pairs']}，Cohen dz={f(rows['paired_mrr']['cohen_dz'], 4)}；Recall@5 improved/worsened/tied 为 {rows['paired_r5']['improved_pairs']}/{rows['paired_r5']['worsened_pairs']}/{rows['paired_r5']['tied_pairs']}"),
            "major",
            "同步 paired improved/worsened/tied 数值。",
        ),
        Claim(
            "seed_stability_claims",
            "stability",
            "outputs/agent_memory_candidate_reranker_seed_stability_zh.md",
            regex_fragment(f"intrinsic_only` 在 {rows['seed_intrinsic']['mrr_positive_seeds']}/{rows['seed_intrinsic']['seeds']} 个 seed 上 MRR 高于 `type_aware`，平均 ΔMRR={float(rows['seed_intrinsic']['mrr_delta_mean']):.4f}"),
            regex_fragment(f"{rows['seed_intrinsic']['mrr_positive_seeds']}/{rows['seed_intrinsic']['seeds']} 个随机划分上 MRR 均高于 type-aware，平均 ΔMRR={signed(rows['seed_intrinsic']['mrr_delta_mean'])}，最小 ΔMRR={signed(rows['seed_intrinsic']['mrr_delta_min'])}"),
            "major",
            "同步 20-seed stability 结论。",
        ),
        Claim(
            "train_fraction_claims",
            "stability",
            "outputs/agent_memory_candidate_reranker_train_fraction_sensitivity_zh.md",
            regex_fragment(f"MRR win rate 最低为 {float(fraction['min_win_rate']):.2f}，最小 seed-level ΔMRR 为 {float(fraction['min_delta']):.4f}，平均 fraction-level ΔMRR 为 {float(fraction['mean_delta']):.4f}"),
            regex_fragment(f"最低 MRR win rate={f(fraction['min_win_rate'], 2)}，最小 seed-level ΔMRR={signed(fraction['min_delta'])}，平均 fraction-level ΔMRR={signed(fraction['mean_delta'])}"),
            "major",
            "同步 train-fraction sensitivity 结论。",
        ),
        Claim(
            "loco_delta_ci_claims",
            "significance",
            "outputs/agent_memory_bootstrap_metric_ci_zh.md",
            regex_fragment(f"candidate_reranker_intrinsic_loco`：MRR delta={f(rows['intrinsic_loco_mrr']['delta_mean'], 4)}，95% CI=[{f(rows['intrinsic_loco_mrr']['delta_ci_low'], 4)}, {f(rows['intrinsic_loco_mrr']['delta_ci_high'], 4)}]"),
            regex_fragment(f"MRR delta 为 {signed(rows['intrinsic_loco_mrr']['delta_mean'])}，95% CI=[{f(rows['intrinsic_loco_mrr']['delta_ci_low'], 4)}, {f(rows['intrinsic_loco_mrr']['delta_ci_high'], 4)}]，Recall@5 delta 为 {signed(rows['intrinsic_loco_r5']['delta_mean'])}，95% CI=[{f(rows['intrinsic_loco_r5']['delta_ci_low'], 4)}, {f(rows['intrinsic_loco_r5']['delta_ci_high'], 4)}]"),
            "major",
            "同步 LOCO bootstrap CI。",
        ),
        Claim(
            "storage_writer_claims",
            "storage",
            "outputs/agent_memory_llm_extraction_locomo10_comparison_zh.md",
            md_row_fragment(["llm_extracted_fact", rows["storage_fact"]["num_memories"], rows["storage_fact"]["memory_tokens"], "1838", "0.503", "0.670", "0.733", "0.609"]),
            regex_fragment(f"fact memory 使用 {rows['storage_fact']['memory_tokens']} 个 memory tokens，而 observation memory 使用 {rows['storage_obs']['memory_tokens']} 个 tokens，fact/observation token ratio 为 {f(storage_ratio)}。DeepSeek writer 三次运行的 MRR mean={f(rows['writer_mrr']['mean'])}, stdev={f(rows['writer_mrr']['stdev'])}；Recall@5 mean={f(rows['writer_r5']['mean'])}, stdev={f(rows['writer_r5']['stdev'])}"),
            "critical",
            "同步存储 token 和 writer stability 口径。",
        ),
        Claim(
            "type3_boundary_claims",
            "negative_result",
            "outputs/agent_memory_type3_coverage_significance_zh.md",
            regex_fragment(f"| supervised_set_selector | supervised_set_selector | coverage_ratio@5 | 0.3775 | 0.3203 | {signed(rows['type3_cov']['mean_delta'])}"),
            regex_fragment(f"Coverage@5 delta 为 {signed(rows['type3_cov']['mean_delta'])}，p={f(rows['type3_cov']['permutation_p_value'], 4)}"),
            "critical",
            "同步 Type 3 边界和负结果数值。",
        ),
    ]


def first_match(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    if not match:
        return ""
    start = max(0, match.start() - 80)
    end = min(len(text), match.end() + 80)
    return " ".join(text[start:end].split())


def build_rows(project_root: Path, manuscript: Path, outputs: Path) -> list[dict[str, Any]]:
    manuscript_text = read_text(project_root / manuscript)
    claims = build_claims(project_root / outputs)
    rows: list[dict[str, Any]] = []
    for claim in claims:
        source = project_root / claim.source_path
        source_text = read_text(source)
        manuscript_ok = bool(re.search(claim.manuscript_pattern, manuscript_text, flags=re.MULTILINE))
        source_ok = bool(re.search(claim.source_pattern, source_text, flags=re.MULTILINE))
        passed = manuscript.exists() and source.exists() and manuscript_ok and source_ok
        rows.append({
            "claim_id": claim.claim_id,
            "group": claim.group,
            "severity": claim.severity,
            "status": "pass" if passed else "fail",
            "manuscript_path": str(manuscript),
            "source_path": claim.source_path,
            "manuscript_match": manuscript_ok,
            "source_match": source_ok,
            "manuscript_evidence": first_match(manuscript_text, claim.manuscript_pattern),
            "source_evidence": first_match(source_text, claim.source_pattern),
            "guidance": claim.guidance,
        })
    return rows


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
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    failures = [row for row in rows if row["status"] != "pass"]
    critical_failures = [row for row in failures if row["severity"] == "critical"]
    table_rows = [
        [row["claim_id"], row["group"], row["severity"], row["status"], row["source_path"], row["guidance"]]
        for row in rows
    ]
    lines = [
        "# Manuscript Numeric Claim Audit",
        "",
        "本文件检查论文正文中的关键数值声明是否能在当前 paper artifacts 中找到一致证据，覆盖主结果、显著性、oracle-gap、稳定性、存储 token 和 Type 3 负结果。",
        "",
        "## 总览",
        "",
        f"- Numeric claim checks: {len(rows)}",
        f"- Failures: {len(failures)}",
        f"- Critical failures: {len(critical_failures)}",
        f"- Ready for citation: {len(failures) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Claim", "Group", "Severity", "Status", "Source", "Guidance"], table_rows),
        "",
        "## 使用边界",
        "",
        "- 可以写：正文关键数值声明已通过自动一致性核对，并可追溯到当前 paper artifacts。",
        "- 应谨慎：该审计只检查数值一致性，不替代外部 embedding baseline、人工标注或跨数据集验证。",
        "- 不能写：数值一致性通过就代表最终投稿 blocker 已解除。",
    ]
    if failures:
        lines.extend(["", "## 失败项", ""])
        for row in failures:
            lines.append(f"- `{row['claim_id']}`：{row['guidance']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate numeric claims in the manuscript draft.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--manuscript", type=Path, default=Path("outputs/agent_memory_manuscript_draft_zh.md"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.manuscript, args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    failures = [row for row in rows if row["status"] != "pass"]
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "failures": len(failures),
        "critical_failures": sum(1 for row in failures if row["severity"] == "critical"),
    }, ensure_ascii=False, indent=2))
    if failures:
        sys.exit(2)


if __name__ == "__main__":
    main()
