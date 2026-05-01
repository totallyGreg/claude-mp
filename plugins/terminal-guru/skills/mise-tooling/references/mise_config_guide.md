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

## Settings

Global settings go in `~/.config/mise/config.toml`:

```toml
[settings]
color = true
color_theme = "default"  # default/charm (dark), base16 (light), catppuccin, dracula
```

The `color_theme` setting controls the interactive TUI picker (`mise run` with no args). The `color = false` setting only affects CLI output, not the interactive picker.
