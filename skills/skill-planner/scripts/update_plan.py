#!/usr/bin/env python3
"""
Update improvement plan with refinements

This script handles plan refinements during the planning phase.
Increments version and updates PLAN.md with new recommendations.

Usage:
    python3 update_plan.py [--instructions "refinement instructions"]

Week 1 Implementation Status:
    [x] Version increment (v1 → v2)
    [x] PLAN.md update and commit
    [ ] Integration with skillsmith research (Week 2)
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


def find_repository_root():
    """Find git repository root"""
    current = Path.cwd()

    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent

    raise Exception("Not in a git repository")


def get_current_branch():
    """Get current git branch name"""
    result = subprocess.run(
        ['git', 'branch', '--show-current'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def is_planning_branch(branch_name):
    """Check if current branch is a planning branch"""
    return branch_name.startswith('plan/')


def read_plan_file():
    """Read current PLAN.md"""
    if not Path('PLAN.md').exists():
        raise Exception("PLAN.md not found. Create a plan first.")

    with open('PLAN.md') as f:
        return f.read()


def get_plan_status(plan_content):
    """Extract status from PLAN.md"""
    for line in plan_content.split('\n'):
        if line.startswith('**Status:**'):
            status = line.split('**Status:**')[1].strip().split('|')[0].strip()
            return status
    return None


def get_current_version(plan_content):
    """Extract current version from PLAN.md"""
    for line in plan_content.split('\n'):
        if line.startswith('**Version:**'):
            version = line.split('**Version:**')[1].strip()
            # Extract version number (e.g., "v1" or "v1 (if refined)" -> 1)
            if version.startswith('v'):
                # Get just the number part before any space or parenthesis
                version_num = version[1:].split()[0].split('(')[0]
                return int(version_num)
    return 1


def increment_version(plan_content):
    """
    Increment version in PLAN.md

    Returns: (updated_content, new_version)
    """
    current_version = get_current_version(plan_content)
    new_version = current_version + 1

    # Update version line
    updated = []
    for line in plan_content.split('\n'):
        if line.startswith('**Version:**'):
            updated.append(f'**Version:** v{new_version}')
        else:
            updated.append(line)

    return '\n'.join(updated), new_version


def add_revision_note(plan_content, version, instructions=None):
    """Add revision note to Revision History section"""
    now = datetime.now().isoformat() + 'Z'

    # Find Revision History section
    lines = plan_content.split('\n')
    revision_idx = None

    for i, line in enumerate(lines):
        if line.startswith('## Revision History'):
            revision_idx = i
            break

    if revision_idx is None:
        raise Exception("Revision History section not found in PLAN.md")

    # Find where to insert (after the header, skip blank line)
    insert_idx = revision_idx + 2

    # Create revision note
    revision_note = [
        '',
        f'### v{version} ({now})',
    ]

    if instructions:
        revision_note.extend([
            f'- Refinement requested: {instructions}',
            '- Plan updated based on feedback'
        ])
    else:
        revision_note.append('- Plan refined and updated')

    # Insert revision note
    lines[insert_idx:insert_idx] = revision_note

    return '\n'.join(lines)


def update_plan(instructions=None, research_findings=None):
    """
    Update PLAN.md with refinements

    For Week 1: Basic update with version increment
    Week 2: Integration with skillsmith research for refinements
    """
    # Verify we're on a planning branch
    current_branch = get_current_branch()
    if not is_planning_branch(current_branch):
        raise Exception(f"Not on a planning branch. Current branch: {current_branch}")

    # Read current plan
    plan_content = read_plan_file()

    # Check status
    status = get_plan_status(plan_content)
    if status not in ['draft', None]:
        raise Exception(f"Cannot update plan with status '{status}'. Only draft plans can be updated.")

    # Increment version
    updated_content, new_version = increment_version(plan_content)

    # Add revision note
    updated_content = add_revision_note(updated_content, new_version, instructions)

    # Week 2: This is where we'll integrate skillsmith research
    # For now, just increment version and add revision note
    if research_findings:
        # TODO Week 2: Apply research findings to proposed changes
        pass

    # Write updated plan
    with open('PLAN.md', 'w') as f:
        f.write(updated_content)

    print(f"✓ Updated PLAN.md to v{new_version}")

    # Git add and commit
    subprocess.run(['git', 'add', 'PLAN.md'], check=True)
    commit_msg = f'Update plan to v{new_version}'
    if instructions:
        commit_msg += f': {instructions}'
    subprocess.run(
        ['git', 'commit', '-m', commit_msg],
        check=True
    )

    print(f"✓ Committed changes to {current_branch}")

    return new_version


def show_update_summary(version):
    """Show update summary"""
    print(f"""
╔═══════════════════════════════════════════════════════╗
║  Plan Updated                                          ║
╚═══════════════════════════════════════════════════════╝

Version: v{version}
Status: draft
Plan: PLAN.md

Next Steps:
  1. Review updated plan
  2. Refine further if needed:
     "Refine plan - <instructions>"
  3. When ready:
     "Approve plan"

Note: This is Week 1 implementation.
      Week 2 will integrate skillsmith research for refinements.
""")


def main():
    """Main entry point"""
    instructions = None
    research_findings = None

    # Parse arguments
    if '--instructions' in sys.argv:
        idx = sys.argv.index('--instructions')
        if idx + 1 < len(sys.argv):
            instructions = sys.argv[idx + 1]

    if '--research-findings' in sys.argv:
        idx = sys.argv.index('--research-findings')
        if idx + 1 < len(sys.argv):
            findings_path = sys.argv[idx + 1]
            with open(findings_path) as f:
                research_findings = json.load(f)

    try:
        # Ensure we're in repository root
        repo_root = find_repository_root()
        os.chdir(repo_root)

        # Update plan
        version = update_plan(instructions, research_findings)

        # Show summary
        show_update_summary(version)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
