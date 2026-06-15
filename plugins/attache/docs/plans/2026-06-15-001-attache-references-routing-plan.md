# Attache OmniFocus Skill — Routing, References, and Shared-Library Doctrine

## Context

The attache plugin contains four skills that interact with OmniFocus, but the agent currently doesn't reliably distinguish *which channel* to use for a given request — `ofo` CLI, an Attache plugin action, a standalone `.omnifocusjs` plugin, or ad-hoc JXA. The result is reinvented functions, inconsistent quality, and wasted tokens when the agent reads broad reference documents to answer narrow questions.

The user wants three things wired together:

1. **A deterministic routing framework** so the agent (and any agent invoking it) knows when to extend the CLI vs. extend the Attache plugin vs. spin up a standalone plugin vs. use JXA.
2. **A shared-library doctrine** that prevents reinvention — `ofo-core.ts` already serves as both the CLI dispatch core and a `PlugIn.Library` baked into `Attache.omnifocusjs`. Generated plugins should consume it (via `PlugIn.find(...).library("ofoCore")`) rather than reimplement task CRUD.
3. **A reorganized reference tree under `omnifocus-generator/references/`** that uses progressive disclosure so the agent reads ≤3 small docs instead of one 177KB monolith — including a re-runnable workflow to refresh the capability inventory from `omni-automation.com` without burning tokens during normal work.

The Foundation Models task-organizer plugin is the **acceptance test**, not a shipped deliverable: if the references are right, a fresh agent on a different machine can build it end-to-end via the foundry plugin's evaluate→explain→fix→re-evaluate loop without needing WebFetch.

A separate concern, equally important: **the core library (`ofo-core.ts`) must answer every coaching question the gtd-coach skill is going to ask.** Today, four of the seven canonical coaching queries (Waiting For aging, Someday/Maybe review, neglected projects, recently completed) are stuck in `gtd-queries.js` JXA — violating the user's stated principle of preferring CLI over JXA for production agent workflows. Project lifecycle gaps (create, status changes, review marking) compound the problem. This plan adds a **D6** deliverable that closes the GTD essentials in `ofoCore` so the shared library is a credible foundation for the doctrine in D3.

**And the foundation under D6:** GTD queries cannot assume how a given user organizes their OmniFocus database. "What's in Waiting For?" depends on whether the user uses a `@Waiting` tag, a `Waiting For` folder, a `Status: Waiting` convention, or something else entirely. The answer lives in the **Attache System Map** — a JSON document produced by `systemDiscovery.discoverSystem()` and currently stored in the note field of a task named "Attache System Map". The infrastructure exists; today it's used opportunistically by gtd-coach (the "System Context" section) but is not treated as a contract. The map can also drift as the user adds tags, restructures folders, or changes conventions. This plan adds a **D7** deliverable that elevates the System Map to a first-class, schema-versioned, drift-aware contract that every D6 query depends on — so an agent on another machine knows: *(1) the map is the source of truth for conventions, (2) here is how to refresh it, (3) here is how to detect when it's stale.*

Issues touching this surface: **#141** (CLI gaps), **#135** (plugin reload), **#161** (unsafe ops + missing project create/move), **#152** (validation handoff), **#177** (agent orchestration scope). **The GTD-essential subsets of #141 and #161 move into D6 scope; everything else remains follow-up.**

## Outcomes

When done, the following are true:

1. `plugins/attache/agents/attache.md` contains a **Channel Selection** section with a decision tree distinguishing the four channels (CLI, Attache action, standalone plugin, JXA) and acceptance examples for each.
2. `plugins/attache/skills/omnifocus-generator/references/` is reorganized into a hierarchical tree with a 00_index.md entry point. The 177KB `omnifocus_api.md` is moved/linked once (no duplication between `omnifocus-core` and `omnifocus-generator`).
3. A new doctrine doc (`40_patterns/library_consumer_pattern.md`) tells the generator: *before generating new code, check whether `ofoCore` already exposes the function*. The generator SKILL.md workflow gains a STEP 1.5 enforcement step.
4. `50_external/inventory_refresh_workflow.md` defines a re-runnable WebFetch workflow that maps the `omni-automation.com` API surface to our local capability docs and reports gaps. The workflow is documented, not executed, by this plan.
5. A walkthrough in `20_capabilities/04_foundation_models.md` shows the Foundation Models task-organizer plugin built end-to-end using only the new references (the acceptance test).
6. **`ofoCore` exposes every GTD-essential capability** — all seven gtd-coach coaching queries answerable without falling through to JXA; project lifecycle (create, status changes, move-to-folder, mark-reviewed) covered. `gtd-coach/SKILL.md` updated to point at `ofo` CLI commands instead of `gtd-queries.js`.
7. **System Map is a first-class, schema-versioned contract.** A documented schema lives in `attache-analyst/references/system_map_schema.md`. CLI commands (`ofo system-map`, `ofo system-map --refresh`, `ofo system-map --drift-check`) make it inspectable and refreshable. Every D6 GTD query auto-resolves conventions from the map. gtd-coach mandates a drift check at session start.
8. **Egregious errors no longer reach OmniFocus load time.** Layered static validation (D8): tightened TS strictness, `no-undef` lint, PlugIn-API antipatterns, manifest↔resources coherence checks, auto-emitted runtime contract skeletons, and optional pre-load smoke test. A deliberately broken spec is caught by the pipeline before any `.omnifocusjs` bundle is written.
9. skillsmith eval on `omnifocus-generator`, `omnifocus-core`, `gtd-coach`, and `attache-analyst` is ≥ pre-change baseline. `validate-plugin.sh` continues to pass on `Attache.omnifocusjs`. `Attache.omnifocusjs` version bumped (because `ofoCore` library functions and `systemDiscovery` schema changed).

## Two-Agent Handoff Model

Execution is split across two foundry-driven agents on separate machines. The split exists because reference research (D4 + capability-doc drafting) is purely read+write inside `omnifocus-generator/references/` and depends only on this plan + the public omni-automation.com surface — no live OmniFocus, no code mutations. Running it as a parallel front-loaded workstream lets the implementation agent start D2 (reorganization) with the new content already in hand.

### Phase 1 — Research Agent

**Scope:** Execute D4 against omni-automation.com and draft new capability content for D2.

**Concrete tasks:**

1. Execute the D4 workflow (the workflow doc said "documented, not executed" — that constraint is LIFTED for Phase 1):
   - Fetch `https://omni-automation.com/omnifocus/` index
   - Fetch each linked topic page
   - Build the `class | method | description | source-url` capability table
   - Compare against `plugins/attache/skills/omnifocus-core/references/omnifocus_api.md` (or the moved version under `omnifocus-generator/references/30_api_reference/` if migration has happened) — mark each row `covered` / `partial` / `missing`
2. Write `plugins/attache/skills/omnifocus-generator/references/50_external/capability_inventory.md` per the D4 spec.
3. Draft skeletons for each `plugins/attache/skills/omnifocus-generator/references/20_capabilities/*.md` doc using the D2 template (what this covers → what NOT → first-stop ofoCore check → native classes → reach-out trigger). Pull content from the fetched omni-automation.com pages. Mark each draft `<!-- DRAFT — review during D2 integration -->` at the top.
4. Update this plan with: (a) a "Phase 1 Research Complete" appendix listing every file written, (b) an "Unsurfaced Capabilities" section listing any high-value gaps that should become follow-up issues (NOT scope additions to D6/D7/D8), (c) the `RESEARCH COMPLETE: <ISO-date>` marker right before the "Verification" section so Phase 2 knows it's safe to start.
5. Hand back a status report: files written, capabilities surfaced, recommended follow-up issues to file (don't file them — implementation agent or human files them as cross-references from this epic).

**Tools required:** WebFetch, Read, Write (no Edit on existing references — Phase 1 only creates new files).

**Explicit restrictions — Phase 1 does NOT:**

- Modify any `.ts`, `.js`, `manifest.json`, agent `.md`, or existing SKILL.md
- Run `build-attache.sh`, `validate-plugin.sh`, or any plugin build/install step
- Migrate or reorganize existing references (that's Phase 2's D2 work)
- Touch the `20_capabilities/*.md` files beyond initial draft creation (no rewrites of its own drafts)
- Make scope decisions about D6/D7/D8 — only surface gaps as recommendations
- Touch repo state outside `plugins/attache/skills/omnifocus-generator/references/` (and this plan file)

**Phase 1 success criterion:** Phase 2 agent reads the plan, sees the `RESEARCH COMPLETE` marker + the file list, and can begin D2 reorganization immediately without further fetching.

### Phase 2 — Implementation Agent

**Scope:** Everything except D4 execution and capability-doc drafting. Specifically: D1, D2 (reorganization + integration of Phase 1 drafts), D3, D5, D6, D7, D8 + final D7.8 capability-map row.

**Concrete tasks:** Follow the Constraints execution order (next section), treating Phase 1's drafted `20_capabilities/*.md` files as authoritative content to integrate (review, polish, cross-link) during D2 — not regenerate from scratch.

**Hard precondition:** This plan file contains a `RESEARCH COMPLETE: <ISO-date>` marker before "Verification". If absent, Phase 2 stops and asks for status of Phase 1 (do not proceed without research output, or you'll duplicate work and end up with two competing capability inventories).

**Tools required:** Full agent toolkit including Bash for builds, Edit/Write for code, the foundry skill loop (`/ss-improve`).

### Handoff Boundary

Phase 1 and Phase 2 touch disjoint file sets:

- **Phase 1 writes only:** new files under `omnifocus-generator/references/50_external/` and `omnifocus-generator/references/20_capabilities/`, plus this plan
- **Phase 2 writes everywhere else** AND reviews/integrates Phase 1's drafts during D2 (may polish them, MUST NOT discard them — the research is the contract)

No locking primitive — the disjoint file sets are the contract. If Phase 2 needs to start before Phase 1 finishes (e.g., D8.1 config tightening), it can — none of the Constraints execution order's early steps touch references/ at all.

## Deliverable D1 — Channel Selection in Attache Agent

**File:** `plugins/attache/agents/attache.md`

Add a new section after the existing routing table (~line 287) titled **"Channel Selection — CLI vs Plugin vs JXA"**. Use this table verbatim as the shape:

| Channel | Use when | Examples | Source location |
|---|---|---|---|
| **`ofo` CLI** | Agent or shell-driven CRUD, queries, batch ops, scheduled work. No UI needed. Default for all agent-led work. | `ofo list overdue`, `ofo create --name`, `ofo perspective Today` | `skills/omnifocus-core/scripts/src/ofo-cli.ts` → `ofo-core.ts` |
| **Attache plugin action** | High-frequency human workflow that needs UI (Form, alert), OmniFocus context (`selection`, `document.windows`), or keyboard shortcut from the app menu. | Daily Review, Weekly Review, Analyze Selected, Discover System | `Attache.omnifocusjs/Resources/<action>.js` |
| **Standalone `.omnifocusjs` plugin** | Specialized feature that doesn't fit Attache's Chief-of-Staff identity, distributable to others, or infrequent enough that bundling would bloat Attache. | `of-organize-with-fm`, `AITaskAnalyzer`, `of-help-me-estimate` | Generated via `omnifocus-generator`, installed in `~/Library/Containers/.../Plug-Ins/` |
| **JXA (`osascript -l JavaScript`)** | Ad-hoc exploration, throwaway diagnostics, or **Apple Shortcuts** integration where Shortcuts must call out via `osascript`. NEVER for production agent workflows. | `gtd-queries.js` (legacy), one-off explorations | `skills/omnifocus-core/scripts/*.js` (legacy only) |

Add the decision tree as prose right after the table:

```
START
├── Is this for an agent or scheduled job, with no UI need?
│   └── Add to ofo CLI (ofo-core.ts function + ofo-cli.ts dispatch).
├── Is this for a human, running often, needing UI or OmniFocus selection context?
│   ├── Does it fit the Chief-of-Staff identity (review, discovery, daily/weekly cadence)?
│   │   ├── YES → Add as an action in Attache.omnifocusjs (Resources/<name>.js + manifest entry).
│   │   └── NO  → Generate a standalone .omnifocusjs via omnifocus-generator skill.
├── Is this needed by Apple Shortcuts or an ad-hoc throwaway exploration?
│   └── JXA is acceptable. Document the asset and link it from references/.
└── None of the above → STOP. Ask the user.
```

End with a one-line link back to the omnifocus-generator references: *"For format selection (solitary, solitary-fm, bundle, solitary-library) once you're committed to a plugin, see `skills/omnifocus-generator/references/10_decision_framework/plugin_format_selection.md`."*

## Deliverable D2 — Reference Reorganization with Progressive Disclosure

**Target:** `plugins/attache/skills/omnifocus-generator/references/`

Final structure (greenfield, no backward-compatibility shims — this is internal documentation):

```
references/
├── 00_index.md                                  ← Entry point. Capability map + reading order.
├── 10_decision_framework/
│   ├── cli_vs_plugin_vs_jxa.md                 ← Mirrors attache.md channel selection (one source of truth — write here, link from agent)
│   └── plugin_format_selection.md              ← solitary / solitary-fm / bundle / solitary-library
├── 20_capabilities/                            ← One doc per capability area. Each ≤300 lines.
│   ├── 01_tasks_projects_tags.md               ← Task/Project/Tag CRUD via PlugIn.Library — POINTS TO ofoCore first
│   ├── 02_perspectives.md
│   ├── 03_forms_ui.md                          ← Form class, alert(), Picker, TextField
│   ├── 04_foundation_models.md                 ← LanguageModel, Schema, prompting + worked Foundation Models walkthrough
│   ├── 05_files_export.md                      ← FileWrapper, FileType, JSON/CSV/Markdown export
│   ├── 06_localization.md                      ← Resources/<locale>.lproj/*.strings
│   ├── 07_url_scheme_callbacks.md              ← omnifocus:// + omnijs-run + x-callback-url
│   ├── 08_libraries_shared_code.md             ← PlugIn.Library pattern, calling Attache's ofoCore from a generated plugin
│   └── 09_settings_preferences.md              ← SyncedPref, hostBoundPref
├── 30_api_reference/
│   ├── omnifocus_api.md                        ← MOVED from omnifocus-core (canonical, 177KB — read only when capability docs say to)
│   ├── omnifocus_d_ts.md                       ← How to read the TypeScript stubs in scripts/typescript/
│   └── api_gaps.md                             ← Known stub gaps (ES2020 false positives, missing types)
├── 40_patterns/
│   ├── iife_wrapper.md                         ← PlugIn.Library IIFE wrap done by build-attache.sh
│   ├── library_consumer_pattern.md             ← D3 lives here. How generated plugins consume ofoCore.
│   ├── validation_pipeline.md                  ← validate-plugin.sh contract + known false positives
│   ├── version_bump_protocol.md                ← Memory rule: always bump manifest version + .strings
│   └── error_handling.md
└── 50_external/
    ├── capability_inventory.md                 ← Generated artifact from inventory workflow (initially placeholder)
    ├── web_fetch_protocol.md                   ← When/how to reach out to omni-automation.com (specific URLs + prompts)
    └── inventory_refresh_workflow.md           ← D4 lives here. The re-runnable workflow.
```

**00_index.md** is the entry point. It contains:

- A 1-paragraph statement of the skill's purpose.
- The **Channel Selection** decision tree (synced with attache.md).
- A **Capability Map** table: `| If building... | Read first | If gap, then |`. Each row points at ≤2 capability docs. Example row: `| A plugin that organizes tasks with on-device AI | 20_capabilities/04_foundation_models.md → 40_patterns/library_consumer_pattern.md | 50_external/web_fetch_protocol.md → fetch https://omni-automation.com/omnifocus/languagemodel-classes.html |`.
- A **Token-Cost Budget** rule: *"For any plugin generation task, you should read ≤3 reference files (~3KB each) before generating code. If the capability map says to read more, that's a signal to refine the capability map."*

**Each `20_capabilities/*.md` doc** follows this template:

1. **What this covers** (1 line).
2. **What this does NOT cover** (link to nearest related doc).
3. **First-stop solution: check `ofoCore`** — does the function exist in `scripts/src/ofo-core.ts`? List the relevant exports. If yes, consume via library. If no, continue.
4. **Native Omni Automation classes** — short reference (class names + key methods) with code skeletons. ≤200 lines.
5. **Reach-out trigger** — if the user's specific question isn't covered here, the exact `WebFetch` invocation: URL + prompt.

**Migration tactics:** The existing flat references move into the new structure. Mapping:

| Old | New |
|---|---|
| `omnifocus-generator/references/code_generation_validation.md` | Split: validation rules → `40_patterns/validation_pipeline.md`; LanguageModel schema → `20_capabilities/04_foundation_models.md`; IIFE assertions → `40_patterns/iife_wrapper.md` |
| `omnifocus-generator/references/omni_automation_guide.md` | Split across `20_capabilities/*.md` per topic |
| `omnifocus-generator/references/automation_best_practices.md` | Split: patterns → `40_patterns/`; anti-patterns → `40_patterns/error_handling.md` |
| `omnifocus-generator/references/channel_selection.md` | Merge into `10_decision_framework/cli_vs_plugin_vs_jxa.md` |
| `omnifocus-core/references/omnifocus_api.md` | MOVE to `omnifocus-generator/references/30_api_reference/omnifocus_api.md`. Leave a 1-line pointer stub in `omnifocus-core/references/` that says: *"Canonical OmniFocus API reference now lives in `../../omnifocus-generator/references/30_api_reference/omnifocus_api.md`."* |
| `omnifocus-core/references/api_reference.md` | Keep in `omnifocus-core` (it's a CLI-user quick lookup, not a generator reference) |

Do **not** duplicate — every fact lives in exactly one file. Cross-link freely.

## Deliverable D3 — Shared-Library Doctrine

**Primary file:** `plugins/attache/skills/omnifocus-generator/references/40_patterns/library_consumer_pattern.md`

This doc establishes the rule: **`ofoCore` is the shared library. Every generated plugin that touches tasks, projects, tags, or perspectives consumes it; it does not reimplement.**

Contents:

1. **The pattern.** Every generated plugin calls:
   ```js
   const ofoCore = PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore");
   const task = ofoCore.getTask(taskId);
   ```
2. **What `ofoCore` exposes today.** List all 20 functions from `scripts/src/ofo-core.ts` (info queries, mutations, batch, queries, analytics, config, dispatch). Each entry: name, signature, what to use it for, and the line in `ofo-core.ts` to consult for current behavior. This is a generated table — note in the doc that it should be regenerated when `ofo-core.ts` changes (link to issue #141 for the broader CLI surface expansion).
3. **The dependency contract.** Generated plugins that consume `ofoCore` declare a runtime dependency on the Attache plugin being installed. Document this in the generated plugin's manifest as a description note ("Requires Attache plugin v2.0+") and in a startup check that fails fast with a clear message if `PlugIn.find(...)` returns null.
4. **When to add to `ofoCore` vs. inline in a plugin.** Rule of thumb: *"If the function would be useful to 2+ plugins or to the CLI, add to `ofoCore`. Otherwise inline."* Adding to `ofoCore` means: TS source in `ofo-core.ts`, dispatch entry in `dispatch()`, CLI command in `ofo-cli.ts` if shell access is wanted, rebuild via `build-attache.sh`.
5. **Library generation for non-Attache shared code.** If a generated plugin needs reusable code that doesn't belong in `ofoCore` (e.g., a domain-specific helper), the `solitary-library` format produces a stand-alone `PlugIn.Library` that other plugins can `find().library()`. Link to format selection.

**Enforcement in the generator workflow.** Update `omnifocus-generator/SKILL.md` to insert a **STEP 1.5** between CLASSIFY and SELECT FORMAT:

> **STEP 1.5 — CHECK ofoCore.** Before generating any code, read `references/40_patterns/library_consumer_pattern.md` and the current `scripts/src/ofo-core.ts` exports. If the operation you need is already there, the plugin should consume it via `PlugIn.find(...).library("ofoCore")`. If only *part* of what you need is there, propose the missing function as an `ofoCore` addition (link to issue #141) and proceed with consumption + a documented gap. Only generate fresh CRUD code when the operation does not belong in `ofoCore` (rare).

Mirror this rule in `attache.md` agent doc near the existing "OmniFocus Execution Hierarchy" section.

## Deliverable D4 — Re-Runnable Web Capability Inventory Workflow

**File:** `plugins/attache/skills/omnifocus-generator/references/50_external/inventory_refresh_workflow.md`

This is the workflow that an agent runs to refresh the capability inventory from omni-automation.com. **Under the Two-Agent Handoff Model, D4 is executed by the Phase 1 Research Agent** as its primary task — the workflow doc AND the populated `capability_inventory.md` AND drafted `20_capabilities/*.md` skeletons are all Phase 1 deliverables. Subsequent re-runs (quarterly cadence, or when a specific capability is missing) follow the same documented workflow.

Workflow shape (document as numbered steps an agent can follow):

1. **Fetch the index.** `WebFetch https://omni-automation.com/omnifocus/ — extract every top-level topic link with its href`.
2. **For each topic, fetch and extract.** `WebFetch <topic-url> — list every documented class, every method on each class, and the one-line description if present. Output as JSON.`
3. **Aggregate** into a single capability table: `class | method | description | source-url`.
4. **Compare against local refs.** For each `(class, method)` row, check if it appears anywhere under `20_capabilities/` or `30_api_reference/`. Mark each row as `covered`, `partial`, or `missing`.
5. **Write `capability_inventory.md`** with: (a) timestamp, (b) the capability table sorted by coverage status (missing first), (c) a TODO list of capability docs that should be added/expanded.
6. **Open follow-up issues** for any `missing` rows judged high-value. Use labels `attache`, `references`, `omnifocus-api`.

**Anti-patterns to call out in the doc:**

- DO NOT read the full body of every topic page during normal work — only run this workflow on schedule (e.g., quarterly) or when a specific capability is missing.
- DO NOT inline the capability inventory into `00_index.md` — it lives in `50_external/capability_inventory.md` and is referenced from the capability map only as needed.
- DO NOT fetch the same URL twice in a single run — WebFetch caches, but the workflow should batch.

**`web_fetch_protocol.md`** (sibling file) documents the contract for *one-off* WebFetches during plugin building (when a capability doc says "if your case isn't covered here, fetch X"): includes the URL format, the prompt template, and a token-cost reminder.

## Deliverable D5 — Foundation Models Worked Example (Acceptance Test)

**File:** `plugins/attache/skills/omnifocus-generator/references/20_capabilities/04_foundation_models.md`

After the standard capability-doc sections, append a section titled **"Worked Example: Organize Project Tasks via Foundation Models"** with a full walkthrough. This is the plan's acceptance criterion — a fresh agent should be able to build the plugin reading only this doc + the docs it links to (`08_libraries_shared_code.md`, `40_patterns/library_consumer_pattern.md`, and `10_decision_framework/plugin_format_selection.md`).

Walkthrough outline (the executing agent fleshes this out):

1. **Channel selection.** Decision tree → standalone `.omnifocusjs` (specialized, not high-frequency enough for Attache). Format → `solitary-fm`.
2. **Library consumption.** Use `ofoCore.getTask`, `ofoCore.tagTask`, `ofoCore.updateTask` for all task I/O. No reimplementation.
3. **Selection input.** Use `selection.projects[0]` or `selection.tasks[0].containingProject`.
4. **Read tasks.** Iterate `project.flattenedTasks`, calling `ofoCore.getTask` per task to get `{name, note, tags, ...}`.
5. **Prepare the model call.** Define a `LanguageModel.Schema` for output: e.g., `{ groupings: [{ category: string, taskIds: string[], suggestedTag: string }] }`. Link to the LanguageModel section of this same doc for schema syntax.
6. **Invoke the model.** Use `LanguageModel.respond(prompt, schema)` (or current API per `omni_automation_api_mapping.md`). Include token-budget guidance: if task list > 50, batch.
7. **Apply suggestions.** For each grouping, `ofoCore.tagTask(taskId, {add: [suggestedTag]})` and optionally `ofoCore.updateTask(taskId, {parent: ...})` to reorder. Wrap in a confirmation Form so the user previews before applying.
8. **Validate & install.** `bash scripts/validate-plugin.sh`, bump version, drop in `~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/Plug-Ins/` (or double-click).

The walkthrough must call out every external reference it relies on with a relative link, so the executing agent's eval can measure: *did the fresh agent need to fetch anything beyond what was linked?*

## Deliverable D6 — GTD Capability Coverage in ofoCore

**Goal:** `ofoCore` must answer every question gtd-coach is going to ask, and support every project lifecycle action the GTD methodology requires. After D6, `gtd-queries.js` becomes a legacy diagnostic shim with no production callers, and the SKILL.md table in gtd-coach points at `ofo` CLI commands.

**Execution order:** D6 should run **before** D2/D3 because the references and the doctrine doc need to enumerate the full `ofoCore` surface accurately. D1 (channel selection) can run in parallel with D6.

### D6.1 — Audit (no code yet)

The executing agent should reproduce this gap table by reading the current `scripts/src/ofo-core.ts` and `skills/gtd-coach/SKILL.md`. If the table below has drifted, the agent's audit wins.

**Coaching queries (gtd-coach SKILL.md table):**

| Coaching question | Today | Required `ofoCore` function |
|---|---|---|
| How many items in your inbox? | ✅ `getStats.inbox` | (covered) |
| Which projects are stalled? | ✅ `stalledProjects` | (covered) |
| What's aging in Waiting For? | ❌ JXA-only | `listWaitingFor({tag, ageThresholdDays})` |
| Any someday/maybe to review? | ❌ JXA-only | `listSomedayMaybe({tag?, folder?})` (convention passed in) |
| Which projects are neglected? | ❌ JXA-only | `listNeglectedProjects({daysSinceModified})` |
| What did you accomplish? | ❌ JXA-only | `listRecentlyCompleted({sinceDate, groupByTag?})` |
| Overall system health? | ✅ `getHealth` | (covered) |

**Project lifecycle (GTD requires reflect + organize phases):**

| Capability | Today | Required `ofoCore` function |
|---|---|---|
| Create project | ❌ (#161) | `createProject({name, folder?, sequential?, note?, reviewInterval?})` |
| Update project (name/status/folder/sequential/review) | ❌ (#161) | `updateProject({id, ...fields})` — including `status: 'active' \| 'onHold' \| 'completed' \| 'dropped'` |
| Mark project as reviewed | ❌ | `markProjectReviewed({id, reviewDate?})` |
| List projects due for review | 🟡 count only in `getStats.reviewOverdue` | `listProjectsForReview({beforeDate?})` |
| List folder hierarchy | ❌ | `listFolders({includeProjects?})` |
| Move project to folder | ❌ | `updateProject({id, folder})` (subsumed) |

**Out of D6 scope (remain on follow-up issues):**

- Folder CRUD (`createFolder`, `deleteFolder`) — low frequency
- Task reordering within project / parent task assignment / sequential→parallel conversion at task level
- Repetition rule editing (`setRepetition`) — complex API surface; Catch Up Automatically toggle is an OmniFocus API limitation (see gtd-coach repeating-tasks reference)
- Task skip-one-occurrence semantics
- Convert single task → project (workaround: create project, move task)

These remain on issues #141 and #161 with their existing scope.

### D6.2 — Library Implementation

Add the new functions to `plugins/attache/skills/omnifocus-core/scripts/src/ofo-core.ts`. Pattern guidance:

- **Mirror existing conventions.** Same `OfoArgs` / `OfoResult` shapes. Same `normalizeTask` helper. Same error-as-data style (`{success: false, error: '...'}` never `throw`).
- **Stateless convention.** `listWaitingFor` and `listSomedayMaybe` take the user's tag/folder convention as an argument; do not read preferences or the System Map from inside `ofoCore`. The CLI layer resolves conventions from the System Map (see D7) before calling. This keeps `ofoCore` decoupled from "what system map exists" — it just answers `listWaitingFor({tag: "Waiting"})`.
- **Reuse `normalizeTask` and `computeStats`.** Don't drift field sets.
- **Add to `dispatch()` switch.** Each new function gets an `ofo-*` action and a switch case. The exhaustiveness `_exhaustive: never` check will guide additions to `OfoAction` in `ofo-types.ts` / `ofo-core-ambient.d.ts`.
- **Project status mapping.** `updateProject` accepts string status values (`'active'`, `'onHold'`, `'completed'`, `'dropped'`) and maps to the OmniFocus `Project.Status.*` enum. Document the mapping at the top of the function.
- **Document the System Map dependency at the function level.** Each query that depends on a convention (waiting, someday, neglected, context-based) gets a JSDoc comment: `@requires SystemMap.conventions.waitingTag` (or similar). This is the contract the CLI dispatch layer is satisfying.

### D6.3 — CLI Surface

Add corresponding commands to `plugins/attache/skills/omnifocus-core/scripts/src/ofo-cli.ts`:

| ofoCore function | CLI command |
|---|---|
| `listWaitingFor` | `ofo list waiting-for --tag <name> [--days N]` |
| `listSomedayMaybe` | `ofo list someday-maybe [--tag <name>] [--folder <name>]` |
| `listNeglectedProjects` | `ofo projects neglected [--days N]` |
| `listRecentlyCompleted` | `ofo completed --since <date> [--by-tag]` |
| `listProjectsForReview` | `ofo projects review [--before <date>]` |
| `markProjectReviewed` | `ofo project review <id> [--date <ISO>]` |
| `listFolders` | `ofo folders [--with-projects]` |
| `createProject` | `ofo project create --name "..." [--folder NAME] [--sequential] [--review every N days]` |
| `updateProject` | `ofo project update <id> [--name] [--status active\|onHold\|completed\|dropped] [--folder] [--sequential\|--parallel]` |

**Convention auto-resolution.** Each list-* command above that depends on user convention (`waiting-for`, `someday-maybe`, `neglected`) MUST attempt to resolve the convention from the System Map first (`ofo system-map` from D7), then accept an explicit `--tag` or `--folder` override. Resolution order:

1. Explicit CLI flag (`--tag`, `--folder`) — highest precedence
2. System Map convention (`conventions.waitingTag`, `conventions.somedayFolder`, etc.)
3. If neither: emit a structured error pointing to `ofo system-map --refresh` (do not silently default to `@waiting` / `Someday/Maybe` — silent defaults mask configuration drift)

Update `ofo --help` output accordingly, and document the resolution chain in the help text for each affected command.

### D6.4 — gtd-coach Skill Update

Edit `plugins/attache/skills/gtd-coach/SKILL.md` "Data-Grounded Coaching" table (lines 246–263). Replace each `osascript -l JavaScript scripts/gtd-queries.js --action X` with the corresponding `ofo` CLI command. After this change:

- The table should show `ofo` commands for all seven coaching questions (Inbox count, stalled projects, waiting-for aging, someday-maybe, neglected projects, recently completed, system health).
- Add a line at the top of the section: *"All coaching queries use the `ofo` CLI. `gtd-queries.js` (JXA) is retained only for ad-hoc diagnostics and Apple Shortcuts integration."*
- Leave the `gtd-queries.js` examples at lines 258–263 in place, but reframe them as "Legacy JXA reference — use `ofo` CLI for production coaching workflows."

**Promote the "System Context" section to a hard prerequisite.** The existing optional "System Context (when provided by omnifocus-agent)" subsection (lines 234–242) becomes a mandatory pre-flight step. Insert at the top of the Data-Grounded Coaching section:

> **STEP 0 — Confirm System Map currency.** Before answering any coaching question, run `ofo system-map --drift-check` (D7.4). If `stale: true`, the first coaching action is to run `ofo system-map --refresh` and explain to the user that their tag/folder conventions have shifted enough that coaching answers based on the cached map may be wrong. If the map is missing, run `ofo system-map --refresh` to create it. Do not proceed with coaching until the map is current. Reference: `attache-analyst/references/system_map_schema.md`.

### D6.5 — gtd-queries.js Disposition

Do **not** delete `scripts/gtd-queries.js`. Leave it in place as legacy/Apple-Shortcuts integration. Update its file header comment to say: *"Legacy JXA query layer. Superseded by `ofo` CLI for production use. Retained for ad-hoc exploration and Apple Shortcuts integration where `osascript` is the only available channel."*

### D6.6 — Build & Validate

After all library + CLI changes:

1. `bash plugins/attache/skills/attache-analyst/scripts/build-attache.sh` — rebuilds `Attache.omnifocusjs` with the expanded `ofoCore`.
2. The build script's "Verify all N ofoCore functions exist in compiled output" check must be updated for the new function count (was 20, will be 20 + new). Update the verification list if needed.
3. Bump `Attache.omnifocusjs/manifest.json` version (per memory: OmniFocus won't recognize updates without a version bump) and corresponding `.strings` localization file.
4. `bash plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh ~/Library/Containers/.../Plug-Ins/Attache.omnifocusjs` — must pass.
5. Smoke-test each new CLI command end-to-end (live OmniFocus database). Capture output samples for the reference docs.

### D6.7 — Feed back into D2/D3

After D6 lands, the executing agent revisits:

- `references/40_patterns/library_consumer_pattern.md` — regenerate the `ofoCore` exports table to include the new functions.
- `references/20_capabilities/01_tasks_projects_tags.md` — update the "check ofoCore first" section to list the new project-lifecycle functions.
- `references/00_index.md` capability map — add rows for the new GTD coaching queries with the right reading order.

## Deliverable D7 — System Map as First-Class Convention Source

**Goal:** Treat the Attache System Map as a contract, not an opportunistic artifact. Every GTD query that depends on "how this user organizes things" reads the map; gtd-coach refuses to answer data-grounded questions until the map is current; the map is re-discoverable and drift-aware. After D7, "what's in Waiting For?" never silently falls through to a hardcoded `@waiting` default.

**Execution order:** D7 runs **before** D6.2/D6.3 so the schema and refresh CLI are in place when the GTD queries are wired up to consume them. D7.1 (audit) and D7.2 (schema) are the earliest steps in the whole execution.

### D7.1 — Current State Audit

Read `plugins/attache/skills/attache-analyst/scripts/src/attache/systemDiscovery.ts` and the deployed `Attache.omnifocusjs/Resources/systemDiscovery.js` + `Resources/discoverSystem.js` action. Document:

- Exact field set produced by `discoverSystem({depth: "full"})` today.
- Storage convention: the JSON lives in the note field of a task named "Attache System Map".
- Versioning: confirm `attacheVersion` field is populated; check whether a `schemaVersion` field exists (likely not yet).
- Inference mode: hybrid rule-based + Foundation Models — note which fields rely on FM (so the agent on the other machine knows the macOS 26+ Apple Silicon constraint).

The audit output is a short markdown block in the new schema doc (D7.2), not a separate deliverable file.

### D7.2 — Canonical Schema (Contract)

Create `plugins/attache/skills/attache-analyst/references/system_map_schema.md`. This is the contract every consumer reads. Contents:

1. **Storage convention.** "Attache System Map" task, note field, JSON-encoded.
2. **Top-level fields (schema v1):**
   - `schemaVersion: number` — incremented when the schema changes; consumers compare against expected and refuse stale schemas
   - `attacheVersion: string` — version of the Attache plugin that produced this map
   - `generatedAt: ISO8601 string` — when the map was last refreshed
   - `discoveryMode: 'rules-only' | 'rules-plus-fm'` — whether Foundation Models was available
   - `tags.categories.{contexts, people, status, duration, schedulingContext}: string[]` — tag taxonomy (existing)
   - `structure.topLevelFolders: [{name, inferredType}]` — folder taxonomy (existing)
   - `tasks.dataQuality.{percentWithDuration, percentWithProject, percentWithTags}: number` — quality signals (existing)
   - `durationModel: 'native' | 'tags' | 'mixed' | 'none'` — inferred from dataQuality (existing)
   - **NEW** `conventions: { waitingTag, somedayTag, somedayFolder, waitingForFolder, defaultContextTag }` — explicit named conventions resolved from the categories above. This is the field the D6 queries consume directly.
3. **Convention resolution rules.** How `conventions.*` is computed from `tags.categories.*` and `structure.topLevelFolders`. Example: `conventions.waitingTag` = first tag in `tags.categories.people` whose name matches `/wait/i`, else first in `tags.categories.status` matching `/wait/i`, else null.
4. **JSON Schema file.** A companion `system_map.schema.json` in the same references directory for machine validation. Pin `schemaVersion: 1` in the `const` field so consumers can validate fast.
5. **Forward-compatibility rule.** When adding fields, bump `schemaVersion`. When removing or renaming, bump `schemaVersion` AND publish a migration note. Old consumers MUST detect higher `schemaVersion` and warn ("System Map produced by newer Attache; some fields may not be understood").

### D7.3 — Refresh & Inspect CLI

Add to `ofo` CLI (extends D6.3):

| Command | Behavior |
|---|---|
| `ofo system-map` | Read the "Attache System Map" task note; return as JSON. If missing → exit non-zero with: `"System Map not found. Run: ofo system-map --refresh"`. |
| `ofo system-map --show` | Human-readable summary: folder count + names, convention values, durationModel, generatedAt age. |
| `ofo system-map --refresh` | Invoke `systemDiscovery.discoverSystem({depth: "full"})` via Attache plugin library; write JSON back to the "Attache System Map" task note (creating the task if absent); echo the new map. |
| `ofo system-map --drift-check` | Compute drift signals (see D7.4); return `{stale: bool, reasons: string[], lastRefresh: ISO}` as JSON. Exit 0 with `stale: false`, exit 0 with `stale: true` (drift is information, not failure). |
| `ofo system-map --validate` | Validate the current map against `system_map.schema.json`. Exit non-zero on validation failure. |

CLI dispatch reads the map via OmniFocus search (find task by exact name "Attache System Map"). Implementation goes in `ofo-cli.ts` — no new `ofo-core.ts` function needed if the map is read by the CLI layer (keeps `ofoCore` stateless). If the CLI layer benefits from a helper, add `getSystemMapTask` to `ofo-core.ts` (returns the task note string; CLI parses).

### D7.4 — Drift Detection

Document drift signals in `system_map_schema.md` under a "Drift Detection" section. The `--drift-check` command checks:

| Signal | Threshold | Reason string |
|---|---|---|
| `schemaVersion` mismatch (map's < current expected) | strict | `"schema-stale: map v{X}, current schema v{Y}"` |
| `generatedAt` older than 30 days (configurable via `ATTACHE_MAP_MAX_AGE_DAYS`) | default 30d | `"age-stale: refreshed {N} days ago"` |
| Tag-count delta (current `flattenedTags.length` vs. sum of `tags.categories.*` arrays) > 10% | 10% | `"tag-drift: {delta} tags added/removed since last refresh"` |
| Folder-count delta vs `structure.topLevelFolders.length` > 10% | 10% | `"folder-drift: top-level folder count changed"` |
| `conventions.waitingTag` no longer exists in `flattenedTags.byName` | strict | `"convention-broken: waitingTag '{X}' no longer exists"` |

The Attache plugin's existing `dailyReview.js` action should ALSO emit a drift signal at session start (showing a non-blocking warning in the Daily Review form). This is a soft notification — the user can ignore and proceed.

### D7.5 — D6 Query Integration

After D7.3 ships, update D6.3 CLI commands to use the resolution chain spelled out in that section (explicit flag → System Map convention → structured error). Specifically:

- `ofo list waiting-for` (no flags) reads `conventions.waitingTag` from System Map.
- `ofo list someday-maybe` (no flags) reads `conventions.somedayTag` AND/OR `conventions.somedayFolder` (both can be in play).
- `ofo projects neglected` does not need conventions (modified-date based), but emits a warning if System Map is stale.
- `ofo completed --since X` does not need conventions; no System Map dependency.

All commands that read the System Map emit a warning to stderr if `--drift-check` would return `stale: true`. The warning is informational, not fatal.

### D7.6 — gtd-coach Integration

This was added in D6.4 (STEP 0 — Confirm System Map currency). D7 ensures the CLI commands STEP 0 references actually exist. Cross-reference: D6.4 STEP 0 ⇄ D7.3 commands ⇄ D7.4 drift signals.

### D7.7 — Generator Reference Doc

Add `plugins/attache/skills/omnifocus-generator/references/40_patterns/system_map_dependency.md`:

- **The rule.** Any generated plugin that does GTD-flavored coaching, querying, or organization MUST consume the System Map. The pattern: `var sm = JSON.parse(systemMapTask.note); var waitingTag = sm.conventions.waitingTag;`.
- **How to find the System Map task from a generated plugin.** Use `flattenedTasks.byName("Attache System Map")` (or first match if the API doesn't expose `byName` on tasks — fall back to filter). Document the OmniFocus API caveat in `30_api_reference/api_gaps.md` if relevant.
- **Schema version handling.** Always check `sm.schemaVersion === expectedVersion` before reading; warn-and-proceed if higher, error-and-exit if lower.
- **Cross-link.** Update `40_patterns/library_consumer_pattern.md` to list `systemDiscovery` as the second mandatory library after `ofoCore` for GTD-flavored plugins.

### D7.8 — Capability Map Integration

In `omnifocus-generator/references/00_index.md`, the Capability Map gets a new row:

| If building... | Read first | If gap, then |
|---|---|---|
| A plugin that organizes/queries the user's GTD system | `40_patterns/system_map_dependency.md` → `attache-analyst/references/system_map_schema.md` | If conventions aren't covered: extend `systemDiscovery` (file an issue) |

This ensures the Foundation Models worked example in D5 reads `system_map_dependency.md` and uses the user's actual convention tags rather than hardcoded examples.

## Deliverable D8 — Static Validation Hardening for Generated Plugins

**Goal:** Catch every class of error in static analysis or pre-emit validation, not at OmniFocus load time. "Build a plugin, install it, watch it crash on first run" should become vanishingly rare. Builds on the existing tsc/ESLint/antipatterns pipeline rather than replacing it.

**Audit baseline (verify the agent's audit matches this; if the codebase has drifted, the agent's audit wins):**

| Layer | Today | Gap |
|---|---|---|
| `tsconfig.plugin.json` strict flags | `strict`, `noImplicitAny`, `strictNullChecks`, `noImplicitReturns`, `noFallthroughCasesInSwitch` all ON | `noUncheckedIndexedAccess` OFF; `exactOptionalPropertyTypes` OFF |
| ESLint (`eslint.config.js`) | OmniFocus globals declared; `no-undef: off`, `no-unused-vars: off` | Globals declared but unused — `no-undef` is the cheap typo-catcher and it's disabled |
| `jxa-antipatterns.json` | `.addTag`, `.clearTags`, `Document.defaultDocument`, exact tag match, `eval`, `Function()`, `NSTask`, `NSURLSession` | No `.byName()` null-check requirement; no `selection[0]` guard; no `PlugIn.find` null-check; no `LanguageModel.Schema` constructor block |
| `validate-plugin.sh` | manifest valid; action `.js` files exist by name | Doesn't verify the file contains a matching `new PlugIn.Action(...)` / `new PlugIn.Library(...)`; doesn't validate `.strings` keys against manifest references |
| Generator runtime skeletons | None auto-emitted | No library-presence check (D8.6 + D3); no System Map version check (D8.7 + D7) |
| Pre-load smoke | None | No "does this bundle even parse + evaluate against a stub environment" gate |

### D8.1 — Tighten TS Strictness

Edit `plugins/attache/skills/omnifocus-core/scripts/src/tsconfig.plugin.json` (and the sibling `tsconfig.cli.json`, `tsconfig.attache-libs.json`):

- Add `"noUncheckedIndexedAccess": true` — `arr[0]` types as `T | undefined`, forcing guards. Big catch for `selection.tasks[0]` and `byName("foo")[0]` patterns.
- Add `"exactOptionalPropertyTypes": true` — distinguishes `{x?: T}` from `{x: T | undefined}`, catches drift between OmniFocus stubs and consumer code.
- Add `"noPropertyAccessFromIndexSignature": true` — forces bracket access on index signatures, makes implicit-any leakage visible.

If turning these on surfaces ≥5 existing errors per file, the executing agent should pause and ask before mass-suppressing — that's a real audit finding, not a config tuning. Use `// @ts-expect-error #ISSUE-N` per call site (tracked, not silenced) and document each in `30_api_reference/api_gaps.md`.

### D8.2 — Enable ESLint Typo-Catching

Edit `plugins/attache/skills/omnifocus-core/eslint.config.js`:

- Flip `no-undef: "off"` → `no-undef: "error"`. With OmniFocus globals already declared, this catches typos like `flattenedTaks` at lint time — the single highest-ROI change in this deliverable.
- Flip `no-unused-vars: "off"` → `"warn"`. Don't error (generated code legitimately has unused params for action handlers), but surface them.
- Verify all PlugIn API classes are in the globals list. Cross-reference against `omnifocus.d.ts` declarations. Missing globals get added (this is mechanical).

### D8.3 — Expand Antipatterns with PlugIn-API Footguns

Add to `plugins/attache/skills/omnifocus-generator/scripts/jxa-antipatterns.json`:

```jsonc
{
  "id": "require-byname-null-check",
  "pattern": "\\.byName\\([^)]+\\)\\.[a-zA-Z]",
  "severity": "error",
  "message": ".byName() returns null when not found. Assign to a variable and null-check before property access."
},
{
  "id": "require-selection-guard",
  "pattern": "selection\\.(tasks|projects|folders|tags)\\[0\\]",
  "severity": "error",
  "message": "selection arrays may be empty. Check .length before [0] access."
},
{
  "id": "require-plugin-find-check",
  "pattern": "PlugIn\\.find\\([^)]+\\)\\.library",
  "severity": "error",
  "message": "PlugIn.find() returns null when plugin missing. Assign and null-check before .library() access."
},
{
  "id": "no-language-model-schema-constructor",
  "pattern": "new\\s+LanguageModel\\.Schema\\b",
  "severity": "error",
  "message": "Use LanguageModel.Schema factory methods (e.g., LanguageModel.Schema.object({...})), not the constructor.",
  "reference": "20_capabilities/04_foundation_models.md"
}
```

Wire these into `validate-jxa-patterns.js` — it already scans for the existing patterns; new entries are picked up automatically if the script iterates the JSON.

### D8.4 — Manifest↔Resources Coherence Validator

Extend `plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh` with a new "Bundle Coherence" section that checks:

For each declared action `{identifier, label}` in manifest.json:
- Confirm `Resources/<identifier>.js` exists (already done)
- **NEW:** Confirm the file contains a `new PlugIn.Action(` constructor (grep — generated code is consistent enough that this works)
- **NEW:** If the action declares a custom identifier inside the file (some patterns do), confirm it matches the manifest identifier

For each declared library `{identifier}` in manifest.json:
- Confirm `Resources/<identifier>.js` exists (already done)
- **NEW:** Confirm the file contains a `new PlugIn.Library(` constructor
- **NEW:** Confirm the library's identifier string matches the manifest entry

For each `.strings` file under `Resources/<locale>.lproj/`:
- **NEW:** Parse keys (line format: `"key" = "value";`)
- **NEW:** For every key referenced in manifest.json (action `label`, plugin `description`, etc.), confirm it exists in the default locale `.strings`
- **NEW:** Warn (not error) on unused keys

This is the layer that catches the silent-load-failure case directly.

### D8.5 — Generator-Emitted Runtime Skeletons

Update `plugins/attache/skills/omnifocus-generator/scripts/generate_plugin.ts` so that:

**When the spec declares `requires: ["ofoCore"]`** (per D3 doctrine), the generator auto-emits at the top of each action:

```js
var attache = PlugIn.find("com.totallytools.omnifocus.attache");
if (!attache) {
  new Alert("Attache Required", "This plugin requires the Attache plugin (v2.0+). Install from <repo URL>.").show();
  return;
}
var ofoCore = attache.library("ofoCore");
if (!ofoCore || typeof ofoCore.getTask !== "function") {
  new Alert("Attache Out of Date", "Attache 'ofoCore' library is missing required functions. Please update Attache.").show();
  return;
}
```

**When the spec declares `requires: ["systemMap"]`** (per D7.7), the generator auto-emits:

```js
var smTask = flattenedTasks.find(function(t) { return t.name === "Attache System Map"; });
if (!smTask) {
  new Alert("System Map Missing", "Run: ofo system-map --refresh").show();
  return;
}
var sm;
try { sm = JSON.parse(smTask.note || "{}"); }
catch (e) { new Alert("System Map Corrupt", "Run: ofo system-map --refresh").show(); return; }
if (sm.schemaVersion !== EXPECTED_SCHEMA_VERSION) {
  new Alert("System Map Schema Mismatch", "Expected v" + EXPECTED_SCHEMA_VERSION + ", got v" + sm.schemaVersion + ". Run: ofo system-map --refresh").show();
  return;
}
```

The `EXPECTED_SCHEMA_VERSION` is templated in from the System Map schema doc at generation time, so generated plugins are pinned to a specific schema version they were validated against.

Document both skeletons in `40_patterns/library_consumer_pattern.md` (D3) and `40_patterns/system_map_dependency.md` (D7.7).

### D8.6 — Pre-Load Smoke Test (Optional but Recommended)

Add `plugins/attache/skills/omnifocus-generator/scripts/smoke-load.js`: a Node.js script that:

1. Loads a minimal stub environment defining the OmniFocus globals as no-ops (e.g., `PlugIn = { find: () => null, Library: function() {} }`).
2. `require()`s each compiled `Resources/*.js` file.
3. Reports any thrown error (syntax error, top-level reference to an undefined identifier, etc.).

This doesn't run action logic — it only confirms the bundle **parses + evaluates at the top level** against stubbed globals. Catches the class of error where a refactor renames a global and the action file still references the old name.

Wire into `validate-plugin.sh` as the final gate. Mark as optional in case Node version constraints make it brittle on the executor's machine; agent should still attempt and report.

### D8.7 — Validation Pipeline Reference Doc

Rewrite `plugins/attache/skills/omnifocus-generator/references/40_patterns/validation_pipeline.md` to document the layered approach as a single source of truth:

1. **Pre-generation (in `generate_plugin.ts`):** Spec validation, template selection, ofoCore-check prompt (per D3 STEP 1.5).
2. **Pre-emit (after TS source is generated):** `tsc --noEmit` with strict flags from D8.1; ESLint with D8.2 + D8.3 rules; refusal-to-emit on error.
3. **Post-emit (after JS is written):** `validate-plugin.sh` runs: manifest validity → required fields → Resources existence → D8.4 bundle coherence → D8.6 smoke-load.
4. **Runtime (built into the generated code by D8.5):** library presence check, System Map version check, selection guards.
5. **Documented deviations:** `api_gaps.md` table of `@ts-expect-error #ISSUE` markers, each linked to a tracking issue.

Include a "What's NOT statically checkable" section listing the runtime contracts that need live testing: Foundation Models availability (macOS 26+ Apple Silicon), version-gated OmniFocus APIs, OmniFocus's silent library reload bug (#135).

### D8.8 — Acceptance: Egregious-Error Repro

The executing agent should construct a deliberately broken plugin spec (e.g., references a non-existent `ofoCore` function, has a typo'd OmniFocus global, declares an action whose file doesn't contain `new PlugIn.Action`, references a manifest `.strings` key not in the localization file) and confirm the pipeline catches every error **before** any `.omnifocusjs` bundle is written to disk. This is the user's stated success criterion: *"I do not want to load built plugins only to find egregious errors."* Document the test cases in `validation_pipeline.md` as a regression suite.

**Out of D8 scope (follow-ups):**

- **CI gate** (GitHub Action running `validate-plugin.sh` on PR) — repo-level infra; track as a separate issue.
- **Property-based testing of the generator itself** — generates random valid specs, asserts output validates. Worth doing eventually but not in this pass.
- **Stub environment for action-level smoke testing** (vs. parse-only D8.6) — would require modeling enough of the OmniFocus runtime to actually execute action handlers; large scope.

## Files to be Modified

Representative paths (not exhaustive — the executing agent will discover the full set during the migration):

- `plugins/attache/agents/attache.md` — channel selection section + STEP 1.5 mention
- `plugins/attache/skills/omnifocus-generator/SKILL.md` — workflow updated with STEP 1.5 and new reference-path discipline
- `plugins/attache/skills/omnifocus-generator/references/**` — entire new structure (new + moved + split files)
- `plugins/attache/skills/omnifocus-core/references/omnifocus_api.md` — replaced with a 1-line pointer stub
- `plugins/attache/skills/omnifocus-core/SKILL.md` — references-section pointer updated; CLI command surface section updated for D6.3 additions
- `plugins/attache/skills/omnifocus-core/scripts/src/ofo-core.ts` — D6.2 new functions (9 new: `listWaitingFor`, `listSomedayMaybe`, `listNeglectedProjects`, `listRecentlyCompleted`, `listProjectsForReview`, `markProjectReviewed`, `listFolders`, `createProject`, `updateProject`) + dispatch additions
- `plugins/attache/skills/omnifocus-core/scripts/src/ofo-cli.ts` — D6.3 CLI surface for the new functions; D7.3 `ofo system-map` subcommands; D7.5 convention resolution chain
- `plugins/attache/skills/omnifocus-core/scripts/src/ofo-types.ts` and `ofo-core-ambient.d.ts` — new `OfoAction` enum entries
- `plugins/attache/skills/omnifocus-core/scripts/gtd-queries.js` — file header comment only (legacy framing)
- `plugins/attache/skills/gtd-coach/SKILL.md` — D6.4 Data-Grounded Coaching table replaced with `ofo` CLI commands; STEP 0 (System Map currency check) added
- `plugins/attache/skills/attache-analyst/scripts/build-attache.sh` — function-count verification list updated for D6.6 (only if the script hardcodes the function list; otherwise no change)
- `plugins/attache/skills/attache-analyst/scripts/src/attache/systemDiscovery.ts` — D7.2 schema additions: `schemaVersion` field, `conventions.*` derived fields, `discoveryMode` field
- `plugins/attache/skills/attache-analyst/references/system_map_schema.md` — NEW, D7.2 contract doc
- `plugins/attache/skills/attache-analyst/references/system_map.schema.json` — NEW, JSON Schema for validation
- `plugins/attache/skills/attache-analyst/SKILL.md` — reference the new schema doc; update System Map field list
- `plugins/attache/skills/omnifocus-generator/references/40_patterns/system_map_dependency.md` — NEW, D7.7 generator-side consumer rule
- `Attache.omnifocusjs/Resources/dailyReview.js` — D7.4 drift signal at session start (soft warning)
- `Attache.omnifocusjs/manifest.json` + `Resources/en.lproj/com.totallytools.omnifocus.attache.strings` — version bump per D6.6 (and again if D7 ships separately)
- `plugins/attache/skills/omnifocus-core/scripts/src/tsconfig.plugin.json` + `tsconfig.cli.json` + `tsconfig.attache-libs.json` — D8.1 strict flag additions
- `plugins/attache/skills/omnifocus-core/eslint.config.js` — D8.2 `no-undef: error` + `no-unused-vars: warn`
- `plugins/attache/skills/omnifocus-generator/scripts/jxa-antipatterns.json` — D8.3 new PlugIn-API footgun rules
- `plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh` — D8.4 bundle coherence checks + D8.6 smoke-load gate
- `plugins/attache/skills/omnifocus-generator/scripts/generate_plugin.ts` — D8.5 runtime skeleton emission for `requires: ["ofoCore"]` and `requires: ["systemMap"]`
- `plugins/attache/skills/omnifocus-generator/scripts/smoke-load.js` — NEW, D8.6 stub-environment parse-evaluate test
- `plugins/attache/skills/omnifocus-generator/references/40_patterns/validation_pipeline.md` — D8.7 layered-pipeline rewrite
- `plugins/attache/skills/omnifocus-generator/references/30_api_reference/api_gaps.md` — D8.1 `@ts-expect-error #ISSUE` tracking table

**Do NOT modify** in this pass:

- Anything inside the deployed `~/Library/Containers/.../Plug-Ins/Attache.omnifocusjs/` directly (changes flow through `build-attache.sh` only)
- Other plugins in the OmniFocus library (AITaskAnalyzer, Templates, etc.)
- Any `gtd-queries.js` action logic — comment header only

## Out of Scope (Surface as Follow-Up Issues)

- **#141 (GTD-essential portions: now in D6)** — Expanding `ofo` CLI to cover full OmniFocus mutation surface. D6 closes: project create/update/move, project review marking, neglected/waiting-for/someday/completed queries, folder listing. **Remaining gaps stay on #141**: skip-one-occurrence, defer-shortcut helpers, repetition rule editing, task-level reordering, parent-task assignment, single-task→project conversion.
- **#161 (GTD-essential portions: now in D6)** — Project create + move + status changes are addressed in D6. **Remaining stays on #161**: the original unsafe-completion bug fix (audit `completeTask` for safety; this plan does not modify `completeTask`) and any task-level project-move safety improvements.
- **#135** — Plugin deploy/library reload bug. Plan documents the manual restart workaround in `40_patterns/validation_pipeline.md`; fix is its own issue. D6 will exercise this bug because `Attache.omnifocusjs` rebuilds — the executing agent should expect to restart OmniFocus after deploy.
- **#152** — Plugin structure validation handoff. Plan documents the contract in `40_patterns/validation_pipeline.md`; fix is its own issue.
- **#177** — Broader attache orchestration scope. Plan's channel-selection section is a partial down payment, but the full agent-description expansion is a separate pass.

## Verification

The executing agent (via foundry plugin) should run, in order:

1. **Structure check.** Confirm every new file in the proposed tree exists. Confirm no duplicate content between `omnifocus-generator/references/` and `omnifocus-core/references/`.
2. **System Map contract test (D7).** Run `ofo system-map --refresh` against a live OmniFocus database. Confirm the resulting JSON validates against `system_map.schema.json`. Confirm `schemaVersion`, `attacheVersion`, `generatedAt`, and `conventions.*` are all populated. Run `ofo system-map --drift-check` immediately after — should return `stale: false`. Manually rename a tag, re-run drift check — should return `stale: true` with reason `convention-broken` or `tag-drift`.
3. **GTD coverage acceptance test (D6).** For each row in the D6.1 audit table marked as a gap, confirm a matching `ofoCore` function exists, is wired into `dispatch()`, and has a CLI command. Then run each new CLI command against a live OmniFocus database and confirm a non-error response. Save sample outputs as inline examples in the relevant reference docs.
4. **Convention auto-resolution test.** Run `ofo list waiting-for` (no `--tag` flag) against a live OmniFocus database with a refreshed System Map. Confirm it auto-resolves the waiting tag from `conventions.waitingTag` and returns matching tasks. Then delete the "Attache System Map" task and re-run; confirm the command exits with the structured error pointing to `--refresh`, not a silent default.
5. **gtd-coach data-grounded coaching test.** Re-run each of the seven coaching questions from `gtd-coach/SKILL.md` using the NEW `ofo` CLI commands. Each must return useful, non-empty output (assuming the user's database has data for it). No fallback to `gtd-queries.js` should be required for any of the seven. Confirm STEP 0 (System Map currency check) fires at the start of the simulated coaching session.
6. **Skillsmith eval.** Run `uv run plugins/foundry/skills/skillsmith/scripts/evaluate_skill.py` on `omnifocus-generator`, `omnifocus-core`, `gtd-coach`, AND `attache-analyst`. All four ≥ pre-change baseline. Record scores in the plugin-level `plugins/attache/README.md` per repo convention.
7. **Plugin validation.** `bash plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/Plug-Ins/Attache.omnifocusjs` — must pass on the rebuilt bundle. Validation now includes D8.4 bundle coherence (manifest↔resources↔strings) and D8.6 pre-load smoke gate.
7a. **Egregious-error regression suite (D8.8).** Run the deliberately-broken-spec test cases from `validation_pipeline.md`. Each case MUST be caught at the layer documented (TS strict / ESLint / antipatterns / bundle coherence / smoke). No case may produce a written `.omnifocusjs` bundle. Confirm the existing happy-path generation still succeeds end-to-end with the tightened gates.
8. **Acceptance test — Foundation Models walkthrough.** Spawn a fresh sub-agent with only the new references available. Prompt: *"Build a standalone OmniFocus plugin that uses Foundation Models to organize a project's tasks into thematic groups and suggests tags. Use the references in `plugins/attache/skills/omnifocus-generator/references/`."* Measure: (a) which reference files it reads (must include `40_patterns/system_map_dependency.md`), (b) does it correctly consume `ofoCore` AND read the System Map for convention tags (not hardcoded `@waiting`), (c) does it pick the right format (`solitary-fm`), (d) does it produce a passing `validate-plugin.sh`, (e) does it WebFetch anything beyond the protocol described in `web_fetch_protocol.md`. Pass if ≤3 reference files read (excluding the schema doc) AND `ofoCore` + System Map both consumed AND validate passes.
9. **Channel-selection regression.** Spot-check 3 scenarios in a fresh attache invocation: *"create a task tagged Question❓"* (expect ofo CLI), *"set up my daily review workflow"* (expect Attache action), *"build a plugin that estimates project completion dates with FM"* (expect standalone plugin). Agent should pick correctly without prompting.
10. **Follow-up issue updates.** Comment on #141 and #161 listing which sub-items were closed by D6 and which remain. Comment on #135, #152, #177 linking to the new reference docs that document the gaps.
11. **Repo convention.** Copy the executed plan to `plugins/attache/docs/plans/2026-06-15-001-attache-references-routing-plan.md` per the repo's plan-tracking convention (this harness path is ephemeral).

## Constraints for the Executing Agent

- **Two-Phase Execution.** See the "Two-Agent Handoff Model" section above for the split. Suggested order BY PHASE:
  - **Phase 1 (Research Agent, parallel start):** D4 workflow doc creation + D4 workflow EXECUTION against omni-automation.com → capability_inventory.md → drafted 20_capabilities/*.md skeletons → plan update with RESEARCH COMPLETE marker.
  - **Phase 2 (Implementation Agent):** D8.1 + D8.2 (config tightening, fast first) → D7.1 → D7.2 → D7.3 → D6.1 → D8.3 (antipatterns, since they constrain generator output) → D6.2 → D6.3 → D6.4 → D6.6 → D7.4 → D7.5 → D7.7 → D8.4 → D8.5 → D8.6 → D8.7 → D8.8 (regression suite) → D1 (parallelizable from Phase 2 start) → D2 (reorg + integrate Phase 1's capability drafts) → D3 → D5 → D7.8 (capability map row).
  - D8.1/D8.2 first in Phase 2 because tightening the existing pipeline surfaces existing-code issues that must be triaged before D6/D7 add new code on top.
- **Phase 2 must NOT re-execute D4 or regenerate capability docs from scratch.** Phase 1's drafts are the source. If Phase 2 finds a draft inadequate, polish it; don't discard.
- **Do NOT fix the remaining portions of #141/#161/#135/#152/#177.** D6 closes only the GTD-essential subsets called out in D6.1; D7 makes them depend on the System Map. Surface the rest as issue comments.
- **`ofo-core.ts` and `ofo-cli.ts` changes are confined to D6 and D7.** No drive-by refactors of existing functions. If you spot a `completeTask` safety concern (the original #161 bug), file a follow-up — do not patch in this pass.
- **`systemDiscovery.ts` changes are confined to D7.2** (adding `schemaVersion`, `conventions.*`, `discoveryMode`). Do not refactor the inference logic in this pass — that's a separate concern.
- **Follow the plugin validation workflow** captured in memory (`feedback_plugin_validation_workflow.md`): skillsmith eval, plugin validation, version bumps (D6.6 AND D7.2 require a manifest version bump because library functions and System Map schema change), marketplace sync.
- **Commit per phase** (memory: `feedback_commit_per_phase.md`): one commit per deliverable (D1, D2, D3, D4, D5, D6, D7, D8). D6 may need sub-commits — split by D6.2 (library), D6.3 (CLI), D6.4 (gtd-coach), D6.6 (build + version bump). D7 sub-commits: D7.2 (schema doc + JSON Schema + systemDiscovery changes), D7.3 (CLI commands), D7.4 (drift signals + dailyReview update), D7.7 (generator reference). D8 sub-commits: D8.1+D8.2 (config tightening with any required `@ts-expect-error` annotations), D8.3 (antipatterns), D8.4 (validate-plugin.sh coherence checks), D8.5 (generator skeletons), D8.6 (smoke-load), D8.7 (reference doc), D8.8 (regression suite).
- **Use the foundry plugin's loop**: evaluate (`/ss-improve`) before changes, explain the gap, fix, re-evaluate. Record the eval delta in the commit message.
- **Cite the plan path** in every commit: `Refs: plugins/attache/docs/plans/2026-06-15-001-attache-references-routing-plan.md`.
- **System Map is the single source of truth for user convention.** Stateless `ofoCore` takes convention as args; the CLI dispatch (and any plugin action) reads the System Map and passes the resolved values. **Do not introduce silent defaults** — if the map is missing or a convention field is empty, surface a structured error pointing to `ofo system-map --refresh`. The old fallback chain ("preferencesManager → common defaults → ask user") is REPLACED by "System Map → structured error". `preferencesManager` continues to store ephemeral learning (e.g., the user's preferred coaching cadence) but is NOT the source of convention truth.
