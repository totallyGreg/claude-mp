#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Redirect wikilinks vault-wide after a note merge or rename.

Replaces all occurrences of [[old-name]] with [[new-name]] across all
markdown files in the vault. Handles aliased links ([[old|display]])
and embeds (![[old]]).

Usage:
    uv run redirect_links.py <vault-path> --old <name> --new <name> [options]

Options:
    --old <name>       Old note name (without .md extension)
    --new <name>       New note name (without .md extension)
    --scope <path>     Limit scan to vault-relative folder (default: entire vault)
    --no-write         Return affected file content as JSON without writing (capped at 50 files)
    --dry-run          Show affected files without writing

Returns:
    JSON with redirect results:
    {
        "status": "success",
        "old_name": "old-note",
        "new_name": "new-note",
        "affected_files": [
            {"path": "file.md", "replacements": 3},
            ...
        ],
        "total_replacements": 15,
        "total_files": 5
    }

    With --no-write, affected_files entries also include "content_after".
    If >50 files would be affected, returns:
    {
        "status": "too_many",
        "affected_count": N,
        "message": "Too many files to return inline. Use script-controlled mode (omit --no-write) with explicit approval."
    }
"""

import sys
import json
import re
from pathlib import Path


def validate_vault_path(vault_path_str: str) -> Path:
    """Validate vault path for security."""
    vault_path = Path(vault_path_str).resolve()
    forbidden = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/System']

    if any(str(vault_path).startswith(p) for p in forbidden):
        raise ValueError(f"Access denied: {vault_path}")

    if not vault_path.exists():
        raise ValueError(f"Vault path does not exist: {vault_path}")

    return vault_path


def build_link_patterns(old_name: str) -> list[tuple[re.Pattern, str]]:
    """Build regex patterns for all wikilink variants.

    Matches:
    - [[old-name]]           → [[new-name]]
    - [[old-name|display]]   → [[new-name|display]]
    - ![[old-name]]          → ![[new-name]]
    - ![[old-name|display]]  → ![[new-name|display]]
    """
    escaped = re.escape(old_name)
    return [
        # [[old-name]] → [[new-name]] (plain link)
        (re.compile(r'\[\[' + escaped + r'\]\]'), '[[{new}]]'),
        # [[old-name|display]] → [[new-name|display]] (aliased link)
        (re.compile(r'\[\[' + escaped + r'\|([^\]]+)\]\]'), '[[{new}|\\1]]'),
        # ![[old-name]] → ![[new-name]] (embed)
        (re.compile(r'!\[\[' + escaped + r'\]\]'), '![[{new}]]'),
        # ![[old-name|display]] → ![[new-name|display]] (aliased embed)
        (re.compile(r'!\[\[' + escaped + r'\|([^\]]+)\]\]'), '![[{new}|\\1]]'),
    ]


NO_WRITE_FILE_CAP = 50


def scan_and_replace(
    vault_path: Path,
    old_name: str,
    new_name: str,
    scope: str | None,
    dry_run: bool,
    no_write: bool = False,
) -> dict:
    """Scan vault for wikilinks and replace them."""
    search_root = vault_path / scope if scope else vault_path

    if not search_root.exists():
        raise ValueError(f"Scope path does not exist: {search_root}")

    patterns = build_link_patterns(old_name)
    affected_files = []
    total_replacements = 0

    for md_file in search_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue

        new_content = content
        file_replacements = 0

        for pattern, replacement_template in patterns:
            replacement = replacement_template.format(new=new_name)
            new_content, count = pattern.subn(replacement, new_content)
            file_replacements += count

        if file_replacements > 0:
            rel_path = str(md_file.relative_to(vault_path))
            entry: dict = {
                "path": rel_path,
                "replacements": file_replacements,
            }
            if no_write or dry_run:
                # Include computed content for agent to apply with Edit tool
                entry["content_after"] = new_content
            affected_files.append(entry)
            total_replacements += file_replacements

            if not dry_run and not no_write:
                md_file.write_text(new_content, encoding='utf-8')

    if no_write and len(affected_files) > NO_WRITE_FILE_CAP:
        return {
            "status": "too_many",
            "affected_count": len(affected_files),
            "total_replacements": total_replacements,
            "message": (
                f"Too many files ({len(affected_files)}) to return inline. "
                "Use script-controlled mode (omit --no-write) with explicit user approval."
            ),
        }

    return {
        "affected_files": affected_files,
        "total_replacements": total_replacements,
        "total_files": len(affected_files),
    }


def main():
    """Main entry point."""
    args = sys.argv[1:]

    if not args:
        print(json.dumps({
            "status": "error",
            "error": "Usage: redirect_links.py <vault-path> --old <name> --new <name> [--scope <path>] [--dry-run]",
        }))
        sys.exit(1)

    vault_path_str = args[0]
    old_name = None
    new_name = None
    scope = None
    dry_run = False
    no_write = False

    # Parse args
    i = 1
    while i < len(args):
        if args[i] == "--old" and i + 1 < len(args):
            old_name = args[i + 1]
            i += 2
        elif args[i] == "--new" and i + 1 < len(args):
            new_name = args[i + 1]
            i += 2
        elif args[i] == "--scope" and i + 1 < len(args):
            scope = args[i + 1]
            i += 2
        elif args[i] == "--no-write":
            no_write = True
            i += 1
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        else:
            i += 1

    if not old_name or not new_name:
        print(json.dumps({
            "status": "error",
            "error": "Must specify both --old and --new note names",
        }))
        sys.exit(1)

    if old_name == new_name:
        print(json.dumps({
            "status": "error",
            "error": "Old and new names must be different",
        }))
        sys.exit(1)

    try:
        vault_path = validate_vault_path(vault_path_str)

        result = scan_and_replace(vault_path, old_name, new_name, scope, dry_run, no_write)
        if result.get("status") == "too_many":
            print(json.dumps(result, indent=2))
            return
        result["status"] = "dry_run" if dry_run else "success"
        result["old_name"] = old_name
        result["new_name"] = new_name

        if scope:
            result["scope"] = scope

        if not result["affected_files"]:
            result["message"] = f"No references to [[{old_name}]] found"

        print(json.dumps(result, indent=2))

    except ValueError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"status": "error", "error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
