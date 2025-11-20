#!/usr/bin/env python3
"""
Add a skill to the Claude Code plugin marketplace.

This script helps manage the .claude-plugin/marketplace.json file by:
- Creating the marketplace structure if it doesn't exist
- Adding new skills to an existing plugin
- Creating new plugins with skills
- Validating the marketplace.json structure
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_marketplace(marketplace_path):
    """Load existing marketplace.json or return empty structure."""
    if marketplace_path.exists():
        with open(marketplace_path, "r") as f:
            return json.load(f)

    # Return empty marketplace structure
    return {
        "name": "",
        "owner": {"name": "", "email": ""},
        "metadata": {"description": "", "version": "1.0.0"},
        "plugins": [],
    }


def save_marketplace(marketplace_path, marketplace_data):
    """Save marketplace.json with pretty formatting."""
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)

    with open(marketplace_path, "w") as f:
        json.dump(marketplace_data, f, indent=2)

    print(f"✅ Updated marketplace at: {marketplace_path}")


def init_marketplace(marketplace_path, name, owner_name, owner_email, description):
    """Initialize a new marketplace.json."""
    marketplace_data = {
        "name": name,
        "owner": {"name": owner_name, "email": owner_email},
        "metadata": {"description": description, "version": "1.0.0"},
        "plugins": [],
    }

    save_marketplace(marketplace_path, marketplace_data)
    print(f"✅ Initialized new marketplace: {name}")


def find_plugin(marketplace_data, plugin_name):
    """Find a plugin by name in the marketplace."""
    for plugin in marketplace_data.get("plugins", []):
        if plugin["name"] == plugin_name:
            return plugin
    return None


def add_skill_to_plugin(marketplace_data, plugin_name, skill_path):
    """Add a skill to an existing plugin."""
    plugin = find_plugin(marketplace_data, plugin_name)

    if not plugin:
        print(f"❌ Plugin '{plugin_name}' not found in marketplace")
        return False

    # Normalize skill path
    skill_path = f"./{skill_path.strip('./')}"

    # Check if skill already exists
    if skill_path in plugin.get("skills", []):
        print(f"⚠️  Skill '{skill_path}' already exists in plugin '{plugin_name}'")
        return False

    # Add skill
    if "skills" not in plugin:
        plugin["skills"] = []

    plugin["skills"].append(skill_path)
    print(f"✅ Added skill '{skill_path}' to plugin '{plugin_name}'")
    return True


def create_plugin(marketplace_data, plugin_name, plugin_description, skill_paths):
    """Create a new plugin with skills."""
    # Check if plugin already exists
    if find_plugin(marketplace_data, plugin_name):
        print(f"❌ Plugin '{plugin_name}' already exists")
        return False

    # Normalize skill paths
    normalized_skills = [f"./{path.strip('./')}" for path in skill_paths]

    # Create new plugin
    new_plugin = {
        "name": plugin_name,
        "description": plugin_description,
        "source": "./",
        "strict": False,
        "skills": normalized_skills,
    }

    marketplace_data["plugins"].append(new_plugin)
    print(f"✅ Created new plugin: {plugin_name}")
    print(f"   Added {len(normalized_skills)} skill(s)")
    return True


def list_marketplace(marketplace_data):
    """List all plugins and skills in the marketplace."""
    print("\n📦 Marketplace:", marketplace_data.get("name", "(unnamed)"))
    print(f"   Owner: {marketplace_data.get('owner', {}).get('name', '(not set)')}")
    print(f"   Version: {marketplace_data.get('metadata', {}).get('version', '1.0.0')}")
    print(
        f"   Description: {marketplace_data.get('metadata', {}).get('description', '(none)')}"
    )

    plugins = marketplace_data.get("plugins", [])
    if not plugins:
        print("\n   No plugins configured")
        return

    print(f"\n   Plugins ({len(plugins)}):")
    for plugin in plugins:
        print(f"\n   • {plugin['name']}")
        print(f"     Description: {plugin.get('description', '(none)')}")
        skills = plugin.get("skills", [])
        if skills:
            print(f"     Skills ({len(skills)}):")
            for skill in skills:
                print(f"       - {skill}")
        else:
            print(f"     No skills")


def validate_skill_exists(skill_path, repo_root):
    """Validate that a skill directory exists and has SKILL.md."""
    skill_dir = repo_root / skill_path.lstrip("./")

    if not skill_dir.exists():
        print(f"⚠️  Warning: Skill directory not found: {skill_dir}")
        return False

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"⚠️  Warning: SKILL.md not found in: {skill_dir}")
        return False

    return True


def parse_version(version_str):
    """Parse semantic version string into (major, minor, patch) tuple."""
    try:
        parts = version_str.split(".")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, AttributeError):
        return (1, 0, 0)


def increment_version(version_str, part="patch"):
    """Increment semantic version.

    Args:
        version_str: Current version (e.g., "1.2.3")
        part: Which part to increment ('major', 'minor', or 'patch')

    Returns:
        New version string
    """
    major, minor, patch = parse_version(version_str)

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_metadata(
    marketplace_data, description=None, version=None, auto_increment=None
):
    """Update marketplace metadata.

    Args:
        marketplace_data: Marketplace data dictionary
        description: New description (optional)
        version: New version (optional)
        auto_increment: Auto-increment version ('major', 'minor', 'patch', or None)

    Returns:
        True if updated, False otherwise
    """
    metadata = marketplace_data.get("metadata", {})
    updated = False

    if description:
        old_desc = metadata.get("description", "(none)")
        metadata["description"] = description
        print(f"✅ Updated description:")
        print(f"   Old: {old_desc}")
        print(f"   New: {description}")
        updated = True

    if version:
        old_version = metadata.get("version", "1.0.0")
        metadata["version"] = version
        print(f"✅ Updated version: {old_version} → {version}")
        updated = True
    elif auto_increment:
        old_version = metadata.get("version", "1.0.0")
        new_version = increment_version(old_version, auto_increment)
        metadata["version"] = new_version
        print(
            f"✅ Auto-incremented version ({auto_increment}): {old_version} → {new_version}"
        )
        updated = True

    if updated:
        marketplace_data["metadata"] = metadata

    return updated


def main():
    parser = argparse.ArgumentParser(
        description="Manage Claude Code plugin marketplace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a new marketplace
  %(prog)s init --name my-marketplace --owner-name "John Doe" \\
    --owner-email "john@example.com" --description "My skills"

  # Create a new plugin with skills
  %(prog)s create-plugin my-plugin "Plugin description" \\
    --skills skill1 skill2 skill3

  # Add a skill to existing plugin
  %(prog)s add-skill my-plugin skill4

  # List all plugins and skills
  %(prog)s list

  # Update marketplace description
  %(prog)s update-metadata --description "New description"

  # Auto-increment version (patch: 1.0.0 → 1.0.1)
  %(prog)s update-metadata --increment patch

  # Auto-increment minor version (1.0.1 → 1.1.0)
  %(prog)s update-metadata --increment minor

  # Set specific version
  %(prog)s update-metadata --version 2.0.0

  # Update both description and version
  %(prog)s update-metadata --description "New desc" --increment minor
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new marketplace")
    init_parser.add_argument("--name", required=True, help="Marketplace name")
    init_parser.add_argument("--owner-name", required=True, help="Owner name")
    init_parser.add_argument("--owner-email", required=True, help="Owner email")
    init_parser.add_argument(
        "--description", required=True, help="Marketplace description"
    )
    init_parser.add_argument(
        "--path", default=".", help="Repository root path (default: current directory)"
    )

    # Create plugin command
    create_parser = subparsers.add_parser("create-plugin", help="Create a new plugin")
    create_parser.add_argument("name", help="Plugin name")
    create_parser.add_argument("description", help="Plugin description")
    create_parser.add_argument("--skills", nargs="+", required=True, help="Skill paths")
    create_parser.add_argument(
        "--path", default=".", help="Repository root path (default: current directory)"
    )

    # Add skill command
    add_parser = subparsers.add_parser(
        "add-skill", help="Add a skill to existing plugin"
    )
    add_parser.add_argument("plugin", help="Plugin name")
    add_parser.add_argument("skill", help="Skill path")
    add_parser.add_argument(
        "--path", default=".", help="Repository root path (default: current directory)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all plugins and skills")
    list_parser.add_argument(
        "--path", default=".", help="Repository root path (default: current directory)"
    )

    # Update metadata command
    update_parser = subparsers.add_parser(
        "update-metadata", help="Update marketplace metadata"
    )
    update_parser.add_argument("--description", help="New marketplace description")
    update_parser.add_argument("--version", help="Set specific version (e.g., '2.0.0')")
    update_parser.add_argument(
        "--increment",
        choices=["major", "minor", "patch"],
        help="Auto-increment version (major, minor, or patch)",
    )
    update_parser.add_argument(
        "--path", default=".", help="Repository root path (default: current directory)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Determine paths
    repo_root = Path(args.path).resolve()
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    # Handle commands
    if args.command == "init":
        if marketplace_path.exists():
            response = input(
                f"Marketplace already exists at {marketplace_path}. Overwrite? [y/N] "
            )
            if response.lower() != "y":
                print("Cancelled")
                return 1

        init_marketplace(
            marketplace_path,
            args.name,
            args.owner_name,
            args.owner_email,
            args.description,
        )

    elif args.command == "list":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found at {marketplace_path}")
            print(f"   Run 'init' command first")
            return 1

        marketplace_data = load_marketplace(marketplace_path)
        list_marketplace(marketplace_data)

    elif args.command == "create-plugin":
        marketplace_data = load_marketplace(marketplace_path)

        # Validate marketplace is initialized
        if not marketplace_data.get("name"):
            print("❌ Marketplace not initialized. Run 'init' command first")
            return 1

        # Validate skills exist
        for skill in args.skills:
            validate_skill_exists(skill, repo_root)

        if create_plugin(marketplace_data, args.name, args.description, args.skills):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            return 1

    elif args.command == "add-skill":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found at {marketplace_path}")
            return 1

        marketplace_data = load_marketplace(marketplace_path)

        # Validate skill exists
        validate_skill_exists(args.skill, repo_root)

        if add_skill_to_plugin(marketplace_data, args.plugin, args.skill):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            return 1

    elif args.command == "update-metadata":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found at {marketplace_path}")
            print(f"   Run 'init' command first")
            return 1

        marketplace_data = load_marketplace(marketplace_path)

        # Check if any update requested
        if not args.description and not args.version and not args.increment:
            print(
                "❌ No updates specified. Use --description, --version, or --increment"
            )
            return 1

        # Check for conflicting options
        if args.version and args.increment:
            print("❌ Cannot use both --version and --increment")
            return 1

        # Update metadata
        if update_metadata(
            marketplace_data,
            description=args.description,
            version=args.version,
            auto_increment=args.increment,
        ):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            print("❌ No changes made")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
