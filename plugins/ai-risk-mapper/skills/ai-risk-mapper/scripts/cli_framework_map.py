#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Get framework mappings for a risk.

Usage:
    uv run scripts/cli_framework_map.py <risk-id> [--framework <name>] [--offline]

Examples:
    uv run scripts/cli_framework_map.py PIJ
    uv run scripts/cli_framework_map.py DP --framework mitre-atlas
    uv run scripts/cli_framework_map.py SDD --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


FRAMEWORKS = ["mitre-atlas", "nist-ai-rmf", "stride", "owasp-llm", "iso-22989"]


def main():
    parser = argparse.ArgumentParser(description="Get framework mappings for a risk")
    parser.add_argument("risk_id", help="Risk identifier (e.g., DP, PIJ)")
    parser.add_argument("--framework", choices=FRAMEWORKS, help="Filter by framework")
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

    print(f"Risk: [{risk.id}] {risk.title}")
    print()

    if args.framework:
        mappings = analyzer.get_framework_mappings(args.risk_id, args.framework)
        print(f"{args.framework.upper()} Mappings:")
        if mappings:
            for m in mappings:
                print(f"  - {m}")
        else:
            print("  (none)")
    else:
        all_mappings = analyzer.get_all_framework_mappings(args.risk_id)
        print("All Framework Mappings:")
        if all_mappings:
            for framework, refs in all_mappings.items():
                if refs:
                    refs_str = ", ".join(str(r) for r in refs) if isinstance(refs, list) else str(refs)
                    print(f"  {framework}: {refs_str}")
        else:
            print("  (no mappings available)")


if __name__ == "__main__":
    main()
