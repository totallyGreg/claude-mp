#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Single-file CI entry point for Claude Code plugin marketplace validation.

Vendorable: copy this one file to any repo and run with python3.
No local imports, no third-party packages (stdlib only).

Subcommands:
    validate          Structural linting against official Anthropic schema
    version-check     Version mismatch detection (marketplace.json vs source)
    structure-check   Detect structural anti-patterns

Usage:
    python3 marketplace_ci.py validate [--format json] [--ci]
    python3 marketplace_ci.py version-check [--mr] [--staged] [--target-branch BRANCH] [--format json] [--ci]
    python3 marketplace_ci.py structure-check [--format json] [--ci]

Canonical sources for inlined functions (keep both in sync when fixing bugs):
    find_repo_root()                  <- utils.py:find_repo_root
    load_marketplace()                <- utils.py:load_marketplace
    parse_semver()                    <- utils.py:parse_semver
    validate_semantic_version()       <- utils.py:validate_semantic_version
    extract_frontmatter_version()     <- utils.py:_extract_frontmatter_version_stdlib
    discover_plugin_skills()          <- utils.py:discover_plugin_skills

Schema aligned with:
    - https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema
    - https://code.claude.com/docs/en/plugins-reference#plugin-manifest-schema
    - plugin-dev manifest-reference.md (claude-plugins-official)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants — aligned with official Anthropic schemas
# ---------------------------------------------------------------------------

PLUGIN_NAME_PATTERN = r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'

MARKETPLACE_REQUIRED_FIELDS = {'name', 'owner', 'plugins'}
# Per official docs: https://code.claude.com/docs/en/plugin-marketplaces
# Only name, owner, and plugins are documented. $schema is standard JSON Schema.
MARKETPLACE_KNOWN_ROOT_FIELDS = {'$schema', 'name', 'owner', 'plugins'}

PLUGIN_ENTRY_REQUIRED_FIELDS = {'name', 'source'}
MARKETPLACE_PLUGIN_KNOWN_FIELDS = {
    'name', 'source', 'description', 'version', 'author',
    'homepage', 'repository', 'license', 'keywords',
    'category', 'tags', 'strict',
    'commands', 'agents', 'hooks', 'mcpServers', 'lspServers',
}

PLUGIN_JSON_KNOWN_FIELDS = {
    'name', 'version', 'description', 'author', 'license', 'keywords',
    'homepage', 'repository',
    'commands', 'agents', 'hooks',
    'mcpServers', 'lspServers',
}
PLUGIN_JSON_REQUIRED_FIELDS = {'name'}

# Files that don't require version bumps when changed
EXCLUDED_PATTERNS = [
    'IMPROVEMENT_PLAN.md', 'CHANGELOG.md', 'LICENSE*', 'README*',
    'docs/*', 'references/*', 'examples/*', 'tests/*',
    '.gitignore', '.skillignore', '.DS_Store', '__pycache__/*', '*.pyc',
    '.claude-plugin/marketplace.json',
]


# ---------------------------------------------------------------------------
# Inlined utility functions (stdlib only)
# ---------------------------------------------------------------------------

def find_repo_root(start_path=None):
    """Find repository root by looking for .git or .claude-plugin."""
    start = Path(start_path).resolve() if start_path else Path.cwd()
    for marker in ('.git', '.claude-plugin'):
        current = start
        while current != current.parent:
            if (current / marker).exists():
                return current
            current = current.parent
        if (current / marker).exists():
            return current
    return None


def load_marketplace(marketplace_path):
    """Load marketplace.json."""
    with open(marketplace_path, 'r') as f:
        return json.load(f)


def parse_semver(version_str):
    """Parse version string into (major, minor, patch). Returns (0,0,0) on failure."""
    if not version_str or not isinstance(version_str, str):
        return (0, 0, 0)
    try:
        base = version_str.split('-', 1)[0]
        parts = base.split('.')
        return tuple(int(p) for p in parts[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def validate_semantic_version(version_str):
    """Check if version_str is valid semver (with optional pre-release)."""
    if not version_str or not isinstance(version_str, str):
        return False
    return bool(re.match(
        r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$',
        version_str
    ))


def extract_frontmatter_version(content):
    """Extract version from SKILL.md content string (stdlib only, no regex).

    Returns (version, is_nonstandard) tuple:
    - version: the version string (metadata.version preferred)
    - is_nonstandard: True if version came from root-level 'version:' field
      (not defined in the AgentSkills Specification)

    Known limitations vs yaml.safe_load():
    - Does not handle multi-line YAML scalars (folded/literal blocks)
    - Does not handle complex nested structures beyond metadata.version
    - Inline comments after values are included in the parsed value
    """
    if not content or not content.startswith('---'):
        return (None, False)

    parts = content.split('---', 2)
    if len(parts) < 3:
        return (None, False)

    metadata_version = None
    version = None
    in_metadata = False

    for line in parts[1].strip().splitlines():
        stripped = line.strip()
        indented = line.startswith(' ') or line.startswith('\t')

        if stripped == 'metadata:':
            in_metadata = True
        elif in_metadata and indented and stripped.startswith('version:'):
            metadata_version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
        elif not indented and stripped.startswith('version:'):
            version = stripped.split(':', 1)[1].strip().strip('"').strip("'")
            in_metadata = False
        elif not indented and stripped and ':' in stripped:
            in_metadata = False

    if metadata_version:
        return (metadata_version, False)
    elif version:
        return (version, True)
    return (None, False)


def discover_plugin_skills(source_dir):
    """Discover skill paths within a plugin directory."""
    source_dir = Path(source_dir)
    if (source_dir / 'SKILL.md').exists():
        return ['./']
    skills_dir = source_dir / 'skills'
    if skills_dir.is_dir():
        found = []
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and (child / 'SKILL.md').exists():
                found.append(f'./skills/{child.name}')
        if found:
            return found
    return []


def extract_plugin_json_version(content):
    """Extract version from plugin.json content string."""
    if not content:
        return None
    try:
        data = json.loads(content)
        return data.get('version')
    except json.JSONDecodeError:
        return None


def is_excluded(filepath):
    """Check if a file path matches exclusion patterns."""
    import fnmatch
    for pattern in EXCLUDED_PATTERNS:
        if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(Path(filepath).name, pattern):
            return True
    return False


# ---------------------------------------------------------------------------
# Subcommand: validate
# ---------------------------------------------------------------------------

def cmd_validate(repo_root, marketplace_data):
    """Validate marketplace.json structure against official schema."""
    issues = []

    # Required root fields
    for field in sorted(MARKETPLACE_REQUIRED_FIELDS):
        if field not in marketplace_data or not marketplace_data[field]:
            issues.append({
                'type': 'error',
                'field': field,
                'message': f"Required field '{field}' is missing or empty"
            })

    # Unknown root fields
    unknown_root = set(marketplace_data.keys()) - MARKETPLACE_KNOWN_ROOT_FIELDS
    for field in sorted(unknown_root):
        if field in ('version', 'description'):
            issues.append({
                'type': 'warning',
                'field': field,
                'message': (
                    f"Root-level '{field}' is not part of the official marketplace schema. "
                    f"Remove this field — for plugins, set '{field}' in each plugin entry instead."
                )
            })
        elif field == 'metadata':
            issues.append({
                'type': 'warning',
                'field': field,
                'message': (
                    "Root-level 'metadata' is not part of the official marketplace schema. "
                    "Remove this field — the official schema uses only name, owner, and plugins."
                )
            })
        else:
            issues.append({
                'type': 'warning',
                'field': field,
                'message': f"Unknown root-level field '{field}'"
            })

    # Marketplace name format
    mp_name = marketplace_data.get('name', '')
    if mp_name and not re.match(PLUGIN_NAME_PATTERN, mp_name):
        issues.append({
            'type': 'error',
            'field': 'name',
            'message': f"Name '{mp_name}' must be kebab-case"
        })

    # Owner validation
    owner = marketplace_data.get('owner', {})
    if isinstance(owner, dict):
        if not owner.get('name'):
            issues.append({
                'type': 'error',
                'field': 'owner.name',
                'message': "Owner name is required"
            })

    # Plugin entries
    plugins = marketplace_data.get('plugins', [])
    if not isinstance(plugins, list):
        issues.append({'type': 'error', 'field': 'plugins', 'message': "Must be an array"})
        plugins = []

    plugin_names = set()
    for idx, plugin in enumerate(plugins):
        prefix = f"plugins[{idx}]"
        p_name = plugin.get('name', '')

        # Required: name
        if not p_name:
            issues.append({
                'type': 'error', 'field': f'{prefix}.name',
                'message': f"Plugin at index {idx} missing 'name'"
            })
        else:
            if not re.match(PLUGIN_NAME_PATTERN, p_name):
                issues.append({
                    'type': 'error', 'field': f'{prefix}.name',
                    'message': f"Name '{p_name}' must be kebab-case"
                })
            if p_name in plugin_names:
                issues.append({
                    'type': 'error', 'field': f'{prefix}.name',
                    'message': f"Duplicate plugin name: {p_name}"
                })
            plugin_names.add(p_name)

        # Required: source
        source = plugin.get('source')
        if not source:
            issues.append({
                'type': 'error', 'field': f'{prefix}.source',
                'message': f"Plugin '{p_name or 'unnamed'}' missing 'source'"
            })

        # Source path validation (relative paths only)
        source_dir = None
        if isinstance(source, str):
            if not source.startswith('./'):
                issues.append({
                    'type': 'error', 'field': f'{prefix}.source',
                    'message': f"Relative path must start with './' (got: {source})"
                })
            elif '..' in source:
                issues.append({
                    'type': 'error', 'field': f'{prefix}.source',
                    'message': f"Path must not contain '..' (got: {source})"
                })
            else:
                source_path_clean = source.lstrip('./')
                source_dir = repo_root / source_path_clean if source_path_clean else repo_root
                if not source_dir.exists():
                    issues.append({
                        'type': 'error', 'field': f'{prefix}.source',
                        'message': f"Source directory not found: {source_dir}"
                    })

        # Unknown plugin fields
        if 'skills' in plugin:
            issues.append({
                'type': 'warning', 'field': f'{prefix}.skills',
                'message': "'skills' not in official schema (auto-discovered from plugin dir)"
            })
        unknown_plugin = set(plugin.keys()) - MARKETPLACE_PLUGIN_KNOWN_FIELDS
        for field in sorted(unknown_plugin):
            if field == 'skills':
                continue
            issues.append({
                'type': 'warning', 'field': f'{prefix}.{field}',
                'message': f"Unknown field '{field}'"
            })

        # Version validation
        if 'version' in plugin and plugin['version']:
            if not validate_semantic_version(plugin['version']):
                issues.append({
                    'type': 'warning', 'field': f'{prefix}.version',
                    'message': f"Invalid version: {plugin['version']}"
                })

        # Validate plugin.json if present
        if source_dir and source_dir.exists():
            plugin_json = source_dir / '.claude-plugin' / 'plugin.json'
            if plugin_json.exists():
                try:
                    with open(plugin_json) as f:
                        pj_data = json.load(f)
                    # Required: name
                    if not pj_data.get('name'):
                        issues.append({
                            'type': 'error', 'field': f'{p_name}/plugin.json.name',
                            'message': "Required field 'name' missing"
                        })
                    elif not re.match(PLUGIN_NAME_PATTERN, pj_data['name']):
                        issues.append({
                            'type': 'error', 'field': f'{p_name}/plugin.json.name',
                            'message': f"Name '{pj_data['name']}' must be kebab-case"
                        })
                    # Recommended
                    for rec in ('version', 'description'):
                        if not pj_data.get(rec):
                            issues.append({
                                'type': 'warning', 'field': f'{p_name}/plugin.json.{rec}',
                                'message': f"Recommended field '{rec}' missing"
                            })
                    # Version format
                    if pj_data.get('version') and not validate_semantic_version(pj_data['version']):
                        issues.append({
                            'type': 'warning', 'field': f'{p_name}/plugin.json.version',
                            'message': f"Invalid version: {pj_data['version']}"
                        })
                    # Unknown fields
                    for field in sorted(set(pj_data.keys()) - PLUGIN_JSON_KNOWN_FIELDS):
                        issues.append({
                            'type': 'warning', 'field': f'{p_name}/plugin.json.{field}',
                            'message': f"Unknown field '{field}'"
                        })
                except (OSError, json.JSONDecodeError) as e:
                    issues.append({
                        'type': 'error', 'field': f'{p_name}/plugin.json',
                        'message': f"Failed to read: {e}"
                    })

            # Validate SKILL.md frontmatter for discovered skills
            for skill_path in discover_plugin_skills(source_dir):
                sp_clean = skill_path.lstrip('./')
                skill_dir = source_dir / sp_clean if sp_clean else source_dir
                skill_md = skill_dir / 'SKILL.md'
                if skill_md.exists():
                    content = skill_md.read_text()
                    ver, is_nonstandard = extract_frontmatter_version(content)
                    if not ver:
                        issues.append({
                            'type': 'warning', 'field': prefix,
                            'message': f"No version in {skill_path}/SKILL.md"
                        })
                    elif is_nonstandard:
                        issues.append({
                            'type': 'warning', 'field': prefix,
                            'message': (
                                f"Root-level 'version' in {skill_path}/SKILL.md "
                                f"(not in AgentSkills spec, use metadata.version)"
                            )
                        })

    return issues


# ---------------------------------------------------------------------------
# Subcommand: version-check
# ---------------------------------------------------------------------------

def get_plugin_version_source(source_dir, skills):
    """Determine version file for a plugin."""
    source_dir = Path(source_dir)
    plugin_json = source_dir / '.claude-plugin' / 'plugin.json'
    if plugin_json.exists():
        return str(plugin_json), 'plugin.json'
    if len(skills) == 1 and skills[0] == './':
        skill_md = source_dir / 'SKILL.md'
        if skill_md.exists():
            return str(skill_md), 'SKILL.md'
    return None, None


def read_version_from_file(filepath):
    """Read version from a version source file."""
    filepath = Path(filepath)
    try:
        content = filepath.read_text()
    except OSError:
        return None

    if filepath.name == 'plugin.json':
        return extract_plugin_json_version(content)
    elif filepath.name == 'SKILL.md':
        ver, _ = extract_frontmatter_version(content)
        return ver
    return None


def get_mr_diff_files(repo_root, target_branch=None):
    """Get files changed in MR/PR vs target branch.

    Auto-detects target branch from CI environment variables.
    Falls back to 'main'. Use --target-branch to override.
    """
    target = target_branch or (
        os.environ.get('CI_MERGE_REQUEST_TARGET_BRANCH_NAME')
        or os.environ.get('GITHUB_BASE_REF')
        or 'main'
    )
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'origin/{target}...HEAD'],
        cwd=repo_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"ERROR: git diff against origin/{target} failed.", file=sys.stderr)
        print(f"Ensure target branch is fetched.", file=sys.stderr)
        sys.exit(1)
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]


def get_staged_files(repo_root):
    """Get currently staged files."""
    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only'],
        cwd=repo_root, capture_output=True, text=True
    )
    if result.returncode != 0:
        return []
    return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]


def map_file_to_component(filepath):
    """Map a file path to its plugin/skill component."""
    parts = Path(filepath).parts
    # plugins/<plugin>/skills/<skill>/*
    if len(parts) >= 4 and parts[0] == 'plugins' and parts[2] == 'skills':
        return f"plugins/{parts[1]}/skills/{parts[3]}"
    # plugins/<plugin>/*
    if len(parts) >= 2 and parts[0] == 'plugins':
        return f"plugins/{parts[1]}"
    # skills/<name>/*
    if len(parts) >= 2 and parts[0] == 'skills':
        return f"skills/{parts[1]}"
    return None


def cmd_version_check(repo_root, marketplace_data, mode='default', target_branch=None):
    """Check for version mismatches or required bumps."""
    mismatches = []
    skill_drift = []
    errors = []
    bumps_needed = []

    # Get changed files for --mr or --staged mode
    changed_files = []
    if mode == 'mr':
        changed_files = get_mr_diff_files(repo_root, target_branch)
    elif mode == 'staged':
        changed_files = get_staged_files(repo_root)

    for plugin in marketplace_data.get('plugins', []):
        p_name = plugin.get('name', 'unknown')
        mp_version = plugin.get('version', 'unknown')
        source = plugin.get('source', './')

        source_path_clean = source.lstrip('./') if isinstance(source, str) else ''
        source_dir = repo_root / source_path_clean if source_path_clean else repo_root

        skills = discover_plugin_skills(source_dir)
        version_file, source_label = get_plugin_version_source(source_dir, skills)

        if version_file is None:
            errors.append({
                'plugin': p_name,
                'error': f'No version source found at {source}',
            })
            continue

        actual_version = read_version_from_file(version_file)
        if actual_version is None:
            errors.append({
                'plugin': p_name,
                'error': f'Could not read version from {source_label}',
            })
            continue

        # Default mode: check marketplace.json vs source
        if mode == 'default':
            if actual_version != mp_version:
                mismatches.append({
                    'plugin': p_name,
                    'source_label': source_label,
                    'source_version': actual_version,
                    'marketplace_version': mp_version,
                })

            # Cross-check: skill versions vs plugin.json
            if source_label == 'plugin.json' and skills:
                plugin_sv = parse_semver(actual_version)
                for skill_path in skills:
                    sp_clean = skill_path.lstrip('./')
                    s_dir = source_dir / sp_clean if sp_clean else source_dir
                    s_md = s_dir / 'SKILL.md'
                    if s_md.exists():
                        content = s_md.read_text()
                        sv, _ = extract_frontmatter_version(content)
                        if sv and parse_semver(sv) > plugin_sv:
                            skill_drift.append({
                                'plugin': p_name,
                                'skill_path': sp_clean or './',
                                'skill_version': sv,
                                'plugin_json_version': actual_version,
                            })

        # MR/staged mode: check if changed files need version bumps
        elif mode in ('mr', 'staged') and changed_files:
            component_prefix = source_path_clean or '.'
            component_files = [
                f for f in changed_files
                if f.startswith(component_prefix) and not is_excluded(f)
            ]
            if component_files:
                # Check if version file itself was changed
                rel_version_file = str(Path(version_file).relative_to(repo_root))
                if rel_version_file not in changed_files:
                    bumps_needed.append({
                        'plugin': p_name,
                        'version_file': rel_version_file,
                        'current_version': actual_version,
                        'changed_files': component_files,
                    })

    result = {
        'mismatches': mismatches,
        'skill_drift': skill_drift,
        'errors': errors,
    }
    if mode in ('mr', 'staged'):
        result['bumps_needed'] = bumps_needed
    return result


# ---------------------------------------------------------------------------
# Subcommand: structure-check
# ---------------------------------------------------------------------------

def cmd_structure_check(repo_root, marketplace_data):
    """Detect structural anti-patterns (shared version sources)."""
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
    for version_file_path, plugins in source_to_plugins.items():
        if len(plugins) > 1:
            issues.append({
                'type': 'shared_version_source',
                'version_file': version_file_path,
                'plugins': plugins,
                'suggestion': (
                    f"Move each plugin into its own subdirectory with its own "
                    f"plugin.json, then update marketplace.json source paths."
                ),
            })

    return {'structure_issues': issues}


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(data, fmt='text', subcommand='validate'):
    """Format output as text or JSON."""
    if fmt == 'json':
        print(json.dumps(data, indent=2))
        return

    if subcommand == 'validate':
        issues = data.get('issues', [])
        if not issues:
            print("Validation passed! No issues found.")
            return
        errors = [i for i in issues if i['type'] == 'error']
        warnings = [i for i in issues if i['type'] == 'warning']
        if errors:
            print(f"ERRORS ({len(errors)}):")
            for i in errors:
                print(f"  {i.get('field', '')}: {i['message']}")
        if warnings:
            print(f"WARNINGS ({len(warnings)}):")
            for i in warnings:
                print(f"  {i.get('field', '')}: {i['message']}")

    elif subcommand == 'version-check':
        mismatches = data.get('mismatches', [])
        drift = data.get('skill_drift', [])
        errors = data.get('errors', [])
        bumps = data.get('bumps_needed', [])

        if not any([mismatches, drift, errors, bumps]):
            print("All versions in sync.")
            return
        for m in mismatches:
            print(f"MISMATCH: {m['plugin']} — {m['source_label']}: {m['source_version']}, marketplace: {m['marketplace_version']}")
        for d in drift:
            print(f"DRIFT: {d['plugin']} — skill {d['skill_path']}: {d['skill_version']} > plugin.json: {d['plugin_json_version']}")
        for e in errors:
            print(f"ERROR: {e['plugin']} — {e['error']}")
        for b in bumps:
            print(f"BUMP NEEDED: {b['plugin']} (v{b['current_version']}) — {len(b['changed_files'])} file(s) changed")

    elif subcommand == 'structure-check':
        issues = data.get('structure_issues', [])
        if not issues:
            print("No structural anti-patterns found.")
            return
        for i in issues:
            print(f"SHARED VERSION SOURCE: {i['version_file']}")
            print(f"  Plugins: {', '.join(i['plugins'])}")
            print(f"  {i['suggestion']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code plugin marketplace CI validation',
        prog='marketplace_ci.py',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # validate
    p_validate = sub.add_parser('validate', help='Validate marketplace.json structure')
    p_validate.add_argument('--format', choices=['text', 'json'], default='text')
    p_validate.add_argument('--ci', action='store_true', help='JSON output + exit 1 on any issue')
    p_validate.add_argument('--path', default='.', help='Repository path')

    # version-check
    p_version = sub.add_parser('version-check', help='Check version mismatches')
    p_version.add_argument('--format', choices=['text', 'json'], default='text')
    p_version.add_argument('--ci', action='store_true')
    p_version.add_argument('--mr', action='store_true', help='MR/PR diff mode')
    p_version.add_argument('--staged', action='store_true', help='Check staged files')
    p_version.add_argument('--target-branch', help='Explicit target branch for --mr')
    p_version.add_argument('--path', default='.', help='Repository path')

    # structure-check
    p_struct = sub.add_parser('structure-check', help='Detect structural anti-patterns')
    p_struct.add_argument('--format', choices=['text', 'json'], default='text')
    p_struct.add_argument('--ci', action='store_true')
    p_struct.add_argument('--path', default='.', help='Repository path')

    args = parser.parse_args()

    # CI mode forces JSON
    fmt = 'json' if args.ci else args.format

    # Find repo root
    if args.path != '.':
        repo_root = Path(args.path).resolve()
    else:
        repo_root = find_repo_root()
        if repo_root is None:
            print("ERROR: Could not find repository root", file=sys.stderr)
            sys.exit(1)

    # Load marketplace.json
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
    if not marketplace_path.exists():
        print(f"ERROR: marketplace.json not found at {marketplace_path}", file=sys.stderr)
        sys.exit(1)

    try:
        marketplace_data = load_marketplace(marketplace_path)
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Failed to load marketplace.json: {e}", file=sys.stderr)
        sys.exit(1)

    # Dispatch
    if args.command == 'validate':
        issues = cmd_validate(repo_root, marketplace_data)
        errors = [i for i in issues if i['type'] == 'error']
        result = {
            'valid': len(errors) == 0,
            'issues': issues,
            'summary': {
                'total': len(issues),
                'errors': len(errors),
                'warnings': len(issues) - len(errors),
            }
        }
        format_output(result, fmt, 'validate')
        if args.ci and issues:
            sys.exit(1)
        elif errors:
            sys.exit(1)

    elif args.command == 'version-check':
        mode = 'mr' if args.mr else ('staged' if args.staged else 'default')
        result = cmd_version_check(repo_root, marketplace_data, mode, args.target_branch)
        format_output(result, fmt, 'version-check')
        has_issues = any([
            result.get('mismatches'), result.get('skill_drift'),
            result.get('errors'), result.get('bumps_needed'),
        ])
        if args.ci and has_issues:
            sys.exit(1)
        elif result.get('errors'):
            sys.exit(1)

    elif args.command == 'structure-check':
        result = cmd_structure_check(repo_root, marketplace_data)
        format_output(result, fmt, 'structure-check')
        if args.ci and result.get('structure_issues'):
            sys.exit(1)


if __name__ == '__main__':
    main()
