---
title: "refactor: Migrate per-skill README.md to plugin-level README.md"
type: refactor
status: active
date: 2026-03-25
origin: "Obsidian: 800 Generated/820 Brainstorms/2026-03-25 Migrate README to Plugin Level Requirements.md"
issue: https://github.com/totallyGreg/claude-mp/issues/148
---

# Migrate Per-Skill README.md to Plugin-Level README.md

## Overview

Remove README.md from all 11 skill directories across 7 plugins, merging their metrics and version history into each plugin's README.md. Update `evaluate_skill.py` and `init_skill.py` to target the new location. Make `--update-readme` auto-detect and migrate any remaining skill-level README.md or IMPROVEMENT_PLAN.md found in skill directories. Aligns with Anthropic's guidance: "Don't include README.md inside your skill folder."

## Problem Frame

Skill-level README.md files are present in the installed plugin cache at `~/.claude/plugins/cache/` with ambiguous runtime loading behavior. Anthropic's Complete Guide to Building Skills explicitly prohibits them. The current `evaluate_skill.py --update-readme` hardcodes the path as `skill_path / 'README.md'`, and `init_skill.py` generates README.md in the skill scaffold for standard/complete templates. (See origin document for full context.)

## Requirements Trace

- R1. Remove README.md from all `plugins/*/skills/*/` directories
- R2. Merge per-skill metrics into plugin-level README.md using `## Skill: <name>` sections
- R3. Plugin README retains existing content; adds skill metrics sections below
- R4. Update `evaluate_skill.py --update-readme` to target plugin-level README.md
- R4a. `--update-readme` auto-detects skill-level README.md or IMPROVEMENT_PLAN.md and migrates content to plugin README (with approval). Idempotent — no-ops if already migrated.
- R5. Review `--export-table-row` for path assumptions — confirmed non-issue (stdout only)
- R6. Stop `init_skill.py` from generating skill-level README.md
- R7. Update skillsmith reference docs; rename `readme_template.md` to `plugin_readme_template.md` for clarity
- R7a. Improve Version History table column headers — replace ambiguous 4-char abbreviations (`Conc | Comp | Spec | Disc | Desc`) with clearer labels; update legend accordingly
- R7b. Compact the Current Metrics display — reduce vertical footprint while preserving the offset from the history table
- R8. Update CLAUDE.md, WORKFLOW.md, MEMORY.md references
- R9. Rename plugin `## Version History` to `## Changelog`
- R10. Add skill name validation to `utils.py` — enforce Anthropic spec (max 64 chars, lowercase letters/numbers/hyphens, no leading/trailing hyphen). Use in `evaluate_skill.py` and `package_skill.py`.
- R11. Remove remaining IMPROVEMENT_PLAN.md references — historical artifacts preserved in git; the reasoning about metrics-tracked changes at plugin level is retained

## Scope Boundaries

- NOT affecting `skills/swift-dev/README.md` (non-plugin legacy layout)
- NOT making `init_skill.py` plugin-aware
- NOT adding `.skillignore` mechanism
- NOT cleaning plugin cache
- NOT changing SKILL.md or references/ behavior

## Context & Research

### Relevant Code and Patterns

- `evaluate_skill.py` lines 1702-1725: `_update_current_metrics_section()` uses regex `r'(?ms)^(## Current Metrics)(.*?)(?=\n## |\n---|\Z)'` — matches first `## Current Metrics` heading. Must be reworked for scoped matching within `## Skill: <name>` sections.
- `evaluate_skill.py` lines 1662-1699: `_generate_metrics_content()` produces the Current Metrics section body — 3-column vertical table (Metric | Score | Interpretation) with 6-7 rows plus date and footer. This is the display to compact.
- `evaluate_skill.py` lines 1728-1834: `generate_skill_readme()` has two paths — idempotent update (README exists) and first-time generation (from IMPROVEMENT_PLAN.md). README path hardcoded as `sp / 'README.md'`.
- `evaluate_skill.py` lines 2800-2856: `--export-table-row` outputs `| {ver} | {date} | {issue} | {summary} | {conc} | {comp} | {spec} | {disc} | {desc} | {overall} |` with 4-char column abbreviations.
- `init_skill.py` lines 338-391: `README_TEMPLATE` constant. Lines 453-454: generated for standard/complete, not minimal.
- `readme_template.md`: Documents skill-level README format. Column legend: `Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality`.
- Skillsmith `utils.py`: `find_repo_root()` single-pass search. No skill name validation utility exists yet.

### Institutional Learnings

- **IMPROVEMENT_PLAN.md → README.md precedent** (`docs/lessons/improvement-plan-migration.md`): hybrid migration worked well. The reasoning for tracking skill changes with measurable metrics should be preserved; the IMPROVEMENT_PLAN.md format and references are historical artifacts in git.
- **`--update-readme` idempotency contract** (`readme_template.md`): only metrics section replaced; all other sections preserved. This contract must be maintained at the plugin level.
- **Multi-skill version sync** (`docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`): multi-skill plugins use "highest version" logic. Plugin README needs per-skill sections.
- **Regex false positive risk** (`docs/lessons/evaluate-skill-false-positives.md`): section replacement regex should handle code blocks carefully.

## Key Technical Decisions

- **Plugin-root discovery**: New `find_plugin_root()` in skillsmith `utils.py`. Walks up from skill path looking for `.claude-plugin/plugin.json`. Falls back with warning for standalone skills. (See origin: brainstorm Key Decisions)
- **Section scoping**: `_update_current_metrics_section()` reworked to find `## Skill: <name>` first, then match `### Current Metrics` within that scope. Consider using a markdown LSP server or structured parser for reliable nested heading extraction rather than fragile regex.
- **Auto-detect and migrate**: When `--update-readme` finds a README.md or IMPROVEMENT_PLAN.md in a skill directory, it extracts metrics content, prompts for approval, migrates to the plugin README, and deletes the skill-level file. Idempotent — skips if `## Skill: <name>` section already exists in plugin README.
- **Auto-create sections**: If `## Skill: <name>` doesn't exist in plugin README and no skill-level README exists to migrate, `--update-readme` appends a fresh section.
- **Heading collision**: Plugin `## Version History` renamed to `## Changelog`. Per-skill sections keep `### Version History`.
- **Skill name in headings**: Directory name (e.g., `zsh-dev`), matching SKILL.md frontmatter `name:`. Validated against Anthropic spec: max 64 chars, lowercase `[a-z0-9-]`, no leading/trailing hyphen.
- **Compact metrics display**: Current Metrics uses a vertical 3-column table (7 rows + header/date/footer = ~12 lines). Compact to a horizontal single-row summary or condensed format while keeping it visually offset from the Version History table.
- **Clearer column headers**: Replace ambiguous abbreviations in Version History table: `Conc` → `CN`, `Comp` → `CX`, `Spec` → `SP`, `Disc` → `PD`, `Desc` → `DQ` with an updated legend, OR use full words if table width permits at the `###` heading level.
- **Rename readme_template.md**: Rename to `plugin_readme_template.md` to reflect that the template now describes plugin-level README format with embedded skill sections.
- **IMPROVEMENT_PLAN.md cleanup**: Remove references to IMPROVEMENT_PLAN.md as a format. Retain the core reasoning: skill changes should be tracked with measurable metrics at the plugin level. Historical IMPROVEMENT_PLAN.md content is preserved in git.
- **Migration approach**: Script-assisted for the initial bulk migration. `--update-readme` handles ongoing detection for any future stragglers.
- **Version bump**: Minor version bump (6.7.0 → 6.8.0). README.md was an informational addition, not part of the skill spec — this is a tooling change, not a breaking API change.

## Open Questions

### Resolved During Planning

- **Migration script vs manual?** Script-assisted for bulk migration. `--update-readme` handles future auto-detection.
- **Skill name format?** Directory name, validated against Anthropic spec.
- **R5 (--export-table-row)?** Confirmed non-issue. Stdout only.
- **R7 reference triage?** `readme_template.md` → rename + rewrite. `improvement_plan_best_practices.md` → rewrite to remove IMPROVEMENT_PLAN references, keep metrics reasoning. Other 5 files → path-swap.
- **Version bump level?** Minor (6.8.0). README was informational, not part of the skill spec.

### Deferred to Implementation

- Exact approach for scoped section replacement — regex vs markdown parser vs LSP-assisted. Depends on testing against real multi-skill README content.
- Specific compact format for Current Metrics display — iterate on options during implementation.
- Whether `generate_skill_readme()` first-time generation path (from IMPROVEMENT_PLAN.md) can be removed — likely dead code, but verify during implementation.

## Implementation Units

### Phase 0: Pre-Migration Cleanup (column headers and display format)

- [ ] **Unit 0: Improve Version History column headers and compact Current Metrics**

  **Goal:** Replace ambiguous 4-char abbreviations in the Version History table with clearer labels. Compact the Current Metrics display. These changes must happen before migration to ensure consistency in the migrated data.

  **Requirements:** R7a, R7b

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` (`_generate_metrics_content()`, `--export-table-row` output format)
  - Modify: `plugins/skillsmith/skills/skillsmith/references/readme_template.md` (column legend)
  - Modify: all 11 `plugins/*/skills/*/README.md` (update existing table headers to match new format)

  **Approach:**
  - Decide on clearer column header format — either short-but-unambiguous abbreviations or full words
  - Update `_generate_metrics_content()` to produce a more compact Current Metrics display while keeping it visually distinct from the history table
  - Update `--export-table-row` output to use the new column headers
  - Update existing Version History tables across all 11 skill READMEs and their legends
  - Update the template/legend in `readme_template.md`

  **Test scenarios:**
  - `--export-table-row` outputs new column header format
  - `--update-readme` produces compact Current Metrics
  - Existing tables readable with new headers

  **Verification:**
  - All 11 skill READMEs + template use consistent column headers
  - Legend is unambiguous

### Phase 1: Tooling Changes (must land before or atomically with README migration)

- [ ] **Unit 1: Add `find_plugin_root()` and `validate_skill_name()` to utils.py**

  **Goal:** Enable evaluate_skill.py to locate the plugin root from any skill path. Add shared skill name validation per Anthropic spec.

  **Requirements:** R4, R10

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/utils.py`

  **Approach:**
  - `find_plugin_root(start_path)`: Walk up from `start_path`, check for `.claude-plugin/plugin.json` at each level. Stop at filesystem root or after 10 levels. Return directory containing `.claude-plugin/` or `None`.
  - `validate_skill_name(name)`: Enforce Anthropic spec — max 64 chars, regex `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, no leading/trailing hyphen. Return `(is_valid, error_message)`.
  - Follow existing `find_repo_root()` pattern

  **Patterns to follow:**
  - `find_repo_root()` in the same file (lines 10-42)
  - `PLUGIN_NAME_PATTERN` in marketplace-manager's `add_to_marketplace.py` for the name regex

  **Test scenarios:**
  - `find_plugin_root('plugins/terminal-guru/skills/zsh-dev/')` → `plugins/terminal-guru/`
  - `find_plugin_root('skills/swift-dev/')` → `None`
  - `validate_skill_name('zsh-dev')` → valid
  - `validate_skill_name('ZSH-Dev')` → invalid (uppercase)
  - `validate_skill_name('-leading-hyphen')` → invalid

  **Verification:**
  - Both functions exist, importable, and handle edge cases

- [ ] **Unit 2: Create migration script**

  **Goal:** Automate the bulk merge of skill-level README metrics into plugin-level READMEs.

  **Requirements:** R2, R3, R9

  **Dependencies:** Unit 0 (column headers must be updated first)

  **Files:**
  - Create: `plugins/skillsmith/skills/skillsmith/scripts/migrate_readme_to_plugin.py`

  **Approach:**
  - For each plugin directory found via glob `plugins/*/`:
    - Read plugin-level README.md
    - Rename `## Version History` to `## Changelog` (R9)
    - For each skill README at `skills/*/README.md` within the plugin:
      - Extract `### Current Metrics` section content (already using new compact format from Unit 0)
      - Extract `### Version History` section content (already using new column headers from Unit 0)
      - Append `## Skill: <directory-name>` section with subsections
    - Write updated plugin README
    - Report changes
  - Support `--dry-run` flag
  - PEP 723 script header (pure stdlib)

  **Test scenarios:**
  - Single-skill plugin: one `## Skill:` section appended
  - Multi-skill plugin (terminal-guru, 3 skills): three sections
  - `--dry-run` previews without writing
  - Idempotent: running twice doesn't duplicate sections

  **Verification:**
  - Plugin READMEs contain all metrics data from their skills' READMEs
  - No data loss — diff each skill README's metrics against merged output
  - `## Changelog` replaces `## Version History` in all plugin READMEs

- [ ] **Unit 3: Rework `evaluate_skill.py --update-readme` for plugin-level targeting with auto-migration**

  **Goal:** Make `--update-readme` write to plugin-level README.md, scoped to the correct `## Skill: <name>` section. Auto-detect and migrate any remaining skill-level README.md or IMPROVEMENT_PLAN.md.

  **Requirements:** R4, R4a

  **Dependencies:** Unit 1 (needs `find_plugin_root()` and `validate_skill_name()`)

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

  **Approach:**
  - In the `--update-readme` code path (lines 2934-2943):
    - Call `find_plugin_root(skill_path)` to locate plugin root
    - If `None`, print warning and skip (standalone skill)
    - Set `readme_path = plugin_root / 'README.md'`
    - Validate skill name with `validate_skill_name()`
  - **Auto-migration detection** (idempotent):
    - Before updating, check if `skill_path / 'README.md'` or `skill_path / 'IMPROVEMENT_PLAN.md'` exists
    - If found and `## Skill: <name>` does NOT exist in plugin README:
      - Extract metrics content from the skill-level file
      - Print what will be migrated, prompt for approval
      - Migrate content to plugin README as `## Skill: <name>` section
      - Delete the skill-level file
    - If `## Skill: <name>` already exists: skip migration, proceed to normal update
  - Rework `_update_current_metrics_section()`:
    - Accept `skill_name` parameter
    - Find `## Skill: <skill_name>` section in plugin README
    - Within that scope, find and replace `### Current Metrics` (note: `###` not `##`)
    - If `## Skill: <name>` not found (and no skill-level file to migrate), auto-create with fresh subsections
  - Consider using markdown parser/LSP for reliable nested heading extraction rather than fragile regex

  **Patterns to follow:**
  - Existing `_update_current_metrics_section()` regex, adapted for scoped matching
  - `_generate_metrics_content()` produces section body (now compact format from Unit 0)

  **Test scenarios:**
  - Normal update: updates `### Current Metrics` under correct `## Skill:` section
  - Multi-skill: only targeted skill section changes
  - Auto-migration: detects skill-level README, prompts, migrates, deletes original
  - Auto-migration idempotent: second run finds section exists, skips migration
  - IMPROVEMENT_PLAN.md detection: extracts and migrates
  - Standalone skill: skips with warning
  - Invalid skill name: warns

  **Verification:**
  - Plugin README `## Skill: <name>` section updates correctly
  - Skill-level README.md removed after migration
  - All other plugin README content untouched

- [ ] **Unit 4: Update `init_skill.py` to stop generating README.md**

  **Goal:** Remove README.md from the skill scaffold.

  **Requirements:** R6

  **Dependencies:** None

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/scripts/init_skill.py`

  **Approach:**
  - Remove the README generation block (lines 453-466) for standard/complete templates
  - Remove `README_TEMPLATE` constant
  - Do NOT add plugin-level README generation — `--update-readme` auto-creates sections (Unit 3)

  **Patterns to follow:**
  - Minimal template already skips README.md; extend that to all templates

  **Test scenarios:**
  - All three template types create no README.md in skill dir

  **Verification:**
  - No `README.md` in any scaffolded skill directory

### Phase 2: Migration Execution

- [ ] **Unit 5: Run migration and delete skill-level READMEs**

  **Goal:** Execute the migration script, verify results, delete skill-level READMEs.

  **Requirements:** R1, R2, R3, R9

  **Dependencies:** Unit 2 (migration script), Unit 3 (evaluate_skill.py changes must land first)

  **Files:**
  - Delete: all 11 `plugins/*/skills/*/README.md` files
  - Modify: all 7 `plugins/*/README.md` files (via migration script)

  **Approach:**
  - Git checkpoint before execution
  - Run migration script with `--dry-run`, review output
  - Run migration to merge content
  - Verify each plugin README
  - Delete all 11 skill-level READMEs
  - Run `evaluate_skill.py --update-readme` on one skill to verify end-to-end

  **Verification:**
  - `find plugins -path '*/skills/*/README.md'` returns empty
  - Each plugin README contains all historical metrics data
  - Diff confirms no data loss

### Phase 3: Documentation Updates

- [ ] **Unit 6: Rename and rewrite readme_template.md; clean up IMPROVEMENT_PLAN references**

  **Goal:** Rename `readme_template.md` → `plugin_readme_template.md`. Rewrite to document plugin-level README format. Remove IMPROVEMENT_PLAN.md references, retaining the metrics-tracking reasoning.

  **Requirements:** R7, R11

  **Dependencies:** Unit 5 (migration complete)

  **Files:**
  - Rename: `plugins/skillsmith/skills/skillsmith/references/readme_template.md` → `plugin_readme_template.md`
  - Rewrite: `plugins/skillsmith/skills/skillsmith/references/improvement_plan_best_practices.md` (remove IMPROVEMENT_PLAN format references; retain reasoning about metrics-tracked changes at plugin level)
  - Modify (path swap): `plugins/skillsmith/skills/skillsmith/references/improvement_workflow_guide.md`
  - Modify (path swap): `plugins/skillsmith/skills/skillsmith/references/integration_guide.md`
  - Modify (path swap): `plugins/skillsmith/skills/skillsmith/references/skill_creation_detailed_guide.md`
  - Modify (path swap): `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md`
  - Modify (path swap): `plugins/skillsmith/skills/skillsmith/references/testing_guide.md`

  **Approach:**
  - `plugin_readme_template.md`: Document `## Skill: <name>` format with `### Current Metrics` (compact) and `### Version History` (clear headers). Update `--update-readme` behavior to describe plugin-level targeting and auto-migration.
  - `improvement_plan_best_practices.md`: Strip IMPROVEMENT_PLAN.md format references. Keep the principle: skill changes tracked with measurable metrics at plugin level. Git history preserves the old format.
  - 5 path-swap files: replace `skills/skill-name/README.md` with plugin-level README references.

  **Verification:**
  - `rg 'IMPROVEMENT_PLAN' plugins/skillsmith/skills/skillsmith/references/` returns no matches except historical context
  - `rg 'readme_template' plugins/skillsmith/` updated to reference `plugin_readme_template`
  - `rg 'skills/.*/README\.md' plugins/skillsmith/skills/skillsmith/references/` returns no matches

- [ ] **Unit 7: Update WORKFLOW.md and project docs**

  **Goal:** Update WORKFLOW.md to reflect that README.md is now at the plugin level. Update CLAUDE.md and MEMORY.md.

  **Requirements:** R8

  **Dependencies:** Unit 5 (migration complete)

  **Files:**
  - Modify: `WORKFLOW.md` (~30 references)
  - Modify: `.claude/CLAUDE.md` (if references exist)
  - Modify: `.claude/projects/-Users-gregwilliams-Documents-Projects-claude-mp/memory/MEMORY.md`

  **Approach:**
  - WORKFLOW.md: Update to reflect evolving practices — skill metrics are now tracked in the containing plugin's README.md. Update directory structure diagram, release commit example, decision tree, release checklist. This repo is a reference implementation for marketplace-manager and skillsmith; WORKFLOW.md should model current best practices.
  - CLAUDE.md: Search for skill-level README references; update if found.
  - MEMORY.md: Update entries referencing skill-level README paths.

  **Verification:**
  - `rg 'skills/.*/README\.md' WORKFLOW.md .claude/CLAUDE.md` returns no skill-level README references

### Phase 4: Version Bump

- [ ] **Unit 8: Bump skillsmith version and run evaluation**

  **Goal:** Bump skillsmith to 6.8.0 reflecting the tooling change.

  **Requirements:** All

  **Dependencies:** Units 0-7

  **Files:**
  - Modify: `plugins/skillsmith/skills/skillsmith/SKILL.md` (version in frontmatter)
  - Modify: `plugins/skillsmith/.claude-plugin/plugin.json` (version)
  - Modify: `plugins/skillsmith/README.md` (add version history row)

  **Approach:**
  - Update `metadata.version` to `6.8.0` in SKILL.md
  - Update `version` to `6.8.0` in plugin.json
  - Run `evaluate_skill.py --update-readme` on skillsmith to verify plugin-level targeting end-to-end
  - Run `evaluate_skill.py --export-table-row --version 6.8.0` and add row to plugin README
  - Run marketplace version sync

  **Verification:**
  - `evaluate_skill.py --update-readme` updates `plugins/skillsmith/README.md` → `## Skill: skillsmith` → `### Current Metrics`
  - Marketplace versions in sync
  - Pre-commit hook passes

## System-Wide Impact

- **Interaction graph:** `evaluate_skill.py` is called by the `on-skill-edit.sh` PostToolUse hook. The hook passes the skill path — the script resolves to plugin root internally. No hook changes needed.
- **Error propagation:** If `find_plugin_root()` returns `None`, `--update-readme` skips gracefully. No silent failures. Auto-migration prompts for approval before destructive action.
- **State lifecycle risks:** Migration ordering is critical — Unit 3 must land before Unit 5. Auto-migration in `--update-readme` provides ongoing safety net for any stragglers.
- **API surface parity:** `--export-table-row` output format changes (clearer column headers). `package_skill.py` gains `validate_skill_name()` from shared utils.
- **Downstream tools:** `validate_skill_name()` in utils.py is available to both evaluate_skill.py and package_skill.py without duplication.

## Risks & Dependencies

- **Regex/parser complexity**: Scoped section replacement within `## Skill: <name>` is the highest-risk change. Consider markdown LSP or structured parser. Mitigated by testing against all 7 plugin READMEs after migration.
- **Data loss during migration**: Mitigated by `--dry-run`, diff verification, git checkpoint, and auto-migration safety net in `--update-readme`.
- **Column header migration**: Changing abbreviations in existing tables requires updating all 11 skill READMEs atomically in Unit 0 before migration. Mitigated by doing this as the first unit.
- **WORKFLOW.md churn**: ~30 references. Risk of missing some. Mitigated by grep verification.

## Sources & References

- **Origin document:** Obsidian vault `800 Generated/820 Brainstorms/2026-03-25 Migrate README to Plugin Level Requirements.md`
- Related issue: [#148](https://github.com/totallyGreg/claude-mp/issues/148)
- Related issue: [#146](https://github.com/totallyGreg/claude-mp/issues/146) (Gap 8 — Anthropic guide alignment)
- Precedent: `docs/lessons/improvement-plan-migration.md` (IMPROVEMENT_PLAN.md → README.md migration reasoning)
- Anthropic guide: "The Complete Guide to Building Skills for Claude" — "Don't include README.md inside your skill folder"
- Anthropic skill name spec: max 64 chars, `[a-z0-9-]`, no leading/trailing hyphen
