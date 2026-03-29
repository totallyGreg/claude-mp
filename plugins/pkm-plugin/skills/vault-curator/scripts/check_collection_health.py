#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Audit Collection Folder Pattern health across a vault.

A collection is a folder containing notes of the same conceptual type, with:
  - A folder note at <Folder>/<Folder>.md
  - A Bases file at 900 📐Templates/970 Bases/<Name>.base
  - Member notes sharing a consistent fileClass

Detection: a folder qualifies as a candidate collection if it contains a folder
note (file named same as the folder) OR ≥5 notes where ≥60% share a fileClass.

Usage:
    uv run check_collection_health.py <vault-path> [options]

Options:
    --scope <path>     Limit scan to vault-relative folder (e.g. "700 Notes")
    --folder <path>    Check a single specific folder (vault-relative)
    --dry-run          Show candidate folders without running health checks

Returns:
    JSON list of collection health reports:
    [
        {
            "folder": "700 Notes/Workflows",
            "name": "Workflows",
            "member_count": 12,
            "has_folder_note": true,
            "folder_note_embeds_bases": true,
            "has_bases_file": true,
            "dominant_fileclass": "Workflow",
            "fileclass_coverage_pct": 91.7,
            "schema_drift_issues": 0,
            "health": "healthy"
        },
        ...
    ]
"""

import sys
import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any

import frontmatter


BASES_DIR = "900 📐Templates/970 Bases"
FORBIDDEN_PATHS = ["/etc", "/var", "/usr", "/bin", "/sbin", "/root", "/System"]


def validate_vault_path(vault_path_str: str) -> Path:
    vault_path = Path(vault_path_str).resolve()
    if any(str(vault_path).startswith(p) for p in FORBIDDEN_PATHS):
        raise ValueError(f"Access denied: {vault_path}")
    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")
    return vault_path


def get_fileclass(metadata: dict) -> str | None:
    return (
        metadata.get("fileClass")
        or metadata.get("fileclass")
        or metadata.get("FileClass")
    )


def classify_value_type(value: Any) -> str:
    if isinstance(value, list):
        return "list"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "date" if re.match(r"^\d{4}-\d{2}-\d{2}", value) else "text"
    return "null" if value is None else "unknown"


def load_all_members(folder: Path) -> list[tuple[Path, dict, str]]:
    """Load all .md files recursively, returning (path, metadata, content)."""
    results = []
    for md_file in folder.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            results.append((md_file, dict(post.metadata), post.content))
        except Exception:
            continue
    return results


def embeds_bases(content: str) -> bool:
    """Check if note content embeds a .base file view."""
    return bool(re.search(r"!\[\[.*?\.base#", content))


def count_schema_drift_issues(
    members: list[tuple[Path, dict, str]],
    folder_note_path: Path | None,
) -> int:
    """Count schema drift issues: properties present in ≥50% of notes but missing from some."""
    # Exclude folder note from member analysis
    notes = [
        (p, m) for p, m, _ in members
        if folder_note_path is None or p != folder_note_path
    ]
    if len(notes) < 3:
        return 0

    prop_counts: dict[str, int] = defaultdict(int)
    for _, meta in notes:
        for key in meta:
            prop_counts[key] += 1

    total = len(notes)
    drift_count = 0
    for _, count in prop_counts.items():
        pct = count / total * 100
        if pct >= 50 and count < total:
            drift_count += 1
    return drift_count


def check_collection(
    folder: Path,
    vault_path: Path,
) -> dict:
    name = folder.name
    folder_note_path = folder / f"{name}.md"
    bases_file_path = vault_path / BASES_DIR / f"{name}.base"

    has_folder_note = folder_note_path.exists()
    folder_note_embeds_bases = False
    if has_folder_note:
        try:
            post = frontmatter.load(folder_note_path)
            folder_note_embeds_bases = embeds_bases(post.content)
        except Exception:
            pass

    has_bases_file = bases_file_path.exists()

    # Load all members (excluding folder note for fileClass analysis)
    all_members = load_all_members(folder)
    member_count = len(all_members)

    fileclasses = [
        get_fileclass(m)
        for _, m, _ in all_members
        if (folder / f"{name}.md") != _  # exclude folder note
    ]
    fileclasses = [fc for fc in fileclasses if fc]
    dominant_fileclass = None
    fileclass_coverage_pct = 0.0
    if fileclasses:
        counter = Counter(fileclasses)
        dominant_fileclass, dominant_count = counter.most_common(1)[0]
        non_folder_total = len(all_members) - (1 if has_folder_note else 0)
        fileclass_coverage_pct = round(dominant_count / non_folder_total * 100, 1) if non_folder_total > 0 else 0.0

    schema_drift_issues = count_schema_drift_issues(
        all_members,
        folder_note_path if has_folder_note else None,
    )

    # Health classification
    missing = []
    if not has_folder_note:
        missing.append("folder_note")
    if not folder_note_embeds_bases:
        missing.append("bases_embed")
    if not has_bases_file:
        missing.append("bases_file")

    if not missing and schema_drift_issues == 0:
        health = "healthy"
    elif not missing:
        health = "partial"  # infrastructure present, schema drift
    elif len(missing) >= 2:
        health = "missing_infrastructure"
    else:
        health = "partial"

    return {
        "folder": str(folder.relative_to(vault_path)),
        "name": name,
        "member_count": member_count,
        "has_folder_note": has_folder_note,
        "folder_note_embeds_bases": folder_note_embeds_bases,
        "has_bases_file": has_bases_file,
        "dominant_fileclass": dominant_fileclass,
        "fileclass_coverage_pct": fileclass_coverage_pct,
        "schema_drift_issues": schema_drift_issues,
        "health": health,
        "missing": missing,
    }


def is_candidate_collection(folder: Path) -> bool:
    """A folder is a candidate collection if it has a folder note OR ≥5 notes with ≥60% sharing a fileClass."""
    name = folder.name

    # Skip hidden, template, or system folders
    if name.startswith(".") or name.startswith("_") or "Template" in name or "📐" in name:
        return False

    folder_note = folder / f"{name}.md"
    if folder_note.exists():
        return True

    notes = list(folder.glob("*.md"))
    if len(notes) < 5:
        return False

    fileclasses = []
    for md_file in notes:
        try:
            post = frontmatter.load(md_file)
            fc = get_fileclass(dict(post.metadata))
            if fc:
                fileclasses.append(fc)
        except Exception:
            continue

    if not fileclasses:
        return False
    counter = Counter(fileclasses)
    top_count = counter.most_common(1)[0][1]
    return (top_count / len(notes)) >= 0.6


def find_candidate_collections(vault_path: Path, scope: str | None) -> list[Path]:
    search_root = vault_path / scope if scope else vault_path
    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    candidates = []
    for folder in sorted(search_root.iterdir()):
        if folder.is_dir() and is_candidate_collection(folder):
            candidates.append(folder)
    return candidates


def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: check_collection_health.py <vault-path> [--scope <path>] [--folder <path>] [--dry-run]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    scope = None
    target_folder = None
    dry_run = False

    i = 1
    while i < len(args):
        if args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--folder" and i + 1 < len(args):
            target_folder = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    try:
        vault_path = validate_vault_path(vault_path_str)

        if target_folder:
            candidates = [vault_path / target_folder]
        else:
            candidates = find_candidate_collections(vault_path, scope)

        if dry_run:
            print(json.dumps({
                "status": "dry_run",
                "vault_path": str(vault_path),
                "scope": scope,
                "candidate_folders": [str(c.relative_to(vault_path)) for c in candidates],
                "count": len(candidates),
            }, indent=2))
            return

        results = [check_collection(folder, vault_path) for folder in candidates if folder.is_dir()]
        summary = {
            "healthy": sum(1 for r in results if r["health"] == "healthy"),
            "partial": sum(1 for r in results if r["health"] == "partial"),
            "missing_infrastructure": sum(1 for r in results if r["health"] == "missing_infrastructure"),
        }

        print(json.dumps({
            "status": "success",
            "vault_path": str(vault_path),
            "scope": scope,
            "collections_checked": len(results),
            "summary": summary,
            "collections": results,
        }, indent=2))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
