#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""Marketplace checks that complement `claude plugin validate`.

plugin.json is the single source of truth for a plugin's version, description
and author. marketplace.json entries carry only name, source and category.

Checks:
1. Official validation -- runs `claude plugin validate` on the marketplace
   (strict) and on plugin directories (errors block, warnings are reported)
2. Duplicate metadata -- a marketplace entry must not repeat `version`
3. Version bumps (--check-versions / --staged) -- every plugin changed since
   the base must raise its plugin.json version, and every skill changed since
   the base must raise its SKILL.md metadata.version. A changed plugin's
   description must also fit the marketplace listing (<= 200 characters)
4. Reverse scan -- plugins on disk missing from marketplace.json (--fix adds them)
5. Structure (--check-structure) -- anti-patterns such as shared source paths

The base is `git merge-base HEAD <ref>`, where <ref> defaults to the remote's
default branch (origin/HEAD, falling back to origin/main).

Stdlib-only. Uses pyyaml when available for SKILL.md frontmatter parsing,
falls back to a minimal subset parser.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Directories that indicate discoverable plugin components
COMPONENT_DIRS = ["skills", "commands", "agents", "hooks"]

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")

# plugin-dev plugin-structure guidance: "Keep under 200 characters for marketplace display"
MAX_DESCRIPTION = 200


# -- YAML frontmatter parsing -----------------------------------------------

def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter from a Markdown file."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
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


def skill_version(text: str | None) -> str | None:
    """Return metadata.version (or legacy top-level version) from SKILL.md text."""
    if text is None:
        return None
    fm = parse_frontmatter(text)
    metadata = fm.get("metadata")
    version = metadata.get("version") if isinstance(metadata, dict) else None
    version = version or fm.get("version")
    return str(version) if version else None


def load_manifest(text: str | None) -> dict:
    """Parse plugin.json text; {} when missing or invalid."""
    if text is None:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def manifest_version(text: str | None) -> str | None:
    """Return the version from plugin.json text."""
    version = load_manifest(text).get("version")
    return str(version) if version else None


def parse_semver(version: str) -> tuple[int, int, int] | None:
    """Parse MAJOR.MINOR.PATCH (pre-release/build suffixes are ignored)."""
    m = SEMVER_RE.match(version)
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


# -- Git helpers -------------------------------------------------------------

def git(repo_root: Path, *args: str) -> str | None:
    """Run a git command; return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args], capture_output=True, text=True, cwd=repo_root,
        )
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 else None


def resolve_base(repo_root: Path, ref: str | None) -> str | None:
    """Return the merge-base commit of HEAD and ref (default: remote default branch)."""
    if ref is None:
        head = git(repo_root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
        ref = head.strip() if head else "origin/main"
    base = git(repo_root, "merge-base", "HEAD", ref)
    return base.strip() if base else None


class Snapshot:
    """Read files from the index (staged) or the working tree, and from base."""

    def __init__(self, repo_root: Path, base: str, staged: bool):
        self.repo_root = repo_root
        self.base = base
        self.staged = staged

    def changed_paths(self) -> list[str]:
        if self.staged:
            out = git(self.repo_root, "diff", "--cached", "--name-only", self.base)
            return (out or "").splitlines()
        out = git(self.repo_root, "diff", "--name-only", self.base) or ""
        untracked = git(self.repo_root, "ls-files", "--others", "--exclude-standard") or ""
        return out.splitlines() + untracked.splitlines()

    def current(self, rel: str) -> str | None:
        if self.staged:
            return git(self.repo_root, "show", f":{rel}")
        path = self.repo_root / rel
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def at_base(self, rel: str) -> str | None:
        return git(self.repo_root, "show", f"{self.base}:{rel}")


# -- Checks ------------------------------------------------------------------

def relative_sources(config: dict) -> list[tuple[str, str]]:
    """Return (name, dir) for every entry with a ./relative source."""
    result = []
    for plugin in config.get("plugins", []):
        source = plugin.get("source", "")
        if isinstance(source, str) and source.startswith("./"):
            result.append((plugin.get("name", "unknown"), source[2:].rstrip("/")))
    return result


def check_duplicate_metadata(config: dict) -> list[str]:
    """Entries must not repeat version; plugin.json is the source of truth."""
    errors = []
    for plugin in config.get("plugins", []):
        source = plugin.get("source", "")
        if "version" in plugin and isinstance(source, str) and source.startswith("./"):
            errors.append(
                f"Plugin '{plugin.get('name')}': remove 'version' from its "
                f"marketplace.json entry -- plugin.json is the only version source"
            )
    return errors


def _bump_error(label: str, path: str, old: str | None, new: str | None) -> str | None:
    """Return an error if new is missing or not semver-greater than old."""
    if new is None:
        return f"{label}: no version in {path}"
    new_v = parse_semver(new)
    if new_v is None:
        return f"{label}: version '{new}' in {path} is not MAJOR.MINOR.PATCH"
    if old is None:
        return None  # new plugin or skill
    old_v = parse_semver(old)
    if old_v is not None and new_v <= old_v:
        return (
            f"{label}: changed since base but version {new} is not greater "
            f"than {old} -- bump {path}"
        )
    return None


def check_versions(config: dict, snap: Snapshot) -> tuple[list[str], list[str]]:
    """Require a version bump for every changed plugin and skill, and a
    listing-sized description for every changed plugin.

    Returns (errors, changed_plugin_dirs).
    """
    errors = []
    changed_dirs = []
    changed = snap.changed_paths()

    for name, plugin_dir in relative_sources(config):
        plugin_changes = [p for p in changed if p.startswith(plugin_dir + "/")]
        if not plugin_changes:
            continue

        manifest = f"{plugin_dir}/.claude-plugin/plugin.json"
        current_manifest = snap.current(manifest)
        if current_manifest is None and not (snap.repo_root / plugin_dir).is_dir():
            continue  # plugin removed
        changed_dirs.append(plugin_dir)

        err = _bump_error(
            f"Plugin '{name}'", manifest,
            manifest_version(snap.at_base(manifest)),
            manifest_version(current_manifest),
        )
        if err:
            errors.append(err)

        description = str(load_manifest(current_manifest).get("description", ""))
        if len(description) > MAX_DESCRIPTION:
            errors.append(
                f"Plugin '{name}': description is {len(description)} characters -- "
                f"shorten it to {MAX_DESCRIPTION} or fewer in {manifest} "
                f"(what the plugin does, not how; see plugin-dev plugin-structure)"
            )

        skills_prefix = f"{plugin_dir}/skills/"
        skills = sorted({
            p[len(skills_prefix):].split("/", 1)[0]
            for p in plugin_changes
            if p.startswith(skills_prefix) and "/" in p[len(skills_prefix):]
        })
        for skill in skills:
            skill_md = f"{skills_prefix}{skill}/SKILL.md"
            current_skill = snap.current(skill_md)
            if current_skill is None:
                continue  # skill removed
            err = _bump_error(
                f"Skill '{name}:{skill}'", skill_md,
                skill_version(snap.at_base(skill_md)),
                skill_version(current_skill),
            )
            if err:
                errors.append(err)

    return errors, changed_dirs


def run_official(target: Path, strict: bool) -> tuple[list[str], list[str]]:
    """Run `claude plugin validate --json`; return (errors, warnings)."""
    cmd = ["claude", "plugin", "validate", str(target), "--json"]
    if strict:
        cmd.append("--strict")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 2 or not result.stdout.strip():
        return [f"claude plugin validate {target}: {result.stderr.strip()}"], []

    report = json.loads(result.stdout)
    errors, warnings = [], []
    parts = [report.get("manifest") or {}] + report.get("contents", [])
    for part in parts:
        where = Path(part.get("file", str(target))).name
        for e in part.get("errors", []):
            errors.append(f"{target}: {where} {e.get('path', '')}: {e.get('message')}")
        for w in part.get("warnings", []):
            line = f"{target}: {where} {w.get('path', '')}: {w.get('message')}"
            (errors if strict else warnings).append(line)
    return errors, warnings


def validate_official(repo_root: Path, plugin_dirs: list[str]) -> tuple[list, list]:
    """Validate the marketplace strictly and each plugin directory normally."""
    if shutil.which("claude") is None:
        return [], ["'claude' CLI not found -- skipped claude plugin validate"]
    errors, warnings = run_official(repo_root, strict=True)
    for plugin_dir in plugin_dirs:
        e, w = run_official(repo_root / plugin_dir, strict=False)
        errors += e
        warnings += w
    return errors, warnings


def scan_reverse(config: dict, repo_root: Path) -> list[dict]:
    """Find plugins under plugins/ that marketplace.json doesn't list."""
    existing = {p.get("name") for p in config.get("plugins", [])}
    missing = []
    plugins_dir = repo_root / "plugins"
    if plugins_dir.is_dir():
        for d in sorted(plugins_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            if (d / ".claude-plugin" / "plugin.json").is_file() and d.name not in existing:
                missing.append({"name": d.name, "source": f"./plugins/{d.name}"})
    return missing


def check_structure(config: dict) -> list[str]:
    """Detect anti-patterns like multiple plugins sharing source paths."""
    warnings = []
    source_users = {}
    for plugin in config.get("plugins", []):
        source = plugin.get("source", "")
        if isinstance(source, str):
            source_users.setdefault(source, []).append(plugin.get("name", "?"))
    for source, names in source_users.items():
        if len(names) > 1:
            warnings.append(
                f"Multiple plugins share source '{source}': {', '.join(names)}. "
                f"They share one version -- give each plugin its own directory."
            )
    return warnings


def fix_manifest(config: dict, missing: list[dict], path: Path) -> None:
    """Append missing plugins as minimal {name, source} entries."""
    config["plugins"].extend(missing)
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# -- Output ------------------------------------------------------------------

def format_text(errors: list, warnings: list, missing: list, fixed: bool) -> str:
    lines = []
    if errors:
        lines.append("ERRORS:")
        lines += [f"  [error] {e}" for e in errors]
    if warnings:
        lines.append("WARNINGS:")
        lines += [f"  [warn]  {w}" for w in warnings]
    if missing:
        names = ", ".join(p["name"] for p in missing)
        if fixed:
            lines.append(f"FIXED: added missing plugins: {names}")
        else:
            lines.append(f"NOT IN MANIFEST: {names}")
            lines.append("  Hint: run with --fix to add them")
    if errors:
        lines.append("Validation failed")
    elif warnings or (missing and not fixed):
        lines.append("Validation passed (with warnings)")
    else:
        lines.append("Validation passed")
    return "\n".join(lines)


# -- Main --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Marketplace checks that complement `claude plugin validate`.",
    )
    parser.add_argument(
        "marketplace_path", nargs="?", default=".claude-plugin/marketplace.json",
        help="Path to marketplace.json (default: .claude-plugin/marketplace.json)",
    )
    parser.add_argument("--check-versions", action="store_true",
                        help="Require version bumps for plugins/skills changed "
                             "since the base (working tree)")
    parser.add_argument("--staged", action="store_true",
                        help="Like --check-versions, but reads the git index "
                             "(pre-commit)")
    parser.add_argument("--base", metavar="REF",
                        help="Compare against merge-base of HEAD and REF "
                             "(default: origin/HEAD, then origin/main)")
    parser.add_argument("--fix", action="store_true",
                        help="Add plugins found on disk but missing from the manifest")
    parser.add_argument("--check-structure", action="store_true",
                        help="Detect structural anti-patterns")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    mp_path = Path(args.marketplace_path)
    if not mp_path.is_file():
        print(f"File not found: {mp_path}", file=sys.stderr)
        sys.exit(1)
    repo_root = mp_path.resolve().parent.parent

    # In pre-commit mode, check the manifest being committed, not the working tree
    text = None
    if args.staged:
        rel = mp_path.resolve().relative_to(repo_root).as_posix()
        text = git(repo_root, "show", f":{rel}")
    try:
        config = json.loads(text or mp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {mp_path}: {e}", file=sys.stderr)
        sys.exit(1)

    errors = check_duplicate_metadata(config)
    warnings = []

    plugin_dirs = [d for _, d in relative_sources(config)]
    if args.check_versions or args.staged:
        base = resolve_base(repo_root, args.base)
        if base is None:
            warnings.append("No base commit (is origin fetched?) -- skipped version check")
        else:
            version_errors, plugin_dirs = check_versions(
                config, Snapshot(repo_root, base, staged=args.staged))
            errors += version_errors

    official_errors, official_warnings = validate_official(repo_root, plugin_dirs)
    errors += official_errors
    warnings += official_warnings

    if args.check_structure:
        warnings += check_structure(config)

    missing = scan_reverse(config, repo_root)
    fixed = False
    if args.fix and missing:
        fix_manifest(config, missing, mp_path)
        fixed = True

    if args.format == "json":
        print(json.dumps({
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "missing": [p["name"] for p in missing],
            "fixed": fixed,
        }, indent=2))
    else:
        print(format_text(errors, warnings, missing, fixed))

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
