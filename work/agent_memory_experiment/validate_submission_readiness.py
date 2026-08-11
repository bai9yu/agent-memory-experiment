#!/usr/bin/env python3
"""Validate paper-submission readiness from cached experiment artifacts."""

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


def count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def gate_row(
    gate: str,
    category: str,
    required_for_submission: bool,
    passed: bool,
    evidence: str,
    next_action: str,
) -> dict[str, Any]:
    if passed:
        status = "pass"
    elif required_for_submission:
        status = "blocker"
    else:
        status = "pending"
    return {
        "gate": gate,
        "category": category,
        "required_for_submission": required_for_submission,
        "pass": passed,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_rows(outputs: Path) -> list[dict[str, Any]]:
    reproducibility_artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    reproducibility_metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    claim_check = read_csv(outputs / "agent_memory_manuscript_claim_check.csv")
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    embedding_preflight = read_csv(outputs / "agent_memory_api_embedding_preflight.csv")
    embedding_postrun = read_csv(outputs / "agent_memory_api_embedding_postrun_gate.csv")
    mock_smoke = read_csv(outputs / "agent_memory_mock_api_embedding_smoke_test.csv")
    human_sample_qc = read_csv(outputs / "agent_memory_human_audit_sample_qc.csv")
    human_gate = read_csv(outputs / "agent_memory_human_audit_readiness_gate.csv")
    gap_analysis = read_csv(outputs / "agent_memory_submission_gap_analysis.csv")
    public_release = read_csv(outputs / "agent_memory_public_release_readiness.csv")
    integrity_manifest = read_csv(outputs / "agent_memory_artifact_integrity_manifest.csv")

    artifact_pass = count(reproducibility_artifacts, "exists", "True")
    metric_pass = count(reproducibility_metrics, "pass", "True")
    claim_pass = count(claim_check, "status", "pass")
    embedding_completed = count(embedding_status, "status", "completed")
    postrun_completed = count(embedding_postrun, "postrun_pass", "True")
    preflight_required = [row for row in embedding_preflight if row.get("severity") == "required"]
    preflight_required_pass = count(preflight_required, "pass", "True")
    smoke_second = lookup(mock_smoke, run="2")
    sample_qc_failures = count(human_sample_qc, "status", "fail")
    sample_qc_rows = len(human_sample_qc)
    priority = lookup(human_gate, label="priority20")
    full = lookup(human_gate, label="full80")
    reviewer_blockers = count(gap_analysis, "risk_level", "blocker")
    public_release_blockers = count(public_release, "status", "blocker")
    integrity_covered = count(integrity_manifest, "exists", "True")
    integrity_ok = count(integrity_manifest, "checksum_status", "ok")
    integrity_self_skips = count(integrity_manifest, "checksum_status", "self_referential_skip")

    rows = [
        gate_row(
            "reproducibility_artifacts",
            "reproducibility",
            True,
            artifact_pass == len(reproducibility_artifacts),
            f"{artifact_pass}/{len(reproducibility_artifacts)} artifacts exist",
            "保持复现清单随新增 artifact 更新。",
        ),
        gate_row(
            "reproducibility_metrics",
            "reproducibility",
            True,
            metric_pass == len(reproducibility_metrics),
            f"{metric_pass}/{len(reproducibility_metrics)} metric thresholds pass",
            "修复任何低于阈值的核心指标或调整论文主张。",
        ),
        gate_row(
            "manuscript_claim_check",
            "paper_writing",
            True,
            claim_pass == len(claim_check),
            f"{claim_pass}/{len(claim_check)} claim checks pass",
            "继续防止正文把 pending 实验写成已完成结论。",
        ),
        gate_row(
            "api_embedding_preflight",
            "external_baseline",
            True,
            preflight_required_pass == len(preflight_required),
            f"{preflight_required_pass}/{len(preflight_required)} required checks pass",
            "配置 OPENAI_API_KEY 或等价外部 embedding provider key 后重跑 preflight。",
        ),
        gate_row(
            "mock_api_embedding_smoke_test",
            "external_baseline",
            False,
            smoke_second.get("requests") == "0" and smoke_second.get("summary_exists") == "True",
            f"second_run_requests={smoke_second.get('requests')}, summary_exists={smoke_second.get('summary_exists')}",
            "保持该 smoke test 作为 API backend/cache 的离线回归测试。",
        ),
        gate_row(
            "external_embedding_completed",
            "external_baseline",
            True,
            embedding_completed >= 1 and postrun_completed >= 1,
            f"completed external embedding baselines={embedding_completed}, postrun_pass={postrun_completed}",
            "实际运行至少一个外部 embedding baseline，并生成与 BGE-M3 的 delta 表。",
        ),
        gate_row(
            "human_audit_sample_qc",
            "reliability",
            True,
            sample_qc_rows > 0 and sample_qc_failures == 0,
            f"sample QC rows={sample_qc_rows}, blocking failures={sample_qc_failures}",
            "修复 priority20/full80 样本数、重复 ID 或覆盖性 QC failure。",
        ),
        gate_row(
            "priority20_human_audit",
            "reliability",
            True,
            int(priority["confirmed_samples"]) >= int(priority["min_required"]) and priority["invalid_labels"] == "0",
            f"priority20 confirmed={priority['confirmed_samples']}/{priority['min_required']}, invalid={priority['invalid_labels']}",
            "填写 priority20 盲审表 human_* 字段，回填 confirmation 后重算 agreement。",
        ),
        gate_row(
            "full80_human_audit",
            "reliability",
            True,
            int(full["confirmed_samples"]) >= int(full["min_required"]) and full["invalid_labels"] == "0",
            f"full80 confirmed={full['confirmed_samples']}/{full['min_required']}, invalid={full['invalid_labels']}",
            "投稿前完成 80 条人工确认并报告 exact agreement 与 Cohen's kappa。",
        ),
        gate_row(
            "reviewer_risk_blockers",
            "submission",
            True,
            reviewer_blockers == 0,
            f"blocker risks={reviewer_blockers}",
            "优先补齐外部 embedding baseline 和人工复核标签。",
        ),
        gate_row(
            "public_release_hygiene",
            "submission",
            True,
            public_release_blockers == 0,
            f"public release blockers={public_release_blockers}",
            "修复公开发布检查中的 key、`.env` 或仓库卫生 blocker。",
        ),
        gate_row(
            "artifact_integrity_manifest",
            "reproducibility",
            True,
            integrity_covered == len(integrity_manifest) and integrity_ok + integrity_self_skips == len(integrity_manifest),
            f"integrity manifest covers={integrity_covered}/{len(integrity_manifest)}, sha256_ok={integrity_ok}, self_skips={integrity_self_skips}",
            "重新生成 artifact integrity manifest，确保所有复现 artifact 都有 sha256 记录。",
        ),
    ]
    return rows


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    required_rows = [row for row in rows if row["required_for_submission"]]
    required_pass = sum(1 for row in required_rows if row["pass"])
    blockers = [row for row in rows if row["status"] == "blocker"]
    optional_pending = [row for row in rows if row["status"] == "pending"]
    ready = not blockers
    table_rows = [
        [
            row["gate"],
            row["category"],
            str(row["required_for_submission"]),
            str(row["pass"]),
            row["status"],
            row["evidence"],
        ]
        for row in rows
    ]
    lines = [
        "# Submission Readiness Gate",
        "",
        "本文件把当前论文实验包的关键门禁统一成一张可复现检查表。它不会把未完成实验包装成已完成结论；只要仍有 blocker，就说明当前不应作为最终投稿版本。",
        "",
        "## 总览",
        "",
        f"- Ready for final submission: {ready}",
        f"- Required gates passed: {required_pass}/{len(required_rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Optional pending: {len(optional_pending)}",
        "",
        "## Gate 明细",
        "",
        markdown_table(["Gate", "Category", "Required", "Pass", "Status", "Evidence"], table_rows),
        "",
        "## 当前 Blocker",
        "",
    ]
    if blockers:
        for row in blockers:
            lines.append(f"- `{row['gate']}`：{row['next_action']}")
    else:
        lines.append("- 无。")
    lines.extend([
        "",
        "## 论文使用判断",
        "",
    ])
    if ready:
        lines.append("- 所有必需门禁均已通过，可以进入最终投稿前的文字润色、格式检查和匿名化准备。")
    else:
        lines.append("- 当前仍可用于组会、开题/中期汇报或内部复现实验；在 blocker 解决前，不建议作为最终投稿稿。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate cached paper-submission readiness gates.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    blockers = sum(1 for row in rows if row["status"] == "blocker")
    required = [row for row in rows if row["required_for_submission"]]
    print(json.dumps({
        "output_report": str(args.output_report),
        "ready_for_final_submission": blockers == 0,
        "required_gates": f"{sum(1 for row in required if row['pass'])}/{len(required)}",
        "blockers": blockers,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
