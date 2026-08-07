---


name: mise-tooling
description: This skill should be used when the user asks to "configure mise.toml", "create a mise task", "set up tool versions", "manage environments with mise", "debug mise config", "task_config includes", "mise task DRY", "mise profiles", "mise env not loading", "create mise run command", or needs help with mise (jdx/mise) for tool versioning, environment variables, or task automation. Also trigger on mentions of mise.toml, .miserc.toml, mise run, mise env, mise tasks, mise profiles, task_config, or exec() in env. Do NOT use for shell configuration or function generation (use zsh-dev instead). Do NOT use for sesh/tmux session management (use environment-composition instead). Do NOT use for signal handling or logging (use signals-monitoring instead). Mise + sesh integration questions should route here for the mise side and environment-composition for the sesh side.
metadata:
  conciseness: 100
  complexity: 90
  spec_compliance: 100
  progressive: 100
  overall: 98
  last_evaluated: 2026-07-23
  reference_currency: 100
  version: "2.7.1"
license: MIT
compatibility: claude-code


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

See `references/mise_environment_management.md` for the multi-tenant credential pattern, keychain integration, cloner-friendly defaults, multi-cluster/multi-target overlay configs, and capturing runtime-discovered values with `mise set` for downstream tasks.

### 4. Tool Version Management

```toml
[tools]
python = "3.12"
node = "lts"
uv = "latest"
```

Multiple versions, per-tool postinstall hooks, and backends (npm, pipx, GitHub releases, aqua).

### 5. Watch Mode & Hooks

Continuous file watching for rebuild-on-change workflows — but prefer a runtime-native watcher (`bun --watch`, `node --watch`, `uvicorn --reload`) over `mise watch`/`watchexec` when the runtime has one (zero extra processes). Use `mise watch` for runtimes without a built-in watcher (Go, Rust, shell) or multi-step task DAGs. Lifecycle hooks (`[hooks]`) for enter/leave/cd events. See `references/mise_config_guide.md`.

### 6. Bootstrap (Declarative Machine Setup, experimental)

`mise bootstrap` provisions a whole machine — `[bootstrap.packages]` (brew/apt/dnf/pacman/apk/mas), `[bootstrap.repos]` (declarative git clones), `[dotfiles]`, shell activation, macOS defaults/LaunchAgents, Linux systemd user units, login shell — before installing project `[tools]`. Separate concern from `[tools]`: machine-global, not version-pinned, no shims.

See `references/mise_bootstrap_system.md` for the full config shape, the 11-step run order, and `--skip`/`--only` part names.

## Common Workflows

### "Create a new task"

Simple inline task:

```toml
[tasks.lint]
description = "Run linter"
run = "ruff check src/"
```

Task with arguments (no `--` needed for positional args):

```toml
[tasks.deploy]
description = "Deploy to environment"
usage = '''
arg "[env]" help="Target environment" default="staging"
flag "-f --force" help="Skip confirmation"
'''
run = 'echo "Deploying to $usage_env (force=$usage_force)"'
```

For complex tasks, use file-based scripts in `.mise/tasks/` with `#USAGE` directives. For reusable patterns, define `[task_templates.*]` and use `extends`.

### "Share tasks across projects"
1. Define tasks in a parent directory's `mise.toml` or `tasks/` directory
2. Child projects inherit automatically via mise's directory walk
3. Use `{{config_root}}` in inline TOML `run` blocks (not file-based scripts — Tera doesn't render those, see `mise_config_guide.md`) to resolve paths relative to the config that defined the task

### "Set up credentials for a new tenant"

```toml
# mise.prod.toml — activated by MISE_ENV=prod or .miserc.toml
[env]
API_KEY = "{{exec(command='keychainctl pair get myapp API_KEY')}}"
```

Set default tenant in `.miserc.toml` (`env = ["prod"]`). Cloners use `_.source = ".env"` as fallback. Switch tenants: `MISE_ENV=staging mise run deploy`.

### "Look up a CLI command"
See `references/mise_cli_reference.md` for compact command tables covering task management, run flags, environment, and tool operations.

### "Apply a proven automation pattern"
See `references/mise_use_case_patterns.md` for milestone aggregation, hardware discovery, interactive confirmation, post-task cleanup, CI/CD adaptation, release pipeline ordering (build-before-publish), implicit tool dependencies, monorepo affected detection, and cross-project task sharing decision trees.

## Authoring Conventions

When writing or editing `mise.toml`, apply these conventions:

- **Section order** (top-to-bottom, omit empty): `[settings]` → `[env]` → `[tools]` → `[hooks]` / `[vars]` / `[task_config]` / `[task_templates]` (if present) → `[tasks.*]`.
- **Task ordering**: lifecycle, not alphabetical — setup/install first, run/operate next, maintenance/occasional last. Slot new tasks into the right group; don't append blindly.
- **Task descriptions**: the `description` is the primary signal an agent (or teammate) reads from `mise tasks ls` to decide whether and how to invoke a task — write it to answer *what it does, what it requires, what it produces, and when to run it*. `"Run test suite"` is too thin; `"Run pytest against src/ with coverage; requires uv; exits non-zero on failure; safe to re-run"` lets the caller act without opening the file. **Compact-listing readability**: the same description shows in the compact `mise tasks` listing and shell completions, where long descriptions wrap and overlap — over-applying the density rule produced full-paragraph descriptions that required a real `cut -c1-94` workaround. Lead with a tight ≤72-char summary that stands alone in the compact listing; push arg-level detail into `#USAGE help=` and the task body; reserve the full what/requires/produces/when for `mise tasks --extended`. Density and compact legibility are in tension — the first clause must be legible on its own.
- **Inline vs script**: one-liners stay inline; once a task needs conditionals, loops, or more than ~5 lines, extract to `scripts/<task>.sh` and invoke via `run = "scripts/<task>.sh"` — easier to shellcheck, test, and reuse outside mise. Upgrade to a file-based task under `.mise/tasks/` only when you want mise-native features: auto-discovery, `#USAGE` arg parsing, `#MISE sources/outputs`, or directory-based namespacing. See `mise_task_patterns.md`.
- **`#USAGE`/`#MISE` are KDL — mind the escapes**: mise parses these directives as KDL. KDL strings accept only KDL's built-in escapes (`\"`, `\n`, `\t`, `\r`, `\uXXXX`, and backslash-backslash for a literal backslash); any *other* backslash escape — notably `\$` — is a parse error, and KDL doesn't interpolate anyway, so write `$VAR` plain in a `help=`/`default` (or reword to avoid `$`). A bad escape makes mise emit `failed to parse task file … Expected quoted string` and **silently breaks `mise tasks` + tab-completion**. Gotcha: the error only surfaces when a task's usage spec is *loaded* — `mise tasks info <name>`, shell completion, or `mise <task> --help` — NOT in a plain `mise tasks`. Catch it in CI by loading every task's spec: `mise tasks | awk 'NF{print $1}' | while read -r t; do mise tasks info "$t" >/dev/null 2>>err; done; grep -i "failed to parse" err`.
- **Editing discipline**: if a task could fit in more than one lifecycle group, ask the user. Do not reorder unrelated existing tasks unless cleanup was explicitly requested.

See `references/mise_config_guide.md` (Style & Layout) for rationale and worked examples.

## Resources

### references/
- **`mise_config_guide.md`** — Configuration hierarchy, precedence, env patterns, exec(), hooks, monorepo, settings, auto_env platform environments
- **`mise_task_patterns.md`** — Task organization, includes (ordering, git:: remote includes), DRY patterns, DAG model, templates, visibility, caching, usage field
- **`mise_environment_management.md`** — Multi-tenant credentials, profiles, keychain integration, shell-style env var expansion, sops secrets
- **`mise_cli_reference.md`** — CLI commands, run flags, task listing, environment and tool management
- **`mise_use_case_patterns.md`** — Milestone aggregation, hardware discovery, confirmation, cleanup, CI/CD, release pipeline ordering, implicit tool dependencies, monorepo affected detection, cross-project sharing
- **`mise_bootstrap_system.md`** — Declarative machine bootstrap: packages, repos, dotfiles, macOS/Linux system config, login shell

### Cross-references
- **environment-composition** `sesh_config_guide.md` — sesh + mise integration for dev environments
- **zsh-dev** — Shell function patterns that complement mise tasks
- **signals-monitoring** — `fswatch`/`entr` for simpler file watching (vs `mise watch`)

### External
- [mise documentation](https://mise.jdx.dev/)
- [GitHub: jdx/mise](https://github.com/jdx/mise)
