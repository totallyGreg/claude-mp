#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///

"""
Count live mentions of renamed things (stale names) and ratchet the count down.

The registry is the vault itself: any note whose frontmatter has `formerly:`
(a string or list) declares those old names as replaced by that note.

    title: new-tool
    formerly: [old-tool, older-tool]

Every mention of an old name outside history counts as one hit. History is
exempt: files whose name starts with a date (YYYY-MM-DD: daily notes, dated
plans and brainstorms), folders whose name contains "archive", version-history
table rows (`| 1.2.0 | …`), notes marked `historical: true` (a record kept
as written, e.g. answers given for a past review), the canonical note's own
frontmatter, and any --exempt prefix.

The count may never rise above the stored baseline. When it falls,
--update-baseline lowers the baseline to match (it never raises it).

Repo mode (no vault, e.g. a pre-commit hook) reads a committed registry
instead; its directory is the root that gets scanned:

    {"names": {"old-tool": "new-tool"}, "exempt": ["docs/lessons/"], "baseline": 3}

Usage:
    uv run check_stale_names.py <vault-path> [options]
    uv run check_stale_names.py --registry <repo>/.stale-names.json [--update-baseline]

Options:
    --repo <path>        Also scan this directory (repeatable), e.g. a plugin repo
    --exempt <prefix>    Extra vault-relative or repo-relative path prefix to skip (repeatable)
    --registry <file>    Repo mode: names, exempt prefixes and baseline from this JSON file
    --baseline <file>    Baseline JSON (default: $XDG_STATE_HOME/archivist/stale-names.json)
    --update-baseline    Record the count as the new baseline if it is lower (or first run)
    --all                List every hit, not just the first 10 per name

Read-only toward the vault and repo. Writes only the baseline (the baseline file, or the
registry's "baseline" key), and only with --update-baseline.

Exit codes: 0 ok / improved / first run / no registry, 1 regressed, 2 error.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

VAULT_EXT = {".md", ".canvas", ".base"}
REPO_EXT = {".md", ".json", ".py", ".ts", ".js", ".sh", ".toml", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".obsidian", ".trash", "node_modules", "__pycache__", ".venv"}
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}")
VERSION_ROW = re.compile(r"^\s*\|\s*v?\d+\.\d+(\.\d+)?\s*\|")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def frontmatter(text: str) -> tuple[dict, int]:
    """Parsed frontmatter and the number of lines it spans (0 if none or unparseable)."""
    m = FRONTMATTER.match(text)
    if not m:
        return {}, 0
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, 0
    return (data if isinstance(data, dict) else {}), m.group(0).count("\n")


def walk(root: Path, exts: set[str], tracked_only: bool = False):
    if tracked_only and (root / ".git").exists():  # a repo: stray untracked copies never count
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, text=True)
        if out.returncode == 0:
            for rel in filter(None, out.stdout.split("\0")):
                f = root / rel
                if f.suffix in exts and not SKIP_DIRS.intersection(Path(rel).parts) and f.is_file():
                    yield f
            return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if Path(name).suffix in exts:
                yield Path(dirpath) / name


def is_history(rel: Path, exempt: list[str]) -> bool:
    if DATED.match(rel.name):
        return True
    if any("archive" in part.lower() for part in rel.parts[:-1]):
        return True
    return any(str(rel).startswith(p) for p in exempt)


def registry(vault: Path) -> dict[str, str]:
    """old name -> canonical note path (vault-relative)."""
    found: dict[str, str] = {}
    for f in walk(vault, {".md"}):
        try:
            data, _ = frontmatter(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        old = data.get("formerly")
        if not old:
            continue
        for name in [old] if isinstance(old, str) else old:
            if isinstance(name, str) and name.strip():
                found[name.strip()] = str(f.relative_to(vault))
    return found


def scan(roots: list[tuple[str, Path, set[str]]], names: dict[str, str], exempt: list[str]):
    patterns = {n: re.compile(rf"(?<![\w-]){re.escape(n)}(?![\w-])", re.I) for n in names}
    hits: dict[str, list[dict]] = {n: [] for n in names}
    scanned = 0
    for label, root, exts in roots:
        for f in walk(root, exts, tracked_only=label != "vault"):
            rel = f.relative_to(root)
            if is_history(rel, exempt):
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm, fm_lines = frontmatter(text)
            if fm.get("historical") is True:
                continue
            scanned += 1
            shown = f"{label}:{rel}" if label != "vault" else str(rel)
            skip_fm = 0
            if label == "vault" and str(rel) in names.values():
                skip_fm = fm_lines  # the canonical note lists its own old names
            for n, pat in patterns.items():
                if not pat.search(text):
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if i <= skip_fm or VERSION_ROW.match(line) or not pat.search(line):
                        continue
                    hits[n].append({"path": shown, "line": i, "text": line.strip()[:160]})
    return hits, scanned


def baseline_path(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    state = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(state) / "archivist" / "stale-names.json"


def status_of(names: dict, total: int, base: int | None) -> str:
    if not names:
        return "no-registry"
    if base is None:
        return "first-run"
    return "regressed" if total > base else "improved" if total < base else "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description="Count live mentions of renamed things and ratchet the count down.")
    ap.add_argument("vault", type=Path, nargs="?")
    ap.add_argument("--registry", type=Path)
    ap.add_argument("--repo", type=Path, action="append", default=[])
    ap.add_argument("--exempt", action="append", default=[])
    ap.add_argument("--baseline")
    ap.add_argument("--update-baseline", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if (args.vault is None) == (args.registry is None):
        print(json.dumps({"error": "give a vault path or --registry, not both"}))
        return 2

    if args.registry:
        reg_file = args.registry.expanduser().resolve()
        try:
            reg = json.loads(reg_file.read_text())
        except (OSError, json.JSONDecodeError) as e:
            print(json.dumps({"error": f"cannot read registry {reg_file}: {e}"}))
            return 2
        root = reg_file.parent
        names = {str(k): f"{reg_file.name}: {v}" for k, v in reg.get("names", {}).items()}
        exempt = args.exempt + list(reg.get("exempt", [])) + [reg_file.name]
        hits, scanned = scan([("repo", root, REPO_EXT)], names, exempt) if names else ({}, 0)
        base = reg.get("baseline")
        location = str(reg_file)
    else:
        vault = args.vault.expanduser().resolve()
        if not vault.is_dir():
            print(json.dumps({"error": f"not a directory: {vault}"}))
            return 2
        root = vault
        names = registry(vault)
        repos = [r.expanduser().resolve() for r in args.repo]
        roots = [("vault", vault, VAULT_EXT)] + [(r.name, r, REPO_EXT) for r in repos]
        hits, scanned = scan(roots, names, args.exempt) if names else ({}, 0)
        bfile = baseline_path(args.baseline)
        stored = json.loads(bfile.read_text()) if bfile.exists() else {}
        key = str(vault) + ("|" + "|".join(sorted(map(str, repos))) if repos else "")
        base = stored.get(key)
        location = str(bfile)

    total = sum(len(h) for h in hits.values())
    status = status_of(names, total, base)

    if args.update_baseline and status in ("first-run", "improved"):
        if args.registry:
            reg["baseline"] = total
            reg_file.write_text(json.dumps(reg, indent=2) + "\n")
        else:
            stored[key] = total
            bfile.parent.mkdir(parents=True, exist_ok=True)
            bfile.write_text(json.dumps(stored, indent=1, sort_keys=True))

    report = {
        "root": str(root),
        "scanned_files": scanned,
        "status": status,
        "total_hits": total,
        "baseline": base,
        "baseline_file": location,
        "names": {
            n: {
                "canonical": names[n],
                "hits": len(h),
                "files": len({x["path"] for x in h}),
                "mentions": h if args.all else h[:10],
            }
            for n, h in sorted(hits.items(), key=lambda kv: -len(kv[1]))
        },
    }
    print(json.dumps(report, indent=1, ensure_ascii=False))
    return 1 if status == "regressed" else 0


if __name__ == "__main__":
    sys.exit(main())
