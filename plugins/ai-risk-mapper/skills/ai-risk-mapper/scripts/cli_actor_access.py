#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml>=6.0.1"]
# ///
"""
Show risks by threat actor access level.

Usage:
    uv run scripts/cli_actor_access.py [access-level] [--offline] [--list]

Examples:
    uv run scripts/cli_actor_access.py --list
    uv run scripts/cli_actor_access.py agent
    uv run scripts/cli_actor_access.py supply-chain --offline
"""

import argparse
import sys
from pathlib import Path

import yaml

from core_analyzer import RiskAnalyzer

VALID_LEVELS = [
    "external", "api", "user", "privileged", "agent",
    "supply-chain", "infrastructure-provider", "service-provider", "physical",
]


def load_actor_access_definitions(yaml_dir: Path) -> list[dict]:
    """Load actor access level definitions from YAML."""
    aa_file = yaml_dir / "actor-access.yaml"
    if not aa_file.exists():
        return []
    with open(aa_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("actorAccessLevels", [])


def main():
    parser = argparse.ArgumentParser(
        description="Show risks by threat actor access level"
    )
    parser.add_argument(
        "access_level", nargs="?",
        help=f"Access level: {', '.join(VALID_LEVELS)}",
    )
    parser.add_argument("--offline", action="store_true", help="Use bundled schemas")
    parser.add_argument("--list", action="store_true", help="List all access levels")
    args = parser.parse_args()

    try:
        analyzer = RiskAnalyzer(offline=args.offline)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    levels = load_actor_access_definitions(analyzer.yaml_dir)

    if args.list or not args.access_level:
        print("Threat Actor Access Levels:\n")
        for level in levels:
            category = level.get("category", "")
            tag = "[AI-specific]" if category == "modern" else "[traditional]"
            print(f"  {level['id']:30s} {tag}")
            print(f"    {level.get('description', '')}")
            risk_count = len(analyzer.get_risks_by_actor_access(level["id"]))
            print(f"    Risks exploitable: {risk_count}")
            print()
        sys.exit(0)

    access_level = args.access_level
    if access_level not in VALID_LEVELS:
        print(f"Unknown access level: {access_level}", file=sys.stderr)
        print(f"Valid levels: {', '.join(VALID_LEVELS)}", file=sys.stderr)
        sys.exit(1)

    level_def = next((l for l in levels if l["id"] == access_level), None)
    if level_def:
        category = level_def.get("category", "")
        tag = "[AI-specific]" if category == "modern" else "[traditional]"
        print(f"Access Level: {level_def['title']} ({access_level}) {tag}")
        print(f"Description: {level_def.get('description', '')}\n")

    risks = analyzer.get_risks_by_actor_access(access_level)

    if not risks:
        print(f"No risks found for access level '{access_level}'")
        sys.exit(0)

    print(f"Risks exploitable at this access level: {len(risks)}\n")

    by_category: dict[str, list] = {}
    for risk in risks:
        cat = risk.category
        by_category.setdefault(cat, []).append(risk)

    for cat, cat_risks in sorted(by_category.items()):
        print(f"  {cat}:")
        for risk in cat_risks:
            other_levels = [l for l in risk.actor_access if l != access_level]
            also = f" (also: {', '.join(other_levels)})" if other_levels else ""
            print(f"    [{risk.id}] {risk.title}{also}")
        print()


if __name__ == "__main__":
    main()
