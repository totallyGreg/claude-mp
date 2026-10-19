# Archivist

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration.

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration

**At a glance:** 2 skills · 2 agents · 9 commands · 2 hooks

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install archivist@totally-tools
```
<!-- END AUTOGEN:overview -->

## Usage

Ask Claude to help with Obsidian PKM tasks. Two agents split the work:

| Agent | Model | Role | Can edit files directly |
|---|---|---|---|
| `archivist` | Claude Haiku 5.5 | Curator: reads, organizes and evolves notes; the entry point for vault work | No — writes only through `vault-write` and the guarded `obsidian` CLI |
| `archivist-architect` | Claude Sonnet 5.5 | Architect: templates, Bases, schemas, collections, vault profiling | Yes, inside the write zones (enforced by a hook) |

The curator hands structural work to the architect as a nested subagent; `/vault architect <task>` goes to the architect directly. Each agent preloads only its own skill. Models were chosen from a measured cost spike (#175): Haiku 5.5 matched Sonnet 5.5 on curator tasks at about 1/15 of the cost.

### Visualization

- "Create a canvas showing me the entire release process for [project]"
- "Generate a knowledge map of everything connected to [topic]"
- "Show me how my project notes link to each other as a canvas"

### Metadata & Schema

- "What properties should this meeting note have?"
- "Find all notes in my Projects folder with inconsistent frontmatter"
- "Detect schema drift across my Customer fileClass"
- "Suggest missing properties for this note based on similar notes"

### Consolidation & Discovery

- "Find duplicate notes in my [folder]"
- "What notes are most related to this one?"
- "Merge these two notes about [topic] and update all links"
- "Find orphaned notes that aren't linked to anything"

### Vault Structure

- "Analyze my vault and suggest improvements"
- "Create a customer meeting note template"
- "Help me set up a temporal rollup system"
- "Set up a collection folder for [repeating note type]"
- "Run a health check on my vault"

## Configuration

The archivist creates `~/.config/archivist/local.md` on first run (or copy `local.md.example` there). It holds write **policy** only: `vault_path` and the three write-zone keys. It lives outside the plugin cache, so updates keep it, and outside the vault, so no vault write can widen its own zones. `$ARCHIVIST_LOCAL_MD` overrides the location. **2.0 no longer reads a `.local.md` inside the plugin cache.** If that's the only config it finds, `vault-write config` refuses and prints the `mv` command that moves it to `~/.config/archivist/local.md`.

```markdown
vault_path: /Users/username/Documents/MyVault
curator_write_zones: 700 Notes, 600 Projects
```

What the vault *is* — folders, plugins, fileClasses, conventions, trust levels — goes in `_vault-profile.md` inside the vault, where it travels with the vault and is shared by every machine. Facts Obsidian already stores, like the daily-notes folder and filename format, are read from the vault's plugin settings each time (`vault-write config`), never copied into either file.

## vault-write (guarded writes, any harness)

`bin/vault-write` is on the Bash tool's `PATH` while the plugin is enabled. It enforces the write rules in code, so they hold for the archivist, the main session, Pi, or any other harness:

```bash
vault-write config                                                 # config in use, zones that don't exist (with did_you_mean), daily-notes folder
vault-write stat  "600 Projects/x/note.md"                         # hash, stable hash, lines, in_zone
vault-write apply "600 Projects/x/note.md" --from new.md --base <hash> [--section "## Heading"]
vault-write check new.md                                           # lint only
vault-write force …                                                # may skip base/zone checks: ask the user first
```

`apply` refuses writes outside the configured zones and writes over a note that changed since `--base` (the *stable* hash ignores trailing whitespace and `date modified`). It blocks unclosed code fences and inline code that starts with an equals sign (Dataview executes it), warns on unresolved wikilinks, commits a git snapshot of the note first, then writes atomically and verifies. It never deletes or moves notes. Output is one line of JSON; exit codes 0 ok, 2 refused, 3 lint.

**Guard hooks.** `hooks/obsidian_guard.py` (PreToolUse on Bash) parses every command, quotes and option order included, and returns a decision:
- **deny** `obsidian delete`, `eval`, `dev:cdp` and `create … overwrite`.
- **deny** CLI writes (`create`, `append`, `prepend`, `property:set`, `property:remove`, task updates, `daily:append`/`daily:prepend`) unless they start with `vault=<configured vault>` before the subcommand. Without it, the CLI writes to the working directory's vault or the focused one, and it silently ignores a `vault=` after the subcommand.
- **deny** those writes (except the daily ones) without an explicit `path=` inside the write zones. Without `path=`, the CLI writes to whatever note is open.
- **ask** for `move`, `rename`, `command`, `template:insert`, `base:create`, `history:restore`, `sync:restore`, plugin/theme installs, and `rm`/`mv` on paths inside the vault.

`hooks/vault_file_guard.py` (PreToolUse on Write/Edit/NotebookEdit) covers direct file edits inside the vault:
- `archivist-architect` may edit inside the write zones; outside them it's denied.
- Any other caller (the main conversation, other agents) is asked to confirm, since vault notes normally go through the curator and `vault-write`.

Wrappers (`timeout`, `env`, `nice`, `xargs`, `sudo`, …) and `bash -c` / `eval` are unwrapped first. Permission rules can't do this reliably: a `*` in the middle of a rule matches a single space-free token, so `Bash(obsidian create * overwrite *)` misses `create path=x content="y" overwrite`, and `obsidian vault=X delete` slips past `Bash(obsidian delete:*)`.

Suggested permission rules (`~/.claude/settings.json`), as a second layer:

```json
{
  "permissions": {
    "allow": ["Bash(vault-write config:*)", "Bash(vault-write stat:*)", "Bash(vault-write check:*)", "Bash(vault-write apply:*)",
              "Bash(obsidian:*)"],
    "ask":   ["Bash(vault-write force:*)"],
    "deny":  ["Bash(obsidian delete:*)", "Bash(obsidian create * overwrite *)"]
  }
}
```

`Bash(obsidian:*)` is broad on purpose. Every CLI call starts with `obsidian vault="…"`, so narrower rules like `Bash(obsidian read:*)` no longer match, and the guard hook enforces the write rules in code. If Claude Code denies a `vault-write` or `obsidian` call, the agents print this block and stop; they never edit settings themselves.

**Other harnesses (Pi, scripts):** they don't get the plugin's `PATH`. Install a shim that always runs the newest installed version:

```bash
cat > ~/bin/vault-write <<'SH'
#!/bin/sh
d=$(ls -d "$HOME"/.claude/plugins/cache/*/archivist/*/bin 2>/dev/null | sort -V | tail -1)
[ -x "$d/vault-write" ] || { echo '{"ok": false, "error": "io", "detail": "archivist plugin not installed"}'; exit 1; }
exec "$d/vault-write" "$@"
SH
chmod +x ~/bin/vault-write
```

claude.ai and Cowork don't install plugins with a `bin/` directory; there the archivist falls back to its previous write path.

## Skill Documentation

See `skills/vault-architect/SKILL.md` for creating new structures and `skills/vault-curator/SKILL.md` for evolving existing content.

Progressive disclosure:
- `SKILL.md` - Core capabilities and workflows
- `references/` - Detailed guides (Templater patterns, Bases queries, etc.)
- `scripts/` - Python analysis tools
- `assets/` - Template examples

## Version

2.0.0

## License

MIT

## Agent: archivist

### Current Metrics

**Score: 87/100** (Good) — 2026-10-18

| Trigger | Prompt | Coherence |
|---------|--------|-----------|
| 93 | 90 | 79 |

### Agent-Native Audit — 2026-04-14

Overall score: **71%** ([#160](https://github.com/totallyGreg/claude-mp/issues/160))

| Principle | Score | % | Status |
|-----------|-------|---|--------|
| Shared Workspace | 7.5/8 | 94% | ✅ |
| Capability Discovery | 6.5/7 | 93% | ✅ |
| Prompt-Native Features | 28/32 | 88% | ✅ |
| Tools as Primitives | 8/10 | 80% | ✅ |
| Context Injection | 5/7 | 71% | ⚠️ |
| CRUD Completeness | 4/7 | 57% | ⚠️ |
| Action Parity | 12/24 | 50% | ⚠️ |
| UI Integration | 6/17 | 35% | ❌ |

### Version History

| Version | Date | Issue | Summary |
|---------|------|-------|---------|
| 2.0.0 | 2026-10-18 | [#175](https://github.com/totallyGreg/claude-mp/issues/175), [#224](https://github.com/totallyGreg/claude-mp/issues/224) | **Split into two agents** (decided from a measured cost spike on #175). `archivist` is now the curator: `claude-haiku-5-5`, no Edit/Write (writes only via `vault-write` and the guarded CLI), preloads vault-curator, hands structural work to the new `archivist-architect`. Lazy init: config + vault identity always; profile and Quick Vault Signals only when needed. Every CLI call passes `vault=` (#224). Prompt 531 → 246 lines; copies of skill workflows replaced by a routing table. Agent eval 93 → 87: Coherence drops on example/body wording alignment (the old prompt repeated the skill text); Trigger 93, Prompt 90. **Removed:** the pre-2.0 `.local.md` fallback in the plugin cache. `vault-write config` refuses and prints the `mv` to `~/.config/archivist/local.md` if that's the only config it finds; `.local.md.example` is now `local.md.example`. **Fixed:** Quick Vault Signals ran the drift and collection scripts with `--dry-run`, which scans nothing, so the drift signal never produced a count. They now run the full collection check and `detect_schema_drift.py --summary` (new; 537 bytes vs 65 KB). Deferred: #226 (local Pi reader tier), #227 (index queries). | **Also:** `vault-write` finds today's daily note by weighing every daily-note plugin (Periodic Notes, Journals, core) against where recent notes actually are, and reports `daily_notes.today` (it was a stale `…/2025` folder). `merge_notes.py`, `redirect_links.py` and `generate_canvas.py` write through `vault-write` (shared `write_note()`), not directly. `vault=` placement measured: it must come before the subcommand (after it, it's silently ignored), and the guard enforces that.
| 1.30.0 | 2026-10-18 | [#222](https://github.com/totallyGreg/claude-mp/issues/222) | Guard hook hardened: wrappers (`timeout`, `env`, `xargs`, `sudo`, …) and `bash -c`/`eval` are unwrapped, so `timeout 5 obsidian delete` no longer slips through. `eval`/`dev:cdp` denied. `rename`, `command`, `template:insert`, history/sync restores and plugin/theme installs ask. CLI writes (`create`, `append`, `prepend`, `property:set`, `property:remove`, task updates) need an explicit `path=` inside the write zones (verified on Obsidian 1.14.4: a missing or mistyped target edits the open note). `_vault-profile.md` is written per section via `vault-write apply` (the old `create … overwrite` step was already denied). drift/canvas/collection/duplicates take arguments (`argument-hint`). Agent eval 93 (no change). |
| 1.29.0 | 2026-10-16 | [#215](https://github.com/totallyGreg/claude-mp/issues/215), [#217](https://github.com/totallyGreg/claude-mp/issues/217), [#218](https://github.com/totallyGreg/claude-mp/issues/218) | Config moves to `~/.config/archivist/local.md` (survives plugin updates; legacy `.local.md` still read and flagged). `vault-write config` reports zones that don't exist with a `did_you_mean`, and the daily-notes folder and format read from the vault's plugin settings; profiling copies folder names exactly; `/session-log` resolves today's note by name. Write safety moves from prompt text into code: new `bin/vault-write` (zones, compare-and-swap on `--base`, lint for unclosed fences and Dataview-executed inline code, git snapshot, atomic verified write; no delete/move) for every harness, plus a PreToolUse guard hook (deny `obsidian delete` / `create … overwrite`, ask for `move` and for `rm`/`mv` inside the vault), with 31 tests. Agent Write Path now writes through `vault-write` (fallback kept for harnesses without plugin `bin/`); added `SendMessage` and a Reporting Back section (results are truncated at ~4K chars; long output goes to a file). Agent eval 93 (no change). |
| 1.28.0 | 2026-06-08 | - | Auto-discover write zones from vault profile when `.local.md` lacks them. Init step 3 now derives `architect_write_zones`/`curator_write_zones`/`designated_output_zones` from `_vault-profile.md` "Directory Trust Levels" table using mapping: `infrastructure` → architect, `personal/guarded`+`project-scoped` → curator, `automated/generated` → designated_output. Derived zones apply for the session; one-time AskUserQuestion offer to persist to `.local.md`. Policy-based refusals now prefix `Archivist policy:` to disambiguate from Claude Code tooling-layer denials (the "denied" wording was sending users down the wrong debugging path — see today's friction report). Empirical evidence: today's session spent ~90 min chasing a Claude Code permission bug that turned out to be the archivist's own bounded-autonomy refusing due to missing `.local.md`. Agent eval 93 (no change — substantive logic, not example/length metrics). |
| 1.27.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass A (friction batch 2026-06-05). A1: Denial Handling — Mode 1/Mode 2 recovery guidance with `permissions.allow` schema + JSON example; Mode 2 labeled "observed empirically, not root-caused." A2: Subagent Input Volume Guard — token-count + file-path-count trigger (not category labels); soft-confirm path before refusal; defense-in-depth framing. A3: External-System Handoffs — new table in §Post-Workflow routing meeting-extraction action items to `attache:attache`. Agent eval 93 (no change). |
| 1.26.0 | 2026-06-04 | [#160](https://github.com/totallyGreg/claude-mp/issues/160), [#129](https://github.com/totallyGreg/claude-mp/issues/129) | Friction fixes (2026-06-04 + 2026-05-28 reports) + Tier-1 wins from #160. Strict Denial Handling (stop on first denial across primitives, Read tool ≠ obsidian read ≠ Write's internal gate, pre-flight refusal when zones missing). Reference Formatting rule (wikilink intra-vault, file:// external, backticks code-only). Index refresh after Python writes. Init drift signal on primary fileClass. New `duplicate-detection-thresholds.md` policy reference. Closed #129 as superseded by current architecture. Agent eval 92→93 (Prompt 91→95). |
| 1.25.0 | 2026-05-03 | - | Safety hardening: Write Path (read-prepare-write protocol), Issue Learning, Fast Init, anti-cascade principle, Drift Triage in curator (mechanical vs semantic). Body trim 4955→3033 words (session-logging + canvas-types moved to references). Agent eval 89→92 (Role:3→15, Prompt:83→91). |
| 1.24.2 | 2026-04-24 | - | Refactor session-log to dispatch through logEntries.js; add resume/pause subcommands; entry enrichment with phase/outcome; linking conventions; progressive frontmatter updates |
| 1.21.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Agent-native improvements: init vault signals (Context Injection), delete workflows (CRUD), multi-vault .local.md (Shared Workspace), --no-write primitives (Tools as Primitives), index refresh after writes (UI Integration), /help + /workflows commands (Capability Discovery + Action Parity) |
| 1.20.0 | 2026-04-13 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add workflow classification (known vs novel detection) and session learning tables (Known Workflows + Workflow Candidates) to _vault-profile.md; promotion rule graduates 2+ occurrence candidates to workflow notes |
| 1.19.0 | 2026-04-09 | - | Add Canvas Types taxonomy (Impact/Workflow/Architecture/Knowledge Maps) and Change Impact Map workflow |

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (2)

| Skill | Description |
|-------|-------|
| `vault-architect` | Provide expert guidance for organizing and evolving Obsidian-based PKM systems. |
| `vault-curator` | Curate and evolve vault content through pattern detection, metadata intelligence, consolidation, discovery, and visualization. |

### Agents (2)

| Agent | Description |
|-------|-------|
| `archivist-architect` | Use this agent to design or change the structure of an Obsidian vault: Templater templates, `.base` files and Bases queries, frontmatter schemas and fileClass notes, new collections with folder… |
| `archivist` | Use this agent for any Personal Knowledge Management question or task involving an Obsidian vault — whether the request is casual and exploratory or a specific named workflow. |

### Commands (9)

| Command | Description |
|-------|-------|
| `/canvas` | Generate a knowledge map canvas for a scope — visualize notes and their connections as an Obsidian canvas file. |
| `/collection` | Scaffold a new collection folder or audit an existing one — folder note, Bases view, Templater template, and member consistency. |
| `/drift` | Detect schema drift for a fileClass — find inconsistent properties, type mismatches, and naming issues across notes. |
| `/duplicates` | Find similar or duplicate notes within a scope and guide consolidation — merge, alias, or create MOCs. |
| `/health` | Run a vault health snapshot — orphan count, collection health, schema drift signals, and top issues. |
| `/help` | List all available archivist slash commands with a one-line description of each. |
| `/session-log` | Manage a session log in your vault. |
| `/vault` | Start a PKM session with the archivist for your Obsidian vault — organizing notes, checking health, fixing metadata, finding duplicates, generating canvases… |
| `/workflows` | Show Known Workflows and Workflow Candidates tables from the vault profile. |

### Hooks (2)

| Hook | Trigger | Purpose |
|-------|-------|-------|
| `obsidian_guard.py` | PreToolUse Bash |  |
| `vault_file_guard.py` | PreToolUse Write\|Edit\|NotebookEdit |  |
<!-- END AUTOGEN:components -->

## Skill: vault-architect

### Current Metrics

**Score: 84/100** (Good) — 2026-10-18

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 77 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.15.0 | 2026-10-18 | [#175](https://github.com/totallyGreg/claude-mp/issues/175), [#224](https://github.com/totallyGreg/claude-mp/issues/224) | Runs inside `archivist-architect`. Write Boundaries now allow structural files inside content zones (folder notes, fileClass notes), matching the file guard; Vault Profiling is handed off by the curator. Score 84 (no change). Examples start every CLI call with `vault=`. | 77 | 90 | 100 | 100 | 100 | 84 |
| 1.14.0 | 2026-10-18 | [#222](https://github.com/totallyGreg/claude-mp/issues/222) | `tags all counts` → `tags counts` (vault-wide is now the default in Obsidian 1.14). Score 84 (no change). | 77 | 90 | 100 | 100 | 100 | 84 |
| 1.13.0 | 2026-10-16 | [#215](https://github.com/totallyGreg/claude-mp/issues/215) | Vault Profiling copies folder names exactly and records no daily-notes folder (#218). Write Boundaries: zone checks happen in `vault-write`; in-zone writes through it need no confirmation, `force`/delete/move/fallback writes still ask. Fixes SKILL.md version drift (was 1.11.0 while this table had 1.12.0). Score 84: the current evaluator also scores unmodified main at 84 (was 93 under the June evaluator); Concs 79→77 from added text. | 77 | 90 | 100 | 100 | 100 | 84 |
| 1.12.0 | 2026-06-08 | - | Align §Write Boundaries with auto-discovery: "No zones configured in `.local.md`" now references the agent's profile-derived zones (mapping doc) rather than refusing outright; refusals prefixed `Archivist policy:` to disambiguate from Claude Code tooling-layer denials. Score 94→93 (Concs 77→76 from added prose; substantive consistency with agent v1.28.0). | 76 | 90 | 100 | 100 | 100 | 93 |
| 1.11.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass C (friction batch 2026-06-05). C1: notation hygiene added to Design Principles "Do:" — per-template pick, prefer Obsidian-native `- [ ]`/`- [x]`, extended markers require Tasks plugin verification, no proactive retrofit. §10 Vault System Documentation updated to include Notation Conventions entry. Also fixed SKILL.md version drift (was stuck at 1.9.0 while README was at 1.10.0). Score 94 (Concs 79→77 from added text; overall floor met). | 77 | 90 | 100 | 100 | 100 | 94 |
| 1.10.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add vault-analysis-checks.md (analyze_vault.py check reference) and frontmatter-schema-reference.md (validate_frontmatter.py fields, severity, violations); update SKILL.md to reference both | 79 | 90 | 100 | 100 | 100 | 93 |
| 1.9.0 | 2026-04-11 | - | Add linking discipline to Design Principles: link aggressively, no backticked vault entities; schema authority: .base default view is canonical, fileClass mirrors it; pointer to linking-discipline.md | 79 | 90 | 100 | 100 | 100 | 93 |
| 1.8.0 | 2026-03-31 | - | Add Vault Profiling workflow, Write Boundaries section, replace hardcoded vault path with ${VAULT_PATH} | 80 | 90 | 100 | 100 | 100 | 94 |
| 1.7.0 | 2026-03-28 | - | Add Linter plugin config read to Vault Discovery; read .obsidian/plugins/obsidian-linter/data.json before writing notes | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.6.0 | 2026-03-28 | - | Add CLI delegation block to Vault Discovery naming obsidian-skills as source; document path= vs file= distinction and folder-note resolution | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.5.0 | 2026-03-26 | - | Reduce to 5 sections for full complexity score; merge Core Principles into intro, Resources into capabilities, Cross-Skill Handoff into Workflows; fix vault analysis to run CLI discovery before asking user | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.4.0 | 2026-03-25 | - | Add Vault Discovery (auto-discover templates/tags/orphans before recommending) and Cross-Skill Handoff sections; add license; add negative trigger clause; compress Workflow Lookup table | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.3.0 | 2026-03-14 | - | Add Workflow Lookup, Capture, and Refinement section: vault discovery via Workflows.base, Workflow fileClass schema, Capture-to-Review pattern reference; add missing `compatibility` field | 83 | 80 | 90 | 100 | 100 | 89 |
| 1.2.0 | 2026-03-05 | - | SKILL.md restructure: 12 trigger phrases, conciseness fix, structural bug fix (#89) | 83 | 80 | 80 | 100 | 100 | 86 |
| 1.1.1 | 2026-03-05 | - | Comprehensive QuickAdd 2.12.0 reference, SKILL.md section update | 34 | 88 | 80 | 100 | 100 | 78 |
| 1.0.0 | 2025-12-15 | - | Initial release with core PKM guidance | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)


## Skill: vault-curator

### Current Metrics

**Score: 96/100** (Excellent) — 2026-10-18

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 78 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 1.19.0 | 2026-10-18 | [#175](https://github.com/totallyGreg/claude-mp/issues/175), [#224](https://github.com/totallyGreg/claude-mp/issues/224) | Runs inside the curator agent with no Edit/Write: canvas edits go through `vault-write apply --from -` (JSON-validated); `cli-patterns.md` adds explicit vault targeting (`vault=`) and the index commands (`properties`, `outline`, `base:query`, `history`, `template:read`, `dev:errors`); session logging passes `vault=` on every call. Score 96 (no change). `cli-patterns.md` documents the measured `vault=` rules (working-directory default, placement, closed vaults open and take focus) and that `daily:*` CLI commands need the core Daily notes plugin. Write-capable scripts go through `vault-write`; `helper.py` (template leftover) removed. `detect_schema_drift.py --summary` returns counts and the top issues. | 79 | 100 | 100 | 100 | 100 | 96 |
| 1.18.0 | 2026-10-18 | [#222](https://github.com/totallyGreg/claude-mp/issues/222) | `cli-patterns.md` rewritten from live `obsidian help` (1.14.4): errors print `Error:` and exit 0, missing or mistyped `path=` falls back to the open note, `</dev/null` in loops, bounded listings, graph caveats; dropped `silent`, `tasks all`, `tags all`, `unresolved sources=true`, `create folder=`. `property:set` inline needs `path=` (guard zone-checks it). Score 86→96: Ref Currency 0→100 from the refreshed reference. | 80 | 100 | 100 | 100 | 100 | 96 |
| 1.17.0 | 2026-10-16 | [#215](https://github.com/totallyGreg/claude-mp/issues/215) | Write rules 4–5 and Write Boundaries now go through `vault-write` (stat → stage → apply with `--base`); in-zone writes need no confirmation; `cli-patterns.md` points updates at `vault-write`. Fixes SKILL.md version drift (was 1.15.0 while this table had 1.16.0). Score 86, same as unmodified main under the current evaluator (was 96 under the June evaluator). | 80 | 100 | 100 | 100 | 100 | 86 |
| 1.16.0 | 2026-06-08 | - | Align §Write Boundaries with agent's profile-derived zone discovery: "No zones configured in `.local.md`" no longer terminates — derived zones from `_vault-profile.md` apply if present. Refusal phrasing standardized to `Archivist policy:` prefix to disambiguate from Claude Code tooling-layer denials. Score 96 (Concs 79→78 from added refusal-phrasing rule; overall unchanged). | 78 | 100 | 100 | 100 | 100 | 96 |
| 1.15.0 | 2026-06-06 | [#176](https://github.com/totallyGreg/claude-mp/issues/176) | Pass B (friction batch 2026-06-05). B1: fileClass validation gate (item 6) — re-read `_vault-profile.md` from disk per write (freshness), parse Active fileClasses (table→bullet→warn-and-skip), refuse+surface gap if value absent. B2: entity wikilink check (item 3a) — batch scan with stop-list, code-fence skip, ~20 cap, single consolidated end-of-scan prompt (no per-candidate blocking). B3: schema-change guard in §Write Boundaries — hard-stop on fileClass/folder-convention/template-schema creation, explicit vault-architect routing. Score 96 (Concs 80→79 from added prose, overall unchanged). | 79 | 100 | 100 | 100 | 100 | 96 |
| 1.14.0 | 2026-06-04 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add `duplicate-detection-thresholds.md` reference (canvas, similarity, coverage thresholds with tuning guidance); link from Find Similar Notes and Canvas Map Generation sections | 80 | 100 | 100 | 100 | 100 | 96 |
| 1.13.0 | 2026-05-03 | - | Add Write Quality Gate rule #5 (read before write), Drift Triage protocol (mechanical vs semantic), session-logging.md reference | 80 | 100 | 100 | 100 | 100 | 96 |
| 1.12.0 | 2026-04-14 | [#160](https://github.com/totallyGreg/claude-mp/issues/160) | Add collection-health-criteria.md reference; add --no-write to generate_canvas.py, merge_notes.py, redirect_links.py (50-file cap on redirect); add --node-width/--node-height/--coverage-threshold CLI args; add fileClass group nodes + edge direction markers to canvas | 83 | 100 | 100 | 100 | 100 | 96 |
| 1.11.0 | 2026-04-11 | - | Add Wikilinks over backticks rule to Write Quality Gate; graph traversal commands to cli-patterns.md; create linking-discipline.md reference (decision table, schema authority, graph CLI commands) | 83 | 100 | 100 | 100 | 100 | 96 |
| 1.10.0 | 2026-04-01 | - | Demote Write Boundaries to H3; add Base Files and File Relocation rules to cli-patterns.md; offload verbose docs to references/ | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.4 | 2026-03-31 | - | Add Write Boundaries section for vault-aware permission zones | 80 | 90 | 100 | 100 | 100 | 94 |
| 1.9.3 | 2026-03-28 | - | Add Vault Write Quality Gate: frontmatter must start on line 1, Linter compliance check, bulk validation pointer | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.9.2 | 2026-03-28 | - | Name obsidian-skills as CLI source in delegation line; reference cli-patterns.md for error handling | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.1 | 2026-03-27 | - | Add vault write triggers ("update this note", "write to vault", "create a note from URL") to route content writes through curator | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.9.0 | 2026-03-26 | - | Add opportunistic drift detection to scope selection; surface schema inconsistencies proactively during any vault operation | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.8.1 | 2026-03-25 | - | Reduce section count for complexity score; merge Core Principles into intro, Visualization into Discovery; add markdown-oxide LSP fallback | 98 | 100 | 100 | 100 | 100 | 99 |
| 1.8.0 | 2026-03-25 | - | Add negative trigger clause to prevent overtriggering vs vault-architect; fix git add -A bug in archivist pre-consolidation checkpoint | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.7.0 | 2026-03-22 | - | Delegate CLI ops to marketplace skills; promote `create overwrite` write pattern inline; strip generic commands from cli-patterns.md to gotchas-only | 98 | 90 | 100 | 100 | 100 | 97 |
| 1.6.0 | 2026-03-20 | - | Add read/append/insertion CLI patterns to references; add license; move scripts table to reference; add available-scripts.md | 97 | 98 | 90 | 100 | 100 | 100 |
| 1.5.3 | 2026-03-16 | [#103](https://github.com/totallyGreg/claude-mp/issues/103) | Fix: document `obsidian file` is read-only; warn content/overwrite silently ignored | 78 | 88 | 90 | 100 | 100 | 90 |
| 1.5.2 | 2026-03-14 | - | Fix: document create+move pattern; warn folder= in create is unreliable | 88 | 90 | 100 | 90 | - | 78 |
| 1.5.1 | 2026-03-05 | [#89](https://github.com/totallyGreg/claude-mp/issues/89) | Description + conciseness improvement: 11 trigger phrases, CLI moved to ref, planned scripts fixed | 78 | 88 | 90 | 100 | 100 | 90 |
| 1.5.0 | 2026-02-16 | - | Visualization workflows: generate_canvas.py | 66 | 86 | 90 | 100 | 80 | 85 |
| 1.4.0 | 2026-02-16 | [#46](https://github.com/totallyGreg/claude-mp/issues/46) | Discovery workflows: find_related.py, progressive discovery views, auto-linking suggestions | 76 | 88 | 90 | 100 | 80 | 87 |
| 1.3.0 | 2026-02-16 | [#45](https://github.com/totallyGreg/claude-mp/issues/45) | Consolidation workflows: find_similar_notes.py, merge_notes.py, redirect_links.py, consolidation-protocol.md | - | - | - | - | - | 89 |
| 1.2.0 | 2026-02-15 | [#44](https://github.com/totallyGreg/claude-mp/issues/44) | Scope selection, metadata workflows (suggest_properties.py, detect_schema_drift.py), SKILL.md restructure | - | - | - | - | - | - |
| 1.0.0 | 2026-02-10 | - | Initial release with meeting extraction, migration patterns, and pattern detection workflows | - | - | - | - | - | - |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Agent: archivist-architect

### Current Metrics

**Score: 89/100** (Good) — 2026-10-18

| Trigger | Prompt | Coherence |
|---------|--------|-----------|
| 93 | 89 | 86 |

### Version History

| Version | Date | Issue | Summary | Trigger | Prompt | Coherence | Score |
|---------|------|-------|---------|---------|--------|-----------|-------|
| 1.0.0 | 2026-10-18 | [#175](https://github.com/totallyGreg/claude-mp/issues/175), [#224](https://github.com/totallyGreg/claude-mp/issues/224) | New agent: `claude-sonnet-5-5`, Edit/Write limited to the write zones by `vault_file_guard.py`, preloads vault-architect. Checks its own work with `base:query`, `template:read resolve` and `dev:errors`. | 93 | 89 | 86 | 89 |

**Metric Legend:** Trigger=Trigger Effectiveness, Prompt=System Prompt Quality, Coherence=Coherence (0-100 scale)
