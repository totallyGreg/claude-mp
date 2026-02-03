#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Create a new standalone plugin structure.

Usage:
    python3 create_plugin.py <plugin-name> [options]

Examples:
    python3 create_plugin.py my-plugin --description "My plugin description"
    python3 create_plugin.py my-plugin --skill ./skills/my-skill --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

from utils import find_repo_root


def create_plugin_structure(
    repo_root: Path,
    plugin_name: str,
    description: str,
    author_name: str,
    author_email: str,
    skill_path: str | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Create a new standalone plugin directory structure.

    Args:
        repo_root: Repository root path
        plugin_name: Name of the plugin to create
        description: Plugin description
        author_name: Author's name
        author_email: Author's email
        skill_path: Optional path to existing skill to include
        dry_run: If True, preview changes without creating files
        verbose: If True, show detailed output

    Returns:
        True if successful, False otherwise
    """
    plugins_dir = repo_root / "plugins"
    plugin_dir = plugins_dir / plugin_name

    # Check if plugin already exists
    if plugin_dir.exists():
        print(f"❌ Error: Plugin directory already exists: {plugin_dir}")
        return False

    # Define structure to create
    directories = [
        plugin_dir / ".claude-plugin",
        plugin_dir / "commands",
        plugin_dir / "skills" / plugin_name,
    ]

    # Create plugin.json content
    plugin_json = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": description,
        "author": {
            "name": author_name,
            "email": author_email,
        },
        "license": "MIT",
        "keywords": [plugin_name],
    }

    if dry_run:
        print(f"🔍 [DRY RUN] Would create plugin: {plugin_name}")
        print()
        print("Directories to create:")
        for d in directories:
            print(f"  📁 {d.relative_to(repo_root)}")
        print()
        print("Files to create:")
        print(f"  📄 {(plugin_dir / '.claude-plugin' / 'plugin.json').relative_to(repo_root)}")
        print(json.dumps(plugin_json, indent=2))
        print()

        if skill_path:
            print(f"Would copy skill from: {skill_path}")
        return True

    # Create directories
    if verbose:
        print(f"📁 Creating plugin structure at: {plugin_dir}")

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"  ✅ Created: {d.relative_to(repo_root)}")

    # Write plugin.json
    plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
    with open(plugin_json_path, "w") as f:
        json.dump(plugin_json, f, indent=2)
        f.write("\n")

    if verbose:
        print(f"  ✅ Created: {plugin_json_path.relative_to(repo_root)}")

    # Create placeholder SKILL.md
    skill_md_path = plugin_dir / "skills" / plugin_name / "SKILL.md"
    skill_md_content = f"""---
name: {plugin_name}
description: Description of {plugin_name} skill
metadata:
  version: "1.0.0"
  author: {author_name}
  license: MIT
---

# {plugin_name.replace('-', ' ').title()}

{description}

## When to Use

Use this skill when:
- TODO: Add use cases

## Quick Commands

| Command | Purpose |
|---------|---------|
| TODO | Add commands |

## Core Operations

TODO: Document core operations

## Reference Documentation

For detailed documentation, see:
- `references/` - Reference documentation
"""
    with open(skill_md_path, "w") as f:
        f.write(skill_md_content)

    if verbose:
        print(f"  ✅ Created: {skill_md_path.relative_to(repo_root)}")

    print(f"✅ Created plugin: {plugin_name}")
    print(f"   Location: {plugin_dir.relative_to(repo_root)}")
    print()
    print("Next steps:")
    print(f"  1. Edit {skill_md_path.relative_to(repo_root)}")
    print(f"  2. Add commands to {(plugin_dir / 'commands').relative_to(repo_root)}/")
    print("  3. Run: python3 scripts/add_to_marketplace.py create-plugin ...")

    return True


def update_marketplace(
    repo_root: Path,
    plugin_name: str,
    description: str,
    author_name: str,
    author_email: str,
    dry_run: bool = False,
) -> bool:
    """Add the new plugin to marketplace.json.

    Args:
        repo_root: Repository root path
        plugin_name: Plugin name
        description: Plugin description
        author_name: Author name
        author_email: Author email
        dry_run: If True, preview changes

    Returns:
        True if successful
    """
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    if not marketplace_path.exists():
        print(f"⚠️  marketplace.json not found at {marketplace_path}")
        print("   You'll need to add the plugin manually")
        return True

    with open(marketplace_path) as f:
        marketplace = json.load(f)

    # Create new plugin entry
    new_entry = {
        "name": plugin_name,
        "description": description,
        "category": "development",
        "version": "1.0.0",
        "author": {
            "name": author_name,
            "email": author_email,
        },
        "source": f"./plugins/{plugin_name}",
        "skills": [f"./skills/{plugin_name}"],
    }

    if dry_run:
        print("Would add to marketplace.json:")
        print(json.dumps(new_entry, indent=2))
        return True

    # Check for duplicate
    for plugin in marketplace.get("plugins", []):
        if plugin.get("name") == plugin_name:
            print(f"⚠️  Plugin '{plugin_name}' already in marketplace.json")
            return True

    marketplace.setdefault("plugins", []).append(new_entry)

    with open(marketplace_path, "w") as f:
        json.dump(marketplace, f, indent=2)
        f.write("\n")

    print(f"✅ Added '{plugin_name}' to marketplace.json")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Create a new standalone plugin structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s my-plugin --description "My plugin description"
    %(prog)s my-plugin --skill ./skills/my-skill --dry-run
        """,
    )
    parser.add_argument("plugin_name", help="Name of the plugin to create")
    parser.add_argument(
        "--description",
        "-d",
        default="A Claude Code plugin",
        help="Plugin description",
    )
    parser.add_argument("--author-name", default="J. Greg Williams", help="Author name")
    parser.add_argument(
        "--author-email",
        default="283704+totallyGreg@users.noreply.github.com",
        help="Author email",
    )
    parser.add_argument("--skill", help="Path to existing skill to include")
    parser.add_argument(
        "--add-to-marketplace",
        action="store_true",
        help="Also add to marketplace.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without creating files",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--path", default=".", help="Repository path")

    args = parser.parse_args()

    # Find repository root
    repo_root = find_repo_root(args.path if args.path != "." else None)
    if repo_root is None:
        print("❌ Error: Could not find repository root")
        sys.exit(1)

    if args.verbose:
        print(f"📁 Repository root: {repo_root}")

    # Create plugin structure
    success = create_plugin_structure(
        repo_root=repo_root,
        plugin_name=args.plugin_name,
        description=args.description,
        author_name=args.author_name,
        author_email=args.author_email,
        skill_path=args.skill,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    if not success:
        sys.exit(1)

    # Optionally add to marketplace
    if args.add_to_marketplace:
        update_marketplace(
            repo_root=repo_root,
            plugin_name=args.plugin_name,
            description=args.description,
            author_name=args.author_name,
            author_email=args.author_email,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    main()
