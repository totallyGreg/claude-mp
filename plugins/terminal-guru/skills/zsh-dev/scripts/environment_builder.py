#!/usr/bin/env python3
"""
Environment Builder - Create isolated zsh test environments using ZDOTDIR.

This module builds isolated test environments by:
1. Creating a unique ZDOTDIR for each test
2. Copying user's zsh configuration files
3. Setting up plugin directories
4. Creating metadata for tracking

All test logic is in Python to avoid shell-testing-shell circular dependency.
"""

import shutil
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class EnvironmentBuilder:
    """Build isolated zsh test environments using ZDOTDIR."""

    def __init__(self, base_dir: str = "~/.terminal-guru/test-environments"):
        """
        Initialize environment builder.

        Args:
            base_dir: Base directory for test environments
        """
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_environment(self, test_name: str, source_config: Optional[str] = None) -> str:
        """
        Create isolated ZDOTDIR test environment.

        Args:
            test_name: Name for this test environment
            source_config: Path to source zsh config directory (default: $HOME)

        Returns:
            Path to created ZDOTDIR
        """
        # Generate unique directory name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        env_name = f"{test_name}-{timestamp}"
        env_path = self.base_dir / env_name

        # Create environment structure
        env_path.mkdir(parents=True, exist_ok=True)
        zdotdir = env_path / "zdotdir"
        zdotdir.mkdir(exist_ok=True)

        # Create subdirectories
        (env_path / "plugins").mkdir(exist_ok=True)
        (env_path / "logs").mkdir(exist_ok=True)
        (env_path / "results").mkdir(exist_ok=True)
        (env_path / "diffs").mkdir(exist_ok=True)

        # Copy configuration files
        source = Path(source_config).expanduser() if source_config else Path.home()
        self.copy_config_files(source, zdotdir)

        # Copy plugins if they exist
        self.copy_plugins(source, env_path / "plugins")

        # Create metadata
        metadata = {
            'test_name': test_name,
            'created': datetime.now().isoformat(),
            'source_config': str(source),
            'zdotdir': str(zdotdir),
            'env_path': str(env_path)
        }
        self.create_metadata(env_path, metadata)

        return str(zdotdir)

    def copy_config_files(self, source: Path, dest: Path) -> None:
        """
        Copy zsh configuration files preserving permissions.

        Args:
            source: Source directory (typically $HOME)
            dest: Destination ZDOTDIR
        """
        # Files to copy
        config_files = ['.zshenv', '.zshrc', '.zprofile', '.zlogin', '.zlogout']

        for config_file in config_files:
            src_file = source / config_file
            if src_file.exists():
                dest_file = dest / config_file
                shutil.copy2(src_file, dest_file)
                print(f"Copied {config_file} to {dest}")

        # Copy functions directory if it exists
        zsh_functions = source / '.zsh' / 'functions'
        if zsh_functions.exists():
            dest_functions = dest / 'functions'
            shutil.copytree(zsh_functions, dest_functions, dirs_exist_ok=True)
            print(f"Copied functions directory to {dest}")

    def copy_plugins(self, source: Path, dest: Path) -> None:
        """
        Copy plugin directories (oh-my-zsh, zinit, etc.).

        Args:
            source: Source directory (typically $HOME)
            dest: Destination plugins directory
        """
        # Common plugin locations
        plugin_locations = [
            '.oh-my-zsh',
            '.zinit',
            '.zplug',
            '.antigen',
            '.zsh/plugins'
        ]

        for plugin_dir in plugin_locations:
            src_plugin = source / plugin_dir
            if src_plugin.exists():
                dest_plugin = dest / plugin_dir
                try:
                    shutil.copytree(src_plugin, dest_plugin, dirs_exist_ok=True)
                    print(f"Copied plugin directory: {plugin_dir}")
                except Exception as e:
                    print(f"Warning: Could not copy {plugin_dir}: {e}")

    def create_metadata(self, env_path: Path, metadata: Dict) -> None:
        """
        Create metadata.json for test environment.

        Args:
            env_path: Path to test environment
            metadata: Metadata dictionary
        """
        metadata_file = env_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def list_environments(self) -> List[Dict]:
        """
        List all test environments.

        Returns:
            List of environment metadata dictionaries
        """
        environments = []

        for env_dir in self.base_dir.iterdir():
            if env_dir.is_dir():
                metadata_file = env_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        environments.append(json.load(f))

        return environments

    def cleanup_environment(self, env_path: str) -> None:
        """
        Remove test environment directory.

        Args:
            env_path: Path to test environment to remove
        """
        env_dir = Path(env_path)
        if env_dir.exists():
            shutil.rmtree(env_dir)
            print(f"Removed test environment: {env_path}")


def main():
    """Command-line interface for environment builder."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Create isolated zsh test environments using ZDOTDIR'
    )
    parser.add_argument(
        '--create',
        metavar='NAME',
        help='Create new test environment with given name'
    )
    parser.add_argument(
        '--source',
        metavar='DIR',
        help='Source config directory (default: $HOME)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all test environments'
    )
    parser.add_argument(
        '--cleanup',
        metavar='PATH',
        help='Remove test environment at given path'
    )

    args = parser.parse_args()
    builder = EnvironmentBuilder()

    if args.create:
        zdotdir = builder.create_environment(args.create, args.source)
        print(f"\nTest environment created!")
        print(f"ZDOTDIR: {zdotdir}")
        print(f"\nTo use this environment:")
        print(f"  ZDOTDIR={zdotdir} zsh")

    elif args.list:
        environments = builder.list_environments()
        if environments:
            print("\nTest Environments:")
            for env in environments:
                print(f"  - {env['test_name']}")
                print(f"    Created: {env['created']}")
                print(f"    ZDOTDIR: {env['zdotdir']}")
        else:
            print("No test environments found")

    elif args.cleanup:
        builder.cleanup_environment(args.cleanup)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
