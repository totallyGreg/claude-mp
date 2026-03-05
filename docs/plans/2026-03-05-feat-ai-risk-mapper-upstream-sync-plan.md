---
title: "ai-risk-mapper: Sync with upstream changes"
type: feat
status: completed
date: 2026-03-05
issue: "#85"
---

# ai-risk-mapper: Sync with upstream changes (v5.1.0)

## Overview

The `cosai-oasis/secure-ai-tooling` upstream repository has evolved since v5.0.0 (2026-02-25). This plan covers syncing missing data files, validating persona query accuracy, fixing deprecated references, and evaluating two optional enhancements (cross-reference tables, entity-level framework mapping).

## Problem Statement / Motivation

Seven gaps exist between the plugin and upstream:
1. **3 missing YAML data files** — `actor-access.yaml`, `impact-type.yaml`, `lifecycle-stage.yaml` exist upstream but aren't bundled or fetched
2. **1 missing JSON schema** — `riskmap.schema.json` (root schema) not bundled
3. **Persona query validation needed** — upstream expanded 8-persona mappings in every control and risk entry; query methods need verification
4. **Deprecated persona in examples** — `SKILL.md` line 40 uses `personaModelCreator`
5. **Entity-level `frameworksApplicableTo`** — upstream added per-entity framework declarations
6. **Cross-reference tables** — upstream generates flat xref tables not leveraged by the plugin
7. **Stale documentation** — `workflow_guide.md` line 17 says "5 YAML + 5 schema" but actual counts are 6 + 10; `forms.md` System Profile Form still shows legacy persona labels

## Proposed Solution

Three-phase approach ordered by dependency and value:

- **Phase 1** — Quick fixes: deprecated persona example, stale doc counts, forms.md alignment, deprecation warning
- **Phase 2** — Data sync: bundle missing files, update fetch script, add root schema, create commit-hash README
- **Phase 3** — Validation & evaluation: persona query verification, evaluate frameworksApplicableTo and xref (decide YAGNI)

## Technical Considerations

### Fetch Script / Bundled Asset Symmetry

Research confirmed the current state: `YAML_FILES` has **6 entries** and `SCHEMA_FILES` has **10 entries** in `fetch_cosai_schemas.py`. After Phase 2:
- `YAML_FILES`: 6 → 9 (add `actor-access.yaml`, `impact-type.yaml`, `lifecycle-stage.yaml`)
- `SCHEMA_FILES`: 10 → 11 (add `riskmap.schema.json`)

Three failure modes exist when fetch and bundle get out of sync:

1. Fetch updated but bundled copies missing → `_fallback_to_bundled()` silently returns `False`, user gets incomplete data
2. Bundled copies added but fetch not updated → online users never download new files
3. New files bundled but no consumer in `core_analyzer.py` → dead data

**Resolution:** Update both `YAML_FILES` list and bundled assets atomically. The 3 new YAML files are **metadata enum files** — they define allowed values for `actorAccess`, `impactType`, and `lifecycleStage` fields already used by `core_analyzer.py`. They should be bundled for completeness and reference, but `core_analyzer.py` doesn't need to load them directly since the enum values are already embedded in the risk/control entries.

### Deprecated Persona Warning

Currently `get_risks_by_persona()` returns results for deprecated personas without warning. The `Persona.deprecated` field is parsed but never checked. Add a warning when a deprecated persona ID is used in `cli_persona_profile.py` (print to stderr, still return results).

### Version Tracking

**Important:** There is no `plugin.json` for this plugin. Version is tracked in `SKILL.md` frontmatter (`metadata.version`) and in `IMPROVEMENT_PLAN.md` version history. The release task updates `SKILL.md`, not a manifest file.

### self-assessment.yaml Legacy Persona Labels

`self-assessment.yaml` still uses `personaModelCreator`/`personaModelConsumer` throughout. This is **upstream CoSAI data** — not a local authoring error. Do not modify this file locally; it should be replaced wholesale when CoSAI publishes an updated version.

### Commit Hash Tracking

`assets/cosai-schemas/` has no README documenting which upstream commit the bundled files correspond to. Add `assets/cosai-schemas/README.md` during Phase 2 to record the CoSAI commit hash and sync date. This is the institutional pattern recommended in `docs/lessons/ai-risk-mapper-quick-reference.md`.

### Entity-Level frameworksApplicableTo

Upstream added `frameworksApplicableTo` at the risk/control entity level (Phase 1b). Currently `core_analyzer.py` reads framework mappings from `risk.mappings{}` dict. The new field would provide more granular compliance mapping. This needs evaluation — may be YAGNI for current usage patterns.

### Cross-Reference Tables (/arm-xref)

Upstream generates pre-built xref tables (persona-to-risk, control-to-risk, etc.). The plugin already provides these relationships via `core_analyzer.py` query methods and existing slash commands. A dedicated `/arm-xref` command would add a 7th command for a capability already accessible. **Likely YAGNI** — defer unless user demand emerges.

## Acceptance Criteria

### Phase 1: Quick Fixes

- [x] **SKILL.md line 40**: Change `personaModelCreator` → `personaModelProvider` in example
- [x] Verify all other SKILL.md examples use active persona IDs
- [x] **`workflow_guide.md`**: Update stale file counts ("5 YAML + 5 schema" → "9 YAML + 11 schema")
- [x] Review `references/exploration_guide.md` for deprecated persona references
- [x] Review `references/personas_guide.md` for deprecated persona references
- [x] Review `references/forms.md` System Profile Form — update `personas.primary_persona` comment from `ModelCreator or ModelConsumer` to reflect 8 active personas (comparison target: the local `forms.md` field comments, not upstream GitHub issue templates)
- [x] Add deprecation warning to `cli_persona_profile.py` when a deprecated persona ID is queried (print to stderr, exit 0, still return results) — scope limited to this script; `cli_gap_analysis.py` and `analyze_risks.py` persona filtering deferred to follow-up

### Phase 2: Data Sync

- [x] Download `actor-access.yaml`, `impact-type.yaml`, `lifecycle-stage.yaml` from upstream
- [x] Copy to `assets/cosai-schemas/yaml/` (bundled, total: 9 YAML files)
- [x] Download `riskmap.schema.json` from upstream
- [x] Copy to `assets/cosai-schemas/schemas/` (bundled, total: 11 schema files)
- [x] **Bundle first**: confirm all 3 YAML files and `riskmap.schema.json` are committed to `assets/cosai-schemas/` before updating the fetch script (required ordering — if fetch references files without a bundled fallback, `_fallback_to_bundled()` silently returns False)
- [x] Update `fetch_cosai_schemas.py` `YAML_FILES` list to include 3 new files (6 → 9)
- [x] Update `fetch_cosai_schemas.py` `SCHEMA_FILES` list to include `riskmap.schema.json` (10 → 11)
- [x] Create `assets/cosai-schemas/README.md` with minimum content: upstream repo URL, CoSAI commit hash, sync date, and file inventory (counts + names)
- [x] Optionally evaluate `mermaid-styles.yaml` — not bundling per YAGNI (no diagram generation planned)
- [x] Verify `_fallback_to_bundled()` works for all new files (bundled copies exist before fetch can reference them)
- [x] Run `fetch_cosai_schemas.py --force` end-to-end and verify 9 YAML + 11 schema files download

### Phase 3: Validation & Evaluation

- [x] Run `cli_persona_profile.py` for all 8 active personas (loop or manual), verify returned risks and controls reflect expanded mappings
- [x] Spot-check: compare `get_risks_for_persona("personaModelProvider")` output count against `grep -c personaModelProvider risks.yaml` — exact match (9 risks, 9 controls)
- [x] Spot-check: compare `get_controls_for_persona("personaAgenticProvider")` output count against `grep -c personaAgenticProvider controls.yaml` — exact match (7 risks, 11 controls)
- [x] **Count mismatch resolution**: no mismatches found, all counts match exactly
- [x] **Decide on enum cross-validation**: enum files align with values used in risks.yaml/controls.yaml. No drift. YAGNI — core_analyzer.py does not need to load these files.
- [x] **Decide on `frameworksApplicableTo`**: field does not exist in current upstream YAML data (0 occurrences). Deferred per YAGNI.
- [x] **Decide on `/arm-xref`**: existing commands cover all xref needs. Not needed — skipped per YAGNI.

### Release

- [x] Update `SKILL.md` `metadata.version` to `5.1.0`
- [x] Update `IMPROVEMENT_PLAN.md` with version entry and eval score (97/100)
- [x] Run skillsmith evaluation: 97/100 (up from 93 in v5.0.0)

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Upstream YAML structure changed since last check | Compare fetched files against bundled before overwriting |
| New YAML files break offline fallback if not bundled | Bundle files before updating fetch script (Phase 2 ordering) |
| Deprecated persona warning could break existing workflows | Warning goes to stderr only; results still returned |
| `frameworksApplicableTo` field may not exist in current data | Check data first, defer if absent (Phase 3 decision gate) |
| `self-assessment.yaml` legacy labels confuse contributors | Document clearly: upstream CoSAI data, do not edit locally |

## Component Scope Guide

Per plugin-dev conventions, here's where each change belongs:

| Change | Component | Scope |
|--------|-----------|-------|
| Fix deprecated persona example | **Skill** (`SKILL.md`) | Content update |
| Fix stale file counts | **Reference** (`workflow_guide.md`) | Documentation |
| Update forms.md persona field | **Reference** (`references/forms.md`) | Documentation |
| Add deprecation warning | **Script** (`cli_persona_profile.py`) | Behavior enhancement |
| Bundle new YAML/schema files | **Assets** (`assets/cosai-schemas/`) | Data update |
| Add commit hash README | **Assets** (`assets/cosai-schemas/README.md`) | Documentation |
| Update fetch script | **Script** (`fetch_cosai_schemas.py`) | File list update |
| Update exploration/personas guides | **Reference** (`references/`) | Documentation |
| Version bump | **Skill** (`SKILL.md` metadata) | Release |

No new slash commands, agents, or hooks needed. All changes are within existing plugin boundaries.

## Success Metrics

- All 8 active persona profiles return non-empty results
- Bundled assets count: 9 YAML + 11 JSON schemas
- Fetch script downloads all files successfully with `--force`
- Offline fallback works for all bundled files
- No deprecated persona IDs in `SKILL.md` examples
- `assets/cosai-schemas/README.md` exists with commit hash recorded
- Skillsmith eval score >= 93 (maintain or improve v5.0.0 score)

## Sources & References

- Issue: [#85](https://github.com/totallyGreg/claude-mp/issues/85)
- Related issues: [#22](https://github.com/totallyGreg/claude-mp/issues/22) (LLM semantic analysis), [#23](https://github.com/totallyGreg/claude-mp/issues/23) (test coverage)
- Prior plan: `docs/plans/2026-02-25-feat-cosai-upstream-data-refresh-plan.md`
- Learnings: `docs/lessons/skill-to-plugin-migration.md` (Stage 2 plugin pattern), `docs/lessons/ai-risk-mapper-quick-reference.md` (sync strategy)
- Upstream repo: `cosai-oasis/secure-ai-tooling`
- Plugin: `plugins/ai-risk-mapper/`
