---
last_verified: 2026-07-03
sources:
  - type: web
    url: "https://mise.jdx.dev/environments/"
    description: "Official mise environments documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/environments/", "docs/environments/secrets/sops.md"]
    description: "mise documentation source for environments"
---

# Mise Environment Management

## Env Var Ergonomics (mise ≥ 2026.6.0–2026.7.0)

**Shell-style variable expansion — enabled by default since 2026.7.0 (PR #10702).** As an alternative to Tera templates, `[env]` values now expand shell-style `$VAR`/`${VAR}` syntax, run *after* Tera rendering so both can be mixed:

```toml
[env]
MY_PROJ_LIB = "{{config_root}}/lib"       # Tera, resolved first
LD_LIBRARY_PATH = "$MY_PROJ_LIB:$LD_LIBRARY_PATH"  # shell-style, resolved second
```

| Syntax | Behavior |
|---|---|
| `$VAR` / `${VAR}` | Expands to `VAR`'s value (`${VAR}` when followed by alphanumerics, e.g. `${VAR}_suffix`) |
| `${VAR:-default}` | Uses `default` if `VAR` is unset or empty |
| `${VAR:-}` | Empty string if unset, suppresses the undefined-variable warning |

Undefined variables with no default are left unexpanded and warn. Controlled by a setting (`true`/unset = enabled, `false` = disabled) — was opt-in before 2026.7.0, now on by default.

**`{ default = "..." }` fallback shorthand (PR #10441).** Sets a value only if the variable is unset or empty — preserves a pre-existing non-empty value from the shell or an earlier config file:

```toml
[env]
NODE_ENV = { default = "development" }   # keeps existing NODE_ENV if already set/non-empty
```

**`required = true` / `required = "help text"`.** Marks a variable that must be set by the shell environment or a later-loaded config file (e.g. `mise.local.toml`); `mise env` fails with a clear error (optionally showing your help text) if it's missing, while shell activation (`hook-env`) only warns so it doesn't break `cd`.

**sops-encrypted `.env.toml` files (PR #10201, experimental).** `env._.file` already supported sops-encrypted `.env.json`/`.env.yaml`; TOML is now supported too — but only via mise's built-in decryption (`sops.rops = true`, the default). The external `sops` CLI itself doesn't support TOML in/out, so setting `sops.rops = false` breaks encrypted `.env.toml` — use `.env.json`/`.env.yaml` if you need the external CLI path. Same age-key setup as JSON/YAML (`MISE_SOPS_AGE_KEY_FILE` / `SOPS_AGE_KEY_FILE`).

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

## Multi-Cluster / Multi-Target Overlay Pattern

One base config with per-environment overlays — each overlay carries its own endpoint, kubeconfig, secrets, and host references. Switching clusters is a single env var.

### Layout

```
project/
├── .mise.toml                  # base defaults, CLUSTER_TARGET="dev", task_config.includes
├── .mise.staging.toml          # staging overrides
├── .mise.production.toml       # production overrides
├── .miserc.toml                # env = ["staging"]  (gitignored — sets local default)
├── bootstrap/
│   └── talos/
│       ├── secrets.dev.yaml
│       └── secrets.staging.yaml
└── tasks/
    ├── talos.toml
    └── infra.toml
```

### Base config

```toml
# .mise.toml
[env]
CLUSTER_TARGET   = "dev"
CLUSTER_NAME     = "homestack"
CLUSTER_ENDPOINT = "https://192.168.1.201:6443"
TALOS_ENDPOINT   = "192.168.1.201"
KUBECONFIG       = "{{env.HOME}}/.kube/config.d/{{env.CLUSTER_NAME}}.yaml"
TALOSCONFIG      = "{{config_root}}/bootstrap/talos/{{env.CLUSTER_TARGET}}.talosconfig"
SECRETS          = "{{config_root}}/bootstrap/talos/secrets.{{env.CLUSTER_TARGET}}.yaml"

[task_config]
includes = ["tasks/talos.toml", "tasks/infra.toml"]
```

### Per-target overlay

```toml
# .mise.staging.toml
[env]
CLUSTER_TARGET   = "staging"
CLUSTER_NAME     = "staging"                    # drives KUBECONFIG filename
# IMPORTANT: define CLUSTER_ENDPOINT explicitly — do NOT rely on template composition
# from other env vars in the same profile (evaluation order is not guaranteed).
CLUSTER_ENDPOINT = "https://10.0.1.50:6443"
TALOS_ENDPOINT   = "10.0.1.50"
TRUENAS_HOST     = "nas.staging.internal"
TRUENAS_API_KEY  = "{{exec(command='keychainctl get STAGING-NAS-API')}}"
```

### Activation

```bash
MISE_ENV=staging mise run bootstrap:apply   # one-shot override
export MISE_ENV=staging                     # shell-session override
echo 'env = ["staging"]' > .miserc.toml    # persistent local default (gitignore this)
```

### Key constraints

- **`CLUSTER_ENDPOINT` must be explicit** in each overlay — if it's composed from another env var defined in the same profile file, evaluation order is not guaranteed and it may resolve to the base value. Define it as a literal string in each profile.
- **`KUBECONFIG` should use `{{env.CLUSTER_NAME}}`**, not the target name — `CLUSTER_NAME` drives what `talosctl gen config` writes, so the kubeconfig filename must match.
- Per-target secrets and API keys: use `exec()` with a per-target keychain entry name so switching profiles also switches credentials automatically.

## Bootstrap Output Capture with `mise set`

When a task discovers a dynamic value (IP address, LB endpoint, generated ID), write it back into the profile with `mise set` so downstream tasks in the same session can use it without manual intervention.

```bash
# Task discovers the gateway LoadBalancer IP after install
LB_IP=$(kubectl get svc gateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
mise set -E "${CLUSTER_TARGET}" GATEWAY_LB_IP="${LB_IP}"
echo "==> Saved GATEWAY_LB_IP=${LB_IP} to .mise.${CLUSTER_TARGET}.toml"
```

The `-E <env>` flag writes to the profile-specific file (`.mise.staging.toml`) rather than the base `.mise.toml`. The value persists across subsequent `mise run` invocations — no need to re-discover it or export it manually.

**When to use:** Any value that is:
- Discovered at runtime (not known at config-write time)
- Needed by downstream tasks in the same bootstrap sequence
- Worth persisting so recovery/re-runs don't need to rediscover it

**Avoid** state files (fragile, separate from mise's env system) and `export` in task bodies (does not propagate to the next `mise run` invocation).
