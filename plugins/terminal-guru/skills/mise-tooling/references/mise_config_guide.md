---
last_verified: 2026-05-03
sources:
  - type: web
    url: "https://mise.jdx.dev/configuration/"
    description: "Official mise configuration documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/configuration/"]
    description: "mise documentation source for configuration"
---

# Mise Configuration Guide

## Configuration Hierarchy

mise walks **up** the directory tree (child finds parent). Files are loaded with this precedence (top overrides bottom):

| File | Purpose |
|------|---------|
| `mise.local.toml` | Git-ignored personal overrides |
| `mise.toml` / `.mise.toml` | Primary project config |
| `.config/mise/conf.d/*.toml` | Fragments loaded alphabetically |
| Parent directory configs | Inherited (walk up tree) |
| `~/.config/mise/config.toml` | Global user config |
| `/etc/mise/config.toml` | System-wide |

Run `mise cfg` to see which files are loaded and their precedence order.

## Profiles and Environments

Profiles load additional config files without modifying the base config.

**Activation methods:**
- Environment variable: `MISE_ENV=development`
- CLI flag: `--env development`
- Config file: `.miserc.toml` (gitignored, contains `env = ["name"]`)
- Multiple envs: `MISE_ENV=ci,test` (last takes precedence)

**File loading order with env set:**
1. `mise.<env>.local.toml`
2. `mise.local.toml`
3. `mise.<env>.toml`
4. `mise.toml`

Environment-specific configs override base config values.

## Environment Variables

```toml
[env]
# Static value
DATABASE_URL = "postgres://localhost/mydb"

# Tera template
PROJECT_NAME = "{{config_root | basename}}"

# Dynamic via command execution
SECRET = "{{exec(command='vault read -field=value secret/myapp')}}"

# exec() with caching (avoids re-running on every shell prompt)
TOKEN = """{{exec(
  command='curl -sf ... | jq -r .access_token',
  cache_key='my_token',
  cache_duration='50m'
)}}"""

# Required (errors if not set by any config layer)
DB_PASSWORD = { required = true, help = "Set in mise.local.toml or export" }

# Redact from output (mise env, mise set)
API_KEY = { value = "secret123", redact = true }

# Clear a variable
UNWANTED = false

# Load from dotenv file
_.file = ".env"

# Source a shell script (supports export KEY=value)
_.source = "{{config_root}}/.secrets"

# Add to PATH
_.path = ["./bin", "./node_modules/.bin"]
```

### exec() details

- Runs at template rendering time (before task scripts execute)
- `cache_key` + `cache_duration` prevent re-execution on every prompt
- Shell environment variables from `[env]` are available inside `exec()` commands — entries are processed top-to-bottom
- `{{config_root}}` resolves to the directory containing the config file

### _.source vs _.file

- `_.file` loads a dotenv-format file (`KEY=value`, no `export` prefix needed)
- `_.source` sources a shell script (`export KEY=value`, supports command substitution)
- Both are processed at the position they appear in `[env]` — later entries override earlier ones

## Tool Version Management

```toml
[tools]
python = "3.12"
node = "lts"
uv = "latest"

# Multiple versions
python = ["3.11", "3.12"]

# With postinstall
node = { version = "22", postinstall = "corepack enable" }
```

## Lifecycle Hooks

Hooks trigger at workspace lifecycle events:

```toml
[hooks.enter]
run = "echo 'Welcome to the project'"

[hooks.leave]
run = "echo 'Goodbye'"

[hooks.cd]
run = "echo 'Changed to {{cwd}}'"
```

Available hook points:
- **`enter`** — triggered when entering the workspace directory
- **`leave`** — triggered when leaving the workspace
- **`cd`** — triggered on every directory change within the workspace
- **`watch`** — file watch listeners that activate when tracked paths update

Hooks run in the shell context with full access to `[env]` variables. The `{{cwd}}` template resolves to the current working directory at hook execution time.

## Monorepo Support

mise supports multi-directory projects with special path syntax:

```toml
# Reference tasks from monorepo root
[tasks.build-all]
depends = ["//frontend:build", "//backend:build"]
run = "echo 'All packages built'"

# Declare sub-project config locations
[monorepo]
config_roots = ["packages/*", "apps/*"]
```

- **`//` prefix** — resolves from monorepo root, not current directory
- **`:` separator** — `//projects/frontend:build` targets a specific sub-project task
- **`*` wildcards** — match across directories and task names
- **`config_roots`** — declares where mise should discover sub-project configs
- **Subdirectory scripts** — auto-prefix with directory path (e.g., `web:test`)

## Secret Handling

```toml
[settings]
# Mask sensitive variable names in logs (supports globs)
redactions = ["*_SECRET", "*_KEY", "*_TOKEN", "CREDENTIALS_*"]
```

Individual env vars can also be redacted:

```toml
[env]
API_KEY = { value = "secret123", redact = true }
```

The `redactions` setting works with patterns — any env var matching the glob is masked in `mise env` output and logs.

## Task-Related Settings

| Setting | Default | Purpose |
|---------|---------|---------|
| `task.jobs` | 4 | Max concurrent workers for parallel task execution |
| `task.output` | `"prefix"` | Log format: `prefix`, `interleave`, or custom |
| `task.timeout` | — | Default timeout for all tasks (seconds) |
| `task_timing` | false | Show timing for every task by default |
| `task_auto_install` | true | Auto-install tools needed by tasks before running |

Configure globally in `~/.config/mise/config.toml` or per-project in `mise.toml`:

```toml
[settings]
task_timing = true
color = true
color_theme = "default"  # default/charm (dark), base16 (light), catppuccin, dracula
```

## Watch Mode

Continuous file watching for rebuild-on-change workflows:

```bash
mise watch build -w src -w Cargo.toml    # rebuild when files change
mise watch build --restart               # restart long-running process on change
mise watch test -w "src/**/*.py"         # glob pattern for watched paths
```

Requires the `watchexec` utility. For simpler file watching needs (single command, no task DAG), consider `entr` or `fswatch` via the signals-monitoring skill.

## Diagnostics

```bash
mise cfg        # show loaded config files and precedence
mise env        # show resolved environment variables
mise doctor     # comprehensive health check
mise trust      # trust a config file (required for untrusted sources)
```
