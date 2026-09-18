#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Community question ledger: capture what the board asked, record the answer, and
promote generalizable answers back toward the skill.

The ledger is private to the community (default: questions/ledger.jsonl next to
community.toml, override with `questions_file` in [community]). One JSON object per
line, append-friendly, greppable. Nothing here is ever written into the plugin;
`promote` only PRINTS a sanitized candidate for a human to place in
references/common-questions.md, a Florida reference, or a friction report.

Usage:
    uv run questions.py add "Why does checking end every day at the same balance?" [--by treasurer] [--tag cash]
    uv run questions.py answer q-2026-09-17-1 "ICS sweep holds a target balance…" \\
        [--source "statement 2026-07 recon"] [--source "tools-and-platforms.md §2"] \\
        [--general "Why does our checking account end every day at the same balance?"]
    uv run questions.py list [--all | --open | --answered | --generalizable]
    uv run questions.py promote q-2026-09-17-1 [--target common-questions|florida|friction]
    uv run questions.py mark q-2026-09-17-1 --promoted-to "common-questions.md#money-on-hand"

Fields: id, asked, by, tag, question, status (open|answered|promoted), answered,
answer, sources[], general (the community-neutral form of the question, present
only when generalizable), promoted_to.
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_statement import mask_account_numbers  # noqa: E402

DEFAULT_LEDGER = Path("questions/ledger.jsonl")


def ledger_path(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    cfg = Path("community.toml")
    if cfg.exists():
        custom = tomllib.loads(cfg.read_text()).get("community", {}).get("questions_file")
        if custom:
            return Path(custom)
    return DEFAULT_LEDGER


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def save(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries))


def next_id(entries: list[dict], today: str) -> str:
    n = sum(1 for e in entries if e["id"].startswith(f"q-{today}-")) + 1
    return f"q-{today}-{n}"


def find(entries: list[dict], qid: str) -> dict:
    for e in entries:
        if e["id"] == qid:
            return e
    sys.exit(f"no entry {qid}")


# --------------------------------------------------------------------------- commands


def cmd_add(a, path):
    entries = load(path)
    today = date.today().isoformat()
    e = {"id": next_id(entries, today), "asked": today, "by": a.by, "tag": a.tag,
         "question": mask_account_numbers(a.question.strip()), "status": "open",
         "answered": None, "answer": None, "sources": [], "general": None, "promoted_to": None}
    entries.append(e)
    save(path, entries)
    print(f"{e['id']}  open  {e['question']}")


def cmd_answer(a, path):
    entries = load(path)
    e = find(entries, a.id)
    e.update(status="answered", answered=date.today().isoformat(),
             answer=mask_account_numbers(a.answer.strip()),
             sources=[mask_account_numbers(s) for s in a.source])
    if a.general:
        e["general"] = a.general.strip()
    save(path, entries)
    print(f"{e['id']}  answered" + ("  (generalizable)" if e["general"] else ""))


def cmd_list(a, path):
    entries = load(path)
    if a.open:
        entries = [e for e in entries if e["status"] == "open"]
    elif a.answered:
        entries = [e for e in entries if e["status"] != "open"]
    elif a.generalizable:
        entries = [e for e in entries if e.get("general") and e["status"] != "promoted"]
    if not entries:
        print("(no entries)")
        return
    print("| id | status | asked | tag | question |\n|---|---|---|---|---|")
    for e in entries:
        print(f"| {e['id']} | {e['status']} | {e['asked']} | {e.get('tag') or ''} | {e['question']} |")


def cmd_promote(a, path):
    """Print a community-neutral candidate. Human review is the safeguard: the
    script cannot know which facts in an answer are private."""
    e = find(load(path), a.id)
    if e["status"] == "open":
        sys.exit(f"{e['id']} has no answer yet")
    general_q = e.get("general") or e["question"]
    print(f"# Promotion candidate from {e['id']} — REVIEW before placing; remove any community-specific facts\n")
    if a.target == "common-questions":
        print("Row for references/common-questions.md (fill Data / How / Confirm):\n")
        print(f"| {general_q} | ? | {'; '.join(e['sources']) or '?'} | ? |")
    elif a.target == "florida":
        print("Bullet for the relevant references/florida/*.md section (cite section + official link):\n")
        print(f"- **{general_q}** — {e['answer']}")
    else:
        print("Friction report (skill gap) — file with your skill-maintenance tool or the plugin's issue tracker:\n")
        print(f"Skill: condo-steward\nQuestion the skill could not answer: {general_q}\n"
              f"Answer found: {e['answer']}\nSources: {'; '.join(e['sources']) or 'none recorded'}\n"
              f"Suggested home: common-questions.md / a florida reference / a new script or profile")
    print(f"\nWhen placed: uv run questions.py mark {e['id']} --promoted-to \"<file#anchor>\"")


def cmd_mark(a, path):
    entries = load(path)
    e = find(entries, a.id)
    e.update(status="promoted", promoted_to=a.promoted_to)
    save(path, entries)
    print(f"{e['id']}  promoted → {a.promoted_to}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=Path, help="ledger file (default: community.toml questions_file or questions/ledger.jsonl)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("add"); s.add_argument("question"); s.add_argument("--by"); s.add_argument("--tag"); s.set_defaults(fn=cmd_add)
    s = sub.add_parser("answer"); s.add_argument("id"); s.add_argument("answer")
    s.add_argument("--source", action="append", default=[]); s.add_argument("--general", help="community-neutral form of the question; marks it generalizable")
    s.set_defaults(fn=cmd_answer)
    s = sub.add_parser("list"); g = s.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true"); g.add_argument("--open", action="store_true")
    g.add_argument("--answered", action="store_true"); g.add_argument("--generalizable", action="store_true")
    s.set_defaults(fn=cmd_list)
    s = sub.add_parser("promote"); s.add_argument("id")
    s.add_argument("--target", choices=["common-questions", "florida", "friction"], default="common-questions")
    s.set_defaults(fn=cmd_promote)
    s = sub.add_parser("mark"); s.add_argument("id"); s.add_argument("--promoted-to", required=True); s.set_defaults(fn=cmd_mark)

    a = ap.parse_args()
    a.fn(a, ledger_path(a.ledger))


if __name__ == "__main__":
    main()
