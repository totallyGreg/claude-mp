---
name: environment-composition
description: This skill should be used when the user asks to "compose tools", "automate this workflow", "make this repeatable", "what patterns do you see", "pipe through fzf", "what tools am I using", "configure sesh.toml", "create a dev environment", "build a session template", "set up sesh config", "clean up worktrees", "resume my session", "should this be a function or a task", "make a droplet", "drag and drop script", "folder action", "run a script when files land in a folder", "Finder Quick Action", "right-click menu item", or needs help composing workflows from existing CLI tools. Also trigger on fzf composition, workflow discovery, pattern graduation, tool landscape, sesh wildcards, or wrapping a script (even one calling Apple's `fm`) in a Finder droplet or Folder Action. Do NOT use for tmux display or keybindings (use terminal-emulation). Do NOT use for worktree lifecycle (use chronicle). Do NOT use for signals or logging (use signals-monitoring). Do NOT use for mise config or tasks (use mise-tooling).
metadata:
  version: "2.3.0"
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
- Wrapping a script in a macOS Finder surface: droplet (with progress window and a right-click Quick Action toggle), Folder Action

## Core Capabilities

### 1. Tool Composition Philosophy

Compose from the user's existing tool landscape. Discover what's installed (brew), what's configured (XDG), and what's frequently used (history) before suggesting compositions. Prefer the Unix pattern — small tools piped together — but recognize when multi-tasking tools (mise, sesh) absorb pipeline complexity.

See `references/composition_philosophy.md` for the full philosophy, Pattern Graduation Pipeline, and composition heuristics.

### 2. fzf Composition Patterns

fzf is the universal composition glue: `source | fzf [--preview] | action`. Master the pattern for git branches, brew packages, mise tasks, file operations, and process management. Use fzf, not tv, for pickers; gum for confirmations.

See `references/fzf_composition.md` for the complete pattern library, power features, and comparison with tv and gum. New fzf actions by version: `tui-experience/references/fzf_features.md`.

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

### 7. macOS Finder Surfaces

Put a script behind Finder: a **droplet** (drop files on an app icon, or right-click → Quick Actions) or a **Folder Action** (files added to a folder run the script). Write and test the core script first — file paths as arguments, absolute tool paths, its own `PATH`/`SSH_AUTH_SOCK`, no TTY, skip files it doesn't handle — then generate the wrapper:

```bash
S=${CLAUDE_PLUGIN_ROOT}/skills/environment-composition/scripts/finder_surface.sh
$S droplet ~/Applications/"Receipt to JSON.app" ~/bin/receipt2json   # --link, --self-reporting
$S folder-action ~/Receipts ~/bin/receipt2json      # $S detach ~/Receipts to remove
```

A generated droplet embeds the script (re-run to update), shows a progress window with Stop, reports by exit status (0 done, 3 already reported, other = failure dialog), and its double-click settings window toggles the Finder right-click Quick Action. Scripts get a real progress bar by writing `$DROPLET_PROGRESS_FILE`.

Scripts that call Apple's on-device model (`/usr/bin/fm`, macOS 27) wrap like any other command — the receipt image → JSON example is worked end to end.

See `references/macos_finder_surfaces.md` for the script contract, exit contract and progress protocol, choosing a surface (droplet, Folder Action, Quick Action, launchd), gotchas (output re-triggering the folder, partial downloads, privacy prompts), and hurdles from a real build (Finder's environment, bash 3.2 traps, GUI-free testing, SSH over one connection). Check those before writing the script.

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

### "Make a drag-and-drop script" / "Process every file dropped in a folder"

1. Write the core script; run it by hand on real files under `env -i PATH=/usr/bin:/bin:/usr/sbin:/sbin`
2. On-demand batches → `finder_surface.sh droplet`; hands-off inbox → `finder_surface.sh folder-action`
3. Test the script first with a stub `osascript` on `PATH` (no pop-ups); then a droplet with `open -a Name.app file`; a folder action by copying a file in
4. See `macos_finder_surfaces.md` for gotchas

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
- **`unix_composition_primer.md`** — Foundation: piping, filtering, transforming + tool preference matrix (rg/grep, fd/find, sd/sed, jq/yq/xsv, fzf/xargs/tee). Load for "how do I combine X and Y" questions.
- **`composition_philosophy.md`** — Unix composition principle, Pattern Graduation Pipeline, tool landscape discovery, fzf as composition glue, composition heuristics
- **`fzf_composition.md`** — fzf patterns, preview, multi-select, keybindings, recipes for git/brew/mise/files/processes, comparison with tv and gum
- **`workflow_discovery.md`** — Signal sources (history, zoxide, brew, XDG, git), output format, profile integration, version auto-detection
- **`sesh_config_guide.md`** — Comprehensive sesh v2.24+ reference: config system, subcommands, picker integrations, naming strategy
- **`claude_cli_composition.md`** — Claude CLI features for environment composition: session management, project config, worktree integration
- **`workflow_patterns.md`** — Environment lifecycle patterns: setup, worktree composition, teardown, decay detection
- **`macos_finder_surfaces.md`** — Script → Finder droplet / Folder Action / Quick Action / launchd; core-script contract, generator usage, gotchas, `fm` receipt example

### scripts/
- **`workflow-discover.sh`** — Multi-source workflow discovery script (referenced by `/workflow-discover` command)
- **`finder_surface.sh`** — Generate a droplet, attach or detach a Folder Action for any executable

### Cross-references
- **tmux-dev** `tmux_session_management.md` — tmux session management, keybindings, pane logging, persistence
- **chronicle** `worktrees-experiments.md` — Git worktree lifecycle patterns
- **zsh-dev** `zsh_function_patterns.md` — Function templates for graduating patterns
- **mise-tooling** `mise_task_patterns.md` — Task creation for graduating patterns to mise
- **local-inference** (local-inference plugin) `apple-fm.md` — Apple `fm` CLI: flags, schemas, OCR vs vision, failure modes
