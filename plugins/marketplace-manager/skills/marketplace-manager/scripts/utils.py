#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""Shared utilities for marketplace-manager scripts."""

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def find_repo_root(start_path=None):
    """Find repository root by traversing up from start_path.

    Two-pass search:
    1. Look for .git directory (most reliable, avoids stopping at plugin-level .claude-plugin)
    2. Fall back to .claude-plugin directory (for standalone plugin repos without .git)

    Args:
        start_path: Starting directory (defaults to current directory)

    Returns:
        Path to repository root, or None if not found
    """
    start = Path(start_path).resolve() if start_path else Path.cwd()

    # Pass 1: Look for .git (preferred — avoids stopping at plugin-level .claude-plugin)
    current = start
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    if (current / ".git").exists():
        return current

    # Pass 2: Fall back to .claude-plugin (standalone plugin repos without .git)
    current = start
    while current != current.parent:
        if (current / ".claude-plugin").exists():
            return current
        current = current.parent
    if (current / ".claude-plugin").exists():
        return current

    return None


def get_repo_root(args_path, verbose=False):
    """Get repository root from args or auto-detect.

    Args:
        args_path: Path from command line args
        verbose: Whether to print verbose output

    Returns:
        Resolved Path to repository root

    Raises:
        SystemExit if repository root cannot be determined
    """
    if args_path != ".":
        # User explicitly provided path
        repo_root = Path(args_path).resolve()
        if not repo_root.exists():
            print(f"❌ Error: Specified path does not exist: {repo_root}")
            sys.exit(1)

        if verbose:
            print(f"ℹ️  Using explicitly provided path: {repo_root}")

        return repo_root

    # Try to auto-detect
    if verbose:
        print(f"🔍 Auto-detecting repository root from: {Path.cwd()}")

    repo_root = find_repo_root()
    if repo_root is None:
        print("❌ Error: Could not find repository root")
        print("   Searched for .git or .claude-plugin directory in parent directories")
        print("   Please run from within a repository or specify --path explicitly")
        print(f"   Current directory: {Path.cwd()}")
        sys.exit(1)

    if verbose:
        print(f"✅ Found repository root: {repo_root}")

    return repo_root


def print_verbose_info(repo_root, marketplace_path):
    """Print detailed path resolution information.

    Args:
        repo_root: Path to repository root
        marketplace_path: Path to marketplace.json file
    """
    print(f"🔍 Path Resolution:")
    print(f"   Current working directory: {Path.cwd()}")
    print(f"   Repository root (detected): {repo_root}")
    print(f"   Marketplace file location: {marketplace_path}")
    print(f"   File exists: {marketplace_path.exists()}")
    print()


def validate_repo_structure(repo_root, command):
    """Validate repository structure for the given command.

    Args:
        repo_root: Path to repository root
        command: Command being executed (e.g., 'init', 'list', etc.)

    Returns:
        True if validation passes, False otherwise
    """
    issues = []

    # Check if .claude-plugin directory exists for non-init commands
    if command != "init":
        claude_plugin_dir = repo_root / ".claude-plugin"
        if not claude_plugin_dir.exists():
            issues.append(f".claude-plugin directory not found at {claude_plugin_dir}")

    # Check if skills directory exists (warning only)
    skills_dir = repo_root / "skills"
    if not skills_dir.exists():
        print(f"⚠️  Warning: 'skills' directory not found at {skills_dir}")
        print(f"   This is unusual but not an error")
        print()

    if issues:
        print("❌ Repository structure validation failed:")
        for issue in issues:
            print(f"   • {issue}")
        return False

    return True


# ---------------------------------------------------------------------------
# Marketplace I/O
# ---------------------------------------------------------------------------

def load_marketplace(marketplace_path):
    """Load existing marketplace.json or return empty structure.

    Args:
        marketplace_path: Path to marketplace.json file

    Returns:
        Parsed marketplace data dict
    """
    marketplace_path = Path(marketplace_path)
    if marketplace_path.exists():
        with open(marketplace_path, "r") as f:
            return json.load(f)
    return {
        "name": "",
        "owner": {"name": ""},
        "plugins": [],
    }


def save_marketplace(marketplace_path, marketplace_data):
    """Save marketplace.json with pretty formatting.

    Args:
        marketplace_path: Path to marketplace.json file
        marketplace_data: Dict to serialize
    """
    marketplace_path = Path(marketplace_path)
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)
    with open(marketplace_path, "w") as f:
        json.dump(marketplace_data, f, indent=2)
        f.write("\n")


def find_plugin(marketplace_data, plugin_name):
    """Find a plugin entry by name in marketplace data.

    Args:
        marketplace_data: Parsed marketplace.json dict
        plugin_name: Plugin name to search for

    Returns:
        Plugin dict if found, None otherwise
    """
    for plugin in marketplace_data.get("plugins", []):
        if plugin.get("name") == plugin_name:
            return plugin
    return None


# ---------------------------------------------------------------------------
# Version parsing
# ---------------------------------------------------------------------------

def parse_semver(version_str):
    """Parse a version string into a comparable (major, minor, patch) tuple.

    Pre-release suffixes (e.g. '1.0.0-alpha.1') are stripped — only the
    numeric base is returned for comparison purposes.

    Returns (0, 0, 0) on failure — conservative default that makes parse
    failures visible and avoids false 'already at 1.0.0' signals.
    """
    if not version_str or not isinstance(version_str, str):
        return (0, 0, 0)
    try:
        # Strip pre-release suffix: '1.0.0-alpha.1' → '1.0.0'
        base = version_str.split('-', 1)[0]
        parts = base.split('.')
        return tuple(int(p) for p in parts[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def validate_semantic_version(version_str):
    """Check if version_str is valid semver (with optional pre-release).

    Accepts: '1.0.0', '1.0.0-alpha.1', '1.0.0-rc.2'
    Rejects: 'latest', '1.0', 'v1.0.0'
    """
    if not version_str or not isinstance(version_str, str):
        return False
    return bool(re.match(
        r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$',
        version_str
    ))


# ---------------------------------------------------------------------------
# Frontmatter version extraction
# ---------------------------------------------------------------------------

def extract_frontmatter_version(skill_md_path):
    """Extract version from SKILL.md YAML frontmatter.

    Uses yaml.safe_load() when available, falls back to string parsing.

    Priority:
    1. metadata.version (AgentSkills spec — preferred)
    2. Root-level version (not in spec — flagged as non-standard)

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Tuple of (version_string, is_nonstandard):
        - version_string: the version, or None if not found
        - is_nonstandard: True if version came from root-level 'version:'
          field (not defined in the AgentSkills Specification)
    """
    skill_md_path = Path(skill_md_path)
    try:
        content = skill_md_path.read_text()
    except (OSError, IOError) as e:
        print(f"⚠️  Warning: Could not read {skill_md_path}: {e}")
        return (None, False)

    if not content.startswith('---'):
        return (None, False)

    end = content.find('---', 3)
    if end == -1:
        return (None, False)

    raw_frontmatter = content[3:end]

    # Prefer yaml.safe_load when available
    if yaml is not None:
        try:
            frontmatter = yaml.safe_load(raw_frontmatter)
            if not isinstance(frontmatter, dict):
                return (None, False)

            metadata = frontmatter.get('metadata', {})
            if isinstance(metadata, dict) and 'version' in metadata:
                return (str(metadata['version']), False)
            if 'version' in frontmatter:
                return (str(frontmatter['version']), True)
            return (None, False)
        except yaml.YAMLError:
            return (None, False)

    # Fallback: string-based parsing (no pyyaml available)
    return _extract_frontmatter_version_stdlib(raw_frontmatter)


def _extract_frontmatter_version_stdlib(raw_frontmatter):
    """String-based frontmatter version extraction (stdlib only).

    Used as fallback when pyyaml is not available.
    """
    metadata_version = None
    version = None
    in_metadata = False

    for line in raw_frontmatter.strip().splitlines():
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
