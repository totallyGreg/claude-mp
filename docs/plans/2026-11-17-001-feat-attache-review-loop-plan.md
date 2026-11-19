# Attache review loop: OmniFocus review → periodic notes

Status: in progress. Triage session 1 done (§ Evidence); tasks 0–3 done 2026-11-17 (attache 12.3.0, plug-in 2.21.0); task 4 next. Branch: `feature/attache-review-loop`.
Issue: [#269](https://github.com/totallyGreg/claude-mp/issues/269). Absorbs [#268](https://github.com/totallyGreg/claude-mp/issues/268) (re-evaluating the 14 Attache actions). Part of [#186](https://github.com/totallyGreg/claude-mp/issues/186).
Brainstorm: vault `800 Generated/820 Brainstorms/attache-omnifocus-review-loop.md` (decisions, requirements, open questions; the source for this plan).

## Goal

Reviews happen again and stay easy. The user reviews inside **OmniFocus's own project review**; the Attache plug-in adds Foundation Models guidance there, applies safe fixes itself, and pushes what happened into the Obsidian periodic notes. Routines become something tracked and encouraged, not a pile of overdue checkboxes.

Success looks like:
- A project review in OmniFocus takes minutes: Attache shows what's vague, duplicated, stale or done, fixes the safe things, asks about the rest, and marks the project reviewed.
- The weekly note fills itself (GTD sections, wins, review friction), and daily notes record routine completions that a chart turns into encouragement.
- `ofo stats` `reviewOverdue` trends to near zero and stays there; overdue stays small.

## Decisions (from the brainstorm)

| Topic | Decision |
|---|---|
| Order | Triage first; friction found in triage becomes requirements. More triage sessions run alongside the build as dogfooding |
| Where reviews happen | Inside OmniFocus's built-in project review (Review perspective, review interval, Mark Reviewed), with Attache + Foundation Models guidance |
| Autonomy | Auto-apply and log: renames, estimates, tag fixes (existing tags only), marking a project reviewed. Ask: complete, drop, defer, repeat changes, merges, moves |
| Vault outputs | Weekly review summary, daily completions, project status, the OmniFocus inbox input's `last_processed` / `open_count` |
| Handoff | The plug-in pushes through an `obsidian://` link that opens Obsidian; the vault is chosen from a list or remembered |
| Health routines | Kept, defer-only dates (done in triage 1), completions tracked in daily-note metadata and charted for the weekly review |
| Logging chores | Removed, unless one click logs to the daily note |
| Subscriptions | One repeating task per subscription stays: it's how the user reviews them |

## Constraints

- **No completion events.** Omni Automation runs only when an action is invoked; a plug-in can't react to the user ticking a checkbox. Click-to-log therefore needs either an Attache action that completes *and* logs, or a one-click "wrap up the day" action that reads today's completions and pushes them. (§ Task 3 decides.)
- **On-device model window: 8,192 tokens** for instructions + input + answer (macOS 27; `local-inference/references/apple-fm.md`). One project's tasks (~10 on average: 877 tasks / 85 projects) fit; the whole database doesn't. Cross-project work (duplicates) must pre-filter deterministically and send the model only candidates. Foundation Models exist only inside Omni Automation, not JXA/`ofo`.
- **The plug-in can't read Obsidian's vault list** (outside OmniFocus's sandbox) — verify; expected design is "ask once, remember, change in settings".
- **Plug-in and CLI must ship together.** `ofo` calls `ofoCore` inside the installed plug-in; on 2026-11-16 the installed plug-in was three releases behind the CLI (`Unknown action: ofo-tagged`). Every change: `npm run build && npm run deploy` (`plugins/attache/CONTRIBUTING.md`).
- Repo rules: version bumps in the first commit touching a plugin/skill; skillsmith eval recorded per skill; JXA validator before JXA commits; vault writes only through the archivist (curator content, architect structure).

## Team

| Seat | Model | Owns |
|---|---|---|
| Orchestrator (this session) | Opus | The design across all pieces; plug-in and `ofo` code (omnifocus-generator work); skill/agent updates; this plan |
| Attache | Sonnet | Triage sessions (GTD coach + omnifocus-core); review-cadence exploration with real projects; friction capture |
| Archivist architect | Sonnet | Vault side of the handoff: link format, note targets and schema, daily-note routine properties, Bases chart, Inputs fields, missing workflow notes |
| Archivist curator | Haiku (lookups) / Sonnet (writes) | Keeps [[OmniFocus]], [[How I Use OmniFocus]], [[Attache]] and workflow notes current as features ship |

## Tasks

### 0. `ofo` gaps found in triage (orchestrator) — done 2026-11-17
Small, unblock the rest. All five shipped and tested against OmniFocus 4.10.1 (writes on a throwaway project, since dropped). Notes: `ofo search` already excluded completed/dropped tasks, so only `--project` was added; new projects default to *not* completing with their last action (6 of 86 active projects do), so the drop guard only fires for those.
- `ofo update --repeat <rule>` (and schedule type): triage couldn't change "every 8 hours" → daily.
- Task status serializes as `[object Task.Status: Dropped]`; emit plain values.
- Installed-plug-in version check: `ofo stats` / `/ofo-health` warns when the installed `Attache.omnifocusjs` is older than the source manifest.
- `ofo search` filters (`--project`, `--active-only`) and a `similar <name>` query for duplicate checks.
- Drop safety: refuse (or warn) when dropping the only task of a project that would then complete.

### 1. Explore the review-cadence pattern (attache + orchestrator) — done 2026-11-17
**Decided: a mix.** Each project's own review interval drives per-project review in the Review perspective; one trimmed weekly routine (~8 items) and one monthly routine (horizons, finances, tags) cover what the perspective can't (inbox zero, calendar, horizons, finances, rituals). Intervals by kind: active work weekly; personal/admin monthly; on-hold and Someday quarterly; templates and annual reviews yearly. **Stagger next-review dates** so reviews arrive a few a day, not 30 at once; clear the 84 overdue in batches (~10 per sitting), never one bulk Mark Reviewed. Findings: intervals were mostly defaults (54 projects last reviewed in one February batch); the second "Monthly Review" and "Update Weekly Plan" were self-described misfits. Changes 1–5 approved (trim Weekly Review, drop the stray Monthly Review, move Update Weekly Plan out of Begin the day, fold finances into Monthly Review); change 6 (intervals for 84 projects, staggered) needed `ofo project update --review-every / --next-review`, added in 2.21.0.

Original question: repeating review projects (Weekly Review, Monthly Review of Finances, Update Weekly Plan, the two Monthly Review tasks) vs each project's own review interval surfacing it in the Review perspective. Try both on a handful of real projects in a triage session; recommend one pattern; record it in the brainstorm and apply it. Output decides task 4's entry point and what happens to those routines.

### 2. Re-evaluate the 14 Attache actions (absorbs #268) — done 2026-11-17
**Decided** (table on #268): Clarify Tasks → Review Assist; Weekly Review rebuilt on the Review perspective + push; Daily Review → Wrap up day; Wins Report merged into it; Stale Routine Recovery → Routine Audit; drop Project Health and Map System; keep Process Inbox (+ capture splitting), What Now, Health Check, Quick Organize, Setup, Monthly/Horizons; drop third-party Open Today's Forecast, later Completed Task Report and Help Me Estimate. **New requirement: kept actions usable as OmniFocus toolbar buttons** (icon + short label per action; verify how OmniFocus 4.10 exposes plug-in actions in the toolbar).

Original scope:
Per action: what it does (run it), FM use and 8K fit, overlap (CLI, slash commands, third-party plug-ins), keep / merge / drop. Drop rule: an action that only reproduces one click in OmniFocus's UI goes. User decides keep/merge/drop; orchestrator does the code-side analysis first. Fix the known `AGENTS.md` inventory errors in the same pass.

### 3. Design the vault handoff (architect, with orchestrator) — done 2026-11-17
Design: vault `800 Generated/820 Brainstorms/attache-vault-handoff-design.md` (Contract section = what the plug-in implements). **Decided:** one `obsidian://quickadd?…&choice=Attache Push&value-payload={json}` link running a QuickAdd macro; the plug-in sends a kind (`wrap-up-day`, `weekly-review`, `project-status`, `inbox`) + data and knows no vault paths; idempotent marker sections; missing weekly/daily notes created from their templates (yes); project status goes to the weekly note's Stalled Projects only; click-to-log is a "Wrap up day" action. Routines are identified by **OmniFocus task id**, with the current name stored beside it for display, so renames don't split the history (decided 2026-11-17). Structural vault changes (QuickAdd choice + script, `Routines.base`, template edits, properties) need approval before task 5; verify QuickAdd `value-*` handling first.

Original scope:
- `obsidian://` mechanics: which action (`new` with append, or a plugin-provided URI), how to target a heading, how properties get written; behaviour when Obsidian is closed.
- Note targets: weekly (`500 ♽ Cycles/530 🗓 Weeks/YYYY-Www.md`, created from its template if missing — none exist after W28), daily, project status destination (project notes vs monthly/quarterly).
- Routine tracking schema: daily-note properties for routine completions; a Bases view that charts a week; how the weekly review reads it.
- Click-to-log path given *no completion events* (see Constraints).
- The OmniFocus inbox input: who updates `last_processed` / `open_count`; fix its dangling `triggers: [[OmniFocus Quick Capture]]`.
- Configuration in the plug-in: vault, path patterns, headings — not hard-coded vault structure.
Output: a design note (architect zone) + the exact URI/payload contract the plug-in implements.

### 4. Build: review assist inside OmniFocus (orchestrator)
- **Entry point (task 1):** open the next project due in the Review perspective; model summary (stalled? next action? duplicates?); offer Mark Reviewed, change interval, on hold, drop. Also runs at the end of the weekly routine.
- **Toolbar buttons** for the kept actions (task 2).
- **Weekly review is done when the project is marked complete, not when every box is ticked.** Evidence (2026-11-17): of 19 completed weekly copies (Jan–Jul 2026), most were marked done with nearly every checklist item unticked; the one copy with every item ticked was never closed. Completing the routine should be one action, and the items left unticked go to the weekly note's Review Friction section instead of being lost.
- **Review Assist** on the project being reviewed: one model pass over that project's tasks → vague names, missing estimates/tags, likely-done, stale, routine problems; auto-apply the safe set with an undo log; ask about the rest in one form; Mark Reviewed.
- **Duplicate finder:** deterministic candidate pairs across all projects (normalized names, shared words), model judges only candidates.
- **Routine audit:** repeaters missed N cycles, routines per area over a cap, due-dated habits → defer-only, frequency sanity; offer stop / reduce / convert.
- **Learning log:** accepted / rejected / edited suggestions by type in `preferencesManager`; feeds prompts and the weekly *Review Friction*.
- **Capture hygiene:** split pasted first line → name, rest → note.
- Batches sized for 8K (`hierarchicalBatcher.ts` still assumes ~5K); measure prompts with `fm count-tokens -q`.

### 5. Build: vault push (orchestrator, per task 3's contract)
Weekly review summary → weekly note; daily wrap-up (completions + routine properties) → daily note; project status; inbox input fields. Vault picker + remembered vault.

### 6. Skills, agent, docs
- `omnifocus-core`, `gtd-coach`, `omnifocus-generator` references and `agents/attache.md` routing: when to send the user to a menu action vs `ofo`; triage-session procedure (the brief that worked in session 1).
- `plugins/attache/README.md`: user-facing menu guide; `AGENTS.md`: corrected inventory.
- Vault (curator): [[OmniFocus]], [[How I Use OmniFocus]], [[Attache]], workflow notes such as [[Push OmniFocus Completions to Daily Note]] (Idea → Operational when shipped).
- Skillsmith eval per changed skill; agentsmith eval for `attache.md`.

### 7. Verify
- Plug-in and CLI rebuilt and installed together; version check passes.
- A full weekly review done in OmniFocus with Review Assist: timed, `reviewOverdue` before/after, weekly note filled.
- A week of routine completions charted from daily notes.
- More triage sessions (duplicates sweep; one area in depth) using the new tools; friction logged.

## Order and parallelism

0 → (1 ∥ 2 ∥ 3) → 4 → 5 → 6 → 7. Task 0 is small and unblocks triage. Tasks 1–3 run in parallel with different seats. 4 waits on 1 (entry point) and the 8K measurements; 5 waits on 3's contract. Docs (6) follow each shipped piece rather than waiting for the end.

## Evidence

Triage session 1 (2026-11-17, attache on Sonnet, overdue + inbox): 12 safe changes applied and verified (9 renames from each task's own note, 11 estimates, 1 URL moved name → note); 24 decisions put to the user; overdue 17 → 4, inbox 3 → 2; health routines converted to defer-only; two chores dropped. Twelve requirements recorded in the brainstorm. Before: 877 active tasks, 85 projects, 84 overdue for review.
