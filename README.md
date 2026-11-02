# FactoryPulse Reporting

Generate a portable HTML operational report from FactoryPulse warehouse data, anomaly events and optional maintenance proposals.

The report is deliberately static and source-linked: it provides evidence for a conversation, not a live control interface or automated operational decision.

## Quick start

```bash
pip install .
factorypulse-report \
  --warehouse api-data/warehouse.duckdb \
  --anomalies api-data/anomalies.jsonl \
  --recommendations maintenance_recommendations.json \
  --output factorypulse_report.html
```

Open the generated file in any browser. It includes telemetry coverage, anomaly evidence and proposed maintenance actions.

## Design choices

- No external service, credentials or telemetry upload is required.
- Input is read-only; the warehouse is opened in DuckDB read-only mode.
- The report labels recommendations as proposals and describes its operational limits.

## Development

```bash
pip install ".[dev]"
pytest -q
```

## License

MIT
