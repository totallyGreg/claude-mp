---
name: chronicle
description: This skill should be used when the user asks to "write a commit message", "write good commits", "configure a branching strategy", "configure git workflow", "fix a merge conflict", "review merge strategies", "analyze branching strategies", "run parallel experiments in git", "build a multi-agent git workflow", "add version control to documents", "convert from svn to git", "review git best practices", "write commit messages for documents", or any question about managing change across code, documents, or content using git, jujutsu, subversion, or other version control tools.
metadata:
  author: J. Greg Williams
  version: "0.1.0"
compatibility: Works with any git installation; jj references require jujutsu installed
license: MIT
---

# Version Control

Managing change well is not just about tracking history — it is about making that history navigable, reversible, and meaningful. This skill covers the full spectrum from daily commit craft to multi-agent experiment orchestration, with git as the primary tool and jujutsu as a modern alternative worth understanding.

## Core Philosophy

Three principles underpin all good version control practice:

1. **Atomic** — each unit of change (commit, patch, revision) captures one logical idea. If you can't describe it in a single imperative sentence, it's probably two commits.
2. **Descriptive** — history is documentation. A well-written commit message is a gift to future readers (including yourself in six months).
3. **Reversible** — prefer strategies that preserve options. Avoid rewriting shared history. Design branches so that reverting them is safe and cheap.

## Tool Orientation

| Tool | Era | Still Relevant? | Notes |
|------|-----|----------------|-------|
| RCS | 1982 | Rarely | Single-file locking model; foundational concepts |
| CVS | 1990 | Legacy only | Centralized; first "directory" VCS |
| Subversion (SVN) | 2000 | Yes, in enterprises | Centralized; still common in regulated industries |
| Git | 2005 | Dominant | Distributed; default recommendation |
| Jujutsu (jj) | 2022 | Growing | Built on git's storage; paradigm shift worth learning |

For detailed history and non-code use cases, see `references/vcs-history.md`.

## Prescribed Defaults

These are the opinionated defaults — understand the tradeoffs before departing from them.

### Branching: Trunk-Based Development

Keep a single long-lived branch (`main`). Work in short-lived feature branches (hours to days, not weeks). Merge frequently. Use feature flags for incomplete work rather than long-lived branches.

**When to deviate**: Release management for versioned software, regulated environments requiring audit trails per-release, or open-source projects with async contribution patterns (use GitHub flow instead). See `references/branching-strategies.md` for the full decision tree.

### Merging: Rebase Local, Merge Shared

- **Local, unshared branches**: rebase onto the target — produces linear, readable history
- **Shared or reviewed branches**: merge commit — preserves the branch's existence in history, makes reverting safe
- **Completed features**: squash-merge into main when the branch's internal commits are noisy and the feature is small enough to be one logical unit

**Never rebase shared history.** Once a commit has been pushed and others have based work on it, rewriting it creates divergence that is painful to untangle.

For the full decision tree with advanced strategies (cherry-pick, octopus merge, rerere), see `references/merge-strategies.md`.

### Commit Messages: Imperative, 50/72

```
<type>(<scope>): <imperative summary under 50 chars>

<body wrapped at 72 chars — the why, not the what>

<footer: issue refs, breaking change notices>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`

The summary line answers: *"If applied, this commit will ___."*

For conventional commits, signing, amend discipline, and non-code content, see `references/commit-craft.md`.

## Multi-Agent Worktree Experiments

Git worktrees allow multiple working trees from the same repository simultaneously — each in a different directory, each on a different branch, sharing the same object store.

This makes worktrees ideal for parallel experimentation:

```bash
# Set up three parallel experiments
git worktree add ../experiment-a experiment/approach-a-$(date +%Y%m%d)
git worktree add ../experiment-b experiment/approach-b-$(date +%Y%m%d)
git worktree add ../experiment-c experiment/approach-c-$(date +%Y%m%d)
```

Each agent works in its own worktree independently. When experiments complete, evaluate results and integrate the best approach back to the parent branch using the appropriate merge strategy for the confidence level.

For full patterns including result evaluation, partial cherry-pick integration, and cleanup, see `references/worktrees-experiments.md`.

## Jujutsu (jj)

Jujutsu is a version control system built on git's storage layer, designed around first-class conflicts and an operation log that makes everything undoable. It eliminates the staging area and treats the working copy as a commit in progress.

Key mental model shift: in jj, there is no "detached HEAD" — you are always on a commit. Conflicts are stored in the repository and resolved lazily rather than halting your workflow.

```bash
# jj equivalent of git's common operations
jj new          # start a new change (like git checkout -b)
jj describe     # write a commit message for the current change
jj squash       # fold current change into parent
jj rebase -d @- # rebase current change onto parent's parent
```

For a full jj workflow guide and git↔jj mental model mapping, see `references/jujutsu.md`.

## Non-Code Use Cases

Version control is not limited to source code. Any content where change matters — documents, configurations, data files, note vaults — benefits from the same principles:

- **Documents**: track drafts, collaborate without overwrite, compare versions with `git diff`
- **Configuration**: version infrastructure config, dotfiles, or application settings
- **Data files**: CSV, JSON, YAML — git diffs are readable and meaningful
- **Note vaults**: Obsidian vaults in git give you history, sync, and conflict resolution

The same atomic/descriptive/reversible philosophy applies. Commit message discipline matters even more when non-developers are reading the history.

## Quick Decision Guide

```
Need to change something? →
  Is the change complete and logical? → commit it atomically
  Is it exploratory? → new branch or jj change

Need to integrate? →
  Is the branch local/unshared? → rebase
  Is it shared or reviewed? → merge commit
  Is it small and noisy internally? → squash merge

Need to experiment in parallel? →
  Use worktrees (see references/worktrees-experiments.md)

Choosing a branching model? →
  Default: trunk-based
  Complex release cadence: see references/branching-strategies.md

Want a different paradigm entirely? →
  Evaluate jj (see references/jujutsu.md)
```

## Additional Resources

### Reference Files

- **`references/commit-craft.md`** — Atomic commits, message format, conventional commits, amend discipline, signing, non-code content
- **`references/branching-strategies.md`** — Trunk-based, GitHub flow, git-flow, release branching — full decision tree
- **`references/merge-strategies.md`** — merge/rebase/squash/cherry-pick/octopus — when each is appropriate with worked examples
- **`references/worktrees-experiments.md`** — Multi-agent experiment patterns, parallel worktrees, evaluating and integrating results
- **`references/jujutsu.md`** — jj workflow, first-class conflicts, git↔jj mental model map, when to prefer jj
- **`references/vcs-history.md`** — RCS→CVS→SVN→Git lineage, non-code use cases, SVN in regulated environments
