# Contributing to omnifocus-manager

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Attache.omnifocusjs                             │
│           (consolidated plugin — installed in OF)                │
│  Core layer: ofoCore (dispatch, normalizeTask, CRUD, stats)     │
│  Analytics: taskMetrics, projectParser, folderParser, etc.      │
│  AI Actions: dailyReview, weeklyReview, analyzeSelected, etc.   │
└──────────┬──────────────────────────────────────────────────────┘
           │ PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore")
     ┌─────┴─────────────────────┐
     │                           │
┌────▼──────────────────┐  ┌────▼────────────────────────────────┐
│  ofo-stub.js (stable) │  │  Attache Actions (built-in)          │
│  calls dispatch(args) │  │  Load ofoCore via this.plugIn         │
└────┬──────────────────┘  │  Apple Intelligence + OmniFocus UI    │
     │                     └─────────────────────────────────────┘
┌────▼──────────────────┐
│  ofo-cli.ts           │
│  Claude Code skills   │
│  and commands         │
└───────────────────────┘
```

The omnifocus-manager plugin uses two execution contexts:

### 1. ofo CLI → TypeScript Plugin Library

All OmniFocus mutations and queries run through the installed Attache plugin.

```
ofo <command> [args]
  ↓
scripts/ofo (bash thin wrapper)
  ↓
node build/ofo-cli.js (TypeScript CLI — arg parsing, URL construction)
  ↓
omnifocus://localhost/omnijs-run?script=<stub>&arg=<json>
  ↓
ofo-stub.js → PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore").dispatch(args)
  ↓
Library returns result → Stub writes JSON to Pasteboard
  ↓
CLI polls pasteboard, outputs JSON to stdout
```

**Source files** (TypeScript, in `scripts/src/`):
- `ofo-core.ts` — 17 named action handlers exposed as library functions plus thin `dispatch()` router
- `ofo-types.ts` — Shared `OfoAction` union + `OfoArgs`/`OfoResult` interfaces (CLI only)
- `ofo-cli.ts` — Argument parsing, URL construction, pasteboard polling
- `ofo-stub.js` — Stable script sent via URL (approved once, never changes)
- `ofo-contract.d.ts` — Shared ambient type contract (OfoTask, OfoArgs, OfoResult)
- `ofo-core-ambient.d.ts` — Ambient type declarations for the plugin build
- `attache/*.ts` — 10 Attache library source files (compiled to IIFE JS)

**Build outputs** (in `scripts/build/`):
- `Attache.omnifocusjs/` — Consolidated plugin bundle installed in OmniFocus
- `ofo-cli.js` — Compiled CLI
- `ofo-stub.js` — Copied from src

### 2. JXA Library (read-only diagnostics)

`scripts/gtd-queries.js` + `scripts/libraries/jxa/` — JavaScript for Automation via `osascript`. Used for read-only diagnostic queries (system-health, stalled-projects, repeating-tasks).

## Adding a New ofo Action

1. Add the action name to `OfoAction` union in **both** `scripts/src/ofo-types.ts` (CLI) and `scripts/src/ofo-contract.d.ts` (contract)
2. Add the handler function to `scripts/src/ofo-core.ts` (named function, not inside dispatch)
3. Add the named export to `build-attache.sh` IIFE footer: `lib.<name> = <functionName>;`
4. Add a case to `dispatch()` calling the named function
5. Add argument parsing in `scripts/src/ofo-cli.ts`
6. Run `npm run build && npm run deploy`
7. Test: `./ofo <new-action> <args>`

## Adding a New Attache Library

1. Create `scripts/src/attache/<name>.ts` — IIFE with `PlugIn.Library`, type annotations
2. Add `{"identifier": "<name>"}` to `assets/Attache.omnifocusjs/manifest.json`
3. Add `<name>` to `ATTACHE_LIBS` array in `build-attache.sh`
4. Run `npm run build` to compile and verify

## Adding a New Attache Action

1. Create `assets/Attache.omnifocusjs/Resources/<name>.js` — action script
2. Add action declaration to `assets/Attache.omnifocusjs/manifest.json`
3. Add `<name>` to `ATTACHE_ACTIONS` array in `build-attache.sh`
4. Add localization string to `en.lproj/manifest.strings`
5. Run `npm run build && npm run deploy`

## Build Commands

```bash
cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts/

npm run build          # Build plugin + CLI
npm run build:plugin   # Build plugin bundle only
npm run build:cli      # Build CLI only
npm run deploy         # Open plugin in OmniFocus
npm run build:generator # Build the plugin generator (generate_plugin.ts)
```

## First-Run Setup

1. `npm run build` — Compiles TypeScript
2. `npm run deploy` — Opens the plugin bundle; OmniFocus prompts for install location
3. Run any `ofo` command — OmniFocus shows an approval dialog
4. Check **"Automatically run this script when sent by this or any other unknown application"**
5. All subsequent commands run with zero prompts

## Plugin Reload

After rebuilding, run `npm run deploy` — OmniFocus opens the updated bundle and reloads it automatically.

## Key Patterns

### Library Cross-Reference (Parameter Passing)

Libraries cannot load other libraries — only action scripts can call `this.plugIn.library()`. Actions wire dependencies via parameters:

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    const core = this.plugIn.library("ofoCore");
    const metrics = this.plugIn.library("taskMetrics");
    const all = metrics.collectAllMetrics(core);  // metrics uses core.normalizeTask()
});
```

### JXA Safety: `whose()` guard
Always check `.length > 0` before indexing `whose()` results — they throw on empty, not return undefined:
```javascript
var tags = doc.flattenedTags.whose({ name: tagName });
if (tags.length === 0) return { error: 'Tag not found' };
var tag = tags[0];
```

### Omni Automation vs JXA
These are different APIs — don't mix syntax:
- **Omni Automation** (in `ofo-core.ts`): `task.name` (property), `Task.byIdentifier(id)`
- **JXA** (in `taskQuery.js`, `gtd-queries.js`): `task.name()` (method call), `doc.flattenedTasks()`

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Auth prompt on every command | "Automatically run" checkbox not checked | Re-run, check the box |
| `Attache plugin not installed` | Plugin not deployed | `npm run deploy` |
| Timeout (10s) | OmniFocus not running or scripts disabled | Check OmniFocus is running; enable Automation > Plug-Ins > Security > external scripts |
| `tsc` errors | Missing type definitions | Check ambient `.d.ts` files cover new APIs |

## Testing

1. **Plugin validator**: `bash scripts/validate-plugin.sh build/Attache.omnifocusjs/`
2. **JXA validator**: `node scripts/validate-jxa-patterns.js scripts/libraries/jxa/taskQuery.js`
3. **Skillsmith eval**: `uv run plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py plugins/omnifocus-manager/skills/omnifocus-manager`
4. **Manual E2E**: Run `ofo info <id>`, `ofo list inbox`, `ofo search test`
