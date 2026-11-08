"""The `software` profile's checks: red first, backlog closed, and the review gate.

**Red first.** On a bugfix branch the bug is reproduced as a failing test
before it is fixed. A fix and its test written together prove only that
they agree; a test committed first, seen failing, then left alone while
the code changes is the proof the bug is gone. From git alone:
1. the branch's first commit changes test files only (`software.tests`);
2. at that commit the tests fail — built in a detached worktree outside
   the repository, then `software.test` run, which must exit non-zero;
   failing to build is not a reproduction;
3. every line it added to a test file is still in the working tree: the
   fix didn't weaken the test that judges it.
A first commit with a `Red-first: skip <reason>` trailer is exempt (a fix
no test can reach), recorded where `git log` shows it.

**Backlog closed.** A bugfix branch removes the bug's BACKLOG item or INBOX
capture, in the working tree (the gate runs before the fix is committed).
It was prose; when the always-loaded page was cut to one page, the sentence
went with the detail and the first config eval found an agent leaving the
line "for when the branch merges". `Backlog: none <reason>` on a commit
exempts a bug found and fixed in one sitting.

**Review needed / commit-msg.** The agent that wrote a branch also merged
it on a green gate: nobody else read the diff. So a merge into `main` that
changes `review_lines` lines of code or touches a risky path or pattern
needs a review by a fresh read-only session first (`devloop review`), and
its message carries a `Review:` trailer. `Review: skip <reason>` merges
without one and says why where `git log` shows it.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from config import Config


def git(cfg: Config, *args: str, cwd: Path | None = None, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(cwd or cfg.root), *args],
                          capture_output=True, text=True, check=check).stdout


def branch(cfg: Config) -> str:
    return git(cfg, "rev-parse", "--abbrev-ref", "HEAD").strip()


def is_test(cfg: Config, path: str) -> bool:
    return path.startswith(tuple(cfg["software"]["tests"]))


def added_lines(cfg: Config, commit: str, path: str) -> list[str]:
    diff = git(cfg, "show", "--format=", "--unified=0", commit, "--", path)
    return [l[1:].strip() for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++") and l[1:].strip()]


def fill(command: str, **values: str) -> str:
    for key, value in values.items():
        command = command.replace("{" + key + "}", value)
    return command


def targets(cfg: Config, files: list[str]) -> list[str]:
    pattern = cfg["software"]["target_pattern"]
    if not pattern:
        return []
    return sorted({m.group(1) for f in files if (m := re.search(pattern, f))})


def run_tests(cfg: Config, tree: Path, scratch: Path, files: list[str], extra: str = "") -> tuple[bool | None, str]:
    """Build (when `software.build` is set) and run `software.test` over the
    given test files in `tree`. Returns (passed, output); passed is None
    when it couldn't build. `{target}` in the command runs it once per
    target that `target_pattern` finds; otherwise `{files}` gets the files."""
    sw = cfg["software"]
    quoted = " ".join(shlex.quote(f) for f in files)
    if sw["build"]:
        built = subprocess.run(fill(sw["build"], scratch=str(scratch), files=quoted), shell=True,
                               cwd=tree, capture_output=True, text=True, timeout=3600)
        if built.returncode != 0:
            return None, built.stdout[-3000:] + built.stderr[-3000:]
    commands = ([fill(sw["test"], target=t, scratch=str(scratch), files=quoted) for t in targets(cfg, files)]
                if "{target}" in sw["test"] else [fill(sw["test"], scratch=str(scratch), files=quoted)])
    output, passed = "", True
    for command in commands:
        run = subprocess.run(f"{command} {extra}".strip(), shell=True, cwd=tree,
                             capture_output=True, text=True, timeout=1800)
        output += run.stdout[-3000:] + run.stderr[-3000:]
        passed = passed and run.returncode == 0
    return passed, output


def scratch_dir(cfg: Config, name: str) -> Path:
    return Path(os.environ.get("DEVLOOP_SCRATCH") or cfg.cache / name)


def red_first(cfg: Config) -> list[str]:
    sw, fails = cfg["software"], []
    here = branch(cfg)
    if not here.startswith(sw["bugfix_prefix"]):
        print(f"red-first: {here} isn't a {sw['bugfix_prefix']} branch — nothing to check")
        return []
    base = git(cfg, "merge-base", cfg["main"], "HEAD").strip()
    commits = git(cfg, "rev-list", "--reverse", "--first-parent", f"{base}..HEAD").split()
    if not commits:
        if git(cfg, "status", "--porcelain", "--untracked-files=no").strip():
            return ["red-first: nothing is committed on this bugfix branch yet. Commit the failing test alone first, then fix."]
        print("red-first: no commits on the branch yet")
        return []
    red = commits[0]
    skip = git(cfg, "log", "-1", "--format=%(trailers:key=Red-first,valueonly)", red).strip()
    if skip:
        print(f"red-first: exempt — {skip}")
        return []
    files = [f for f in git(cfg, "diff-tree", "--no-commit-id", "--name-only", "-r", red).split("\n") if f]
    tests = [f for f in files if is_test(cfg, f)]
    others = [f for f in files if not is_test(cfg, f)]
    if others or not tests:
        return [f"red-first: the branch's first commit {red[:7]} must be the failing test alone; it changes "
                + (", ".join(others) if others else "no test file")
                + f" (tests are under {', '.join(sw['tests'])}). Commit the reproducing test first, then the fix."]
    for path in tests:
        file = cfg.root / path
        if not file.exists():
            fails.append(f"red-first: {path}, the red commit's test, is gone")
            continue
        now = {line.strip() for line in file.read_text(encoding="utf-8").splitlines()}
        missing = [line for line in added_lines(cfg, red, path) if line not in now]
        if missing:
            fails.append(f"red-first: the fix changed what {path} asserts — lines the red commit added are gone:\n    "
                         + "\n    ".join(missing[:5]))
    if fails:
        return fails
    if not sw["test"] or ("{target}" in sw["test"] and not targets(cfg, tests)):
        print("red-first: shape checked; red not run (no `software.test` that reaches these files)")
        return []

    scratch = scratch_dir(cfg, "red-first")
    tree, build = scratch / "tree", scratch / "build"
    subprocess.run(["git", "-C", str(cfg.root), "worktree", "remove", "--force", str(tree)], capture_output=True)
    shutil.rmtree(tree, ignore_errors=True)
    tree.parent.mkdir(parents=True, exist_ok=True)
    git(cfg, "worktree", "add", "-q", "--detach", str(tree), red)
    try:
        passed, output = run_tests(cfg, tree, build, tests)
    finally:
        subprocess.run(["git", "-C", str(cfg.root), "worktree", "remove", "--force", str(tree)], capture_output=True)
    if passed is None:
        print(output, file=sys.stderr)
        return [f"red-first: the red commit {red[:7]} doesn't build. A reproduction fails at an assertion: "
                "write the test against what exists, or add a `Red-first: skip <reason>` trailer."]
    if passed:
        return [f"red-first: the tests pass at the red commit {red[:7]} — they don't reproduce the bug."]
    print(f"red-first: the tests fail at {red[:7]}, as they should")
    return []


def backlog_closed(cfg: Config) -> list[str]:
    sw = cfg["software"]
    here = branch(cfg)
    if cfg.tier < 1 or not here.startswith(sw["bugfix_prefix"]):
        print(f"backlog-closed: {here} isn't a {sw['bugfix_prefix']} branch — nothing to check")
        return []
    base = git(cfg, "merge-base", cfg["main"], "HEAD").strip()
    if not git(cfg, "diff", "--name-only", base).strip():
        print("backlog-closed: nothing changed on the branch yet")
        return []
    for commit in git(cfg, "rev-list", f"{base}..HEAD").split():
        reason = git(cfg, "log", "-1", "--format=%(trailers:key=Backlog,valueonly)", commit).strip()
        if reason.lower().startswith("none"):
            print(f"backlog-closed: exempt — {reason}")
            return []
    item = {cfg.docname("backlog"): re.compile(r"^-- \*\*P[0-3]\*\*"),
            cfg.docname("inbox"): re.compile(r"^-- \*\*\d{4}-\d{2}-\d{2}\*\*")}
    for path, pattern in item.items():
        if any(pattern.match(line) for line in git(cfg, "diff", base, "--", path).splitlines()):
            print(f"backlog-closed: the fix removes its {path} line")
            return []
    return [f"backlog-closed: this bugfix branch removes no {cfg.docname('backlog')} item or "
            f"{cfg.docname('inbox')} capture. Delete the bug's line in the fix's commit, or add a "
            "`Backlog: none <reason>` trailer to a commit when it was never written down."]


def review_file(cfg: Config, tip: str) -> Path:
    return cfg.cache / "reviews" / f"{tip}.md"


def review_reasons(cfg: Config, base: str, tip: str) -> list[str]:
    sw = cfg["software"]
    found, lines = [], 0
    risk_content = re.compile("|".join(sw["review_risk_content"])) if sw["review_risk_content"] else None
    for row in git(cfg, "diff", "--numstat", f"{base}...{tip}").splitlines():
        added, deleted, path = row.split("\t", 2)
        if added == "-" or is_test(cfg, path) or not any(fnmatch.fnmatch(path, g) for g in sw["review_code"]):
            continue
        lines += int(added) + int(deleted)
        if path.startswith(tuple(sw["review_risk_paths"])) and sw["review_risk_paths"]:
            found.append(f"{path} is on a risky path (software.review_risk_paths)")
            continue
        if risk_content:
            text = git(cfg, "show", f"{tip}:{path}", check=False)
            if risk_content.search(text):
                found.append(f"{path} matches a risky pattern (software.review_risk_content)")
    if lines >= sw["review_lines"]:
        found.insert(0, f"{lines} lines of code changed (review from {sw['review_lines']})")
    return found


def commit_msg(cfg: Config, message_file: str) -> int:
    """The commit-msg hook: a due merge into main carries its review."""
    git_dir = Path(git(cfg, "rev-parse", "--absolute-git-dir").strip())
    if not (git_dir / "MERGE_HEAD").exists() or branch(cfg) != cfg["main"]:
        return 0
    tip = (git_dir / "MERGE_HEAD").read_text().split()[0]
    due = review_reasons(cfg, "HEAD", tip)
    if not due:
        return 0
    trailers = git(cfg, "interpret-trailers", "--parse", message_file)
    trailer = next((l for l in trailers.splitlines() if l.lower().startswith("review:")), "")
    if re.match(r"(?i)^review: *skip \S", trailer):
        return 0
    short, file = tip[:7], review_file(cfg, tip)
    if not file.exists():
        print(f"Merge blocked: {short} needs an independent review first, because:", file=sys.stderr)
        print("\n".join(f"  - {d}" for d in due), file=sys.stderr)
        print(f"\nRun `devloop review` on the branch (it reviews {short}), fix what matters, review the new tip,\n"
              "then merge with a `Review: <outcome>` trailer — or `Review: skip <reason>`.", file=sys.stderr)
        return 1
    if not trailer:
        print(f"Merge blocked: {short} was reviewed ({file}) but the message has no `Review:` trailer.\n"
              "Add one, e.g. `Review: 3 fixed, 2 captured, 1 dismissed — <what>`.", file=sys.stderr)
        return 1
    return 0


REVIEW_TOOLS = ["Read", "Grep", "Glob", "Agent", "Skill", "Bash(git diff:*)", "Bash(git log:*)",
                "Bash(git show:*)", "Bash(git merge-base:*)", "Bash(git rev-parse:*)", "Bash(git blame:*)"]


def review(cfg: Config, base: str | None, tip: str | None) -> int:
    """An independent review: /code-review in a fresh headless session that
    can only read, saved under the tip's SHA where commit-msg looks."""
    explicit = tip is not None
    tip = git(cfg, "rev-parse", tip or "HEAD").strip()
    base = git(cfg, "rev-parse", base or git(cfg, "merge-base", cfg["main"], tip).strip()).strip()
    if not explicit and git(cfg, "status", "--porcelain", "--untracked-files=no").strip():
        print("review: commit first — uncommitted changes aren't what merges.", file=sys.stderr)
        return 1
    if base == tip:
        print(f"review: nothing between {cfg['main']} and {tip[:7]}.", file=sys.stderr)
        return 1
    file = review_file(cfg, tip)
    file.parent.mkdir(parents=True, exist_ok=True)
    rng = f"{base[:12]}...{tip[:12]}"
    # The diff and log are saved for the reviewer to Read: a Bash allowlist
    # can be defeated by a hook that rewrites commands (`git diff` → `rtk git
    # diff`), and the first smoke review then saw only the tree at HEAD.
    diff, log = file.with_suffix(".diff"), file.with_suffix(".log")
    diff.write_text(git(cfg, "diff", f"{base}...{tip}"), encoding="utf-8")
    log.write_text(git(cfg, "log", "--format=%H %s%n%n%b", f"{base}..{tip}"), encoding="utf-8")
    print(f"review: reviewing {rng} — this takes a few minutes", file=sys.stderr)
    session = subprocess.run(
        ["claude", "-p", f"/code-review high — the change under review is `git diff {base}...{tip}` "
                         f"(commits: `git log {base}..{tip}`), not the working tree. Both are saved: "
                         f"Read {diff} for the diff and {log} for the commits, titles and bodies",
         "--append-system-prompt", f"You are reviewing a branch you did not write, before it merges into "
                                   f"{cfg['main']}. Read {cfg.docname('agents')} first: its conventions are the bar, "
                                   "along with any stage file or backlog line the commits name. Do not edit anything.",
         "--allowedTools", *REVIEW_TOOLS, "--permission-mode", "dontAsk", "--no-session-persistence",
         "--output-format", "text"],
        cwd=cfg.root, capture_output=True, text=True,
    )
    if session.returncode != 0:
        print(session.stderr[-2000:], file=sys.stderr)
        return session.returncode
    from datetime import datetime
    file.write_text(f"# Review of {rng}\n\n- Base: {base}\n- Tip: {tip}\n- Date: "
                    f"{datetime.now():%Y-%m-%d %H:%M}\n\n{session.stdout}", encoding="utf-8")
    print(file.read_text(encoding="utf-8"))
    print(f"review: saved {file}", file=sys.stderr)
    return 0
