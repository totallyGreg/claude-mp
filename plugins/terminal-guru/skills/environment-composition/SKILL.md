---
name: environment-composition
description: This skill should be used when the user asks to "compose tools", "automate this workflow", "make this repeatable", "what patterns do you see", "pipe through fzf", "what tools am I using", "configure sesh.toml", "create a dev environment", "build a session template", "set up sesh config", "clean up worktrees", "resume my session", "should this be a function or a task", or needs help composing workflows from existing CLI tools. Also trigger on fzf composition, workflow discovery, pattern graduation, tool landscape, or sesh wildcards. Do NOT use for tmux display or keybindings (use terminal-emulation). Do NOT use for worktree lifecycle (use chronicle). Do NOT use for signals or logging (use signals-monitoring). Do NOT use for mise config or tasks (use mise-tooling).
metadata:
  version: "2.0.0"
---

# Environment Composition

## Overview

Compose workflows and development environments by combining existing CLI tools. This skill is the **composition engine** — pull it in when the goal is to BUILD something from known tools, not just diagnose or configure a single tool.

The core principle: **compose existing tools before creating new ones**. Discover what the user has (brew, XDG configs, history), then compose from that inventory. Follow the Pattern Graduation Pipeline to promote ad-hoc commands into reusable automation at the right level.

Sesh + claude CLI + worktrees are one common composition target, but any combination of installed tools is in scope. fzf is the universal composition glue — it turns any list into an interactive workflow.

## When to Use This Skill

- Composing CLI tools into workflows (fzf pipelines, tool chains, automation)
- Discovering the user's tool landscape and usage patterns (`/workflow-discover`)
- Graduating patterns: ad-hoc commands → zsh functions → mise tasks
- Building multi-tool development environments (sesh + claude + worktrees)
- Writing or modifying `sesh.toml` configurations
- Setting up paired sesh + claude CLI sessions
- Graceful teardown and decay detection for environments
- fzf composition patterns (preview, multi-select, keybindings)

## Core Capabilities

### 1. Tool Composition Philosophy

Compose from the user's existing tool landscape. Discover what's installed (brew), what's configured (XDG), and what's frequently used (history) before suggesting compositions. Prefer the Unix pattern — small tools piped together — but recognize when multi-tasking tools (mise, sesh) absorb pipeline complexity.

See `references/composition_philosophy.md` for the full philosophy, Pattern Graduation Pipeline, and composition heuristics.

### 2. fzf Composition Patterns

fzf is the universal composition glue: `source | fzf [--preview] | action`. Master the pattern for git branches, brew packages, mise tasks, file operations, and process management. Know when to use alternatives (tv for file search, gum for confirmations).

See `references/fzf_composition.md` for the complete pattern library, power features, and comparison with tv and gum.

### 3. Workflow Discovery

Scan multiple signal sources — command history, zoxide frecency, homebrew inventory, XDG configs, git log — to build a picture of how the user works. Surface patterns ripe for graduation and tool preferences.

See `references/workflow_discovery.md` for signal sources, output format, and profile integration. The discovery script lives at `scripts/workflow-discover.sh`.

### 4. Sesh Config System

Sesh's `sesh.toml` is one of several composition targets. It supports named sessions, wildcard patterns, reusable windows, startup commands, config imports, and picker integrations.

See `references/sesh_config_guide.md` for the complete config reference.

### 5. Claude CLI Integration

The `claude --continue` flag resumes context scoped to the current directory — pairs naturally with sesh sessions and worktrees.

See `references/claude_cli_composition.md` for session management, project config, and worktree integration.

### 6. Environment Workflows

Four lifecycle categories: setup/resume, worktree composition, teardown, and decay detection.

See `references/workflow_patterns.md` for patterns, commands, and diagnostic checklists.

## Common Use Cases

### "I keep running the same commands, can this be simpler?"

1. Run `/workflow-discover` to identify the repeated pattern
2. Apply the Pattern Graduation Pipeline (see `composition_philosophy.md`)
3. If the pattern needs shell context → create a zsh function
4. If the pattern is project-scoped or team-shared → create a mise task
5. If the pattern involves interactive selection → wrap with fzf

### "Pipe something through fzf"

1. Identify the source (what list to filter)
2. Add preview (`--preview 'command {}'`) for context
3. Define the action (what to do with the selection)
4. See `fzf_composition.md` for recipes and power features

### "What tools am I using?"

1. Run `/workflow-discover` for the full landscape
2. Review brew inventory, XDG configs, and history frequency
3. Identify tools that are installed but unconfigured (or configured but unused)
4. Suggest compositions that leverage the existing landscape

### "Set up a project environment"

1. Suggest a `[[session]]` or `[[wildcard]]` in `sesh.toml` with startup_command and windows
2. `sesh connect <project>` to create the session
3. `claude --continue` to resume AI context

### "Clean up old environments"

1. Check for stale sessions: `tmux list-sessions`
2. Check for orphaned worktrees: `git worktree list`
3. Review unused sesh configs: `sesh list -c`
4. See `workflow_patterns.md` for the full decay detection checklist

## Resources

### references/
- **`composition_philosophy.md`** — Unix composition principle, Pattern Graduation Pipeline, tool landscape discovery, fzf as composition glue, composition heuristics
- **`fzf_composition.md`** — fzf patterns, preview, multi-select, keybindings, recipes for git/brew/mise/files/processes, comparison with tv and gum
- **`workflow_discovery.md`** — Signal sources (history, zoxide, brew, XDG, git), output format, profile integration, version auto-detection
- **`sesh_config_guide.md`** — Comprehensive sesh v2.24+ reference: config system, subcommands, picker integrations, naming strategy
- **`claude_cli_composition.md`** — Claude CLI features for environment composition: session management, project config, worktree integration
- **`workflow_patterns.md`** — Environment lifecycle patterns: setup, worktree composition, teardown, decay detection

### scripts/
- **`workflow-discover.sh`** — Multi-source workflow discovery script (referenced by `/workflow-discover` command)

### Cross-references
- **terminal-emulation** `tmux_session_management.md` — General tmux keybindings, pane logging, session persistence
- **chronicle** `worktrees-experiments.md` — Git worktree lifecycle patterns
- **zsh-dev** `zsh_function_patterns.md` — Function templates for graduating patterns
- **mise-tooling** `mise_task_patterns.md` — Task creation for graduating patterns to mise
