"""Capture an idea or bug into INBOX § Open without breaking stride.

The point is that this takes two seconds. An idea that has to be
well-formed before it can be written down gets lost, so this asks for the
text and nothing else — no category, no priority, no triage. Triage is a
separate, later pass.

It does stamp the branch and short SHA you were standing on: that is
evidence, not a category, it costs nothing now, and it is most of the
grouping decision at triage.

The entry goes under `## Open`, newest first. Whatever sits there that
isn't a `- ` bullet is the placeholder and is dropped, matched by shape
rather than by its wording, which drifts. Then INBOX alone is committed
(a pathspec commit leaves anything else staged as it was): an uncommitted
capture once blocked a release. Neither git call is ever fatal — the note
is already written.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date

from config import Config


def git(cfg: Config, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cfg.root), *args], capture_output=True, text=True)


def where(cfg: Config) -> str:
    branch = git(cfg, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    sha = git(cfg, "rev-parse", "--short", "HEAD").stdout.strip()
    parts = [branch] if branch and branch != "HEAD" else []
    if sha:
        parts.append(f"@{sha}")
    return " ".join(parts)


def entry(text: str, stamp: str, today: str) -> str:
    first, *rest = text.splitlines()
    line = f"- **{today}**" + (f" · `{stamp}`" if stamp else "") + f" — {first.strip()}"
    return "\n".join([line] + [f"  {r}" for r in rest])


def insert(inbox: str, item: str) -> str:
    lines = inbox.split("\n")
    try:
        at = lines.index("## Open")
    except ValueError:
        raise SystemExit("capture: no '## Open' section in the inbox")
    head, tail = lines[: at + 1], lines[at + 1:]
    while tail and tail[0].strip() == "":
        tail.pop(0)
    # The placeholder: whatever leads the section that isn't an entry, a rule or a heading.
    if tail and not tail[0].startswith(("- ", "---", "#")):
        tail.pop(0)
        while tail and tail[0].strip() == "":
            tail.pop(0)
    return "\n".join(head + ["", item, ""] + tail)


def capture(cfg: Config, text: str) -> int:
    text = text.strip()
    if not text:
        print("capture: nothing to capture", file=sys.stderr)
        return 1
    path = cfg.doc("inbox")
    if not path.is_file():
        print(f"capture: {path.name} not found — run /devloop-init", file=sys.stderr)
        return 1
    item = entry(text, where(cfg), date.today().isoformat())
    path.write_text(insert(path.read_text(encoding="utf-8"), item), encoding="utf-8")
    first = text.splitlines()[0].strip()
    print(f"Captured to {path.name}:\n  {first}")

    rel = cfg.docname("inbox")
    if git(cfg, "rev-parse", "--is-inside-work-tree").returncode == 0:
        if git(cfg, "ls-files", "--error-unmatch", rel).returncode != 0:
            git(cfg, "add", "--", rel)  # first capture into a new, untracked inbox
        done = git(cfg, "commit", "-q", "-m", f"{path.stem}: {first[:60]}", "--", rel).returncode == 0
        print("  (committed)" if done else f"  (not committed — commit {rel} by hand)",
              file=sys.stdout if done else sys.stderr)
    return 0
