---
title: "refactor: Migrate ofo CLI to TypeScript plugin library architecture"
type: refactor
status: active
date: 2026-03-19
origin: 800 Generated/820 Brainstorms/2026-03-19-ofo-typescript-plugin-pipeline-requirements.md
---

# refactor: Migrate ofo CLI to TypeScript Plugin Library Architecture

## Overview

Migrate the ofo CLI from its current bash+python3+vanilla-JS stack to a TypeScript-authored OmniFocus plugin library architecture. All core functions are authored in TypeScript, compiled to vanilla JS, and packaged as an installed `.omnifocusjs` plugin bundle. The CLI calls plugin library functions via a stable stub script, eliminating per-session auth prompts and enabling single-language extensibility.

## Problem Statement / Motivation

The ofo CLI currently spans three languages (bash, embedded python3, vanilla JS) across two files. Adding a new action requires editing argument parsing in bash, JSON construction in python3, and handler logic in vanilla JS. This friction directly blocks the learning pipeline (issue #111) that would automatically promote usage patterns into new CLI commands.

Meanwhile, a full TypeScript toolchain already exists in the same directory (`generate_plugin.ts`, `omnifocus.d.ts`, `tsconfig.json`, `package.json`) but is only used for generating user-facing plugins — not for the CLI core itself.

(see origin: `820 Brainstorms/2026-03-19-ofo-typescript-plugin-pipeline-requirements.md`)

## Proposed Solution

### Architecture

```
TypeScript Source (src/)
  │
  ├── build (tsc)
  │   │
  │   ├── ofo-core.omnifocusjs/        ← Installed OmniFocus plugin bundle
  │   │   ├── manifest.json
  │   │   ├── Resources/
  │   │   │   ├── ofoCore.js           ← Compiled library (all 7+ actions)
  │   │   │   └── en.lproj/manifest.strings
  │   │   └── (auto-deployed to OF4 Plug-Ins/)
  │   │
  │   └── ofo-stub.js                  ← Stable stub script (copied from src/, never changes)
  │
  └── ofo (bash entry point, thin wrapper)
      └── Reads ofo-stub.js, encodes, opens omnijs-run URL with &arg=
```

### Execution Flow

```
ofo search "end of day"
  ↓
TypeScript CLI parses args → {"action":"search","query":"end of day"}
  ↓
Reads stable ofo-stub.js from file (always identical text)
  ↓
open "omnifocus://localhost/omnijs-run?script=<stub>&arg=<json>"
  ↓
Stub: result = PlugIn.find("com.totally-tools.ofo-core").library("ofoCore").dispatch(args)
  ↓
Library returns result object → Stub writes JSON to Pasteboard.general.string
  ↓
CLI polls pasteboard (sentinel pattern), returns result
```

### Auth Model (Validated by POC)

| Component | Auth prompts |
|-----------|-------------|
| Plugin library install | Once (on first install) |
| Stub script (identical every call) | Once (check "Automatically run" checkbox) |
| Different actions via `&arg=` | Zero (not part of approval key) |

## Technical Approach

### Phase 1: Plugin Library Bundle

**Goal:** Move dispatcher logic into an installed OmniFocus plugin library.

**Tasks:**

1. **Create TypeScript source for library** (`src/ofo-core.ts`)
   - Port all 7 action handlers from `ofo-dispatcher.js` to TypeScript
   - Add `dispatch(args)` entry point that routes on `args.action`
   - Use existing `omnifocus.d.ts` type definitions for full type safety
   - Wrap all handlers in try/catch with error serialization (return error objects; stub writes to pasteboard)
   - **IIFE wrapper requirement:** Omni Automation libraries must return from `(() => { var lib = new PlugIn.Library(...); return lib; })()`. `tsc` compiles inner logic → build script wraps output in IIFE shell (prepend/append)

2. **Create plugin manifest** (`src/manifest.json`)
   - Bundle ID: `com.totally-tools.ofo-core`
   - Declare library: `ofoCore`
   - No actions (library-only plugin — invisible in Automation menu)

3. **Create stub script** (`src/ofo-stub.js`)
   - ~5 lines, stable text that never changes
   - Calls `PlugIn.find().library().dispatch(argument)`
   - **Stub owns pasteboard writes** — library returns result objects, stub serializes to `Pasteboard.general.string` (keeps library pure, stub handles I/O)
   - Error handling for plugin-not-found (writes error JSON to pasteboard)

4. **Configure build** (`src/tsconfig.plugin.json`)
   - Target: ES2020 (OmniFocus 4 JavaScript engine supports modern JS — validated by POC using arrow functions, const/let, template literals)
   - Strict mode enabled
   - Output to `build/ofo-core.omnifocusjs/Resources/`
   - **Build pipeline:** `tsc` compiles to intermediate JS → build script wraps in `PlugIn.Library` IIFE shell → outputs final `ofoCore.js`

5. **Add build + deploy scripts** (`package.json`)
   - `npm run build:plugin` — `tsc` compile + IIFE wrap → vanilla JS plugin bundle
   - `npm run build:cli` — `tsc` compile `ofo-cli.ts` → `build/ofo-cli.js`
   - `npm run deploy` — copy bundle to `~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/Plug-Ins/`
   - `npm run build` — build:plugin + build:cli + deploy

**Key files:**
- `scripts/src/ofo-core.ts` (new)
- `scripts/src/manifest.json` (new)
- `scripts/src/ofo-stub.js` (new)
- `scripts/src/tsconfig.plugin.json` (new)
- `scripts/package.json` (modified — add build scripts)

**Validation:**
- `bash scripts/validate-plugin.sh build/ofo-core.omnifocusjs/`
- Manual: `ofo info <known-task-id>` returns identical JSON to current version
- Manual: `ofo search "test"` returns identical JSON

### Phase 2: CLI Wrapper Migration

**Goal:** Replace bash+python3 argument parsing with TypeScript.

**Tasks:**

1. **Create TypeScript CLI** (`src/ofo-cli.ts`)
   - Argument parsing for all commands (info, complete, create, update, search, list, perspective, help)
   - URL construction (read stub file, encode, open omnifocus:// URL)
   - Pasteboard polling via `pbcopy`/`pbpaste` (sentinel pattern — preserve exact current behavior; macOS-only, matching current architecture)
   - JSON output to stdout
   - Error handling with exit codes matching current behavior
   - `--version` flag showing architecture and version

2. **Compile CLI** with `tsc`
   - TypeScript already a dependency — no new tooling needed
   - `tsc` compiles `ofo-cli.ts` → `ofo-cli.js`, run with `node`

3. **Update bash entry point** (`scripts/ofo`)
   - Replace current 308-line bash+python3 with thin wrapper:
     ```bash
     #!/usr/bin/env bash
     exec node "$(dirname "$0")/build/ofo-cli.js" "$@"
     ```
   - Preserves `ofo` as the command name for all existing consumers

4. **Backward compatibility validation**
   - Capture golden output from current bash version for all 7 commands
   - Run same inputs through TypeScript version
   - Diff outputs — must be identical JSON structure
   - Verify exit codes match (0 for success, 1 for errors)

**Key files:**
- `scripts/src/ofo-cli.ts` (new)
- `scripts/ofo` (modified — simplified to thin wrapper)
- `scripts/package.json` (modified — add cli build target)

### Phase 3: Documentation & Cleanup

**Goal:** Update CONTRIBUTING.md, clean up legacy code.

**Tasks:**

1. **Update CONTRIBUTING.md**
   - Architecture diagram (TypeScript → build → plugin library → CLI)
   - How to add a new action (single TypeScript function + rebuild)
   - Build commands (`npm run build`, `npm run deploy`)
   - Plugin reload behavior (document whether OmniFocus hot-reloads or needs restart)
   - First-run setup instructions (install plugin, check "Automatically run" checkbox)
   - Troubleshooting (plugin not found, permission prompts, timeouts)

2. **Remove legacy dispatcher**
   - Delete `ofo-dispatcher.js` after migration validation passes (git history serves as rollback)

3. **Update SKILL.md**
   - Remove references to `ofo-dispatcher.js` as the execution mechanism
   - Update the CRITICAL plugin generation workflow to reference shared type definitions
   - Run skillsmith evaluation

4. **Update command files**
   - All `commands/ofo-*.md` files continue to call `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo` — no changes needed since the bash entry point is preserved

**Key files:**
- `CONTRIBUTING.md` (modified)
- `scripts/ofo-dispatcher.js` (deleted)
- `skills/omnifocus-manager/SKILL.md` (modified)

## System-Wide Impact

- **Interaction graph:** `ofo` bash entry → `node ofo-cli.js` → `open omnifocus://` URL → OmniFocus plugin library → `Pasteboard.general.string` → `pbpaste` in CLI → stdout. No callbacks or observers.
- **Error propagation:** Plugin library try/catch → JSON error on pasteboard → CLI detects `success: false` → stderr + exit 1. Current behavior preserved.
- **State lifecycle risks:** Pasteboard is the shared state. Current sentinel pattern (`__ofo_pending__`) prevents stale reads. Concurrent calls remain a known limitation (documented, not solved — matches current behavior).
- **API surface parity:** All existing `/ofo:*` commands call `ofo` by name — the bash entry point is preserved, so all consumers work unchanged.
- **Integration test scenarios:** (1) `ofo search` → plugin library → pasteboard → JSON output matches golden file. (2) `ofo create --name "test"` → task appears in OmniFocus inbox. (3) Plugin not installed → error within 2 seconds, not 10-second timeout.

## Acceptance Criteria

- [ ] All 7 existing ofo actions work identically (info, complete, create, update, search, list, perspective)
- [ ] Adding a new action requires editing only TypeScript files
- [ ] Zero auth prompts after one-time "Automatically run" checkbox approval
- [ ] `ofo --version` shows version and architecture type
- [ ] `npm run build` produces both plugin bundle and CLI in one command
- [ ] `validate-plugin.sh` passes on built plugin bundle
- [ ] Skillsmith evaluation score >= 95 after SKILL.md updates
- [ ] CONTRIBUTING.md documents full build → deploy → extend workflow
- [ ] Golden output comparison passes for all 7 actions (JSON structure match)
- [ ] Plugin-not-found error returns within 2 seconds with actionable message

## Dependencies & Risks

**Dependencies:**
- Node.js >= 18 (already required by `generate_plugin.ts`)
- TypeScript 5.3+ (already in `package.json`)
- OmniFocus 4 with Omni Automation enabled

**Risks:**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OmniFocus JS engine doesn't support compiled TS output | Low (POC validated ES2020 features) | High | Target ES2015 as fallback; test each feature |
| Plugin reload requires OmniFocus restart | Medium | Low (dev inconvenience) | Document in CONTRIBUTING.md; add `npm run restart-of` helper |
| Pasteboard concurrency issues | Low (existing limitation) | Medium | Document as known limitation; same as current behavior |
| TypeScript arg parsing misses bash edge cases | Medium | Medium | Golden output comparison catches regressions |

## Sources & References

### Origin

- **Origin document:** [820 Brainstorms/2026-03-19-ofo-typescript-plugin-pipeline-requirements.md](../../Documents/PAN_Projects/Notes/800%20Generated/820%20Brainstorms/2026-03-19-ofo-typescript-plugin-pipeline-requirements.md) — Key decisions: plugin library over actions, TypeScript with build step, stable stub + &arg= for auth, pasteboard args approach

### Internal References

- Current dispatcher: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ofo-dispatcher.js`
- Current CLI: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ofo`
- TypeScript defs: `plugins/omnifocus-manager/skills/omnifocus-manager/typescript/omnifocus.d.ts`
- Plugin generator: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/generate_plugin.ts`
- Build config: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/package.json`
- Script consolidation plan: `docs/plans/2026-03-16-001-fix-omnifocus-manager-script-consolidation-tag-perf-plan.md`
- Automation decision framework: `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md`
- Code generation validation: `plugins/omnifocus-manager/skills/omnifocus-manager/references/code_generation_validation.md`

### Related Work

- Issue #111: Automatic learning pipeline for OmniFocus interaction patterns (this plan provides the foundation)
- Omni Automation guide: `plugins/omnifocus-manager/skills/omnifocus-manager/references/omni_automation_guide.md` (Section 6: Libraries, Section 10: External Script Integration, Section 12: Script Security)
