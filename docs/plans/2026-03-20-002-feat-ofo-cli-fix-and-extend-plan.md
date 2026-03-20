---
title: "feat: ofo CLI distribution fix, tag manipulation, and stdin support"
type: feat
status: active
date: 2026-03-20
origin: "800 Generated/820 Brainstorms/2026-03-20-ofo-cli-fix-and-extend-requirements.md"
---

# feat: ofo CLI Distribution Fix, Tag Manipulation, and Stdin Support

## Overview

Fix the broken ofo CLI distribution (#114), add granular tag manipulation with capture pipeline shortcuts, a tag discovery command, and stdin/pipe support for task creation.

## Problem Statement / Motivation

The ofo CLI is the omnifocus-manager skill's primary recommended method for task CRUD, but it's completely broken in distribution — the root `.gitignore` excludes `build/` globally, so compiled JS never ships to the plugin cache. Beyond the breakage, the CLI lacks tag manipulation (only full-replacement via `update --tags`), has no tag discovery for agents, and doesn't support piped input.

## Proposed Solution

Four workstreams, ordered by dependency:

1. **Fix distribution** — Unblock `build/` from gitignore, update `.skillignore`, commit artifacts
2. **Tag commands** — New `ofo tag` (add/remove/capture) and `ofo tags` (hierarchy listing) commands with corresponding `ofo-core.omnifocusjs` plugin actions
3. **Stdin support** — Extend `ofo create` to read from stdin when piped (JSON or plain text)
4. **Build safety** — Pre-commit hook to keep build artifacts in sync

## Technical Considerations

### Architecture

The CLI follows a two-tier pattern (see origin: `820 Brainstorms/2026-03-20-ofo-cli-fix-and-extend-requirements.md`):

- **`ofo-cli.ts`** — Argument parsing, OmniFocus URL construction, pasteboard polling
- **`ofo-core.ts`** — Plugin library actions running inside OmniFocus via `dispatch()`
- **Communication** — CLI writes sentinel to pasteboard, opens `omnifocus://localhost/omnijs-run?script=<stub>&arg=<json>`, polls pasteboard for result

Adding new commands follows the 5-step pattern documented in `CONTRIBUTING.md`:
1. Add handler function to `ofo-core.ts`
2. Add case to `dispatch()` switch
3. Add CLI command function + case in `ofo-cli.ts`
4. Run `npm run build`
5. Run `npm run deploy`

### Key Learnings Applied

- **Tag query performance**: Use `tag.tasks()` (~870ms) not `doc.flattenedTasks()` + filter (~490s) (see `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md`)
- **JXA tag bugs don't apply**: We use Omni Automation (TypeScript), not JXA. `addTag()`, `clearTags()` work correctly in this context.
- **IIFE wrapper**: `build-plugin.sh` wraps tsc output in `PlugIn.Library` IIFE — new actions just need a function + dispatch case.

### Edge Case Decisions

These resolve the critical SpecFlow gaps identified during planning:

| Gap | Decision | Rationale |
|-----|----------|-----------|
| `--add` and `--remove` same tag | Error: "Cannot add and remove the same tag" | Prevents ambiguous state |
| Tag name not found for `--add` | Return success with `warnings` array | Agents can detect typos without hard failure |
| `--remove` tag not on task | Silent no-op | Idempotent removal is standard |
| `--capture` with `--add`/`--remove` | Allowed — `--capture` is sugar for `--add` with name mapping | Natural composition |
| Stdin empty | Error: "No input received from stdin" | Prevents blank task creation |
| JSON detection | Try `JSON.parse()`, fall through to plain text on failure | `{Budget} Review` fails JSON parse, correctly treated as text |
| Stdin + `--name` conflict | `--name` wins, stdin becomes note | CLI flags always override; documented |
| JSON array partial failure | Best-effort with per-item results array | Agents can inspect what succeeded |
| Pre-commit hook, node missing | Soft fail with warning | Doesn't block non-CLI commits |
| Pre-commit hook triggers | Any staged file in `scripts/src/`, `scripts/package.json`, or `scripts/tsconfig*.json` | Covers all build-affecting changes |

## Implementation Phases

### Phase 1: Fix Distribution (R1, R3) — Closes #114

**Files to modify:**

- `.gitignore:9` — Add exception for ofo build directory
- `plugins/omnifocus-manager/skills/omnifocus-manager/.skillignore` — Add exclusions

**Steps:**

1. Add to root `.gitignore` (negate specific files rather than directory to avoid gitignore edge cases):
   ```
   build/
   !plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build/ofo-cli.js
   !plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build/ofo-stub.js
   ```

2. Update `.skillignore` to exclude development-only files:
   ```
   # TypeScript source (build output is distributed instead)
   scripts/src/
   # Build dependencies (not needed at runtime — CLI uses Node built-ins only)
   scripts/node_modules/
   scripts/package.json
   scripts/package-lock.json
   scripts/build-plugin.sh
   # TypeScript configs
   scripts/tsconfig*.json
   # Build intermediates
   scripts/build/intermediate/
   scripts/build/ofo-core.omnifocusjs/
   # Test and validation scripts
   scripts/test-*.js
   scripts/validate-*.js
   # Legacy generator (not used by CLI)
   scripts/generate_plugin.js
   ```

   Note: `scripts/build/ofo-cli.js`, `scripts/build/ofo-stub.js`, and `scripts/ofo` (wrapper) MUST remain included.
   Note: `scripts/build/ofo-core.omnifocusjs/` is excluded from distribution because it's deployed directly to OmniFocus's Plug-Ins directory via `npm run deploy`, not used from the plugin cache.

3. Verify current `scripts/build/` contents are complete:
   ```bash
   cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts
   npm run build
   ```

4. Stage and commit the build artifacts:
   ```bash
   git add plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build/ofo-cli.js
   git add plugins/omnifocus-manager/skills/omnifocus-manager/scripts/build/ofo-stub.js
   ```

**Acceptance criteria:**
- [ ] `scripts/build/ofo-cli.js` and `scripts/build/ofo-stub.js` are tracked in git
- [ ] `.skillignore` excludes TS source, node_modules, build configs
- [ ] `ofo create --name "Test"` works from a fresh plugin cache clone

### Phase 2: Tag Commands (R4, R5, R7)

**New plugin action — `ofoTag` in `scripts/src/ofo-core.ts`:**

```typescript
function ofoTag(args: OfoArgs): OfoResult {
  const task = Task.byIdentifier(args.id as string);
  if (!task) return { success: false, error: `Task not found: ${args.id}` };

  const warnings: string[] = [];
  const addTags = (args.add as string[]) || [];
  const removeTags = (args.remove as string[]) || [];

  // Check for add+remove conflict
  const conflict = addTags.find(t => removeTags.includes(t));
  if (conflict) return { success: false, error: `Cannot add and remove the same tag: ${conflict}` };

  // Remove first (idempotent — removeTag is safe if tag not present)
  for (const tagName of removeTags) {
    const tag = flattenedTags.byName(tagName);
    if (tag) {
      task.removeTag(tag);
    }
  }

  // Then add
  for (const tagName of addTags) {
    const tag = flattenedTags.byName(tagName);
    if (tag) {
      task.addTag(tag);
    } else {
      warnings.push(`Tag '${tagName}' not found, skipped`);
    }
  }

  const result: OfoResult = {
    success: true,
    task: { id: task.id.primaryKey, name: task.name, tags: task.tags.map(t => t.name) }
  };
  if (warnings.length > 0) result.warnings = warnings;
  return result;
}
```

**New plugin action — `ofoTags` in `scripts/src/ofo-core.ts`:**

```typescript
function ofoTags(_args: OfoArgs): OfoResult {
  function buildTree(tags: Tag[]): object[] {
    return tags
      .filter(t => t.status === Tag.Status.Active || t.status === Tag.Status.OnHold)
      .map(t => ({
        id: t.id.primaryKey,
        name: t.name,
        status: t.status === Tag.Status.Active ? 'active' : 'on-hold',
        children: t.children.length > 0 ? buildTree(t.children) : [],
        activeTaskCount: t.remainingTasks.length
      }));
  }
  return { success: true, tags: buildTree(document.tags) };
}
```

**New CLI command — `cmdTag` in `scripts/src/ofo-cli.ts`:**

```typescript
const CAPTURE_MAP: Record<string, string> = {
  question:    'Question❓',
  discontent:  'Discontent⁉️',
  decide:      'Decide😤',
  routine:     'Routine🔁',
  evening:     'Evening🕕',
};

function cmdTag(args: string[]): void {
  if (args.length < 1) die('Usage: ofo tag <id> --add "Tag" --remove "Tag" --capture <shortcut>');
  const id = parseOmniFocusUrl(args[0]!);

  const addTags: string[] = [];
  const removeTags: string[] = [];
  let i = 1;
  while (i < args.length) {
    switch (args[i]) {
      case '--add':     addTags.push(args[++i] || ''); break;
      case '--remove':  removeTags.push(args[++i] || ''); break;
      case '--capture': {
        const shortcut = (args[++i] || '').toLowerCase();
        const mapped = CAPTURE_MAP[shortcut];
        if (!mapped) die(`Unknown capture shortcut: ${shortcut}. Available: ${Object.keys(CAPTURE_MAP).join(', ')}`);
        addTags.push(mapped);
        break;
      }
      default: die('Unknown option: ' + args[i]);
    }
    i++;
  }

  runAction('ofo-tag', { id, add: addTags, remove: removeTags });
}

function cmdTags(): void {
  runAction('ofo-tags', {});
}
```

**Dispatch cases in `ofo-core.ts`:**
```typescript
case 'ofo-tag':  return ofoTag(args);
case 'ofo-tags': return ofoTags(args);
```

**Main switch in `ofo-cli.ts`:**
```typescript
case 'tag':         cmdTag(commandArgs); break;
case 'tags':        cmdTags(); break;
```

**Update `cmdHelp()` to include new commands.**

**Acceptance criteria:**
- [ ] `ofo tag <id> --add "TagName"` adds tag without affecting existing tags
- [ ] `ofo tag <id> --remove "TagName"` removes tag (no-op if not present)
- [ ] `ofo tag <id> --capture question` adds `Question❓` tag
- [ ] `ofo tag <id> --capture unknown` shows available shortcuts in error
- [ ] `ofo tag <id> --capture question --add "Extra"` combines both
- [ ] `ofo tags` returns full tag hierarchy as JSON with id, name, status, children, activeTaskCount
- [ ] `ofo tags` excludes dropped tags, includes on-hold with status field
- [ ] Warnings returned for tag names not found in OmniFocus

### Phase 3: Stdin Support (R6)

**Modify `ofo-cli.ts` — add stdin reading to `cmdCreate`:**

```typescript
import { readFileSync } from 'fs';

function readStdin(): string | null {
  if (process.stdin.isTTY) return null;
  try {
    return readFileSync(0, 'utf-8').trim();  // fd 0 = stdin
  } catch {
    return null;
  }
}

function parseStdinInput(raw: string): { name: string; note?: string } | Record<string, unknown>[] | Record<string, unknown> {
  // Try JSON first
  try {
    const parsed = JSON.parse(raw);
    return parsed; // object or array
  } catch {
    // Plain text: first line = name, rest = note
    const lines = raw.split('\n');
    const name = lines[0]!.trim();
    const note = lines.slice(1).join('\n').trim();
    if (!name) throw new Error('No input received from stdin');
    const result: { name: string; note?: string } = { name };
    if (note) result.note = note;
    return result;
  }
}
```

**New plugin action — `ofoCreateBatch` in `scripts/src/ofo-core.ts`:**

Accepts an array of task specs, creates all tasks in a single OmniFocus call (one pasteboard round-trip), and returns per-item results:

```typescript
function ofoCreateBatch(args: OfoArgs): OfoResult {
  const items = args.items as Record<string, unknown>[];
  const results: OfoResult[] = [];
  for (const item of items) {
    try {
      results.push(ofoCreate(item as OfoArgs));
    } catch (e) {
      results.push({ success: false, error: String(e) });
    }
  }
  const created = results.filter(r => r.success).length;
  return { success: true, results, created, failed: items.length - created };
}
```

Add dispatch case: `case 'ofo-create-batch': return ofoCreateBatch(args);`

**Modify `cmdCreate` to check stdin before argument parsing:**

When stdin is present:
- If JSON array: call `runAction('ofo-create-batch', { items: array })` — single OmniFocus round-trip
- If JSON object or plain text: merge with CLI flags (flags override stdin fields)
- `--name` from CLI overrides stdin-derived name; stdin text becomes note in that case

**Output for batch creates:**
```json
{"success": true, "results": [{"success": true, "task": {...}}, ...], "created": 2, "failed": 0}
```

**Acceptance criteria:**
- [ ] `echo "Buy milk" | ofo create` creates task named "Buy milk"
- [ ] `printf "Buy milk\nAt the store on Oak St" | ofo create` creates task with name "Buy milk" and note "At the store on Oak St"
- [ ] `echo '{"name":"Task","project":"Inbox"}' | ofo create` parses JSON and creates task
- [ ] `echo '[{"name":"A"},{"name":"B"}]' | ofo create` creates both tasks, returns results array
- [ ] `echo "Buy milk" | ofo create --project "Errands"` merges stdin name with CLI project flag
- [ ] `echo "Buy milk" | ofo create --name "Override"` uses --name, stdin becomes note
- [ ] `echo "" | ofo create` errors with "No input received from stdin"
- [ ] `pbpaste | ofo create` works as expected

### Phase 4: Build Safety (R2)

**Extend existing pre-commit hook at `.git/hooks/pre-commit`:**

Add a section before the marketplace-manager checks that:
1. Checks if any staged files match `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/**` or `scripts/package.json` or `scripts/tsconfig*.json`
2. If yes, runs `cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts && npm run build:cli`
3. Stages the updated build artifacts
4. If node/npm is not available, prints warning and continues (soft fail)

```bash
# --- ofo CLI build sync ---
OFO_SCRIPTS="plugins/omnifocus-manager/skills/omnifocus-manager/scripts"
if git diff --cached --name-only | grep -qE "^${OFO_SCRIPTS}/src/|^${OFO_SCRIPTS}/package\.json|^${OFO_SCRIPTS}/tsconfig"; then
  if command -v node >/dev/null 2>&1; then
    echo "ofo: Rebuilding CLI from TypeScript source..."
    (cd "$OFO_SCRIPTS" && npm run build:cli --silent) || {
      echo "WARNING: ofo CLI build failed. Commit proceeding, but build may be stale."
    }
    git add "$OFO_SCRIPTS/build/ofo-cli.js" "$OFO_SCRIPTS/build/ofo-stub.js" 2>/dev/null
  else
    echo "WARNING: node not found, skipping ofo CLI rebuild. Run 'npm run build:cli' manually."
  fi
fi
```

**Acceptance criteria:**
- [ ] Editing `scripts/src/ofo-cli.ts` and committing auto-rebuilds and stages build output
- [ ] Editing unrelated files does NOT trigger rebuild
- [ ] Hook soft-fails with warning if node is unavailable
- [ ] Existing marketplace-manager hook behavior is preserved

## System-Wide Impact

- **SKILL.md**: Update to reflect new `tag`, `tags` commands and stdin support in the CLI reference section
- **Help text**: `cmdHelp()` must document new commands
- **CONTRIBUTING.md**: Add `tag`/`tags` to the action table, document stdin behavior
- **Plugin version**: Bump `ofo-core` manifest version and skill version after all changes

## Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| Root `.gitignore` `build/` rule may cause future confusion | Comment explaining the exception |
| Pasteboard collision during batch creates | Pre-existing risk; document as known limitation |
| Capture tag emoji names may differ from actual OmniFocus tags | Verify exact tag names before implementation |
| Pre-commit hook adds latency to commits | Build step is fast (~2s); only triggers on relevant files |

## Follow-Up: TypeScript Architecture Rationalization

After this plan ships, create a separate GitHub issue to rationalize the omnifocus-manager TypeScript architecture:
- Extract shared types (`OfoArgs`, `OfoResult`, action name union) into a common `.d.ts` referenced by both CLI and plugin tsconfigs
- Relocate `typescript/` directory contents to `references/` or `assets/` per agentic skill specs
- Unify OmniFocus interaction patterns so improvements in one place benefit both CLI and generated plugins
- Eliminate duplicated magic strings (action names) with compile-time validated types

This work will retroactively improve the commands added in this plan.

## Sources & References

### Origin

- **Origin document:** `800 Generated/820 Brainstorms/2026-03-20-ofo-cli-fix-and-extend-requirements.md` — Key decisions: ship pre-built JS, pre-commit hook for build safety, simple heuristic text parsing, hardcoded capture shortcuts

### Internal References

- Contributing guide: `plugins/omnifocus-manager/CONTRIBUTING.md` — 5-step action addition workflow
- Automation framework: `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — tag query performance, JXA bug catalog
- TypeScript migration plan: `docs/plans/2026-03-19-001-refactor-ofo-typescript-plugin-library-plan.md` — IIFE wrapper, auth model
- Tag perf lesson: `docs/plans/2026-03-16-001-fix-omnifocus-manager-script-consolidation-tag-perf-plan.md` — `tag.tasks()` vs `flattenedTasks()`

### Related Work

- Issue #114: ofo CLI broken — build artifacts not distributed
- Issue #111: automatic learning pipeline (TypeScript migration complete, pipeline layers deferred)
- PR #112: ofo TypeScript plugin library migration (merged)
