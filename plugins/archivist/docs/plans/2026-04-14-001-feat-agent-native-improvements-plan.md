---
title: "feat: Agent-native architecture improvements from audit #160"
type: feat
status: active
date: 2026-04-14
---

# feat: Agent-native architecture improvements from audit #160

## Overview

The archivist plugin scored 71% on an agent-native architecture audit (2026-04-13). This plan implements the improvements identified, organized by effort tier. Low-effort wins (documentation, init enrichment, new commands) are sequenced first; medium-effort structural changes (script primitive refactor, threshold externalization, CRUD gaps, multi-vault) follow. Longer-term items are explicitly deferred.

## Problem Frame

Eight agent-native principles were audited. Four are passing or near-passing (Action Parity 100%, Capability Discovery 93%, Shared Workspace 87.5%, Tools as Primitives 75%). Four need attention:
- **Prompt-Native Features (40%)**: Policy and thresholds are buried in script docstrings and hardcoded constants — invisible to the agent and to users
- **CRUD Completeness (58%)**: No delete path exists for templates, Bases files, or canvas files
- **Context Injection (54.5%)**: Initialization is cold — orphan count, schema drift signals, and collection health are not surfaced until the user asks
- **UI Integration (62.5%)**: Python write operations complete without triggering Obsidian's index refresh, causing 1–5s backlink latency after writes

## Requirements Trace

**Prompt-Native (R1, R2, R8)**
- R1. Policy thresholds (similarity, coverage, node cap) visible in `references/` markdown
- R2. Code-native feature criteria (collection health, vault analysis categories, frontmatter schema) documented in `references/`
- R8. All hardcoded thresholds exposed as CLI args with documented defaults

**UI Integration (R3)**
- R3. Obsidian index refresh triggered after any Python write operation or agent file write

**Context Injection (R4)**
- R4. Init surfaces orphan count + schema drift pre-flight + unhealthy collections before first user prompt

**Action Parity + Capability Discovery (R5, R6)**
- R5. `/workflows` command exposes Known Workflows and Workflow Candidates tables
- R6. `/commands/help.md` is the missing discovery mechanism

**Tools as Primitives (R7)**
- R7. `generate_canvas.py`, `merge_notes.py`, `redirect_links.py` return JSON, never write files; agent controls write decision

**CRUD Completeness (R9)**
- R9. Delete workflows exist for templates, Bases files, and canvas files

**Shared Workspace (R10)**
- R10. `.local.md` supports named vault profiles for multi-vault users

## Scope Boundaries

- No new external Python dependencies
- Permission model remains advisory (skill instructions, not filesystem ACLs)
- Vault file format unchanged (markdown + YAML frontmatter)
- No changes to `vault-architect` scripts (`analyze_vault.py`, `validate_frontmatter.py`) — these already return JSON and do not write vault files

### Deferred to Separate Tasks

- **Git-based vault momentum metrics** (`_vault-profile.md` activity signals): separate issue, requires git CLI integration
- **Move behavioral policies from script docstrings to `references/`**: lower priority once thresholds are externalized via CLI args
- **Canvas/Bases file update-and-refresh workflows**: separate task after primitives refactor lands
- **Property schema creation** (currently only updates existing properties): scope/design needs its own issue
- **#113 canvas layout gaps** (frontmatter grouping, edge labels, color mapping): addressed in Unit 6 for the layout portion; full #113 closure deferred pending canvas primitives

## Context & Research

### Relevant Code and Patterns

- `plugins/archivist/agents/archivist.md` — Initialization, workflow orchestration, bounded autonomy, scripts table
- `plugins/archivist/skills/vault-curator/scripts/generate_canvas.py` — Writes `.canvas` file directly; has `--dry-run` mode that returns JSON but skips write; hardcoded `NODE_WIDTH=300`, `max_nodes=50`
- `plugins/archivist/skills/vault-curator/scripts/merge_notes.py` — Writes merged target note directly; `--dry-run` returns JSON diff
- `plugins/archivist/skills/vault-curator/scripts/redirect_links.py` — Edits all matching vault files directly; `--dry-run` returns affected-file list
- `plugins/archivist/skills/vault-curator/scripts/find_similar_notes.py` — Already accepts `--min-similarity` as CLI arg (good pattern to follow)
- `plugins/archivist/skills/vault-curator/scripts/check_collection_health.py` — Returns JSON; `BASES_DIR = "900 📐Templates/970 Bases"` hardcoded; coverage threshold hardcoded in detection logic
- `plugins/archivist/commands/` — Six commands exist: canvas, collection, drift, duplicates, health, vault. `help.md` and `workflows.md` are missing.
- `plugins/archivist/.local.md.example` — Single-vault format; no named-profile support yet

### Institutional Learnings

- The `--dry-run` pattern already in all three target scripts is the right primitives entry point: extend it so normal (non-dry-run) mode also returns JSON without writing — writing becomes the caller's responsibility
- `find_similar_notes.py` already exposes `--min-similarity` — use it as the template for how to add CLI args to other scripts
- The existing `Bounded Autonomy` zone model in `archivist.md` already handles "agent controls writes" — the primitives refactor closes the gap where scripts bypass this by writing directly

### External References

- [Obsidian JSON Canvas spec](https://jsoncanvas.org/) — Node types, edge schema, group node semantics (relevant to Unit 6)
- Issue #113 — canvas generation gaps (frontmatter grouping, layout, color mapping) — partially addressed in Unit 6

## Key Technical Decisions

- **Primitives via flag, not architecture change**: Add `--no-write` flag to `generate_canvas.py`, `merge_notes.py`, `redirect_links.py`. When set, return JSON and skip all file I/O. This is backward-compatible and testable. The agent's workflows change from calling scripts that write to calling scripts with `--no-write`, receiving JSON, then using the Write/Edit tool.
- **`merge_notes.py --no-write`**: Returns proposed target note content as a JSON field alongside the existing `frontmatter_changes` structure. Agent writes the target file with Write/Edit tool.
- **`redirect_links.py --no-write`**: Returns `{affected_files: [{path, content_after}]}`. Agent applies edits. For large vaults (many affected files) this could be heavy — cap at 50 affected files and warn; bulk cases fall back to script-controlled writes with explicit user approval.
- **Index refresh step**: `bash obsidian vault` is a read-only command that verifies connection. The actual trigger is `bash obsidian` CLI operations. After any Write/Edit tool write to the vault, add a follow-up `bash obsidian search query="<written-note-title>"` to force Obsidian to index the change (or simply document that users may need to wait 1–5s for backlinks).
- **Multi-vault `.local.md`**: Use a named-profile YAML structure (`vaults:` map) while keeping the legacy flat `vault_path:` key readable. Init selects by matching against `$PWD` or the first defined vault if unambiguous.
- **Delete workflows**: No new Python scripts needed. Deletes are handled by the agent using `bash rm` (for files in `designated_output_zones`) or `bash obsidian` delete commands, always preceded by a link-redirect dry-run to surface downstream impact.

## Open Questions

### Resolved During Planning

- **Should `redirect_links.py --no-write` return full file content?** Yes for correctness, but cap at 50 files to avoid memory issues. Beyond cap, fall back to script-controlled writes with user approval.
- **Does `obsidian vault` trigger indexing?** No — it's a read-only health check. Real index trigger is any write via `obsidian create`/`obsidian append`. After agent Write tool calls, index refresh requires a follow-up `obsidian` command or explicit wait instruction.
- **#113 scope in this plan?** Partially: Unit 6 addresses layout improvements (node grouping by fileClass, edge direction labels). Full #113 closure (Chronos integration, edge type vocabulary) is deferred.

### Deferred to Implementation

- Exact YAML structure for multi-vault `.local.md`: implement the simplest viable format that doesn't break single-vault users; refine based on real usage
- Whether `redirect_links.py --no-write` should embed full file content or just diff hunks: start with full content, optimize if context window pressure appears

## Output Structure

```
plugins/archivist/
├── agents/
│   └── archivist.md                      (modified — init enrichment, workflow refresh hints, delete workflows)
├── commands/
│   ├── help.md                           (new — capability discovery)
│   └── workflows.md                      (new — /workflows action parity)
├── skills/
│   ├── vault-architect/
│   │   └── references/
│   │       ├── vault-analysis-checks.md         (new — documents analyze_vault.py checks)
│   │       └── frontmatter-schema-reference.md  (new — documents validate_frontmatter.py fields)
│   └── vault-curator/
│       ├── references/
│       │   └── collection-health-criteria.md    (new — documents check_collection_health.py criteria)
│       └── scripts/
│           ├── generate_canvas.py        (modified — --no-write flag, --node-width, --node-height, fileClass grouping)
│           ├── merge_notes.py            (modified — --no-write flag)
│           ├── redirect_links.py         (modified — --no-write flag, 50-file cap)
│           └── check_collection_health.py (modified — --coverage-threshold flag)
└── .local.md.example                     (modified — named-vault profile format)
```

## Implementation Units

- [ ] **Unit 1: Prompt-Native Reference Files**

**Goal:** Move code-native policy knowledge out of script docstrings and into loadable markdown references so the agent can cite them and users can understand the rules.

**Requirements:** R1, R2

**Dependencies:** None

**Files:**
- Create: `plugins/archivist/skills/vault-curator/references/collection-health-criteria.md`
- Create: `plugins/archivist/skills/vault-architect/references/vault-analysis-checks.md`
- Create: `plugins/archivist/skills/vault-architect/references/frontmatter-schema-reference.md`

**Approach:**
- `collection-health-criteria.md` (vault-curator): document what makes a collection "healthy" vs "partial" vs "missing_infrastructure"; explain the 60% fileClass coverage threshold; define the 5 required parts (folder, folder note, Bases embed, Bases file, template); explain detection heuristic (folder note OR ≥5 notes with ≥60% fileClass coverage)
- `vault-analysis-checks.md` (vault-architect): document each check `analyze_vault.py` runs (orphan detection, untagged notes, inconsistent frontmatter, duplicate titles, missing temporal links); define what "orphan" means (no incoming wikilinks); describe output field meanings
- `frontmatter-schema-reference.md` (vault-architect): document the fields `validate_frontmatter.py` checks; severity levels; common violations and remediation
- Add `Load when:` annotations at the top of each file so the agent knows when to pull them in

**Test scenarios:**
- Test expectation: none — pure documentation files, no executable behavior change

**Verification:**
- All three files exist and are non-empty
- Each file's `Load when:` annotation matches the triggering workflow in `archivist.md`
- `check_collection_health.py` docstring's field descriptions match `collection-health-criteria.md`

---

- [ ] **Unit 2: Context Injection — Enriched Initialization**

**Goal:** Surface actionable vault signals (orphan count, schema drift indicators, unhealthy collections) at session start before the user asks, so the agent can lead with the highest-priority issue.

**Requirements:** R4

**Dependencies:** None (pure `archivist.md` change; Units 1 references loaded when needed)

**Files:**
- Modify: `plugins/archivist/agents/archivist.md` — Initialization section (step 4 or new step 5)

**Approach:**
- After the existing 4 init steps, add a "Quick Vault Signals" pass:
  - Run `obsidian orphans | wc -l` to get orphan count
  - Run `check_collection_health.py --dry-run` to get candidate folder list; then run `check_collection_health.py` (no `--dry-run`) scoped to each candidate folder to get actual health status; flag any folder returning `health: partial` or `health: missing_infrastructure`
  - Do NOT run full `analyze_vault.py` at init — too slow; reserve for `/health` command
- Store results in session state and use them to prime the opening prompt:
  - If orphan count > 20: surface as issue #1
  - If unhealthy collections found: surface as issue #2
  - If no issues: open with "Vault looks healthy — what would you like to work on?"
- Add a note that `references/collection-health-criteria.md` explains health thresholds

**Test scenarios:**
- Happy path: vault with no issues → agent reports "Vault looks healthy"
- Edge case: `obsidian orphans` unavailable (CLI not running) → agent falls back to skipping orphan count, continues without signal
- Edge case: vault with 0 collections → health check returns empty list, no error
- Integration: unhealthy collection detected at init → agent mentions it as a suggested workflow before user speaks

**Verification:**
- Init completes without requiring user input for vaults with `.local.md` configured
- Agent's opening message references specific signals (orphan count, unhealthy collection names) rather than generic greetings
- If CLI unavailable, init still completes (no hard failure)

---

- [ ] **Unit 3: UI Integration — Obsidian Index Refresh**

**Goal:** After any agent-controlled write to the vault, trigger Obsidian's indexer so backlinks and graph data are current within seconds rather than minutes.

**Requirements:** R3

**Dependencies:** Unit 6 (primitives refactor) — the write step moves from scripts to the agent; this unit updates `archivist.md` workflow steps that include agent Write/Edit calls. Can be applied before Unit 6 to script-write workflows and re-applied after Unit 6 to agent-write workflows.

**Files:**
- Modify: `plugins/archivist/agents/archivist.md` — Visualization: Canvas Map Generation workflow; Consolidation: Merge Notes workflow; Consolidation: Redirect Links workflow

**Approach:**
- After each step that writes a vault file (whether via script or agent Write tool), add: `bash obsidian search query="<written-note-title>" format=json limit=1` — intended to prompt Obsidian to recheck its index
- Document the refresh step with a comment: `# Trigger Obsidian index refresh — resolves backlink latency after write`
- **NOTE (implementation-time verification required):** Confirm whether `obsidian search` actually triggers a fresh index pass or reads the existing stale index. If it reads stale, replace with an explicit wait instruction: `# Obsidian may take 1–5s to index new files; backlinks will resolve shortly`
- If `obsidian` CLI is unavailable (Obsidian not running), the search fails silently — document that fallback: `# If CLI unavailable, backlinks may take up to 30s to appear`
- For canvas writes: use the canvas filename stem as the search query

**Test scenarios:**
- Happy path: after writing a note, search returns the note within 2s
- Edge case: Obsidian not running → search fails; agent continues without error
- Integration: after merge + redirect, backlinks from redirected notes resolve to new target within the same session

**Verification:**
- Every `archivist.md` workflow step that writes a file has a follow-up index refresh command
- No workflow step writes and then immediately reads backlinks without a refresh call between

---

- [ ] **Unit 4: Action Parity + Capability Discovery — Commands**

**Goal:** Add the two missing command files to close the capability discovery gap and expose the Known Workflows table as a slash command.

**Requirements:** R5, R6

**Dependencies:** None

**Files:**
- Create: `plugins/archivist/commands/help.md`
- Create: `plugins/archivist/commands/workflows.md`

**Approach:**
- `commands/help.md`: Invoke the archivist agent to list all available slash commands with a one-line description of each. Agent should: read its own `commands/` directory (Glob `${CLAUDE_PLUGIN_ROOT}/commands/*.md`), read each command's `description` frontmatter field, and present a formatted table. Include a note pointing to `skills/vault-*/SKILL.md` for deeper capability docs.
- `commands/workflows.md`: Invoke the archivist agent to: (1) read `_vault-profile.md` from the vault, (2) extract the `## Known Workflows` table and `## Workflow Candidates` table, (3) present both to the user. If `_vault-profile.md` is absent, surface that as the issue and offer to run vault profiling.
- Both commands follow the existing command file convention: `name` + `description` frontmatter, then prose instructions for the agent.

**Test scenarios:**
- Happy path: `/help` produces a table of all 8 commands (canvas, collection, drift, duplicates, health, vault, workflows, help)
- Happy path: `/workflows` loads `_vault-profile.md` and presents both tables
- Edge case: `/workflows` called before vault profiling (no `_vault-profile.md`) → agent explains and offers profiling
- Edge case: `_vault-profile.md` exists but has no workflow tables yet → agent reports empty tables, offers to run workflows to populate

**Verification:**
- `commands/help.md` and `commands/workflows.md` exist with valid frontmatter
- `help.md` produces output listing all 8 commands when invoked
- `workflows.md` reads from `_vault-profile.md` and presents both tables without running any Python scripts

---

- [ ] **Unit 5: Prompt-Native — Externalize Hardcoded Thresholds**

**Goal:** Move hardcoded numeric constants in Python scripts to CLI args with documented defaults, making them overridable without code changes.

**Requirements:** R1, R8

**Dependencies:** None (independent of Unit 7)

**Files:**
- Modify: `plugins/archivist/skills/vault-curator/scripts/generate_canvas.py` — add `--node-width`, `--node-height`; document existing `--max-nodes` in archivist.md table
- Modify: `plugins/archivist/skills/vault-curator/scripts/check_collection_health.py` — add `--coverage-threshold` (currently hardcoded via detection heuristic)
- Modify: `plugins/archivist/agents/archivist.md` — Scripts table: document new args; Collection Health Check workflow: note coverage threshold override

**Approach:**
- `generate_canvas.py`: `--max-nodes` already accepted; add `--node-width <px>` (default 300) and `--node-height <px>` (default 120). Constants `NODE_WIDTH`, `NODE_HEIGHT` become CLI args fed to layout and generation functions.
- `check_collection_health.py`: add `--coverage-threshold <pct>` (default 60). The detection condition `≥60% share a fileClass` reads this value from args.
- `find_similar_notes.py`: already has `--min-similarity` — no change needed, just document it in `collection-health-criteria.md` reference
- Do NOT expose `NODE_SPACING_X`, `NODE_SPACING_Y`, `GROUP_PADDING`, `GROUP_LABEL_HEIGHT` — these are layout internals, not user-facing policy thresholds
- Update `archivist.md` Scripts table to include the new args

**Test scenarios:**
- Happy path: `generate_canvas.py --node-width 400` produces nodes with width=400 in output JSON
- Happy path: `check_collection_health.py --coverage-threshold 80` flags collections that would be "healthy" at 60% but not at 80%
- Edge case: `--coverage-threshold 0` → all folders qualify; script should not error, but output will be large
- Edge case: `--node-width 0` → invalid; script should return JSON error `{"status": "error", "error": "node-width must be > 0"}`

**Verification:**
- `generate_canvas.py --help` (or running without args) documents `--node-width` and `--node-height`
- `check_collection_health.py --coverage-threshold 80` returns different results than at 60% for a vault with partially-covered collections
- All new args have default values matching the previous hardcoded constants (no behavior change when args omitted)

---

- [ ] **Unit 6a: Tools as Primitives — Script Primitive Refactor**

**Goal:** Refactor `generate_canvas.py`, `merge_notes.py`, and `redirect_links.py` so they never write files — they compute and return structured JSON. The agent controls the write decision.

**Requirements:** R7

**Dependencies:** Unit 5 (threshold args in place before this refactor to avoid two passes on the same scripts)

**Files:**
- Modify: `plugins/archivist/skills/vault-curator/scripts/generate_canvas.py` — add `--no-write` flag
- Modify: `plugins/archivist/skills/vault-curator/scripts/merge_notes.py` — add `--no-write` flag; return proposed target content in JSON
- Modify: `plugins/archivist/skills/vault-curator/scripts/redirect_links.py` — add `--no-write` flag; return `{affected_files: [{path, content_after}]}` capped at 50 files
- Modify: `plugins/archivist/agents/archivist.md` — update Canvas Map Generation, Merge Notes, and Redirect Links workflows to use `--no-write`, receive JSON, then use Write/Edit tool

**Approach:**

*generate_canvas.py `--no-write`:*
- Current non-dry-run: computes canvas data → writes `.canvas` file → prints result JSON
- With `--no-write`: computes canvas data → prints full result JSON under a `canvas_data` key → does not write
- Result shape: `{"status": "success", "canvas_path": "...(suggested)", "canvas_data": {...nodes, edges...}, "nodes": N, "edges": M, "clusters": [...], "total_notes_scanned": K}`
- Agent receives this, reviews `canvas_data`, then uses Write tool to write `<scope>/<output_name>.canvas` with `json.dumps(canvas_data)`

*merge_notes.py `--no-write`:*
- Current non-dry-run: computes merged frontmatter + appended content → writes target file → prints result JSON
- With `--no-write`: computes merged result → returns `{"status": "success", ..., "target_content": "<full merged markdown string>"}` → does not write
- Conflict resolution workflow: (1) call `--dry-run` to get conflict list; (2) present conflicts to user; (3) call `--no-write` to get `target_content`; (4) agent applies user resolutions to `target_content` string; (5) agent writes resolved content with Write tool
- Dry-run remains unchanged (still used for initial conflict preview)

*redirect_links.py `--no-write`:*
- Current non-dry-run: scans all vault files → applies regex replacements in place → prints summary
- With `--no-write`: scans and computes replacements → returns `{"affected_files": [{"path": "...", "content_after": "..."}], "total_replacements": N}` capped at 50 files; if >50 affected files, returns `{"status": "too_many", "affected_count": N, "message": "Too many files to return inline. Use script-controlled mode (omit --no-write) with explicit approval."}` → does not write
- Agent iterates `affected_files`, applies each with Edit tool; for the >50 cap case, agent obtains explicit user confirmation then calls script without `--no-write`

*archivist.md workflow updates:*
- Canvas: call with `--no-write`, receive JSON, write canvas file with Write tool, run index refresh
- Merge: call dry-run for conflict preview, resolve conflicts agent-side, call with `--no-write`, write target with Write tool, run index refresh
- Redirect: call with `--no-write`, apply edits with Edit tool per file (or fall back for large sets), run index refresh

**Patterns to follow:**
- `--dry-run` in all three scripts (existing pattern) — `--no-write` follows the same flag convention
- `find_similar_notes.py` dry-run behavior — always returns JSON, never writes

**Test scenarios:**
- Happy path: `generate_canvas.py --no-write --scope "700 Notes"` returns JSON with `canvas_data` key and no file written
- Happy path: `merge_notes.py --no-write --source A.md --target B.md` returns `target_content` string with merged frontmatter + content
- Happy path: `redirect_links.py --no-write --old A --new B` returns `affected_files` list with `content_after` for each
- Edge case: redirect with >50 affected files → returns `status: too_many` with count; agent falls back to script-controlled mode
- Edge case: `generate_canvas.py --no-write` on empty scope → returns `total_notes: 0` with empty canvas_data
- Integration: full canvas workflow (agent calls `--no-write`, receives JSON, writes `.canvas` file with Write tool, runs index refresh) produces a valid readable canvas in Obsidian
- Integration: full merge workflow (dry-run → conflict resolution → `--no-write` → agent reconstructs resolved content → Write tool) produces correct merged note
- Error path: script error (e.g., vault path invalid) → returns `{"status": "error", "error": "..."}` same as before

**Verification:**
- All three scripts with `--no-write` produce zero file writes during execution
- `archivist.md` workflows no longer have steps that say "Execute (remove --dry-run)" — instead they say "Apply JSON result with Write/Edit tool"
- Canvas files written by the agent via Write tool are valid JSON Canvas spec format and open in Obsidian without error

---

- [ ] **Unit 6b: Canvas Quality — FileClass Grouping + Edge Labels**

**Goal:** Improve canvas layout quality by grouping nodes by `file_class` into named group nodes (beyond folder clustering) and making link direction visible via edge labels.

**Requirements:** partial R1 (canvas layout policy now documentable); partial closure of #113

**Dependencies:** Unit 6a (`generate_canvas.py` is already being modified; do this in the same or immediately following pass to avoid a third touch)

**Files:**
- Modify: `plugins/archivist/skills/vault-curator/scripts/generate_canvas.py` — add fileClass group node layout; add edge direction markers; expand `fileclass_color()` mapping

**Approach:**
- After clustering by folder, group notes by `file_class` into named group nodes (JSON Canvas `type: "group"` nodes). Group nodes are labeled with the fileClass name and contain all member node IDs.
- Add `"fromEnd": "arrow"` (or `"label": "→"`) on edges to make link direction visible in Obsidian's canvas view
- Expand `fileclass_color()` mapping with additional entries: `workflow`, `capture`, `template` (map to appropriate preset colors from the existing scheme)
- Document the grouping strategy in `vault-curator/references/collection-health-criteria.md` (or a new canvas layout reference if it grows large enough)

**Patterns to follow:**
- Existing `fileclass_color()` function and color preset scheme in `generate_canvas.py`
- JSON Canvas spec group node schema at jsoncanvas.org

**Test scenarios:**
- Happy path: canvas with mixed fileClasses produces group nodes labeled by fileClass
- Happy path: edges have direction markers visible in Obsidian canvas view
- Edge case: notes with no `file_class` frontmatter → placed in an "Uncategorized" group or left ungrouped (implementer decision)
- Edge case: single-member fileClass group → still rendered as a group node (consistent presentation)
- Regression: existing canvas output fields (`clusters`, `total_notes_scanned`, `nodes`, `edges`) unchanged

**Verification:**
- `generate_canvas.py` output includes `type: "group"` nodes when fileClass data is present
- Edges include direction markers
- `fileclass_color()` handles `workflow`, `capture`, `template` without falling through to default

---

- [ ] **Unit 7: CRUD — Delete Workflows**

**Goal:** Add explicit delete workflows for vault infrastructure (templates, Bases files, canvas files) so users have a clean path to remove cruft without the agent refusing or improvising.

**Requirements:** R9

**Dependencies:** Unit 3 (UI integration — index refresh after delete)

**Files:**
- Modify: `plugins/archivist/agents/archivist.md` — add Delete Workflows section under Workflow Orchestration

**Approach:**
- Add three named workflows in `archivist.md`:
  - **Delete Template**: check for references to the template (Glob `*.md` for `[[TemplateName]]`); present impacted notes; confirm; delete using `bash rm "${VAULT_PATH}/<template-path>"`; run index refresh
  - **Delete Bases File**: check for `![[BaseName.base]]` embeds in folder notes; present impacted folder notes; confirm; delete `.base` file; offer to remove embed from folder notes (separate confirmation); run index refresh
  - **Delete Canvas**: canvas files have no dependents (they're outputs, not sources); confirm once; delete; run index refresh
- All deletes: require explicit confirmation, log the deletion in session notes, never delete without a dependency check first
- Use `bash rm` only for files in `designated_output_zones` (generated, no confirmation-extra needed); for structural zones (templates, bases), require a pre-delete impact check
- Add to `archivist.md` Bounded Autonomy table: Delete is always a structural-zone operation requiring confirmation regardless of zone

**Test scenarios:**
- Happy path: delete canvas file → no dependency check needed → single confirmation → file removed
- Happy path: delete template → agent finds 3 notes using it → presents them → user confirms → template deleted
- Error path: delete Bases file that is embedded in 10 folder notes → agent lists all 10, requires per-operation confirmation, does not proceed without it
- Edge case: template has no references → agent confirms "No notes reference this template" → proceeds after confirmation
- Edge case: file to delete does not exist → agent reports gracefully, no error crash

**Verification:**
- Delete workflows are listed in the `archivist.md` Workflow Orchestration section
- Each delete workflow includes: dependency check → impact presentation → confirmation → delete → index refresh
- No delete workflow omits the dependency check step

---

- [ ] **Unit 8: Shared Workspace — Multi-Vault `.local.md`**

**Goal:** Allow `.local.md` to store named vault profiles so users with multiple Obsidian vaults can switch contexts without manually editing the config file.

**Requirements:** R10

**Dependencies:** Unit 2 (init enrichment uses `.local.md`)

**Files:**
- Modify: `plugins/archivist/.local.md.example` — add named-vault YAML structure
- Modify: `plugins/archivist/agents/archivist.md` — Initialization step 2: add multi-vault detection and selection logic

**Approach:**
- `.local.md` new format (backward-compatible): keep flat `vault_path:` as a legacy fallback; add optional `vaults:` map where each key is a vault name and value includes `path:`, optional `architect_write_zones:`, `curator_write_zones:`, `designated_output_zones:`
- Init logic: if `vaults:` key present with 2+ entries, check `$PWD` against each vault's `path:`; if $PWD is inside a vault path, auto-select it. If ambiguous (PWD not inside any vault), present named choices via `AskUserQuestion`.
- If only one vault defined (or legacy `vault_path:` format), no selection needed — existing behavior unchanged
- Update `.local.md.example` with a commented-out `vaults:` block showing two named vaults alongside the legacy `vault_path:` format

**Patterns to follow:**
- Current `.local.md.example` for field naming conventions
- Current init step 2 in `archivist.md` for the read/parse/prompt flow

**Test scenarios:**
- Happy path: single `vault_path:` → auto-selected, no prompt (existing behavior preserved)
- Happy path: two vaults defined, $PWD inside vault A → vault A auto-selected
- Happy path: two vaults defined, $PWD not in either → AskUserQuestion presents vault names, user picks one
- Edge case: `vaults:` defined with one entry → auto-selected without prompt
- Edge case: vault path in `vaults:` uses `~` → expansion handled correctly
- Edge case: `.local.md` has both `vault_path:` (legacy) and `vaults:` → `vaults:` takes precedence, warn user about redundancy

**Verification:**
- `.local.md.example` shows both legacy and new format with clear comments explaining the difference
- Init step 2 in `archivist.md` documents multi-vault selection logic
- Single-vault users experience no change in init behavior

## System-Wide Impact

- **Interaction graph:** All three refactored scripts (`generate_canvas.py`, `merge_notes.py`, `redirect_links.py`) are called from `archivist.md` workflows — those workflow steps must be updated in the same commit as the `--no-write` flag addition to avoid a broken intermediate state
- **Error propagation:** Scripts returning `{"status": "error", ...}` — agent must handle these before calling Write tool (don't write if script errored)
- **State lifecycle risks:** `redirect_links.py` in `--no-write` mode returns `content_after` for up to 50 files. Agent must apply all edits or none (git checkpoint before link redirect remains in the workflow)
- **API surface parity:** The `--dry-run` flag behavior is unchanged; `--no-write` is additive. Existing callers using `--dry-run` continue to work.
- **Integration coverage:** Canvas write-then-read-backlinks scenario requires Unit 3 (index refresh) to be in place alongside Unit 6a (primitives) to avoid stale-backlink issues in the same session
- **Unchanged invariants:** `analyze_vault.py` and `validate_frontmatter.py` already return JSON and do not write files — they are not touched. The existing `--dry-run` behavior on all scripts is preserved unchanged.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| `redirect_links.py --no-write` returns large payloads for heavily-linked notes | 50-file cap with fallback to script-controlled mode; cap is explicit in the API contract |
| Init enrichment (Unit 2) adds latency to session start | Run `obsidian orphans \| wc -l` only (not full list); use `check_collection_health.py --dry-run` (candidate scan, not full health check); skip if CLI unavailable |
| Multi-vault `.local.md` change breaks existing single-vault setups | Legacy `vault_path:` key is preserved; new `vaults:` key is additive and optional |
| `--no-write` flag changes the caller contract for `generate_canvas.py` | `--dry-run` (preview only) and `--no-write` (full compute, no write) are clearly distinct; `archivist.md` workflows updated atomically with Unit 6a |
| Canvas quality improvements (fileClass grouping) change output format | JSON Canvas spec allows group nodes — grouping is additive; existing canvases are not modified; isolated in Unit 6b so it can be skipped without affecting primitives |
| Deleting a template that is referenced by an active Templater QuickAdd macro | Dependency check scans wikilinks but not plugin config JSON; document this limitation in the delete workflow |

## Documentation / Operational Notes

- `SKILL.md` for `vault-curator` should reference the new `references/collection-health-criteria.md` and `references/vault-analysis-checks.md` files in its Collection Health Check section
- Run `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` on both `SKILL.md` files and on `archivist.md` after each unit that modifies them; record scores in `README.md` version history
- The `archivist.md` agent file does not go through skillsmith evaluation (it's an agent, not a skill), but its version history entry in `README.md` should note which audit principles improved

## Sources & References

- **Related issue:** [#160](https://github.com/totallyGreg/claude-mp/issues/160) — agent-native architecture audit (source of all improvements)
- **Related issue:** [#113](https://github.com/totallyGreg/claude-mp/issues/113) — canvas generation gaps (partially addressed in Unit 6)
- **Existing archivist plan:** `plugins/archivist/docs/plans/2026-03-31-001-feat-archivist-permissions-vault-state-commands-plan.md` (completed — context for where we started)
- Related code: `plugins/archivist/agents/archivist.md` (init, workflows)
- Related code: `plugins/archivist/skills/vault-curator/scripts/generate_canvas.py` (primitives refactor target)
- Related code: `plugins/archivist/skills/vault-curator/scripts/find_similar_notes.py` (CLI arg pattern to follow)
- External: [JSON Canvas spec](https://jsoncanvas.org/) (canvas node/edge schema)
