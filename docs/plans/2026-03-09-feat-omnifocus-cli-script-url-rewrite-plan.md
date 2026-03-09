---
title: "OmniFocus CLI via Omni Automation Script URLs"
type: feat
status: active
date: 2026-03-09
origin: docs/brainstorms/2026-03-09-omnifocus-cli-rewrite-brainstorm.md
---

# feat: OmniFocus CLI via Omni Automation Script URLs

## Overview

Replace the omnifocus-manager skill's JXA/osascript execution model with a thin `ofo` CLI wrapper that sends Omni Automation JavaScript directly to OmniFocus via `omnifocus://localhost/omnijs-run?script=<stable>&arg=<dynamic>` URLs. This eliminates JXA permissions errors, removes verbose invocation patterns, and provides an `obsidian`-CLI-like ergonomic interface for task management.

(see brainstorm: docs/brainstorms/2026-03-09-omnifocus-cli-rewrite-brainstorm.md)

## Problem Statement / Motivation

Four problems with the current JXA-based approach (see brainstorm: "Problems This Solves"):

1. **Task completion fails** -- `complete` command errors with "Access not allowed"; `update --completed true` reports success but doesn't change state. Root cause: JXA's `task.completed = true` assignment fails through the Apple Events bridge.
2. **Skill/script command drift** -- `ofo-info.md` references `task-info` but the actual command is `info`.
3. **Verbose invocation** -- Every command requires `cd <plugin-root> && osascript -l JavaScript scripts/manage_omnifocus.js <action> --flags`.
4. **No native URL handling** -- `omnifocus:///task/<id>` URLs require manual parsing in each slash command.

## Proposed Solution

A shell script `ofo` that:
1. Stores 6 stable Omni Automation JavaScript action scripts
2. Constructs `omnifocus://localhost/omnijs-run?script=<encoded-script>&arg=<encoded-json>` URLs
3. Invokes via `open` (sends to running OmniFocus)
4. Reads results from `Pasteboard.general.string` via `pbpaste`
5. Outputs JSON to stdout for Claude Code to parse

### Spike Validation (2026-03-09)

All three feasibility gates confirmed working (see brainstorm: "Prototype Spike Results"):

| Gate | Result | API |
|------|--------|-----|
| Find task by ID | PASS | `flattenedTasks.find(t => t.id.primaryKey === id)` |
| Mark complete | PASS | `task.markComplete()` -- full permissions, no JXA errors |
| Return data | PASS | `Pasteboard.general.string = JSON.stringify(result)` |
| File I/O | FAIL | OmniFocus sandboxed -- pasteboard is the only return path |

## Technical Approach

### Architecture

```
Claude Code slash command (e.g. /ofo:info)
  -> ofo info <id>
  -> ofo script reads stable JS from scripts/omni-actions/<action>.js
  -> URL-encodes script, JSON-encodes argument
  -> open "omnifocus://localhost/omnijs-run?script=<encoded>&arg=<encoded>"
  -> OmniFocus executes JS natively (full API access)
  -> Script writes JSON to Pasteboard.general.string
  -> ofo reads pbpaste, outputs to stdout
  -> Claude formats and presents to user
```

### Key Technical Decisions

1. **Pasteboard-only return** -- OmniFocus is sandboxed; `FileWrapper.write()` fails on `/tmp/`. All results go through `Pasteboard.general.string` -> `pbpaste`. (see brainstorm: Resolved Question 5)
2. **Stable script + variable argument** -- Each action script is a fixed JS file approved once in OmniFocus. The `&arg=` parameter carries per-invocation data (task IDs, filters, etc.) without triggering re-approval. (see brainstorm: Key Decision 2)
3. **Task lookup by `.find()`** -- `flattenedTasks.byIdentifier()` is NOT available despite being documented. Use `flattenedTasks.find(t => t.id.primaryKey === id)`. (see brainstorm: Resolved Question 3)
4. **`markComplete()` method** -- Not property assignment. `task.markComplete()` works; `task.completed = true` does not. (see brainstorm: Resolved Question 4)
5. **Standalone CLI** -- No dependency on Attache or other plugins. Shared patterns may emerge but the CLI works independently. (see brainstorm: Resolved Question 1)

### Implementation Phases

#### Phase 1: Core CLI + Action Scripts

Create the `ofo` shell wrapper and 6 action scripts.

**Files to create:**

- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ofo` -- Main CLI shell script
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-info.js` -- Task/project info
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-complete.js` -- Mark complete
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-update.js` -- Update properties
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-search.js` -- Search tasks
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-list.js` -- List tasks (inbox/flagged/today)
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/omni-actions/ofo-create.js` -- Create task

**`ofo` CLI interface:**

```bash
ofo info <id-or-omnifocus-url>       # Task/project details as JSON
ofo complete <id-or-omnifocus-url>   # Mark task complete
ofo create --name "Task" [--project "P"] [--tags "t1,t2"] [--due YYYY-MM-DD]
ofo update <id> [--name "New"] [--due YYYY-MM-DD] [--flagged]
ofo search <query>                   # Search by name/note
ofo list <filter>                    # inbox | flagged | today
ofo setup                            # Trigger approval for all action scripts
ofo help                             # Show usage
```

**URL parsing:** All commands accepting `<id>` also accept `omnifocus:///task/<id>` or `omnifocus:///project/<id>`, extracting the ID automatically.

**Action script structure** (each `.js` file):

```javascript
// ofo-info.js -- stable script body, approved once
// argument is passed via &arg= parameter as JSON
var args = argument;
var t = flattenedTasks.find(function(task) {
  return task.id.primaryKey === args.id;
});
if (t) {
  Pasteboard.general.string = JSON.stringify({
    success: true,
    task: {
      id: t.id.primaryKey,
      name: t.name,
      completed: t.completed,
      flagged: t.flagged,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      deferDate: t.deferDate ? t.deferDate.toISOString() : null,
      note: t.note,
      project: t.containingProject ? t.containingProject.name : null,
      tags: t.tags.map(function(tag) { return tag.name; }),
      estimatedMinutes: t.estimatedMinutes
    }
  });
} else {
  Pasteboard.general.string = JSON.stringify({
    success: false, error: "Task not found: " + args.id
  });
}
```

**`ofo` shell script core logic:**

```bash
#!/usr/bin/env bash
# ofo -- OmniFocus CLI via Omni Automation script URLs

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIONS_DIR="${SCRIPTS_DIR}/omni-actions"

parse_omnifocus_url() {
  local input="$1"
  if [[ "$input" == omnifocus:///* ]]; then
    echo "$input" | sed -E 's|omnifocus:///[a-z]+/||'
  else
    echo "$input"
  fi
}

run_action() {
  local action="$1"
  local arg_json="$2"
  local script
  script=$(<"${ACTIONS_DIR}/${action}.js")
  local encoded_script encoded_arg
  encoded_script=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.stdin.read()))" <<< "$script")
  encoded_arg=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.stdin.read()))" <<< "$arg_json")
  # Clear pasteboard sentinel
  echo "__ofo_pending__" | pbcopy
  open "omnifocus://localhost/omnijs-run?script=${encoded_script}&arg=${encoded_arg}"
  # Poll for result (pasteboard changes from sentinel)
  local max_attempts=50  # 50 * 0.2s = 10 second timeout
  local attempt=0
  while [ $attempt -lt $max_attempts ]; do
    sleep 0.2
    local result
    result=$(pbpaste)
    if [ "$result" != "__ofo_pending__" ]; then
      echo "$result"
      return 0
    fi
    attempt=$((attempt + 1))
  done
  echo '{"success":false,"error":"Timeout waiting for OmniFocus response"}'
  return 1
}
```

**Timing mechanism:** Write a sentinel value to pasteboard before sending the URL, then poll until pasteboard changes. This resolves Open Question 1 from the brainstorm.

**Large result sets:** Action scripts that return lists (`ofo-list`, `ofo-search`) will filter server-side and limit results (e.g., max 100 tasks). This resolves Open Question 4 from the brainstorm.

##### Phase 1 Deliverables

- [x] `ofo` shell script with command routing, URL parsing, pasteboard polling
- [x] `omni-actions/ofo-info.js` -- task and project info (detect type from argument)
- [x] `omni-actions/ofo-complete.js` -- `markComplete()` with success confirmation
- [x] `omni-actions/ofo-create.js` -- create task with name, project, tags, due, note
- [x] `omni-actions/ofo-update.js` -- update name, due, defer, flagged, note, tags
- [x] `omni-actions/ofo-search.js` -- search by name/note substring, limit 50
- [x] `omni-actions/ofo-list.js` -- filter by inbox/flagged/today/overdue, limit 100
- [x] `ofo setup` command that sends each action script once to trigger approval dialogs
- [x] Smoke test: `ofo info <known-id>` returns valid JSON

#### Phase 2: Slash Command Migration

Update existing slash commands to use `ofo` instead of `osascript`.

**Files to modify:**

- `plugins/omnifocus-manager/commands/ofo-info.md` -- Replace `osascript -l JavaScript scripts/manage_omnifocus.js task-info` with `ofo info`
- `plugins/omnifocus-manager/commands/ofo-today.md` -- Replace JXA invocation with `ofo list today`
- `plugins/omnifocus-manager/commands/ofo-inbox.md` -- Replace with `ofo list inbox`
- `plugins/omnifocus-manager/commands/ofo-search.md` -- Replace with `ofo search`
- `plugins/omnifocus-manager/commands/ofo-health.md` -- Replace with `ofo list` calls
- `plugins/omnifocus-manager/commands/ofo-overdue.md` -- Replace with `ofo list overdue`
- `plugins/omnifocus-manager/hooks/omnifocus-task-sync.sh` -- Replace JXA `complete` call with `ofo complete`
- `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md` -- Update script invocation patterns

**`allowed-tools` update:** Commands currently restrict to `Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)`. The `ofo` script lives in this path, so no change needed.

##### Phase 2 Deliverables

- [x] All 6 `ofo:` slash commands updated to use `ofo` CLI
- [x] `omnifocus-task-sync.sh` hook updated to use `ofo complete`
- [x] SKILL.md updated with new invocation patterns
- [x] Verify each command works end-to-end

#### Phase 3: Documentation + Skill Quality

- [ ] Update `references/omnifocus_url_scheme.md` with script URL findings from spike
- [ ] Update `references/channel_selection.md` -- script URLs are now viable with `&arg=` pattern
- [ ] Add `references/omni_automation_api_mapping.md` -- JXA vs Omni Automation API mapping table from spike
- [ ] Update IMPROVEMENT_PLAN.md with version entry and eval score
- [ ] Run skillsmith evaluation: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager`
- [ ] Decide migration path for existing JXA scripts (keep as fallback or deprecate)

## Acceptance Criteria

### Functional Requirements

- [ ] `ofo info <id>` returns JSON with task name, status, project, tags, dates
- [ ] `ofo info omnifocus:///task/<id>` parses URL and returns same result
- [ ] `ofo complete <id>` actually marks the task complete (verified by `ofo info`)
- [ ] `ofo create --name "Test"` creates a task and returns its ID
- [ ] `ofo search <query>` returns matching tasks
- [ ] `ofo list inbox` returns inbox tasks
- [ ] `ofo list today` returns today's flagged + due tasks
- [ ] `ofo setup` triggers approval for all 6 action scripts
- [ ] All existing `/ofo:*` slash commands work with the new CLI backend

### Non-Functional Requirements

- [ ] Response time < 2 seconds for single-task operations (after initial approval)
- [ ] Pasteboard polling timeout prevents hanging
- [ ] Graceful error when OmniFocus is not running
- [ ] JSON output parseable by Claude Code

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Script approval friction on first use | `ofo setup` command batches all approvals. Document in SKILL.md. |
| Pasteboard clobber during concurrent use | Sentinel-based polling detects stale results. Accept as trade-off. |
| OmniFocus not running | Check `pgrep -x OmniFocus` before sending URL. Clear error message. |
| Large result sets exceed pasteboard limits | Server-side filtering and result limits (50-100 tasks). |
| `flattenedTasks.find()` performance on 1800+ tasks | Linear scan is fast for JS arrays. Monitor and optimize only if needed. |

## Open Questions (from brainstorm, addressed in plan)

1. **Timing** -- Resolved: sentinel-based pasteboard polling with 10-second timeout.
2. **Migration path** -- Addressed in Phase 3: decide during implementation based on stability.
3. **CLI installation** -- The script lives in `scripts/ofo` within the plugin. Claude Code accesses it via `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo`. No PATH installation needed for skill use; optional symlink for terminal use.
4. **Large result sets** -- Resolved: server-side filtering with configurable limits.

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-09-omnifocus-cli-rewrite-brainstorm.md](docs/brainstorms/2026-03-09-omnifocus-cli-rewrite-brainstorm.md) -- Key decisions carried forward: script URL architecture with `&arg=` reuse pattern, pasteboard-only return mechanism, core CRUD scope (~8 commands)

### Internal References

- Channel selection framework: `plugins/omnifocus-manager/skills/omnifocus-manager/references/channel_selection.md`
- URL scheme docs: `plugins/omnifocus-manager/skills/omnifocus-manager/references/omnifocus_url_scheme.md:246-272`
- API reference (Omni Automation): `plugins/omnifocus-manager/skills/omnifocus-manager/references/api_reference.md`
- Existing JXA script: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/manage_omnifocus.js`
- Existing shell wrapper pattern: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/weekly-review-collect.sh`
- Hook pattern: `plugins/omnifocus-manager/hooks/omnifocus-task-sync.sh`
- Plugin architecture lessons: `docs/lessons/plugin-integration-and-architecture.md`

### External References

- Omni Automation script URL docs: `https://omni-automation.com/script-url/index.html`
- OmniFocus Omni Automation reference: `https://omni-automation.com/omnifocus/index.html`
