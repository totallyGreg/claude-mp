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
from typing import NamedTuple

from utils import find_repo_root


class PathIssue(NamedTuple):
    """Represents a path reference issue found during audit."""

    file_path: Path
    line_number: int
    line_content: str
    issue_type: str  # 'hardcoded_absolute' or 'relative_skill_ref'
    matched_pattern: str


# File extensions to scan for path references
SCANNABLE_EXTENSIONS = {
    ".md",
    ".js",
    ".ts",
    ".json",
    ".sh",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

# Binary/generated directories to skip
SKIP_DIRS = {"node_modules", ".git", "__pycache__", "dist", "build", ".next"}


def get_tracked_top_level_items(repo_root: Path, source_dir: Path) -> list[Path]:
    """Get top-level items in source_dir that are tracked by git.

    Uses `git ls-files` to respect .gitignore and only return tracked items.

    Args:
        repo_root: Repository root path
        source_dir: Directory to list

    Returns:
        List of Path objects for top-level tracked files/directories
    """
    rel_source = source_dir.relative_to(repo_root)
    cmd = ["git", "ls-files", str(rel_source)]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)

    if result.returncode != 0:
        return []

    # Get unique top-level items from tracked files
    top_level_items: set[Path] = set()
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        file_path = repo_root / line
        # Get the immediate child of source_dir
        try:
            rel_to_source = file_path.relative_to(source_dir)
            top_item = source_dir / rel_to_source.parts[0]
            top_level_items.add(top_item)
        except ValueError:
            continue

    return sorted(top_level_items)


def should_scan_file(file_path: Path) -> bool:
    """Check if file should be scanned for path references.

    Args:
        file_path: Path to check

    Returns:
        True if file should be scanned
    """
    # Skip files in excluded directories
    for part in file_path.parts:
        if part in SKIP_DIRS:
            return False

    # Only scan text files with known extensions
    return file_path.suffix.lower() in SCANNABLE_EXTENSIONS


def find_path_issues_in_file(file_path: Path, skill_name: str) -> list[PathIssue]:
    """Scan a single file for path reference issues.

    Args:
        file_path: Path to file to scan
        skill_name: Name of skill being migrated

    Returns:
        List of PathIssue objects found
    """
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return issues

    lines = content.splitlines()

    # Pattern for hardcoded absolute paths containing skill name
    # Matches: /Users/*/skills/<name>/ or /home/*/skills/<name>/
    abs_pattern = re.compile(
        rf"(/(?:Users|home)/[^/]+/[^'\"\s]*skills/{re.escape(skill_name)}[^'\"\s]*)"
    )

    # Pattern for relative skill references in repo context
    # Matches: skills/<name>/ or ./skills/<name>/
    rel_pattern = re.compile(
        rf"(?:^|['\"\s(])(\./)?skills/{re.escape(skill_name)}(?:/|['\"\s)]|$)"
    )

    for line_num, line in enumerate(lines, start=1):
        # Check for hardcoded absolute paths
        abs_matches = abs_pattern.findall(line)
        for match in abs_matches:
            issues.append(
                PathIssue(
                    file_path=file_path,
                    line_number=line_num,
                    line_content=line.strip()[:100],
                    issue_type="hardcoded_absolute",
                    matched_pattern=match,
                )
            )

        # Check for relative skill references (only in certain file types)
        # Skip if this looks like it's within the skill itself (internal refs are ok)
        if file_path.suffix in {".md", ".json", ".yaml", ".yml"}:
            if rel_pattern.search(line):
                # Extract the matched portion
                match = rel_pattern.search(line)
                if match:
                    issues.append(
                        PathIssue(
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line.strip()[:100],
                            issue_type="relative_skill_ref",
                            matched_pattern=f"skills/{skill_name}",
                        )
                    )

    return issues


def audit_path_references(
    source_dir: Path, skill_name: str
) -> dict[str, list[PathIssue]]:
    """Scan all files in skill directory for path reference issues.

    Args:
        source_dir: Skill source directory
        skill_name: Name of skill being migrated

    Returns:
        Dictionary with 'hardcoded_absolute' and 'relative_skill_ref' lists
    """
    results: dict[str, list[PathIssue]] = {
        "hardcoded_absolute": [],
        "relative_skill_ref": [],
    }

    # Walk all files in source directory
    for file_path in source_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if not should_scan_file(file_path):
            continue

        issues = find_path_issues_in_file(file_path, skill_name)
        for issue in issues:
            results[issue.issue_type].append(issue)

    return results


def print_audit_results(
    audit_results: dict[str, list[PathIssue]],
    repo_root: Path,
    verbose: bool = False,
) -> None:
    """Print audit results in a readable format.

    Args:
        audit_results: Results from audit_path_references
        repo_root: Repository root for relative path display
        verbose: Show full details
    """
    hardcoded = audit_results["hardcoded_absolute"]
    relative = audit_results["relative_skill_ref"]

    if not hardcoded and not relative:
        print("  ✅ No path reference issues detected")
        return

    total_issues = len(hardcoded) + len(relative)
    print(f"\n  Found {total_issues} path references to update to ${{CLAUDE_PLUGIN_ROOT}}:")

    if hardcoded:
        print(f"\n  📍 Hardcoded absolute paths ({len(hardcoded)}):")
        seen_files: set[Path] = set()
        for issue in hardcoded:
            rel_path = issue.file_path.relative_to(repo_root)
            if verbose or issue.file_path not in seen_files:
                print(f"     • {rel_path}:{issue.line_number}")
                if verbose:
                    print(f"       {issue.line_content}")
                seen_files.add(issue.file_path)

    if relative:
        print(f"\n  📍 Relative skill references ({len(relative)}):")
        seen_files = set()
        for issue in relative:
            rel_path = issue.file_path.relative_to(repo_root)
            if verbose or issue.file_path not in seen_files:
                print(f"     • {rel_path}:{issue.line_number}")
                if verbose:
                    print(f"       {issue.line_content}")
                seen_files.add(issue.file_path)


def fix_path_references(
    source_dir: Path,
    skill_name: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> list[dict]:
    """Fix all path references to use ${CLAUDE_PLUGIN_ROOT}.

    Replaces:
    - Hardcoded absolute paths: /Users/.../skills/<name>/... → ${CLAUDE_PLUGIN_ROOT}/skills/<name>/...
    - Relative repo paths: skills/<name>/... → ${CLAUDE_PLUGIN_ROOT}/skills/<name>/...

    Args:
        source_dir: Skill source directory
        skill_name: Name of skill being migrated
        dry_run: If True, don't actually modify files
        verbose: Show detailed output

    Returns:
        List of fix records with file and replacement details
    """
    fixes_applied = []

    # Pattern for hardcoded absolute paths
    # Matches: /Users/*/...skills/<name>/ or /home/*/...skills/<name>/
    abs_pattern = re.compile(
        rf"(/(?:Users|home)/[^'\"\s]*/skills/{re.escape(skill_name)})"
    )

    # Replacement target using CLAUDE_PLUGIN_ROOT
    plugin_root_path = f"${{CLAUDE_PLUGIN_ROOT}}/skills/{skill_name}"

    for file_path in source_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if not should_scan_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        original_content = content
        replacements = []

        # Fix hardcoded absolute paths
        abs_matches = abs_pattern.findall(content)
        if abs_matches:
            for match in set(abs_matches):
                content = content.replace(match, plugin_root_path)
                replacements.append(
                    {"type": "absolute", "old": match, "new": plugin_root_path}
                )

        # Fix relative skill references (skills/<name> without leading /)
        # But avoid matching if already using ${CLAUDE_PLUGIN_ROOT}
        rel_pattern = f"skills/{skill_name}"
        if rel_pattern in content and "${CLAUDE_PLUGIN_ROOT}" not in content:
            # Only replace standalone references, not ones already fixed
            content = content.replace(rel_pattern, plugin_root_path)
            replacements.append(
                {"type": "relative", "old": rel_pattern, "new": plugin_root_path}
            )

        if content != original_content:
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")

            fixes_applied.append(
                {
                    "file": file_path,
                    "replacements": replacements,
                }
            )

            if verbose:
                prefix = "[DRY RUN] " if dry_run else ""
                print(f"  {prefix}Fixed: {file_path.name} ({len(replacements)} replacements)")

    return fixes_applied


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

            # Extract description (handles both single-line and YAML multiline)
            desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
            if desc_match:
                desc_value = desc_match.group(1).strip()
                # Check for YAML multiline indicators (| or >)
                if desc_value in ("|", ">", "|+", "|-", ">+", ">-"):
                    # Extract indented lines following the indicator
                    multiline_match = re.search(
                        r"^description:\s*[|>][-+]?\s*\n((?:[ \t]+.+\n?)+)",
                        frontmatter,
                        re.MULTILINE,
                    )
                    if multiline_match:
                        # Join lines and normalize whitespace
                        lines = multiline_match.group(1).strip().split("\n")
                        desc_value = " ".join(line.strip() for line in lines)
                metadata["description"] = desc_value

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

    # Audit path references
    print("🔍 Auditing path references...")
    audit_results = audit_path_references(source_dir, skill_name)
    print_audit_results(audit_results, repo_root, verbose)

    # Fix path references (convert to ${CLAUDE_PLUGIN_ROOT})
    has_path_issues = (
        audit_results["hardcoded_absolute"] or audit_results["relative_skill_ref"]
    )
    path_fixes: list[dict] = []
    if has_path_issues:
        print()
        print("🔧 Fixing path references to use ${CLAUDE_PLUGIN_ROOT}...")
        path_fixes = fix_path_references(
            source_dir, skill_name, dry_run=dry_run, verbose=verbose
        )
        if path_fixes:
            print(f"  ✅ Updated {len(path_fixes)} file(s)")
        else:
            print("  ℹ️  No fixes applied (patterns may have been in non-scannable files)")
    print()

    # Define migration plan
    new_dirs = [
        target_dir / ".claude-plugin",
        target_dir / "commands",
        target_dir / "skills" / skill_name,
    ]

    # Define files to move (only git-tracked items, respects .gitignore)
    source_contents = get_tracked_top_level_items(repo_root, source_dir)

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
        print()

        # Dry-run summary
        if path_fixes:
            print("Path fixes to apply:")
            for fix in path_fixes:
                rel_path = fix["file"].relative_to(repo_root)
                print(f"  🔧 {rel_path}")
            print()

        print("Run without --dry-run to execute migration.")
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

    # Print migration report
    print()
    print("=" * 60)
    print(f"✅ Migration complete: {skill_name}")
    print("=" * 60)
    print()
    print(f"📁 New location: {target_dir.relative_to(repo_root)}")
    print()

    # Path fixes summary
    if path_fixes:
        print("🔧 Path references updated:")
        for fix in path_fixes:
            rel_path = fix["file"].relative_to(repo_root)
            count = len(fix["replacements"])
            print(f"   • {rel_path} ({count} replacement(s))")
        print()

    print("📋 Next steps:")
    print("  1. Review path changes in updated files")
    print("  2. Add commands to commands/ directory (optional)")
    print("  3. Bump version (major version for breaking change)")
    print("  4. Test scripts still work with new paths")
    print("  5. Validate with: /skillsmith evaluate")
    print("  6. Commit with:")
    print(f"     git commit -m 'feat({skill_name}): Migrate to standalone plugin'")

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
