# devloop

A capture-to-ship development loop for any git repository agents work in — code, infrastructure or docs — with checks and hooks that enforce its rules.

Every step of the loop ends in a committed document the next step reads. Every rule that git or a script can check ships as a check or a hook, and evals guard only judgment. A repository holds its documents and one `loop.toml`; the checks run from this plugin and read it. Packaged from AudiobookOCD's loop (design: `docs/plans/2026-11-08-001-feat-devloop-plan.md`).

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

A capture-to-ship development loop for any git repository agents work in: loop documents, one config file, and checks and hooks that enforce the rules.

**At a glance:** 1 skill · 3 commands · 2 hooks

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install devloop@totally-tools
```
<!-- END AUTOGEN:overview -->

## Quickstart

```
/devloop-init                      # in a git repo: loop.toml + AGENTS, INBOX (+ BACKLOG, PLAN, DECISIONS, LOOP)
/capture the export drops the last row
/review-backlog                    # when the session start says it's due
```

Then add the checks to the repository's gate:

```bash
"$(git config devloop.root)"/skills/devloop/scripts/devloop.py check
```

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (1)

| Skill | Description |
|-------|-------|
| `devloop` | A development loop for any git repository where agents do the work. |

### Commands (3)

| Command | Description |
|-------|-------|
| `/capture` | Capture an idea or bug into the repo's INBOX without breaking stride |
| `/devloop-init` | Set up the devloop in this git repository — loop.toml and the loop documents |
| `/review-backlog` | Review the backlog — verify, regroup, re-rank, rewrite Now |

### Hooks (2)

| Hook | Trigger | Purpose |
|-------|-------|-------|
| `no_blanket_add.py` | PreToolUse Bash |  |
| `devloop.py` | SessionStart |  |
<!-- END AUTOGEN:components -->
## Changelog

| Version | Changes |
|---------|---------|
| 0.1.0 | New plugin: core (loop skill, init, `/capture`, `/review-backlog`, loop/doc checks, ranking, review-due, no-blanket-add) and the `software` profile (red-first, backlog-closed, review gate, evals) |

## Skill: devloop

### Current Metrics

**Score: 98/100** (Excellent) — 2026-11-08

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 0.1.0 | 2026-11-08 | - | New skill: the loop, its documents and grammars, loop.toml, the software profile; issue not yet filed | 100 | 90 | 100 | 100 | 100 | 98 |
