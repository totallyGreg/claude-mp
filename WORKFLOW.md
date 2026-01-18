# Development Workflow

## Overview: Source of Truth Hierarchy

```
docs/lessons/         →  docs/plans/           →  GitHub Issues      →  IMPROVEMENT_PLAN.md
(Post-work learnings)    (Pre-work planning)      (Active tracking)      (Issue state summary)
                                                  (SOURCE OF TRUTH)
```

**Key Principle**: GitHub Issues are the canonical source of truth for work tracking. IMPROVEMENT_PLAN.md is a simple table that reflects issue state, not detailed planning.

## Quick Reference

**Simple changes**: Commit directly to main
**Complex work**: Lessons → Plans → Issues → IMPROVEMENT_PLAN.md

## Workflow Steps

### 1. Capture Learnings

After completing work, document lessons learned in `docs/lessons/<topic>.md`:
- What went wrong/right
- Patterns discovered
- Improvements needed across skills

**Example**: After refactoring error handling across multiple skills, create `docs/lessons/error-handling-patterns.md` to document the approach for future work.

### 2. Create Plan (for complex work)

When lessons identify complex improvements:
- Create `docs/plans/<YYYY-MM-DD>-<topic>.md`
- Research and design implementation
- Break down into concrete tasks
- Get user approval

**When to create a plan**:
- Multi-file changes
- Architectural decisions
- Work requiring research
- Changes affecting multiple skills

**Example**: `docs/plans/2026-01-18-unified-validation.md` for implementing consistent validation across all skills.

### 3. Create GitHub Issue (Source of Truth)

**GitHub Issues are the canonical source of work tracking:**

```bash
gh issue create \
  --title "skill-name: Feature Name" \
  --body "**Goal**: Brief description

**Plan**: See docs/plans/2026-01-18-topic.md

**Tasks**:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

**Related Skills**: skill-name, other-skill
" \
  --assignee @me
```

The issue checklist is the **source of truth** for work status.

**Why GitHub Issues?**
- Cross-machine accessible
- Native task tracking (checkboxes)
- Searchable, linkable, closable
- Timeline and discussion history
- Email notifications and mentions

### 4. Update IMPROVEMENT_PLAN.md (Reflects Issues)

**IMPORTANT**: IMPROVEMENT_PLAN.md is a **simple summary** of GitHub issue state, not detailed planning.

**Format - Simple Table:**

```markdown
## 🔮 Planned Improvements

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #123  | High     | Feature Name | In Progress |
| #124  | Medium   | Enhancement | Open |

_For details, see linked GitHub issues._

## ✅ Completed Improvements

| Version | Date | Issue | Title | Key Changes |
|---------|------|-------|-------|-------------|
| v1.5.0  | 2026-01-18 | #123 | Feature Name | • Improved validation performance<br>• Added caching layer<br>• Reduced memory usage by 30% |
| v1.4.0  | 2026-01-15 | #120 | Previous Feature | • Implemented new API endpoint<br>• Enhanced error handling<br>• See docs/lessons/api-refactor.md |

_For implementation details, see closed issues and docs/lessons/._
```

**Detailed information lives in:**
- GitHub Issue body and comments (active work)
- `docs/plans/` (pre-work design)
- `docs/lessons/` (post-work learnings)

**Example workflow:**
1. Create issue #123 with tasks
2. Add row to IMPROVEMENT_PLAN.md Planned table: `| #123 | High | Feature Name | Open |`
3. Start work: Update status to "In Progress"
4. Complete work: Move to Completed table with version, date, and key changes

### 5. Implementation & Release

**During work:**
```bash
# Reference issue in commits
git commit -m "feat(skill-name): Description (#123)"
git commit -m "fix(skill-name): Bug fix (#123)"
```

**On release (two commits):**

**Commit 1 - Implementation** (version unchanged):
```bash
git add path/to/implementation/files
git commit -m "feat(skill-name): Final changes (#123)"
```

**Commit 2 - Release** (version bump):
- Update IMPROVEMENT_PLAN.md table (move #123 from Planned → Completed)
- Add version, date, and key changes to Completed table
- Bump version in SKILL.md
- Close GitHub issue with commit message

```bash
git add skills/skill-name/IMPROVEMENT_PLAN.md skills/skill-name/SKILL.md
git commit -m "chore: Release skill-name v1.5.0

Closes #123"
```

**Post-release:**
- GitHub automatically closes issue #123
- IMPROVEMENT_PLAN.md now shows historical record in Completed table
- Issue remains searchable with full implementation discussion

## Directory Structure

```
docs/
  plans/          # Ephemeral planning (pre-work, can be deleted after issue created)
  lessons/        # Cross-skill learnings (permanent, referenced in IMPROVEMENT_PLAN.md)
skills/
  skill-name/
    IMPROVEMENT_PLAN.md  # Simple table format (permanent, travels with skill)
    SKILL.md            # Metadata and version
    references/         # Detailed documentation
```

## Information Architecture

**What goes where:**

| Type | Location | Purpose | Lifespan |
|------|----------|---------|----------|
| Active work tracking | GitHub Issues | Source of truth for in-progress work | Until closed |
| Pre-work planning | docs/plans/ | Design and research before implementation | Ephemeral |
| Post-work learnings | docs/lessons/ | Retrospectives and patterns | Permanent |
| Quick overview | IMPROVEMENT_PLAN.md | Simple table of planned/completed work | Permanent |
| Detailed docs | skills/*/references/ | Implementation guides and API docs | Permanent |

## Decision Tree

**Choosing the right approach:**

```
Is it a typo or small fix?
├─ Yes → Commit directly to main
└─ No → Is it complex (multi-file, architectural)?
    ├─ No → Add to IMPROVEMENT_PLAN.md table, create issue, implement
    └─ Yes → Follow full workflow:
        1. Document learnings in docs/lessons/ (if post-work)
        2. Create plan in docs/plans/ (if pre-work research needed)
        3. Create GitHub issue with task checklist
        4. Add to IMPROVEMENT_PLAN.md Planned table
        5. Implement with commits referencing issue
        6. Release with two-commit pattern
```

## Examples

### Simple Feature (No Planning Doc Needed)

```bash
# 1. Create issue
gh issue create --title "omnifocus-manager: Add task filtering" \
  --body "**Goal**: Filter tasks by project

**Tasks**:
- [ ] Add filter parameter to query
- [ ] Update documentation
- [ ] Add tests"

# 2. Add to IMPROVEMENT_PLAN.md Planned table
# | #125 | Medium | Add task filtering | Open |

# 3. Implement
git commit -m "feat(omnifocus-manager): Add task filtering (#125)"

# 4. Release
# Move #125 to Completed table with version v2.1.0
git commit -m "chore: Release omnifocus-manager v2.1.0

Closes #125"
```

### Complex Feature (With Planning Doc)

```bash
# 1. Create plan
# Create docs/plans/2026-01-20-typescript-validation.md
# Research and design TypeScript validation system

# 2. Create issue referencing plan
gh issue create --title "omnifocus-manager: Add TypeScript validation" \
  --body "**Goal**: Validate plugin code before execution

**Plan**: See docs/plans/2026-01-20-typescript-validation.md

**Tasks**:
- [ ] Implement TypeScript compiler integration
- [ ] Add validation to plugin execution
- [ ] Create error reporting system
- [ ] Update documentation
- [ ] Add tests"

# 3. Add to IMPROVEMENT_PLAN.md Planned table
# | #126 | High | TypeScript validation | Open |

# 4. Implement with multiple commits
git commit -m "feat(omnifocus-manager): Add TS compiler integration (#126)"
git commit -m "feat(omnifocus-manager): Validate plugins on execution (#126)"

# 5. Release
# Move #126 to Completed table with v2.2.0 and key changes
git commit -m "chore: Release omnifocus-manager v2.2.0

Closes #126"

# 6. Optional: Create retrospective
# Create docs/lessons/typescript-validation-learnings.md
# Document challenges and solutions for future reference
```

## Migration from Old Format

**Old format** (verbose, detailed planning in IMPROVEMENT_PLAN.md):
```markdown
#### 1. Feature Name
**GitHub Issue**: #123
**Goal**: Detailed description...
**Problem Identified**: Long explanation...
**Planned Features**:
- Feature 1 with details
- Feature 2 with details
```

**New format** (simple table, details in issue):
```markdown
| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #123  | High     | Feature Name | Open |
```

**Migration strategy:**
- Use table format for all new planned/completed improvements
- Keep historical verbose entries as-is (optional: add "Archive" section)
- See `docs/lessons/improvement-plan-migration.md` for detailed guide

## Benefits

1. **Single Source of Truth**
   - GitHub Issues are canonical (not IMPROVEMENT_PLAN.md)
   - No duplication of planning details
   - Cross-machine accessible and searchable

2. **Clear Information Architecture**
   - `docs/lessons/` - Post-work learnings
   - `docs/plans/` - Pre-work design
   - GitHub Issues - Active tracking
   - IMPROVEMENT_PLAN.md - Simple summary

3. **Lightweight IMPROVEMENT_PLAN.md**
   - Scannable table format
   - Quick overview of skill evolution
   - Easy to maintain (just issue references)
   - Still provides historical record

4. **Better Collaboration**
   - GitHub Issues work across machines
   - Native discussion and timeline
   - Task checkboxes for tracking progress
   - Email notifications and mentions
