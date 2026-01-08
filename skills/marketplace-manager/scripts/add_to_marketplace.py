#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Add a skill to the Claude Code plugin marketplace.

This script helps manage the .claude-plugin/marketplace.json file by:
- Creating the marketplace structure if it doesn't exist
- Adding new skills to an existing plugin
- Creating new plugins with skills
- Validating the marketplace.json structure
"""

import argparse
import json
import os
import sys
from pathlib import Path

from utils import get_repo_root, print_verbose_info, validate_repo_structure


def load_marketplace(marketplace_path):
    """Load existing marketplace.json or return empty structure."""
    if marketplace_path.exists():
        with open(marketplace_path, "r") as f:
            return json.load(f)

    # Return empty marketplace structure
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": "",
        "version": "1.0.0",
        "description": "",
        "owner": {"name": "", "email": ""},
        "plugins": [],
    }


def save_marketplace(marketplace_path, marketplace_data):
    """Save marketplace.json with pretty formatting."""
    marketplace_path.parent.mkdir(parents=True, exist_ok=True)

    with open(marketplace_path, "w") as f:
        json.dump(marketplace_data, f, indent=2)

    print(f"✅ Updated marketplace at: {marketplace_path}")


def init_marketplace(marketplace_path, name, owner_name, owner_email, description):
    """Initialize a new marketplace.json."""
    marketplace_data = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": name,
        "version": "1.0.0",
        "description": description,
        "owner": {"name": owner_name, "email": owner_email},
        "plugins": [],
    }

    save_marketplace(marketplace_path, marketplace_data)
    print(f"✅ Initialized new marketplace: {name}")


def find_plugin(marketplace_data, plugin_name):
    """Find a plugin by name in the marketplace."""
    for plugin in marketplace_data.get("plugins", []):
        if plugin["name"] == plugin_name:
            return plugin
    return None


def add_skill_to_plugin(marketplace_data, plugin_name, skill_path):
    """Add a skill to an existing plugin."""
    plugin = find_plugin(marketplace_data, plugin_name)

    if not plugin:
        print(f"❌ Plugin '{plugin_name}' not found in marketplace")
        return False

    # Normalize skill path
    skill_path = f"./{skill_path.strip('./')}"

    # Check if skill already exists
    if skill_path in plugin.get("skills", []):
        print(f"⚠️  Skill '{skill_path}' already exists in plugin '{plugin_name}'")
        return False

    # Add skill
    if "skills" not in plugin:
        plugin["skills"] = []

    plugin["skills"].append(skill_path)
    print(f"✅ Added skill '{skill_path}' to plugin '{plugin_name}'")
    return True


def create_plugin(marketplace_data, plugin_name, plugin_description, skill_paths):
    """Create a new plugin with skills."""
    # Check if plugin already exists
    if find_plugin(marketplace_data, plugin_name):
        print(f"❌ Plugin '{plugin_name}' already exists")
        return False

    # Normalize skill paths
    normalized_skills = [f"./{path.strip('./')}" for path in skill_paths]

    # Create new plugin
    new_plugin = {
        "name": plugin_name,
        "description": plugin_description,
        "source": "./",
        "strict": False,
        "skills": normalized_skills,
    }

    marketplace_data["plugins"].append(new_plugin)
    print(f"✅ Created new plugin: {plugin_name}")
    print(f"   Added {len(normalized_skills)} skill(s)")
    return True


def list_marketplace(marketplace_data):
    """List all plugins and skills in the marketplace."""
    print("\n📦 Marketplace:", marketplace_data.get("name", "(unnamed)"))
    print(f"   Owner: {marketplace_data.get('owner', {}).get('name', '(not set)')}")
    print(f"   Version: {marketplace_data.get('version', '1.0.0')}")
    print(f"   Description: {marketplace_data.get('description', '(none)')}")

    plugins = marketplace_data.get("plugins", [])
    if not plugins:
        print("\n   No plugins configured")
        return

    print(f"\n   Plugins ({len(plugins)}):")
    for plugin in plugins:
        print(f"\n   • {plugin['name']}")
        print(f"     Description: {plugin.get('description', '(none)')}")
        skills = plugin.get("skills", [])
        if skills:
            print(f"     Skills ({len(skills)}):")
            for skill in skills:
                print(f"       - {skill}")
        else:
            print(f"     No skills")


def validate_skill_exists(skill_path, repo_root):
    """Validate that a skill directory exists and has SKILL.md."""
    skill_dir = repo_root / skill_path.lstrip("./")

    if not skill_dir.exists():
        print(f"⚠️  Warning: Skill directory not found: {skill_dir}")
        return False

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        print(f"⚠️  Warning: SKILL.md not found in: {skill_dir}")
        return False

    return True


def parse_version(version_str):
    """Parse semantic version string into (major, minor, patch) tuple."""
    try:
        parts = version_str.split(".")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, AttributeError):
        return (1, 0, 0)


def increment_version(version_str, part="patch"):
    """Increment semantic version.

    Args:
        version_str: Current version (e.g., "1.2.3")
        part: Which part to increment ('major', 'minor', or 'patch')

    Returns:
        New version string
    """
    major, minor, patch = parse_version(version_str)

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def update_metadata(
    marketplace_data, description=None, version=None, auto_increment=None
):
    """Update marketplace metadata.

    Args:
        marketplace_data: Marketplace data dictionary
        description: New description (optional)
        version: New version (optional)
        auto_increment: Auto-increment version ('major', 'minor', 'patch', or None)

    Returns:
        True if updated, False otherwise
    """
    updated = False

    if description:
        old_desc = marketplace_data.get("description", "(none)")
        marketplace_data["description"] = description
        print(f"✅ Updated description:")
        print(f"   Old: {old_desc}")
        print(f"   New: {description}")
        updated = True

    if version:
        old_version = marketplace_data.get("version", "1.0.0")
        marketplace_data["version"] = version
        print(f"✅ Updated version: {old_version} → {version}")
        updated = True
    elif auto_increment:
        old_version = marketplace_data.get("version", "1.0.0")
        new_version = increment_version(old_version, auto_increment)
        marketplace_data["version"] = new_version
        print(
            f"✅ Auto-incremented version ({auto_increment}): {old_version} → {new_version}"
        )
        updated = True

    return updated


def validate_semantic_version(version_str):
    """Validate semantic version format (X.Y.Z).

    Args:
        version_str: Version string to validate

    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, str(version_str)))


def validate_email(email_str):
    """Basic email validation.

    Args:
        email_str: Email string to validate

    Returns:
        True if valid format, False otherwise
    """
    if not email_str:
        return True  # Email is optional
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email_str))


def validate_marketplace(marketplace_path, repo_root, output_format='text'):
    """Comprehensively validate marketplace.json structure.

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root directory
        output_format: 'text' or 'json'

    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []

    # Load marketplace
    try:
        marketplace_data = load_marketplace(marketplace_path)
    except Exception as e:
        issues.append({
            'type': 'error',
            'category': 'schema',
            'message': f"Failed to load marketplace.json: {e}"
        })
        return False, issues

    # Validate required fields
    required_fields = ['name', 'version', 'description', 'owner', 'plugins']
    for field in required_fields:
        if field not in marketplace_data or not marketplace_data[field]:
            issues.append({
                'type': 'error',
                'category': 'schema',
                'field': field,
                'message': f"Required field '{field}' is missing or empty"
            })

    # Validate $schema URL
    expected_schema = "https://anthropic.com/claude-code/marketplace.schema.json"
    if '$schema' not in marketplace_data:
        issues.append({
            'type': 'warning',
            'category': 'schema',
            'field': '$schema',
            'message': f"Missing $schema field (expected: {expected_schema})"
        })
    elif marketplace_data['$schema'] != expected_schema:
        issues.append({
            'type': 'warning',
            'category': 'schema',
            'field': '$schema',
            'message': f"Unexpected schema URL: {marketplace_data['$schema']}"
        })

    # Validate marketplace version
    if 'version' in marketplace_data:
        if not validate_semantic_version(marketplace_data['version']):
            issues.append({
                'type': 'error',
                'category': 'version',
                'field': 'version',
                'value': marketplace_data['version'],
                'message': f"Invalid semantic version format: {marketplace_data['version']} (expected X.Y.Z)"
            })

    # Validate owner
    if 'owner' in marketplace_data:
        owner = marketplace_data['owner']
        if not isinstance(owner, dict):
            issues.append({
                'type': 'error',
                'category': 'schema',
                'field': 'owner',
                'message': "Owner must be an object with 'name' and optional 'email'"
            })
        else:
            if 'name' not in owner or not owner['name']:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': 'owner.name',
                    'message': "Owner name is required"
                })
            if 'email' in owner and not validate_email(owner['email']):
                issues.append({
                    'type': 'warning',
                    'category': 'format',
                    'field': 'owner.email',
                    'value': owner['email'],
                    'message': f"Invalid email format: {owner['email']}"
                })

    # Validate plugins
    if 'plugins' not in marketplace_data or not isinstance(marketplace_data['plugins'], list):
        issues.append({
            'type': 'error',
            'category': 'schema',
            'field': 'plugins',
            'message': "Plugins must be an array"
        })
    else:
        plugins = marketplace_data['plugins']
        plugin_names = set()

        for idx, plugin in enumerate(plugins):
            plugin_prefix = f"plugins[{idx}]"

            # Check required plugin fields
            if 'name' not in plugin or not plugin['name']:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.name',
                    'message': f"Plugin at index {idx} missing required 'name' field"
                })
            else:
                plugin_name = plugin['name']

                # Check for duplicate names
                if plugin_name in plugin_names:
                    issues.append({
                        'type': 'error',
                        'category': 'duplicate',
                        'field': f'{plugin_prefix}.name',
                        'value': plugin_name,
                        'message': f"Duplicate plugin name: {plugin_name}"
                    })
                plugin_names.add(plugin_name)

            if 'description' not in plugin or not plugin['description']:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.description',
                    'message': f"Plugin '{plugin.get('name', 'unnamed')}' missing required 'description' field"
                })

            if 'version' not in plugin or not plugin['version']:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.version',
                    'message': f"Plugin '{plugin.get('name', 'unnamed')}' missing required 'version' field"
                })
            elif not validate_semantic_version(plugin['version']):
                issues.append({
                    'type': 'error',
                    'category': 'version',
                    'field': f'{plugin_prefix}.version',
                    'value': plugin['version'],
                    'message': f"Plugin '{plugin.get('name', 'unnamed')}' has invalid version: {plugin['version']}"
                })

            # Validate skill paths
            if 'skills' in plugin and isinstance(plugin['skills'], list):
                for skill_idx, skill_path in enumerate(plugin['skills']):
                    skill_path_clean = skill_path.lstrip('./')
                    skill_dir = repo_root / skill_path_clean

                    # Check if path starts with './'
                    if not skill_path.startswith('./'):
                        issues.append({
                            'type': 'warning',
                            'category': 'format',
                            'field': f'{plugin_prefix}.skills[{skill_idx}]',
                            'value': skill_path,
                            'message': f"Skill path should start with './' (got: {skill_path})"
                        })

                    # Check if skill directory exists
                    if not skill_dir.exists():
                        issues.append({
                            'type': 'error',
                            'category': 'missing_file',
                            'field': f'{plugin_prefix}.skills[{skill_idx}]',
                            'value': skill_path,
                            'message': f"Skill directory not found: {skill_dir}"
                        })
                    else:
                        skill_md = skill_dir / 'SKILL.md'
                        if not skill_md.exists():
                            issues.append({
                                'type': 'error',
                                'category': 'missing_file',
                                'field': f'{plugin_prefix}.skills[{skill_idx}]',
                                'value': skill_path,
                                'message': f"SKILL.md not found in: {skill_dir}"
                            })
                        else:
                            # Validate SKILL.md frontmatter
                            from sync_marketplace_versions import extract_frontmatter_version
                            version, is_deprecated = extract_frontmatter_version(skill_md)
                            if not version:
                                issues.append({
                                    'type': 'warning',
                                    'category': 'metadata',
                                    'field': f'{plugin_prefix}.skills[{skill_idx}]',
                                    'value': skill_path,
                                    'message': f"No version found in {skill_path}/SKILL.md frontmatter"
                                })
                            elif is_deprecated:
                                issues.append({
                                    'type': 'warning',
                                    'category': 'deprecated',
                                    'field': f'{plugin_prefix}.skills[{skill_idx}]',
                                    'value': skill_path,
                                    'message': f"Skill uses deprecated 'version' field (use 'metadata.version' instead)"
                                })

            # Validate author email if present
            if 'author' in plugin and isinstance(plugin['author'], dict):
                if 'email' in plugin['author'] and not validate_email(plugin['author']['email']):
                    issues.append({
                        'type': 'warning',
                        'category': 'format',
                        'field': f'{plugin_prefix}.author.email',
                        'value': plugin['author']['email'],
                        'message': f"Invalid email format: {plugin['author']['email']}"
                    })

    # Determine if valid
    errors = [i for i in issues if i['type'] == 'error']
    is_valid = len(errors) == 0

    return is_valid, issues


def format_validation_output(is_valid, issues, format_type='text'):
    """Format validation results for output.

    Args:
        is_valid: Boolean indicating if validation passed
        issues: List of issue dictionaries
        format_type: 'text' or 'json'

    Returns:
        None (prints to stdout)
    """
    if format_type == 'json':
        import json
        result = {
            'valid': is_valid,
            'issues': issues,
            'summary': {
                'total': len(issues),
                'errors': len([i for i in issues if i['type'] == 'error']),
                'warnings': len([i for i in issues if i['type'] == 'warning'])
            }
        }
        print(json.dumps(result, indent=2))
    else:
        # Text format
        print("\n" + "="*60)
        print("Marketplace Validation Report")
        print("="*60 + "\n")

        if is_valid and not issues:
            print("✅ Validation passed! No issues found.\n")
            return

        errors = [i for i in issues if i['type'] == 'error']
        warnings = [i for i in issues if i['type'] == 'warning']

        if errors:
            print(f"❌ Errors ({len(errors)}):\n")
            for issue in errors:
                field = issue.get('field', 'unknown')
                message = issue['message']
                value = issue.get('value', '')
                if value:
                    print(f"  • [{field}] {message}")
                    print(f"    Value: {value}")
                else:
                    print(f"  • [{field}] {message}")
            print()

        if warnings:
            print(f"⚠️  Warnings ({len(warnings)}):\n")
            for issue in warnings:
                field = issue.get('field', 'unknown')
                message = issue['message']
                value = issue.get('value', '')
                if value:
                    print(f"  • [{field}] {message}")
                    print(f"    Value: {value}")
                else:
                    print(f"  • [{field}] {message}")
            print()

        print("="*60)
        if is_valid:
            print("✅ Validation passed (with warnings)")
        else:
            print("❌ Validation failed")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Claude Code plugin marketplace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize a new marketplace
  %(prog)s init --name my-marketplace --owner-name "John Doe" \\
    --owner-email "john@example.com" --description "My skills"

  # Create a new plugin with skills
  %(prog)s create-plugin my-plugin "Plugin description" \\
    --skills skill1 skill2 skill3

  # Add a skill to existing plugin
  %(prog)s add-skill my-plugin skill4

  # List all plugins and skills
  %(prog)s list

  # Update marketplace description
  %(prog)s update-metadata --description "New description"

  # Auto-increment version (patch: 1.0.0 → 1.0.1)
  %(prog)s update-metadata --increment patch

  # Auto-increment minor version (1.0.1 → 1.1.0)
  %(prog)s update-metadata --increment minor

  # Set specific version
  %(prog)s update-metadata --version 2.0.0

  # Update both description and version
  %(prog)s update-metadata --description "New desc" --increment minor
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new marketplace")
    init_parser.add_argument("--name", required=True, help="Marketplace name")
    init_parser.add_argument("--owner-name", required=True, help="Owner name")
    init_parser.add_argument("--owner-email", required=True, help="Owner email")
    init_parser.add_argument(
        "--description", required=True, help="Marketplace description"
    )
    init_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    init_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    # Create plugin command
    create_parser = subparsers.add_parser("create-plugin", help="Create a new plugin")
    create_parser.add_argument("name", help="Plugin name")
    create_parser.add_argument("description", help="Plugin description")
    create_parser.add_argument("--skills", nargs="+", required=True, help="Skill paths")
    create_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    create_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    # Add skill command
    add_parser = subparsers.add_parser(
        "add-skill", help="Add a skill to existing plugin"
    )
    add_parser.add_argument("plugin", help="Plugin name")
    add_parser.add_argument("skill", help="Skill path")
    add_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    add_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List all plugins and skills")
    list_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    list_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    # Update metadata command
    update_parser = subparsers.add_parser(
        "update-metadata", help="Update marketplace metadata"
    )
    update_parser.add_argument("--description", help="New marketplace description")
    update_parser.add_argument("--version", help="Set specific version (e.g., '2.0.0')")
    update_parser.add_argument(
        "--increment",
        choices=["major", "minor", "patch"],
        help="Auto-increment version (major, minor, or patch)",
    )
    update_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    update_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate marketplace.json structure and compliance"
    )
    validate_parser.add_argument(
        "--path", default=".", help="Repository root path (default: auto-detect)"
    )
    validate_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (text or json)"
    )
    validate_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed path resolution information"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Determine paths with auto-detection
    repo_root = get_repo_root(args.path, verbose=args.verbose)
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"

    # Print verbose info if requested
    if args.verbose:
        print_verbose_info(repo_root, marketplace_path)

    # Validate repository structure (skip for init command)
    if args.command != "init" and not validate_repo_structure(repo_root, args.command):
        return 1

    # Handle commands
    if args.command == "init":
        if marketplace_path.exists():
            response = input(
                f"Marketplace already exists at {marketplace_path}. Overwrite? [y/N] "
            )
            if response.lower() != "y":
                print("Cancelled")
                return 1

        init_marketplace(
            marketplace_path,
            args.name,
            args.owner_name,
            args.owner_email,
            args.description,
        )

    elif args.command == "list":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found")
            print(f"   Expected location: {marketplace_path}")
            print(f"   Repository root: {repo_root}")
            print(f"   Current directory: {Path.cwd()}")
            print(f"\n   Run 'init' command first or specify correct --path")
            return 1

        marketplace_data = load_marketplace(marketplace_path)
        list_marketplace(marketplace_data)

    elif args.command == "create-plugin":
        marketplace_data = load_marketplace(marketplace_path)

        # Validate marketplace is initialized
        if not marketplace_data.get("name"):
            print("❌ Marketplace not initialized or invalid")
            print(f"   Checked location: {marketplace_path}")
            if marketplace_path.exists():
                print(f"   File exists but 'name' field is empty")
                print(f"   Run 'init' command to initialize properly")
            else:
                print(f"   File not found - Run 'init' command first")
            print(f"\n   Repository root: {repo_root}")
            print(f"   Current directory: {Path.cwd()}")
            return 1

        # Validate skills exist
        for skill in args.skills:
            validate_skill_exists(skill, repo_root)

        if create_plugin(marketplace_data, args.name, args.description, args.skills):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            return 1

    elif args.command == "add-skill":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found")
            print(f"   Expected location: {marketplace_path}")
            print(f"   Repository root: {repo_root}")
            print(f"   Current directory: {Path.cwd()}")
            print(f"\n   Run 'init' command first or specify correct --path")
            return 1

        marketplace_data = load_marketplace(marketplace_path)

        # Validate skill exists
        validate_skill_exists(args.skill, repo_root)

        if add_skill_to_plugin(marketplace_data, args.plugin, args.skill):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            return 1

    elif args.command == "update-metadata":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found")
            print(f"   Expected location: {marketplace_path}")
            print(f"   Repository root: {repo_root}")
            print(f"   Current directory: {Path.cwd()}")
            print(f"\n   Run 'init' command first or specify correct --path")
            return 1

        marketplace_data = load_marketplace(marketplace_path)

        # Check if any update requested
        if not args.description and not args.version and not args.increment:
            print(
                "❌ No updates specified. Use --description, --version, or --increment"
            )
            return 1

        # Check for conflicting options
        if args.version and args.increment:
            print("❌ Cannot use both --version and --increment")
            return 1

        # Update metadata
        if update_metadata(
            marketplace_data,
            description=args.description,
            version=args.version,
            auto_increment=args.increment,
        ):
            save_marketplace(marketplace_path, marketplace_data)
        else:
            print("❌ No changes made")
            return 1

    elif args.command == "validate":
        if not marketplace_path.exists():
            print(f"❌ No marketplace found")
            print(f"   Expected location: {marketplace_path}")
            print(f"   Repository root: {repo_root}")
            print(f"   Current directory: {Path.cwd()}")
            print(f"\n   Run 'init' command first or specify correct --path")
            return 1

        # Run validation
        is_valid, issues = validate_marketplace(marketplace_path, repo_root, output_format=args.format)

        # Format and print results
        format_validation_output(is_valid, issues, format_type=args.format)

        # Exit with error code if validation failed
        return 0 if is_valid else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
