# Plan: OmniFocus-Manager Skill Refinement

**Date:** 2026-01-18
**Status:** Completed (v4.4.0)
**GitHub Issue:** N/A (should have been #123)

## Overview

Refine omnifocus-manager skill to make plugin generation deterministic and prevent agents from skipping critical workflow steps.

**Problem:** Agents skip `generate_plugin.js`, don't run TypeScript validation, don't run `validate-plugin.sh`

**Root Cause:** Workflow buried in SKILL.md, weak enforcement, tools in wrong directories

**Solution:** Restructure SKILL.md with CRITICAL workflow at top, move tools to scripts/, add self-check mechanisms

## Completed Implementation

See `skills/omnifocus-manager/IMPROVEMENT_PLAN.md` v4.4.0 entry for full details.

**Key Changes:**
- ⚡ CRITICAL workflow moved to line 23
- Validation tools moved to scripts/
- COMPLIANCE SELF-CHECK added
- plugin-templates/README.md created
- All references updated

## Lessons Learned

See `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` for complete refinement errors and skillsmith improvement recommendations.

---

# Skillsmith Integration Improvements

Based on this refinement experience, the following improvements should be added to skillsmith's IMPROVEMENT_PLAN.md workflow:

## 1. GitHub Issue Integration

**Problem:** IMPROVEMENT_PLAN.md tracking is manual and error-prone. No way to verify if improvement is actually complete beyond what's written in the document.

**Solution:** Link improvements to GitHub Issues for automated state tracking.

### Proposed Enhancement to IMPROVEMENT_PLAN.md Structure

```markdown
## 🔮 Planned Improvements
> Last Updated: YYYY-MM-DD

### High Priority

#### 1. Feature Name
**GitHub Issue:** #123
**Status:** ![Issue Status](https://img.shields.io/github/issues/detail/state/user/repo/123)
**Goal:** Description
**Planned Features:**
- [ ] Feature 1 (tracked in issue)
- [ ] Feature 2 (tracked in issue)
```

### Benefits

1. **Single source of truth:** GitHub issue checklist is the canonical state
2. **Cross-machine sync:** Issue state automatically synced
3. **Verifiable completion:** Can't mark complete if issue still open
4. **Better resumption:** Full context in issue, linked from IMPROVEMENT_PLAN.md

## 2. Automated Sync Validation

**Problem:** IMPROVEMENT_PLAN.md can claim completion while GitHub issue is still open.

**Solution:** Validation script checks for mismatches.

### Implementation

Add to `scripts/evaluate_skill.py`:

```python
def validate_issue_sync(improvement_plan_path):
    """Validate GitHub issue references match actual issue state."""
    # Parse IMPROVEMENT_PLAN.md for issue references
    # Check if completed improvements have closed issues
    # Check if planned improvements reference open issues

    errors = []

    for improvement in completed_improvements:
        if improvement.has_github_issue:
            issue_state = gh_api.get_issue_state(improvement.issue_number)
            if issue_state == "open":
                errors.append(
                    f"❌ Improvement marked complete but #{improvement.issue_number} still open"
                )

    return errors
```

Usage:
```bash
python3 scripts/evaluate_skill.py --check-improvement-plan --check-github-sync skills/my-skill
```

## 3. Two-Way Linking Pattern

**Problem:** Issue references IMPROVEMENT_PLAN.md but IMPROVEMENT_PLAN.md doesn't always reference issue.

**Solution:** Enforce bidirectional links.

### Skillsmith Template Update

When creating improvement in IMPROVEMENT_PLAN.md, skillsmith should:

1. **Prompt for GitHub integration:**
   ```
   Create GitHub issue for this improvement? (y/n)
   ```

2. **If yes, generate issue body from IMPROVEMENT_PLAN.md:**
   ```bash
   gh issue create \
     --title "skill-name: Feature Name" \
     --body "$(extract_improvement_details IMPROVEMENT_PLAN.md 1)" \
     --label enhancement \
     --assignee @me
   ```

3. **Update IMPROVEMENT_PLAN.md with issue link:**
   ```markdown
   #### 1. Feature Name
   **GitHub Issue:** #123
   ```

4. **Add comment to issue with IMPROVEMENT_PLAN.md reference:**
   ```bash
   gh issue comment 123 --body "Tracking in IMPROVEMENT_PLAN.md improvement #1"
   ```

## 4. Issue-Driven Completion Workflow

**Problem:** Manual workflow is error-prone (forget to close issue, forget to update IMPROVEMENT_PLAN.md).

**Solution:** Script that orchestrates the release workflow.

### Implementation

Create `scripts/release_improvement.sh`:

```bash
#!/bin/bash
# Usage: ./release_improvement.sh <skill-path> <improvement-number> <version>

SKILL_PATH=$1
IMPROVEMENT_NUM=$2
VERSION=$3

# 1. Extract improvement from Planned section
IMPROVEMENT_TEXT=$(extract_improvement "$SKILL_PATH/IMPROVEMENT_PLAN.md" "$IMPROVEMENT_NUM")
ISSUE_NUM=$(extract_issue_number "$IMPROVEMENT_TEXT")

# 2. Verify issue is closed
ISSUE_STATE=$(gh issue view "$ISSUE_NUM" --json state -q .state)
if [ "$ISSUE_STATE" != "CLOSED" ]; then
    echo "❌ Error: Issue #$ISSUE_NUM is still open"
    echo "   Close issue first or use --force"
    exit 1
fi

# 3. Update IMPROVEMENT_PLAN.md
# - Cut from Planned
# - Update header with version and date
# - Paste at top of Completed
# - Add to version history table

# 4. Update SKILL.md version

# 5. Stage changes
git add "$SKILL_PATH/IMPROVEMENT_PLAN.md" "$SKILL_PATH/SKILL.md"

# 6. Commit with issue reference
git commit -m "chore: Release $(basename $SKILL_PATH) v$VERSION

Closes #$ISSUE_NUM"

echo "✅ Released v$VERSION"
echo "   Issue: #$ISSUE_NUM"
echo "   Next: Review and push"
```

Usage:
```bash
# Close issue first
gh issue close 123 --comment "Implementation complete, ready for release"

# Run release script
./scripts/release_improvement.sh skills/my-skill 1 1.5.0
```

## 5. Status Dashboard

**Problem:** No overview of all skills' planned vs completed improvements.

**Solution:** Generate dashboard from IMPROVEMENT_PLAN.md files + GitHub issues.

### Implementation

Create `scripts/improvement_dashboard.py`:

```python
#!/usr/bin/env python3
"""Generate dashboard of all skill improvements."""

def generate_dashboard():
    """
    Scans all skills/*/IMPROVEMENT_PLAN.md files and generates:

    | Skill | Planned | In Progress | Completed (v) | GitHub Issues |
    |-------|---------|-------------|---------------|---------------|
    | omnifocus-manager | 3 | 1 (#124) | v4.4.0 | 🔗 |
    | skillsmith | 5 | 0 | v1.5.0 | 🔗 |
    """
    pass

if __name__ == "__main__":
    generate_dashboard()
```

Output to `docs/IMPROVEMENT_DASHBOARD.md`:
```markdown
# Skill Improvement Dashboard

Last updated: 2026-01-18

## Active Work

| Skill | Current | Planned | In Progress | GitHub |
|-------|---------|---------|-------------|--------|
| omnifocus-manager | v4.4.0 | 2 | #125 | [View](https://github.com/user/repo/issues?q=label:omnifocus-manager) |

## Summary

- Total skills: 9
- Total planned improvements: 23
- Active GitHub issues: 3
- Completed this month: 5
```

## 6. Release Checklist Enforcement

**Problem:** Easy to forget steps in release workflow.

**Solution:** Interactive release script with checklist.

### Implementation

Update `scripts/release_improvement.sh` with interactive mode:

```bash
#!/bin/bash
# Interactive release with checklist

echo "📋 Release Checklist for v$VERSION"
echo ""

# Checklist
confirm "✓ Implementation complete and tested?"
confirm "✓ GitHub issue closed?"
confirm "✓ IMPROVEMENT_PLAN.md updated?"
confirm "✓ SKILL.md version updated?"
confirm "✓ Validation passed?"

echo ""
echo "Running automated checks..."

# Run validation
python3 scripts/evaluate_skill.py --quick --check-improvement-plan "$SKILL_PATH"

# Check issue state
if [ -n "$ISSUE_NUM" ]; then
    STATE=$(gh issue view "$ISSUE_NUM" --json state -q .state)
    if [ "$STATE" = "OPEN" ]; then
        echo "❌ Issue #$ISSUE_NUM is still open"
        exit 1
    fi
    echo "✅ Issue #$ISSUE_NUM is closed"
fi

echo ""
echo "Proceeding with release..."
```

## Summary of Skillsmith Improvements

These improvements make IMPROVEMENT_PLAN.md workflow:

1. **Automated:** Script-driven instead of manual
2. **Verifiable:** GitHub issue state is source of truth
3. **Bidirectional:** Issue ↔ IMPROVEMENT_PLAN.md links enforced
4. **Safe:** Validation prevents inconsistent state
5. **Observable:** Dashboard shows all active work
6. **Resumable:** Full context in GitHub issue

### Implementation Priority

**High Priority (next release):**
1. Two-way linking pattern (skillsmith template update)
2. Release script with checklist
3. Validation for issue sync

**Medium Priority:**
4. Automated sync validation in evaluate_skill.py
5. Issue-driven completion workflow script

**Low Priority:**
6. Status dashboard (nice to have)

### Example Workflow After Implementation

```bash
# 1. Planning
skillsmith improve my-skill
# Prompts: "Create GitHub issue? (y/n)"
# Creates issue, updates IMPROVEMENT_PLAN.md with link

# 2. Implementation (over multiple sessions)
git commit -m "feat: implement X (#123)"
# GitHub issue shows progress, can resume on any machine

# 3. Mark complete
gh issue close 123 --comment "Implementation complete"

# 4. Release
./scripts/release_improvement.sh skills/my-skill 1 1.5.0
# Validates issue is closed
# Updates IMPROVEMENT_PLAN.md
# Creates release commit
# All automated!
```

---

## Next Steps

1. Add these improvements as numbered items to `skills/skillsmith/IMPROVEMENT_PLAN.md`
2. Create GitHub issue: "Integrate IMPROVEMENT_PLAN.md with GitHub Issues"
3. Implement high-priority items first
4. Test workflow with next skill improvement
5. Document in skillsmith references/

## References

- Completed work: `skills/omnifocus-manager/IMPROVEMENT_PLAN.md` v4.4.0
- Lessons learned: `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`
- Repository workflow: `WORKFLOW.md`
