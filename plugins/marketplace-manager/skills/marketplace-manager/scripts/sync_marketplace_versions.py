#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Sync plugin versions to marketplace.json.

Version source per plugin type:
- Plugins with .claude-plugin/plugin.json: read version from plugin.json
- Single-skill plugins (skills: ["./"]): read version from SKILL.md frontmatter

After syncing marketplace.json, also syncs README.md plugin tables.

Run this before committing changes to ensure marketplace versions stay in sync.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from utils import get_repo_root, print_verbose_info, validate_repo_structure
from sync_readme import sync_readme


def extract_frontmatter_version(skill_md_path):
    """Extract version from SKILL.md YAML frontmatter.

    Priority:
    1. metadata.version (Agent Skills spec - preferred)
    2. version (deprecated but supported)

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Tuple of (version_string, is_deprecated) or (None, None) if not found
    """
    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()

        # Match YAML frontmatter (between --- markers)
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None, None

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter for both metadata.version and version
        metadata_version = None
        version = None
        in_metadata = False

        for line in frontmatter.split('\n'):
            stripped = line.strip()
            is_indented = line.startswith(' ') or line.startswith('\t')

            if stripped.startswith('metadata:'):
                in_metadata = True
            elif in_metadata and stripped.startswith('version:'):
                # metadata.version (preferred)
                metadata_version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
                in_metadata = False
            elif not in_metadata and stripped.startswith('version:'):
                # deprecated version field
                version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
            elif stripped and not is_indented and not stripped.startswith('-'):
                in_metadata = False

        # Return preferred version
        if metadata_version:
            return metadata_version, False
        elif version:
            return version, True
        else:
            return None, None

    except Exception as e:
        print(f"⚠️  Warning: Could not read {skill_md_path}: {e}")
        return None, None


def read_plugin_json_version(plugin_json_path):
    """Read version from a plugin's .claude-plugin/plugin.json.

    Args:
        plugin_json_path: Path to plugin.json file

    Returns:
        Version string or None
    """
    try:
        with open(plugin_json_path, 'r') as f:
            data = json.load(f)
        return data.get('version')
    except Exception as e:
        print(f"⚠️  Warning: Could not read {plugin_json_path}: {e}")
        return None


def get_plugin_version(source_dir, skills):
    """Determine version source and read version for a plugin.

    Version source logic:
    - If source_dir/.claude-plugin/plugin.json exists → read from plugin.json
    - If skills: ["./"] (single-skill IS the plugin) → read from SKILL.md
    - Otherwise → None (no version source found)

    Args:
        source_dir: Resolved path to plugin source directory
        skills: List of skill paths from marketplace.json

    Returns:
        Tuple of (version, source_label, is_deprecated)
    """
    plugin_json = source_dir / '.claude-plugin' / 'plugin.json'

    if plugin_json.exists():
        version = read_plugin_json_version(plugin_json)
        if version:
            return version, 'plugin.json', False

    # Single-skill with skills: ["./"] — SKILL.md is the version source
    if len(skills) == 1 and skills[0] == './':
        skill_md = source_dir / 'SKILL.md'
        if skill_md.exists():
            version, is_deprecated = extract_frontmatter_version(skill_md)
            if version:
                return version, 'SKILL.md', is_deprecated

    return None, None, None


def get_skill_versions(source_dir, skills):
    """Get individual skill versions for informational reporting.

    Args:
        source_dir: Resolved path to plugin source directory
        skills: List of skill paths from marketplace.json

    Returns:
        List of (skill_path, version) tuples
    """
    versions = []
    for skill_path in skills:
        skill_path_clean = skill_path.lstrip('./')
        skill_dir = source_dir / skill_path_clean if skill_path_clean else source_dir
        skill_md = skill_dir / 'SKILL.md'
        if skill_md.exists():
            version, _ = extract_frontmatter_version(skill_md)
            if version:
                versions.append((skill_path_clean or './', version))
    return versions


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


def sync_versions(marketplace_path, repo_root, dry_run=False, mode='auto'):
    """Sync versions from version sources to marketplace.json.

    Version source per plugin type:
    - plugin.json (if exists) for plugins with .claude-plugin/plugin.json
    - SKILL.md for single-skill plugins with skills: ["./"]

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root directory
        dry_run: If True, don't save changes
        mode: 'auto' (auto-update) or 'manual' (warn only)

    Returns:
        Number of plugins updated, or -1 if warnings exist
    """
    marketplace_data = load_marketplace(marketplace_path)
    if not marketplace_data:
        return 0

    plugins = marketplace_data.get('plugins', [])
    if not plugins:
        print("ℹ️  No plugins found in marketplace")
        return 0

    updated_count = 0
    warnings = []

    for plugin in plugins:
        plugin_name = plugin.get('name', '(unnamed)')
        skills = plugin.get('skills', [])
        source = plugin.get('source', './')

        if not skills:
            print(f"ℹ️  Plugin '{plugin_name}' has no skills, skipping")
            continue

        # Resolve source directory
        source_path_clean = source.lstrip('./')
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        # Get plugin version from the appropriate source
        source_version, source_label, is_deprecated = get_plugin_version(source_dir, skills)

        if not source_version:
            print(f"⚠️  No version source found for plugin '{plugin_name}' at {source}")
            continue

        if is_deprecated:
            print(f"⚠️  Plugin '{plugin_name}' uses deprecated 'version' field in SKILL.md")
            print(f"   Please use 'metadata.version' instead")

        current_marketplace_version = plugin.get('version', '1.0.0')

        # Report individual skill versions for multi-skill plugins
        has_multiple_skills = len(skills) > 1
        skill_versions = get_skill_versions(source_dir, skills) if has_multiple_skills else []

        if source_version != current_marketplace_version:
            if mode == 'manual':
                print(f"⚠️  Version mismatch for plugin '{plugin_name}':")
                print(f"   Marketplace version: {current_marketplace_version}")
                print(f"   {source_label} version: {source_version}")
                if has_multiple_skills:
                    for sp, sv in skill_versions:
                        print(f"   Skill {sp}: {sv}")
                warnings.append({
                    'plugin': plugin_name,
                    'source': source_label,
                    'source_version': source_version,
                    'marketplace_version': current_marketplace_version,
                })
            else:
                print(f"🔄 Updating plugin '{plugin_name}':")
                print(f"   {current_marketplace_version} → {source_version}")
                print(f"   (from {source_label})")
                if has_multiple_skills:
                    for sp, sv in skill_versions:
                        print(f"   Skill {sp}: {sv}")

                if not dry_run:
                    plugin['version'] = source_version
                updated_count += 1
        else:
            print(f"✓ Plugin '{plugin_name}' already at version {source_version}")

    # Save changes if any updates were made
    if updated_count > 0:
        if dry_run:
            print(f"\n🔍 Dry run: Would update {updated_count} plugin(s)")
        else:
            save_marketplace(marketplace_path, marketplace_data)
            print(f"\n✅ Updated {updated_count} plugin(s)")
    elif warnings:
        print(f"\n⚠️  {len(warnings)} version mismatch(es) detected")
        print("   Run with --mode=auto to update automatically")
        print("   or update versions manually")
    else:
        print("\n✓ All plugin versions are up to date")

    return updated_count if not warnings else -1


def main():
    parser = argparse.ArgumentParser(
        description='Sync plugin versions to marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Version source per plugin type:
  - Plugins with .claude-plugin/plugin.json: version from plugin.json
  - Single-skill plugins (skills: ["./"]): version from SKILL.md

Examples:
  # Auto-sync plugin versions (default)
  %(prog)s

  # Manual mode: warn about mismatches, don't auto-update
  %(prog)s --mode=manual

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

    parser.add_argument(
        '--mode',
        choices=['auto', 'manual'],
        default='auto',
        help='Versioning mode: auto (auto-update) or manual (warn only)'
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
    if args.mode == 'manual':
        print(f"🔧 Mode: Manual (warn only, no auto-updates)")
    else:
        print(f"🔧 Mode: Auto (auto-update plugin versions)")
    print()

    updated_count = sync_versions(marketplace_path, repo_root, dry_run=args.dry_run, mode=args.mode)

    # Sync README.md from marketplace.json
    readme_path = repo_root / 'README.md'
    if readme_path.exists():
        print()  # Blank line before README sync
        readme_changed = sync_readme(marketplace_path, readme_path, dry_run=args.dry_run)
        if readme_changed:
            if args.dry_run:
                print("   Run without --dry-run to apply README changes")
        else:
            print("✓ README.md already up to date")
    else:
        if args.verbose:
            print(f"ℹ️  No README.md found at {readme_path}, skipping README sync")

    if args.dry_run and updated_count > 0:
        return 1  # Exit with error in dry-run mode if changes needed

    if updated_count < 0:
        return 1  # Exit with error if warnings exist

    return 0


if __name__ == '__main__':
    sys.exit(main())
