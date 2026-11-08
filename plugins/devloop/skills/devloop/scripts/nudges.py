"""Session-start nudges: a due item says so, and never fails anything.

**Review due** once any of these holds since the last review:
- a release has shipped — the work just finished stops being "what we're
  doing", and older items start sinking under it;
- `max_age_days` have passed — a week of captures without a release
  still drifts;
- INBOX § Open holds `max_inbox` lines — untriaged captures are invisible
  to the ranking.
"Reviewed" is the newest commit that changed BACKLOG's `Reviewed:` line or
is titled "Backlog review…" (a second review on the same day leaves the
date as it was). A release is since it when the newest tag matching
`release_tags` isn't an ancestor of that commit. An uncommitted change to
the line counts as a review in progress.

**Evals due** (software profile, tier 2) once the agent-facing prose
(`evals_prose`) has changed by `evals_threshold` lines since the newest
eval run. A change to a script or hook doesn't count: its behaviour is
tested as code. With no run yet it says nothing — the first run is a
choice, not a debt.
"""

from __future__ import annotations

import json
import re
import subprocess
import time

from config import Config


def git(cfg: Config, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cfg.root), *args], capture_output=True, text=True).stdout.strip()


def open_inbox_lines(cfg: Config) -> int:
    path = cfg.doc("inbox")
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")
    body = text.split("## Open", 1)[-1] if "## Open" in text else ""
    body = re.split(r"^(?:---|## )", body, maxsplit=1, flags=re.M)[0]
    return sum(1 for line in body.splitlines() if line.startswith("- "))


def review_reasons(cfg: Config) -> list[str]:
    if cfg.tier < 1:
        return []
    backlog, due = cfg.docname("backlog"), cfg["review_due"]
    if git(cfg, "diff", "HEAD", "-G", "^Reviewed:", "--", backlog):
        return []  # a review is under way in the working tree
    reviews = [sha for sha in (
        git(cfg, "log", "-1", "--format=%H", "-G", "^Reviewed:", "--", backlog),
        git(cfg, "log", "-1", "--format=%H", "--grep=^Backlog review"),
    ) if sha]
    found = []
    tag = git(cfg, "describe", "--tags", "--abbrev=0", "--match", due["release_tags"])
    if tag and not any(
        subprocess.run(["git", "-C", str(cfg.root), "merge-base", "--is-ancestor", tag, sha]).returncode == 0
        for sha in reviews
    ):
        found.append(f"{tag} shipped since the last review")
    newest = max((int(git(cfg, "log", "-1", "--format=%ct", sha) or 0) for sha in reviews), default=0)
    days = int((time.time() - newest) / 86400)
    if reviews and days >= due["max_age_days"]:
        found.append(f"the last review was {days} days ago")
    inbox = open_inbox_lines(cfg)
    if inbox >= due["max_inbox"]:
        found.append(f"{cfg.docname('inbox')} holds {inbox} untriaged captures")
    return found


def results_file(cfg: Config):
    return cfg.cache / "evals" / "results.jsonl"


def evals_reason(cfg: Config) -> str | None:
    sw = cfg["software"]
    if not (cfg.software and cfg.tier >= 2 and sw["evals_prose"]):
        return None
    results = results_file(cfg)
    if not results.exists():
        return None
    runs = [json.loads(line) for line in results.read_text().splitlines() if line.strip()]
    if not runs:
        return None
    last = runs[-1]
    out = git(cfg, "diff", "--numstat", last["head"], "--", *sw["evals_prose"])
    lines = sum(int(a) + int(d) for a, d, _ in (row.split("\t", 2) for row in out.splitlines()) if a != "-")
    if lines < sw["evals_threshold"]:
        return None
    return (f"Config evals due: {lines} lines of agent-facing prose changed since the eval run of "
            f"{last['stamp']} (at {last['head']}). Run the cases the changed rules touch "
            "(`devloop evals <id>`), or all of them for a rewrite.")


def messages(cfg: Config) -> list[str]:
    out = []
    found = review_reasons(cfg)
    if found:
        out.append(f"Backlog review due: {'; '.join(found)}. Run /review-backlog before starting other work.")
    evals = evals_reason(cfg)
    if evals:
        out.append(evals)
    return out
