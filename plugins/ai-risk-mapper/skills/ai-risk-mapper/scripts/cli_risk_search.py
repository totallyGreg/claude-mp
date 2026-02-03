#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Search CoSAI risks by keyword.

Usage:
    uv run scripts/cli_risk_search.py <query> [--offline]

Examples:
    uv run scripts/cli_risk_search.py "data poisoning"
    uv run scripts/cli_risk_search.py injection --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Search CoSAI risks by keyword")
    parser.add_argument("query", help="Search term")
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    risks = analyzer.search_risks(args.query)

    if not risks:
        print(f"No risks found matching '{args.query}'")
        sys.exit(0)

    print(f"Found {len(risks)} matching risks:\n")
    for risk in risks:
        print(f"[{risk.id}] {risk.title}")
        print(f"  Category: {risk.category}")
        print(f"  Personas: {', '.join(risk.personas)}")
        print(f"  Controls: {len(risk.controls)}")
        desc = risk.short_description[:150] + "..." if len(risk.short_description) > 150 else risk.short_description
        print(f"  Description: {desc.strip()}")
        print()


if __name__ == "__main__":
    main()
