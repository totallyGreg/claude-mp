#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6.0",
#   "ruamel.yaml>=0.18",
# ]
# ///
"""Count vault noise and ratchet each count down; the baselines live in `_vault-profile.md`.

The profile's `## Noise` section is the one record of what counts as noise and how much is
allowed. It holds two settings lines and a table:

    Orphans exclude: `900 Templates`, `799 Archived Notes`
    Daily notes: `500 Cycles/520 Days`
    Link fields exempt: `processed`

    | Count | Baseline | Last | Updated | Definition |

Counts:
- orphans: .md notes from `obsidian orphans` (read on stdin with --orphans -), minus the
  excluded folders and the daily notes folder
- broken_week_links: daily notes (YYYY-MM-DD.md) whose `Week` link names no note in the vault
- stale_names: live mentions of a `formerly:` name (same rules as check_stale_names.py)
- broken_frontmatter: .md notes outside the excluded folders whose frontmatter Obsidian can't read
  (a vault-write frontmatter rule fails, or YAML 1.2 doesn't parse it to a mapping), so every view
  and K-Plex sees none of their properties. YAML 1.2 (ruamel, round-trip) because Obsidian's parser
  is 1.2: PyYAML (1.1) rejects `[https://a?b=c]` and `{{x}}: y`, which Obsidian reads.
- unmapped_link_fields: (note, field) pairs where a frontmatter field holds a [[link]] but K-Plex
  gives the field no role, outside the excluded folders and minus `Link fields exempt:`. Field
  names match the way K-Plex matches them (case, spaces and hyphens ignored). The roles come from
  `.obsidian/plugins/k-plex/data.json` (read-only); without it the count is skipped.

A count above its baseline is a regression (exit 1). A lower count becomes the new baseline.
This script never writes the vault: it prints the new section as `section`, and the agent
writes it with `vault-write apply _vault-profile.md --section "## Noise"`.

Usage:
    obsidian vault=<name> orphans | noise_counts.py <vault> --orphans -
    obsidian vault=<name> orphans | noise_counts.py <vault> --orphans - --list   # every broken_frontmatter path
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
    "broken_frontmatter": "notes whose frontmatter Obsidian can't read, so their properties are invisible",
    "unmapped_link_fields": "frontmatter fields holding a wikilink that K-Plex gives no role (per note and field)",
}
KPLEX = Path(".obsidian/plugins/k-plex/data.json")
KPLEX_LISTS = ("parents", "children", "friends", "leftFriends", "rightFriends", "previous", "next", "hidden")


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


def parse_section(body: str) -> tuple[list[str], str | None, list[str], dict[str, int]]:
    """(orphan excludes, daily notes folder, exempt link fields, baselines) from the section body."""
    excludes, days, exempt, baselines = [], None, [], {}
    for line in body.splitlines():
        if line.startswith("Orphans exclude:"):
            excludes = TICKS.findall(line)
        elif line.startswith("Link fields exempt:"):
            exempt = TICKS.findall(line)
        elif line.startswith("Daily notes:"):
            found = TICKS.findall(line)
            days = found[0] if found else None
        elif m := ROW.match(line):
            baselines[m.group(1)] = int(m.group(2))
    return excludes, days, exempt, baselines


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


def field_key(name: str) -> str:
    """K-Plex's matching: `Parent Name`, `parent-name` and `parent name` are one field."""
    return re.sub(r"[\s-]+", "-", name.strip().casefold())


def kplex_names(entry: str) -> list[str]:
    """Field names in one role-list entry. A paired entry is `field/partner` (`implemented by/implements`);
    a slash or backslash inside a name is escaped as `\\/` or `\\\\` (`📓\\/☀️`)."""
    names, cur, i = [], [], 0
    while i < len(entry):
        ch = entry[i]
        if ch == "\\" and i + 1 < len(entry):
            cur.append(entry[i + 1])
            i += 2
            continue
        if ch == "/":
            names.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    names.append("".join(cur))
    return [n for n in (x.strip() for x in names) if n]


def kplex_fields(vault: Path) -> set[str] | None:
    """Normalized names of every field K-Plex has a role for, partners included; None if K-Plex isn't installed."""
    try:
        hierarchy = json.loads((vault / KPLEX).read_text(encoding="utf-8")).get("hierarchy") or {}
    except (OSError, ValueError):
        return None
    return {field_key(n) for lst in KPLEX_LISTS for e in hierarchy.get(lst) or [] if isinstance(e, str)
            for n in kplex_names(e)}


TOP_KEY = re.compile(r"^([^\s#'\"-][^:]*):(.*)$")


def link_fields(text: str) -> set[str]:
    """Top-level frontmatter keys whose value (inline or in an indented list) holds a [[link]]."""
    fm = FRONT.match(text)
    found, key = set(), None
    for line in (fm.group(1).splitlines() if fm else []):
        m = TOP_KEY.match(line)
        if m:
            key, value = m.group(1).strip(), m.group(2)
        elif key and line[:1] in (" ", "\t", "-"):
            value = line
        else:
            key, value = None, ""
        if key and "[[" in value:
            found.add(key)
    return found


def count_unmapped_link_fields(vault: Path, skip: list[str], exempt: list[str]) -> tuple[int, list] | None:
    """(count, top fields) of link-holding frontmatter fields K-Plex gives no role; None without K-Plex."""
    known = kplex_fields(vault)
    if known is None:
        return None
    known |= {field_key(e) for e in exempt}
    tally: dict[str, int] = {}
    shown: dict[str, str] = {}  # normalized key -> first spelling seen, so `Owner`/`owner` list once
    for f in walk(vault, {".md"}):
        rel = f.relative_to(vault).as_posix()
        if under(rel, skip):
            continue
        try:
            fields = link_fields(f.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        for name in fields:
            key = field_key(name)
            if key not in known:
                tally[key] = tally.get(key, 0) + 1
                shown.setdefault(key, name)
    top = sorted(((shown[k], n) for k, n in tally.items()), key=lambda kv: (-kv[1], kv[0]))[:10]
    return sum(tally.values()), top


def vault_write():
    """The vault-write module, so this count uses the same frontmatter rules as the write gate."""
    import importlib.util
    from importlib.machinery import SourceFileLoader

    path = str(Path(__file__).resolve().parents[3] / "bin" / "vault-write")
    loader = SourceFileLoader("vault_write", path)
    spec = importlib.util.spec_from_loader("vault_write", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def count_broken_frontmatter(vault: Path, skip: list[str]) -> list[str]:
    """Sorted paths of notes whose frontmatter Obsidian can't read."""
    from ruamel.yaml import YAML, YAMLError

    rules = vault_write().frontmatter_errors
    parser = YAML(typ="rt", pure=True)
    broken = []
    for f in walk(vault, {".md"}):
        rel = f.relative_to(vault).as_posix()
        if under(rel, skip):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = text.splitlines()
        if not lines or lines[0].rstrip() != "---":
            continue
        fm = FRONT.match(text)
        # No Templater skip: templates sit in excluded folders, so `<% %>` here was never rendered
        # (e.g. daily notes with `Week: "[[<% tp.date.now("YYYY-[W]WW", …) %>]]"`, nested quotes)
        bad = bool(rules(lines))  # includes "no closing ---"
        if not bad and fm:  # an empty block (`---` twice) has no group to parse
            try:
                data = parser.load(fm.group(1))
                bad = data is not None and not isinstance(data, dict)
            except (YAMLError, ValueError, TypeError):
                bad = True
        if bad:
            broken.append(rel)
    return sorted(broken)


def count_stale_names(vault: Path) -> int:
    names = registry(vault)
    if not names:
        return 0
    hits, _ = scan([("vault", vault, VAULT_EXT)], names, [])
    return sum(len(h) for h in hits.values())


def render(excludes: list[str], days: str | None, exempt: list[str], rows: dict[str, dict], today: str) -> str:
    lines = [
        "Counts that may only fall (#237). `/health` updates this section with `noise_counts.py`;",
        "a rise is a regression to fix, never a new baseline.",
        "",
        "Orphans exclude: " + ", ".join(f"`{e}`" for e in excludes),
        f"Daily notes: `{days}`" if days else "Daily notes:",
        "Link fields exempt: " + ", ".join(f"`{e}`" for e in exempt),
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
    ap.add_argument("--link-exempt", action="append", help="link field K-Plex need not map (replaces the profile's list)")
    ap.add_argument("--list", action="store_true",
                    help="list every broken_frontmatter path (broken_frontmatter_all), not just the first ten")
    ap.add_argument("--today", default=datetime.date.today().isoformat(), help=argparse.SUPPRESS)
    args = ap.parse_args()

    vault = args.vault.expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"not a directory: {vault}"}))
        return 2
    excludes, days, exempt, baselines = parse_section(read_section(vault / PROFILE))
    excludes = args.exclude if args.exclude is not None else excludes
    exempt = args.link_exempt if args.link_exempt is not None else exempt
    days = (args.days or days or "").rstrip("/") or None

    counts = {
        "broken_week_links": count_broken_week_links(vault, days),
        "stale_names": count_stale_names(vault),
    }
    details = {}
    broken = count_broken_frontmatter(vault, excludes)
    counts["broken_frontmatter"], details["broken_frontmatter_first"] = len(broken), broken[:10]
    if args.list:
        details["broken_frontmatter_all"] = broken
    unmapped = count_unmapped_link_fields(vault, excludes, exempt)
    if unmapped is not None:
        counts["unmapped_link_fields"], details["unmapped_link_fields_top"] = unmapped
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
        **details,
        "section_heading": SECTION,
        "section": render(excludes, days, exempt, rows, args.today),
    }, indent=1, ensure_ascii=False))
    return 1 if regressed else 0


if __name__ == "__main__":
    sys.exit(main())
