#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Check that a merged note kept the text of the notes it was merged from.

Run it before writing any merge that a model wrote or restructured, rather than
merge_notes.py's plain concatenation: a model can reword a line ("AI services"
→ "LLM services") that reads fine and is wrong.

Usage:
    uv run check_merge_preserved.py --merged <file> <source> [<source> ...]

A source line counts as kept when it appears in the merged note after collapsing
whitespace, non-breaking spaces and table padding. Heading lines may change
level or lose bold markup (restructuring is allowed); their text must survive.
Frontmatter is not compared — merging it is merge_notes.py's job.

Output (JSON) and exit code:
    {"ok": true|false, "missing_urls": [...], "missing_wikilinks": [...],
     "missing_lines": [{"source": ..., "line": ...}], "missing_headings": [...]}
    exit 0 = everything kept, 1 = something missing, 2 = bad arguments.
"""

import argparse
import json
import re
import sys
from pathlib import Path

URL = re.compile(r"https?://[^\s)\]>|]+")
WIKILINK = re.compile(r"\[\[[^\]]+\]\]")


def body(text: str) -> str:
    """Text without its YAML frontmatter."""
    m = re.match(r"---\n.*?\n---\n?", text, re.S)
    return text[m.end():] if m else text


def norm(s: str) -> str:
    """Collapse whitespace, NBSP and table padding/separators so reflowed tables match."""
    return re.sub(r"[\s |:-]+", " ", s).strip()


def heading_text(line: str) -> str:
    return norm(re.sub(r"^#+\s*", "", line).replace("**", ""))


def check(merged: str, sources: dict[str, str]) -> dict:
    m_body = body(merged)
    m_norm = norm(m_body)
    m_headings = {heading_text(l) for l in m_body.splitlines() if l.lstrip().startswith("#")}
    result = {"missing_urls": [], "missing_wikilinks": [], "missing_lines": [], "missing_headings": []}
    for name, text in sources.items():
        s_body = body(text)
        result["missing_urls"] += sorted(set(URL.findall(s_body)) - set(URL.findall(m_body)))
        result["missing_wikilinks"] += sorted(set(WIKILINK.findall(s_body)) - set(WIKILINK.findall(m_body)))
        for line in s_body.splitlines():
            if not norm(line):
                continue
            if line.lstrip().startswith("#"):
                if heading_text(line) not in m_headings and heading_text(line) not in m_norm:
                    result["missing_headings"].append({"source": name, "line": line.strip()})
            elif norm(line) not in m_norm:
                result["missing_lines"].append({"source": name, "line": line.strip()})
    for key in ("missing_urls", "missing_wikilinks"):
        result[key] = sorted(set(result[key]))
    ok = not any(result[k] for k in ("missing_urls", "missing_wikilinks", "missing_lines"))
    return {"ok": ok, **result}


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a merged note kept its sources' text.")
    ap.add_argument("--merged", required=True, type=Path)
    ap.add_argument("sources", nargs="+", type=Path)
    args = ap.parse_args()
    try:
        merged = args.merged.read_text()
        sources = {str(p): p.read_text() for p in args.sources}
    except OSError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 2
    out = check(merged, sources)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
