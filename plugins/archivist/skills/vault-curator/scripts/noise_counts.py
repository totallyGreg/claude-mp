#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""Count vault noise and ratchet each count down; the baselines live in `_vault-profile.md`.

The profile's `## Noise` section is the one record of what counts as noise and how much is
allowed. It holds two settings lines and a table:

    Orphans exclude: `900 Templates`, `799 Archived Notes`
    Daily notes: `500 Cycles/520 Days`

    | Count | Baseline | Last | Updated | Definition |

Counts:
- orphans: .md notes from `obsidian orphans` (read on stdin with --orphans -), minus the
  excluded folders and the daily notes folder
- broken_week_links: daily notes (YYYY-MM-DD.md) whose `Week` link names no note in the vault
- stale_names: live mentions of a `formerly:` name (same rules as check_stale_names.py)

A count above its baseline is a regression (exit 1). A lower count becomes the new baseline.
This script never writes the vault: it prints the new section as `section`, and the agent
writes it with `vault-write apply _vault-profile.md --section "## Noise"`.

Usage:
    obsidian vault=<name> orphans | noise_counts.py <vault> --orphans -
    noise_counts.py <vault> --orphans - --exclude "900 Templates" --days "500 Cycles/520 Days"
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_stale_names import VAULT_EXT, registry, scan, walk  # noqa: E402

PROFILE = "_vault-profile.md"
SECTION = "## Noise"
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TICKS = re.compile(r"`([^`]+)`")
ROW = re.compile(r"^\|\s*([a-z_]+)\s*\|\s*(\d+)\s*\|")
DEFINITIONS = {
    "orphans": "notes nothing links to, outside the excluded folders and daily notes",
    "broken_week_links": "daily notes whose Week link names no note or is unrendered Templater",
    "stale_names": "live mentions of a `formerly:` name (check_stale_names.py lists them)",
}


def read_section(profile: Path) -> str:
    """Body of `## Noise`, up to the next `## ` heading ('' if absent)."""
    if not profile.is_file():
        return ""
    lines = profile.read_text(encoding="utf-8").splitlines()
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line.strip() == SECTION
            continue
        if inside:
            out.append(line)
    return "\n".join(out)


def parse_section(body: str) -> tuple[list[str], str | None, dict[str, int]]:
    """(orphan excludes, daily notes folder, baselines) from the section body."""
    excludes, days, baselines = [], None, {}
    for line in body.splitlines():
        if line.startswith("Orphans exclude:"):
            excludes = TICKS.findall(line)
        elif line.startswith("Daily notes:"):
            found = TICKS.findall(line)
            days = found[0] if found else None
        elif m := ROW.match(line):
            baselines[m.group(1)] = int(m.group(2))
    return excludes, days, baselines


def under(path: str, folders: list[str]) -> bool:
    return any(path == f or path.startswith(f.rstrip("/") + "/") for f in folders)


def count_orphans(lines: list[str], excludes: list[str], days: str | None) -> int:
    skip = excludes + ([days] if days else [])
    return sum(1 for p in (l.strip() for l in lines) if p.endswith(".md") and not under(p, skip))


WEEK_LINE = re.compile(r"^Week:[ \t]*(.*)$", re.M)
FRONT = re.compile(r"\A---\n(.*?)\n---", re.S)


def week_value(text: str) -> str | None:
    """Raw `Week:` value from the frontmatter lines, so unparseable YAML still counts."""
    fm = FRONT.match(text)
    m = WEEK_LINE.search(fm.group(1)) if fm else None
    return m.group(1).strip().strip("'\"") if m and m.group(1).strip() else None


def link_target(value: str) -> str | None:
    """'[[2026-W45|Week 45]]' -> '2026-W45'; None for an empty value."""
    m = re.search(r"\[\[([^\]|#]+)", value)
    target = (m.group(1) if m else value).strip()
    return Path(target).name or None


def count_broken_week_links(vault: Path, days: str | None) -> int:
    """Daily notes whose Week link names no note, or holds unrendered Templater (`<%`)."""
    if not days or not (vault / days).is_dir():
        return 0
    notes = {f.stem.casefold() for f in walk(vault, {".md"})}
    broken = 0
    for f in walk(vault / days, {".md"}):
        if not DAY.match(f.stem):
            continue
        try:
            value = week_value(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if not value:
            continue
        target = link_target(value)
        if "<%" in value or (target and target.casefold() not in notes):
            broken += 1
    return broken


def count_stale_names(vault: Path) -> int:
    names = registry(vault)
    if not names:
        return 0
    hits, _ = scan([("vault", vault, VAULT_EXT)], names, [])
    return sum(len(h) for h in hits.values())


def render(excludes: list[str], days: str | None, rows: dict[str, dict], today: str) -> str:
    lines = [
        "Counts that may only fall (#237). `/health` updates this section with `noise_counts.py`;",
        "a rise is a regression to fix, never a new baseline.",
        "",
        "Orphans exclude: " + ", ".join(f"`{e}`" for e in excludes),
        f"Daily notes: `{days}`" if days else "Daily notes:",
        "",
        "| Count | Baseline | Last | Updated | Definition |",
        "|---|---|---|---|---|",
    ]
    for name, r in rows.items():
        lines.append(f"| {name} | {r['baseline']} | {r['count']} | {today} | {DEFINITIONS[name]} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Count vault noise and ratchet it down (baselines in _vault-profile.md).")
    ap.add_argument("vault", type=Path)
    ap.add_argument("--orphans", help="file with `obsidian orphans` output; - for stdin")
    ap.add_argument("--exclude", action="append", help="folder left out of orphans (replaces the profile's list)")
    ap.add_argument("--days", help="daily notes folder (replaces the profile's)")
    ap.add_argument("--today", default=datetime.date.today().isoformat(), help=argparse.SUPPRESS)
    args = ap.parse_args()

    vault = args.vault.expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"not a directory: {vault}"}))
        return 2
    excludes, days, baselines = parse_section(read_section(vault / PROFILE))
    excludes = args.exclude if args.exclude is not None else excludes
    days = (args.days or days or "").rstrip("/") or None

    counts = {
        "broken_week_links": count_broken_week_links(vault, days),
        "stale_names": count_stale_names(vault),
    }
    if args.orphans:
        text = sys.stdin.read() if args.orphans == "-" else Path(args.orphans).read_text(encoding="utf-8")
        counts = {"orphans": count_orphans(text.splitlines(), excludes, days), **counts}
    elif "orphans" in baselines:
        print(json.dumps({"error": "pass `obsidian orphans` output with --orphans -; the profile tracks orphans"}))
        return 2

    rows, regressed = {}, []
    for name, n in counts.items():
        base = baselines.get(name)
        status = "first-run" if base is None else "regressed" if n > base else "improved" if n < base else "ok"
        if status == "regressed":
            regressed.append(name)
        rows[name] = {"count": n, "baseline": n if base is None else min(base, n), "status": status}

    print(json.dumps({
        "profile": PROFILE,
        "status": "regressed" if regressed else "ok",
        "regressed": regressed,
        "counts": rows,
        "section_heading": SECTION,
        "section": render(excludes, days, rows, args.today),
    }, indent=1, ensure_ascii=False))
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
