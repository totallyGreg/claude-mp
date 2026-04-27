#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Plugin creator and legacy skill migrator.

Subcommands:
    create <name>       Create a new plugin with official Anthropic structure
    migrate <skill-path> Move a legacy flat skill into plugin structure

Examples:
    python3 scaffold.py create my-plugin --description "Does things"
    python3 scaffold.py create my-plugin --with-commands --with-agents
    python3 scaffold.py create my-plugin --no-plugin-json
    python3 scaffold.py migrate skills/old-skill --dry-run
    python3 scaffold.py migrate old-skill
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# YAML frontmatter parsing (try pyyaml, fall back to stdlib)
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
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

    Handles:  name: value, metadata:\\n  version: "1.0.0", quoted/unquoted values
    Skips:    multi-line strings (>- |), anchors, aliases, sequences
    """
    result: dict = {}
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _git_available() -> bool:
    """Return True if git is available and we are inside a work tree."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, check=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def _find_marketplace_json(plugins_dir: Path) -> Path | None:
    """Look for marketplace.json starting from the plugins dir upward."""
    for parent in [plugins_dir.parent, plugins_dir.parent.parent]:
        candidate = parent / ".claude-plugin" / "marketplace.json"
        if candidate.is_file():
            return candidate
    return None


def _write_json(path: Path, data: dict) -> None:
    """Write JSON with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _make_plugin_json(name: str, description: str | None) -> dict:
    """Build a plugin.json dict using only official schema fields."""
    manifest: dict = {"name": name, "version": "1.0.0"}
    if description:
        manifest["description"] = description
    return manifest


SKILL_MD_TEMPLATE = """\
---
name: "{name}"
description: "{description}"
version: "1.0.0"
---

# {title}

{description}

## Usage

<!-- Describe how to use this skill -->
"""


def _make_skill_md(name: str, description: str) -> str:
    """Render a SKILL.md template."""
    title = name.replace("-", " ").title()
    return SKILL_MD_TEMPLATE.format(
        name=name,
        description=description,
        title=title,
    )


MCP_JSON_TEMPLATE = """\
{
  "mcpServers": {}
}
"""


# ---------------------------------------------------------------------------
# create subcommand
# ---------------------------------------------------------------------------

def cmd_create(args: argparse.Namespace) -> int:
    """Create a new plugin with official Anthropic directory structure."""
    name: str = args.name
    plugins_dir = Path(args.plugins_dir).resolve()
    plugin_root = plugins_dir / name
    description = args.description or f"A Claude Code plugin for {name}"

    if plugin_root.exists():
        print(f"ERROR: Directory already exists: {plugin_root}", file=sys.stderr)
        return 1

    # Core directories
    skill_dir = plugin_root / "skills" / name
    skill_dir.mkdir(parents=True)

    # plugin.json (unless --no-plugin-json)
    if not args.no_plugin_json:
        manifest = _make_plugin_json(name, description)
        manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
        _write_json(manifest_path, manifest)
        print(f"  Created {manifest_path.relative_to(plugins_dir.parent)}")

    # SKILL.md
    skill_md_path = skill_dir / "SKILL.md"
    skill_md_path.write_text(_make_skill_md(name, description))
    print(f"  Created {skill_md_path.relative_to(plugins_dir.parent)}")

    # Optional directories
    if args.with_commands:
        commands_dir = plugin_root / "commands"
        commands_dir.mkdir()
        print(f"  Created {commands_dir.relative_to(plugins_dir.parent)}/")

    if args.with_agents:
        agents_dir = plugin_root / "agents"
        agents_dir.mkdir()
        print(f"  Created {agents_dir.relative_to(plugins_dir.parent)}/")

    if args.with_mcp:
        mcp_path = plugin_root / ".mcp.json"
        mcp_path.write_text(MCP_JSON_TEMPLATE)
        print(f"  Created {mcp_path.relative_to(plugins_dir.parent)}")

    print(f"\nPlugin '{name}' created at {plugin_root}")
    if args.no_plugin_json:
        print("  (no plugin.json -- Claude Code will auto-discover components)")
    return 0


# ---------------------------------------------------------------------------
# migrate subcommand
# ---------------------------------------------------------------------------

def cmd_migrate(args: argparse.Namespace) -> int:
    """Migrate a legacy flat skill into plugin structure."""
    raw_path = args.skill_path
    plugins_dir = Path(args.plugins_dir).resolve()
    dry_run: bool = args.dry_run

    # Normalise: accept "skills/foo", "foo", or an absolute path
    skill_path = Path(raw_path)
    if not skill_path.is_absolute():
        # If it looks like "skills/foo", resolve relative to cwd
        skill_path = Path.cwd() / skill_path
    skill_path = skill_path.resolve()

    # Derive the skill name from the directory name
    skill_name = skill_path.name

    # If the user passed just a name (e.g. "old-skill"), try skills/<name>
    if not skill_path.is_dir():
        alt = Path.cwd() / "skills" / skill_name
        if alt.is_dir():
            skill_path = alt
        else:
            print(f"ERROR: Skill directory not found: {skill_path}", file=sys.stderr)
            return 1

    # Verify SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR: No SKILL.md found in {skill_path}", file=sys.stderr)
        return 1

    # Target structure
    plugin_root = plugins_dir / skill_name
    target_skill_dir = plugin_root / "skills" / skill_name

    if plugin_root.exists():
        print(f"ERROR: Target directory already exists: {plugin_root}", file=sys.stderr)
        return 1

    # Parse SKILL.md for metadata
    frontmatter = parse_frontmatter(skill_md.read_text())
    fm_name = frontmatter.get("name", skill_name)
    fm_description = frontmatter.get("description", "")
    fm_version = frontmatter.get("version", "1.0.0")
    # Handle nested metadata.version
    if isinstance(frontmatter.get("metadata"), dict):
        fm_version = frontmatter["metadata"].get("version", fm_version)

    # Plan the migration steps
    steps: list[str] = []
    steps.append(f"mkdir -p {target_skill_dir}")
    steps.append(f"git mv {skill_path} {target_skill_dir.parent / skill_name}")

    manifest_data = _make_plugin_json(fm_name, fm_description)
    manifest_data["version"] = fm_version
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    steps.append(f"create {manifest_path}")

    # Check marketplace.json
    marketplace_json = _find_marketplace_json(plugins_dir)
    marketplace_update = None
    if marketplace_json and marketplace_json.is_file():
        mp_data = json.loads(marketplace_json.read_text())
        old_source = f"./skills/{skill_name}"
        new_source = f"./plugins/{skill_name}"
        for plugin_entry in mp_data.get("plugins", []):
            src = plugin_entry.get("source", "")
            if isinstance(src, str) and (src == old_source or src.rstrip("/") == old_source.rstrip("/")):
                marketplace_update = (marketplace_json, plugin_entry, old_source, new_source)
                steps.append(f"update marketplace.json: source '{old_source}' -> '{new_source}'")
                break

    # Preview or execute
    print(f"Migrating skill '{skill_name}' to plugin structure:\n")
    for step in steps:
        prefix = "[DRY RUN] " if dry_run else "  "
        print(f"{prefix}{step}")

    if dry_run:
        print("\nDry run complete. No changes made.")
        return 0

    # Check git is available
    if not _git_available():
        print("ERROR: git is not available or not inside a work tree.", file=sys.stderr)
        return 1

    # Execute migration
    # 1. Create target parent directories
    target_skill_dir.parent.mkdir(parents=True, exist_ok=True)

    # 2. git mv the skill directory
    result = subprocess.run(
        ["git", "mv", str(skill_path), str(target_skill_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"ERROR: git mv failed: {result.stderr.strip()}", file=sys.stderr)
        return 1
    print(f"  Moved {skill_path} -> {target_skill_dir}")

    # 3. Create plugin.json
    _write_json(manifest_path, manifest_data)
    print(f"  Created {manifest_path}")

    # 4. Update marketplace.json if applicable
    if marketplace_update:
        mp_file, _entry, old_src, new_src = marketplace_update
        mp_data = json.loads(mp_file.read_text())
        for plugin_entry in mp_data.get("plugins", []):
            src = plugin_entry.get("source", "")
            if isinstance(src, str) and src.rstrip("/") == old_src.rstrip("/"):
                plugin_entry["source"] = new_src
                break
        _write_json(mp_file, mp_data)
        print(f"  Updated {mp_file}: source '{old_src}' -> '{new_src}'")

    print(f"\nMigration complete. Plugin '{skill_name}' is now at {plugin_root}")
    print("Remember to 'git add' the new files and commit the migration.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with create and migrate subcommands."""
    parser = argparse.ArgumentParser(
        description="Plugin creator and legacy skill migrator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- create --
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new plugin with official Anthropic structure",
    )
    create_parser.add_argument("name", help="Plugin name (kebab-case)")
    create_parser.add_argument(
        "--description", help="Plugin description",
    )
    create_parser.add_argument(
        "--no-plugin-json", action="store_true",
        help="Skip plugin.json (rely on auto-discovery)",
    )
    create_parser.add_argument(
        "--with-commands", action="store_true",
        help="Create a commands/ directory",
    )
    create_parser.add_argument(
        "--with-agents", action="store_true",
        help="Create an agents/ directory",
    )
    create_parser.add_argument(
        "--with-mcp", action="store_true",
        help="Create a .mcp.json template",
    )
    create_parser.add_argument(
        "--plugins-dir", default="./plugins",
        help="Base directory for plugins (default: ./plugins)",
    )

    # -- migrate --
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Move a legacy flat skill into plugin structure",
    )
    migrate_parser.add_argument(
        "skill_path",
        help="Path to legacy skill (e.g. skills/old-skill or just old-skill)",
    )
    migrate_parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without executing",
    )
    migrate_parser.add_argument(
        "--plugins-dir", default="./plugins",
        help="Destination base directory (default: ./plugins)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "migrate":
        return cmd_migrate(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
