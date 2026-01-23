# IMPROVEMENT_PLAN.md Best Practices

## Overview

IMPROVEMENT_PLAN.md is a **lightweight release notes + metrics tracker**, not a planning document. It provides a bounded, scannable history of skill evolution.

**Target Size:** 100-300 lines total (bounded and maintainable)

**Purpose:**
- Track version history with metrics (Version History table)
- List active work items (Active Work section linking to GitHub Issues)
- Track known bugs (Known Issues section)
- Provide archive pointers (Archive section)

**Key Principle:** GitHub Issues are the canonical source of truth for ALL planning. IMPROVEMENT_PLAN.md just reflects issue state with version history and metrics.

## Standard Format

```markdown
# {Skill Name} - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.0.0 | 2026-01-18 | [#123](link) | TypeScript validation | 67 | 90 | 100 | 100 | 89 |
| 1.5.0 | 2026-01-10 | [#120](link) | Plugin generation | 72 | 88 | 95 | 100 | 89 |
| 1.0.0 | 2025-12-01 | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#125](link): Database optimization (In Progress)
- [#126](link): UI redesign (Planning)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

- Performance degradation with >10k tasks ([#128](link))

## Archive

For complete development history:
- Git commit history: `git log --grep="skill-name"`
- Closed issues: https://github.com/user/repo/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/
```

**Size Breakdown:**
- Version History table: ~20-50 lines (grows slowly, 1-2 rows per release)
- Active Work: ~10-30 lines (current sprint only, links to issues)
- Known Issues: ~5-20 lines (links to issues)
- Archive section: ~10 lines (static)
- **Total: 100-200 lines** (bounded, scannable)

## GitHub Issue-Based Planning

All detailed planning happens in GitHub Issues, not IMPROVEMENT_PLAN.md.

### Creating Issues for Skill Improvements

**Title format:** `skill-name: Feature description`

**Example:**
```bash
gh issue create --title "omnifocus-manager: Add TypeScript validation" \
  --label "enhancement" \
  --body "**Goal**: Validate plugin code before execution

**Plan**: See docs/plans/2026-01-20-typescript-validation.md

**Tasks**:
- [ ] Implement TypeScript compiler integration
- [ ] Add validation to plugin execution
- [ ] Create error reporting system
- [ ] Update documentation
- [ ] Add tests"
```

### Label Usage

- **enhancement**: Skill-specific improvements
- **bug**: Bug fixes
- **documentation**: Documentation updates

For multi-skill or repo-level work, use title prefix:
- `"repo: Update WORKFLOW.md"` - Repo infrastructure
- `"Standardize error handling across skills"` - Multi-skill pattern

## Version Management

### Semantic Versioning

Follow semantic versioning (MAJOR.MINOR.PATCH):

- **PATCH** (1.0.0 → 1.0.1): Bug fixes, typo corrections, minor docs
- **MINOR** (1.0.0 → 1.1.0): New features, backward-compatible changes
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites

### Version Decision Tree

```
Does this change the skill's behavior or capabilities?
│
├─ NO → Just commit implementation
│        - Documentation updates (unless substantial)
│        - Internal refactoring (no user-facing changes)
│        - Comment/formatting changes
│        → No version change needed
│
└─ YES → Which type of change?
         │
         ├─ PATCH (1.4.0 → 1.4.1)
         │  - Bug fixes
         │  - Typo corrections
         │  - Minor documentation improvements
         │
         ├─ MINOR (1.4.0 → 1.5.0)
         │  - New features
         │  - Enhancements to existing features
         │  - Substantial documentation additions
         │
         └─ MAJOR (1.4.0 → 2.0.0)
            - Breaking changes
            - Skill renames
            - Major restructuring
```

## Release Workflow

### Two-Commit Strategy (Recommended)

For any work that warrants a version bump:

#### Commit 1: Implementation Only

```bash
# 1. Create GitHub issue with detailed tasks
gh issue create --title "omnifocus-manager: Add task filtering" \
  --label "enhancement" \
  --body "**Goal**: Filter tasks by project

**Tasks**:
- [ ] Add filter parameter to query
- [ ] Update documentation
- [ ] Add tests"

# Returns: Created issue #125

# 2. Add to IMPROVEMENT_PLAN.md Active Work section
# - [#125](link): Add task filtering (Planning)

# 3. Implement the changes
# Edit SKILL.md content, scripts, references, etc.

# 4. Commit implementation (without version bump)
git add skills/my-skill/
git commit -m "feat(my-skill): Add task filtering (#125)"

# SKILL.md version stays at current (e.g., 1.4.0)
# IMPROVEMENT_PLAN.md shows issue in Active Work
```

#### Commit 2: Release (When Ready)

```bash
# 1. Run evaluate_skill.py with --export-table-row flag
cd skills/my-skill
uv run ../../skillsmith/scripts/evaluate_skill.py . --export-table-row --version 2.1.0 --issue 125

# Output (ready to paste into IMPROVEMENT_PLAN.md):
# | 2.1.0 | 2026-01-23 | [#125](https://github.com/user/repo/issues/125) | Add task filtering | 72 | 88 | 95 | 100 | 90 |

# 2. Update IMPROVEMENT_PLAN.md:
#    a) Copy the table row to Version History table (at top)
#    b) Remove from Active Work section

# 3. Update SKILL.md frontmatter version
# version: 2.1.0

# 4. Commit release
git add skills/my-skill/IMPROVEMENT_PLAN.md skills/my-skill/SKILL.md
git commit -m "chore: Release my-skill v2.1.0

Closes #125"

# 5. Push to remote (GitHub automatically closes issue #125)
git push
```

### Example: Full Workflow

**Phase 1: Planning & Implementation**

1. Create GitHub Issue #125: "omnifocus-manager: Add task filtering"
2. Add to IMPROVEMENT_PLAN.md Active Work: `- [#125](link): Add task filtering (Planning)`
3. Implement feature with commits: `git commit -m "feat(omnifocus-manager): Add filtering (#125)"`
4. Update status in Active Work: Change `(Planning)` to `(In Progress)`

**Phase 2: Release**

1. Run evaluate_skill.py:
   ```bash
   uv run scripts/evaluate_skill.py . --export-table-row --version 2.1.0 --issue 125
   ```

2. Update IMPROVEMENT_PLAN.md:
   - Add exported row to Version History table (at top)
   - Remove #125 from Active Work section

3. Update SKILL.md: `version: 2.1.0`

4. Commit release: `git commit -m "chore: Release v2.1.0\n\nCloses #125"`

5. Push (issue auto-closes)

**After Release:**

Version History table now shows:
```markdown
| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.1.0 | 2026-01-23 | [#125](link) | Add task filtering | 72 | 88 | 95 | 100 | 90 |
| 2.0.0 | 2026-01-18 | [#123](link) | TypeScript validation | 67 | 90 | 100 | 100 | 89 |
```

Active Work section now empty or shows next issues.

## Pre-Release Checklist

Before releasing a new version:

- [ ] **Implementation complete** and tested
- [ ] **Decide version number** using Version Decision Tree (patch/minor/major)
- [ ] **Run evaluate_skill.py** to capture metrics:
  ```bash
  uv run scripts/evaluate_skill.py . --export-table-row --version X.Y.Z --issue NNN
  ```
- [ ] **Update IMPROVEMENT_PLAN.md:**
  - [ ] Add exported table row to Version History (at top)
  - [ ] Remove completed issue from Active Work section
  - [ ] Add any new bugs to Known Issues (if discovered)
- [ ] **Update SKILL.md frontmatter:**
  ```yaml
  metadata:
    version: X.Y.Z
  ```
- [ ] **Run validation** to ensure no regressions:
  ```bash
  uv run scripts/evaluate_skill.py . --quick
  ```
- [ ] **Commit release** referencing issue:
  ```bash
  git commit -m "chore: Release skill-name vX.Y.Z

  Closes #NNN"
  ```
- [ ] **Push** changes (GitHub auto-closes issue)

## Metrics Tracking

### Understanding Metrics

Metrics are scored 0-100:

- **Conciseness (Conc)**: How lean is SKILL.md? Lower token counts = higher scores
- **Complexity (Comp)**: How manageable is the skill? Fewer files/lines = higher scores
- **Spec Compliance (Spec)**: Does it follow AgentSkills specification? Full compliance = 100
- **Progressive Disclosure (Disc)**: Are references used well? Good balance = higher scores
- **Overall**: Weighted average of all metrics

### Using --export-table-row

The `--export-table-row` flag eliminates manual transcription errors:

```bash
# Basic usage
uv run scripts/evaluate_skill.py . --export-table-row --version 2.0.0 --issue 123

# Output (ready to paste):
| 2.0.0 | 2026-01-23 | [#123](https://github.com/user/repo/issues/123) | Description | 67 | 90 | 100 | 100 | 89 |
```

**Parameters:**
- `--version`: The version being released (e.g., 2.0.0)
- `--issue`: The GitHub issue number being closed (optional)

**Without issue number:**
```bash
uv run scripts/evaluate_skill.py . --export-table-row --version 1.0.0

# Output:
| 1.0.0 | 2026-01-23 | - | Initial release | 72 | 85 | 95 | 100 | 88 |
```

### Tracking Quality Over Time

Version History with metrics shows quality trends:

```markdown
| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.1.0 | 2026-01-23 | [#125](link) | Task filtering | 72 | 88 | 95 | 100 | 90 |
| 2.0.0 | 2026-01-18 | [#123](link) | TS validation | 67 | 90 | 100 | 100 | 89 |
| 1.5.0 | 2026-01-10 | [#120](link) | Plugin gen | 72 | 88 | 95 | 100 | 89 |
```

**Analysis:**
- Conciseness improved: 67 → 72 (removed unnecessary content)
- Complexity stable: 88-90 (controlled growth)
- Spec Compliance improved: 95 → 100 (fixed validation issues)
- Overall trend: 89 → 90 (quality improving)

Use "-" for historical versions where metrics weren't captured.

## Common Pitfalls

### 1. Detailed Planning in IMPROVEMENT_PLAN.md

**Problem:**
```markdown
## Active Work

- [#123](link): Add TypeScript validation (In Progress)
  **Goal:** Validate plugin code before execution
  **Planned Features:**
  - Integrate TS compiler API
  - Add validation to plugin execution
  (500 lines of detailed planning...)
```

**Solution:**
Put detailed planning in the GitHub Issue #123, not IMPROVEMENT_PLAN.md:

```markdown
## Active Work

- [#123](link): Add TypeScript validation (In Progress)

See GitHub Issues for detailed plans and task checklists.
```

### 2. Missing Version History Metrics

**Problem:**
```markdown
| Version | Date | Issue | Summary |
|---------|------|-------|---------|
| 2.0.0 | 2026-01-18 | [#123](link) | TypeScript validation |
```

**Solution:**
Always include metrics columns (use `--export-table-row`):

```markdown
| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.0.0 | 2026-01-18 | [#123](link) | TypeScript validation | 67 | 90 | 100 | 100 | 89 |
```

### 3. Forgetting to Remove from Active Work

**Problem:**
After release, issue #123 is closed but still listed in Active Work section.

**Solution:**
When adding version row to Version History, also remove the issue from Active Work section.

### 4. Not Referencing Issues in Commits

**Problem:**
```bash
git commit -m "feat: Add TypeScript validation"
```

**Solution:**
Always reference the issue number:
```bash
git commit -m "feat(skill-name): Add TypeScript validation (#123)"
```

This creates automatic GitHub issue links and helps track work.

## Migration from Old Format

If your skill has an old verbose IMPROVEMENT_PLAN.md format:

### Old Format (Verbose)
```markdown
#### 1. Enhanced Skill Validation

**Goal:** Improve validation coverage

**Problem Identified:** Current validation misses several edge cases...
(500 lines of detailed planning)

**Planned Features:**
- Feature 1 with extensive details
- Feature 2 with implementation notes
- Feature 3 with code examples
```

### New Format (Minimal)
```markdown
## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.0.0 | 2026-01-18 | [#130](link) | Enhanced validation | 68 | 90 | 100 | 100 | 90 |

## Active Work

- [#131](link): Next improvement (Planning)
```

### Migration Steps

1. **Extract planned improvements** from old IMPROVEMENT_PLAN.md
2. **Create GitHub Issues** for each active planned improvement:
   - Copy detailed planning from IMPROVEMENT_PLAN.md into issue body
   - Add task checklist in issue
   - Get issue number (e.g., #130)
3. **Update IMPROVEMENT_PLAN.md** to new format:
   - Create Version History table with metrics
   - Create Active Work section listing open issues
   - Add Known Issues section (if any bugs)
   - Add Archive section
4. **Target size:** 100-300 lines total

See issue #6 and `docs/plans/2026-01-23-skill-planning-consolidation.md` for detailed migration plan affecting multiple skills.

## Examples from Real Skills

### Example 1: Simple Skill (marketplace-manager)

```markdown
# Marketplace Manager - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 1.4.0 | 2026-01-22 | [#4](link) | Version sync automation | 75 | 92 | 100 | 100 | 92 |
| 1.3.0 | 2026-01-18 | - | Marketplace hooks | 72 | 90 | 100 | 100 | 91 |
| 1.0.0 | 2025-12-01 | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

No active work. Future improvements tracked in GitHub Issues.

## Known Issues

None.

## Archive

For development history:
- Git commits: `git log --grep="marketplace-manager"`
- Closed issues: https://github.com/user/repo/issues?q=label:enhancement+is:closed
```

**Total: ~30 lines** (very lean skill)

### Example 2: Skill with Active Work

```markdown
# OmniFocus Manager - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 4.4.0 | 2026-01-20 | [#10](link) | TypeScript validation | 60 | 88 | 100 | 100 | 87 |
| 4.3.0 | 2026-01-15 | [#8](link) | Plugin generation | 65 | 85 | 100 | 100 | 87 |
| 4.0.0 | 2026-01-10 | - | Major refactor | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

- [#12](link): Database optimization (In Progress)
- [#13](link): Memory leak fix (Blocked by #12)
- [#14](link): UI redesign (Planning)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

- Performance degradation with >10k tasks ([#15](link))
- macOS 15.2 compatibility issue ([#16](link))

## Archive

For development history:
- Git commits: `git log --grep="omnifocus-manager"`
- Closed issues: https://github.com/user/repo/issues?q=label:enhancement+is:closed
- Cross-skill learnings: docs/lessons/typescript-validation-patterns.md
```

**Total: ~40 lines** (bounded even with active work)

## Summary

### Key Principles

1. **Lightweight format**: 100-300 lines total, not 2000+
2. **GitHub Issues are source of truth**: All detailed planning happens there
3. **Version History with metrics**: Track quality over time with evaluate_skill.py
4. **Active Work links to issues**: Just list issue numbers and status
5. **Use --export-table-row**: Eliminates manual transcription errors
6. **Two-commit strategy**: Implementation separate from release
7. **Reference issues in commits**: `git commit -m "feat(skill): Description (#123)"`

### Simple Release Workflow

1. Create GitHub Issue with detailed tasks
2. Add to Active Work section in IMPROVEMENT_PLAN.md
3. Implement changes (commits reference issue #)
4. Run `evaluate_skill.py --export-table-row`
5. Add row to Version History, remove from Active Work
6. Update SKILL.md version
7. Commit release: `chore: Release vX.Y.Z\n\nCloses #N`
8. Push (issue auto-closes)

This ensures your skill's development history is clear, bounded, and maintainable while keeping detailed planning in GitHub Issues where it belongs.
