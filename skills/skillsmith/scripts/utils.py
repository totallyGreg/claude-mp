"""Shared utilities for skillsmith scripts."""

import sys
from pathlib import Path


def find_repo_root(start_path=None):
    """Find repository root by searching for .git or .claude-plugin directory.

    Args:
        start_path: Starting directory (defaults to current directory)

    Returns:
        Path to repository root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path

    # Search up to 10 levels (prevent infinite loops)
    for _ in range(10):
        # Check for .git directory (most reliable)
        if (current / ".git").exists():
            return current

        # Check for .claude-plugin directory
        if (current / ".claude-plugin").exists():
            return current

        # Move to parent
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

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
