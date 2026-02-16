#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Find notes related to a given note by shared tags, properties, and links.

Ranks connections by strength:
  - Shared properties (weighted highest): same fileClass, scope, project, etc.
  - Shared tags: overlapping tag sets
  - Folder proximity: notes in the same or sibling directories
  - Shared links: wikilinks pointing to the same targets

Usage:
    uv run find_related.py <vault-path> <note-path> [options]

Options:
    --scope <path>    Limit search to vault-relative folder (default: whole vault)
    --top <n>         Number of results to return (default: 10)

Returns:
    JSON with related notes:
    {
        "status": "success",
        "target": "Work/Projects/My Project.md",
        "scope": "Work",
        "total_scanned": 150,
        "related": [
            {
                "path": "Work/Projects/Related Note.md",
                "title": "Related Note",
                "score": 85.0,
                "reasons": [
                    {"type": "shared_property", "detail": "fileClass=Project", "weight": 30},
                    {"type": "shared_tag", "detail": "tags: docker, devops", "weight": 20},
                    {"type": "shared_link", "detail": "both link to [[Kubernetes]]", "weight": 25},
                    {"type": "folder_proximity", "detail": "same folder", "weight": 10}
                ]
            },
            ...
        ]
    }
"""

import sys
import json
import re
from pathlib import Path
from typing import Any
import frontmatter


# --- Scoring weights ---
WEIGHT_SHARED_PROPERTY = 10  # per shared non-trivial property value
WEIGHT_SHARED_TAG = 8        # per shared tag
WEIGHT_SHARED_LINK = 12      # per shared wikilink target
WEIGHT_SAME_FOLDER = 5       # same immediate folder
WEIGHT_SIBLING_FOLDER = 2    # parent folder is the same
WEIGHT_SAME_FILECLASS = 15   # same fileClass value

# Properties to compare values (not just presence)
VALUE_PROPERTIES = {'fileClass', 'fileclass', 'FileClass', 'scope', 'project', 'type', 'category', 'status'}

# Properties to skip when comparing (meta/structural)
SKIP_PROPERTIES = {'title', 'name', 'date', 'created', 'modified', 'updated', 'aliases', 'cssclass', 'cssclasses', 'publish', 'permalink'}


def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/System']

    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")

    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    return vault_path


def extract_tags(metadata: dict) -> set[str]:
    """Extract tags from frontmatter as a normalized set."""
    tags = metadata.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',')]
    if not isinstance(tags, list):
        return set()
    return {str(t).lower().lstrip('#') for t in tags if t}


def extract_wikilinks(content: str) -> set[str]:
    """Extract wikilink targets from note content."""
    # Match [[Target]] and [[Target|Display]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    links = set()
    for match in re.finditer(pattern, content):
        target = match.group(1).strip()
        if target:
            links.add(target.lower())
    return links


def load_note(vault_path: Path, note_path: str) -> dict[str, Any]:
    """Load a single note with metadata, tags, links, and folder info."""
    full_path = vault_path / note_path
    if not full_path.exists():
        raise ValueError(f"Note not found: {note_path}")

    post = frontmatter.load(full_path)
    metadata = dict(post.metadata)
    title = metadata.get('title') or metadata.get('name') or full_path.stem

    return {
        "path": note_path,
        "title": str(title),
        "metadata": metadata,
        "tags": extract_tags(metadata),
        "links": extract_wikilinks(post.content),
        "folder": str(full_path.parent.relative_to(vault_path)),
        "parent_folder": str(full_path.parent.parent.relative_to(vault_path)) if full_path.parent != vault_path else "",
    }


def load_scope_notes(vault_path: Path, scope: str | None, exclude_path: str) -> list[dict[str, Any]]:
    """Load all markdown notes within scope, excluding the target."""
    search_root = vault_path / scope if scope else vault_path

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    skip_dirs = {'templates', 'Templates', '_templates', '.obsidian', '.trash'}
    notes = []

    for md_file in search_root.rglob("*.md"):
        rel_path = str(md_file.relative_to(vault_path))

        if rel_path == exclude_path:
            continue

        if any(part in skip_dirs for part in md_file.relative_to(vault_path).parts):
            continue

        try:
            post = frontmatter.load(md_file)
            metadata = dict(post.metadata)
            title = metadata.get('title') or metadata.get('name') or md_file.stem

            notes.append({
                "path": rel_path,
                "title": str(title),
                "metadata": metadata,
                "tags": extract_tags(metadata),
                "links": extract_wikilinks(post.content),
                "folder": str(md_file.parent.relative_to(vault_path)),
                "parent_folder": str(md_file.parent.parent.relative_to(vault_path)) if md_file.parent != vault_path else "",
            })
        except Exception:
            continue

    return notes


def score_relationship(target: dict, candidate: dict) -> tuple[float, list[dict]]:
    """Score how related a candidate note is to the target. Returns (score, reasons)."""
    reasons = []
    score = 0.0

    target_meta = target["metadata"]
    cand_meta = candidate["metadata"]

    # 1. Shared fileClass (highest signal)
    target_fc = (target_meta.get('fileClass') or target_meta.get('fileclass') or '').lower()
    cand_fc = (cand_meta.get('fileClass') or cand_meta.get('fileclass') or '').lower()

    if target_fc and cand_fc and target_fc == cand_fc:
        score += WEIGHT_SAME_FILECLASS
        reasons.append({
            "type": "shared_property",
            "detail": f"fileClass={cand_meta.get('fileClass') or cand_meta.get('fileclass')}",
            "weight": WEIGHT_SAME_FILECLASS,
        })

    # 2. Shared property values (scope, project, type, etc.)
    for prop in VALUE_PROPERTIES - {'fileClass', 'fileclass', 'FileClass'}:
        target_val = target_meta.get(prop)
        cand_val = cand_meta.get(prop)

        if target_val is None or cand_val is None:
            continue

        # Normalize for comparison
        t_set = _to_comparable_set(target_val)
        c_set = _to_comparable_set(cand_val)
        shared = t_set & c_set

        if shared:
            weight = WEIGHT_SHARED_PROPERTY * len(shared)
            score += weight
            reasons.append({
                "type": "shared_property",
                "detail": f"{prop}: {', '.join(sorted(shared))}",
                "weight": weight,
            })

    # 3. Shared tags
    shared_tags = target["tags"] & candidate["tags"]
    if shared_tags:
        weight = WEIGHT_SHARED_TAG * len(shared_tags)
        score += weight
        reasons.append({
            "type": "shared_tag",
            "detail": f"tags: {', '.join(sorted(shared_tags))}",
            "weight": weight,
        })

    # 4. Shared wikilink targets
    shared_links = target["links"] & candidate["links"]
    if shared_links:
        weight = WEIGHT_SHARED_LINK * len(shared_links)
        score += weight
        # Show up to 5 shared links
        link_display = sorted(shared_links)[:5]
        detail = f"both link to {', '.join(f'[[{l}]]' for l in link_display)}"
        if len(shared_links) > 5:
            detail += f" (+{len(shared_links) - 5} more)"
        reasons.append({
            "type": "shared_link",
            "detail": detail,
            "weight": weight,
        })

    # 5. Folder proximity
    if target["folder"] == candidate["folder"]:
        score += WEIGHT_SAME_FOLDER
        reasons.append({
            "type": "folder_proximity",
            "detail": "same folder",
            "weight": WEIGHT_SAME_FOLDER,
        })
    elif target["parent_folder"] and target["parent_folder"] == candidate["parent_folder"]:
        score += WEIGHT_SIBLING_FOLDER
        reasons.append({
            "type": "folder_proximity",
            "detail": "sibling folder",
            "weight": WEIGHT_SIBLING_FOLDER,
        })

    return score, reasons


def _to_comparable_set(value: Any) -> set[str]:
    """Convert a property value to a set of lowercase strings for comparison."""
    if isinstance(value, list):
        return {str(v).lower().strip() for v in value if v}
    if isinstance(value, str):
        return {value.lower().strip()} if value.strip() else set()
    if value is not None:
        return {str(value).lower()}
    return set()


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if len(args) < 2:
        print(json.dumps({
            "status": "error",
            "error": "Usage: find_related.py <vault-path> <note-path> [--scope <path>] [--top <n>]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    note_path = args[1]
    scope = None
    top_n = 10

    # Parse optional args
    i = 2
    while i < len(args):
        if args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--top" and i + 1 < len(args):
            top_n = int(args[i + 1])
            i += 2
        else:
            i += 1

    try:
        vault_path = validate_vault_path(vault_path_str)
        target = load_note(vault_path, note_path)
        candidates = load_scope_notes(vault_path, scope, note_path)

        if not candidates:
            print(json.dumps({
                "status": "success",
                "target": note_path,
                "scope": scope or "(whole vault)",
                "total_scanned": 0,
                "related": [],
                "message": "No notes found in scope to compare against.",
            }, indent=2))
            return

        # Score all candidates
        scored = []
        for cand in candidates:
            score, reasons = score_relationship(target, cand)
            if score > 0:
                scored.append({
                    "path": cand["path"],
                    "title": cand["title"],
                    "score": round(score, 1),
                    "reasons": reasons,
                })

        # Sort by score descending, take top N
        scored.sort(key=lambda x: -x["score"])
        top_results = scored[:top_n]

        result = {
            "status": "success",
            "target": note_path,
            "scope": scope or "(whole vault)",
            "total_scanned": len(candidates),
            "related": top_results,
        }

        if not scored:
            result["message"] = "No related notes found. The target note may have unique tags/properties, or the scope may be too narrow."

        print(json.dumps(result, indent=2, default=str))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
