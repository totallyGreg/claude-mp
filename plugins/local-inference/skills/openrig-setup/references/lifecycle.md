# Rig lifecycle and committing the setup

Checked against OpenRig 0.5.17 on 2026-10-02 (full stop and `rig start --last`
of a Claude lead + native Pi rig).

## Shut down and restart

```bash
rig down <your-rig> --snapshot          # each of your rigs — never `rig down kernel`
cd ~ && rig daemon stop
cd ~ && rig start --last                # daemon + kernel + rigs that were running
```

- `kernel` is OpenRig's own rig (advisor, operator, queue worker); the daemon
  boots it. Stop it yourself and it counts as deliberately stopped: neither
  `--last` nor `--rigs kernel` restores it — `rig up kernel --existing` does.
- `rig daemon stop` may report "incomplete shutdown: timed-out;
  phase=connections"; harmless when the PID is gone and the restart is healthy.
- Seats come back `resumed`: the Claude conversation and the native Pi session
  file both continue. The lead's permission mode doesn't — OpenRig re-applies
  `acceptEdits` each boot, so auto mode has to be switched on again. Restore
  doesn't re-merge guidance; the resumed session already holds the brief.

## Committing the setup

Commit `AGENTS.md`, the `CLAUDE.md` symlink and
`openrig-specs/` to a branch and base the coder worktrees on it, so they get
the instructions and specs too. The scaffold writes `openrig-specs/.gitignore`
for the files OpenRig regenerates. A native Pi seat merges OpenRig's blocks
into a tracked `AGENTS.md` in its worktree; the scaffold marks it
`git update-index --skip-worktree` there (per-worktree index), so the lead's
diffs stay clean. A new worktree's submodules aren't checked out —
`git -C <worktree> submodule update --init --recursive` before building.
