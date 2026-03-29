#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Suggest missing properties for a note based on peer analysis.

Scans sibling notes (same fileClass or same folder) to identify common
properties the target note is missing. Returns suggestions with confidence
scores based on adoption percentage among peers.

Usage:
    uv run suggest_properties.py <vault-path> <note-path> [options]

Options:
    --min-confidence <pct>  Minimum adoption % to suggest (default: 50)

Returns:
    JSON with suggestions:
    {
        "status": "success",
        "target": "path/to/note.md",
        "file_class": "Meeting",
        "peer_count": 42,
        "existing_properties": ["title", "date", "fileClass"],
        "suggestions": [
            {
                "property": "scope",
                "confidence": 90.5,
                "peer_count": 38,
                "common_types": ["list"],
                "example_values": ["[[Company]]", "[[Project]]"],
                "rationale": "90.5% of Meeting notes have 'scope'"
            },
            ...
        ]
    }
"""

import sys
import json
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
    elif isinstance(value, (int, float)):
        return "number"
    elif isinstance(value, str):
        return "text"
    elif value is None:
        return "null"
    return "unknown"


def load_target_note(vault_path: Path, note_path: str) -> tuple[dict, str | None]:
    """Load the target note and extract its metadata."""
    full_path = vault_path / note_path
    if not full_path.exists():
        raise ValueError(f"Note not found: {note_path}")

    post = frontmatter.load(full_path)
    metadata = dict(post.metadata)
    file_class = metadata.get("fileClass") or metadata.get("fileclass") or metadata.get("FileClass")
    return metadata, file_class


def find_peer_notes(
    vault_path: Path,
    note_path: str,
    file_class: str | None,
) -> list[dict]:
    """Find peer notes by fileClass or folder."""
    target_full = vault_path / note_path
    peers = []

    if file_class:
        # Search entire vault for same fileClass
        for md_file in vault_path.rglob("*.md"):
            if md_file == target_full:
                continue
            try:
                post = frontmatter.load(md_file)
                fc = post.get("fileClass") or post.get("fileclass") or post.get("FileClass")
                if fc and fc.lower() == file_class.lower():
                    peers.append(dict(post.metadata))
            except Exception:
                continue
    else:
        # Fall back to same folder
        folder = target_full.parent
        for md_file in folder.glob("*.md"):
            if md_file == target_full:
                continue
            try:
                post = frontmatter.load(md_file)
                peers.append(dict(post.metadata))
            except Exception:
                continue

    return peers


def format_example_value(value: Any) -> str:
    """Format a value for display as an example."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value[:3])
    return str(value)[:80]


def analyze_peers(
    target_metadata: dict,
    peers: list[dict],
    min_confidence: float,
) -> list[dict]:
    """Analyze peer notes to find property suggestions."""
    if not peers:
        return []

    total = len(peers)

    # Count property usage across peers
    property_counts: dict[str, int] = defaultdict(int)
    property_types: dict[str, list[str]] = defaultdict(list)
    property_examples: dict[str, list[Any]] = defaultdict(list)

    for peer in peers:
        for key, value in peer.items():
            property_counts[key] += 1
            property_types[key].append(classify_value_type(value))
            if len(property_examples[key]) < 5:
                property_examples[key].append(value)

    # Find properties missing from target
    existing = set(target_metadata.keys())
    suggestions = []

    for prop, count in sorted(property_counts.items(), key=lambda x: -x[1]):
        if prop in existing:
            continue

        confidence = round(count / total * 100, 1)
        if confidence < min_confidence:
            continue

        types = list(set(property_types[prop]))
        examples = [format_example_value(v) for v in property_examples[prop][:3]]
        # Deduplicate examples
        examples = list(dict.fromkeys(examples))

        suggestions.append({
            "property": prop,
            "confidence": confidence,
            "peer_count": count,
            "common_types": types,
            "example_values": examples,
            "rationale": f"{confidence}% of peer notes have '{prop}'",
        })

    return suggestions


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if len(args) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: suggest_properties.py <vault-path> <note-path> [--min-confidence <pct>]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    note_path = args[1]
    min_confidence = 50.0

    # Parse optional args
    i = 2
    while i < len(args):
        if args[i] == "--min-confidence" and i + 1 < len(args):
            min_confidence = float(args[i + 1])
            i += 2
        else:
            i += 1

    try:
        vault_path = validate_vault_path(vault_path_str)
        target_metadata, file_class = load_target_note(vault_path, note_path)
        peers = find_peer_notes(vault_path, note_path, file_class)

        suggestions = analyze_peers(target_metadata, peers, min_confidence)

        result = {
            "status": "success",
            "target": note_path,
            "file_class": file_class,
            "peer_count": len(peers),
            "existing_properties": sorted(target_metadata.keys()),
            "suggestions": suggestions,
        }

        if not peers:
            result["message"] = "No peer notes found. Try specifying fileClass in frontmatter or checking folder contents."

        if not suggestions and peers:
            result["message"] = "No missing properties found — this note has all common properties."

        print(json.dumps(result, indent=2, default=str))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
