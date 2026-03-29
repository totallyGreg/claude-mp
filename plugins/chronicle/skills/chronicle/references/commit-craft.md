# Commit Craft

The commit is the fundamental unit of version control. A well-crafted commit is atomic, self-describing, and reversible. A poorly crafted one is a liability — difficult to bisect, impossible to revert cleanly, and confusing to future readers.

## The Atomic Commit

An atomic commit captures exactly one logical change. It compiles, passes tests, and leaves the codebase in a valid state. Atomicity enables:

- **Safe bisect**: `git bisect` can isolate a regression to a single commit only if each commit is independently valid
- **Clean revert**: reverting an atomic commit removes exactly the change it introduced, nothing more
- **Readable blame**: `git blame` is meaningful only when commits represent coherent ideas

### What atomic means in practice

**Atomic:**
- Add a single function and its tests
- Fix a single bug
- Rename a variable consistently across a file
- Update a dependency and adjust the call sites it affects

**Not atomic:**
- "Fix bug and clean up formatting" (two changes)
- "WIP" (incomplete change)
- "Various fixes" (unknown number of changes)
- A feature plus its documentation plus a refactor noticed along the way

When work spans multiple concerns, use `git add -p` (patch staging) to split it into separate commits:

```bash
git add -p path/to/file   # interactively stage hunks
```

## Commit Message Format

The 50/72 convention is widely understood and renders well in all git tooling:

```
<type>(<scope>): <imperative summary — 50 chars max>
<blank line>
<body — wrapped at 72 chars, explains WHY not WHAT>
<blank line>
<footer — issue refs, breaking changes, co-authors>
```

### The summary line

Write in imperative mood: the summary answers *"If applied, this commit will ___."*

```
# Good
feat(auth): add OAuth2 refresh token rotation
fix(parser): handle empty input without panicking
docs(readme): clarify installation on Apple Silicon

# Bad
fixed the bug
auth changes
WIP - do not merge
updated stuff
```

The type prefix communicates intent at a glance. Standard types:

| Type | When to use |
|------|-------------|
| `feat` | New capability, visible to users or callers |
| `fix` | Bug correction |
| `docs` | Documentation only |
| `refactor` | No behavior change, improved structure |
| `test` | Adding or fixing tests |
| `chore` | Build tooling, dependencies, configuration |
| `perf` | Performance improvement |
| `revert` | Reverting a prior commit |

### The body

The body explains *why* the change was made, not what was changed (the diff shows that). Write for a reader who has the diff open and is asking "but why?":

```
fix(cache): evict entries on memory pressure signal

The LRU cache held references to full response bodies, which
caused OOM kills under sustained traffic. Entries are now
evicted when the process receives SIGUSR1 or when heap usage
exceeds 80%.

Fixes #1423.
```

Omit the body for trivial changes where the summary is fully self-explanatory.

### The footer

```
Fixes #123          # closes the issue on merge (GitHub/GitLab)
Closes #456
Refs #789           # links without closing
BREAKING CHANGE: <description>   # triggers major version bump in semver tooling
Co-authored-by: Name <email>     # for pair/AI-assisted commits
```

## Amend Discipline

`git commit --amend` rewrites the most recent commit. Use it freely for local, unpushed commits to fix typos, add forgotten files, or improve the message.

**Never amend a commit that has been pushed to a shared branch.** This rewrites history others may have based work on.

For pushed commits that need correction, create a new fixup commit and squash during the next rebase:

```bash
git commit --fixup=<sha>          # creates a "fixup! <original message>" commit
git rebase -i --autosquash HEAD~5 # squashes fixups into their targets automatically
```

## Interactive Rebase for History Cleanup

Before merging a feature branch, clean up the commit history with interactive rebase:

```bash
git rebase -i main
```

This opens an editor with commits listed. Common operations:

| Command | Effect |
|---------|--------|
| `pick` | keep as-is |
| `reword` | keep, edit the message |
| `squash` | fold into the previous commit, combine messages |
| `fixup` | fold into the previous commit, discard this message |
| `drop` | remove this commit entirely |
| `edit` | pause here to amend |

A clean history before merge is considerate. A messy history after merge is permanent.

## Signing Commits

Signed commits provide cryptographic proof of authorship. Configure once:

```bash
git config --global user.signingkey <KEY_ID>
git config --global commit.gpgsign true   # sign all commits automatically
```

Verify: `git log --show-signature`

Signing is most valuable in open-source and regulated environments where commit provenance matters. For personal or private repos it is optional.

## Non-Code Content

The same atomic/descriptive principles apply to documents, configurations, and data files — arguably more so, because the audience for the history may not be technical.

**Document commits**: treat each meaningful revision as a commit. "Draft introduction" is better than "updates". "Restructure argument in section 3" is better than "edits".

```bash
# Useful for document work — see what actually changed in prose
git diff --word-diff
git diff --word-diff=color
```

**Configuration commits**: make one logical change per commit. "Enable rate limiting for /api/upload" is better than "config changes".

**CSV/JSON/YAML**: git diffs work well on structured text. Keep each commit coherent — changing a schema and updating all its data in the same commit is atomic; changing schema in one commit and data in another is a recipe for broken intermediate states.

## Stashing for Context Switches

When interruption strikes mid-change:

```bash
git stash push -m "WIP: refactoring auth middleware"  # always name your stash
git stash list                                          # see all stashes
git stash pop                                           # restore most recent
git stash apply stash@{2}                              # restore specific stash
```

Prefer named stashes over anonymous ones. Unnamed stashes accumulate and become confusing.

For longer interruptions or parallel work, a short-lived branch is cleaner than a stash:

```bash
git switch -c wip/auth-refactor    # save as a branch instead
git switch main                    # context switch cleanly
```

## Git Log Aliases Worth Having

```bash
git log --oneline --graph --decorate --all   # full history as ASCII graph
git log --follow -p -- path/to/file          # full history of a single file
git log --author="Name" --since="2 weeks"    # filtered history
git log --grep="feat" --oneline              # search commit messages
```

Add as aliases in `~/.gitconfig`:

```ini
[alias]
  lg = log --oneline --graph --decorate --all
  lf = log --follow -p --
```
