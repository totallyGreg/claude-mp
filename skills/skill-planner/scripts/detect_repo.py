#!/usr/bin/env python3
"""
Detect skill location and determine work mode

This script helps skill-planner determine where a skill is located
and whether it should work in repository or ask the user.

Usage:
    python3 detect_repo.py <skill-name>

Returns JSON with detection results.

Week 1 Implementation Status:
    [x] Repository detection
    [x] Marketplace detection
    [x] Installed plugin detection
    [x] Work mode recommendation
"""

import os
import sys
import json
from pathlib import Path


def find_repository_root():
    """Find git repository root"""
    current = Path.cwd()

    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent

    return None


def find_skill_in_repository(repo_root, skill_name):
    """
    Check if skill exists in repository

    Returns: Path to skill or None
    """
    if not repo_root:
        return None

    skills_dir = repo_root / 'skills' / skill_name
    if skills_dir.exists() and (skills_dir / 'SKILL.md').exists():
        return skills_dir

    return None


def find_skill_in_marketplace(repo_root):
    """
    Load marketplace.json and find all skills in own marketplace

    Returns: dict of skill_name -> metadata
    """
    if not repo_root:
        return {}

    marketplace_file = repo_root / '.claude-plugin' / 'marketplace.json'
    if not marketplace_file.exists():
        return {}

    try:
        with open(marketplace_file) as f:
            marketplace = json.load(f)

        skills = {}
        for plugin in marketplace.get('plugins', []):
            plugin_name = plugin.get('name', '')
            for skill in plugin.get('skills', []):
                skill_name = skill.get('name', '')
                if skill_name:
                    skills[skill_name] = {
                        'plugin': plugin_name,
                        'version': skill.get('version', 'unknown'),
                        'metadata': skill
                    }

        return skills
    except Exception as e:
        print(f"Warning: Could not read marketplace.json: {e}", file=sys.stderr)
        return {}


def find_installed_plugins():
    """
    Find installed plugins

    Claude plugins are typically installed in:
    - ~/.config/claude-code/plugins/
    - or similar location

    Returns: dict of skill_name -> install_path
    """
    # Common plugin installation locations
    possible_locations = [
        Path.home() / '.config' / 'claude-code' / 'plugins',
        Path.home() / '.claude-code' / 'plugins',
        Path.home() / 'Library' / 'Application Support' / 'claude-code' / 'plugins',
    ]

    installed = {}

    for location in possible_locations:
        if not location.exists():
            continue

        # Look for plugin directories
        for plugin_dir in location.iterdir():
            if not plugin_dir.is_dir():
                continue

            # Look for skills in this plugin
            skills_dir = plugin_dir / 'skills'
            if skills_dir.exists():
                for skill_dir in skills_dir.iterdir():
                    if skill_dir.is_dir() and (skill_dir / 'SKILL.md').exists():
                        skill_name = skill_dir.name
                        installed[skill_name] = str(skill_dir)

    return installed


def detect_skill_location(skill_name):
    """
    Detect where a skill is located and recommend work mode

    Returns: {
        'skill_name': str,
        'found': bool,
        'repository_path': str or None,
        'in_marketplace': bool,
        'marketplace_info': dict or None,
        'installed_path': str or None,
        'work_mode': 'repository' | 'ask_clone' | 'ask_new' | 'not_found',
        'recommendation': str
    }
    """
    result = {
        'skill_name': skill_name,
        'found': False,
        'repository_path': None,
        'in_marketplace': False,
        'marketplace_info': None,
        'installed_path': None,
        'work_mode': 'not_found',
        'recommendation': ''
    }

    # Find repository
    repo_root = find_repository_root()

    # Check repository
    repo_path = find_skill_in_repository(repo_root, skill_name)
    if repo_path:
        result['repository_path'] = str(repo_path)
        result['found'] = True

    # Check marketplace
    marketplace_skills = find_skill_in_marketplace(repo_root)
    if skill_name in marketplace_skills:
        result['in_marketplace'] = True
        result['marketplace_info'] = marketplace_skills[skill_name]
        result['found'] = True

    # Check installed
    installed_skills = find_installed_plugins()
    if skill_name in installed_skills:
        result['installed_path'] = installed_skills[skill_name]
        result['found'] = True

    # Determine work mode
    if result['repository_path']:
        # Skill is in our repository - always work there
        result['work_mode'] = 'repository'
        result['recommendation'] = f"Work in repository: {result['repository_path']}"

    elif result['in_marketplace'] and not result['repository_path']:
        # In marketplace but not found in repo - should not happen, but ask
        result['work_mode'] = 'ask_clone'
        result['recommendation'] = "Skill is in marketplace but not found in repository. Clone or check repository?"

    elif result['installed_path'] and not result['in_marketplace']:
        # Installed but not from our marketplace - ask user
        result['work_mode'] = 'ask_clone'
        result['recommendation'] = f"Skill installed from external source at {result['installed_path']}. Clone to repository to work on it?"

    else:
        # Unknown skill
        result['work_mode'] = 'ask_new'
        result['recommendation'] = f"Skill '{skill_name}' not found. Create new skill in repository?"

    return result


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python3 detect_repo.py <skill-name>")
        print("")
        print("Example:")
        print("  python3 detect_repo.py skillsmith")
        sys.exit(1)

    skill_name = sys.argv[1]

    try:
        result = detect_skill_location(skill_name)

        # Output as JSON
        print(json.dumps(result, indent=2))

    except Exception as e:
        error_result = {
            'skill_name': skill_name,
            'found': False,
            'error': str(e)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
