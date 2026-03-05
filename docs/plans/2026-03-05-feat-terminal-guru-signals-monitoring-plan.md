---
title: "feat: Add signals-monitoring skill to terminal-guru"
type: feat
status: completed
date: 2026-03-05
origin: docs/brainstorms/2026-03-05-terminal-guru-macos-logging-brainstorm.md
supersedes: docs/plans/2026-03-05-feat-terminal-guru-macos-logging-plan.md
---

# feat: Add signals-monitoring skill to terminal-guru

## Overview

Add a new 3rd skill — `signals-monitoring` — to the terminal-guru plugin. This skill covers two closely paired terminal primitives: **Unix process signals** (sending, trapping, handling) and **system monitoring** (macOS unified logging, file watching, process inspection, and notifications). The two sides are naturally complementary: you monitor to detect events, and signals are how you respond to them.

This plan supersedes the narrower `macos-logging` plan from earlier today. The scope expanded during brainstorming to capture the fuller abstraction (see brainstorm: `docs/brainstorms/2026-03-05-terminal-guru-macos-logging-brainstorm.md`).

## Problem Statement

terminal-guru currently covers two domains: display issues (terminal-emulation) and shell development (zsh-dev). But users regularly encounter a third class of problems:

- "Why is my app doing this? Let me check the logs."
- "My script isn't cleaning up when I Ctrl+C it."
- "I want to watch for file changes and rebuild automatically."
- "How do I get notified when a long deployment finishes?"

These are observability and event-response problems — neither display nor shell config. Without a dedicated skill, the agent has no home to route these, and users get no structured guidance.

## Proposed Solution

New skill `signals-monitoring` with four domains, plus cross-cutting tmux integration:

```
plugins/terminal-guru/
  skills/
    terminal-emulation/          (existing — display, terminfo, unicode)
    zsh-dev/                     (existing — autoload, fpath, functions)
    signals-monitoring/          (NEW)
      SKILL.md
      references/
        macos_logging_guide.md   (log show/stream/collect, predicates, logger)
        signals_guide.md         (Unix signals, trap, kill, job control)
        file_watching_guide.md   (fswatch, entr, process monitoring)
        notifications_guide.md   (osascript, terminal-notifier)
      scripts/
        logwatch                 (zsh autoload function — tmux log stream pane)
  agents/terminal-guru.md        (MODIFIED — add signals-monitoring routing)
  .claude-plugin/plugin.json     (MODIFIED — add skill, update keywords)
  README.md                      (MODIFIED — add skill description)
```

## Domain Coverage

### Signals (`references/signals_guide.md`)

Unix signals every terminal user encounters:

| Signal | Number | Common use |
|--------|--------|------------|
| SIGINT | 2 | Ctrl+C — interrupt |
| SIGTERM | 15 | Graceful shutdown request |
| SIGKILL | 9 | Force kill (uncatchable) |
| SIGHUP | 1 | Terminal closed; reload config |
| SIGSTOP/CONT | 19/18 | Pause/resume (Ctrl+Z, `fg`) |
| SIGUSR1/2 | 30/31 | App-defined custom signals |
| SIGPIPE | 13 | Broken pipe in shell pipelines |

Key patterns to document:
- Sending: `kill -TERM <pid>`, `pkill -f name`, `killall App`
- `trap` for cleanup on EXIT, INT, TERM, HUP in scripts
- Long-running zsh function pattern with cleanup trap
- Daemon reload via SIGHUP (`kill -HUP $(pgrep nginx)`)
- SIGPIPE suppression in shell pipelines

### macOS Unified Logging (`references/macos_logging_guide.md`)

Reading logs (see brainstorm for full command map):
- `log show` — historical logs with `--last`, `--predicate`, `--style`
- `log stream` — real-time with `--predicate`, `--level`, `--timeout`
- `log collect` — snapshot to `.logarchive`, including paired iOS devices
- `log stats` — per-process/sender log volume analysis

Writing logs from shell:
- `logger -t <tag> -p user.info "message"` — writes into unified log
- `_log` helper wrapper for consistent tagging in zsh functions
- Retrieving: `log show --predicate 'process=="logger" and eventMessage contains "my-tag"'`

Predicate filtering (NSPredicate + shorthand):
- Keys: `subsystem`, `category`, `process`, `eventMessage`, `messageType`, `sender`
- Shorthand: `s=com.apple.sharing and c:airdrop and type=error`
- Compound: `(subsystem=="com.example") && (category IN {"net","auth"})`

> **Footnote — `log config`**: Enabling debug logging for a specific subsystem (`sudo log config --mode "level:debug" --subsystem com.myapp`) is useful during development but requires root and affects system-wide logging. Mentioned in references, not a top-level capability.

> **Future capability — `dtrace`/`dtruss`/`instruments` CLI**: The skill is aware these tools exist for deep system tracing. Not covered in v1 — noted in SKILL.md under "Advanced / Future" for discovery.

### File Watching (`references/file_watching_guide.md`)

- `fswatch -o <path> | xargs -n1 <cmd>` — run command on any change
- `ls src/**/*.swift | entr -c swift test` — re-run tests on source changes
- `pgrep`, `lsof -p <pid>`, `lsof -i :8080` — process inspection
- `top -pid <pid>` — per-process resource usage

### Notifications (`references/notifications_guide.md`)

Completes the monitor→alert loop (see brainstorm: decision #7).

Native (no dependencies):
```bash
osascript -e 'display notification "Build done" with title "Terminal" sound name "Glass"'
```

`terminal-notifier` (richer — `brew install terminal-notifier`):
```bash
terminal-notifier -title "Deploy" -message "Production live" -sound default
terminal-notifier -title "Watch" -message "File: $file" -group "file-watcher"
```

`notify_when_done` zsh function pattern — wraps any command, notifies on success/failure.

### Cross-Cutting: `logwatch` tmux Integration

The key integration pattern: open a tmux pane with a filtered `log stream` for live monitoring while working (see brainstorm: decision #2).

```zsh
# scripts/logwatch — installable zsh autoload function
logwatch() {
    local subsystem="${1:-}"
    local predicate="${2:-}"
    [[ -n "$subsystem" && -z "$predicate" ]] && predicate="subsystem==\"$subsystem\""
    local cmd="sudo log stream --level debug"
    [[ -n "$predicate" ]] && cmd+=" --predicate '$predicate'"
    if [[ -n "$TMUX" ]]; then
        tmux split-window -v "$cmd"
    else
        eval "$cmd"
    fi
}
```

Lives in **both** (see brainstorm: decision #2):
1. `signals-monitoring/scripts/logwatch` — documented in SKILL.md as a provided script
2. Installable as a zsh autoload function via `zsh-dev`'s `install_autoload.sh`

## Technical Considerations

**Agent routing update** — `agents/terminal-guru.md` needs new rows in the routing table:

| Symptom | Routes to |
|---|---|
| "check logs", "stream logs", "why is X doing Y" | signals-monitoring |
| "Ctrl+C not working", "trap SIGTERM", "graceful shutdown" | signals-monitoring |
| "watch files", "run on change", "trigger on save" | signals-monitoring |
| "notify me when done", "send a notification" | signals-monitoring |
| "kill a process", "send a signal" | signals-monitoring |

**Plugin.json** — update `keywords` to include `logging`, `signals`, `monitoring`, `notifications`, and update `description`.

**README.md** — add `signals-monitoring` component block following the existing pattern.

**zsh-dev cross-reference** — add a short "Logging from Zsh Functions" note to `references/zsh_function_patterns.md` pointing to signals-monitoring for `logger`/`_log` patterns.

**Skillsmith evaluation** — run after implementation, record score in IMPROVEMENT_PLAN.md.

## Implementation Phases

### Phase 1: Skill Scaffold + macOS Logging

*Core capability — the original trigger for this work.*

- [x] Create `skills/signals-monitoring/` directory structure
- [x] Write `SKILL.md` — overview, when-to-use, all 4 domains, `logwatch` usage, dtrace future note
- [x] Write `references/macos_logging_guide.md` — `log show/stream/collect/stats`, predicate reference (NSPredicate + shorthand), `logger` usage, `_log` helper pattern
- [x] Add `log config` footnote in logging guide
- [x] Update `plugin.json` keywords and description

### Phase 2: Signals Reference

- [x] Write `references/signals_guide.md` — signal table, `kill`/`pkill`/`killall`, `trap` patterns (EXIT cleanup, TERM/INT handler, HUP reload, PIPE suppress), long-running zsh function template with trap
- [x] Update agent routing table in `agents/terminal-guru.md`

### Phase 3: File Watching + Notifications

- [x] Write `references/file_watching_guide.md` — `fswatch`, `entr`, `pgrep`, `lsof` patterns
- [x] Write `references/notifications_guide.md` — `osascript` display notification, `terminal-notifier` (with `-group`, `-activate`), `notify_when_done` function pattern
- [x] Update `README.md` with signals-monitoring component block

### Phase 4: `logwatch` Function + Integration

- [x] Write `scripts/logwatch` as a complete zsh autoload function with subsystem and raw predicate modes, tmux-aware fallback
- [x] Add note to `zsh-dev/references/zsh_function_patterns.md` cross-referencing signals-monitoring for logging patterns
- [x] Run skillsmith evaluation: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/terminal-guru/skills/signals-monitoring`
- [x] Record eval score in `skills/signals-monitoring/IMPROVEMENT_PLAN.md` (create it)

## Acceptance Criteria

- [ ] `skills/signals-monitoring/SKILL.md` created and covers all 4 domains with clear when-to-use trigger phrases
- [ ] `references/macos_logging_guide.md` covers: `log show/stream/collect/stats`, predicate filtering (NSPredicate + shorthand keys), `logger` usage, `_log` helper, `log config` footnote
- [ ] `references/signals_guide.md` covers: signal table, sending signals, `trap` patterns (EXIT, TERM, INT, HUP, PIPE), long-running function template
- [ ] `references/file_watching_guide.md` covers: `fswatch`, `entr`, `pgrep`, `lsof`
- [ ] `references/notifications_guide.md` covers: `osascript` notification, `terminal-notifier`, `notify_when_done` pattern
- [ ] `scripts/logwatch` is a working zsh autoload function, tmux-aware, installable via `install_autoload.sh`
- [ ] `agents/terminal-guru.md` updated with signals-monitoring routing rows
- [ ] `plugin.json` updated with new keywords and description
- [ ] `README.md` updated with signals-monitoring component
- [ ] `zsh-dev` references cross-link to signals-monitoring for logger patterns
- [ ] dtrace/dtruss noted as future capability in SKILL.md
- [ ] Skillsmith eval run and score recorded in IMPROVEMENT_PLAN.md

## Dependencies & Risks

- **`terminal-notifier`** is a Homebrew package — not pre-installed. Document as optional; always cover native `osascript` fallback first.
- **`fswatch`/`entr`** are also Homebrew packages — same pattern: document as installable, show native alternatives where possible.
- **`log` commands often require `sudo`** — note this consistently in examples. Non-root `log show` only shows process-owned logs.
- **Agent routing** — adding signals-monitoring requires careful ordering so it doesn't accidentally swallow zsh-dev or terminal-emulation queries. Review the routing table holistically before committing.

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-05-terminal-guru-macos-logging-brainstorm.md](docs/brainstorms/2026-03-05-terminal-guru-macos-logging-brainstorm.md)
  Key decisions carried forward: new `signals-monitoring` skill (not split), `logwatch` in both scripts/ and as zsh autoload, macOS notifications in scope, dtrace as future capability

### Internal References

- Existing skill pattern: `plugins/terminal-guru/skills/terminal-emulation/SKILL.md`
- Existing reference pattern: `plugins/terminal-guru/skills/terminal-emulation/references/terminfo_guide.md`
- Agent routing structure: `plugins/terminal-guru/agents/terminal-guru.md:53`
- Install helper: `plugins/terminal-guru/skills/zsh-dev/scripts/install_autoload.sh`
- Function patterns to cross-reference: `plugins/terminal-guru/skills/zsh-dev/references/zsh_function_patterns.md`

### External References

- macOS log command guide: https://the-sequence.com/mac-logging-and-the-log-command-a-guide-for-apple-admins
- `man log` (macOS 26.3) — predicate filtering, all subcommands
- `man logger` (macOS 26.3) — BSD syslog interface
- Apple Predicate Programming Guide: https://developer.apple.com/library/mac/documentation/Cocoa/Conceptual/Predicates/Articles/pSyntax.html
