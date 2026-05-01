# Omni Automation API Mapping (JXA vs Script URLs)

**Official API Reference:** <https://omni-automation.com/omnifocus/OF-API.html>

Validated by prototype spike on 2026-03-09. The Omni Automation API used inside OmniFocus (via `omnijs-run` script URLs) differs from the JXA API used via `osascript`. When in doubt, verify against the official API above.

## Context Differences

| Aspect | JXA (osascript) | Omni Automation (script URLs) |
|--------|-----------------|-------------------------------|
| Entry point | `Application('OmniFocus')` | Global scope (no app reference) |
| Document | `app.defaultDocument` | Not needed — globals are database-level |
| Execution | `osascript -l JavaScript` subprocess | `open "omnifocus://localhost/omnijs-run?script=..."` |
| Return values | stdout (captured by shell) | `Pasteboard.general.string` (read via `pbpaste`) |
| File I/O | Full filesystem access | **Sandboxed** — cannot write to `/tmp/` or any path |
| Permissions | Apple Events bridge (may fail for some operations) | Full API access inside OmniFocus |

## Operation Mapping

| Operation | JXA | Omni Automation |
|-----------|-----|-----------------|
| Global tasks | `app.defaultDocument.flattenedTasks` | `flattenedTasks` |
| Global projects | `app.defaultDocument.flattenedProjects` | `flattenedProjects` |
| Global tags | `app.defaultDocument.flattenedTags` | `flattenedTags` |
| Inbox | `app.defaultDocument.inboxTasks` | `inbox` |
| Find task by ID | `flattenedTasks.byId(id)` | `Task.byIdentifier(id)` (class function, not on TaskArray) |
| Find project by ID | `flattenedProjects.byId(id)` | `Project.byIdentifier(id)` (class function) |
| Find by name | `flattenedTasks.whose({name: n})` | `flattenedTasks.byName(n)` |
| Get task ID | JXA-specific | `task.id.primaryKey` |
| Mark complete | `task.completed = true` (**FAILS** via Apple Events) | `task.markComplete()` |
| Mark incomplete | `task.completed = false` | `task.markIncomplete()` |
| Create task | `app.Task({name: "..."})` | `new Task("name", inbox.ending)` |
| Add tag | `app.add(tag, {to: task.tags})` | `task.addTag(tag)` |
| Remove tag | Custom iteration | `task.removeTag(tag)` |
| Clear all tags | Manual iteration | `task.clearTags()` |
| Set property | `task.name.set("...")` | `task.name = "..."` |
| Read property | `task.name()` (method call) | `task.name` (direct access) |
| Filter tasks | `flattenedTasks.whose({...})` | `flattenedTasks.filter(t => ...)` |
| Write pasteboard | N/A | `Pasteboard.general.string = "data"` |

## Key Gotchas

1. **`byIdentifier()` is a class function**, not an instance method on arrays. Use `Task.byIdentifier(id)` and `Project.byIdentifier(id)` — NOT `flattenedTasks.byIdentifier(id)`. The `TaskArray` type only has `byName()` plus standard JS array methods (`find`, `filter`, `forEach`).
2. **Property access is direct** — `task.name` not `task.name()`. Methods use parentheses: `task.markComplete()`.
3. **`Pasteboard.makeUnique()` exists** but unique pasteboards aren't readable from the CLI (`pbpaste` only reads `Pasteboard.general`).
4. **Date handling**: `task.dueDate` returns a JS `Date` object. Use `.toISOString()` for serialization.
5. **Arrow functions work** in the Omni Automation context, but `function()` syntax is safer for script URL approval (more readable in the approval dialog).

## Script URL Architecture

```
Shell CLI (ofo)
  -> Reads stable .js file from scripts/omni-actions/
  -> URL-encodes script body (approved once per unique script)
  -> JSON-encodes argument data (changes freely via &arg=)
  -> open "omnifocus://localhost/omnijs-run?script=<encoded>&arg=<encoded>"
  -> OmniFocus executes JS with full API access
  -> Script writes JSON result to Pasteboard.general.string
  -> CLI reads via pbpaste (sentinel-based polling, 10s timeout)
  -> CLI outputs JSON to stdout
```
