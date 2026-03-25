#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Migrate per-skill README.md metrics into plugin-level README.md.

Extracts Current Metrics and Version History from each skill's README.md
and appends them as ## Skill: <name> sections in the plugin's README.md.
Also renames ## Version History to ## Changelog in plugin READMEs.

Usage:
    uv run migrate_readme_to_plugin.py [--dry-run] [--path <repo-root>]
"""

import argparse
import re
import sys
from pathlib import Path

from utils import get_repo_root


def extract_section(content, heading):
    """Extract a markdown section by heading (## level).

    Returns the section body (without the heading line) up to the next
    same-level or higher heading, --- separator, or end of file.
    Returns None if heading not found.
    """
    pattern = rf'(?m)^{re.escape(heading)}\s*\n(.*?)(?=\n## |\n---|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def build_skill_section(skill_name, metrics_body, history_body):
    """Build a ## Skill: <name> section with subsections."""
    lines = [f'\n## Skill: {skill_name}\n']
    if metrics_body:
        lines.append(f'### Current Metrics\n\n{metrics_body}\n')
    if history_body:
        lines.append(f'### Version History\n\n{history_body}\n')
    return '\n'.join(lines)


def migrate_plugin(plugin_dir, dry_run=False):
    """Migrate skill READMEs into a plugin's README.md.

    Returns list of actions taken.
    """
    actions = []
    plugin_name = plugin_dir.name
    plugin_readme = plugin_dir / 'README.md'

    if not plugin_readme.exists():
        actions.append(f"  SKIP {plugin_name}: no plugin README.md")
        return actions

    content = plugin_readme.read_text(encoding='utf-8')

    # Check for existing ## Skill: sections to avoid duplicates
    existing_skills = set(re.findall(r'^## Skill: (.+)$', content, re.MULTILINE))

    # Rename ## Version History to ## Changelog (if not already done)
    if '\n## Version History' in content and '\n## Changelog' not in content:
        content = content.replace('\n## Version History', '\n## Changelog')
        actions.append(f"  RENAME {plugin_name}: ## Version History -> ## Changelog")

    # Find skill READMEs
    skills_dir = plugin_dir / 'skills'
    if not skills_dir.exists():
        actions.append(f"  SKIP {plugin_name}: no skills/ directory")
        return actions

    skill_sections = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_readme = skill_dir / 'README.md'
        if not skill_readme.exists():
            continue

        skill_name = skill_dir.name

        if skill_name in existing_skills:
            actions.append(f"  SKIP {plugin_name}/skills/{skill_name}: "
                           f"## Skill: {skill_name} already exists in plugin README")
            continue

        skill_content = skill_readme.read_text(encoding='utf-8')

        # Extract sections
        metrics_body = extract_section(skill_content, '## Current Metrics')
        history_body = extract_section(skill_content, '## Version History')

        if not metrics_body and not history_body:
            actions.append(f"  SKIP {plugin_name}/skills/{skill_name}: "
                           f"no metrics or history sections found")
            continue

        section = build_skill_section(skill_name, metrics_body, history_body)
        skill_sections.append(section)
        actions.append(f"  MERGE {plugin_name}/skills/{skill_name} -> "
                       f"## Skill: {skill_name}")

    if skill_sections:
        # Append skill sections to plugin README
        # Remove trailing whitespace/newlines, add sections, ensure trailing newline
        content = content.rstrip() + '\n' + '\n'.join(skill_sections) + '\n'

        if not dry_run:
            plugin_readme.write_text(content, encoding='utf-8')
            actions.append(f"  WRITE {plugin_readme}")
        else:
            actions.append(f"  WOULD WRITE {plugin_readme}")

    return actions


def main():
    parser = argparse.ArgumentParser(
        description="Migrate per-skill README.md metrics to plugin-level README.md"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing files"
    )
    parser.add_argument(
        "--path", default=".",
        help="Repository root path (default: auto-detect)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed output"
    )

    args = parser.parse_args()
    repo_root = get_repo_root(args.path, verbose=args.verbose)

    plugins_dir = repo_root / 'plugins'
    if not plugins_dir.exists():
        print("No plugins/ directory found")
        return 1

    if args.dry_run:
        print("DRY RUN — no files will be modified\n")

    all_actions = []
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        if not (plugin_dir / '.claude-plugin').exists():
            continue

        print(f"Processing: {plugin_dir.name}")
        actions = migrate_plugin(plugin_dir, dry_run=args.dry_run)
        all_actions.extend(actions)
        for action in actions:
            print(action)
        print()

    # Summary
    merges = sum(1 for a in all_actions if 'MERGE' in a)
    renames = sum(1 for a in all_actions if 'RENAME' in a)
    skips = sum(1 for a in all_actions if 'SKIP' in a)
    print(f"Summary: {merges} merged, {renames} renamed, {skips} skipped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
