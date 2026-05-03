---
last_verified: 2026-05-03
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

Pull task files from a specific location:

```toml
[task_config]
includes = [
  "../shared-tasks/auth.toml",
  "../shared-tasks/deploy.toml",
]
```

**Use when:** Task files live in a separate repo or non-parent directory. Remember: must list files explicitly (directory globs silently fail).

### Decision tree

1. Are projects in the same workspace? → Parent inheritance (simpler, automatic)
2. Are tasks in a separate repo? → `task_config.includes` with explicit paths
3. Need per-project task overrides? → Child config redefines the task (same name wins)
4. Need tasks that reference project-local files? → Use `{{config_root}}` for portability
