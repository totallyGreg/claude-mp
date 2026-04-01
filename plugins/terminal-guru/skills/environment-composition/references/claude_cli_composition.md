# Claude CLI: Environment Composition Reference

## Overview

This reference covers the subset of Claude CLI features that participate in composing development environments -- session management, project configuration, worktree isolation, and direnv integration. These are the building blocks that sesh, tmux, and direnv orchestrate into cohesive workspaces.

For the full CLI reference, run `claude --help`.

## Session Management

Claude sessions are directory-scoped. This is the architectural keystone of the sesh+claude pairing: sesh creates sessions at directory paths, and claude's session flags operate on the same directory context.

### Flags

| Flag | Short | Purpose |
|------|-------|---------|
| `--continue` | `-c` | Resume most recent conversation in current directory |
| `--resume [term]` | `-r` | Resume by session ID, or open interactive picker with optional search term |
| `--name <name>` | `-n` | Set display name for session |
| `--session-id <uuid>` | | Target specific session by UUID (programmatic use) |
| `--fork-session` | | Branch from an existing session without modifying the original |
| `--from-pr [value]` | | Resume session linked to a PR by number or URL |

### `--continue` (Primary Pairing with sesh)

The most important flag for environment composition. Resumes the most recent conversation scoped to the current working directory.

```bash
# sesh creates a session at ~/Projects/my-app
# tmux pane opens in ~/Projects/my-app
# claude picks up right where it left off
claude --continue
```

Directory-scoped behavior means each project directory maintains its own conversation history. When sesh switches you to a project directory, `--continue` finds the right session automatically.

### `--resume` (Cross-Project Discovery)

Use when `--continue` doesn't find the right session, or when you need to discover sessions across projects.

```bash
# Interactive picker -- browse all sessions
claude --resume

# Search by term
claude --resume "auth refactor"

# Resume specific session by ID
claude --session-id abc123-def456
```

### `--fork-session` (Exploratory Work)

Create a new session branching from an existing one. Useful for exploratory work without polluting the original session's context.

```bash
# Fork from the most recent session in this directory
claude --continue --fork-session

# Fork from a specific session
claude --resume abc123 --fork-session
```

### `--name` (Session Identification)

Set a human-readable name. Pairs with sesh session naming for consistent identification across tools.

```bash
claude --name "auth-feature-exploration"
```

**Note:** There is no `claude sessions` subcommand. Session discovery uses `--resume` with the interactive picker.

## Project Configuration

These configuration files define the "software environment" for claude within a project. They are loaded automatically based on directory context.

### CLAUDE.md

Project instructions loaded automatically when claude starts in a directory. Defines conventions, workflow rules, and project-specific context.

```
project-root/
  CLAUDE.md                    # Project-level instructions
  .claude/CLAUDE.md            # Alternative location
  src/
    CLAUDE.md                  # Directory-scoped instructions (additive)
```

In the context of environment composition, `CLAUDE.md` is one of three files that together define the full project environment (alongside `.envrc` and `.mcp.json`).

### .claude/ Directory

Project-level settings, permissions, and tool configuration.

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Shared permission configuration (committed to repo) |
| `.claude/settings.local.json` | Local permission overrides (gitignored) |
| `.claude/CLAUDE.md` | Alternative location for project instructions |

### .mcp.json (MCP Server Configuration)

Project-specific MCP tool servers. Relevant to environment composition because different projects may need different tools -- a data project might configure BigQuery MCP, while a web project configures Playwright.

```json
{
  "mcpServers": {
    "my-tools": {
      "command": "npx",
      "args": ["my-mcp-server"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

MCP servers defined in `.mcp.json` are loaded when claude starts in that directory. Environment variables referenced in the config (like `${API_KEY}`) are resolved from the shell environment -- which is where direnv comes in.

## Worktree Integration

Worktrees provide code isolation for parallel feature work. Claude can create and manage worktrees directly.

### Flags

| Flag | Short | Purpose |
|------|-------|---------|
| `--worktree [name]` | `-w` | Create a new git worktree for the session |
| `--tmux` | | Create a tmux session for the worktree (requires `--worktree`) |

### Combined Usage

```bash
# Create worktree + tmux session in one step
claude --worktree feat-auth --tmux

# Uses iTerm2 native panes when available
# Use --tmux=classic for traditional tmux
claude --worktree feat-auth --tmux=classic
```

### Interaction with sesh and --continue

Worktree directories are real directories on disk, so `--continue` should work with them. However, this is an edge case worth testing with representative sesh+worktree setups. Use `--resume` as a fallback if directory-scoping proves unreliable in worktree contexts.

**Cross-reference:** See the chronicle plugin's `worktrees-experiments.md` for worktree lifecycle patterns (create, evaluate, cleanup).

## direnv Patterns

direnv is the environment variable layer of the composition stack. It ensures project-specific variables are available to all tools in the session.

### How Variables Flow

```
.envrc (project root)
  -> direnv hook in shell rc (zsh/bash)
    -> tmux inherits shell environment
      -> new tmux panes source .envrc via direnv hook
        -> claude CLI inherits pane environment
```

When sesh creates a session at a project path, direnv loads the `.envrc` automatically. Every pane in that tmux session inherits the project's environment.

### Environment Variables Claude Recognizes

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API authentication |
| `CLAUDE_CODE_*` | Claude Code configuration variables |
| Project-specific vars | Available to MCP servers, scripts, and tools |

### Example .envrc

```bash
# Project-specific environment
export PROJECT_NAME="my-app"
export API_KEY="$(op read 'op://Dev/my-app/api-key')"  # 1Password CLI

# Claude-specific
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"

# Tool-specific (used by MCP servers in .mcp.json)
export DATABASE_URL="postgresql://localhost:5432/myapp_dev"
```

### tmux update-environment

Ensure specific environment variables propagate to new panes by configuring tmux:

```bash
# In tmux.conf
set-option -g update-environment "ANTHROPIC_API_KEY PROJECT_NAME API_KEY DATABASE_URL"
```

Without this, new panes may inherit stale values from the tmux server's original environment rather than the current direnv-loaded values.

### The Full Composition

The three files that together define a composed development environment:

| File | Layer | What It Provides |
|------|-------|------------------|
| `.envrc` | Shell environment | API keys, tool config, project vars |
| `CLAUDE.md` | Claude context | Instructions, conventions, workflow rules |
| `.mcp.json` | Tool servers | Project-specific MCP integrations |

When sesh creates a session at a project directory:
1. direnv loads `.envrc` into the shell environment
2. claude loads `CLAUDE.md` for project context
3. claude loads `.mcp.json` for available tools
4. `--continue` resumes the conversation scoped to that directory

This is the complete "environment" for a composed development session.

## Resources

- `claude --help` -- Full CLI reference
- `claude config` -- Configuration management
- `man direnv` -- direnv documentation
- `man direnv-stdlib` -- direnv standard library functions
