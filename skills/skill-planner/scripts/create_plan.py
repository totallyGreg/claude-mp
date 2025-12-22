#!/usr/bin/env python3
"""
Create improvement plan with git branch workflow

This is the core script for skill-planner's planning phase.
Creates a planning branch and PLAN.md from research findings.

Usage:
    python3 create_plan.py <skill-name> [--research-findings path/to/research.json]

Week 1 Implementation Status:
    [x] Git branch creation
    [x] PLAN.md template population
    [x] Basic workflow
    [ ] Integration with skillsmith research (Week 2)
    [ ] Full research findings integration (Week 2)
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


def create_planning_branch(skill_name, description="improvement"):
    """
    Create planning branch for skill improvement

    Branch name format: plan/{skill-name}-{description}-{YYYYMMDD}

    Returns: branch name
    """
    date_str = datetime.now().strftime("%Y%m%d")
    branch_name = f"plan/{skill_name}-{description}-{date_str}"

    # Check if branch already exists
    result = subprocess.run(
        ['git', 'branch', '--list', branch_name],
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        raise Exception(f"Planning branch already exists: {branch_name}\n" +
                       "Complete or delete existing plan first.")

    # Create and checkout planning branch
    subprocess.run(
        ['git', 'checkout', '-b', branch_name],
        check=True
    )

    print(f"✓ Created planning branch: {branch_name}")

    return branch_name


def load_plan_template():
    """Load PLAN.md template"""
    # Find skill-planner directory
    repo_root = find_repository_root()
    template_path = repo_root / 'skills' / 'skill-planner' / 'references' / 'plan_template.md'

    if not template_path.exists():
        raise Exception(f"Plan template not found: {template_path}")

    with open(template_path) as f:
        return f.read()


def populate_plan_template(template, skill_name, research_findings=None):
    """
    Populate PLAN.md template with research findings

    Week 2: Full integration with skillsmith research
    """
    now = datetime.now().isoformat() + 'Z'

    # Basic replacements
    plan = template.replace('{Skill Name}', skill_name)
    plan = plan.replace('{Short Description}', 'improvement')
    plan = plan.replace('{YYYY-MM-DDTHH:MM:SSZ}', now)
    plan = plan.replace('{skill-name}', skill_name)
    plan = plan.replace('{short-desc}', 'improvement')
    plan = plan.replace('{YYYYMMDD}', datetime.now().strftime("%Y%m%d"))
    plan = plan.replace('v{N}', 'v1')

    # If research findings provided, populate from them
    if research_findings:
        # Week 2: Integrate actual research findings

        # Goal
        intent = research_findings.get('phase1_intent', {})
        domain = research_findings.get('phase2_domain', {})
        impl = research_findings.get('phase5_implementation', {})

        plan = plan.replace('{What we\'re trying to achieve with this improvement}',
                           'Improve skill quality based on Agent Skills specification and domain best practices')

        # Current State - Understanding
        plan = plan.replace('{What the skill does}', intent.get('description', 'N/A'))
        plan = plan.replace('{Domain classification}', domain.get('domain', 'N/A'))
        plan = plan.replace('{Simple | Moderate | Complex | Meta}', domain.get('complexity', 'N/A'))

        # Current State - Metrics (Baseline)
        if impl and 'metrics' in impl:
            metrics = impl['metrics']
            basic = metrics.get('basic_metrics', {})

            plan = plan.replace('{N} lines', f"{basic.get('skill_md_lines', 'N/A')} lines")
            plan = plan.replace('~{N}', f"~{basic.get('skill_md_tokens', 'N/A')}")
            plan = plan.replace('{N} files, {N} lines',
                              f"{basic.get('references_count', 0)} files, {basic.get('references_lines', 0)} lines")
            plan = plan.replace('{N}', '0')  # Default for other {N} placeholders

            # Scores with bars
            concise = metrics.get('conciseness', {}).get('score', 0)
            complex = metrics.get('complexity', {}).get('score', 0)
            spec = metrics.get('spec_compliance', {}).get('score', 0)
            prog = metrics.get('progressive_disclosure', {}).get('score', 0)
            overall = metrics.get('overall_score', 0)

            plan = plan.replace('[{bars}] {score}/100', format_score_bar(concise), 1)
            plan = plan.replace('[{bars}] {score}/100', format_score_bar(complex), 1)
            plan = plan.replace('[{bars}] {score}/100', format_score_bar(spec), 1)
            plan = plan.replace('[{bars}] {score}/100', format_score_bar(prog), 1)
            plan = plan.replace('[{bars}] {score}/100', format_score_bar(overall), 1)

        # Analysis - Strengths, Weaknesses, Opportunities
        if impl:
            strengths = impl.get('strengths', [])
            weaknesses = impl.get('weaknesses', [])
            opportunities = impl.get('opportunities', [])

            # Replace first two of each
            if len(strengths) >= 1:
                plan = plan.replace('{Strength 1}', strengths[0], 1)
            if len(strengths) >= 2:
                plan = plan.replace('{Strength 2}', strengths[1], 1)
            else:
                plan = plan.replace('- {Strength 2}\n', '', 1)

            if len(weaknesses) >= 1:
                plan = plan.replace('{Weakness 1}', weaknesses[0], 1)
            if len(weaknesses) >= 2:
                plan = plan.replace('{Weakness 2}', weaknesses[1], 1)
            else:
                plan = plan.replace('- {Weakness 2}\n', '', 1)

            if len(opportunities) >= 1:
                plan = plan.replace('{Opportunity 1}', opportunities[0], 1)
            if len(opportunities) >= 2:
                plan = plan.replace('{Opportunity 2}', opportunities[1], 1)
            else:
                plan = plan.replace('- {Opportunity 2}\n', '', 1)

        # Spec Compliance
        compliance = research_findings.get('phase6_compliance', {})
        violations = compliance.get('violations', [])
        warnings = compliance.get('warnings', [])

        plan = plan.replace('{count}', str(len(violations)), 1)
        if violations:
            plan = plan.replace('{Violation 1}', violations[0], 1)
        else:
            plan = plan.replace('- {Violation 1}\n', 'None\n', 1)

        plan = plan.replace('{count}', str(len(warnings)), 1)
        if warnings:
            plan = plan.replace('{Warning 1}', warnings[0], 1)
        else:
            plan = plan.replace('- {Warning 1}\n', 'None\n', 1)

    else:
        # No research findings provided
        plan = plan.replace('{What we\'re trying to achieve with this improvement}',
                           'TODO: Run research to define improvement goal')
        plan = plan.replace('{What the skill does}',
                           'TODO: Populate from research findings')
        plan = plan.replace('{Domain classification}',
                           'TODO: Populate from research findings')
        plan = plan.replace('{Simple | Moderate | Complex | Meta}',
                           'TODO: Populate from research findings')

    return plan


def format_score_bar(score, width=10):
    """Format score as visual bar"""
    filled = int((score / 100) * width)
    empty = width - filled
    return f"{'█' * filled}{'░' * empty} {score}"


def create_plan_file(branch_name, skill_name, research_findings=None):
    """Create PLAN.md in current directory"""
    template = load_plan_template()
    plan_content = populate_plan_template(template, skill_name, research_findings)

    # Write PLAN.md to repository root
    with open('PLAN.md', 'w') as f:
        f.write(plan_content)

    print(f"✓ Created PLAN.md")

    # Git add and commit
    subprocess.run(['git', 'add', 'PLAN.md'], check=True)
    subprocess.run(
        ['git', 'commit', '-m', f'Initial plan for {skill_name} improvement'],
        check=True
    )

    print(f"✓ Committed PLAN.md to {branch_name}")


def show_next_steps(branch_name, skill_name):
    """Show user what to do next"""
    print(f"""
╔═══════════════════════════════════════════════════════╗
║  Plan Created Successfully                             ║
╚═══════════════════════════════════════════════════════╝

Branch: {branch_name}
Status: draft
Plan: PLAN.md (in repository root)

Next Steps:
  1. Review PLAN.md
  2. Refine plan if needed:
     "Refine plan - <instructions>"
  3. When ready:
     "Approve plan"

Note: This is Week 1 implementation with placeholder research.
      Week 2 will integrate full skillsmith research findings.
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 create_plan.py <skill-name> [--research-findings path]")
        print("")
        print("Example:")
        print("  python3 create_plan.py skillsmith")
        print("  python3 create_plan.py omnifocus-manager --research-findings research.json")
        sys.exit(1)

    skill_name = sys.argv[1]
    research_findings = None

    # Check for research findings file
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

        # Check we're on main branch
        current_branch = get_current_branch()
        if current_branch != 'main':
            print(f"⚠ Warning: Not on main branch (currently on: {current_branch})")
            response = input("Create planning branch from current branch? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled")
                sys.exit(0)

        # Create planning branch
        branch_name = create_planning_branch(skill_name)

        # Create PLAN.md
        create_plan_file(branch_name, skill_name, research_findings)

        # Show next steps
        show_next_steps(branch_name, skill_name)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
