#!/usr/bin/env python3
"""Generate a self-contained HTML visualization for memory experiment results."""

from __future__ import annotations

import argparse
import csv
import html
import re
from pathlib import Path


COLORS = {
    "vector": "#4c78a8",
    "hybrid": "#f58518",
    "time_aware": "#54a24b",
}


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_size(name: str) -> int:
    match = re.search(r"(\d+)$", name)
    return int(match.group(1)) if match else 10


def scale_points(values: list[tuple[int, float]], width: int, height: int, margin: int) -> list[tuple[float, float]]:
    xs = [x for x, _ in values]
    min_x, max_x = min(xs), max(xs)
    if min_x == max_x:
        min_x = 0
    points = []
    for x, y in values:
        px = margin + (x - min_x) / (max_x - min_x) * (width - 2 * margin)
        py = height - margin - y * (height - 2 * margin)
        points.append((px, py))
    return points


def line_chart(title: str, series: dict[str, list[tuple[int, float]]], y_label: str) -> str:
    width = 760
    height = 360
    margin = 56
    axis = f"""
      <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#333"/>
      <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#333"/>
      <text x="{width / 2}" y="{height - 10}" text-anchor="middle" font-size="13">Memory count</text>
      <text x="18" y="{height / 2}" transform="rotate(-90, 18, {height / 2})" text-anchor="middle" font-size="13">{html.escape(y_label)}</text>
    """
    ticks = []
    all_sizes = sorted({x for values in series.values() for x, _ in values})
    for size in all_sizes:
        px = scale_points([(size, 0)], width, height, margin)[0][0] if len(all_sizes) == 1 else (
            margin + (size - min(all_sizes)) / (max(all_sizes) - min(all_sizes)) * (width - 2 * margin)
        )
        ticks.append(f'<text x="{px:.1f}" y="{height - margin + 22}" text-anchor="middle" font-size="11">{size}</text>')
    for y in [0.0, 0.25, 0.5, 0.75, 1.0]:
        py = height - margin - y * (height - 2 * margin)
        ticks.append(f'<line x1="{margin - 4}" y1="{py:.1f}" x2="{margin}" y2="{py:.1f}" stroke="#333"/>')
        ticks.append(f'<text x="{margin - 10}" y="{py + 4:.1f}" text-anchor="end" font-size="11">{y:.2f}</text>')
        ticks.append(f'<line x1="{margin}" y1="{py:.1f}" x2="{width - margin}" y2="{py:.1f}" stroke="#eee"/>')

    plotted = []
    for method, values in sorted(series.items()):
        values = sorted(values)
        points = scale_points(values, width, height, margin)
        path = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        color = COLORS.get(method, "#777")
        plotted.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="3"/>')
        for (x, y), (_, raw_y) in zip(points, values):
            plotted.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
            plotted.append(f'<text x="{x:.1f}" y="{y - 9:.1f}" text-anchor="middle" font-size="10">{raw_y:.3f}</text>')

    legend_items = []
    for i, method in enumerate(sorted(series)):
        x = margin + i * 150
        y = margin - 24
        color = COLORS.get(method, "#777")
        legend_items.append(f'<rect x="{x}" y="{y - 10}" width="14" height="14" fill="{color}"/>')
        legend_items.append(f'<text x="{x + 20}" y="{y + 1}" font-size="12">{html.escape(method)}</text>')

    return f"""
    <section>
      <h2>{html.escape(title)}</h2>
      <svg viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">
        {''.join(ticks)}
        {axis}
        {''.join(plotted)}
        {''.join(legend_items)}
      </svg>
    </section>
    """


def build_overall_series(rows: list[dict], metric: str) -> dict[str, list[tuple[int, float]]]:
    series: dict[str, list[tuple[int, float]]] = {}
    for row in rows:
        series.setdefault(row["method"], []).append((run_size(row["run"]), float(row[metric])))
    return series


def build_temporal_series(result_dirs: list[Path], metric: str) -> dict[str, list[tuple[int, float]]]:
    series: dict[str, list[tuple[int, float]]] = {}
    for result_dir in result_dirs:
        rows = read_csv(result_dir / "summary_by_type.csv")
        size = run_size(result_dir.name)
        for row in rows:
            if row.get("query_type") == "temporal-update":
                series.setdefault(row["method"], []).append((size, float(row[metric])))
    return series


def write_html(trend_rows: list[dict], result_dirs: list[Path], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    overall = build_overall_series(trend_rows, "recall@1")
    temporal = build_temporal_series(result_dirs, "recall@1")
    mrr = build_overall_series(trend_rows, "mrr")

    table_rows = []
    for row in trend_rows:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(row['run'])}</td>"
            f"<td>{html.escape(row['method'])}</td>"
            f"<td>{float(row['recall@1']):.3f}</td>"
            f"<td>{float(row['recall@3']):.3f}</td>"
            f"<td>{float(row['recall@5']):.3f}</td>"
            f"<td>{float(row['mrr']):.3f}</td>"
            "</tr>"
        )

    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Agent Memory Experiment Visualization</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 32px; color: #202124; }}
    main {{ max-width: 980px; margin: 0 auto; }}
    h1 {{ font-size: 30px; margin-bottom: 8px; }}
    h2 {{ margin-top: 34px; }}
    .note {{ color: #555; line-height: 1.5; }}
    svg {{ width: 100%; height: auto; border: 1px solid #ddd; background: #fff; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 16px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px 10px; text-align: right; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    th {{ background: #f6f7f8; }}
  </style>
</head>
<body>
<main>
  <h1>Agent Memory Experiment Visualization</h1>
  <p class="note">Offline first-stage retrieval experiment. The main signal is that time-aware reranking keeps a clear advantage on temporal-update questions as memory count grows.</p>
  {line_chart("Overall Recall@1 Trend", overall, "Recall@1")}
  {line_chart("Temporal-Update Recall@1 Trend", temporal, "Recall@1")}
  {line_chart("Overall MRR Trend", mrr, "MRR")}
  <section>
    <h2>Overall Results Table</h2>
    <table>
      <thead><tr><th>Run</th><th>Method</th><th>Recall@1</th><th>Recall@3</th><th>Recall@5</th><th>MRR</th></tr></thead>
      <tbody>{''.join(table_rows)}</tbody>
    </table>
  </section>
</main>
</body>
</html>
"""
    output.write_text(doc, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an HTML visualization for experiment results.")
    parser.add_argument("--trend-csv", type=Path, default=Path("outputs/agent_memory_experiment_trends.csv"))
    parser.add_argument("--result-dirs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/agent_memory_experiment_visualization.html"))
    args = parser.parse_args()
    write_html(read_csv(args.trend_csv), args.result_dirs, args.output)
    print(str(args.output))


if __name__ == "__main__":
    main()
