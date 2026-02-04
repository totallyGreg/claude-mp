#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Detect version mismatches between SKILL.md and marketplace.json

Scans all skills in marketplace.json and compares their versions with
the version in their SKILL.md frontmatter. Reports any mismatches.

Also supports checking staged files for version bump requirements.

Usage:
    python3 detect_version_changes.py [--format json|text]
    python3 detect_version_changes.py --check-staged [--format json|text]

Modes:
    Default: Check SKILL.md vs marketplace.json mismatches
    --check-staged: Check if staged files require version bumps
"""

import fnmatch
import json
import subprocess
import sys
from pathlib import Path


def find_repository_root():
    """Find git repository root"""
    current = Path.cwd()

    while current != current.parent:
        if (current / '.git').exists() or (current / '.claude-plugin').exists():
            return current
        current = current.parent

    raise Exception("Not in a git repository")


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


def get_staged_files(repo_root):
    """Get list of staged files from git"""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Failed to get staged files: {result.stderr}")

    files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    return files


def is_excluded(filepath):
    """Check if filepath matches exclusion patterns"""
    # Get the basename and relative path components
    parts = Path(filepath).parts
    basename = parts[-1] if parts else ''

    for pattern in EXCLUDED_PATTERNS:
        # Check if pattern matches basename
        if fnmatch.fnmatch(basename, pattern):
            return True
        # Check if pattern matches any suffix of the path
        if fnmatch.fnmatch(filepath, pattern):
            return True
        if fnmatch.fnmatch(filepath, '*/' + pattern):
            return True
        # Check for directory patterns like docs/*
        if '/' in pattern:
            dir_pattern = pattern.rstrip('/*')
            for part in parts[:-1]:
                if fnmatch.fnmatch(part, dir_pattern):
                    return True
    return False


def map_file_to_component(filepath):
    """
    Map a file path to its parent component's version file.

    Returns: (component_path, version_file) or (None, None) if not mappable

    Mappings:
    - skills/<name>/* -> skills/<name>/SKILL.md
    - plugins/<plugin>/skills/<skill>/* -> plugins/<plugin>/skills/<skill>/SKILL.md
    - plugins/<plugin>/* (non-skill) -> plugins/<plugin>/.claude-plugin/plugin.json
    """
    parts = Path(filepath).parts

    # Check for plugins/<plugin>/skills/<skill>/*
    if len(parts) >= 4 and parts[0] == 'plugins' and parts[2] == 'skills':
        plugin_name = parts[1]
        skill_name = parts[3]
        component_path = f"plugins/{plugin_name}/skills/{skill_name}"
        version_file = f"{component_path}/SKILL.md"
        return component_path, version_file

    # Check for skills/<name>/*
    if len(parts) >= 2 and parts[0] == 'skills':
        skill_name = parts[1]
        component_path = f"skills/{skill_name}"
        version_file = f"{component_path}/SKILL.md"
        return component_path, version_file

    # Check for plugins/<plugin>/* (non-skill files)
    if len(parts) >= 2 and parts[0] == 'plugins':
        plugin_name = parts[1]
        component_path = f"plugins/{plugin_name}"
        version_file = f"{component_path}/.claude-plugin/plugin.json"
        return component_path, version_file

    return None, None


def get_file_content_at_ref(repo_root, filepath, ref='HEAD'):
    """Get file content at a specific git ref"""
    result = subprocess.run(
        ['git', 'show', f'{ref}:{filepath}'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None  # File doesn't exist at ref
    return result.stdout


def get_staged_content(repo_root, filepath):
    """Get staged content of a file"""
    result = subprocess.run(
        ['git', 'show', f':{filepath}'],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout


def extract_version_from_skill_md(content):
    """Extract version from SKILL.md content"""
    if not content or not content.startswith('---'):
        return None

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None

    frontmatter = parts[1].strip()
    in_metadata = False

    for line in frontmatter.split('\n'):
        line_stripped = line.strip()

        if line_stripped.startswith('metadata:'):
            in_metadata = True
        elif in_metadata and line_stripped.startswith('version:'):
            return line_stripped.split(':', 1)[1].strip().strip('"')
        elif not in_metadata and line_stripped.startswith('version:'):
            return line_stripped.split(':', 1)[1].strip().strip('"')
        elif line_stripped and not line_stripped.startswith(' ') and not line_stripped.startswith('-'):
            in_metadata = False

    return None


def extract_version_from_plugin_json(content):
    """Extract version from plugin.json content"""
    if not content:
        return None
    try:
        data = json.loads(content)
        return data.get('version')
    except json.JSONDecodeError:
        return None


def check_version_bumped(repo_root, version_file):
    """
    Check if version file is staged with an actual version change.

    Returns: (is_bumped, head_version, staged_version)
    """
    head_content = get_file_content_at_ref(repo_root, version_file, 'HEAD')
    staged_content = get_staged_content(repo_root, version_file)

    # Determine extractor based on file type
    if version_file.endswith('SKILL.md'):
        extractor = extract_version_from_skill_md
    elif version_file.endswith('plugin.json'):
        extractor = extract_version_from_plugin_json
    else:
        return False, None, None

    head_version = extractor(head_content) if head_content else None
    staged_version = extractor(staged_content) if staged_content else None

    # If no HEAD version, this is a new file - consider it bumped
    if head_version is None and staged_version is not None:
        return True, None, staged_version

    # If versions differ, it's been bumped
    if head_version != staged_version and staged_version is not None:
        return True, head_version, staged_version

    return False, head_version, staged_version


def detect_staged_changes(repo_root):
    """
    Detect staged files that require version bumps.

    Returns: {
        'missing_bumps': [
            {
                'component': str,
                'version_file': str,
                'current_version': str,
                'modified_files': [str]
            }
        ],
        'bumped': [
            {
                'component': str,
                'version_file': str,
                'old_version': str,
                'new_version': str
            }
        ]
    }
    """
    staged_files = get_staged_files(repo_root)

    # Group files by component
    component_files = {}  # {(component_path, version_file): [files]}

    for filepath in staged_files:
        if is_excluded(filepath):
            continue

        component, version_file = map_file_to_component(filepath)
        if component is None:
            continue

        # Skip version files themselves from modification list
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
        source = plugin.get('source', './')

        # Resolve source directory
        source_path_clean = source.lstrip('./')
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        for skill_path_str in plugin.get('skills', []):
            skill_path_clean = skill_path_str.lstrip('./')
            # Resolve skill path relative to source
            skill_path = source_dir / skill_path_clean if skill_path_clean else source_dir

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


def format_staged_text_output(results):
    """Format staged check results as human-readable text"""
    print("\n" + "="*60)
    print("Staged Files Version Check")
    print("="*60 + "\n")

    missing = results['missing_bumps']
    bumped = results['bumped']

    if not missing and not bumped:
        print("✓ No staged files require version bumps\n")
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

        print("="*60)
        print("Please bump the version in the appropriate file before committing.")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    output_format = 'text'
    check_staged = '--check-staged' in sys.argv

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    try:
        # Find repository
        repo_root = find_repository_root()

        if check_staged:
            # Check staged files for version bump requirements
            results = detect_staged_changes(repo_root)

            if output_format == 'json':
                print(json.dumps(results, indent=2))
            else:
                format_staged_text_output(results)

            # Exit with error code if missing bumps found
            if results['missing_bumps']:
                sys.exit(1)
            else:
                sys.exit(0)
        else:
            # Default: Check SKILL.md vs marketplace.json
            marketplace_data = read_marketplace_json(repo_root)
            results = detect_version_changes(repo_root, marketplace_data)

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
