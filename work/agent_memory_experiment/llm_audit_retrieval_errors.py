#!/usr/bin/env python3
"""Use an LLM to create a reviewer draft for retrieval-error audit labels."""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from llm_memory_extractor import load_dotenv


SYSTEM_PROMPT = """You audit retrieval-error labels for an agent memory experiment.
Return strict JSON only. For each item, decide:
- manual_reason: best short error reason.
- auto_reason_correct: yes, partial, or no.
- top_memory_relevant: yes, partial, or no.
- gold_memory_sufficient: yes, no, or unclear.
- auditor_notes: one short sentence with the key reason.
Be conservative. If the top memory is related but not enough to answer, use partial.
"""

ALLOWED = {
    "auto_reason_correct": {"yes", "partial", "no"},
    "top_memory_relevant": {"yes", "partial", "no"},
    "gold_memory_sufficient": {"yes", "no", "unclear"},
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def chunked(rows: list[dict[str, str]], size: int) -> list[list[dict[str, str]]]:
    return [rows[i:i + size] for i in range(0, len(rows), size)]


def compact_item(row: dict[str, str]) -> dict[str, str]:
    return {
        "audit_id": row["audit_id"],
        "query": row["query"],
        "query_type": row["query_type"],
        "auto_reason": row["auto_reason"],
        "top_memory_type": row["top_memory_type"],
        "top_memory_text": row["top_memory_text"],
        "gold_memory_types": row["gold_memory_types"],
        "gold_memory_texts": row["gold_memory_texts"],
    }


def build_prompt(rows: list[dict[str, str]]) -> str:
    items = [compact_item(row) for row in rows]
    return "\n".join([
        "Audit the following retrieval errors.",
        "Return JSON in this exact shape:",
        '{"audits":[{"audit_id":"audit_001","manual_reason":"...","auto_reason_correct":"yes|partial|no","top_memory_relevant":"yes|partial|no","gold_memory_sufficient":"yes|no|unclear","auditor_notes":"..."}]}',
        "",
        json.dumps(items, ensure_ascii=False, indent=2),
    ])


def call_chat(
    prompt: str,
    model: str,
    base_url: str,
    api_key: str,
    temperature: float,
    timeout: int,
    retries: int,
    retry_sleep: float,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    payload = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            if exc.code != 429 and exc.code < 500:
                raise RuntimeError(f"DeepSeek API error {exc.code}: {message}") from exc
            if attempt >= retries:
                raise RuntimeError(f"DeepSeek API error {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            if attempt >= retries:
                raise RuntimeError(f"DeepSeek API network error after {retries + 1} attempts: {exc}") from exc
        time.sleep(retry_sleep * (attempt + 1))
    if payload is None:
        raise RuntimeError("DeepSeek API returned no payload.")
    content = payload["choices"][0]["message"]["content"]
    data = json.loads(content)
    if not isinstance(data, dict) or not isinstance(data.get("audits"), list):
        raise RuntimeError("LLM audit response must be a JSON object with an audits list.")
    return {"data": data, "usage": payload.get("usage", {})}


def normalize_label(value: Any, allowed: set[str], default: str) -> str:
    text = str(value or "").strip().lower()
    return text if text in allowed else default


def merge_labels(rows: list[dict[str, str]], labels: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for row in rows:
        label = labels.get(row["audit_id"], {})
        merged = dict(row)
        merged["manual_reason"] = str(label.get("manual_reason") or row["auto_reason"]).strip() or row["auto_reason"]
        merged["auto_reason_correct"] = normalize_label(label.get("auto_reason_correct"), ALLOWED["auto_reason_correct"], "partial")
        merged["top_memory_relevant"] = normalize_label(label.get("top_memory_relevant"), ALLOWED["top_memory_relevant"], "partial")
        merged["gold_memory_sufficient"] = normalize_label(label.get("gold_memory_sufficient"), ALLOWED["gold_memory_sufficient"], "unclear")
        note = str(label.get("auditor_notes") or "").strip()
        merged["auditor_notes"] = f"llm_assisted: {note}" if note else "llm_assisted"
        out.append(merged)
    return out


def write_report(path: Path, rows: list[dict[str, str]], usage_rows: list[dict[str, Any]]) -> None:
    total_tokens = sum(int(row["total_tokens"]) for row in usage_rows)
    correct = {"yes": 0, "partial": 0, "no": 0}
    for row in rows:
        correct[row["auto_reason_correct"]] = correct.get(row["auto_reason_correct"], 0) + 1
    lines = [
        "# LLM-assisted 错误复核初稿",
        "",
        "本文件使用 DeepSeek 对人工复核样本生成第一版标注。它不是人工标注结果，适合作为人工复核前的预标注和一致性检查材料。",
        "",
        "## 总览",
        "",
        f"- 样本数：{len(rows)}",
        f"- API 批次：{len(usage_rows)}",
        f"- API total tokens：{total_tokens}",
        "",
        "## auto_reason_correct 初稿分布",
        "",
        "| Label | Count |",
        "|---|---:|",
    ]
    for label in ("yes", "partial", "no"):
        lines.append(f"| {label} | {correct.get(label, 0)} |")
    lines.extend([
        "",
        "## 论文使用判断",
        "",
        "- 可以把该文件作为人工复核加速材料或附录中的 LLM-assisted audit protocol。",
        "- 不能把它直接写成 human audit；最终论文仍应由人工确认或至少抽样复查这些预标注。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LLM-assisted audit labels for retrieval errors.")
    parser.add_argument("--audit-csv", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-usage", type=Path, required=True)
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    args = parser.parse_args()

    load_dotenv(args.env_file)
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    if not api_key:
        raise SystemExit("DEEPSEEK_API_KEY is missing. Put it in .env or the environment.")

    rows = read_csv(args.audit_csv)
    labels: dict[str, dict[str, Any]] = {}
    usage_rows = []
    for batch_idx, batch in enumerate(chunked(rows, args.batch_size), start=1):
        result = call_chat(
            build_prompt(batch),
            model,
            base_url,
            api_key,
            args.temperature,
            args.timeout,
            args.retries,
            args.retry_sleep,
        )
        for item in result["data"]["audits"]:
            if isinstance(item, dict) and item.get("audit_id"):
                labels[str(item["audit_id"])] = item
        usage = result["usage"]
        usage_rows.append({
            "batch_idx": batch_idx,
            "items": len(batch),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        })

    missing = [row["audit_id"] for row in rows if row["audit_id"] not in labels]
    if missing:
        raise RuntimeError(f"Missing LLM audit labels for {len(missing)} rows: {missing[:5]}")
    merged = merge_labels(rows, labels)
    write_csv(args.output_csv, merged, list(rows[0].keys()))
    write_csv(args.output_usage, usage_rows, list(usage_rows[0].keys()))
    write_report(args.output_report, merged, usage_rows)
    print(json.dumps({
        "output_csv": str(args.output_csv),
        "output_report": str(args.output_report),
        "samples": len(merged),
        "batches": len(usage_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
