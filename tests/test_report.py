import json

import duckdb

from factorypulse_reporting.report import build_report


def test_report_contains_evidence_and_safe_scope(tmp_path) -> None:
    warehouse = tmp_path / "warehouse.duckdb"
    conn = duckdb.connect(str(warehouse))
    conn.execute("create table telemetry_silver (asset_id varchar, occurred_at timestamp)")
    conn.execute("insert into telemetry_silver values ('PUMP-01', '2026-01-01 12:00:00')")
    conn.close()
    anomalies = tmp_path / "anomalies.jsonl"
    anomalies.write_text(json.dumps({"asset_id": "PUMP-01", "severity": "critical", "reasons": ["vibration critical"]}) + "\n")
    recommendations = tmp_path / "recommendations.json"
    recommendations.write_text(json.dumps([{"asset_id": "PUMP-01", "priority": "P1", "action": "Inspect bearing", "status": "proposed"}]))
    output = tmp_path / "report.html"
    metrics = build_report(warehouse, anomalies, output, recommendations)
    page = output.read_text()
    assert metrics == {"readings": 1, "assets": 1, "anomalies": 1, "critical": 1, "recommendations": 1}
    assert "Inspect bearing" in page
    assert "does not command equipment" in page
