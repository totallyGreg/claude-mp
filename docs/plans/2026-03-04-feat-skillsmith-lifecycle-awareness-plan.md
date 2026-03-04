---
title: "feat: Skillsmith Lifecycle-Aware Skill Management"
type: feat
status: active
date: 2026-03-04
origin: docs/brainstorms/2026-03-04-skillsmith-lifecycle-awareness-brainstorm.md
---

# Skillsmith: Lifecycle-Aware Skill Management

## Overview

Evolve Skillsmith from a skill evaluator into a lifecycle-aware companion that detects when skills have outgrown their structure and suggests graduation to plugin architecture, handing off to the appropriate plugin-dev skills. Ships incrementally across four phases: v5.2.1 (bugs) → v5.3.0 (consolidation) → v5.4.0 (explain) → v6.0.0 (graduation).

(See brainstorm: `docs/brainstorms/2026-03-04-skillsmith-lifecycle-awareness-brainstorm.md`)

## Problem Statement

Skillsmith treats every skill as an isolated artifact. It validates structure and scores quality but has no awareness that a skill with many scripts, large reference sets, or complex tooling has outgrown the "skill" structure and should graduate to a plugin. The existing "When NOT to use" section (v5.1.0) is a static redirect — what's needed is dynamic, data-driven detection with actionable suggestions aligned to the plugin-dev skill ecosystem.

## Proposed Solution

Build graduation awareness incrementally on the existing evaluate_skill.py architecture:

1. **Fix existing bugs** that undermine trust in evaluation output
2. **Consolidate scripts** to simplify the tool surface before adding features
3. **Add --explain mode** to transform the evaluator from a scorecard into a coach
4. **Add graduation signal detection** with context awareness and a maturity model decision tree in SKILL.md

Key design decisions (from brainstorm):
- **Deterministic only** — no LLM-as-judge; Claude is the semantic judge when it reads skills
- **3 measurable signals** — script count, script complexity, reference sprawl
- **Context-aware** — distinguish standalone skills from plugin-bundled skills to avoid false positives

## Technical Considerations

### Self-Referential Paradox (Critical — from SpecFlow Analysis)

Skillsmith's own skill has 11 reference files (148KB) and evaluate_skill.py is 2160 lines. After Phase 4, evaluating skillsmith would trigger all graduation signals. Since CLAUDE.md mandates evaluation before every commit, this would produce noise on every skillsmith change.

**Resolution**: Graduation signals must be **context-aware**. Walk upward from the skill directory looking for a `.claude-plugin/plugin.json` file in any ancestor directory. If found, the skill is already bundled in a plugin. Signals are reframed as "structural notes" rather than graduation suggestions.

```python
def is_plugin_bundled(skill_path):
    """Walk up from skill directory to find .claude-plugin/plugin.json."""
    current = os.path.dirname(os.path.abspath(skill_path))
    for _ in range(5):  # max 5 levels up to avoid infinite walk
        candidate = os.path.join(current, '.claude-plugin', 'plugin.json')
        if os.path.isfile(candidate):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return False
```

### Two Orphan Detection Code Paths (#82)

evaluate_skill.py has TWO separate orphan detection paths:
1. `validate_file_references()` at ~line 1095 — regex with backtick-only matching
2. Unnamed check at ~line 1372-1387 — string containment for backtick and bare paths

Both miss markdown link syntax `[text](references/file.md)`. The fix must address BOTH code paths.

### evaluate_skill.py Growth

The script will grow ~40% across all phases (2160 → ~2900 lines). This is accepted technical debt given the "no argparse migration" constraint. Mitigations:
- Extract scoring functions into clearly delimited sections with comment headers (already the pattern)
- Each new capability gets its own function, not inline logic
- Track line count in IMPROVEMENT_PLAN.md as a known metric

### Graduation Signals Are Informational, Not Scoring

Graduation signals do NOT affect the evaluation score. A skill can score 95/100 and still have graduation signals. They appear as a separate section after scoring in normal mode, with expanded explanations in `--explain` mode.

### Flag Interaction Matrix (Post-Phase 3)

| Flag Combo | Behavior |
|------------|----------|
| `--explain` | Comprehensive + per-metric explanations + graduation signals + top-3 summary |
| `--explain --quick` | Warning: "explain requires comprehensive mode", ignores --explain |
| `--explain --format json` | Adds `"explanation"` and `"graduation_signals"` keys |
| `--explain --export-table-row` | Ignored — table row mode exits before explain |
| `--explain --compare` | Explanations reference deltas vs. original |
| `--validate-references` | Standalone reference validation (from Phase 2 absorption) |
| `--detect-duplicates` | Opt-in similarity detection (from Phase 2 absorption) |
| Normal comprehensive | Includes reference validation automatically + graduation signals as brief one-liners |

## Acceptance Criteria

### Phase 1: Bug Fixes (v5.2.1)

- [ ] #82: `validate_file_references()` and the unnamed check (~line 1372) both parse `[text](references/file.md)` markdown link syntax
- [ ] #82: Existing backtick and bare-path detection remains functional
- [ ] #82: Test with omnifocus-manager skill (the skill that originally exposed the bug)
- [ ] #81: SKILL.md Step 6 distinguishes three evaluation contexts:
  - During development iteration: `--quick`
  - Before each commit: full evaluation (no flags)
  - Pre-release gate: `--quick --strict`
- [ ] #81: `references/validation_tools_guide.md` updated to match
- [ ] Evaluation passes: `uv run scripts/evaluate_skill.py plugins/skillsmith/skills/skillsmith --quick --strict`
- [ ] IMPROVEMENT_PLAN.md updated with v5.2.1 entry and eval scores

### Phase 2: Script Consolidation (v5.3.0, #24)

- [ ] `--validate-references` flag absorbs `update_references.py` validation logic
- [ ] `--detect-duplicates` flag absorbs similarity checking (opt-in)
- [ ] Comprehensive mode includes reference validation automatically
- [ ] Delete: `validate_workflow.py`, `audit_improvements.py`, `update_references.py`, `research_skill.py`
- [ ] Delete: `commands/ss-research.md`
- [ ] Update: `references/validation_tools_guide.md` — remove deleted script docs
- [ ] Delete or update: `references/research_guide.md` — remove if vestigial
- [ ] Verify: No dangling references to deleted scripts in SKILL.md or any reference file
- [ ] Verify: CLAUDE.md and WORKFLOW.md have no references to deleted scripts
- [ ] Final inventory: `evaluate_skill.py`, `init_skill.py`, `utils.py` only

### Phase 3: Explain Mode (v5.4.0, #37)

- [ ] `--explain` produces per-metric explanation with why/suggestions/impact
- [ ] Top-3 improvement summary at end with estimated score improvements
- [ ] Flag interactions work per matrix above
- [ ] JSON output includes `"explanation"` key per dimension + `"top_improvements"` list
- [ ] Reserve `"graduation_signals"` key in JSON schema (empty for now, populated in Phase 4)
- [ ] No regressions: existing flags work unchanged

### Phase 4: Graduation Awareness (v6.0.0)

- [ ] Three graduation signals detected:
  - Script count >3 → suggest plugin-dev:plugin-structure
  - Script complexity >500 lines → suggest splitting or extracting
  - Reference sprawl >10 files OR >50KB total → suggest plugin-level documentation
- [ ] Context-aware: walk ancestors for `.claude-plugin/plugin.json` — if found, reframe as structural notes, not graduation suggestions
- [ ] Graduation signals appear as separate section after scoring in comprehensive mode
- [ ] `--explain` expands signals with rationale and action items
- [ ] `--format json` includes `"graduation_signals"` array
- [ ] Skill Maturity Model decision tree added to SKILL.md (after "When NOT to Use" section)
- [ ] Decision tree references plugin-dev skills: plugin-structure, command-development, hook-development, agent-development, mcp-integration
- [ ] "When NOT to Use" section updated with a one-line reference to the maturity model ("For skills that are growing complex, see Skill Maturity Model below"). The two sections remain separate: "When NOT to Use" handles wrong-tool routing; "Skill Maturity Model" handles right-tool-but-outgrowing-it guidance.
- [ ] Follows plugin-dev conventions: third-person description, imperative writing, `${CLAUDE_PLUGIN_ROOT}` for paths

## Implementation Phases

### Phase 1: Bug Fixes (v5.2.1)

**Files changed:**
- `scripts/evaluate_skill.py` — fix both orphan detection code paths for markdown link syntax
- `SKILL.md` — update Step 6 iteration workflow with three-context evaluation table
- `references/validation_tools_guide.md` — align with Step 6 changes

**Approach for #82:**
Add regex pattern `r'\[.*?\]\(references/([a-z0-9_.-]+\.md)\)'` to both detection paths. Test against known false positives documented in `docs/lessons/evaluate-skill-false-positives.md`.

**Approach for #81:**
Replace Step 6's current "run `--quick --strict` before committing" with a clear table:

```
| Context                          | Command                                    |
|----------------------------------|--------------------------------------------|
| During development iteration     | `--quick`                                  |
| Before each commit               | Full evaluation (no flags)                 |
| Pre-release / CI gate            | `--quick --strict`                         |
| Version bump with metrics export | `--export-table-row --version X.Y.Z`       |
```

**Release:**
- Commit 1: `fix(skillsmith): fix orphan detection for markdown links (#82)`
- Commit 2: `fix(skillsmith): mandate full evaluation before commits (#81)`
- Commit 3: `chore: Release skillsmith v5.2.1`

### Phase 2: Script Consolidation (v5.3.0, #24)

**Files changed:**
- `scripts/evaluate_skill.py` — absorb reference validation and duplicate detection
- `scripts/validate_workflow.py` — DELETE
- `scripts/audit_improvements.py` — DELETE
- `scripts/update_references.py` — DELETE
- `scripts/research_skill.py` — DELETE
- `commands/ss-research.md` — DELETE
- `references/validation_tools_guide.md` — update to reflect 3-script inventory
- `references/research_guide.md` — DELETE if vestigial
- `SKILL.md` — remove any references to deleted files/commands

**Prerequisite check:** Verify no external references to deleted scripts in CLAUDE.md, WORKFLOW.md, or other skills.

**Release:**
- Commit 1: `feat(skillsmith): complete script consolidation (#24)`
- Commit 2: `chore: Release skillsmith v5.3.0`

### Phase 3: Explain Mode (v5.4.0, #37)

Follow the detailed plan in [GitHub Issue #37](https://github.com/totallyGreg/claude-mp/issues/37). Key additions beyond the existing plan:

- Reserve `"graduation_signals"` key in JSON schema (returns empty array until Phase 4)
- Include reference validation explanations if Phase 2 has already landed

**Release:**
- Commit 1: `feat(skillsmith): add --explain mode to evaluate_skill.py (#37)`
- Commit 2: `chore: Release skillsmith v5.4.0`

### Phase 4: Graduation Awareness (v6.0.0)

**Files changed:**
- `scripts/evaluate_skill.py`:
  - New function: `detect_graduation_signals(skill_path, basic_metrics)` returning list of signal dicts
  - Context detection: `is_plugin_bundled(skill_path)` checking for `../../.claude-plugin/plugin.json`
  - Wire into `calculate_all_metrics()`, `print_evaluation_text()`, `--explain`, and `--format json`
- `SKILL.md`:
  - New section after "When NOT to Use": "Skill Maturity Model" with decision tree
  - Update "When NOT to Use" to reference the maturity model
- `references/` — possible new reference: `graduation_guide.md` with detailed criteria and migration steps

**Graduation signal output format (comprehensive mode):**
```
━━━ Graduation Signals ━━━
⚠ Reference sprawl: 11 reference files, 148KB total (threshold: >10 files or >50KB)
  → Consider plugin-level documentation structure (plugin-dev:plugin-structure)

ℹ This skill is already bundled in a plugin. Signals shown as structural notes.
```

**Graduation signal output format (--explain mode):**
```
━━━ Graduation Signals ━━━
⚠ Reference sprawl: 11 reference files, 148KB total

  Why: Skills with extensive reference documentation may benefit from plugin-level
  organization with commands, agents, and structured discovery.

  Context: This skill is already bundled in a plugin (.claude-plugin/plugin.json found).
  These signals are informational — the graduation has already occurred.

  If standalone: Consult plugin-dev:plugin-structure to scaffold a plugin around this skill.
  Migration preserves all existing references and scripts.
```

**Release:**
- Commit 1: `feat(skillsmith): add graduation signal detection`
- Commit 2: `feat(skillsmith): add skill maturity model to SKILL.md`
- Commit 3: `chore: Release skillsmith v6.0.0`

## Dependencies & Risks

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| evaluate_skill.py exceeds 3000 lines | High | Accept as technical debt; each function is self-contained; track in IMPROVEMENT_PLAN.md |
| False positives in orphan detection fix (#82) | Medium | Test against documented false positives in `docs/lessons/evaluate-skill-false-positives.md` |
| Phase ordering dependency (--explain needs graduation signals later) | Low | Reserve JSON schema key in Phase 3; graduation integration is additive |
| Graduation signals produce noise for plugin-bundled skills | Medium | Context-aware detection (check for plugin.json) resolves this |

## Success Metrics

- #82 and #81 resolved with no regressions
- Script count reduced from 7 to 3 (Phase 2)
- evaluate_skill.py correctly detects graduation signals on skills like `helm-chart-developer` (22KB SKILL.md, minimal structure) while correctly noting context for plugin-bundled skills
- Maturity model decision tree in SKILL.md references all 5 relevant plugin-dev skills

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-04-skillsmith-lifecycle-awareness-brainstorm.md](docs/brainstorms/2026-03-04-skillsmith-lifecycle-awareness-brainstorm.md)
  - Key decisions: deterministic-only evaluation, 3 graduation signals, incremental enhancement approach

### Internal References

- evaluate_skill.py scoring pattern: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:963` (calculate_overall_score)
- Orphan detection path 1: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:1095` (validate_file_references)
- Orphan detection path 2: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:1372` (unnamed check)
- "When NOT to use" section: `plugins/skillsmith/skills/skillsmith/SKILL.md:15-20`
- Skill evolution framework: `docs/lessons/skill-to-plugin-migration.md` (3-stage model)
- Known false positives: `docs/lessons/evaluate-skill-false-positives.md`
- Plugin-dev conventions: `~/.claude/plugins/cache/claude-plugins-official/plugin-dev/*/skills/`

### Related Issues

- #82: Orphan detection misses markdown link references
- #81: Iteration workflow should mandate full evaluation
- #37: Add --explain mode (detailed plan in issue)
- #24: Complete script consolidation Phases 2-3
