---
title: "feat: Integrate jackal obsidian-cli learnings into pkm-plugin and establish first-in-line vault routing"
type: feat
status: completed
date: 2026-03-28
---

# feat: Integrate jackal obsidian-cli learnings into pkm-plugin and establish first-in-line vault routing

## Overview

The pkm-plugin's vault-architect skill has no CLI delegation guidance at all. vault-curator's gotcha reference is incomplete (missing jackal's template-placement, mkdir-p, format=json matches, and error table). pkm-manager duplicates CLI safety rules instead of deferring to the obsidian-cli skill. This plan integrates the richer patterns from the installed jackal obsidian-cli skill, removes duplication, and ensures pkm-manager is explicitly first-in-line when interacting with Obsidian vaults.

## Problem Frame

Four problems compound together:

1. **vault-architect** uses obsidian CLI commands in its Vault Discovery section but never tells an agent loading it where to go for full CLI guidance, gotchas, or fallback rules. An agent loading only vault-architect has no safety net.
2. **vault-curator/references/cli-patterns.md** captures three confirmed bugs and six safety rules, but misses several gotchas documented in the now-installed jackal skill: template-placement, mkdir-p requirement, `format=json matches` for programmatic search, and the error/fallback table.
3. **pkm-manager.md** has a standalone "Obsidian CLI Usage" section (lines 90–97) that duplicates what `cli-patterns.md` already covers. Two sources of truth create drift risk.
4. **pkm-manager** has no explicit negative trigger or DO NOT language to prevent an agent from bypassing it and going directly to the obsidian-cli skill when vault context is present. The agent description reads as "use for PKM questions" — it needs to declare itself first-in-line for all Obsidian vault interactions.

## Requirements Trace

- R1. vault-architect/SKILL.md must have a CLI delegation block pointing to the obsidian-cli skill, with a note on the `file=` vs `path=` distinction used in its own commands.
- R2. vault-curator/references/cli-patterns.md must incorporate all additional gotchas from the jackal obsidian-cli skill: template-placement, mkdir-p, `format=json matches`, and the error/fallback table.
- R3. archivist agent body must remove the embedded CLI safety rules and replace them with a single pointer to the obsidian-cli skill via the vault-curator reference chain.
- R4. archivist agent description must declare itself first-in-line for Obsidian vault interactions, with DO NOT examples that cover direct CLI requests.
- R5. Skill delegation references across vault-architect and vault-curator must explicitly name their source plugin (obsidian-skills for all delegated CLI/content/bases/canvas ops).

## Scope Boundaries

- No changes to skill logic, workflow steps, or Python scripts — this is CLI guidance and routing only.
- No changes to skill versions in this pass — version bump deferred until after skillsmith eval.
- kepano's plugin-dev workflow commands (dev:errors, plugin:reload, etc.) are out of scope — the pkm-plugin has no plugin-dev use case.
- **After this work, `obsidian-official-cli-skills` (jackal) marketplace is no longer needed** — all relevant learnings are absorbed into `cli-patterns.md` and the decision framework. The canonical ongoing external CLI skill becomes kepano's `obsidian-skills` obsidian-cli.

## Context & Research

### Relevant Code and Patterns

- `plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` — existing gotchas file; the right home for additional jackal patterns
- `plugins/pkm-plugin/skills/vault-architect/SKILL.md` lines 1–40 — Vault Discovery section uses CLI commands without delegation pointer
- `plugins/pkm-plugin/agents/pkm-manager.md` lines 90–97 — "Obsidian CLI Usage" section to be removed
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md` line 58 — the canonical delegation line (`obsidian-cli (operations), obsidian-markdown (content)...`) to mirror in vault-architect
- Installed jackal skill: `/Users/totally/.claude/plugins/marketplaces/obsidian-official-cli-skills/plugins/obsidian-cli/skills/obsidian-cli/SKILL.md`
- kepano skills marketplace: `/Users/totally/.claude/plugins/marketplaces/obsidian-skills/`

### Institutional Learnings

- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — Critical workflows buried past line 50 get skipped. CLI delegation and fallback must be in first 50 lines of any SKILL.md that uses CLI commands.
- `docs/lessons/plugin-integration-and-architecture.md` — New CLI patterns belong in `references/cli-patterns.md`, not in SKILL.md body. SKILL = domain knowledge, not command reference.
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — Duplicated CLI safety rules across agent and skill create a two-source-of-truth problem; consolidate and point.
- `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — When vault-curator version bumps, verify plugin.json and marketplace.json both reflect the new highest version.

### External References

- jackal obsidian-cli SKILL.md (installed): richer gotchas — template placement, mkdir-p, format=json matches, error/fallback table, safety rules section
- kepano obsidian-cli SKILL.md (installed): plugin-dev workflow (out of scope but worth noting in delegation line as source for dev: commands)

## Key Technical Decisions

- **Add CLI delegation to vault-architect in the Vault Discovery section, not as a new top-level section**: The Vault Discovery section is where vault-architect's CLI commands appear. Adding the delegation pointer there keeps it co-located with the commands that need it. Consistent with vault-curator's placement.
- **Consolidate pkm-manager CLI rules by pointer, not by deletion and reference-file enhancement**: The pkm-manager section must go. We point to vault-curator's `cli-patterns.md` rather than inlining even a summary. This keeps one canonical source of CLI guidance in the plugin.
- **Extend cli-patterns.md rather than creating a new reference file**: Follows the `SKILL = domain knowledge, not command reference` rule. Adding to the existing gotcha file avoids orphan-file risk and is consistent with how `cli-patterns.md` is already linked from vault-curator SKILL.md.
- **pkm-manager first-in-line via DO NOT USE examples in description**: The agent description is the correct surface for routing intent. A `Do NOT use` block with 1–2 examples (user asks for `obsidian search`; user asks about backlinks) explicitly redirects direct CLI requests through pkm-manager.
- **Name source plugins in delegation lines, pointing to kepano obsidian-skills**: After this work only one obsidian-cli skill remains needed — kepano's. Delegation lines name `obsidian-skills` explicitly. This makes the obsidian-official-cli-skills marketplace safe to uninstall.

## Open Questions

### Resolved During Planning

- *Which obsidian-cli skill to reference going forward?* kepano's `obsidian-skills` obsidian-cli — it is the canonical ongoing reference. The jackal skill (`obsidian-official-cli-skills`) is a one-time source: its gotchas and decision framework are absorbed into `cli-patterns.md` in this work, after which the jackal marketplace can be uninstalled. Delegation lines point to `obsidian-skills` only.
- *Should vault-architect get a cli-patterns.md of its own?* No — vault-architect has no unique CLI bugs. The existing vault-curator file is the single reference; vault-architect delegates to it by pointing to the obsidian-cli skill.
- *Should pkm-manager version bump now?* No — version bump deferred to after skillsmith eval post-implementation.

### Deferred to Implementation

- Exact line numbers in vault-curator SKILL.md line 58 (may have shifted; verify at edit time).
- Whether kepano skills are installed at the expected path — verify before adding source plugin names.

## Implementation Units

- [ ] **Unit 0: Rename pkm-manager agent to archivist**

**Goal:** The agent name reflects its actual domain (Obsidian vault stewardship) rather than a generic PKM manager label.

**Requirements:** R4 (strengthens first-in-line identity)

**Dependencies:** None — do this first so subsequent units use the new name.

**Files:**
- Rename: `plugins/pkm-plugin/agents/pkm-manager.md` → `plugins/pkm-plugin/agents/archivist.md`
- Modify: `plugins/pkm-plugin/agents/archivist.md` — update `name: pkm-manager` → `name: archivist`; update all inline commentary references from "pkm-manager agent" → "archivist agent"; update `subagent_type: pkm-plugin:pkm-manager` → `subagent_type: pkm-plugin:archivist`
- Modify: `plugins/pkm-plugin/commands/vault.md` — update description and invocation line
- Modify: `plugins/pkm-plugin/skills/vault-curator/references/consolidation-protocol.md` — 2 references (lines ~36 and ~197)
- Modify: `plugins/pkm-plugin/README.md` — 2 references
- Modify: `~/.claude/projects/-Users-totally-Documents-Projects-claude-mp/memory/MEMORY.md` — update `pkm-manager` agent name references (outside repo, must be edited manually)

**Approach:**
- Git rename (`git mv`) preserves history. Rename first, then edit.
- Brainstorm files in `docs/brainstorms/` are historical artifacts — leave untouched.
- After rename, grep for any remaining `pkm-manager` references in the plugin to catch stragglers.

**Test scenarios:**
- Happy path: `grep -r "pkm-manager" plugins/pkm-plugin/` returns only brainstorm files.
- Edge case: `subagent_type: pkm-plugin:archivist` in the agent file matches the new filename-based registration.

**Verification:**
- `ls plugins/pkm-plugin/agents/` shows `archivist.md`, no `pkm-manager.md`.
- `grep -r "pkm-manager" plugins/pkm-plugin/ --include="*.md" --include="*.json" | grep -v "docs/brainstorms"` returns empty.

---

- [ ] **Unit 1: Add CLI delegation block to vault-architect/SKILL.md**

**Goal:** Any agent loading vault-architect gets pointed to the obsidian-cli skill for command reference, fallbacks, and gotchas — the same guarantee vault-curator already provides.

**Requirements:** R1, R5

**Dependencies:** None

**Files:**
- Modify: `plugins/pkm-plugin/skills/vault-architect/SKILL.md`

**Approach:**
- Locate the Vault Discovery section (lines ~25–45). Add a short "CLI Delegation" sub-note immediately before or after the first command block.
- Include: (a) pointer to kepano's `obsidian-skills` obsidian-cli skill for full command reference and fallback rules; (b) note that `file=` (link-style) vs `path=` (vault-relative) are distinct targeting modes — vault-architect uses `file=` intentionally for folder-note resolution; (c) fallback: if `obsidian vault` fails, use Glob/Grep/Read.
- Keep it 4–6 lines. No command reference duplication.
- Mirror the voice and style of vault-curator's existing delegation line.

**Patterns to follow:**
- vault-curator SKILL.md delegation line (~line 58)
- jackal SKILL.md "When to Use CLI vs File Tools" section structure

**Test scenarios:**
- Happy path: An agent loading vault-architect encounters the CLI delegation block before the first obsidian command in Vault Discovery.
- Edge case: The delegation block mentions `file=` vs `path=` distinction so the `obsidian read file="Workflows"` command in the section is self-explanatory.
- Verification: No obsidian command in vault-architect SKILL.md appears without the delegation block being visible above it.

**Verification:**
- `grep -n "obsidian-skills" plugins/pkm-plugin/skills/vault-architect/SKILL.md` returns a match before line 50.
- `grep -n "file=\|path=" plugins/pkm-plugin/skills/vault-architect/SKILL.md` returns a match in the delegation block (file= and path= discussed as separate modes).

---

- [ ] **Unit 2: Enhance vault-curator/references/cli-patterns.md with jackal gotchas**

**Goal:** The gotcha reference file becomes complete: all jackal learnings are captured alongside existing ones, and there is an error/fallback table.

**Requirements:** R2

**Dependencies:** None (can run in parallel with Unit 1)

**Files:**
- Modify: `plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md`

**Approach:**
- Add a **"CLI vs file tools" decision rule** at the top of the file (this is the most critical missing piece from jackal): Use obsidian CLI when Obsidian's index adds value (search, backlinks, tags, tasks, properties, bases). Use file tools (Read/Write/Edit/Grep/Glob) for simple read/write, bulk text replacement, or grep across files — no app dependency. Rule of thumb: if Obsidian's index adds value, use CLI; if it's plain text manipulation, use file tools.
- Add the following gotchas from the jackal skill — each as a standalone rule with the same formatting as existing rules:
  1. **Template placement**: `create` with `template=` may place the file in the template's configured folder, ignoring `path=`. Always verify actual path with `obsidian search` or `obsidian files` after template-based creation.
  2. **mkdir-p requirement**: `create` does not auto-create directories. Use `mkdir -p` via Bash first if the parent folder doesn't exist.
  3. **format=json matches**: for programmatic search, prefer `obsidian search query="..." format=json matches` — returns `[{"file":"path","matches":[{"line":N,"text":"..."}]}]` rather than flat file list.
  4. **Error/fallback table**: read the jackal SKILL.md Error Handling section at `/Users/totally/.claude/plugins/marketplaces/obsidian-official-cli-skills/plugins/obsidian-cli/skills/obsidian-cli/SKILL.md` and copy the exact table verbatim including formatting. Do not paraphrase.
- Preserve all existing rules verbatim (folder=, file/overwrite, silent, tasks all, tags all, create-overwrite is destructive).
- Update preamble to name kepano's `obsidian-skills` as the canonical CLI skill reference (replaces any reference to `obsidian-official-cli-skills`).

**Patterns to follow:**
- Existing formatting in `cli-patterns.md` (bullet rules with bold gotcha label, then explanation)
- jackal SKILL.md "Gotchas" and "Error Handling" sections

**Test scenarios:**
- Happy path: All four new gotchas are present with the same style as existing rules.
- Edge case: Error/fallback table uses correct symptom descriptions matching jackal's (not paraphrased so broadly they lose precision).
- Verification: Existing rules are untouched — diff shows only additions.

**Verification:**
- `grep -c "template-placement" plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` returns 1+.
- `grep -c "mkdir" plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` returns 1+.
- `grep -c "format=json matches" plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` returns 1+.
- `grep -c "Unknown command" plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` returns 1+.
- `grep -c "cli-patterns" plugins/pkm-plugin/skills/vault-curator/SKILL.md` returns 1+ (link intact after any edits).

---

- [ ] **Unit 3: Consolidate pkm-manager CLI guidance and strengthen first-in-line routing**

**Goal:** pkm-manager is unambiguously the first point of contact for any Obsidian vault interaction, and it no longer duplicates CLI safety rules.

**Requirements:** R3, R4

**Dependencies:** Unit 2 (cli-patterns.md must be complete before pkm-manager points to it)

**Dependencies:** Unit 0 (file is named `archivist.md` after rename). Unit 2 can run in parallel — `cli-patterns.md` exists and is already linked; the pointer is valid regardless of whether Unit 2's additions are complete yet.

**Files:**
- Modify: `plugins/pkm-plugin/agents/archivist.md` (renamed from `pkm-manager.md` in Unit 0)

**Approach:**
- **Remove** the "Obsidian CLI Usage" section (currently lines 90–97 containing the six safety rules). Replace with a single line: `For CLI gotchas and safety rules, see vault-curator's cli-patterns.md reference (loaded during initialization).`
- **Add DO NOT USE block** to the agent description (after the existing examples, before the closing `---`). Include 2 examples:
  - User asks `obsidian search query="..."` directly → route through pkm-manager for vault context first
  - User asks "show my backlinks for X" → pkm-manager, not raw obsidian-cli skill
- Keep the init step `obsidian vault` connection check — that is agent plumbing, not duplicated CLI guidance.
- The `format=json` usage already in the agent (line ~94) will be removed with the section; if it's referenced elsewhere in the agent body, update to point to cli-patterns.md.

**Patterns to follow:**
- pkm-manager.md existing example block style for DO NOT USE examples
- omnifocus-manager agent description's DO NOT USE section as a structural model (if present)

**Test scenarios:**
- Happy path: pkm-manager description has a DO NOT use block with obsidian-cli example.
- Edge case: pkm-manager still has the vault connection check (`obsidian vault`) — only the duplicated safety rules section is removed.
- Verification: `grep -n "Obsidian CLI Usage" plugins/pkm-plugin/agents/pkm-manager.md` returns no matches.

**Verification:**
- The "Obsidian CLI Usage" section is gone; a pointer to vault-curator's cli-patterns.md is present in its place; the DO NOT use block exists in the description.

---

- [ ] **Unit 4: Name source plugin in vault-curator SKILL.md delegation line**

**Goal:** vault-curator's delegation line explicitly names `obsidian-skills` as the source marketplace plugin, matching the delegation block added to vault-architect in Unit 1.

**Requirements:** R5

**Dependencies:** Unit 1 (vault-architect delegation block already names the source; vault-curator should match)

**Files:**
- Modify: `plugins/pkm-plugin/skills/vault-curator/SKILL.md`

**Approach:**
- Locate the delegation line (~line 58). Confirm actual position with `grep -n "cli-patterns\|obsidian-cli" vault-curator/SKILL.md` before editing.
- Update to read: `obsidian-cli (vault ops), obsidian-markdown (content), obsidian-bases (.base files), json-canvas (.canvas files) — all from obsidian-skills`
- Remove any reference to `obsidian-official-cli-skills` — its learnings are now absorbed.
- Note parenthetically: kepano's obsidian-cli also covers plugin dev commands (dev:errors, plugin:reload) — available but out of scope for PKM vault work.
- Verify obsidian-skills is installed at `/Users/totally/.claude/plugins/marketplaces/obsidian-skills/skills/obsidian-cli/SKILL.md` (flat `skills/` layout, no `plugins/` subdirectory) before naming it. If not found, emit `from obsidian-skills (install separately)`.
- After edit, verify the `cli-patterns.md` reference on the same line is preserved — do not accidentally remove it.

**Note:** Source plugin naming for vault-architect is handled inline in Unit 1. This unit completes the mirror for vault-curator only.

**Test scenarios:**
- Happy path: vault-curator delegation line names `obsidian-skills` as source.
- Edge case: `cli-patterns.md` link on or near the same line is intact after edits.
- Edge case: `grep -n "obsidian-official-cli-skills" vault-curator/SKILL.md` returns empty.

**Verification:**
- `grep -n "obsidian-skills" plugins/pkm-plugin/skills/vault-curator/SKILL.md` returns a match.
- `grep -c "cli-patterns" plugins/pkm-plugin/skills/vault-curator/SKILL.md` returns 1+ (link preserved).

## System-Wide Impact

- **Interaction graph:** pkm-manager.md loads both SKILL.md files at init — changes to vault-architect SKILL.md and vault-curator SKILL.md are immediately visible to the agent at runtime without any other changes.
- **Error propagation:** Removing the duplicate CLI rules from pkm-manager creates a single point of failure: if an agent doesn't load vault-curator's cli-patterns.md, it has no gotcha reference. This is acceptable — pkm-manager already loads vault-curator SKILL.md at init, and vault-curator SKILL.md points to cli-patterns.md.
- **Unchanged invariants:** vault-curator's `cli-patterns.md` file-link from SKILL.md must remain — if that reference is lost, the consolidated guidance becomes orphaned. Verify this link is intact after edits.
- **Integration coverage:** Skills are loaded by value (Read tool), not by reference — changes to SKILL.md files take effect immediately for any new agent session.

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| vault-curator SKILL.md delegation line has shifted from line 58 | Verify with grep before editing |
| kepano obsidian-skills not installed at expected path | Check path before naming it in delegation lines; fall back to "(install separately)" note |
| Removing pkm-manager CLI section breaks an agent that relied on it being local | The init sequence already loads vault-curator SKILL.md which points to cli-patterns.md — the pointer chain is intact |
| Version bump skipped when it should be triggered | Run skillsmith eval after all units complete; bump only if score changes materially |

## Sources & References

- Related code: `plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md`
- Related code: `plugins/pkm-plugin/skills/vault-architect/SKILL.md` lines 25–45
- Related code: `plugins/pkm-plugin/agents/pkm-manager.md` lines 90–97
- Related lessons: `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`
- Related lessons: `docs/lessons/plugin-integration-and-architecture.md`
- External (installed): `/Users/totally/.claude/plugins/marketplaces/obsidian-official-cli-skills/plugins/obsidian-cli/skills/obsidian-cli/SKILL.md`
- External (installed): `/Users/totally/.claude/plugins/marketplaces/obsidian-skills/`
