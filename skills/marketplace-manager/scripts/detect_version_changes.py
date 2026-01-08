#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Detect version mismatches between SKILL.md and marketplace.json

Scans all skills in marketplace.json and compares their versions with
the version in their SKILL.md frontmatter. Reports any mismatches.

Usage:
    python3 detect_version_changes.py [--format json|text]

Week 3 Implementation Status:
    [x] Read marketplace.json
    [x] Scan skill SKILL.md frontmatter
    [x] Compare versions
    [x] Report mismatches
    [x] Support both text and JSON output
"""

import os
import sys
import json
from pathlib import Path


def find_repository_root():
    """Find git repository root"""
    current = Path.cwd()

    while current != current.parent:
        if (current / '.git').exists() or (current / '.claude-plugin').exists():
            return current
        current = current.parent

    raise Exception("Not in a git repository")


def read_marketplace_json(repo_root):
    """Read marketplace.json"""
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'

    if not marketplace_path.exists():
        raise Exception(f"marketplace.json not found at {marketplace_path}")

    with open(marketplace_path) as f:
        return json.load(f)


def read_skill_version(skill_path):
    """
    Read version from skill's SKILL.md frontmatter

    Priority:
    1. metadata.version (Agent Skills spec)
    2. version (deprecated)

    Returns: (version, is_deprecated)
    """
    skill_md = skill_path / 'SKILL.md'

    if not skill_md.exists():
        return None, None

    with open(skill_md) as f:
        content = f.read()

    # Extract frontmatter
    if not content.startswith('---'):
        return None, None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, None

    frontmatter = parts[1].strip()

    # Parse frontmatter
    metadata_version = None
    version = None
    in_metadata = False

    for line in frontmatter.split('\n'):
        line = line.strip()

        if line.startswith('metadata:'):
            in_metadata = True
        elif in_metadata and line.startswith('version:'):
            # metadata.version (preferred)
            metadata_version = line.split(':', 1)[1].strip().strip('"')
            in_metadata = False
        elif not in_metadata and line.startswith('version:'):
            # deprecated version field
            version = line.split(':', 1)[1].strip().strip('"')
        elif line and not line.startswith(' ') and not line.startswith('-'):
            in_metadata = False

    # Return preferred version
    if metadata_version:
        return metadata_version, False
    elif version:
        return version, True
    else:
        return None, None


def detect_version_changes(repo_root, marketplace_data):
    """
    Detect version mismatches between skills and marketplace

    Returns: {
        'mismatches': [
            {
                'skill_name': str,
                'skill_path': str,
                'skill_version': str,
                'marketplace_version': str,
                'plugin': str,
                'using_deprecated_field': bool
            }
        ],
        'errors': [
            {
                'skill_path': str,
                'error': str
            }
        ]
    }
    """
    mismatches = []
    errors = []

    for plugin in marketplace_data.get('plugins', []):
        plugin_name = plugin.get('name', 'unknown')
        plugin_version = plugin.get('version', 'unknown')

        for skill_path_str in plugin.get('skills', []):
            skill_path = repo_root / skill_path_str.lstrip('./')

            # Read skill version
            skill_version, is_deprecated = read_skill_version(skill_path)

            if skill_version is None:
                errors.append({
                    'skill_path': skill_path_str,
                    'error': 'Could not read version from SKILL.md'
                })
                continue

            # Compare versions
            if skill_version != plugin_version:
                skill_name = skill_path.name

                mismatches.append({
                    'skill_name': skill_name,
                    'skill_path': skill_path_str,
                    'skill_version': skill_version,
                    'marketplace_version': plugin_version,
                    'plugin': plugin_name,
                    'using_deprecated_field': is_deprecated
                })

    return {
        'mismatches': mismatches,
        'errors': errors
    }


def format_text_output(results):
    """Format results as human-readable text"""
    print("\n" + "="*60)
    print("Version Mismatch Detection")
    print("="*60 + "\n")

    mismatches = results['mismatches']
    errors = results['errors']

    if not mismatches and not errors:
        print("✓ All skill versions are synchronized with marketplace.json\n")
        return

    if mismatches:
        print(f"Mismatches found: {len(mismatches)}\n")

        for m in mismatches:
            print(f"{m['skill_name']}:")
            print(f"  SKILL.md:         {m['skill_version']}")
            print(f"  marketplace.json: {m['marketplace_version']}")
            print(f"  Plugin:           {m['plugin']}")

            if m['using_deprecated_field']:
                print(f"  ⚠ Using deprecated 'version' field (use 'metadata.version')")

            print(f"  → Sync needed\n")

    if errors:
        print(f"Errors: {len(errors)}\n")

        for e in errors:
            print(f"{e['skill_path']}:")
            print(f"  Error: {e['error']}\n")

    print("="*60)
    print("Run sync: python3 scripts/sync_marketplace_versions.py")
    print("="*60 + "\n")


def main():
    """Main entry point"""
    output_format = 'text'

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    try:
        # Find repository
        repo_root = find_repository_root()

        # Read marketplace.json
        marketplace_data = read_marketplace_json(repo_root)

        # Detect changes
        results = detect_version_changes(repo_root, marketplace_data)

        # Output results
        if output_format == 'json':
            print(json.dumps(results, indent=2))
        else:
            format_text_output(results)

        # Exit with error code if mismatches found
        if results['mismatches'] or results['errors']:
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
