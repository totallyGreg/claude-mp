#!/usr/bin/env python3
"""
OmniFocus Plugin Generator

Quickly create plugin bundles from templates with correct API patterns.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATES = {
    'query-simple': 'Simple query plugin with Alert display',
    'stats-overview': 'Statistics overview dashboard with detailed breakdowns',
}

TEMPLATE_VARS = {
    'PLUGIN_NAME': 'Plugin display name',
    'IDENTIFIER': 'Reverse domain identifier (e.g., com.user.myplugin)',
    'AUTHOR': 'Plugin author name',
    'DESCRIPTION': 'Plugin description',
    'ACTION_ID': 'Action identifier (camelCase)',
    'ACTION_LABEL': 'Action label shown in menus',
    'ICON': 'SF Symbol icon name (e.g., list.bullet, chart.bar)',
}

def find_omnifocus_manager_root():
    """Find the omnifocus-manager skill root directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / 'SKILL.md').exists() and current.name == 'omnifocus-manager':
            return current
        current = current.parent
    return None

def replace_template_vars(content, variables):
    """Replace template variables in content."""
    for key, value in variables.items():
        placeholder = '{{' + key + '}}'
        content = content.replace(placeholder, value)
    return content

def process_file(file_path, variables):
    """Process a single file, replacing template variables."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = replace_template_vars(content, variables)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"  ⚠️  Error processing {file_path}: {e}")
        return False

def camel_case(text):
    """Convert text to camelCase."""
    words = text.replace('-', ' ').replace('_', ' ').split()
    if not words:
        return ''
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def validate_javascript(output_path):
    """Validate JavaScript files using eslint_d."""
    print(f"\n🔍 Validating JavaScript files...")

    resources_dir = output_path / 'Resources'
    if not resources_dir.exists():
        return True

    js_files = list(resources_dir.glob('*.js'))
    if not js_files:
        return True

    errors = 0
    for js_file in js_files:
        try:
            result = subprocess.run(
                ['eslint_d', str(js_file)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"  ✅ {js_file.name} - no linting errors")
            else:
                print(f"  ⚠️  {js_file.name} - linting issues found:")
                print(result.stdout)
                errors += 1
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  {js_file.name} - validation timeout")
            errors += 1
        except FileNotFoundError:
            print(f"  ℹ️  eslint_d not found - skipping validation")
            print(f"     Install with: npm install -g eslint_d")
            return True
        except Exception as e:
            print(f"  ⚠️  {js_file.name} - validation error: {e}")
            errors += 1

    if errors > 0:
        print(f"\n⚠️  Found linting issues in {errors} file(s)")
        print(f"   Run: eslint_d {output_path}/Resources/*.js")
        return False

    return True

def generate_plugin(template, name, identifier=None, author=None, description=None, output_dir=None):
    """Generate a plugin from a template."""

    # Find omnifocus-manager root
    root = find_omnifocus_manager_root()
    if not root:
        print("❌ Error: Could not find omnifocus-manager root directory")
        return False

    # Set defaults
    if not identifier:
        identifier = f"com.user.omnifocus.{name.lower().replace(' ', '')}"
    if not author:
        author = "OmniFocus User"
    if not description:
        description = f"{name} plugin for OmniFocus"
    if not output_dir:
        output_dir = root / 'assets'

    # Template paths
    template_dir = root / 'assets' / 'plugin-templates' / template
    if not template_dir.exists():
        print(f"❌ Error: Template '{template}' not found at {template_dir}")
        return False

    # Output path
    plugin_name = f"{name.replace(' ', '')}.omnifocusjs"
    output_path = Path(output_dir) / plugin_name

    if output_path.exists():
        print(f"❌ Error: Plugin already exists at {output_path}")
        response = input("Overwrite? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return False
        shutil.rmtree(output_path)

    # Prepare template variables
    action_id = camel_case(name)
    variables = {
        'PLUGIN_NAME': name,
        'IDENTIFIER': identifier,
        'AUTHOR': author,
        'DESCRIPTION': description,
        'ACTION_ID': action_id,
        'ACTION_LABEL': f"Show {name}",
        'ICON': 'list.bullet',
    }

    print(f"\n🔨 Generating plugin from template '{template}'...")
    print(f"   Plugin: {name}")
    print(f"   Identifier: {identifier}")
    print(f"   Output: {output_path}\n")

    # Copy template directory
    try:
        shutil.copytree(template_dir, output_path)
        print(f"✅ Copied template to {output_path}")
    except Exception as e:
        print(f"❌ Error copying template: {e}")
        return False

    # Process all files
    processed = 0
    for root_dir, dirs, files in os.walk(output_path):
        # Skip README files (template documentation)
        dirs[:] = [d for d in dirs if d not in ['.git']]

        for file in files:
            if file == 'README.md':
                # Remove template README
                os.remove(Path(root_dir) / file)
                continue

            file_path = Path(root_dir) / file

            # Rename action.js to match ACTION_ID
            if file == 'action.js' and 'Resources' in root_dir:
                new_name = f"{action_id}.js"
                new_path = Path(root_dir) / new_name
                os.rename(file_path, new_path)
                file_path = new_path
                print(f"  → Renamed action.js to {new_name}")

            if process_file(file_path, variables):
                processed += 1

    print(f"✅ Processed {processed} files")

    # Validate JavaScript files
    if not validate_javascript(output_path):
        print(f"\n⚠️  Plugin generated with linting warnings")
        print(f"   Fix issues before installing to OmniFocus")
    else:
        # Success message
        print(f"\n🎉 Plugin generated successfully!")
    print(f"\n📦 Installation:")
    print(f"   cp -r {output_path} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/")
    print(f"\n🧪 Testing:")
    print(f"   1. Restart OmniFocus (if running)")
    print(f"   2. Go to Automation → {name}")
    print(f"   3. Select 'Show {name}' action")
    print(f"\n✏️  Customization:")
    print(f"   Edit: {output_path}/Resources/*.js")
    print(f"   Manifest: {output_path}/manifest.json")

    return True

def main():
    parser = argparse.ArgumentParser(
        description='Generate OmniFocus plugin from template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate simple query plugin
  %(prog)s --template query-simple --name "My Tasks"

  # Generate stats overview plugin
  %(prog)s --template stats-overview --name "Database Overview"

  # With custom identifier and author
  %(prog)s --template query-simple --name "Flagged" \\
    --identifier com.mycompany.flagged --author "John Doe"

Available templates:
''' + '\n'.join(f"  {name}: {desc}" for name, desc in TEMPLATES.items())
    )

    parser.add_argument('--template', '-t',
                       choices=TEMPLATES.keys(),
                       required=True,
                       help='Plugin template type')
    parser.add_argument('--name', '-n',
                       required=True,
                       help='Plugin name (e.g., "My Plugin")')
    parser.add_argument('--identifier', '-i',
                       help='Reverse domain identifier (default: auto-generated)')
    parser.add_argument('--author', '-a',
                       help='Plugin author (default: "OmniFocus User")')
    parser.add_argument('--description', '-d',
                       help='Plugin description (default: auto-generated)')
    parser.add_argument('--output', '-o',
                       help='Output directory (default: assets/)')

    args = parser.parse_args()

    success = generate_plugin(
        template=args.template,
        name=args.name,
        identifier=args.identifier,
        author=args.author,
        description=args.description,
        output_dir=args.output
    )

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
