#!/usr/bin/env python3
"""
Obsidian Frontmatter Validator

Validates frontmatter in Obsidian notes against a defined schema.

Usage:
    python3 validate_frontmatter.py /path/to/vault --schema schema.json
    python3 validate_frontmatter.py /path/to/vault --generate-schema

Options:
    --schema FILE         Path to schema JSON file
    --generate-schema     Generate schema from existing notes
    --required FIELDS     Comma-separated list of required fields
    --fix                 Attempt to fix common issues
    --json                Output results as JSON
"""

import os
import sys
import re
import json
import yaml
from pathlib import Path
from collections import defaultdict
import argparse

class FrontmatterValidator:
    def __init__(self, vault_path, schema=None):
        self.vault_path = Path(vault_path)
        self.schema = schema or {}
        self.issues = defaultdict(list)
        self.notes = []

    def scan_vault(self):
        """Scan vault and collect frontmatter"""
        for file_path in self.vault_path.rglob("*.md"):
            # Skip templates and hidden files
            if "Template" in str(file_path) or file_path.name.startswith("_"):
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter = self.extract_frontmatter(content)

            if frontmatter is not None:
                self.notes.append({
                    'path': file_path,
                    'relative_path': file_path.relative_to(self.vault_path),
                    'frontmatter': frontmatter,
                    'content': content
                })

    def extract_frontmatter(self, content):
        """Extract and parse YAML frontmatter"""
        if not content.startswith('---'):
            return None

        parts = content.split('---', 2)
        if len(parts) < 3:
            return None

        fm_text = parts[1]
        try:
            return yaml.safe_load(fm_text) or {}
        except yaml.YAMLError:
            return {}

    def generate_schema(self):
        """Generate schema from existing notes"""
        field_types = defaultdict(lambda: defaultdict(int))
        field_examples = defaultdict(set)

        for note in self.notes:
            for field, value in note['frontmatter'].items():
                value_type = type(value).__name__
                field_types[field][value_type] += 1

                # Store example values
                if isinstance(value, (str, int, float, bool)):
                    field_examples[field].add(str(value)[:50])  # Truncate long values

        # Build schema
        schema = {
            'fields': {}
        }

        for field, types in field_types.items():
            # Determine primary type
            primary_type = max(types.items(), key=lambda x: x[1])[0]

            schema['fields'][field] = {
                'type': primary_type,
                'usage_count': sum(types.values()),
                'percentage': round(sum(types.values()) / len(self.notes) * 100, 1),
                'examples': list(field_examples[field])[:5]
            }

        return schema

    def validate_required_fields(self, required_fields):
        """Check for missing required fields"""
        for note in self.notes:
            missing = []
            for field in required_fields:
                if field not in note['frontmatter']:
                    missing.append(field)

            if missing:
                self.issues['missing_required'].append({
                    'note': note['relative_path'],
                    'missing': missing
                })

    def validate_field_types(self):
        """Validate field types against schema"""
        if not self.schema or 'fields' not in self.schema:
            return

        for note in self.notes:
            for field, value in note['frontmatter'].items():
                if field in self.schema['fields']:
                    expected_type = self.schema['fields'][field].get('type')
                    actual_type = type(value).__name__

                    if expected_type and actual_type != expected_type:
                        self.issues['type_mismatch'].append({
                            'note': note['relative_path'],
                            'field': field,
                            'expected': expected_type,
                            'actual': actual_type,
                            'value': str(value)[:50]
                        })

    def check_common_issues(self):
        """Check for common frontmatter problems"""
        for note in self.notes:
            fm = note['frontmatter']

            # Check for empty values
            for field, value in fm.items():
                if value == '' or value is None:
                    self.issues['empty_values'].append({
                        'note': note['relative_path'],
                        'field': field
                    })

            # Check for inconsistent date formats
            date_fields = ['date', 'date created', 'date modified', 'created', 'modified']
            for field in date_fields:
                if field in fm:
                    value = str(fm[field])
                    # Check if it looks like a date
                    if not re.match(r'\d{4}-\d{2}-\d{2}', value):
                        self.issues['inconsistent_dates'].append({
                            'note': note['relative_path'],
                            'field': field,
                            'value': value
                        })

            # Check for duplicate fields (case variations)
            fields_lower = defaultdict(list)
            for field in fm.keys():
                fields_lower[field.lower()].append(field)

            for lower, originals in fields_lower.items():
                if len(originals) > 1:
                    self.issues['duplicate_fields'].append({
                        'note': note['relative_path'],
                        'fields': originals
                    })

    def generate_report(self, as_json=False):
        """Generate validation report"""
        if as_json:
            return json.dumps(self.issues, indent=2, default=str)

        report = []
        report.append("=" * 60)
        report.append("FRONTMATTER VALIDATION REPORT")
        report.append("=" * 60)
        report.append(f"Vault: {self.vault_path}")
        report.append(f"Notes analyzed: {len(self.notes)}")
        report.append("")

        total_issues = sum(len(v) for v in self.issues.values())

        if total_issues == 0:
            report.append("✓ No issues found!")
            report.append("")
            return "\n".join(report)

        if 'missing_required' in self.issues and self.issues['missing_required']:
            report.append("-" * 60)
            report.append("MISSING REQUIRED FIELDS")
            report.append("-" * 60)
            for item in self.issues['missing_required'][:10]:
                report.append(f"{item['note']}")
                report.append(f"  Missing: {', '.join(item['missing'])}")
            if len(self.issues['missing_required']) > 10:
                report.append(f"  ... and {len(self.issues['missing_required']) - 10} more")
            report.append("")

        if 'type_mismatch' in self.issues and self.issues['type_mismatch']:
            report.append("-" * 60)
            report.append("TYPE MISMATCHES")
            report.append("-" * 60)
            for item in self.issues['type_mismatch'][:10]:
                report.append(f"{item['note']}")
                report.append(f"  Field: {item['field']}")
                report.append(f"  Expected: {item['expected']}, Got: {item['actual']}")
                report.append(f"  Value: {item['value']}")
            if len(self.issues['type_mismatch']) > 10:
                report.append(f"  ... and {len(self.issues['type_mismatch']) - 10} more")
            report.append("")

        if 'empty_values' in self.issues and self.issues['empty_values']:
            report.append("-" * 60)
            report.append("EMPTY VALUES")
            report.append("-" * 60)
            field_counts = defaultdict(int)
            for item in self.issues['empty_values']:
                field_counts[item['field']] += 1
            for field, count in sorted(field_counts.items(), key=lambda x: -x[1])[:10]:
                report.append(f"  {field}: {count} notes")
            report.append("")

        if 'inconsistent_dates' in self.issues and self.issues['inconsistent_dates']:
            report.append("-" * 60)
            report.append("INCONSISTENT DATE FORMATS")
            report.append("-" * 60)
            for item in self.issues['inconsistent_dates'][:10]:
                report.append(f"{item['note']}")
                report.append(f"  {item['field']}: {item['value']}")
            if len(self.issues['inconsistent_dates']) > 10:
                report.append(f"  ... and {len(self.issues['inconsistent_dates']) - 10} more")
            report.append("")

        if 'duplicate_fields' in self.issues and self.issues['duplicate_fields']:
            report.append("-" * 60)
            report.append("DUPLICATE FIELDS (case variations)")
            report.append("-" * 60)
            for item in self.issues['duplicate_fields'][:10]:
                report.append(f"{item['note']}")
                report.append(f"  Fields: {', '.join(item['fields'])}")
            if len(self.issues['duplicate_fields']) > 10:
                report.append(f"  ... and {len(self.issues['duplicate_fields']) - 10} more")
            report.append("")

        report.append("=" * 60)
        report.append(f"Total issues: {total_issues}")
        report.append("=" * 60)

        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Validate Obsidian frontmatter')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--schema', help='Path to schema JSON file')
    parser.add_argument('--generate-schema', action='store_true', help='Generate schema from vault')
    parser.add_argument('--required', help='Comma-separated required fields')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if not os.path.isdir(args.vault_path):
        print(f"Error: '{args.vault_path}' is not a valid directory")
        sys.exit(1)

    # Load schema if provided
    schema = None
    if args.schema:
        with open(args.schema, 'r') as f:
            schema = json.load(f)

    validator = FrontmatterValidator(args.vault_path, schema)

    print("Scanning vault...", file=sys.stderr)
    validator.scan_vault()
    print(f"Found {len(validator.notes)} notes with frontmatter\n", file=sys.stderr)

    if args.generate_schema:
        print("Generating schema...", file=sys.stderr)
        schema = validator.generate_schema()
        print(json.dumps(schema, indent=2))
        sys.exit(0)

    # Validate
    print("Validating frontmatter...", file=sys.stderr)

    if args.required:
        required_fields = [f.strip() for f in args.required.split(',')]
        validator.validate_required_fields(required_fields)

    if schema:
        validator.validate_field_types()

    validator.check_common_issues()

    print("\n", file=sys.stderr)
    print(validator.generate_report(as_json=args.json))

if __name__ == '__main__':
    main()
