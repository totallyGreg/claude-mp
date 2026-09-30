---
last_verified: 2026-07-03
sources:
  - type: web
    url: "https://mise.jdx.dev/tasks/"
    description: "Official mise task documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/tasks/"]
    description: "mise documentation source for task patterns"
---

# Mise Use Case Patterns

Reusable patterns for common task automation scenarios. Each pattern shows the mise.toml structure and explains when to apply it.

## Milestone Aggregation

Meta-tasks that chain domain-specific work into milestone targets. Each milestone `depends` on its prerequisites, forming a progressive deployment pipeline.

```toml
[tasks."cluster:up"]
description = "Zero to running k8s cluster"
depends = ["cluster:nodes", "cluster:network"]

[tasks."cluster:network"]
description = "Gateway + cert-manager + HTTPS"
depends = ["cluster:up"]

[tasks."cluster:storage"]
description = "NFS + iSCSI provisioners"
depends = ["cluster:network"]
```

**When to use:** Multi-phase infrastructure or deployment pipelines where later phases build on earlier ones. `mise run cluster:storage` automatically runs everything from scratch.

## Hardware Discovery Workflow

Tasks with dependencies plus a manual checkpoint where the user sets an environment variable between steps:

```toml
[tasks."vm:start"]
description = "Start virtual machine"
run = "qemu-system-x86_64 ..."

[tasks."vm:discover"]
description = "Scan for VM IP address"
depends = ["vm:start"]
run = "nmap -p 50000 10.0.0.0/24"

[tasks."talos:apply"]
description = "Apply Talos config (requires TALOS_ENDPOINT)"
env = { TALOS_ENDPOINT = { required = true, help = "Set to discovered IP" } }
run = "talosctl apply-config --nodes $TALOS_ENDPOINT ..."
```

**When to use:** Workflows where an intermediate step produces output that a human must inspect and feed forward. The `required = true` env var forces the user to set it before the next phase runs.

## Interactive Confirmation

Protect destructive operations with `confirm`:

```toml
[tasks."cluster:destroy"]
description = "Full cluster teardown"
confirm = "WARNING: This will destroy the entire cluster. Type YES to proceed:"
run = "./scripts/destroy.sh"

[tasks."db:drop"]
description = "Drop database"
confirm = "This will delete all data in {{vars.db_name}}. Continue?"
run = "dropdb {{vars.db_name}}"
```

The `confirm` field supports Tera templates — reference `{{vars.*}}` or env vars in the prompt. In CI, use `mise run --yes <task>` to auto-confirm.

**When to use:** Any task that deletes data, tears down infrastructure, or has irreversible side effects.

## Post-Task Cleanup

Use `depends_post` for cleanup that must run regardless of task success:

```toml
[tasks.deploy]
description = "Deploy to staging"
depends = ["build", "test"]
depends_post = ["cleanup:artifacts"]
run = "kubectl apply -f manifest.yaml"

[tasks."cleanup:artifacts"]
description = "Remove build artifacts"
hide = true
run = "rm -rf dist/ .build-cache/"
```

`depends_post` tasks run **after** the parent completes — even if the parent fails. The cleanup task is `hide = true` since it's not meant to be invoked directly.

**When to use:** Temporary files, docker containers, test fixtures, or staging environments that must be cleaned up.

## CI/CD Adaptation

Use profiles to change task behavior between local and CI environments:

```toml
# mise.toml — base tasks
[tasks.test]
run = "pytest --tb=short"

[tasks.deploy]
run = "./scripts/deploy.sh"
confirm = "Deploy to production?"
```

```toml
# mise.ci.toml — CI overrides
[tasks.test]
run = "pytest --tb=long --junitxml=results.xml"

[tasks.deploy]
run = "./scripts/deploy.sh"
# No confirm in CI — auto-approved via pipeline
```

Activate with `MISE_ENV=ci` in the CI runner. The CI profile overrides base tasks without modifying the shared config.

**When to use:** Different output formats, stricter checks, or removed interactive prompts in CI.

## Release Pipeline Ordering

Release workflows have phases that must run in order (version → build → publish). Defining them as independent tasks without `depends` means nothing enforces ordering — a stray `mise run release:publish` runs before artifacts exist and fails late:

```toml
# ❌ publish has no dependency on build — can run in any order
[tasks."release:build"]
run = "maturin build --release"

[tasks."release:publish"]
run = "./scripts/publish.sh"   # fails with "no artifacts found" if build hasn't run
```

Wire the DAG so every standalone invocation is safe:

```toml
[tasks."release:build"]
depends = ["release:version"]      # bump version first, so artifacts carry the right version
run = "maturin build --release && cp target/wheels/* dist/"

[tasks."release:publish"]
depends = ["release:build"]        # ✅ publish can never run before build
run = "./scripts/publish.sh"       # reads only from dist/

[tasks."release:full"]
description = "Full release: version → build → publish"
depends = ["release:publish"]      # orchestrator pulls the whole chain
```

**Rule:** if two tasks must always run in a specific order, wire it with `depends`. "Manual step after X" is documentation, not enforcement — it gets skipped under pressure. Consolidate all build artifacts into one directory (`dist/`) so the publish step has a single place to look.

**Selective re-run:** when builds are slow and you want to re-publish without rebuilding, swap the `depends` for a hidden guard task that checks the artifact exists and fails with a clear message:

```toml
[tasks._guard-artifacts]
hide = true
run = '[ -n "$(find dist -name "*.whl" 2>/dev/null)" ] || { echo "No wheels in dist/ — run release:build first"; exit 1; }'

[tasks."release:publish"]
depends = ["_guard-artifacts"]     # guard instead of a full rebuild
run = "./scripts/publish.sh"
```

**When to use:** any multi-phase release/deploy pipeline where phases produce artifacts consumed by later phases.

## Implicit Tool Dependencies

Some tools accept flags that silently require *other* tools. When the helper is missing they don't fail fast — they produce wrong output or fail cryptically late. Declare every helper in `[tools]`:

```toml
[tools]
zig = "latest"
"cargo:maturin" = "latest"
"cargo:cargo-zigbuild" = "latest"   # maturin --zig silently needs this for manylinux compliance
```

Common cases:

| Primary tool | Implicit dependency | Symptom if missing |
|---|---|---|
| `maturin --zig` | `cargo-zigbuild` | manylinux compliance failure (late) |
| `cargo build` (PyO3) | `python` on PATH | "Python not found" during link |
| `semantic-release` | `bun` or `npm` | "Cannot find module" |
| `gh pr create` | `GH_TOKEN` in env | 401 / login prompt |

**Rule:** if a tool flag name-checks another tool (`--zig`, `--with-node`, …), check whether that tool — or a helper for it — belongs in `[tools]`. Read the flag's docs to find undeclared dependencies.

## Monorepo Affected Detection

mise has **no native affected detection** — it can't tell which packages a git change touched. For small monorepos (< ~10 packages), a hidden git-diff task is enough:

```toml
[tasks._changed-packages]
description = "List packages changed since origin/main"
hide = true
run = '''
git diff --name-only origin/main 2>/dev/null \
  | grep -E '^packages/[^/]+/' | cut -d/ -f2 | sort -u
'''

[tasks."test:affected"]
description = "Test only changed packages"
run = '''
for pkg in $(mise run _changed-packages); do
  mise run "test:$pkg" || exit 1
done
'''
```

**Limitation:** this is direct-change only — it does **not** follow transitive dependencies. If `shared-types` changes, packages that import it won't be tested unless they also changed. Once that gap bites (or you pass ~10 packages), graduate to a build tool with a real dependency graph:

| Scale / shape | Tool | Why |
|---|---|---|
| < 10 packages | mise + git-diff task (above) | Minimal overhead |
| 10–50, Python-heavy | Pants (`pants --changed-since=origin/main`) | Native affected + dependency inference; coexists with mise |
| 50+ balanced polyglot | Bazel | Proven scale, remote execution |
| JS-only | Turborepo / Nx | Best JS tooling |

Keep mise for runtime versions + env even after adopting one of these — mise owns `[tools]`, the build tool owns the graph.

**When to use:** CI that should skip unaffected packages, or local pre-push checks scoped to what you touched.

## Cross-Project Task Sharing

Two patterns for sharing tasks across projects — choose based on your needs:

### Parent Directory Inheritance

mise walks up the directory tree automatically. Tasks in a parent config are available in all child projects:

```
workspace/.mise.toml          # defines auth:check, scan:all
└── project-a/.mise.toml      # defines build, test
    $ mise tasks              # shows BOTH parent and project tasks
└── project-b/.mise.toml
    $ mise tasks              # same parent tasks, different project tasks
```

**Use when:** Projects are co-located in a workspace directory and share operational tasks (auth, scanning, deployment).

### task_config.includes

Pull task files from a specific location — a directory entry now loads every `.toml` file *and* file-based task script inside it (mise ≥ ~2026.6.0; older versions only picked up file tasks from a directory, never `.toml` files — list them explicitly on those versions):

```toml
[task_config]
includes = [
  "../shared-tasks",              # directory: loads all .toml + file tasks inside
  "../shared-tasks/deploy.toml",  # or list a specific file
]
```

**Use when:** Task files live in a separate repo or non-parent directory checked out locally.

### git:: remote includes (new, experimental)

Pull tasks straight from a remote git repo, no local checkout needed:

```toml
[task_config]
includes = [
  "git::https://github.com/myorg/shared-tasks.git//tasks?ref=v1.0.0",
  ".mise/tasks",  # local tasks listed after — same-named local task wins (last entry wins)
]
```

**Use when:** Sharing tasks across repos you don't want to vendor or symlink — mise clones/caches the repo under `MISE_CACHE_DIR/remote-git-tasks-cache`. Pin `?ref=` to a tag/commit for reproducibility; omit it to track the default branch.

### Decision tree

1. Are projects in the same workspace? → Parent inheritance (simpler, automatic)
2. Are tasks in a separate repo you already have checked out? → `task_config.includes` with a directory or explicit file path
3. Are tasks in a repo you don't want to check out locally? → `git::` remote include
4. Need per-project task overrides? → Child config redefines the task (same name wins); with multiple includes, remember **last entry wins** for same-named tasks
5. Need tasks that reference project-local files? → Use `{{config_root}}` for portability — but note this only resolves inside inline TOML `run` blocks, not file-based task scripts (see `mise_config_guide.md`)
