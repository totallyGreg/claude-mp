---
title: "feat: omnifocus-agent System Map bootstrap for personalized GTD coaching"
type: feat
status: active
date: 2026-03-22
github_issue: "https://github.com/totallyGreg/claude-mp/issues/123"
---

# feat: omnifocus-agent System Map bootstrap for personalized GTD coaching

## Overview

The `omnifocus-agent` currently operates blind — it has no knowledge of the user's actual
OmniFocus folder names, tag taxonomy, or conventions. It gives generic examples (`@work`,
`@computer`) even when Attache has already discovered and cached the user's real system
structure in the "Attache System Map" task note in `⚙️ Synced Preferences`.

This plan adds five targeted text changes to two files to wire the agent to that cached map,
so every coaching interaction uses the user's real tag and folder names. It also fixes the
execution rules, which still reference JXA as the primary execution path despite ofo CLI
being preferred since v7.0.

**Phase 1 scope:** markdown/text edits only — no TypeScript changes. Native OmniFocus field
gaps (see below) are documented and deferred to Phase 2.

`ofo system-map` CLI command (single-step map retrieval) is explicitly out of scope and
tracked separately.

## Problem Statement

1. **Generic coaching** — gtd-coach uses hardcoded examples (`@waiting`, `@computer`, `@phone`).
   If the user's waiting tag is `⏳ Waiting On` or their someday folder is "💭 Ideas", the
   coach's instructions are wrong by name.

2. **Execution rules mismatch** — `omnifocus-agent.md` line 190 says "Run scripts directly"
   with `osascript -l JavaScript` as the implied path, contradicting SKILL.md's "Use ofo for
   all task CRUD and queries when possible."

3. **No context bridge** — when routing to gtd-coach, no system context is passed. The skill
   reads only its own SKILL.md, so it can never refer to the user's actual system.

4. **Health checks go deep unnecessarily** — "How's my system?" routes directly to
   `gtd-queries.js --action system-health` (slow JXA full-database scan). `ofo stats` gives
   inbox/flagged/overdue counts in ~1s and covers most "quick pulse" questions.

5. **System Map misrepresents native fields** — `systemDiscovery.js` `TIME_PATTERNS` conflates
   native duration (`estimatedMinutes`) with scheduling-context tags (`morning`, `afternoon`)
   in a single `tags.categories.time[]` array. The agent must split these before passing context
   to gtd-coach.

6. **ofo CLI gaps prevent full insight** — several native OmniFocus fields central to GTD
   coaching are absent from the ofo stack entirely (see ofo CLI Field Gaps section).

## ofo CLI Field Gaps (Phase 2 work)

These native OmniFocus fields are missing from the ofo CLI and limit the depth of coaching.
Documented here so Phase 1 implementation is honest about what the System Map can and cannot
represent.

| Field | OmniFocus Object | Gap | Impact |
|-------|-----------------|-----|--------|
| `plannedDate` | Task | Entirely absent from `ofo-core.ts`, `ofo-cli.ts`, `gtd-queries.js`, `systemDiscovery.js` | Cannot surface "scheduled for today" without a due date; `ofo list today` misses planned tasks |
| `estimatedMinutes` | Task | Present in `getTask()` (line 78) but absent from `taskSummary()` (line 198-208, used by `ofo list`) | List views cannot show effort/duration |
| `estimatedMinutes` | Project | Absent from project branch of `getTask()` (lines 19-38) | Project-level effort rollups impossible |
| `reviewInterval` | Project | Entirely absent from ofo output | Cannot coach on review cadence |
| `nextReviewDate` | Project | Entirely absent from ofo output | Cannot flag overdue reviews |
| `repetitionRule` | Task | Entirely absent from ofo output | Cannot distinguish repeating from one-off tasks |
| `plannedDate` in `ofo list today` | Task | Filter is `isDueToday \|\| isFlagged` — misses tasks where `plannedDate = today` | Daily planning misses intentionally scheduled work |

**`plannedDate` requires a database migration guard** — OmniFocus 4 only. Any ofo-core.ts
implementation must detect whether the field exists before accessing it and fall back gracefully.

## Native Fields vs. Tag Inference (Design Principle)

Where OmniFocus provides a native field, use it — do not infer the same signal from text tags.

| Signal | Native field | Tag-based inference (avoid) |
|--------|-------------|----------------------------|
| Task duration/effort | `estimatedMinutes` | `15min`, `30min`, `1hr` tags |
| Scheduled intent | `plannedDate` | Date-in-task-name patterns |
| Review cadence | `reviewInterval` / `nextReviewDate` | Folder naming conventions |
| Recurrence | `repetitionRule` | Naming suffixes like "daily" |

Tags for duration (`15min`, `30min`) remain valid as **fallback** when `estimatedMinutes` is not
set. The agent should surface which model a user is actually using (see `durationModel` below).

## Proposed Solution

Five implementation units, all markdown/text edits — no TypeScript changes in Phase 1:

| Unit | File | Change |
|------|------|--------|
| 1 | `agents/omnifocus-agent.md` | Add `## System Map Context` section with lazy bootstrap procedure |
| 2 | `agents/omnifocus-agent.md` | Fix Execution Rules: ofo CLI → gtd-queries.js → manage_omnifocus.js hierarchy |
| 3 | `agents/omnifocus-agent.md` | Multi-skill routing: pass System Map excerpts to gtd-coach (with TIME_PATTERNS split) |
| 4 | `agents/omnifocus-agent.md` | Health check routing: `ofo stats` as fast first-pass |
| 5 | `skills/gtd-coach/SKILL.md` | Add `## System Context` section for injected map data |

## Technical Approach

### System Map storage (read-only — Attache writes, agent only reads)

```
Folder:  ⚙️ Synced Preferences
Project: ⚙️ Synced Preferences   (same name, inside the folder)
Task:    Attache System Map        (task note = JSON)
```

Retrieved via two existing ofo commands:
```bash
# Step 1: locate
"${ofo}" search "Attache System Map"   # returns id, name, project

# Step 2: read note
"${ofo}" info <id>                     # returns full task object including .note (JSON string)
```

### System Map JSON shape (relevant subset)

```json
{
  "structure": {
    "topLevelFolders": [
      { "name": "Work", "inferredType": "area", "projectCount": 12 },
      { "name": "Archive", "inferredType": "archive" }
    ]
  },
  "tags": {
    "categories": {
      "contexts": [{ "tag": "@office", "usage": 34 }],
      "people":   [{ "tag": "@waiting", "usage": 8 }],
      "status":   [{ "tag": "someday", "usage": 15 }],
      "energy":   [{ "tag": "@focus", "usage": 22 }],
      "time":     [{ "tag": "15min", "usage": 41 }, { "tag": "morning", "usage": 12 }]
    }
  },
  "tasks": {
    "dataQuality": {
      "percentWithDuration": 72
    }
  },
  "conventions": {
    "tagConventions": { "usesAtPrefix": true, "usesEmoji": false }
  }
}
```

**`tags.categories.time[]` conflation warning:** `systemDiscovery.js` stores both duration tags
(`15min`, `30min`, `1hr`) and scheduling-context tags (`morning`, `afternoon`, `evening`,
`weekend`, `weekday`) in the same `time` array. When passing to gtd-coach, the agent must
split them:

- **Duration tags**: entries matching time-magnitude patterns (`\d+(min|hr|h|m)`, `quick`, `deep`)
- **Scheduling-context tags**: entries matching time-of-day/week patterns (`morning`, `afternoon`,
  `evening`, `weekend`, `weekday`)

### durationModel derivation

After loading the System Map, derive the user's duration convention and hold it in context:

```
percentWithDuration = tasks.dataQuality.percentWithDuration  (from systemDiscovery)

durationModel =
  "native"  if percentWithDuration > 50
  "tags"    if percentWithDuration < 20 AND duration tags exist in tags.categories.time[]
  "mixed"   if percentWithDuration 20-50 AND duration tags exist
  "none"    otherwise
```

Pass `durationModel` to gtd-coach so it coaches on `estimatedMinutes` vs. duration tags
appropriately. If `durationModel = "native"`, coach: "Use the Estimate field on the task."
If `durationModel = "tags"`, coach: "Use your `15min` / `30min` tags."

### Design decisions (resolved from SpecFlow analysis)

| Question | Decision |
|----------|----------|
| When does bootstrap run? | **Lazy** — on first request that benefits from System Map context (coaching, health, search). Not for simple task CRUD. |
| How is context passed to gtd-coach? | Agent prepends a `**System Map context:**` block inline before the coaching content when System Map was loaded. gtd-coach SKILL.md section explains how to use injected blocks. |
| JSON.parse failure? | Warn user: "Attache System Map note could not be parsed — it may be corrupted. Re-run Attache Setup in OmniFocus." Fall back to generic examples. |
| Multiple search results? | Take first result, warn: "Found N tasks named 'Attache System Map' — using the first. Complete or rename duplicates to avoid confusion." |
| Tag divergence (map vs. reality)? | Phase 1: document as known limitation. Phase 2: cross-reference `ofo tags` output. |
| Staleness detection? | Not possible without modification timestamp in ofo info output. Show `lastWritten` date from System Map JSON as a hint to the user. |
| ofo stats vs. /ofo:health? | `ofo stats` for fast first-pass counts; `/ofo:health` for full diagnostic when user wants a complete picture. |
| ofo system-map command? | Out of scope — tracked as a separate issue. |
| Attache not set up? | Continue session with generic coaching. Mention: "Run Attache's Setup action in OmniFocus to personalize future sessions." |
| TIME_PATTERNS conflation? | Agent splits time[] into duration-tags vs. scheduling-context-tags before passing to gtd-coach. |
| Duration coaching model? | Derive `durationModel` from `tasks.dataQuality.percentWithDuration`; coach on native field vs. tags accordingly. |
| plannedDate absent? | Document gap. `ofo list today` misses planned tasks. Phase 2: add to ofo-core.ts with migration guard. |

### Unit 1: System Map Context section (omnifocus-agent.md)

Add after `## Skills Available`, before `## Intent Classification`:

```markdown
## System Map Context

The Attache plugin stores a cached map of the user's OmniFocus structure in a task note.
Read it **lazily** — on the first request that benefits from knowing the user's tags/folders
(any coaching, health, or search session). Skip for simple task CRUD one-offs.

**Retrieve:**
```bash
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo" search "Attache System Map"
# → get the task ID from results
"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo" info <id>
# → parse the .note field as JSON
```

**Extract and hold in context:**
- `tags.categories.contexts[]` — user's actual context tags (what GTD calls "Next Action" contexts)
- `tags.categories.people[]` — user's waiting/delegation tags
- `tags.categories.status[]` — user's someday/maybe and on-hold tags
- `tags.categories.time[]` — **split before use**: duration tags (`15min`, `30min`, `1hr`) vs.
  scheduling-context tags (`morning`, `afternoon`, `evening`, `weekend`)
- `tags.categories.energy[]` — effort tags
- `structure.topLevelFolders[]` — folder names and inferred types (area/archive/someday/reference)
- `tasks.dataQuality.percentWithDuration` — derive `durationModel` (see below)
- `lastWritten` — show this date if the map appears stale

**Derive `durationModel`:**
```
percentWithDuration = tasks.dataQuality.percentWithDuration
durationModel =
  "native"  if > 50%     → user sets Estimate field; coach on estimatedMinutes
  "tags"    if < 20% and duration tags exist → user tags duration; coach on tags
  "mixed"   if 20-50%    → hybrid; surface both
  "none"    otherwise    → no duration practice; suggest starting one
```

**Fallback behavior:**
- 0 results → continue with generic examples; mention "Run Attache Setup in OmniFocus to
  personalize future coaching sessions"
- note is empty or not valid JSON → warn "Attache System Map note could not be parsed —
  re-run Attache Setup in OmniFocus"; fall back to generic examples
- multiple results → use first result; warn "Found N matches for 'Attache System Map'"
- Attache not installed → skip silently, use generic examples

**Known limitations:**
- System Map tags are not validated against the live tag list — re-run Attache Setup after
  reorganizing tags
- `plannedDate` is not in the System Map or `ofo list today` — tasks scheduled via the
  Forecast plan field are invisible to the agent (Phase 2 gap)
```

### Unit 2: Fix Execution Rules (omnifocus-agent.md)

Replace lines 187-193 with a clear ofo-first hierarchy:

```markdown
## Execution Rules

- **Load skills on-demand** — only load SKILL.md when routing to that skill
- **Load references as needed** — read from `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/references/` when deeper detail is required
- **Execution hierarchy** (follow this order):
  1. **ofo CLI** (preferred for all CRUD and queries): `"${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo" <command>`
  2. **gtd-queries.js** (JXA diagnostics only): `cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/gtd-queries.js --action <action>`
  3. **manage_omnifocus.js** (legacy — bulk-create and project hierarchy only): `cd "${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager" && osascript -l JavaScript scripts/manage_omnifocus.js bulk-create --json-file <path>`
- **Respect boundaries** — gtd-coach should never run OmniFocus automation; omnifocus-manager should not coach GTD methodology
- **Default to omnifocus-manager** — if unclear whether a request is methodology or execution, start with omnifocus-manager
```

### Unit 3: System Map → gtd-coach context passing (omnifocus-agent.md)

In `### Multi-Skill Requests (Both)`, add after "Lead with methodology":

```markdown
**When System Map is loaded**, prepend a context block before the coaching content.
Split `tags.categories.time[]` before passing — duration tags and scheduling-context tags
must not be mixed:

> **System Map context (from Attache):**
> - Context tags: `@office`, `@home`, `@phone` (from `tags.categories.contexts`)
> - Waiting tag: `@waiting` (from `tags.categories.people`)
> - Someday/on-hold: `someday` tag or "💭 Ideas" folder (from `tags.categories.status` + folder type "someday")
> - Duration tags: `15min`, `30min`, `1hr` (duration entries from `tags.categories.time`)
> - Scheduling context: `morning`, `weekend` (time-of-day/week entries from `tags.categories.time`)
> - Duration model: `native` — user sets Estimate field; coach on the Estimate field, not tags
> - Areas: "Work", "Personal" folders (from `structure.topLevelFolders` where type = "area")
> - ⚠️ Gap: `plannedDate` is not surfaced — tasks scheduled via Forecast may not appear in lists
>
> [coaching content follows]

If System Map is not available, proceed with generic GTD terminology — the coaching is still
correct, just not personalized to this user's naming conventions.
```

### Unit 4: Health check routing update (omnifocus-agent.md)

Add two entries to the routing table:

```markdown
| "Quick stats" / "Give me a snapshot" | omnifocus-manager | `ofo stats` (fast: inbox/flagged/overdue/projects counts) |
| "How's my system?" / "Quick health check" | omnifocus-manager | `ofo stats` first, then `/ofo:health` for full diagnostic |
```

(Remove or update the existing "How's my GTD system?" → `gtd-queries.js --action system-health`
entry to clarify that system-health is the deep scan, stats is the fast one.)

### Unit 5: System Context section in gtd-coach SKILL.md

Add a new section after `## The Five Phases`:

```markdown
## System Context (when provided by omnifocus-agent)

When the omnifocus-agent provides a `**System Map context:**` block, use the user's actual
names throughout your coaching — do not fall back to generic GTD examples.

**Use the System Map to:**
- Replace generic context examples (`@computer`, `@phone`) with the user's actual context tags
- Refer to their specific waiting tag by name ("move this to your `@waiting` tag")
- Name their actual Someday/Maybe tag or folder when coaching defer decisions
- Reference their real Area folders when discussing horizons of focus
- Coach on duration using the right model:
  - `durationModel: native` → "Set the Estimate field to 30 minutes"
  - `durationModel: tags` → "Tag this with `30min`"
  - `durationModel: mixed` → ask which they prefer; help them pick one
  - `durationModel: none` → suggest starting an estimation practice

**Scheduling gap — mention when relevant:** OmniFocus's `plannedDate` (Forecast scheduling)
is not yet surfaced by the ofo CLI. If a user asks "why isn't this task showing up today?",
check whether they used the Forecast plan date — that field is invisible to the agent.

**If no System Map is provided:** use generic GTD terminology. The coaching principles are
correct regardless of the user's specific tag names.

**Example — with System Map (native duration model):**
> "Since you use the Estimate field, set this task's estimate to 30 minutes. That way your
> context views can filter by effort when you're short on time."

**Example — with System Map (tag duration model):**
> "Tag this with `30min` so your context views can filter by effort."

**Example — without System Map:**
> "Add a duration signal — either the Estimate field or a time tag — so you can filter tasks
> by effort when you're short on time."
```

## Acceptance Criteria

### Functional

- [ ] Agent includes a `## System Map Context` section documenting the lazy bootstrap procedure
- [ ] Bootstrap uses `ofo search "Attache System Map"` + `ofo info <id>` (no new CLI commands)
- [ ] All four fallback cases are documented: 0 results, empty/invalid note, multiple results, Attache not installed
- [ ] System Map context section documents the TIME_PATTERNS split (duration vs. scheduling-context)
- [ ] `durationModel` derivation is documented in the bootstrap section
- [ ] `plannedDate` gap is disclosed in the bootstrap section and in Unit 3 context block
- [ ] Execution Rules establish ofo → gtd-queries.js → manage_omnifocus.js hierarchy explicitly
- [ ] Multi-skill routing section includes System Map context block format for gtd-coach with split time tags
- [ ] Routing table has `ofo stats` for fast health checks, distinguishes from `/ofo:health` deep scan
- [ ] gtd-coach SKILL.md has `## System Context` section explaining how to use injected map data
- [ ] gtd-coach section coaches on `durationModel` (native vs. tags vs. mixed vs. none)
- [ ] gtd-coach section mentions `plannedDate` gap
- [ ] gtd-coach section includes before/after examples for each duration model

### Boundaries

- [ ] No new ofo CLI commands added (Phase 2)
- [ ] No changes to ofo-core.ts or ofo-cli.ts
- [ ] No changes to Attache plugin files
- [ ] `ofo system-map` command is not implemented — tracked as separate issue

### Quality

- [ ] Skillsmith eval ≥ 97/100 on omnifocus-manager skill after changes
- [ ] System Map bootstrap section appears before line 100 in the agent body (per SKILL.md lesson: critical workflows must be early)

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| System Map JSON schema changes in future Attache version | Agent reads only a stable subset (`tags.categories`, `structure.topLevelFolders`, `tasks.dataQuality`, `conventions`) — not all fields |
| User has not run Attache Setup | Documented fallback: continue with generic coaching |
| `ofo search` returns completed/dropped tasks | `searchTasks` in ofo-core.ts already filters out completed/dropped (confirmed lines 166-168) |
| Tag names in map diverge from current OmniFocus state | Phase 1 known limitation; documented in agent |
| TIME_PATTERNS conflation misleads coaching | Agent splits the array before passing to gtd-coach; duration and scheduling-context tags are labeled separately |
| `plannedDate` absent causes "why isn't this showing?" confusion | Gap disclosed in bootstrap section and in gtd-coach context block |
| `durationModel` mis-derived if `percentWithDuration` is stale | Show `lastWritten` date; prompt re-run of Attache Setup if >30 days |

## Implementation Sequence

```
Unit 2 (Execution Rules)        — independent, 5 min
Unit 4 (Health check routing)   — independent, 5 min
Unit 1 (System Map section)     — main addition, 25 min
Unit 3 (gtd-coach context pass) — depends on Unit 1 wording, 15 min
Unit 5 (gtd-coach SKILL.md)    — depends on Unit 3 interface, 15 min
```

Run skillsmith eval after all units, bump version (9.2.0), update README.md history.

## Future Work (out of scope)

### Phase 2: ofo CLI native field coverage

- **`plannedDate` in ofo-core.ts** — expose on task info and list commands; requires database
  migration guard (OmniFocus 4 only; detect field existence before access)
- **`ofo list today` expanded** — add `plannedDate = today` to the filter alongside `isDueToday || isFlagged`
- **`estimatedMinutes` in `taskSummary()`** — add to the lean shape returned by `ofo list` so
  list views can show effort without a second `ofo info` call
- **`estimatedMinutes` on project branch** — add to project info output in `getTask()`
- **`reviewInterval` and `nextReviewDate` in project info** — expose so agent can flag overdue reviews
- **`repetitionRule` in task info** — distinguish repeating from one-off tasks in coaching
- **`ofo stats` enriched** — add `reviewOverdue`, `plannedToday`, and `withEstimate` counts for richer coaching snapshots

### Phase 2: System Map improvements

- **`ofo system-map` command** — single-step read from Synced Preferences; tracked as separate issue
- **Tag validation** — cross-reference System Map tags against `ofo tags` live output; surface stale tags
- **Modification timestamp in `ofo info`** — needed for automatic staleness detection; ofoCore data model change
- **Split `TIME_PATTERNS` in systemDiscovery.js** — store duration tags and scheduling-context tags in
  separate arrays in the System Map JSON so the agent does not need to split them

## Sources & References

- `plugins/omnifocus-manager/agents/omnifocus-agent.md` — current agent (lines 187-193: execution rules to fix)
- `plugins/omnifocus-manager/skills/gtd-coach/SKILL.md` — gtd-coach current state
- `plugins/omnifocus-manager/skills/omnifocus-manager/assets/Attache.omnifocusjs/Resources/preferencesManager.js` — System Map storage path (lines 25-27, 51-53)
- `plugins/omnifocus-manager/skills/omnifocus-manager/assets/Attache.omnifocusjs/Resources/systemDiscovery.js` — System Map JSON schema (lines 715-776); TIME_PATTERNS conflation (line 45); `percentWithDuration` tracking (lines 304-346)
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src/ofo-core.ts` — `getTask` return shape (lines 66-84); `taskSummary` shape (lines 198-208); `searchTasks` filtering (lines 166-168); `ofo list today` filter (line 228)
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/omnifocus_api.md` — `plannedDate` (lines 742-743, OmniFocus 4 + migration); `estimatedMinutes` (lines 718-719); `reviewInterval` (line 913)
- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — "critical workflows must appear before line 100"
- `docs/plans/2026-03-22-002-refactor-ofo-script-consolidation-gtd-coverage-plan.md` — prior consolidation work (PR #122)
- Related PR: #122 (merged — script consolidation)
