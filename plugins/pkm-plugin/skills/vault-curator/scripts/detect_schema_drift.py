#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Detect schema drift across notes of a given fileClass or folder.

Scans notes sharing a fileClass (or in the same folder) and reports
inconsistencies: missing properties, type mismatches, and naming
convention violations.

Usage:
    uv run detect_schema_drift.py <vault-path> [options]

Options:
    --file-class <class>   Target fileClass (e.g., Meeting, Person, Project)
    --scope <path>         Limit scan to vault-relative folder path
    --dry-run              Show what would be analyzed without scanning

Returns:
    JSON with drift report:
    {
        "status": "success",
        "file_class": "Meeting",
        "total_notes": 42,
        "properties": {
            "scope": {"count": 38, "percentage": 90.5, "types": ["list"], "missing_in": [...]},
            ...
        },
        "issues": [
            {"type": "missing_property", "property": "scope", "file": "path.md", ...},
            {"type": "type_mismatch", "property": "tags", "expected": "list", ...},
            ...
        ],
        "recommendations": [...]
    }
"""

import sys
import json
import re
from pathlib import Path
from typing import Any
from collections import defaultdict

import frontmatter


def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/System']

    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")

    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    return vault_path


def classify_value_type(value: Any) -> str:
    """Classify a frontmatter value's type."""
    if isinstance(value, list):
        return "list"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "number"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        if re.match(r'^\d{4}-\d{2}-\d{2}', value):
            return "date"
        return "text"
    elif value is None:
        return "null"
    else:
        return "unknown"


def find_notes_by_file_class(
    vault_path: Path,
    file_class: str,
    scope: str | None = None,
) -> list[tuple[Path, dict]]:
    """Find all notes matching a fileClass within optional scope."""
    results = []
    search_root = vault_path / scope if scope else vault_path

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    for md_file in search_root.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            fc = post.get("fileClass") or post.get("fileclass") or post.get("FileClass")
            if fc and fc.lower() == file_class.lower():
                results.append((md_file, dict(post.metadata)))
        except Exception:
            continue

    return results


def find_notes_in_folder(
    vault_path: Path,
    scope: str,
) -> list[tuple[Path, dict]]:
    """Find all notes in a folder (when no fileClass specified)."""
    results = []
    search_root = vault_path / scope

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    for md_file in search_root.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            results.append((md_file, dict(post.metadata)))
        except Exception:
            continue

    return results


def analyze_schema(
    vault_path: Path,
    notes: list[tuple[Path, dict]],
) -> dict:
    """Analyze property usage across notes to detect drift."""
    total = len(notes)
    if total == 0:
        return {"properties": {}, "issues": [], "recommendations": []}

    # Collect property stats
    property_counts: dict[str, int] = defaultdict(int)
    property_types: dict[str, list[str]] = defaultdict(list)
    property_files: dict[str, list[str]] = defaultdict(list)

    for file_path, metadata in notes:
        rel_path = str(file_path.relative_to(vault_path))
        for key, value in metadata.items():
            property_counts[key] += 1
            vtype = classify_value_type(value)
            property_types[key].append(vtype)
            property_files[key].append(rel_path)

    # Build property report
    properties = {}
    for prop, count in sorted(property_counts.items(), key=lambda x: -x[1]):
        types = list(set(property_types[prop]))
        pct = round(count / total * 100, 1)
        present_files = set(property_files[prop])
        missing_in = [
            str(fp.relative_to(vault_path))
            for fp, _ in notes
            if str(fp.relative_to(vault_path)) not in present_files
        ]

        properties[prop] = {
            "count": count,
            "percentage": pct,
            "types": types,
            "missing_in": missing_in[:10],  # cap to avoid huge output
            "missing_count": len(missing_in),
        }

    # Detect issues
    issues = []

    for prop, info in properties.items():
        # Type mismatches
        if len(info["types"]) > 1:
            issues.append({
                "type": "type_mismatch",
                "property": prop,
                "expected_types": info["types"],
                "message": f"Property '{prop}' has mixed types: {', '.join(info['types'])}",
            })

        # Missing from >20% of notes but present in >50%
        if info["percentage"] >= 50 and info["missing_count"] > 0:
            issues.append({
                "type": "missing_property",
                "property": prop,
                "present_pct": info["percentage"],
                "missing_count": info["missing_count"],
                "message": f"Property '{prop}' is in {info['percentage']}% of notes but missing from {info['missing_count']}",
                "sample_missing": info["missing_in"][:5],
            })

    # Detect naming convention issues
    prop_names = list(property_counts.keys())
    camel_case = [p for p in prop_names if re.match(r'^[a-z]+[A-Z]', p)]
    kebab_case = [p for p in prop_names if '-' in p]
    snake_case = [p for p in prop_names if '_' in p]

    conventions_used = []
    if camel_case:
        conventions_used.append(f"camelCase ({', '.join(camel_case[:3])})")
    if kebab_case:
        conventions_used.append(f"kebab-case ({', '.join(kebab_case[:3])})")
    if snake_case:
        conventions_used.append(f"snake_case ({', '.join(snake_case[:3])})")

    if len(conventions_used) > 1:
        issues.append({
            "type": "naming_convention_mix",
            "conventions": conventions_used,
            "message": f"Mixed naming conventions: {'; '.join(conventions_used)}",
        })

    # Generate recommendations
    recommendations = []

    type_issues = [i for i in issues if i["type"] == "type_mismatch"]
    if type_issues:
        recommendations.append(
            f"Standardize property types for: {', '.join(i['property'] for i in type_issues)}"
        )

    missing_issues = [i for i in issues if i["type"] == "missing_property"]
    if missing_issues:
        high_pct = [i for i in missing_issues if i["present_pct"] >= 80]
        if high_pct:
            recommendations.append(
                f"Add missing properties (>80% adoption): {', '.join(i['property'] for i in high_pct)}"
            )

    if any(i["type"] == "naming_convention_mix" for i in issues):
        recommendations.append("Standardize property naming convention (recommend camelCase for Obsidian)")

    return {
        "properties": properties,
        "issues": issues,
        "recommendations": recommendations,
    }


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: detect_schema_drift.py <vault-path> [--file-class <class>] [--scope <path>] [--dry-run]"
        }))
        sys.exit(1)

    vault_path_str = args[0]
    file_class = None
    scope = None
    dry_run = False

    # Parse args
    i = 1
    while i < len(args):
        if args[i] == "--file-class" and i + 1 < len(args):
            file_class = args[i + 1]
            i += 2
        elif args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    try:
        vault_path = validate_vault_path(vault_path_str)

        if dry_run:
            print(json.dumps({
                "status": "dry_run",
                "vault_path": str(vault_path),
                "file_class": file_class,
                "scope": scope,
                "message": "Would scan for schema drift with these parameters",
            }, indent=2))
            return

        # Find notes
        if file_class:
            notes = find_notes_by_file_class(vault_path, file_class, scope)
        elif scope:
            notes = find_notes_in_folder(vault_path, scope)
        else:
            print(json.dumps({
                "status": "error",
                "error": "Must specify --file-class or --scope (or both)",
            }))
            sys.exit(1)

        if not notes:
            print(json.dumps({
                "status": "success",
                "file_class": file_class,
                "scope": scope,
                "total_notes": 0,
                "message": "No matching notes found",
                "properties": {},
                "issues": [],
                "recommendations": ["Check fileClass spelling or broaden scope"],
            }, indent=2))
            return

        # Analyze
        result = analyze_schema(vault_path, notes)
        result["status"] = "success"
        result["file_class"] = file_class
        result["scope"] = scope
        result["total_notes"] = len(notes)

        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
