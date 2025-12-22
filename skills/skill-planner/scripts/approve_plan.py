#!/usr/bin/env python3
"""
Approve improvement plan

This script marks a plan as approved and creates a git tag.
Approval is required before implementation can begin.

Usage:
    python3 approve_plan.py

Week 1 Implementation Status:
    [x] Status update (draft → approved)
    [x] Timestamp recording
    [x] Git tag creation
    [x] Commit approval
"""

import os
import sys
import subprocess
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


def extract_skill_info_from_branch(branch_name):
    """
    Extract skill name and description from branch name

    Branch format: plan/{skill-name}-{description}-{YYYYMMDD}
    Returns: (skill_name, description, date)
    """
    if not branch_name.startswith('plan/'):
        raise Exception(f"Invalid planning branch name: {branch_name}")

    parts = branch_name[5:].rsplit('-', 1)  # Remove 'plan/' prefix and split from right
    if len(parts) != 2:
        raise Exception(f"Cannot parse branch name: {branch_name}")

    name_and_desc = parts[0]
    date = parts[1]

    # Further split name and description (skill-name-description)
    # This is tricky as both can have hyphens. We'll use the last hyphen as separator
    parts2 = name_and_desc.rsplit('-', 1)
    if len(parts2) == 2:
        skill_name, description = parts2
    else:
        skill_name = parts2[0]
        description = 'improvement'

    return skill_name, description, date


def update_plan_status_to_approved(plan_content):
    """
    Update plan status from draft to approved

    Returns: updated plan content
    """
    now = datetime.now().isoformat() + 'Z'
    lines = plan_content.split('\n')
    updated = []

    for line in lines:
        if line.startswith('**Status:**'):
            # Update status to approved
            updated.append('**Status:** approved')
        elif line.startswith('**Approved:**'):
            # Update approved timestamp
            updated.append(f'**Approved:** {now}')
        else:
            updated.append(line)

    return '\n'.join(updated)


def approve_plan(branch_name):
    """
    Approve the current plan

    1. Verify status is draft
    2. Update PLAN.md status to approved
    3. Add approved timestamp
    4. Commit changes
    5. Create git tag
    """
    # Read current plan
    plan_content = read_plan_file()

    # Check status
    status = get_plan_status(plan_content)
    if status == 'approved':
        raise Exception("Plan is already approved")
    elif status not in ['draft', None]:
        raise Exception(f"Cannot approve plan with status '{status}'")

    # Update status to approved
    updated_content = update_plan_status_to_approved(plan_content)

    # Write updated plan
    with open('PLAN.md', 'w') as f:
        f.write(updated_content)

    print("✓ Updated PLAN.md status to approved")

    # Git add and commit
    subprocess.run(['git', 'add', 'PLAN.md'], check=True)

    skill_name, description, date = extract_skill_info_from_branch(branch_name)
    subprocess.run(
        ['git', 'commit', '-m', f'Approved plan for {skill_name}'],
        check=True
    )

    print(f"✓ Committed approval to {branch_name}")

    # Create git tag
    tag_name = f"approved/{skill_name}-{description}-{date}"

    # Check if tag already exists
    result = subprocess.run(
        ['git', 'tag', '-l', tag_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        raise Exception(f"Tag already exists: {tag_name}")

    subprocess.run(
        ['git', 'tag', tag_name],
        check=True
    )

    print(f"✓ Created approval tag: {tag_name}")

    return tag_name, skill_name


def show_approval_summary(branch_name, tag_name, skill_name):
    """Show approval summary"""
    print(f"""
╔═══════════════════════════════════════════════════════╗
║  Plan Approved!                                        ║
╚═══════════════════════════════════════════════════════╝

Skill: {skill_name}
Branch: {branch_name}
Tag: {tag_name}
Status: approved

Next Steps:
  1. Review the approved plan one final time
  2. When ready to implement:
     "Implement approved plan"

Note: Implementation requires explicit approval.
      Use "Implement approved plan" command to proceed.
""")


def main():
    """Main entry point"""
    try:
        # Ensure we're in repository root
        repo_root = find_repository_root()
        os.chdir(repo_root)

        # Verify we're on a planning branch
        current_branch = get_current_branch()
        if not is_planning_branch(current_branch):
            raise Exception(f"Not on a planning branch. Current branch: {current_branch}")

        # Approve plan
        tag_name, skill_name = approve_plan(current_branch)

        # Show summary
        show_approval_summary(current_branch, tag_name, skill_name)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
