# Merge Strategies

Choosing the right integration strategy determines whether history is readable, whether reverts are safe, and whether the team can bisect regressions effectively. No single strategy is universally correct — each makes tradeoffs between linearity, auditability, and flexibility.

## The Core Three

### Merge Commit (`git merge`)

Creates a new commit with two parents, preserving the full history of both branches.

```
before:  main: A──B──C
              \
         feature: D──E──F

after:   main: A──B──C──G
              \        /
         feature: D──E──F
```

**Commit G** is the merge commit. It records that these two lines of work were integrated at this point.

**Use when:**
- Integrating a shared or reviewed branch (PR merge)
- The branch's history is coherent and worth preserving
- Safe revert is important (reverting G removes the entire feature cleanly)
- The branch represents a discrete unit of work that should be visible as such in history

**Command:**
```bash
git switch main
git merge --no-ff feature/my-feature    # --no-ff forces a merge commit even if fast-forward is possible
```

**`--no-ff` matters**: without it, git fast-forwards when possible, producing no merge commit and losing the record that a branch existed.

---

### Rebase (`git rebase`)

Replays commits from the feature branch onto the tip of the target branch, producing a linear history.

```
before:  main: A──B──C
              \
         feature: D──E──F

after:   main: A──B──C──D'──E'──F'
```

D', E', F' are new commits — same changes, different SHAs, rebased onto C.

**Use when:**
- Integrating a local, unshared branch before pushing
- Cleaning up history before opening a PR
- The branch is logically a continuation of main (not a parallel track)

**Command:**
```bash
git switch feature/my-feature
git rebase main                   # replay feature commits onto main
git switch main
git merge --ff-only feature/my-feature   # fast-forward only (safe after rebase)
```

**Never rebase shared history.** Once commits have been pushed and others have based work on them, rebasing rewrites their SHAs and creates divergence that requires force-push to resolve — breaking everyone else's local state.

**Interactive rebase for cleanup:**
```bash
git rebase -i main    # clean up commits before opening a PR
```

---

### Squash Merge (`git merge --squash`)

Collapses all commits from the feature branch into a single commit on the target branch.

```
before:  main: A──B──C
              \
         feature: D──E──F──G──H (noisy WIP commits)

after:   main: A──B──C──S    (S = squashed: D+E+F+G+H as one commit)
```

**Use when:**
- The feature branch has messy WIP commits that don't add value to history
- The entire feature is small enough to be one coherent change
- The branch will be deleted after merge (no history to preserve)

**Command:**
```bash
git switch main
git merge --squash feature/my-feature
git commit -m "feat(payments): add Stripe checkout integration"
```

**Caution:** Squash merges make reverting easy but lose individual authorship and granularity. If the squashed feature is large, bisecting within it becomes impossible.

---

## Decision Table

| Situation | Strategy |
|-----------|----------|
| Merging a reviewed PR | `merge --no-ff` |
| Integrating local work before push | `rebase` |
| Noisy branch, clean feature | `merge --squash` |
| Branch with meaningful commit history | `merge --no-ff` |
| Keeping history linear on main | `rebase` then `ff-only merge` |
| Feature that must be revertable as a unit | `merge --no-ff` |
| Large refactor with many atomic commits | `merge --no-ff` |

---

## Advanced Strategies

### Cherry-Pick

Apply a specific commit from one branch to another without merging the entire branch.

```bash
git cherry-pick <sha>                    # apply one commit
git cherry-pick <sha1>..<sha2>           # apply a range (exclusive..inclusive)
git cherry-pick <sha> --no-commit        # stage the changes without committing
```

**Use when:**
- Backporting a fix to a release branch
- Pulling one commit from an experiment that isn't ready to merge fully
- Recovering a dropped commit after a bad rebase

**Caution:** Cherry-picked commits have different SHAs than their originals. If both branches eventually merge, git will try to apply the change twice — usually producing a conflict. Use cherry-pick for point-to-point transfers, not as a substitute for proper integration.

---

### Rerere (Reuse Recorded Resolution)

Git can memorize how you resolved a conflict and reapply that resolution automatically next time the same conflict appears. Invaluable for long-lived branches or repeated rebases.

```bash
git config rerere.enabled true           # enable globally
git config rerere.autoUpdate true        # auto-stage rerere-resolved files
```

Once enabled, git records conflict resolutions in `.git/rr-cache/`. The next time the same conflict occurs (e.g., rebasing the same branch after a colleague merged), it resolves automatically.

---

### Octopus Merge

Merges more than two branches simultaneously into one commit with multiple parents.

```bash
git merge feature-a feature-b feature-c
```

Git uses the octopus strategy automatically for multi-branch merges. It works only when there are no conflicts between the incoming branches.

**Use when:**
- Integrating multiple independent parallel workstreams simultaneously
- Merging the results of parallel agent experiments (see `references/worktrees-experiments.md`)
- The branches don't conflict (octopus refuses to run if they do)

**When not to use:** Any conflict between branches — fall back to sequential merges, resolving conflicts one branch at a time.

---

### `git merge -X` Strategy Options

For automated or scripted merges, the `-X` flag passes options to the merge strategy:

```bash
git merge -X ours feature-branch        # on conflict, prefer our version
git merge -X theirs feature-branch      # on conflict, prefer their version
git merge -X patience feature-branch    # slower but better diff for complex changes
```

`-X ours` / `-X theirs` are blunt instruments — they resolve all conflicts in one direction without inspection. Use only in scripted pipelines where conflicts are expected and a policy decision has been made.

---

## Conflict Resolution

When a merge conflict occurs, git marks the file:

```
<<<<<<< HEAD
current version of the line
=======
incoming version of the line
>>>>>>> feature/my-feature
```

Resolve by editing to the correct state, then:

```bash
git add path/to/resolved/file
git merge --continue                     # complete the merge
# or
git commit                               # if not using --continue
```

### Abort and start over

```bash
git merge --abort         # abandon the merge, restore pre-merge state
git rebase --abort        # abandon the rebase, restore pre-rebase state
```

### Three-way diff tools

```bash
git mergetool             # opens configured merge tool (vimdiff, meld, etc.)
```

Configure a tool:
```bash
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
```

### Understanding the conflict

Before resolving, understand *why* both changes exist:

```bash
git log --merge           # show commits that caused the conflict
git diff --merge-base HEAD feature/branch   # see what diverged
```

Resolving based on the diff alone without understanding intent often produces subtle bugs.

---

## History Inspection After Merge

```bash
git log --merges                         # show only merge commits
git log --no-merges                      # show only non-merge commits
git log --first-parent main              # see main's history without branch internals
git show <merge-sha>                     # inspect a specific merge commit
git diff <merge-sha>^1 <merge-sha>^2    # diff between the two parents of a merge
```

`--first-parent` is particularly useful: it shows only the commits that landed directly on main (merge commits), hiding the branch noise, giving a clean release-level view of history.
