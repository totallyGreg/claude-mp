---
date: 2026-02-16
topic: skillsmith-companion-agent-priorities
---

# Skillsmith: Companion Agent Priority Work

## What We're Building

Three focused improvements to make skillsmith a better companion agent, post-v5.0.0 plugin-dev alignment:

1. **#32 — "When NOT to use" boundary guidance** (Approach A: SKILL.md section)
2. **#37 — `--explain` mode with per-metric detail + top-3 summary** (Approach C: combined)
3. **#24 — Script consolidation Phases 2-3** (Approach A: absorb and delete)

## Why These Three

After v5.0.0 aligned skillsmith with official plugin-dev patterns, the remaining open issues fall into two camps: still relevant vs. redundant. These three are the highest-leverage items that directly improve the companion agent experience:

- #32 prevents skillsmith from overstepping into plugin-dev territory
- #37 transforms skillsmith from a scorecard into a coach
- #24 reduces maintenance surface and simplifies the tool inventory

### Issues deprioritized (post-alignment redundancy)

- **#38** (`--compare-to-official`): Official patterns already baked into v5.0.0 scoring
- **#26** (plugin-specific context): Knowledge lives in `plugin-dev:skill-development`; skillsmith should reference, not reproduce
- **#17** (URL support): Edge case; slash commands already handle invocation
- **#10** (interactive mode): Claude's natural Q&A already covers this
- **#11** (triage enhancements): Resolved by this brainstorm

## Key Decisions

### #32: SKILL.md "When NOT to Use" section
- **Approach**: Add ~5-line redirect section after "About Skills" intro
- **Redirects to**: `plugin-dev:command-development`, `plugin-dev:plugin-structure`, `plugin-dev:hook-development`, `plugin-dev:agent-development`
- **Rationale**: Simplest fix, always visible when skill triggers, directly addresses the misrouting problem

### #37: `--explain` mode (combined per-metric + summary)
- **Approach**: Add `--explain` flag to `evaluate_skill.py` that provides:
  1. Per-metric explanation blocks (why the score, what to change, expected impact)
  2. "Top 3 improvements" summary at the end with estimated score improvement
- **Per-metric template**:
  ```
  Conciseness Score: 56/100

    Why: SKILL.md is 391 lines (target: <300 for bonus)

    To improve:
    - Move "Common Mistakes" section -> references/ (-55 lines)
    - Move "Quick Reference" section -> references/ (-75 lines)

    See: references/progressive_disclosure_discipline.md
  ```
- **Summary template**:
  ```
  Top 3 improvements:
  1. Reduce SKILL.md by ~130 lines -> +24 conciseness
  2. Add 2 more trigger phrases -> +10 description quality
  3. Add examples/ directory -> +5 spec compliance

  Estimated overall improvement: 85 -> 92
  ```
- **Rationale**: Highest-value single feature; combined approach gives both understanding and actionability

### #24: Script consolidation (absorb and delete)
- **Phase 2**: Integrate into `evaluate_skill.py`:
  - `--validate-references` flag (absorbs `update_references.py` validation logic)
  - `--detect-duplicates` flag (opt-in, absorbs similarity checking)
- **Phase 3**: Delete deprecated scripts:
  - `validate_workflow.py` (deprecated since v3.7.2)
  - `audit_improvements.py` (deprecated since v3.7.2)
  - `update_references.py` (after Phase 2 integration verified)
  - `research_skill.py` (experimental, no demonstrated demand)
- **Target inventory**:
  ```
  scripts/
  ├── evaluate_skill.py    # Unified validation/evaluation/explanation
  ├── init_skill.py        # Skill scaffolding
  └── utils.py             # Shared utilities
  ```
- **Rationale**: Finish what was started; single entry point is easier to document and discover

## Open Questions

- Should the deprioritized issues (#38, #26, #17, #10) be closed with a "won't fix" or left open for potential future reconsideration?
- For #37, should `--explain` be the default behavior in comprehensive mode (no flags), or always require the explicit flag?

## Next Steps

-> `/workflows:plan` for implementation details on each issue
