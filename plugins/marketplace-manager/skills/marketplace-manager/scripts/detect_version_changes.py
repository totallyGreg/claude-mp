#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Detect version mismatches between version sources and marketplace.json.

Version source per plugin type:
- Plugins with .claude-plugin/plugin.json: version from plugin.json
- Single-skill plugins (skills: ["./"]): version from SKILL.md frontmatter

Also supports checking staged files for version bump requirements.

Usage:
    python3 detect_version_changes.py [--format json|text]
    python3 detect_version_changes.py --check-staged [--format json|text]

Modes:
    Default: Check version source vs marketplace.json mismatches
    --check-staged: Check if staged files require version bumps
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

from utils import find_repo_root


# Exclusion patterns - files that don't require version bumps
EXCLUDED_PATTERNS = [
    'IMPROVEMENT_PLAN.md',
    'CHANGELOG.md',
    'LICENSE*',
    'README*',
    'docs/*',
    'references/*',
    'examples/*',
    'tests/*',
    '.gitignore',
    '.skillignore',
    '.DS_Store',
    '__pycache__/*',
    '*.pyc',
    '.claude-plugin/marketplace.json',
]


# --- Version extraction helpers ---

def extract_frontmatter_version(content):
    """Extract version from SKILL.md content string.

    Priority: metadata.version > version (deprecated)
    """
    if not content or not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    frontmatter = parts[1].strip()
    metadata_version = None
    version = None
    in_metadata = False

    for line in frontmatter.split('\n'):
        stripped = line.strip()

        if stripped.startswith('metadata:'):
            in_metadata = True
        elif in_metadata and stripped.startswith('version:'):
            metadata_version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
            in_metadata = False
        elif not in_metadata and stripped.startswith('version:'):
            version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
        elif stripped and not stripped.startswith(' ') and not stripped.startswith('-'):
            in_metadata = False

    return metadata_version or version


def extract_plugin_json_version(content):
    """Extract version from plugin.json content string."""
    if not content:
        return None
    try:
        data = json.loads(content)
        return data.get('version')
    except json.JSONDecodeError:
        return None


def read_version_from_file(filepath):
    """Read version from a file on disk (SKILL.md or plugin.json)."""
    try:
        with open(filepath) as f:
            content = f.read()
    except Exception:
        return None

    if str(filepath).endswith('SKILL.md'):
        return extract_frontmatter_version(content)
    elif str(filepath).endswith('plugin.json'):
        return extract_plugin_json_version(content)
    return None


def get_plugin_version_source(source_dir, skills):
    """Determine the version source path for a plugin.

    Returns:
        Tuple of (version_file_path, source_label) or (None, None)
    """
    plugin_json = source_dir / '.claude-plugin' / 'plugin.json'
    if plugin_json.exists():
        return plugin_json, 'plugin.json'

    if len(skills) == 1 and skills[0] == './':
        skill_md = source_dir / 'SKILL.md'
        if skill_md.exists():
            return skill_md, 'SKILL.md'

    return None, None


# --- Git helpers ---

def get_staged_files(repo_root):
    """Get list of staged files from git."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Failed to get staged files: {result.stderr}")

    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]


def get_file_content_at_ref(repo_root, filepath, ref='HEAD'):
    """Get file content at a specific git ref."""
    result = subprocess.run(
        ['git', 'show', f'{ref}:{filepath}'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout


def get_staged_content(repo_root, filepath):
    """Get staged content of a file."""
    result = subprocess.run(
        ['git', 'show', f':{filepath}'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout


# --- Staged file checks ---

def is_excluded(filepath):
    """Check if filepath matches exclusion patterns."""
    parts = Path(filepath).parts
    basename = parts[-1] if parts else ''

    for pattern in EXCLUDED_PATTERNS:
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(filepath, pattern):
            return True
        if fnmatch.fnmatch(filepath, '*/' + pattern):
            return True
        if '/' in pattern:
            dir_pattern = pattern.rstrip('/*')
            for part in parts[:-1]:
                if fnmatch.fnmatch(part, dir_pattern):
                    return True
    return False


def map_file_to_component(filepath):
    """Map a file path to its parent component's version file.

    Returns: (component_path, version_file) or (None, None)

    Mappings:
    - skills/<name>/* -> skills/<name>/SKILL.md
    - plugins/<plugin>/skills/<skill>/* -> plugins/<plugin>/skills/<skill>/SKILL.md
    - plugins/<plugin>/* (non-skill) -> plugins/<plugin>/.claude-plugin/plugin.json
    """
    parts = Path(filepath).parts

    # plugins/<plugin>/skills/<skill>/*
    if len(parts) >= 4 and parts[0] == 'plugins' and parts[2] == 'skills':
        plugin_name = parts[1]
        skill_name = parts[3]
        component_path = f"plugins/{plugin_name}/skills/{skill_name}"
        version_file = f"{component_path}/SKILL.md"
        return component_path, version_file

    # skills/<name>/*
    if len(parts) >= 2 and parts[0] == 'skills':
        skill_name = parts[1]
        component_path = f"skills/{skill_name}"
        version_file = f"{component_path}/SKILL.md"
        return component_path, version_file

    # plugins/<plugin>/* (non-skill files like agents, commands, hooks)
    if len(parts) >= 2 and parts[0] == 'plugins':
        plugin_name = parts[1]
        component_path = f"plugins/{plugin_name}"
        version_file = f"{component_path}/.claude-plugin/plugin.json"
        return component_path, version_file

    return None, None


def check_version_bumped(repo_root, version_file):
    """Check if version file is staged with an actual version change.

    Returns: (is_bumped, head_version, staged_version)
    """
    head_content = get_file_content_at_ref(repo_root, version_file, 'HEAD')
    staged_content = get_staged_content(repo_root, version_file)

    if version_file.endswith('SKILL.md'):
        extractor = extract_frontmatter_version
    elif version_file.endswith('plugin.json'):
        extractor = extract_plugin_json_version
    else:
        return False, None, None

    head_version = extractor(head_content) if head_content else None
    staged_version = extractor(staged_content) if staged_content else None

    if head_version is None and staged_version is not None:
        return True, None, staged_version

    if head_version != staged_version and staged_version is not None:
        return True, head_version, staged_version

    return False, head_version, staged_version


def detect_staged_changes(repo_root):
    """Detect staged files that require version bumps."""
    staged_files = get_staged_files(repo_root)

    component_files = {}

    for filepath in staged_files:
        if is_excluded(filepath):
            continue

        component, version_file = map_file_to_component(filepath)
        if component is None:
            continue

        if filepath == version_file:
            continue

        key = (component, version_file)
        if key not in component_files:
            component_files[key] = []
        component_files[key].append(filepath)

    missing_bumps = []
    bumped = []

    for (component, version_file), files in component_files.items():
        is_bumped, head_version, staged_version = check_version_bumped(
            repo_root, version_file
        )

        if is_bumped:
            bumped.append({
                'component': component,
                'version_file': version_file,
                'old_version': head_version,
                'new_version': staged_version
            })
        else:
            missing_bumps.append({
                'component': component,
                'version_file': version_file,
                'current_version': head_version,
                'modified_files': files
            })

    return {
        'missing_bumps': missing_bumps,
        'bumped': bumped
    }


# --- Default mode: version source vs marketplace.json ---

def detect_version_mismatches(repo_root, marketplace_data):
    """Detect mismatches between version sources and marketplace.json.

    Compares each plugin's version source (plugin.json or SKILL.md)
    against the version in marketplace.json. One check per plugin.
    """
    mismatches = []
    errors = []

    for plugin in marketplace_data.get('plugins', []):
        plugin_name = plugin.get('name', 'unknown')
        marketplace_version = plugin.get('version', 'unknown')
        source = plugin.get('source', './')
        skills = plugin.get('skills', [])

        source_path_clean = source.lstrip('./')
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        version_file, source_label = get_plugin_version_source(source_dir, skills)

        if version_file is None:
            errors.append({
                'plugin': plugin_name,
                'error': f'No version source found (no plugin.json or SKILL.md) at {source}',
            })
            continue

        actual_version = read_version_from_file(version_file)

        if actual_version is None:
            errors.append({
                'plugin': plugin_name,
                'error': f'Could not read version from {source_label}',
            })
            continue

        if actual_version != marketplace_version:
            mismatches.append({
                'plugin': plugin_name,
                'source_label': source_label,
                'source_version': actual_version,
                'marketplace_version': marketplace_version,
            })

    return {
        'mismatches': mismatches,
        'errors': errors
    }


# --- Output formatters ---

def format_text_output(results):
    """Format default mode results as human-readable text."""
    mismatches = results['mismatches']
    errors = results['errors']

    if not mismatches and not errors:
        print("✓ All plugin versions are synchronized with marketplace.json")
        return

    if mismatches:
        print(f"Mismatches found: {len(mismatches)}\n")
        for m in mismatches:
            print(f"{m['plugin']}:")
            print(f"  {m['source_label']}:      {m['source_version']}")
            print(f"  marketplace.json: {m['marketplace_version']}")
            print(f"  → Sync needed\n")

    if errors:
        print(f"Errors: {len(errors)}\n")
        for e in errors:
            print(f"{e['plugin']}:")
            print(f"  Error: {e['error']}\n")


def format_staged_text_output(results):
    """Format staged check results as human-readable text."""
    missing = results['missing_bumps']
    bumped = results['bumped']

    if not missing and not bumped:
        return

    if bumped:
        print(f"Components with version bumps: {len(bumped)}\n")
        for b in bumped:
            old_ver = b['old_version'] or 'new'
            print(f"  ✓ {b['component']}: {old_ver} → {b['new_version']}")
        print()

    if missing:
        print(f"⚠️  Components missing version bumps: {len(missing)}\n")
        for m in missing:
            print(f"{m['component']}:")
            print(f"  Version file: {m['version_file']}")
            print(f"  Current version: {m['current_version'] or 'unknown'}")
            print(f"  Modified files:")
            for f in m['modified_files']:
                print(f"    - {f}")
            print()

        print("=" * 60)
        print("Please bump the version in the appropriate file before committing.")
        print("=" * 60 + "\n")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description='Detect version mismatches between version sources and marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Default:        Compare version source (plugin.json or SKILL.md) vs marketplace.json
  --check-staged: Check if staged files require version bumps

Examples:
  %(prog)s                    # Check for mismatches
  %(prog)s --check-staged     # Check staged files
  %(prog)s --format json      # JSON output
""",
    )

    parser.add_argument(
        '--check-staged',
        action='store_true',
        help='Check if staged files require version bumps'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    try:
        repo_root = find_repo_root()
        if repo_root is None:
            print("❌ Error: Could not find repository root")
            sys.exit(1)

        if args.check_staged:
            results = detect_staged_changes(repo_root)

            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                format_staged_text_output(results)

            sys.exit(1 if results['missing_bumps'] else 0)
        else:
            marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
            if not marketplace_path.exists():
                print(f"❌ marketplace.json not found at {marketplace_path}")
                sys.exit(1)

            with open(marketplace_path) as f:
                marketplace_data = json.load(f)

            results = detect_version_mismatches(repo_root, marketplace_data)

            if args.format == 'json':
                print(json.dumps(results, indent=2))
            else:
                format_text_output(results)

            sys.exit(1 if results['mismatches'] or results['errors'] else 0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
