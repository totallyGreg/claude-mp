---
title: "feat: PKM Plugin Skill Consolidation and Improvement"
type: feat
status: completed
date: 2026-03-05
issue: "#89"
---

# PKM Plugin Skill Consolidation and Improvement

## Overview

Both skills in the pkm-plugin (vault-architect and vault-curator) have structural and scoring issues identified by skillsmith evaluation and plugin-dev reviewers. This plan addresses conciseness, description quality, plugin-level fixes, and cross-skill consistency to bring both skills to overall >= 85.

**Current State:**

| Skill | Overall | Conciseness | Complexity | Spec | Progressive | Description |
|-------|---------|-------------|------------|------|-------------|-------------|
| vault-architect | 78 | 34 | 88 | 80 | 100 | 100 |
| vault-curator | 85 | 66 | 86 | 90 | 100 | 80 |

**Target State:** Both skills overall >= 85, all individual scores >= 60.

## Problem Statement

1. **vault-architect conciseness (34/100)** — SKILL.md is ~3800 words with ~1500 words duplicating reference content. Sections 5 and 6 (Chronos, QuickAdd) are structurally orphaned after the Resources section.
2. **vault-curator description (80/100)** — 18 trigger phrases but only 1 ("generate canvas") uses a verb from the evaluator's recognized list: `create`, `validate`, `evaluate`, `improve`, `analyze`, `check`, `init`, `add`, `build`, `configure`, `set up`, `research`, `sync`, `generate`, `update`, `fix`, `debug`.
3. **Plugin-level issues** — Stale README, invalid agent color, missing model field, empty directories, stale names.

## Proposed Solution

Three phases of focused changes, each independently committable.

## Technical Considerations

- **Evaluator verb list** (`evaluate_skill.py:901-904`): Only specific verbs are recognized for trigger phrase scoring. Rephrase vault-curator triggers to use recognized verbs while preserving natural-language alternatives.
- **Conciseness scoring** (`evaluate_skill.py`): Both line count and token count factor in. Moving content to references improves the score while maintaining progressive disclosure.
- **False positive awareness** (see `docs/lessons/evaluate-skill-false-positives.md`): Path references in documentation can trigger false warnings. Use bare filenames when listing reference examples.
- **Metrics tracking** (see `docs/lessons/improvement-plan-metrics-tracking.md`): Capture full metric breakdown in IMPROVEMENT_PLAN.md version history tables.

## Acceptance Criteria

- [x] vault-architect overall >= 85, conciseness >= 60 (86/100, conciseness 83)
- [x] vault-architect trigger phrases >= 10 (12 found)
- [x] vault-architect structural bug fixed (Chronos/QuickAdd inside Core Capabilities)
- [x] vault-curator overall >= 85, description score = 100 (90/100, description 100)
- [x] vault-curator conciseness >= 75 (78)
- [x] No references to non-existent scripts in SKILL.md
- [x] Plugin-level fixes: README, agent color, stale names, empty dirs
- [x] Both IMPROVEMENT_PLAN.md files updated with eval metrics
- [x] Skillsmith evaluation passes for both skills

## Implementation Phases

### Phase 1: vault-architect SKILL.md Restructure

**Goal:** Conciseness from 34 to >= 60, trigger phrases from 4 to >= 10.

**Files modified:**
- `plugins/pkm-plugin/skills/vault-architect/SKILL.md`
- `plugins/pkm-plugin/skills/vault-architect/IMPROVEMENT_PLAN.md`

**Tasks:**

1. **Fix structural bug** — Move orphaned sections (Chronos at line 408, QuickAdd at line 431) into Core Capabilities, renumbering as sections 5 and 6 (before the existing section 7: Vault System Documentation).

2. **Expand trigger phrases in description** — Add recognized-verb triggers:
   - "create a template", "create Obsidian templates" (already present)
   - "design Bases queries" (already present)
   - "set up vault structure" (already present)
   - "configure Templater workflows" (already present)
   - "create a .base file"
   - "set up daily weekly monthly rollup"
   - "analyze vault organization"
   - "configure Excalibrain"
   - "build temporal rollup system"
   - "update frontmatter schema"
   - "fix vault organization"
   - "add metadata to templates"

3. **Slash inline content** — Replace detailed code/examples with 2-3 sentence summaries pointing to existing references:

   | Section | Action | Est. lines saved |
   |---------|--------|-----------------|
   | Section 2: Template Creation (lines 76-163) | Remove Templater API code block and full meeting template example. Keep 5-line summary pointing to `templater-api.md` and `templater-patterns.md` | ~60 |
   | Section 3: Bases Query Design (lines 164-192) | Remove Core Bases Concepts enumeration and .base template list. Keep summary with pointer to `bases-query-reference.md` and `bases-patterns.md` | ~20 |
   | Section 4: Frontmatter Schema (lines 193-221) | Remove full field enumerations. Keep summary with pointers to `excalibrain-metadata.md` | ~15 |
   | Section 5: Temporal Rollup (lines 222-258) | Condense implementation details. Keep principles and pointer | ~15 |
   | Section 6: Job-Agnostic (lines 260-292) | Remove folder tree. Keep summary pointing to `folder-structures.md` | ~20 |
   | Workflow sections (lines 314-386) | Condense two workflow checklists to brief summaries since they restate core capabilities | ~40 |
   | Examples (lines 466-524) | Condense to 1-2 brief examples inline, remove verbose ones | ~30 |

   **Target:** ~200 lines removed, bringing SKILL.md from ~528 to ~330 lines.

4. **Add boundary note** — Add one paragraph at top of Core Capabilities clarifying: vault-architect creates new structures, vault-curator maintains/evolves existing content.

5. **Run skillsmith evaluation**, record metrics in IMPROVEMENT_PLAN.md.

### Phase 2: vault-curator SKILL.md Improvements

**Goal:** Description from 80 to 100, conciseness from 66 to >= 75.

**Files modified:**
- `plugins/pkm-plugin/skills/vault-curator/SKILL.md`
- `plugins/pkm-plugin/skills/vault-curator/IMPROVEMENT_PLAN.md`

**Tasks:**

1. **Rephrase trigger phrases** — Replace key phrases with recognized-verb equivalents while keeping natural triggers as supplementary text:

   ```yaml
   description: >
     This skill should be used when users ask to "analyze vault metadata",
     "check for schema drift", "fix duplicate notes", "update note properties",
     "generate canvas", "improve vault connections", "create discovery view",
     "validate frontmatter consistency", "build knowledge map",
     "check for orphaned notes", or "analyze note relationships".
     Also handles: "find duplicates", "merge notes", "redirect links",
     "suggest properties", "show connections", "extract meeting from log",
     "migrate vault notes", "visualize my notes", or "show me a map".
     Curates and evolves existing vault content through pattern detection,
     migration workflows, metadata intelligence, consolidation, discovery,
     visualization, and programmatic manipulation.
   ```

   This gives 11 recognized-verb phrases (analyze x2, check x2, fix, update, generate, improve, create, validate, build) plus 9 natural-language supplementary triggers.

2. **Move CLI commands to reference** — Create `references/cli-patterns.md` from the CLI block (lines 57-83). Replace with 3-line summary:
   ```markdown
   ## Obsidian CLI Integration
   Use obsidian-cli for property, search, structure, and tag operations.
   **See:** `references/cli-patterns.md` for command reference and safety rules.
   **Fallback:** If CLI unavailable (Obsidian not running), use Grep/Glob/Read.
   ```

3. **Trim Python Script Patterns section** (lines 316-337) — Reduce from 22 lines to 5 lines. The PEP 723 boilerplate is not needed in the skill body.

4. **Fix non-existent script references** — In Pattern Detection section (lines 298-314):
   - `find_orphans.py` (line 305): Replace code block with note: "Use `obsidian orphans` CLI command. Dedicated script planned."
   - `find_note_clusters.py` (line 311): Replace code block with note: "Planned — use `find_related.py` with `--scope` for similar functionality."
   - Update Available Scripts table: remove "Planned" entries or clearly mark them with footnotes.

5. **Run skillsmith evaluation**, record metrics in IMPROVEMENT_PLAN.md.

### Phase 3: Plugin-Level Fixes

**Goal:** Clean up all plugin infrastructure issues.

**Files modified:**
- `plugins/pkm-plugin/README.md`
- `plugins/pkm-plugin/agents/pkm-manager.md`
- `plugins/pkm-plugin/skills/vault-architect/IMPROVEMENT_PLAN.md`

**Tasks:**

1. **Fix README.md:**
   - Replace broken path `skills/obsidian-pkm-manager/SKILL.md` with correct paths: `skills/vault-architect/SKILL.md` and `skills/vault-curator/SKILL.md`
   - Update version from `1.0.0` to match `plugin.json` (`1.5.0`)

2. **Fix agent `pkm-manager.md`:**
   - Change `color: purple` to `color: magenta` (valid spec value)
   - Add `model: inherit` to frontmatter

3. **Fix stale name** in vault-architect `IMPROVEMENT_PLAN.md`:
   - Replace "obsidian-pkm-manager skill" with "vault-architect skill" in overview line

4. **Handle empty `templater-snippets/` directory:**
   - Option A: Remove directory and its SKILL.md reference
   - Option B: Add a README.md placeholder explaining planned content
   - **Recommendation:** Option A — remove per YAGNI. If snippets are needed later, recreate.

5. **Run plugin validator** to confirm all issues resolved.

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Over-trimming SKILL.md breaks progressive disclosure | Low | Keep summaries that explain *when* to load references, not just pointers |
| Trigger phrase rewording reduces natural-language triggering | Low | Keep original phrases as supplementary text in description |
| Conciseness score doesn't reach target | Medium | If below 60 after restructure, consider creating additional reference files for workflows/examples |
| Empty templater-snippets removal breaks something | Very Low | Directory is empty — nothing depends on it |

## Success Metrics

| Metric | Current (architect) | Current (curator) | Target |
|--------|-------------------|-------------------|--------|
| Overall | 78 | 85 | >= 85 |
| Conciseness | 34 | 66 | >= 60 / >= 75 |
| Description | 100 | 80 | 100 / 100 |
| Trigger Phrases | 4 | 1 | >= 10 / >= 10 |

## Sources & References

- Issue: [#89](https://github.com/totallyGreg/claude-mp/issues/89)
- Evaluator verb list: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:901-904`
- Lessons: `docs/lessons/evaluate-skill-false-positives.md` — false positive warnings for paths in docs
- Lessons: `docs/lessons/improvement-plan-metrics-tracking.md` — metrics table format conventions
- Skill reviewer analysis: vault-architect agent (a1b55f1d6ac4e388d), vault-curator agent (a9b98392c0a94d810)
- Plugin validator analysis: agent (aafcd06d72b31e318)
