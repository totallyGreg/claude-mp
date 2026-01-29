#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Assess control coverage gaps for a specific risk.

Usage:
    uv run scripts/cli_gap_analysis.py <risk-id> --implemented <control-ids> [--offline]

Examples:
    uv run scripts/cli_gap_analysis.py DP --implemented controlTrainingDataSanitization
    uv run scripts/cli_gap_analysis.py PIJ --implemented controlInputValidation controlOutputFiltering --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Assess control gaps for a risk")
    parser.add_argument("risk_id", help="Risk identifier (e.g., DP, PIJ)")
    parser.add_argument(
        "--implemented",
        nargs="+",
        default=[],
        help="List of implemented control IDs",
    )
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    gap = analyzer.assess_risk_gap(args.risk_id, args.implemented)

    if "error" in gap:
        print(f"Error: {gap['error']}", file=sys.stderr)
        print(f"Available risks: {', '.join(analyzer.get_risk_ids())}")
        sys.exit(1)

    print(f"Gap Analysis: [{gap['risk_id']}] {gap['risk_title']}")
    print()
    print(f"Coverage: {gap['coverage_percentage']}% ({gap['implemented_count']} of {gap['applicable_controls']} controls)")
    print()

    if gap["implemented_controls"]:
        print("Implemented Controls:")
        for control in gap["implemented_controls"]:
            print(f"  ✓ [{control.id}] {control.title}")
        print()

    if gap["missing_controls"]:
        print("Missing Controls:")
        for control in gap["missing_controls"]:
            print(f"  ✗ [{control.id}] {control.title}")
        print()

        print("Recommendations:")
        for i, control in enumerate(gap["missing_controls"][:3], 1):
            print(f"  Priority {i}: Implement {control.title}")
    else:
        print("All applicable controls are implemented!")


if __name__ == "__main__":
    main()
