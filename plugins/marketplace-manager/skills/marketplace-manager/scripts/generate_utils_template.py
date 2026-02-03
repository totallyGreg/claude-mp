#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Generate consistent utils.py for Claude Code skills.

This script generates a utils.py file in a skill's scripts directory
using a standard template. This ensures code duplication is consistent
across skills while maintaining self-contained distributions.

Usage:
    uv run scripts/generate_utils_template.py --skill new-skill
    uv run scripts/generate_utils_template.py --skill my-skill --force
"""

import argparse
import sys
from pathlib import Path

from utils import get_repo_root, print_verbose_info


def load_template(template_path):
    """Load utils.py template file.

    Args:
        template_path: Path to template file

    Returns:
        Template content as string
    """
    try:
        with open(template_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Template not found: {template_path}")
        return None
    except Exception as e:
        print(f"❌ Error loading template: {e}")
        return None


def generate_utils(skill_name, template_content):
    """Generate utils.py content from template.

    Args:
        skill_name: Name of skill
        template_content: Template file content

    Returns:
        Generated utils.py content
    """
    # Replace placeholders
    content = template_content.replace('{SKILL_NAME}', skill_name)
    return content


def write_utils_file(utils_path, content, force=False):
    """Write utils.py file to skill directory.

    Args:
        utils_path: Path where utils.py should be written
        content: Content to write
        force: If True, overwrite existing file

    Returns:
        True if successful, False otherwise
    """
    # Check if file already exists
    if utils_path.exists() and not force:
        print(f"❌ File already exists: {utils_path}")
        print(f"   Use --force to overwrite")
        return False

    # Ensure parent directory exists
    utils_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    try:
        with open(utils_path, 'w') as f:
            f.write(content)
        print(f"✅ Created utils.py: {utils_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Generate consistent utils.py for Claude Code skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate utils.py for a new skill
  %(prog)s --skill my-new-skill

  # Overwrite existing utils.py
  %(prog)s --skill existing-skill --force

  # Generate in specific repository
  %(prog)s --skill my-skill --path /path/to/repo

Notes:
  - Template location: scripts/templates/utils.py.template
  - Output location: skills/{skill-name}/scripts/utils.py
  - Code duplication is intentional for self-contained plugin distributions
""",
    )

    parser.add_argument(
        '--skill',
        required=True,
        help='Name of skill to generate utils.py for'
    )

    parser.add_argument(
        '--path',
        default='.',
        help='Repository root path (default: auto-detect)'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite existing utils.py file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed path resolution information'
    )

    args = parser.parse_args()

    # Determine paths with auto-detection
    repo_root = get_repo_root(args.path, verbose=args.verbose)
    template_path = repo_root / 'skills' / 'marketplace-manager' / 'scripts' / 'templates' / 'utils.py.template'
    skill_scripts_dir = repo_root / 'skills' / args.skill / 'scripts'
    utils_path = skill_scripts_dir / 'utils.py'

    # Print verbose info if requested
    if args.verbose:
        print(f"🔍 Path Resolution:")
        print(f"   Repository root: {repo_root}")
        print(f"   Template path: {template_path}")
        print(f"   Target skill: {args.skill}")
        print(f"   Output path: {utils_path}")
        print()

    print(f"🔧 Generating utils.py for skill: {args.skill}")

    # Check if skill directory exists
    skill_dir = repo_root / 'skills' / args.skill
    if not skill_dir.exists():
        print(f"⚠️  Warning: Skill directory not found: {skill_dir}")
        print(f"   Creating directory structure...")
        skill_dir.mkdir(parents=True, exist_ok=True)

    # Load template
    print(f"📄 Loading template: {template_path.relative_to(repo_root)}")
    template_content = load_template(template_path)
    if template_content is None:
        return 1

    # Generate content
    print(f"⚙️  Generating utils.py from template...")
    utils_content = generate_utils(args.skill, template_content)

    # Write file
    if write_utils_file(utils_path, utils_content, force=args.force):
        print(f"\n✨ Success!")
        print(f"   Generated: {utils_path.relative_to(repo_root)}")
        print(f"   Skill: {args.skill}")
        print(f"\n   Next steps:")
        print(f"   1. Review the generated utils.py")
        print(f"   2. Import in your skill scripts: from utils import get_repo_root")
        print(f"   3. Customize if needed for skill-specific requirements")
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
