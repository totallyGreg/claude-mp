---
title: "refactor: Unify omnifocus-manager CLI with single library source"
type: refactor
date: 2026-03-01
---

# refactor: Unify omnifocus-manager CLI with single library source

## Overview

Make `taskQuery.js` the single source of truth for all query logic. Refactor
`manage_omnifocus.js` to load and delegate to the JXA libraries instead of duplicating
their logic inline. Delete `omnifocus.js` once its `loadLibrary()` pattern is adopted.

**Context:** `omnifocus.js` already demonstrated the correct pattern for loading JXA libraries
via `eval()`. `manage_omnifocus.js` was built as a monolith and duplicates `formatTaskInfo`,
`parseDate`, `parseEstimate`, and all query functions from the library. When OmniFocus API
changes (e.g., PlannedDates), both files need updating — violating DRY.

**Current state:** v5.1.0 — `overdue` added, `gtd-queries.js` uses library correctly.
`manage_omnifocus.js` still has ~200 lines of duplicated library code.

## Problem Statement

`manage_omnifocus.js` (811 lines) duplicates the following from the JXA libraries:

| Inline function | Duplicates from |
|----------------|-----------------|
| `formatTaskInfo()` | `taskQuery.formatTaskInfo()` |
| `parseArgs()` | `argParser.parseArgs()` |
| `parseDate()` | `dateUtils.parseDate()` |
| `parseEstimate()` | `dateUtils.parseEstimate()` |
| `getTodayTasks()` | `taskQuery.getTodayTasks()` |
| `getDueSoon()` | `taskQuery.getDueSoon()` |
| `getOverdue()` | `taskQuery.getOverdueTasks()` |
| `getFlagged()` | `taskQuery.getFlagged()` |
| `listTasks()` | `taskQuery.listTasks()` |
| `getTaskInfo()` | `taskQuery.getTaskInfo()` |
| `searchTasks()` | `taskQuery.searchTasks()` |

Adding PlannedDates (or any new OmniFocus property) today requires editing both
`taskQuery.js` and `manage_omnifocus.js`. This will keep happening.

## Proposed Solution

1. Add `loadLibrary()` to `manage_omnifocus.js` (copy pattern from `omnifocus.js`)
2. Load `taskQuery`, `taskMutation`, `argParser`, `dateUtils` at startup
3. Replace each duplicated inline function with a thin wrapper that delegates to the library
4. Delete `omnifocus.js` — its only value was the library pattern, which now lives in `manage_omnifocus.js`
5. Update SKILL.md help text to confirm `manage_omnifocus.js` is canonical

## Technical Approach

### The `loadLibrary()` Pattern (from `omnifocus.js`)

```javascript
// scripts/manage_omnifocus.js — add after ObjC imports
ObjC.import('stdlib');
ObjC.import('Foundation');

function loadLibrary(filename) {
    const scriptDir = $.NSString.alloc.initWithUTF8String($.getenv('_'))
        .stringByDeletingLastPathComponent.js;
    const libPath = `${scriptDir}/../libraries/jxa/${filename}`;
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

// Load once at startup
const taskQuery    = loadLibrary('taskQuery.js');
const taskMutation = loadLibrary('taskMutation.js');
const argParser    = loadLibrary('argParser.js');
const dateUtils    = loadLibrary('dateUtils.js');
```

### Query Function Conversion Pattern

Each query function becomes a thin wrapper. Example:

```javascript
// BEFORE (inline, duplicated):
function getTodayTasks(app, args) {
    const doc = app.defaultDocument;
    const tasks = doc.flattenedTasks();
    // ... 25 lines of duplicated logic ...
}

// AFTER (thin wrapper):
function getTodayTasks(app, args) {
    const doc = app.defaultDocument;
    const tasks = taskQuery.getTodayTasks(doc);
    return JSON.stringify({ success: true, count: tasks.length, tasks });
}
```

**⚠️ `this` binding:** `taskQuery` methods call `this.formatTaskInfo()` internally.
Always call as `taskQuery.getTodayTasks(doc)` — never destructure the method off the object.

### Mutation Functions

Check `taskMutation.js` to see if `createTask`, `updateTask`, `completeTask`, `deleteTask`
are implemented there. If yes, convert those too. If not, leave them inline for now.

### Argument Parsing

```javascript
// BEFORE:
function parseArgs(argv) { /* ~30 lines duplicated */ }

// AFTER: delete function, use library directly in run():
const args = argParser.parseArgs(argv);
```

## Acceptance Criteria

- [x] `manage_omnifocus.js` loads JXA libraries via `loadLibrary()` — no inline copies
- [x] All query functions delegate to `taskQuery.*` (10-15 line max per wrapper)
- [x] `formatTaskInfo`, `parseArgs`, `parseDate`, `parseEstimate` removed from `manage_omnifocus.js`
- [x] All existing commands still work: `today`, `due-soon`, `overdue`, `flagged`, `search`, CRUD
- [x] `omnifocus.js` deleted (pattern migrated to manage_omnifocus.js)
- [x] SKILL.md updated: no omnifocus.js references, manage_omnifocus.js confirmed canonical
- [x] `query_omnifocus.py` deleted (deprecated file removed)
- [x] Live test: `osascript -l JavaScript scripts/manage_omnifocus.js overdue` returns valid JSON
- [x] Skill version bumped to 5.2.0 in SKILL.md
- [x] Run skillsmith evaluation (84/100), record score in IMPROVEMENT_PLAN.md

## Dependencies & Risks

**Prerequisite:** Update plugin cache from 5.0.0 → 5.1.0 before testing. The `overdue`
command was added in v5.1.0 but the cache is stale.

**Risk:** `argParser.parseArgs` may not have the exact same interface as the inline version.
Compare argument handling carefully before removing the inline version.

**Risk:** `taskMutation.js` may not cover all cases handled by inline mutation functions
(e.g., `--create-project`, `--create-tags` flags). Audit before removing inline mutations.

**Not in scope:**
- PlannedDates support (separate issue — add to taskQuery.js after this refactor)
- Structural test harness (separate issue)
- Claude Code slash commands (separate issue)
- OmniFocus plugin actions (separate issue)

## References

- `scripts/omnifocus.js` — copy `loadLibrary()` from here, then delete this file
- `scripts/manage_omnifocus.js:99` — `parseArgs` to replace
- `scripts/manage_omnifocus.js:655` — `formatTaskInfo` to delete
- `scripts/manage_omnifocus.js:677` — `parseDate`/`parseEstimate` to delete
- `scripts/manage_omnifocus.js:498–650` — query functions to convert to thin wrappers
- `scripts/libraries/jxa/taskQuery.js` — the canonical source
- `scripts/libraries/jxa/taskMutation.js` — check for mutation coverage
- [omni-automation.com](https://omni-automation.com/) — JXA reference if any patterns need verification
- Brainstorm: `docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md`
