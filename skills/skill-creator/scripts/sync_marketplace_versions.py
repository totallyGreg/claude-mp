#!/usr/bin/env python3
"""
Sync skill versions from SKILL.md files to marketplace.json.

This script:
- Scans all skills referenced in marketplace.json
- Reads version from each SKILL.md frontmatter
- Updates the corresponding plugin version in marketplace.json
- Reports any changes made

Run this before committing changes to ensure marketplace versions stay in sync.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from utils import get_repo_root, print_verbose_info, validate_repo_structure


def extract_frontmatter_version(skill_md_path):
    """Extract version from SKILL.md YAML frontmatter.

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Version string or None if not found
    """
    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()

        # Match YAML frontmatter (between --- markers)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter = frontmatter_match.group(1)

        # Extract version field
        version_match = re.search(r'^version:\s*([^\n]+)', frontmatter, re.MULTILINE)
        if version_match:
            return version_match.group(1).strip()

        return None

    except Exception as e:
        print(f"⚠️  Warning: Could not read {skill_md_path}: {e}")
        return None


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


def save_marketplace(marketplace_path, marketplace_data):
    """Save marketplace.json with pretty formatting."""
    with open(marketplace_path, 'w') as f:
        json.dump(marketplace_data, f, indent=2)
    print(f"✅ Updated marketplace: {marketplace_path}")


def sync_versions(marketplace_path, repo_root, dry_run=False):
    """Sync versions from SKILL.md files to marketplace.json.

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root directory
        dry_run: If True, don't save changes

    Returns:
        Number of plugins updated
    """
    marketplace_data = load_marketplace(marketplace_path)
    if not marketplace_data:
        return 0

    plugins = marketplace_data.get('plugins', [])
    if not plugins:
        print("ℹ️  No plugins found in marketplace")
        return 0

    updated_count = 0

    for plugin in plugins:
        plugin_name = plugin.get('name', '(unnamed)')
        skills = plugin.get('skills', [])

        if not skills:
            print(f"ℹ️  Plugin '{plugin_name}' has no skills, skipping")
            continue

        # For plugins with multiple skills, use the first skill's version
        # This assumes all skills in a plugin should share the same version
        first_skill_path = skills[0].lstrip('./')
        skill_md = repo_root / first_skill_path / 'SKILL.md'

        if not skill_md.exists():
            print(f"⚠️  SKILL.md not found for plugin '{plugin_name}': {skill_md}")
            continue

        skill_version = extract_frontmatter_version(skill_md)

        if not skill_version:
            print(f"ℹ️  No version found in {first_skill_path}/SKILL.md, skipping plugin '{plugin_name}'")
            continue

        current_plugin_version = plugin.get('version', '1.0.0')

        if skill_version != current_plugin_version:
            print(f"🔄 Updating plugin '{plugin_name}':")
            print(f"   {current_plugin_version} → {skill_version}")
            print(f"   (from {first_skill_path}/SKILL.md)")

            if not dry_run:
                plugin['version'] = skill_version
            updated_count += 1
        else:
            print(f"✓ Plugin '{plugin_name}' already at version {skill_version}")

    if updated_count > 0:
        if dry_run:
            print(f"\n🔍 Dry run: Would update {updated_count} plugin(s)")
        else:
            save_marketplace(marketplace_path, marketplace_data)
            print(f"\n✅ Updated {updated_count} plugin(s)")
    else:
        print("\n✓ All plugin versions are up to date")

    return updated_count


def main():
    parser = argparse.ArgumentParser(
        description='Sync skill versions from SKILL.md to marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync versions in current directory
  %(prog)s

  # Sync versions in specific repository
  %(prog)s --path /path/to/repo

  # Preview changes without saving
  %(prog)s --dry-run

  # Use in git pre-commit hook
  %(prog)s || exit 1
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

    # Determine paths with auto-detection
    repo_root = get_repo_root(args.path, verbose=args.verbose)
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'

    # Print verbose info if requested
    if args.verbose:
        print_verbose_info(repo_root, marketplace_path)

    # Validate repository structure
    if not validate_repo_structure(repo_root, 'sync'):
        sys.exit(1)

    if not marketplace_path.exists():
        print(f"❌ No marketplace found")
        print(f"   Expected location: {marketplace_path}")
        print(f"   Repository root: {repo_root}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"\n   This script requires .claude-plugin/marketplace.json")
        print(f"   Please run add_to_marketplace.py init first")
        return 1

    print(f"📦 Syncing versions for marketplace: {marketplace_path}")
    print()

    updated_count = sync_versions(marketplace_path, repo_root, dry_run=args.dry_run)

    if args.dry_run and updated_count > 0:
        return 1  # Exit with error in dry-run mode if changes needed

    return 0


if __name__ == '__main__':
    sys.exit(main())
