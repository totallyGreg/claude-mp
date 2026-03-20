# Contributing to omnifocus-manager

## Architecture

The omnifocus-manager plugin uses two execution contexts:

### 1. ofo CLI → TypeScript Plugin Library

All OmniFocus mutations and queries run through an installed plugin library.

```
ofo <command> [args]
  ↓
scripts/ofo (bash thin wrapper)
  ↓
node build/ofo-cli.js (TypeScript CLI — arg parsing, URL construction)
  ↓
omnifocus://localhost/omnijs-run?script=<stub>&arg=<json>
  ↓
ofo-stub.js → PlugIn.find("com.totally-tools.ofo-core").library("ofoCore").dispatch(args)
  ↓
Library returns result → Stub writes JSON to Pasteboard
  ↓
CLI polls pasteboard, outputs JSON to stdout
```

**Source files** (TypeScript, in `scripts/src/`):
- `ofo-core.ts` — All action handlers (info, complete, create, create-batch, update, search, list, tag, tags, perspective, perspective-configure)
- `ofo-cli.ts` — Argument parsing, URL construction, pasteboard polling
- `ofo-stub.js` — Stable script sent via URL (approved once, never changes)
- `manifest.json` — Plugin bundle manifest

**Build outputs** (in `scripts/build/`):
- `ofo-core.omnifocusjs/` — Plugin bundle installed in OmniFocus
- `ofo-cli.js` — Compiled CLI
- `ofo-stub.js` — Copied from src

### 2. JXA Library (read-only diagnostics)

`scripts/gtd-queries.js` + `scripts/libraries/jxa/` — JavaScript for Automation via `osascript`. Used for read-only diagnostic queries (system-health, stalled-projects, repeating-tasks).

## Adding a New ofo Action

1. Add a handler function to `scripts/src/ofo-core.ts`
2. Add a case to the `dispatch()` switch
3. Add argument parsing in `scripts/src/ofo-cli.ts`
4. Run `npm run build` (compiles TypeScript + deploys plugin)
5. Test: `./ofo <new-action> <args>`

That's it — one language, one build command.

## Build Commands

```bash
cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts/

npm run build          # Build plugin + CLI + deploy to OmniFocus
npm run build:plugin   # Build plugin bundle only
npm run build:cli      # Build CLI only
npm run deploy         # Copy plugin bundle to OmniFocus Plug-Ins directory
npm run build:generator # Build the plugin generator (generate_plugin.ts)
```

## First-Run Setup

1. `npm run build` — Compiles and deploys the plugin
2. Run any `ofo` command — OmniFocus shows an approval dialog
3. Check **"Automatically run this script when sent by this or any other unknown application"**
4. All subsequent commands run with zero prompts

## Plugin Reload

When you rebuild and redeploy the plugin (`npm run build`), OmniFocus picks up changes automatically — no restart required. If changes aren't reflected, restart OmniFocus.

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
- **Omni Automation** (in `ofo-core.ts`): `task.name` (property), `Task.byIdentifier(id)`
- **JXA** (in `taskQuery.js`, `gtd-queries.js`): `task.name()` (method call), `doc.flattenedTasks()`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Auth prompt on every command | "Automatically run" checkbox not checked | Re-run, check the box |
| `ofo-core plugin not installed` | Plugin not deployed | `npm run deploy` |
| Timeout (10s) | OmniFocus not running or scripts disabled | Check OmniFocus is running; enable Automation > Plug-Ins > Security > external scripts |
| `tsc` errors | Missing type definitions | Check `ofo-core-ambient.d.ts` covers new APIs |

## Testing

1. **Plugin validator**: `bash scripts/validate-plugin.sh build/ofo-core.omnifocusjs/`
2. **JXA validator**: `node scripts/validate-jxa-patterns.js scripts/libraries/jxa/taskQuery.js`
3. **Skillsmith eval**: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager`
4. **Manual E2E**: Run `ofo info <id>`, `ofo list inbox`, `ofo search test`
