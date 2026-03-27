#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Initialize a Claude Code marketplace repository for self-sufficiency.

Sets up a marketplace repo with:
- .claude-plugin/marketplace.json (official Anthropic schema)
- Repo-local validation and sync scripts
- Pre-commit hook for automated checks

After setup, the repo owns its own validation and sync logic with no
runtime dependency on marketplace-manager.

Usage:
    python3 setup.py init [--name NAME] [--owner-name NAME] [--owner-email EMAIL]
    python3 setup.py install-scripts [--target-dir ./scripts]
    python3 setup.py install-hook [--dry-run]
    python3 setup.py all [--name NAME] [--owner-name NAME] [--owner-email EMAIL]
"""

import argparse
import json
import shutil
import stat
import sys
from datetime import datetime
from pathlib import Path

# Location of repo-level scripts bundled with marketplace-manager
REPO_SCRIPTS_DIR = Path(__file__).parent / "repo"
REPO_SCRIPTS = ["validate.py", "sync.py"]

HOOK_CONTENT = """\
#!/bin/sh
# Pre-commit hook: validate marketplace.json and sync versions.
# Installed by marketplace-manager setup.py

set -e

if [ -f ".claude-plugin/marketplace.json" ]; then
    python3 scripts/validate.py --staged
    python3 scripts/sync.py
fi
"""


# -- Subcommands -------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> bool:
    """Create .claude-plugin/marketplace.json with official schema fields."""
    mp_dir = Path(".claude-plugin")
    mp_path = mp_dir / "marketplace.json"

    if mp_path.exists():
        print(f"Already exists: {mp_path}")
        print("  Use a text editor to modify it directly.")
        return True

    # Gather name
    name = args.name
    if not name:
        name = input("Marketplace name (kebab-case): ").strip()
    if not name:
        print("Error: marketplace name is required.", file=sys.stderr)
        return False

    # Gather owner
    owner_name = args.owner_name
    if not owner_name:
        owner_name = input("Owner name: ").strip()
    if not owner_name:
        print("Error: owner name is required.", file=sys.stderr)
        return False

    owner = {"name": owner_name}
    owner_email = args.owner_email
    if not owner_email:
        owner_email = input("Owner email (optional, press Enter to skip): ").strip()
    if owner_email:
        owner["email"] = owner_email

    # Build manifest with official schema fields only
    manifest = {
        "name": name,
        "owner": owner,
        "plugins": [],
    }

    # Create directory and write
    mp_dir.mkdir(parents=True, exist_ok=True)
    with open(mp_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Created {mp_path}")
    print(f"  name: {name}")
    print(f"  owner: {owner_name}")
    return True


def cmd_install_scripts(args: argparse.Namespace) -> bool:
    """Copy validate.py and sync.py into the target repo's scripts directory."""
    target_dir = Path(args.target_dir)
    force = getattr(args, "force", False)

    if not REPO_SCRIPTS_DIR.is_dir():
        print(
            f"Error: repo scripts directory not found: {REPO_SCRIPTS_DIR}",
            file=sys.stderr,
        )
        return False

    # Verify all source scripts exist before copying
    for script_name in REPO_SCRIPTS:
        src = REPO_SCRIPTS_DIR / script_name
        if not src.is_file():
            print(f"Error: source script not found: {src}", file=sys.stderr)
            return False

    target_dir.mkdir(parents=True, exist_ok=True)

    for script_name in REPO_SCRIPTS:
        src = REPO_SCRIPTS_DIR / script_name
        dst = target_dir / script_name
        if dst.exists() and not force:
            print(f"  Skipped {dst} (already exists; use --force to overwrite)")
            continue
        action = "Updated" if dst.exists() else "Copied"
        shutil.copy2(src, dst)
        print(f"  {action} {dst}")

    print(f"Repo scripts installed to {target_dir}/")
    return True


def cmd_install_hook(args: argparse.Namespace) -> bool:
    """Install a pre-commit hook that runs validate.py and sync.py."""
    hooks_dir = Path(".git/hooks")

    if not Path(".git").is_dir():
        print("Error: not a git repository (no .git directory).", file=sys.stderr)
        return False

    hook_path = hooks_dir / "pre-commit"

    if args.dry_run:
        print("Would install pre-commit hook:")
        print(f"  Path: {hook_path}")
        if hook_path.exists():
            print("  Note: existing hook would be backed up")
        print()
        print("Hook content:")
        for line in HOOK_CONTENT.strip().splitlines():
            print(f"  {line}")
        return True

    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Back up existing hook
    if hook_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup = hook_path.with_suffix(f".backup-{timestamp}")
        shutil.copy2(hook_path, backup)
        print(f"  Backed up existing hook to {backup}")

    hook_path.write_text(HOOK_CONTENT)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    print(f"  Installed pre-commit hook: {hook_path}")
    return True


def cmd_all(args: argparse.Namespace) -> bool:
    """Run init + install-scripts + install-hook in sequence."""
    print("=== Step 1/3: Initialize marketplace.json ===")
    if not cmd_init(args):
        return False

    print()
    print("=== Step 2/3: Install repo scripts ===")
    if not cmd_install_scripts(args):
        return False

    print()
    print("=== Step 3/3: Install pre-commit hook ===")
    if not cmd_install_hook(args):
        return False

    print()
    print("Setup complete. Your marketplace repo is now self-sufficient.")
    print("  - Run 'python3 scripts/validate.py' to validate")
    print("  - Run 'python3 scripts/sync.py' to sync versions")
    print("  - Pre-commit hook runs both automatically")
    return True


# -- CLI ---------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Initialize a Claude Code marketplace repository.",
        prog="setup.py",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser(
        "init", help="Create .claude-plugin/marketplace.json",
    )
    p_init.add_argument("--name", help="Marketplace name (kebab-case)")
    p_init.add_argument("--owner-name", help="Owner name")
    p_init.add_argument("--owner-email", help="Owner email (optional)")

    # install-scripts
    p_scripts = subparsers.add_parser(
        "install-scripts",
        help="Copy validate.py and sync.py into the repo",
    )
    p_scripts.add_argument(
        "--target-dir", default="./scripts",
        help="Destination directory (default: ./scripts)",
    )
    p_scripts.add_argument(
        "--force", action="store_true",
        help="Overwrite existing scripts",
    )

    # install-hook
    p_hook = subparsers.add_parser(
        "install-hook", help="Install a pre-commit hook",
    )
    p_hook.add_argument(
        "--dry-run", action="store_true",
        help="Preview hook content without installing",
    )

    # all
    p_all = subparsers.add_parser(
        "all", help="Run init + install-scripts + install-hook",
    )
    p_all.add_argument("--name", help="Marketplace name (kebab-case)")
    p_all.add_argument("--owner-name", help="Owner name")
    p_all.add_argument("--owner-email", help="Owner email (optional)")
    p_all.add_argument(
        "--target-dir", default="./scripts",
        help="Scripts destination directory (default: ./scripts)",
    )
    p_all.add_argument(
        "--dry-run", action="store_true",
        help="Preview hook content without installing",
    )
    p_all.add_argument(
        "--force", action="store_true",
        help="Overwrite existing scripts",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "install-scripts": cmd_install_scripts,
        "install-hook": cmd_install_hook,
        "all": cmd_all,
    }

    handler = commands.get(args.command)
    if not handler:
        parser.print_help()
        sys.exit(1)

    success = handler(args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
