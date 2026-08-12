#!/usr/bin/env python3
"""Validate manuscript claims against current experiment readiness."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["rule_id", "severity", "status", "evidence", "guidance"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def lookup(rows: list[dict[str, str]], **keys: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in keys.items()):
            return row
    raise KeyError(keys)


def contains_any(text: str, patterns: list[str]) -> list[str]:
    hits = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def contains_forbidden_claim(text: str, patterns: list[str]) -> list[str]:
    hits = []
    negators = ("不能", "尚未", "未完成", "不应", "不等同", "不能把", "不能宣称", "not ", "cannot", "should not")
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            prefix = text[max(0, match.start() - 40):match.start()]
            if any(negator in prefix for negator in negators):
                continue
            hits.append(pattern)
            break
    return hits


def validate(manuscript: str, outputs: Path) -> list[dict[str, str]]:
    embedding_status = read_csv(outputs / "agent_memory_embedding_baseline_status.csv")
    embedding_acceptance = read_csv(outputs / "agent_memory_api_embedding_paper_acceptance.csv")
    priority_agreement = read_csv(outputs / "agent_memory_human_llm_audit_priority20_agreement.csv")
    full_agreement = read_csv(outputs / "agent_memory_human_llm_audit_agreement.csv")

    embedding_completed = sum(1 for row in embedding_status if row.get("status") == "completed")
    embedding_accepted = sum(1 for row in embedding_acceptance if row.get("paper_acceptance_pass") == "True")
    priority_confirmed = int(lookup(priority_agreement, group="overview", label="confirmed_samples")["count"])
    full_confirmed = int(lookup(full_agreement, group="overview", label="confirmed_samples")["count"])

    checks: list[dict[str, str]] = []

    external_done_hits = contains_forbidden_claim(manuscript, [
        r"外部\s*embedding\s*baseline\s*(已经|已)\s*(完成|验证|跑完)",
        r"external\s+embedding\s+baseline\s+(is\s+)?(completed|validated)",
        r"text-embedding-3-small.*(优于|超过|提升|completed)",
    ])
    if embedding_completed == 0 and external_done_hits:
        checks.append({
            "rule_id": "external_embedding_not_completed",
            "severity": "blocker",
            "status": "fail",
            "evidence": "; ".join(external_done_hits),
            "guidance": "外部 embedding baseline 尚未完成，正文只能写为 pending/protocol/limitation。",
        })
    else:
        checks.append({
            "rule_id": "external_embedding_not_completed",
            "severity": "blocker",
            "status": "pass",
            "evidence": f"completed={embedding_completed}; no forbidden completion claim found",
            "guidance": "保持外部 embedding baseline 为待补实验，直到 summary.csv、postrun gate 和 strict paper acceptance 均通过。",
        })

    acceptance_boundary_present = (
        "paper_acceptance_pass" in manuscript
        or "strict paper acceptance" in manuscript
        or "agent_memory_api_embedding_paper_acceptance_zh.md" in manuscript
    )
    if embedding_accepted == 0 and not acceptance_boundary_present:
        checks.append({
            "rule_id": "external_embedding_acceptance_caveat",
            "severity": "minor",
            "status": "fail",
            "evidence": f"paper_acceptance_pass={embedding_accepted}; strict acceptance caveat missing",
            "guidance": "正文/附录应明确外部 embedding 需要 postrun gate 和 strict paper acceptance，不能只写 summary/comparison。",
        })
    else:
        checks.append({
            "rule_id": "external_embedding_acceptance_caveat",
            "severity": "minor",
            "status": "pass",
            "evidence": f"paper_acceptance_pass={embedding_accepted}; strict acceptance caveat present",
            "guidance": "保持外部 embedding 的最终引用标准与 acceptance gate 一致。",
        })

    human_verified_hits = contains_forbidden_claim(manuscript, [
        r"human-verified\s+error\s+analysis",
        r"人工(已经|已)?(验证|确认|复核).*错误分析",
        r"错误分析.*(已经|已).*(人工验证|人工确认|人工复核)",
    ])
    if full_confirmed < 80 and human_verified_hits:
        checks.append({
            "rule_id": "human_audit_not_completed",
            "severity": "blocker",
            "status": "fail",
            "evidence": "; ".join(human_verified_hits),
            "guidance": "完整 80 条人工确认未完成，不能写 human-verified error analysis。",
        })
    else:
        checks.append({
            "rule_id": "human_audit_not_completed",
            "severity": "blocker",
            "status": "pass",
            "evidence": f"full_confirmed={full_confirmed}; no forbidden human-verified claim found",
            "guidance": "可以写 LLM-assisted audit draft 或人工确认流程；完成后再升级声明。",
        })

    quick_review_hits = contains_forbidden_claim(manuscript, [
        r"quick-review.*(完成|completed|validated)",
        r"priority20.*(已经|已).*(确认|验证|复核)",
    ])
    if priority_confirmed < 20 and quick_review_hits:
        checks.append({
            "rule_id": "priority20_not_completed",
            "severity": "major",
            "status": "fail",
            "evidence": "; ".join(quick_review_hits),
            "guidance": "priority20 尚未人工确认，不能写 quick-review 已完成。",
        })
    else:
        checks.append({
            "rule_id": "priority20_not_completed",
            "severity": "major",
            "status": "pass",
            "evidence": f"priority_confirmed={priority_confirmed}; no forbidden quick-review completion claim found",
            "guidance": "可以写 priority20 确认包已准备好，但不能写已完成人工一致性。",
        })

    cross_dataset_hits = contains_forbidden_claim(manuscript, [
        r"跨数据集(泛化|有效|验证)",
        r"cross-dataset\s+(generalization|validated|robust)",
        r"一般(智能体|agent).*场景.*(有效|泛化)",
    ])
    allowed_boundary = "不等同于跨数据集泛化" in manuscript or "不能写一般智能体记忆场景均有效" in manuscript
    if cross_dataset_hits and not allowed_boundary:
        checks.append({
            "rule_id": "cross_dataset_overclaim",
            "severity": "major",
            "status": "fail",
            "evidence": "; ".join(cross_dataset_hits),
            "guidance": "当前只有 LoCoMo10 和 LOCO split，不能宣称跨数据集泛化。",
        })
    else:
        checks.append({
            "rule_id": "cross_dataset_overclaim",
            "severity": "major",
            "status": "pass",
            "evidence": "cross-dataset wording is absent or explicitly framed as a limitation",
            "guidance": "跨数据集结论需要第二数据集或更大真实切片支撑。",
        })

    production_scale_hits = contains_forbidden_claim(manuscript, [
        r"生产规模.*(验证|有效|可用)",
        r"production-scale.*(validated|ready|robust)",
    ])
    production_boundary = "不能直接代表真实生产规模" in manuscript or "synthetic distractor" in manuscript
    if production_scale_hits and not production_boundary:
        checks.append({
            "rule_id": "production_scale_overclaim",
            "severity": "major",
            "status": "fail",
            "evidence": "; ".join(production_scale_hits),
            "guidance": "当前 100k 结果是 synthetic distractor efficiency diagnostic。",
        })
    else:
        checks.append({
            "rule_id": "production_scale_overclaim",
            "severity": "major",
            "status": "pass",
            "evidence": "production-scale wording is absent or explicitly framed as a limitation",
            "guidance": "保留 synthetic/diagnostic 限定。",
        })

    required_caveats = {
        "external_embedding_caveat": "外部 embedding baseline completed=0",
        "human_audit_caveat": "不能宣称 human-verified error analysis",
        "locomo10_scope": "LoCoMo10 answerable slice",
    }
    for rule_id, phrase in required_caveats.items():
        checks.append({
            "rule_id": rule_id,
            "severity": "minor",
            "status": "pass" if phrase in manuscript else "fail",
            "evidence": phrase,
            "guidance": f"正文应明确包含 `{phrase}` 以提醒读者当前范围。",
        })
    return checks


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def write_report(path: Path, checks: list[dict[str, str]]) -> None:
    failures = [row for row in checks if row["status"] == "fail"]
    blocker_failures = [row for row in failures if row["severity"] == "blocker"]
    status = "pass" if not failures else "fail"
    if blocker_failures:
        status = "blocker_fail"
    rows = [
        [row["rule_id"], row["severity"], row["status"], row["evidence"], row["guidance"]]
        for row in checks
    ]
    lines = [
        "# 论文声明一致性检查",
        "",
        "本文件检查正文草稿是否把当前仍处于 pending/protocol 的实验写成已完成结论。它是论文写作阶段的安全闸门，不替代实验本身。",
        "",
        "## 总览",
        "",
        f"- 状态：`{status}`",
        f"- 检查项：{len(checks)}",
        f"- 失败项：{len(failures)}",
        f"- blocker 失败项：{len(blocker_failures)}",
        "",
        "## 检查结果",
        "",
        markdown_table(["Rule", "Severity", "Status", "Evidence", "Guidance"], rows),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate manuscript claims against experiment readiness.")
    parser.add_argument("--manuscript", type=Path, required=True)
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    manuscript = args.manuscript.read_text(encoding="utf-8")
    checks = validate(manuscript, args.outputs_dir)
    write_csv(args.output_csv, checks)
    write_report(args.output_report, checks)
    failures = [row for row in checks if row["status"] == "fail"]
    print(json.dumps({
        "checks": len(checks),
        "failures": len(failures),
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
    }, ensure_ascii=False, indent=2))
    if any(row["severity"] == "blocker" for row in failures):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
