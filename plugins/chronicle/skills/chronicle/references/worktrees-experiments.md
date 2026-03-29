# Worktrees and Parallel Experiments

Git worktrees allow multiple working trees to exist simultaneously from the same repository — each in a different directory, each on a different branch, sharing the same object store. No cloning, no duplication of history.

This makes worktrees the natural primitive for parallel experimentation: multiple approaches running simultaneously, evaluated, and the best integrated back.

## Worktree Basics

```bash
# Add a worktree on a new branch
git worktree add ../my-experiment experiment/approach-a-$(date +%Y%m%d)

# Add a worktree on an existing branch
git worktree add ../hotfix-work release/1.0

# List all worktrees
git worktree list

# Remove a worktree (deletes the directory link, not the branch)
git worktree remove ../my-experiment

# Prune stale worktree references (after manually deleting a directory)
git worktree prune
```

Each worktree shares `.git/` — commits, branches, tags, stashes, and rerere cache are all shared. A commit made in one worktree is immediately visible to others.

**Constraint**: a branch can only be checked out in one worktree at a time. Git enforces this — attempting to check out an already-active branch in a second worktree will fail.

## Multi-Agent Experiment Pattern

The canonical use case: run N agents in parallel worktrees exploring different approaches to the same problem, then integrate the best result.

### Setup

```bash
EXPERIMENT_DATE=$(date +%Y%m%d)
BASE_DIR=$(git rev-parse --show-toplevel)
PARENT_DIR=$(dirname "$BASE_DIR")

# Create experiment branches and worktrees
git worktree add "$PARENT_DIR/experiment-a" "experiment/approach-a-$EXPERIMENT_DATE"
git worktree add "$PARENT_DIR/experiment-b" "experiment/approach-b-$EXPERIMENT_DATE"
git worktree add "$PARENT_DIR/experiment-c" "experiment/approach-c-$EXPERIMENT_DATE"

echo "Worktrees ready:"
git worktree list
```

Each agent receives its worktree path and operates independently. Agents can read each other's worktrees (they're just directories) but cannot check out the same branch.

### During Experiments

Each agent works normally within its worktree:

```bash
# Agent A, working in experiment-a/
git add specific-file.py
git commit -m "experiment(approach-a): try vector embedding approach"
```

Agents should commit frequently — partial results are recoverable, and the commit history becomes part of the evaluation record.

### Evaluation

After agents complete, evaluate results from the main repository:

```bash
# Compare experiment results against main
git diff main..experiment/approach-a-20250401 -- src/
git diff main..experiment/approach-b-20250401 -- src/

# Review each experiment's commit history
git log --oneline main..experiment/approach-a-20250401
git log --oneline main..experiment/approach-b-20250401

# See file-level summary of what changed
git diff --stat main..experiment/approach-a-20250401
```

Evaluation criteria are domain-specific but typically include: correctness, performance, code clarity, test coverage, and alignment with existing patterns.

### Integration Strategies

**Scenario 1: One clear winner — merge the branch**

```bash
git switch main
git merge --no-ff experiment/approach-b-20250401 \
  -m "feat(search): adopt vector similarity approach from experiment-b

Experiment-b outperformed approach-a on recall (0.94 vs 0.87) with
comparable latency. Approach-c was eliminated due to dependency conflict.

Closes #123."
```

**Scenario 2: Best-of-multiple — cherry-pick across experiments**

```bash
# Take the indexing logic from experiment-a, the query handler from experiment-b
git switch main
git cherry-pick <sha-from-a>    # indexing commit
git cherry-pick <sha-from-b>    # query handler commit
git cherry-pick <sha-from-a>    # test suite commit
```

Document the multi-source integration clearly in the commit message or a follow-up commit.

**Scenario 3: No conflicts between experiments — octopus merge**

```bash
git switch main
git merge experiment/approach-a-20250401 experiment/approach-b-20250401
# Git uses octopus strategy automatically for 2+ branches
```

Octopus merge fails if any conflict exists between the branches. Fall back to sequential merges if conflicts occur.

**Scenario 4: Partial adoption — squash and curate**

When an experiment has useful pieces buried in noisy WIP commits:

```bash
# In a curation branch
git switch -c integrate/from-experiments main
git merge --squash experiment/approach-a-20250401
git add -p    # interactively stage only the parts worth keeping
git commit -m "feat(search): integrate vector indexing from experiment-a"
```

### Cleanup

After integration, clean up worktrees and branches:

```bash
# Remove worktree directories
git worktree remove ../experiment-a
git worktree remove ../experiment-b
git worktree remove ../experiment-c

# Delete experiment branches
git branch -d experiment/approach-a-20250401
git branch -d experiment/approach-b-20250401
git branch -d experiment/approach-c-20250401

# Prune any stale references
git worktree prune
git remote prune origin
```

Keep experiment branches that were integrated (they become historical record). Delete branches representing discarded approaches unless they contain findings worth preserving.

## Worktrees for Parallel Development (Non-Experiment)

Worktrees are useful beyond experiments for any parallel workload:

**Reviewing a PR while continuing feature work:**
```bash
git worktree add ../pr-review origin/feature/colleague-branch
# Review in ../pr-review, continue working in main directory
```

**Hotfix while mid-feature:**
```bash
git worktree add ../hotfix release/2.1
# Fix the bug in ../hotfix, stay in feature branch in main directory
```

**Running different versions simultaneously:**
```bash
git worktree add ../stable v2.0.0
# Run stable in ../stable for comparison while developing in main
```

## Worktree Conventions

Establish naming and location conventions before using worktrees across a team or in automated pipelines:

```
Parent directory layout:
my-repo/           # main worktree (main branch)
my-repo-pr-456/    # PR review worktree
my-repo-exp-a/     # experiment worktree A
my-repo-exp-b/     # experiment worktree B

Branch naming convention:
experiment/<descriptive-name>-<YYYYMMDD>
wip/<feature>-worktree
pr-review/<pr-number>
```

Keep worktree directories adjacent to the main repository directory — this makes `git worktree list` output readable and makes cleanup systematic.

## Agent Coordination Patterns

When multiple agents share worktrees, coordinate through:

**Branch-per-agent**: each agent has its own branch, no coordination needed within the branch. Coordination happens at merge time.

**Commit signaling**: agents write structured commit messages that other agents can parse:
```
experiment(approach-a): CHECKPOINT — indexing complete, awaiting eval
experiment(approach-a): DONE — score 0.94 recall, 45ms p99
```

**Shared notes ref**: git has a rarely-used `refs/notes/` namespace for attaching metadata to commits without rewriting them:
```bash
git notes add -m "eval: recall=0.94, latency_p99=45ms" <sha>
git notes show <sha>
git log --show-notes
```

Notes survive cherry-picks and are visible to all agents sharing the repository.

## Limitations and Gotchas

- **One branch per worktree**: cannot check out the same branch in two worktrees simultaneously
- **Submodules**: worktrees and submodules interact poorly — avoid combining them
- **Hooks**: `.git/hooks/` is shared — hooks run in all worktrees, which may be unexpected
- **Stash is global**: `git stash` stashes against the repository, not the worktree — stashes from one worktree are visible in all
- **IDE confusion**: some IDEs discover only the first worktree; configure explicitly if needed
