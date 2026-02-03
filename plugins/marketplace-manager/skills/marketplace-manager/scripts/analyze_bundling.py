#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Analyze skills and recommend bundling opportunities for Claude Code marketplace.

This script analyzes relationships between skills and recommends which ones
should be bundled together as multi-skill plugins.

Usage:
    uv run scripts/analyze_bundling.py
    uv run scripts/analyze_bundling.py --interactive
    uv run scripts/analyze_bundling.py --format json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from utils import get_repo_root, print_verbose_info, validate_repo_structure


def load_marketplace(marketplace_path):
    """Load marketplace.json file."""
    try:
        with open(marketplace_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Marketplace not found: {marketplace_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in marketplace.json: {e}")
        return None


def extract_skill_metadata(skill_md_path):
    """Extract metadata from SKILL.md frontmatter.

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Dict with metadata fields
    """
    metadata = {
        'name': None,
        'version': None,
        'description': None,
        'category': None,
        'tags': []
    }

    if not skill_md_path.exists():
        return metadata

    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()

        # Match YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return metadata

        frontmatter = frontmatter_match.group(1)

        # Parse frontmatter
        for line in frontmatter.split('\n'):
            stripped = line.strip()
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key == 'name':
                    metadata['name'] = value
                elif key == 'description':
                    metadata['description'] = value
                elif key == 'category':
                    metadata['category'] = value
                elif key == 'tags':
                    # Parse tags array
                    metadata['tags'] = [t.strip().strip('-').strip() for t in value.split(',')]

    except Exception as e:
        print(f"⚠️  Warning: Could not read {skill_md_path}: {e}")

    return metadata


def scan_skill_references(skill_md_path):
    """Scan SKILL.md for references to other skills.

    Args:
        skill_md_path: Path to SKILL.md file

    Returns:
        Set of skill names referenced
    """
    references = set()

    if not skill_md_path.exists():
        return references

    try:
        with open(skill_md_path, 'r') as f:
            content = f.read()

        # Look for skill references in various patterns:
        # - skill-name (hyphenated)
        # - "skill-name" (quoted)
        # - `/skill-name` (slash command style)
        # - `skill-name` (code style)

        # Find all potential skill names (lowercase with hyphens)
        potential_refs = re.findall(r'\b([a-z]+-[a-z-]+)\b', content.lower())

        for ref in potential_refs:
            # Filter out common words that match the pattern
            if ref not in ['command-line', 'pre-commit', 'post-commit', 'how-to', 'sub-command']:
                references.add(ref)

    except Exception as e:
        print(f"⚠️  Warning: Could not scan {skill_md_path}: {e}")

    return references


def analyze_skills(repo_root, marketplace_data):
    """Analyze all skills for bundling opportunities.

    Args:
        repo_root: Repository root path
        marketplace_data: Marketplace data dict

    Returns:
        Dict with analysis results
    """
    skills_analysis = {}
    category_groups = defaultdict(list)
    reference_graph = defaultdict(set)

    # Analyze each plugin's skills
    for plugin in marketplace_data.get('plugins', []):
        plugin_name = plugin['name']
        source = plugin.get('source', './')
        source_path = repo_root / source.lstrip('./')

        # Get SKILL.md
        skill_md = source_path / 'SKILL.md'
        if not skill_md.exists():
            continue

        # Extract metadata
        metadata = extract_skill_metadata(skill_md)
        references = scan_skill_references(skill_md)

        skills_analysis[plugin_name] = {
            'metadata': metadata,
            'references': list(references),
            'source': source,
            'plugin_data': plugin
        }

        # Group by category
        category = plugin.get('category', metadata.get('category', 'uncategorized'))
        category_groups[category].append(plugin_name)

        # Build reference graph
        reference_graph[plugin_name] = references

    return {
        'skills': skills_analysis,
        'categories': dict(category_groups),
        'references': dict(reference_graph)
    }


def calculate_bundling_score(skill1_name, skill2_name, analysis):
    """Calculate a bundling affinity score between two skills.

    Args:
        skill1_name: First skill name
        skill2_name: Second skill name
        analysis: Analysis results dict

    Returns:
        Score (0-100) indicating bundling affinity
    """
    score = 0
    skill1 = analysis['skills'].get(skill1_name, {})
    skill2 = analysis['skills'].get(skill2_name, {})

    # Same category: +30 points
    cat1 = skill1.get('plugin_data', {}).get('category')
    cat2 = skill2.get('plugin_data', {}).get('category')
    if cat1 and cat2 and cat1 == cat2:
        score += 30

    # Cross-references: +40 points
    refs1 = set(skill1.get('references', []))
    refs2 = set(skill2.get('references', []))
    if skill2_name in refs1 or skill1_name in refs2:
        score += 40

    # Bidirectional references: +20 bonus
    if skill2_name in refs1 and skill1_name in refs2:
        score += 20

    # Similar descriptions (keyword overlap): +10 points
    desc1 = skill1.get('metadata', {}).get('description', '').lower()
    desc2 = skill2.get('metadata', {}).get('description', '').lower()
    if desc1 and desc2:
        words1 = set(desc1.split())
        words2 = set(desc2.split())
        common_words = words1 & words2
        # Filter out common words
        meaningful_words = {w for w in common_words if len(w) > 4}
        if len(meaningful_words) >= 2:
            score += 10

    return min(score, 100)


def recommend_bundles(analysis, min_score=40):
    """Recommend bundling opportunities.

    Args:
        analysis: Analysis results dict
        min_score: Minimum affinity score for bundling (default: 40)

    Returns:
        List of bundle recommendations
    """
    recommendations = []
    skills = list(analysis['skills'].keys())

    # Calculate all pairwise scores
    pairs = []
    for i, skill1 in enumerate(skills):
        for skill2 in skills[i+1:]:
            score = calculate_bundling_score(skill1, skill2, analysis)
            if score >= min_score:
                pairs.append({
                    'skills': [skill1, skill2],
                    'score': score,
                    'reasons': []
                })

    # Sort by score
    pairs.sort(key=lambda x: x['score'], reverse=True)

    # Add reasons for top recommendations
    for pair in pairs[:5]:  # Top 5 recommendations
        skill1, skill2 = pair['skills']
        reasons = []

        # Check why they scored high
        if calculate_bundling_score(skill1, skill2, analysis) >= 30:
            cat1 = analysis['skills'][skill1]['plugin_data'].get('category')
            cat2 = analysis['skills'][skill2]['plugin_data'].get('category')
            if cat1 == cat2:
                reasons.append(f"Both in '{cat1}' category")

        refs1 = set(analysis['skills'][skill1].get('references', []))
        refs2 = set(analysis['skills'][skill2].get('references', []))

        if skill2 in refs1:
            reasons.append(f"{skill1} references {skill2}")
        if skill1 in refs2:
            reasons.append(f"{skill2} references {skill1}")

        pair['reasons'] = reasons
        recommendations.append(pair)

    return recommendations


def format_text_output(analysis, recommendations):
    """Format analysis results as human-readable text."""
    print("\n" + "="*70)
    print("Bundling Analysis Report")
    print("="*70 + "\n")

    # Category summary
    print("Skills by Category:")
    for category, skills in sorted(analysis['categories'].items()):
        print(f"\n  {category} ({len(skills)} skill(s)):")
        for skill in sorted(skills):
            print(f"    • {skill}")

    # Reference graph
    print("\n" + "-"*70)
    print("Cross-Skill References:")
    refs_found = False
    for skill, refs in sorted(analysis['references'].items()):
        # Only show references to other actual skills
        actual_refs = [r for r in refs if r in analysis['skills']]
        if actual_refs:
            refs_found = True
            print(f"\n  {skill}:")
            for ref in sorted(actual_refs):
                print(f"    → {ref}")

    if not refs_found:
        print("\n  (No cross-skill references detected)")

    # Bundling recommendations
    print("\n" + "="*70)
    print("Bundling Recommendations")
    print("="*70)

    if not recommendations:
        print("\nNo strong bundling opportunities detected (score threshold: 40)")
        print("\nConsider bundling if you:")
        print("  • Have skills in the same category")
        print("  • Have skills that reference each other")
        print("  • Have skills frequently used together")
    else:
        for idx, rec in enumerate(recommendations, 1):
            print(f"\n{idx}. Bundle: {' + '.join(rec['skills'])}")
            print(f"   Affinity Score: {rec['score']}/100")
            if rec['reasons']:
                print(f"   Reasons:")
                for reason in rec['reasons']:
                    print(f"     • {reason}")

            # Suggest bundle name and description
            skill_names = rec['skills']
            bundle_name = '-'.join(sorted(skill_names))
            print(f"\n   Suggested Bundle:")
            print(f"     Name: {bundle_name}")
            print(f"     Description: Combines {', '.join(skill_names)} for integrated workflow")

    print("\n" + "="*70)
    print("Next Steps")
    print("="*70)
    print("\nTo create a bundle:")
    print("  1. Use add_to_marketplace.py create-plugin with multiple --skills")
    print("  2. Update SKILL.md to document the bundle")
    print("  3. Consider keeping individual skill distributions for users who only need one")
    print()


def interactive_mode(analysis, recommendations):
    """Interactive bundling workflow.

    Args:
        analysis: Analysis results dict
        recommendations: Bundle recommendations list
    """
    print("\n" + "="*70)
    print("Interactive Bundling Workflow")
    print("="*70)

    if not recommendations:
        print("\n❌ No bundling recommendations available")
        print("   Try lowering the threshold with --min-score")
        return

    print(f"\nFound {len(recommendations)} bundling recommendation(s)")

    for idx, rec in enumerate(recommendations, 1):
        print(f"\n{'-'*70}")
        print(f"Recommendation {idx}/{len(recommendations)}")
        print(f"Skills: {', '.join(rec['skills'])}")
        print(f"Score: {rec['score']}/100")
        print(f"Reasons: {', '.join(rec['reasons'])}")

        response = input("\nCreate this bundle? [y/N/q] ")

        if response.lower() == 'q':
            print("Exiting interactive mode")
            break
        elif response.lower() == 'y':
            bundle_name = input(f"Bundle name [{'-'.join(rec['skills'])}]: ").strip()
            if not bundle_name:
                bundle_name = '-'.join(rec['skills'])

            bundle_desc = input("Bundle description: ").strip()

            print(f"\n📦 To create this bundle, run:")
            print(f"\n  python3 scripts/add_to_marketplace.py create-plugin {bundle_name} \\")
            print(f"    \"{bundle_desc}\" \\")
            print(f"    --skills {' '.join([f'./skills/{s}' for s in rec['skills']])}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze skills and recommend bundling opportunities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and show recommendations
  %(prog)s

  # Output as JSON
  %(prog)s --format json

  # Interactive bundling workflow
  %(prog)s --interactive

  # Adjust minimum affinity score
  %(prog)s --min-score 30
""",
    )

    parser.add_argument(
        '--path',
        default='.',
        help='Repository root path (default: auto-detect)'
    )

    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (text or json)'
    )

    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Interactive bundling workflow'
    )

    parser.add_argument(
        '--min-score',
        type=int,
        default=40,
        help='Minimum affinity score for recommendations (default: 40)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed path resolution information'
    )

    args = parser.parse_args()

    # Determine paths with auto-detection
    repo_root = get_repo_root(args.path, verbose=args.verbose)
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'

    # Print verbose info if requested
    if args.verbose:
        print_verbose_info(repo_root, marketplace_path)

    # Validate repository structure
    if not validate_repo_structure(repo_root, 'analyze-bundling'):
        return 1

    if not marketplace_path.exists():
        print(f"❌ No marketplace found")
        print(f"   Expected location: {marketplace_path}")
        return 1

    # Load marketplace
    marketplace_data = load_marketplace(marketplace_path)
    if not marketplace_data:
        return 1

    # Analyze skills
    analysis = analyze_skills(repo_root, marketplace_data)

    # Generate recommendations
    recommendations = recommend_bundles(analysis, min_score=args.min_score)

    # Output results
    if args.format == 'json':
        output = {
            'analysis': {
                'skills': len(analysis['skills']),
                'categories': analysis['categories'],
                'references': analysis['references']
            },
            'recommendations': recommendations
        }
        print(json.dumps(output, indent=2))
    else:
        format_text_output(analysis, recommendations)

        if args.interactive:
            interactive_mode(analysis, recommendations)

    return 0


if __name__ == '__main__':
    sys.exit(main())
