#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///

"""
Merge two notes into one, combining frontmatter and content.

Takes a source and target note. The target is the "surviving" note that
receives merged content. The source note is left unchanged (deletion is
a separate step handled by the agent after link redirect).

Usage:
    uv run merge_notes.py <vault-path> --source <path> --target <path> [options]

Options:
    --source <path>    Source note path (relative to vault) — will be absorbed
    --target <path>    Target note path (relative to vault) — will survive
    --dry-run          Show planned merge without writing

Returns:
    JSON with merge result:
    {
        "status": "success",
        "source": "path/to/source.md",
        "target": "path/to/target.md",
        "frontmatter_changes": {
            "added": {"key": "value"},
            "conflicts": [{"property": "type", "source": "meeting", "target": "standup"}],
            "merged_lists": {"tags": ["a", "b", "c"]}
        },
        "content_appended": true
    }
"""

import sys
import json
from pathlib import Path
from typing import Any
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


def merge_list_values(source_val: list, target_val: list) -> list:
    """Merge two list values, deduplicating while preserving order."""
    seen = set()
    merged = []
    for item in target_val + source_val:
        key = str(item).lower() if isinstance(item, str) else str(item)
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def merge_frontmatter(
    source_meta: dict,
    target_meta: dict,
) -> dict[str, Any]:
    """Merge source frontmatter into target following the consolidation protocol.

    Rules:
    - Source has value, target missing → copy from source
    - Target has value, source missing → keep target
    - Both have same value → keep as-is
    - Both have different scalar values → conflict (report, don't resolve)
    - Both have list values → union (deduplicated)
    - aliases: always union, add source title
    - fileClass: keep target
    - tags: union
    - created: keep earliest
    """
    added: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    merged_lists: dict[str, list] = {}

    # Properties to skip in merge (managed separately)
    skip_props = {'fileClass', 'fileclass', 'FileClass'}

    for key, source_val in source_meta.items():
        if key in skip_props:
            continue

        if key not in target_meta:
            # Source has value, target missing → copy
            added[key] = source_val
            continue

        target_val = target_meta[key]

        # Both are lists → union
        if isinstance(source_val, list) and isinstance(target_val, list):
            merged = merge_list_values(source_val, target_val)
            if set(str(x) for x in merged) != set(str(x) for x in target_val):
                merged_lists[key] = merged
            continue

        # Special: created → keep earliest
        if key == 'created':
            try:
                if str(source_val) < str(target_val):
                    added[key] = source_val
            except (TypeError, ValueError):
                pass
            continue

        # Same value → skip
        if source_val == target_val:
            continue

        # Different scalar values → conflict
        conflicts.append({
            "property": key,
            "source": source_val,
            "target": target_val,
        })

    return {
        "added": added,
        "conflicts": conflicts,
        "merged_lists": merged_lists,
    }


def merge_content(
    source_content: str,
    target_content: str,
    source_path: str,
) -> str:
    """Merge source content into target with separator and provenance header."""
    source_name = Path(source_path).stem
    separator = f"\n\n---\n\n## Merged from: [[{source_name}]]\n\n"
    return target_content.rstrip() + separator + source_content.strip() + "\n"


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: merge_notes.py <vault-path> --source <path> --target <path> [--dry-run]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    source_path = None
    target_path = None
    dry_run = False

    # Parse args
    i = 1
    while i < len(args):
        if args[i] == "--source" and i + 1 < len(args):
            source_path = args[i + 1]
            i += 2
        elif args[i] == "--target" and i + 1 < len(args):
            target_path = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    if not source_path or not target_path:
        print(json.dumps({
            "status": "error",
            "error": "Must specify both --source and --target paths",
        }))
        sys.exit(1)

    try:
        vault_path = validate_vault_path(vault_path_str)

        source_file = vault_path / source_path
        target_file = vault_path / target_path

        if not source_file.exists():
            raise ValueError(f"Source note not found: {source_path}")
        if not target_file.exists():
            raise ValueError(f"Target note not found: {target_path}")

        # Load both notes
        source_post = frontmatter.load(source_file)
        target_post = frontmatter.load(target_file)

        source_meta = dict(source_post.metadata)
        target_meta = dict(target_post.metadata)

        # Merge frontmatter
        fm_changes = merge_frontmatter(source_meta, target_meta)

        # Add source title as alias
        source_title = source_meta.get('title') or source_meta.get('name') or source_file.stem
        existing_aliases = target_meta.get('aliases', [])
        if isinstance(existing_aliases, str):
            existing_aliases = [existing_aliases]
        if str(source_title) not in [str(a) for a in existing_aliases]:
            if 'aliases' not in fm_changes['merged_lists']:
                fm_changes['merged_lists']['aliases'] = list(existing_aliases)
            fm_changes['merged_lists']['aliases'].append(str(source_title))

        # Merge content
        merged_content = merge_content(source_post.content, target_post.content, source_path)

        result = {
            "status": "dry_run" if dry_run else "success",
            "source": source_path,
            "target": target_path,
            "frontmatter_changes": {
                "added": fm_changes["added"],
                "conflicts": fm_changes["conflicts"],
                "merged_lists": {k: v for k, v in fm_changes["merged_lists"].items()},
            },
            "content_appended": bool(source_post.content.strip()),
        }

        if fm_changes["conflicts"]:
            result["has_conflicts"] = True
            result["message"] = f"{len(fm_changes['conflicts'])} property conflict(s) require user resolution"

        if not dry_run:
            # Apply frontmatter changes
            for key, val in fm_changes["added"].items():
                target_post.metadata[key] = val
            for key, val in fm_changes["merged_lists"].items():
                target_post.metadata[key] = val

            # Apply content merge
            target_post.content = merged_content

            # Write target
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(target_post))

            result["written"] = str(target_file.relative_to(vault_path))

        print(json.dumps(result, indent=2, default=str))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
