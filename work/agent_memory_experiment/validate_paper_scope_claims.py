#!/usr/bin/env python3
"""Audit paper-facing documents for scope and generalization overclaims."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_DOCUMENTS = [
    "README.md",
    "outputs/agent_memory_manuscript_draft_zh.md",
    "outputs/agent_memory_experiment_protocol_zh.md",
    "outputs/agent_memory_submission_gap_analysis_zh.md",
    "outputs/agent_memory_threats_to_validity_zh.md",
    "outputs/agent_memory_reproducibility_checklist_zh.md",
    "outputs/agent_memory_current_design_zh.md",
]

NEGATORS = (
    "不能",
    "尚未",
    "未完成",
    "未",
    "不应",
    "不等同",
    "不能把",
    "不能宣称",
    "不宣称",
    "避免",
    "禁止",
    "不可",
    "谨慎",
    "限制",
    "待补",
    "pending",
    "limitation",
    "not ",
    "cannot",
    "should not",
    "does not",
)

FORBIDDEN_CLAIMS = [
    (
        "cross_dataset_generalization",
        "major",
        [
            r"跨数据集(泛化|有效|验证|鲁棒)",
            r"cross-dataset\s+(generalization|validated|robust)",
            r"一般(智能体|agent).*场景.*(有效|泛化)",
        ],
        "当前证据主要是 LoCoMo10 answerable slice 与 LOCO split，不能写成跨数据集泛化。",
    ),
    (
        "external_embedding_completed",
        "blocker",
        [
            r"外部\s*embedding\s*baseline\s*(已经|已)\s*(完成|验证|跑完)",
            r"external\s+embedding\s+baseline\s+(is\s+)?(completed|validated)",
            r"text-embedding-3-small.*(优于|超过|提升|completed)",
        ],
        "外部 embedding baseline completed=0，不能写成已完成结果。",
    ),
    (
        "human_verified_error_analysis",
        "blocker",
        [
            r"human-verified\s+error\s+analysis",
            r"人工(已经|已)?(验证|确认|复核).*错误分析",
            r"错误分析.*(已经|已).*(人工验证|人工确认|人工复核)",
        ],
        "人工确认仍为 0，不能写 human-verified error analysis。",
    ),
    (
        "production_scale_validation",
        "major",
        [
            r"生产规模.*(验证|有效|可用)",
            r"production-scale.*(validated|ready|robust)",
        ],
        "100k 扩展实验是 synthetic distractor diagnostic，不能写生产规模验证。",
    ),
    (
        "end_to_end_agent_success",
        "major",
        [
            r"端到端\s*agent\s*task\s*(success|成功).*(提升|验证|解决)",
            r"end-to-end\s+agent\s+task\s+success\s+(improved|validated|solved)",
        ],
        "当前评估是 memory retrieval，不等同端到端 agent task success。",
    ),
]

REQUIRED_BOUNDARIES = [
    (
        "locomo10_scope",
        "LoCoMo10 answerable slice",
        "至少一个核心文档需要明确主结论限定在 LoCoMo10 answerable slice。",
    ),
    (
        "external_embedding_pending",
        "外部 embedding baseline completed=0",
        "至少一个核心文档需要明确外部 embedding baseline 尚未完成。",
    ),
    (
        "human_audit_pending",
        "不能宣称 human-verified error analysis",
        "至少一个核心文档需要明确人工错误分析尚未 human-verified。",
    ),
    (
        "synthetic_scaling_limit",
        "synthetic distractor",
        "至少一个核心文档需要说明大规模效率实验包含 synthetic distractor 限定。",
    ),
    (
        "retrieval_not_agent_success",
        "不等价于端到端 agent task success",
        "至少一个核心文档需要说明检索指标不等价于端到端 agent 成功。",
    ),
]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def is_negated(text: str, start: int) -> bool:
    context = text[max(0, start - 80):start + 120]
    return any(negator in context for negator in NEGATORS)


def overclaim_hits(rel: str, text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim_id, severity, patterns, guidance in FORBIDDEN_CLAIMS:
        hit_evidence = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if is_negated(text, match.start()):
                    continue
                snippet = text[max(0, match.start() - 80):match.end() + 80].replace("\n", " ")
                hit_evidence.append(snippet[:240])
                break
        rows.append({
            "group": "forbidden_overclaim",
            "item": claim_id,
            "document": rel,
            "severity": severity,
            "pass": not hit_evidence,
            "status": "pass" if not hit_evidence else severity,
            "evidence": "no unqualified overclaim found" if not hit_evidence else " || ".join(hit_evidence[:3]),
            "guidance": guidance,
        })
    return rows


def boundary_rows(text_by_doc: dict[str, str]) -> list[dict[str, Any]]:
    combined = "\n".join(text_by_doc.values())
    rows = []
    for boundary_id, phrase, guidance in REQUIRED_BOUNDARIES:
        docs = [rel for rel, text in text_by_doc.items() if phrase in text]
        rows.append({
            "group": "required_boundary",
            "item": boundary_id,
            "document": ";".join(docs),
            "severity": "major",
            "pass": bool(docs),
            "status": "pass" if docs else "major",
            "evidence": phrase if phrase in combined else "missing boundary phrase",
            "guidance": guidance,
        })
    return rows


def build_rows(root: Path, documents: list[str]) -> list[dict[str, Any]]:
    text_by_doc = {rel: file_text(root / rel) for rel in documents}
    rows: list[dict[str, Any]] = []
    for rel, text in text_by_doc.items():
        if not text:
            rows.append({
                "group": "document_presence",
                "item": "document_exists",
                "document": rel,
                "severity": "major",
                "pass": False,
                "status": "major",
                "evidence": "missing or unreadable",
                "guidance": "Regenerate or restore the paper-facing document.",
            })
            continue
        rows.append({
            "group": "document_presence",
            "item": "document_exists",
            "document": rel,
            "severity": "info",
            "pass": True,
            "status": "pass",
            "evidence": f"chars={len(text)}",
            "guidance": "Document is available for scope-claim audit.",
        })
        rows.extend(overclaim_hits(rel, text))
    rows.extend(boundary_rows(text_by_doc))
    return rows


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
    majors = [row for row in rows if row["status"] == "major"]
    table = [
        [row["group"], row["item"], row["document"], row["severity"], str(row["pass"]), row["evidence"], row["guidance"]]
        for row in rows
    ]
    lines = [
        "# Paper Scope Claim Audit",
        "",
        "本文件跨 README、正文草稿、实验协议、风险矩阵、有效性威胁和复现文档检查论文声明边界，防止把 LoCoMo10 检索实验过度写成跨数据集、生产规模或端到端 agent 成功结论。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major warnings: {len(majors)}",
        f"- Scope-safe for current draft: {len(blockers) == 0 and len(majors) == 0}",
        "",
        "## 检查明细",
        "",
        markdown_table(["Group", "Item", "Document", "Severity", "Pass", "Evidence", "Guidance"], table),
        "",
        "## 论文使用边界",
        "",
        "- 可以写：当前 paper-facing 文档的主要结论边界与 LoCoMo10 answerable slice、pending external embedding baseline、pending human audit 一致。",
        "- 不能写：该审计通过就等于外部泛化、人工验证或生产级部署已经完成。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit paper-facing documents for scope/generalization overclaims.")
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--documents", nargs="*", default=DEFAULT_DOCUMENTS)
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_paper_scope_claim_audit.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_paper_scope_claim_audit_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.project_root, args.documents)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    blockers = sum(1 for row in rows if row["status"] == "blocker")
    majors = sum(1 for row in rows if row["status"] == "major")
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "checks": len(rows),
        "blockers": blockers,
        "major": majors,
        "scope_safe": blockers == 0 and majors == 0,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
