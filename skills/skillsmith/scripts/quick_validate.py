#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
Compatible with upstream Anthropic skill-creator
"""

import sys
import os
import re
import argparse
from pathlib import Path


def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter = match.group(1)

    # Check required fields
    if 'name:' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description:' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name_match = re.search(r'name:\s*(.+)', frontmatter)
    if name_match:
        name = name_match.group(1).strip()
        # Check naming convention (hyphen-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"

    # Extract and validate description
    desc_match = re.search(r'description:\s*(.+)', frontmatter)
    if desc_match:
        description = desc_match.group(1).strip()
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"

    # Extract version for potential use by other scripts
    version_match = re.search(r'version:\s*(.+)', frontmatter)
    skill_version = version_match.group(1).strip() if version_match else None

    return True, "Skill is valid!", skill_version


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate skill structure')
    parser.add_argument('skill_directory', help='Path to skill directory')

    args = parser.parse_args()

    # Basic skill validation
    result = validate_skill(args.skill_directory)
    valid = result[0]
    message = result[1]

    print(message)

    sys.exit(0 if valid else 1)
