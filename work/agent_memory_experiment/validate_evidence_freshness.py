#!/usr/bin/env python3
"""Check paper-facing artifacts for stale reproducibility gate counts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


TARGETS = (
    "agent_memory_reproducibility_checklist_zh.md",
    "agent_memory_artifact_integrity_manifest_zh.md",
    "agent_memory_submission_readiness_zh.md",
    "agent_memory_submission_gap_analysis_zh.md",
    "agent_memory_paper_evidence_matrix_zh.md",
    "agent_memory_manuscript_draft_zh.md",
    "agent_memory_reviewer_response_prep_zh.md",
    "agent_memory_submission_package_index_zh.md",
)

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{
            "file": "",
            "line": "",
            "kind": "",
            "observed": "",
            "expected": "",
            "status": "pass",
            "context": "No stale reproducibility count found.",
        }]
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count(rows: list[dict[str, str]], key: str, value: str) -> int:
    return sum(1 for row in rows if row.get(key) == value)


def current_counts(outputs: Path) -> dict[str, str]:
    artifacts = read_csv(outputs / "agent_memory_reproducibility_artifacts.csv")
    metrics = read_csv(outputs / "agent_memory_reproducibility_metrics.csv")
    manifest = read_csv(outputs / "agent_memory_artifact_integrity_manifest.csv")
    return {
        "artifact_gate": f"{count(artifacts, 'exists', 'True')}/{len(artifacts)}",
        "metric_gate": f"{count(metrics, 'pass', 'True')}/{len(metrics)}",
        "integrity_gate": f"{count(manifest, 'exists', 'True')}/{len(manifest)}",
        "sha256_ok": str(count(manifest, "checksum_status", "ok")),
        "self_skips": str(count(manifest, "checksum_status", "self_referential_skip")),
    }


def relevant_line(line: str) -> bool:
    lowered = line.lower()
    keywords = (
        "artifact",
        "metric",
        "reproducibility",
        "integrity manifest",
        "复现",
        "关键指标",
        "完整性",
        "门禁",
    )
    return any(keyword in lowered or keyword in line for keyword in keywords)


def classify_count(text: str) -> str | None:
    lowered = text.lower()
    if "metric" in lowered or "关键指标" in text:
        return "metric_gate"
    if "integrity manifest" in lowered or "完整性" in text:
        return "integrity_gate"
    if "artifact" in lowered or "复现清单 artifact" in text or "Artifact 存在性" in text:
        return "artifact_gate"
    return None


def classify_match(line: str, start: int) -> str | None:
    prefix = line[max(0, start - 80):start].lower()
    candidates: list[tuple[int, str]] = []
    keyword_groups = {
        "metric_gate": ("metric", "metrics", "关键指标"),
        "integrity_gate": ("integrity manifest", "integrity", "完整性"),
        "artifact_gate": ("artifact", "artifacts", "artifact gate", "复现清单 artifact", "artifact 存在性"),
    }
    for kind, keywords in keyword_groups.items():
        for keyword in keywords:
            pos = prefix.rfind(keyword.lower())
            if pos >= 0:
                candidates.append((pos, kind))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return classify_count(line)


def scan_file(path: Path, counts: dict[str, str]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if not path.exists():
        findings.append({
            "file": str(path),
            "line": "",
            "kind": "missing_target",
            "observed": "",
            "expected": "",
            "status": "warn",
            "context": "Paper-facing target file does not exist.",
        })
        return findings
    count_re = re.compile(r"(?<!\d)(\d+)/(\d+)(?!\d)")
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not relevant_line(line):
            continue
        for match in count_re.finditer(line):
            kind = classify_match(line, match.start())
            if kind is None:
                continue
            expected = counts[kind]
            observed = f"{match.group(1)}/{match.group(2)}"
            if observed != expected:
                findings.append({
                    "file": str(path),
                    "line": line_no,
                    "kind": kind,
                    "observed": observed,
                    "expected": expected,
                    "status": "stale_count",
                    "context": line.strip(),
                })
    return findings


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, rows: list[dict[str, Any]], counts: dict[str, str]) -> None:
    stale = [row for row in rows if row["status"] == "stale_count"]
    warnings = [row for row in rows if row["status"] == "warn"]
    lines = [
        "# Evidence Freshness Audit",
        "",
        "本文件检查论文面向读者的关键 artifact 是否还残留旧的复现门禁数字。它用于避免新增实验后，manuscript、evidence matrix、submission gap 等文档出现互相矛盾的 artifact/metric 数。",
        "",
        "## 当前权威门禁",
        "",
        f"- Reproducibility artifact gate: {counts['artifact_gate']}",
        f"- Reproducibility metric gate: {counts['metric_gate']}",
        f"- Artifact integrity gate: {counts['integrity_gate']}",
        f"- sha256 ok / self skips: {counts['sha256_ok']} / {counts['self_skips']}",
        "",
        "## 结果",
        "",
        f"- stale count findings: {len(stale)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if stale:
        lines.extend([
            "## Stale Count Findings",
            "",
            markdown_table(
                ["File", "Line", "Kind", "Observed", "Expected", "Context"],
                [
                    [
                        row["file"],
                        str(row["line"]),
                        row["kind"],
                        row["observed"],
                        row["expected"],
                        row["context"],
                    ]
                    for row in stale
                ],
            ),
            "",
        ])
    else:
        lines.extend([
            "## Stale Count Findings",
            "",
            "- 无。关键论文文档没有发现旧的 artifact/metric/integrity 门禁数字。",
            "",
        ])
    if warnings:
        lines.extend([
            "## Warnings",
            "",
            markdown_table(
                ["File", "Status", "Context"],
                [[row["file"], row["status"], row["context"]] for row in warnings],
            ),
            "",
        ])
    lines.extend([
        "## 使用边界",
        "",
        "- 该检查只覆盖复现门禁数字的新旧一致性，不验证实验结论本身是否正确。",
        "- 每次新增 artifact、metric 或重新生成论文文档后，都应重新运行本检查。",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate evidence freshness for paper-facing reports.")
    parser.add_argument("--outputs", type=Path, default=Path("outputs"))
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    args = parser.parse_args()

    counts = current_counts(args.outputs)
    rows: list[dict[str, Any]] = []
    for target in TARGETS:
        rows.extend(scan_file(args.outputs / target, counts))
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows, counts)
    stale_count = sum(1 for row in rows if row["status"] == "stale_count")
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "stale_count_findings": stale_count,
        "artifact_gate": counts["artifact_gate"],
        "metric_gate": counts["metric_gate"],
        "integrity_gate": counts["integrity_gate"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
