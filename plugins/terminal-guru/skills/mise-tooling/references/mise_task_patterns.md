---
last_verified: 2026-05-03
sources:
  - type: web
    url: "https://mise.jdx.dev/tasks/"
    description: "Official mise task documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/tasks/"]
    description: "mise documentation source for tasks"
---

# Mise Task Patterns

## Defining Tasks

### Inline (in mise.toml)

```toml
[tasks.test]
run = "pytest"

[tasks."test:unit"]
run = "pytest tests/unit"
depends = ["build"]
```

### Included files (task_config.includes)

```toml
# mise.toml
[task_config]
includes = [
  "tasks/scm.toml",
  "tasks/redteam.toml",
  "tasks/model.toml",
]
```

**Critical: directory paths silently fail.** `includes = ["tasks/"]` does NOT work — you must list each file explicitly.

Included files use **simplified schema** — no `[tasks]` prefix:

```toml
# tasks/redteam.toml
["redteam:targets"]
description = "List red team targets"
run = "curl -sf ..."

["redteam:scans"]
description = "List red team scans"
run = "curl -sf ..."
```

### File-based tasks

Place executable scripts in any of these auto-discovered directories:

- `mise-tasks/`
- `.mise-tasks/`
- `mise/tasks/`
- `.mise/tasks/`
- `.config/mise/tasks/`

Scripts in subdirectories get auto-prefixed: `mise-tasks/build/docker.sh` becomes task `build:docker`. The special filename `_default` strips the suffix.

Add metadata via `#MISE` comment directives at the top of scripts:

```bash
#!/usr/bin/env bash
#MISE description="Discover Talos endpoints"
#MISE depends=["vm:start"]
#MISE env={CLUSTER="bee3"}
#MISE sources=["src/**"]
nmap -p 50000 10.0.0.0/24
```

Supports any shebang: bash, node, python, deno, powershell.

## Task Namespacing

Use colon-separated names for logical grouping by service area:

```
redteam:targets    redteam:scans
model:groups       model:rules       model:scan
scm:auth           scm:profiles      scm:profile-cleanup
hol:build          hol:dev           hol:restart
```

Convention: `<service>:<action>` — the service prefix groups related operations.

## Core Task Properties

| Property | Type | Purpose |
|----------|------|---------|
| `run` | string / array | Command(s) to execute. Arrays run sequentially. |
| `run_windows` | string | Windows-specific override. |
| `description` | string | Shown in `mise tasks --extended` and completions. |
| `alias` / `aliases` | string / array | Alternative invocation names. |
| `depends` | string / array | Prerequisites that must succeed first. Forms DAG edges. |
| `depends_post` | string / array | Runs after parent completes regardless of success. |
| `wait_for` | string / array | Soft dependency — pauses until target completes but doesn't fail if target failed. |
| `dir` | string | Working directory override. `{{cwd}}` for caller's CWD. |
| `shell` | string | Override interpreter (e.g., `"bash"`, `"fish"`). |
| `tools` | object | Per-task tool installs (e.g., `{rust = "1.80"}`). Auto-installed before run. |
| `env` | object | Task-level env vars. NOT propagated to dependencies. |
| `confirm` | string | Interactive prompt before running. Supports Tera templates. |
| `hide` | bool | Hide from `mise tasks` listing and completions. |
| `quiet` | bool | Suppress "running: \<command\>" header. |
| `silent` | bool / string | Mute stdout/stderr. Value can target `"stdout"` or `"stderr"`. |
| `raw` | bool | Direct I/O passthrough. Breaks parallelism. |
| `interactive` | bool | Exclusive stdio lock — blocks other tasks. |
| `raw_args` | bool | Bypass argument parsing, forward inputs verbatim. |
| `sources` | array | Input file globs for freshness checking. |
| `outputs` | array | Output file globs. `{ auto = true }` for hash-based cache. |
| `no_output_cache` | bool | Disable output caching for this task. |

## vars (Task-Scoped Variables)

Shared between tasks via templates but NOT exported as environment variables:

```toml
[vars]
default_group = "03140d51-de69-43a4-8aba-dc447b3cebf9"

[tasks.scan]
run = "model-security scan --security-group-uuid {{vars.default_group}}"
```

**Limitation:** `[vars]` cannot be top-level in included task files. Define `[vars]` in the root `mise.toml` — they are accessible in all included tasks via `{{vars.x}}`.

## depends (Task Dependencies)

```toml
[tasks."hol:up"]
depends = ["hol:build"]
run = "mise run hol:run"
```

**Limitation:** `depends` tasks run in separate processes. Environment variables and shell `export` statements do NOT leak between them. Each task's `env` is scoped to that task only.

## DAG Execution Model

mise builds a **Directed Acyclic Graph** from all task dependencies:

1. Resolve full DAG from task definitions
2. Topological sort to determine execution order
3. Launch independent tasks in parallel (up to `task.jobs`, default 4)
4. When a task completes, check if dependents are now unblocked
5. `depends_post` runs after the entire graph settles

Key behaviors:
- **Shared dependencies run once** — if both `test:unit` and `test:integration` depend on `build`, `build` runs only once
- **`depends`**: prerequisite must **succeed** before dependent runs
- **`depends_post`**: cleanup runs **after** parent regardless of outcome
- **`wait_for`**: soft sync — waits but doesn't fail if target failed

```bash
mise run build ::: test ::: lint   # parallel execution
mise run --jobs 8 build test lint  # parallel with job limit
mise tasks deps <task>             # print dependency graph (DOT format)
mise run --dry-run <task>          # show execution plan without running
```

## Task Templates & Inheritance

Reusable task definitions via `[task_templates.*]` and the `extends` property:

```toml
[task_templates.python:test]
run = "pytest"
tools = { python = "3.12" }

[tasks.api-test]
extends = "python:test"
env = { API_URL = "http://localhost:8080" }
```

**Merge rules for `extends`:**

| Property | Strategy |
|----------|----------|
| `run` / `run_windows` | **Replaces** (never merged) |
| `depends` | **Replaces** (not accumulated) |
| `env` | **Deep merge** (template env preserved) |
| `tools` | **Deep merge** |
| `dir` / `description` / `shell` | **Does not inherit** — must redefine |

## Output Caching & Incremental Builds

Make-like skip logic: when all `outputs` are newer than all `sources`, the task is skipped entirely.

```toml
[tasks.build]
sources = ["src/**/*.rs", "Cargo.toml"]
outputs = ["target/release/myapp"]
run = "cargo build --release"
```

- `sources` — input file globs (changes trigger rebuild)
- `outputs` — output file globs; `{ auto = true }` uses hash-based cache keys
- `no_output_cache = true` — bypass caching for this task
- `mise run --force` — force re-execution regardless of cache
- `mise run --no-cache` — skip all caching for this run

## DRY Pattern: Shared Shell Functions

For logic shared across tasks (e.g., OAuth token fetch), define helper functions in a script and source them per-task:

```bash
# scripts/sase-token.sh
sase_token() {
  local response
  response=$(curl -sf -X POST "$SASE_AUTH_ENDPOINT" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -u "$CLIENT_ID:$CLIENT_SECRET" \
    -d "grant_type=client_credentials&scope=tsg_id:$TSG_ID") || {
    echo "FAILED: Could not obtain access token" >&2
    return 1
  }
  echo "$response" | jq -r '.access_token'
}
```

Then in each task:

```toml
["redteam:targets"]
run = '''
source "{{config_root}}/scripts/sase-token.sh"
ACCESS_TOKEN=$(sase_token) || exit 1
curl -sf "$API_BASE/targets" -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
'''
```

`{{config_root}}` resolves to the directory of the `mise.toml` that defined the task — critical for tasks inherited by child projects.

## usage Field (CLI Arg Parsing)

Turns tasks into full CLIs with argument parsing and shell autocomplete:

```toml
[tasks.scan]
usage = '''
arg "<model_path>" help="Path or URI to scan"
option "-g --group" help="Security group UUID"
flag "-v --verbose" help="Verbose output"
flag "--delete" help="Actually delete (default is dry-run)"
'''
run = "model-security scan --model-path {{arg(name='model_path')}}"
```

Access parsed values via `$usage_<name>` in the `run` script.

**Advanced patterns:**
- `<arg>` — mandatory positional argument
- `[arg]` — optional positional argument
- `${usage_var?}` — error if variable not set
- `${usage_var:-default}` — default value (non-mutating)
- Template functions: `{{arg(name='x')}}`, `{{option(name='x')}}`, `{{flag(name='x')}}`

## Running Tasks

```bash
mise run build              # also: mise r build, or just: mise build
mise run test -- --verbose  # pass extra args after --
mise run build ::: test     # parallel execution
mise run --jobs 8 build     # parallel with job limit
mise run --skip-deps deploy # skip dependency tasks
mise run --timings build    # show timing per task
mise run --timeout 60 test  # set max execution time
mise run --yes deploy       # auto-confirm prompts
mise tasks                  # list all available tasks
mise tasks info <task>      # show task metadata
```

## TOML String Gotcha

Always use TOML literal multiline strings (`'''`) for `run` blocks. Basic multiline strings (`"""`) process backslash escapes, breaking jq (`\(.field)`), heredocs, and other shell constructs:

```toml
# WRONG — breaks jq
run = """
  jq -r '"result: \(.id)"'
"""

# CORRECT — content reaches bash verbatim
run = '''
  jq -r '"result: \(.id)"'
'''
```
