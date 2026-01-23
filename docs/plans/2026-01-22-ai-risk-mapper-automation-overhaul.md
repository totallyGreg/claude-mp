# AI Risk Mapper - Automation Overhaul Plan

**Date**: 2026-01-22
**Skill**: ai-risk-mapper
**Goal**: Transform ai-risk-mapper from documentation-oriented skill to action-oriented automation skill

## Executive Summary

The ai-risk-mapper skill has excellent automation scripts but fails to leverage them due to its documentation-oriented design. When invoked, it only loads SKILL.md into context, requiring Claude to manually orchestrate the workflow. This plan addresses critical execution gaps, network failure handling, and documentation restructuring.

**Source**: Based on real-world usage analysis and Skillsmith evaluation (see `/ai-risk-mapper-improvement-recommendations.md`)

## Critical Issues Identified

### Issue #1: No Automatic Workflow Execution
**Problem**: Skill invocation displays documentation instead of executing automated workflows.

**Current Reality**:
- User invokes skill → Claude reads 539-line SKILL.md → Claude manually runs Bash commands
- Expected: Invoke skill → Automated risk assessment runs → Results presented

**Root Cause**: Skills are documentation-based by design; no mechanism to auto-execute workflows.

### Issue #2: SSL Certificate Failures
**Problem**: `fetch_cosai_schemas.py` fails in corporate environments with SSL errors, blocking entire workflow.

**Root Cause**:
- Corporate proxies with self-signed certificates
- No SSL verification bypass option
- No bundled offline schemas

### Issue #3: Documentation vs Execution Disconnect
**Problem**: SKILL.md promises "automated risk identification" but requires manual orchestration.

### Issue #4: No Graceful Degradation
**Problem**: When schemas can't be fetched, skill becomes completely unusable.

### Issue #5: Excessive SKILL.md Length
**Problem**: 539 lines (~4585 tokens) exceeds recommendations (500 lines, 2000 tokens).

**Impact**: Poor conciseness score (23/100), increased context load, violates progressive disclosure principles.

## Implementation Phases

### Phase 1: Critical Automation Fixes (v1.1.0)
**Priority**: CRITICAL - IMMEDIATE
**Target Issues**: #1, #2, #4
**Version Bump**: 1.0.0 → 1.1.0 (MINOR - new features, backward compatible)

#### Changes

1. **Create Workflow Orchestrator Script**
   - **File**: `scripts/orchestrate_risk_assessment.py` (NEW)
   - **Purpose**: Single command to run complete assessment workflow
   - **Features**:
     - Auto-fetch schemas with fallback to bundled cache
     - Run risk analysis on target
     - Generate report
     - Handle errors gracefully with fallback modes
   - **Usage**: `uv run scripts/orchestrate_risk_assessment.py --target <path>`

2. **Bundle CoSAI Schemas for Offline Mode**
   - **Directory**: `assets/cosai-schemas/` (NEW)
   - **Contents**:
     - `yaml/*.yaml` - 5 YAML schema files
     - `schemas/*.json` - 5 JSON schema files
   - **Purpose**: Offline fallback when network/SSL fails

3. **Update Schema Fetcher with Fallback Logic**
   - **File**: `scripts/fetch_cosai_schemas.py` (MODIFY)
   - **Changes**:
     - Add SSL bypass option (`--insecure` flag)
     - Auto-fallback to bundled schemas on network failure
     - Better error messages

4. **Update SKILL.md with Orchestrator Instructions**
   - **File**: `SKILL.md` (MODIFY)
   - **Changes**:
     - Add "When Invoked" section at top
     - Immediate action: Run orchestrator script
     - Document error handling and fallback modes
     - Keep detailed workflow as "Manual Workflow (For Customization)"

5. **Add Graceful Manual Analysis Mode**
   - **File**: `scripts/orchestrate_risk_assessment.py`
   - **Feature**: When automation fails, provide manual CoSAI checklist
   - **Purpose**: Skill remains useful even when scripts can't run

#### Success Criteria
- ✅ Skill invocation automatically runs orchestrator
- ✅ SSL failures gracefully fallback to bundled schemas
- ✅ Complete workflow executes without manual intervention
- ✅ Manual mode available when automation fails

#### Files Modified/Created
**Modified**:
- `SKILL.md` - Add orchestrator invocation instructions
- `scripts/fetch_cosai_schemas.py` - Add SSL bypass + bundled fallback

**Created**:
- `scripts/orchestrate_risk_assessment.py` - Workflow orchestrator
- `assets/cosai-schemas/yaml/*.yaml` - 5 bundled YAML schemas
- `assets/cosai-schemas/schemas/*.json` - 5 bundled JSON schemas

#### Testing Plan
1. **Happy path**: Network available, schemas fetch successfully
2. **SSL failure**: Corporate proxy environment, auto-fallback to bundled
3. **Offline mode**: No network, use `--offline` flag
4. **Missing target**: Proper error message

---

### Phase 2: Documentation Overhaul (v2.0.0)
**Priority**: HIGH - SHORT-TERM
**Target Issues**: #3, #5
**Version Bump**: 1.1.0 → 2.0.0 (MAJOR - breaking changes to workflow instructions)

#### Changes

1. **Restructure SKILL.md to Action-Oriented Format**
   - **Current**: 539 lines, documentation-heavy
   - **Target**: <300 lines, action-oriented
   - **Structure**:
     ```
     When Invoked (20 lines)      - Immediate orchestrator execution
     Error Handling (40 lines)     - Fallback modes
     Manual Workflow (30 lines)    - For customization
     Framework Reference (20 lines) - Pointers to references/
     Usage Examples (30 lines)     - Real scenarios
     Resources (20 lines)          - Scripts and assets
     ```

2. **Move Detailed Framework Docs to references/**
   - **Create**: `references/workflow_guide.md` (NEW)
   - **Move content from SKILL.md**:
     - Detailed CoSAI framework explanations
     - Extensive persona responsibilities
     - Schema structure details
     - Control category descriptions

3. **Add Usage Examples**
   - **In SKILL.md**: Add 3-5 real-world examples
   - **Show**:
     - Automated assessment
     - Network failure graceful handling
     - Manual mode when automation unavailable

4. **Add License Field to Frontmatter**
   - **File**: `SKILL.md` frontmatter
   - **Add**: `license: Apache 2.0`
   - **Fixes**: Skillsmith validation warning

#### Success Criteria
- ✅ SKILL.md <300 lines and <2000 tokens
- ✅ First 50 lines provide immediate action items
- ✅ Examples show expected behavior
- ✅ Reference docs separated from procedural instructions
- ✅ Conciseness score improves to "Good" (60+/100)

#### Files Modified/Created
**Modified**:
- `SKILL.md` - Complete restructure (539 → ~200 lines)

**Created**:
- `references/workflow_guide.md` - Detailed workflow documentation

---

### Phase 3: Enhanced Automation (v2.1.0+)
**Priority**: MEDIUM - MEDIUM-TERM
**Target**: Future enhancements from existing IMPROVEMENT_PLAN.md
**Version Bump**: 2.0.0 → 2.1.0+ (MINOR - new features)

#### Future Improvements
1. **LLM-Based Semantic Analysis** (existing planned improvement #1)
   - Replace keyword matching with Claude API integration
   - Context-aware risk assessment
   - Improves detection accuracy

2. **Interactive Risk Visualization Dashboard** (existing planned improvement #2)
   - D3.js interactive dashboard
   - Risk heatmap by severity/lifecycle
   - Visual risk-to-control mappings

3. **Control Implementation Tracker** (existing planned improvement #3)
   - SQLite database for tracking
   - Progress reports showing control coverage
   - Historical effectiveness tracking

## Before & After Comparison

### Before (Current v1.0.0)
**User Request**: "Examine model-context-protocol-security.md using ai-risk-mapper"

**What Happens**:
1. Skill loads 539-line SKILL.md
2. Claude reads documentation
3. Claude runs `fetch_cosai_schemas.py`
4. Script fails with SSL error
5. Workflow blocked, no fallback
6. Claude performs manual analysis
7. No automated report

**Result**: Manual orchestration, no automation benefit

### After Phase 1 (v1.1.0)
**User Request**: "Examine model-context-protocol-security.md using ai-risk-mapper"

**What Happens**:
1. Skill loads SKILL.md with orchestrator instructions
2. Claude runs: `uv run scripts/orchestrate_risk_assessment.py --target model-context-protocol-security.md`
3. Orchestrator attempts schema fetch
4. SSL error → Auto-fallback to bundled schemas
5. Analysis runs using cached data
6. Report auto-generated
7. Results presented

**Result**: Fully automated with graceful error handling

### After Phase 2 (v2.0.0)
**Additional Benefits**:
- SKILL.md: 539 → ~200 lines (63% reduction)
- Context load: ~4585 → ~2000 tokens (56% reduction)
- Time to first action: ~30s → <5s
- Conciseness score: 23/100 → 60+/100

## Implementation Strategy

### Phase 1 Workflow (following WORKFLOW.md)

1. **Create GitHub Issue**
   ```bash
   gh issue create \
     --title "ai-risk-mapper: Add workflow automation and offline support (v1.1.0)" \
     --body "See docs/plans/2026-01-22-ai-risk-mapper-automation-overhaul.md Phase 1"
   ```

2. **Update IMPROVEMENT_PLAN.md**
   - Add to Planned table: `| #<issue> | Critical | Workflow automation & offline support | In Progress |`

3. **Implement changes**
   - Create orchestrator script
   - Bundle CoSAI schemas
   - Update fetch script with fallback
   - Update SKILL.md with orchestrator instructions
   - Test all scenarios

4. **Two-commit release**
   - Commit 1: Implementation files
   - Commit 2: Version bump + IMPROVEMENT_PLAN.md update

### Phase 2 Workflow

1. **Create separate GitHub Issue** for documentation overhaul
2. **Update IMPROVEMENT_PLAN.md** Planned table
3. **Implement restructuring**
4. **Two-commit release** (v2.0.0)

### Phase 3 Workflow

Each future enhancement gets its own issue and follows standard workflow.

## Metrics for Success

| Metric | Current (v1.0.0) | Target v1.1.0 | Target v2.0.0 |
|--------|------------------|---------------|---------------|
| Automation Rate | 0% | 95% | 95% |
| Network Failure Handling | None | Graceful fallback | Graceful fallback |
| SKILL.md Length | 539 lines | 539 lines | <300 lines |
| SKILL.md Tokens | ~4585 | ~4585 | ~2000 |
| Time to First Action | ~30s | <5s | <5s |
| Error Recovery | Manual | Automatic | Automatic |
| Conciseness Score | 23/100 | 23/100 | 60+/100 |

## Risk Mitigation

### Risk: Breaking Existing Workflows
**Mitigation**:
- Phase 1 is backward compatible (all individual scripts still work)
- Orchestrator is additive, doesn't replace manual workflow
- Users can still run scripts individually

### Risk: Bundled Schemas Become Stale
**Mitigation**:
- Orchestrator prefers fresh schemas (network fetch first)
- Bundled schemas only used as fallback
- Document schema update process in IMPROVEMENT_PLAN.md
- Consider automation to fetch/bundle latest schemas periodically

### Risk: Orchestrator Script Complexity
**Mitigation**:
- Keep orchestrator focused on workflow coordination
- Reuse existing analyze_risks.py and generate_report.py logic
- Comprehensive error handling with clear messages
- Fallback to manual mode if orchestrator fails

## Dependencies

- Python 3.x with uv
- PyYAML (existing dependency)
- CoSAI schemas (will be bundled)
- No new external dependencies

## Open Questions

1. **Schema bundling**: Should we automate fetching latest schemas for bundling, or manually update?
   - **Recommendation**: Manual initially, automate in Phase 3

2. **Orchestrator options**: How much customization should orchestrator expose?
   - **Recommendation**: Start simple (--target, --offline, --output-dir), expand based on feedback

3. **Backward compatibility**: Should old workflow remain in SKILL.md?
   - **Recommendation**: Yes, as "Manual Workflow (For Customization)" section

## References

- **Recommendations Source**: `/ai-risk-mapper-improvement-recommendations.md`
- **Current SKILL.md**: `skills/ai-risk-mapper/SKILL.md`
- **Current IMPROVEMENT_PLAN.md**: `skills/ai-risk-mapper/IMPROVEMENT_PLAN.md`
- **Workflow Guide**: `/WORKFLOW.md`
