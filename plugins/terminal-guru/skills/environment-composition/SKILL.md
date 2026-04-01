---
name: environment-composition
description: This skill should be used when the user asks to "configure sesh.toml", "create a dev environment", "build a session template", "set up sesh config", "add a sesh wildcard", "configure startup command", "create workspace with sesh", "clean up worktrees", "resume my session", "debug environment decay", or needs help composing development environments from sesh, claude CLI, direnv, and git worktrees. Also trigger on mentions of sesh.toml, environment composition, session templates, sesh wildcards, or teardown patterns. Do NOT use for general tmux session management, display issues, or keybindings (use terminal-emulation instead). Do NOT use for worktree lifecycle management (use chronicle instead). Do NOT use for signal handling or system logging (use signals-monitoring instead).
metadata:
  version: "1.0.0"
---

# Environment Composition

## Overview

Compose development environments by combining sesh (tmux session manager), claude CLI, direnv, and git worktrees. Sesh's config system (`sesh.toml`) is the foundation layer — it already implements most of the composition pattern natively through session declarations, wildcard templates, reusable windows, and startup commands.

When suggesting compositions, use the Lens framework as a mental checklist: **Selection** (which project/directory/worktree), **Arrangement** (tmux windows, startup commands, claude session), **Purpose** (what task this environment serves), **Activation** (how to trigger it — sesh wildcard, picker, zoxide). Favor sesh-native solutions — output `sesh.toml` config snippets that users add to their own config.

## When to Use This Skill

- Composing multi-tool development environments (sesh + claude + direnv + worktrees)
- Writing or modifying `sesh.toml` configurations (sessions, wildcards, windows, startup commands)
- Setting up paired sesh + claude CLI sessions for a project
- Creating worktree-per-session isolation for parallel feature work
- Graceful teardown of environments (preserving state, cleaning up)
- Detecting environment decay (stale sessions, orphaned worktrees)
- Choosing and configuring sesh picker integrations (fzf, television, gum, built-in)

## Core Capabilities

### 1. Sesh Config System

Sesh's `sesh.toml` is the primary tool for defining and managing development environments. It supports named sessions, wildcard patterns for project categories, reusable window definitions, startup commands, config imports, and multiple picker integrations.

See `references/sesh_config_guide.md` for the complete config reference including all `sesh.toml` sections, subcommands, picker integrations, and naming strategies.

### 2. Claude CLI Integration

The `claude --continue` flag resumes the most recent conversation in the current directory — this naturally pairs with sesh's directory-based session creation. Combined with `--worktree --tmux` for native worktree+session creation, claude CLI integrates directly into the sesh workflow.

See `references/claude_cli_composition.md` for session management flags, project configuration (`CLAUDE.md`, `.claude/`, MCP), worktree integration, and direnv patterns.

### 3. Environment Workflows

Four workflow categories cover the full environment lifecycle:
- **Setup and Resume**: Pair sesh sessions with claude context via `--continue` or `startup_command`
- **Worktree Composition**: One sesh session per git worktree for isolated parallel work
- **Teardown**: Graceful shutdown preserving claude session state
- **Decay Detection**: Identify stale sessions, orphaned worktrees, outdated configs

See `references/workflow_patterns.md` for patterns, commands, and diagnostic checklists.

### 4. sesh.toml as Local State

Users' `sesh.toml` (at `~/.config/sesh/sesh.toml`) naturally serves as local state for environment composition. The agent suggests config snippets — `[[session]]`, `[[wildcard]]`, `startup_command` entries — that users add to their own config. No separate state file needed. Proven patterns can graduate to skill references.

## Common Use Cases

### "I want to set up a project environment"
1. Create or navigate to the project directory
2. Add a `[[session]]` or `[[wildcard]]` entry in `sesh.toml` with `startup_command` and `windows`
3. `sesh connect <project>` to create the session
4. `claude --continue` to resume AI context

### "I want parallel feature branches"
1. Create worktrees: `git worktree add ../project-feat feat-branch`
2. `sesh connect` to each worktree directory (auto-named by sesh)
3. Each session gets its own `claude --continue` context
4. Navigate between them with `sesh` picker or `sesh connect --root`

### "I want to clean up old environments"
1. Check for stale sessions: `tmux list-sessions`
2. Check for orphaned worktrees: `git worktree list` + branch verification
3. Review unused sesh configs: `sesh list -c` against actual directories
4. See `references/workflow_patterns.md` for the full decay detection checklist

### "I want to clone a repo and start working immediately"
1. `sesh clone git@github.com:org/repo.git` — clones and creates session
2. Wildcard configs in `sesh.toml` automatically apply startup commands and windows
3. `claude --continue` to start AI-assisted work in the new project

## Resources

### references/
- **`sesh_config_guide.md`** — Comprehensive sesh v2.24+ reference: config system, subcommands, picker integrations, naming strategy
- **`claude_cli_composition.md`** — Claude CLI features for environment composition: session management, project config, worktree integration, direnv patterns
- **`workflow_patterns.md`** — Environment lifecycle patterns: setup, worktree composition, teardown, decay detection

### Cross-references
- **terminal-emulation** `tmux_session_management.md` — General tmux keybindings, pane logging, session persistence
- **chronicle** `worktrees-experiments.md` — Git worktree lifecycle patterns (create, evaluate, cleanup)
