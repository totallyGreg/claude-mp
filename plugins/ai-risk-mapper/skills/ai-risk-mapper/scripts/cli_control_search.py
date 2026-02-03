#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Search CoSAI controls by keyword.

Usage:
    uv run scripts/cli_control_search.py <query> [--offline]

Examples:
    uv run scripts/cli_control_search.py "training"
    uv run scripts/cli_control_search.py validation --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Search CoSAI controls by keyword")
    parser.add_argument("query", help="Search term")
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    controls = analyzer.search_controls(args.query)

    if not controls:
        print(f"No controls found matching '{args.query}'")
        sys.exit(0)

    print(f"Found {len(controls)} matching controls:\n")
    for control in controls:
        print(f"[{control.id}] {control.title}")
        print(f"  Category: {control.category}")
        print(f"  Personas: {', '.join(control.personas)}")
        print(f"  Risks mitigated: {', '.join(control.risks[:5])}")
        if len(control.risks) > 5:
            print(f"                   ...and {len(control.risks) - 5} more")
        desc = control.description[:150] + "..." if len(control.description) > 150 else control.description
        print(f"  Description: {desc.strip()}")
        print()


if __name__ == "__main__":
    main()
