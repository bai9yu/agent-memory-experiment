#!/usr/bin/env python3
"""Generate an action-oriented final-submission checklist."""

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


def lookup(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str]:
    for row in rows:
        if row.get(key) == value:
            return row
    return {}


def count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() == "true"


def checklist_row(
    order: int,
    phase: str,
    item: str,
    required: bool,
    passed: bool,
    evidence: str,
    next_action: str,
    paper_update_after_pass: str,
) -> dict[str, Any]:
    if passed:
        status = "pass"
    elif required:
        status = "blocker"
    else:
        status = "pending"
    return {
        "order": order,
        "phase": phase,
        "item": item,
        "required_for_submission": required,
        "pass": passed,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
        "paper_update_after_pass": paper_update_after_pass,
    }


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    readiness = read_csv(outputs / "agent_memory_submission_readiness.csv")
    embedding_upgrade = read_csv(outputs / "agent_memory_embedding_paper_claim_upgrade.csv")
    human_upgrade = read_csv(outputs / "agent_memory_human_audit_paper_claim_upgrade.csv")
    supplement = read_csv(outputs / "agent_memory_supplementary_package_manifest.csv")
    anonymous = read_csv(outputs / "agent_memory_anonymous_submission_readiness.csv")
    public_release = read_csv(outputs / "agent_memory_public_release_readiness.csv")
    freshness = read_csv(outputs / "agent_memory_evidence_freshness_audit.csv")
    scope = read_csv(outputs / "agent_memory_paper_scope_claim_audit.csv")
    numeric = read_csv(outputs / "agent_memory_manuscript_numeric_claim_check.csv")

    api_preflight = lookup(readiness, "gate", "api_embedding_preflight")
    external_completed = lookup(readiness, "gate", "external_embedding_completed")
    priority_human = lookup(readiness, "gate", "priority20_human_audit")
    full_human = lookup(readiness, "gate", "full80_human_audit")
    reviewer_risk = lookup(readiness, "gate", "reviewer_risk_blockers")
    public_hygiene = lookup(readiness, "gate", "public_release_hygiene")
    repro_artifacts = lookup(readiness, "gate", "reproducibility_artifacts")
    repro_metrics = lookup(readiness, "gate", "reproducibility_metrics")
    manuscript_claims = lookup(readiness, "gate", "manuscript_claim_check")
    manuscript_numbers = lookup(readiness, "gate", "manuscript_numeric_claim_check")
    integrity = lookup(readiness, "gate", "artifact_integrity_manifest")

    embedding_paper_ready = lookup(embedding_upgrade, "tier", "paper_claim_ready")
    human_verified = lookup(human_upgrade, "tier", "human_verified_ready")
    supplement_findings = [row for row in supplement if row.get("anonymization_findings")]
    supplement_missing = [row for row in supplement if row.get("exists") != "True"]
    supplement_blocked = [row for row in supplement if row.get("package_bucket") == "exclude_until_blocker_closed"]
    public_blockers = count(public_release, "status", "blocker")
    anonymous_blockers = count(anonymous, "status", "blocker")
    scope_failures = count(scope, "status", "fail")
    numeric_failures = count(numeric, "status", "fail")
    stale_findings = count(freshness, "status", "fail")

    return [
        checklist_row(
            1,
            "external_embedding",
            "API embedding preflight",
            True,
            as_bool(api_preflight.get("pass")),
            api_preflight.get("evidence", ""),
            "配置 OPENAI_API_KEY 或 OpenAI-compatible provider key 后重跑 preflight。",
            "可把外部 embedding 从 pending protocol 升级为 safe-to-run baseline。",
        ),
        checklist_row(
            2,
            "external_embedding",
            "External embedding paper-ready baseline",
            True,
            as_bool(external_completed.get("pass")) and as_bool(embedding_paper_ready.get("pass")),
            f"{external_completed.get('evidence', '')}; embedding_tier={embedding_paper_ready.get('status', 'missing')}",
            "运行真实 API embedding baseline、comparison 和 postrun gate。",
            "把外部 embedding baseline 加入主表或 robustness 对照，并刷新摘要/结论边界。",
        ),
        checklist_row(
            3,
            "human_audit",
            "Priority20 quick human review",
            True,
            as_bool(priority_human.get("pass")),
            priority_human.get("evidence", ""),
            "填写 priority20 blind review 的 human_* 字段并回填 agreement。",
            "可报告 priority20 quick-review agreement，但仍需标注为小样本人工抽查。",
        ),
        checklist_row(
            4,
            "human_audit",
            "Full80 human audit",
            True,
            as_bool(full_human.get("pass")) and as_bool(human_verified.get("pass")),
            f"{full_human.get('evidence', '')}; human_tier={human_verified.get('status', 'missing')}",
            "完成 full80 single/dual/adjudication 标签并刷新 agreement/readiness。",
            "可把错误分析升级为 human-verified error analysis，并报告 exact agreement / kappa。",
        ),
        checklist_row(
            5,
            "paper_claims",
            "Manuscript claim and numeric consistency",
            True,
            as_bool(manuscript_claims.get("pass")) and as_bool(manuscript_numbers.get("pass")) and scope_failures == 0 and numeric_failures == 0,
            f"{manuscript_claims.get('evidence', '')}; {manuscript_numbers.get('evidence', '')}; scope_failures={scope_failures}; numeric_failures={numeric_failures}",
            "补完 blocker 后重新生成 manuscript、scope audit 和 numeric claim audit。",
            "摘要、贡献和结果段可以升级到与已完成证据一致的最终措辞。",
        ),
        checklist_row(
            6,
            "reproducibility",
            "Reproducibility, integrity, and freshness",
            True,
            as_bool(repro_artifacts.get("pass")) and as_bool(repro_metrics.get("pass")) and as_bool(integrity.get("pass")) and stale_findings == 0,
            f"{repro_artifacts.get('evidence', '')}; {repro_metrics.get('evidence', '')}; {integrity.get('evidence', '')}; stale_findings={stale_findings}",
            "任何实验或 artifact 变化后重跑 refresh、reproducibility、integrity 和 freshness。",
            "可在 supplement/appendix 中写 artifact-checked reproducibility package。",
        ),
        checklist_row(
            7,
            "supplement",
            "Supplement package manifest",
            True,
            not supplement_findings and not supplement_missing and bool(supplement),
            f"include_now={sum(1 for row in supplement if as_bool(row.get('include_in_current_supplement')))}, blocked={len(supplement_blocked)}, anonymization_findings={len(supplement_findings)}, missing={len(supplement_missing)}",
            "关闭外部 embedding 和人审 blocker 后重新生成 supplement manifest。",
            "可把 include_now 项作为补充材料候选，并保留 internal gates 作为仓库复现材料。",
        ),
        checklist_row(
            8,
            "release",
            "Public release and anonymization hygiene",
            True,
            as_bool(public_hygiene.get("pass")) and public_blockers == 0 and anonymous_blockers == 0,
            f"{public_hygiene.get('evidence', '')}; public_blockers={public_blockers}; anonymous_blockers={anonymous_blockers}",
            "正式匿名投稿前按会议要求移除作者、仓库 URL、账号身份信息；开源前补 LICENSE。",
            "可将仓库作为公开/内部复现 artifact 的基础版本。",
        ),
        checklist_row(
            9,
            "reviewer_risk",
            "Reviewer blocker risks closed",
            True,
            as_bool(reviewer_risk.get("pass")),
            reviewer_risk.get("evidence", ""),
            "补完外部 embedding baseline 和人工审计后重跑 gap analysis/reviewer prep。",
            "可把稿件从 internal draft 升级为 final-submission candidate。",
        ),
    ]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [row for row in rows if row["status"] == "blocker"]
    passed = [row for row in rows if row["pass"]]
    table_rows = [
        [
            str(row["order"]),
            row["phase"],
            row["item"],
            row["status"],
            row["evidence"],
            row["next_action"],
        ]
        for row in rows
    ]
    lines = [
        "# Final Submission Checklist",
        "",
        "本文件把最终投稿前的实验、论文、补充材料、匿名化和审稿风险动作整理成可执行 checklist。它不把未完成 blocker 包装成完成状态；只说明当前距离 final-submission candidate 还差什么。",
        "",
        "## 总览",
        "",
        f"- Checklist items: {len(rows)}",
        f"- Passed: {len(passed)}/{len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Ready for final-submission candidate: {len(blockers) == 0}",
        "",
        "## Checklist",
        "",
        markdown_table(["Order", "Phase", "Item", "Status", "Evidence", "Next Action"], table_rows),
        "",
        "## 当前最短收口路线",
        "",
    ]
    if blockers:
        for row in blockers:
            lines.append(f"- `{row['item']}`：{row['next_action']}")
    else:
        lines.append("- 所有必需项已通过，可以进入目标会议格式化、匿名化和最终排版检查。")
    lines.extend([
        "",
        "## 论文升级规则",
        "",
        "- 外部 embedding 与 full80 人审未通过前，不应写最终投稿级强结论。",
        "- 任何 blocker 关闭后，都要重新运行 refresh pipeline、claim checks、freshness、supplement manifest 和 submission readiness。",
        "- checklist 全部通过后，才把 `agent_memory_manuscript_draft_zh.md` 视为 final-submission candidate 的正文基础。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate final paper-submission checklist.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "passed": f"{sum(1 for row in rows if row['pass'])}/{len(rows)}",
        "blockers": sum(1 for row in rows if row["status"] == "blocker"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
