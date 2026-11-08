---
description: Review the backlog — verify, regroup, re-rank, rewrite Now
argument-hint: (none)
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/devloop/scripts/devloop.py:*), Bash(git log:*), Bash(git show:*), Bash(git diff:*), Bash(git status:*), Bash(git add:*), Bash(git commit:*), Read, Edit, Grep, Glob
---

Review the backlog so it is true, grouped and ranked. A release, a week, or five
inbox captures make this due; the session start says so. Run it then, before other
work. `D="${CLAUDE_PLUGIN_ROOT}"/skills/devloop/scripts/devloop.py`. Document names,
Areas and caps come from the repository's `loop.toml`.

## 1. Gather evidence (read-only)

- Inbox § Open: each line is triaged in step 2. Check it against git first; a
  capture already fixed is just deleted.
- Every § Work item: `git log --oneline --since=<its date> --grep=<key words>` and
  read the code or files it names. Decide **fixed** (delete it), **still true**
  (keep, maybe re-rank), or **unknown** (needs a repro — say so, don't guess).
- § Verify, § Blocked, § Questions: still accurate? Blocked rows are unblocked,
  split, or dropped with a reason — never left by default.

## 2. Triage, regroup and re-rank § Work

- Each inbox line becomes one § Work item (or Blocked / Questions, or a rejected
  idea with the reason) and is deleted from the inbox.
- Group items one branch would fix together: a shared file, cause or surface. Bugs
  and improvements share groups; a heading names the thing being fixed.
- Priority is what it costs to leave the item undone (P0–P3, LOOP.md). A P1 that has
  sat for a month is either not P1 or belongs in Now.
- The grammar is the loop check's; `$D check --only loop` says where a line breaks it.

## 3. Rewrite § Now

Up to three items from the top of `$D rank`; at most one marked `**Itch** —`. Now #1
is the ranked top or starts `**Chosen** — <reason> —`. A stage is named by its open
step ("S7 step 2"). Check every in-progress stage's `## Steps` against git: tick what
shipped, with where; a stage with every box ticked is `**Status:** shipped` and
leaves the plan and Now.

## 4. Close

- Set `Reviewed: <today>` in the backlog.
- `$D check` green. Commit the documents you changed, by name, titled
  `Backlog review: …`, listing what was deleted as fixed and what changed rank.
- End with the **decisions only the user can make** — Blocked choices, priorities
  that depend on intent, repros needing their hardware or data — as a short
  numbered list. Don't make them.
