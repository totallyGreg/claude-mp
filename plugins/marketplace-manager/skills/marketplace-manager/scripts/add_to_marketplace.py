#!/usr/bin/env python3
# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
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
import sys
from pathlib import Path

try:
    import yaml  # noqa: F401 — dependency provided by uv (see /// script block above)
except ImportError:
    print("Error: missing dependencies. Run this script via: uv run add_to_marketplace.py", file=sys.stderr)
    sys.exit(1)

from utils import (
    get_repo_root, print_verbose_info, validate_repo_structure,
    parse_semver, load_marketplace, save_marketplace, find_plugin,
)


def init_marketplace(marketplace_path, name, owner_name, owner_email, description):
    """Initialize a new marketplace.json."""
    marketplace_data = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": name,
        "owner": {"name": owner_name, "email": owner_email},
        "metadata": {
            "version": "1.0.0",
            "description": description,
        },
        "plugins": [],
    }

    save_marketplace(marketplace_path, marketplace_data)
    print(f"✅ Initialized new marketplace: {name}")


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


def extract_skill_version(skill_path, repo_root):
    """Extract version from a skill's SKILL.md frontmatter.

    Returns version string or "1.0.0" as default.
    """
    import yaml

    skill_dir = repo_root / skill_path.lstrip("./")
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return "1.0.0"

    try:
        content = skill_md.read_text()
        if not content.startswith("---"):
            return "1.0.0"

        end = content.find("---", 3)
        if end == -1:
            return "1.0.0"

        frontmatter = yaml.safe_load(content[3:end])
        if not frontmatter:
            return "1.0.0"

        # Check metadata.version first, then deprecated version field
        metadata = frontmatter.get("metadata", {})
        if isinstance(metadata, dict) and "version" in metadata:
            return str(metadata["version"])
        if "version" in frontmatter:
            return str(frontmatter["version"])
    except Exception:
        pass

    return "1.0.0"


def create_plugin(marketplace_data, plugin_name, plugin_description, skill_paths):
    """Create a new plugin with skills."""
    # Check if plugin already exists
    if find_plugin(marketplace_data, plugin_name):
        print(f"❌ Plugin '{plugin_name}' already exists")
        return False

    # Normalize skill paths
    normalized_skills = [f"./{path.strip('./')}" for path in skill_paths]

    # Determine source path
    # For single-skill plugins (1:1 mapping): source = skill path, skills = ["./"]
    # For multi-skill plugins (bundles): source = common parent, skills = relative paths
    if len(normalized_skills) == 1:
        # Single skill plugin - use skill directory as source
        source_path = normalized_skills[0]
        skills_list = ["./"]
    else:
        # Multi-skill bundle - use common parent as source
        source_path = "./"
        skills_list = normalized_skills

    # Extract version from skill frontmatter
    repo_root = Path(marketplace_data.get("_repo_root", "."))
    version = extract_skill_version(normalized_skills[0], repo_root)

    # Inherit author from marketplace owner
    owner = marketplace_data.get("owner", {})

    # Create new plugin with all required fields
    new_plugin = {
        "name": plugin_name,
        "description": plugin_description,
        "category": "productivity",
        "version": version,
        "author": {
            "name": owner.get("name", ""),
            "email": owner.get("email", ""),
        },
        "source": source_path,
        "skills": skills_list,
    }

    marketplace_data["plugins"].append(new_plugin)
    print(f"✅ Created new plugin: {plugin_name}")
    print(f"   Source: {source_path}")
    print(f"   Version: {version}")
    print(f"   Skills: {skills_list}")
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
    """Parse semantic version string into (major, minor, patch) tuple.

    DEPRECATED: Use parse_semver() from utils instead. This wrapper exists
    for backward compatibility with callers that expected (1,0,0) default.
    New code should use parse_semver() directly (returns (0,0,0) on failure).
    """
    return parse_semver(version_str)


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
    """Validate semantic version format (X.Y.Z with optional pre-release).

    Accepts: '1.0.0', '1.0.0-alpha.1', '1.0.0-rc.2'
    Rejects: 'latest', '1.0', 'v1.0.0'
    """
    from utils import validate_semantic_version as _validate
    return _validate(version_str)


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


# Plugin name format per plugin-dev manifest-reference.md
PLUGIN_NAME_PATTERN = r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$'

# Known valid fields for .claude-plugin/plugin.json
# Aligned with plugin-dev manifest-reference.md + official docs
PLUGIN_JSON_KNOWN_FIELDS = {
    # Required
    'name',
    # Recommended metadata
    'version', 'description', 'author', 'license', 'keywords',
    'homepage', 'repository',
    # Component path overrides (supplement defaults, don't replace)
    'commands', 'agents', 'hooks',
    # Server definitions
    'mcpServers', 'lspServers',
}

# Only 'name' is required per plugin-dev minimal example
PLUGIN_JSON_REQUIRED_FIELDS = {'name'}

# marketplace.json root-level required fields per official schema
MARKETPLACE_REQUIRED_FIELDS = {'name', 'owner', 'plugins'}

# marketplace.json plugin entry required fields per official schema
PLUGIN_ENTRY_REQUIRED_FIELDS = {'name', 'source'}

# Known valid fields for marketplace.json root level
# Per official docs: https://code.claude.com/docs/en/plugin-marketplaces
# Only name, owner, and plugins are documented. $schema is standard JSON Schema.
MARKETPLACE_KNOWN_ROOT_FIELDS = {
    '$schema', 'name', 'owner', 'plugins',
}

# Known valid fields for marketplace.json plugin entries
# Per official docs: any plugin.json field is valid here, plus marketplace-specific fields
MARKETPLACE_PLUGIN_KNOWN_FIELDS = {
    'name', 'source', 'description', 'version', 'author',
    'homepage', 'repository', 'license', 'keywords',
    'category', 'tags', 'strict',
    'commands', 'agents', 'hooks', 'mcpServers', 'lspServers',
}


def validate_plugin_json(plugin_json_path, plugin_name):
    """Validate plugin.json against known schema.

    Aligned with plugin-dev manifest-reference.md:
    - Only 'name' is required
    - 'version' and 'description' recommended (warn if missing)
    - Unknown fields warn, not error (per plugin-validator agent)
    - 'author' and 'repository' accept string or object
    - Name format validated per manifest-reference.md regex

    Returns list of issue dicts.
    """
    import re
    issues = []
    try:
        with open(plugin_json_path) as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        issues.append({
            'type': 'error',
            'category': 'plugin_json',
            'field': f'{plugin_name}/plugin.json',
            'message': f"Failed to read plugin.json: {e}"
        })
        return issues

    # Check required fields
    for field in sorted(PLUGIN_JSON_REQUIRED_FIELDS):
        if field not in data or not data[field]:
            issues.append({
                'type': 'error',
                'category': 'plugin_json',
                'field': f'{plugin_name}/plugin.json.{field}',
                'message': f"Required field '{field}' missing from plugin.json"
            })

    # Name format validation
    name = data.get('name', '')
    if name and not re.match(PLUGIN_NAME_PATTERN, name):
        issues.append({
            'type': 'error',
            'category': 'plugin_json',
            'field': f'{plugin_name}/plugin.json.name',
            'message': (
                f"Plugin name '{name}' does not match required format: "
                f"kebab-case, start with letter, a-z0-9 and hyphens only"
            )
        })

    # Recommended fields (warn if missing)
    for field in ('version', 'description'):
        if field not in data or not data[field]:
            issues.append({
                'type': 'warning',
                'category': 'plugin_json',
                'field': f'{plugin_name}/plugin.json.{field}',
                'message': f"Recommended field '{field}' missing from plugin.json"
            })

    # Version format validation (if present)
    if 'version' in data and data['version']:
        if not validate_semantic_version(data['version']):
            issues.append({
                'type': 'warning',
                'category': 'plugin_json',
                'field': f'{plugin_name}/plugin.json.version',
                'message': f"Invalid version format: {data['version']} (expected X.Y.Z or X.Y.Z-prerelease)"
            })

    # Unknown fields — warn, don't error (per plugin-validator agent)
    unknown = set(data.keys()) - PLUGIN_JSON_KNOWN_FIELDS
    for field in sorted(unknown):
        issues.append({
            'type': 'warning',
            'category': 'plugin_json',
            'field': f'{plugin_name}/plugin.json.{field}',
            'message': f"Unknown field '{field}' in plugin.json"
        })

    # Component path overrides validation
    for path_field in ('commands', 'agents'):
        if path_field in data:
            val = data[path_field]
            paths = [val] if isinstance(val, str) else (val if isinstance(val, list) else [])
            for p in paths:
                if isinstance(p, str) and ('..' in p):
                    issues.append({
                        'type': 'error',
                        'category': 'plugin_json',
                        'field': f'{plugin_name}/plugin.json.{path_field}',
                        'message': f"Path '{p}' must not contain '..'"
                    })

    return issues


def validate_marketplace(marketplace_path, repo_root, output_format='text'):
    """Comprehensively validate marketplace.json structure.

    Aligned with official Anthropic schema:
    https://code.claude.com/docs/en/plugin-marketplaces#marketplace-schema

    Required root fields: name, owner, plugins
    Optional metadata: nested under 'metadata' object
    Plugin entries: only name and source required

    Args:
        marketplace_path: Path to marketplace.json
        repo_root: Repository root directory
        output_format: 'text' or 'json'

    Returns:
        Tuple of (is_valid, issues)
    """
    import re
    from utils import extract_frontmatter_version, discover_plugin_skills

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

    # Validate required root fields (per official schema)
    for field in sorted(MARKETPLACE_REQUIRED_FIELDS):
        if field not in marketplace_data or not marketplace_data[field]:
            issues.append({
                'type': 'error',
                'category': 'schema',
                'field': field,
                'message': f"Required field '{field}' is missing or empty"
            })

    # Check for unknown root fields
    unknown_root = set(marketplace_data.keys()) - MARKETPLACE_KNOWN_ROOT_FIELDS
    for field in sorted(unknown_root):
        # Special handling for legacy fields with migration guidance
        if field in ('version', 'description'):
            issues.append({
                'type': 'warning',
                'category': 'schema',
                'field': field,
                'message': (
                    f"Root-level '{field}' is not part of the official marketplace schema. "
                    f"Remove this field — for plugins, set '{field}' in each plugin entry instead."
                )
            })
        elif field == 'metadata':
            issues.append({
                'type': 'warning',
                'category': 'schema',
                'field': field,
                'message': (
                    "Root-level 'metadata' is not part of the official marketplace schema. "
                    "Remove this field — the official schema uses only name, owner, and plugins."
                )
            })
        else:
            issues.append({
                'type': 'warning',
                'category': 'schema',
                'field': field,
                'message': f"Unknown root-level field '{field}'"
            })

    # Validate marketplace name format
    mp_name = marketplace_data.get('name', '')
    if mp_name and not re.match(PLUGIN_NAME_PATTERN, mp_name):
        issues.append({
            'type': 'error',
            'category': 'schema',
            'field': 'name',
            'message': (
                f"Marketplace name '{mp_name}' must be kebab-case: "
                f"lowercase letters, numbers, and hyphens only"
            )
        })

    # Validate owner
    if 'owner' in marketplace_data:
        owner = marketplace_data['owner']
        if not isinstance(owner, dict):
            issues.append({
                'type': 'error',
                'category': 'schema',
                'field': 'owner',
                'message': "Owner must be an object with 'name' (required) and 'email' (optional)"
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
            p_name = plugin.get('name', '')

            # Required: name
            if not p_name:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.name',
                    'message': f"Plugin at index {idx} missing required 'name' field"
                })
            else:
                # Name format validation
                if not re.match(PLUGIN_NAME_PATTERN, p_name):
                    issues.append({
                        'type': 'error',
                        'category': 'schema',
                        'field': f'{plugin_prefix}.name',
                        'message': (
                            f"Plugin name '{p_name}' must be kebab-case: "
                            f"lowercase letters, numbers, and hyphens only"
                        )
                    })
                # Duplicate check
                if p_name in plugin_names:
                    issues.append({
                        'type': 'error',
                        'category': 'duplicate',
                        'field': f'{plugin_prefix}.name',
                        'value': p_name,
                        'message': f"Duplicate plugin name: {p_name}"
                    })
                plugin_names.add(p_name)

            # Required: source
            source = plugin.get('source')
            if not source:
                issues.append({
                    'type': 'error',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.source',
                    'message': f"Plugin '{p_name or 'unnamed'}' missing required 'source' field"
                })

            # Validate source (relative paths validated thoroughly; objects accepted)
            source_dir = None
            if isinstance(source, str):
                if not source.startswith('./'):
                    issues.append({
                        'type': 'error',
                        'category': 'schema',
                        'field': f'{plugin_prefix}.source',
                        'value': source,
                        'message': f"Relative source path must start with './' (got: {source})"
                    })
                elif '..' in source:
                    issues.append({
                        'type': 'error',
                        'category': 'schema',
                        'field': f'{plugin_prefix}.source',
                        'value': source,
                        'message': f"Source path must not contain '..' (got: {source})"
                    })
                else:
                    source_path_clean = source.lstrip('./')
                    source_dir = repo_root / source_path_clean if source_path_clean else repo_root
                    if not source_dir.exists():
                        issues.append({
                            'type': 'error',
                            'category': 'missing_file',
                            'field': f'{plugin_prefix}.source',
                            'value': source,
                            'message': f"Source directory not found: {source_dir}"
                        })
            elif isinstance(source, dict):
                # Object source types (github, url, git-subdir, npm) — accept without
                # detailed validation per plan scope boundaries (YAGNI)
                pass

            # Unknown plugin entry fields — warn, not error
            if 'skills' in plugin:
                issues.append({
                    'type': 'warning',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.skills',
                    'message': (
                        "The 'skills' field is not part of the official marketplace schema. "
                        "Skills are defined in the plugin directory and auto-discovered by Claude Code. "
                        "Remove this field from the plugin entry."
                    )
                })
            unknown_plugin = set(plugin.keys()) - MARKETPLACE_PLUGIN_KNOWN_FIELDS
            for field in sorted(unknown_plugin):
                if field == 'skills':
                    continue  # Already handled above with specific message
                issues.append({
                    'type': 'warning',
                    'category': 'schema',
                    'field': f'{plugin_prefix}.{field}',
                    'message': f"Unknown field '{field}' in plugin entry"
                })

            # Version format validation (if present)
            if 'version' in plugin and plugin['version']:
                if not validate_semantic_version(plugin['version']):
                    issues.append({
                        'type': 'warning',
                        'category': 'version',
                        'field': f'{plugin_prefix}.version',
                        'value': plugin['version'],
                        'message': f"Invalid version format: {plugin['version']}"
                    })

            # Author validation — accept string or object
            if 'author' in plugin:
                author = plugin['author']
                if isinstance(author, dict):
                    if 'email' in author and not validate_email(author['email']):
                        issues.append({
                            'type': 'warning',
                            'category': 'format',
                            'field': f'{plugin_prefix}.author.email',
                            'value': author['email'],
                            'message': f"Invalid email format: {author['email']}"
                        })
                elif not isinstance(author, str):
                    issues.append({
                        'type': 'warning',
                        'category': 'schema',
                        'field': f'{plugin_prefix}.author',
                        'message': "Author must be a string or object"
                    })

            # Validate plugin.json schema (if source resolves to local dir)
            if source_dir and source_dir.exists():
                plugin_json_path = source_dir / '.claude-plugin' / 'plugin.json'
                if plugin_json_path.exists():
                    issues.extend(validate_plugin_json(
                        plugin_json_path, p_name or f'plugins[{idx}]'
                    ))

                # Validate discovered skills' SKILL.md frontmatter
                discovered_skills = discover_plugin_skills(source_dir)
                for skill_path in discovered_skills:
                    skill_path_clean = skill_path.lstrip('./')
                    skill_dir = source_dir / skill_path_clean if skill_path_clean else source_dir
                    skill_md = skill_dir / 'SKILL.md'
                    if skill_md.exists():
                        version, is_nonstandard = extract_frontmatter_version(skill_md)
                        if not version:
                            issues.append({
                                'type': 'warning',
                                'category': 'metadata',
                                'field': f'{plugin_prefix}',
                                'value': skill_path,
                                'message': f"No version found in {skill_path}/SKILL.md frontmatter"
                            })
                        elif is_nonstandard:
                            issues.append({
                                'type': 'warning',
                                'category': 'nonstandard',
                                'field': f'{plugin_prefix}',
                                'value': skill_path,
                                'message': (
                                    f"Skill uses root-level 'version' field (not in AgentSkills spec). "
                                    f"Use 'metadata.version' instead."
                                )
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

        # Pass repo_root for version extraction, then remove before saving
        marketplace_data["_repo_root"] = str(repo_root)
        if create_plugin(marketplace_data, args.name, args.description, args.skills):
            marketplace_data.pop("_repo_root", None)
            save_marketplace(marketplace_path, marketplace_data)
        else:
            marketplace_data.pop("_repo_root", None)
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
