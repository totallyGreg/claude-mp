---
title: "feat: Skillsmith companion agent improvements (#32, #37, #24)"
type: feat
date: 2026-02-16
---

# Skillsmith Companion Agent Improvements

## Overview

Three focused improvements to make skillsmith a better companion agent after the v5.0.0 plugin-dev alignment:

1. **#32** — "When NOT to use skillsmith" boundary guidance in SKILL.md
2. **#37** — `--explain` mode for evaluate_skill.py (per-metric + top-3 summary)
3. **#24** — Script consolidation Phases 2-3 (absorb and delete)

## Problem Statement / Motivation

- **#32**: Skillsmith triggers when users need `plugin-dev:command-development` or similar skills, leading to over-analysis of simple tasks (e.g., wrapping existing scripts as slash commands)
- **#37**: Evaluation scores are opaque — users see numbers but don't understand why or how to improve. Skillsmith should coach, not just score.
- **#24**: 7 scripts exist where 3 are needed. Deprecated/experimental scripts confuse users and inflate maintenance surface.

## Execution Order

Sequential, each as its own two-commit release:

1. **#32 first** — Small, isolated SKILL.md change. No risk.
2. **#37 second** — Additive feature to evaluate_skill.py. Stable foundation before #24 changes the file further.
3. **#24 last** — Destructive consolidation. Benefits from #37 being stable first. Also cleans up references that #37 may add to.

## Implementation Phases

### Phase 1: "When NOT to Use" Section (#32)

**Scope:** ~5 lines added to SKILL.md

**Changes:**

#### `plugins/skillsmith/skills/skillsmith/SKILL.md`

Add after the intro paragraph (line 13) and before "## About Skills" (line 16):

```markdown
## When NOT to Use Skillsmith

- **Adding commands to existing plugins** → Use `plugin-dev:command-development`
- **Plugin structure/manifest changes** → Use `plugin-dev:plugin-structure`
- **Creating hooks or agents** → Use `plugin-dev:hook-development` or `plugin-dev:agent-development`
- **Wrapping existing scripts as commands** → Commands are thin wrappers, not skills
```

**Acceptance Criteria:**

- [ ] Section is ≤8 lines
- [ ] Placed before "About Skills" as a guard clause
- [ ] All 4 redirect targets are valid plugin-dev skill names
- [ ] SKILL.md stays under 400 lines
- [ ] `uv run scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith --quick --strict` passes

**Release:**
- Commit 1: Add section to SKILL.md
- Commit 2: Bump version to 5.1.0, update IMPROVEMENT_PLAN.md with eval score

---

### Phase 2: `--explain` Mode (#37)

**Scope:** New flag in evaluate_skill.py, ~150-250 lines of additions

#### Flag Interaction Rules

| Combination | Behavior |
|---|---|
| `--explain` (alone) | Runs comprehensive + per-metric explanations + top-3 summary |
| `--explain --quick` | Warning: "explain requires comprehensive mode", ignores `--explain` |
| `--explain --format json` | Adds `"explanation"` key per dimension + `"top_improvements"` list |
| `--explain --export-table-row` | Ignored — table row mode exits before explain runs |
| `--explain --compare <path>` | Explanations reference deltas vs. original |

#### Changes:

##### `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

1. **Add `--explain` to argument parsing** (~line 1920)
   - Parse `--explain` from sys.argv (follow existing manual parsing pattern)
   - No argparse migration — extend existing pattern for consistency

2. **Add explanation templates per metric** (new function, ~100 lines)

   ```python
   def generate_explanations(metrics: dict, skill_path: Path) -> dict:
       """Generate per-metric explanation blocks.

       Returns dict mapping metric name to explanation dict with:
       - why: str (what drove the score)
       - suggestions: list[str] (what to change)
       - impact: str (estimated score improvement)
       - reference: str (relevant reference file)
       """
   ```

   Each metric's explanation uses the sub-metrics already returned by scoring functions:
   - **Conciseness**: `line_score`, `token_score`, `reference_bonus` → identify which sections to move to references
   - **Complexity**: heading depth, section count → identify overly nested sections
   - **Spec compliance**: violations list, warnings list → list each violation with fix
   - **Progressive disclosure**: reference/script/asset counts → suggest what to add
   - **Description quality**: trigger phrase count, format check → suggest specific trigger phrases

3. **Add top-3 improvements ranking** (new function, ~50 lines)

   ```python
   def rank_improvements(explanations: dict, current_scores: dict) -> list[dict]:
       """Rank top 3 improvements by weighted score deficit.

       Uses: (max_score - current_score) * metric_weight
       Returns list of {metric, suggestion, estimated_gain}
       """
   ```

   Ranking algorithm: For each sub-metric, compute `(max - current) * dimension_weight`. Sort descending. Take top 3. Estimate gain from the scoring tier thresholds already in the code.

4. **Integrate into text output** (~line 1755 in `print_evaluation_text()`)

   After each metric's score bar, print explanation block:

   ```
   Conciseness:     [██████████████░░░░░░] 56/100

     Why: SKILL.md is 392 lines (target: <300 for bonus, <200 for max)

     To improve:
     - Move "Common Mistakes" section → references/ (~55 lines, est. +8 pts)
     - Move "Quick Reference" section → references/ (~75 lines, est. +12 pts)

     See: references/progressive_disclosure_discipline.md
   ```

   After all metrics, print top-3 summary:

   ```
   ━━━ Top 3 Improvements ━━━
   1. Move 2 sections to references/ → est. conciseness 56 → 76 (+20)
   2. Add 2 trigger phrases to description → est. description 80 → 90 (+10)
   3. Add examples/ directory → est. spec compliance 70 → 75 (+5)

   Estimated overall: 85 → 91
   ```

5. **Integrate into JSON output** (in `--format json` handler)

   Add `"explanation"` key to each dimension dict and `"top_improvements"` at top level.

##### `plugins/skillsmith/commands/ss-evaluate.md`

Update examples to include `--explain`:

```
/ss-evaluate skills/my-skill --explain
```

##### `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md`

Document `--explain` flag with examples.

##### `plugins/skillsmith/skills/skillsmith/tests/test_evaluate_skill.py`

Add tests:
- [ ] `--explain` produces explanation blocks for each metric
- [ ] `--explain --quick` prints warning and ignores explain
- [ ] `generate_explanations()` returns correct structure
- [ ] `rank_improvements()` returns sorted top-3

**Acceptance Criteria:**

- [ ] `--explain` produces per-metric explanation with why/suggestions/impact
- [ ] Top-3 summary appears at end with estimated score improvements
- [ ] `--explain --quick` gracefully degrades with warning
- [ ] `--explain --format json` includes explanations in JSON
- [ ] No regressions: existing flags work unchanged
- [ ] `uv run scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith --quick --strict` passes

**Release:**
- Commit 1: Implementation + tests
- Commit 2: Bump version to 5.2.0, update IMPROVEMENT_PLAN.md with eval score

---

### Phase 3: Script Consolidation (#24)

**Scope:** Absorb 2 functions into evaluate_skill.py, delete 4 scripts, update references

#### Phase 3a: Absorb update_references.py into evaluate_skill.py

##### `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

1. **Add `--validate-references` flag** (~line 1920)
   - Absorbs full `validate_references_structure()` from update_references.py:
     - Nested subdirectory detection (spec violation)
     - File readability checks
     - Large file warnings (>100KB)
   - Also absorbs orphaned-reference detection (the default mode of update_references.py — `validate_reference_mentions()`) since this is the most-used feature
   - Runs automatically in comprehensive mode (no flag needed); `--validate-references` runs it standalone

2. **Add `--detect-duplicates` flag** (~line 1920)
   - Absorbs `detect_similar_references()` from update_references.py
   - Jaccard similarity for consolidation opportunities
   - Opt-in only (computationally expensive)

3. **Adapt imports** — strip argparse dependency from absorbed code; use existing sys.argv pattern

##### `plugins/skillsmith/skills/skillsmith/tests/test_evaluate_skill.py`

Add tests:
- [ ] `--validate-references` detects nested subdirectories
- [ ] `--validate-references` detects orphaned reference files
- [ ] `--validate-references` warns on large files
- [ ] `--detect-duplicates` finds similar reference files

#### Phase 3b: Delete deprecated/experimental scripts

| Script to Delete | Lines | Status |
|---|---|---|
| `validate_workflow.py` | 260 | DEPRECATED since v3.7.2 |
| `audit_improvements.py` | 354 | DEPRECATED since v3.7.2 |
| `update_references.py` | 444 | Absorbed in Phase 3a |
| `research_skill.py` | ~30 | EXPERIMENTAL, 40% complete, no users |

**Final scripts inventory:**
```
scripts/
├── evaluate_skill.py    # Unified validation/evaluation/explanation
├── init_skill.py        # Skill scaffolding
└── utils.py             # Shared utilities (used by init_skill.py)
```

#### Phase 3c: Delete ss-research command

Delete `plugins/skillsmith/commands/ss-research.md` — research_skill.py no longer exists.

#### Phase 3d: Update references to deleted scripts

##### `plugins/skillsmith/skills/skillsmith/references/validation_tools_guide.md`

- Remove `research_skill.py` documentation
- Remove deprecated script listings
- Remove `update_references.py` command documentation
- Update command mapping to reflect final 3-script inventory

##### `plugins/skillsmith/skills/skillsmith/references/research_guide.md`

- Remove `research_skill.py` references
- Refocus on evaluate_skill.py as the primary analysis tool
- If file becomes empty/vestigial, delete it entirely

##### `plugins/skillsmith/skills/skillsmith/SKILL.md`

- Remove reference to `research_guide.md` at line 371 (if file is deleted)
- Verify all Advanced Topics references still point to existing files

**Acceptance Criteria:**

- [ ] `--validate-references` detects nested subdirs, orphaned files, large files
- [ ] `--detect-duplicates` finds similar reference files (opt-in)
- [ ] Comprehensive mode includes reference validation automatically
- [ ] Only 3 scripts remain: evaluate_skill.py, init_skill.py, utils.py
- [ ] ss-research command deleted
- [ ] No dangling references to deleted scripts in any reference file or SKILL.md
- [ ] All existing tests pass
- [ ] New tests cover absorbed functions
- [ ] `uv run scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith --quick --strict` passes

**Release:**
- Commit 1: Absorb functions, delete scripts, update references
- Commit 2: Bump version to 5.3.0, update IMPROVEMENT_PLAN.md with eval score

---

## Technical Considerations

### Argument Parsing

evaluate_skill.py uses manual `sys.argv` parsing (not argparse). This work adds 3 new flags (`--explain`, `--validate-references`, `--detect-duplicates`), growing the parsing block from ~15 to ~18 branches. Migration to argparse is explicitly **out of scope** — extend the existing pattern for consistency. Note as tech debt for a future cleanup.

### Bootstrap Problem

For Phase 3, evaluate_skill.py is both the tool being modified and the validation tool required before committing. Mitigate by:
1. Running evaluation with `--quick --strict` before starting destructive changes
2. Ensuring evaluate_skill.py is functional at each intermediate step
3. Running final evaluation after all changes are complete

### SKILL.md Line Budget

Current: ~392 lines. Phase 1 adds ~6 lines (→ ~398). Phases 2-3 may remove a reference line if research_guide.md is deleted (→ ~397). Well within the 500-line limit.

## Dependencies & Risks

| Risk | Mitigation |
|---|---|
| #37 and #24 both modify evaluate_skill.py | Sequential execution: #37 first, #24 second |
| Deleted scripts referenced in docs | Phase 3d explicitly updates all references |
| `--explain` estimates could be misleading | Use conservative estimates based on tier thresholds already in code |
| utils.py becomes orphaned | Verified: only imported by init_skill.py, stays |

## Success Metrics

- Skillsmith overall eval score stays ≥85 across all 3 releases
- `--explain` output is actionable (test with 3+ real skills)
- Script count drops from 7 → 3
- No user-facing breakage (existing flags, commands, and workflows unchanged)

## References

- Brainstorm: `docs/brainstorms/2026-02-16-skillsmith-companion-agent-priorities-brainstorm.md`
- Issue #32: <https://github.com/totallyGreg/claude-mp/issues/32>
- Issue #37: <https://github.com/totallyGreg/claude-mp/issues/37>
- Issue #24: <https://github.com/totallyGreg/claude-mp/issues/24>
- evaluate_skill.py: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`
- update_references.py: `plugins/skillsmith/skills/skillsmith/scripts/update_references.py`
- WORKFLOW.md: `/WORKFLOW.md` (two-commit release strategy)
