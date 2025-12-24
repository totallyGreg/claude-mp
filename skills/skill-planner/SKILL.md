---
name: skill-planner
description: Provides systematic planning for complex skill improvements. Invoked by Skillsmith when improvements require structured planning with git branch workflow (research → plan → approve → implement). Use when Skillsmith delegates complex changes, or when explicit planning workflow is needed. Triggers when invoked by Skillsmith or when user explicitly requests planning.
metadata:
  version: "1.1.0"
compatibility: Requires git, python3, access to repository with .git directory
---

# Skill Planner

Manages the complete improvement planning lifecycle using git branches as the state mechanism.

## Core Workflow

The planning workflow follows four phases with explicit gates:

```
Research → Plan → Approve → Implement
```

Each phase is distinct and requires user approval to proceed.

## When to Use

Use skill-planner when:
- Planning improvements to existing skills
- Creating structured improvement plans
- Managing plan refinements and iterations
- Ensuring proper approval before implementation
- Tracking plan completion

## How It Works

### Sub-Skill Mode

When invoked by Skillsmith for complex skill improvements:
- Receives improvement context and goals from Skillsmith
- Runs complete workflow (research → plan → approve → implement)
- Returns control to Skillsmith with implementation results
- Skillsmith handles final version management and marketplace sync

This mode enables Skillsmith to delegate complex improvements while handling quick updates directly.

### Git Branch-Based Planning

Each improvement plan gets its own git branch:
- Branch name: `plan/{skill-name}-{description}-{date}`
- Example: `plan/skillsmith-metrics-20251221`
- Plan document: `PLAN.md` in the branch
- State tracked via: git commits, tags, and plan status

### State Transitions

```
draft → approved → implemented → completed
```

- **draft**: Plan is being created and refined
- **approved**: Plan explicitly approved by user (git tag created)
- **implemented**: Changes implemented in plan branch
- **completed**: Plan branch merged to main

## Workflow Phases

### Phase 1: Research

**Trigger:** User: "I want to improve {skill-name}"

**Actions:**
1. Detect skill location (repository vs installed)
2. Invoke skillsmith for deep research
3. Receive research findings:
   - Understanding of skill intent
   - Domain classification
   - Best practices for domain
   - Similar skills as examples
   - Current implementation analysis
   - Spec compliance check
   - Synthesized recommendations

4. Present research summary to user

**Output:**
```
Research complete for {skill-name}:

Understanding:
  Purpose: ...
  Domain: ...
  Complexity: ...

Key Findings:
  - Finding 1
  - Finding 2
  - Finding 3

Recommendations:
  1. High priority recommendation
  2. Medium priority recommendation
  ...

Next: 'Create plan' to formalize these findings
```

### Phase 2: Plan

**Trigger:** User: "Create plan"

**Actions:**
1. Create planning branch:
   ```bash
   git checkout -b plan/{skill-name}-{short-desc}-{YYYYMMDD}
   ```

2. Create PLAN.md from research findings:
   - Use template (see `references/plan_template.md`)
   - Populate with research recommendations
   - Add expected metrics from skillsmith

3. Commit PLAN.md to branch:
   ```bash
   git add PLAN.md
   git commit -m "Initial plan for {skill-name} improvement"
   ```

4. Show plan to user

**Refinement Loop:**

**Trigger:** User: "Refine plan - {instructions}"

**Actions:**
1. Invoke skillsmith with refinement instructions
2. Update PLAN.md:
   - Increment version (v1 → v2)
   - Update proposed changes
   - Update expected metrics
   - Add revision note

3. Commit updated PLAN.md
4. Show updated plan with diff

**Continues** until user approves

**Output:**
```
Plan created/updated (v{N}):

Proposed Changes:
  1. Change description
     Impact: metrics

  2. Another change
     Impact: metrics

Expected Outcome:
  Metrics before → after
  Score: before → after

Review and refine more, or: 'Approve plan'
```

### Phase 3: Approve

**Trigger:** User: "Approve plan"

**Actions:**
1. Verify plan state = draft

2. Update PLAN.md:
   - Status: draft → approved
   - Approved by: {user}
   - Approved at: {timestamp}

3. Commit approval:
   ```bash
   git add PLAN.md
   git commit -m "Approved plan for {skill-name}"
   ```

4. Create git tag:
   ```bash
   git tag approved/{skill-name}-{short-desc}-{YYYYMMDD}
   ```

**Output:**
```
Plan approved! ✓
Branch: plan/{skill-name}-{desc}-{date}
Tag: approved/{skill-name}-{desc}-{date}

Ready to implement: 'Implement approved plan'
```

### Phase 4: Implement

**Trigger:** User: "Implement approved plan"

**Actions:**
1. Verify plan status = approved (check for git tag)

2. Read PLAN.md to get approved changes

3. Invoke skillsmith with implementation instructions:
   - "Implement this approved plan: [plan details]"

4. skillsmith implements changes in SAME branch

5. skillsmith measures after metrics

6. skillsmith reports before/after comparison

7. Update PLAN.md:
   - Status: approved → implemented
   - Implemented at: {timestamp}
   - Actual metrics: {from skillsmith}

8. Commit implementation marker:
   ```bash
   git add PLAN.md
   git commit -m "Implementation complete for {skill-name}"
   ```

**Output:**
```
Implementation complete! ✓

Before/After Metrics:
  Metric 1: before → after
  Metric 2: before → after

Current branch: plan/{skill-name}-{desc}-{date}

Next steps:
  - Test the changes
  - If good: Merge to main (or create PR)
  - If issues: Make adjustments and re-test
```

### Phase 5: Completion (After Merge)

**Trigger:** Plan branch merged to main (auto-detected)

**Actions:**
1. Detect merge to main (git hook or manual check)

2. Update PLAN.md in archive:
   - Status: implemented → completed
   - Completed at: {timestamp}
   - Merged in commit: {sha}

3. Move PLAN.md to archive:
   ```bash
   mkdir -p completed/{skill-name}/
   cp PLAN.md completed/{skill-name}/{desc}-{date}.md
   ```

4. Optionally delete planning branch or keep for history

**Output:**
```
Plan completed! ✓

Improvement archived: completed/{skill-name}/{desc}-{date}.md
Branch: {kept|deleted} for history
```

## Repository Detection

skill-planner determines where work should happen:

**Skill in own marketplace (claude-mp):**
→ Work in repository branch (always)

**Skill installed from own marketplace:**
→ Find in repository, work in branch

**Skill installed but NOT in marketplace:**
→ Ask user:
  - "Clone to repository and work there"
  - "Create plan only (no implementation)"
  - "Cancel"

**Unknown skill:**
→ Ask user:
  - "Create new skill in repository"
  - "Specify path to existing skill"
  - "Cancel"

## Scripts

- `scripts/create_plan.py` - Create planning branch and PLAN.md
- `scripts/update_plan.py` - Update PLAN.md with revisions
- `scripts/approve_plan.py` - Mark plan as approved, create git tag
- `scripts/complete_plan.py` - Archive completed plan
- `scripts/detect_repo.py` - Determine skill location and work mode

## References

- [PLAN.md Template](references/plan_template.md) - Complete template with all sections
- [Git Branch Workflow](references/git_workflow.md) - Detailed git operations
- [State Machine](references/state_machine.md) - Plan state transitions

## Safety Features

**Prevents Premature Implementation:**
- Cannot implement without approval
- Approval requires explicit "Approve plan" command
- Implementation requires explicit "Implement approved plan" command
- Git tags track approval state

**Repository Protection:**
- Auto-detects repository vs installed plugins
- Refuses to modify installed plugins directly
- Always works in repository branches
- Changes isolated until merge

**Plan History:**
- All plan versions tracked in git commits
- Planning branch preserved after merge (optional)
- Completed plans archived for reference
- Full audit trail of decisions

## Workflow Safety

### Two-Phase Approval

Implementation requires TWO explicit user commands:

1. **"Approve plan"** - Marks plan as ready
2. **"Implement approved plan"** - Actually executes

This prevents accidental implementation.

### Branch Isolation

All planning and implementation happens in dedicated branch:
- Main branch remains untouched until merge
- Easy to abandon plan (delete branch)
- Can have multiple concurrent plans
- Clean rollback if needed

### State Validation

Every phase transition checks state:
- Cannot approve without plan
- Cannot implement without approval
- Cannot complete without implementation
- Git tags enforce state

## Example Session

```
User: "I want to improve skillsmith"

skill-planner:
✓ Research phase starting...
[skillsmith researches]
✓ Research complete
  Key findings: [summary]
  Next: "Create plan"

User: "Create plan"

skill-planner:
✓ Branch: plan/skillsmith-improvement-20251221
✓ Plan created (v1)
  Proposed: [changes]
  Expected: [metrics]
  Review or: "Approve plan"

User: "Refine plan - focus more on X"

skill-planner:
✓ Plan updated (v2)
  Changes: [diff]
  Review or: "Approve plan"

User: "Approve plan"

skill-planner:
✓ Plan approved
✓ Tag: approved/skillsmith-improvement-20251221
  Ready: "Implement approved plan"

User: "Implement approved plan"

skill-planner:
✓ Implementing...
[skillsmith implements]
✓ Implementation complete
  Before/After: [metrics]
  Test, then merge to main

User: [tests, then merges to main]

skill-planner:
✓ Plan completed
✓ Archived: completed/skillsmith/improvement-20251221.md
```

## Integration with Skillsmith

skill-planner works as a specialized sub-skill invoked BY Skillsmith:

**When Invoked:**
- Skillsmith analyzes skill improvement request
- Determines change is complex (multi-file, structural, >50 lines)
- Invokes skill-planner with improvement context

**During Workflow:**
- skill-planner executes research → plan → approve → implement phases
- Uses skillsmith's evaluation scripts (evaluate_skill.py, research_skill.py)
- Manages git branch workflow and PLAN.md
- Implements approved changes

**After Completion:**
- Returns implementation results to Skillsmith
- Skillsmith determines version bump (MINOR or MAJOR)
- Skillsmith calls marketplace-manager for version sync and commit
- skill-planner archives completed plan after merge

## Integration with marketplace-manager

After plan is implemented and merged:
- marketplace-manager auto-detects changes
- Syncs marketplace.json versions
- Adds to commit automatically

## Best Practices

**When Planning:**
- Be specific about what you want to achieve
- Iterate on the plan multiple times
- Don't rush to approval - refine until right
- Consider impact on existing functionality

**When Refining:**
- Focus on one aspect at a time
- Ask for before/after metrics
- Compare alternatives
- Check alignment with domain best practices

**When Approving:**
- Review full plan carefully
- Verify expected metrics are reasonable
- Ensure all changes are necessary
- Consider implementation effort

**When Implementing:**
- Test thoroughly before merging
- Verify metrics match expectations
- Check for unintended side effects
- Validate with quick_validate.py

## Troubleshooting

**"Cannot find skill":**
- Check skill name spelling
- Verify skill is in repository or installed
- Use full path if needed

**"Plan already exists":**
- Check for existing planning branch
- Delete old branch or use different name
- Complete or abandon existing plan first

**"Cannot approve without plan":**
- Ensure you've created plan first
- Check current branch is planning branch
- Verify PLAN.md exists

**"Cannot implement without approval":**
- Run "Approve plan" first
- Check for approved/* git tag
- Verify plan status = approved

## See Also

- **skillsmith** - Main actor for all skill work; invokes skill-planner for complex improvements
- **marketplace-manager** - Handles version sync, commits, and marketplace updates
- [THREE_SKILL_ARCHITECTURE.md](../../THREE_SKILL_ARCHITECTURE.md) - Complete system architecture (if exists)
