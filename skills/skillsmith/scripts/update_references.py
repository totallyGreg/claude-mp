#!/usr/bin/env python3
"""
Reference Management Tool for AgentSkills

Scans references/ directory, extracts metadata, detects consolidation opportunities,
and generates/updates REFERENCE.md catalog.

Usage:
    update_references.py <skill-path> [--output REFERENCE.md] [--format markdown|json]
    update_references.py <skill-path> --detect-duplicates
    update_references.py <skill-path> --validate-structure

Features:
    - Scans references/ directory and extracts metadata from each file
    - Generates structured REFERENCE.md catalog
    - Detects similar descriptions signaling consolidation needs
    - Validates references/ directory structure per spec
    - Supports both markdown and JSON output
    - Reusable by other skills (not skillsmith-specific)
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def scan_references_directory(skill_path: Path) -> List[Path]:
    """
    Discover all .md files in references/ directory

    Args:
        skill_path: Path to skill directory

    Returns:
        List of reference file paths (excludes REFERENCE.md itself)
    """
    refs_dir = skill_path / 'references'

    if not refs_dir.exists():
        return []

    # Get all .md files except REFERENCE.md and hidden files
    ref_files = [
        f for f in refs_dir.glob('*.md')
        if f.is_file()
        and f.name != 'REFERENCE.md'
        and not f.name.startswith('.')
    ]

    return sorted(ref_files, key=lambda x: x.name.lower())


def extract_reference_metadata(ref_file_path: Path) -> Dict:
    """
    Extract metadata from a reference file

    Args:
        ref_file_path: Path to reference file

    Returns:
        Dict containing:
            - filename: str
            - title: str (first H1 heading or filename)
            - purpose: str (first paragraph or description)
            - topics: List[str] (keywords from headings)
            - size_kb: float
            - line_count: int
            - key_sections: List[str] (H2 headings)
            - last_modified: str (ISO format date)
    """
    try:
        with open(ref_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {
            'filename': ref_file_path.name,
            'title': ref_file_path.stem,
            'purpose': f'Error reading file: {str(e)}',
            'topics': [],
            'size_kb': 0,
            'line_count': 0,
            'key_sections': [],
            'last_modified': '',
            'error': str(e)
        }

    lines = content.split('\n')
    size_kb = len(content.encode('utf-8')) / 1024

    # Extract title (first H1 heading)
    title = ref_file_path.stem  # Default to filename without extension
    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()

    # Extract purpose (first paragraph after H1, or first paragraph)
    purpose = ''
    # Remove H1 and get first substantial paragraph
    content_without_h1 = re.sub(r'^#\s+.+$', '', content, count=1, flags=re.MULTILINE)
    paragraphs = [p.strip() for p in content_without_h1.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    if paragraphs:
        purpose = paragraphs[0][:200]  # First 200 chars
        # Clean up markdown syntax for purpose
        purpose = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', purpose)  # Remove links
        purpose = re.sub(r'[*_`]', '', purpose)  # Remove formatting
        if len(paragraphs[0]) > 200:
            purpose += '...'

    # Extract key sections (H2 headings)
    key_sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
    key_sections = [s.strip() for s in key_sections]

    # Extract topics from headings (H1, H2, H3)
    all_headings = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
    # Extract keywords from headings (lowercase, alphanumeric)
    topics = set()
    for heading in all_headings:
        # Clean heading and extract significant words
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-_]{2,}\b', heading.lower())
        # Filter out common words
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'about', 'how', 'what', 'when', 'where'}
        topics.update(word for word in words if word not in common_words)

    # Limit topics to top 10 most relevant (by frequency)
    topics = sorted(list(topics))[:10]

    # Get last modified time
    try:
        last_modified = datetime.fromtimestamp(ref_file_path.stat().st_mtime).strftime('%Y-%m-%d')
    except:
        last_modified = ''

    return {
        'filename': ref_file_path.name,
        'title': title,
        'purpose': purpose,
        'topics': topics,
        'size_kb': round(size_kb, 1),
        'line_count': len(lines),
        'key_sections': key_sections,
        'last_modified': last_modified
    }


def detect_similar_references(references_list: List[Dict]) -> List[Dict]:
    """
    Identify consolidation opportunities by finding similar references

    Uses Jaccard similarity on descriptions/purposes to find overlapping content.

    Args:
        references_list: List of reference metadata dicts

    Returns:
        List of similarity clusters with recommendations:
        [
            {
                'files': [str, str],
                'similarity': float,
                'recommendation': str
            }
        ]
    """
    def tokenize(text: str) -> set:
        """Tokenize text into words"""
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-_]{2,}\b', text.lower())
        # Filter out common words
        common_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'about',
                       'how', 'what', 'when', 'where', 'which', 'who', 'will', 'can',
                       'are', 'was', 'were', 'been', 'have', 'has', 'had', 'does', 'did'}
        return set(word for word in words if word not in common_words)

    def jaccard_similarity(tokens1: set, tokens2: set) -> float:
        """Calculate Jaccard similarity between two token sets"""
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        return len(intersection) / len(union) if union else 0.0

    # Build descriptions from purpose + topics
    descriptions = {}
    for ref in references_list:
        desc_text = ref.get('purpose', '') + ' ' + ' '.join(ref.get('topics', []))
        descriptions[ref['filename']] = tokenize(desc_text)

    # Find similar pairs
    clusters = []
    filenames = list(descriptions.keys())

    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            similarity = jaccard_similarity(descriptions[filenames[i]], descriptions[filenames[j]])

            if similarity > 0.70:
                # Determine recommendation based on similarity level
                if similarity > 0.90:
                    recommendation = 'High priority consolidation (likely duplicates)'
                elif similarity > 0.70:
                    recommendation = 'Review for overlapping content'
                else:
                    recommendation = 'No consolidation needed'

                clusters.append({
                    'files': [filenames[i], filenames[j]],
                    'similarity': round(similarity * 100, 1),
                    'recommendation': recommendation
                })

    # Sort by similarity descending
    clusters.sort(key=lambda x: x['similarity'], reverse=True)

    return clusters


def validate_references_structure(skill_path: Path) -> Dict:
    """
    Validate references/ directory structure against AgentSkills spec

    Args:
        skill_path: Path to skill directory

    Returns:
        Dict containing:
            - valid: bool
            - issues: List[str]
            - warnings: List[str]
    """
    issues = []
    warnings = []
    refs_dir = skill_path / 'references'

    # Check if references/ exists
    if not refs_dir.exists():
        return {
            'valid': True,  # Not having references is valid
            'issues': [],
            'warnings': []
        }

    # Check for nested subdirectories (spec requires one-level depth)
    for item in refs_dir.rglob('*'):
        if item.is_dir():
            issues.append(f'Nested subdirectory not allowed per spec: {item.relative_to(refs_dir)}')

    # Check all markdown files are readable
    for ref_file in refs_dir.glob('*.md'):
        if ref_file.name.startswith('.'):
            continue

        try:
            with open(ref_file, 'r', encoding='utf-8') as f:
                content = f.read()
                size_kb = len(content.encode('utf-8')) / 1024

                # Warn about large files (>100KB)
                if size_kb > 100:
                    warnings.append(f'{ref_file.name}: Large file ({size_kb:.1f} KB) - consider including grep patterns in SKILL.md')
        except Exception as e:
            issues.append(f'{ref_file.name}: Cannot read file - {str(e)}')

    # Check if REFERENCE.md exists for skills with 3+ references
    ref_files = scan_references_directory(skill_path)
    catalog_file = refs_dir / 'REFERENCE.md'

    if len(ref_files) >= 3 and not catalog_file.exists():
        warnings.append(f'REFERENCE.md recommended for skills with {len(ref_files)} references')

    valid = len(issues) == 0

    return {
        'valid': valid,
        'issues': issues,
        'warnings': warnings
    }


def generate_reference_catalog(references_list: List[Dict], format: str = 'markdown') -> str:
    """
    Generate reference catalog content

    Args:
        references_list: List of reference metadata dicts
        format: Output format ('markdown' or 'json')

    Returns:
        Catalog content as string
    """
    if format == 'json':
        return json.dumps({
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
            'references': references_list,
            'count': len(references_list)
        }, indent=2)

    # Markdown format
    lines = []
    lines.append('# Reference Catalog')
    lines.append('')
    lines.append(f'Last updated: {datetime.now().strftime("%Y-%m-%d")}')
    lines.append('')
    lines.append('This catalog indexes all reference documentation in this skill. Each reference file serves a specific purpose in the skill\'s domain knowledge.')
    lines.append('')

    # Quick Reference section
    lines.append('## Quick Reference')
    lines.append('')
    for ref in references_list:
        # Create one-line description from title
        one_liner = ref['title']
        if ref['topics']:
            one_liner += ' (' + ', '.join(ref['topics'][:3]) + ')'
        lines.append(f'- **{ref["filename"]}** - {one_liner}')
    lines.append('')

    # Detailed Index section
    lines.append('## Detailed Index')
    lines.append('')

    for ref in references_list:
        lines.append(f'### {ref["filename"]}')

        # Metadata line
        metadata_parts = [
            f'**Size**: {ref["size_kb"]} KB',
            f'**Lines**: {ref["line_count"]}'
        ]
        if ref['topics']:
            metadata_parts.append(f'**Topics**: {", ".join(ref["topics"])}')
        lines.append(' | '.join(metadata_parts))

        # Purpose
        if ref['purpose']:
            lines.append(f'**Purpose**: {ref["purpose"]}')

        # When to use (derived from purpose and topics)
        when_to_use = f'Reference when working with {", ".join(ref["topics"][:3])}' if ref['topics'] else 'General reference documentation'
        lines.append(f'**When to use**: {when_to_use}')

        # Key sections
        if ref['key_sections']:
            lines.append(f'**Key sections**: {", ".join(ref["key_sections"][:5])}')

        lines.append('')

    # Consolidation status
    consolidation_clusters = detect_similar_references(references_list)

    lines.append('## Consolidation Status')
    lines.append('')

    if consolidation_clusters:
        lines.append(f'⚠️  {len(consolidation_clusters)} potential consolidation opportunit{"y" if len(consolidation_clusters) == 1 else "ies"} detected:')
        lines.append('')
        for i, cluster in enumerate(consolidation_clusters, 1):
            lines.append(f'**Cluster {i}** ({cluster["similarity"]}% similar):')
            for file in cluster['files']:
                lines.append(f'  - {file}')
            lines.append(f'  *{cluster["recommendation"]}*')
            lines.append('')
    else:
        lines.append('No similar references detected requiring consolidation.')
        lines.append('')

    # Footer
    lines.append('---')
    lines.append('')
    lines.append('*This catalog is automatically generated by `scripts/update_references.py`. To regenerate: `python3 scripts/update_references.py .`*')

    return '\n'.join(lines)


def update_reference_catalog(skill_path: Path, output_file: str = 'REFERENCE.md',
                             format: str = 'markdown', force: bool = False) -> Dict:
    """
    Main orchestrator function to update reference catalog

    Args:
        skill_path: Path to skill directory
        output_file: Output filename (default: REFERENCE.md)
        format: Output format ('markdown' or 'json')
        force: Force regeneration even if catalog is up-to-date

    Returns:
        Dict containing:
            - success: bool
            - message: str
            - references_count: int
            - consolidation_opportunities: int
    """
    # Validate skill path
    if not skill_path.exists():
        return {
            'success': False,
            'message': f'Skill path does not exist: {skill_path}',
            'references_count': 0,
            'consolidation_opportunities': 0
        }

    refs_dir = skill_path / 'references'

    if not refs_dir.exists():
        return {
            'success': False,
            'message': f'No references/ directory found in {skill_path}',
            'references_count': 0,
            'consolidation_opportunities': 0
        }

    # Scan references directory
    ref_files = scan_references_directory(skill_path)

    if not ref_files:
        return {
            'success': False,
            'message': 'No reference files found in references/ directory',
            'references_count': 0,
            'consolidation_opportunities': 0
        }

    # Extract metadata from all references
    references_metadata = []
    for ref_file in ref_files:
        metadata = extract_reference_metadata(ref_file)
        references_metadata.append(metadata)

    # Generate catalog
    catalog_content = generate_reference_catalog(references_metadata, format=format)

    # Write catalog to file
    output_path = refs_dir / output_file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(catalog_content)
    except Exception as e:
        return {
            'success': False,
            'message': f'Error writing catalog file: {str(e)}',
            'references_count': len(references_metadata),
            'consolidation_opportunities': 0
        }

    # Detect consolidation opportunities
    clusters = detect_similar_references(references_metadata)

    return {
        'success': True,
        'message': f'Successfully generated {output_file} with {len(references_metadata)} references',
        'references_count': len(references_metadata),
        'consolidation_opportunities': len(clusters),
        'output_path': str(output_path)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Reference Management Tool for AgentSkills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate or update catalog for current skill
  python3 update_references.py .

  # For other skills (from skillsmith directory)
  python3 update_references.py ../other-skill

  # Detect consolidation opportunities only
  python3 update_references.py . --detect-duplicates

  # Validate reference structure only
  python3 update_references.py . --validate-structure

  # Output JSON format instead of markdown
  python3 update_references.py . --format json
        '''
    )

    parser.add_argument('skill_path', type=str, help='Path to skill directory')
    parser.add_argument('--output', type=str, default='REFERENCE.md',
                       help='Output filename (default: REFERENCE.md)')
    parser.add_argument('--format', type=str, choices=['markdown', 'json'], default='markdown',
                       help='Output format (default: markdown)')
    parser.add_argument('--detect-duplicates', action='store_true',
                       help='Detect and report consolidation opportunities only')
    parser.add_argument('--validate-structure', action='store_true',
                       help='Validate references/ directory structure only')
    parser.add_argument('--force', action='store_true',
                       help='Force regeneration even if catalog is up-to-date')

    args = parser.parse_args()

    # Convert skill path to Path object
    skill_path = Path(args.skill_path).resolve()

    # Validate structure mode
    if args.validate_structure:
        print(f'Validating references/ structure in {skill_path}...')
        print()
        result = validate_references_structure(skill_path)

        if result['valid']:
            print('✓ References directory structure is valid')
        else:
            print('✗ References directory structure has issues:')

        if result['issues']:
            print('\nIssues:')
            for issue in result['issues']:
                print(f'  - {issue}')

        if result['warnings']:
            print('\nWarnings:')
            for warning in result['warnings']:
                print(f'  - {warning}')

        sys.exit(0 if result['valid'] else 1)

    # Detect duplicates mode
    if args.detect_duplicates:
        print(f'Detecting consolidation opportunities in {skill_path}...')
        print()

        ref_files = scan_references_directory(skill_path)
        if not ref_files:
            print('No reference files found')
            sys.exit(0)

        references_metadata = [extract_reference_metadata(f) for f in ref_files]
        clusters = detect_similar_references(references_metadata)

        if clusters:
            print(f'Consolidation Opportunities Detected:\n')
            for i, cluster in enumerate(clusters, 1):
                print(f'Cluster {i} ({cluster["similarity"]}% similar):')
                for file in cluster['files']:
                    print(f'  - references/{file}')
                print(f'  Recommendation: {cluster["recommendation"]}')
                print()
        else:
            print('No consolidation opportunities detected')

        sys.exit(0)

    # Generate catalog mode (default)
    print(f'Generating reference catalog for {skill_path}...')
    print()

    result = update_reference_catalog(
        skill_path=skill_path,
        output_file=args.output,
        format=args.format,
        force=args.force
    )

    if result['success']:
        print(f'✓ {result["message"]}')
        print(f'  References cataloged: {result["references_count"]}')
        if result['consolidation_opportunities'] > 0:
            print(f'  ⚠️  Consolidation opportunities: {result["consolidation_opportunities"]}')
            print(f'      Run with --detect-duplicates to see details')
        print(f'  Output: {result["output_path"]}')
    else:
        print(f'✗ {result["message"]}')
        sys.exit(1)


if __name__ == '__main__':
    main()
