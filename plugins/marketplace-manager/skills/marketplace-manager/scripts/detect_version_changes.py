#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
DEPRECATION NOTICE: For CI pipelines, use marketplace_ci.py instead.
This script is retained for backward compatibility with pre-commit hooks
(pre-commit.template v5.2.0 references it by name). Future hook template
v6.0.0 should migrate callers to marketplace_ci.py.

Detect version mismatches between version sources and marketplace.json.

Version source per plugin type:
- Plugins with .claude-plugin/plugin.json: version from plugin.json
- Single-skill plugins (skills: ["./"]): version from SKILL.md frontmatter

Also supports checking staged files for version bump requirements.

Usage:
    python3 detect_version_changes.py [--format json|text]
    python3 detect_version_changes.py --check-staged [--format json|text]
    python3 detect_version_changes.py --check-structure [--ci]

Modes:
    Default:          Check version source vs marketplace.json mismatches
    --check-staged:   Check if staged files require version bumps
    --check-structure: Detect structural anti-patterns (shared version sources)
    --ci:             Machine-readable JSON output, exit 1 for any issue
"""

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

from utils import find_repo_root, parse_semver, discover_plugin_skills


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


# --- Structure checks ---

def check_structure(repo_root, marketplace_data):
    """Detect structural anti-patterns in marketplace layout.

    Anti-pattern: multiple distinct plugin entries resolve to the same version file.
    Valid pattern: a single plugin entry with multiple skills (multi-skill bundle).

    Returns dict with 'structure_issues' list and 'suggested_fixes' list.
    """
    source_to_plugins = {}

    for plugin in marketplace_data.get('plugins', []):
        source = plugin.get('source', './')

        source_path_clean = source.lstrip('./') if isinstance(source, str) else ''
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        skills = discover_plugin_skills(source_dir)
        version_file, _ = get_plugin_version_source(source_dir, skills)
        key = str(version_file) if version_file else str(source_dir)

        source_to_plugins.setdefault(key, []).append(plugin.get('name', 'unknown'))

    issues = []
    fixes = []

    for version_file_path, plugins in source_to_plugins.items():
        if len(plugins) > 1:
            issues.append({
                'type': 'shared_version_source',
                'version_file': version_file_path,
                'plugins': plugins,
            })
            fixes.append({
                'plugins': plugins,
                'suggestion': (
                    f"Move each plugin into its own subdirectory (e.g. plugins/<name>/) "
                    f"with its own .claude-plugin/plugin.json, then update marketplace.json "
                    f"source paths accordingly."
                ),
            })

    return {'structure_issues': issues, 'suggested_fixes': fixes}


# --- Default mode: version source vs marketplace.json ---

def get_skill_versions_for_plugin(source_dir, skills):
    """Get SKILL.md metadata.version for each skill in a plugin.

    Returns list of (skill_path, version) tuples.
    """
    versions = []
    for skill_path in skills:
        skill_path_clean = skill_path.lstrip('./')
        skill_dir = source_dir / skill_path_clean if skill_path_clean else source_dir
        skill_md = skill_dir / 'SKILL.md'
        if skill_md.exists():
            version = read_version_from_file(skill_md)
            if version:
                versions.append((skill_path_clean or './', version))
    return versions


def detect_version_mismatches(repo_root, marketplace_data):
    """Detect mismatches between version sources and marketplace.json.

    Compares each plugin's version source (plugin.json or SKILL.md)
    against the version in marketplace.json. One check per plugin.

    For multi-skill plugins with plugin.json, also checks whether any
    SKILL.md metadata.version exceeds plugin.json — indicating plugin.json
    was not bumped after a skill version bump.
    """
    mismatches = []
    skill_drift = []
    errors = []

    for plugin in marketplace_data.get('plugins', []):
        plugin_name = plugin.get('name', 'unknown')
        marketplace_version = plugin.get('version', 'unknown')
        source = plugin.get('source', './')

        source_path_clean = source.lstrip('./') if isinstance(source, str) else ''
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        skills = discover_plugin_skills(source_dir)
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

        # Cross-check: for multi-skill plugins using plugin.json,
        # verify no SKILL.md version exceeds plugin.json version
        if source_label == 'plugin.json' and len(skills) >= 1:
            plugin_semver = parse_semver(actual_version)
            skill_versions = get_skill_versions_for_plugin(source_dir, skills)
            for skill_path, skill_version in skill_versions:
                if parse_semver(skill_version) > plugin_semver:
                    skill_drift.append({
                        'plugin': plugin_name,
                        'skill_path': skill_path,
                        'skill_version': skill_version,
                        'plugin_json_version': actual_version,
                    })

    return {
        'mismatches': mismatches,
        'skill_drift': skill_drift,
        'errors': errors
    }


# --- Output formatters ---

def format_text_output(results):
    """Format default mode results as human-readable text."""
    mismatches = results['mismatches']
    skill_drift = results.get('skill_drift', [])
    errors = results['errors']

    if not mismatches and not skill_drift and not errors:
        print("✓ All plugin versions are synchronized with marketplace.json")
        return

    if mismatches:
        print(f"Mismatches found: {len(mismatches)}\n")
        for m in mismatches:
            print(f"{m['plugin']}:")
            print(f"  {m['source_label']}:      {m['source_version']}")
            print(f"  marketplace.json: {m['marketplace_version']}")
            print(f"  → Sync needed\n")

    if skill_drift:
        print(f"Skill version drift detected: {len(skill_drift)}\n")
        for d in skill_drift:
            print(f"{d['plugin']}:")
            print(f"  skill {d['skill_path']}:  {d['skill_version']}")
            print(f"  plugin.json:        {d['plugin_json_version']}")
            print(f"  → plugin.json needs a version bump\n")

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


def format_structure_text_output(results):
    """Format structure check results as human-readable text."""
    issues = results.get('structure_issues', [])
    fixes = results.get('suggested_fixes', [])

    if not issues:
        print("✓ No structural anti-patterns detected")
        return

    print(f"⚠️  Structural issues found: {len(issues)}\n")
    for issue, fix in zip(issues, fixes):
        print(f"Shared version source: {issue['version_file']}")
        print(f"  Plugins sharing this source: {', '.join(issue['plugins'])}")
        print(f"  Fix: {fix['suggestion']}")
        print()


# --- Main ---

def main():
    parser = argparse.ArgumentParser(
        description='Detect version mismatches between version sources and marketplace.json',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Default:           Compare version source (plugin.json or SKILL.md) vs marketplace.json
  --check-staged:    Check if staged files require version bumps
  --check-structure: Detect structural anti-patterns (shared version sources)

Flags:
  --ci:              Always output JSON; exit 1 for any issue (for use in CI pipelines)

Examples:
  %(prog)s                              # Check for mismatches
  %(prog)s --check-staged               # Check staged files
  %(prog)s --check-structure            # Check for structural anti-patterns
  %(prog)s --check-staged --ci          # CI-mode staged check
  %(prog)s --check-structure --ci       # CI-mode structure check
  %(prog)s --format json                # JSON output (default mode)
""",
    )

    parser.add_argument(
        '--check-staged',
        action='store_true',
        help='Check if staged files require version bumps'
    )

    parser.add_argument(
        '--check-structure',
        action='store_true',
        help='Detect structural anti-patterns (multiple plugins sharing a version source)'
    )

    parser.add_argument(
        '--ci',
        action='store_true',
        help='CI mode: always output JSON, exit 1 for any issue'
    )

    parser.add_argument(
        '--format',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text; overridden to json when --ci is set)'
    )

    args = parser.parse_args()

    # --ci forces JSON output
    output_json = args.ci or args.format == 'json'

    try:
        repo_root = find_repo_root()
        if repo_root is None:
            print("❌ Error: Could not find repository root")
            sys.exit(1)

        if args.check_staged:
            results = detect_staged_changes(repo_root)

            if output_json:
                print(json.dumps(results, indent=2))
            else:
                format_staged_text_output(results)

            sys.exit(1 if results['missing_bumps'] else 0)

        # Load marketplace.json (needed for both structure check and default mode)
        marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
        if not marketplace_path.exists():
            print(f"❌ marketplace.json not found at {marketplace_path}")
            sys.exit(1)

        with open(marketplace_path) as f:
            marketplace_data = json.load(f)

        if args.check_structure:
            results = check_structure(repo_root, marketplace_data)

            if output_json:
                print(json.dumps(results, indent=2))
            else:
                format_structure_text_output(results)

            has_issues = bool(results.get('structure_issues'))
            sys.exit(1 if has_issues else 0)

        else:
            results = detect_version_mismatches(repo_root, marketplace_data)

            if output_json:
                print(json.dumps(results, indent=2))
            else:
                format_text_output(results)

            has_issues = (results['mismatches']
                         or results.get('skill_drift')
                         or results['errors'])
            sys.exit(1 if has_issues else 0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
