#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Find similar and duplicate notes within a vault scope.

Uses tiered detection:
  Tier 1: Identical titles after normalization → "likely duplicates"
  Tier 2: >80% title similarity OR identical tags + same folder → "possible duplicates"

Usage:
    uv run find_similar_notes.py <vault-path> --scope <path> [options]

Options:
    --scope <path>          Vault-relative folder to scan (required)
    --min-similarity <pct>  Minimum title similarity for Tier 2 (default: 80)
    --max-groups <n>        Maximum groups to return (default: 20)
    --dry-run               Show scan parameters without scanning

Returns:
    JSON with duplicate groups:
    {
        "status": "success",
        "scope": "Work/Projects",
        "total_notes": 150,
        "groups": [
            {
                "tier": 1,
                "reason": "identical_title",
                "similarity": 1.0,
                "notes": [
                    {"path": "...", "title": "...", "fileClass": "..."},
                    ...
                ]
            },
            ...
        ],
        "summary": {"tier1": 3, "tier2": 5, "total_groups": 8}
    }
"""

import sys
import json
import re
from pathlib import Path
from typing import Any
from collections import defaultdict
from difflib import SequenceMatcher

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


def normalize_title(title: str) -> str:
    """Normalize a title for comparison.

    Lowercases, strips punctuation, collapses whitespace.
    """
    normalized = re.sub(r'[^\w\s]', '', title.lower())
    return re.sub(r'\s+', ' ', normalized).strip()


def title_similarity(a: str, b: str) -> float:
    """Compute similarity ratio between two titles."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def extract_tags(metadata: dict) -> set[str]:
    """Extract tags from frontmatter as a normalized set."""
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',')]
    if not isinstance(tags, list):
        return set()
    return {str(t).lower().lstrip('#') for t in tags if t}


def load_notes(vault_path: Path, scope: str) -> list[dict[str, Any]]:
    """Load all markdown notes within scope."""
    search_root = vault_path / scope

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    # Skip template directories
    skip_dirs = {'templates', 'Templates', '_templates'}

    notes = []
    for md_file in search_root.rglob("*.md"):
        # Skip template directories
        if any(part in skip_dirs for part in md_file.relative_to(search_root).parts):
            continue

        try:
            post = frontmatter.load(md_file)
            metadata = dict(post.metadata)
            rel_path = str(md_file.relative_to(vault_path))

            # Use filename (without extension) as title fallback
            title = metadata.get('title') or metadata.get('name') or md_file.stem

            notes.append({
                "path": rel_path,
                "title": str(title),
                "normalized_title": normalize_title(str(title)),
                "fileClass": metadata.get('fileClass') or metadata.get('fileclass', ''),
                "tags": extract_tags(metadata),
                "folder": str(md_file.parent.relative_to(vault_path)),
                "properties": set(metadata.keys()),
            })
        except Exception:
            continue

    return notes


def find_tier1_duplicates(notes: list[dict]) -> list[dict]:
    """Find notes with identical normalized titles."""
    title_groups: dict[str, list[dict]] = defaultdict(list)

    for note in notes:
        if note["normalized_title"]:
            title_groups[note["normalized_title"]].append(note)

    groups = []
    for normalized, group_notes in title_groups.items():
        if len(group_notes) >= 2:
            groups.append({
                "tier": 1,
                "reason": "identical_title",
                "similarity": 1.0,
                "normalized_title": normalized,
                "notes": [
                    {"path": n["path"], "title": n["title"], "fileClass": n["fileClass"]}
                    for n in group_notes
                ],
            })

    return groups


def find_tier2_duplicates(
    notes: list[dict],
    tier1_paths: set[str],
    min_similarity: float,
) -> list[dict]:
    """Find notes with high title similarity or matching tags+folder."""
    groups = []
    seen_pairs: set[tuple[str, str]] = set()

    for i, a in enumerate(notes):
        for j, b in enumerate(notes):
            if j <= i:
                continue

            pair = (a["path"], b["path"])
            if pair in seen_pairs:
                continue

            # Skip if both already in a Tier 1 group
            if a["path"] in tier1_paths and b["path"] in tier1_paths:
                continue

            reason = None
            similarity = 0.0

            # Check title similarity
            sim = title_similarity(a["title"], b["title"])
            if sim >= min_similarity / 100.0:
                reason = "similar_title"
                similarity = round(sim * 100, 1)

            # Check identical tags + same folder
            if not reason and a["tags"] and b["tags"]:
                if a["tags"] == b["tags"] and a["folder"] == b["folder"]:
                    reason = "same_tags_and_folder"
                    similarity = round(len(a["tags"] & b["tags"]) / max(len(a["tags"] | b["tags"]), 1) * 100, 1)

            if reason:
                seen_pairs.add(pair)
                groups.append({
                    "tier": 2,
                    "reason": reason,
                    "similarity": similarity,
                    "notes": [
                        {"path": a["path"], "title": a["title"], "fileClass": a["fileClass"]},
                        {"path": b["path"], "title": b["title"], "fileClass": b["fileClass"]},
                    ],
                })

    return groups


def merge_tier2_groups(groups: list[dict]) -> list[dict]:
    """Merge overlapping Tier 2 pairs into larger groups."""
    if not groups:
        return []

    # Build adjacency from pairs
    path_to_note: dict[str, dict] = {}
    adjacency: dict[str, set[str]] = defaultdict(set)

    for group in groups:
        paths = [n["path"] for n in group["notes"]]
        for note in group["notes"]:
            path_to_note[note["path"]] = note
        for p in paths:
            for q in paths:
                if p != q:
                    adjacency[p].add(q)

    # BFS to find connected components
    visited: set[str] = set()
    merged = []

    for start in adjacency:
        if start in visited:
            continue
        component: list[str] = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            queue.extend(adjacency[node] - visited)

        if len(component) >= 2:
            # Find the best reason/similarity from contributing groups
            best_sim = 0.0
            best_reason = "similar_title"
            component_set = set(component)
            for g in groups:
                g_paths = {n["path"] for n in g["notes"]}
                if g_paths & component_set:
                    if g["similarity"] > best_sim:
                        best_sim = g["similarity"]
                        best_reason = g["reason"]

            merged.append({
                "tier": 2,
                "reason": best_reason,
                "similarity": best_sim,
                "notes": [path_to_note[p] for p in component],
            })

    return merged


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: find_similar_notes.py <vault-path> --scope <path> [--min-similarity <pct>] [--max-groups <n>] [--dry-run]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    scope = None
    min_similarity = 80.0
    max_groups = 20
    dry_run = False

    # Parse args
    i = 1
    while i < len(args):
        if args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--min-similarity" and i + 1 < len(args):
            min_similarity = float(args[i + 1])
            i += 2
        elif args[i] == "--max-groups" and i + 1 < len(args):
            max_groups = int(args[i + 1])
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    if not scope:
        print(json.dumps({
            "status": "error",
            "error": "Must specify --scope <path>",
        }))
        sys.exit(1)

    try:
        vault_path = validate_vault_path(vault_path_str)

        if dry_run:
            print(json.dumps({
                "status": "dry_run",
                "vault_path": str(vault_path),
                "scope": scope,
                "min_similarity": min_similarity,
                "max_groups": max_groups,
                "message": "Would scan for similar notes with these parameters",
            }, indent=2))
            return

        # Load notes
        notes = load_notes(vault_path, scope)

        if not notes:
            print(json.dumps({
                "status": "success",
                "scope": scope,
                "total_notes": 0,
                "groups": [],
                "summary": {"tier1": 0, "tier2": 0, "total_groups": 0},
                "message": "No markdown files found in scope",
            }, indent=2))
            return

        # Tier 1: Identical titles
        tier1_groups = find_tier1_duplicates(notes)
        tier1_paths = set()
        for group in tier1_groups:
            for note in group["notes"]:
                tier1_paths.add(note["path"])

        # Tier 2: Similar titles or matching tags+folder
        tier2_pairs = find_tier2_duplicates(notes, tier1_paths, min_similarity)
        tier2_groups = merge_tier2_groups(tier2_pairs)

        # Combine and cap
        all_groups = tier1_groups + tier2_groups
        # Sort by tier (1 first), then by similarity descending
        all_groups.sort(key=lambda g: (g["tier"], -g["similarity"]))

        capped = all_groups[:max_groups]
        was_capped = len(all_groups) > max_groups

        result = {
            "status": "success",
            "scope": scope,
            "total_notes": len(notes),
            "groups": capped,
            "summary": {
                "tier1": len(tier1_groups),
                "tier2": len(tier2_groups),
                "total_groups": len(all_groups),
            },
        }

        if was_capped:
            result["message"] = f"Results capped at {max_groups} groups. {len(all_groups) - max_groups} additional groups found. Narrow scope for more detail."

        if not all_groups:
            result["message"] = "No similar notes found in scope."

        print(json.dumps(result, indent=2, default=str))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
