"""devloop init: write loop.toml and the loop documents into a repository.

Only what the repository owns is written: the documents and loop.toml. The
checks stay in the plugin and read loop.toml (configuration, not copies).
An existing file is never overwritten — it is reported as kept, so init is
safe to rerun and an existing repository keeps its own documents.

Tiers: 0 AGENTS + INBOX · 1 adds BACKLOG, PLAN, DECISIONS, LOOP · 2 adds the
software profile's review gate (a commit-msg shim) and the eval case file.
Nothing is committed: the caller stages the files it wants, by name.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

import config

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = "skills/devloop/scripts/devloop.py"
DEVLOOP = f'"$(git config devloop.root)"/{SCRIPT}'

SHIM = f"""#!/usr/bin/env bash
# devloop's review gate (software profile): a merge into main that needs a
# review carries one. The logic lives in the plugin; this only finds it.
# Bypass once: git merge --no-verify
root=$(git config devloop.root)
if [ -z "$root" ] || [ ! -x "$root/{SCRIPT}" ]; then
	echo "devloop: plugin not found (git config devloop.root); review gate not checked" >&2
	exit 0
fi
exec "$root/{SCRIPT}" commit-msg "$1"
"""

INDEX = {
    "LOOP.md": ("The loop step by step, priority, the Areas", "Triaging, planning, shipping"),
    "BACKLOG.md": ("**Now**, the ranked **Work** (one line each), Verify, Blocked, Questions",
                   "Starting a session; deciding what next"),
    "backlog/*.md": ("One item's detail, linked from its line and deleted with the fix", "Picking that item up"),
    "PLAN.md": ("The ordered queue of specified stages", "Picking the next stage"),
    "stages/s<N>-*.md": ("One stage's brief, Status, `## Steps`", "Building or reviewing that stage"),
    "DECISIONS.md": ("Decisions, why, and rejected ideas", "Before proposing a change of direction"),
    "decisions/NNNN-*.md": ("One decision and its trade-offs", "A settled debate looks reopenable"),
    "INBOX.md": ("Untriaged captures", "Planning the next effort — triage first"),
    "loop.toml": ("The loop's configuration: names, caps, Areas, profile", "Changing how the loop is checked"),
    "`git log --grep`": ("What was wrong and how it was fixed — commits are the postmortem",
                         "A symptom looks familiar"),
}


def arguments(p) -> None:
    p.add_argument("--project", help="name for the document titles (default: the repository folder)")
    p.add_argument("--kind", choices=["none", "software"], default="none")
    p.add_argument("--tier", type=int, choices=[0, 1, 2], default=1)
    p.add_argument("--gate", required=True, help="the one command 'done' needs green, e.g. 'mise run gate'")
    p.add_argument("--areas", default="", help="comma-separated Areas (required from tier 1)")
    p.add_argument("--main", default="main")
    p.add_argument("--tests", default="tests/", help="software: comma-separated test path prefixes")
    p.add_argument("--test", default="", help="software: test command, e.g. 'uv run pytest {files}'")


def fill(text: str, values: dict) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def quoted(items: list[str]) -> str:
    return ", ".join(json.dumps(i) for i in items)


def agents_page(tier: int, software: bool) -> dict:
    docs = ["INBOX.md", "loop.toml", "`git log --grep`"]
    if tier >= 1:
        docs = ["LOOP.md", "BACKLOG.md", "backlog/*.md", "PLAN.md", "stages/s<N>-*.md",
                "DECISIONS.md", "decisions/NNNN-*.md"] + docs
    link = lambda d: f"[{d}]({d})" if d.endswith((".md", ".toml")) and "*" not in d else (  # noqa: E731
        d if d.startswith("`") else f"`{d}`")
    rows = "\n".join(f"| {link(d)} | {INDEX[d][0]} | {INDEX[d][1]} |" for d in docs)
    commands = [f"/capture <text>                    # an idea or bug into INBOX, committed alone"]
    if tier >= 1:
        commands += [f"/review-backlog                    # when the session start says it's due",
                     f"{DEVLOOP} rank    # what next",
                     f"{DEVLOOP} check   # the loop's checks — part of the gate"]
    if software and tier >= 2:
        commands += [f"{DEVLOOP} review  # independent review before a due merge",
                     f"{DEVLOOP} evals   # replay past fixes under today's rules (slow)"]
    rules = ["- Stage files by name; never `git add .`, `-A`, `-u` or `commit -a` (devloop's no-blanket-add hook).",
             "- **The commit is the postmortem**: the title says what changed, the body what was wrong and how it was found."]
    if tier >= 1:
        rules += ["- Work finished from any list leaves it in the commit that finished it (`devloop check`).",
                  "- BACKLOG and PLAN follow their grammar and ranking; Now #1 is the ranked next or says why (`devloop check`)."]
    if software:
        rules += ["- A bug is reproduced as a failing test, committed alone, before the fix (`devloop check`: red-first).",
                  "- A bugfix branch deletes its BACKLOG or INBOX line in the fix (`devloop check`: backlog-closed)."]
        if tier >= 2:
            rules.append("- A merge into main that `devloop review-needed` flags carries a `Review:` trailer (commit-msg hook).")
    loop = ("Capture (`/capture`) → Triage into BACKLOG → Review when due (`/review-backlog`) → Plan § Now → "
            "Build → Ship (gate green, the end-to-end check shown) → Compound (amend the stage, a decision, "
            "a rule here with its enforcer). Each step: [LOOP.md](LOOP.md).") if tier >= 1 else (
            "Capture (`/capture`) into INBOX; work from it; the gate green before done.")
    return {"index_rows": rows, "commands": "\n".join(commands), "rules": "\n".join(rules), "loop_line": loop}


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def run(args) -> int:
    root = Path(args.root) if args.root else config.git_root()
    areas = [a.strip() for a in args.areas.split(",") if a.strip()]
    if args.tier >= 1 and not areas:
        print("init: tier 1 and up need --areas (what a change is about, e.g. 'Core, Docs, Tooling')")
        return 2
    software = args.kind == "software"
    values = {
        "project": args.project or root.name, "gate": args.gate, "kind": args.kind, "tier": args.tier,
        "main": args.main, "areas": quoted(areas), "today": date.today().isoformat(),
        "agents": "AGENTS.md", "loop": "LOOP.md", "backlog": "BACKLOG.md", "inbox": "INBOX.md",
        "plan": "PLAN.md", "decisions": "DECISIONS.md", "stages_dir": "stages", "backlog_dir": "backlog",
        "decisions_dir": "decisions",
    }
    values["software"] = fill((TEMPLATES / "software.toml").read_text(), {
        "tests": quoted([t.strip() for t in args.tests.split(",") if t.strip()]), "test": args.test,
    }) if software else ""
    values.update(agents_page(args.tier, software))

    files = {"loop.toml": "loop.toml", "AGENTS.md": "AGENTS.md", "INBOX.md": "INBOX.md"}
    if args.tier >= 1:
        files.update({n: n for n in ("LOOP.md", "BACKLOG.md", "PLAN.md", "DECISIONS.md")})
    written, kept = [], []
    for target, template in files.items():
        path = root / target
        if path.exists():
            kept.append(target)
            continue
        path.write_text(fill((TEMPLATES / template).read_text(), values), encoding="utf-8")
        written.append(target)

    if software and args.tier >= 2:
        cases = root / "evals" / "cases.json"
        if cases.exists():
            kept.append("evals/cases.json")
        else:
            cases.parent.mkdir(exist_ok=True)
            cases.write_text(json.dumps({"about": "devloop config evals: each case is a merged bugfix branch; "
                                         "the task is the BACKLOG line its fix deleted, the check its tests.",
                                         "cases": []}, indent=2) + "\n")
            written.append("evals/cases.json")
        hooks = git(root, "config", "core.hooksPath").stdout.strip()
        if not hooks:
            hooks = ".githooks"
            git(root, "config", "core.hooksPath", hooks)
        shim = root / hooks / "commit-msg"
        if shim.exists():
            kept.append(f"{hooks}/commit-msg (add: exec {DEVLOOP} commit-msg \"$1\")")
        else:
            shim.parent.mkdir(parents=True, exist_ok=True)
            shim.write_text(SHIM)
            shim.chmod(0o755)
            written.append(f"{hooks}/commit-msg")

    git(root, "config", "devloop.root", str(PLUGIN_ROOT))
    for name in written:
        print(f"  wrote  {name}")
    for name in kept:
        print(f"  kept   {name} (exists; not overwritten)")
    print(f"\ngit config devloop.root = {PLUGIN_ROOT} (the session-start hook keeps it current)")
    if args.tier >= 1:
        print(f"Add the loop's checks to the gate ({args.gate}):\n  {DEVLOOP} check")
    print("Nothing is committed: stage the files above by name.")
    return 0
