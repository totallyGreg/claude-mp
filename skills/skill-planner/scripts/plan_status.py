#!/usr/bin/env python3
"""
Check current plan status

This is a helper script to check the status of the current plan.
Useful for debugging and for skill-planner to verify state.

Usage:
    python3 plan_status.py

Week 1 Implementation Status:
    [x] Read PLAN.md
    [x] Display status, version, branch
    [x] Check for approval tag
    [x] Show next available actions
"""

import os
import sys
import subprocess
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
        return None

    with open('PLAN.md') as f:
        return f.read()


def extract_plan_metadata(plan_content):
    """
    Extract metadata from PLAN.md

    Returns: dict with status, version, timestamps
    """
    metadata = {
        'status': None,
        'version': None,
        'created': None,
        'approved': None,
        'implemented': None,
        'completed': None,
        'branch': None
    }

    for line in plan_content.split('\n'):
        if line.startswith('**Status:**'):
            metadata['status'] = line.split('**Status:**')[1].strip().split('|')[0].strip()
        elif line.startswith('**Version:**'):
            metadata['version'] = line.split('**Version:**')[1].strip()
        elif line.startswith('**Created:**'):
            metadata['created'] = line.split('**Created:**')[1].strip().split('(')[0].strip()
        elif line.startswith('**Approved:**'):
            metadata['approved'] = line.split('**Approved:**')[1].strip().split('(')[0].strip()
        elif line.startswith('**Implemented:**'):
            metadata['implemented'] = line.split('**Implemented:**')[1].strip().split('(')[0].strip()
        elif line.startswith('**Completed:**'):
            metadata['completed'] = line.split('**Completed:**')[1].strip().split('(')[0].strip()
        elif line.startswith('**Branch:**'):
            metadata['branch'] = line.split('**Branch:**')[1].strip()

    return metadata


def check_approval_tag(branch_name):
    """Check if approval tag exists for this branch"""
    if not branch_name.startswith('plan/'):
        return None

    # Extract tag name from branch name
    tag_prefix = 'approved/' + branch_name[5:]  # Remove 'plan/' and add 'approved/'

    result = subprocess.run(
        ['git', 'tag', '-l', tag_prefix],
        capture_output=True,
        text=True
    )

    return result.stdout.strip() if result.stdout.strip() else None


def get_next_actions(status, has_approval_tag):
    """Determine next available actions based on current state"""
    actions = []

    if status == 'draft' or status is None:
        actions.append("'Refine plan - <instructions>' to update the plan")
        actions.append("'Approve plan' when ready to approve")

    elif status == 'approved':
        if has_approval_tag:
            actions.append("'Implement approved plan' to begin implementation")
        else:
            actions.append("⚠ Warning: Status is approved but no git tag found")
            actions.append("Run approve_plan.py to create approval tag")

    elif status == 'implemented':
        actions.append("Test the implementation")
        actions.append("Merge to main when testing is complete")

    elif status == 'completed':
        actions.append("Plan is completed and archived")

    return actions


def show_status(metadata, current_branch, approval_tag, actions):
    """Display plan status"""
    print("╔═══════════════════════════════════════════════════════╗")
    print("║  Current Plan Status                                   ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print()
    print(f"Branch: {current_branch}")
    print(f"Status: {metadata['status'] or 'unknown'}")
    print(f"Version: {metadata['version'] or 'v1'}")
    print()

    if metadata['created'] and metadata['created'] != '{YYYY-MM-DDTHH:MM:SSZ}':
        print(f"Created: {metadata['created']}")
    if metadata['approved'] and metadata['approved'] != '{YYYY-MM-DDTHH:MM:SSZ}':
        print(f"Approved: {metadata['approved']}")
    if metadata['implemented'] and metadata['implemented'] != '{YYYY-MM-DDTHH:MM:SSZ}':
        print(f"Implemented: {metadata['implemented']}")
    if metadata['completed'] and metadata['completed'] != '{YYYY-MM-DDTHH:MM:SSZ}':
        print(f"Completed: {metadata['completed']}")

    if approval_tag:
        print()
        print(f"Approval Tag: {approval_tag} ✓")

    print()
    print("Next Actions:")
    for action in actions:
        if action.startswith("⚠"):
            print(f"  {action}")
        else:
            print(f"  - {action}")


def main():
    """Main entry point"""
    try:
        # Ensure we're in repository root
        repo_root = find_repository_root()
        os.chdir(repo_root)

        # Get current branch
        current_branch = get_current_branch()

        # Check if on planning branch
        if not is_planning_branch(current_branch):
            print(f"Not on a planning branch. Current branch: {current_branch}")
            print()
            print("To start planning:")
            print("  1. 'I want to improve <skill-name>' to begin research")
            print("  2. 'Create plan' to create planning branch")
            sys.exit(0)

        # Read plan file
        plan_content = read_plan_file()
        if not plan_content:
            print(f"On planning branch {current_branch} but PLAN.md not found")
            print()
            print("Run create_plan.py to create PLAN.md")
            sys.exit(1)

        # Extract metadata
        metadata = extract_plan_metadata(plan_content)

        # Check for approval tag
        approval_tag = check_approval_tag(current_branch)

        # Determine next actions
        actions = get_next_actions(metadata['status'], approval_tag)

        # Show status
        show_status(metadata, current_branch, approval_tag, actions)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
