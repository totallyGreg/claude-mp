# Jujutsu (jj)

Jujutsu is a version control system built on git's storage layer. It is compatible with git repositories and can be adopted incrementally. Its design resolves several of git's most persistent friction points by rethinking the fundamental model.

## The Core Mental Model Shift

In git, the working directory is separate from commits. Work exists in a liminal state until staged, then committed. HEAD points to the last commit; the working tree may or may not match it.

In jj, **the working copy is always a commit**. There is no staging area. Every save to disk is automatically part of the current change. When work is ready, it gets described (given a message) and a new empty change begins.

```
git model:
  [working tree] → [staging area] → [commit] → [commit] → ...
                        add ↑          commit ↑

jj model:
  [current change (auto-recorded)] → [change] → [change] → ...
                                      describe ↑
```

This eliminates the staging area entirely and makes "I forgot to stage that file" impossible.

## Installation and Git Coexistence

```bash
# macOS
brew install jj

# Initialize jj in an existing git repo
cd my-git-repo
jj git init --colocate    # jj and git coexist; .git/ is shared

# Clone a git repo with jj
jj git clone https://github.com/org/repo
```

In colocated mode, both `jj` and `git` commands work. Commits made with jj are visible to git and vice versa. This makes incremental adoption safe — team members can continue using git while one person experiments with jj.

## Core Commands: git↔jj Mental Model Map

| Intent | git | jj |
|--------|-----|----|
| See status | `git status` | `jj status` / `jj st` |
| See log | `git log --oneline --graph` | `jj log` |
| Describe current work | `git commit -m "..."` | `jj describe -m "..."` |
| Start new work | `git checkout -b new-branch` | `jj new` |
| Create named bookmark | `git branch name` | `jj bookmark create name` |
| Switch to existing work | `git checkout branch` | `jj edit <change-id>` |
| Incorporate upstream | `git pull --rebase` | `jj rebase -d main@origin` |
| Squash into parent | `git commit --amend` (roughly) | `jj squash` |
| Split a change | `git add -p` + two commits | `jj split` |
| Undo last operation | `git reflog` + reset | `jj undo` |
| Inspect full history | `git log --all` | `jj log -r 'all()'` |

## Change IDs vs Commit SHAs

Every change in jj has two identifiers:

1. **Change ID**: stable, persists through rewrites. This is what jj uses for most operations. Example: `qmvznykp`
2. **Commit ID**: the git SHA, changes when the commit is rewritten.

This distinction is profound: in git, rebasing produces new SHAs that break references. In jj, the change ID remains stable through any rewrite, so references don't break.

```bash
jj log
# @  qmvznykp you@example.com 2025-04-01 15:32:44
# │  (no description set)
# ○  wqnykzlp you@example.com 2025-04-01 14:00:00
# │  feat(auth): add OAuth2 refresh token rotation
```

`@` is the current change (working copy). Refer to changes by their short ID.

## First-Class Conflicts

In git, a merge conflict halts the operation. The working tree is left in a conflicted state that must be resolved before work can continue.

In jj, **conflicts are stored in the repository as a state**. Work can continue through a conflict; it does not block commits or rebases.

```bash
jj rebase -d main    # rebase current change onto main
# If a conflict exists, it is recorded in the commit — not blocking

jj resolve           # open a merge tool to resolve the conflict when ready
jj log               # conflict is marked with a (conflict) indicator
```

This is particularly valuable for multi-step rebases and large integrations: conflicts can be identified, catalogued, and resolved systematically rather than interrupting the workflow at each occurrence.

## The Operation Log

Every jj command that changes the repository is recorded in an operation log. Any operation can be undone.

```bash
jj op log            # see all operations
jj undo              # undo the last operation
jj op restore <id>   # restore to any prior state
```

This is more powerful than git's reflog. It is not just commits that are logged — branch moves, rebases, and configuration changes are all reversible. "I made a mistake" becomes "jj undo" in almost every scenario.

## Typical jj Workflow

### Daily development

```bash
# Start a new session — create a fresh change from main
jj new main -m "feat(payments): add webhook signature verification"

# Work normally — files are auto-tracked
# No git add needed

# See what's changed
jj diff
jj status

# Refine the description
jj describe -m "feat(payments): add HMAC-SHA256 webhook signature verification"

# Create a bookmark (branch) to push
jj bookmark create feature/webhook-signatures -r @

# Push to remote
jj git push --bookmark feature/webhook-signatures
```

### Amending in-progress work

```bash
# Make more changes, fold them into the current change
jj squash               # fold working copy into the parent change

# Or fold into a specific ancestor
jj squash --into <change-id>
```

### Splitting a change

```bash
jj split               # interactive: choose which hunks go into which change
```

This is the jj equivalent of `git add -p` + two commits, but operates on an existing commit rather than staged changes.

### Rebasing

```bash
# Rebase current change onto latest main
jj rebase -d main@origin

# Rebase a range of changes
jj rebase -s <start-change-id> -d <destination>

# Rebase multiple changes simultaneously (powerful for reorganizing work)
jj rebase -r 'ancestors(feature)' -d main
```

Because jj tracks change IDs, rebasing does not break references — other changes that depend on the rebased one are automatically updated.

## Revsets: Querying History

jj uses a functional query language called revsets to address sets of changes:

```bash
jj log -r 'main..@'              # changes between main and current
jj log -r 'ancestors(@, 5)'      # last 5 ancestors of current
jj log -r 'description("feat")'  # changes with "feat" in the message
jj log -r 'author("alice")'      # changes by a specific author
jj log -r 'conflict()'           # changes with unresolved conflicts
jj log -r 'all()'                # everything
```

Revsets can be combined: `jj log -r 'main..@ & author("alice")'`

This is significantly more expressive than git's revision syntax.

## When to Prefer jj

**Prefer jj when:**
- Working on complex, multi-step rebases (first-class conflicts reduce friction significantly)
- Running parallel experiments (change IDs remain stable through reorganization)
- Solo developer wanting an undo-everything safety net
- Interested in a cleaner conceptual model without the staging area
- The repository already uses git (colocated mode makes adoption low-risk)

**Stick with git when:**
- Team tooling assumes git (GitHub Actions, CI, PR workflows all work with jj via colocated mode, but requires setup)
- Team members are unfamiliar with jj and training cost outweighs benefit
- Third-party integrations (git hooks, IDE extensions) need pure git behavior

**Both simultaneously (colocated mode):**
In a colocated repo, `git` and `jj` commands both work. Use jj for local work (commits, rebases, splits), use git for remote operations (push, pull) if the team expects git. This is a practical adoption path — the individual gains jj's benefits without requiring the team to change.

## jj for Non-Code Content

jj's strengths apply equally to documents, configurations, and any diffable content:

- **Operation log**: every edit is reversible, far beyond git's reflog
- **First-class conflicts**: document conflicts can be deferred and resolved in batch
- **Auto-tracking**: no staging area means no "I forgot to add this file" scenarios
- **Splitting changes**: `jj split` makes it easy to separate a document reorganization from a content edit, even after the fact

For personal document vaults, jj's operation log is particularly compelling — it provides a safety net that git's reflog approximates but does not match.
