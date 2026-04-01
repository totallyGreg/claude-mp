# Environment Composition Workflow Patterns

## Overview

These patterns describe how sesh, tmux, git worktrees, and claude CLI compose into development environments. Each pattern is annotated with a Lens lifecycle label indicating maturity:

- **Crystallized** — Stable, proven pattern. Use with confidence.
- **Emerging** — Works but still evolving. Expect refinement.
- **Composed** — Assembled from other tools/patterns. Integration points may shift.

---

## Setup and Resume

### Basic Setup [Crystallized]

`sesh connect` creates or attaches a tmux session rooted at the project directory. `claude --continue` resumes AI context scoped to that directory.

```bash
# Create/attach session for a project
sesh connect my-project

# Resume claude context (directory-scoped)
claude --continue
```

### Auto-Launch Claude via startup_command [Emerging]

In `sesh.toml`, set `startup_command = "claude --continue"` on a session or wildcard. Because claude is interactive, this works best as the primary pane activity. For multi-pane workflows, launch claude manually after pane setup.

```toml
[[session]]
name = "my-project"
path = "~/projects/my-project"
startup_command = "claude --continue"
```

### Wildcard-Based Project Templates [Emerging]

Use `[[wildcard]]` patterns to auto-configure environments for entire project categories. Any directory matching the pattern gets the same session layout and startup behavior.

```toml
[[wildcard]]
pattern = "~/projects/*"
startup_command = "claude --continue"
windows = ["git", "server"]
```

### Config Imports for Work/Personal Split [Crystallized]

Use `import` to maintain separate environment configs without duplicating shared settings.

```toml
import = ["~/.config/sesh/work.toml"]
```

### Clone and Connect [Crystallized]

One-step clone and session creation. Combined with wildcard configs, the new repo automatically gets the right environment.

```bash
sesh clone git@github.com:org/repo.git
```

### Resume Pairing

Two layers of persistence work together on reconnection:

- **sesh** (tmux-resurrect/continuum) preserves the terminal layout — panes, windows, working directories.
- **claude --continue** (directory-scoped) preserves the AI context — conversation history, tool state, memory.

Together, both layers restore on reconnection. Neither requires the other, but combined they provide full environment continuity.

---

## Worktree Composition

### Native Claude Worktree + tmux [Composed]

`claude --worktree feat-name --tmux` creates a git worktree AND tmux session in one step. Good for ad-hoc parallel work when you don't need sesh's config system.

```bash
claude --worktree feat-name --tmux
```

### sesh + Manual Worktree [Emerging]

Create the worktree first, then `sesh connect` to the worktree directory. This gives you sesh's config system (windows, startup_command) applied to the worktree.

```bash
# Create worktree
git worktree add ../project-feat-name feat-name

# Connect sesh to the worktree directory
sesh connect project-feat-name
```

### Navigating Between Worktrees

```bash
# Jump to the git root / worktree root
sesh connect --root

# See all sessions including worktree-based ones
sesh list
```

### One Session Per Worktree Pattern

Each git worktree gets its own sesh session (auto-named by sesh's git-aware naming). Each session gets its own claude context via `--continue`. This enables parallel feature development with full isolation — separate terminal layouts, separate AI conversations, separate working trees.

> Cross-reference: See chronicle plugin's `worktrees-experiments.md` for worktree lifecycle patterns (creation, evaluation, branch management, cleanup).

---

## Teardown

### Graceful Shutdown Sequence

```
1. Exit claude CLI
   (session auto-persists to disk — no explicit save needed)

2. If using worktrees: merge/delete branch, then remove worktree
   git worktree remove <path>

3. Kill tmux session
   Close last pane, or: tmux kill-session -t <name>

4. sesh with detach-on-destroy off automatically switches
   to the next session instead of detaching
```

### What Is Preserved

- claude session history (on disk, resumable via `--continue` or `--resume`)
- sesh.toml configs (declarative, always available)
- zoxide frecency data (directory visit history)
- .envrc files (project-specific environment variables)

### What Is Lost

- tmux pane contents (unless pane logging was enabled)
- Unsaved file edits
- Running processes in panes

### Partial Teardown

Kill the tmux session but keep the worktree. Resume later:

```bash
# Later: reconnect to the worktree directory
sesh connect project-feat-name

# Resume AI context
claude --continue
```

---

## Decay Detection

Diagnostic checklist for identifying stale environments that should be cleaned up.

### Stale tmux Sessions

```bash
# List all sessions with creation time
tmux list-sessions -F '#{session_name} #{session_created} #{session_activity}'

# Kill sessions older than N days (manual review recommended)
```

### Orphaned Git Worktrees

```bash
# List worktrees with status
git worktree list --porcelain

# Look for worktrees whose branch no longer exists
git worktree list | while read path commit branch; do
  branch_name=${branch#\[}; branch_name=${branch_name%\]}
  git rev-parse --verify "$branch_name" >/dev/null 2>&1 || echo "ORPHANED: $path ($branch)"
done

# Prune worktrees with missing directories
git worktree prune
```

### Outdated .envrc Files

```bash
# Find .envrc files not modified in 30+ days
find ~/projects -name .envrc -mtime +30 -ls

# Check direnv status in current directory
direnv status
```

### Unused sesh Configs

Review `sesh list -c` against actual project directories. Remove `[[session]]` entries whose paths no longer exist.
