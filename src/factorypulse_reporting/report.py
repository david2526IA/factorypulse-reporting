"""Create a portable HTML report from FactoryPulse artifacts."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import duckdb


def _anomalies(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _recommendations(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _table(rows: list[list[str]], headers: list[str]) -> str:
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build_report(warehouse: Path, anomalies_path: Path, output: Path, recommendations_path: Path | None = None) -> dict[str, int]:
    """Write a self-contained report and return its transparent metric summary."""
    conn = duckdb.connect(str(warehouse), read_only=True)
    try:
        readings = int(conn.execute("select count(*) from telemetry_silver").fetchone()[0])
        assets = int(conn.execute("select count(distinct asset_id) from telemetry_silver").fetchone()[0])
        latest = conn.execute(
            "select asset_id, max(occurred_at) from telemetry_silver group by asset_id order by asset_id"
        ).fetchall()
    finally:
        conn.close()
    anomalies = _anomalies(anomalies_path)
    recommendations = _recommendations(recommendations_path)
    critical = sum(event.get("severity") == "critical" for event in anomalies)
    latest_rows = [[str(asset), str(timestamp)] for asset, timestamp in latest]
    anomaly_rows = [
        [str(event.get("asset_id")), str(event.get("severity")), "; ".join(event.get("reasons", []))]
        for event in anomalies
    ] or [["—", "—", "No anomaly events supplied"]]
    recommendation_rows = [
        [str(item.get("asset_id")), str(item.get("priority")), str(item.get("action")), str(item.get("status"))]
        for item in recommendations
    ] or [["—", "—", "No maintenance recommendations supplied", "—"]]
    metrics = {"readings": readings, "assets": assets, "anomalies": len(anomalies), "critical": critical, "recommendations": len(recommendations)}
    cards = "".join(f"<article><strong>{value}</strong><span>{label}</span></article>" for label, value in metrics.items())
    page = f"""<!doctype html>
<html lang=\"en\"><meta charset=\"utf-8\"><title>FactoryPulse operational report</title>
<style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;color:#17212b}}h1{{margin-bottom:4px}}.muted{{color:#526273}}.cards{{display:flex;gap:12px;flex-wrap:wrap}}article{{padding:18px;border:1px solid #d6dde5;border-radius:10px;min-width:110px}}article strong{{font-size:2rem;display:block}}article span{{text-transform:capitalize;color:#526273}}table{{border-collapse:collapse;width:100%;margin:14px 0 30px}}th,td{{text-align:left;border-bottom:1px solid #d6dde5;padding:10px;vertical-align:top}}th{{background:#f4f7fa}}footer{{border-top:1px solid #d6dde5;padding-top:12px;color:#526273;font-size:.9rem}}</style>
<body><h1>FactoryPulse operational report</h1><p class=\"muted\">Static, evidence-linked summary. It does not command equipment or replace qualified operational judgement.</p>
<section class=\"cards\">{cards}</section><h2>Telemetry coverage</h2>{_table(latest_rows, ['Asset', 'Latest reading'])}
<h2>Anomaly evidence</h2>{_table(anomaly_rows, ['Asset', 'Severity', 'Reasons'])}
<h2>Maintenance proposals</h2>{_table(recommendation_rows, ['Asset', 'Priority', 'Proposed action', 'Status'])}
<footer>Sources: FactoryPulse lakehouse, anomaly stream and optional maintenance planner output. Generated locally.</footer></body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    return metrics
