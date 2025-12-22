#!/usr/bin/env python3
"""
Complete and archive improvement plan

This script is called after a plan branch has been merged to main.
Archives the completed plan and optionally cleans up the branch.

Usage:
    python3 complete_plan.py <branch-name> [--delete-branch]

Week 1 Implementation Status:
    [x] Plan archival to completed/ directory
    [x] Status update to completed
    [x] Optional branch deletion
    [x] Completion summary
"""

import os
import sys
import subprocess
import shutil
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


def branch_exists(branch_name):
    """Check if branch exists"""
    result = subprocess.run(
        ['git', 'branch', '--list', branch_name],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())


def is_branch_merged(branch_name, into_branch='main'):
    """Check if branch has been merged into target branch"""
    result = subprocess.run(
        ['git', 'branch', '--merged', into_branch],
        capture_output=True,
        text=True
    )
    branches = result.stdout.strip().split('\n')
    # Remove leading spaces and asterisks
    branches = [b.strip().lstrip('* ') for b in branches]
    return branch_name in branches


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

    # Further split name and description
    parts2 = name_and_desc.rsplit('-', 1)
    if len(parts2) == 2:
        skill_name, description = parts2
    else:
        skill_name = parts2[0]
        description = 'improvement'

    return skill_name, description, date


def get_merge_commit_sha(branch_name):
    """Get the merge commit SHA for the branch"""
    result = subprocess.run(
        ['git', 'log', '--merges', '--grep', f'Merge.*{branch_name}', '-n', '1', '--format=%H'],
        capture_output=True,
        text=True
    )
    sha = result.stdout.strip()
    if not sha:
        # Try alternative: find most recent commit from branch
        result = subprocess.run(
            ['git', 'log', '-n', '1', '--format=%H', branch_name],
            capture_output=True,
            text=True
        )
        sha = result.stdout.strip()
    return sha if sha else 'unknown'


def read_plan_from_branch(branch_name):
    """Read PLAN.md from the planning branch"""
    result = subprocess.run(
        ['git', 'show', f'{branch_name}:PLAN.md'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Cannot read PLAN.md from branch {branch_name}")

    return result.stdout


def update_plan_status_to_completed(plan_content, merge_sha):
    """
    Update plan status to completed

    Returns: updated plan content
    """
    now = datetime.now().isoformat() + 'Z'
    lines = plan_content.split('\n')
    updated = []

    for line in lines:
        if line.startswith('**Status:**'):
            updated.append('**Status:** completed')
        elif line.startswith('**Completed:**'):
            updated.append(f'**Completed:** {now}')
        else:
            updated.append(line)

    # Add merge commit info at the end of header section
    # Find the end of the header (first ---)
    for i, line in enumerate(updated):
        if line.strip() == '---':
            updated.insert(i, f'**Merged in commit:** {merge_sha[:8]}')
            break

    return '\n'.join(updated)


def archive_plan(branch_name, delete_branch=False):
    """
    Archive completed plan

    1. Read PLAN.md from branch
    2. Update status to completed
    3. Create completed/{skill-name}/ directory
    4. Save as {description}-{date}.md
    5. Optionally delete branch
    """
    # Extract skill info
    skill_name, description, date = extract_skill_info_from_branch(branch_name)

    # Verify branch exists
    if not branch_exists(branch_name):
        raise Exception(f"Branch does not exist: {branch_name}")

    # Verify branch is merged
    if not is_branch_merged(branch_name):
        print(f"⚠ Warning: Branch {branch_name} does not appear to be merged to main")
        response = input("Archive anyway? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            sys.exit(0)

    # Get merge commit SHA
    merge_sha = get_merge_commit_sha(branch_name)

    # Read plan from branch
    plan_content = read_plan_from_branch(branch_name)

    # Update status to completed
    completed_plan = update_plan_status_to_completed(plan_content, merge_sha)

    # Create archive directory
    archive_dir = Path('completed') / skill_name
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Write archived plan
    archive_path = archive_dir / f'{description}-{date}.md'
    with open(archive_path, 'w') as f:
        f.write(completed_plan)

    print(f"✓ Archived plan to {archive_path}")

    # Optionally delete branch
    if delete_branch:
        # Only delete if we're not currently on that branch
        current_branch = get_current_branch()
        if current_branch == branch_name:
            raise Exception(f"Cannot delete branch {branch_name}: currently checked out")

        subprocess.run(['git', 'branch', '-d', branch_name], check=True)
        print(f"✓ Deleted branch {branch_name}")
        branch_status = "deleted"
    else:
        print(f"✓ Kept branch {branch_name} for history")
        branch_status = "kept"

    return archive_path, branch_status, skill_name, merge_sha


def show_completion_summary(archive_path, branch_name, branch_status, skill_name, merge_sha):
    """Show completion summary"""
    print(f"""
╔═══════════════════════════════════════════════════════╗
║  Plan Completed!                                       ║
╚═══════════════════════════════════════════════════════╝

Skill: {skill_name}
Branch: {branch_name} ({branch_status})
Archived: {archive_path}
Merge commit: {merge_sha[:8]}

The improvement has been successfully completed and merged to main.
The plan has been archived for reference.
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 complete_plan.py <branch-name> [--delete-branch]")
        print("")
        print("Example:")
        print("  python3 complete_plan.py plan/skillsmith-improvement-20251221")
        print("  python3 complete_plan.py plan/skillsmith-improvement-20251221 --delete-branch")
        sys.exit(1)

    branch_name = sys.argv[1]
    delete_branch = '--delete-branch' in sys.argv

    try:
        # Ensure we're in repository root
        repo_root = find_repository_root()
        os.chdir(repo_root)

        # Archive plan
        archive_path, branch_status, skill_name, merge_sha = archive_plan(
            branch_name,
            delete_branch
        )

        # Show summary
        show_completion_summary(
            archive_path,
            branch_name,
            branch_status,
            skill_name,
            merge_sha
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
