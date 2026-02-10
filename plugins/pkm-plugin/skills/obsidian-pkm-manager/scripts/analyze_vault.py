#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0",
# ]
# requires-python = ">=3.10"
# ///
"""
Obsidian Vault Analyzer

Analyzes an Obsidian vault for common organizational issues:
- Untagged notes
- Orphaned files (no links in or out)
- Inconsistent frontmatter
- Missing temporal links
- Duplicate or similar titles

Usage:
    python3 analyze_vault.py /path/to/vault [options]

Options:
    --check-tags            Check for untagged notes
    --check-orphans         Check for orphaned notes
    --check-frontmatter     Check frontmatter consistency
    --check-temporal        Check temporal link consistency
    --check-duplicates      Check for duplicate titles
    --all                   Run all checks (default)
    --json                  Output results as JSON
"""

import os
import sys
import re
import json
from pathlib import Path
from collections import defaultdict
import argparse

def validate_vault_path(vault_path_str):
    """Validate vault path for security.

    Prevents directory traversal and access to system directories.
    Returns resolved Path object if valid, raises ValueError otherwise.
    """
    vault_path = Path(vault_path_str).resolve()

    # Must be a directory
    if not vault_path.is_dir():
        raise ValueError(f"Not a directory: {vault_path}")

    # Block system directories
    forbidden_prefixes = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root', '/boot', '/sys', '/proc']
    vault_str = str(vault_path)

    for forbidden in forbidden_prefixes:
        if vault_str.startswith(forbidden):
            raise ValueError(f"Access to system directory denied: {vault_path}")

    # Warn if outside typical user directories
    home = Path.home()
    typical_prefixes = [
        str(home / 'Documents'),
        str(home / 'Dropbox'),
        str(home / 'iCloud'),
        str(home / 'Library/Mobile Documents'),
    ]

    if not any(vault_str.startswith(prefix) for prefix in typical_prefixes):
        print(f"⚠️  Warning: Vault path outside typical Obsidian locations", file=sys.stderr)
        print(f"   Path: {vault_path}", file=sys.stderr)

    return vault_path

class VaultAnalyzer:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        self.notes = []
        self.issues = defaultdict(list)

    def scan_vault(self):
        """Scan vault and collect all markdown files"""
        for file_path in self.vault_path.rglob("*.md"):
            # Skip templates and hidden files
            if "Template" in str(file_path) or file_path.name.startswith("_"):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter, body = self.parse_note(content)

            self.notes.append({
                'path': file_path,
                'relative_path': file_path.relative_to(self.vault_path),
                'name': file_path.stem,
                'frontmatter': frontmatter,
                'body': body,
                'content': content
            })

    def parse_note(self, content):
        """Extract frontmatter and body from note content"""
        frontmatter = {}
        body = content

        # Check for YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                body = parts[2]

                # Simple YAML parsing (basic key: value pairs)
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

        return frontmatter, body

    def extract_links(self, content):
        """Extract wikilinks from content"""
        # Match [[Link]] or [[Link|Display]]
        pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        return re.findall(pattern, content)

    def check_untagged(self):
        """Find notes without tags"""
        untagged = []
        for note in self.notes:
            has_tags = 'tags' in note['frontmatter']
            has_inline_tags = bool(re.search(r'#\w+', note['body']))

            if not has_tags and not has_inline_tags:
                untagged.append(note['relative_path'])

        self.issues['untagged'] = untagged
        return len(untagged)

    def check_orphans(self):
        """Find notes with no incoming or outgoing links"""
        # Build link graph
        links_out = defaultdict(set)
        links_in = defaultdict(set)

        for note in self.notes:
            note_name = note['name']
            outgoing = self.extract_links(note['content'])

            for link in outgoing:
                links_out[note_name].add(link)
                links_in[link].add(note_name)

        orphans = []
        for note in self.notes:
            note_name = note['name']
            has_out = len(links_out[note_name]) > 0
            has_in = len(links_in[note_name]) > 0

            if not has_out and not has_in:
                orphans.append(note['relative_path'])

        self.issues['orphans'] = orphans
        return len(orphans)

    def check_frontmatter_consistency(self):
        """Check for inconsistent frontmatter schemas"""
        field_usage = defaultdict(int)
        missing_common = defaultdict(list)

        # Count field usage
        for note in self.notes:
            for field in note['frontmatter']:
                field_usage[field] += 1

        # Find common fields (used in >50% of notes)
        total_notes = len(self.notes)
        common_fields = {
            field for field, count in field_usage.items()
            if count > total_notes * 0.5
        }

        # Find notes missing common fields
        for note in self.notes:
            for field in common_fields:
                if field not in note['frontmatter']:
                    missing_common[field].append(note['relative_path'])

        self.issues['missing_common_fields'] = dict(missing_common)
        self.issues['common_fields'] = list(common_fields)
        return len(missing_common)

    def check_temporal_links(self):
        """Check daily notes for missing Week/Month links"""
        missing_temporal = []

        for note in self.notes:
            # Check if this looks like a daily note
            is_daily = (
                'daily' in note['frontmatter'].get('tags', '').lower() or
                '#daily' in note['body'] or
                re.match(r'\d{4}-\d{2}-\d{2}', note['name'])
            )

            if is_daily:
                fm = note['frontmatter']
                missing = []

                if 'Week' not in fm and 'week' not in fm:
                    missing.append('Week')
                if 'Month' not in fm and 'month' not in fm:
                    missing.append('Month')

                if missing:
                    missing_temporal.append({
                        'note': note['relative_path'],
                        'missing': missing
                    })

        self.issues['missing_temporal_links'] = missing_temporal
        return len(missing_temporal)

    def check_duplicates(self):
        """Find potentially duplicate note titles"""
        titles = defaultdict(list)

        for note in self.notes:
            # Normalize title for comparison
            normalized = note['name'].lower()
            normalized = re.sub(r'\W+', '', normalized)
            titles[normalized].append(note['relative_path'])

        duplicates = {
            title: paths for title, paths in titles.items()
            if len(paths) > 1
        }

        self.issues['potential_duplicates'] = duplicates
        return len(duplicates)

    def generate_report(self, as_json=False):
        """Generate analysis report"""
        if as_json:
            return json.dumps(self.issues, indent=2, default=str)

        report = []
        report.append("=" * 60)
        report.append("OBSIDIAN VAULT ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Vault: {self.vault_path}")
        report.append(f"Notes analyzed: {len(self.notes)}")
        report.append("")

        if 'untagged' in self.issues:
            report.append("-" * 60)
            report.append("UNTAGGED NOTES")
            report.append("-" * 60)
            if self.issues['untagged']:
                report.append(f"Found {len(self.issues['untagged'])} notes without tags:")
                for path in self.issues['untagged'][:10]:  # Show first 10
                    report.append(f"  - {path}")
                if len(self.issues['untagged']) > 10:
                    report.append(f"  ... and {len(self.issues['untagged']) - 10} more")
            else:
                report.append("✓ All notes have tags")
            report.append("")

        if 'orphans' in self.issues:
            report.append("-" * 60)
            report.append("ORPHANED NOTES (no links in or out)")
            report.append("-" * 60)
            if self.issues['orphans']:
                report.append(f"Found {len(self.issues['orphans'])} orphaned notes:")
                for path in self.issues['orphans'][:10]:
                    report.append(f"  - {path}")
                if len(self.issues['orphans']) > 10:
                    report.append(f"  ... and {len(self.issues['orphans']) - 10} more")
            else:
                report.append("✓ No orphaned notes found")
            report.append("")

        if 'missing_common_fields' in self.issues:
            report.append("-" * 60)
            report.append("FRONTMATTER CONSISTENCY")
            report.append("-" * 60)
            report.append(f"Common fields (used in >50% of notes): {', '.join(self.issues['common_fields'])}")
            report.append("")
            for field, paths in self.issues['missing_common_fields'].items():
                if paths:
                    report.append(f"{len(paths)} notes missing '{field}' field")
            report.append("")

        if 'missing_temporal_links' in self.issues:
            report.append("-" * 60)
            report.append("TEMPORAL LINKS (Week/Month)")
            report.append("-" * 60)
            if self.issues['missing_temporal_links']:
                report.append(f"Found {len(self.issues['missing_temporal_links'])} daily notes with missing temporal links:")
                for item in self.issues['missing_temporal_links'][:10]:
                    report.append(f"  - {item['note']}: missing {', '.join(item['missing'])}")
                if len(self.issues['missing_temporal_links']) > 10:
                    report.append(f"  ... and {len(self.issues['missing_temporal_links']) - 10} more")
            else:
                report.append("✓ All daily notes have temporal links")
            report.append("")

        if 'potential_duplicates' in self.issues:
            report.append("-" * 60)
            report.append("POTENTIAL DUPLICATE TITLES")
            report.append("-" * 60)
            if self.issues['potential_duplicates']:
                report.append(f"Found {len(self.issues['potential_duplicates'])} sets of potentially duplicate titles:")
                count = 0
                for title, paths in self.issues['potential_duplicates'].items():
                    if count >= 10:
                        remaining = len(self.issues['potential_duplicates']) - 10
                        report.append(f"  ... and {remaining} more duplicate sets")
                        break
                    report.append(f"  Normalized: '{title}'")
                    for path in paths:
                        report.append(f"    - {path}")
                    count += 1
            else:
                report.append("✓ No duplicate titles found")
            report.append("")

        report.append("=" * 60)
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Analyze Obsidian vault for organizational issues')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--check-tags', action='store_true', help='Check for untagged notes')
    parser.add_argument('--check-orphans', action='store_true', help='Check for orphaned notes')
    parser.add_argument('--check-frontmatter', action='store_true', help='Check frontmatter consistency')
    parser.add_argument('--check-temporal', action='store_true', help='Check temporal link consistency')
    parser.add_argument('--check-duplicates', action='store_true', help='Check for duplicate titles')
    parser.add_argument('--all', action='store_true', help='Run all checks (default)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Validate vault path for security
    try:
        vault_path = validate_vault_path(args.vault_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # If no specific checks, run all
    run_all = args.all or not any([
        args.check_tags,
        args.check_orphans,
        args.check_frontmatter,
        args.check_temporal,
        args.check_duplicates
    ])

    analyzer = VaultAnalyzer(vault_path)

    print("Scanning vault...", file=sys.stderr)
    analyzer.scan_vault()
    print(f"Found {len(analyzer.notes)} notes\n", file=sys.stderr)

    if run_all or args.check_tags:
        print("Checking for untagged notes...", file=sys.stderr)
        analyzer.check_untagged()

    if run_all or args.check_orphans:
        print("Checking for orphaned notes...", file=sys.stderr)
        analyzer.check_orphans()

    if run_all or args.check_frontmatter:
        print("Checking frontmatter consistency...", file=sys.stderr)
        analyzer.check_frontmatter_consistency()

    if run_all or args.check_temporal:
        print("Checking temporal links...", file=sys.stderr)
        analyzer.check_temporal_links()

    if run_all or args.check_duplicates:
        print("Checking for duplicates...", file=sys.stderr)
        analyzer.check_duplicates()

    print("\n", file=sys.stderr)
    print(analyzer.generate_report(as_json=args.json))

if __name__ == '__main__':
    main()
