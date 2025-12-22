#!/usr/bin/env python3
"""
Calculate quality metrics for skills

Calculates objective metrics to assess skill quality:
- Conciseness: Line count, token count vs guidelines
- Complexity: Nesting depth, section count
- Spec Compliance: Frontmatter, required fields
- Progressive Disclosure: Proper use of bundled resources
- Overall: Weighted average

Usage:
    python3 calculate_metrics.py <skill-path> [--format json|text]

Week 2 Implementation Status:
    [x] Basic metrics (lines, tokens, files)
    [x] Conciseness score
    [x] Complexity score
    [x] Spec Compliance score (basic)
    [x] Progressive Disclosure score
    [x] Overall score calculation
"""

import os
import sys
import json
from pathlib import Path
from collections import defaultdict


# ============================================================================
# Guidelines and Thresholds
# ============================================================================

# Agent Skills spec guidelines
GUIDELINE_MAX_LINES = 500
GUIDELINE_MAX_TOKENS = 2000
GUIDELINE_RECOMMENDED_LINES = 300

# Required frontmatter fields
REQUIRED_FRONTMATTER = ['name', 'description']

# Recommended frontmatter fields (Agent Skills spec)
RECOMMENDED_FRONTMATTER = ['metadata', 'compatibility', 'license']


# ============================================================================
# File Reading Utilities
# ============================================================================

def count_lines(file_path):
    """Count lines in a file"""
    with open(file_path) as f:
        return len(f.readlines())


def count_files_recursive(directory, extension=None):
    """Count files recursively in directory"""
    if not directory.exists():
        return 0

    count = 0
    for item in directory.rglob('*'):
        if item.is_file():
            if extension is None or item.suffix == extension:
                count += 1
    return count


def count_total_lines_recursive(directory):
    """Count total lines in all files in directory"""
    if not directory.exists():
        return 0

    total = 0
    for item in directory.rglob('*'):
        if item.is_file() and not item.name.startswith('.'):
            try:
                total += count_lines(item)
            except:
                pass  # Skip binary files
    return total


def estimate_tokens(text):
    """Estimate token count (rough: 1 token ≈ 4 chars)"""
    return len(text) // 4


def read_skill_md(skill_path):
    """Read SKILL.md and separate frontmatter from body"""
    skill_md = skill_path / 'SKILL.md'

    if not skill_md.exists():
        raise Exception(f"SKILL.md not found in {skill_path}")

    with open(skill_md) as f:
        content = f.read()

    # Extract frontmatter
    if not content.startswith('---'):
        raise Exception("SKILL.md missing frontmatter")

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise Exception("SKILL.md has malformed frontmatter")

    frontmatter = parts[1].strip()
    body = parts[2].strip()

    return frontmatter, body, content


def parse_frontmatter(frontmatter):
    """Parse YAML frontmatter into dict"""
    metadata = {}
    current_key = None
    current_value = []

    for line in frontmatter.split('\n'):
        if ':' in line and not line.startswith(' '):
            # New key-value pair
            if current_key:
                metadata[current_key] = '\n'.join(current_value).strip()

            key, value = line.split(':', 1)
            current_key = key.strip()
            current_value = [value.strip()] if value.strip() else []
        elif current_key and line.startswith(' '):
            # Continuation of previous value
            current_value.append(line.strip())

    # Add last key
    if current_key:
        metadata[current_key] = '\n'.join(current_value).strip()

    return metadata


# ============================================================================
# Metric Calculations
# ============================================================================

def calculate_basic_metrics(skill_path):
    """
    Calculate basic metrics about the skill

    Returns: {
        'skill_md_lines': int,
        'skill_md_tokens': int,
        'scripts_count': int,
        'scripts_lines': int,
        'references_count': int,
        'references_lines': int,
        'assets_count': int,
        'total_resource_files': int,
        'total_resource_lines': int
    }
    """
    frontmatter, body, content = read_skill_md(skill_path)

    # SKILL.md metrics
    skill_md_lines = count_lines(skill_path / 'SKILL.md')
    skill_md_tokens = estimate_tokens(content)

    # Bundled resources
    scripts_count = count_files_recursive(skill_path / 'scripts')
    scripts_lines = count_total_lines_recursive(skill_path / 'scripts')

    references_count = count_files_recursive(skill_path / 'references')
    references_lines = count_total_lines_recursive(skill_path / 'references')

    assets_count = count_files_recursive(skill_path / 'assets')

    total_resource_files = scripts_count + references_count + assets_count
    total_resource_lines = scripts_lines + references_lines

    return {
        'skill_md_lines': skill_md_lines,
        'skill_md_tokens': skill_md_tokens,
        'scripts_count': scripts_count,
        'scripts_lines': scripts_lines,
        'references_count': references_count,
        'references_lines': references_lines,
        'assets_count': assets_count,
        'total_resource_files': total_resource_files,
        'total_resource_lines': total_resource_lines
    }


def calculate_conciseness_score(basic_metrics):
    """
    Calculate conciseness score (0-100)

    Score based on:
    - Line count vs guidelines (500 max, 300 recommended)
    - Token count vs guidelines (2000 max)
    """
    lines = basic_metrics['skill_md_lines']
    tokens = basic_metrics['skill_md_tokens']

    # Line score (0-50 points)
    if lines <= GUIDELINE_RECOMMENDED_LINES:
        line_score = 50
    elif lines <= GUIDELINE_MAX_LINES:
        # Linear decrease from 50 to 25
        line_score = 50 - ((lines - GUIDELINE_RECOMMENDED_LINES) / (GUIDELINE_MAX_LINES - GUIDELINE_RECOMMENDED_LINES)) * 25
    else:
        # Over max: decrease from 25 to 0
        line_score = max(0, 25 - ((lines - GUIDELINE_MAX_LINES) / 500) * 25)

    # Token score (0-50 points)
    if tokens <= GUIDELINE_MAX_TOKENS:
        token_score = 50
    else:
        # Over max: decrease from 50 to 0
        token_score = max(0, 50 - ((tokens - GUIDELINE_MAX_TOKENS) / 2000) * 50)

    total_score = int(line_score + token_score)

    return {
        'score': total_score,
        'line_score': int(line_score),
        'token_score': int(token_score),
        'lines_vs_guideline': f"{lines}/{GUIDELINE_MAX_LINES}",
        'tokens_vs_guideline': f"{tokens}/{GUIDELINE_MAX_TOKENS}"
    }


def calculate_complexity_score(skill_path, body):
    """
    Calculate complexity score (0-100)

    Higher score = lower complexity (better)
    Score based on:
    - Nesting depth of headings
    - Number of sections
    - Use of code blocks vs prose
    """
    lines = body.split('\n')

    # Count headings and their levels
    heading_levels = []
    section_count = 0
    code_block_count = 0
    in_code_block = False

    for line in lines:
        if line.startswith('```'):
            in_code_block = not in_code_block
            if in_code_block:
                code_block_count += 1
        elif line.startswith('#') and not in_code_block:
            level = len(line) - len(line.lstrip('#'))
            heading_levels.append(level)
            if level <= 2:
                section_count += 1

    # Calculate max nesting depth
    max_depth = max(heading_levels) if heading_levels else 0

    # Complexity scoring
    # - Fewer sections = simpler (max 20 points)
    if section_count <= 5:
        section_score = 40
    elif section_count <= 10:
        section_score = 30
    else:
        section_score = max(0, 30 - (section_count - 10) * 2)

    # - Lower nesting = simpler (max 30 points)
    if max_depth <= 3:
        depth_score = 30
    elif max_depth <= 5:
        depth_score = 20
    else:
        depth_score = max(0, 20 - (max_depth - 5) * 5)

    # - Moderate code blocks = good (max 30 points)
    if 2 <= code_block_count <= 10:
        code_score = 30
    elif code_block_count < 2:
        code_score = 20
    else:
        code_score = max(0, 30 - (code_block_count - 10))

    total_score = int(section_score + depth_score + code_score)

    return {
        'score': total_score,
        'section_count': section_count,
        'max_nesting_depth': max_depth,
        'code_blocks': code_block_count
    }


def calculate_spec_compliance_score(frontmatter_dict, basic_metrics):
    """
    Calculate spec compliance score (0-100)

    Score based on:
    - Required frontmatter fields present
    - Recommended frontmatter fields present
    - Proper structure (has bundled resources if > 300 lines)
    """
    score = 0
    violations = []
    warnings = []

    # Required fields (50 points)
    required_present = sum(1 for field in REQUIRED_FRONTMATTER if field in frontmatter_dict)
    score += (required_present / len(REQUIRED_FRONTMATTER)) * 50

    for field in REQUIRED_FRONTMATTER:
        if field not in frontmatter_dict:
            violations.append(f"Missing required frontmatter field: {field}")

    # Recommended fields (30 points)
    recommended_present = sum(1 for field in RECOMMENDED_FRONTMATTER if field in frontmatter_dict)
    score += (recommended_present / len(RECOMMENDED_FRONTMATTER)) * 30

    for field in RECOMMENDED_FRONTMATTER:
        if field not in frontmatter_dict:
            warnings.append(f"Missing recommended frontmatter field: {field}")

    # Structure checks (20 points)
    structure_score = 20

    # Check for old 'version' field (should be metadata.version)
    if 'version' in frontmatter_dict and 'metadata' not in frontmatter_dict:
        warnings.append("Using deprecated 'version' field; use 'metadata.version' instead")
        structure_score -= 5

    # If skill is long, should have bundled resources
    if basic_metrics['skill_md_lines'] > 300 and basic_metrics['total_resource_files'] == 0:
        warnings.append("Skill > 300 lines with no bundled resources; consider moving content to references/")
        structure_score -= 10

    score += structure_score

    return {
        'score': int(score),
        'violations': violations,
        'warnings': warnings,
        'required_fields_present': f"{required_present}/{len(REQUIRED_FRONTMATTER)}",
        'recommended_fields_present': f"{recommended_present}/{len(RECOMMENDED_FRONTMATTER)}"
    }


def calculate_progressive_disclosure_score(basic_metrics):
    """
    Calculate progressive disclosure score (0-100)

    Score based on:
    - Proper use of bundled resources
    - Balance between SKILL.md and references
    - Appropriate separation of concerns
    """
    score = 100
    issues = []

    lines = basic_metrics['skill_md_lines']
    has_scripts = basic_metrics['scripts_count'] > 0
    has_references = basic_metrics['references_count'] > 0
    has_assets = basic_metrics['assets_count'] > 0

    # If skill is very long but has no references, likely violating progressive disclosure
    if lines > 500 and not has_references:
        score -= 30
        issues.append("Very long SKILL.md with no references; content should be split")

    # If skill is moderate length with no bundled resources, that's okay
    if 200 < lines <= 500 and not (has_scripts or has_references or has_assets):
        score -= 10
        issues.append("Moderate length with no bundled resources; consider if content could be split")

    # If skill has many references, it should be leveraging them properly
    if has_references and basic_metrics['references_lines'] < 50:
        score -= 15
        issues.append("Has references directory but minimal content; ensure references are substantial")

    # Good use of progressive disclosure
    if has_references and 200 <= lines <= 400:
        # Bonus for good balance
        score = min(100, score + 10)

    return {
        'score': int(score),
        'issues': issues,
        'uses_scripts': has_scripts,
        'uses_references': has_references,
        'uses_assets': has_assets
    }


def calculate_overall_score(conciseness, complexity, spec_compliance, progressive):
    """
    Calculate weighted overall score

    Weights:
    - Conciseness: 25%
    - Complexity: 20%
    - Spec Compliance: 35%
    - Progressive Disclosure: 20%
    """
    overall = (
        conciseness['score'] * 0.25 +
        complexity['score'] * 0.20 +
        spec_compliance['score'] * 0.35 +
        progressive['score'] * 0.20
    )

    return int(overall)


# ============================================================================
# Main Metrics Calculation
# ============================================================================

def calculate_all_metrics(skill_path):
    """
    Calculate all quality metrics for a skill

    Returns: Complete metrics dict
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        raise Exception(f"Skill path does not exist: {skill_path}")

    # Read skill files
    frontmatter, body, content = read_skill_md(skill_path)
    frontmatter_dict = parse_frontmatter(frontmatter)

    # Calculate metrics
    basic = calculate_basic_metrics(skill_path)
    conciseness = calculate_conciseness_score(basic)
    complexity = calculate_complexity_score(skill_path, body)
    spec_compliance = calculate_spec_compliance_score(frontmatter_dict, basic)
    progressive = calculate_progressive_disclosure_score(basic)
    overall = calculate_overall_score(conciseness, complexity, spec_compliance, progressive)

    return {
        'skill_name': frontmatter_dict.get('name', skill_path.name),
        'basic_metrics': basic,
        'conciseness': conciseness,
        'complexity': complexity,
        'spec_compliance': spec_compliance,
        'progressive_disclosure': progressive,
        'overall_score': overall
    }


def format_score_bar(score, width=20):
    """Format score as visual bar (e.g., [████████░░░░░░░░░░░░] 75/100)"""
    filled = int((score / 100) * width)
    empty = width - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {score}/100"


def print_metrics_text(metrics):
    """Print metrics in human-readable text format"""
    print(f"\n{'='*60}")
    print(f"Quality Metrics: {metrics['skill_name']}")
    print(f"{'='*60}\n")

    basic = metrics['basic_metrics']
    print("Basic Metrics:")
    print(f"  SKILL.md: {basic['skill_md_lines']} lines, ~{basic['skill_md_tokens']} tokens")
    print(f"  Scripts: {basic['scripts_count']} files, {basic['scripts_lines']} lines")
    print(f"  References: {basic['references_count']} files, {basic['references_lines']} lines")
    print(f"  Assets: {basic['assets_count']} files")
    print()

    print("Quality Scores:")
    print(f"  Conciseness:     {format_score_bar(metrics['conciseness']['score'])}")
    print(f"  Complexity:      {format_score_bar(metrics['complexity']['score'])}")
    print(f"  Spec Compliance: {format_score_bar(metrics['spec_compliance']['score'])}")
    print(f"  Progressive:     {format_score_bar(metrics['progressive_disclosure']['score'])}")
    print(f"  Overall:         {format_score_bar(metrics['overall_score'])}")
    print()

    # Show violations and warnings
    if metrics['spec_compliance']['violations']:
        print("❌ Violations:")
        for v in metrics['spec_compliance']['violations']:
            print(f"  - {v}")
        print()

    if metrics['spec_compliance']['warnings']:
        print("⚠ Warnings:")
        for w in metrics['spec_compliance']['warnings']:
            print(f"  - {w}")
        print()

    if metrics['progressive_disclosure']['issues']:
        print("ℹ Progressive Disclosure:")
        for i in metrics['progressive_disclosure']['issues']:
            print(f"  - {i}")
        print()

    print(f"{'='*60}\n")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 calculate_metrics.py <skill-path> [--format json|text]")
        print("")
        print("Example:")
        print("  python3 calculate_metrics.py skills/skillsmith")
        print("  python3 calculate_metrics.py skills/omnifocus-manager --format json")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_format = 'text'

    if '--format' in sys.argv:
        idx = sys.argv.index('--format')
        if idx + 1 < len(sys.argv):
            output_format = sys.argv[idx + 1]

    try:
        metrics = calculate_all_metrics(skill_path)

        if output_format == 'json':
            print(json.dumps(metrics, indent=2))
        else:
            print_metrics_text(metrics)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
