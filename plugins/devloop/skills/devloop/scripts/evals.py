"""Config evals: does the agent configuration still fix real bugs?

The always-loaded page, the loop documents, skills and hooks change, and a
change that reads well can still make agents worse. So the configuration is
regression-tested like code, on real past tasks with accepted outcomes:
the repository's own past bug fixes. Each fix's commit deletes the BACKLOG
line that stated the bug (the task) and adds tests that prove it gone (the
check). `software.evals_cases` names the merges:

    {"cases": [{"id": "short-name", "merge": "<merge sha>",
                "skip": {"pattern": "<test filter>", "why": "<reason>"}}]}

A case's optional `skip` leaves out fix tests that ask for more than the
BACKLOG line says — no reader of the line could know — with the reason
(rendered through `software.evals_skip_arg`, e.g. `--skip {pattern}`).

For each case:
1. a worktree on a fresh `<bugfix_prefix>eval-<id>-<stamp>` branch at the
   merge's first parent, in the devloop cache — never where the project's
   own build scratch goes;
2. today's configuration (`evals_overlay`, plus loop.toml) laid over that
   code, marked skip-worktree so the agent's commits never carry it;
3. a headless `claude -p` session with the BACKLOG line as its task;
4. grading after it stops: **fixed** — the fix's own test files copied in
   over the agent's, and `software.test` passing on them; **red-first** —
   the red-first check on the agent's branch; turns, time and cost;
5. the worktree and branch removed however the case ends; one JSON per case
   and a line in results.jsonl with the configuration's fingerprint.

Each eval finding becomes a deterministic check, so the set shrinks. Run it
on a large change to the agent-facing prose (the session-start nudge says
when), never in the gate.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import software
from config import FILE, Config
from nudges import results_file

CASE_TIMEOUT = 60 * 60
DEFAULT_TOOLS = [
    "Read", "Edit", "Write", "Grep", "Glob", "Agent", "Skill",
    "Bash(git status:*)", "Bash(git diff:*)", "Bash(git log:*)", "Bash(git show:*)", "Bash(git add:*)",
    "Bash(git commit:*)", "Bash(git switch:*)", "Bash(git branch:*)", "Bash(git rev-parse:*)",
    "Bash(git merge-base:*)", "Bash(git grep:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)",
    "Bash(tail:*)", "Bash(grep:*)", "Bash(sed -n:*)", "Bash(wc:*)", "Bash(find:*)",
]

PROMPT = """Fix this bug. It is the {backlog} line that describes it:

{task}

Work as {agents} says a bug is fixed, on the branch you are on ({branch}): a
failing test first, committed alone, then the fix, the gate ({gate}), the
commit. Configuration files may show as untracked or differ from history;
leave them alone. This is an evaluation in a scratch worktree: stop once the
fix is committed — do not merge, release or push, and do not ask questions;
decide and say why."""


def overlay_names(cfg: Config) -> list[str]:
    return list(dict.fromkeys([FILE, *cfg["software"]["evals_overlay"]]))


def fingerprint(cfg: Config) -> str:
    digest = hashlib.sha256()
    for name in overlay_names(cfg):
        root = cfg.root / name
        for path in sorted([root] if root.is_file() else root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                digest.update(str(path.relative_to(cfg.root)).encode() + path.read_bytes())
    return digest.hexdigest()[:12]


def overlay(cfg: Config, tree: Path) -> None:
    for name in overlay_names(cfg):
        source, target = cfg.root / name, tree / name
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True, symlinks=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
        elif source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    tracked = software.git(cfg, "ls-files", "--", *overlay_names(cfg), cwd=tree).split()
    if tracked:
        software.git(cfg, "update-index", "--skip-worktree", *tracked, cwd=tree)


def task(cfg: Config, merge: str) -> tuple[str, list[str]]:
    """The BACKLOG line the fix deleted (with any backlog/ detail) and its test files."""
    base, tip = f"{merge}^1", f"{merge}^2"
    removed = [l.removeprefix("-- ") for l in
               software.git(cfg, "diff", f"{base}...{tip}", "--", cfg.docname("backlog")).splitlines()
               if l.startswith("-- **")]
    text = removed[0] if removed else ""
    detail = cfg["docs"]["backlog_dir"] + "/"
    for path in software.git(cfg, "diff", "--name-only", "--diff-filter=D", f"{base}...{tip}", "--", detail).split():
        text += f"\n\nIts detail, {path}:\n" + software.git(cfg, "show", f"{base}:{path}")
    tests = [p for p in software.git(cfg, "diff", "--name-only", f"{base}...{tip}").split()
             if software.is_test(cfg, p)]
    return text, tests


def grade(cfg: Config, case: dict, merge: str, base: str, text: str, tests: list[str],
          branch: str, tree: Path, out: Path, scratch: Path) -> dict:
    sw = cfg["software"]
    result = {"id": case["id"], "merge": merge[:12], "base": base[:12], "tests": tests}
    started = time.time()
    prompt = PROMPT.format(backlog=cfg.docname("backlog"), agents=cfg.docname("agents"),
                           task=text, branch=branch, gate=cfg["gate"] or "the gate")
    tools = list(sw["evals_allowed_tools"] or DEFAULT_TOOLS) + ([f"Bash({cfg['gate']}:*)"] if cfg["gate"] else [])
    try:
        session = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json", "--permission-mode", "acceptEdits",
             "--no-session-persistence", "--allowedTools", *software.allowed(cfg, tools)],
            cwd=tree, capture_output=True, text=True, timeout=CASE_TIMEOUT,
        )
        try:
            meta = json.loads(session.stdout)
        except ValueError:
            meta = {"result": session.stdout[-4000:], "is_error": True}
        result.update(turns=meta.get("num_turns"), cost_usd=meta.get("total_cost_usd"),
                      agent_error=meta.get("is_error"), summary=(meta.get("result") or "")[-1500:])
    except subprocess.TimeoutExpired:
        result.update(agent_error=True, summary=f"timed out after {CASE_TIMEOUT} s")
    result["agent_seconds"] = round(time.time() - started)
    result["commits"] = len(software.git(cfg, "rev-list", f"{base}..{branch}", cwd=tree).split())

    here = Path(__file__).resolve().parent / "devloop.py"
    red = subprocess.run([sys.executable, str(here), "check", "--only", "red-first"], cwd=tree,
                         capture_output=True, text=True, timeout=3600,
                         env={**os.environ, "DEVLOOP_SCRATCH": str(scratch / "red-first")})
    result["red_first"] = red.returncode == 0
    result["red_first_says"] = (red.stdout + red.stderr).strip()[-600:]

    subprocess.run(["git", "-C", str(tree), "checkout", merge, "--", *tests], capture_output=True)
    skip = case.get("skip", {}).get("pattern")
    extra = software.fill(sw["evals_skip_arg"], pattern=skip) if skip and sw["evals_skip_arg"] else ""
    passed, output = software.run_tests(cfg, tree, scratch / "check", tests, extra)
    result["fixed"] = bool(passed)
    if not passed:
        result["failing"] = (["the fix's tests don't build against the agent's code"] if passed is None else []) \
            + output.splitlines()[-10:]
    result["diff"] = software.git(cfg, "diff", "--stat", f"{base}...{branch}", cwd=tree).strip().splitlines()[-1:]
    (out / f"{case['id']}.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def run_case(cfg: Config, case: dict, stamp: str, out: Path) -> dict:
    merge = software.git(cfg, "rev-parse", case["merge"]).strip()
    base = software.git(cfg, "rev-parse", f"{merge}^1").strip()
    text, tests = task(cfg, merge)
    branch = f"{cfg['software']['bugfix_prefix']}eval-{case['id']}-{stamp}"
    work = cfg.cache / "evals" / "trees"
    tree, scratch = work / case["id"], cfg.cache / "evals" / "scratch" / case["id"]
    subprocess.run(["git", "-C", str(cfg.root), "worktree", "remove", "--force", str(tree)], capture_output=True)
    shutil.rmtree(tree, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    software.git(cfg, "worktree", "add", "-q", "-b", branch, str(tree), base)
    overlay(cfg, tree)
    try:
        return grade(cfg, case, merge, base, text, tests, branch, tree, out, scratch)
    finally:
        subprocess.run(["git", "-C", str(cfg.root), "worktree", "remove", "--force", str(tree)], capture_output=True)
        subprocess.run(["git", "-C", str(cfg.root), "branch", "-D", branch], capture_output=True)


def run(cfg: Config, wanted: list[str]) -> int:
    if not cfg.software or not cfg["software"]["test"]:
        print("evals: needs kind = \"software\" and `software.test` in loop.toml", file=sys.stderr)
        return 1
    cases_path = cfg.root / cfg["software"]["evals_cases"]
    if not cases_path.is_file():
        print(f"evals: no case file at {cases_path.relative_to(cfg.root)}", file=sys.stderr)
        return 1
    cases = json.loads(cases_path.read_text())["cases"]
    if wanted:
        cases = [c for c in cases if c["id"] in wanted]
        if not cases:
            print(f"evals: no case named {', '.join(wanted)}", file=sys.stderr)
            return 1
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    out = results_file(cfg).parent / stamp
    out.mkdir(parents=True, exist_ok=True)
    config = fingerprint(cfg)
    print(f"evals: {len(cases)} case(s), configuration {config}, results in {out}", flush=True)
    results = []
    for case in cases:
        print(f"evals: {case['id']} …", flush=True)
        r = run_case(cfg, case, stamp, out)
        results.append(r)
        print(f"  fixed={r['fixed']} red_first={r['red_first']} turns={r.get('turns')} "
              f"{r['agent_seconds']}s cost={r.get('cost_usd')}", flush=True)
    line = {"stamp": stamp, "config": config, "head": software.git(cfg, "rev-parse", "--short", "HEAD").strip(),
            "cases": len(results), "fixed": sum(r["fixed"] for r in results),
            "red_first": sum(r["red_first"] for r in results), "ids": [r["id"] for r in results]}
    with results_file(cfg).open("a") as log:
        log.write(json.dumps(line) + "\n")
    print(f"evals: {line['fixed']}/{line['cases']} fixed, {line['red_first']}/{line['cases']} red-first")
    return 0
