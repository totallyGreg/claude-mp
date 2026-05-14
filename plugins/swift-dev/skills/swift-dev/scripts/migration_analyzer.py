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
        # Check for legacy concurrency patterns (HIGH PRIORITY)
        gcd_patterns = re.findall(
            r'\bdispatch_(?:async|sync|after|once|barrier_async|barrier_sync)\b|'
            r'\bdispatch_get_(?:main_queue|global_queue)\b',
            content
        )
        if gcd_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'high',
                'category': 'concurrency',
                'issue': 'Legacy GCD patterns',
                'count': len(gcd_patterns),
                'recommendation': 'Use Task for background work + MainActor.run for UI updates',
                'reference': 'objc_to_swift6_migration.md - Concurrency Migration'
            })

        # Check for thread-safety mechanisms
        lock_patterns = re.findall(
            r'@synchronized\s*\(|'
            r'\b(?:NSLock|NSRecursiveLock|NSCondition|NSConditionLock)\b|'
            r'\bpthread_mutex|'
            r'\bdispatch_semaphore',
            content
        )
        if lock_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'high',
                'category': 'concurrency',
                'issue': 'Thread-safety mechanisms (@synchronized, NSLock, etc.)',
                'count': len(lock_patterns),
                'recommendation': 'Replace with Swift actors for compiler-enforced thread safety',
                'reference': 'objc_to_swift6_migration.md - Locks to Actors'
            })

        # Check for NSOperation patterns
        nsoperation_patterns = re.findall(
            r'\bNSOperation(?:Queue)?\b|'
            r'\bNSBlockOperation\b',
            content
        )
        if nsoperation_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'high',
                'category': 'concurrency',
                'issue': 'NSOperation/NSOperationQueue usage',
                'count': len(nsoperation_patterns),
                'recommendation': 'Use TaskGroup for structured concurrency with dependencies',
                'reference': 'objc_to_swift6_migration.md - NSOperationQueue to TaskGroup'
            })

        # Check for legacy data flow patterns (MEDIUM PRIORITY)
        kvo_patterns = re.findall(
            r'addObserver.*forKeyPath:|'
            r'observeValueForKeyPath:|'
            r'removeObserver.*forKeyPath:',
            content
        )
        if kvo_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'category': 'data_flow',
                'issue': 'Key-Value Observing (KVO) usage',
                'count': len(kvo_patterns),
                'recommendation': 'Replace with @Observable macro or Combine @Published',
                'reference': 'objc_to_swift6_migration.md - KVO to @Observable'
            })

        # Check for NSNotificationCenter patterns
        notification_patterns = re.findall(
            r'\bNSNotificationCenter\b|'
            r'addObserver.*selector.*name:|'
            r'postNotificationName:',
            content
        )
        if notification_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'category': 'data_flow',
                'issue': 'NSNotificationCenter usage',
                'count': len(notification_patterns),
                'recommendation': 'Use AsyncStream for iteration-based notifications or Combine publishers',
                'reference': 'objc_to_swift6_migration.md - NSNotificationCenter to AsyncStream'
            })

        # Check for NSError** patterns (MEDIUM PRIORITY)
        nserror_patterns = re.findall(
            r'NSError\s*\*\*|'
            r'\(NSError\s*\*\*\)\s*error',
            content
        )
        if nserror_patterns:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'category': 'error_handling',
                'issue': 'NSError** out parameters',
                'count': len(nserror_patterns),
                'recommendation': 'Convert to Swift throws or typed throws (Swift 6)',
                'reference': 'objc_to_swift6_migration.md - Error Handling'
            })

        # Check for missing nullability annotations
        properties_without_null = re.findall(
            r'@property.*\*\s+\w+;(?!.*\b(?:nullable|nonnull|_Nullable|_Nonnull)\b)',
            content
        )
        if properties_without_null:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'category': 'type_safety',
                'issue': 'Missing nullability annotations',
                'count': len(properties_without_null),
                'recommendation': 'Add nonnull/nullable annotations for proper Swift Optional mapping',
                'reference': 'objc_interop.md - Nullability'
            })

        # Check for C-style APIs
        c_apis = re.findall(r'\b(?:malloc|free|strcpy|strcat|printf|sprintf)\b', content)
        if c_apis:
            self.issues.append({
                'file': filepath,
                'severity': 'high',
                'category': 'c_interop',
                'issue': 'C-style APIs',
                'count': len(c_apis),
                'recommendation': 'Replace with Swift standard library equivalents',
                'reference': 'Swift Standard Library documentation'
            })

        # Check for macros
        macros = re.findall(r'^#define\s+\w+', content, re.MULTILINE)
        if macros:
            self.issues.append({
                'file': filepath,
                'severity': 'medium',
                'category': 'legacy_patterns',
                'issue': 'Preprocessor macros',
                'count': len(macros),
                'recommendation': 'Convert to Swift functions, constants, or computed properties',
                'reference': 'Swift language guide - Functions and Properties'
            })

        # Check for manual memory management
        manual_memory = re.findall(r'\b(?:retain|release|autorelease|dealloc)\b', content)
        if manual_memory:
            self.issues.append({
                'file': filepath,
                'severity': 'low',
                'category': 'legacy_patterns',
                'issue': 'Manual memory management',
                'count': len(manual_memory),
                'recommendation': 'Remove manual memory management; ARC handles this automatically',
                'reference': 'Automatic Reference Counting (ARC)'
            })

    def print_report(self):
        """Print analysis report."""
        print("\n" + "="*60)
        print("Objective-C to Swift 6 Migration Analysis")
        print("="*60)

        print("\n📊 Code Statistics:")
        print("-" * 60)
        for key, value in sorted(self.stats.items()):
            print(f"  {key.capitalize():20s}: {value:4d}")

        if self.issues:
            print("\n🔄 Swift 6 Migration Opportunities:")
            print("-" * 60)

            # Group issues by severity and category
            severity_order = {'high': 1, 'medium': 2, 'low': 3}
            sorted_issues = sorted(self.issues, key=lambda x: (severity_order[x['severity']], x.get('category', '')))

            # Group by severity
            severity_groups = {'high': [], 'medium': [], 'low': []}
            for issue in sorted_issues:
                severity_groups[issue['severity']].append(issue)

            # Print high priority issues
            if severity_groups['high']:
                print("\n🔴 HIGH PRIORITY")
                for issue in severity_groups['high']:
                    self._print_issue(issue)

            # Print medium priority issues
            if severity_groups['medium']:
                print("\n🟡 MEDIUM PRIORITY")
                for issue in severity_groups['medium']:
                    self._print_issue(issue)

            # Print low priority issues
            if severity_groups['low']:
                print("\n🟢 LOW PRIORITY")
                for issue in severity_groups['low']:
                    self._print_issue(issue)

        print("\n" + "="*60)
        print("Complexity Assessment:")
        print("-" * 60)

        total_items = sum(self.stats.values())
        issue_count = len(self.issues)
        high_priority_count = sum(1 for issue in self.issues if issue['severity'] == 'high')

        # Updated complexity calculation considering Swift 6 modernization priorities
        if high_priority_count > 10 or total_items > 200:
            complexity = "HIGH"
            desc = "Significant Swift 6 modernization effort required"
        elif high_priority_count > 5 or total_items > 50:
            complexity = "MEDIUM"
            desc = "Moderate Swift 6 migration effort required"
        else:
            complexity = "LOW"
            desc = "Good candidate for Swift 6 migration"

        print(f"  Overall Complexity: {complexity}")
        print(f"  {desc}")
        print(f"  High Priority Issues: {high_priority_count}")
        print(f"  Total Issues: {issue_count}")
        print("="*60 + "\n")

    def _print_issue(self, issue):
        """Print a single issue with full details."""
        print(f"\n   • {issue['issue']}")
        print(f"     Count: {issue['count']} occurrence(s)")
        print(f"     File: {issue['file']}")
        if 'recommendation' in issue:
            print(f"     Swift 6: {issue['recommendation']}")
        if 'reference' in issue:
            print(f"     Reference: {issue['reference']}")

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
