#!/usr/bin/env python3
"""Generate a reviewer-question preparation matrix for the paper package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def lookup(rows: list[dict[str, str]], default: dict[str, str] | None = None, **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    if default is not None:
        return default
    raise KeyError(keys)


def f(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "NA"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        escaped = [cell.replace("|", "\\|").replace("\n", "<br>") for cell in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    baseline = read_csv(outputs / "agent_memory_baseline_comparison_locomo10.csv")
    reranker = read_csv(outputs / "agent_memory_candidate_reranker_locomo10_summary.csv")
    feature_ablation = read_csv(outputs / "agent_memory_candidate_reranker_feature_ablation_summary.csv")
    bootstrap = read_csv(outputs / "agent_memory_bootstrap_metric_ci.csv")
    intrinsic_loco = read_csv(outputs / "agent_memory_candidate_reranker_intrinsic_loco_summary.csv")
    writer = read_csv(outputs / "agent_memory_writer_stability_aggregate.csv")
    type3 = read_csv(outputs / "agent_memory_type3_coverage_significance_summary.csv")
    readiness = read_csv(outputs / "agent_memory_submission_readiness_gate.csv")
    public_release = read_csv(outputs / "agent_memory_public_release_readiness.csv")
    human_gate = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    embedding = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    repro_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    repro_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    integrity = read_csv(outputs / "agent_memory_artifact_integrity_manifest.csv")

    fact_type = lookup(baseline, variant="llm_extracted_fact", method="type_aware")
    obs_type = lookup(baseline, variant="locomo_observation", method="type_aware")
    reranker_row = lookup(reranker, method="candidate_reranker")
    reranker_base = lookup(reranker, method="type_aware")
    intrinsic_row = lookup(feature_ablation, method="ablation_intrinsic_only")
    intrinsic_loco_row = lookup(intrinsic_loco, method="intrinsic_reranker_loco")
    intrinsic_ci = lookup(
        bootstrap,
        scenario="candidate_reranker_intrinsic_ablation_vs_type_aware",
        metric="mrr",
        default={"delta_mean": "NA", "delta_ci_low": "NA", "delta_ci_high": "NA"},
    )
    intrinsic_loco_ci = lookup(
        bootstrap,
        scenario="candidate_reranker_intrinsic_loco",
        metric="mrr",
        default={"delta_mean": "NA", "delta_ci_low": "NA", "delta_ci_high": "NA"},
    )
    writer_mrr = lookup(writer, metric="mrr", default={"completed_runs": "0", "stdev": "NA", "status": "missing"})
    type3_cov = lookup(
        type3,
        experiment="supervised_set_selector",
        metric="coverage_ratio@5",
        default={"mean_delta": "NA", "bootstrap_ci_low": "NA", "bootstrap_ci_high": "NA"},
    )
    priority20 = lookup(
        human_gate,
        label="priority20",
        default={"confirmed_samples": "0", "min_required": "20", "invalid_labels": "NA"},
    )
    full80 = lookup(
        human_gate,
        label="full80",
        default={"confirmed_samples": "0", "min_required": "80", "invalid_labels": "NA"},
    )

    embedding_completed = sum(1 for row in embedding if row.get("status") == "completed")
    public_blockers = sum(1 for row in public_release if row.get("status") == "blocker")
    readiness_blockers = [row for row in readiness if row.get("status") == "blocker"]
    artifact_pass = sum(1 for row in repro_artifacts if row.get("exists") == "True")
    metric_pass = sum(1 for row in repro_metrics if row.get("pass") == "True")
    integrity_ok = sum(
        1
        for row in integrity
        if row.get("checksum_status") in {"ok", "self_referential_skip"} and row.get("exists") == "True"
    )

    return [
        {
            "reviewer_question": "为什么要用 LLM-written fact memory，而不是直接用 LoCoMo observation memory？",
            "risk_level": "medium",
            "current_answer": (
                f"DeepSeek fact memory + type-aware MRR={f(fact_type.get('mrr'))}, Recall@5={f(fact_type.get('recall@5'))}; "
                f"observation + type-aware MRR={f(obs_type.get('mrr'))}, Recall@5={f(obs_type.get('recall@5'))}。"
            ),
            "evidence_artifacts": "agent_memory_baseline_comparison_locomo10.csv; agent_memory_manuscript_draft_zh.md",
            "remaining_gap": "还需要人工抽查 fact memory 是否忠实于原始对话，避免只用检索指标证明 memory writer 质量。",
            "planned_response": "正文把该结论写成 representation-level retrieval gain，不宣称所有事实抽取均完全正确。",
        },
        {
            "reviewer_question": "方法增益是否只是调参或泄漏？",
            "risk_level": "medium",
            "current_answer": (
                f"held-out candidate reranker MRR={f(reranker_row.get('mrr_mean'))} vs type-aware {f(reranker_base.get('mrr_mean'))}; "
                f"intrinsic-only MRR={f(intrinsic_row.get('mrr_mean'))}, delta={f(intrinsic_ci.get('delta_mean'), 4)}, "
                f"95% CI=[{f(intrinsic_ci.get('delta_ci_low'), 4)}, {f(intrinsic_ci.get('delta_ci_high'), 4)}]。"
            ),
            "evidence_artifacts": "agent_memory_candidate_reranker_feature_ablation_zh.md; agent_memory_bootstrap_metric_ci_zh.md",
            "remaining_gap": "投稿前仍建议补一个更明确的 train/dev/test seed sweep 或固定随机种子表。",
            "planned_response": "强调候选级学习重排使用 held-out query split，并报告 intrinsic-only 消融减少 method-rank 特征依赖。",
        },
        {
            "reviewer_question": "该方法能否跨对话泛化？",
            "risk_level": "low",
            "current_answer": (
                f"intrinsic LOCO MRR={f(intrinsic_loco_row.get('mrr_mean'))}, Recall@5={f(intrinsic_loco_row.get('recall@5_mean'))}; "
                f"MRR delta={f(intrinsic_loco_ci.get('delta_mean'), 4)}, "
                f"95% CI=[{f(intrinsic_loco_ci.get('delta_ci_low'), 4)}, {f(intrinsic_loco_ci.get('delta_ci_high'), 4)}]。"
            ),
            "evidence_artifacts": "agent_memory_candidate_reranker_intrinsic_loco_zh.md; agent_memory_bootstrap_metric_ci_zh.md",
            "remaining_gap": "LoCoMo10 仍是小规模 benchmark，外部数据集泛化尚未验证。",
            "planned_response": "把 LOCO 作为跨 conversation 泛化证据，同时在 threats 中承认数据集数量限制。",
        },
        {
            "reviewer_question": "为什么没有直接接 OpenAI/Cohere/Jina 等外部 embedding baseline？",
            "risk_level": "blocker",
            "current_answer": f"当前 completed external embedding baselines={embedding_completed}，submission gate 仍将其列为 blocker。",
            "evidence_artifacts": "agent_memory_embedding_baseline_status_zh.md; agent_memory_external_embedding_blocker_audit_zh.md",
            "remaining_gap": "需要配置 OPENAI_API_KEY 或等价 OpenAI-compatible embedding provider key 并完成一次真实 API baseline。",
            "planned_response": "在最终投稿前必须补齐；当前内部稿只能说明主结果基于本地 BGE-M3。",
        },
        {
            "reviewer_question": "错误分析是否有人类标注支撑？",
            "risk_level": "blocker",
            "current_answer": (
                f"priority20 confirmed={priority20.get('confirmed_samples')}/{priority20.get('min_required')}; "
                f"full80 confirmed={full80.get('confirmed_samples')}/{full80.get('min_required')}。"
            ),
            "evidence_artifacts": "agent_memory_human_audit_annotation_codebook_zh.md; agent_memory_human_audit_readiness_gate_zh.md",
            "remaining_gap": "需要人工填写 priority20，最终投稿建议 full80 双人标注并报告一致性。",
            "planned_response": "当前只能把 LLM-assisted audit 写成辅助诊断，不能当作人工可靠性结论。",
        },
        {
            "reviewer_question": "Type 3 多证据问题是否真的被解决？",
            "risk_level": "medium",
            "current_answer": (
                f"Type 3 supervised set selector Coverage@5 delta={f(type3_cov.get('mean_delta'), 4)}, "
                f"95% CI=[{f(type3_cov.get('bootstrap_ci_low'), 4)}, {f(type3_cov.get('bootstrap_ci_high'), 4)}]，当前是负结果。"
            ),
            "evidence_artifacts": "agent_memory_type3_coverage_significance_zh.md; agent_memory_paper_experiment_status_zh.md",
            "remaining_gap": "需要 listwise/setwise objective 或 LLM query decomposition，当前方法没有解决 Type 3。",
            "planned_response": "把 Type 3 写成清晰边界和未来工作，不把它包装成主贡献。",
        },
        {
            "reviewer_question": "结果是否可复现，artifact 是否完整？",
            "risk_level": "low",
            "current_answer": (
                f"reproducibility artifacts={artifact_pass}/{len(repro_artifacts)}, metrics={metric_pass}/{len(repro_metrics)}, "
                f"integrity ok/skip={integrity_ok}/{len(integrity)}。"
            ),
            "evidence_artifacts": "agent_memory_reproducibility_checklist_zh.md; agent_memory_artifact_integrity_manifest_zh.md",
            "remaining_gap": "新增 artifact 后必须同步刷新清单和 manifest。",
            "planned_response": "随论文提交附复现命令、artifact index 和 sha256 manifest。",
        },
        {
            "reviewer_question": "仓库公开发布是否会泄露 API key 或本地敏感文件？",
            "risk_level": "low" if public_blockers == 0 else "blocker",
            "current_answer": f"public release blockers={public_blockers}; readiness blockers={len(readiness_blockers)}。",
            "evidence_artifacts": "agent_memory_public_release_readiness_zh.md; agent_memory_submission_readiness_gate_zh.md",
            "remaining_gap": "推送前继续只提交明确 artifact，避免 `.env`、cache 和原始密钥进入版本库。",
            "planned_response": "公开仓库保留 `.env.example`，真实 key 只在本地 `.env`。",
        },
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [row for row in rows if row["risk_level"] == "blocker"]
    medium = [row for row in rows if row["risk_level"] == "medium"]
    table_rows = [
        [
            row["reviewer_question"],
            row["risk_level"],
            row["current_answer"],
            row["remaining_gap"],
            row["planned_response"],
        ]
        for row in rows
    ]
    lines = [
        "# 审稿问题准备矩阵",
        "",
        "本文件把当前实验包最容易被追问的问题整理成“可回答证据、剩余缺口、投稿前动作”。它的作用是帮助后续论文写作和答辩，而不是把未完成实验写成已完成结果。",
        "",
        "## 总览",
        "",
        f"- Reviewer questions tracked: {len(rows)}",
        f"- Blocker-level questions: {len(blockers)}",
        f"- Medium-risk questions: {len(medium)}",
        "",
        markdown_table(
            ["Reviewer Question", "Risk", "Current Evidence", "Remaining Gap", "Planned Response"],
            table_rows,
        ),
        "",
        "## 投稿前优先级",
        "",
        "1. 先解决 blocker：真实外部 embedding baseline、priority20/full80 人工复核。",
        "2. 再补强 medium risk：随机种子/划分稳定性、外部数据集或更大 slice、Type 3 set-level 方法。",
        "3. 最后做文字层面：把所有 pending 内容写进 limitations，而不是写成主结论。",
        "",
        "## 写作边界",
        "",
        "- 可以写：BGE-M3 本地 embedding + fact-level memory + intrinsic candidate reranker 在 LoCoMo10 answerable slice 上有稳定提升。",
        "- 可以写：Type 3 多证据问题仍是当前方法边界，并由负结果支持。",
        "- 暂不能写：外部商业 embedding 已验证、人工审计已确认错误类型、方法已经跨多个真实 benchmark 泛化。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reviewer response preparation matrix.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "tracked_questions": len(rows),
        "blockers": sum(1 for row in rows if row["risk_level"] == "blocker"),
        "medium_risks": sum(1 for row in rows if row["risk_level"] == "medium"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
