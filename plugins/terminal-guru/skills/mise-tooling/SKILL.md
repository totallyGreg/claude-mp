---
name: mise-tooling
description: This skill should be used when the user asks to "configure mise.toml", "create a mise task", "set up tool versions", "manage environments with mise", "debug mise config", "task_config includes", "mise task DRY", "mise profiles", "mise env not loading", "create mise run command", or needs help with mise (jdx/mise) for tool versioning, environment variables, or task automation. Also trigger on mentions of mise.toml, .miserc.toml, mise run, mise env, mise tasks, mise profiles, task_config, or exec() in env. Do NOT use for shell configuration or function generation (use zsh-dev instead). Do NOT use for sesh/tmux session management (use environment-composition instead). Do NOT use for signal handling or logging (use signals-monitoring instead). Mise + sesh integration questions should route here for the mise side and environment-composition for the sesh side.
metadata:
  version: "2.0.0"
---

# Mise Tooling

## Overview

mise (jdx/mise) is a polyglot dev environment manager that replaces asdf + direnv + make. It manages tool versions, per-project environment variables, and tasks in a single config file. This skill covers configuration patterns, task organization, environment management, and the DRY patterns needed for multi-project workspaces.

When helping with mise, prefer outputting `mise.toml` config snippets. Always check `mise cfg` to see what config files are loaded before diagnosing issues. Use `mise tasks` to show available tasks and `mise env` to show resolved environment variables.

## When to Use This Skill

- Writing or modifying `mise.toml` / `.mise.toml` configurations
- Creating tasks (inline TOML, included files, or file-based scripts)
- Setting up `[env]` with dynamic values (`exec()`, `_.source`, `_.file`)
- Organizing tasks across multiple files with `task_config.includes`
- Debugging environment variable resolution or profile switching
- Setting up multi-tenant credential management with profiles
- DRY patterns for shared task logic across projects
- Task templates and inheritance for reusable definitions
- Looking up mise CLI commands and flags

## Core Capabilities

### 1. Configuration System

mise walks UP the directory tree — child projects inherit parent configs. This enables shared tasks at the workspace root with project-specific overrides.

See `references/mise_config_guide.md` for the full configuration hierarchy, file precedence, profile loading order, `[env]` patterns, lifecycle hooks, monorepo support, and secret handling.

### 2. Task System

Tasks are the most powerful feature — they turn complex workflows into `mise run <name>` commands. Tasks can be defined inline in `mise.toml`, in separate included files, or as executable scripts in `mise-tasks/`. mise builds a DAG from task dependencies and executes independent tasks in parallel.

See `references/mise_task_patterns.md` for task organization, `task_config.includes` behavior (critical gotchas), DRY patterns, task templates/inheritance, DAG execution model, visibility controls, output caching, and the `usage` field for CLI arg parsing.

### 3. Environment Management

Profiles (`mise.{env}.toml`) enable multi-tenant credential switching. Combined with `exec()` for dynamic secret resolution (keychains, vaults) and `_.source` for dotenv files, mise handles the full spectrum from simple `.env` files to enterprise credential management.

See `references/mise_environment_management.md` for the multi-tenant credential pattern, keychain integration, and cloner-friendly defaults.

### 4. Tool Version Management

```toml
[tools]
python = "3.12"
node = "lts"
uv = "latest"
```

Multiple versions, per-tool postinstall hooks, and backends (npm, pipx, GitHub releases, aqua).

### 5. Watch Mode & Hooks

Continuous file watching (`mise watch`) for rebuild-on-change workflows. Lifecycle hooks (`[hooks]`) for enter/leave/cd events. See `references/mise_config_guide.md`.

## Common Workflows

### "Create a new task"
1. For simple tasks, add inline to `[tasks]` in `mise.toml`
2. For service-grouped tasks, create `tasks/<service>.toml` and include via `task_config.includes`
3. For complex tasks, use `usage` field for arg parsing and `depends` for ordering
4. For reusable patterns, define `[task_templates.*]` and use `extends`

### "Share tasks across projects"
1. Define tasks in a parent directory's `mise.toml` or `tasks/` directory
2. Child projects inherit automatically via mise's directory walk
3. Use `{{config_root}}` in task scripts to resolve paths relative to the config that defined the task

### "Set up credentials for a new tenant"
1. Create `mise.<tenant>.toml` with `exec()` calls to keychain/vault
2. Project sets default tenant in `.miserc.toml` (`env = ["tenant"]`)
3. Cloners use `_.source = ".env"` for simple credential files
4. Switch tenants: `MISE_ENV=other mise run <task>`

### "Look up a CLI command"
See `references/mise_cli_reference.md` for compact command tables covering task management, run flags, environment, and tool operations.

### "Apply a proven automation pattern"
See `references/mise_use_case_patterns.md` for milestone aggregation, hardware discovery, interactive confirmation, post-task cleanup, CI/CD adaptation, and cross-project task sharing decision trees.

## Resources

### references/
- **`mise_config_guide.md`** — Configuration hierarchy, precedence, env patterns, exec(), hooks, monorepo, settings
- **`mise_task_patterns.md`** — Task organization, includes, DRY patterns, DAG model, templates, visibility, caching, usage field
- **`mise_environment_management.md`** — Multi-tenant credentials, profiles, keychain integration
- **`mise_cli_reference.md`** — CLI commands, run flags, task listing, environment and tool management
- **`mise_use_case_patterns.md`** — Milestone aggregation, hardware discovery, confirmation, cleanup, CI/CD, cross-project sharing

### Cross-references
- **environment-composition** `sesh_config_guide.md` — sesh + mise integration for dev environments
- **zsh-dev** — Shell function patterns that complement mise tasks
- **signals-monitoring** — `fswatch`/`entr` for simpler file watching (vs `mise watch`)

### External
- [mise documentation](https://mise.jdx.dev/)
- [GitHub: jdx/mise](https://github.com/jdx/mise)
