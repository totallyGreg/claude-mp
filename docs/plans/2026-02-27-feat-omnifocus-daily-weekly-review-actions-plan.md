---
title: "feat: Add dailyReview and weeklyReview actions to AITaskAnalyzer"
type: feat
date: 2026-02-27
plugin: omnifocus-manager
brainstorm: docs/brainstorms/2026-02-27-omnifocus-review-actions-brainstorm.md
deepened: 2026-02-27
---

# feat: Add dailyReview and weeklyReview actions to AITaskAnalyzer

## Enhancement Summary

**Deepened on:** 2026-02-27
**Research agents used:** architecture-strategist, performance-oracle, julik-frontend-races-reviewer, code-simplicity-reviewer, framework-docs-researcher, best-practices-researcher

### Key Improvements Discovered

1. **Version bump correction**: Use `3.4.0` not `4.0.0` — these are additive actions, no breaking changes
2. **Critical performance fix**: Replace `p.flattenedTasks.filter(available)` with `p.numberOfAvailableTasks` scalar — eliminates O(n×m×3) traversal in `getStalledProjects()`
3. **Eliminate duplication**: `getStalledProjects()` in taskMetrics duplicates `projectParser.identifyStalledProjects()` — route through existing function
4. **Per-step FM isolation**: Every `respondWithSchema()` call needs its own try/catch; FM failure mid-review must not abort the entire flow
5. **Concurrency guard**: Module-level `_reviewInProgress` flag prevents double-invocation during long FM calls
6. **Token budget discipline**: Apple Foundation Models practical limit is `< 1000 tokens` — cap all data inputs, use labeled concise sections, set GTD persona in session constructor not per-prompt
7. **Schema format**: OmniFocus uses its own `LanguageModel.Schema.fromJSON({ properties: [...] })` format — NOT JSON Schema
8. **Step 6 simplicity**: Accumulated `reviewSummary` for final FM synthesis = 4 scalar numbers only (inboxCount, stalledCount, overdueCount, completedCount)

### New Risks Identified

- `getStalledProjects()` O(n×m) scan could freeze OmniFocus on databases with 200+ projects — use `numberOfAvailableTasks` scalar immediately
- Sequential FM calls across 6 steps: estimated 18–60 seconds total — user needs progress indication at each step
- No concurrent-invocation protection in existing actions either — this is a new pattern to establish

---

## Overview

Add two new actions to the existing `AITaskAnalyzer.omnifocusjs` plugin bundle that support daily and weekly GTD review workflows — all running on-device via Apple Foundation Models with no Claude required.

**Daily review**: Morning/evening check-in showing completed work + upcoming tasks + GTD coaching.
**Weekly review**: Step-by-step guided GTD weekly review using sequential Alert dialogs with Foundation Models coaching at each of 6 GTD horizons.

## Problem Statement / Motivation

The existing `analyzeTasksWithAI` action analyzes today's + overdue tasks but has four gaps:
1. **No completed tasks** — can't see what was accomplished
2. **Generic prompts** — insufficient GTD coaching depth (no next-action vocabulary, project health framing)
3. **Context overflow** — hard cap at 10 tasks each loses signal from larger systems
4. **No weekly review** — no guided path through the GTD weekly review checklist

Users must run Claude for complex GTD reviews. The goal is a self-sufficient OmniFocus plugin.

## Proposed Solution

Add two new actions to the existing bundle. Extend `taskMetrics.js` with missing query methods. Improve Foundation Models prompt quality across both new actions. Keep all 5 existing actions unchanged.

### dailyReview action

Collects: completed today (`getCompletedToday()`) + today's tasks (`getTodayTasks()`) + overdue (`getOverdueTasks()`) + flagged (`getFlaggedTasks()`).

Sends to Foundation Models with a GTD-specific prompt that asks for:
- Celebration / pattern recognition on completed work
- Top 3 next actions for the remainder of the day
- Overdue triage recommendations
- Workload assessment using GTD language (not just "manageable/heavy")

Output displayed in an Alert with clipboard export option. Same pattern as `analyzeTasksWithAI` but with completed tasks added and richer prompt.

### weeklyReview action (step-by-step flow)

Sequential Alert/Form dialogs guide user through 6 GTD horizons. Foundation Models coaches at each step using the collected data.

| Step | GTD Horizon | Data Queried | FM Coaching |
|------|------------|--------------|-------------|
| 1 | Get Clear (Inbox) | `inboxTasks.length`, oldest item age | Process-to-zero strategy |
| 2 | Projects Sweep | Stalled projects (no next actions), on-hold count | Next action suggestions per stalled project |
| 3 | Someday/Maybe | On-hold projects not reviewed >90 days | Re-commit vs archive recommendations |
| 4 | Celebrate & Reflect | `getCompletedThisWeek()` grouped by project | Completion pattern insights, wins to acknowledge |
| 5 | Horizon Check | Overdue + due next 7 days | Realistic rescheduling recommendations |
| 6 | Plan the Week | Synthesizes all prior steps | Top weekly priorities, system health score |

Each step shows data + FM coaching, then offers **Continue / Stop** so user can exit early.

### Research Insights — Weekly Review UX

**Step ordering matters (GTD's "Get Clear before Get Current" principle):**
The canonical GTD order and the production `weekly-review.js` reference both validate: inbox → overdue → stalled projects → someday/maybe → week preview. The current 6-step plan already follows this — steps 1–6 are in the right order.

**Minimum Viable Review:** Three numbers surface the most actionable signal: inbox count, stalled project count, overdue task count. Step 1 of the flow should lead with these three numbers as a health snapshot before diving into details.

**"Stop Review" vs native Escape:** The second button on each Alert step can be removed or made "Done for now" — native macOS dismiss (Escape key / clicking outside) already cancels the Alert. This reduces button noise at each step.

**Empty-state acknowledgment:** When a step finds no data (e.g., inbox already empty), show `"✓ Nothing to review here"` and skip the FM call entirely. Still require the user to press Continue to confirm the step was reviewed.

---

## Technical Considerations

### Files to Modify

**`assets/AITaskAnalyzer.omnifocusjs/manifest.json`**
- Add two new action declarations:
  - `{ "identifier": "dailyReview", "image": "sun.horizon" }`
  - `{ "identifier": "weeklyReview", "image": "calendar.badge.checkmark" }`
- No new libraries needed (all data queries go into `taskMetrics.js`)
- **Bump version to `3.4.0`** (minor additive — 2 new actions, no breaking changes)

> **Architecture Note:** `4.0.0` was the original plan, but these are purely additive actions. Existing actions and library APIs are unchanged. Semantic versioning convention in this bundle: major = breaking API change, minor = new actions. Use `3.4.0`.

**`assets/AITaskAnalyzer.omnifocusjs/Resources/taskMetrics.js`**

Add three new methods (see corrected implementations below).

**`assets/AITaskAnalyzer.omnifocusjs/Resources/en.lproj/manifest.strings`** *(required — was missing from original plan)*

Must add localized labels for both new actions. Follow the existing pattern:

```
"dailyReview.label" = "Daily Review";
"dailyReview.shortLabel" = "Daily";
"dailyReview.mediumLabel" = "Daily Review";
"weeklyReview.label" = "Weekly Review";
"weeklyReview.shortLabel" = "Weekly";
"weeklyReview.mediumLabel" = "Weekly Review";
```

Without these entries, the OmniFocus menu will show raw identifiers instead of human-readable labels.

### Files to Create

**`assets/AITaskAnalyzer.omnifocusjs/Resources/dailyReview.js`**

Pattern: same IIFE + `PlugIn.Action` as `analyzeTasksWithAI.js`. Load `fmUtils`, check availability, collect data from taskMetrics, build enriched GTD prompt, call `respondWithSchema()`, display in Alert.

Key prompt improvement over `analyzeTasksWithAI`:
```
COMPLETED TODAY (${completedCount} tasks):
${completedSummary}

NEXT ACTIONS FOR TODAY (${todayCount} total, showing ${shown}):
${todayTaskSummary}

OVERDUE (${overdueCount} tasks, showing ${shown}):
${overdueTaskSummary}

Using GTD principles, provide:
1. A brief celebration of what was accomplished
2. Top 3 concrete next actions to take now (specific, physical, visible)
3. Overdue triage: which to do today, which to defer, which to drop
4. Honest workload assessment: is this system in control or overwhelmed?
```

Schema adds `completedHighlights` array alongside existing `priorityRecommendations` etc.

**`assets/AITaskAnalyzer.omnifocusjs/Resources/weeklyReview.js`**

Sequential Alert flow with concurrency guard and per-step FM isolation:

```javascript
// Module-level concurrency guard (prevents double-invocation during long FM calls)
let _reviewInProgress = false;

// Each step: collect data → FM coaching (with try/catch) → Alert → Continue/Stop
for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const data = step.query();

    // Empty-state: skip FM call, show acknowledgment
    if (step.isEmpty(data)) {
        const alert = new Alert(`Step ${i+1} of 6: ${step.name}`, "✓ Nothing to review here.");
        alert.addOption("Continue");
        await alert.show();
        continue;
    }

    // Per-step FM isolation — failure here must not abort the review
    let coaching = null;
    try {
        const session = new LanguageModel.Session(GTD_COACH_INSTRUCTIONS);
        coaching = JSON.parse(await session.respondWithSchema(
            buildPrompt(step, data),
            step.schema,
            null
        ));
    } catch (fmError) {
        // FM unavailable or timed out — show data without coaching
        coaching = { note: "AI coaching unavailable for this step." };
    }

    const message = formatStep(step, data, coaching);
    const alert = new Alert(`Weekly Review: Step ${i+1} of 6 — ${step.name}`, message);
    alert.addOption("Continue");
    alert.addOption("Stop Review");
    const choice = await alert.show();
    if (choice === 1) break; // Stop Review
}
```

> **Architecture Note:** Create one `new LanguageModel.Session()` per step (not one shared session). A shared session accumulates context across 6 steps and risks overflow. Per-step sessions are isolated and context-bounded.

**`assets/AITaskAnalyzer.omnifocusjs/Resources/en.lproj/manifest.strings`**

Add localized labels as shown above.

### taskMetrics.js — Corrected Implementations

```javascript
// For weeklyReview step 4 (completed this week)
// Cap at 100 to avoid scanning full task history
lib.getCompletedThisWeek = function() {
    const today = new Date();
    today.setHours(23, 59, 59, 999);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    weekAgo.setHours(0, 0, 0, 0);

    return flattenedTasks.filter(task => {
        if (!task.completed) return false;
        const d = task.completionDate;
        return d && d >= weekAgo && d <= today;
    }).slice(0, 100).map(lib.normalizeCompletedTask.bind(lib));
};

// For weeklyReview step 2 (project sweep)
// IMPORTANT: Use p.numberOfAvailableTasks (precomputed scalar) NOT p.flattenedTasks.filter()
// p.flattenedTasks.filter() triggers O(n) traversal per project → O(n×m) total
// Cap at 50 active projects to prevent freeze on large databases
lib.getStalledProjects = function() {
    return flattenedProjects.filter(p => {
        if (p.status !== Project.Status.Active) return false;
        return p.numberOfAvailableTasks === 0 && p.flattenedTasks.length > 0;
    }).slice(0, 50).map(p => ({
        name: p.name,
        taskCount: p.flattenedTasks.length,
        lastModified: p.modified
    }));
};
// NOTE: Before implementing, check if projectParser.js has identifyStalledProjects()
// If it does, route through projectParser to avoid duplication.

// For weeklyReview step 3 (someday/maybe)
// Hardcode 90 days — parameterizing this is YAGNI at this stage
// Cap at 100 on-hold projects
lib.getOnHoldProjects = function() {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 90);

    return flattenedProjects.filter(p => {
        return p.status === Project.Status.OnHold &&
               (!p.modified || p.modified < cutoff);
    }).slice(0, 100).map(p => ({
        name: p.name,
        lastModified: p.modified
    }));
};
```

### Research Insights — taskMetrics.js

**Performance: `getStalledProjects()` is the critical path**

The naive implementation (`p.flattenedTasks.filter(t => t.taskStatus === Task.Status.Available)`) is O(n×m×3) because:
- It iterates `flattenedProjects` (n projects)
- For each project, iterates `flattenedTasks` twice (once for filter, once for `.length`)
- Then maps over the result for `.length` again

`p.numberOfAvailableTasks` is a precomputed scalar on the OmniFocus `Project` class — use it. The check becomes `p.numberOfAvailableTasks === 0` — O(1) per project.

**Duplication check: verify against `projectParser.js`**

Before implementing `getStalledProjects()` in `taskMetrics.js`, read `projectParser.js` (already a declared library in `manifest.json`). If `identifyStalledProjects()` exists there, use it via `PlugIn.find("com.omnigroup.AITaskAnalyzer").libraries.projectParser.identifyStalledProjects()`. Adding the same logic to `taskMetrics.js` creates a maintenance burden when the OmniFocus API changes.

**`getCompletedThisWeek()` scope**

`flattenedTasks` includes completed tasks for the entire history of the database. On long-running OmniFocus databases (3+ years), this can be thousands of tasks. The `.slice(0, 100)` cap prevents slow iteration. Alternatively, consider whether a date-ranged filter from `flattenedProjects` (tasks only from active projects) would be a better scope — but this would miss inbox tasks and tasks in completed projects.

### Research Insights — Apple Foundation Models API

**Confirmed `respondWithSchema()` signature:**
```javascript
session.respondWithSchema(
    prompt: String,
    schema: LanguageModel.Schema,
    generationOptions: LanguageModel.GenerationOptions | null
): Promise<String>  // Returns JSON string — always JSON.parse() the result
```

**Schema format — OmniFocus custom format, NOT JSON Schema:**
```javascript
// CORRECT
const schema = LanguageModel.Schema.fromJSON({
    name: "daily-review-schema",
    properties: [
        { name: "completedHighlights" },          // required string
        { name: "topThreeActions", schema: {       // array of objects
            arrayOf: {
                name: "action-item",
                properties: [
                    { name: "task" },
                    { name: "reason" }
                ]
            }
        }},
        { name: "overdueAdvice" },
        { name: "workloadAssessment" },
        { name: "systemHealth", schema: {          // enum constant
            anyOf: [
                { constant: "in-control" },
                { constant: "manageable" },
                { constant: "overwhelmed" }
            ]
        }}
    ]
});

// WRONG — does not work with OmniFocus LanguageModel API
new LanguageModel.Schema({ type: "object", properties: { ... } });
```

**Token budget: < 1000 tokens practical limit**

Each prompt (system instructions + data payload + output request) must stay under ~700–800 tokens:
- Session instructions: 50–100 tokens (set once, not per-prompt)
- Data payload: max 10 items × ~50 chars each = ~500 tokens
- Output request: 50–100 tokens
- Reserve 300–400 tokens for response

**GTD persona in session constructor, not per-prompt:**
```javascript
const GTD_COACH_INSTRUCTIONS =
    "You are a GTD productivity coach. Be concise. Focus on actionable next steps. " +
    "Use specific GTD vocabulary: next actions, projects, contexts, weekly review.";

// Create per step (not shared across steps)
const session = new LanguageModel.Session(GTD_COACH_INSTRUCTIONS);
```

**Always guard optional schema fields:**
```javascript
const result = JSON.parse(await session.respondWithSchema(prompt, schema, null));
// Guard every optional field
const highlights = result.completedHighlights || "No completed tasks today.";
const actions = Array.isArray(result.topThreeActions) ? result.topThreeActions : [];
```

**Generation options for response length control:**
```javascript
const opts = new LanguageModel.GenerationOptions();
opts.maximumResponseTokens = 200;  // Keep responses concise for Alert display
const json = await session.respondWithSchema(prompt, schema, opts);
```

### Context Window Strategy for weeklyReview

Each step sends a small, focused prompt to Foundation Models — NOT one big batch:
- Step 1 (inbox): just 2 numbers (inboxCount, oldest item age in days) — ~20 tokens
- Step 2 (stalled projects): max 10 project names × ~30 chars = ~75 tokens
- Step 3 (someday/maybe): max 10 on-hold project names — ~75 tokens
- Step 4 (completed this week): max 10 task names grouped by project — ~100 tokens
- Step 5 (horizon): overdue count + upcoming count + top 5 task names — ~75 tokens
- Step 6 (planning synthesis): **4 scalar numbers only** — `{ inboxCount, stalledCount, overdueCount, completedThisWeek }` — ~20 tokens

No need for `hierarchicalBatcher` in these actions.

> **Simplicity Note:** Step 6's `reviewSummary` should be exactly these 4 scalars. Passing raw task lists from prior steps into the final FM call risks exceeding token budget and produces less focused synthesis. The FM has enough signal from counts alone to generate weekly priorities.

### Concurrency Guard Pattern

```javascript
// At module scope (outside the PlugIn.Action IIFE)
let _reviewInProgress = false;

// Inside weeklyReview action:
perform: async function(selection) {
    if (_reviewInProgress) {
        const alert = new Alert("Weekly Review", "A review is already in progress.");
        alert.addOption("OK");
        await alert.show();
        return;
    }
    _reviewInProgress = true;
    try {
        // ... review flow ...
    } finally {
        _reviewInProgress = false;  // Always release, even on error
    }
}
```

### Generation Workflow

Since these are additions to an EXISTING bundle (not a new plugin), `generate_plugin.js` is used only for bootstrapping action scaffolds. The actual files are written following the established IIFE + `PlugIn.Action` pattern from `analyzeHierarchy.js`.

Reference pattern: `assets/AITaskAnalyzer.omnifocusjs/Resources/analyzeTasksWithAI.js` (for FM integration) and `assets/CompletedTasksSummary.omnifocusjs/Resources/copyToClipboard.js` (for minimal non-FM pattern).

Also reference: `assets/examples/jxa-scripts/weekly-review.js` for GTD health metric patterns (note: this is JXA not Omni Automation — adapt the logic but not the API calls).

---

## Acceptance Criteria

### dailyReview action
- [ ] Action appears in Tools → AI Analyzer → Daily Review (or equivalent menu path)
- [ ] Collects completed tasks from `getCompletedToday()` — shows count even if 0
- [ ] Collects today's tasks, overdue tasks, flagged tasks
- [ ] Sends enriched GTD prompt to Foundation Models with persona set in session constructor
- [ ] Response schema uses OmniFocus `LanguageModel.Schema.fromJSON()` format (not JSON Schema)
- [ ] Response includes: completed celebration, top 3 next actions, overdue triage, workload assessment
- [ ] Output displays in Alert with "Copy to Clipboard" and "Done" options
- [ ] Falls back gracefully if no tasks found (appropriate empty-state messages)
- [ ] `validate` returns false if `operatingSystemVersion < 26` (FM requirement)
- [ ] FM failure shows inline "AI unavailable" message in Alert — does not throw uncaught error

### weeklyReview action
- [ ] Action appears in Tools → AI Analyzer → Weekly Review
- [ ] Module-level `_reviewInProgress` flag prevents concurrent invocations
- [ ] Presents 6 sequential Alert steps, each labeled with step number (e.g., "Step 2 of 6")
- [ ] Each step shows relevant raw data + FM coaching in the Alert body
- [ ] "Stop Review" button exits the flow at any step without error; `_reviewInProgress` released
- [ ] Empty-state steps show "✓ Nothing to review here" and skip FM call
- [ ] Step 1 (Inbox): shows inbox item count + oldest age + FM processing advice
- [ ] Step 2 (Projects): shows stalled project names + count + FM next-action suggestions
- [ ] Step 3 (Someday/Maybe): shows neglected on-hold projects + FM re-evaluate advice
- [ ] Step 4 (Celebrate): shows completed tasks this week grouped by project + FM pattern insights
- [ ] Step 5 (Horizon): shows overdue count + upcoming next 7 days + FM rescheduling advice
- [ ] Step 6 (Plan): FM synthesizes `{ inboxCount, stalledCount, overdueCount, completedThisWeek }` into weekly priorities
- [ ] Final step offers "Copy Weekly Summary" to clipboard
- [ ] `validate` returns false if `operatingSystemVersion < 26`

### taskMetrics.js extensions
- [ ] `getCompletedThisWeek()` returns tasks completed in last 7 days (calendar, not rolling 24h), capped at 100
- [ ] `getStalledProjects()` uses `p.numberOfAvailableTasks === 0` (NOT `p.flattenedTasks.filter()`), capped at 50
- [ ] `getOnHoldProjects()` returns on-hold projects not modified in 90 days (hardcoded), capped at 100
- [ ] All new methods follow existing `normalizeTask` / `normalizeCompletedTask` return shapes
- [ ] Check if `projectParser.identifyStalledProjects()` exists — if so, use it instead of duplicating

### manifest and localization
- [ ] `manifest.json` version bumped to `3.4.0` (not `4.0.0`)
- [ ] `en.lproj/manifest.strings` contains labels for both new actions (label, shortLabel, mediumLabel)

### No regressions
- [ ] All 5 existing actions (`analyzeTasksWithAI`, `analyzeProjects`, `analyzeSelectedTasks`, `analyzeHierarchy`, `discoverSystem`) continue to function
- [ ] Plugin reinstalls cleanly (no manifest validation errors)
- [ ] Bundle validates via `scripts/validate-plugin.sh`

---

## Dependencies & Risks

**Dependency**: OmniFocus 4.8+ / macOS 26+ (same as existing AI actions). No new dependencies.

**Risk: `getStalledProjects()` query performance** — MITIGATED. Use `p.numberOfAvailableTasks` (precomputed scalar) instead of `p.flattenedTasks.filter()`. Cap at 50 active projects.

**Risk: weeklyReview session reuse** — MITIGATED. Create one `new LanguageModel.Session()` per step, not shared. Per-step sessions prevent context accumulation and timeout risk.

**Risk: Total weeklyReview duration** — 6 sequential FM calls × 3–10 seconds each = 18–60 seconds total. Mitigate with a brief "Generating coaching…" note in the Alert title or body before the FM call resolves. Consider showing data first, then replacing with "Loading..." state — but Alert content is static once shown, so the practical mitigation is to show the Alert header immediately and mention coaching is being generated in the initial body text.

**Risk: `Project.Status.OnHold` API availability** — Check `typescript/omnifocus.d.ts` for the enum values. If `OnHold` is not available, fall back to checking `p.status.name === "on hold"` (string comparison).

**Risk: `inboxTasks` global** — If not available in plugin context, filter `flattenedTasks` where `containingProject === null`. This is the documented fallback.

**Risk: FM failure mid-review** — MITIGATED by per-step try/catch. FM failure shows inline message; review continues with data displayed. User does not lose review progress.

**Risk: Double-invocation** — MITIGATED by `_reviewInProgress` flag with `finally` release.

---

## Implementation Clarifications (from SpecFlow Analysis + Research)

| Decision | Default Assumption | Why It Matters |
|----------|-------------------|----------------|
| "Last 24hrs" vs calendar day for `dailyReview` | Use **calendar day** (midnight to now) — consistent with existing `getCompletedToday()` | A rolling 24hr window is a different query; pick one convention |
| "Someday/Maybe" definition in `weeklyReview` Step 3 | Query **on-hold projects** (`Project.Status.OnHold`) not modified in >90 days (hardcoded) | OmniFocus has no native Someday/Maybe — convention varies by user setup |
| Session strategy for `weeklyReview` | **One new `LanguageModel.Session()` per step** — isolated, not shared | Reusing one session accumulates context and risks overflow across 6 steps |
| FM failure mid-review | **Continue with data displayed** (inline "AI unavailable" note), do not abort | Aborting on step 3 of 6 loses all review progress |
| Empty-state steps in `weeklyReview` | Show "✓ Nothing to review here" message, **skip AI call**, require Continue | No data = no useful coaching; still allow user to acknowledge the step |
| "Done" button availability | Available **at every step** (early exit), not just final step | Trapping user until step 6 is a UX problem for long reviews |
| Step 6 data source (planning) | Use **4 scalar numbers only**: `{ inboxCount, stalledCount, overdueCount, completedThisWeek }` | Raw task lists exceed token budget; scalars give FM enough signal to synthesize |
| Project review date update | **Do not update** OmniFocus native review dates | Risky write operation; defer to a future version |
| Capture during review | **Not included** in v1 — user uses native Quick Entry | Adds complexity; out of scope for initial implementation |
| `inboxTasks` global availability | If not available, filter `flattenedTasks` where `containingProject === null` | Verify in OmniFocus API; fallback is safe |
| Version bump | **3.4.0** not 4.0.0 | Additive actions, no breaking API changes |
| `getStalledProjects()` parameter | **None** — hardcode 0 available tasks threshold | Parameterizing is YAGNI; the definition of "stalled" is stable |
| `getOnHoldProjects()` parameter | **None** — hardcode 90 days | Parameterizing `daysSinceReview` is YAGNI |
| Schema format | **OmniFocus `LanguageModel.Schema.fromJSON()`** — NOT JSON Schema | This is a breaking difference; wrong format produces no output |

---

## References & Research

### Internal References
- Existing FM action pattern: `assets/AITaskAnalyzer.omnifocusjs/Resources/analyzeTasksWithAI.js`
- Existing form/multi-step pattern: `assets/AITaskAnalyzer.omnifocusjs/Resources/analyzeHierarchy.js`
- Completed task query pattern: `assets/AITaskAnalyzer.omnifocusjs/Resources/taskMetrics.js:78`
- GTD detection patterns: `references/insight_patterns.md`
- GTD vocabulary and weekly review definition: `references/gtd_guide.md`
- Weekly review JXA reference (adapt logic only): `assets/examples/jxa-scripts/weekly-review.js`
- FM utility helpers: `assets/AITaskAnalyzer.omnifocusjs/Resources/foundationModelsUtils.js`
- Bundle validation: `scripts/validate-plugin.sh`
- Enforcement patterns (avoid version bump mistakes): `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`
- LanguageModel API type definitions: `typescript/omnifocus-extensions.d.ts`
- Schema format and token budget rules: `references/code_generation_validation.md`
- Stalled project detection: `assets/AITaskAnalyzer.omnifocusjs/Resources/projectParser.js` *(check for `identifyStalledProjects()` before reimplementing)*

### Related Work
- Brainstorm: `docs/brainstorms/2026-02-27-omnifocus-review-actions-brainstorm.md`
- GitHub Issue: #62 (active tracking)
- OmniFocus Omni Automation API: https://omni-automation.com/omnifocus/
