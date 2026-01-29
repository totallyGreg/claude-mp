#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Get controls that mitigate a specific risk.

Usage:
    uv run scripts/cli_controls_for_risk.py <risk-id> [--offline]

Examples:
    uv run scripts/cli_controls_for_risk.py DP
    uv run scripts/cli_controls_for_risk.py PIJ --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Get controls for a risk")
    parser.add_argument("risk_id", help="Risk identifier (e.g., DP, PIJ)")
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    risk = analyzer.find_risk(args.risk_id)
    if not risk:
        print(f"Risk not found: {args.risk_id}", file=sys.stderr)
        print(f"Available risks: {', '.join(analyzer.get_risk_ids())}")
        sys.exit(1)

    controls = analyzer.get_controls_for_risk(args.risk_id)

    print(f"Risk: [{risk.id}] {risk.title}")
    print(f"Description: {risk.short_description.strip()[:200]}...")
    print(f"\n{len(controls)} controls mitigate this risk:\n")

    for i, control in enumerate(controls, 1):
        print(f"{i}. [{control.id}] {control.title}")
        desc = control.description[:200] + "..." if len(control.description) > 200 else control.description
        print(f"   Description: {desc.strip()}")
        if control.components:
            print(f"   Components: {', '.join(control.components[:3])}")
        print()


if __name__ == "__main__":
    main()
