#!/usr/bin/env python3
"""Generate an index of paper submission artifacts and remaining blockers."""

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


def exists(outputs: Path, path: str) -> str:
    return str((outputs.parent / path).exists() if path.startswith("outputs/") else Path(path).exists())


def build_rows(root: Path) -> list[dict[str, Any]]:
    outputs = root / "outputs"
    readiness = read_csv(outputs / "agent_memory_submission_readiness_gate.csv")
    claim_check = read_csv(outputs / "agent_memory_manuscript_claim_check.csv")
    blocker_evidence = "; ".join(
        f"{row.get('gate')}={row.get('evidence')}"
        for row in readiness
        if row.get("status") == "blocker"
    )
    external_evidence = "; ".join(
        f"{row.get('gate')}={row.get('evidence')}"
        for row in readiness
        if row.get("status") == "blocker" and row.get("category") == "external_baseline"
    )
    human_evidence = "; ".join(
        f"{row.get('gate')}={row.get('evidence')}"
        for row in readiness
        if row.get("status") == "blocker" and row.get("category") == "reliability"
    )
    claim_evidence = "; ".join(
        f"{row.get('rule_id')}={row.get('status')}"
        for row in claim_check
    )
    rows = [
        {
            "section": "Manuscript",
            "artifact": "outputs/agent_memory_manuscript_draft_zh.md",
            "role": "中文正文初稿，含摘要、方法、实验、结果、Threats to Validity 和投稿前 TODO。",
            "status": "ready_for_internal_review",
            "evidence": claim_evidence,
            "next_action": "外部 embedding 与人工复核完成后重新生成正文并重跑 claim check。",
        },
        {
            "section": "Main Tables",
            "artifact": "outputs/agent_memory_paper_tables_zh.md",
            "role": "论文主表、消融表、LOCO 验证表和 Type 3 负结果表的 Markdown 版本。",
            "status": "ready",
            "evidence": "paired/bootstrap results already cached",
            "next_action": "投稿前同步最终 embedding baseline 行。",
        },
        {
            "section": "Main Tables",
            "artifact": "outputs/agent_memory_paper_tables.tex",
            "role": "可复制进论文的 LaTeX booktabs 表格。",
            "status": "ready",
            "evidence": "generated from cached result tables",
            "next_action": "投稿前根据目标模板微调 caption/label。",
        },
        {
            "section": "Method Appendix",
            "artifact": "outputs/agent_memory_intrinsic_reranker_method_appendix_zh.md",
            "role": "intrinsic feature reranker 的候选池、特征、模型、验证协议和复现命令。",
            "status": "ready",
            "evidence": "held-out and LOCO intrinsic reranker results present",
            "next_action": "将核心公式与特征表压缩进正文方法小节。",
        },
        {
            "section": "Method Appendix",
            "artifact": "outputs/agent_memory_candidate_reranker_seed_stability_zh.md",
            "role": "intrinsic candidate reranker 的 20-seed 随机划分稳定性证据。",
            "status": "ready",
            "evidence": "intrinsic reranker improves over type-aware in 20/20 seeds",
            "next_action": "投稿正文可把该结果写入 robustness/stability 小节。",
        },
        {
            "section": "Method Appendix",
            "artifact": "outputs/agent_memory_candidate_reranker_paired_effect_size_zh.md",
            "role": "intrinsic candidate reranker 的 improved/worsened/tied、query type breakdown 和 paired Cohen's dz。",
            "status": "ready",
            "evidence": "paired outcome and effect-size diagnostics generated",
            "next_action": "投稿正文可用该结果解释收益分布和 Type 3 边界。",
        },
        {
            "section": "Experiment Protocol",
            "artifact": "outputs/agent_memory_experiment_protocol_zh.md",
            "role": "数据切片、指标公式、显著性检验、主结果、负结果和写法边界。",
            "status": "ready",
            "evidence": "protocol appendix generated from cached metrics",
            "next_action": "作为 supplementary material 或实验设置附录。",
        },
        {
            "section": "Evidence Matrix",
            "artifact": "outputs/agent_memory_paper_evidence_matrix_zh.md",
            "role": "论文主张、证据强度、剩余缺口和可写边界矩阵。",
            "status": "ready",
            "evidence": "claim check passes and blockers are explicit",
            "next_action": "写作时逐条核对摘要/贡献是否过度宣称。",
        },
        {
            "section": "Threats to Validity",
            "artifact": "outputs/agent_memory_threats_to_validity_zh.md",
            "role": "内部/外部/构念/统计/规模/复现有效性威胁与缓解措施。",
            "status": "ready_with_blockers_declared",
            "evidence": "2 blocker threats are explicitly listed",
            "next_action": "外部 embedding 和人工复核完成后更新 blocker 行。",
        },
        {
            "section": "Reviewer Prep",
            "artifact": "outputs/agent_memory_reviewer_response_prep_zh.md",
            "role": "审稿人可能追问的问题、当前证据、剩余缺口和安全写作边界。",
            "status": "ready_with_blockers_declared",
            "evidence": "external embedding and human audit blockers are explicitly listed",
            "next_action": "每次补完 blocker 或修改主张后重新生成。",
        },
        {
            "section": "External Embedding",
            "artifact": "outputs/agent_memory_external_embedding_blocker_audit_zh.md",
            "role": "外部 embedding baseline 的 key、preflight、summary 和 comparison blocker 审计。",
            "status": "blocked",
            "evidence": external_evidence,
            "next_action": "配置 OPENAI_API_KEY 或 OpenAI-compatible provider key 后运行 API baseline。",
        },
        {
            "section": "Human Audit",
            "artifact": "outputs/agent_memory_human_audit_annotation_codebook_zh.md",
            "role": "人工复核 yes/partial/no、gold sufficiency、manual reason 和双人标注规则。",
            "status": "ready_for_labeling",
            "evidence": human_evidence,
            "next_action": "先填写 priority20 盲审 CSV，再扩展 full80。",
        },
        {
            "section": "Human Audit",
            "artifact": "outputs/agent_memory_human_audit_priority20_review_packet_zh.md",
            "role": "20 条优先人工复核阅读包。",
            "status": "ready_for_labeling",
            "evidence": "priority20 confirmed=0/20",
            "next_action": "人工填写 blind review CSV 的 human_* 字段。",
        },
        {
            "section": "Reproducibility",
            "artifact": "outputs/agent_memory_reproducibility_checklist_zh.md",
            "role": "artifact、指标阈值、数据规模、复现命令和环境入口清单。",
            "status": "pass",
            "evidence": "artifact gate and metric gate pass",
            "next_action": "新增任何 artifact 后重新生成。",
        },
        {
            "section": "Reproducibility",
            "artifact": "outputs/agent_memory_artifact_integrity_manifest_zh.md",
            "role": "复现 artifact sha256、大小和行数 manifest。",
            "status": "pass",
            "evidence": "manifest covers all reproducibility artifacts",
            "next_action": "每次结果更新后重新生成。",
        },
        {
            "section": "Submission Gate",
            "artifact": "outputs/agent_memory_submission_readiness_gate_zh.md",
            "role": "最终投稿门禁，聚合复现、claim check、外部 baseline、人工复核和公开发布卫生。",
            "status": "not_ready",
            "evidence": blocker_evidence,
            "next_action": "解除 external_embedding_completed、priority20/full80_human_audit 和 reviewer_risk_blockers。",
        },
    ]
    for row in rows:
        row["exists"] = exists(outputs, row["artifact"])
    return rows


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    missing = [row for row in rows if row["exists"] != "True"]
    blocked = [row for row in rows if row["status"] in {"blocked", "not_ready"}]
    table_rows = [
        [
            row["section"],
            row["artifact"],
            row["exists"],
            row["status"],
            row["role"],
            row["next_action"],
        ]
        for row in rows
    ]
    lines = [
        "# 论文提交包索引",
        "",
        "本文件把当前论文相关 artifact 按正文、表格、方法附录、有效性威胁、外部 embedding、人审和复现门禁组织起来。它用于内部检查和后续投稿打包，不替代真实未完成实验。",
        "",
        "## 总览",
        "",
        f"- Indexed artifacts: {len(rows)}",
        f"- Missing indexed artifacts: {len(missing)}",
        f"- Blocked/not-ready sections: {len(blocked)}",
        "",
        markdown_table(
            ["Section", "Artifact", "Exists", "Status", "Role", "Next Action"],
            table_rows,
        ),
        "",
        "## 最小投稿前路径",
        "",
        "1. 运行至少一个真实外部 embedding baseline，并生成 completed comparison table。",
        "2. 完成 priority20 人工盲审；若目标为最终投稿，继续完成 full80 双人/仲裁复核。",
        "3. 重新生成 manuscript、paper tables、evidence matrix、threats appendix、reproducibility checklist 和 submission readiness gate。",
        "4. 确认 submission gate 从 `ready_for_final_submission=false` 变为 true 后，再把正文和附录作为最终投稿包。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate submission package index.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "indexed_artifacts": len(rows),
        "blocked": sum(1 for row in rows if row["status"] in {"blocked", "not_ready"}),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
