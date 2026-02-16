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

**IMPORTANT**: IMPROVEMENT_PLAN.md is a **lightweight release notes + metrics tracker**, not detailed planning.

**Target Size**: 100-300 lines total (bounded and scannable)

**Format - Version History with Metrics:**

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
- Closed issues: https://github.com/user/repo/issues?q=label:skill:skill-name+is:closed
- Cross-skill learnings: docs/lessons/
```

**Detailed information lives in:**
- GitHub Issue body and comments (active work, source of truth)
- `docs/plans/` (pre-work design, version controlled in repo)
- `docs/lessons/` (post-work learnings, cross-skill patterns)

**Example workflow:**
1. Create issue #123 with detailed tasks
2. Add to IMPROVEMENT_PLAN.md Active Work section: `- [#123](link): Feature Name (Planning)`
3. Start work: Update to "In Progress"
4. Complete work: Add row to Version History table with metrics from `evaluate_skill.py --export-table-row`
5. Close issue #123 in GitHub

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
- Sync marketplace: run `/mp-sync` or `uv run .../sync_marketplace_versions.py`
- Close GitHub issue with commit message

```bash
# Sync marketplace before committing release
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py

git add skills/skill-name/IMPROVEMENT_PLAN.md skills/skill-name/SKILL.md .claude-plugin/marketplace.json
git commit -m "chore: Release skill-name v1.5.0

Closes #123"
```

**Post-release:**
- GitHub automatically closes issue #123
- IMPROVEMENT_PLAN.md now shows historical record in Completed table
- Issue remains searchable with full implementation discussion

### 6. Closing an Issue

**CRITICAL**: Before closing any GitHub Issue, complete this checklist to ensure the issue is properly documented and closed:

**Closing an Issue Checklist:**

```bash
# 1. Verify all work is complete
# - [ ] All checkboxes in issue description are checked (if applicable)
# - [ ] All commits reference the issue number (#N)
# - [ ] All planned tasks completed

# 2. Update issue status
gh issue edit N --body "$(cat issue-body-with-checkboxes-updated.md)"

# 3. Add final completion comment with results
gh issue comment N --body "✅ Complete: [summary of results, metrics, commits]"

# 4. Create follow-up issues if needed
gh issue create --title "follow-up task" --body "Related: #N"

# 5. Close issue with summary
gh issue close N --comment "All work complete. [Final summary, commits, follow-up issues]"
```

**Required in closing comment:**
- ✅ Status (all phases/tasks complete)
- 📊 Results/metrics (if applicable)
- 🔗 Related commits (git SHA or commit message summary)
- 🎯 Follow-up issues (if work spawned new issues)

**Example closing comment:**
```markdown
All phases complete! Closing issue.

**Final Results:**
- ✅ All 5 phases completed
- ✅ All success criteria met
- 📊 4584 → 199 lines (96% reduction)

**Commits:**
- b4f84ec: Phase 1
- 3a6ef2e: Phase 2
- 967db8b: Phase 5

**Follow-up Work:**
See issues #12, #13, #14
```

**Common mistakes to avoid:**
- ❌ Closing issue without updating checkboxes in issue body
- ❌ Closing without a summary comment
- ❌ Forgetting to link related commits
- ❌ Not creating follow-up issues for discovered work
- ❌ Letting "Closes #N" in commit auto-close without proper documentation

## Directory Structure

```
docs/
  plans/          # IN-REPO planning (version controlled, cross-machine accessible)
                  # Can be ephemeral OR permanent depending on value
                  # CRITICAL: Use docs/plans/, NOT ~/.claude/plans/ (outside repo)
  lessons/        # Cross-skill learnings (permanent, post-work retrospectives)
skills/
  skill-name/
    IMPROVEMENT_PLAN.md  # Lightweight metrics + release notes (~100-300 lines)
    SKILL.md            # Metadata and version
    references/         # Detailed documentation
```

**docs/plans/ Purpose:**

Keep planning documents INSIDE the repository where they are:
- Tracked in git history
- Accessible across all machines via git pull/push
- Referenceable from GitHub Issues
- Searchable within the repository

**When to use docs/plans/:**
- Complex architectural planning (multi-file, multi-skill changes)
- Research documents (comparing approaches, feasibility studies)
- Workflow consolidations
- Any planning that benefits from structured markdown

**Simple planning** can go directly in GitHub Issue descriptions.

## Information Architecture

**What goes where:**

| Type | Location | Purpose | Lifespan |
|------|----------|---------|----------|
| Active work tracking | GitHub Issues | Source of truth for ALL planning & tracking | Until closed |
| Pre-work planning | docs/plans/ | Design and research (version controlled in repo) | Ephemeral or permanent |
| Post-work learnings | docs/lessons/ | Cross-skill retrospectives and patterns | Permanent |
| Release notes + metrics | IMPROVEMENT_PLAN.md | Lightweight version history (~100-300 lines) | Permanent |
| Detailed docs | skills/*/references/ | Implementation guides and API docs | Permanent |

**Key Principle**: ALL detailed planning happens in GitHub Issues. IMPROVEMENT_PLAN.md just reflects issue state with version history and metrics.

## Validation Gates and Quality Enforcement

Skills use a validation gate system to ensure quality before release:

### Two-Stage Validation

**Stage 1: Standard Validation (during development)**
- Catch structural errors early
- Allow warnings to accumulate for batch fixing
- Enables rapid iteration
- Command: `uv run scripts/evaluate_skill.py <skill> --quick`

**Stage 2: Strict Validation (before release)**
- Enforce both errors AND warnings
- Prevents regressions in quality
- Blocks completion until all issues resolved
- Command: `uv run scripts/evaluate_skill.py <skill> --quick --strict`

### Workflow Integration

1. **Development phase**: Use standard validation for quick feedback
2. **Before release**: Run strict validation to ensure quality
3. **If issues found in strict mode**:
   - Either fix them (preferred)
   - Or explicitly defer with GitHub issue + document in IMPROVEMENT_PLAN.md
4. **Release**: Only release when strict validation passes (exit code 0)

### Marketplace Sync

After any skill version bump, marketplace.json must be updated to reflect the new version. Stale marketplace versions mean users installing the plugin get outdated metadata.

**During development (before PR):**
```bash
# Check for version drift
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py --dry-run

# Apply sync (include marketplace.json in PR)
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py
```

**Or use the slash command:**
```bash
/mp-sync          # sync versions
/mp-status        # check for mismatches
```

**Multi-skill plugins:** The sync script auto-updates multi-skill plugins to the highest skill version. For example, if pkm-plugin has vault-architect at 1.1.0 and vault-curator at 1.4.0, the plugin version is set to 1.4.0. Use `--mode=manual` to warn without auto-updating.

**Automation:** Install the pre-commit hook to auto-sync on every commit:
```bash
bash plugins/marketplace-manager/skills/marketplace-manager/scripts/install_hook.sh
```

### Skill Release Checklist

```bash
# Before releasing skill-name v2.0.0:

# 1. Run strict validation (skillsmith)
uv run scripts/evaluate_skill.py skills/skill-name --quick --strict

# 2. If issues found:
#    Option A (preferred): Fix them and re-run validation
#    Option B: Create GitHub issue and document deferral

# 3. Validation passes (exit code 0)
# 4. Update IMPROVEMENT_PLAN.md with metrics and new version
# 5. Bump version in SKILL.md metadata.version
# 6. Sync marketplace versions
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py
# 7. Include marketplace.json in release commit
# 8. Create two-commit release (see "Implementing & Release" section)
```

## Decision Trees

### Simple vs Complex Changes

**Choosing the right approach:**

```
Is it a typo or small fix?
├─ Yes → Commit directly to main
└─ No → Is it complex (multi-file, architectural)?
    ├─ No → Create GitHub issue, add to IMPROVEMENT_PLAN.md Active Work, implement
    │       Run: `uv run scripts/evaluate_skill.py <skill> --quick` periodically
    │       Before release: Run with `--strict` flag
    │
    └─ Yes → Follow full workflow:
            1. Create plan in docs/plans/ (if pre-work research needed)
            2. Create GitHub issue with task checklist (source of truth)
            3. Add to IMPROVEMENT_PLAN.md Active Work section
            4. Implement with commits referencing issue
            5. Validate with: `uv run scripts/evaluate_skill.py <skill> --quick --strict`
            6. Sync marketplace: `uv run .../sync_marketplace_versions.py`
            7. Release: Add version row to IMPROVEMENT_PLAN.md with metrics
            8. Optional: Document learnings in docs/lessons/ (if cross-skill pattern)
```

### Skill-Specific vs Repo-Level Work

**Use GitHub Issue labels to distinguish scope:**

```
Is this improvement specific to ONE skill?
├─ YES → Create GitHub Issue with label "enhancement"
│        Title format: "skill-name: Feature description"
│        Example: "omnifocus-manager: Add TypeScript validation"
│        Update: skills/skill-name/IMPROVEMENT_PLAN.md
│
└─ NO → Does it affect multiple skills OR repo structure?
         ├─ Multiple skills → Consider creating individual issues per skill
         │                   OR one issue with "enhancement" label
         │                   Title: "Standardize error handling across skills"
         │                   Document pattern in docs/lessons/ after completion
         │
         └─ Repo infrastructure → Label: "documentation"
                                  Title: "repo: Update WORKFLOW.md pattern"
                                  Example: Workflow changes, CI/CD updates
```

**Key Insight:**
- ALL improvements use GitHub Issues (source of truth)
- Title prefix distinguishes scope ("skill-name:" vs "repo:")
- Labels help filter and search issues
- Both follow same workflow

## Examples

### Simple Feature (No Planning Doc Needed)

```bash
# 1. Create issue
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

# 3. Implement
git commit -m "feat(omnifocus-manager): Add task filtering (#125)"

# 4. Release with metrics
# Run: uv run skills/skillsmith/scripts/evaluate_skill.py skills/omnifocus-manager --export-table-row --version 2.1.0 --issue 125
# Copy output to IMPROVEMENT_PLAN.md Version History table
# Remove from Active Work section
git commit -m "chore: Release omnifocus-manager v2.1.0

Closes #125"
```

### Complex Feature (With Planning Doc)

```bash
# 1. Create plan in docs/plans/ (IN REPO, not ~/.claude/plans/)
# Create docs/plans/2026-01-20-typescript-validation.md
# Research and design TypeScript validation system

# 2. Commit plan to repo
git add docs/plans/2026-01-20-typescript-validation.md
git commit -m "docs: Add TypeScript validation plan"

# 3. Create issue referencing plan
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

# Returns: Created issue #126

# 4. Add to IMPROVEMENT_PLAN.md Active Work section
# - [#126](link): TypeScript validation (Planning)

# 5. Implement with multiple commits
git commit -m "feat(omnifocus-manager): Add TS compiler integration (#126)"
git commit -m "feat(omnifocus-manager): Validate plugins on execution (#126)"

# 6. Release with metrics
# Run: uv run skills/skillsmith/scripts/evaluate_skill.py skills/omnifocus-manager --export-table-row --version 2.2.0 --issue 126
# Add row to IMPROVEMENT_PLAN.md Version History table
# Remove from Active Work section
git commit -m "chore: Release omnifocus-manager v2.2.0

Closes #126"

# 7. Optional: Create retrospective (if pattern applies to multiple skills)
# Create docs/lessons/typescript-validation-pattern.md
# Document approach for other skills that might need similar validation
```

## Migration from Old Format

**Old format** (verbose, detailed planning in IMPROVEMENT_PLAN.md):
```markdown
#### 1. Feature Name
**GitHub Issue**: #123
**Goal**: Detailed description...
**Problem Identified**: Long explanation...
**Planned Features**:
- Feature 1 with details (500 lines of detailed planning)
- Feature 2 with details
```

**New format** (lightweight release notes with metrics):
```markdown
## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.0.0 | 2026-01-18 | [#123](link) | Feature Name | 67 | 90 | 100 | 100 | 89 |

## Active Work

- [#124](link): Next feature (Planning)
```

**Migration strategy:**
1. Extract planned improvements from IMPROVEMENT_PLAN.md
2. Create GitHub Issues for each active planned improvement (copy details to issue)
3. Update IMPROVEMENT_PLAN.md to new format:
   - Version History table for completed work
   - Active Work section listing open issues
   - Known Issues section
   - Archive section pointing to git history
4. Target size: 100-300 lines total (bounded and scannable)
5. See issue #6 and docs/plans/2026-01-23-skill-planning-consolidation.md for detailed migration plan

## Benefits

1. **Single Source of Truth**
   - GitHub Issues are canonical for ALL planning (not IMPROVEMENT_PLAN.md)
   - No duplication of planning details
   - Cross-machine accessible and searchable
   - Native task tracking with checkboxes

2. **Clear Information Architecture**
   - `docs/lessons/` - Cross-skill post-work learnings
   - `docs/plans/` - Pre-work design (version controlled in repo)
   - GitHub Issues - Active tracking (source of truth)
   - IMPROVEMENT_PLAN.md - Lightweight release notes + metrics

3. **Bounded IMPROVEMENT_PLAN.md Size**
   - Target: 100-300 lines (vs current 2000+ in some skills)
   - Scannable version history table with metrics
   - Quick overview of skill evolution
   - Easy to maintain (just version rows and active issue links)
   - Focuses on "what changed" not "why" (that's in the issue)

4. **Better Collaboration**
   - GitHub Issues work across machines and operating systems
   - Native discussion threads and timeline
   - Task checkboxes for detailed progress tracking
   - Email notifications, mentions, and labels
   - Detailed planning preserved in issue comments

5. **Measurable Quality**
   - Metrics tracked per release (Conciseness, Complexity, Spec Compliance, Progressive Disclosure)
   - Compare skill efficacy over time
   - Identify improvement trends
   - `evaluate_skill.py --export-table-row` eliminates transcription errors
