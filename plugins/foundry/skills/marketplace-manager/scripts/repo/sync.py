#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Sync plugin versions from source (plugin.json / SKILL.md) to marketplace.json.

For each plugin with a relative source path:
1. Check .claude-plugin/plugin.json -- if found and has version, use it
2. Otherwise scan for a single skill (skills/*/SKILL.md) -- extract version
   from YAML frontmatter
3. Compare with marketplace.json and update where they differ

Stdlib-only. Uses pyyaml when available for frontmatter parsing, falls back
to a minimal subset parser.
"""

import argparse
import json
import sys
from pathlib import Path


# -- YAML frontmatter parsing ------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a Markdown file."""
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    raw = text[3:end]
    try:
        import yaml
        return yaml.safe_load(raw) or {}
    except ImportError:
        return _parse_frontmatter_stdlib(raw)


def _parse_frontmatter_stdlib(raw: str) -> dict:
    """Minimal YAML subset parser -- flat keys and one level of nesting.

    Handles:  name: value, metadata:\n  version: "1.0.0", quoted/unquoted
    Skips:    multi-line strings, anchors, aliases, sequences
    """
    result = {}
    current_map = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip().strip("\"'")
        if indent == 0:
            if val:
                result[key] = val
                current_map = None
            else:
                result[key] = {}
                current_map = result[key]
        elif indent > 0 and isinstance(current_map, dict):
            if val:
                current_map[key] = val
    return result


# -- Version resolution ------------------------------------------------------

def _parse_semver(version_str: str) -> tuple[int, ...]:
    """Parse a semver string into a comparable tuple."""
    parts = version_str.split(".")
    result = []
    for part in parts[:3]:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _extract_skill_version(skill_md: Path) -> str | None:
    """Extract version from a SKILL.md frontmatter."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return None

    fm = parse_frontmatter(text)
    version = fm.get("version")
    if not version:
        metadata = fm.get("metadata")
        if isinstance(metadata, dict):
            version = metadata.get("version")

    return str(version) if version else None


def resolve_version(plugin_dir: Path) -> tuple[str | None, str]:
    """Resolve the authoritative version for a plugin directory.

    Returns (version, source_label) where source_label describes where
    the version came from (for reporting).

    Priority:
    1. .claude-plugin/plugin.json "version" field
    2. Highest SKILL.md version across all skills (handles multi-skill plugins)
    """
    # Try plugin.json first
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"
    if plugin_json.is_file():
        try:
            with open(plugin_json) as f:
                data = json.load(f)
            version = data.get("version")
            if version:
                return version, "plugin.json"
        except (json.JSONDecodeError, OSError):
            pass

    # Fall back to SKILL.md frontmatter — use highest version across all skills
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return None, "no source"

    skill_dirs = [
        d for d in sorted(skills_dir.iterdir())
        if d.is_dir() and not d.name.startswith(".")
        and (d / "SKILL.md").exists()
    ]

    if len(skill_dirs) == 0:
        return None, "no skills found"

    skill_versions = []
    for skill_dir in skill_dirs:
        version = _extract_skill_version(skill_dir / "SKILL.md")
        if version:
            skill_versions.append((skill_dir.name, version))

    if not skill_versions:
        return None, "SKILL.md (no version)"

    if len(skill_versions) == 1:
        name, version = skill_versions[0]
        return version, f"SKILL.md ({name})"

    # Multi-skill: select highest version
    highest_name, highest_version = max(
        skill_versions, key=lambda nv: _parse_semver(nv[1])
    )
    return highest_version, f"SKILL.md ({highest_name}, highest of {len(skill_versions)})"


# -- Sync logic --------------------------------------------------------------

def sync_versions(config: dict, repo_root: Path, dry_run: bool) -> list[dict]:
    """Compare and optionally update marketplace.json plugin versions.

    Returns a list of change records: {name, old, new, source}.
    """
    changes = []

    for plugin in config.get("plugins", []):
        name = plugin.get("name", "unknown")
        source = plugin.get("source", "")

        # Only process relative source paths
        if not isinstance(source, str) or not source.startswith("./"):
            continue

        plugin_dir = repo_root / source
        if not plugin_dir.is_dir():
            continue

        source_version, source_label = resolve_version(plugin_dir)

        if source_version is None:
            if source_label == "multi-skill (ambiguous)":
                print(
                    f"  [skip] {name}: multi-skill plugin -- "
                    f"set version in plugin.json instead",
                    file=sys.stderr,
                )
            continue

        current_version = plugin.get("version")
        if current_version == source_version:
            continue

        changes.append({
            "name": name,
            "old": current_version,
            "new": source_version,
            "source": source_label,
        })

        if not dry_run:
            plugin["version"] = source_version

    return changes


# -- Main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync plugin versions from source files to "
                    "marketplace.json.",
    )
    parser.add_argument(
        "marketplace_path", nargs="?",
        default=".claude-plugin/marketplace.json",
        help="Path to marketplace.json "
             "(default: .claude-plugin/marketplace.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would change without writing",
    )
    args = parser.parse_args()

    mp_path = Path(args.marketplace_path)
    if not mp_path.exists():
        print(f"File not found: {mp_path}", file=sys.stderr)
        sys.exit(1)

    # Repo root is parent of .claude-plugin/
    repo_root = mp_path.parent.parent

    try:
        with open(mp_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {mp_path}: {e}", file=sys.stderr)
        sys.exit(1)

    changes = sync_versions(config, repo_root, args.dry_run)

    if not changes:
        print("All versions are in sync.")
        sys.exit(0)

    # Report changes
    action = "Would update" if args.dry_run else "Updated"
    for c in changes:
        old = c["old"] or "(none)"
        print(f"  {action} {c['name']}: {old} -> {c['new']} (from {c['source']})")

    # Write updated config
    if not args.dry_run:
        with open(mp_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\n{len(changes)} version(s) synced to {mp_path}")
    else:
        print(f"\n{len(changes)} version(s) would be updated. "
              f"Run without --dry-run to apply.")

    # Exit 1 when changes are needed (useful for CI: sync.py --dry-run)
    if args.dry_run:
        sys.exit(1)


if __name__ == "__main__":
    main()
