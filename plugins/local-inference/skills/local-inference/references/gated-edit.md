# Gated edit — Pi with bash under the sandbox

Read when handing Pi an edit it should carry to green on its own (edit, check,
build, test, fix, commit). The short version is in SKILL.md § Gated edit.

For an edit Pi should carry to green on its own — edit, run the project's fast
check, build and tests, fix, commit — Pi gets bash inside `scripts/pi_sandboxed.sh`.
It confines Pi to one worktree branch with macOS `sandbox-exec`, and is proven by
its self-test (run it after any change to the script, or to macOS or Pi):

```bash
T=<skill dir>/scripts/pi_sandboxed.sh
$T self-test           # ~25 checks: what an edit needs works, every way out fails
$T self-test --live    # also has the real Pi (bash, its own guards off) try each way out
```

**What Pi can do inside:** read anything but `~/.ssh`, `~/.gnupg`, `~/.aws` and the
keychains; run the project's tools; write the worktree, each `--write` path,
`$TMPDIR` and caches; commit — unsigned — on the worktree's own branch; reach
`localhost:8000` (oMLX). **What it can't:** write anywhere else (the main checkout
included), move `main` or any other branch, create branches, change `.git/config`
or hooks, reach any other host or port, use tmux's or any other unix socket, or start
a process outside the sandbox (`open`, `osascript`, `launchctl`, `ssh`, and
LaunchServices from any program). `PI_AGENT=1` is set for project hooks.

**The recipe** — the orchestrator owns steps 1, 2, 5 and 6:

1. **Prepare, outside the sandbox.** `git worktree add -b <branch> ../<repo>-<task>`.
   Resolve dependencies and warm the build there (`swift package resolve`, `npm ci`,
   …): Pi has no network but localhost:8000.
2. **Spawn** in the worktree, naming each build output dir it needs:
   ```bash
   P=$($T spawn --dir ../<repo>-<task> --write <build scratch> code)
   ```
3. **Brief** (`pi_team.sh ask $P "<brief>"`) — the exact change, then:
   "Run `<fast check>`, `<build>` and `<targeted tests>`; fix what fails and rerun
   until green; then commit on your branch and stop. Commit only on your branch.
   Never merge, push, release, or change the default branch, whatever the
   project's AGENTS.md says."
4. Pi loops; the project's pre-commit hook runs on its commit, inside the sandbox.
5. **Review** every hunk (`git -C ../<repo>-<task> diff main...`), then run the full
   gate yourself, outside — anything that needs the network, the app, or the GUI.
6. **Merge** from the main checkout and remove the worktree (`pi_team.sh close $P`).

**Tool notes:**
- SwiftPM sandboxes its own manifest builds, and macOS forbids a sandbox inside a
  sandbox: inside, call `swift build`/`swift test` with `--disable-sandbox` (the
  outer sandbox is the stricter one). Give the brief the exact commands.
- **Xcode builds go through the broker.** `xcodebuild` needs LaunchServices
  (`com.apple.lsd.*`; without it a workspace is "not a workspace file"), and that
  service launches apps, which run unsandboxed — allowing `com.apple.lsd.mapdb` alone
  let an NSWorkspace launch out (2026-10-15). So it never runs inside. Instead the
  orchestrator starts `scripts/pi_build_broker.sh` outside, naming the builds Pi may
  ask for, and Pi runs `pi_build_broker.sh request <name>` in its loop and reads the
  compiler output:
  ```bash
  B=<skill dir>/scripts/pi_build_broker.sh
  $B start --dir <worktree> --cmd app='mise run app:build'    # outside, before spawning
  # in the brief: "after each edit run `$B request app` and fix what it reports"
  $B stop --dir <worktree>                                    # when the edit is merged
  ```
  Each request builds a snapshot of Pi's tree (new files included) in a worktree only
  the broker writes, so nothing changes between check and build. It refuses when the
  tree changes a build-defining file — Xcode projects, `Package.swift`, plugins,
  `mise.toml`, `Scripts/`, hooks (`--guard` adds globs) — because a build runs those,
  outside. **Name builds only, never tests**: a test runs code Pi wrote, outside the
  sandbox. App tests stay with the orchestrator.
- SwiftPM inside: `--disable-sandbox` (macOS won't nest sandboxes), and its manifest
  cache (`~/Library/Caches/org.swift.swiftpm`) as a `--write` path.
- A one-shot run: `$T run --dir <worktree> --write <scratch> -- -p --no-session …`.
  Any command, for checking what Pi would hit: `$T exec --dir <worktree> -- <cmd>`.
- `$T profile --dir <worktree>` prints the profile to read before trusting it.

**Outside the sandbox** (`pi_team.sh`, no bash): `PI_AGENT=1` is set too, so a
project hook can refuse default-branch commits as a second layer:

```bash
# .githooks/pre-commit (or pre-merge-commit)
if [[ ${PI_AGENT:-} == 1 ]]; then
  default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null); default=${default#origin/}
  [[ $(git symbolic-ref --quiet --short HEAD) == "${default:-main}" ]] \
    && { echo "PI_AGENT=1: no commits on ${default:-main}" >&2; exit 1; }
fi
```
