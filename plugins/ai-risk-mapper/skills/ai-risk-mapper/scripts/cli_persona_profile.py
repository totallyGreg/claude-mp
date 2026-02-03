#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Get complete risk profile for a persona.

Usage:
    uv run scripts/cli_persona_profile.py <persona-id> [--offline]

Examples:
    uv run scripts/cli_persona_profile.py personaModelCreator
    uv run scripts/cli_persona_profile.py personaModelConsumer --offline
"""

import argparse
import sys
from core_analyzer import RiskAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Get persona risk profile")
    parser.add_argument("persona_id", help="Persona identifier")
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    profile = analyzer.get_persona_risk_profile(args.persona_id)

    if "error" in profile:
        print(f"Error: {profile['error']}", file=sys.stderr)
        print(f"Available personas: {', '.join(analyzer.get_persona_ids())}")
        sys.exit(1)

    print(f"Persona: {profile['persona_title']}")
    print(f"Description: {profile['description'][:200]}...")
    print()

    if profile.get("responsibilities"):
        print("Responsibilities:")
        for resp in profile["responsibilities"]:
            print(f"  - {resp}")
        print()

    print(f"Relevant Risks: {profile['risks_count']}")
    if profile.get("risks_by_category"):
        for category, risks in profile["risks_by_category"].items():
            risk_ids = ", ".join(r.id for r in risks)
            print(f"  {category}: {risk_ids}")
    print()

    print(f"Relevant Controls: {profile['controls_count']}")
    for control in profile["controls"][:5]:
        print(f"  - [{control.id}] {control.title}")
    if profile["controls_count"] > 5:
        print(f"  ... and {profile['controls_count'] - 5} more")


if __name__ == "__main__":
    main()
