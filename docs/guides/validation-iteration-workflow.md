# Validation & Iteration Workflow Guide

This guide documents the complete validation iteration workflow for skill development and improvement cycles.

---

## Overview

The validation iteration workflow is the continuous cycle of:
1. Evaluating skills to understand current state
2. Identifying improvements via metrics
3. Implementing improvements
4. Validating improvements
5. Repeating until quality goals met

This process ensures skills continuously improve while maintaining backwards compatibility and quality standards.

---

## Validation Workflow Architecture

```
┌─────────────────────────────────────────────────────┐
│         Skill Development Cycle                     │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 1. EVALUATE (Full Evaluation)                       │
│    - Run: validate_workflow.py --mode full          │
│    - Output: Baseline metrics (Conc/Comp/Spec/Disc)│
│    - Identify: Improvement opportunities            │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 2. IDENTIFY IMPROVEMENTS                            │
│    - Review metrics against quality goals           │
│    - Select target areas (conciseness, etc)         │
│    - Set specific improvement targets               │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 3. IMPLEMENT CHANGES                                │
│    - Make targeted improvements                     │
│    - Validate periodically with quick mode          │
│    - Commit when stable                             │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 4. VALIDATE IMPROVEMENTS (Full Evaluation)          │
│    - Run: validate_workflow.py --mode full          │
│    - Measure: New metrics                           │
│    - Compare: Before/after metrics                  │
│    - Verify: No regressions                         │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 5. DECIDE: Release or Iterate?                      │
│    - If metrics meet goals → RELEASE                │
│    - If more improvements needed → Back to step 2   │
└─────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────┐
│ 6. RELEASE (if decision is release)                 │
│    - Run: validate_workflow.py --mode release       │
│    - Update: IMPROVEMENT_PLAN.md metrics            │
│    - Bump: Version in SKILL.md                      │
│    - Commit: Release commit                         │
│    - Sync: marketplace-manager                      │
└─────────────────────────────────────────────────────┘
```

---

## Step-by-Step Validation Iteration

### Step 1: Evaluate Current State

**Command:**
```bash
uv run skills/skillsmith/scripts/validate_workflow.py skills/my-skill --mode full
```

**What to look for:**
- **Conciseness score:** Is SKILL.md too large? (Target: >70/100)
- **Complexity score:** Is structure too intricate? (Target: >80/100)
- **Spec Compliance:** Are all requirements met? (Target: 100/100)
- **Progressive Disclosure:** Is information well-distributed? (Target: 100/100)

**Record baseline metrics:**
```
Baseline Metrics (v1.0.0):
- Conciseness: 48/100
- Complexity: 90/100
- Spec Compliance: 100/100
- Progressive: 100/100
- Overall: 85/100
```

---

### Step 2: Identify Improvement Opportunities

**Analysis questions:**
1. Which metric is lowest? Start there.
2. What specific content could be moved/consolidated?
3. Are there regressions from previous versions?
4. What would unblock other improvements?

**Set improvement targets:**
```
Target Metrics (v1.5.0):
- Conciseness: 48 → 70/100 (+22 points)
- Complexity: 90 → 90/100 (maintain)
- Spec Compliance: 100 → 100/100 (maintain)
- Progressive: 100 → 100/100 (maintain)
- Overall: 85 → 90/100 (+5 points)
```

**Create improvement plan:**
- GitHub Issue with specific tasks
- Break into phases if large
- Prioritize by impact and effort
- Link to IMPROVEMENT_PLAN.md

---

### Step 3: Implement Changes

**During implementation:**

1. **Make incremental changes**
   - Focus on one improvement area at a time
   - Keep commits focused and reviewable

2. **Validate frequently**
   ```bash
   # After each logical change
   uv run scripts/validate_workflow.py skills/my-skill --mode quick
   ```

3. **Fix issues immediately**
   - Don't accumulate validation errors
   - Quick mode allows warnings; fix them anyway

4. **Track progress**
   - Update GitHub Issue as you complete tasks
   - Add metrics if doing multiple iterations

---

### Step 4: Validate Improvements

**Before claiming victory:**

**Command:**
```bash
uv run scripts/validate_workflow.py skills/my-skill --mode full
```

**Verification checklist:**
- [ ] All metrics improved or maintained
- [ ] No regressions from baseline
- [ ] Overall score meets target
- [ ] All references still work
- [ ] Spec compliance maintained

**Metric comparison:**
```
Before (v1.0.0):      After (v1.5.0):       Change:
- Conc: 48/100        - Conc: 70/100        +22 ✅
- Comp: 90/100        - Comp: 90/100        - ✅
- Spec: 100/100       - Spec: 100/100       - ✅
- Prog: 100/100       - Prog: 100/100       - ✅
- Overall: 85/100     - Overall: 90/100     +5 ✅
```

---

### Step 5: Decide: Release or Iterate?

**Release criteria (all must be true):**
- ✅ Target metrics achieved
- ✅ No regressions from baseline
- ✅ All spec compliance maintained
- ✅ All tests pass
- ✅ Documentation complete

**Iterate criteria (if any are true):**
- Metrics still below target
- Regressions detected
- Spec compliance dropped
- New improvement opportunities identified

**Decision tree:**
```
Metrics meet target?
├─ YES: All validation pass?
│       ├─ YES: READY FOR RELEASE
│       └─ NO: Fix failures, re-validate
└─ NO: More improvements possible?
       ├─ YES: Back to Step 2 (Identify improvements)
       └─ NO: Release as-is or defer improvements
```

---

### Step 6: Release

**Pre-release checklist:**

1. **Final validation (strict mode):**
   ```bash
   uv run scripts/validate_workflow.py skills/my-skill --mode release
   ```
   - All errors fixed
   - All warnings resolved

2. **Update IMPROVEMENT_PLAN.md:**
   - Add new version row to Version History table
   - Copy metrics from validation output
   - Link to GitHub Issue
   - Update Active Work section

3. **Update version:**
   - Edit SKILL.md metadata.version
   - Determine PATCH/MINOR/MAJOR based on changes
   - PATCH: Bug fixes, minor improvements
   - MINOR: New features, improvements
   - MAJOR: Breaking changes, major rewrites

4. **Commit changes:**
   ```bash
   git add SKILL.md IMPROVEMENT_PLAN.md
   git commit -m "chore: Release skill-name vX.Y.Z with improvements

   Phase X completion: [description]

   Metrics:
   - Conciseness: 48 → 70/100 (+22)
   - Overall: 85 → 90/100 (+5)

   Closes #[issue-number]"
   ```

5. **Sync to marketplace:**
   ```bash
   # If using marketplace-manager
   # It will auto-sync and commit marketplace.json
   ```

---

## Validation Modes Recap

### Quick Mode (Development)
```bash
uv run scripts/validate_workflow.py <skill> --mode quick
```
- **Purpose:** Fast feedback during development
- **Speed:** <1 second
- **Use:** After each change
- **Exit:** 0=valid, 1=errors, 2=warnings
- **Check:** Structural only (no metrics)

### Full Mode (Evaluation)
```bash
uv run scripts/validate_workflow.py <skill> --mode full
```
- **Purpose:** Complete quality assessment
- **Speed:** 2 seconds
- **Use:** Baseline, improvement identification, verification
- **Exit:** 0=valid, 1=issues
- **Check:** All metrics + spec compliance

### Release Mode (Strict)
```bash
uv run scripts/validate_workflow.py <skill> --mode release
```
- **Purpose:** Pre-release quality gate
- **Speed:** 2 seconds
- **Use:** Before version bump and release
- **Exit:** 0=ready, 1=not ready
- **Check:** Everything in full mode + strict enforcement

---

## Common Validation Patterns

### Pattern 1: Fixing Conciseness Issues

**Identify:**
```bash
validate_workflow.py --mode full
# Result: Conciseness: 48/100 (SKILL.md: 309 lines)
```

**Improve:**
1. Identify detailed sections that can be moved to references/
2. Create new reference file(s)
3. Replace detailed sections with brief summaries + pointers
4. Verify quick validation: `--mode quick`

**Verify:**
```bash
validate_workflow.py --mode full
# Result: Conciseness: 70/100 (SKILL.md: 220 lines)
```

### Pattern 2: Fixing Spec Compliance

**Identify:**
```bash
validate_workflow.py --mode full
# Result: References not mentioned in SKILL.md
```

**Improve:**
1. Add reference mention to SKILL.md
2. Update Advanced Topics list
3. Ensure backtick-wrapped references

**Verify:**
```bash
validate_workflow.py --mode quick
# Result: Spec Compliance: 100/100
```

### Pattern 3: Maintaining Quality Through Iteration

**Establish baseline:**
```bash
validate_workflow.py --mode full
# Baseline: Overall: 85/100
```

**Make improvements:**
- Change 1: Conciseness improvements
- Change 2: Content consolidation
- Change 3: Reference enhancement

**Validate after each change:**
```bash
validate_workflow.py --mode quick  # After each change
validate_workflow.py --mode full   # After group of changes
```

**Verify no regressions:**
- Overall score maintained or improved
- Spec compliance maintained at 100%
- Progressive disclosure maintained at 100%

---

## Metrics Interpretation Guide

### When to Improve Each Metric

**Conciseness (<70):**
- Move detailed content to references/
- Consolidate related information
- Use reference pointers instead of inline detail
- Remove redundant explanations

**Complexity (<80):**
- Flatten nested structures
- Reduce code block depth
- Simplify workflow steps
- Improve section organization

**Progressive Disclosure (<100):**
- Ensure 3-level loading system
- Metadata always available
- SKILL.md available on-demand
- References available as needed

**Spec Compliance (<100):**
- Fix naming conventions
- Add required fields
- Fix character limits
- Add missing metadata

---

## Integration with GitHub Issues

**Create improvement issue:**
```markdown
# Title: [Skill name]: Improve conciseness to 70+/100

**Goal:** Improve conciseness score from 48 to 70/100 by consolidating content

**Current Metrics:**
- Conciseness: 48/100
- Overall: 85/100

**Target Metrics:**
- Conciseness: 70/100
- Overall: 88/100

**Tasks:**
- [ ] Phase 1: Move Step 4-6 content to references
- [ ] Phase 2: Update SKILL.md with reference pointers
- [ ] Phase 3: Validate and measure improvements

**Related:** Issue #[number]
```

**Track progress:**
- Check off tasks as completed
- Comment with metric updates
- Link validation outputs
- Close with final metrics

---

## Quick Reference Checklist

### During Development
- [ ] Make changes
- [ ] Run `validate_workflow.py --mode quick`
- [ ] Fix any errors
- [ ] Commit

### Before Improvement Planning
- [ ] Run `validate_workflow.py --mode full`
- [ ] Record baseline metrics
- [ ] Identify improvement targets
- [ ] Create GitHub Issue with tasks

### During Improvements
- [ ] Implement changes focused on one area
- [ ] Run `validate_workflow.py --mode quick` frequently
- [ ] Update GitHub Issue progress

### Before Release
- [ ] Run `validate_workflow.py --mode full`
- [ ] Verify all improvements
- [ ] Check for regressions
- [ ] Run `validate_workflow.py --mode release`
- [ ] Update IMPROVEMENT_PLAN.md
- [ ] Bump version in SKILL.md
- [ ] Commit and sync to marketplace

---

## Troubleshooting

**Quick validation fails but shouldn't:**
- Check for absolute paths (use relative)
- Verify SKILL.md frontmatter syntax
- Ensure name matches directory

**Metrics don't improve as expected:**
- Verify changes actually committed
- Check file saved with correct content
- Re-run validation to get latest metrics

**Regressions detected during improvement:**
- Review what changed
- Understand why metric dropped
- Consider if trade-off is acceptable
- Document if intentional regression

---

## Best Practices

1. **Validate frequently** - Don't let issues accumulate
2. **Track baselines** - Record metrics before making changes
3. **Iterate systematically** - One improvement area at a time
4. **Verify no regressions** - Always check before/after
5. **Document progress** - Use GitHub Issues to track work
6. **Release cleanly** - Use strict mode before bumping version
7. **Learn from metrics** - Use patterns to improve other skills

---

## See Also

- `docs/lessons/validation-feedback-loop.md` - Cross-skill learnings
- `skills/skillsmith/references/validation_tools_guide.md` - Validation tool details
- `skills/skillsmith/references/integration_guide.md` - Marketplace integration
- `WORKFLOW.md` - Repository-wide workflow patterns
