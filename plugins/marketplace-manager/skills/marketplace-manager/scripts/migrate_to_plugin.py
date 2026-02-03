#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Migrate a legacy skill from skills/ to standalone plugin structure in plugins/.

Usage:
    python3 migrate_to_plugin.py <skill-name> [options]

Examples:
    python3 migrate_to_plugin.py my-skill --dry-run
    python3 migrate_to_plugin.py my-skill --verbose
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from utils import find_repo_root


def extract_skill_metadata(skill_md_path: Path) -> dict:
    """Extract metadata from SKILL.md frontmatter.

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Dictionary with extracted metadata
    """
    metadata = {
        "name": "",
        "description": "",
        "version": "1.0.0",
        "author": "Unknown",
    }

    if not skill_md_path.exists():
        return metadata

    content = skill_md_path.read_text()

    # Extract frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]

            # Extract name
            name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
            if name_match:
                metadata["name"] = name_match.group(1).strip()

            # Extract description
            desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
            if desc_match:
                metadata["description"] = desc_match.group(1).strip()

            # Extract version (check metadata.version first, then version)
            meta_version_match = re.search(
                r"metadata:\s*\n\s+version:\s*[\"']?([^\"'\n]+)[\"']?",
                frontmatter,
                re.MULTILINE,
            )
            if meta_version_match:
                metadata["version"] = meta_version_match.group(1).strip()
            else:
                version_match = re.search(
                    r"^version:\s*[\"']?([^\"'\n]+)[\"']?$",
                    frontmatter,
                    re.MULTILINE,
                )
                if version_match:
                    metadata["version"] = version_match.group(1).strip()

            # Extract author from metadata
            author_match = re.search(
                r"author:\s*(.+)$",
                frontmatter,
                re.MULTILINE,
            )
            if author_match:
                metadata["author"] = author_match.group(1).strip()

    return metadata


def migrate_skill(
    repo_root: Path,
    skill_name: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """Migrate a skill from skills/ to plugins/ structure.

    Args:
        repo_root: Repository root path
        skill_name: Name of skill to migrate
        dry_run: If True, preview changes without executing
        verbose: If True, show detailed output

    Returns:
        True if successful, False otherwise
    """
    skills_dir = repo_root / "skills"
    plugins_dir = repo_root / "plugins"
    source_dir = skills_dir / skill_name
    target_dir = plugins_dir / skill_name

    # Validate source exists
    if not source_dir.exists():
        print(f"❌ Error: Skill not found at {source_dir}")
        return False

    # Check target doesn't exist
    if target_dir.exists():
        print(f"❌ Error: Plugin directory already exists at {target_dir}")
        return False

    # Extract metadata from SKILL.md
    skill_md_path = source_dir / "SKILL.md"
    metadata = extract_skill_metadata(skill_md_path)

    if verbose:
        print(f"📋 Extracted metadata:")
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print()

    # Define migration plan
    new_dirs = [
        target_dir / ".claude-plugin",
        target_dir / "commands",
        target_dir / "skills" / skill_name,
    ]

    # Define files to move
    source_contents = list(source_dir.iterdir()) if source_dir.exists() else []

    # Create plugin.json
    plugin_json = {
        "name": skill_name,
        "version": metadata["version"],
        "description": metadata["description"] or f"{skill_name} plugin",
        "author": {
            "name": "J. Greg Williams",
            "email": "283704+totallyGreg@users.noreply.github.com",
        },
        "license": "MIT",
        "keywords": [skill_name],
    }

    if dry_run:
        print(f"🔍 [DRY RUN] Migration plan for: {skill_name}")
        print()
        print("Directories to create:")
        for d in new_dirs:
            print(f"  📁 {d.relative_to(repo_root)}")
        print()
        print("Files to move (git mv):")
        for item in source_contents:
            rel_source = item.relative_to(repo_root)
            rel_target = target_dir / "skills" / skill_name / item.name
            print(f"  📄 {rel_source} → {rel_target.relative_to(repo_root)}")
        print()
        print("Files to create:")
        print(f"  📄 {(target_dir / '.claude-plugin' / 'plugin.json').relative_to(repo_root)}")
        print(json.dumps(plugin_json, indent=2))
        print()
        print("marketplace.json update:")
        print(f"  source: ./skills/{skill_name} → ./plugins/{skill_name}")
        print(f"  skills: ['./'] → ['./skills/{skill_name}']")
        print()
        print("Empty directory to remove:")
        print(f"  📁 {source_dir.relative_to(repo_root)}")
        return True

    # Execute migration
    print(f"🚀 Migrating {skill_name} to standalone plugin...")

    # Create directories
    for d in new_dirs:
        d.mkdir(parents=True, exist_ok=True)
        if verbose:
            print(f"  ✅ Created: {d.relative_to(repo_root)}")

    # Write plugin.json
    plugin_json_path = target_dir / ".claude-plugin" / "plugin.json"
    with open(plugin_json_path, "w") as f:
        json.dump(plugin_json, f, indent=2)
        f.write("\n")
    if verbose:
        print(f"  ✅ Created: {plugin_json_path.relative_to(repo_root)}")

    # Move files with git mv
    for item in source_contents:
        target_path = target_dir / "skills" / skill_name / item.name
        cmd = ["git", "mv", str(item), str(target_path)]
        if verbose:
            print(f"  🔄 git mv {item.relative_to(repo_root)} → {target_path.relative_to(repo_root)}")
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ git mv failed: {result.stderr}")
            return False

    # Remove empty source directory
    if source_dir.exists() and not any(source_dir.iterdir()):
        source_dir.rmdir()
        if verbose:
            print(f"  ✅ Removed empty: {source_dir.relative_to(repo_root)}")

    # Update marketplace.json
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    if marketplace_path.exists():
        with open(marketplace_path) as f:
            marketplace = json.load(f)

        updated = False
        for plugin in marketplace.get("plugins", []):
            if plugin.get("name") == skill_name:
                old_source = plugin.get("source", "")
                plugin["source"] = f"./plugins/{skill_name}"
                plugin["skills"] = [f"./skills/{skill_name}"]
                plugin["version"] = metadata["version"]
                updated = True
                if verbose:
                    print(f"  ✅ Updated marketplace.json: {old_source} → ./plugins/{skill_name}")
                break

        if updated:
            with open(marketplace_path, "w") as f:
                json.dump(marketplace, f, indent=2)
                f.write("\n")

    print()
    print(f"✅ Migration complete: {skill_name}")
    print(f"   New location: {target_dir.relative_to(repo_root)}")
    print()
    print("Next steps:")
    print("  1. Add commands to commands/ directory")
    print("  2. Update version to major bump (breaking change)")
    print("  3. Update IMPROVEMENT_PLAN.md")
    print("  4. Test all scripts still work")
    print("  5. Commit with: git commit -m 'refactor: Migrate to standalone plugin'")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate a legacy skill to standalone plugin structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s my-skill --dry-run
    %(prog)s my-skill --verbose
        """,
    )
    parser.add_argument("skill_name", help="Name of skill to migrate")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without executing",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--path", default=".", help="Repository path")

    args = parser.parse_args()

    # Find repository root
    repo_root = find_repo_root(args.path if args.path != "." else None)
    if repo_root is None:
        print("❌ Error: Could not find repository root")
        sys.exit(1)

    if args.verbose:
        print(f"📁 Repository root: {repo_root}")
        print()

    # Execute migration
    success = migrate_skill(
        repo_root=repo_root,
        skill_name=args.skill_name,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
