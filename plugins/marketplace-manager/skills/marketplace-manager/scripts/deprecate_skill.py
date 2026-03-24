#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Automated skill deprecation workflow for Claude Code marketplace.

This script helps deprecate skills by:
- Removing plugin from marketplace.json
- Scanning for references in other skills
- Generating cleanup checklist
- Creating optional migration guide

Usage:
    uv run scripts/deprecate_skill.py --skill skill-planner \\
        --reason "Superseded by WORKFLOW.md GitHub Issues pattern" \\
        --migration-notes "Use GitHub Issues + docs/plans/ instead"
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from utils import (
    get_repo_root, print_verbose_info, validate_repo_structure,
    load_marketplace, save_marketplace,
)


def find_plugin_with_index(marketplace_data, plugin_name):
    """Find a plugin by name in the marketplace, returning its index too."""
    for idx, plugin in enumerate(marketplace_data.get('plugins', [])):
        if plugin.get('name') == plugin_name:
            return plugin, idx
    return None, -1


def scan_skill_references(repo_root, skill_name):
    """Scan all SKILL.md files for references to the deprecated skill.

    Args:
        repo_root: Repository root path
        skill_name: Name of skill to search for

    Returns:
        List of tuples (skill_path, line_numbers) containing references
    """
    references = []
    skills_dir = repo_root / 'skills'

    if not skills_dir.exists():
        return references

    # Search all SKILL.md files
    for skill_md in skills_dir.rglob('SKILL.md'):
        # Skip the deprecated skill's own SKILL.md
        if skill_name in str(skill_md.parent):
            continue

        try:
            with open(skill_md, 'r') as f:
                lines = f.readlines()

            matching_lines = []
            for line_num, line in enumerate(lines, 1):
                # Look for skill name in text (case-insensitive)
                if skill_name.lower() in line.lower():
                    matching_lines.append((line_num, line.strip()))

            if matching_lines:
                references.append({
                    'skill': skill_md.parent.name,
                    'path': str(skill_md.relative_to(repo_root)),
                    'matches': matching_lines
                })
        except Exception as e:
            print(f"⚠️  Warning: Could not read {skill_md}: {e}")

    return references


def create_migration_guide(repo_root, skill_name, reason, migration_notes):
    """Create migration guide in docs/lessons/.

    Args:
        repo_root: Repository root path
        skill_name: Name of deprecated skill
        reason: Reason for deprecation
        migration_notes: Migration guidance for users

    Returns:
        Path to created guide or None
    """
    lessons_dir = repo_root / 'docs' / 'lessons'
    lessons_dir.mkdir(parents=True, exist_ok=True)

    guide_name = f"deprecation-{skill_name}-{datetime.now().strftime('%Y%m%d')}.md"
    guide_path = lessons_dir / guide_name

    content = f"""# Deprecation: {skill_name}

**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Reason**: {reason}

## Migration Guide

{migration_notes}

## What Changed

The `{skill_name}` skill has been removed from the marketplace. This document provides guidance for users who were using this skill.

## Recommended Alternatives

{migration_notes}

## Cleanup Steps

If you have `{skill_name}` installed:

1. Uninstall the skill from your Claude Code installation
2. Review any custom configurations that referenced this skill
3. Follow the migration guidance above for alternative approaches

## Questions

If you have questions about this deprecation, please:
- Review the GitHub issue that tracked this deprecation
- Check the WORKFLOW.md documentation for current patterns
- Open a discussion in the repository if clarification is needed
"""

    try:
        with open(guide_path, 'w') as f:
            f.write(content)
        return guide_path
    except Exception as e:
        print(f"⚠️  Warning: Could not create migration guide: {e}")
        return None


def generate_cleanup_checklist(skill_name, plugin_data, references, has_migration_guide):
    """Generate cleanup checklist for manual tasks.

    Args:
        skill_name: Name of deprecated skill
        plugin_data: Plugin metadata from marketplace.json
        references: List of skills referencing the deprecated skill
        has_migration_guide: Whether migration guide was created

    Returns:
        Formatted checklist string
    """
    checklist = f"""
{'='*70}
Deprecation Cleanup Checklist: {skill_name}
{'='*70}

Plugin removed from marketplace: {plugin_data['name']} v{plugin_data.get('version', 'unknown')}

MANUAL CLEANUP REQUIRED:

1. Update Skills Referencing {skill_name}:
"""

    if references:
        for ref in references:
            checklist += f"\n   [ ] {ref['skill']} ({ref['path']})\n"
            for line_num, line in ref['matches'][:3]:  # Show first 3 matches
                checklist += f"       Line {line_num}: {line[:60]}...\n"
            if len(ref['matches']) > 3:
                checklist += f"       ... and {len(ref['matches']) - 3} more\n"
    else:
        checklist += "\n   ✓ No references found in other skills\n"

    checklist += f"""
2. Delete Skill Files:
   [ ] git rm -r skills/{skill_name}/
   [ ] Commit the deletion

3. Update Documentation:
"""

    if has_migration_guide:
        checklist += f"   ✓ Migration guide created in docs/lessons/\n"
    else:
        checklist += f"   [ ] Create migration guide if needed\n"

    checklist += f"""
4. Commit Changes:
   [ ] Review all changes
   [ ] git add .claude-plugin/marketplace.json
   [ ] git commit -m "chore: Deprecate {skill_name} skill"

5. Notify Users (if applicable):
   [ ] Update CHANGELOG or release notes
   [ ] Communicate deprecation to users

{'='*70}
"""
    return checklist


def deprecate_skill(
    marketplace_path,
    repo_root,
    skill_name,
    reason,
    migration_notes=None,
    dry_run=False,
    auto_confirm=False
):
    """Deprecate a skill from the marketplace.

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root path
        skill_name: Name of skill to deprecate
        reason: Reason for deprecation
        migration_notes: Optional migration guidance
        dry_run: If True, don't make changes
        auto_confirm: If True, skip confirmation prompts

    Returns:
        True if successful, False otherwise
    """
    # Load marketplace
    marketplace_data = load_marketplace(marketplace_path)
    if not marketplace_data:
        return False

    # Find plugin
    plugin, plugin_idx = find_plugin_with_index(marketplace_data, skill_name)
    if not plugin:
        print(f"❌ Plugin '{skill_name}' not found in marketplace")
        print(f"\nAvailable plugins:")
        for p in marketplace_data.get('plugins', []):
            print(f"  - {p['name']}")
        return False

    print(f"\n📦 Found plugin: {plugin['name']} v{plugin.get('version', 'unknown')}")
    print(f"   Description: {plugin.get('description', '(none)')}")
    print(f"   Source: {plugin.get('source', './')}")

    # Scan for references
    print(f"\n🔍 Scanning for references to '{skill_name}'...")
    references = scan_skill_references(repo_root, skill_name)

    if references:
        print(f"\n⚠️  Found {len(references)} skill(s) with references:")
        for ref in references:
            print(f"   • {ref['skill']} ({len(ref['matches'])} reference(s))")
    else:
        print(f"\n✓ No references found in other skills")

    # Show what will be done
    print(f"\n📋 Deprecation Plan:")
    print(f"   1. Remove '{skill_name}' from marketplace.json")
    print(f"   2. Reason: {reason}")
    if migration_notes:
        print(f"   3. Create migration guide in docs/lessons/")
    if references:
        print(f"   4. Report {len(references)} skill(s) that need manual updates")

    # Confirm unless auto-confirm or dry-run
    if not auto_confirm and not dry_run:
        response = input(f"\nProceed with deprecation? [y/N] ")
        if response.lower() != 'y':
            print("Cancelled")
            return False

    # Create migration guide if requested
    migration_guide_path = None
    if migration_notes and not dry_run:
        print(f"\n📝 Creating migration guide...")
        migration_guide_path = create_migration_guide(
            repo_root, skill_name, reason, migration_notes
        )
        if migration_guide_path:
            print(f"✅ Migration guide: {migration_guide_path.relative_to(repo_root)}")

    # Remove from marketplace
    if dry_run:
        print(f"\n🔍 DRY RUN: Would remove plugin at index {plugin_idx}")
    else:
        marketplace_data['plugins'].pop(plugin_idx)
        save_marketplace(marketplace_path, marketplace_data)
        print(f"✅ Removed '{skill_name}' from marketplace")

    # Generate cleanup checklist
    checklist = generate_cleanup_checklist(
        skill_name, plugin, references, migration_guide_path is not None
    )
    print(checklist)

    # Save checklist to file
    if not dry_run:
        checklist_path = repo_root / f"deprecate-{skill_name}-checklist.txt"
        with open(checklist_path, 'w') as f:
            f.write(checklist)
        print(f"📄 Checklist saved to: {checklist_path.name}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Deprecate a skill from the Claude Code marketplace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deprecate a skill with reason
  %(prog)s --skill skill-planner \\
    --reason "Superseded by WORKFLOW.md GitHub Issues pattern"

  # Include migration notes
  %(prog)s --skill skill-planner \\
    --reason "Superseded by WORKFLOW.md" \\
    --migration-notes "Use GitHub Issues + docs/plans/ instead"

  # Dry run to preview changes
  %(prog)s --skill skill-planner --reason "Testing" --dry-run

  # Auto-confirm (no prompts)
  %(prog)s --skill skill-planner --reason "Automated" --yes
""",
    )

    parser.add_argument(
        '--skill',
        required=True,
        help='Name of skill/plugin to deprecate'
    )

    parser.add_argument(
        '--reason',
        required=True,
        help='Reason for deprecation'
    )

    parser.add_argument(
        '--migration-notes',
        help='Migration guidance for users (creates guide in docs/lessons/)'
    )

    parser.add_argument(
        '--path',
        default='.',
        help='Repository root path (default: auto-detect)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Auto-confirm, skip prompts'
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
    if not validate_repo_structure(repo_root, 'deprecate'):
        return 1

    if not marketplace_path.exists():
        print(f"❌ No marketplace found")
        print(f"   Expected location: {marketplace_path}")
        print(f"   Repository root: {repo_root}")
        return 1

    print(f"🗑️  Deprecating skill from marketplace: {marketplace_path}")
    if args.dry_run:
        print(f"🔍 DRY RUN MODE - No changes will be made")
    print()

    success = deprecate_skill(
        marketplace_path,
        repo_root,
        args.skill,
        args.reason,
        migration_notes=args.migration_notes,
        dry_run=args.dry_run,
        auto_confirm=args.yes
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
