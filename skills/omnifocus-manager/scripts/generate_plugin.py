#!/usr/bin/env python3
"""
OmniFocus Plugin Generator

Quickly create plugins from templates with correct API patterns.
Supports both solitary (single-file) and bundle (folder) formats.

Usage:
    # Solitary action plugin (simple, single file)
    python3 generate_plugin.py --format solitary --name "My Quick Action"

    # Solitary action with Foundation Models
    python3 generate_plugin.py --format solitary-fm --name "AI Analyzer"

    # Solitary library plugin
    python3 generate_plugin.py --format solitary-library --name "My Utils"

    # Bundle plugin (multiple actions, libraries, localization)
    python3 generate_plugin.py --format bundle --template query-simple --name "My Plugin"
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Plugin formats
FORMATS = {
    'solitary': 'Single-file action plugin (.omnijs)',
    'solitary-fm': 'Single-file action plugin with Foundation Models (.omnijs)',
    'solitary-library': 'Single-file library plugin (.omnijs)',
    'bundle': 'Bundle plugin with localization (.omnifocusjs folder)',
}

# Bundle templates
BUNDLE_TEMPLATES = {
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
    'SHORT_LABEL': 'Short label (1-2 words)',
    'MEDIUM_LABEL': 'Medium label',
    'LONG_LABEL': 'Long descriptive label',
    'PALETTE_LABEL': 'Palette/toolbar label',
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


def validate_javascript(file_path):
    """Validate JavaScript file using eslint_d."""
    try:
        result = subprocess.run(
            ['eslint_d', str(file_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print(f"  ✅ {file_path.name} - no linting errors")
            return True
        else:
            print(f"  ⚠️  {file_path.name} - linting issues found:")
            print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⚠️  {file_path.name} - validation timeout")
        return False
    except FileNotFoundError:
        print(f"  ℹ️  eslint_d not found - skipping validation")
        return True
    except Exception as e:
        print(f"  ⚠️  {file_path.name} - validation error: {e}")
        return False


def generate_solitary_plugin(format_type, name, identifier=None, author=None, description=None, output_dir=None):
    """Generate a solitary (single-file) plugin."""

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

    # Determine template based on format
    if format_type == 'solitary':
        template_file = root / 'assets' / 'plugin-templates' / 'solitary-action' / 'action.omnijs.template'
        output_ext = '.omnijs'
    elif format_type == 'solitary-fm':
        template_file = root / 'assets' / 'plugin-templates' / 'solitary-action-fm' / 'action.omnijs.template'
        output_ext = '.omnijs'
    elif format_type == 'solitary-library':
        template_file = root / 'assets' / 'plugin-templates' / 'solitary-library' / 'library.omnijs.template'
        output_ext = '.omnijs'
    else:
        print(f"❌ Error: Unknown solitary format '{format_type}'")
        return False

    if not template_file.exists():
        print(f"❌ Error: Template not found at {template_file}")
        return False

    # Output path
    output_filename = f"{name.replace(' ', '')}{output_ext}"
    output_path = Path(output_dir) / output_filename

    if output_path.exists():
        print(f"❌ Error: Plugin already exists at {output_path}")
        response = input("Overwrite? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return False
        output_path.unlink()

    # Prepare template variables
    action_id = camel_case(name)
    short_label = name.split()[0] if ' ' in name else name
    variables = {
        'PLUGIN_NAME': name,
        'IDENTIFIER': identifier,
        'AUTHOR': author,
        'DESCRIPTION': description,
        'ACTION_ID': action_id,
        'ACTION_LABEL': name,
        'SHORT_LABEL': short_label,
        'MEDIUM_LABEL': name,
        'LONG_LABEL': f"{name} with OmniFocus Automation",
        'PALETTE_LABEL': name,
        'ICON': 'apple.intelligence' if format_type == 'solitary-fm' else 'list.bullet',
    }

    print(f"\n🔨 Generating solitary plugin...")
    print(f"   Format: {format_type}")
    print(f"   Plugin: {name}")
    print(f"   Identifier: {identifier}")
    print(f"   Output: {output_path}\n")

    # Read and process template
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

        content = replace_template_vars(content, variables)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Created {output_path}")
    except Exception as e:
        print(f"❌ Error creating plugin: {e}")
        return False

    # Validate
    print(f"\n🔍 Validating JavaScript...")
    validate_javascript(output_path)

    # Success message
    print(f"\n🎉 Plugin generated successfully!")
    print(f"\n📦 Installation:")
    print(f"   cp {output_path} ~/Library/Application\\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/")
    print(f"\n🧪 Testing:")
    print(f"   1. Restart OmniFocus (if running)")
    print(f"   2. Go to Automation menu")
    print(f"   3. Find '{name}'")

    return True


def generate_bundle_plugin(template, name, identifier=None, author=None, description=None, output_dir=None):
    """Generate a bundle plugin from a template."""

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
    short_label = name.split()[0] if ' ' in name else name
    variables = {
        'PLUGIN_NAME': name,
        'IDENTIFIER': identifier,
        'AUTHOR': author,
        'DESCRIPTION': description,
        'ACTION_ID': action_id,
        'ACTION_LABEL': f"Show {name}",
        'SHORT_LABEL': short_label,
        'MEDIUM_LABEL': f"Show {name}",
        'LONG_LABEL': f"Show {name} with OmniFocus Automation",
        'PALETTE_LABEL': name,
        'ICON': 'list.bullet',
    }

    print(f"\n🔨 Generating bundle plugin from template '{template}'...")
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
    js_files = []
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
            if file == 'action.js' and 'Resources' in root_dir and 'en.lproj' not in root_dir:
                new_name = f"{action_id}.js"
                new_path = Path(root_dir) / new_name
                os.rename(file_path, new_path)
                file_path = new_path
                print(f"  → Renamed action.js to {new_name}")

                # Also rename the .strings file if it exists
                old_strings = Path(root_dir) / 'en.lproj' / 'action.strings'
                if old_strings.exists():
                    new_strings = Path(root_dir) / 'en.lproj' / f'{action_id}.strings'
                    os.rename(old_strings, new_strings)
                    print(f"  → Renamed action.strings to {action_id}.strings")

            if process_file(file_path, variables):
                processed += 1

            if file_path.suffix == '.js':
                js_files.append(file_path)

    print(f"✅ Processed {processed} files")

    # Validate JavaScript files
    print(f"\n🔍 Validating JavaScript files...")
    errors = 0
    for js_file in js_files:
        if js_file.exists() and not validate_javascript(js_file):
            errors += 1

    if errors > 0:
        print(f"\n⚠️  Plugin generated with {errors} linting warning(s)")
        print(f"   Fix issues before installing to OmniFocus")
    else:
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
    print(f"   Localization: {output_path}/Resources/en.lproj/*.strings")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Generate OmniFocus plugin from template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Simple solitary plugin (single file)
  %(prog)s --format solitary --name "My Quick Action"

  # Solitary plugin with Foundation Models / Apple Intelligence
  %(prog)s --format solitary-fm --name "AI Task Analyzer"

  # Solitary library plugin
  %(prog)s --format solitary-library --name "My Utils"

  # Bundle plugin (folder with localization)
  %(prog)s --format bundle --template query-simple --name "My Tasks"

  # Bundle with custom identifier
  %(prog)s --format bundle --template stats-overview --name "Overview" \\
    --identifier com.mycompany.overview --author "John Doe"

Available formats:
''' + '\n'.join(f"  {name}: {desc}" for name, desc in FORMATS.items()) + '''

Bundle templates:
''' + '\n'.join(f"  {name}: {desc}" for name, desc in BUNDLE_TEMPLATES.items())
    )

    parser.add_argument('--format', '-f',
                        choices=FORMATS.keys(),
                        required=True,
                        help='Plugin format type')
    parser.add_argument('--template', '-t',
                        choices=BUNDLE_TEMPLATES.keys(),
                        help='Bundle template (required for --format bundle)')
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

    # Validate bundle requires template
    if args.format == 'bundle' and not args.template:
        parser.error("--template is required when --format is 'bundle'")

    # Generate based on format
    if args.format in ['solitary', 'solitary-fm', 'solitary-library']:
        success = generate_solitary_plugin(
            format_type=args.format,
            name=args.name,
            identifier=args.identifier,
            author=args.author,
            description=args.description,
            output_dir=args.output
        )
    else:  # bundle
        success = generate_bundle_plugin(
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
