---
title: "Attache: Unified OmniFocus AI Assistant Plugin"
type: feat
status: active
date: 2026-03-08
deepened: 2026-03-08
origin: docs/brainstorms/2026-03-08-attache-omnifocus-plugin-brainstorm.md
---

# Attache: Unified OmniFocus AI Assistant Plugin

## Enhancement Summary

**Deepened on:** 2026-03-08
**Research agents used:** architecture-strategist, pattern-recognition-specialist, code-simplicity-reviewer, security-sentinel, performance-oracle, framework-docs-researcher, best-practices-researcher, omnifocus-agent (GTD coach)

### Key Improvements from Research
1. **Scope reduction:** 14 actions -> 9 for v1.0 (defer curation actions to v1.1); cut command palette hub action
2. **Form API resolved:** `Form.validate` CAN add/remove fields per OmniFocus API docs, but `Form.Field.Option` has no in-place mutation API — dynamic filtering requires field replacement with unknown UX quality
3. **Hybrid persistence:** Use native `Preferences` API as local cache + task-note JSON as synced authoritative store
4. **Performance wins:** Single-pass metrics collector (4-5x scan reduction), FM session reuse, speculative prefetch
5. **GTD gap found:** Weekly review missing explicit Waiting For step — significant omission per GTD canon
6. **Security finding:** `systemDiscovery.js` `collectTaskSample()` could leak task names into preference cache — must strip before persisting
7. **Architecture fix:** Keep `systemDiscovery.js` pure; orchestrate cache in action, not library

### New Considerations Discovered
- OmniAutomation actions cannot programmatically invoke sibling actions — command palette must dispatch to library functions
- `curationActions.js` violates SRP — three unrelated operations; inline or rename to `taskOperations.js`
- Action label prefix ("Attache: ...") needed to prevent Automation menu scattering
- `fmUtils.createSession()` lacks system prompt support — newer actions bypass it; unify in Phase 0
- `analyzeProjects.js` has inline functions duplicating parser library functionality — clean up during migration

---

## Overview

Attache is a renamed, expanded, and unified replacement for `AITaskAnalyzer.omnifocusjs`. It consolidates ~8 scattered AI and curation plugins into a single composable OmniAutomation bundle with persistent memory. The north star is making GTD daily and weekly reviews effortless by already knowing the user's system, completed work, and patterns.

**Requires macOS 26+** (Apple Intelligence / Foundation Models). All actions gate on this. Deterministic logic (date math, task counts) runs as code; FM is used only where it adds value (analysis, NL understanding, generation).

**Bundle ID:** `com.totallytools.omnifocus.attache` (clean break from `ai-task-analyzer`)

## Problem Statement / Motivation

1. **No memory** — Every plugin run starts cold. `systemDiscovery.js` re-discovers the same system structure each time. GTD preferences are never remembered.
2. **Too many separate plugins** — ~20 installed plugins with no unified entry point. AI capabilities duplicated across `of-afm-assist`, `of-help-me-plan`, `of-help-me-estimate`.
3. **Reviews are hard** — `weeklyReview.js` and `dailyReview.js` start fresh with no knowledge of user's personal GTD conventions.
4. **OS version bug** — `foundationModelsUtils.js` gates on `15.2`; should be `26`. Error messages reference iOS hardware.

(see brainstorm: docs/brainstorms/2026-03-08-attache-omnifocus-plugin-brainstorm.md)

## Proposed Solution

### Single Composable Bundle

One `Attache.omnifocusjs` bundle with shared `PlugIn.Library` modules, replacing AITaskAnalyzer and absorbing 3 other plugins. Individual actions accessible for toolbar/shortcut assignment via OmniFocus's native Automation menu.

### Research Insights: Bundle Architecture

- **14 actions is within OmniAutomation norms** — `of-date-controls` has ~20, `updateEstimatedDuration` has 12. However, simplicity review recommends shipping v1.0 with 9 actions (see Simplified Scope below).
- **Action label prefix required** — Use "Attache: Daily Review", "Attache: Analyze Selected" etc. in the manifest to prevent actions scattering alphabetically across the Automation menu mixed with other plugins.
- **Actions cannot invoke sibling actions** — The `attache` command palette cannot programmatically call `dailyReview`. It would need to inline logic or call shared library functions. This is the architectural reason to cut the command palette for v1.0.

### Simplified Scope (v1.0 vs v1.1)

Based on simplicity review, ship v1.0 with the core value proposition (persistence + consolidation) and defer curation actions:

**v1.0 — 9 Actions (7 migrated + 2 new):**

| Action | Source | Status |
|--------|--------|--------|
| `dailyReview` | AITaskAnalyzer (existing) | Migrate + enhance with cached prefs |
| `weeklyReview` | AITaskAnalyzer (existing) | Migrate + enhance + add Waiting For step |
| `analyzeSelected` | AITaskAnalyzer (existing) | Migrate (already includes time estimates) |
| `analyzeProjects` | AITaskAnalyzer (existing) | Migrate |
| `analyzeHierarchy` | AITaskAnalyzer (existing) | Migrate |
| `discoverSystem` | AITaskAnalyzer (existing) | Migrate (becomes `systemSetup` with cache) |
| `analyzeTasksWithAI` | AITaskAnalyzer (existing) | Migrate |
| `completedSummary` | CompletedTasksSummary (absorbed) | New action |
| `systemSetup` | New | Runs discovery + caches + view prefs |

**v1.1 — Deferred Actions (5):**

| Action | Reason to Defer |
|--------|-----------------|
| `planSelected` | `analyzeSelected` already suggests improvements; overlap |
| `estimateSelected` | `analyzeSelected` already returns `estimatedMinutes` |
| `deferTo` | `of-date-controls` already handles defer dates |
| `convertToProject` | `of-tasks-to-projects` already works |
| `markWaiting` | `of-complete-await-reply` (Rosemary Orchard) already works |

**Cut entirely:**

| Action | Reason |
|--------|--------|
| `attache` (command palette) | OmniFocus Automation menu IS the palette; building a launcher for a launcher |
| `preferences` (separate action) | Merged into `systemSetup` — no user-configurable settings exist |

### Persistent Preferences via Hybrid Storage

Attache uses a **hybrid persistence strategy** discovered during research:

1. **Synced store (authoritative):** Task-note JSON in `Synced Preferences` project — syncs via iCloud to all devices
2. **Local cache (fast reads):** Native `Preferences` API — device-local, no parse overhead

**Read flow:** Check `Preferences` first (cache hit) -> fall back to task note (cache miss) -> write back to `Preferences`
**Write flow:** Write to both simultaneously

### Research Insights: Persistence

- **OmniAutomation `Preferences` API exists** (`new Preferences(null)` scopes to bundle ID) but is device-local only. This is why `SyncedPreferences.omnifocusjs` exists — the task-note pattern is the **canonical workaround** for cross-device sync.
- **Schema versioning:** Use integer `schemaVersion` (not semver string) with chain-of-migration-functions pattern. Include `lastWritten` ISO timestamp and `lastWrittenDevice` name for conflict diagnostics.
- **Preference task protection:** Use distinctive task name "Attache System Map" and check regardless of completion/dropped status. Users may accidentally complete or drop during cleanup.
- **Cache the task reference in IIFE closure scope** (pattern from `weeklyReview.js` concurrency guard) to avoid repeated `flattenedTasks` lookups.

### Research Insights: Security — Preference Cache Content

**Critical finding:** `systemDiscovery.js` with `depth: "full"` calls `collectTaskSample()` which includes actual task names. Task names frequently contain sensitive information (people's names, financial figures, medical/legal matters).

`preferencesManager.writePreferences()` must use an **explicit allowlist** of fields:
- **Persist:** folder names, folder types, tag names, tag categories, project counts, GTD health scores, conventions
- **Strip before writing:** `rawData.tasks`, all `aiReasoning` fields, `recommendations`, `id.primaryKey` values

## Technical Considerations

### Architecture

The existing AITaskAnalyzer library architecture (8 `PlugIn.Library` modules) is the foundation. Libraries are extended, not rewritten:

| Library | Current | Attache Changes |
|---------|---------|-----------------|
| `taskMetrics.js` | Task counting, completion stats | Add `collectAllMetrics()` single-pass method; add count-only methods |
| `foundationModelsUtils.js` | FM session creation, schema | Fix OS version gate (15.2 -> 26); add system prompt support to `createSession()` |
| `systemDiscovery.js` | System map generation | **Keep pure.** Do NOT add cache logic here; orchestrate in action |
| `exportUtils.js` | Alert/clipboard output | Add unified output pattern (Alert + Copy + Done) |
| `hierarchicalBatcher.js` | Context batching | Validate batch size against macOS 26 context window |
| `folderParser.js` | Folder hierarchy parsing | Unchanged |
| `projectParser.js` | Project parsing | Unchanged |
| `taskParser.js` | Task parsing | Unchanged |

**New library (1, not 2):**

| Library | Purpose |
|---------|---------|
| `preferencesManager.js` | Read/write/version cached preferences (hybrid Preferences API + task note) |

### Research Insights: Architecture

- **Keep `systemDiscovery.js` pure** — adding persistence to a library that currently has a pure analysis role conflates discovery with persistence. The `systemSetup` action should orchestrate: call `systemDiscovery` -> call `preferencesManager.write()`.
- **`curationActions.js` eliminated** — the three planned curation operations (deferTo, convertToProject, markWaiting) share almost no logic. If they ship in v1.1, keep logic inline in each action file.
- **Clean up `analyzeProjects.js` during migration** — it has inline functions (`getAllFolders()`, `analyzeHierarchy()`, `calculateMetrics()`) that duplicate parser library functionality. Existed before the parser libraries were created. Refactor to use `folderParser.js`/`projectParser.js`.
- **Unify FM session creation** — `fmUtils.createSession()` currently takes no arguments, so `dailyReview.js` and `weeklyReview.js` bypass it to pass a system prompt. Add optional `systemPrompt` parameter to `createSession()` in Phase 0.

### Research Insights: Existing Pattern Consistency

All 7 existing actions follow consistent patterns that Attache should preserve:

| Pattern | Convention | Notes |
|---------|-----------|-------|
| IIFE wrapper | `(() => { ... })();` | Minor inconsistency: some use leading `;` |
| Action lifecycle | `new PlugIn.Action(async fn)` + `action.validate` + `return action` | All actions follow this |
| Library loading | `this.plugIn.library("name")` | Load fmUtils first, check availability |
| FM guard clause | Check `fmUtils.isAvailable()` -> `showUnavailableAlert()` -> return | 6 of 7 actions |
| Output pattern | Alert + "Copy to Clipboard" / "Done" buttons | Standard |
| Error handling | try/catch -> Alert with error message | `weeklyReview.js` adds `finally` for concurrency guard |
| Form pattern | Create form -> add fields -> `await form.show()` -> check null -> extract values | Consistent across 3 actions |
| Schema names | kebab-case (`"daily-review-schema"`) | Consistent |

### Generation Workflow

All new files generated through `generate_plugin.js --format bundle` following the existing CRITICAL plugin generation workflow. No hand-writing plugin files.

### Plugin Absorption Inventory

**Absorbed into Attache v1.0 (from this repo's assets):**

| Plugin | Actions | Libraries | Notes |
|--------|---------|-----------|-------|
| `AITaskAnalyzer.omnifocusjs` | 7 | 8 | Renamed, core of Attache |
| `CompletedTasksSummary.omnifocusjs` | 2 | 3 | -> `completedSummary` action |
| `Overview.omnifocusjs` | 1 | 0 | Fold stats into `dailyReview` |
| `TodaysTasks.omnifocusjs` | 1 | 0 | Fold into `dailyReview` |

**Deferred absorption (v1.1, only if curation actions ship):**

| Plugin | Disposition |
|--------|-------------|
| `of-afm-assist.omnifocusjs` | -> `planSelected` |
| `of-help-me-estimate.omnifocusjs` | -> `estimateSelected` |
| `of-help-me-plan.omnifocusjs` | -> `planSelected` |
| `of-tasks-to-projects.omnifocusjs` | -> `convertToProject` |
| `CompletedTaskReport.omnifocusjs` | -> `completedSummary` |
| `functionLibrary.omnifocusjs` | Audit; absorb only functions called by absorbed plugins |

**Kept separate (unchanged):**

| Plugin | Reason |
|--------|--------|
| `TreeExplorer.omnifocusjs` | Export utility, different purpose |
| `of-date-controls.omnifocusjs` | Toolbar utility (~20 actions) |
| `updateEstimatedDuration.omnifocusjs` | Toolbar utility (12 actions) |
| `of-complete-await-reply.omnifocusjs` | External author (Rosemary Orchard) |

### Performance Implications

- FM calls are on-device (Apple Intelligence) — no network latency, but model inference time varies with system load
- Weekly review makes 6-7 sequential FM calls — estimated 5-10 seconds under normal load, up to 15 seconds under heavy load
- System map cache eliminates cold-start discovery on every run (current ~2-3 second overhead)

### Research Insights: Performance

**Single-pass metrics collector (HIGH priority):**

Current `taskMetrics.js` iterates `flattenedTasks` separately for every query method (inbox, overdue, today, flagged, completed). On a 5,000-task database, each scan takes ~50ms. Status bar computation (3 scans) = ~150ms; daily review (4-5 scans) = ~250ms.

```javascript
// Recommended: single-pass that buckets all categories simultaneously
lib.collectAllMetrics = function() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
    const result = { inbox: [], today: [], overdue: [], flagged: [], completedToday: [] };
    for (const task of flattenedTasks) {
        // single iteration, multiple buckets
    }
    return result;
};
```

Expected improvement: 4-5x reduction in `flattenedTasks` iteration cost.

**FM session reuse (HIGH priority):**

`weeklyReview.js` creates a new `LanguageModel.Session` for each of 6 `getCoaching()` calls. Session creation has overhead (~100-200ms each). Since the system prompt is identical across steps and `respondWithSchema` is stateless per call, reuse one session:

```javascript
const session = new LanguageModel.Session(GTD_COACH);
// Pass session to all 6 getCoaching calls instead of creating new ones
```

Expected improvement: ~500ms-1s saved (5 session creations eliminated).

**Speculative FM prefetch (MEDIUM priority):**

While showing step N's Alert and waiting for user interaction, fire step N+1's FM call in the background:

```javascript
const step2Promise = getCoaching(session, step2Prompt, step2Schema);
const cont1 = await showStep(1, 7, "Get Clear", step1Message);
if (!cont1) return;
const coaching2 = await step2Promise; // likely already resolved
```

Expected improvement: 3-6 seconds saved on weekly review (FM inference overlaps user reading time). Requires validation that OmniAutomation supports concurrent async operations.

**Count-only methods (MEDIUM priority):**

For status computations, avoid creating normalized task objects. Add integer-returning methods that skip `.map(normalizeTask)`:

```javascript
lib.getOverdueCount = function() {
    let count = 0;
    for (const task of flattenedTasks) {
        if (!task.completed && !task.dropped && task.dueDate && task.dueDate < today) count++;
    }
    return count;
};
```

**Batch size validation (LOW priority):**

`hierarchicalBatcher.js` targets ~20K chars (~5000 tokens) per batch. The macOS 26 on-device model context window is estimated at 4096-8192 tokens. The current `estimateTokens` function uses `chars / 4` which underestimates for JSON (should be ~`chars / 3.2`). A 20K char batch could be ~6250 tokens — potentially over budget. Consider reducing to 15K chars to leave headroom. Validate empirically on macOS 26 beta.

**Bundle size impact: None.** Going from 7 to 9 actions in one bundle (~280KB total) will not produce measurable impact on OmniFocus startup. Libraries are loaded lazily. `validate()` calls are lightweight OS version checks (<5ms total for 9 actions).

### Security Considerations

- All FM processing is on-device (Apple Intelligence privacy model)
- Task data (names, notes, projects) sent to on-device model only
- Preference task contains system map — structure metadata only, task content stripped
- No network calls, no external APIs

### Research Insights: Security

**FM privacy assumption:**

Apple Intelligence currently processes Foundation Models requests on-device. However, Apple has a tiered model (on-device + Private Cloud Compute) and the FM API may transparently route requests to PCC for larger prompts. OmniAutomation plugins cannot inspect or control transport routing.

**Recommendations:**
- Document the on-device assumption in the plugin's help/about text
- Minimize prompt content: send task names only, avoid task note content where possible
- Task notes are the most likely place for sensitive data (URLs, passwords, personal details)

**Write operations (v1.1 curation actions):**

When curation actions ship, all write operations need confirmation flows with explicit details:
- `planSelected`: Show proposed subtask names before creation (not just "Create Subtasks?")
- `deferTo`: Show full formatted date with day-of-week + echo original NL input ("You said: 'next tuesday' — Parsed as: Tuesday, March 10, 2026")
- `deferTo`: Add sanity bounds (reject past dates, warn on dates >1 year out)
- `convertToProject`: Show task name, destination folder, structural implications
- `markWaiting`: **Must add confirmation flow** — plan omitted this; accidental trigger completes the original task irreversibly

## System-Wide Impact

### Interaction Graph

Each action -> `preferencesManager.js` (cache read) -> deterministic metrics (`taskMetrics` single-pass) -> FM session (optional coaching via null-return pattern) -> Alert output

Plugin generation: `generate_plugin.js` -> TypeScript validation -> ESLint -> `validate-plugin.sh` -> asset output

### Error Propagation

- FM unavailable: each action degrades gracefully (show deterministic data, skip coaching) — standardize `weeklyReview.js` `getCoaching()` null-return pattern universally
- Preference task missing: first-run detection creates it; actions work without cache in degraded mode
- Synced Preferences project missing: require `SyncedPreferences.omnifocusjs` to be installed; fail with clear error (do not auto-create project)
- macOS < 26: clear Alert with actual OS version shown, action blocked
- JSON parse failure on preference read: treat as first-run, show advisory suggesting `systemSetup`

### State Lifecycle Risks

- **Preference task note corruption:** JSON parse failure on read -> treat as first-run, show advisory (do NOT auto-re-discover — that's a side effect the user didn't request)
- **Concurrent device writes:** iCloud last-writer-wins -> acceptable (system maps should be identical). Add `lastWritten` timestamp + `lastWrittenDevice` for diagnostics.
- **Preference schema versioning:** Integer `schemaVersion` field from day one. Chain-of-migration-functions pattern for future upgrades. Read-repair: migrate on read, write back immediately.
- **Preference task deletion:** User could accidentally complete/drop the task. `findPreferenceTask()` must search regardless of task status.

### API Surface Parity

- All 9 Attache v1.0 actions accessible individually (toolbar, shortcuts, AppleScript)
- Existing Claude Code slash commands (`/ofo:*`) unchanged — they use JXA scripts, not the OmniFocus plugin directly
- The omnifocus-manager SKILL.md needs updating to reference Attache for Pillar 4

### Research Insights: GTD Methodology Alignment

**Weekly review gap — Waiting For step missing:**

The plan's 6-step weekly review omits an explicit Waiting For review. GTD treats Waiting For as a first-class list that must be reviewed weekly. Both the gtd-coach skill (SKILL.md line 88: "Review Waiting For list — follow up on stale items") and the GTD methodology reference include it. Add as step 3 between Project Sweep and Someday/Maybe.

**Revised weekly review flow (7 steps):**
1. Get Clear — Inbox count + mind-sweep prompt
2. Project Sweep — Projects with no next actions, stalled, on hold
3. **Waiting For — Review delegated items, follow up on stale waits** (NEW)
4. Someday/Maybe — Review deferred/on-hold items
5. Completed this week — Celebrate/reflect on finished work
6. Horizon check — Overdue + upcoming next week
7. Planning — AI coaching on priorities for coming week

**Daily review gap — Calendar prompt:**

GTD's daily review starts with calendar because date-specific commitments are non-negotiable anchors. While external calendar is outside OmniFocus scope, the daily review should surface "items due today" and "items with defer dates that just became available" explicitly, and include a text prompt: "Review your calendar for today's commitments."

**Attache persona is strongly aligned with GTD** — "quiet diplomatic aide that knows your system" maps directly to GTD's "trusted system" concept. No concerns here.

## Acceptance Criteria

### Functional Requirements (v1.0)

- [ ] `Attache.omnifocusjs` bundle installs and registers in OmniFocus on macOS 26+
- [ ] All 9 actions appear in OmniFocus Automation menu with "Attache: " prefix
- [ ] `systemSetup` discovers system, caches to both Preferences and task note, shows cached map
- [ ] `dailyReview` shows completed (24h), today's tasks, newly-available deferred items, overdue, with FM coaching and calendar prompt
- [ ] `weeklyReview` runs 7-step GTD review including explicit Waiting For step, with cached system context
- [ ] `analyzeSelected` returns clarity score, name suggestions, tags, time estimate
- [ ] `analyzeProjects` produces project health report (stalled, overdue, completion rate)
- [ ] `analyzeHierarchy` produces full system GTD analysis
- [ ] `analyzeTasksWithAI` (hub) shows analysis with Form options
- [ ] `completedSummary` shows accomplished work (today/week/month) with clipboard output
- [ ] All actions gate on macOS 26 with clear error message showing actual OS version
- [ ] All actions degrade gracefully when FM is unavailable (show data without coaching)
- [ ] Absorbed plugin functionality fully replaced (no feature regression)
- [ ] Preference cache strips task names, AI reasoning, and internal IDs before persisting

### Non-Functional Requirements

- [ ] Bundle ID is `com.totallytools.omnifocus.attache`
- [ ] Preference JSON includes integer `schemaVersion`, `lastWritten` timestamp, `lastWrittenDevice`
- [ ] Plugin passes `validate-plugin.sh` validation
- [ ] `foundationModelsUtils.js` error messages reference macOS 26 (not 15.2)
- [ ] Alert text stays within readable limits (~2000 chars, with truncation)
- [ ] Action labels use "Attache: " prefix in manifest

### Quality Gates

- [ ] Generated via `generate_plugin.js` — no hand-written plugin files
- [ ] All libraries pass `test-plugin-libraries.js`
- [ ] Validated via `bash scripts/validate-plugin.sh`
- [ ] Skillsmith evaluation score >= 85

## Implementation Phases

### Phase 0: Foundation & Bug Fixes (Pre-Attache)

Standalone fixes that ship as AITaskAnalyzer v3.5.0. No new plugin yet.

**Tasks:**
- [ ] Fix `foundationModelsUtils.js` error messages: `15.2` -> `26`, remove iOS hardware references
  - File: `assets/AITaskAnalyzer.omnifocusjs/Resources/foundationModelsUtils.js` (lines 58-59)
  - Note: The actual version GATE logic already checks for `LanguageModel` API existence, not OS version. The bug is in the error *message text* only.
- [ ] Add optional `systemPrompt` parameter to `fmUtils.createSession(systemPrompt?)`
  - Currently: `dailyReview.js` and `weeklyReview.js` bypass fmUtils to pass system prompts
  - After: all actions use `fmUtils.createSession(GTD_COACH)` consistently
- [ ] Standardize FM degradation pattern across all existing actions (adopt weeklyReview null-return)
  - Files: `dailyReview.js` (currently hard-fails on FM error), `analyzeProjects.js`, `analyzeSelectedTasks.js`
  - Pattern: `try { return JSON.parse(await session.respondWithSchema(...)); } catch { return null; }`
- [ ] Fix redundant `fmUtils` re-loading in catch blocks (load once at top, reference in both try and catch)

**Deliverable:** AITaskAnalyzer v3.5.0 with bug fixes.

### Phase 1: Preference Persistence Layer

The core new capability that enables everything else.

**Tasks:**
- [ ] Create `preferencesManager.js` library (~40-60 lines):
  - `findPreferenceTask()` — locate task by name "Attache System Map" in Synced Preferences project; search regardless of completion/dropped status; cache reference in IIFE closure
  - `read()` — check `Preferences` API first (local cache); fall back to `JSON.parse(task.note)`; return null on failure
  - `write(data)` — strip task names, aiReasoning, recommendations, id.primaryKey; add `schemaVersion`, `lastWritten`, `lastWrittenDevice`; write to both `Preferences` API and task note
  - `getOrCreate()` — find task or create in Synced Preferences project
  - Require `SyncedPreferences.omnifocusjs` to be installed; fail with clear error if project missing
- [ ] Create `systemSetup` action — runs `systemDiscovery`, passes result to `preferencesManager.write()`, shows cached map with option to re-discover (replaces both `discoverSystem` and `preferences` actions)
- [ ] Add first-run detection to all actions: check for preference data; if absent, show advisory suggesting `systemSetup`; proceed with degraded output (do NOT auto-discover)

### Research Insights: preferencesManager Implementation

```javascript
// Minimal implementation — 4 core functions
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));
    const TASK_NAME = "Attache System Map";
    const CURRENT_SCHEMA = 1;
    let _cachedTask = null; // IIFE closure cache

    lib.findPreferenceTask = function() {
        if (_cachedTask && _cachedTask.name === TASK_NAME) return _cachedTask;
        const project = flattenedProjects.byName("Synced Preferences");
        if (!project) return null;
        // Search regardless of completion/dropped status
        _cachedTask = project.flattenedTasks.find(t => t.name === TASK_NAME) || null;
        return _cachedTask;
    };

    lib.read = function() {
        // Try local cache first
        const prefs = new Preferences(null);
        const cached = prefs.readString("systemMap");
        if (cached) {
            try { return JSON.parse(cached); } catch {}
        }
        // Fall back to synced task note
        const task = lib.findPreferenceTask();
        if (!task || !task.note) return null;
        try {
            const data = JSON.parse(task.note);
            // Write back to local cache
            prefs.write("systemMap", task.note);
            return data;
        } catch { return null; }
    };

    lib.write = function(data) {
        // Strip sensitive fields
        const safe = { ...data };
        delete safe.tasks; delete safe.aiReasoning; delete safe.recommendations;
        safe.schemaVersion = CURRENT_SCHEMA;
        safe.lastWritten = new Date().toISOString();
        safe.lastWrittenDevice = Device.current.name;
        const json = JSON.stringify(safe, null, 2);
        // Write to both stores
        const task = lib.findPreferenceTask() || lib.getOrCreate();
        task.note = json;
        new Preferences(null).write("systemMap", json);
        save();
    };

    lib.getOrCreate = function() { /* ... */ };
    return lib;
})();
```

**Deliverable:** Preference persistence working, system map cached and readable across devices.

### Phase 2: Bundle Rename & Plugin Absorption

Rename to Attache and absorb the 4 in-repo plugins. **Move migration advisory here** (not Phase 4).

**Tasks:**
- [ ] Create `Attache.omnifocusjs` bundle with new manifest:
  - Bundle ID: `com.totallytools.omnifocus.attache`
  - Version: `1.0.0`
  - 9 actions declared (7 migrated + completedSummary + systemSetup)
  - All action labels prefixed with "Attache: "
- [ ] Migrate all AITaskAnalyzer actions (7) into Attache bundle
  - Refactor `analyzeProjects.js` to use parser libraries instead of inline duplicates
  - Update all `this.plugIn.library()` calls for new bundle identifier
- [ ] Absorb `CompletedTasksSummary` — create `completedSummary` action with period selection (today/week/month) + Alert + clipboard output
- [ ] Absorb `Overview` stats — fold into `dailyReview` orientation section
- [ ] Absorb `TodaysTasks` — fold into `dailyReview` completed+today view
- [ ] Add single-pass `collectAllMetrics()` to `taskMetrics.js`
- [ ] Reuse FM session across weekly review steps (one session, passed to all `getCoaching` calls)
- [ ] Add Waiting For as explicit step 3 in weekly review (7-step flow)
- [ ] Add calendar/due-date prompt to daily review
- [ ] Add migration advisory: on first run, check for installed plugins with known absorbed bundle IDs via `PlugIn.all`, show one-time advisory
- [ ] Update `generate_plugin.js` to support Attache bundle ID

**Deliverable:** `Attache.omnifocusjs` v1.0.0 bundle replacing AITaskAnalyzer + 3 absorbed plugins.

### Phase 3: Polish & Documentation

Final integration, testing, and skill updates.

**Tasks:**
- [ ] End-to-end testing of all 9 actions on macOS 26
- [ ] Validate `hierarchicalBatcher.js` batch sizes against macOS 26 FM context window
- [ ] Update omnifocus-manager SKILL.md to reference Attache (Pillar 4 update)
  - Add guidance: "for quick daily review, use Attache in OmniFocus; for deep system analysis, use Claude Code"
- [ ] Update `generate_plugin.js` templates if needed for Attache patterns
- [ ] Validate with `bash scripts/validate-plugin.sh`
- [ ] Run skillsmith evaluation
- [ ] Add README note: "After installing Attache, you can remove: AITaskAnalyzer, CompletedTasksSummary, Overview, TodaysTasks"

**Deliverable:** Production-ready Attache v1.0.0.

### Future: v1.1 Curation Actions

Ship only if v1.0 user experience reveals genuine gaps not covered by existing plugins.

**Potential actions:** `planSelected`, `estimateSelected`, `deferTo`, `convertToProject`, `markWaiting`

**Prerequisites for each:**
- Confirmation flow with explicit details for all write operations
- `deferTo`: full formatted date with day-of-week, sanity bounds, echo original input
- `markWaiting`: confirmation required (currently unspecified — accidental trigger completes task irreversibly)

## Alternative Approaches Considered

1. **Retrofit AITaskAnalyzer** — Add features to existing bundle without renaming. Rejected: accumulates too much baggage, bundle ID implies single-purpose, no clean break.
2. **Hub-and-spoke architecture** — Central dispatcher calling into separate mini-plugins. Rejected: adds complexity, OmniAutomation doesn't support inter-plugin communication well.
3. **Command palette hub action** — Build an `attache` action as unified entry point. Rejected during deepening: OmniFocus Automation menu IS the palette; `Form.Field.Option` has no in-place mutation API so dynamic filtering requires unproven field replacement; actions cannot invoke sibling actions so dispatch logic must be duplicated.
4. **Approach chosen: Single composable bundle with focused v1.0 scope** — Clean rename, shared libraries, persistent memory, 9 well-tested actions. Curation actions deferred until proven needed.

(see brainstorm: docs/brainstorms/2026-03-08-attache-omnifocus-plugin-brainstorm.md — Architecture section)

## Risk Analysis & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Preference task accidentally deleted/completed | MEDIUM | Lose cached state | `findPreferenceTask()` searches regardless of status; first-run detection re-creates |
| `analyzeProjects.js` refactor introduces regressions | MEDIUM | Broken action | Test against existing behavior before and after parser library migration |
| FM degradation inconsistency across actions | LOW | Poor UX on failure | Phase 0 standardizes null-return pattern before Attache ships |
| iCloud sync conflicts on preferences | LOW | Stale cache on one device | Last-writer-wins acceptable; `lastWritten` timestamp for diagnostics |
| Batcher token budget exceeds macOS 26 context window | LOW | Degraded FM output | Phase 3 empirical validation; reduce to 15K chars if needed |
| Apple changes FM routing to include cloud models | LOW | Privacy assumption violated | Document assumption; minimize prompt content; avoid task notes in prompts |

## Dependencies & Prerequisites

- **macOS 26 beta** — Required for Foundation Models API testing
- **OmniFocus 4** — Required for OmniAutomation PlugIn.Library support
- **`SyncedPreferences.omnifocusjs`** — Must be installed (Attache does NOT create the project)
- **Existing AITaskAnalyzer v3.4.1** — Starting point for code migration
- **`generate_plugin.js`** — Plugin generation toolchain must support new bundle ID

## Open Questions

1. **`completedSummary` output destination** — Clipboard, OmniFocus note, or user's choice? (Non-blocking; default to Alert + Copy pattern)
2. **Form API dynamic filtering** — API docs confirm `Form.validate` can add/remove fields, but `Form.Field.Option` has no in-place mutation. Field replacement is theoretically possible but UX quality unknown. (Informational only — command palette cut from v1.0)
3. **`functionLibrary.omnifocusjs` audit** — Which functions are worth absorbing? (v1.1 research task; gate: only absorb functions called by absorbed plugins)
4. **FM speculative prefetch** — Does OmniAutomation support concurrent async operations? (v1.0 optimization opportunity if validated)

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-08-attache-omnifocus-plugin-brainstorm.md](docs/brainstorms/2026-03-08-attache-omnifocus-plugin-brainstorm.md)
  - Key decisions: single composable bundle, persistent memory via Synced Preferences task, macOS 26 gate, `com.totallytools.omnifocus.attache` bundle ID
  - Scope reduction during deepening: 14 actions -> 9 for v1.0; command palette deferred
- **Related brainstorms:**
  - [docs/brainstorms/2026-02-27-omnifocus-review-actions-brainstorm.md](docs/brainstorms/2026-02-27-omnifocus-review-actions-brainstorm.md) — dailyReview + weeklyReview design decisions
  - [docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md](docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md) — channel selection layer, JXA validation pipeline

### Internal References

- Plugin manifest: `plugins/omnifocus-manager/skills/omnifocus-manager/assets/AITaskAnalyzer.omnifocusjs/manifest.json`
- FM utilities: `assets/AITaskAnalyzer.omnifocusjs/Resources/foundationModelsUtils.js` (OS version bug at lines 58-59 — message text only)
- System discovery: `assets/AITaskAnalyzer.omnifocusjs/Resources/systemDiscovery.js` (keep pure, do not add cache logic)
- Weekly review FM pattern: `assets/AITaskAnalyzer.omnifocusjs/Resources/weeklyReview.js` (getCoaching null-return, per-call sessions, concurrency guard)
- Task metrics: `assets/AITaskAnalyzer.omnifocusjs/Resources/taskMetrics.js` (needs single-pass refactor)
- Hierarchical batcher: `assets/AITaskAnalyzer.omnifocusjs/Resources/hierarchicalBatcher.js` (batch size validation needed)
- OmniFocus API: `references/OmniFocus-API.md` (line 1286: Form.validate can add/remove fields)
- Foundation Models: `references/foundation_models_integration.md` (complete FM API reference)
- TypeScript declarations: `typescript/omnifocus.d.ts` (Form.Field.Option — no mutation methods)
- Plugin generator: `scripts/generate_plugin.js`
- Validation: `scripts/validate-plugin.sh`
- Automation decision framework: `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md`

### Institutional Learnings Applied

- **JXA validation asymmetry** — Omni Automation plugins catch 95%+ errors at build time; JXA only at runtime. Attache benefits from the plugin validation pipeline. (docs/lessons/omnifocus-manager-refinement-2026-01-18.md)
- **80/15/5 rule** — Execute existing scripts (80%), compose from libraries (15%), generate novel code (5%). Attache follows this by reusing 8 existing libraries. (docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md)
- **Self-improvement loop** — Fix bugs across all affected files, document in references, update guides. Applied: Phase 0 standardizes FM patterns across all actions before migration. (docs/lessons/omnifocus-manager-refinement-2026-01-18.md)
- **Plugin evolution stages** — Stage 2 (Plugin+Commands) is the right level; don't force Stage 3 agents unless autonomous orchestration is needed. Attache is a Stage 2 enhancement. (docs/lessons/plugin-integration-and-architecture.md)

### Related Work

- IMPROVEMENT_PLAN: `plugins/omnifocus-manager/skills/omnifocus-manager/IMPROVEMENT_PLAN.md` (v6.5.0 current)
- Recent issues: #84 (ofo: commands), #90 (GTD analysis), #80 (perspectives), #76 (channel selection)

---

## Appendix: CoSAI AI Risk Assessment (Informational)

A CoSAI Risk Map assessment was run against this plan on 2026-03-08. Full automated report at `docs/plans/attache-risk-assessment/ai_security_assessment.md`.

**Triage summary:** Of 26 generic CoSAI risks identified, **6 genuinely apply** to Attache's sandboxed, single-user, on-device architecture. 15 are not applicable (no model training, no multi-tenancy, no network access). Overall risk posture: **LOW**.

**Applicable risks (contextualized):**

| Risk | Severity | Attache Context | Plan Status |
|------|----------|----------------|-------------|
| **[PIJ] Prompt Injection** | Low-Med | Task names in FM prompts could manipulate output. Impact limited: output is advisory (v1.0) or confirmed before write (v1.1). `respondWithSchema` constrains format. | Partially mitigated. Consider truncating task names (~200 chars) and bounds-checking numeric outputs. |
| **[SDD] Sensitive Data Disclosure** | Medium | Task names may contain sensitive info; sent to on-device FM. `collectTaskSample()` could leak task names into preference cache. Apple could change FM routing to cloud (PCC). | Mitigated by cache allowlist (strips tasks, aiReasoning, IDs). FM routing is accepted dependency on Apple's privacy model. |
| **[RA] Rogue Actions** | Low-Med | v1.1 write operations (subtask creation, task completion, defer dates) are irreversible. FM misparse could cause unintended changes. | Mitigated by confirmation flows. Gap found: `markWaiting` needs confirmation (added to plan). Add `console.log` audit trail. |
| **[IMO] Insecure Model Output** | Low | FM coaching could be incorrect (hallucinated tag names, bad estimates). Advisory-only in v1.0. | Partially mitigated by schema constraints. Consider validating suggested tags exist in database. |
| **[EDH-I] Excessive Data Handling** | Low | FM prompts include task names across multiple actions. Task notes should NOT be sent where names suffice. | Planned. Document what data is sent to FM. |
| **[PCP] Cache Poisoning** | Low | Preference cache (task-note JSON) could be corrupted via sync conflict or manual edit. | Mitigated by schema version check, corrupt JSON graceful degradation, `lastWritten` timestamp. |

**Not applicable (15 risks):** Data Poisoning, Model Source Tampering, Model Exfiltration, Model Reverse Engineering, Unauthorized Training Data, Excessive Data Handling (Training), Denial of ML Service, Accelerator Side-channels, Economic Denial of Wallet, Federated Training Privacy, Adapter Injection, Evaluation Manipulation, Covert Channels, Malicious Loader, Vector Store Poisoning. All relate to model training, multi-tenancy, or network-accessible infrastructure that Attache does not have.

**Key OWASP LLM Top 10 mappings:** LLM01 (Prompt Injection) via task names, LLM06 (Sensitive Information Disclosure) via FM prompts and preference cache, LLM08 (Excessive Agency) via v1.1 write operations.

This assessment is informational. Future plan iterations may or may not need to act on these findings.
