#!/usr/bin/env python3
"""Validate consistency across submission blocker closure artifacts."""

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


def lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(k) == v for k, v in filters.items()):
            return row
    return {}


def row(check: str, passed: bool, severity: str, evidence: str, action: str) -> dict[str, Any]:
    return {
        "check": check,
        "pass": passed,
        "severity": severity,
        "status": "pass" if passed else severity,
        "evidence": evidence,
        "action": action,
    }


def text_contains(path: Path, token: str) -> bool:
    return path.exists() and token in path.read_text(encoding="utf-8")


def checklist_runbook_refs_exist_and_are_executable(checklist: list[dict[str, str]], outputs: Path) -> tuple[bool, str]:
    expected = {
        "agent_memory_api_embedding_execution_runbook_zh.md": "## 命令附录",
        "agent_memory_human_audit_execution_plan_zh.md": "## 命令附录",
        "agent_memory_submission_blocker_closure_plan_zh.md": "## 关闭路线",
    }
    text = "\n".join(row.get("next_action", "") for row in checklist)
    evidence: list[str] = []
    ok = True
    for filename, required_token in expected.items():
        referenced = filename in text
        path = outputs / filename
        exists = path.exists()
        token_present = text_contains(path, required_token)
        evidence.append(
            f"{filename}: referenced={referenced}, exists={exists}, token={required_token in path.read_text(encoding='utf-8') if exists else False}"
        )
        ok = ok and referenced and exists and token_present
    return ok, "; ".join(evidence)


def command_scripts(primary_command: str) -> list[str]:
    scripts: list[str] = []
    for part in primary_command.split(";"):
        token = part.strip().split(" ", 1)[0]
        if token.endswith(".py"):
            scripts.append(token)
    return scripts


def missing_command_scripts(closure: list[dict[str, str]], project_root: Path) -> list[str]:
    missing: list[str] = []
    script_root = project_root / "work" / "agent_memory_experiment"
    for closure_row in closure:
        for script in command_scripts(closure_row.get("primary_command", "")):
            if not (script_root / script).exists():
                missing.append(f"{closure_row.get('blocker_group', 'unknown')}:{script}")
    return missing


def readiness_blocker_gates(readiness: list[dict[str, str]]) -> set[str]:
    return {
        row.get("gate", "")
        for row in readiness
        if row.get("required_for_submission", row.get("required")) == "True"
        and row.get("status") == "blocker"
    }


def closure_blocker_groups(closure: list[dict[str, str]]) -> set[str]:
    return {row.get("blocker_group", "") for row in closure}


def covered_readiness_blockers(closure: list[dict[str, str]]) -> set[str]:
    groups = closure_blocker_groups(closure)
    covered = set(groups)
    if "external_embedding_preflight" in groups:
        covered.add("api_embedding_preflight")
    if "priority20_human_audit" in groups or "full80_human_audit" in groups:
        covered.add("reviewer_risk_blockers")
    if "external_embedding_completed" in groups:
        covered.add("reviewer_risk_blockers")
    return covered


def build_rows(outputs: Path, project_root: Path) -> list[dict[str, Any]]:
    closure_csv = outputs / "agent_memory_submission_blocker_closure_plan.csv"
    closure_md = outputs / "agent_memory_submission_blocker_closure_plan_zh.md"
    checklist_csv = outputs / "agent_memory_final_submission_checklist.csv"
    checklist_md = outputs / "agent_memory_final_submission_checklist_zh.md"
    readiness_csv = outputs / "agent_memory_submission_readiness.csv"
    gap_csv = outputs / "agent_memory_submission_gap_analysis.csv"
    reviewer_csv = outputs / "agent_memory_reviewer_response_prep.csv"
    acceptance_csv = outputs / "agent_memory_api_embedding_paper_acceptance.csv"
    postrun_csv = outputs / "agent_memory_api_embedding_postrun_gate.csv"

    closure = read_csv(closure_csv)
    checklist = read_csv(checklist_csv)
    readiness = read_csv(readiness_csv)
    gap = read_csv(gap_csv)
    reviewer = read_csv(reviewer_csv)
    acceptance = read_csv(acceptance_csv)
    postrun = read_csv(postrun_csv)

    closure_external = lookup(closure, blocker_group="external_embedding_completed")
    checklist_external = lookup(checklist, item="External embedding paper-ready baseline")
    readiness_external = lookup(readiness, gate="external_embedding_completed")
    reviewer_blockers = sum(1 for r in reviewer if r.get("risk") == "blocker" or r.get("risk_level") == "blocker")
    gap_blockers = sum(1 for r in gap if r.get("risk_level") == "blocker")
    accepted = sum(1 for r in acceptance if r.get("paper_acceptance_pass") == "True")
    postrun_pass = sum(1 for r in postrun if r.get("postrun_pass") == "True")
    missing_scripts = missing_command_scripts(closure, project_root)
    blocker_gates = readiness_blocker_gates(readiness)
    uncovered_blockers = sorted(blocker_gates - covered_readiness_blockers(closure))
    runbook_refs_ok, runbook_refs_evidence = checklist_runbook_refs_exist_and_are_executable(checklist, outputs)

    return [
        row(
            "closure_plan_exists",
            closure_csv.exists() and closure_md.exists() and len(closure) >= 6,
            "blocker",
            f"csv_exists={closure_csv.exists()}, md_exists={closure_md.exists()}, rows={len(closure)}",
            "Regenerate the submission blocker closure plan.",
        ),
        row(
            "closure_primary_commands_exist",
            len(missing_scripts) == 0,
            "blocker",
            "all closure primary command scripts exist" if not missing_scripts else "; ".join(missing_scripts),
            "Update closure primary_command entries to reference existing scripts under work/agent_memory_experiment.",
        ),
        row(
            "closure_covers_readiness_blockers",
            len(uncovered_blockers) == 0,
            "blocker",
            f"readiness_blockers={sorted(blocker_gates)}, uncovered={uncovered_blockers}",
            "Add a closure-plan row for every required readiness blocker, or document its dependency on another closure row.",
        ),
        row(
            "closure_external_requires_paper_acceptance",
            "validate_api_embedding_paper_acceptance.py" in closure_external.get("primary_command", "")
            and "paper_acceptance_pass=1" in closure_external.get("acceptance_criterion", ""),
            "blocker",
            f"primary_command={closure_external.get('primary_command', '')}; acceptance={closure_external.get('acceptance_criterion', '')}",
            "Update external embedding closure step to require strict paper acceptance, not only summary/compare files.",
        ),
        row(
            "closure_diagram_mentions_acceptance",
            text_contains(closure_md, "Postrun + paper acceptance pass"),
            "major",
            "diagram token present" if text_contains(closure_md, "Postrun + paper acceptance pass") else "diagram token missing",
            "Update the closure dependency diagram to include postrun and paper acceptance before reviewer-risk closure.",
        ),
        row(
            "final_checklist_mentions_paper_acceptance",
            "paper_acceptance_pass=" in checklist_external.get("evidence", "") and text_contains(checklist_md, "paper_acceptance_pass"),
            "blocker",
            f"checklist_evidence={checklist_external.get('evidence', '')}",
            "Regenerate final submission checklist after strict API embedding acceptance changes.",
        ),
        row(
            "final_checklist_runbook_refs_exist",
            runbook_refs_ok,
            "blocker",
            runbook_refs_evidence,
            "Update final checklist next actions to reference executable API, human-audit, and closure runbooks.",
        ),
        row(
            "submission_readiness_mentions_paper_acceptance",
            "paper_acceptance_pass=" in readiness_external.get("evidence", ""),
            "blocker",
            f"readiness_evidence={readiness_external.get('evidence', '')}",
            "Regenerate submission readiness after strict API embedding acceptance changes.",
        ),
        row(
            "acceptance_and_postrun_counts_aligned",
            accepted <= postrun_pass,
            "major",
            f"accepted={accepted}, postrun_pass={postrun_pass}",
            "A provider should not be accepted for paper unless its postrun gate also passes.",
        ),
        row(
            "reviewer_blocker_counts_consistent",
            reviewer_blockers == 0 or reviewer_blockers == gap_blockers,
            "major",
            f"reviewer_blockers={reviewer_blockers}, gap_blockers={gap_blockers}",
            "Regenerate reviewer response prep and submission gap analysis from the same blocker state.",
        ),
    ]


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    blockers = [r for r in rows if r["status"] == "blocker"]
    major = [r for r in rows if r["status"] == "major"]
    table = [[r["check"], str(r["pass"]), r["status"], r["evidence"], r["action"]] for r in rows]
    lines = [
        "# Submission Closure Consistency Audit",
        "",
        "本文件检查 blocker closure plan、final checklist、submission readiness、reviewer prep 和 API embedding acceptance 是否使用同一套投稿前验收标准。它用于防止某个计划文档落后于最新门禁，尤其是外部 embedding baseline 的 strict paper acceptance。",
        "",
        "## 总览",
        "",
        f"- Checks: {len(rows)}",
        f"- Blockers: {len(blockers)}",
        f"- Major issues: {len(major)}",
        f"- Closure artifacts consistent: {len(blockers) == 0 and len(major) == 0}",
        "",
        "## 明细",
        "",
        markdown_table(["Check", "Pass", "Status", "Evidence", "Action"], table),
        "",
        "## 使用边界",
        "",
        "- 可以写：投稿前 blocker 收口计划与当前 strict acceptance / final checklist / readiness gate 保持一致。",
        "- 不能写：一致性通过就代表 blocker 已解除；它只证明收口文档没有过期或互相矛盾。",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate submission closure artifact consistency.")
    parser.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_submission_closure_consistency.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_submission_closure_consistency_zh.md"))
    args = parser.parse_args()

    rows = build_rows(args.outputs_dir, args.project_root)
    write_csv(args.output_csv, rows)
    write_report(args.output_report, rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "checks": len(rows),
        "blockers": sum(1 for r in rows if r["status"] == "blocker"),
        "major": sum(1 for r in rows if r["status"] == "major"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
