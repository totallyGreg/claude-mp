# AI Risk Mapper: Recommendations vs GitHub Issues Coverage Analysis

**Analysis Date**: 2026-01-28
**Document Purpose**: Cross-reference `ai-risk-mapper-improvement-recommendations.md` against GitHub Issues #2 and #3 to identify coverage gaps and future work.

---

## Executive Summary

The recommendations document is **well-aligned with GitHub Issues #2 and #3**, with comprehensive coverage of Phase 1 (v1.1.0) and Phase 2 (v2.0.0) improvements. However, there are notable gaps in tracking Phase 3+ improvements and emerging Skillsmith evaluation recommendations.

### Coverage Statistics
- **Total Recommendations**: 7 major improvements identified
- **Tracked in Issues**: 5 improvements (71%)
- **Untracked**: 2 improvements (29%)
- **Coverage by Phase**:
  - Phase 1 (v1.1.0): 4/4 improvements in Issue #2 (100%)
  - Phase 2 (v2.0.0): 1/1 improvement in Issue #3 (100%)
  - Phase 3+ (v2.1.0+): 0/2 improvements tracked in any issue (0%)

### Key Findings
1. **Phase 1 & 2 well-tracked**: Issues #2 and #3 comprehensively capture critical fixes and documentation overhaul
2. **Skillsmith evaluation gaps**: New recommendations from Skillsmith evaluation (Recommendation #1 and #2) not yet filed as issues
3. **Phase 3 unaddressed**: Enhanced automation improvements for v2.1.0+ not yet captured
4. **Migration guide missing**: User migration path (v1.0.0 → v1.1.0) documented in recommendations but not tracked in issues

---

## Part 1: Phase 1 (v1.1.0) Coverage - Issue #2 Analysis

**GitHub Issue**: [#2 - Add workflow automation and offline support](https://github.com/totallyGreg/claude-mp/issues/2)

### Improvement #1: Add Workflow Orchestration Script ⭐ CRITICAL

**Status in Recommendations**: Lines 86-297
**Status in Issue #2**: ✅ Fully tracked

**Issue Tasks Mapping**:
- [ ] Create `scripts/orchestrate_risk_assessment.py` orchestrator ✅
- [ ] Bundle CoSAI schemas in `assets/cosai-schemas/` (see Improvement #2)
- [ ] Update `fetch_cosai_schemas.py` with SSL bypass + bundled fallback (see Improvement #2)
- [ ] Update `SKILL.md` with orchestrator invocation instructions ✅
- [ ] Add graceful manual analysis mode to orchestrator ✅
- [ ] Test scenarios (happy path, SSL failure, offline mode, missing target) ✅

**Details Captured**:
- ✅ Full Python implementation provided
- ✅ Command-line interface specified
- ✅ Error handling approach defined
- ✅ Integration with existing scripts documented
- ✅ SKILL.md update example provided

**Notes**: Issue #2 provides comprehensive task checklist and implementation specifications align with recommendations document.

---

### Improvement #2: Bundle Pre-Cached CoSAI Schemas ⭐ CRITICAL

**Status in Recommendations**: Lines 299-358
**Status in Issue #2**: ✅ Fully tracked

**Issue Tasks Mapping**:
- [ ] Add bundled schemas to `assets/cosai-schemas/` ✅
- [ ] Update `fetch_cosai_schemas.py` with SSL handling ✅
- [ ] Update `fetch_cosai_schemas.py` with bundled fallback ✅
- [ ] Add SSL bypass option for corporate environments ✅

**Details Captured**:
- ✅ Directory structure provided (yaml/ and schemas/ subdirectories)
- ✅ File naming conventions specified
- ✅ Implementation code examples for fallback logic
- ✅ SSL bypass flag documented (`--insecure`)
- ✅ Error handling patterns shown

**Notes**: Issue #2 explicitly includes bundled schema implementation in task list and success criteria.

---

### Improvement #3: Add Action-Oriented Skill Instructions (SKILL.md Restructure)

**Status in Recommendations**: Lines 361-490
**Status in Issue #2**: ⚠️ Partially tracked

**Why Partial**:
- Issue #2 mentions "Update SKILL.md with orchestrator invocation instructions" (task 4)
- However, the deep restructuring and conciseness improvements are NOT in Issue #2
- These are fully captured in Issue #3 instead (see Phase 2 section below)

**Details Captured in #2**:
- ✅ Core orchestrator invocation section
- ✅ Error handling and fallback modes
- ✅ Manual workflow reference

**Details Captured in #3 (Preferred Home)**:
- ✅ Comprehensive restructuring guidelines
- ✅ Conciseness and line count targets
- ✅ Progressive disclosure structure
- ✅ Framework reference organization

**Notes**: This improvement spans both issues, with Issue #2 handling immediate execution details and Issue #3 handling the deeper structural overhaul.

---

### Improvement #4: Add Graceful Manual Analysis Mode

**Status in Recommendations**: Lines 492-524
**Status in Issue #2**: ✅ Fully tracked

**Issue Tasks Mapping**:
- [ ] Add manual analysis fallback to orchestrator ✅

**Details Captured**:
- ✅ Fallback mechanism when automation fails
- ✅ Reference loading guidance
- ✅ Manual risk checklist example
- ✅ Integration point in orchestrator error handling

**Notes**: Correctly identified as part of Issue #2 Phase 1 improvements.

---

### Improvement #5: Add Skill Behavior Examples

**Status in Recommendations**: Lines 527-586
**Status in Issue #2**: ⚠️ Partially tracked

**Coverage**:
- Mentioned in Issue #2 context but NOT explicitly listed as a task
- Related to SKILL.md improvements (Issue #3 territory)
- However, conceptually part of "action-oriented instructions" in Phase 1

**Examples Provided in Recommendations**:
- Example 1: Automated Assessment (happy path)
- Example 2: Network Failure Graceful Handling
- Example 3: Manual Mode When Automation Unavailable

**Notes**: These examples are important for demonstrating the orchestrator in action, but would likely be better formalized in Issue #3 (SKILL.md restructuring) since they belong in the updated documentation.

---

### Phase 1 Summary

**Coverage**: 4/5 improvements fully tracked, 1/5 partially tracked
**Recommendation**: Issue #2 comprehensively covers Phase 1 work with detailed tasks and success criteria. The SKILL.md-related improvements are appropriately split between Issue #2 (execution) and Issue #3 (documentation overhaul).

---

## Part 2: Phase 2 (v2.0.0) Coverage - Issue #3 Analysis

**GitHub Issue**: [#3 - Restructure SKILL.md for conciseness](https://github.com/totallyGreg/claude-mp/issues/3)

### Improvement #3: Add Action-Oriented Skill Instructions (Comprehensive Restructure)

**Status in Recommendations**: Lines 361-490
**Status in Issue #3**: ✅ Fully tracked

**Issue Tasks Mapping**:
- [ ] Create `references/workflow_guide.md` for detailed content ✅
- [ ] Move framework explanations from SKILL.md → workflow_guide.md ✅
- [ ] Move persona responsibilities details → workflow_guide.md ✅
- [ ] Move schema structure details → workflow_guide.md ✅
- [ ] Move control category descriptions → workflow_guide.md ✅
- [ ] Restructure SKILL.md with action-oriented format ✅
- [ ] Add usage examples section ✅
- [ ] Add `license: Apache 2.0` to frontmatter ✅

**Details Captured**:
- ✅ Target length (<300 lines vs current 539)
- ✅ Target token count (<2000 tokens)
- ✅ Progressive disclosure structure
- ✅ Section organization plan
- ✅ New reference file organization
- ✅ Success criteria and metrics

**Notes**: Issue #3 comprehensively captures the structural overhaul with detailed task list and measurable success criteria.

---

### Phase 2 Summary

**Coverage**: 1/1 improvement fully tracked
**Recommendation**: Issue #3 provides comprehensive guidance for SKILL.md restructuring with clear success metrics and task breakdown.

---

## Part 3: Uncovered Recommendations

### Uncovered #1: Skillsmith Evaluation - SKILL.md Conciseness (Recommendation #1)

**Status in Recommendations**: Lines 835-862
**Status in Issues**: ❌ NOT explicitly tracked

**Details**:
- Problem: SKILL.md is 538 lines, 4585 tokens (exceeds 500 lines, 2000 token guidelines)
- Conciseness score: 23/100 (Poor)
- Proposed Solution: Move content to references/, restructure for action-orientation
- Target: <300 lines, ~2000 tokens, achieve 60+/100 conciseness score

**Current Situation**:
- Issue #3 DOES address this through SKILL.md restructuring
- However, Issue #3 was created BEFORE the Skillsmith evaluation
- The explicit "Skillsmith Evaluation Recommendation #1" is not formally referenced in Issue #3
- Evaluation metrics (conciseness score target of 60+/100) not in Issue #3 task list

**Recommendation**: Issue #3 should be updated to explicitly reference Skillsmith Recommendation #1 and add conciseness score measurement task.

**Suggested Task Addition to Issue #3**:
```
- [ ] Measure conciseness score using skillsmith evaluation
      uv run skills/skillsmith/scripts/evaluate_skill.py skills/ai-risk-mapper
- [ ] Verify Skillsmith conciseness score ≥ 60/100 before completion
```

---

### Uncovered #2: Skillsmith Evaluation - Missing License Field (Recommendation #2)

**Status in Recommendations**: Lines 864-890
**Status in Issues**: ❌ NOT tracked in any issue

**Details**:
- Problem: SKILL.md frontmatter missing `license` field
- Impact: Specification compliance warning during validation
- Solution: Add `license: Apache 2.0` to YAML frontmatter
- Version Bump: PATCH (1.1.0 → 1.1.1 or 1.2.0 → 1.2.1)

**Current Situation**:
- Issue #3 INCLUDES this task: "Add `license: Apache 2.0` to frontmatter"
- However, it's grouped with Phase 2 (v2.0.0) improvements
- Skillsmith recommends PATCH version bump, not MINOR version bump
- This is truly a quick fix that could be done anytime

**Recommendation**: Consider extracting this as a separate quick-fix task that can be done independently. Add to Issue #3 with note that it's a small metadata fix that doesn't require full SKILL.md restructuring.

**Current Status in Issue #3**: ✅ Included in task list (though not clearly separated as quick-fix)

---

### Uncovered #3: Phase 3 Enhanced Automation (v2.1.0+)

**Status in Recommendations**: Lines 644-652
**Status in Issues**: ❌ NOT tracked in any issue

**Details**:
- LLM-based semantic analysis (replaces keyword matching)
- Interactive risk visualization dashboard
- Control implementation tracker

**Current Situation**:
- Identified in recommendations as "medium-term" improvements
- Explicitly marked as v2.1.0 and beyond
- No GitHub issue created yet
- These are enhancement features, not critical fixes

**Impact**: Important for long-term skill enhancement but lower priority than v1.1.0 and v2.0.0 work.

**Recommendation**: These should be filed as Issue #4 (v2.1.0 roadmap) after Phase 1 and Phase 2 are complete. See "Recommended New Issues" section below.

---

### Uncovered #4: Migration Guide Documentation

**Status in Recommendations**: Lines 785-810
**Status in Issues**: ❌ NOT tracked in any issue

**Details**:
- Backward compatibility guidance for users upgrading from v1.0.0
- Shows mapping between old workflow and new orchestrator workflow
- Documents that individual scripts still work independently

**Current Situation**:
- Documented in recommendations for user education
- Important for user experience during migration from v1.0.0 → v1.1.0
- Not explicitly included in Issue #2 task list
- Could be valuable addition to documentation

**Recommendation**: Add to Issue #2 as documentation task, or ensure migration guide is created as part of SKILL.md restructuring (Issue #3).

**Suggested Task Addition to Issue #2 or #3**:
```
- [ ] Create migration guide showing v1.0.0 → v1.1.0 workflow changes
- [ ] Document backward compatibility of individual scripts
```

---

### Uncovered #5: Testing Plan and Scenarios

**Status in Recommendations**: Lines 719-764
**Status in Issues**: ⚠️ Mentioned but not detailed

**Details**:
- Test Scenario 1: Happy Path
- Test Scenario 2: SSL Failure → Offline Fallback
- Test Scenario 3: Complete Offline Mode
- Test Scenario 4: Missing Target

**Current Situation**:
- Issue #2 includes test tasks but without detailed scenarios
- Recommendations document provides specific test commands and expected outputs
- Good foundation for detailed QA checklist

**Recommendation**: Use recommendations document as reference for detailed test plan when executing Issue #2. Consider creating `tests/` directory with automated test suite.

---

### Uncovered #6: Metrics and Success Measurements

**Status in Recommendations**: Lines 767-782
**Status in Issues**: ⚠️ Partially captured

**Details**:
- Automation rate target (0% → 95%)
- Network failure handling metric
- SKILL.md length reduction target (540 → <200 lines)
- Time to first action target (~30s → <5s)
- Error recovery metric

**Current Situation**:
- Issue #3 includes success criteria for SKILL.md length
- Issue #2 includes success criteria for automation
- Recommendations provide broader metrics context

**Recommendation**: These metrics are implicitly captured in both issues but could be more explicit. Consider adding to IMPROVEMENT_PLAN.md after completing phases.

---

## Part 4: Categorized Uncovered Recommendations

### IMMEDIATE (Should be done with Phase 1)

1. **Skillsmith Evaluation Recommendation #2: Add license field**
   - Priority: HIGH (Specification compliance)
   - Effort: 5 minutes
   - Status: ✅ Included in Issue #3
   - Version: PATCH or included in v2.0.0

### SHORT-TERM (Phase 2 timing)

1. **Skillsmith Evaluation Recommendation #1: Conciseness metrics**
   - Priority: HIGH (Evaluation framework)
   - Effort: Add 1 task to Issue #3
   - Status: ❌ Not explicitly tracked
   - Version: v2.0.0
   - **Recommendation**: Add explicit measurement task to Issue #3

2. **Migration guide for v1.0.0 → v1.1.0**
   - Priority: MEDIUM (User documentation)
   - Effort: 2-3 hours (content creation + integration)
   - Status: ❌ Not tracked
   - Version: v1.1.0 documentation
   - **Recommendation**: Add to Issue #2 or #3 documentation tasks

### MEDIUM-TERM (Phase 3+)

1. **Phase 3 Enhanced Automation (v2.1.0)**
   - LLM-based semantic analysis
   - Interactive risk visualization dashboard
   - Control implementation tracker
   - Priority: MEDIUM (Enhancement features)
   - Effort: Unknown (research needed)
   - Status: ❌ No issue created
   - Version: v2.1.0
   - **Recommendation**: Create Issue #4 after Phase 1 & 2 complete

---

## Part 5: Recommended New Issues

Based on coverage gap analysis, recommend creating the following new issues:

### Issue #4: Enhanced Automation and UI (v2.1.0)

**Title**: `ai-risk-mapper: Enhanced automation and visualization (v2.1.0)`

**Description**:
```
**Goal**: Enhance risk assessment with semantic analysis and interactive UI

**Priority**: MEDIUM - MEDIUM-TERM (after v2.0.0)

**Features**:
1. LLM-based semantic analysis
   - Replace keyword matching with semantic risk detection
   - Better identification of subtle security issues
   - Improved accuracy and reduced false positives

2. Interactive risk visualization dashboard
   - Visual representation of risk landscape
   - Risk distribution by lifecycle stage
   - Control coverage analysis

3. Control implementation tracker
   - Manage control implementation status
   - Track remediation progress
   - Timeline and ownership tracking

**Version Bump**: 2.0.0 → 2.1.0 (MINOR - new features)

**Source**: `/ai-risk-mapper-improvement-recommendations.md` Phase 3 section

**Blocked By**: Issue #2, Issue #3 (must complete v1.1.0 and v2.0.0 first)
```

---

### Enhancement #1: Update Issue #3 - Add Skillsmith Metrics Task

**Suggested Task Addition**:
```markdown
- [ ] Measure conciseness score using skillsmith evaluation
      Command: uv run skills/skillsmith/scripts/evaluate_skill.py skills/ai-risk-mapper --version 2.0.0
- [ ] Verify Skillsmith conciseness score ≥ 60/100 before closure
```

**Rationale**: Skillsmith Recommendation #1 explicitly calls for measuring conciseness score as success criterion. Should be formalized in Issue #3 task list.

---

### Enhancement #2: Add Migration Guide to Issue #2 or #3

**Suggested Task Addition**:
```markdown
## Documentation Tasks
- [ ] Create migration guide document showing v1.0.0 → v1.1.0+ workflow changes
- [ ] Document backward compatibility of individual scripts
- [ ] Include in updated SKILL.md or separate references/migration_guide.md
```

**Rationale**: Recommendations document provides user migration path but it's not explicitly tracked in any issue. Important for user communication.

---

## Part 6: Comparison Matrix

| Improvement | Title | Phase | v1.1.0 | v2.0.0 | Issue | Status |
|-------------|-------|-------|--------|--------|-------|--------|
| #1 | Orchestration Script | 1 | ✅ | - | #2 | Fully tracked |
| #2 | Bundled Schemas & SSL | 1 | ✅ | - | #2 | Fully tracked |
| #3 | Action-Oriented SKILL.md | 1+2 | ⚠️ | ✅ | #2, #3 | Fully tracked (split) |
| #4 | Graceful Manual Mode | 1 | ✅ | - | #2 | Fully tracked |
| #5 | Usage Examples | 1+2 | ⚠️ | ✅ | #2, #3 | Mostly tracked |
| Skill #1 | Conciseness Metrics | 2 | - | ⚠️ | #3 | Partially tracked |
| Skill #2 | License Field | 2 | - | ✅ | #3 | Fully tracked |
| Phase 3 | Enhanced Automation | 3 | - | - | NONE | NOT tracked |

**Legend**: ✅ = Fully tracked, ⚠️ = Partially tracked, ❌ = Not tracked, NONE = No issue

---

## Part 7: Implementation Priorities & Timeline

### Phase 1: Critical Fixes (v1.1.0) - Issue #2

**Timeline**: Immediate (weeks 1-4)
**Status**: Ready to implement
**Coverage**: 4/5 improvements fully tracked, 1/5 partially
**Recommendation**: Proceed with Issue #2 as planned

**Action Items**:
- [ ] Proceed with Issue #2 implementation
- [ ] Use recommendations document as reference for implementation details
- [ ] Follow testing scenarios provided in recommendations (lines 719-764)
- [ ] Consider adding migration guide to documentation tasks

---

### Phase 2: Documentation Overhaul (v2.0.0) - Issue #3

**Timeline**: Short-term (weeks 5-8, after Phase 1)
**Status**: Depends on Phase 1 completion
**Coverage**: 1/1 improvement fully tracked
**Recommendation**: Proceed with Issue #3, with enhancement for metrics

**Action Items**:
- [ ] Proceed with Issue #3 implementation as planned
- [ ] ADD: Explicit task to measure Skillsmith conciseness score
- [ ] ADD: Task to verify ≥60/100 conciseness score before closure
- [ ] Use detailed restructuring examples from recommendations (lines 385-480)
- [ ] Consider migration guide as documentation enhancement

---

### Phase 3: Enhanced Automation (v2.1.0) - Proposed Issue #4

**Timeline**: Medium-term (weeks 12+, after Phase 2)
**Status**: Requires research and planning
**Coverage**: 0/3 improvements tracked (all new territory)
**Recommendation**: Create Issue #4 after Phase 1 & 2 complete

**Action Items**:
- [ ] Create Issue #4 after Phase 2 completion
- [ ] Research LLM-based semantic analysis approaches
- [ ] Prototype visualization dashboard options
- [ ] Define control tracker data model and UI

---

## Part 8: Key Takeaways

### What's Working Well
1. **Issues #2 and #3 are comprehensive** - They capture all critical and high-priority work
2. **Good alignment with recommendations** - GitHub issues match the recommendations document closely
3. **Clear phase separation** - v1.1.0 vs v2.0.0 work is well-organized
4. **Detailed task lists** - Both issues provide specific, actionable tasks

### Improvement Opportunities
1. **Skillsmith metrics should be explicit in Issue #3** - Add conciseness score measurement as formal success criterion
2. **Migration guide not tracked** - Consider adding to Issue #2 or #3 documentation
3. **Phase 3 needs separate issue** - LLM semantic analysis and visualization should be Issue #4
4. **License field is quick fix** - Could be completed before Phase 2 or as separate quick-fix PR

### Recommendations Summary

| Action | Priority | Effort | Impact |
|--------|----------|--------|--------|
| Proceed with Issue #2 | CRITICAL | Medium | Fixes critical skill gaps |
| Proceed with Issue #3 | HIGH | Medium | Improves skill usability |
| Add metrics task to #3 | HIGH | Low | Formalizes Skillsmith eval |
| Add migration guide doc | MEDIUM | Medium | Improves user experience |
| Create Issue #4 (Phase 3) | MEDIUM | High | Future enhancement roadmap |

---

## Part 9: File Structure and Cross-References

### Key Files
- **Recommendations Document**: `/Users/gregwilliams/Documents/Projects/claude-mp/ai-risk-mapper-improvement-recommendations.md`
- **IMPROVEMENT_PLAN.md**: `/Users/gregwilliams/Documents/Projects/claude-mp/skills/ai-risk-mapper/IMPROVEMENT_PLAN.md`
- **SKILL.md**: `/Users/gregwilliams/Documents/Projects/claude-mp/skills/ai-risk-mapper/SKILL.md`
- **GitHub Issue #2**: Workflow automation and offline support (v1.1.0)
- **GitHub Issue #3**: Restructure SKILL.md for conciseness (v2.0.0)

### Related Documentation
- Testing scenarios: Recommendations lines 719-764
- Migration guide: Recommendations lines 785-810
- Metrics and targets: Recommendations lines 767-782
- Skillsmith eval: Recommendations lines 835-892

---

## Conclusion

The `ai-risk-mapper-improvement-recommendations.md` document is well-aligned with GitHub Issues #2 and #3, providing comprehensive guidance for Phase 1 and Phase 2 improvements. Coverage gaps exist primarily in Phase 3+ enhancements and some Skillsmith evaluation recommendations.

**Recommended Next Steps**:
1. Proceed with Issue #2 and #3 implementation as planned
2. Enhance Issue #3 with explicit Skillsmith metrics tasks
3. Consider adding migration guide documentation
4. Create Issue #4 (v2.1.0) after Phase 1 & 2 complete
5. Use recommendations document as detailed reference during implementation

**Overall Assessment**: 71% of recommendations tracked in GitHub issues, with 100% coverage of Phase 1 & 2 critical work. Phase 3+ improvements need separate issue tracking.

---

**Analysis Prepared By**: Claude Code Agent
**Date**: 2026-01-28
**Related Files**: ai-risk-mapper-improvement-recommendations.md, GitHub Issues #2, #3
**Next Review**: After Issue #2 completion, before starting Issue #3
