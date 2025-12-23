#!/usr/bin/env python3
"""
Comprehensive skill evaluation and validation

Provides comprehensive skill assessment including:
- Baseline calculation of skill metrics
- Comparison of original vs improved skills to verify improvements
- Verification of Agent Spec and best practices compliance
- Optional base functionality validation with resource metrics
- Store metrics under metadata (conciseness, complexity, spec_compliance, progressive)

Usage:
    # Quick validation (fast, structure-only)
    python3 evaluate_skill.py <skill-path> --quick
    python3 evaluate_skill.py <skill-path> --quick --check-improvement-plan

    # Baseline evaluation
    python3 evaluate_skill.py <skill-path>

    # Compare original vs improved
    python3 evaluate_skill.py <skill-path> --compare <original-path>

    # With functionality validation
    python3 evaluate_skill.py <skill-path> --validate-functionality

    # Store metrics in skill metadata
    python3 evaluate_skill.py <skill-path> --store-metrics

    # Full evaluation with all options
    python3 evaluate_skill.py <skill-path> --compare <original-path> --validate-functionality --store-metrics --format json

Options:
    --quick                   Fast validation mode (structure only)
    --check-improvement-plan  Validate IMPROVEMENT_PLAN.md (requires --quick)
    --compare <path>          Compare against original skill version
    --validate-functionality  Run functionality validation tests
    --store-metrics          Store metrics in SKILL.md metadata
    --format json|text       Output format (default: text)
    --output <file>          Save results to file
"""

import os
import sys
import json
import re
import subprocess
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Import basic validation from quick_validate.py
from quick_validate import validate_skill


# ============================================================================
# IMPROVEMENT_PLAN Validation (custom enhancement)
# ============================================================================


def validate_improvement_plan(skill_path, skill_version=None):
    """
    Validate IMPROVEMENT_PLAN.md completeness and consistency (from quick_validate.py)

    Returns: (valid: bool, message: str)
    """
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


def quick_validate(skill_path, check_improvement_plan=False):
    """
    Perform quick validation of skill structure

    Uses validate_skill() from quick_validate.py for basic validation,
    optionally adds IMPROVEMENT_PLAN validation (custom enhancement).

    Returns: {
        'valid': bool,
        'structure': dict,
        'improvement_plan': dict | None
    }
    """
    skill_path = Path(skill_path)

    # Basic structure validation (imported from quick_validate.py)
    struct_valid, struct_message, skill_version = validate_skill(skill_path)

    result = {
        'valid': struct_valid,
        'structure': {
            'valid': struct_valid,
            'message': struct_message,
            'skill_version': skill_version
        }
    }

    # IMPROVEMENT_PLAN validation if requested (custom enhancement)
    if check_improvement_plan:
        ip_valid, ip_message = validate_improvement_plan(skill_path, skill_version)
        result['improvement_plan'] = {
            'valid': ip_valid,
            'message': ip_message
        }
        result['valid'] = struct_valid and ip_valid

    return result


# ============================================================================
# Import calculate_metrics functionality
# ============================================================================

# Guidelines and Thresholds
GUIDELINE_MAX_LINES = 500
GUIDELINE_MAX_TOKENS = 2000
GUIDELINE_RECOMMENDED_LINES = 300

# Required frontmatter fields
REQUIRED_FRONTMATTER = ['name', 'description']

# Recommended frontmatter fields (Agent Skills spec)
RECOMMENDED_FRONTMATTER = ['metadata', 'compatibility', 'license']


# ============================================================================
# File Reading Utilities (from calculate_metrics.py)
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
# Metric Calculations (from calculate_metrics.py)
# ============================================================================

def calculate_basic_metrics(skill_path):
    """Calculate basic metrics about the skill"""
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
    """Calculate conciseness score (0-100)"""
    lines = basic_metrics['skill_md_lines']
    tokens = basic_metrics['skill_md_tokens']

    # Line score (0-50 points)
    if lines <= GUIDELINE_RECOMMENDED_LINES:
        line_score = 50
    elif lines <= GUIDELINE_MAX_LINES:
        line_score = 50 - ((lines - GUIDELINE_RECOMMENDED_LINES) / (GUIDELINE_MAX_LINES - GUIDELINE_RECOMMENDED_LINES)) * 25
    else:
        line_score = max(0, 25 - ((lines - GUIDELINE_MAX_LINES) / 500) * 25)

    # Token score (0-50 points)
    if tokens <= GUIDELINE_MAX_TOKENS:
        token_score = 50
    else:
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
    """Calculate complexity score (0-100)"""
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
    if section_count <= 5:
        section_score = 40
    elif section_count <= 10:
        section_score = 30
    else:
        section_score = max(0, 30 - (section_count - 10) * 2)

    if max_depth <= 3:
        depth_score = 30
    elif max_depth <= 5:
        depth_score = 20
    else:
        depth_score = max(0, 20 - (max_depth - 5) * 5)

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
    """Calculate spec compliance score (0-100)"""
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

    # Check for old 'version' field
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
    """Calculate progressive disclosure score (0-100)"""
    score = 100
    issues = []

    lines = basic_metrics['skill_md_lines']
    has_scripts = basic_metrics['scripts_count'] > 0
    has_references = basic_metrics['references_count'] > 0
    has_assets = basic_metrics['assets_count'] > 0

    # If skill is very long but has no references
    if lines > 500 and not has_references:
        score -= 30
        issues.append("Very long SKILL.md with no references; content should be split")

    # If skill is moderate length with no bundled resources
    if 200 < lines <= 500 and not (has_scripts or has_references or has_assets):
        score -= 10
        issues.append("Moderate length with no bundled resources; consider if content could be split")

    # If skill has references but minimal content
    if has_references and basic_metrics['references_lines'] < 50:
        score -= 15
        issues.append("Has references directory but minimal content; ensure references are substantial")

    # Good use of progressive disclosure
    if has_references and 200 <= lines <= 400:
        score = min(100, score + 10)

    return {
        'score': int(score),
        'issues': issues,
        'uses_scripts': has_scripts,
        'uses_references': has_references,
        'uses_assets': has_assets
    }


def calculate_overall_score(conciseness, complexity, spec_compliance, progressive):
    """Calculate weighted overall score"""
    overall = (
        conciseness['score'] * 0.25 +
        complexity['score'] * 0.20 +
        spec_compliance['score'] * 0.35 +
        progressive['score'] * 0.20
    )

    return int(overall)


# ============================================================================
# Enhanced AgentSkills Specification Validation
# ============================================================================

def validate_naming_conventions(skill_path, frontmatter_dict):
    """
    Validate naming conventions per AgentSkills spec

    Returns: {
        'valid': bool,
        'violations': [str],
        'warnings': [str]
    }
    """
    violations = []
    warnings = []

    name = frontmatter_dict.get('name', '')
    dir_name = skill_path.name

    # Name must be 1-64 characters
    if not name:
        violations.append("Name field is empty")
    elif len(name) > 64:
        violations.append(f"Name exceeds 64 characters ({len(name)})")

    # Lowercase alphanumeric and hyphens only
    if name and not all(c.islower() or c.isdigit() or c == '-' for c in name):
        violations.append(f"Name contains invalid characters (must be lowercase alphanumeric and hyphens only): {name}")

    # Cannot start or end with hyphens
    if name and (name.startswith('-') or name.endswith('-')):
        violations.append(f"Name cannot start or end with hyphens: {name}")

    # Cannot contain consecutive hyphens
    if name and '--' in name:
        violations.append(f"Name cannot contain consecutive hyphens: {name}")

    # Must match directory name
    if name and name != dir_name:
        violations.append(f"Name '{name}' does not match directory name '{dir_name}'")

    # Description validation
    description = frontmatter_dict.get('description', '')
    if not description:
        violations.append("Description is empty")
    elif len(description) > 1024:
        violations.append(f"Description exceeds 1024 characters ({len(description)})")

    # Description should be third-person
    if description and not any(phrase in description.lower() for phrase in ['this skill', 'use when', 'use this']):
        warnings.append("Description should use third-person (e.g., 'This skill should be used when...')")

    return {
        'valid': len(violations) == 0,
        'violations': violations,
        'warnings': warnings
    }


def validate_file_references(skill_path, body):
    """
    Validate file references use relative paths and follow best practices

    Returns: {
        'valid': bool,
        'issues': [str]
    }
    """
    issues = []

    # Check for absolute paths
    if '/Users/' in body or '/home/' in body or 'C:\\' in body:
        issues.append("Found absolute paths in SKILL.md; use relative paths")

    # Check for deeply nested references
    if 'references/' in body:
        lines = body.split('\n')
        for line in lines:
            if 'references/' in line:
                # Count directory depth
                if line.count('/') > 2:  # references/subdir/file = 2 levels
                    issues.append(f"Deep nested reference found (keep one-level deep): {line.strip()}")

    return {
        'valid': len(issues) == 0,
        'issues': issues
    }


def validate_agentskills_spec(skill_path, frontmatter_dict, basic_metrics, body):
    """
    Complete AgentSkills specification validation

    Returns: {
        'spec_compliant': bool,
        'naming': dict,
        'file_references': dict,
        'progressive_disclosure_check': dict,
        'violations': [str],
        'warnings': [str]
    }
    """
    all_violations = []
    all_warnings = []

    # Naming conventions
    naming = validate_naming_conventions(skill_path, frontmatter_dict)
    all_violations.extend(naming['violations'])
    all_warnings.extend(naming['warnings'])

    # File references
    file_refs = validate_file_references(skill_path, body)
    if not file_refs['valid']:
        all_warnings.extend(file_refs['issues'])

    # Progressive disclosure
    lines = basic_metrics['skill_md_lines']
    prog_check = {
        'follows_guidelines': lines <= GUIDELINE_MAX_LINES,
        'recommended_range': lines <= GUIDELINE_RECOMMENDED_LINES,
        'issues': []
    }

    if lines > GUIDELINE_MAX_LINES:
        prog_check['issues'].append(f"SKILL.md exceeds recommended max of {GUIDELINE_MAX_LINES} lines ({lines} lines)")
        all_warnings.append(f"Consider moving content to references/ to reduce SKILL.md size")

    return {
        'spec_compliant': len(all_violations) == 0,
        'naming': naming,
        'file_references': file_refs,
        'progressive_disclosure_check': prog_check,
        'violations': all_violations,
        'warnings': all_warnings
    }


# ============================================================================
# Functionality Validation
# ============================================================================

def validate_skill_loading(skill_path):
    """
    Test that skill can be loaded properly

    Returns: {
        'can_load': bool,
        'load_time_ms': float,
        'issues': [str]
    }
    """
    issues = []
    start_time = time.time()

    try:
        # Try to read SKILL.md
        frontmatter, body, content = read_skill_md(skill_path)
        frontmatter_dict = parse_frontmatter(frontmatter)

        # Check required fields
        if 'name' not in frontmatter_dict:
            issues.append("Cannot load: missing 'name' field")
        if 'description' not in frontmatter_dict:
            issues.append("Cannot load: missing 'description' field")

        load_time = (time.time() - start_time) * 1000

        return {
            'can_load': len(issues) == 0,
            'load_time_ms': round(load_time, 2),
            'issues': issues
        }
    except Exception as e:
        return {
            'can_load': False,
            'load_time_ms': 0,
            'issues': [f"Failed to load skill: {str(e)}"]
        }


def validate_scripts(skill_path):
    """
    Check that bundled scripts are executable

    Returns: {
        'scripts': [{
            'path': str,
            'executable': bool,
            'issues': [str]
        }]
    }
    """
    scripts_dir = skill_path / 'scripts'
    results = []

    if not scripts_dir.exists():
        return {'scripts': []}

    for script_file in scripts_dir.rglob('*'):
        if script_file.is_file() and not script_file.name.startswith('.'):
            issues = []

            # Check if file is executable
            is_executable = os.access(script_file, os.X_OK)
            if not is_executable and script_file.suffix in ['.py', '.sh', '.bash']:
                issues.append(f"Script is not executable (chmod +x may be needed)")

            # Check for shebang
            try:
                with open(script_file, 'r') as f:
                    first_line = f.readline()
                    if not first_line.startswith('#!'):
                        issues.append("Missing shebang line (e.g., #!/usr/bin/env python3)")
            except:
                issues.append("Could not read file (may be binary)")

            results.append({
                'path': str(script_file.relative_to(skill_path)),
                'executable': is_executable,
                'issues': issues
            })

    return {'scripts': results}


def validate_references_readable(skill_path):
    """
    Check that reference files are readable

    Returns: {
        'references': [{
            'path': str,
            'readable': bool,
            'size_kb': float,
            'issues': [str]
        }]
    }
    """
    refs_dir = skill_path / 'references'
    results = []

    if not refs_dir.exists():
        return {'references': []}

    for ref_file in refs_dir.rglob('*'):
        if ref_file.is_file() and not ref_file.name.startswith('.'):
            issues = []
            readable = False
            size_kb = 0

            try:
                with open(ref_file, 'r') as f:
                    content = f.read()
                    readable = True
                    size_kb = len(content) / 1024

                    # Warn if very large
                    if size_kb > 100:
                        issues.append(f"Large file ({size_kb:.1f} KB); consider including grep patterns in SKILL.md")
            except Exception as e:
                issues.append(f"Could not read file: {str(e)}")

            results.append({
                'path': str(ref_file.relative_to(skill_path)),
                'readable': readable,
                'size_kb': round(size_kb, 2),
                'issues': issues
            })

    return {'references': results}


def validate_functionality(skill_path):
    """
    Run complete functionality validation

    Returns: {
        'loading': dict,
        'scripts': dict,
        'references': dict,
        'overall_functional': bool
    }
    """
    loading = validate_skill_loading(skill_path)
    scripts = validate_scripts(skill_path)
    references = validate_references_readable(skill_path)

    # Determine overall functionality
    overall_functional = loading['can_load']

    # Check for critical script issues
    for script in scripts.get('scripts', []):
        if script['issues'] and any('executable' in issue.lower() for issue in script['issues']):
            overall_functional = False

    return {
        'loading': loading,
        'scripts': scripts,
        'references': references,
        'overall_functional': overall_functional
    }


# ============================================================================
# Comparison Functionality
# ============================================================================

def compare_skills(improved_path, original_path):
    """
    Compare improved skill against original to verify improvements

    Returns: {
        'improved': dict,      # Full metrics for improved skill
        'original': dict,      # Full metrics for original skill
        'comparison': dict,    # Score deltas and analysis
        'verified_better': bool
    }
    """
    # Calculate metrics for both
    improved_metrics = calculate_all_metrics(improved_path)
    original_metrics = calculate_all_metrics(original_path)

    # Calculate deltas
    deltas = {
        'conciseness': improved_metrics['conciseness']['score'] - original_metrics['conciseness']['score'],
        'complexity': improved_metrics['complexity']['score'] - original_metrics['complexity']['score'],
        'spec_compliance': improved_metrics['spec_compliance']['score'] - original_metrics['spec_compliance']['score'],
        'progressive_disclosure': improved_metrics['progressive_disclosure']['score'] - original_metrics['progressive_disclosure']['score'],
        'overall': improved_metrics['overall_score'] - original_metrics['overall_score']
    }

    # Analysis
    improvements = []
    regressions = []

    for metric, delta in deltas.items():
        if delta > 5:
            improvements.append(f"{metric}: +{delta} points")
        elif delta < -5:
            regressions.append(f"{metric}: {delta} points")

    verified_better = deltas['overall'] > 0 and len(regressions) == 0

    return {
        'improved': improved_metrics,
        'original': original_metrics,
        'comparison': {
            'deltas': deltas,
            'improvements': improvements,
            'regressions': regressions
        },
        'verified_better': verified_better
    }


# ============================================================================
# Metadata Storage
# ============================================================================

def store_metrics_in_metadata(skill_path, metrics):
    """
    Store metrics in SKILL.md frontmatter under metadata

    Updates frontmatter with:
        metadata:
          conciseness: <score>
          complexity: <score>
          spec_compliance: <score>
          progressive: <score>
    """
    skill_md = skill_path / 'SKILL.md'

    with open(skill_md, 'r') as f:
        content = f.read()

    # Parse frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise Exception("Malformed frontmatter")

    frontmatter = parts[1]
    body = parts[2]

    # Parse existing frontmatter
    frontmatter_dict = parse_frontmatter(frontmatter)

    # Add/update metrics in metadata
    metrics_data = {
        'conciseness': metrics['conciseness']['score'],
        'complexity': metrics['complexity']['score'],
        'spec_compliance': metrics['spec_compliance']['score'],
        'progressive': metrics['progressive_disclosure']['score'],
        'overall': metrics['overall_score'],
        'last_evaluated': datetime.now().strftime('%Y-%m-%d')
    }

    # Build new frontmatter (preserve existing fields)
    new_frontmatter_lines = []
    in_metadata = False
    metadata_written = False

    for line in frontmatter.split('\n'):
        if line.strip().startswith('metadata:'):
            in_metadata = True
            new_frontmatter_lines.append(line)
            # Add metrics under metadata
            for key, value in metrics_data.items():
                new_frontmatter_lines.append(f"  {key}: {value}")
            metadata_written = True
        elif in_metadata and line.startswith('  ') and ':' in line:
            # Skip existing metadata fields that we're updating
            key = line.split(':')[0].strip()
            if key not in metrics_data:
                new_frontmatter_lines.append(line)
        elif in_metadata and not line.startswith(' '):
            in_metadata = False
            new_frontmatter_lines.append(line)
        else:
            new_frontmatter_lines.append(line)

    # If no metadata section existed, add it
    if not metadata_written:
        new_frontmatter_lines.append('metadata:')
        for key, value in metrics_data.items():
            new_frontmatter_lines.append(f"  {key}: {value}")

    # Reconstruct file
    new_content = '---\n' + '\n'.join(new_frontmatter_lines) + '\n---' + body

    # Write back
    with open(skill_md, 'w') as f:
        f.write(new_content)

    return True


# ============================================================================
# Main Evaluation Function
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


def evaluate_skill(skill_path, compare_with=None, validate_func=False, store_metrics=False, quiet=False):
    """
    Comprehensive skill evaluation

    Args:
        skill_path: Path to skill to evaluate
        compare_with: Optional path to original skill for comparison
        validate_func: Whether to run functionality validation
        store_metrics: Whether to store metrics in SKILL.md metadata
        quiet: Suppress status messages (for JSON output)

    Returns: Complete evaluation results
    """
    skill_path = Path(skill_path)

    # Baseline metrics
    if not quiet:
        print(f"Evaluating skill: {skill_path.name}", file=sys.stderr)
    metrics = calculate_all_metrics(skill_path)

    # Enhanced spec validation
    frontmatter, body, content = read_skill_md(skill_path)
    frontmatter_dict = parse_frontmatter(frontmatter)
    spec_validation = validate_agentskills_spec(skill_path, frontmatter_dict, metrics['basic_metrics'], body)

    # Comparison (if requested)
    comparison = None
    if compare_with:
        if not quiet:
            print(f"Comparing with original: {compare_with}", file=sys.stderr)
        comparison = compare_skills(skill_path, Path(compare_with))

    # Functionality validation (if requested)
    functionality = None
    if validate_func:
        if not quiet:
            print("Validating functionality...", file=sys.stderr)
        functionality = validate_functionality(skill_path)

    # Store metrics (if requested)
    if store_metrics:
        if not quiet:
            print("Storing metrics in SKILL.md metadata...", file=sys.stderr)
        store_metrics_in_metadata(skill_path, metrics)

    return {
        'skill_path': str(skill_path),
        'timestamp': datetime.now().isoformat(),
        'metrics': metrics,
        'spec_validation': spec_validation,
        'comparison': comparison,
        'functionality': functionality,
        'metrics_stored': store_metrics
    }


# ============================================================================
# Output Formatting
# ============================================================================

def print_quick_validation_text(validation_result):
    """Print quick validation in human-readable text format"""
    struct = validation_result['structure']
    print(struct['message'])

    if not struct['valid']:
        sys.exit(1)

    # IMPROVEMENT_PLAN validation
    if 'improvement_plan' in validation_result:
        print()  # Blank line
        ip = validation_result['improvement_plan']
        print(ip['message'])

        if not ip['valid']:
            sys.exit(1)

    sys.exit(0)


def format_score_bar(score, width=20):
    """Format score as visual bar"""
    filled = int((score / 100) * width)
    empty = width - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {score}/100"


def print_evaluation_text(evaluation):
    """Print evaluation in human-readable text format"""
    print(f"\n{'='*60}")
    print(f"Skill Evaluation: {evaluation['metrics']['skill_name']}")
    print(f"{'='*60}\n")

    # Basic Metrics
    basic = evaluation['metrics']['basic_metrics']
    print("Basic Metrics:")
    print(f"  SKILL.md: {basic['skill_md_lines']} lines, ~{basic['skill_md_tokens']} tokens")
    print(f"  Scripts: {basic['scripts_count']} files, {basic['scripts_lines']} lines")
    print(f"  References: {basic['references_count']} files, {basic['references_lines']} lines")
    print(f"  Assets: {basic['assets_count']} files")
    print()

    # Quality Scores
    metrics = evaluation['metrics']
    print("Quality Scores:")
    print(f"  Conciseness:     {format_score_bar(metrics['conciseness']['score'])}")
    print(f"  Complexity:      {format_score_bar(metrics['complexity']['score'])}")
    print(f"  Spec Compliance: {format_score_bar(metrics['spec_compliance']['score'])}")
    print(f"  Progressive:     {format_score_bar(metrics['progressive_disclosure']['score'])}")
    print(f"  Overall:         {format_score_bar(metrics['overall_score'])}")
    print()

    # Spec Validation
    spec = evaluation['spec_validation']
    print(f"AgentSkills Spec Compliance: {'✓ PASS' if spec['spec_compliant'] else '✗ FAIL'}")
    if spec['violations']:
        print("\n❌ Violations:")
        for v in spec['violations']:
            print(f"  - {v}")
    if spec['warnings']:
        print("\n⚠ Warnings:")
        for w in spec['warnings']:
            print(f"  - {w}")
    print()

    # Comparison
    if evaluation.get('comparison'):
        comp = evaluation['comparison']
        print(f"{'='*60}")
        print("Comparison with Original")
        print(f"{'='*60}\n")

        print("Score Changes:")
        for metric, delta in comp['comparison']['deltas'].items():
            symbol = '↑' if delta > 0 else ('↓' if delta < 0 else '→')
            color = '+' if delta > 0 else ''
            print(f"  {metric}: {symbol} {color}{delta:+d} points")
        print()

        if comp['comparison']['improvements']:
            print("✓ Improvements:")
            for imp in comp['comparison']['improvements']:
                print(f"  - {imp}")
            print()

        if comp['comparison']['regressions']:
            print("✗ Regressions:")
            for reg in comp['comparison']['regressions']:
                print(f"  - {reg}")
            print()

        print(f"Verified Better: {'✓ YES' if comp['verified_better'] else '✗ NO'}")
        print()

    # Functionality
    if evaluation.get('functionality'):
        func = evaluation['functionality']
        print(f"{'='*60}")
        print("Functionality Validation")
        print(f"{'='*60}\n")

        loading = func['loading']
        print(f"Loading: {'✓ PASS' if loading['can_load'] else '✗ FAIL'} ({loading['load_time_ms']}ms)")
        if loading['issues']:
            for issue in loading['issues']:
                print(f"  - {issue}")
        print()

        if func['scripts']['scripts']:
            print(f"Scripts ({len(func['scripts']['scripts'])}):")
            for script in func['scripts']['scripts']:
                status = '✓' if script['executable'] else '⚠'
                print(f"  {status} {script['path']}")
                for issue in script['issues']:
                    print(f"      - {issue}")
            print()

        if func['references']['references']:
            print(f"References ({len(func['references']['references'])}):")
            for ref in func['references']['references']:
                status = '✓' if ref['readable'] else '✗'
                print(f"  {status} {ref['path']} ({ref['size_kb']} KB)")
                for issue in ref['issues']:
                    print(f"      - {issue}")
            print()

        print(f"Overall Functional: {'✓ YES' if func['overall_functional'] else '✗ NO'}")
        print()

    print(f"{'='*60}\n")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv or '-h' in sys.argv else 1)

    skill_path = sys.argv[1]
    quick_mode = False
    check_improvement_plan = False
    compare_with = None
    validate_func = False
    store_metrics_flag = False
    output_format = 'text'
    output_file = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--quick':
            quick_mode = True
            i += 1
        elif arg == '--check-improvement-plan':
            check_improvement_plan = True
            i += 1
        elif arg == '--compare' and i + 1 < len(sys.argv):
            compare_with = sys.argv[i + 1]
            i += 2
        elif arg == '--validate-functionality':
            validate_func = True
            i += 1
        elif arg == '--store-metrics':
            store_metrics_flag = True
            i += 1
        elif arg == '--format' and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    try:
        # Quick validation mode
        if quick_mode:
            validation_result = quick_validate(skill_path, check_improvement_plan)

            if output_format == 'json':
                output = json.dumps(validation_result, indent=2)
                if output_file:
                    with open(output_file, 'w') as f:
                        f.write(output)
                    print(f"Results saved to {output_file}")
                else:
                    print(output)
                sys.exit(0 if validation_result['valid'] else 1)
            else:
                print_quick_validation_text(validation_result)
                # This function exits with appropriate code

        # Comprehensive evaluation mode
        evaluation = evaluate_skill(
            skill_path,
            compare_with=compare_with,
            validate_func=validate_func,
            store_metrics=store_metrics_flag,
            quiet=(output_format == 'json')
        )

        # Output results
        if output_format == 'json':
            output = json.dumps(evaluation, indent=2)
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(output)
                print(f"Results saved to {output_file}")
            else:
                print(output)
        else:
            print_evaluation_text(evaluation)
            if output_file:
                # Save JSON version to file even in text mode
                with open(output_file, 'w') as f:
                    json.dump(evaluation, f, indent=2)
                print(f"Detailed results saved to {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
