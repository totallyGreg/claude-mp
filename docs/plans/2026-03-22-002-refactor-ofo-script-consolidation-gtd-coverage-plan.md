---
title: "refactor: ofo script consolidation — orphan cleanup, manage_omnifocus migration, GTD coverage gaps"
type: refactor
status: active
date: 2026-03-22
github_issue: "https://github.com/totallyGreg/claude-mp/issues/121"
related_plans:
  - docs/plans/2026-03-22-001-refactor-ofo-library-separation-plan.md
  - docs/plans/2026-03-20-002-feat-ofo-cli-fix-and-extend-plan.md
---

# refactor: ofo Script Consolidation — Orphan Cleanup, manage_omnifocus Migration, GTD Coverage Gaps

## Overview

The 2026-03-22 library separation refactor completed the ofo architecture (named exports, shared types, Attache reconciliation). This plan executes the **next consolidation layer**: delete orphaned scripts that accumulated before the ofo CLI matured, migrate the three commands still calling `manage_omnifocus.js`, close the GTD-coach-identified coverage gaps in the ofo CLI, and retire `manage_omnifocus.js`. The gtd-coach skill's data-grounded coaching questions (informed by `gtd-queries.js`) reveal the one meaningful hole: **due-soon queries** for the GTD Reflect phase.

## Research Corrections (Post-Agent Verification)

Research agents identified three dead references in existing commands that change scope:

| Command | Dead reference | Reality |
|---------|---------------|---------|
| `ofo-expound.md` | `gtd-queries.js --action task-search` | `task-search` action does NOT exist in gtd-queries.js dispatch |
| `ofo-expound.md` | `gtd-queries.js --action list-tags` | `list-tags` action does NOT exist in gtd-queries.js dispatch |
| `ofo-plan.md` | `manage_omnifocus.js project-update --note-append` | `--note-append` flag does NOT exist in `projectUpdate()` — the ofo-plan note-append step has been silently broken since shipping |

Additionally: `ofo perspective-list` is documented in SKILL.md and the CLI help text but has no backing OfoAction or handler in ofo-core.ts — `ofo dump` returns perspective names as a side-effect.

**Impact on phases:** Phase 4 (expound migration) now also fixes two broken calls, not just migrates them. Phase 3 (note-append) is now fixing a broken workflow in ofo-plan rather than replacing a working one. Phase 4 ofo-plan bulk-create needs a gap assessment (see Technical Considerations).

---

## Problem Statement

### 1. Orphaned scripts (44KB of dead code)

Four scripts exist with no command references and no SKILL.md workflow:

| Script | Size | Why orphaned |
|--------|------|-------------|
| `ai-analyze.js` | 11KB | AI analysis via Claude API concept abandoned before shipping |
| `analyze_insights.js` | 12.7KB | Insight/perspective analysis path superseded by ofo perspective-rules |
| `create_from_template.js` | 8.1KB | Template task creation; `omni/templateEngine.js` serves this in plugin context; no ofo-plan integration |
| `perspective-config.js` | 11.7KB | Requires Omni Automation plugin runtime (not JXA); SKILL.md has a warning; ofo perspective-configure supersedes it |

### 2. Three commands still calling manage_omnifocus.js

Every call now has a direct ofo equivalent except `project-update --note-append`:

| Command | manage_omnifocus.js call | ofo equivalent |
|---------|--------------------------|----------------|
| `ofo-work.md` | `project-info --name X` | `ofo info X` |
| `ofo-expound.md` | `task-info --id X` | `ofo info X` |
| `ofo-expound.md` | `update --id X --name Y` | `ofo update X --name Y` |
| `ofo-expound.md` | `update --id X --add-tag Y` | `ofo tag X --add Y` |
| `ofo-expound.md` | `gtd-queries --action list-tags` | `ofo tags` |
| `ofo-plan.md` | `bulk-create --json-file X` | `cat X \| ofo create` (JSON stdin) |
| `ofo-plan.md` | `project-update --id X --note-append "text"` | **missing** → needs Phase 3 |

### 3. GTD coverage gaps (via gtd-coach skill analysis)

The gtd-coach skill's coaching table maps GTD phases to available tools. Auditing each coaching question against current tools reveals one gap:

| GTD Phase | Coaching Question | Current Tool | Status |
|-----------|------------------|--------------|--------|
| Capture | Quick add | `ofo create` | ✅ |
| Clarify | Inbox review | `ofo list inbox` | ✅ |
| Organize | Assign project/tags/dates | `ofo update`, `ofo tag` | ✅ |
| Reflect (daily) | What's flagged/due today? | `ofo list today` | ✅ |
| Reflect (weekly) | What's due in next N days? | `manage_omnifocus.js due-soon` | ❌ missing in ofo |
| Reflect (weekly) | Stalled/waiting/neglected | `gtd-queries.js` | ✅ |
| Reflect (weekly) | Recently completed | `ofo completed-today`, `gtd-queries.js` | ✅ |
| Engage | By context/tag | `ofo-tagged` command → `gtd-queries.js tagged-tasks` | ✅ |
| Engage | Overdue | `ofo list overdue` | ✅ |

**Gap:** `ofo list due-soon --days N` — weekly review needs "what's due in the next 3–7 days?" The `weekly-review-collect.sh` fetches overdue and completed but not upcoming. GTD-coach coaching for the Reflect phase requires this.

### 4. Documentation debt from Phase 5 of the library separation plan

The 2026-03-22 library plan (status: completed) has unchecked Phase 5 items:

- [ ] CONTRIBUTING.md: architecture diagram (three-layer), null-guard pattern, "add new action" 5-step workflow
- [ ] `references/omni_automation_guide.md`: "Using ofoCore from another plugin" code example
- [ ] SKILL.md: Fix version footer inconsistency (`Current version: 8.1.0` vs frontmatter `9.0.0`)
- [ ] SKILL.md: Line 32 decision tree still says "use manage_omnifocus.js" for query/execution
- [ ] Skillsmith eval at 9.0.0 + version bump in `plugin.json` and `marketplace.json` + README.md

## Proposed Solution

Five phases in dependency order:

1. **Phase 1: Documentation debt** — Complete Phase 5 of the library plan while context is fresh
2. **Phase 2: Delete orphaned scripts** — Remove 4 dead scripts, clean SKILL.md references
3. **Phase 3: Extend ofo CLI** — Add `due-soon` list and `update --note-append`
4. **Phase 4: Migrate commands** — Update 3 command files to use ofo; update gtd_guide.md Automation Mapping table
5. **Phase 5: Deprecate manage_omnifocus.js** — Archive or delete; final reference cleanup

## Technical Considerations

### manage_omnifocus.js commands NOT needed in ofo

These manage_omnifocus.js commands have no active consumers and do not need ofo equivalents:
- `delete` — destructive, not used in any command; risk outweighs convenience
- `batch-update` — not used in any command
- `rename-tag`, `move-tag`, `delete-tag` — OmniFocus tag DB management, not AI workflow

### Due-soon implementation

`ofo list due-soon --days N` maps to the listTasks action in `ofo-core.ts`. Pattern:
```typescript
// ofo-core.ts addition to listTasks() filter branches
} else if (filter === 'due-soon') {
  const days = (args.days as number) || 7;
  const cutoff = new Date(todayStart.getTime() + days * 86400000);
  flattenedTasks.forEach(function(t: Task) {
    if (results.length >= limit) return;
    if (t.taskStatus === Task.Status.Completed || t.taskStatus === Task.Status.Dropped) return;
    if (t.effectivelyCompleted || t.effectivelyDropped) return;
    if (t.dueDate && t.dueDate >= todayStart && t.dueDate < cutoff) {
      results.push(taskSummary(t));
    }
  });
}
```

CLI addition in `ofo-cli.ts` `cmdList()`:
```typescript
case 'due-soon': {
  const days = commandArgs[1] ? parseInt(commandArgs[1], 10) : 7;
  runAction('ofo-list', { filter: 'due-soon', days });
  break;
}
```

Usage: `ofo list due-soon` (default 7 days) or `ofo list due-soon 3`.

### Note-append implementation

`ofo update <id> --note-append "text"` requires a new branch in `updateTask()` in `ofo-core.ts`:
```typescript
// In updateTask(), after handling note:
if (args.noteAppend) {
  const existing = task.note || '';
  const sep = existing.length > 0 ? '\n' : '';
  task.note = existing + sep + (args.noteAppend as string);
}
```

CLI in `ofo-cli.ts` `cmdUpdate()`:
```typescript
case '--note-append': argObj.noteAppend = args[++i] || ''; break;
```

Usage: `ofo update <id> --note-append "Issue: https://github.com/..."`.

### ofo-types.ts and ofo-core-ambient.d.ts sync

`ofo-list` already exists in the OfoAction union. No new action strings needed — `due-soon` and `note-append` are filter/arg values within existing actions. No type union changes required.

### build-plugin.sh rebuild required after Phase 3

After adding due-soon and note-append to ofo-core.ts, run:
```bash
cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts
npm run build && npm run deploy
```

The pre-commit hook (from the 2026-03-20 plan) will auto-rebuild on staged src/ changes.

### ofo-plan bulk-create migration (gap assessment)

`manage_omnifocus.js bulk-create` does more than flat task creation — it creates structured **projects with action groups** from a hierarchical JSON schema. The ofo `ofo-create-batch` action creates only flat tasks (iterates `createTask` per item). These are not equivalent.

**Options:**
1. **Defer** — leave `bulk-create` on `manage_omnifocus.js` for now; migrate only the `--note-append` call (which is already broken). manage_omnifocus.js stays but is no longer the primary tool.
2. **Port** — add `ofo-create-project` action to ofo-core.ts that accepts the hierarchical JSON schema (project + action groups + tasks). This unlocks full ofo-plan migration but is a larger scope change.

**Recommended for this plan: Option 1 (defer).** The note-append fix is the highest-value change (currently broken). Full bulk-create migration belongs in a subsequent PR focused on project lifecycle operations (referenced in 2026-03-22-001 future considerations as "project lifecycle" follow-on to issue #119).

## Implementation Phases

### Phase 1: Documentation Debt (from library plan Phase 5)

**Files to modify:**
- `plugins/omnifocus-manager/CONTRIBUTING.md` — add architecture diagram + null-guard + "add new action" 5-step workflow
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/omni_automation_guide.md` — add "Using ofoCore from another plugin" section
- `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md` — fix version footer, fix line 32 decision tree

**Steps:**

1. **CONTRIBUTING.md:** Add three-layer architecture diagram in Mermaid:
   ```
   ofoCore library (ofo-core.omnifocusjs)
     ├── ofo-stub.js → ofo-cli.ts → Claude Code skills
     └── Feature Plugins (Attache, future FM plugins via PlugIn.find())
   ```
   Add "Null-guard pattern" section: every feature plugin must check `PlugIn.find()` return before calling.
   Add "Add a new ofoCore action" 5-step workflow: ofo-core.ts → dispatch → build-plugin.sh exports → ofo-types.ts union → CLI cmdXxx.

2. **references/omni_automation_guide.md:** Add Section 7 "Loading ofoCore from a feature plugin" with the null-guard code example and cross-reference to CONTRIBUTING.md.

3. **SKILL.md line 32:** Change:
   > `"show me", "what tasks", "analyze" → QUERY/EXECUTION (use manage_omnifocus.js, STOP)`
   To:
   > `"show me", "what tasks", "analyze" → QUERY/EXECUTION (use ofo CLI or gtd-queries.js, STOP)`

4. **SKILL.md footer:** Update "Current version: 8.1.0" → "Current version: 9.0.0"

5. **Skillsmith eval:**
   ```bash
   uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py \
     plugins/omnifocus-manager/skills/omnifocus-manager \
     --version 9.0.0 --export-table-row
   ```
   Record score in README.md version history.

6. **Version files:** Verify `plugin.json` and `marketplace.json` both show `9.0.0`.

### Phase 2: Delete Orphaned Scripts

**Files to delete:**
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ai-analyze.js`
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/analyze_insights.js`
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/create_from_template.js`
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/perspective-config.js`

**Files to update:**
- `SKILL.md` line 149: Remove the `perspective-config.js` warning comment entirely
- `references/jxa_guide.md`: Remove any references to `ai-analyze.js`, `analyze_insights.js`, `create_from_template.js`

**Verification:**
```bash
# Confirm no commands reference deleted scripts
grep -r "ai-analyze\|analyze_insights\|create_from_template\|perspective-config" \
  plugins/omnifocus-manager/commands/ \
  plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md
```
Expected: no matches (or only the deletion-context comment if you add one).

### Phase 3: Extend ofo CLI for GTD Coverage Gaps

**Files to modify:**
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts` — add due-soon filter branch to `listTasks()`, add `--note-append` branch to `updateTask()`
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-cli.ts` — add `due-soon [N]` to `cmdList()`, add `--note-append` to `cmdUpdate()`

**Steps:**

1. Add `due-soon` filter to `listTasks()` in `ofo-core.ts` (see Technical Considerations)
2. Add `--note-append` branch to `updateTask()` in `ofo-core.ts` (see Technical Considerations)
3. Wire `cmdList('due-soon', days)` in `ofo-cli.ts`
4. Wire `--note-append` arg in `cmdUpdate()` in `ofo-cli.ts`
5. Update `cmdHelp()` to document both additions
6. Run `npm run build && npm run deploy`
7. Smoke test:
   ```bash
   # Due-soon
   cd plugins/omnifocus-manager/skills/omnifocus-manager
   scripts/ofo list due-soon       # tasks due in next 7 days
   scripts/ofo list due-soon 3     # tasks due in next 3 days
   # Note-append (use a real task ID from your OF)
   scripts/ofo info <id>
   scripts/ofo update <id> --note-append "Test append"
   scripts/ofo info <id>           # verify note contains appended text
   ```

**SKILL.md update:**
- Add `scripts/ofo list due-soon [N]` to the ofo CLI command table (line ~93)

### Phase 4: Migrate Commands from manage_omnifocus.js

**Files to modify:**
- `plugins/omnifocus-manager/commands/ofo-expound.md`
- `plugins/omnifocus-manager/commands/ofo-work.md`
- `plugins/omnifocus-manager/commands/ofo-plan.md`
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/gtd_guide.md`

**ofo-expound.md changes:**

This command has both manage_omnifocus.js calls AND two dead gtd-queries.js references. Fix everything together:

| Old call | Status | New call |
|----------|--------|----------|
| `osascript ... scripts/gtd-queries.js --action task-search --name X` | **BROKEN** (action doesn't exist) | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo search "$ARGUMENTS"` |
| `osascript ... scripts/gtd-queries.js --action list-tags` | **BROKEN** (action doesn't exist) | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo tags` |
| `osascript ... scripts/manage_omnifocus.js task-info --id "<id>"` | legacy | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo info "<id>"` |
| `osascript ... scripts/manage_omnifocus.js update --id "<id>" --name "<new name>"` | legacy | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo update "<id>" --name "<new name>"` |
| `osascript ... scripts/manage_omnifocus.js update --id "<id>" --add-tag "<tag>"` | legacy | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo tag "<id>" --add "<tag>"` |

Note: `task-search --include-projects true` fallback (if used) → `ofo search "$ARGUMENTS"` + `ofo info "$ARGUMENTS"` (search covers both tasks and projects).

**ofo-work.md changes:**

| Old call | New call |
|----------|----------|
| `osascript -l JavaScript scripts/manage_omnifocus.js project-info --name "<project>"` | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo info "<project>"` |

The ofo `info` command detects type from URL or searches by name. Verify it handles project lookup by name correctly before migrating.

**ofo-plan.md changes:**

| Old call | Status | New call |
|----------|--------|----------|
| `osascript ... scripts/manage_omnifocus.js project-update --id "<id>" --note-append "<url>"` | **BROKEN** (`--note-append` doesn't exist in manage_omnifocus.js) | `${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo update "<id>" --note-append "<url>"` (after Phase 3) |
| `osascript ... scripts/manage_omnifocus.js bulk-create --json-file /tmp/of-plan-bulk-create.json` | legacy (creates project + action groups) | **Deferred** — leave on manage_omnifocus.js; ofo batch-create only does flat tasks |

**references/gtd_guide.md Automation Mapping table:**

Replace all `manage_omnifocus.js` references with ofo equivalents:

| GTD Phase | Old | New |
|-----------|-----|-----|
| Capture (detailed) | `manage_omnifocus.js create --name "Item"` | `ofo create --name "Item"` |
| Clarify (review inbox) | `manage_omnifocus.js list --filter active` | `ofo list inbox` |
| Organize (assign project) | `manage_omnifocus.js update --name "Task" --project "P"` | `ofo update <id> --project "P"` |
| Reflect (daily) | `manage_omnifocus.js today` | `ofo list today` |
| Reflect (weekly) | `manage_omnifocus.js due-soon --days 7` | `ofo list due-soon 7` |
| Engage (by context) | `manage_omnifocus.js search --query "@office"` | `ofo-tagged` command or `ofo tags` + `ofo list --tag "@office"` |
| Engage (flagged) | `manage_omnifocus.js flagged` | `ofo list flagged` |

**ofo-expound.md allowed-tools update:**
Remove `Bash(osascript:*)` allowed tool if it was only needed for manage_omnifocus.js calls (check against remaining osascript calls for gtd-queries.js).

### Phase 5: Deprecate manage_omnifocus.js

**Precondition:** Phase 3 and Phase 4 complete, all three commands migrated.

**Verification sweep:**
```bash
# Confirm no remaining command or skill references
grep -r "manage_omnifocus" \
  plugins/omnifocus-manager/commands/ \
  plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md \
  plugins/omnifocus-manager/skills/omnifocus-manager/references/
```

**Options (prefer delete over archive):**
- Delete `scripts/manage_omnifocus.js` — 38KB removed, no git subtlety needed
- Update `references/jxa_guide.md` Section 5 ("Command-Line Interface") to remove the manage_omnifocus.js command table (or mark it historical and point to ofo)
- SKILL.md line 126-127: Remove "Legacy task/project commands via scripts/manage_omnifocus.js" section entirely

## System-Wide Impact

### Interaction Graph

**After Phase 4 completes**, the command → script dependency graph simplifies to:

```
Commands → ofo CLI (all CRUD, list, search, tags, perspectives, batch)
         → gtd-queries.js (GTD diagnostics: stalled, waiting, analyze, repeating, health, ai-agent)
         → update-weekly-note.js (weekly review note append)
         → weekly-review-collect.sh (parallel data collection wrapper)
```

`manage_omnifocus.js` drops out entirely.

### Dependency on gtd-queries.js

**gtd-queries.js is NOT a cleanup target.** It provides GTD-specific analysis capabilities that the ofo CLI deliberately does not replicate (stalled projects, waiting-for aging, AI agent task tracking, repeating task analysis). The gtd-coach skill's data-grounded coaching table depends on all its actions remaining stable.

### ofo info for projects (Phase 4 risk)

`ofo info` is documented for task/URL lookup. It may not handle project-by-name lookup (used in ofo-work project-info migration). Verify before migrating:
```bash
scripts/ofo info "My Project Name"
```
If it returns project data, migration is safe. If not, `ofo search "My Project Name"` can substitute. Check ofo-core.ts `getTask()` to see if it falls through to project search.

### Skillsmith eval cadence

Run eval after each phase that modifies SKILL.md or command files. Don't batch all phases into a single version bump.

## Acceptance Criteria

### Phase 1 — Documentation
- [ ] CONTRIBUTING.md has three-layer architecture diagram and null-guard pattern
- [ ] CONTRIBUTING.md has "add new action" 5-step workflow
- [ ] `references/omni_automation_guide.md` has "Using ofoCore from another plugin" section
- [ ] SKILL.md version footer reads "Current version: 9.0.0"
- [ ] SKILL.md line 32 no longer references `manage_omnifocus.js`
- [ ] Skillsmith eval ≥ 95/100 at version 9.0.0

### Phase 2 — Orphan Deletion
- [ ] 4 orphaned scripts deleted
- [ ] `grep -r "ai-analyze\|analyze_insights\|create_from_template\|perspective-config" commands/ SKILL.md` returns no matches
- [ ] SKILL.md perspective-config warning comment removed

### Phase 3 — ofo CLI Extensions
- [ ] `ofo list due-soon` returns tasks due within next 7 days
- [ ] `ofo list due-soon 3` returns tasks due within next 3 days
- [ ] `ofo update <id> --note-append "text"` appends text to task/project note without overwriting existing note
- [ ] `npm run build` produces zero TypeScript errors
- [ ] `ofo-core.omnifocusjs` redeployed and smoke tests pass

### Phase 4 — Command Migration
- [ ] `ofo-expound.md` contains no `manage_omnifocus.js` references
- [ ] `ofo-work.md` contains no `manage_omnifocus.js` references
- [ ] `ofo-plan.md` contains no `manage_omnifocus.js` references
- [ ] `references/gtd_guide.md` Automation Mapping table references ofo commands, not manage_omnifocus.js
- [ ] All migrated commands tested: ofo-expound flow works end-to-end, ofo-plan bulk-create creates tasks via stdin

### Phase 5 — Deprecation
- [ ] `manage_omnifocus.js` deleted (38KB removed)
- [ ] `grep -r "manage_omnifocus" commands/ skills/` returns no matches
- [ ] `references/jxa_guide.md` Section 5 updated or removed
- [ ] README.md version history entry added

## Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `ofo info` doesn't handle project-by-name lookup for ofo-work migration | Medium | Low | Test before migrating; fallback to `ofo search "name"` |
| `ofo create` stdin batch fails for ofo-plan bulk-create format (JSON schema differences) | Medium | Medium | Test with actual ofo-plan JSON template before migrating; manage_omnifocus.js may have different field names |
| gtd-queries.js `--action tagged-tasks` used in ofo-expound is NOT replaced by `ofo tags` | N/A | N/A | Already resolved: ofo-expound uses task-search (keeps gtd-queries.js) for search, list-tags only for tag listing (→ `ofo tags`) |
| Deleting scripts others have shell-aliased locally | Low | Low | Document deletion in README.md version history |
| SKILL.md version bump without skillsmith eval creates false quality signal | Medium | Low | Strict ordering: eval before bump, bump before commit |

## Sources & References

### Internal References

- Completed parent plan: `docs/plans/2026-03-22-001-refactor-ofo-library-separation-plan.md` (Phase 5 unchecked items carried forward)
- ofo CLI fix plan (tag ops, stdin): `docs/plans/2026-03-20-002-feat-ofo-cli-fix-and-extend-plan.md`
- Tag perf lesson: `docs/plans/2026-03-16-001-fix-omnifocus-manager-script-consolidation-tag-perf-plan.md`

### Key Files

- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts` — add due-soon + note-append
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-cli.ts` — wire CLI args
- `plugins/omnifocus-manager/commands/ofo-expound.md`, `ofo-work.md`, `ofo-plan.md` — migrate
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/gtd_guide.md` — update automation table
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/jxa_guide.md` — remove manage_omnifocus CLI section
- `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md` — version footer, line 32 decision tree
- `plugins/omnifocus-manager/CONTRIBUTING.md` — architecture + null-guard + action workflow

### Skills Consulted

- `gtd-coach` skill — coaching question audit drove the due-soon coverage gap identification
- `omnifocus-manager` skill SKILL.md — tool selection hierarchy informed migration decisions
