# /// script
# dependencies = [
#   "pyyaml>=6.0.1",
# ]
# ///
"""
Shared utilities for agentsmith evaluation.

Provides agent file resolution, baseline management, and plugin root discovery.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def find_agent_file(path: str) -> Path:
    """Resolve an agent path to the actual .md file.

    Handles both flat and directory-based agent layouts:
      - Direct .md file path: return as-is if it exists
      - Directory with AGENT.md inside: return AGENT.md
      - Directory whose name matches a sibling .md: return <dirname>.md in parent

    Raises:
        FileNotFoundError: if no agent file can be resolved
    """
    p = Path(path).resolve()

    # Direct .md file
    if p.is_file() and p.suffix == '.md':
        return p

    # Directory-based: check for AGENT.md inside
    if p.is_dir():
        agent_md = p / 'AGENT.md'
        if agent_md.is_file():
            return agent_md

        # Flat pattern: <parent>/agents/<name>.md when given <parent>/agents/<name>/
        flat_md = p.parent / f'{p.name}.md'
        if flat_md.is_file():
            return flat_md

    raise FileNotFoundError(
        f"No agent file found at '{path}'. "
        f"Expected a .md file, a directory with AGENT.md, or a directory "
        f"whose name matches a sibling .md file."
    )


def find_plugin_root(path: str) -> Path | None:
    """Walk up from path to find the plugin root containing .claude-plugin/plugin.json.

    Returns the plugin root directory, or None if not found.
    """
    current = Path(path).resolve()
    if current.is_file():
        current = current.parent

    while current != current.parent:
        plugin_json = current / '.claude-plugin' / 'plugin.json'
        if plugin_json.is_file():
            return current
        current = current.parent

    return None


def load_baselines(plugin_dir: Path) -> dict:
    """Load .agentsmith-baselines.json from a plugin directory.

    Returns an empty dict if the file does not exist or is malformed.
    """
    baseline_file = plugin_dir / '.agentsmith-baselines.json'
    if not baseline_file.is_file():
        return {}

    try:
        with open(baseline_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_baselines(plugin_dir: Path, baselines: dict) -> None:
    """Save baselines to .agentsmith-baselines.json in the plugin directory."""
    baseline_file = plugin_dir / '.agentsmith-baselines.json'
    with open(baseline_file, 'w') as f:
        json.dump(baselines, f, indent=2)
        f.write('\n')
