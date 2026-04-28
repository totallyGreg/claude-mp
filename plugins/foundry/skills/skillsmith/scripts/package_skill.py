#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
Skill Packager - Creates a distributable skill.zip from a skill directory

Packages a skill directory into a spec-compliant skill.zip for distribution
via agentskills.io. Respects .skillignore rules and validates the skill
structure before packaging.

Usage:
    uv run scripts/package_skill.py <skill-path> [--output <path>] [--dry-run]

Arguments:
    skill-path          Path to the skill directory to package
    --output <path>     Output path for the zip file (default: <skill-name>.zip in cwd)
    --dry-run           Show what would be included without creating the zip

Examples:
    uv run scripts/package_skill.py skills/my-skill
    uv run scripts/package_skill.py ./pdf-editor --output dist/pdf-editor-1.0.0.zip
    uv run scripts/package_skill.py skills/my-skill --dry-run
"""

import argparse
import fnmatch
import re
import sys
import zipfile
from pathlib import Path

import yaml

# Directories that are valid per the AgentSkills spec
SPEC_DIRS = {"scripts", "references", "assets"}

# Default ignore patterns (used when no .skillignore is present)
DEFAULT_IGNORE_PATTERNS = [
    "tests/",
    "test/",
    "*.test.js",
    "*.test.py",
    "*.spec.js",
    "*.spec.py",
    "dist/",
    "build/",
    "*.zip",
    ".git/",
    ".gitignore",
    ".vscode/",
    ".idea/",
    "*.swp",
    "*.swo",
    "*~",
    ".DS_Store",
    "tmp/",
    "temp/",
    "*.tmp",
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "node_modules/",
]


def load_skillignore(skill_root: Path) -> list[str]:
    """Load ignore patterns from .skillignore, falling back to defaults."""
    skillignore = skill_root / ".skillignore"
    if not skillignore.exists():
        return DEFAULT_IGNORE_PATTERNS

    patterns = []
    for line in skillignore.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)
    return patterns


def is_ignored(path: Path, skill_root: Path, patterns: list[str]) -> bool:
    """Return True if the path matches any ignore pattern."""
    rel = path.relative_to(skill_root)
    rel_str = str(rel)

    for pattern in patterns:
        # Directory pattern (ends with /)
        if pattern.endswith("/"):
            dir_name = pattern.rstrip("/")
            # Check if any component of the path matches
            if any(part == dir_name for part in rel.parts):
                return True
        else:
            # Match against the full relative path and the filename
            if fnmatch.fnmatch(rel_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True
    return False


def parse_frontmatter(skill_md: Path) -> dict:
    """Extract and validate YAML frontmatter from SKILL.md."""
    content = skill_md.read_text()
    if not content.startswith("---"):
        return {}

    end = content.find("\n---", 3)
    if end == -1:
        return {}

    yaml_block = content[3:end].strip()
    return yaml.safe_load(yaml_block) or {}


def validate_skill(skill_root: Path) -> list[str]:
    """
    Validate skill structure against AgentSkills spec.
    Returns a list of error messages (empty = valid).
    """
    errors = []
    skill_md = skill_root / "SKILL.md"

    if not skill_md.exists():
        errors.append("SKILL.md not found — required by AgentSkills spec")
        return errors

    frontmatter = parse_frontmatter(skill_md)

    # Validate name
    name = frontmatter.get("name", "")
    if not name:
        errors.append("frontmatter missing required field: name")
    else:
        dir_name = skill_root.name
        if name != dir_name:
            errors.append(f"name '{name}' does not match directory name '{dir_name}'")
        if len(name) > 64:
            errors.append(f"name exceeds 64 characters ({len(name)})")
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$", name):
            errors.append(
                f"name '{name}' must be lowercase alphanumeric with hyphens, "
                "cannot start/end with hyphens"
            )
        if "--" in name:
            errors.append(f"name '{name}' contains consecutive hyphens")

    # Validate description
    description = frontmatter.get("description", "")
    if not description:
        errors.append("frontmatter missing required field: description")
    elif len(description) > 1024:
        errors.append(f"description exceeds 1024 characters ({len(description)})")

    return errors


def collect_files(skill_root: Path, patterns: list[str]) -> list[Path]:
    """
    Collect all files to include in the zip.
    Only includes SKILL.md and files under spec-defined directories.
    """
    included = []

    skill_md = skill_root / "SKILL.md"
    if skill_md.exists():
        included.append(skill_md)

    # README.md travels with the skill (per .skillignore comment)
    readme = skill_root / "README.md"
    if readme.exists() and not is_ignored(readme, skill_root, patterns):
        included.append(readme)

    # Include LICENSE if present
    for license_name in ("LICENSE", "LICENSE.txt", "LICENSE.md"):
        lic = skill_root / license_name
        if lic.exists() and not is_ignored(lic, skill_root, patterns):
            included.append(lic)

    # Walk only spec-defined directories
    for dir_name in sorted(SPEC_DIRS):
        spec_dir = skill_root / dir_name
        if not spec_dir.is_dir():
            continue
        for file_path in sorted(spec_dir.rglob("*")):
            if not file_path.is_file():
                continue
            if is_ignored(file_path, skill_root, patterns):
                continue
            included.append(file_path)

    return included


def create_zip(skill_root: Path, files: list[Path], output_path: Path) -> None:
    """Write the skill zip, using skill directory name as the archive prefix."""
    skill_name = skill_root.name
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            arcname = f"{skill_name}/{file_path.relative_to(skill_root)}"
            zf.write(file_path, arcname)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Package a skill directory into a distributable skill.zip"
    )
    parser.add_argument("skill_path", help="Path to the skill directory")
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for the zip file (default: <skill-name>.zip in cwd)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be included without creating the zip",
    )
    args = parser.parse_args()

    skill_root = Path(args.skill_path).resolve()
    if not skill_root.is_dir():
        print(f"Error: '{skill_root}' is not a directory", file=sys.stderr)
        return 1

    # Validate
    errors = validate_skill(skill_root)
    if errors:
        print("Validation failed — skill does not meet AgentSkills spec:\n")
        for err in errors:
            print(f"  ✗ {err}")
        return 1

    skill_name = skill_root.name
    output_path = Path(args.output).resolve() if args.output else Path.cwd() / f"{skill_name}.zip"

    # Load ignore patterns and collect files
    patterns = load_skillignore(skill_root)
    files = collect_files(skill_root, patterns)

    if not files:
        print("Error: no files to package (SKILL.md missing?)", file=sys.stderr)
        return 1

    # Report
    print(f"Skill:  {skill_name}")
    print(f"Source: {skill_root}")
    print(f"Output: {output_path}")
    print(f"\nFiles to include ({len(files)}):")
    for f in files:
        rel = f.relative_to(skill_root)
        print(f"  {skill_name}/{rel}")

    if args.dry_run:
        print("\nDry run — no zip created.")
        return 0

    create_zip(skill_root, files, output_path)
    size_kb = output_path.stat().st_size / 1024
    print(f"\n✓ Created {output_path.name} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
