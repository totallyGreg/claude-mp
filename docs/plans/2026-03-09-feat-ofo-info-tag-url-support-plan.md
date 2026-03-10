---
title: "ofo info: add tag URL support (omnifocus:///tag/)"
type: feat
status: completed
date: 2026-03-09
issue: "#99"
---

# ofo info: add tag URL support (omnifocus:///tag/)

`ofo info omnifocus:///tag/<id>` currently fails with `"Task not found"` because `detect_type_from_url` defaults to `"task"` for any URL that isn't a project, then `Task.byIdentifier()` returns nothing.

## Problem Statement

The `detect_type_from_url` function in `scripts/ofo` only recognises `omnifocus:///project/*`. Anything else (including `///tag/`) falls through to `"task"`. The `ofo-info.js` Omni Automation action then calls `Task.byIdentifier(tagId)` and fails.

Discovered when resolving `omnifocus:///tag/fjyi9aLKyru` (the AI Agent 🤖 tag) — had to fall back to inline JXA.

## Proposed Solution

Two-file change:

1. **`scripts/ofo`** — extend `detect_type_from_url` to return `"tag"` for `omnifocus:///tag/*` URLs
2. **`scripts/omni-actions/ofo-info.js`** — add a `"tag"` branch that uses `Tag.byIdentifier()` and returns tag metadata + active task list

## Implementation

### `scripts/ofo` — `detect_type_from_url` (lines 45–52)

```bash
detect_type_from_url() {
  local input="$1"
  if [[ "$input" == omnifocus:///project/* ]]; then
    echo "project"
  elif [[ "$input" == omnifocus:///tag/* ]]; then
    echo "tag"
  else
    echo "task"
  fi
}
```

### `scripts/omni-actions/ofo-info.js` — add tag branch

```js
} else if (args.type === "tag") {
  var tag = Tag.byIdentifier(args.id);
  if (tag) {
    var activeTasks = [];
    tag.flattenedTasks.forEach(function(t) {
      if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
      if (t.effectivelyCompleted || t.effectivelyDropped || t.completed) return;
      activeTasks.push(t);
    });
    result = {
      success: true,
      tag: {
        id: tag.id.primaryKey,
        name: tag.name,
        activeTaskCount: activeTasks.length,
        tasks: activeTasks.slice(0, 50).map(function(t) {
          return {
            id: t.id.primaryKey,
            name: t.name,
            project: t.containingProject ? t.containingProject.name : null,
            dueDate: t.dueDate ? t.dueDate.toISOString() : null,
            flagged: t.flagged
          };
        })
      }
    };
  } else {
    result = { success: false, error: "Tag not found: " + args.id };
  }
}
```

**Notes:**
- `Tag.byIdentifier()` follows the same Omni Automation API as `Task.byIdentifier` / `Project.byIdentifier` already used in the file
- Triple-check filter pattern (from fix #98 / commit 6ee42b6): `taskStatus` + `effectivelyCompleted` + `effectivelyDropped` + `completed`
- Cap task list at 50, consistent with `ofo search` limit
- `tag.flattenedTasks` returns all tasks at any depth under the tag

## Acceptance Criteria

- [x] `ofo info omnifocus:///tag/<id>` returns `{ success: true, tag: { id, name, activeTaskCount, tasks: [...] } }`
- [x] `ofo info omnifocus:///task/<id>` and `omnifocus:///project/<id>` continue to work unchanged
- [x] Returned tasks include: id, name, project, dueDate, flagged
- [x] Completed/dropped tasks excluded via triple-check pattern
- [x] Returns `{ success: false, error: "Tag not found: ..." }` for invalid tag IDs

## Context

- **Issue**: #99
- **Architecture**: Omni Automation script URL pattern — NOT JXA
- **Filter pattern**: Triple-check introduced in #98 (commit 6ee42b6) — `taskStatus` + `effectivelyCompleted` + `effectivelyDropped` + `completed`
- **Task cap**: 50 tasks, consistent with `ofo search`
- **Bare ID routing**: Bare IDs (no URL scheme) continue to route as "task" — correct, since tag lookup via bare ID is not a use case

## Validation

```bash
# Requires OmniFocus running with external script execution enabled
ofo info omnifocus:///tag/fjyi9aLKyru    # AI Agent tag — should return tag data
ofo info omnifocus:///task/<valid-id>    # Regression check
ofo info omnifocus:///project/<valid-id> # Regression check
ofo info omnifocus:///tag/nonexistent    # Should return error JSON
```

Run validators after editing `ofo-info.js`:
```bash
node scripts/validate-js-syntax.js scripts/omni-actions/ofo-info.js
node scripts/validate-jxa-patterns.js scripts/omni-actions/ofo-info.js
```
