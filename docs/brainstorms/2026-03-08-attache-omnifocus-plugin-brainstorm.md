# Brainstorm: Attache — Unified OmniFocus AI Assistant

**Date:** 2026-03-08
**Status:** Ready for planning
**Participants:** User, Claude

---

## What We're Building

**Attache** is a renamed, expanded, and unified replacement for `AITaskAnalyzer.omnifocusjs`. It consolidates scattered AI and curation plugins into a single composable bundle with persistent memory — acting as a quiet diplomatic aide that knows your GTD system and brings what you need, when you need it.

The primary motivation is reviews: daily and weekly reviews are hard. Attache's north star is making reviews effortless by already knowing your system, your completed work, and your patterns.

**Requires macOS 26+ (Apple Intelligence).** All actions gate on this. Deterministic logic (date math, task counts) runs as code; FM is used where it adds value (natural language understanding, analysis, generation).

---

## Problem Statement

1. **No memory** — Every plugin run starts cold. `systemDiscovery.js` re-discovers the same system structure each time. GTD preferences are never remembered.
2. **Too many separate plugins** — ~20 installed plugins with no unified entry point. AI capabilities duplicated across `of-afm-assist`, `of-help-me-plan`, `of-help-me-estimate`.
3. **Reviews are hard** — `weeklyReview.js` and `dailyReview.js` start fresh with no knowledge of the user's personal GTD conventions.
4. **OS version bug** — `foundationModelsUtils.js` gates on `15.2`; should be `26`. Inconsistent behavior today.

---

## Existing Plugin Inventory

### Assets in This Repo (`assets/`)
| Plugin | Actions | Disposition |
|--------|---------|-------------|
| `AITaskAnalyzer.omnifocusjs` | 7 | Renamed → Attache; enhanced |
| `CompletedTasksSummary.omnifocusjs` | 2 | Absorb |
| `Overview.omnifocusjs` | 1 | Absorb |
| `TodaysTasks.omnifocusjs` | 1 | Absorb |
| `TreeExplorer.omnifocusjs` | 4 | Keep separate (export utility) |

### Installed in iCloud Plug-Ins
| Plugin | Purpose | Disposition |
|--------|---------|-------------|
| `SyncedPreferences.omnifocusjs` | iCloud-synced preferences via task notes | **Adopt pattern; store Attache prefs as task in existing project** |
| `of-afm-assist.omnifocusjs` | Subtask generation (overlaps `analyzeSelected`) | Absorb; retire |
| `of-help-me-estimate.omnifocusjs` | AI time estimation | Absorb |
| `of-help-me-plan.omnifocusjs` (Ken Case) | AI task breakdown (overlaps `analyzeSelected`) | Absorb; retire |
| `of-tasks-to-projects.omnifocusjs` | Convert tasks to projects | Absorb into curation actions |
| `CompletedTaskReport.omnifocusjs` | Completed task reporting | Absorb |
| `functionLibrary.omnifocusjs` | Shared utilities | Read and fold useful parts into Attache libraries |
| `of-date-controls.omnifocusjs` | Defer/due date bumping (~20 actions) | Keep separate — toolbar utility |
| `updateEstimatedDuration.omnifocusjs` | Time estimate controls (12 actions) | Keep separate — toolbar utility |
| `of-complete-await-reply.omnifocusjs` | Complete + create Waiting task (Rosemary Orchard) | Keep separate — external author |
| All others | UI utilities, Obsidian, calendar, clipboard | Keep separate |

---

## The Persona: The Diplomatic Aide

An *attaché* carries your briefing materials, stays quietly in the background, and surfaces what you need. No showboating.

- Invoked, works, reports clearly
- Output structured and scannable
- On first run: learns your system. Every subsequent run: already knows it.

---

## Architecture

### Composable Bundle with Persistent Memory

Single `Attache.omnifocusjs` bundle with shared PlugIn.Library modules.

**Entry point:** `attache` — a command palette action (see UX below). Individual actions also accessible from the action palette for toolbar/shortcut assignment.

**Persistence:** Attache adds a task to the existing `⚙️ Synced Preferences` project (created by `SyncedPreferences.omnifocusjs`) using the same task-note JSON pattern. Synced via iCloud automatically. On first run, `systemSetup` runs `discoverSystem`, caches the result as the Attache preference task, and doesn't re-run unless explicitly triggered. Preferences are **inferred** from OmniFocus configuration, not manually entered.

**macOS requirement:** All actions gate on `Device.current.operatingSystemVersion.atLeast(new Version("26"))`. On failure: clear alert with OS version shown. Fix the current `15.2` bug throughout.

### Command Palette UX (`attache` action)

The main entry point uses the OmniAutomation `Form` API:

- **Title**: Live status bar — `"📥 3 inbox  |  🔴 7 overdue  |  ✅ 12 done today"`
- **`Form.Field.String`**: Natural language input — `"What do you want to achieve?"` — used for deferred date input, task intent, or filtering
- **`Form.Field.Option`**: Action list, filtered dynamically via `Form.validate` as user types in the string field
- **Flow**: Tab to switch between fields; Enter to confirm. FM parses natural language input (dates, intent) before applying.
- **Contextual**: Selection present → task-focused actions first. No selection → review and analysis actions first.

---

## Proposed Action Set

### AI Actions
| Action | Description |
|--------|-------------|
| `attache` | Command palette entry point |
| `dailyReview` | Morning orientation: wins, top 3 next actions, overdue triage |
| `weeklyReview` | Full GTD weekly review with cached system context |
| `analyzeSelected` | Selected tasks: clarity score, name suggestions, tags, time estimate |
| `planSelected` | Subtask generation from task name/note |
| `estimateSelected` | Time estimation for selected tasks |
| `analyzeProjects` | Project health: stalled, overdue, completion rate |
| `analyzeHierarchy` | Full system GTD analysis |
| `completedSummary` | What I accomplished: today / this week / this month |

### Curation Actions (code-driven, FM assists where useful)
| Action | Description |
|--------|-------------|
| `deferTo` | Natural language defer date input — FM parses, code applies |
| `convertToProject` | Convert selected tasks to projects |
| `markWaiting` | Complete + create "Waiting: [task]" copy |
| `systemSetup` | First-run: discover + cache system map |
| `preferences` | View/update cached preferences and system map |

---

## Key Design Decisions

1. **macOS 26 required throughout** — Simplifies the requirement surface. No silent fallback mode.
2. **Code for deterministic, FM for understanding** — Date arithmetic, task counts, filtering: pure JS. Analysis, NL dates, suggestions: FM.
3. **Inferred preferences** — `systemSetup` runs `discoverSystem` once and caches. No settings forms.
4. **Preferences stored in `⚙️ Synced Preferences`** — Reuse existing iCloud-synced project; Attache adds its own task there. No new OmniFocus folder created.
5. **Composable: absorb AI duplicates, leave toolbar utilities** — `of-date-controls` and `updateEstimatedDuration` stay separate.
6. **Bundle ID**: `com.totallytools.omnifocus.attache` — clean break from `ai-task-analyzer`.

---

## Open Questions

1. **`completedSummary` output** — Clipboard, OmniFocus note, or user's choice? (Non-blocking; can decide at implementation.)

---

## Out of Scope

- iOS-specific actions
- Date/time toolbar button arrays (stay in `of-date-controls`, `updateEstimatedDuration`)
- Obsidian, calendar, clipboard ecosystem integrations
- Custom SwiftUI settings panel (not possible in Omni Automation)
