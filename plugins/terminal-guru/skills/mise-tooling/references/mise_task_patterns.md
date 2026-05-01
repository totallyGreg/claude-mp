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

Place executable scripts in `mise-tasks/` or `.mise/tasks/`. mise discovers them automatically by filename.

## Task Namespacing

Use colon-separated names for logical grouping by service area:

```
redteam:targets    redteam:scans
model:groups       model:rules       model:scan
scm:auth           scm:profiles      scm:profile-cleanup
hol:build          hol:dev           hol:restart
```

Convention: `<service>:<action>` — the service prefix groups related operations.

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
run = """
source "{{config_root}}/scripts/sase-token.sh"
ACCESS_TOKEN=$(sase_token) || exit 1
curl -sf "$API_BASE/targets" -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
"""
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

## Running Tasks

```bash
mise run build              # also: mise r build, or just: mise build
mise run test -- --verbose  # pass extra args after --
mise run build ::: test     # parallel execution
mise run --jobs 8 build     # parallel with job limit
mise run --skip-deps deploy # skip dependency tasks
mise tasks                  # list all available tasks
```

## Other Features

- `confirm = "Are you sure?"` — prompt before destructive tasks
- `raw = true` — for interactive tasks that need stdin
- `sources` / `outputs` — make-like skip logic (only runs if sources newer than outputs)
- `depends_post` — tasks to run after this task completes
