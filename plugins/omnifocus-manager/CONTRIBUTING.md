# Contributing to omnifocus-manager

## Architecture: The Bridge Pattern

The omnifocus-manager plugin bridges two execution contexts:

1. **ofo CLI scripts** (`scripts/ofo`, `scripts/ofo-dispatcher.js`) — bash + Omni Automation JS executed via `omnifocus://` URL scheme. Source of truth for all OmniFocus mutations (create, complete, update) and interactive queries.

2. **JXA library** (`scripts/libraries/jxa/`, `scripts/gtd-queries.js`) — JavaScript for Automation executed via `osascript`. Used for read-only diagnostic queries (system-health, stalled-projects, repeating-tasks) and batch analysis.

**When adding new logic:**
- If it's a repeatable action (create, update, complete) → add to `ofo-dispatcher.js`
- If it's a diagnostic/read-only query → add to `gtd-queries.js` with a new `--action`
- If it's an interactive command for users → create a command in `commands/ofo-*.md`

## Key Patterns

### JXA Safety: `whose()` guard
Always check `.length > 0` before indexing `whose()` results — they throw on empty, not return undefined:
```javascript
var tags = doc.flattenedTags.whose({ name: tagName });
if (tags.length === 0) return { error: 'Tag not found' };
var tag = tags[0];
```

### Tag queries: use `tag.tasks()` not `flattenedTasks()`
Direct lookup is O(k) vs O(n) full database scan. See `searchTasksByTag` and `getTasksByTagGrouped` in `taskQuery.js`.

### Omni Automation vs JXA
These are different APIs — don't mix syntax:
- **Omni Automation** (in `ofo-dispatcher.js`): `task.name` (property), `Task.byIdentifier(id)`
- **JXA** (in `taskQuery.js`, `gtd-queries.js`): `task.name()` (method call), `doc.flattenedTasks()`

## Testing

1. **JXA validator**: `node scripts/validate-jxa-patterns.js scripts/libraries/jxa/taskQuery.js`
2. **Skillsmith eval**: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager`
3. **Manual**: Run `ofo info`, `ofo list inbox`, `ofo search test` to verify end-to-end
