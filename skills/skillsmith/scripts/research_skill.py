#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Deep research analysis for skills

Implements 7-phase research workflow to understand skills and identify
improvement opportunities.

Usage:
    uv run scripts/research_skill.py <skill-path> [--output research.json]

Research Phases:
    1. Understand Intent - What the skill does, when to use it
    2. Identify Domain - Classify domain and complexity
    3. Research Best Practices - Domain-specific patterns from Agent Skills spec
    4. Find Similar Skills - Learn from examples in repository
    5. Analyze Implementation - Strengths, weaknesses, opportunities
    6. Check Spec Compliance - Validate against Agent Skills specification
    7. Synthesize Findings - Consolidate into actionable recommendations

Week 2 Implementation Status:
    [x] Phase 1: Understand Intent
    [x] Phase 2: Identify Domain
    [ ] Phase 3: Research Best Practices (requires Agent Skills spec access)
    [ ] Phase 4: Find Similar Skills
    [ ] Phase 5: Analyze Implementation (requires metrics script)
    [ ] Phase 6: Check Spec Compliance
    [ ] Phase 7: Synthesize Findings
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


def find_repository_root():
    """Find git repository root"""
    current = Path.cwd()

    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent

    raise Exception("Not in a git repository")


def validate_skill_path(skill_path):
    """
    Validate that skill path exists and has SKILL.md

    Returns: Path object
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        raise Exception(f"Skill path does not exist: {skill_path}")

    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        raise Exception(f"SKILL.md not found in {skill_path}")

    return skill_path


def read_skill_metadata(skill_path):
    """
    Read skill frontmatter metadata from SKILL.md

    Returns: dict with name, description, version, etc.
    """
    skill_md = skill_path / 'SKILL.md'

    with open(skill_md) as f:
        content = f.read()

    # Extract frontmatter (between --- markers)
    if not content.startswith('---'):
        raise Exception("SKILL.md missing frontmatter")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise Exception("SKILL.md has malformed frontmatter")

    frontmatter = parts[1].strip()
    body = parts[2].strip()

    # Parse YAML frontmatter (simple parser for key: value)
    metadata = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip()

    return metadata, body


def read_improvement_plan(skill_path):
    """Read IMPROVEMENT_PLAN.md if it exists"""
    improvement_plan = skill_path / 'IMPROVEMENT_PLAN.md'

    if improvement_plan.exists():
        with open(improvement_plan) as f:
            return f.read()

    return None


def count_lines(file_path):
    """Count lines in a file"""
    with open(file_path) as f:
        return len(f.readlines())


def estimate_tokens(text):
    """Estimate token count (rough: 1 token ≈ 4 chars)"""
    return len(text) // 4


# ============================================================================
# Phase 1: Understand Intent
# ============================================================================

def phase1_understand_intent(skill_path, metadata, body, improvement_plan):
    """
    Phase 1: Understand what the skill does and when to use it

    Returns: {
        'name': str,
        'description': str,
        'purpose': str,
        'triggers': [str],
        'when_to_use': str,
        'has_improvement_plan': bool
    }
    """
    print("Phase 1: Understanding skill intent...")

    # Extract name and description
    name = metadata.get('name', skill_path.name)
    description = metadata.get('description', '')

    # Analyze description for triggers
    triggers = []
    if 'when' in description.lower():
        triggers.append("Conditional usage pattern detected in description")

    # Summarize purpose from body (first paragraph after frontmatter)
    paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
    purpose = paragraphs[0] if paragraphs else "Purpose not clearly stated"

    # Check for improvement plan
    has_improvement_plan = improvement_plan is not None

    return {
        'name': name,
        'description': description,
        'purpose': purpose[:500],  # First 500 chars
        'triggers': triggers,
        'when_to_use': description,
        'has_improvement_plan': has_improvement_plan,
        'metadata_fields': list(metadata.keys())
    }


# ============================================================================
# Phase 2: Identify Domain & Complexity
# ============================================================================

DOMAIN_KEYWORDS = {
    'productivity': ['todo', 'task', 'workflow', 'automation', 'productivity'],
    'dev-tools': ['git', 'code', 'develop', 'test', 'build', 'deploy'],
    'security': ['security', 'auth', 'encrypt', 'permission', 'access'],
    'data': ['data', 'database', 'query', 'analytics', 'etl'],
    'documentation': ['document', 'docs', 'write', 'markdown', 'readme'],
    'api': ['api', 'endpoint', 'request', 'response', 'http'],
    'meta': ['skill', 'agent', 'plugin', 'marketplace', 'claude'],
    'design': ['design', 'ui', 'frontend', 'template', 'asset'],
    'finance': ['finance', 'money', 'payment', 'invoice', 'accounting'],
    'communication': ['email', 'slack', 'message', 'notification']
}


def identify_domain(name, description, body):
    """Identify skill domain based on keywords"""
    text = f"{name} {description} {body[:1000]}".lower()

    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > 0:
            scores[domain] = score

    if not scores:
        return 'general'

    # Return domain with highest score
    return max(scores, key=scores.get)


def assess_complexity(skill_path, body):
    """
    Assess skill complexity

    Simple: <200 lines, basic workflow
    Moderate: 200-500 lines, multiple workflows
    Complex: >500 lines, advanced features
    Meta: Skills about skills/agents
    """
    skill_md = skill_path / 'SKILL.md'
    line_count = count_lines(skill_md)

    # Check for bundled resources
    has_scripts = (skill_path / 'scripts').exists()
    has_references = (skill_path / 'references').exists()
    has_assets = (skill_path / 'assets').exists()

    resource_count = sum([has_scripts, has_references, has_assets])

    # Meta skills (about skills/agents)
    if any(word in body.lower() for word in ['skill', 'agent', 'claude', 'plugin']):
        return 'Meta'

    # Complexity assessment
    if line_count < 200 and resource_count == 0:
        return 'Simple'
    elif line_count > 500 or resource_count >= 2:
        return 'Complex'
    else:
        return 'Moderate'


def phase2_identify_domain(skill_path, intent):
    """
    Phase 2: Identify domain and assess complexity

    Returns: {
        'domain': str,
        'complexity': str (Simple | Moderate | Complex | Meta),
        'has_scripts': bool,
        'has_references': bool,
        'has_assets': bool,
        'special_considerations': [str]
    }
    """
    print("Phase 2: Identifying domain and complexity...")

    metadata, body = read_skill_metadata(skill_path)

    # Identify domain
    domain = identify_domain(
        intent['name'],
        intent['description'],
        body
    )

    # Assess complexity
    complexity = assess_complexity(skill_path, body)

    # Check for bundled resources
    has_scripts = (skill_path / 'scripts').exists()
    has_references = (skill_path / 'references').exists()
    has_assets = (skill_path / 'assets').exists()

    # Special considerations
    considerations = []
    if has_scripts:
        considerations.append("Contains executable scripts - ensure proper error handling")
    if has_references:
        considerations.append("Contains reference files - check for duplication with SKILL.md")
    if has_assets:
        considerations.append("Contains assets - verify they're output files, not documentation")
    if complexity == 'Meta':
        considerations.append("Meta skill - must align with Agent Skills specification")

    return {
        'domain': domain,
        'complexity': complexity,
        'has_scripts': has_scripts,
        'has_references': has_references,
        'has_assets': has_assets,
        'special_considerations': considerations
    }


# ============================================================================
# Phase 5: Analyze Implementation
# ============================================================================

def phase5_analyze_implementation(skill_path):
    """
    Phase 5: Analyze current implementation with metrics

    Returns: {
        'metrics': dict,  # Full metrics from evaluate_skill.py
        'strengths': [str],
        'weaknesses': [str],
        'opportunities': [str]
    }
    """
    print("Phase 5: Analyzing implementation...")

    # Get directory containing this script
    script_dir = Path(__file__).parent

    # Call evaluate_skill.py
    evaluate_script = script_dir / 'evaluate_skill.py'

    result = subprocess.run(
        [sys.executable, str(evaluate_script), str(skill_path), '--format', 'json'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Evaluation failed: {result.stderr}")

    evaluation = json.loads(result.stdout)
    metrics = evaluation['metrics']

    # Analyze metrics to identify strengths, weaknesses, opportunities
    strengths = []
    weaknesses = []
    opportunities = []

    # Conciseness analysis
    concise_score = metrics['conciseness']['score']
    if concise_score >= 75:
        strengths.append(f"Excellent conciseness ({concise_score}/100)")
    elif concise_score >= 50:
        opportunities.append(f"Moderate conciseness ({concise_score}/100) - could be more concise")
    else:
        weaknesses.append(f"Poor conciseness ({concise_score}/100) - exceeds guidelines significantly")
        opportunities.append("Move detailed content to references/ files")

    # Complexity analysis
    complex_score = metrics['complexity']['score']
    if complex_score >= 75:
        strengths.append(f"Good structure and organization ({complex_score}/100)")
    elif complex_score >= 50:
        opportunities.append(f"Structure could be improved ({complex_score}/100)")
    else:
        weaknesses.append(f"Overly complex structure ({complex_score}/100)")
        opportunities.append("Simplify heading structure and reduce nesting")

    # Spec compliance analysis
    spec_score = metrics['spec_compliance']['score']
    if spec_score >= 90:
        strengths.append(f"Excellent spec compliance ({spec_score}/100)")
    elif spec_score >= 70:
        opportunities.append(f"Good spec compliance ({spec_score}/100) - minor improvements possible")
        # Add specific opportunities from violations/warnings
        if metrics['spec_compliance']['warnings']:
            for warning in metrics['spec_compliance']['warnings']:
                opportunities.append(f"Spec: {warning}")
    else:
        weaknesses.append(f"Poor spec compliance ({spec_score}/100)")
        # Add specific weaknesses from violations
        if metrics['spec_compliance']['violations']:
            for violation in metrics['spec_compliance']['violations']:
                weaknesses.append(f"Spec violation: {violation}")

    # Progressive disclosure analysis
    prog_score = metrics['progressive_disclosure']['score']
    if prog_score >= 90:
        strengths.append(f"Excellent use of progressive disclosure ({prog_score}/100)")
    elif prog_score >= 70:
        opportunities.append(f"Good progressive disclosure ({prog_score}/100)")
        if metrics['progressive_disclosure']['issues']:
            for issue in metrics['progressive_disclosure']['issues']:
                opportunities.append(f"Progressive: {issue}")
    else:
        weaknesses.append(f"Poor progressive disclosure ({prog_score}/100)")
        if metrics['progressive_disclosure']['issues']:
            for issue in metrics['progressive_disclosure']['issues']:
                weaknesses.append(f"Progressive: {issue}")

    # Overall assessment
    overall = metrics['overall_score']
    if overall >= 80:
        strengths.append(f"High overall quality ({overall}/100)")
    elif overall < 60:
        weaknesses.append(f"Overall quality needs improvement ({overall}/100)")

    return {
        'metrics': metrics,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'opportunities': opportunities
    }


# ============================================================================
# Research Orchestration
# ============================================================================

def conduct_research(skill_path):
    """
    Conduct full 7-phase research on a skill

    Returns: Complete research findings as dict
    """
    print(f"\n{'='*60}")
    print(f"Research Analysis: {skill_path.name}")
    print(f"{'='*60}\n")

    # Validate skill
    skill_path = validate_skill_path(skill_path)

    # Read skill files
    metadata, body = read_skill_metadata(skill_path)
    improvement_plan = read_improvement_plan(skill_path)

    # Phase 1: Understand Intent
    intent = phase1_understand_intent(skill_path, metadata, body, improvement_plan)
    print(f"  ✓ Intent: {intent['name']}")
    print(f"    Purpose: {intent['purpose'][:100]}...")

    # Phase 2: Identify Domain & Complexity
    domain_info = phase2_identify_domain(skill_path, intent)
    print(f"  ✓ Domain: {domain_info['domain']}")
    print(f"    Complexity: {domain_info['complexity']}")

    # Phase 3: Research Best Practices (Week 2: Stub)
    print("  ⚠ Phase 3: Research Best Practices (Week 2: Not yet implemented)")
    best_practices = {
        'critical': [],
        'important': [],
        'note': 'Week 2: Will load from Agent Skills spec'
    }

    # Phase 4: Find Similar Skills (Week 2: Stub)
    print("  ⚠ Phase 4: Find Similar Skills (Week 2: Not yet implemented)")
    similar_skills = {
        'examples': [],
        'patterns': [],
        'note': 'Week 2: Will search repository'
    }

    # Phase 5: Analyze Implementation
    implementation = phase5_analyze_implementation(skill_path)
    print(f"  ✓ Implementation analyzed")
    print(f"    Strengths: {len(implementation['strengths'])}, Weaknesses: {len(implementation['weaknesses'])}, Opportunities: {len(implementation['opportunities'])}")
    print(f"    Overall Score: {implementation['metrics']['overall_score']}/100")

    # Phase 6: Check Spec Compliance (extracted from metrics)
    compliance = {
        'score': implementation['metrics']['spec_compliance']['score'],
        'violations': implementation['metrics']['spec_compliance']['violations'],
        'warnings': implementation['metrics']['spec_compliance']['warnings']
    }
    print(f"  ✓ Spec compliance checked")
    print(f"    Score: {compliance['score']}/100")
    print(f"    Violations: {len(compliance['violations'])}, Warnings: {len(compliance['warnings'])}")

    # Phase 7: Synthesize Findings (Week 2: Stub)
    print("  ⚠ Phase 7: Synthesize Findings (Week 2: Not yet implemented)")
    recommendations = {
        'high_priority': [],
        'medium_priority': [],
        'low_priority': [],
        'consolidation_opportunities': [],
        'note': 'Week 2: Will synthesize all findings'
    }

    # Compile complete research report
    research = {
        'timestamp': datetime.now().isoformat() + 'Z',
        'skill_path': str(skill_path),
        'phase1_intent': intent,
        'phase2_domain': domain_info,
        'phase3_best_practices': best_practices,
        'phase4_similar_skills': similar_skills,
        'phase5_implementation': implementation,
        'phase6_compliance': compliance,
        'phase7_recommendations': recommendations,
        'completion_status': 'partial',
        'note': 'Week 2 partial implementation: Phases 1-2 complete, 3-7 pending'
    }

    print(f"\n{'='*60}")
    print("Research Summary")
    print(f"{'='*60}")
    print(f"Skill: {intent['name']}")
    print(f"Domain: {domain_info['domain']}")
    print(f"Complexity: {domain_info['complexity']}")
    print(f"Status: Phases 1-2 complete (Week 2 partial implementation)")
    print(f"{'='*60}\n")

    return research


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 research_skill.py <skill-path> [--output research.json]")
        print("")
        print("Example:")
        print("  python3 research_skill.py skills/skillsmith")
        print("  python3 research_skill.py skills/omnifocus-manager --output research.json")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_file = None

    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    try:
        # Conduct research
        research = conduct_research(Path(skill_path))

        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(research, f, indent=2)
            print(f"Research findings saved to {output_file}")
        else:
            print("\nResearch Findings (JSON):")
            print(json.dumps(research, indent=2))

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
