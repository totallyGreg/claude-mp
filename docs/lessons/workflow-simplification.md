# Workflow Simplification: From skill-planner to WORKFLOW.md Pattern

**Date**: 2026-01-23
**Issue**: [#5](https://github.com/totallyGreg/claude-mp/issues/5)
**Reason**: Consolidate to single source of truth

## Background

The claude-mp repository previously supported two competing planning paradigms:

1. **skill-planner**: Git branch workflow with PLAN.md files and git tags
2. **WORKFLOW.md**: GitHub Issues as source of truth with IMPROVEMENT_PLAN.md tables

This created confusion and competing sources of truth. The WORKFLOW.md pattern emerged as superior due to better cross-machine accessibility, web-based issue tracking, and simpler state management.

## What Changed

### Deprecated: skill-planner

The skill-planner skill has been completely removed from the marketplace and repository. It used a git branch-based workflow:

\`\`\`
plan/{skill}-{desc}-{date} branch → PLAN.md → git tags → merge to main
\`\`\`

**Why deprecated:**
- Required git fetch for cross-machine sync
- State tracked in git tags (difficult to query)
- PLAN.md files permanent in branches (clutter)
- Competing with WORKFLOW.md pattern already in use

### Current Standard: WORKFLOW.md Pattern

All improvements now follow a unified pattern:

\`\`\`
GitHub Issues (source of truth) → IMPROVEMENT_PLAN.md table → docs/plans/ (ephemeral)
\`\`\`

**Advantages:**
- Web-accessible from any machine
- Issue checkboxes provide clear progress tracking
- IMPROVEMENT_PLAN.md shows history in simple table
- Ephemeral planning docs reduce clutter
- Single source of truth (no branch/tag confusion)

## Migration Guide

### For Simple Changes

Work directly in main branch:

1. Make changes
2. Commit with clear message
3. Link commit to issue if tracking work

### For Complex Changes

Follow WORKFLOW.md pattern:

1. **Create GitHub Issue**:
   \`\`\`bash
   gh issue create \\
     --title "Descriptive title" \\
     --body "**Tasks:**
   - [ ] Task 1
   - [ ] Task 2
   - [ ] Task 3"
   \`\`\`

2. **Add to IMPROVEMENT_PLAN.md**:
   \`\`\`markdown
   | Issue | Priority | Title | Status |
   |-------|----------|-------|--------|
   | #123  | High     | Feature description | Open |
   \`\`\`

3. **Create planning doc** (if needed for design):
   \`\`\`bash
   # Create in docs/plans/ with date prefix
   touch docs/plans/2026-01-23-skill-name-feature.md

   # Link from GitHub Issue
   # Can delete after completion
   \`\`\`

4. **Implement and track**:
   - Check off tasks in GitHub Issue as completed
   - Update code following the plan
   - Close issue when done

5. **Update IMPROVEMENT_PLAN.md**:
   - Move from Planned to Completed section
   - Add completion date and summary

### Workflow Comparison

| Aspect | skill-planner (OLD) | WORKFLOW.md (NEW) |
|--------|---------------------|-------------------|
| Source of truth | PLAN.md in git branches | GitHub Issues |
| State tracking | Git tags (approved/*) | Issue checkboxes |
| Planning docs | PLAN.md (permanent in branch) | docs/plans/ (ephemeral) |
| History | Completed plans archived | Completed table in IMPROVEMENT_PLAN.md |
| Cross-machine | Requires git fetch | Web-accessible GitHub |
| Complexity | High (git workflows) | Low (web UI + markdown) |

## Skills Affected

The following skills have been updated to remove skill-planner references:

- **skillsmith**: Updated to use WORKFLOW.md pattern for complex improvements
  - \`SKILL.md\`: Removed skill-planner delegation guidance
  - \`references/improvement_workflow_guide.md\`: Rewritten for WORKFLOW.md pattern
  - \`references/integration_guide.md\`: Updated integration patterns
  - \`references/research_guide.md\`: Updated integration section
  - \`references/validation_tools_guide.md\`: Updated integration examples
  - \`references/reference_management_guide.md\`: Updated workflow references

- **marketplace-manager**: Updated workflow integration documentation
  - \`SKILL.md\` line 48: Removed skill-planner → Skillsmith workflow

## Lessons Learned

### What Worked

- **Ephemeral planning docs**: docs/plans/ pattern works well for pre-work design
- **Simple tables**: IMPROVEMENT_PLAN.md table format is easy to maintain
- **GitHub Issues**: Web accessibility and issue checkboxes provide superior UX
- **Single source of truth**: Eliminates confusion about where to look for status

### What Didn't Work

- **Git branch isolation**: Too much ceremony for most improvements
- **PLAN.md permanence**: Created clutter in git history
- **Tag-based state**: Difficult to query and visualize
- **Competing paradigms**: Two systems created decision fatigue

### Key Takeaways

1. **Web-first wins**: Cross-machine accessibility is critical
2. **Simple beats complex**: Markdown tables > git workflows
3. **Ephemeral is OK**: Not everything needs to be permanent
4. **Consistency matters**: One pattern > multiple options

## Questions?

- Review [WORKFLOW.md](/WORKFLOW.md) for complete pattern documentation
- Check [GitHub Issue #5](https://github.com/totallyGreg/claude-mp/issues/5) for deprecation details
- See skillsmith's \`references/improvement_workflow_guide.md\` for implementation guidance
