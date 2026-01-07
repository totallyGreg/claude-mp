#!/usr/bin/env python3
"""
Reference Management Tool for AgentSkills

Validates that all reference files in references/ directory are mentioned
contextually in SKILL.md, maintaining AgentSkills one-level reference architecture.

Usage:
    update_references.py <skill-path>
    update_references.py <skill-path> --detect-duplicates
    update_references.py <skill-path> --validate-structure

Features:
    - Scans references/ directory and extracts metadata from each file
    - Validates that all reference files are mentioned in SKILL.md
    - Detects orphaned references (files not mentioned anywhere)
    - Detects similar descriptions signaling consolidation needs
    - Validates references/ directory structure per spec
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

    valid = len(issues) == 0

    return {
        'valid': valid,
        'issues': issues,
        'warnings': warnings
    }


def validate_reference_mentions(skill_md_path: Path, references_list: List[Dict]) -> List[str]:
    """
    Validate that all reference files are mentioned in SKILL.md

    Args:
        skill_md_path: Path to SKILL.md file
        references_list: List of reference metadata dicts

    Returns:
        List of orphaned reference filenames (not mentioned in SKILL.md)
    """
    # Read SKILL.md content
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    orphaned_refs = []

    for ref in references_list:
        filename = ref['filename']

        # Check if reference is mentioned in SKILL.md
        # Look for patterns like:
        # - `references/filename.md`
        # - references/filename.md
        # - `filename.md` (sometimes just filename if context is clear)

        patterns = [
            f'`references/{filename}`',
            f'references/{filename}',
            f'`{filename}`',
        ]

        is_mentioned = any(pattern in skill_content for pattern in patterns)

        if not is_mentioned:
            orphaned_refs.append(filename)

    return orphaned_refs


def main():
    parser = argparse.ArgumentParser(
        description='Reference Management Tool for AgentSkills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Validate reference mentions for current skill
  python3 update_references.py .

  # For other skills (from skillsmith directory)
  python3 update_references.py ../other-skill

  # Detect consolidation opportunities only
  python3 update_references.py . --detect-duplicates

  # Validate reference structure only
  python3 update_references.py . --validate-structure
        '''
    )

    parser.add_argument('skill_path', type=str, help='Path to skill directory')
    parser.add_argument('--detect-duplicates', action='store_true',
                       help='Detect and report consolidation opportunities only')
    parser.add_argument('--validate-structure', action='store_true',
                       help='Validate references/ directory structure only')

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

    # Validate reference mentions mode (default)
    print(f'Validating reference mentions for {skill_path}...')
    print()

    # Scan references directory
    ref_files = scan_references_directory(skill_path)

    if not ref_files:
        print('No reference files found in references/ directory')
        sys.exit(0)

    print(f'Found {len(ref_files)} reference file(s)')
    print()

    # Extract metadata from all reference files
    references_list = []
    for ref_file in ref_files:
        metadata = extract_reference_metadata(ref_file)
        references_list.append(metadata)

    # Validate references are mentioned in SKILL.md
    skill_md_path = skill_path / 'SKILL.md'

    if not skill_md_path.exists():
        print(f'✗ SKILL.md not found at {skill_md_path}')
        sys.exit(1)

    orphaned_refs = validate_reference_mentions(skill_md_path, references_list)

    if orphaned_refs:
        print(f"⚠️  Warning: {len(orphaned_refs)} reference file(s) not mentioned in SKILL.md:")
        for ref in orphaned_refs:
            print(f"  - {ref}")
        print("\nConsider adding contextual mentions in SKILL.md, such as:")
        print("  - 'See `references/filename.md` for details'")
        print("  - 'Use templates from `references/filename.md`'")
        print("  - 'API documentation in `references/filename.md`'")
        sys.exit(1)
    else:
        print(f"✓ All {len(references_list)} reference files are mentioned in SKILL.md")
        sys.exit(0)


if __name__ == '__main__':
    main()
