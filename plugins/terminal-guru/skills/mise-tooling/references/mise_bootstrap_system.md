---
last_verified: 2026-07-03
sources:
  - type: web
    url: "https://mise.jdx.dev/bootstrap.html"
    description: "Official mise bootstrap documentation"
  - type: github
    repo: "jdx/mise"
    paths: ["docs/bootstrap/"]
    description: "mise documentation source for declarative machine bootstrap"
---

# Mise Bootstrap (Declarative Machine Setup)

<!-- Badge: experimental as of mise 2026.7.0 -->

`mise bootstrap` is a newer (still experimental) mise capability, separate from `[tools]`/tasks/env: it declaratively provisions a **machine or workstation** — system packages, git repos, dotfiles, shell activation, macOS defaults/LaunchAgents, Linux systemd user units, and the user's login shell — before a project is even opened. Everything under `[bootstrap.*]` is manual/idempotent: nothing runs on its own, only via `mise bootstrap` or its per-part `apply` subcommands.

**When to reach for it vs `[tools]`:** `[tools]` is per-project, version-pinned, gets shims. `[bootstrap.packages]` is machine-global, not version-pinned, no shims — native libraries, build deps, GUI apps (`libssl-dev`, `postgresql`, `firefox`), not project dev tools.

## The sequence

`mise bootstrap` runs, in order:

1. `mise bootstrap packages apply` — installs missing `[bootstrap.packages]`
2. `mise bootstrap repos apply` — clones/updates `[bootstrap.repos]`
3. `mise bootstrap dotfiles apply` — applies `[dotfiles]`
4. `mise bootstrap mise-shell-activate apply` — shell activation from `[bootstrap.mise_shell_activate]`
5. `mise bootstrap macos defaults apply` — `[bootstrap.macos.defaults]` (macOS only)
6. `mise bootstrap macos launchd-agents apply` — `[bootstrap.macos.launchd.agents]` (macOS only)
7. `mise bootstrap linux systemd-units apply` — `[bootstrap.linux.systemd.units]` (Linux only)
8. `mise bootstrap user apply` — `[bootstrap.user]` (e.g. login shell)
9. `mise install` — installs missing `[tools]`
10. `mise run bootstrap` — runs a task literally named `bootstrap`, if one exists
11. `[bootstrap.hooks.final]` — runs after the bootstrap task

Skip or scope parts: `mise bootstrap --skip packages,repos` / `mise bootstrap --only dotfiles,tools` (mutually exclusive). Hook phases also exist around each step: `pre-packages`, `post-packages`, `pre-repos`, `post-repos`, `pre-dotfiles`, `post-dotfiles`, `pre-defaults`, `post-defaults`, `pre-user`, `post-user`, `pre-tools`, `post-tools`.

Every declarative step **converges**: already-installed packages, repos at the right ref, matching dotfiles, or already-set defaults are skipped. The `bootstrap` task (step 10) runs every time — keep it idempotent yourself.

## `[bootstrap.packages]` — cross-distro package managers

```toml
[bootstrap.packages]
"apk:build-base" = "latest"        # Alpine
"apt:libssl-dev" = "latest"        # Debian/Ubuntu
"dnf:gcc" = "latest"               # Fedora/RHEL/CentOS/Rocky/Alma
"pacman:base-devel" = "latest"     # Arch/Manjaro
"brew:postgresql@17" = "latest"    # macOS + Linux, no Homebrew required
"brew-cask:firefox" = "latest"     # macOS, no Homebrew required
"mas:497799835" = "latest"         # macOS App Store, requires `mas` CLI on PATH
```

Key format is `"manager:package"` — the manager prefix is required. `brew`/`brew-cask` use mise's own built-in Homebrew installer (you don't need Homebrew itself present).

## `[bootstrap.repos]` — declarative git clones

```toml
[bootstrap.repos]
"~/src/dotfiles" = { url = "git@github.com:jdx/dotfiles.git", ref = "main" }
"~/src/mise"     = { url = "https://github.com/jdx/mise.git" }
```

Runs after packages, before dotfiles — so a bootstrap config can install `git`, clone dotfiles, then apply them. Safe-updates-only: clones missing repos or empty targets, updates existing repos only when the worktree is clean and `origin` matches. Dirty repos or mismatched origins fail loudly rather than overwriting local work — no forced resets.

## `[bootstrap.user]` — login shell

```toml
[bootstrap.user]
login_shell = "/bin/zsh"
```

If the shell isn't in `/etc/shells`, mise appends it first, then runs `chsh -s /bin/zsh` if it differs from the account's current shell. "Most local wins" (unlike package/repo lists which merge, this is a single desired value overridden by the most specific config).

## macOS-specific: defaults + LaunchAgents

```toml
[bootstrap.macos.dock]
autohide = true
tilesize = 48

[bootstrap.macos.finder]
show_all_files = true

[bootstrap.macos.defaults]
"com.apple.finder" = { AppleShowAllFiles = true }   # raw domain/key escape hatch
```

Curated sections (`[bootstrap.macos.dock]`, `.finder`, `.keyboard`, `.trackpad`, etc.) compile down to raw `defaults write` entries; `[bootstrap.macos.defaults]` is the raw escape hatch for anything not covered by a friendly section. Raw entries in the same file override friendly-section-generated entries for the same domain/key; normal global→local config precedence still applies across files.

LaunchAgents (`[bootstrap.macos.launchd.agents]`) are written and loaded by `mise bootstrap macos launchd-agents apply` — same declarative/idempotent model.

## Linux-specific: systemd user units

`[bootstrap.linux.systemd.units]`, applied by `mise bootstrap linux systemd-units apply` — converges by writing unit files and enabling/disabling + starting/stopping them per config, mirroring the macOS LaunchAgents model for the Linux side.

## Relationship to `[dotfiles]` and `[tools]`

- `[dotfiles]` (see `mise dotfiles` commands) is applied at step 3, between repos and shell activation — typically pointed at a repo cloned in step 2.
- `[tools]` installs (step 9) happen *after* all the machine-level bootstrap steps, so a freshly bootstrapped machine has its package managers, dotfiles, and shell ready before mise starts installing project tool versions.

## Gotcha

This whole feature is marked experimental as of mise 2026.7.0 — expect config shape to still shift. Don't build critical automation on top of `[bootstrap.*]` without pinning a mise version.
