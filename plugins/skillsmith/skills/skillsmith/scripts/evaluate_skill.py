#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
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
    uv run scripts/evaluate_skill.py <skill-path> --quick
    uv run scripts/evaluate_skill.py <skill-path> --quick --check-improvement-plan

    # Baseline evaluation
    uv run scripts/evaluate_skill.py <skill-path>

    # Compare original vs improved
    uv run scripts/evaluate_skill.py <skill-path> --compare <original-path>

    # With functionality validation
    uv run scripts/evaluate_skill.py <skill-path> --validate-functionality

    # Store metrics in skill metadata
    uv run scripts/evaluate_skill.py <skill-path> --store-metrics

    # Full evaluation with all options
    uv run scripts/evaluate_skill.py <skill-path> --compare <original-path> --validate-functionality --store-metrics --format json

    # Export version history table row for IMPROVEMENT_PLAN.md
    uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version 2.0.0 --issue 123
    uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version 1.0.0

    # Per-metric coaching with actionable improvement suggestions
    uv run scripts/evaluate_skill.py <skill-path> --explain

    # Validate reference file mentions and structure
    uv run scripts/evaluate_skill.py <skill-path> --validate-references

    # Detect consolidation opportunities across reference files
    uv run scripts/evaluate_skill.py <skill-path> --detect-duplicates

    # Generate/update README.md with capabilities prose + metrics + version history
    uv run scripts/evaluate_skill.py <skill-path> --update-readme

Options:
    --quick                   Fast validation mode (structure only)
    --strict                  Strict mode: treat warnings as errors (requires --quick)
    --check-improvement-plan  Validate IMPROVEMENT_PLAN.md if present (legacy, requires --quick)
    --explain                 Per-metric coaching with actionable improvements (incompatible with --quick)
    --validate-references     Validate references/ structure and mention coverage
    --detect-duplicates       Detect consolidation opportunities across reference files (opt-in)
    --update-readme           Generate/update README.md with capabilities prose + metrics + version history
    --compare <path>          Compare against original skill version
    --validate-functionality  Run functionality validation tests
    --store-metrics          Store metrics in SKILL.md metadata
    --export-table-row       Export version history table row (requires --version)
    --version <version>      Version number for table row export (e.g., 2.0.0)
    --issue <number>         GitHub issue number for table row export (optional)
    --format json|text       Output format (default: text)
    --output <file>          Save results to file
"""

import atexit
import os
import shutil
import sys
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

# Previously imported from quick_validate.py (now deleted - functionality integrated below)
# from quick_validate import validate_skill

# Inlined validate_skill function (previously from quick_validate.py)
def validate_skill(skill_path):
    """Basic validation of a skill - inlined from quick_validate.py"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found", None

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found", None

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format", None

    frontmatter_text = match.group(1)

    # Parse frontmatter as YAML to correctly handle block scalars (|, >), quoted
    # strings, and nested keys — avoiding false positives from raw text scanning.
    import yaml
    try:
        fm = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError as e:
        return False, f"Invalid YAML frontmatter: {e}", None

    # Check required fields
    if 'name' not in fm:
        return False, "Missing 'name' in frontmatter", None
    if 'description' not in fm:
        return False, "Missing 'description' in frontmatter", None

    # Validate name
    name = str(fm['name']).strip()
    if not re.match(r'^[a-z0-9-]+$', name):
        return False, f"Name '{name}' should be hyphen-case (lowercase letters, digits, and hyphens only)", None
    if name.startswith('-') or name.endswith('-') or '--' in name:
        return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens", None

    # Validate description (parsed value — block scalar indicators are not included)
    description = str(fm['description']).strip()
    if '<' in description or '>' in description:
        return False, "Description cannot contain angle brackets (< or >)", None

    # Extract version — may be top-level or nested under metadata:
    metadata = fm.get('metadata', {}) or {}
    skill_version = str(fm['version']).strip() if 'version' in fm else \
                    str(metadata['version']).strip() if 'version' in metadata else None

    return True, "Skill is valid!", skill_version


# ============================================================================
# IMPROVEMENT_PLAN Validation (custom enhancement)
# ============================================================================


def validate_improvement_plan_table_format(content):
    """
    Validate new table-based IMPROVEMENT_PLAN.md format

    Returns: (valid: bool, issues: [str], warnings: [str])
    """
    issues = []
    warnings = []

    # Check for Planned Improvements section
    has_planned = '## 🔮 Planned Improvements' in content or '## Planned Improvements' in content
    has_completed = '## ✅ Completed Improvements' in content or '## Completed Improvements' in content

    if not has_planned and not has_completed:
        # Might be old format, skip table validation
        return True, issues, warnings

    # Validate Planned Improvements table structure
    if has_planned:
        # Check for table with required columns
        planned_section = content.split('## 🔮 Planned Improvements' if '## 🔮 Planned Improvements' in content else '## Planned Improvements')[1]
        planned_section = planned_section.split('##')[0]  # Get section until next heading

        # Check for table headers
        if '| Issue |' not in planned_section and '|Issue|' not in planned_section:
            issues.append("Planned Improvements section missing table headers (Issue, Priority, Title, Status)")
        else:
            # Check for required columns
            required_cols = ['Issue', 'Priority', 'Title', 'Status']
            for col in required_cols:
                if col not in planned_section:
                    issues.append(f"Planned Improvements table missing '{col}' column")

            # Check for issue number format (#XXX)
            issue_lines = [line for line in planned_section.split('\n') if line.strip().startswith('|') and '---' not in line and 'Issue' not in line]
            for line in issue_lines:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) > 0:
                    issue_num = parts[0]
                    if issue_num and issue_num.upper() not in ['TBD', 'N/A'] and not issue_num.startswith('#'):
                        warnings.append(f"Issue number should use #XXX format: '{issue_num}'")

    # Validate Completed Improvements table structure
    if has_completed:
        completed_section = content.split('## ✅ Completed Improvements' if '## ✅ Completed Improvements' in content else '## Completed Improvements')[1]
        completed_section = completed_section.split('##')[0]

        # Check for table headers
        if '| Version |' not in completed_section and '|Version|' not in completed_section:
            issues.append("Completed Improvements section missing table headers (Version, Date, Issue, Title, Key Changes)")
        else:
            # Check for required columns
            required_cols = ['Version', 'Date', 'Issue', 'Title', 'Key Changes']
            for col in required_cols:
                if col not in completed_section:
                    issues.append(f"Completed Improvements table missing '{col}' column")

            # Check for issue number format (#XXX)
            issue_lines = [line for line in completed_section.split('\n') if line.strip().startswith('|') and '---' not in line and 'Version' not in line]
            for line in issue_lines:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3:  # Version, Date, Issue at minimum
                    issue_num = parts[2]
                    if issue_num and issue_num.upper() not in ['TBD', 'N/A'] and not issue_num.startswith('#'):
                        warnings.append(f"Issue number should use #XXX format: '{issue_num}'")

    return len(issues) == 0, issues, warnings


def validate_improvement_plan(skill_path, skill_version=None):
    """
    Validate IMPROVEMENT_PLAN.md completeness and consistency

    Supports both old format (Version History table) and new format (Planned/Completed tables)

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

        # Check for new table format first
        has_new_format = ('## 🔮 Planned Improvements' in content or '## Planned Improvements' in content) and \
                        ('## ✅ Completed Improvements' in content or '## Completed Improvements' in content)

        if has_new_format:
            # Validate new table format
            table_valid, table_issues, table_warnings = validate_improvement_plan_table_format(content)
            errors.extend(table_issues)
            warnings.extend(table_warnings)

            # Return results
            if errors:
                return False, '\n\n'.join(['❌ ' + e for e in errors])
            elif warnings:
                return True, '\n\n'.join(['⚠️  ' + w for w in warnings])
            else:
                return True, "✓ IMPROVEMENT_PLAN.md table format is valid"

        # Fall back to old format validation
        # Find version history table
        version_history_start = None
        for i, line in enumerate(lines):
            if '## Version History' in line:
                version_history_start = i
                break

        if version_history_start is None:
            return True, "✓ IMPROVEMENT_PLAN.md exists but no recognized format found"

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


# ============================================================================
# Python Script PEP 723 Validation
# ============================================================================


def check_python_scripts_pep723(skill_dir):
    """
    Check if Python scripts use PEP 723 inline metadata.

    Args:
        skill_dir: Path to skill directory

    Returns:
        Tuple of (issues, warnings) lists
    """
    issues = []
    warnings = []
    scripts_dir = Path(skill_dir) / "scripts"

    if not scripts_dir.exists():
        return issues, warnings

    python_scripts = list(scripts_dir.glob("*.py"))

    if not python_scripts:
        return issues, warnings

    scripts_without_pep723 = []

    for script in python_scripts:
        try:
            content = script.read_text(encoding='utf-8')

            # Check for PEP 723 metadata block
            has_pep723 = "# /// script" in content

            if not has_pep723:
                scripts_without_pep723.append(script.name)

        except Exception as e:
            warnings.append(f"Could not read {script.name}: {e}")

    if scripts_without_pep723:
        issues.append(
            f"Python scripts missing PEP 723 metadata: {', '.join(scripts_without_pep723)}\n"
            f"   All Python scripts in skills MUST use PEP 723 inline metadata for uv execution.\n"
            f"   Load skillsmith's references/python_uv_guide.md for conversion guidance.\n"
            f"   See: https://peps.python.org/pep-0723/"
        )

    return issues, warnings


def check_uv_compatibility(skill_dir):
    """
    Check if skill with Python scripts declares uv compatibility.

    Args:
        skill_dir: Path to skill directory

    Returns:
        Tuple of (issues, warnings) lists
    """
    issues = []
    warnings = []

    scripts_dir = Path(skill_dir) / "scripts"
    skill_md = Path(skill_dir) / "SKILL.md"

    # Check if there are Python scripts
    if not scripts_dir.exists():
        return issues, warnings

    python_scripts = list(scripts_dir.glob("*.py"))
    if not python_scripts:
        return issues, warnings

    # If Python scripts exist, check compatibility field
    try:
        content = skill_md.read_text(encoding='utf-8')

        # Check if compatibility mentions uv
        if 'compatibility:' in content:
            # Extract compatibility section (simplified check)
            if 'uv' not in content.lower():
                warnings.append(
                    "Skill has Python scripts but compatibility field doesn't mention 'uv'.\n"
                    "   Add 'Requires uv for Python script execution' to compatibility field."
                )
        else:
            warnings.append(
                "Skill has Python scripts but no compatibility field.\n"
                "   Add compatibility field mentioning uv requirement."
            )

    except Exception as e:
        warnings.append(f"Could not verify uv compatibility: {e}")

    return issues, warnings


def quick_validate(skill_path, check_improvement_plan=False):
    """
    Perform quick validation of skill structure

    Uses validate_skill() from quick_validate.py for basic validation,
    optionally adds IMPROVEMENT_PLAN validation (custom enhancement).
    Enhanced with metadata.version checking.

    Returns: {
        'valid': bool,
        'structure': dict,
        'improvement_plan': dict | None
    }
    """
    skill_path = Path(skill_path)

    # Basic structure validation (imported from quick_validate.py)
    struct_valid, struct_message, skill_version = validate_skill(skill_path)

    # Enhanced version checking (check metadata.version specifically)
    if struct_valid:
        try:
            skill_md = Path(skill_path) / 'SKILL.md'
            content = skill_md.read_text()
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if match:
                import yaml
                try:
                    frontmatter = yaml.safe_load(match.group(1))

                    # Check for version in metadata (preferred location)
                    has_metadata_version = (
                        isinstance(frontmatter, dict) and
                        'metadata' in frontmatter and
                        isinstance(frontmatter['metadata'], dict) and
                        'version' in frontmatter['metadata']
                    )

                    # Check for version at top level (deprecated)
                    has_toplevel_version = (
                        isinstance(frontmatter, dict) and
                        'version' in frontmatter and
                        'metadata' not in frontmatter
                    )

                    # Use metadata.version if available, otherwise top-level version
                    if has_metadata_version:
                        skill_version = frontmatter['metadata']['version']
                    elif has_toplevel_version:
                        skill_version = frontmatter['version']
                        struct_message = f"{struct_message} (Note: using deprecated 'version' field; prefer 'metadata.version')"
                    elif not skill_version:
                        # No version found in either location
                        struct_valid = False
                        struct_message = "Missing version field (should be in metadata.version)"

                except yaml.YAMLError:
                    # YAML parsing failed, but quick_validate already caught this
                    pass
        except Exception:
            # File read error, but quick_validate already caught this
            pass

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

    # Python PEP 723 validation
    pep723_issues, pep723_warnings = check_python_scripts_pep723(skill_path)
    uv_issues, uv_warnings = check_uv_compatibility(skill_path)

    all_pep723_issues = pep723_issues + uv_issues
    all_pep723_warnings = pep723_warnings + uv_warnings

    if all_pep723_issues or all_pep723_warnings:
        result['pep723'] = {
            'issues': all_pep723_issues,
            'warnings': all_pep723_warnings
        }
        # PEP 723 issues make the skill invalid
        if all_pep723_issues:
            result['valid'] = False

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
    """Estimate token count (word-count based: ~1.3 tokens per word for English prose)"""
    return int(len(text.split()) * 1.3)


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


_LEGACY_MARKERS = [
    re.compile(r'\blegacy\b', re.IGNORECASE),
    re.compile(r'\bdeprecated\b', re.IGNORECASE),
    re.compile(r'prefer .+? instead', re.IGNORECASE),
    re.compile(r'use .+? instead', re.IGNORECASE),
    re.compile(r'\bold approach\b', re.IGNORECASE),
]

_REFERENCE_POINTER = re.compile(
    r'(?:[Ss]ee|[Ff]ull guide in|[Cc]omplete guide in)\s+`?references/',
)


def check_qualitative_conciseness(skill_path: 'Path', skill_content: str) -> list[str]:
    """
    Detect qualitative conciseness issues not caught by line/token counts.

    Returns a list of warning strings (informational — no score change).

    Three detectors:
    1. Legacy/deprecated blocks — collapsed consecutive matched lines into one warning
    2. Inline content (5+ lines) immediately before a "See references/" pointer
    3. Headings in reference files that also appear verbatim in SKILL.md
    """
    warnings: list[str] = []
    lines = skill_content.splitlines()

    # ── Detector 1: Legacy/deprecated blocks ────────────────────────────────
    legacy_blocks: list[tuple[int, int]] = []  # (start_line, end_line) 1-indexed
    block_start: int | None = None
    for i, line in enumerate(lines, 1):
        is_match = any(pat.search(line) for pat in _LEGACY_MARKERS)
        if is_match:
            if block_start is None:
                block_start = i
        else:
            if block_start is not None:
                legacy_blocks.append((block_start, i - 1))
                block_start = None
    if block_start is not None:
        legacy_blocks.append((block_start, len(lines)))

    for start, end in legacy_blocks:
        size = end - start + 1
        snippet = lines[start - 1][:60].strip()
        warnings.append(
            f'⚠ Qualitative: legacy/deprecated block (~{size} line(s), line {start}): '
            f'"{snippet}" — consider collapsing to a single reference link'
        )

    # ── Detector 2: Inline content before "See references/" pointer ─────────
    for i, line in enumerate(lines):
        if _REFERENCE_POINTER.search(line):
            # Count non-empty lines in the 8 lines before this one
            preceding = [l for l in lines[max(0, i - 8):i] if l.strip()]
            if len(preceding) >= 5:
                ref_match = re.search(r'references/\S+', line)
                ref_name = ref_match.group(0).rstrip('`).') if ref_match else 'references/'
                warnings.append(
                    f'⚠ Qualitative: inline block before "{ref_name}" pointer '
                    f'(~{len(preceding)} lines, around line {i + 1}) — '
                    f'offload to references/ or remove inline content'
                )

    # ── Detector 3: Reference heading duplication ────────────────────────────
    refs_dir = Path(skill_path) / 'references'
    if refs_dir.exists():
        heading_pat = re.compile(r'^#{2,3}\s+(.+)', re.MULTILINE)
        for ref_file in refs_dir.glob('*.md'):
            try:
                ref_text = ref_file.read_text()
            except Exception:
                continue
            for heading_match in heading_pat.finditer(ref_text):
                heading = heading_match.group(1).strip()
                # Only flag headings with ≥3 words (avoids generic "Overview", "Usage", etc.)
                if len(heading.split()) >= 3 and heading in skill_content:
                    warnings.append(
                        f'⚠ Qualitative: heading "{heading}" from {ref_file.name} '
                        f'appears duplicated in SKILL.md — remove inline copy'
                    )

    return warnings


def calculate_conciseness_score(basic_metrics):
    """Calculate conciseness score (0-100) with tiered scoring and reference offloading bonus"""
    lines = basic_metrics['skill_md_lines']
    tokens = basic_metrics['skill_md_tokens']
    has_references = basic_metrics['references_count'] > 0
    reference_lines = basic_metrics['references_lines']

    # Line score (0-50 points) - tiered scoring
    if lines <= 150:
        line_score = 50  # Excellent: very concise
    elif lines <= GUIDELINE_RECOMMENDED_LINES:  # 250
        line_score = 48  # Very good: within recommended
    elif lines <= 350:
        line_score = 45  # Good: slightly over recommended
    elif lines <= GUIDELINE_MAX_LINES:  # 500
        line_score = 40  # Acceptable: approaching max
    elif lines <= 750:
        line_score = 25  # Poor: significantly over max
    else:
        line_score = max(0, 10 - ((lines - 750) / 500) * 10)  # Very poor: way over

    # Token score (0-50 points) - stricter token limits
    token_limit = GUIDELINE_MAX_TOKENS  # 2000
    if tokens <= 1500:
        token_score = 50
    elif tokens <= token_limit:
        token_score = 45
    elif tokens <= 3000:
        token_score = 30
    else:
        token_score = max(0, 30 - ((tokens - 3000) / 2000) * 30)

    # Bonus for reference offloading (+5 points if substantial references exist)
    reference_bonus = 0
    if has_references and reference_lines > 500:
        reference_bonus = 5  # Bonus for moving content to references

    total_score = min(100, int(line_score + token_score + reference_bonus))

    return {
        'score': total_score,
        'line_score': int(line_score),
        'token_score': int(token_score),
        'reference_bonus': reference_bonus,
        'lines_vs_guideline': f"{lines}/{GUIDELINE_RECOMMENDED_LINES} (recommended)",
        'tokens_vs_guideline': f"{tokens}/{GUIDELINE_MAX_TOKENS} (max)",
        'reference_lines': reference_lines
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

    # Detect scannable structure: many short sections score better than a few dense ones
    total_lines = len(lines)
    avg_section_length = total_lines / section_count if section_count > 0 else total_lines
    is_scannable = avg_section_length < 15  # short avg section = well-organized reference table

    # Complexity scoring
    if section_count <= 5:
        section_score = 40
    elif section_count <= 10:
        section_score = 30
    else:
        raw_deduction = (section_count - 10) * 2
        if is_scannable:
            raw_deduction = int(raw_deduction * 0.8)  # 20% reduction for scannable structure
        section_score = max(0, 30 - raw_deduction)

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

    # If skill has references but minimal content (require ≥100 total lines AND ≥2 files)
    refs_lines = basic_metrics['references_lines']
    refs_count = basic_metrics['references_count']
    if has_references and (refs_lines < 100 or refs_count < 2):
        score -= 15
        issues.append(
            "References directory exists but is too thin "
            f"({refs_lines} lines, {refs_count} file(s)); "
            "aim for ≥100 lines across ≥2 files"
        )

    # Good use of progressive disclosure: medium-length skill with substantial references
    if has_references and 200 <= lines <= 400 and refs_lines >= 100 and refs_count >= 2:
        score = min(100, score + 10)

    return {
        'score': int(score),
        'issues': issues,
        'uses_scripts': has_scripts,
        'uses_references': has_references,
        'uses_assets': has_assets
    }


def validate_description_quality(frontmatter_dict):
    """
    Calculate description quality score (0-100)

    Scoring:
    - Trigger phrases present (+40 points): Specific quoted phrases like "create X", "validate Y"
    - Third-person format (+30 points): Uses "This skill should be used when..."
    - Specific vs generic (+20 points): Contains specific scenarios, not just vague terms
    - Under 1024 chars (+10 points): Complies with AgentSkills spec

    Returns: {
        'score': int,
        'trigger_phrases_found': [str],
        'has_third_person': bool,
        'is_specific': bool,
        'length_ok': bool,
        'issues': [str],
        'suggestions': [str]
    }
    """
    description = frontmatter_dict.get('description', '')
    score = 0
    issues = []
    suggestions = []
    trigger_phrases_found = []

    # Check for trigger phrases (patterns in quotes)
    import re
    _TRIGGER_VERBS = {
        'create', 'validate', 'evaluate', 'improve', 'analyze', 'check', 'init',
        'add', 'build', 'configure', 'set up', 'research', 'sync', 'generate',
        'update', 'fix', 'debug', 'run', 'install', 'migrate', 'deploy', 'optimize',
        'refactor', 'review', 'test', 'write', 'parse', 'convert', 'search',
    }
    _ARTICLES = {'a', 'an', 'the', 'my', 'your', 'its', 'this', 'that', 'all',
                 'any', 'some', 'new', 'existing'}
    _NEGATION_WORDS = {'not', "don't", "don't", 'never', 'no', 'without',
                       'avoid', "don't", 'cannot', "can't", 'stop', 'prevent'}

    def _is_valid_trigger_phrase(phrase):
        """Return True if phrase has a trigger verb as its first non-article word,
        with no negation before the verb."""
        words = phrase.lower().split()
        if not words:
            return False
        # Reject phrases containing negation anywhere
        if any(w in _NEGATION_WORDS for w in words):
            return False
        # Verb must be the first non-article word
        for word in words:
            if word in _ARTICLES:
                continue
            return any(word == verb or word.startswith(verb) for verb in _TRIGGER_VERBS)
        return False

    quoted_phrases = re.findall(r'"([^"]+)"', description)
    trigger_patterns = [p for p in quoted_phrases if _is_valid_trigger_phrase(p)]
    trigger_phrases_found = trigger_patterns

    if len(trigger_patterns) >= 3:
        score += 40
    elif len(trigger_patterns) >= 1:
        score += 20
        suggestions.append(f"Add more trigger phrases (found {len(trigger_patterns)}, recommend 3+)")
    else:
        issues.append("No trigger phrases found in description")
        suggestions.append("Add specific trigger phrases like '\"create a skill\"', '\"validate for quality\"'")

    # Check for third-person format
    third_person_patterns = [
        'this skill should be used',
        'this skill is used',
        'use this skill when',
        'should be used when',
    ]
    has_third_person = any(pattern in description.lower() for pattern in third_person_patterns)
    if has_third_person:
        score += 30
    else:
        issues.append("Description not in third-person format")
        suggestions.append("Start with 'This skill should be used when...'")

    # Check specificity (not just generic terms)
    generic_terms = ['provides guidance', 'helps with', 'assists with', 'for working with']
    is_generic = any(term in description.lower() for term in generic_terms) and len(trigger_patterns) == 0
    is_specific = len(trigger_patterns) > 0 or len(description) > 100

    if is_specific and not is_generic:
        score += 20
    elif is_generic:
        issues.append("Description is too generic")
        suggestions.append("Be more specific about when to use this skill")
    else:
        score += 10  # Partial credit

    # Check length
    length_ok = len(description) <= 1024
    if length_ok:
        score += 10
    else:
        issues.append(f"Description exceeds 1024 characters ({len(description)})")
        suggestions.append("Shorten description to comply with AgentSkills spec")

    # Detect negative trigger clause (coaching only, not scored)
    # Positive signal: description explicitly says when NOT to use the skill
    _NEGATIVE_TRIGGER_PATTERNS = [
        'do not use', "don't use", 'not for', 'when not to', 'avoid when',
        'instead use', 'not intended for', 'not designed for',
    ]
    has_negative_trigger = any(
        p in description.lower() for p in _NEGATIVE_TRIGGER_PATTERNS
    )

    return {
        'score': score,
        'trigger_phrases_found': trigger_phrases_found,
        'has_third_person': has_third_person,
        'is_specific': is_specific,
        'length_ok': length_ok,
        'has_negative_trigger': has_negative_trigger,
        'issues': issues,
        'suggestions': suggestions
    }


def calculate_overall_score(conciseness, complexity, spec_compliance, progressive, description_quality=None):
    """Calculate weighted overall score

    Weights without description quality:
    - Conciseness: 0.25
    - Complexity: 0.20
    - Spec Compliance: 0.35
    - Progressive Disclosure: 0.20

    Weights with description quality (v5.0.0+):
    - Conciseness: 0.20
    - Complexity: 0.20
    - Spec Compliance: 0.30
    - Progressive Disclosure: 0.20
    - Description Quality: 0.10
    """
    if description_quality:
        overall = (
            conciseness['score'] * 0.20 +
            complexity['score'] * 0.20 +
            spec_compliance['score'] * 0.30 +
            progressive['score'] * 0.20 +
            description_quality['score'] * 0.10
        )
    else:
        # Legacy calculation for backward compatibility
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
    dir_name = Path(skill_path).resolve().name

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
    Validate file references use relative paths and follow best practices.
    Checks for:
    - Absolute paths (should use relative)
    - Orphaned reference files (exist but not mentioned in SKILL.md)
    - Missing reference files (mentioned but don't exist)
    - Improper file naming (should be snake_case.md)

    Returns: {
        'valid': bool,
        'issues': [str],
        'warnings': [str],
        'summary': {
            'referenced_files': [str],
            'orphaned_files': [str],
            'missing_files': [str]
        }
    }
    """
    issues = []
    warnings = []
    referenced_files = []
    orphaned_files = []
    missing_files = []

    skill_path = Path(skill_path)
    refs_dir = skill_path / 'references'

    # Check for absolute paths — strip code blocks first to avoid false positives
    import re as _re
    _body_no_code = _re.sub(r'```.*?```', '', body, flags=_re.DOTALL)
    _body_no_code = _re.sub(r'`[^`\n]+`', '', _body_no_code)
    if '/Users/' in _body_no_code or '/home/' in _body_no_code or 'C:\\' in _body_no_code:
        issues.append("Found absolute paths in SKILL.md; use relative paths")

    # Extract all referenced files from body
    # Only match actual references (backtick-wrapped), not inline examples
    import re
    reference_pattern = r'`references/([a-z0-9_-]+\.md)`'
    matches = re.findall(reference_pattern, body)
    referenced_files = list(set(matches))  # Deduplicate

    # Check if referenced files exist
    for ref_file in referenced_files:
        ref_path = refs_dir / ref_file
        if not ref_path.exists():
            missing_files.append(ref_file)
            issues.append(f"Referenced file does not exist: `references/{ref_file}`")

    # Find orphaned reference files (exist but not mentioned)
    if refs_dir.exists():
        for ref_file in refs_dir.glob('*.md'):
            filename = ref_file.name
            if filename not in referenced_files and not filename.startswith('.'):
                orphaned_files.append(filename)
                warnings.append(f"Orphaned reference file not mentioned in SKILL.md: `references/{filename}`")

            # Check naming convention (should be snake_case.md)
            if not re.match(r'^[a-z0-9_-]+\.md$', filename):
                warnings.append(f"Reference file should use snake_case naming: {filename} → {filename.lower().replace(' ', '_').replace('-', '_')}")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'summary': {
            'referenced_files': referenced_files,
            'orphaned_files': orphaned_files,
            'missing_files': missing_files
        }
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
        all_violations.extend(file_refs['issues'])  # Errors/violations
    all_warnings.extend(file_refs['warnings'])  # Warnings only

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


def validate_reference_catalog(skill_path):
    """
    Validate that all reference files are mentioned in SKILL.md (validation-based approach)

    Returns: {
        'all_mentioned': bool,  # True if all references are mentioned in SKILL.md
        'orphaned_refs': [str],  # Reference files not mentioned in SKILL.md
        'total_refs': int,  # Total number of reference files
        'issues': [str]
    }
    """
    refs_dir = skill_path / 'references'

    if not refs_dir.exists():
        return {
            'all_mentioned': True,
            'orphaned_refs': [],
            'total_refs': 0,
            'issues': []
        }

    # Get actual reference files
    actual_refs = [
        f.name for f in refs_dir.glob('*.md')
        if f.is_file() and not f.name.startswith('.')
    ]

    if not actual_refs:
        return {
            'all_mentioned': True,
            'orphaned_refs': [],
            'total_refs': 0,
            'issues': []
        }

    # Check if SKILL.md exists
    skill_md_path = skill_path / 'SKILL.md'
    if not skill_md_path.exists():
        return {
            'all_mentioned': False,
            'orphaned_refs': actual_refs,
            'total_refs': len(actual_refs),
            'issues': ['SKILL.md not found - cannot validate reference mentions']
        }

    # Read SKILL.md content
    try:
        with open(skill_md_path, 'r', encoding='utf-8') as f:
            skill_content = f.read()
    except Exception as e:
        return {
            'all_mentioned': False,
            'orphaned_refs': actual_refs,
            'total_refs': len(actual_refs),
            'issues': [f'Error reading SKILL.md: {str(e)}']
        }

    # Check which references are mentioned in SKILL.md
    def _ref_is_mentioned(content: str, ref: str) -> bool:
        patterns = [
            f'`references/{ref}`',
            f'references/{ref}',
            f'`{ref}`',
        ]
        if any(p in content for p in patterns):
            return True
        # Also match markdown link syntax: [any text](references/filename.md)
        return bool(re.search(rf'\(references/{re.escape(ref)}\)', content))

    orphaned_refs = []
    for ref in actual_refs:
        if not _ref_is_mentioned(skill_content, ref):
            orphaned_refs.append(ref)

    # Build result
    issues = []
    if orphaned_refs:
        issues.append(f'Reference files not mentioned in SKILL.md: {", ".join(orphaned_refs)}')

    return {
        'all_mentioned': len(orphaned_refs) == 0,
        'orphaned_refs': orphaned_refs,
        'total_refs': len(actual_refs),
        'issues': issues
    }


def detect_duplicate_references(skill_path):
    """
    Detect consolidation opportunities in references/ using Jaccard similarity.

    Ported from update_references.py detect_similar_references().

    Returns: list of dicts:
        [{
            'files': [str, str],
            'similarity': float,   # percentage
            'recommendation': str
        }]
    """
    refs_dir = Path(skill_path) / 'references'
    if not refs_dir.exists():
        return []

    def _tokenize(text):
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-_]{2,}\b', text.lower())
        common = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'about',
                  'how', 'what', 'when', 'where', 'which', 'who', 'will', 'can',
                  'are', 'was', 'were', 'been', 'have', 'has', 'had', 'does', 'did'}
        return set(w for w in words if w not in common)

    def _jaccard(a, b):
        union = a | b
        return len(a & b) / len(union) if union else 0.0

    # Build token sets from headings + first paragraph of each ref file
    tokens_by_file = {}
    for ref_file in sorted(refs_dir.glob('*.md')):
        if ref_file.name.startswith('.'):
            continue
        try:
            content = ref_file.read_text(encoding='utf-8')
        except Exception:
            continue
        headings = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
        paras = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        text = ' '.join(headings) + ' ' + (paras[0][:300] if paras else '')
        tokens_by_file[ref_file.name] = _tokenize(text)

    filenames = list(tokens_by_file.keys())
    clusters = []
    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            sim = _jaccard(tokens_by_file[filenames[i]], tokens_by_file[filenames[j]])
            if sim > 0.70:
                rec = ('High priority consolidation (likely duplicates)' if sim > 0.90
                       else 'Review for overlapping content')
                clusters.append({
                    'files': [filenames[i], filenames[j]],
                    'similarity': round(sim * 100, 1),
                    'recommendation': rec
                })

    clusters.sort(key=lambda x: x['similarity'], reverse=True)
    return clusters


def _extract_improvement_plan_sections(skill_path):
    """
    Extract version history table and active work from IMPROVEMENT_PLAN.md.

    Returns: {
        'version_table': str,   # raw markdown table block (empty string if not found)
        'active_work': str,     # raw active work list (empty string if not found)
        'metric_legend': str,   # legend line (empty string if not found)
    }
    """
    ip_path = Path(skill_path) / 'IMPROVEMENT_PLAN.md'
    if not ip_path.exists():
        return {'version_table': '', 'active_work': '', 'metric_legend': ''}

    content = ip_path.read_text(encoding='utf-8')

    # Extract Version History table (from "## Version History" to next "##")
    version_table = ''
    table_match = re.search(
        r'## Version History\s*\n(.*?)(?=\n## |\Z)',
        content, re.DOTALL
    )
    if table_match:
        version_table = table_match.group(1).strip()

    # Extract metric legend line
    metric_legend = ''
    legend_match = re.search(r'\*\*Metric Legend:.*?\*\*', content)
    if legend_match:
        metric_legend = legend_match.group(0)

    # Extract Active Work section
    active_work = ''
    active_match = re.search(
        r'## Active Work\s*\n(.*?)(?=\n## |\Z)',
        content, re.DOTALL
    )
    if active_match:
        active_work = active_match.group(1).strip()

    return {
        'version_table': version_table,
        'active_work': active_work,
        'metric_legend': metric_legend,
    }


def _interp(score):
    """Interpret a metric score as a human-readable label."""
    if score >= 95:
        return 'Excellent'
    elif score >= 80:
        return 'Good'
    elif score >= 60:
        return 'Fair'
    return 'Needs work'


def _generate_metrics_content(metrics, today):
    """
    Generate the body of the Current Metrics section (everything after the heading line).
    Compact format: one-line summary + horizontal detail table.
    Starts with \\n\\n and ends with \\n (single newline, no trailing blank line).
    """
    conc = metrics['conciseness']['score']
    comp = metrics['complexity']['score']
    spec = metrics['spec_compliance']['score']
    disc = metrics['progressive_disclosure']['score']
    desc_q = metrics.get('description_quality', {}).get('score', '-')
    overall = metrics['overall_score']

    desc_val = str(int(desc_q)) if desc_q != '-' else '-'

    return (
        f'\n\n**Score: {overall}/100** ({_interp(overall)}) — {today}\n\n'
        '| Concs | Complx | Spec | Progr | Descr |\n'
        '|-------|--------|------|-------|-------|\n'
        f'| {conc} | {comp} | {spec} | {disc} | {desc_val} |\n'
    )


def _update_current_metrics_section(content, metrics_content):
    """
    Replace the ## Current Metrics section body in existing README.md.
    Preserves all other sections verbatim. If section not found, inserts before footer.

    metrics_content: return value of _generate_metrics_content (starts \\n\\n, ends \\n)
    """
    # Match heading (at start of line) + body up to next ## section, --- separator, or end of file
    # (?ms) = MULTILINE (^ matches start of line) + DOTALL (. matches newlines)
    pattern = r'(?ms)^(## Current Metrics)(.*?)(?=\n## |\n---|\Z)'
    updated, n = re.subn(
        pattern,
        lambda m: m.group(1) + metrics_content,
        content
    )
    if n == 0:
        # Section not found — insert before footer separator or append
        sep = '\n\n---\n'
        if sep in content:
            idx = content.rfind(sep)
            updated = content[:idx] + '\n\n## Current Metrics' + metrics_content + content[idx:]
        else:
            updated = content.rstrip('\n') + '\n\n## Current Metrics' + metrics_content
    return updated


def generate_skill_readme(skill_path, metrics):
    """
    Generate or update README.md content for a skill.

    If README.md already exists: only the ## Current Metrics section is replaced
    (idempotent — all other sections are preserved verbatim).

    If README.md does not exist: generates a full document from scratch using
    SKILL.md frontmatter and IMPROVEMENT_PLAN.md version history (migration path).

    Args:
        skill_path: Path to skill directory
        metrics: dict from calculate_all_metrics()

    Returns:
        str: Complete README.md content
    """
    sp = Path(skill_path)
    today = datetime.now().strftime('%Y-%m-%d')
    metrics_content = _generate_metrics_content(metrics, today)

    # IDEMPOTENT PATH: if README.md already exists, only refresh ## Current Metrics
    readme_path = sp / 'README.md'
    if readme_path.exists():
        existing = readme_path.read_text(encoding='utf-8')
        return _update_current_metrics_section(existing, metrics_content)

    # FIRST-TIME GENERATION: build full document from SKILL.md + IMPROVEMENT_PLAN.md
    frontmatter, body, _ = read_skill_md(sp)
    fm = parse_frontmatter(frontmatter)

    skill_name = fm.get('name', sp.name)
    description = fm.get('description', '')
    when_to_use = fm.get('when_to_use', '')

    # Pull version history from IMPROVEMENT_PLAN.md if present
    ip_sections = _extract_improvement_plan_sections(sp)

    lines = [f"# {skill_name}", '']

    # Capabilities section — use description as prose
    if description:
        # Strip "This skill should be used when..." prefix for cleaner prose
        prose = re.sub(
            r'^This skill should be used when[^.]*\.\s*',
            '',
            description,
            flags=re.IGNORECASE
        ).strip()
        lines += ['## Capabilities', '', prose or description, '']
    elif when_to_use:
        lines += ['## Capabilities', '', when_to_use, '']

    # Metrics section (inline for consistent list-building in fresh-gen path)
    conc = metrics['conciseness']['score']
    comp = metrics['complexity']['score']
    spec = metrics['spec_compliance']['score']
    disc = metrics['progressive_disclosure']['score']
    desc_q = metrics.get('description_quality', {}).get('score', '-')
    overall = metrics['overall_score']

    def _interp(score):
        if score >= 95:
            return 'Excellent'
        elif score >= 80:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        return 'Needs work'

    lines += [
        '## Current Metrics',
        '',
        f'*Last evaluated: {today}*',
        '',
        '| Metric | Score | Interpretation |',
        '|--------|-------|----------------|',
        f'| Conciseness | {conc}/100 | {_interp(conc)} |',
        f'| Complexity | {comp}/100 | {_interp(comp)} |',
        f'| Spec Compliance | {spec}/100 | {_interp(spec)} |',
        f'| Progressive Disclosure | {disc}/100 | {_interp(disc)} |',
    ]
    if desc_q != '-':
        lines.append(f'| Description Quality | {desc_q}/100 | {_interp(int(desc_q))} |')
    lines += [
        f'| **Overall** | **{overall}/100** | **{_interp(overall)}** |',
        '',
        'Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.',
        '',
    ]

    # Version history from IMPROVEMENT_PLAN.md
    if ip_sections['version_table']:
        lines += ['## Version History', '', ip_sections['version_table'], '']

    # Active work from IMPROVEMENT_PLAN.md
    if ip_sections['active_work']:
        lines += ['## Active Work', '', ip_sections['active_work'], '']

    lines += [
        '---',
        '',
        f'*Generated by skillsmith on {today}. '
        'Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh.*',
    ]

    return '\n'.join(lines) + '\n'


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
    reference_catalog = validate_reference_catalog(skill_path)

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
        'reference_catalog': reference_catalog,
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
    conciseness['qualitative_warnings'] = check_qualitative_conciseness(skill_path, body)
    spec_compliance = calculate_spec_compliance_score(frontmatter_dict, basic)
    # Warn if legacy IMPROVEMENT_PLAN.md exists without README.md
    if (skill_path / 'IMPROVEMENT_PLAN.md').exists() and not (skill_path / 'README.md').exists():
        spec_compliance['warnings'].append(
            "IMPROVEMENT_PLAN.md found without README.md — "
            "run /ss-improve to migrate to README.md format"
        )
    progressive = calculate_progressive_disclosure_score(basic)
    description_quality = validate_description_quality(frontmatter_dict)
    overall = calculate_overall_score(conciseness, complexity, spec_compliance, progressive, description_quality)

    return {
        'skill_name': frontmatter_dict.get('name', skill_path.name),
        'basic_metrics': basic,
        'conciseness': conciseness,
        'complexity': complexity,
        'spec_compliance': spec_compliance,
        'progressive_disclosure': progressive,
        'description_quality': description_quality,
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

def apply_strict_mode(validation_result, strict_enabled):
    """
    Apply strict mode: treat warnings as errors if strict_enabled

    In strict mode:
    - Warnings are moved to errors
    - Overall validation result becomes invalid if warnings exist
    - Used for pre-release quality gates
    """
    if not strict_enabled:
        return validation_result

    # Collect all warnings from different validation stages
    all_warnings = []

    # PEP 723 warnings
    if 'pep723' in validation_result and validation_result['pep723'].get('warnings'):
        all_warnings.extend(validation_result['pep723']['warnings'])

    # Only treat warnings as errors if strict mode is enabled
    if all_warnings:
        # Mark result as invalid if warnings exist in strict mode
        validation_result['strict_mode_warnings'] = all_warnings
        validation_result['valid'] = False
        validation_result['structure']['valid'] = False

    return validation_result


def print_quick_validation_text(validation_result, strict_mode=False):
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

    # PEP 723 validation
    if 'pep723' in validation_result:
        pep723 = validation_result['pep723']

        if pep723['issues']:
            print()
            print("❌ PEP 723 ISSUES:")
            for issue in pep723['issues']:
                print(issue)
            sys.exit(1)

        if pep723['warnings']:
            print()
            if strict_mode:
                print("❌ STRICT MODE: PEP 723 WARNINGS TREATED AS ERRORS")
                for warning in pep723['warnings']:
                    print(f"  ✗ {warning}")
            else:
                print("⚠️  PEP 723 WARNINGS:")
                for warning in pep723['warnings']:
                    print(warning)

    # Strict mode warnings (converted to errors)
    if 'strict_mode_warnings' in validation_result and validation_result['strict_mode_warnings']:
        print()
        print("❌ STRICT MODE: WARNINGS TREATED AS ERRORS")
        for warning in validation_result['strict_mode_warnings']:
            print(f"  ✗ {warning}")
        sys.exit(1)

    # Exit with appropriate code based on validation results
    if not validation_result.get('valid', True):
        sys.exit(1)

    sys.exit(0)


def format_score_bar(score, width=20):
    """Format score as visual bar"""
    filled = int((score / 100) * width)
    empty = width - filled
    bar = '█' * filled + '░' * empty
    return f"[{bar}] {score}/100"


def print_explain_output(evaluation):
    """Print per-metric coaching output with actionable improvement suggestions.

    Template (from #37 spec):
      <Metric> Score: <N>/100

        Why: <reason>

        To improve:
        - <specific action>

        See: <reference file if relevant>

    Followed by a Top-3 improvements summary with estimated overall score delta.
    """
    metrics = evaluation['metrics']
    basic = metrics['basic_metrics']
    overall = int(metrics['overall_score'])

    print(f"\n{'='*60}")
    print(f"Skill Evaluation: {metrics['skill_name']} — Explain Mode")
    print(f"{'='*60}\n")

    # Brief score overview
    print("Quality Scores:")
    print(f"  Conciseness:     {format_score_bar(metrics['conciseness']['score'])}")
    print(f"  Complexity:      {format_score_bar(metrics['complexity']['score'])}")
    print(f"  Spec Compliance: {format_score_bar(metrics['spec_compliance']['score'])}")
    print(f"  Progressive:     {format_score_bar(metrics['progressive_disclosure']['score'])}")
    if 'description_quality' in metrics:
        print(f"  Description:     {format_score_bar(metrics['description_quality']['score'])}")
    print(f"  Overall:         {format_score_bar(overall)}")
    print()

    improvements = []  # list of (delta_overall, label)

    # ── CONCISENESS ──────────────────────────────────────────────────────────
    conc = metrics['conciseness']
    conc_score = conc['score']
    lines = basic['skill_md_lines']
    tokens = basic['skill_md_tokens']
    ref_lines = basic['references_lines']

    print(f"Conciseness Score: {conc_score}/100\n")
    print("  Why:")
    if lines <= 150:
        print(f"    SKILL.md is {lines} lines — excellent (≤150 target ✓)")
    elif lines <= 250:
        print(f"    SKILL.md is {lines} lines — within ≤250 recommended range")
    elif lines <= 350:
        print(f"    SKILL.md is {lines} lines — slightly over ≤250 recommended range")
    elif lines <= 500:
        print(f"    SKILL.md is {lines} lines — approaching 500-line max")
    else:
        print(f"    SKILL.md is {lines} lines — over 500-line max")

    if tokens <= 1500:
        print(f"    Tokens: ~{tokens} — excellent (≤1500 target ✓)")
    elif tokens <= 2000:
        print(f"    Tokens: ~{tokens} — within ≤2000 max")
    else:
        print(f"    Tokens: ~{tokens} — over 2000-token max")
    print()

    conc_gap = 100 - conc_score
    if conc_gap > 0:
        print("  To improve:")
        if lines > 150:
            over = lines - 150
            print(f"    - Move supplemental content to references/ to reduce by ~{over} lines")
            print(f"      (target: ≤150 lines for max line score)")
        if tokens > 1500:
            print(f"    - Reduce prose density; aim for ≤1500 tokens (currently ~{tokens})")
        if ref_lines <= 500:
            print(f"    - references/ content >500 lines earns a +5 bonus (currently {ref_lines})")
        delta = int(conc_gap * 0.20)
        if delta > 0:
            improvements.append((delta, f"Reduce SKILL.md length/tokens → +{delta} overall"))
    else:
        print("  ✓ Nothing to improve — already at 100")

    qual_warnings = conc.get('qualitative_warnings', [])
    if qual_warnings:
        print()
        print("  Qualitative findings (informational — not scored):")
        for w in qual_warnings:
            print(f"    {w}")
    print()

    # ── COMPLEXITY ───────────────────────────────────────────────────────────
    comp = metrics['complexity']
    comp_score = comp['score']
    section_count = comp['section_count']
    max_depth = comp['max_nesting_depth']
    code_blocks = comp['code_blocks']

    # Reconstruct sub-scores for the "Why" explanation
    if section_count <= 5:
        section_sub = 40
    elif section_count <= 10:
        section_sub = 30
    else:
        section_sub = max(0, 30 - (section_count - 10) * 2)

    if max_depth <= 3:
        depth_sub = 30
    elif max_depth <= 5:
        depth_sub = 20
    else:
        depth_sub = max(0, 20 - (max_depth - 5) * 5)

    if 2 <= code_blocks <= 10:
        code_sub = 30
    elif code_blocks < 2:
        code_sub = 20
    else:
        code_sub = max(0, 30 - (code_blocks - 10))

    print(f"Complexity Score: {comp_score}/100\n")
    print("  Why:")
    print(f"    Sections (H1/H2): {section_count}  → {section_sub}/40 pts")
    print(f"    Max nesting depth: {max_depth}      → {depth_sub}/30 pts")
    print(f"    Code blocks: {code_blocks}           → {code_sub}/30 pts")
    print()

    comp_gap = 100 - comp_score
    if comp_gap > 0:
        print("  To improve:")
        if section_count > 10:
            print(f"    - Merge or flatten sections (currently {section_count}; target ≤10 for 30 pts)")
        if max_depth > 3:
            print(f"    - Reduce heading nesting (currently depth {max_depth}; target ≤3 for 30 pts)")
        if code_blocks < 2:
            print(f"    - Add at least 2 code examples (currently {code_blocks}; 2-10 earns 30 pts)")
        elif code_blocks > 10:
            print(f"    - Move code-heavy content to references/ (currently {code_blocks} blocks)")
        delta = int(comp_gap * 0.20)
        if delta > 0:
            improvements.append((delta, f"Fix complexity sub-scores → +{delta} overall"))
    else:
        print("  ✓ Nothing to improve — already at 100")
    print()

    # ── SPEC COMPLIANCE ──────────────────────────────────────────────────────
    spec = metrics['spec_compliance']
    spec_score = spec['score']

    print(f"Spec Compliance Score: {spec_score}/100\n")
    print("  Why:")
    print(f"    Required frontmatter: {spec['required_fields_present']}")
    print(f"    Recommended frontmatter: {spec['recommended_fields_present']}")
    for v in spec['violations']:
        print(f"    ✗ {v}")
    for w in spec['warnings']:
        print(f"    ⚠ {w}")
    print()

    spec_gap = 100 - spec_score
    if spec_gap > 0:
        print("  To improve:")
        for v in spec['violations']:
            print(f"    - Fix violation: {v}")
        for w in spec['warnings']:
            print(f"    - Address warning: {w}")
        delta = int(spec_gap * 0.30)
        if delta > 0:
            improvements.append((delta, f"Fix spec violations/warnings → +{delta} overall"))
    else:
        print("  ✓ Nothing to improve — already at 100")
    print()

    # ── PROGRESSIVE DISCLOSURE ───────────────────────────────────────────────
    prog = metrics['progressive_disclosure']
    prog_score = prog['score']

    print(f"Progressive Disclosure Score: {prog_score}/100\n")
    print("  Why:")
    if prog['issues']:
        for issue in prog['issues']:
            print(f"    - {issue}")
    else:
        uses = []
        if prog['uses_scripts']:
            uses.append("scripts")
        if prog['uses_references']:
            uses.append("references")
        if prog['uses_assets']:
            uses.append("assets")
        layer_str = ", ".join(uses) if uses else "none"
        print(f"    Layered content ({layer_str}) — no issues detected")
    print()

    prog_gap = 100 - prog_score
    if prog_gap > 0:
        print("  To improve:")
        for issue in prog['issues']:
            if "Very long" in issue:
                print("    - Create references/ directory and move supporting content there")
            elif "Moderate length" in issue:
                print("    - Consider splitting verbose sections into references/ or scripts/")
            elif "too thin" in issue:
                print("    - Add more reference files (aim for ≥100 lines across ≥2 files)")
            else:
                print(f"    - {issue}")
        delta = int(prog_gap * 0.20)
        if delta > 0:
            improvements.append((delta, f"Improve disclosure layering → +{delta} overall"))
    else:
        print("  ✓ Nothing to improve — already at 100")
    print()

    # ── DESCRIPTION QUALITY ──────────────────────────────────────────────────
    if 'description_quality' in metrics:
        desc = metrics['description_quality']
        desc_score = desc['score']
        phrases = desc.get('trigger_phrases_found', [])

        print(f"Description Quality Score: {desc_score}/100\n")
        print("  Why:")
        if phrases:
            sample = ', '.join(f'"{p}"' for p in phrases[:3])
            print(f"    Trigger phrases ({len(phrases)} found): {sample}")
        else:
            print("    No trigger phrases found (need ≥3 quoted action phrases for full score)")
        print(f"    Third-person format: {'✓' if desc.get('has_third_person') else '✗'}")
        print(f"    Specific scenarios: {'✓' if desc.get('is_specific') else '✗'}")
        print(f"    Under 1024 chars: {'✓' if desc.get('length_ok') else '✗'}")
        # Negative trigger coaching (not scored)
        if desc.get('has_negative_trigger'):
            print("    Negative trigger clause: ✓ (prevents overtriggering)")
        else:
            print("    Negative trigger clause: ✗ (missing — consider adding)")
        for issue in desc.get('issues', []):
            print(f"    ✗ {issue}")

        # Over/undertrigger diagnostic signals
        num_phrases = len(phrases)
        phrase_lengths = [len(p.split()) for p in phrases] if phrases else []
        if num_phrases < 2 or (phrase_lengths and all(n <= 2 for n in phrase_lengths)):
            print("    ⚠ Undertrigger risk: too few or too narrow trigger phrases")
            print("      → Add more specific quoted phrases or expand short phrases with domain nouns")
        elif num_phrases >= 8:
            print("    ⚠ Overtrigger risk: many trigger phrases may cause broad matching")
            print("      → Narrow scope with a 'Do NOT use for X (use Y instead)' clause")
        print()

        desc_gap = 100 - desc_score
        if desc_gap > 0:
            print("  To improve:")
            for suggestion in desc.get('suggestions', []):
                print(f"    - {suggestion}")
            if not desc.get('has_third_person'):
                print('    - Start description with: "This skill should be used when..."')
            if not desc.get('is_specific'):
                print("    - Add concrete scenarios rather than vague capability descriptions")
            if not desc.get('length_ok'):
                print("    - Trim description to under 1024 characters")
            if not desc.get('has_negative_trigger'):
                print('    - Add a negative trigger: "Do NOT use for X (use Y skill instead)"')
            delta = int(desc_gap * 0.10)
            if delta > 0:
                improvements.append((delta, f"Improve description quality → +{delta} overall"))
        else:
            # Still surface negative trigger coaching even at 100
            if not desc.get('has_negative_trigger'):
                print("  To improve:")
                print('    - Add a negative trigger clause: "Do NOT use for X (use Y skill instead)"')
                print("      (no score impact — prevents overtriggering in multi-skill environments)")
                print()
            else:
                print("  ✓ Nothing to improve — already at 100")
        print()

    # ── TOP-3 SUMMARY ─────────────────────────────────────────────────────────
    improvements.sort(reverse=True)
    print(f"{'='*60}")
    print("Top improvements:")
    if not improvements:
        print("  ✓ All metrics at 100 — no improvements needed")
    else:
        for i, (delta, label) in enumerate(improvements[:3], 1):
            print(f"  {i}. {label}")
        total_delta = sum(d for d, _ in improvements[:3])
        estimated = min(100, overall + total_delta)
        print(f"\n  Estimated overall: {overall} → {estimated}")
    print()


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
    if 'description_quality' in metrics:
        print(f"  Description:     {format_score_bar(metrics['description_quality']['score'])}")
    print(f"  Overall:         {format_score_bar(metrics['overall_score'])}")
    print()

    # Description Quality Details
    if 'description_quality' in metrics:
        desc_q = metrics['description_quality']
        if desc_q['trigger_phrases_found']:
            print(f"Trigger Phrases Found: {len(desc_q['trigger_phrases_found'])}")
            for phrase in desc_q['trigger_phrases_found'][:5]:  # Show up to 5
                print(f"  - \"{phrase}\"")
        if desc_q['issues']:
            print("\n⚠ Description Issues:")
            for issue in desc_q['issues']:
                print(f"  - {issue}")
        if desc_q['suggestions']:
            print("\n💡 Suggestions:")
            for suggestion in desc_q['suggestions']:
                print(f"  - {suggestion}")
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
# Remote URL Resolution
# ============================================================================

def resolve_remote_skill(url):
    """
    Resolve a remote GitLab/GitHub URL to a local path by cloning the repo.

    Supports URLs like:
      - https://code.pan.run/user/repo/-/tree/branch/skills/skill-name?ref_type=heads
      - https://github.com/user/repo/tree/branch/skills/skill-name

    Returns: Path to the local skill directory
    Raises: SystemExit on failure
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    path_parts = parsed.path.strip('/').split('/')

    # Determine clone tool and parse URL structure
    if hostname and 'github.com' in hostname:
        clone_cmd = 'gh'
        # github.com/user/repo/tree/branch/path/to/skill
        if len(path_parts) < 4 or path_parts[2] != 'tree':
            print(f"❌ Error: Cannot parse GitHub URL: {url}", file=sys.stderr)
            print("  Expected format: https://github.com/user/repo/tree/branch/path/to/skill", file=sys.stderr)
            sys.exit(1)
        repo_slug = f"{path_parts[0]}/{path_parts[1]}"
        branch = path_parts[3]
        skill_subpath = '/'.join(path_parts[4:])
    elif hostname and hostname.endswith(('.pan.run',)):
        clone_cmd = 'glab'
        # code.pan.run/user/repo/-/tree/branch/path/to/skill
        if len(path_parts) < 5 or path_parts[2] != '-' or path_parts[3] != 'tree':
            print(f"❌ Error: Cannot parse GitLab URL: {url}", file=sys.stderr)
            print("  Expected format: https://code.pan.run/user/repo/-/tree/branch/path/to/skill", file=sys.stderr)
            sys.exit(1)
        repo_slug = f"{path_parts[0]}/{path_parts[1]}"
        branch = path_parts[4]
        skill_subpath = '/'.join(path_parts[5:])
    else:
        print(f"❌ Error: Unsupported remote host: {hostname}", file=sys.stderr)
        print("  Supported: github.com, *.pan.run (GitLab)", file=sys.stderr)
        sys.exit(1)

    # Strip query params from skill subpath (e.g., ?ref_type=heads)
    if '?' in skill_subpath:
        skill_subpath = skill_subpath.split('?')[0]

    # Create temp directory and register cleanup
    tmp_dir = tempfile.mkdtemp(prefix='skill-eval-')
    atexit.register(shutil.rmtree, tmp_dir, ignore_errors=True)

    clone_target = os.path.join(tmp_dir, 'repo')

    # Clone with sparse checkout for efficiency
    if clone_cmd == 'gh':
        cmd = ['gh', 'repo', 'clone', repo_slug, clone_target, '--', '--depth', '1', '--branch', branch, '--sparse']
    else:
        cmd = ['glab', 'repo', 'clone', repo_slug, clone_target, '--', '--depth', '1', '--branch', branch, '--sparse']

    print(f"Cloning {repo_slug} (branch: {branch})...", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: Clone failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    # Set sparse checkout to only the skill subdirectory
    if skill_subpath:
        sparse_result = subprocess.run(
            ['git', 'sparse-checkout', 'set', skill_subpath],
            cwd=clone_target, capture_output=True, text=True
        )
        if sparse_result.returncode != 0:
            print(f"❌ Error: Sparse checkout failed: {sparse_result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)

    local_skill_path = os.path.join(clone_target, skill_subpath) if skill_subpath else clone_target

    if not os.path.isdir(local_skill_path):
        print(f"❌ Error: Skill directory not found after clone: {local_skill_path}", file=sys.stderr)
        sys.exit(1)

    skill_md = os.path.join(local_skill_path, 'SKILL.md')
    if not os.path.isfile(skill_md):
        print(f"❌ Error: No SKILL.md found at {local_skill_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Resolved remote skill to: {local_skill_path}", file=sys.stderr)
    return local_skill_path


def is_remote_url(path):
    """Check if the given path is a remote URL."""
    return path.startswith(('https://', 'http://'))


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main entry point"""
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv or '-h' in sys.argv else 1)

    skill_path = sys.argv[1]

    # Resolve remote URLs to local paths
    if is_remote_url(skill_path):
        skill_path = resolve_remote_skill(skill_path)
    quick_mode = False
    strict_mode = False
    check_improvement_plan = False
    explain_mode = False
    validate_refs_mode = False
    detect_dups_mode = False
    update_readme_mode = False
    compare_with = None
    validate_func = False
    store_metrics_flag = False
    export_table_row = False
    version_number = None
    issue_number = None
    output_format = 'text'
    output_file = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--quick':
            quick_mode = True
            i += 1
        elif arg == '--strict':
            strict_mode = True
            i += 1
        elif arg == '--check-improvement-plan':
            check_improvement_plan = True
            i += 1
        elif arg == '--explain':
            explain_mode = True
            i += 1
        elif arg == '--validate-references':
            validate_refs_mode = True
            i += 1
        elif arg == '--detect-duplicates':
            detect_dups_mode = True
            i += 1
        elif arg == '--update-readme':
            update_readme_mode = True
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
        elif arg == '--export-table-row':
            export_table_row = True
            i += 1
        elif arg == '--version' and i + 1 < len(sys.argv):
            version_number = sys.argv[i + 1]
            i += 2
        elif arg == '--issue' and i + 1 < len(sys.argv):
            issue_number = sys.argv[i + 1]
            i += 2
        elif arg == '--format' and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        elif arg == '--output' and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)

    # Validate flag compatibility
    if explain_mode and quick_mode:
        print("❌ Error: --explain is incompatible with --quick (explain requires full evaluation)")
        sys.exit(1)

    try:
        # Export table row mode
        if export_table_row:
            if not version_number:
                print("❌ Error: --export-table-row requires --version <version>")
                sys.exit(1)

            # Calculate metrics
            metrics = calculate_all_metrics(skill_path)

            # Get today's date
            today = datetime.now().strftime("%Y-%m-%d")

            # Format issue link or dash
            if issue_number:
                # Try to detect GitHub repo URL from git remote
                try:
                    git_remote = subprocess.run(
                        ['git', 'config', '--get', 'remote.origin.url'],
                        capture_output=True,
                        text=True,
                        cwd=Path(skill_path).parent if Path(skill_path).is_file() else skill_path
                    )
                    if git_remote.returncode == 0:
                        remote_url = git_remote.stdout.strip()
                        # Convert git@github.com:user/repo.git to https://github.com/user/repo
                        if remote_url.startswith('git@github.com:'):
                            repo_path = remote_url.replace('git@github.com:', '').replace('.git', '')
                            github_url = f"https://github.com/{repo_path}"
                        elif 'github.com' in remote_url:
                            github_url = remote_url.replace('.git', '')
                        else:
                            github_url = "https://github.com/user/repo"
                        issue_link = f"[#{issue_number}]({github_url}/issues/{issue_number})"
                    else:
                        issue_link = f"[#{issue_number}](link)"
                except:
                    issue_link = f"[#{issue_number}](link)"
            else:
                issue_link = "-"

            # Get skill name for summary (use last part of path as default)
            skill_name = metrics.get('skill_name', Path(skill_path).name)
            summary = f"{skill_name} v{version_number}"

            # Extract metric scores
            conc = int(metrics['conciseness']['score'])
            comp = int(metrics['complexity']['score'])
            spec = int(metrics['spec_compliance']['score'])
            disc = int(metrics['progressive_disclosure']['score'])
            desc_q = metrics.get('description_quality', {}).get('score', '-')
            desc_str = str(int(desc_q)) if desc_q != '-' else '-'
            overall = int(metrics['overall_score'])

            # Output table row for Version History (plugin-level README.md)
            table_row = f"| {version_number} | {today} | {issue_link} | {summary} | {conc} | {comp} | {spec} | {disc} | {desc_str} | {overall} |"
            print(table_row)
            sys.exit(0)

        # Validate references mode
        if validate_refs_mode:
            sp = Path(skill_path)
            _, body, _ = read_skill_md(sp)
            ref_result = validate_file_references(sp, body)
            structure = {'issues': [], 'warnings': []}
            refs_dir = sp / 'references'
            if refs_dir.exists():
                for item in refs_dir.rglob('*'):
                    if item.is_dir():
                        structure['issues'].append(
                            f"Nested subdirectory not allowed: {item.relative_to(refs_dir)}"
                        )
                for ref_file in refs_dir.glob('*.md'):
                    try:
                        size_kb = len(ref_file.read_text(encoding='utf-8').encode()) / 1024
                        if size_kb > 100:
                            structure['warnings'].append(
                                f"{ref_file.name}: Large file ({size_kb:.1f} KB)"
                            )
                    except Exception as e:
                        structure['issues'].append(f"{ref_file.name}: Cannot read — {e}")
            all_ok = (ref_result['valid'] and not structure['issues']
                      and not ref_result['summary']['orphaned_files']
                      and not ref_result['summary']['missing_files'])
            print(f"\nReference Validation: {sp.name}")
            print(f"{'='*40}")
            if ref_result['summary']['orphaned_files']:
                print("\n⚠ Orphaned references (exist but not mentioned in SKILL.md):")
                for f in ref_result['summary']['orphaned_files']:
                    print(f"  - {f}")
            if ref_result['summary']['missing_files']:
                print("\n✗ Missing references (mentioned but not on disk):")
                for f in ref_result['summary']['missing_files']:
                    print(f"  - {f}")
            if structure['issues']:
                print("\n✗ Structure issues:")
                for issue in structure['issues']:
                    print(f"  - {issue}")
            if structure['warnings']:
                print("\n⚠ Warnings:")
                for w in structure['warnings']:
                    print(f"  - {w}")
            if ref_result['issues']:
                print("\n✗ Issues:")
                for issue in ref_result['issues']:
                    print(f"  - {issue}")
            # Filter warnings: omit orphan warnings already shown from summary
            extra_warnings = [w for w in ref_result['warnings'] if 'Orphaned reference' not in w]
            if extra_warnings:
                print("\n⚠ Other warnings:")
                for w in extra_warnings:
                    print(f"  - {w}")
            if all_ok and not ref_result['summary']['orphaned_files']:
                print("✓ All references valid and mentioned in SKILL.md")
            print()
            sys.exit(0 if all_ok else 1)

        # Detect duplicates mode
        if detect_dups_mode:
            sp = Path(skill_path)
            clusters = detect_duplicate_references(sp)
            print(f"\nDuplicate Detection: {sp.name}")
            print(f"{'='*40}")
            if not clusters:
                print("✓ No consolidation opportunities detected")
            else:
                print(f"\nConsolidation Opportunities ({len(clusters)} cluster(s)):\n")
                for i, cluster in enumerate(clusters, 1):
                    print(f"Cluster {i} ({cluster['similarity']}% similar):")
                    for f in cluster['files']:
                        print(f"  - references/{f}")
                    print(f"  Recommendation: {cluster['recommendation']}")
                    print()
            sys.exit(0)

        # Update README mode
        if update_readme_mode:
            sp = Path(skill_path)
            metrics = calculate_all_metrics(sp)
            readme_content = generate_skill_readme(sp, metrics)
            readme_path = sp / 'README.md'
            readme_path.write_text(readme_content, encoding='utf-8')
            print(f"✓ README.md written to {readme_path}")
            print(f"  Overall score: {metrics['overall_score']}/100")
            sys.exit(0)

        # Quick validation mode
        if quick_mode:
            validation_result = quick_validate(skill_path, check_improvement_plan)

            # Apply strict mode if enabled
            if strict_mode:
                validation_result = apply_strict_mode(validation_result, strict_mode)

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
                print_quick_validation_text(validation_result, strict_mode)
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
        elif explain_mode and not export_table_row:
            print_explain_output(evaluation)
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(evaluation, f, indent=2)
                print(f"Detailed results saved to {output_file}")
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
