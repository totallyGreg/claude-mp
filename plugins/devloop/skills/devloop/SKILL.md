---
name: devloop
description: This skill should be used when the user asks to "set up a development loop", "add a backlog to this repo", "init devloop", "capture this idea", "triage the inbox", "review the backlog", "what should I work on next", "rank the backlog", "why did the loop check fail", "fix a bug red-first", "configure loop.toml", "add a review gate", or "run the config evals" in a git repository agents work in (code, infrastructure or docs). Covers the capture → triage → review → plan → build → ship → compound loop, its documents (AGENTS, INBOX, BACKLOG, PLAN, DECISIONS, LOOP), loop.toml, and the checks and hooks that enforce it. Do NOT use for personal tasks or OmniFocus (use attache), Obsidian vault notes (use archivist), or git mechanics alone (use chronicle).
metadata:
  author: J. Greg Williams
  version: "0.1.0"
compatibility: Requires git, uv (scripts run with Python 3.11+ via uv), and the claude CLI for review and evals
license: MIT
---

# devloop

A development loop for any git repository where agents do the work. Every
step ends in a committed document the next step reads, and every rule that
git or a script can check ships as a check or a hook. The repository holds
only its documents and `loop.toml`; the checks run from this plugin.

`D="${CLAUDE_PLUGIN_ROOT}/skills/devloop/scripts/devloop.py"` — outside a
Claude session, `"$(git config devloop.root)"/skills/devloop/scripts/devloop.py`
(the session-start hook keeps that pointer current).

## The loop

| Step | Do | Enforced by |
|------|----|-------------|
| Capture | `/capture <text>` → INBOX § Open, stamped, committed alone. Never triage here | `capture` |
| Triage | Each Open line → one BACKLOG item with priority and Area, or a rejected idea; delete it from INBOX | loop check (struck/done lines fail) |
| Review | When the session start says due: `/review-backlog` | `nudge` (SessionStart) |
| Plan | Rewrite BACKLOG § Now: ≤3, Now #1 = top of `$D rank` or `**Chosen** — <reason> —` | loop check |
| Build | One sitting: a branch, the backlog line is the brief. Handed off: a `stages/` brief + PLAN row | loop check (stages) |
| Ship | The gate green, the end-to-end check *shown*; tick `## Steps` in the commit that finishes it | the repo's gate + `$D check` |
| Compound | A rule worth keeping → AGENTS.md, one line naming its enforcer | doc check (index, cap) |

Why each rule exists, the priority scale and the grammars:
`references/grammar.md`.

## Set up a repository

Run `/devloop-init`. It reads the repository, asks only for what it can't
infer (kind, tier, gate, Areas), writes `loop.toml` and the documents
(never overwriting), and shows `$D check`. Then add `$D check` to the
repository's gate command; init prints the line but never edits build files.

| Tier | Turns on | When |
|------|----------|------|
| 0 | AGENTS.md, INBOX, `/capture`, the gate, no-blanket-add | Any repository |
| 1 | + BACKLOG, PLAN, DECISIONS, LOOP; loop check, ranking, review-due | Multi-month work |
| 2 | + review gate (commit-msg) and evals (software profile) | When it has earned it |

Every key, its default, and an existing repository's adoption path:
`references/loop-toml.md`.

## Commands

```bash
$D check [--only docs loop red-first backlog-closed]   # the gate's checks; exit 1 on failure
$D rank                         # the ranked "what next"
$D capture "<text>"             # what /capture runs
$D review-needed <base> <tip>   # exit 0 + reasons when a merge needs review
$D review                       # read-only /code-review in a fresh claude -p, saved by tip SHA
$D evals [<id> …]               # replay past fixes under today's configuration (slow)
```

## When a check fails

Read the FAIL line: it names the file, the line and the fix.

```
[2/2] loop
  FAIL  BACKLOG.md:44: unknown Area 'Bogus' — loop.toml `areas` lists the known ones
  FAIL  BACKLOG.md:53: one line per item — move the detail to backlog/<slug>.md and link it
```

Fix the document, not the check. Never weaken a check to pass; if a rule is wrong,
change `loop.toml` (a cap, an Area) and say why in the commit. A check that
crashes is a failure, not a pass.

## The software profile

`kind = "software"` adds, for `bugfix/` branches: **red-first** (the first
commit is the failing test alone, and it fails at that commit) and
**backlog-closed** (the fix deletes its backlog line). Tier 2 adds the
**review gate** and **evals**. Procedures, trailers and the eval case
format: `references/software-profile.md`.

## Rules for agents in a devloop repository

- Stage files by name — the no-blanket-add hook blocks `git add .`, `-A`, `-u`, `commit -a`.
- The commit is the postmortem: the title says what changed, the body what was wrong and how it was found.
- Work finished from any list leaves it in the commit that finished it.
- A hook or nudge never fails a session start; a check fails the gate; a due item nudges.
- The repository is the definition. Notes elsewhere (a vault) link to it, never restate it.

## Reference Documentation

| Reference | Content |
|-----------|---------|
| `references/grammar.md` | Document grammars, the priority scale, ranking, and why each loop rule exists |
| `references/loop-toml.md` | Every `loop.toml` key and default; adopting devloop in an existing repository |
| `references/software-profile.md` | Red-first, backlog-closed, the review gate, evals and their case file |
