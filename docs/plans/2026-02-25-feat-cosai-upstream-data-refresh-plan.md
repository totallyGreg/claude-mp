---
title: "feat: Refresh ai-risk-mapper CoSAI upstream data (8-persona model, taxonomy fixes, bug fixes)"
type: feat
date: 2026-02-25
plugin: ai-risk-mapper
target_version: 5.0.0
---

# Refresh ai-risk-mapper CoSAI Upstream Data

## Overview

The ai-risk-mapper plugin (v4.0.1) bundles CoSAI Risk Map data that is now significantly behind the upstream `cosai-oasis/secure-ai-tooling` repository. Three major upstream changes need to be incorporated:

1. **8-Persona Model** (Feb 2026) — expanded from 2 to 8 personas aligned with ISO 22989
2. **Risk & Control Taxonomy Changes** (Nov 2025) — new controls, risk renames, privacy control splits
3. **Framework Validation Tooling** (Nov 2025) — `frameworks.yaml` added as formal data file

Additionally, the research phase uncovered two parsing bugs and a fabricated exploration guide that need fixing.

## Problem Statement

- Bundled `personas.yaml` has 2 personas; upstream has 8 (old 2 are deprecated)
- Bundled schemas are missing 6 files (`frameworks.yaml`, 5 JSON schemas)
- `core_analyzer.py` has two YAML key mismatches causing silent data loss:
  - `lifecycleStages` vs actual key `lifecycleStage` → lifecycle filtering always returns `[]`
  - `impactTypes` vs actual key `impactType` → severity inference always returns "Medium"
- `exploration_guide.md` risk ID table contains entirely fabricated IDs (none match actual YAML)
- 9 files have hardcoded 2-persona references that will break with the new model

## Proposed Solution

A phased approach: fix bugs first, then refresh data, then update documentation.

**Version bump rationale:** MAJOR (5.0.0) — the persona model change is breaking for any user referencing `personaModelCreator`/`personaModelConsumer` (now deprecated).

## Phase 1: Bug Fixes (No data changes)

Fix existing bugs independent of the data refresh.

### 1.1 Fix YAML key mismatches in `core_analyzer.py`

**File:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/core_analyzer.py`

- [ ] Line 186: Change `risk_data.get("lifecycleStages", [])` → `risk_data.get("lifecycleStage", [])`
- [ ] Line 187: Change `risk_data.get("impactTypes", [])` → `risk_data.get("impactType", [])`
- [ ] Verify `export_risk_as_dict()` (line 809) keeps Python-side attribute names unchanged (`lifecycle_stages`, `impact_types`) for backward compat — only the YAML key parsing changes

### 1.2 Add `deprecated` field to `Persona` dataclass

**File:** `core_analyzer.py`

- [ ] Add `deprecated: bool = False` to `Persona` dataclass
- [ ] Update `_load_personas()` to read `persona_data.get("deprecated", False)`

### 1.3 Fix IMPROVEMENT_PLAN.md stale reference

**File:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/IMPROVEMENT_PLAN.md`

- [ ] Line 19: Change `#4` → `#22` (semantic risk detection issue)

## Phase 2: Data Refresh

Replace bundled CoSAI data with upstream versions.

### 2.1 Update fetch script file lists

**File:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/fetch_cosai_schemas.py`

- [ ] Add `frameworks.yaml` to `YAML_FILES` list
- [ ] Add to `SCHEMA_FILES`: `frameworks.schema.json`, `actor-access.schema.json`, `impact-type.schema.json`, `lifecycle-stage.schema.json`, `mermaid-styles.schema.json`

### 2.2 Fetch and bundle latest upstream data

- [ ] Run `fetch_cosai_schemas.py --force` to download latest from upstream
- [ ] Copy fetched files to `assets/cosai-schemas/yaml/` and `assets/cosai-schemas/schemas/`
- [ ] Verify all 6 YAML files present (components, controls, frameworks, personas, risks, self-assessment)
- [ ] Verify all 10 JSON schema files present
- [ ] Validate: new `personas.yaml` has 8 personas with `deprecated` flags on old 2

### 2.3 Update hardcoded persona references (9 files)

| File | Change Needed |
|------|---------------|
| `scripts/analyze_risks.py` (~line 258) | Update `choices=["ModelCreator", "ModelConsumer"]` to include all 8 |
| `scripts/orchestrate_risk_assessment.py` (~line 209) | Update help text persona list |
| `scripts/cli_persona_profile.py` | Update help text / error message persona list |
| `commands/arm-persona-profile.md` | Add 6 new persona options |
| `assets/cosai-schemas/schemas/personas.schema.json` | Updated via upstream fetch (Phase 2.2) |
| `skills/ai-risk-mapper/SKILL.md` (~line 76) | Update `--persona` options |
| `references/exploration_guide.md` (~lines 39-43) | Update persona table (Phase 3) |
| `references/cosai_overview.md` (~line 64) | Update "Personas (2 defined)" → 8 |
| `references/schemas_reference.md` (~lines 113-126) | Update persona descriptions |

**Approach for `analyze_risks.py` persona choices:** Rather than hardcoding 8 names, consider dynamically loading persona IDs from the YAML. This prevents future hardcoding drift.

## Phase 3: Documentation Refresh

### 3.1 Rewrite `exploration_guide.md` risk ID table

**File:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/exploration_guide.md`

- [ ] Replace fabricated risk IDs (lines 9-37) with actual IDs from `risks.yaml`
- [ ] Update persona table (lines 39-43) to list all 8 personas
- [ ] Verify all example commands use valid IDs

### 3.2 Rewrite `personas_guide.md`

**File:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/references/personas_guide.md`

- [ ] Restructure from 2 personas to 8
- [ ] Include ISO 22989 mappings, responsibilities, identification questions from upstream data
- [ ] Mark `personaModelCreator` and `personaModelConsumer` as deprecated with migration guidance
- [ ] Update organizational examples for new persona model

### 3.3 Update `cosai_overview.md` and `schemas_reference.md`

- [ ] Update persona counts and descriptions
- [ ] Add `frameworks.yaml` to schema reference
- [ ] Update any risk/control counts if changed

## Phase 4: Validation & Release

### 4.1 Manual smoke testing

- [ ] `cli_persona_profile.py personaModelProvider --offline` → returns valid profile
- [ ] `cli_persona_profile.py personaModelCreator --offline` → shows deprecated notice
- [ ] `cli_risk_search.py injection --offline` → returns matching risks
- [ ] `cli_controls_for_risk.py DP --offline` → returns controls
- [ ] `cli_gap_analysis.py DP --offline` → returns gap assessment
- [ ] `cli_framework_map.py DP --framework mitre-atlas --offline` → returns mappings
- [ ] `orchestrate_risk_assessment.py --target "LLM chatbot" --output-dir /tmp/test-assessment` → completes successfully
- [ ] Verify lifecycle filtering works: `analyze_risks.py` with `--lifecycle` flag returns non-empty results

### 4.2 Skillsmith evaluation

- [ ] Run `uv run plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py plugins/ai-risk-mapper/skills/ai-risk-mapper`
- [ ] Record score in IMPROVEMENT_PLAN.md

### 4.3 Release (two-commit strategy)

**Commit 1 — Implementation:**
```
feat(ai-risk-mapper): Refresh CoSAI data to 8-persona model (#XX)
```

**Commit 2 — Release:**
```
chore: Release ai-risk-mapper v5.0.0

Closes #XX
```

## Acceptance Criteria

- [ ] 8 personas load correctly from bundled YAML (offline mode)
- [ ] Deprecated personas (`personaModelCreator`, `personaModelConsumer`) are marked as such
- [ ] Lifecycle stage filtering returns non-empty results for risks that have lifecycle data
- [ ] Impact type filtering returns non-empty results (severity inference no longer always "Medium")
- [ ] All 6 CLI commands work with new persona IDs
- [ ] `exploration_guide.md` risk IDs match actual `risks.yaml` content
- [ ] `frameworks.yaml` is bundled and fetched
- [ ] No hardcoded 2-persona references remain

## Out of Scope (Deferred)

| Item | Issue | Rationale |
|------|-------|-----------|
| LLM semantic analysis | #22 | Orthogonal feature, separate effort |
| Test coverage & troubleshooting docs | #23 | Separate issue; basic smoke tests included here |
| `actorAccess` field parsing | — | YAGNI until user demand |
| New `self.frameworks` query methods | — | YAGNI; data loaded but no user flow requires it yet |
| `search_all()` adding personas | — | Nice-to-have, not blocking |
| Dynamic persona choices in `analyze_risks.py` | — | Recommended but can be a follow-up if scope grows |

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Upstream YAML structure may have changed beyond what we expect | Fetch first, inspect, then update code |
| Control-persona mappings may still reference only old 2 persona IDs | Verify upstream controls.yaml has remapped personas; if not, document limitation |
| Breaking change for users referencing old persona IDs | MAJOR version bump; document deprecation in IMPROVEMENT_PLAN |

## References

### Internal
- `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/core_analyzer.py` — main analyzer
- `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/fetch_cosai_schemas.py` — schema fetcher
- `docs/lessons/ai-risk-mapper-quick-reference.md` — prior gap analysis
- `WORKFLOW.md` — two-commit release strategy

### External
- [CoSAI secure-ai-tooling repo](https://github.com/cosai-oasis/secure-ai-tooling)
- [8-Persona PRs](https://github.com/cosai-oasis/secure-ai-tooling/pull/128) — #128, #131, #140, #142, #146
- [Content updates PR #101](https://github.com/cosai-oasis/secure-ai-tooling/pull/101) — Nov 2025 risk/control changes
- [Framework validation PRs](https://github.com/cosai-oasis/secure-ai-tooling/pull/94) — #94, #99, #105
