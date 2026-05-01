# Mise Environment Management

## Multi-Tenant Credential Pattern

A layered config pattern that gives cloners a simple `.env` workflow while power users get keychain-backed tenant switching via parent environment configs.

### Layout

```
workspace/                         # not a git repo
├── .mise.toml                     # shared tasks (task_config.includes)
├── scripts/sase-token.sh          # shared auth helper
├── tasks/                         # included task files
│   ├── scm.toml
│   ├── redteam.toml
│   └── model.toml
├── mise.tenant-a.toml             # tenant A — keychainctl exec()
├── mise.tenant-b.toml             # tenant B — keychainctl exec()
└── project/                       # git repo
    ├── .mise.toml                 # app defaults + _.source = ".env"
    ├── .miserc.toml               # env = ["tenant-a"] (gitignored)
    ├── .env                       # credentials (gitignored, cp from template)
    └── env.template               # documented credential template (committed)
```

### How it works

**Cloner path** (no keychain, no parent configs):
1. `cp env.template .env` → fill in credentials
2. `.mise.toml` sources `.env` via `_.source`
3. Docker uses `.env` via `--env-file`

**Power user path** (keychain + tenant switching):
1. All tenant values in one keychain entry as JSON:
   ```bash
   keychainctl pair set -l "My Tenant" tenant-name \
     TSG_ID=123 CLIENT_ID=... CLIENT_SECRET=...
   ```
2. Parent `mise.tenant-name.toml` pulls each value via `exec()`:
   ```toml
   [env]
   TSG_ID = "{{exec(command='keychainctl pair get tenant-name TSG_ID')}}"
   CLIENT_ID = "{{exec(command='keychainctl pair get tenant-name CLIENT_ID')}}"
   ```
3. `.miserc.toml` selects `env = ["tenant-name"]` → mise loads parent tenant config
4. Switch tenants: `MISE_ENV=tenant-b mise run dev`

### Precedence (highest wins)
1. Parent `mise.<env>.toml` (keychain values, if `.miserc.toml` exists)
2. `.mise.toml` `_.source` → `.env` (local credential overrides)
3. `.mise.toml` `[env]` static values (app defaults)

### Design decisions
- `.env` serves double duty — mise sources it AND Docker uses it via `--env-file`
- `.miserc.toml` is gitignored — cloners never see the tenant-switching layer
- One keychain entry per tenant — `keychainctl pair set` stores all values as compressed JSON
- `env.template` is the single reference — documents all required variables

## Task Inheritance

Tasks defined in parent directory configs are automatically available in child projects:

```
workspace/.mise.toml          # defines scm:auth, redteam:targets
└── project/.mise.toml        # defines hol:build, hol:dev
    $ mise tasks              # shows BOTH parent and project tasks
```

Tasks using `source` or file paths should use `{{config_root}}` to resolve relative to the config that defined them, not the current working directory.

## Profile-Specific Tasks

Tasks can be conditionally available based on the active profile by defining them in `mise.<env>.toml` files. This keeps tenant-specific operations (like profile cleanup) separate from general tasks.
