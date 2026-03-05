---
title: "ai-risk-mapper: Sync with upstream changes"
type: feat
status: active
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
4. **Deprecated persona in examples** — SKILL.md line 40 uses `personaModelCreator`
5. **Entity-level `frameworksApplicableTo`** — upstream added per-entity framework declarations
6. **Cross-reference tables** — upstream generates flat xref tables not leveraged by the plugin
7. **forms.md alignment** — upstream issue templates define canonical fields

## Proposed Solution

Three-phase approach ordered by dependency and value:

- **Phase 1** — Quick fixes: deprecated persona example, forms.md alignment
- **Phase 2** — Data sync: bundle missing files, update fetch script, add root schema
- **Phase 3** — Validation & evaluation: persona query verification, evaluate frameworksApplicableTo and xref (decide YAGNI)

## Technical Considerations

### Fetch Script / Bundled Asset Symmetry

The SpecFlow analysis identified **3 failure modes** when fetch and bundle get out of sync:

1. Fetch updated but bundled copies missing → `_fallback_to_bundled()` silently returns `False`, user gets incomplete data
2. Bundled copies added but fetch not updated → online users never download new files
3. New files bundled but no consumer in `core_analyzer.py` → dead data

**Resolution:** Update both `YAML_FILES` list and bundled assets atomically. For the 3 new YAML files, these are **metadata enum files** — they define allowed values for `actorAccess`, `impactType`, and `lifecycleStage` fields already used by `core_analyzer.py`. They should be bundled for completeness and reference, but `core_analyzer.py` doesn't need to load them directly since the enum values are already embedded in the risk/control entries.

### Deprecated Persona Warning

Currently `get_risks_by_persona()` returns results for deprecated personas without warning. The `Persona.deprecated` field is parsed but never checked. Consider adding a warning when a deprecated persona ID is used in `cli_persona_profile.py`.

### Entity-Level frameworksApplicableTo

Upstream added `frameworksApplicableTo` at the risk/control entity level (Phase 1b). Currently `core_analyzer.py` reads framework mappings from `risk.mappings{}` dict. The new field would provide more granular compliance mapping. This needs evaluation — may be YAGNI for current usage patterns.

### Cross-Reference Tables (/arm-xref)

Upstream generates pre-built xref tables (persona-to-risk, control-to-risk, etc.). The plugin already provides these relationships via `core_analyzer.py` query methods and existing slash commands. A dedicated `/arm-xref` command would add a 7th command for a capability already accessible. **Likely YAGNI** — defer unless user demand emerges.

## Acceptance Criteria

### Phase 1: Quick Fixes

- [ ] **SKILL.md line 40**: Change `personaModelCreator` → `personaModelProvider` in example
- [ ] Verify all other SKILL.md examples use active persona IDs
- [ ] Review `references/exploration_guide.md` for deprecated persona references
- [ ] Review `references/personas_guide.md` for deprecated persona references
- [ ] Review `references/forms.md` against upstream issue templates; update field definitions if misaligned
- [ ] Add deprecation warning to `cli_persona_profile.py` when a deprecated persona ID is queried (print to stderr, still return results)

### Phase 2: Data Sync

- [ ] Download `actor-access.yaml`, `impact-type.yaml`, `lifecycle-stage.yaml` from upstream
- [ ] Copy to `assets/cosai-schemas/yaml/` (bundled)
- [ ] Download `riskmap.schema.json` from upstream
- [ ] Copy to `assets/cosai-schemas/schemas/` (bundled)
- [ ] Update `fetch_cosai_schemas.py` `YAML_FILES` list to include 3 new files (total: 9)
- [ ] Update `fetch_cosai_schemas.py` `SCHEMA_FILES` list to include `riskmap.schema.json` (total: 11)
- [ ] Optionally evaluate `mermaid-styles.yaml` — bundle only if diagram generation is planned
- [ ] Verify `_fallback_to_bundled()` works for all new files (bundled copies exist before fetch can reference them)
- [ ] Run `fetch_cosai_schemas.py --force` end-to-end and verify 9 YAML + 11 schema files download

### Phase 3: Validation & Evaluation

- [ ] Run `cli_persona_profile.py` for all 8 active personas, verify returned risks and controls reflect expanded mappings
- [ ] Spot-check: compare `get_risks_for_persona("personaModelProvider")` output count against `grep -c personaModelProvider risks.yaml`
- [ ] Spot-check: compare `get_controls_for_persona("personaAgenticProvider")` output count against `grep -c personaAgenticProvider controls.yaml`
- [ ] **Decide on `frameworksApplicableTo`**: Check if any risk/control entries in current YAML actually contain this field. If not present in data yet, defer (YAGNI). If present, evaluate whether `get_framework_mappings()` should also read it.
- [ ] **Decide on `/arm-xref`**: Review whether existing commands already cover xref needs. If so, document as "not needed" and close that sub-item.

### Release

- [ ] Update `plugin.json` version to `5.1.0`
- [ ] Update `IMPROVEMENT_PLAN.md` with version entry and eval score
- [ ] Run skillsmith evaluation: `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/ai-risk-mapper/skills/ai-risk-mapper`

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Upstream YAML structure changed since last check | Compare fetched files against bundled before overwriting |
| New YAML files break offline fallback if not bundled | Bundle files before updating fetch script (Phase 2 ordering) |
| Deprecated persona warning could break existing workflows | Warning goes to stderr only; results still returned |
| `frameworksApplicableTo` field may not exist in current data | Check data first, defer if absent (Phase 3 decision gate) |

## Component Scope Guide

Per plugin-dev conventions, here's where each change belongs:

| Change | Component | Scope |
|--------|-----------|-------|
| Fix deprecated persona example | **Skill** (SKILL.md) | Content update |
| Add deprecation warning | **Script** (cli_persona_profile.py) | Behavior enhancement |
| Bundle new YAML/schema files | **Assets** (assets/cosai-schemas/) | Data update |
| Update fetch script | **Script** (fetch_cosai_schemas.py) | File list update |
| Update forms.md | **Reference** (references/forms.md) | Documentation |
| Update exploration/personas guides | **Reference** (references/) | Documentation |
| Version bump | **Manifest** (plugin.json) | Release |

No new slash commands, agents, or hooks needed. All changes are within existing plugin boundaries.

## Success Metrics

- All 8 active persona profiles return non-empty results
- Bundled assets count: 9 YAML + 11 JSON schemas
- Fetch script downloads all files successfully with `--force`
- Offline fallback works for all bundled files
- No deprecated persona IDs in SKILL.md examples
- Skillsmith eval score >= 93 (maintain or improve v5.0.0 score)

## Sources & References

- Issue: [#85](https://github.com/totallyGreg/claude-mp/issues/85)
- Related issues: [#22](https://github.com/totallyGreg/claude-mp/issues/22) (LLM semantic analysis), [#23](https://github.com/totallyGreg/claude-mp/issues/23) (test coverage)
- Prior plan: `docs/plans/2026-02-25-feat-cosai-upstream-data-refresh-plan.md`
- Learnings: `docs/lessons/skill-to-plugin-migration.md` (Stage 2 plugin pattern)
- Upstream repo: `cosai-oasis/secure-ai-tooling`
- Plugin: `plugins/ai-risk-mapper/`
