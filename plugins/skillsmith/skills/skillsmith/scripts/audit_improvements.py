#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Audit IMPROVEMENT_PLAN.md to detect completed work

⚠️  DEPRECATED: This script only works with the OLD IMPROVEMENT_PLAN.md format
that used "#### N. Title" numbered sections. The new table-based format is now
validated by evaluate_skill.py:

    uv run scripts/evaluate_skill.py <path> --quick --check-improvement-plan

This script will be removed in a future version. For tracking improvements,
use GitHub Issues as the source of truth (see WORKFLOW.md).

---

Analyzes a skill's IMPROVEMENT_PLAN.md and detects which planned improvements
have actually been implemented but not yet marked as complete.

Usage:
    uv run scripts/audit_improvements.py <skill-path>
    uv run scripts/audit_improvements.py skills/skillsmith
    uv run scripts/audit_improvements.py skills/omnifocus-manager --verbose

Output:
    ✅ COMPLETED - Evidence found that work is done
    🟡 PARTIAL - Some evidence found, needs review
    ❌ NOT STARTED - No evidence of implementation

Evidence sources:
    - Files in scripts/, references/, assets/ directories
    - Git commit history (commits mentioning the improvement)
    - File content analysis

Options:
    --verbose    Show detailed evidence for each improvement
"""

import sys
import re
import subprocess
from pathlib import Path
from collections import defaultdict

def read_improvement_plan(skill_path):
    """
    Read and parse IMPROVEMENT_PLAN.md

    Returns: dict with 'planned' and 'completed' sections
    """
    skill_path = Path(skill_path)
    improvement_plan = skill_path / 'IMPROVEMENT_PLAN.md'

    if not improvement_plan.exists():
        return None

    content = improvement_plan.read_text()

    # Find planned improvements section (look for 🔮 or "Planned")
    planned_section = ""
    completed_section = ""

    # Try to find sections
    planned_match = re.search(r'##\s*🔮\s*Planned Improvements.*?(?=##\s*(?:✅|Enhancement|Technical|$))', content, re.DOTALL | re.IGNORECASE)
    if planned_match:
        planned_section = planned_match.group(0)

    completed_match = re.search(r'##\s*✅\s*.*?Completed.*?(?=##\s*(?:Enhancement|Contributing|Notes|$))', content, re.DOTALL | re.IGNORECASE)
    if completed_match:
        completed_section = completed_match.group(0)

    return {
        'planned': planned_section,
        'completed': completed_section,
        'full_content': content
    }

def extract_planned_improvements(planned_section):
    """
    Extract individual planned improvement items

    Returns: list of dicts with {number, title, content}
    """
    if not planned_section:
        return []

    improvements = []

    # Find numbered improvements (#### N. Title)
    pattern = r'####\s*(\d+)\.\s*(.+?)(?=####\s*\d+\.|###|##|$)'
    matches = re.finditer(pattern, planned_section, re.DOTALL)

    for match in matches:
        number = match.group(1)
        full_content = match.group(0)

        # Extract title (first line after ####)
        title_match = re.match(r'####\s*\d+\.\s*(.+?)(?:\n|$)', full_content)
        title = title_match.group(1).strip() if title_match else f"Item {number}"

        improvements.append({
            'number': number,
            'title': title,
            'content': full_content
        })

    return improvements

def check_for_scripts(improvement, skill_path):
    """
    Check if improvement mentions scripts that exist in scripts/ directory
    """
    scripts_dir = skill_path / 'scripts'
    if not scripts_dir.exists():
        return []

    # Extract script names mentioned in improvement content
    # Look for .py files mentioned
    script_patterns = re.findall(r'`?([a-z_]+\.py)`?', improvement['content'], re.IGNORECASE)

    found_scripts = []
    for script_name in script_patterns:
        script_path = scripts_dir / script_name
        if script_path.exists():
            # Get line count
            try:
                lines = len(script_path.read_text().splitlines())
                found_scripts.append((script_name, lines))
            except:
                found_scripts.append((script_name, 0))

    return found_scripts

def check_git_history(improvement, skill_path):
    """
    Check git history for commits related to this improvement
    """
    # Extract keywords from title
    title = improvement['title'].lower()
    keywords = [w for w in re.findall(r'\w+', title) if len(w) > 3]

    if not keywords:
        return []

    try:
        # Search git log for any of the keywords
        commits = []
        for keyword in keywords[:3]:  # Check top 3 keywords
            result = subprocess.run(
                ['git', 'log', '--oneline', '--all', f'--grep={keyword}'],
                cwd=skill_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                commits.extend(lines)

        # Deduplicate by commit hash
        unique_commits = list(dict.fromkeys(commits))
        return unique_commits[:5]  # Return top 5 matches

    except:
        return []

def check_for_references(improvement, skill_path):
    """
    Check if improvement mentions reference files that exist
    """
    references_dir = skill_path / 'references'
    if not references_dir.exists():
        return []

    # Extract .md files mentioned
    ref_patterns = re.findall(r'`?([a-z_]+\.md)`?', improvement['content'], re.IGNORECASE)

    found_refs = []
    for ref_name in ref_patterns:
        ref_path = references_dir / ref_name
        if ref_path.exists():
            try:
                lines = len(ref_path.read_text().splitlines())
                found_refs.append((ref_name, lines))
            except:
                found_refs.append((ref_name, 0))

    return found_refs

def analyze_improvement(improvement, skill_path):
    """
    Analyze a single improvement and determine completion status

    Returns: dict with status and evidence
    """
    scripts = check_for_scripts(improvement, skill_path)
    commits = check_git_history(improvement, skill_path)
    refs = check_for_references(improvement, skill_path)

    # Check for "Already Implemented" markers in content
    already_impl = '✅' in improvement['content'] or 'Already Implemented' in improvement['content']

    # Determine status
    evidence_count = len(scripts) + len(refs) + (1 if commits else 0)

    if already_impl:
        status = 'PARTIAL'  # Has checkmarks but still in planned section
    elif evidence_count >= 2:
        status = 'COMPLETED'
    elif evidence_count == 1:
        status = 'PARTIAL'
    else:
        status = 'NOT_STARTED'

    return {
        'status': status,
        'scripts': scripts,
        'commits': commits,
        'references': refs,
        'already_impl_markers': already_impl
    }

def print_audit_report(improvements, skill_path, verbose=False):
    """
    Print audit report to console
    """
    skill_name = skill_path.name

    print(f"\n📋 IMPROVEMENT_PLAN.md Audit Report: {skill_name}")
    print("=" * 80)

    if not improvements:
        print("\n✅ No planned improvements found in IMPROVEMENT_PLAN.md")
        print("   (This may mean the file uses the new minimal format)")
        return

    # Analyze each improvement
    results = []
    for improvement in improvements:
        analysis = analyze_improvement(improvement, skill_path)
        results.append({
            'improvement': improvement,
            'analysis': analysis
        })

    # Print summary
    completed = sum(1 for r in results if r['analysis']['status'] == 'COMPLETED')
    partial = sum(1 for r in results if r['analysis']['status'] == 'PARTIAL')
    not_started = sum(1 for r in results if r['analysis']['status'] == 'NOT_STARTED')

    print(f"\nSummary: {len(improvements)} planned improvements")
    print(f"  ✅ Completed: {completed}")
    print(f"  🟡 Partial: {partial}")
    print(f"  ❌ Not Started: {not_started}")
    print()

    # Print detailed results
    for result in results:
        imp = result['improvement']
        analysis = result['analysis']

        # Status icon
        if analysis['status'] == 'COMPLETED':
            icon = '✅'
        elif analysis['status'] == 'PARTIAL':
            icon = '🟡'
        else:
            icon = '❌'

        print(f"{icon} #{imp['number']}: {imp['title']}")

        if verbose or analysis['status'] != 'NOT_STARTED':
            # Show evidence
            if analysis['scripts']:
                print("   Evidence (scripts/):")
                for script, lines in analysis['scripts']:
                    print(f"     - {script} ({lines} lines)")

            if analysis['references']:
                print("   Evidence (references/):")
                for ref, lines in analysis['references']:
                    print(f"     - {ref} ({lines} lines)")

            if analysis['commits']:
                print(f"   Evidence (git history): {len(analysis['commits'])} related commits")
                if verbose:
                    for commit in analysis['commits'][:3]:
                        print(f"     - {commit}")

            if analysis['already_impl_markers']:
                print("   Note: Contains '✅' or 'Already Implemented' markers")

            # Suggestion
            if analysis['status'] == 'COMPLETED':
                print("   💡 Suggestion: Close issue, update IMPROVEMENT_PLAN.md to completed")
            elif analysis['status'] == 'PARTIAL':
                print("   💡 Suggestion: Review implementation status, may be partially complete")

        print()

    # Recommendations
    print("=" * 80)
    print("\n📝 Recommendations:")
    print()

    if completed > 0:
        print(f"✅ {completed} improvements appear completed:")
        print("   - Create GitHub Issues for any active remaining work")
        print("   - Migrate IMPROVEMENT_PLAN.md to new minimal format")
        print("   - Move completed items to version history")

    if partial > 0:
        print(f"\n🟡 {partial} improvements are partially complete:")
        print("   - Review each to determine actual status")
        print("   - Create GitHub Issues for remaining work")
        print("   - Update IMPROVEMENT_PLAN.md to reflect current state")

    if not_started > 0:
        print(f"\n❌ {not_started} improvements not started:")
        print("   - Create GitHub Issues if still needed")
        print("   - Remove from IMPROVEMENT_PLAN.md if obsolete")
        print("   - Defer to backlog if not high priority")

    print()

def main():
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv or '-h' in sys.argv else 1)

    skill_path = Path(sys.argv[1])
    verbose = '--verbose' in sys.argv or '-v' in sys.argv

    if not skill_path.exists():
        print(f"❌ Error: Skill path does not exist: {skill_path}")
        sys.exit(1)

    # Read IMPROVEMENT_PLAN.md
    plan_data = read_improvement_plan(skill_path)

    if not plan_data:
        print(f"❌ Error: IMPROVEMENT_PLAN.md not found in {skill_path}")
        sys.exit(1)

    # Extract planned improvements
    improvements = extract_planned_improvements(plan_data['planned'])

    # Print audit report
    print_audit_report(improvements, skill_path, verbose)

if __name__ == '__main__':
    main()
