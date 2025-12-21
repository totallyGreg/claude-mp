#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import argparse
from pathlib import Path
from datetime import datetime

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

    # Extract version for improvement plan validation
    version_match = re.search(r'version:\s*(.+)', frontmatter)
    skill_version = version_match.group(1).strip() if version_match else None

    return True, "Skill is valid!", skill_version


def validate_improvement_plan(skill_path, skill_version=None):
    """Validate IMPROVEMENT_PLAN.md completeness and consistency"""
    skill_path = Path(skill_path)
    improvement_plan = skill_path / 'IMPROVEMENT_PLAN.md'

    if not improvement_plan.exists():
        return True, "✓ IMPROVEMENT_PLAN.md not present (optional)"

    errors = []
    warnings = []

    try:
        content = improvement_plan.read_text()
        lines = content.split('\n')

        # Find version history table
        version_history_start = None
        for i, line in enumerate(lines):
            if '## Version History' in line:
                version_history_start = i
                break

        if version_history_start is None:
            return True, "✓ IMPROVEMENT_PLAN.md exists but no version history found"

        # Parse version history table
        versions = []
        in_table = False
        for i in range(version_history_start, len(lines)):
            line = lines[i].strip()

            # Skip header and separator rows
            if line.startswith('|') and 'Version' in line:
                in_table = True
                continue
            if line.startswith('|') and '---' in line:
                continue
            if not line.startswith('|'):
                if in_table:
                    break
                continue

            # Parse version row: | version | date | description |
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Skip empty first/last
            if len(parts) >= 2:
                version = parts[0]
                date = parts[1]
                versions.append({
                    'version': version,
                    'date': date,
                    'line': i + 1
                })

        if not versions:
            return True, "✓ IMPROVEMENT_PLAN.md version history table is empty"

        # Check for TBD in version history
        tbd_versions = [v for v in versions if v['date'].upper() == 'TBD']
        if tbd_versions:
            for v in tbd_versions:
                # If this is the current skill version, it's an error
                if skill_version and v['version'] == skill_version:
                    errors.append(
                        f"❌ Version {v['version']} in SKILL.md shows 'TBD' in IMPROVEMENT_PLAN.md\n"
                        f"   → Replace 'TBD' with completion date (YYYY-MM-DD) before release\n"
                        f"   → File: IMPROVEMENT_PLAN.md line {v['line']}"
                    )
                else:
                    warnings.append(
                        f"⚠️  Version {v['version']} has 'TBD' date\n"
                        f"   → This is acceptable for planned/in-progress versions\n"
                        f"   → File: IMPROVEMENT_PLAN.md line {v['line']}"
                    )

        # Check version consistency
        if skill_version and versions:
            latest_version = versions[0]['version']  # Assumes newest first
            if skill_version != latest_version:
                warnings.append(
                    f"⚠️  SKILL.md version ({skill_version}) differs from latest IMPROVEMENT_PLAN.md version ({latest_version})\n"
                    f"   → This may be intentional if you haven't updated SKILL.md yet"
                )

        # Check date chronology (if not TBD)
        dated_versions = [v for v in versions if v['date'].upper() != 'TBD' and v['date'].lower() != 'initial']
        if len(dated_versions) > 1:
            try:
                dates = [datetime.strptime(v['date'], '%Y-%m-%d') for v in dated_versions]
                # Check if dates are in descending order (newest first)
                if dates != sorted(dates, reverse=True):
                    warnings.append(
                        "⚠️  Version history dates may not be in chronological order\n"
                        "   → Consider ordering newest versions first"
                    )
            except ValueError:
                # Invalid date format, skip chronology check
                pass

        # Return results
        if errors:
            return False, '\n\n'.join(errors)
        elif warnings:
            return True, '\n\n'.join(warnings)
        else:
            return True, "✓ IMPROVEMENT_PLAN.md is complete and consistent"

    except Exception as e:
        return False, f"❌ Error validating IMPROVEMENT_PLAN.md: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate skill structure and consistency')
    parser.add_argument('skill_directory', help='Path to skill directory')
    parser.add_argument('--check-improvement-plan', action='store_true',
                       help='Also validate IMPROVEMENT_PLAN.md completeness')

    args = parser.parse_args()

    # Basic skill validation
    result = validate_skill(args.skill_directory)
    valid = result[0]
    message = result[1]
    skill_version = result[2] if len(result) > 2 else None

    print(message)

    if not valid:
        sys.exit(1)

    # IMPROVEMENT_PLAN.md validation if requested
    if args.check_improvement_plan:
        print()  # Blank line
        ip_valid, ip_message = validate_improvement_plan(args.skill_directory, skill_version)
        print(ip_message)

        if not ip_valid:
            sys.exit(1)

    sys.exit(0)