# The software profile

`kind = "software"` in loop.toml. Red-first and backlog-closed run in
`devloop.py check` (so the gate); the review gate and evals are tier 2.

## Contents

- [Fixing a bug](#fixing-a-bug)
- [Red first](#red-first)
- [Backlog closed](#backlog-closed)
- [The review gate](#the-review-gate)
- [Evals](#evals)

## Fixing a bug

"Fix X" means: `bugfix/<name>` → the failing test, committed alone → the fix
→ the gate green → commit, deleting the item's BACKLOG line (and `backlog/`
file) in that commit → `devloop.py review` when `review-needed` says it's due
→ merge with `--no-ff` → delete the branch. Push and release wait to be asked.

## Red first

A fix and its test written together prove only that they agree. A test
committed first, seen failing, then left alone while the code changes proves
the bug is gone. On a `bugfix_prefix` branch the check requires:

1. The first commit changes only files under `tests`.
2. At that commit the tests fail: a detached worktree in the cache, `build`
   then `test`. A build failure is not a reproduction — write the test against
   what exists.
3. Every line the first commit added to a test is still in the working tree:
   the fix didn't weaken its judge.

A branch with changes and no commit yet fails: the red commit must exist
before the gate runs. Exempt a fix no test can reach (a build setting, a
UI-only defect) with a `Red-first: skip <reason>` trailer on the first commit.

## Backlog closed

From the merge-base with `main` to the working tree, BACKLOG must lose an item
line or INBOX a capture. Exempt a bug found and fixed in one sitting, never
written down, with `Backlog: none <reason>` on any commit of the branch.

## The review gate

The agent that wrote a branch shouldn't be its only reader. A merge into
`main` needs an independent review when `review-needed <base> <tip>` says so:
`review_lines` lines of `review_code` changed, or a `review_risk_paths` path
or `review_risk_content` match.

- `devloop.py review` runs `/code-review high` in a fresh headless `claude -p`
  with read-only tools and saves the findings to the cache under the tip SHA.
  The diff and commit log are saved beside it (`<tip>.diff`, `<tip>.log`) for
  the reviewer to Read, so a review never depends on Bash permissions (a hook
  that rewrites `git diff` defeats an allowlist). The tree must be clean: what
  is reviewed is what merges.
- Fix what matters, review the new tip, and merge with a trailer:
  `Review: 3 fixed, 2 captured, 1 dismissed — <what>`, or `Review: skip <reason>`.
- The commit-msg hook (`.githooks/commit-msg`, a shim init writes) blocks a due
  merge with no saved review or no trailer. Bypass once: `git merge --no-verify`.

## Evals

The configuration (AGENTS.md, the loop documents, commands, hooks) is
regression-tested like code, on the repository's own past bug fixes. Each
fix's merge deleted the BACKLOG line that stated the bug (the task) and added
tests that prove it gone (the check). `evals/cases.json`:

```json
{"cases": [
  {"id": "author-title-split", "merge": "3bb04c6",
   "skip": {"pattern": "authorDashTitle\\b",
            "why": "the line asks for folder names; the fix also split file names, which no reader of the line could know"}}
]}
```

`skip` scopes the grade, with a reason, when the fix's tests ask for more than
the task line says. Each case: a worktree at the merge's first parent, today's
configuration overlaid (`evals_overlay`), a headless agent given the line,
then graded — **fixed** (the fix's own tests pass over the agent's code) and
**red-first** — with turns, time and cost. Results: the cache's `evals/`.

Run the cases a changed rule touches (`devloop.py evals <id>`) when the
session start says evals are due, all of them for a rewrite; never in the
gate. **Each eval finding becomes a deterministic check**, so the set shrinks:
backlog-closed exists because the first eval found an agent leaving the line.
