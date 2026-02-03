#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Sync README.md plugin tables from marketplace.json.

This script:
- Reads plugin data from marketplace.json
- Groups plugins by category
- Generates markdown tables for each category
- Updates the "Available Plugins" section in README.md

Run this after syncing marketplace.json to keep README in sync.
"""

import json
import re
import sys
from pathlib import Path

from utils import get_repo_root, validate_repo_structure


def load_marketplace(marketplace_path):
    """Load marketplace.json file."""
    try:
        with open(marketplace_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Marketplace not found: {marketplace_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in marketplace.json: {e}")
        return None


def group_plugins_by_category(plugins):
    """Group plugins by their category.

    Args:
        plugins: List of plugin dictionaries

    Returns:
        Dict mapping category name to list of plugins
    """
    categories = {}
    for plugin in plugins:
        category = plugin.get('category', 'other')
        if category not in categories:
            categories[category] = []
        categories[category].append(plugin)

    # Sort plugins within each category by name
    for category in categories:
        categories[category].sort(key=lambda p: p.get('name', ''))

    return categories


def generate_plugin_table(plugins):
    """Generate a markdown table for a list of plugins.

    Args:
        plugins: List of plugin dictionaries

    Returns:
        Markdown table string
    """
    lines = [
        "| Plugin | Version | Description |",
        "|--------|---------|-------------|"
    ]

    for plugin in plugins:
        name = plugin.get('name', 'unknown')
        version = plugin.get('version', '0.0.0')
        description = plugin.get('description', '')
        lines.append(f"| **{name}** | {version} | {description} |")

    return '\n'.join(lines)


def generate_available_plugins_section(marketplace_data):
    """Generate the full Available Plugins section.

    Args:
        marketplace_data: Parsed marketplace.json data

    Returns:
        Markdown string for the Available Plugins section
    """
    plugins = marketplace_data.get('plugins', [])
    if not plugins:
        return "## Available Plugins\n\nNo plugins available."

    categories = group_plugins_by_category(plugins)

    # Define category display order and titles
    category_order = ['development', 'productivity', 'security', 'infrastructure', 'other']
    category_titles = {
        'development': 'Development',
        'productivity': 'Productivity',
        'security': 'Security',
        'infrastructure': 'Infrastructure',
        'other': 'Other'
    }

    lines = ["## Available Plugins"]

    # Process categories in order
    for category in category_order:
        if category not in categories:
            continue

        category_plugins = categories[category]
        title = category_titles.get(category, category.title())
        count = len(category_plugins)

        lines.append("")
        lines.append(f"### {title} ({count} plugin{'s' if count != 1 else ''})")
        lines.append("")
        lines.append(generate_plugin_table(category_plugins))

    # Handle any categories not in the predefined order
    for category in sorted(categories.keys()):
        if category in category_order:
            continue

        category_plugins = categories[category]
        title = category.title()
        count = len(category_plugins)

        lines.append("")
        lines.append(f"### {title} ({count} plugin{'s' if count != 1 else ''})")
        lines.append("")
        lines.append(generate_plugin_table(category_plugins))

    return '\n'.join(lines)


def update_readme(readme_path, new_section):
    """Update the Available Plugins section in README.md.

    Args:
        readme_path: Path to README.md
        new_section: New content for Available Plugins section

    Returns:
        True if updated, False if no changes needed
    """
    try:
        with open(readme_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ README not found: {readme_path}")
        return False

    # Pattern to match the Available Plugins section
    # Matches from "## Available Plugins" to the next "## " heading or end of file
    pattern = r'(## Available Plugins\n)(.*?)(?=\n## |\Z)'

    # Check if section exists
    if not re.search(pattern, content, re.DOTALL):
        print(f"⚠️  'Available Plugins' section not found in README.md")
        print(f"   Please add '## Available Plugins' heading to README.md")
        return False

    # Replace the section
    new_content = re.sub(
        pattern,
        new_section + '\n',
        content,
        flags=re.DOTALL
    )

    if new_content == content:
        return False  # No changes

    with open(readme_path, 'w') as f:
        f.write(new_content)

    return True


def sync_readme(marketplace_path, readme_path, dry_run=False):
    """Sync README.md from marketplace.json.

    Args:
        marketplace_path: Path to marketplace.json
        readme_path: Path to README.md
        dry_run: If True, don't save changes

    Returns:
        True if changes were made (or would be made in dry-run), False otherwise
    """
    marketplace_data = load_marketplace(marketplace_path)
    if not marketplace_data:
        return False

    new_section = generate_available_plugins_section(marketplace_data)

    if dry_run:
        # Check if changes would be made
        try:
            with open(readme_path, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ README not found: {readme_path}")
            return False

        pattern = r'(## Available Plugins\n)(.*?)(?=\n## |\Z)'
        new_content = re.sub(pattern, new_section + '\n', content, flags=re.DOTALL)

        if new_content != content:
            print(f"🔍 Dry run: Would update README.md")
            return True
        return False

    if update_readme(readme_path, new_section):
        print(f"✅ Updated README.md with plugin information")
        return True

    return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Sync README.md plugin tables from marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync README from marketplace.json
  %(prog)s

  # Preview changes without saving
  %(prog)s --dry-run

  # Sync in specific repository
  %(prog)s --path /path/to/repo
""",
    )

    parser.add_argument(
        '--path',
        default='.',
        help='Repository root path (default: auto-detect)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed path resolution information'
    )

    args = parser.parse_args()

    # Determine paths
    repo_root = get_repo_root(args.path, verbose=args.verbose)
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
    readme_path = repo_root / 'README.md'

    # Validate repository structure
    if not validate_repo_structure(repo_root, 'sync'):
        sys.exit(1)

    if not marketplace_path.exists():
        print(f"❌ No marketplace found: {marketplace_path}")
        return 1

    if not readme_path.exists():
        print(f"❌ No README.md found: {readme_path}")
        return 1

    print(f"📄 Syncing README.md from marketplace.json")

    changed = sync_readme(marketplace_path, readme_path, dry_run=args.dry_run)

    if changed:
        if args.dry_run:
            return 1  # Exit with error in dry-run if changes needed
        print("✓ README.md synchronized")
    else:
        print("✓ README.md already up to date")

    return 0


if __name__ == '__main__':
    sys.exit(main())
