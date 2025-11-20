#!/usr/bin/env python3
"""
Analyze Objective-C code for Swift migration complexity.

Usage:
    python3 migration_analyzer.py <objc-file-or-directory>
"""

import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict

class MigrationAnalyzer:
    def __init__(self):
        self.stats = defaultdict(int)
        self.issues = []

    def analyze_file(self, filepath: Path):
        """Analyze a single Objective-C file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            self._count_patterns(content, filepath)
            self._check_migration_issues(content, filepath)

        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    def _count_patterns(self, content: str, filepath: Path):
        """Count various Objective-C patterns."""
        patterns = {
            'classes': r'@interface\s+\w+',
            'protocols': r'@protocol\s+\w+',
            'properties': r'@property',
            'methods': r'^\s*[-+]\s*\(',
            'blocks': r'\(?\^\w*\)?[\(\{]',
            'categories': r'@interface\s+\w+\s*\(',
        }

        for name, pattern in patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE)
            self.stats[name] += len(matches)

    def _check_migration_issues(self, content: str, filepath: Path):
        """Check for migration complexity indicators."""
        # Check for missing nullability annotations
        properties_without_null = re.findall(
            r'@property.*\*\s+\w+;(?!.*\b(?:nullable|nonnull|_Nullable|_Nonnull)\b)',
            content
        )
        if properties_without_null:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'issue': 'Missing nullability annotations',
                'count': len(properties_without_null)
            })

        # Check for C-style APIs
        c_apis = re.findall(r'\b(?:malloc|free|strcpy|printf)\b', content)
        if c_apis:
            self.issues.append({
                'file': filepath,
                'severity': 'high',
                'issue': 'C-style APIs that need Swift replacement',
                'count': len(c_apis)
            })

        # Check for macros
        macros = re.findall(r'^#define\s+\w+', content, re.MULTILINE)
        if macros:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'issue': 'Macros that need conversion to functions/constants',
                'count': len(macros)
            })

        # Check for manual memory management
        manual_memory = re.findall(r'\b(?:retain|release|autorelease|dealloc)\b', content)
        if manual_memory:
            self.issues.append({
                'file': filepath,
                'severity': 'low',
                'issue': 'Manual memory management (ARC should handle)',
                'count': len(manual_memory)
            })

    def print_report(self):
        """Print analysis report."""
        print("\n" + "="*60)
        print("Objective-C to Swift Migration Analysis")
        print("="*60)

        print("\n📊 Code Statistics:")
        print("-" * 60)
        for key, value in sorted(self.stats.items()):
            print(f"  {key.capitalize():20s}: {value:4d}")

        if self.issues:
            print("\n⚠️  Migration Issues:")
            print("-" * 60)

            severity_order = {'high': 1, 'medium': 2, 'low': 3}
            sorted_issues = sorted(self.issues, key=lambda x: severity_order[x['severity']])

            for issue in sorted_issues:
                severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[issue['severity']]
                print(f"\n  {severity_icon} {issue['severity'].upper()}: {issue['issue']}")
                print(f"     File: {issue['file']}")
                print(f"     Count: {issue['count']}")

        print("\n" + "="*60)
        print("Complexity Assessment:")
        print("-" * 60)

        total_items = sum(self.stats.values())
        issue_count = len(self.issues)

        if total_items < 50 and issue_count < 5:
            complexity = "LOW"
            desc = "Good candidate for migration"
        elif total_items < 200 and issue_count < 15:
            complexity = "MEDIUM"
            desc = "Moderate migration effort required"
        else:
            complexity = "HIGH"
            desc = "Significant migration effort required"

        print(f"  Overall Complexity: {complexity}")
        print(f"  {desc}")
        print("="*60 + "\n")

def analyze_path(path: Path, analyzer: MigrationAnalyzer):
    """Recursively analyze Objective-C files."""
    if path.is_file():
        if path.suffix in ['.h', '.m', '.mm']:
            analyzer.analyze_file(path)
    elif path.is_dir():
        for objc_file in path.rglob('*.h'):
            analyzer.analyze_file(objc_file)
        for objc_file in path.rglob('*.m'):
            analyzer.analyze_file(objc_file)
        for objc_file in path.rglob('*.mm'):
            analyzer.analyze_file(objc_file)

def main():
    parser = argparse.ArgumentParser(description='Analyze Objective-C code for Swift migration')
    parser.add_argument('path', help='Objective-C file or directory to analyze')

    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{path}' does not exist")
        sys.exit(1)

    analyzer = MigrationAnalyzer()
    analyze_path(path, analyzer)
    analyzer.print_report()

if __name__ == '__main__':
    main()
