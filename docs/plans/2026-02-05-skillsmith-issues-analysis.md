# Skillsmith Issues Analysis

**Date:** 2026-02-05
**Purpose:** Consolidate and link all skillsmith-related GitHub issues

## Summary

Found **18 skillsmith-related issues**: 11 OPEN, 7 CLOSED

## Issue Relationship Map

```
                           CLOSED                                    OPEN
                             │                                         │
                             ▼                                         │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                     │
│  #33 (CLOSED) ─────────┬──────────► #37 (OPEN) --explain mode                       │
│  v5.0.0 alignment      │                                                           │
│                        └──────────► #38 (OPEN) --compare-to-official                │
│                                                                                     │
│  #25 (OPEN) ──────────────────────► #26 (OPEN) plugin-specific context              │
│  plugin-dev relationship             Blocked by #25                                 │
│                                                                                     │
│  #8 (CLOSED) ─────────────────────► #24 (OPEN) script consolidation                 │
│  validation features                 Phases 2-3 remaining                           │
│                                                                                     │
│  #6 (CLOSED) ─────────────────────► #11 (OPEN) triage enhancement ideas             │
│  planning consolidation              From old IMPROVEMENT_PLAN.md                   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘

STANDALONE OPEN ISSUES:
  #32 - When NOT to use skillsmith (Related to #31)
  #10 - Interactive mode for skill template
  #17 - URL support for evaluate_skill.py
  #18 - /evaluate-skill command + version shadowing (marketplace-manager)
  #39 - Pre-commit plugin.json version bump (discovered during skillsmith work)
```

## Issues by Status

### OPEN Issues - Skillsmith Core (8)

| # | Title | Blockers | Work Status |
|---|-------|----------|-------------|
| #37 | Add --explain mode to evaluate_skill.py | None (parent #33 closed) | **Ready to start** |
| #38 | Add --compare-to-official flag | None (parent #33 closed) | **Ready to start** |
| #24 | Complete script consolidation (Phases 2-3) | None | **Phase 1 done** |
| #32 | Add guidance on when NOT to use skillsmith | None | **Ready to start** |
| #26 | Add plugin-specific context | Blocked by #25 | **Blocked** |
| #10 | Add interactive mode to skill template | None | Planning |
| #11 | Review and triage future enhancement ideas | None | Planning |
| #17 | Add URL support to evaluate_skill.py | None | Planning |

### OPEN Issues - Related (3)

| # | Title | Relationship |
|---|-------|--------------|
| #18 | Add /evaluate-skill command + version shadowing | Uses skillsmith, labeled marketplace-manager |
| #25 | Clarify plugin-dev relationship | Blocks #26 |
| #39 | Pre-commit plugin.json version bump | Discovered during skillsmith v5.0.0 work |

### CLOSED Issues - Skillsmith (7)

| # | Title | Completion |
|---|-------|------------|
| #33 | Align with official plugin-dev patterns v5.0.0 | Phases 1-2 done, Phases 3-4 have children |
| #28 | Migrate to standalone plugin structure | Complete (v4.0.0) |
| #16 | Create /evaluate-skill command wrapper | Complete (v4.0.0) |
| #8 | Advanced validation features | Complete (v3.5.0-3.7.0) |
| #9 | Complete reference consolidation verification | Complete |
| #7 | Add --strict validation mode | Complete (v3.4.0) |
| #5 | Deprecate skill-planner skill | Complete |

## Work Status Analysis

### Completed Work
- v5.0.0: Official plugin-dev alignment (Description Quality Score, trigger validation, Common Mistakes section, Quick Reference templates) - #33
- v4.0.0: Standalone plugin migration + slash commands (/ss-validate, /ss-evaluate, /ss-init, /ss-research) - #28, #16
- v3.7.x: Script consolidation Phase 1, validation improvements - #24, #8
- v3.4.0: Strict validation mode - #7
- v3.3.0: Planning consolidation - #6

### Work Still Needed

**High Priority (unblocked, parent issue closed):**
1. **#37** - Add --explain mode (orphaned from closed #33)
2. **#38** - Add --compare-to-official flag (orphaned from closed #33)
3. **#24** - Complete script consolidation Phases 2-3

**Medium Priority:**
4. **#32** - Add "when NOT to use" guidance
5. **#25** - Clarify plugin-dev relationship (unblocks #26)
6. **#10** - Interactive mode for skill template

**Lower Priority (needs triage):**
7. **#11** - Review enhancement ideas from old plan
8. **#17** - URL support for evaluate_skill.py

## Relationship Gaps Found

The following issue links need to be added:

1. **#33 → #37, #38**: Parent issue should reference children (currently children reference parent but not vice versa)
2. **#8 → #24**: Original issue should reference continuation work
3. **#6 → #11**: Planning consolidation led to this triage issue

## Recommendations

### 1. Close #33 Properly
Issue #33 is marked CLOSED but has uncompleted child tasks (#37, #38). Either:
- Reopen #33 and complete Phases 3-4, OR
- Add comment to #33 noting orphaned work in #37, #38

### 2. Resolve Blocker Chain
- Complete #25 (Clarify plugin-dev relationship)
- This unblocks #26 (Add plugin-specific context)

### 3. Prioritize Orphaned Work
Issues #37 and #38 were created as part of #33's Phase 3 but weren't completed before #33 was closed. These are ready to implement.

### 4. Update IMPROVEMENT_PLAN.md Active Work Section
Current Active Work section is missing:
- #37 (--explain mode)
- #38 (--compare-to-official)
- #32 (when NOT to use)

## Proposed Actions

1. **Add cross-references to #33** noting #37, #38 are orphaned children
2. **Update IMPROVEMENT_PLAN.md** Active Work to include #37, #38, #32
3. **Create parent-child links** where missing
4. **Add label `skill:skillsmith`** to #37, #38 (currently unlabeled)
