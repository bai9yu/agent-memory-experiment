#!/usr/bin/env python3
"""Generate offline HTML interfaces for blinded human-audit annotation."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


HUMAN_FIELDS = [
    "human_manual_reason",
    "human_auto_reason_correct",
    "human_top_memory_relevant",
    "human_gold_memory_sufficient",
    "human_auditor_notes",
]

AUTO_REASON_OPTIONS = [
    "memory_type_mismatch",
    "time_mismatch",
    "entity_mismatch",
    "under_specific",
    "multi_evidence_missing",
    "retrieval_noise",
    "query_ambiguous",
    "other",
]

YES_PARTIAL_NO = ["yes", "partial", "no"]
YES_NO_UNCLEAR = ["yes", "no", "unclear"]


def read_csv(path: Path) -> list[dict[str, str]]:
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


def escape_json(rows: list[dict[str, str]]) -> str:
    return json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")


def select_options(options: list[str]) -> str:
    parts = ['<option value=""></option>']
    parts.extend(f'<option value="{html.escape(option)}">{html.escape(option)}</option>' for option in options)
    return "\n".join(parts)


def render_html(title: str, rows: list[dict[str, str]], source_csv: Path, output_filename: str) -> str:
    data = escape_json(rows)
    auto_reason = select_options(AUTO_REASON_OPTIONS)
    yes_partial_no = select_options(YES_PARTIAL_NO)
    yes_no_unclear = select_options(YES_NO_UNCLEAR)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1f2933;
      --muted: #5f6b7a;
      --line: #d8dee8;
      --panel: #f7f8fb;
      --accent: #1f6feb;
      --ok: #0a7f45;
      --warn: #a15c00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: #ffffff;
    }}
    header {{
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      gap: 16px;
      align-items: center;
      justify-content: space-between;
      padding: 14px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.96);
    }}
    h1 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.25;
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 4px;
    }}
    .controls {{
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    button {{
      min-height: 36px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 6px;
      padding: 8px 12px;
      font-weight: 600;
      cursor: pointer;
    }}
    button.primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #fff;
    }}
    main {{
      max-width: 1180px;
      margin: 0 auto;
      padding: 18px;
    }}
    .progress {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 8px;
      margin-bottom: 16px;
    }}
    .metric {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 10px 12px;
    }}
    .metric strong {{
      display: block;
      font-size: 20px;
      margin-bottom: 2px;
    }}
    .metric span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .item {{
      border-top: 1px solid var(--line);
      padding: 18px 0;
    }}
    .item:first-of-type {{
      border-top: 0;
    }}
    .item-title {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .badge {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 3px 8px;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 12px;
    }}
    .box {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      min-height: 118px;
    }}
    .label {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      margin-bottom: 6px;
    }}
    .text {{
      white-space: pre-wrap;
      line-height: 1.5;
    }}
    .form {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
      align-items: end;
    }}
    label {{
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    select, input, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      min-height: 34px;
      padding: 7px 8px;
      font: inherit;
      color: var(--ink);
      background: #fff;
    }}
    textarea {{
      min-height: 72px;
      resize: vertical;
    }}
    .wide {{
      grid-column: span 2;
    }}
    .complete .item-title h2::after {{
      content: "已填";
      margin-left: 8px;
      color: var(--ok);
      font-size: 12px;
    }}
    .incomplete .item-title h2::after {{
      content: "待填";
      margin-left: 8px;
      color: var(--warn);
      font-size: 12px;
    }}
    h2 {{
      margin: 0;
      font-size: 16px;
    }}
    @media (max-width: 860px) {{
      header {{ align-items: flex-start; flex-direction: column; }}
      .controls {{ justify-content: flex-start; }}
      .progress {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .grid, .form {{ grid-template-columns: 1fr; }}
      .wide {{ grid-column: auto; }}
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{html.escape(title)}</h1>
      <div class="meta">源文件：{html.escape(str(source_csv))} · 样本数：{len(rows)}</div>
    </div>
    <div class="controls">
      <button type="button" onclick="showIncomplete()">跳到下一条待填</button>
      <button type="button" class="primary" onclick="downloadCsv()">导出 CSV</button>
    </div>
  </header>
  <main>
    <section class="progress">
      <div class="metric"><strong id="doneCount">0</strong><span>已完成</span></div>
      <div class="metric"><strong id="totalCount">{len(rows)}</strong><span>总样本</span></div>
      <div class="metric"><strong id="missingCount">{len(rows)}</strong><span>待填写</span></div>
      <div class="metric"><strong id="percentDone">0%</strong><span>完成度</span></div>
    </section>
    <section id="items"></section>
  </main>
  <script>
    const rows = {data};
    const outputFilename = {json.dumps(output_filename)};
    const humanFields = {json.dumps(HUMAN_FIELDS)};

    function cell(value) {{
      return String(value ?? "");
    }}

    function isComplete(row) {{
      return humanFields.every((field) => cell(row[field]).trim().length > 0);
    }}

    function escapeHtml(value) {{
      return cell(value).replace(/[&<>"']/g, (ch) => ({{
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\\"": "&quot;",
        "'": "&#39;"
      }}[ch]));
    }}

    function fieldId(rowIndex, field) {{
      return `row_${{rowIndex}}_${{field}}`;
    }}

    function renderItems() {{
      const items = document.getElementById("items");
      items.innerHTML = rows.map((row, idx) => `
        <article class="item ${{isComplete(row) ? "complete" : "incomplete"}}" id="item_${{idx}}">
          <div class="item-title">
            <h2>#${{escapeHtml(row.review_order)}} · ${{escapeHtml(row.audit_id)}} · ${{escapeHtml(row.query_id)}}</h2>
            <div>
              <span class="badge">query type ${{escapeHtml(row.query_type)}}</span>
              <span class="badge">first rank ${{escapeHtml(row.first_rank)}}</span>
              <span class="badge">auto ${{escapeHtml(row.auto_reason)}}</span>
            </div>
          </div>
          <div class="grid">
            <div class="box">
              <div class="label">Query</div>
              <div class="text">${{escapeHtml(row.query)}}</div>
            </div>
            <div class="box">
              <div class="label">Top Memory · ${{escapeHtml(row.top_memory_id)}} · ${{escapeHtml(row.top_memory_type)}}</div>
              <div class="text">${{escapeHtml(row.top_memory_text)}}</div>
            </div>
            <div class="box">
              <div class="label">Gold Memory · ${{escapeHtml(row.gold_memory_ids)}} · ${{escapeHtml(row.gold_memory_types)}}</div>
              <div class="text">${{escapeHtml(row.gold_memory_texts)}}</div>
            </div>
            <div class="box">
              <div class="label">Human Labels</div>
              <div class="form">
                <label>Manual reason
                  <select id="${{fieldId(idx, "human_manual_reason")}}" onchange="updateField(${{idx}}, 'human_manual_reason', this.value)">
                    {auto_reason}
                  </select>
                </label>
                <label>Auto reason correct
                  <select id="${{fieldId(idx, "human_auto_reason_correct")}}" onchange="updateField(${{idx}}, 'human_auto_reason_correct', this.value)">
                    {yes_partial_no}
                  </select>
                </label>
                <label>Top memory relevant
                  <select id="${{fieldId(idx, "human_top_memory_relevant")}}" onchange="updateField(${{idx}}, 'human_top_memory_relevant', this.value)">
                    {yes_partial_no}
                  </select>
                </label>
                <label>Gold memory sufficient
                  <select id="${{fieldId(idx, "human_gold_memory_sufficient")}}" onchange="updateField(${{idx}}, 'human_gold_memory_sufficient', this.value)">
                    {yes_no_unclear}
                  </select>
                </label>
                <label class="wide">Auditor notes
                  <textarea id="${{fieldId(idx, "human_auditor_notes")}}" oninput="updateField(${{idx}}, 'human_auditor_notes', this.value)"></textarea>
                </label>
              </div>
            </div>
          </div>
        </article>
      `).join("");
      rows.forEach((row, idx) => {{
        humanFields.forEach((field) => {{
          const element = document.getElementById(fieldId(idx, field));
          if (element) element.value = cell(row[field]);
        }});
      }});
      updateProgress();
    }}

    function updateField(index, field, value) {{
      rows[index][field] = value;
      const item = document.getElementById(`item_${{index}}`);
      item.classList.toggle("complete", isComplete(rows[index]));
      item.classList.toggle("incomplete", !isComplete(rows[index]));
      updateProgress();
    }}

    function updateProgress() {{
      const done = rows.filter(isComplete).length;
      const total = rows.length;
      document.getElementById("doneCount").textContent = done;
      document.getElementById("missingCount").textContent = total - done;
      document.getElementById("percentDone").textContent = total ? `${{Math.round(done / total * 100)}}%` : "0%";
    }}

    function showIncomplete() {{
      const index = rows.findIndex((row) => !isComplete(row));
      const target = document.getElementById(`item_${{index < 0 ? 0 : index}}`);
      if (target) target.scrollIntoView({{behavior: "smooth", block: "start"}});
    }}

    function csvEscape(value) {{
      const text = cell(value);
      return /[",\\n\\r]/.test(text) ? `"${{text.replace(/"/g, '""')}}"` : text;
    }}

    function downloadCsv() {{
      const headers = Object.keys(rows[0] || {{}});
      const csv = [headers.join(","), ...rows.map((row) => headers.map((h) => csvEscape(row[h])).join(","))].join("\\n");
      const blob = new Blob([csv], {{type: "text/csv;charset=utf-8"}});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = outputFilename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }}

    renderItems();
  </script>
</body>
</html>
"""


def count_complete(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if all((row.get(field) or "").strip() for field in HUMAN_FIELDS))


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Human Audit Annotation Interface",
        "",
        "本文件记录已生成的离线人工标注界面。HTML 文件内嵌盲审样本，只展示人工判断需要的信息，不展示 LLM-assisted 预标注标签；标注者填写后可直接导出 CSV。",
        "",
        "## 总览",
        "",
        "| Split | Samples | Completed | Pending | HTML | Source CSV |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['split']} | {row['samples']} | {row['completed']} | {row['pending']} | "
            f"`{row['html']}` | `{row['source_csv']}` |"
        )
    lines.extend([
        "",
        "## 使用边界",
        "",
        "- 可以写：人工审计已有离线标注界面、盲审 CSV 和 codebook，标注流程可复现。",
        "- 不能写：HTML 生成完成就等于人工审计完成；最终仍以 exported CSV 回填后的 agreement/readiness gate 为准。",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate offline HTML annotation interfaces for human audit CSVs.")
    parser.add_argument("--priority-csv", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_blind_review.csv"))
    parser.add_argument("--full-csv", type=Path, default=Path("outputs/agent_memory_human_audit_full80_blind_review.csv"))
    parser.add_argument("--priority-html", type=Path, default=Path("outputs/agent_memory_human_audit_priority20_annotation.html"))
    parser.add_argument("--full-html", type=Path, default=Path("outputs/agent_memory_human_audit_full80_annotation.html"))
    parser.add_argument("--output-csv", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_interface.csv"))
    parser.add_argument("--output-report", type=Path, default=Path("outputs/agent_memory_human_audit_annotation_interface_zh.md"))
    args = parser.parse_args()

    configs = [
        ("priority20", args.priority_csv, args.priority_html, "agent_memory_human_audit_priority20_completed.csv"),
        ("full80", args.full_csv, args.full_html, "agent_memory_human_audit_full80_completed.csv"),
    ]
    summary_rows = []
    for split, source_csv, output_html, download_name in configs:
        rows = read_csv(source_csv)
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(
            render_html(f"Human Audit Annotation · {split}", rows, source_csv, download_name),
            encoding="utf-8",
        )
        completed = count_complete(rows)
        summary_rows.append({
            "split": split,
            "samples": len(rows),
            "completed": completed,
            "pending": len(rows) - completed,
            "html": str(output_html),
            "source_csv": str(source_csv),
        })

    write_csv(args.output_csv, summary_rows)
    write_report(args.output_report, summary_rows)
    print(json.dumps({
        "output_report": str(args.output_report),
        "output_csv": str(args.output_csv),
        "interfaces": len(summary_rows),
        "pending": sum(int(row["pending"]) for row in summary_rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
