"""Two document invariants: every document is indexed, and none outgrows its cap.

AGENTS.md is the one page every session loads, so a document it doesn't
list is invisible to agents. Three sub-indexes keep it from needing a line
per file:
- a file under `decisions_dir` is indexed when DECISIONS lists it;
- a file under `backlog_dir` is indexed by the BACKLOG line that links it,
  and is deleted with the fix — one nobody links is an orphan;
- a file under `stages_dir` is indexed by PLAN while queued; once out of
  the queue its own `**Status:**` (shipped, superseded, …) is the record.

A size cap keeps a living document from becoming a dumping ground; for
AGENTS.md it keeps the always-loaded page one page. A rule that must hold
stays on the page or becomes a check: moving it out loses it.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess

from config import Config

ALWAYS_EXCLUDED = (".claude/*", "*/node_modules/*", "node_modules/*")


def documents(cfg: Config) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=cfg.root, capture_output=True, text=True, check=True,
    ).stdout.split("\n")
    patterns = ALWAYS_EXCLUDED + tuple(cfg["docs"]["exclude"])
    return sorted({
        f for f in out
        if f and (cfg.root / f).is_file() and not any(fnmatch.fnmatch(f, p) for p in patterns)
    })


def read(cfg: Config, rel: str) -> str:
    path = cfg.root / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def check(cfg: Config) -> list[str]:
    docs_cfg, failures = cfg["docs"], []
    docs = documents(cfg)

    for f in docs:
        cap = docs_cfg["caps"].get(f, docs_cfg["cap_bytes"])
        size = (cfg.root / f).stat().st_size
        if cap and size > cap:
            failures.append(f"{f}: {size} bytes exceeds its cap of {cap} — split the detail out")

    index_name = cfg.docname("agents")
    index = read(cfg, index_name)
    if not index:
        return failures + [f"{index_name} is missing — it is the document index every session loads"]
    subs = {
        docs_cfg["decisions_dir"] + "/": cfg.docname("decisions"),
        docs_cfg["backlog_dir"] + "/": cfg.docname("backlog"),
        docs_cfg["stages_dir"] + "/": cfg.docname("plan"),
    }
    terminal = "|".join(re.escape(s) for s in docs_cfg["stage_terminal"]).replace("'", ".")
    for f in docs:
        if f == index_name or f in index:
            continue
        prefix = next((p for p in subs if f.startswith(p)), None)
        if prefix is None:
            failures.append(f"{f} is not referenced in {index_name} — an unindexed document is invisible to agents")
            continue
        sub = subs[prefix]
        if f in read(cfg, sub):
            continue
        if prefix == docs_cfg["backlog_dir"] + "/":
            failures.append(f"{f} is linked from no {sub} item — its item was fixed or dropped, so delete it")
        elif prefix == docs_cfg["stages_dir"] + "/":
            if not re.search(rf"^\*\*Status:\*\* *({terminal})", read(cfg, f), re.M | re.I):
                failures.append(f"{f} is neither queued in {sub} nor marked "
                                f"{'/'.join(docs_cfg['stage_terminal'])} in its **Status:** line")
        else:
            failures.append(f"{f} is listed in neither {index_name} nor {sub}")
    return failures
