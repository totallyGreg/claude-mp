---
title: "fix: weekly-review-collect.sh sets wrong CWD, breaking all gtd-queries.js library loads"
type: fix
date: 2026-03-01
---

# fix: weekly-review-collect.sh sets wrong CWD, breaking all gtd-queries.js library loads

## Problem Statement

All 5 parallel OmniFocus queries in `/weekly-review` fail with:

```
TypeError: undefined is not an object (evaluating 'taskQuery.getInboxTasks')
```

## Root Cause

`weekly-review-collect.sh` (line 19) `cd`s into the `scripts/` directory before invoking `gtd-queries.js`:

```bash
# weekly-review-collect.sh:17-19
# cd to scripts dir so JXA library loading (relative to CWD) works correctly
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPTS_DIR"   # ← CWD = .../skills/omnifocus-manager/scripts/
```

But `gtd-queries.js` loads `taskQuery.js` using a path that assumes CWD is the **skill root** (`skills/omnifocus-manager/`), not `scripts/`:

```javascript
// gtd-queries.js:47 — comment says exactly this:
// Run commands from the skills/omnifocus-manager/ root so paths resolve correctly.

const taskQuery = loadLibrary('scripts/libraries/jxa/taskQuery.js');
//                             ^^^^^^^
//    "scripts/" prefix is relative to skills/omnifocus-manager/
//    When CWD is already scripts/, this resolves to:
//    .../scripts/scripts/libraries/jxa/taskQuery.js  ← doesn't exist
```

`$.NSFileManager` returns `null` for the missing file. `eval(null.js)` → `undefined`. `taskQuery` is `undefined`. Every `taskQuery.getXxx()` call throws.

The comment in the shell script is incorrect — it's the source of the bug.

## Fix

Two-line change in `weekly-review-collect.sh`:

**`weekly-review-collect.sh`**

```bash
# BEFORE:
# cd to scripts dir so JXA library loading (relative to CWD) works correctly
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPTS_DIR"

osascript -l JavaScript gtd-queries.js --action inbox-count      > "$TMP/inbox.json"     2>&1 &
osascript -l JavaScript gtd-queries.js --action overdue          > "$TMP/overdue.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action waiting-for      > "$TMP/waiting.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action stalled-projects > "$TMP/stalled.json"   2>&1 &
osascript -l JavaScript gtd-queries.js --action recently-completed --days 7 \
                                                                 > "$TMP/completed.json" 2>&1 &

# AFTER:
# cd to skill root (parent of scripts/) so gtd-queries.js library paths resolve correctly
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPTS_DIR")"

osascript -l JavaScript scripts/gtd-queries.js --action inbox-count      > "$TMP/inbox.json"     2>&1 &
osascript -l JavaScript scripts/gtd-queries.js --action overdue          > "$TMP/overdue.json"   2>&1 &
osascript -l JavaScript scripts/gtd-queries.js --action waiting-for      > "$TMP/waiting.json"   2>&1 &
osascript -l JavaScript scripts/gtd-queries.js --action stalled-projects > "$TMP/stalled.json"   2>&1 &
osascript -l JavaScript scripts/gtd-queries.js --action recently-completed --days 7 \
                                                                          > "$TMP/completed.json" 2>&1 &
```

Changes:
1. `cd "$SCRIPTS_DIR"` → `cd "$(dirname "$SCRIPTS_DIR")"` — CWD is now `skills/omnifocus-manager/`
2. `gtd-queries.js` → `scripts/gtd-queries.js` in each `osascript` call — script path updated to match new CWD

No changes to `gtd-queries.js` or any JXA library are needed.

## Acceptance Criteria

### Immediate fix

- [x] `bash skills/omnifocus-manager/scripts/weekly-review-collect.sh` returns valid JSON with all 5 keys (`inbox`, `overdue`, `waitingFor`, `recentlyCompleted`, `stalledProjects`)
- [ ] Each key has `"success": true` (requires OmniFocus running — verify manually)
- [ ] `/weekly-review` command produces a complete GTD report with real OmniFocus data

### Harden against recurrence

**Standardize `loadLibrary` to self-locating pattern in `gtd-queries.js`**

`manage_omnifocus.js` already uses a CWD-independent pattern that derives the script's own directory from `$.getenv('_')`. `gtd-queries.js` should use the same pattern so no shell caller can break it:

```javascript
// gtd-queries.js — replace CWD-based loadLibrary with self-locating version
function loadLibrary(filename) {
    const scriptDir = $.NSString.alloc.initWithUTF8String($.getenv('_'))
        .stringByDeletingLastPathComponent.js;
    const libPath = `${scriptDir}/libraries/jxa/${filename}`;
    try {
        const content = $.NSString.alloc.initWithContentsOfFileEncodingError(
            libPath, $.NSUTF8StringEncoding, null
        );
        if (!content) throw new Error(`Library not found: ${libPath}`);
        return eval(content.js);
    } catch (error) {
        throw new Error(`Failed to load library ${filename}: ${error.message}`);
    }
}

// Call with filename only — no path prefix needed
const taskQuery = loadLibrary('taskQuery.js');
```

- [x] `gtd-queries.js` `loadLibrary` is consistent with `manage_omnifocus.js` (CWD-relative from skill root)
- [x] all 4 JXA libraries load successfully when CWD = skill root (verified by test-queries.sh library phase)

**Add script conventions to `jxa_guide.md`**

Add a **Script Conventions** section to `references/jxa_guide.md` establishing the canonical `loadLibrary` pattern, so future scripts have a clear template to copy:

- [x] `jxa_guide.md` § 7 documents the canonical CWD-relative `loadLibrary` pattern
- [x] `jxa_guide.md` § 7 documents the wrong-CWD shell caller as the anti-pattern

**Add script conventions to SKILL.md**

Add a short **Script Conventions** section to SKILL.md so Claude sees the contract when generating new scripts:

```markdown
## Script Conventions
- All JXA scripts use `$.getenv('_')` for self-locating library paths (CWD-independent)
- Shell wrappers `cd` to the skill root, not `scripts/`, when invoking JXA scripts
- Commands reference scripts via `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/`
```

- [x] SKILL.md has a Script Conventions section with the above rules

**Add smoke test**

Add `scripts/test-queries.sh` — runs one action from each JXA entry-point script and asserts `"success": true`. Run before bumping version:

- [x] `scripts/test-queries.sh` exists and validates library loads + live queries
- [x] `test-queries.sh` is referenced in SKILL.md Script Conventions and jxa_guide.md § 7

### Release

- [x] Bump to v5.5.0 in `plugin.json` and `IMPROVEMENT_PLAN.md` (hardening warrants minor bump)

## Context

- Plugin: `omnifocus-manager` v5.4.3
- Script: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/weekly-review-collect.sh:19`
- `gtd-queries.js` comment at line 47 already documents the correct CWD requirement — the shell script just violated it
- `manage_omnifocus.js` works correctly because it is invoked from the skill root by the omnifocus-manager skill, not via this shell script

## References

- Shell script: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/weekly-review-collect.sh:17-19`
- JXA script: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/gtd-queries.js:47-63`
- Library: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js`
- Brainstorm: `docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md`
