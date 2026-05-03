---
last_verified: 2026-05-03
sources:
  - type: web
    url: "https://mise.jdx.dev/cli/"
    description: "Official mise CLI documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/cli/"]
    description: "mise documentation source for CLI commands"
---

# Mise CLI Reference

## Task Management

| Command | Alias | Description |
|---------|-------|-------------|
| `mise run <TASK> [ARGS...]` | `mise r <TASK>` / `mise <TASK>` | Run a task with optional args |
| `mise tasks ls` | `mise tasks` / `mise task list` | List all discovered tasks |
| `mise tasks info <TASK>` | — | Show task metadata (`--json` for machine output) |
| `mise tasks edit <TASK>` | — | Open task source file in `$EDITOR` |
| `mise tasks add` | — | Add a new task definition interactively |
| `mise tasks deps <TASK>` | — | Print dependency graph (DOT format) |
| `mise tasks validate` | — | Validate task definitions against schema |

## Run Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--jobs` | `-j` | Max concurrent workers (default: 4) |
| `--continue-on-error` | `-c` | Continue dependents even if a dep fails |
| `--dry-run` | `-n` | Print execution plan without running |
| `--force` | `-f` | Force re-execution, bypass cache |
| `--fresh-env` | — | Bypass cached env state |
| `--no-cache` | — | Skip all caching for this run |
| `--skip-deps` | — | Don't run dependency tasks |
| `--skip-tools` | — | Don't auto-install tools before running |
| `--timeout` | — | Set max execution time per task |
| `--timings` | — | Show timing for each task |
| `--yes` | `-y` | Auto-confirm interactive prompts |

## Task Listing Flags

| Flag | Description |
|------|-------------|
| `--all` | Show global, system, and project tasks |
| `--hidden` | Include normally hidden tasks |
| `--json` | JSON output |
| `--extended` | Extra columns (aliases, source file) |
| `--common` | Only tasks common across subdirectories |

## Parallel Execution

```bash
mise run build ::: test ::: lint    # run 3 tasks in parallel
mise run --jobs 8 build test lint   # parallel with job limit
mise run --timings build test       # show per-task timing
```

## Environment & Configuration

| Command | Description |
|---------|-------------|
| `mise env` | Show resolved environment variables |
| `mise cfg` | Show loaded config files and precedence |
| `mise set KEY=value` | Set an environment variable |
| `mise trust [FILE]` | Trust a config file for execution |
| `mise doctor` | Comprehensive health check |

## Tool Management

| Command | Description |
|---------|-------------|
| `mise install` | Install all configured tools |
| `mise install <TOOL>@<VERSION>` | Install a specific tool version |
| `mise ls` | List installed tools |
| `mise use <TOOL>@<VERSION>` | Pin a tool version in config |
| `mise outdated` | Check for outdated tools |
| `mise prune` | Remove unused tool versions |

## Watch Mode

```bash
mise watch <TASK> -w <PATH>         # watch paths and re-run on change
mise watch <TASK> --restart         # restart long-running processes
mise watch build -w src -w Cargo.toml
```

Requires `watchexec` utility.
