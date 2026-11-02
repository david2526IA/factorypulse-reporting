from __future__ import annotations

import argparse
import json
from pathlib import Path

from .report import build_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a static FactoryPulse operational report.")
    parser.add_argument("--warehouse", type=Path, required=True)
    parser.add_argument("--anomalies", type=Path, required=True)
    parser.add_argument("--recommendations", type=Path)
    parser.add_argument("--output", type=Path, default=Path("factorypulse_report.html"))
    args = parser.parse_args()
    print(json.dumps(build_report(args.warehouse, args.anomalies, args.output, args.recommendations), sort_keys=True))
