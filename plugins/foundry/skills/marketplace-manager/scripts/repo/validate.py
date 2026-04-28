#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Validate Claude Code marketplace.json against the official Anthropic schema.

Performs three checks:
1. Schema validation -- required fields, known fields, naming, versions
2. Forward validation -- plugin source paths resolve to real directories
3. Reverse scan -- detect extensions on disk not listed in the manifest

Use --fix to auto-add missing plugins. Use --staged for pre-commit checks.
Use --check-structure to detect anti-patterns like shared source paths.

Stdlib-only. No external dependencies required (uses pyyaml when available
for SKILL.md frontmatter parsing, falls back to a minimal subset parser).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# -- Schema constants (official Anthropic marketplace schema) ----------------

REQUIRED_ROOT = {"name", "owner", "plugins"}
KNOWN_ROOT = {"name", "owner", "plugins", "$schema", "metadata"}
KNOWN_METADATA = {"description", "version", "pluginRoot"}

REQUIRED_PLUGIN = {"name", "source"}
KNOWN_PLUGIN = {
    "name", "source", "description", "version", "author", "homepage",
    "repository", "license", "keywords", "category", "tags", "strict",
    "commands", "agents", "hooks", "mcpServers", "lspServers",
}

NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^v?\d+\.\d+\.\d+")

# Directories that indicate discoverable plugin components
COMPONENT_DIRS = ["skills", "commands", "agents", "hooks"]
COMPONENT_FILES = [".mcp.json", ".lsp.json", "settings.json"]


# -- YAML frontmatter parsing -----------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a Markdown file."""
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    raw = text[3:end]
    try:
        import yaml
        return yaml.safe_load(raw) or {}
    except ImportError:
        return _parse_frontmatter_stdlib(raw)


def _parse_frontmatter_stdlib(raw: str) -> dict:
    """Minimal YAML subset parser -- flat keys and one level of nesting.

    Handles:  name: value, metadata:\n  version: "1.0.0", quoted/unquoted
    Skips:    multi-line strings, anchors, aliases, sequences
    """
    result = {}
    current_map = None
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if ":" not in stripped:
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip().strip("\"'")
        if indent == 0:
            if val:
                result[key] = val
                current_map = None
            else:
                result[key] = {}
                current_map = result[key]
        elif indent > 0 and isinstance(current_map, dict):
            if val:
                current_map[key] = val
    return result


# -- Validation functions ----------------------------------------------------

def validate_schema(config: dict, repo_root: Path) -> tuple[list, list]:
    """Validate marketplace.json against the official Anthropic schema."""
    errors = []
    warnings = []

    # Required root fields
    for field in REQUIRED_ROOT:
        if field not in config:
            errors.append(f"Missing required root field: '{field}'")

    # Unknown root fields
    for field in config:
        if field not in KNOWN_ROOT:
            if field in ("version", "description"):
                warnings.append(
                    f"Root-level '{field}' is not in the official schema. "
                    f"Move to metadata.{field} per official schema."
                )
            else:
                warnings.append(f"Unknown root field: '{field}'")

    # Owner validation
    owner = config.get("owner")
    if isinstance(owner, dict) and "name" not in owner:
        errors.append("owner object missing required 'name' field")

    # Root name format
    root_name = config.get("name", "")
    if root_name and not NAME_RE.match(root_name):
        warnings.append(
            f"Marketplace name '{root_name}' is not kebab-case "
            f"(expected pattern: {NAME_RE.pattern})"
        )

    # Metadata validation
    metadata = config.get("metadata")
    if isinstance(metadata, dict):
        for field in metadata:
            if field not in KNOWN_METADATA:
                warnings.append(f"Unknown metadata field: '{field}'")

    # Plugin entries
    plugins = config.get("plugins", [])
    if not isinstance(plugins, list):
        errors.append("'plugins' must be an array")
        return errors, warnings

    seen_names = {}
    plugin_root = ""
    if isinstance(metadata, dict):
        plugin_root = metadata.get("pluginRoot", "")

    for i, plugin in enumerate(plugins):
        label = plugin.get("name", f"plugins[{i}]")

        # Required plugin fields
        for field in REQUIRED_PLUGIN:
            if field not in plugin:
                errors.append(f"Plugin '{label}': missing required field '{field}'")

        # Unknown plugin fields
        for field in plugin:
            if field not in KNOWN_PLUGIN:
                if field == "skills":
                    warnings.append(
                        f"Plugin '{label}': the 'skills' field is not part of "
                        f"the official marketplace schema. Skills are "
                        f"auto-discovered from skills/*/SKILL.md. "
                        f"Consider removing this field."
                    )
                else:
                    warnings.append(
                        f"Plugin '{label}': unknown field '{field}'"
                    )

        # Name format
        name = plugin.get("name", "")
        if name and not NAME_RE.match(name):
            warnings.append(
                f"Plugin '{label}': name is not kebab-case "
                f"(expected pattern: {NAME_RE.pattern})"
            )

        # Duplicate name detection
        if name:
            if name in seen_names:
                errors.append(
                    f"Plugin '{name}': duplicate name "
                    f"(first at index {seen_names[name]})"
                )
            else:
                seen_names[name] = i

        # Version format
        version = plugin.get("version", "")
        if version:
            if not SEMVER_RE.match(version):
                warnings.append(
                    f"Plugin '{label}': version '{version}' "
                    f"does not look like semver"
                )
            elif version.startswith("v"):
                warnings.append(
                    f"Plugin '{label}': version '{version}' has 'v' prefix; "
                    f"prefer '{''.join(version[1:])}'"
                )

        # Source path validation (relative paths only)
        source = plugin.get("source", "")
        if isinstance(source, str) and source.startswith("./"):
            if ".." in source:
                errors.append(
                    f"Plugin '{label}': source path must not contain '..'"
                )
            resolved = repo_root / source
            if plugin_root and not source.startswith("./"):
                resolved = repo_root / plugin_root / source
            if not resolved.is_dir():
                errors.append(
                    f"Plugin '{label}': source directory not found: {source}"
                )

    return errors, warnings


def validate_forward(config: dict, repo_root: Path) -> tuple[list, list]:
    """Check that plugin source directories have discoverable components."""
    errors = []
    warnings = []

    for plugin in config.get("plugins", []):
        name = plugin.get("name", "unknown")
        source = plugin.get("source", "")

        if not isinstance(source, str) or not source.startswith("./"):
            continue

        source_dir = repo_root / source
        if not source_dir.is_dir():
            continue  # Already caught by schema validation

        # Check for any discoverable components
        has_components = False
        for d in COMPONENT_DIRS:
            if (source_dir / d).is_dir():
                has_components = True
                break
        if not has_components:
            for f in COMPONENT_FILES:
                if (source_dir / f).exists():
                    has_components = True
                    break
        if not has_components and (source_dir / ".claude-plugin").is_dir():
            has_components = True

        if not has_components:
            warnings.append(
                f"Plugin '{name}': source directory '{source}' has no "
                f"discoverable components (skills/, commands/, agents/, "
                f"hooks/, .mcp.json, etc.)"
            )

    return errors, warnings


def scan_reverse(config: dict, repo_root: Path) -> list[dict]:
    """Find extensions on disk not listed in marketplace.json."""
    existing = {p.get("name") for p in config.get("plugins", [])}
    missing = []

    # Scan plugins/*/
    plugins_dir = repo_root / "plugins"
    if plugins_dir.is_dir():
        for d in sorted(plugins_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            has_plugin = (d / "skills").is_dir() or (d / ".claude-plugin").is_dir()
            if has_plugin and d.name not in existing:
                missing.append({
                    "name": d.name,
                    "source": f"./plugins/{d.name}",
                })

    # Scan root skills/*/ (legacy flat layout)
    skills_dir = repo_root / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if (d / "SKILL.md").exists() and d.name not in existing:
                missing.append({
                    "name": d.name,
                    "source": f"./skills/{d.name}",
                })

    # Scan mcp-servers/*/
    servers_dir = repo_root / "mcp-servers"
    if servers_dir.is_dir():
        for d in sorted(servers_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            has_manifest = (
                (d / "package.json").exists()
                or (d / "pyproject.toml").exists()
            )
            if has_manifest and d.name not in existing:
                missing.append({
                    "name": d.name,
                    "source": f"./mcp-servers/{d.name}",
                })

    # Scan commands/*.md at root level
    commands_dir = repo_root / "commands"
    if commands_dir.is_dir():
        for f in sorted(commands_dir.glob("*.md")):
            if f.name.lower() == "readme.md":
                continue
            if f.stem not in existing:
                missing.append({
                    "name": f.stem,
                    "source": "./",
                })

    return missing


def check_structure(config: dict) -> list[str]:
    """Detect anti-patterns like multiple plugins sharing source paths."""
    warnings = []
    source_users = {}

    for plugin in config.get("plugins", []):
        source = plugin.get("source", "")
        if not isinstance(source, str):
            continue
        source_users.setdefault(source, []).append(plugin.get("name", "?"))

    for source, names in source_users.items():
        if len(names) > 1:
            warnings.append(
                f"Multiple plugins share source '{source}': "
                f"{', '.join(names)}. This causes version enforcement "
                f"conflicts. Give each plugin its own directory."
            )

    return warnings


def check_staged(config: dict, repo_root: Path) -> list[str]:
    """Check git staged files for version bumps when content changed."""
    warnings = []
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=repo_root,
        )
        if result.returncode != 0:
            return []
        staged = set(result.stdout.strip().splitlines())
    except FileNotFoundError:
        return []

    if not staged:
        return []

    for plugin in config.get("plugins", []):
        source = plugin.get("source", "")
        if not isinstance(source, str) or not source.startswith("./"):
            continue

        source_rel = source.lstrip("./")
        plugin_staged = [f for f in staged if f.startswith(source_rel + "/")]
        if not plugin_staged:
            continue

        name = plugin.get("name", "unknown")
        # Check if version-bearing files are also staged
        skill_staged = [
            f for f in plugin_staged if f.endswith("SKILL.md")
        ]
        pjson_staged = [
            f for f in plugin_staged
            if f.endswith("plugin.json")
            and ".claude-plugin/" in f
        ]

        # Content files changed but no version file staged
        content_changed = [
            f for f in plugin_staged
            if not f.endswith("SKILL.md")
            and not (f.endswith("plugin.json") and ".claude-plugin/" in f)
        ]

        if content_changed and not skill_staged and not pjson_staged:
            warnings.append(
                f"Plugin '{name}': content files changed but no version bump "
                f"detected. Stage a SKILL.md or plugin.json with an updated "
                f"version."
            )

    return warnings


# -- Auto-fix ----------------------------------------------------------------

def fix_manifest(config: dict, missing: list[dict], path: Path) -> None:
    """Add missing plugins and write sorted marketplace.json."""
    config["plugins"].extend(missing)
    config["plugins"].sort(key=lambda p: p.get("name", ""))
    with open(path, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        f.write("\n")


# -- Output formatting -------------------------------------------------------

def format_text(errors: list, warnings: list, missing: list,
                structure: list, staged: list, fixed: bool) -> str:
    """Format results as human-readable text."""
    lines = []
    if errors:
        lines.append("ERRORS:")
        for e in errors:
            lines.append(f"  [error] {e}")
    if warnings:
        lines.append("WARNINGS:")
        for w in warnings:
            lines.append(f"  [warn]  {w}")
    if structure:
        lines.append("STRUCTURE:")
        for s in structure:
            lines.append(f"  [warn]  {s}")
    if staged:
        lines.append("STAGED:")
        for s in staged:
            lines.append(f"  [warn]  {s}")
    if missing:
        names = ", ".join(p["name"] for p in missing)
        if fixed:
            lines.append(f"FIXED: added missing plugins: {names}")
        else:
            lines.append(f"NOT IN MANIFEST: {names}")
            lines.append("  Hint: run with --fix to auto-add missing plugins")
    if not errors and not warnings and not missing and not structure and not staged:
        lines.append("Marketplace configuration is valid")
    elif not errors:
        lines.append("Validation passed (with warnings)")
    return "\n".join(lines)


def format_json(errors: list, warnings: list, missing: list,
                structure: list, staged: list, fixed: bool) -> str:
    """Format results as JSON for CI consumption."""
    return json.dumps({
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "missing": [p["name"] for p in missing],
        "structure_warnings": structure,
        "staged_warnings": staged,
        "fixed": fixed,
    }, indent=2)


# -- Main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate marketplace.json against the official "
                    "Anthropic marketplace schema.",
    )
    parser.add_argument(
        "marketplace_path", nargs="?",
        default=".claude-plugin/marketplace.json",
        help="Path to marketplace.json "
             "(default: .claude-plugin/marketplace.json)",
    )
    parser.add_argument("--fix", action="store_true",
                        help="Auto-add missing plugins to the manifest")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--staged", action="store_true",
                        help="Check staged files for version bumps")
    parser.add_argument("--check-structure", action="store_true",
                        help="Detect structural anti-patterns")
    args = parser.parse_args()

    mp_path = Path(args.marketplace_path)
    if not mp_path.exists():
        print(f"File not found: {mp_path}", file=sys.stderr)
        sys.exit(1)

    repo_root = mp_path.parent.parent

    try:
        with open(mp_path) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {mp_path}: {e}", file=sys.stderr)
        sys.exit(1)

    # Run validations
    schema_errors, schema_warnings = validate_schema(config, repo_root)
    fwd_errors, fwd_warnings = validate_forward(config, repo_root)
    missing = scan_reverse(config, repo_root)

    all_errors = schema_errors + fwd_errors
    all_warnings = schema_warnings + fwd_warnings

    structure_warnings = []
    if args.check_structure:
        structure_warnings = check_structure(config)

    staged_warnings = []
    if args.staged:
        staged_warnings = check_staged(config, repo_root)

    # Auto-fix
    fixed = False
    if args.fix and missing:
        fix_manifest(config, missing, mp_path)
        fixed = True

    # Output
    if args.format == "json":
        print(format_json(all_errors, all_warnings, missing,
                          structure_warnings, staged_warnings, fixed))
    else:
        print(format_text(all_errors, all_warnings, missing,
                          structure_warnings, staged_warnings, fixed))

    # Exit code: 1 on errors (warnings are OK)
    if all_errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
