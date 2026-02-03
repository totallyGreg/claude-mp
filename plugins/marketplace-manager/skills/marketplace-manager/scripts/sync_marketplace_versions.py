#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
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
    """Sync versions from SKILL.md files to marketplace.json.

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root directory
        dry_run: If True, don't save changes
        mode: Versioning mode - 'auto' (auto-update single-skill plugins) or 'manual' (warn only)

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

        # Check if multi-skill plugin (skills array has multiple entries, not all "./")
        is_multi_skill = len(skills) > 1 or (len(skills) == 1 and skills[0] != './')

        # For plugins with multiple skills, check all skill versions
        if is_multi_skill:
            skill_versions = []
            for skill_path in skills:
                skill_path_clean = skill_path.lstrip('./')
                # Resolve skill path relative to source
                skill_dir = source_dir / skill_path_clean if skill_path_clean else source_dir
                skill_md = skill_dir / 'SKILL.md'
                if skill_md.exists():
                    version, _ = extract_frontmatter_version(skill_md)
                    if version:
                        skill_versions.append((skill_path_clean or source, version))

            if skill_versions:
                current_plugin_version = plugin.get('version', '1.0.0')
                # Warn if any skill version changed
                for skill_path, version in skill_versions:
                    if version != current_plugin_version:
                        warnings.append({
                            'plugin': plugin_name,
                            'skill': skill_path,
                            'skill_version': version,
                            'plugin_version': current_plugin_version
                        })
                if not any(v == current_plugin_version for _, v in skill_versions):
                    print(f"⚠️  Multi-skill plugin '{plugin_name}' version mismatch detected")
                    print(f"   Plugin version: {current_plugin_version}")
                    for skill_path, version in skill_versions:
                        print(f"   Skill {skill_path}: {version}")
                    print(f"   → Manual plugin version update recommended")
                else:
                    print(f"✓ Plugin '{plugin_name}' version matches at least one skill")
            continue

        # Single-skill plugin handling (skills = ["./"])
        # SKILL.md is in the source directory
        skill_md = source_dir / 'SKILL.md'

        if not skill_md.exists():
            print(f"⚠️  SKILL.md not found for plugin '{plugin_name}': {skill_md}")
            continue

        skill_version, is_deprecated = extract_frontmatter_version(skill_md)

        if not skill_version:
            print(f"ℹ️  No version found in {source}/SKILL.md, skipping plugin '{plugin_name}'")
            continue

        if is_deprecated:
            print(f"⚠️  Plugin '{plugin_name}' skill uses deprecated 'version' field")
            print(f"   Please use 'metadata.version' instead in {source}/SKILL.md")

        current_plugin_version = plugin.get('version', '1.0.0')

        if skill_version != current_plugin_version:
            if mode == 'manual':
                # Manual mode: warn only, don't update
                print(f"⚠️  Version mismatch for plugin '{plugin_name}':")
                print(f"   Plugin version: {current_plugin_version}")
                print(f"   Skill version:  {skill_version} (from {source}/SKILL.md)")
                print(f"   → Please update plugin version manually in marketplace.json")
                warnings.append({
                    'plugin': plugin_name,
                    'skill': source,
                    'skill_version': skill_version,
                    'plugin_version': current_plugin_version
                })
            else:
                # Auto mode: update single-skill plugins
                print(f"🔄 Updating plugin '{plugin_name}':")
                print(f"   {current_plugin_version} → {skill_version}")
                print(f"   (from {source}/SKILL.md)")

                if not dry_run:
                    plugin['version'] = skill_version
                updated_count += 1
        else:
            print(f"✓ Plugin '{plugin_name}' already at version {skill_version}")

    # Save changes if any updates were made
    if updated_count > 0:
        if dry_run:
            print(f"\n🔍 Dry run: Would update {updated_count} plugin(s)")
        else:
            save_marketplace(marketplace_path, marketplace_data)
            print(f"\n✅ Updated {updated_count} plugin(s)")
    elif warnings:
        print(f"\n⚠️  {len(warnings)} version mismatch(es) detected")
        print("   Run with --mode=auto to update single-skill plugins automatically")
        print("   or update plugin versions manually in marketplace.json")
    else:
        print("\n✓ All plugin versions are up to date")

    return updated_count if not warnings else -1  # Return -1 if warnings exist


def main():
    parser = argparse.ArgumentParser(
        description='Sync skill versions from SKILL.md to marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-sync single-skill plugin versions (default)
  %(prog)s

  # Manual mode: warn about mismatches, don't auto-update
  %(prog)s --mode=manual

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

    parser.add_argument(
        '--mode',
        choices=['auto', 'manual'],
        default='auto',
        help='Versioning mode: auto (auto-update single-skill plugins) or manual (warn only, no auto-updates)'
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
        print(f"🔧 Mode: Auto (auto-update single-skill plugins)")
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
