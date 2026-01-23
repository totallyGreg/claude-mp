# Skill Planning Workflow Consolidation Plan

## Executive Summary

**Goal:** Streamline skill development workflow to eliminate confusion between repo-level and skill-level improvements, minimize IMPROVEMENT_PLAN.md size, and establish GitHub Issues as the single source of truth for ALL planning.

**Key Insight:** User wants IMPROVEMENT_PLAN.md to be "release notes + metrics" (~100-200 lines), not a planning document. Teachable moments and plans should flow directly into GitHub Issues, leveraging git history instead of massive inline docs.

**Critical Corrections from User Feedback:**

1. **docs/plans/ stays (NOT deprecated):** Its purpose is to keep plans IN the repo (version controlled, cross-machine accessible). This very plan is currently in ~/.claude/plans/ (OUTSIDE repo) - it should be moved to docs/plans/2026-01-23-skill-planning-consolidation.md.

2. **Don't blindly create issues for all planned items:** Many may already be implemented or need re-evaluation. For bloated skills (terminal-guru with 2138 lines), create ONE consolidation issue to track all ideas, then triage into focused issues later.

3. **All Python scripts use `uv run` with PEP 723 metadata:** Consistency requirement - no direct `python3` invocation.

## Current State Problems

### 1. Inconsistent Formats
- **Pattern A** (marketplace-manager, ai-risk-mapper): Simple tables, GitHub Issues, ~150-450 lines
- **Pattern B** (skillsmith, omnifocus-manager, terminal-guru): Detailed narratives, 675-2135 lines

### 2. Unclear Information Architecture
- docs/lessons/ - Post-work learnings (but should these just be GitHub Issue retrospectives?)
- docs/plans/ - Pre-work planning (but should these just be GitHub Issue descriptions?)
- IMPROVEMENT_PLAN.md - Currently 2000+ lines in some skills (should be release notes only)

### 3. Confusion Between Audiences
- **Developers:** Need task tracking, planning, cross-machine sync
- **End Users:** Need SKILL.md, references/, scripts/ (IMPROVEMENT_PLAN.md excluded via .skillignore)

### 4. Meta-Level Tool Confusion
- skillsmith and marketplace-manager affect multiple skills
- Unclear if their improvements should follow repo-level or skill-level patterns

## User Requirements (from questions)

1. ✅ IMPROVEMENT_PLAN.md stays excluded from distribution (dev artifact only)
2. ✅ Skills work with Gemini experimental.skill mode (already do via directory spec)
3. ✅ Minimize IMPROVEMENT_PLAN.md size (~100-200 lines max)
4. ✅ Use git history for tracking, not massive inline docs
5. ✅ IMPROVEMENT_PLAN.md = "release notes + metrics to compare skill efficacy"
6. ✅ GitHub Issues track all implementation work
7. ❓ Where should skill-specific plans live? (To be determined)
8. ❓ Should docs/lessons/ exist or just use GitHub Issues? (To be determined)

## Proposed Solution: GitHub Issues as Universal Planning System

### Core Principle

**"Capture → Issue → Implement → Release Notes"**

```
Reflection/Bug/Idea
    ↓
GitHub Issue Created Immediately
    ↓
Planning happens IN issue (description, tasks, discussion)
    ↓
Implementation commits reference issue (#123)
    ↓
IMPROVEMENT_PLAN.md updated with version + metrics + issue link
```

### Information Architecture

#### GitHub Issues (Source of Truth for ALL planning)

**Skill-Specific Improvements:**
```
Title: "omnifocus-manager: Add TypeScript validation"
Labels: skill:omnifocus-manager, type:feature, priority:high

Body:
**Problem:** Plugins fail at runtime due to syntax errors

**Goal:** Validate TypeScript before execution

**Tasks:**
- [ ] Integrate TS compiler API
- [ ] Add validation to plugin execution
- [ ] Create error reporting system
- [ ] Update documentation
- [ ] Add tests

**Plan:** (can be detailed right here in issue description)
- Use ts.createProgram() for validation
- Cache validation results
- Report errors before execution

**Related Issues:** #120, #115
**Related Skills:** marketplace-manager (may need similar validation)
```

**Repo-Level Improvements:**
```
Title: "repo: Standardize IMPROVEMENT_PLAN.md format"
Labels: type:documentation, scope:repo

Body:
**Goal:** Consolidate all skills to minimal release notes format

**Affected Skills:** terminal-guru, omnifocus-manager, skillsmith, swift-dev

**Tasks:**
- [ ] Update WORKFLOW.md with new format
- [ ] Migrate terminal-guru (2138 lines → ~200 lines)
- [ ] Update skillsmith init_skill.py template
- [ ] Update improvement_plan_best_practices.md
```

**Meta-Tool Improvements (skillsmith, marketplace-manager):**
```
Title: "skillsmith: Add audit_improvements.py script"
Labels: skill:skillsmith, type:tooling

Body:
**Goal:** Automate detection of completed work not yet moved to Completed section

**Background:** See docs/lessons/improvement-plan-metrics-tracking.md

**Tasks:**
- [ ] Parse IMPROVEMENT_PLAN.md planned improvements
- [ ] Check scripts/ for mentioned scripts
- [ ] Check git history for related commits
- [ ] Output status report (Complete/Partial/Not Started)
```

#### IMPROVEMENT_PLAN.md (Minimal Release Notes Format)

**Structure: ~100-300 lines total**

```markdown
# {Skill Name} - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| 2.0.0 | 2026-01-18 | [#123](link) | TypeScript validation | 67 | 90 | 100 | 100 | 89 |
| 1.5.0 | 2026-01-10 | [#120](link) | Plugin generation | 72 | 88 | 95 | 100 | 89 |
| 1.0.0 | 2025-12-01 | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work (Q1 2026)

- [#125](link): Database optimization (In Progress)
- [#126](link): UI redesign (Planning)
- [#127](link): Memory leak fix (Blocked by #125)

See GitHub Issues for detailed plans and task checklists.

## Known Issues

- Performance degradation with >10k tasks ([#128](link))
- macOS 15.2 compatibility issue ([#129](link))

## Archive

For complete development history:
- Git commit history: `git log --grep="omnifocus-manager"`
- Closed issues: https://github.com/user/repo/issues?q=label:skill:omnifocus-manager+is:closed
- Cross-skill learnings: docs/lessons/
```

**Size Breakdown:**
- Version History table: ~20-50 lines (grows slowly, 1-2 rows per release)
- Active Work: ~10-30 lines (current sprint only, moves to history on completion)
- Known Issues: ~5-20 lines (links to issues)
- Archive section: ~10 lines (static)
- **Total: 100-200 lines** (bounded, maintainable)

#### docs/lessons/ (Optional Cross-Skill Deep Dives)

**Purpose:** Document patterns that affect MULTIPLE skills or are teaching moments for the broader project

**Examples:**
- `improvement-plan-metrics-tracking.md` (already exists, valuable!)
- `typescript-validation-patterns.md` (if omnifocus-manager and marketplace-manager both implement TS validation)
- `plugin-architecture-evolution.md` (affects multiple skills)

**NOT for:** Individual skill release notes (use GitHub Issues + IMPROVEMENT_PLAN.md instead)

**When to create:**
- Pattern discovered during implementation that applies to 2+ skills
- Meta-level learning about the development process itself
- Deep technical dive that's too detailed for a GitHub Issue

#### docs/plans/ (IN-REPO Planning Documents)

**Purpose:** Keep planning documents INSIDE the repository (version controlled, cross-machine accessible)

**Key Principle:** Plans should be in docs/plans/ (inside repo), NOT in ~/.claude/plans/ (outside repo). This ensures:
- Plans are tracked in git history
- Plans sync across machines via git pull/push
- Plans can be referenced from GitHub Issues
- Plans are searchable in the repository

**Workflow:**
1. Create `docs/plans/2026-01-23-typescript-validation.md` with research/design IN THE REPO
2. Commit to git: `git add docs/plans/2026-01-23-typescript-validation.md && git commit`
3. Create GitHub Issue #123 with: "**Plan:** See docs/plans/2026-01-23-typescript-validation.md"
4. Implement work (referencing issue #123)
5. OPTIONAL: Delete/archive plan after work completes if it's no longer needed (ephemeral)
6. OR KEEP: If the plan documents important architectural decisions, keep it permanently

**Use for:**
- Complex architectural planning (multi-file, multi-skill changes)
- Research documents (comparing approaches, feasibility studies)
- Workflow consolidations (like this very plan!)
- Any planning that benefits from structured markdown with examples

**Do NOT use ~/.claude/plans/:** That's outside the repo and doesn't sync via git

## Skill-Specific vs Repo-Level Decision Tree

```
Is this improvement specific to ONE skill?
├─ YES → Create GitHub Issue with label "skill:{name}"
│        Example: "omnifocus-manager: Add TypeScript validation"
│
└─ NO → Does it affect multiple skills OR repo structure?
         ├─ Multiple skills → Label: "scope:multi-skill"
         │                   Example: "Standardize error handling across all skills"
         │
         ├─ Repo infrastructure → Label: "scope:repo"
         │                        Example: "Update WORKFLOW.md pattern"
         │
         └─ Meta-tool (skillsmith/marketplace-manager) → Label: "skill:{meta-tool}"
                                                         Example: "skillsmith: Add audit script"
```

**Key Insight:** ALL improvements use GitHub Issues. Labels distinguish scope.

## Migration Strategy

**IMPORTANT: Phase Ordering Rationale**

The phases are ordered to build foundation before implementation:

1. **Phase 1 (Documentation):** Document the new standard before implementing it
2. **Phase 2 (Templates):** Show concrete format in templates
3. **Phase 3 (Automation):** Build tools to detect completed work BEFORE migrating
4. **Phase 4 (Audit):** Use automation to understand what's really done
5. **Phase 5 (Migration):** Now we have docs, templates, and tools to guide migration

This prevents manual migration work before we have the documentation, templates, and automation to guide it correctly.

### Phase 1: Update WORKFLOW.md Documentation

**File:** `/Users/gregwilliams/Documents/Projects/claude-mp/WORKFLOW.md`

**Changes:**

1. **Clarify IMPROVEMENT_PLAN.md purpose:**
   - Update line 77: "IMPROVEMENT_PLAN.md is a **lightweight release notes + metrics tracker**"
   - Add size guidance: "Target: 100-300 lines total"
   - Show minimal format example

2. **Strengthen docs/plans/ guidance:**
   - Clarify purpose: Keep plans IN the repo (version controlled, cross-machine accessible)
   - **Critical:** Plans should be in docs/plans/, NOT ~/.claude/plans/ (outside repo)
   - Show when to use: Complex planning, research docs, workflow consolidations
   - Ephemeral vs permanent: Can delete after implementation OR keep for architectural records
   - Simple planning can go directly in GitHub Issue descriptions

3. **Add skill-specific vs repo-level decision tree:**
   - Show label usage: `skill:{name}`, `scope:repo`, `scope:multi-skill`
   - Clarify that both use same GitHub Issues workflow

4. **Strengthen GitHub Issues as source of truth:**
   - Issues are for ALL planning (skill-level AND repo-level)
   - IMPROVEMENT_PLAN.md just reflects issue state
   - docs/lessons/ for cross-skill learnings only

### Phase 2: Update Skillsmith Templates

**File:** `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/init_skill.py`

**Update IMPROVEMENT_PLAN_TEMPLATE:**

```python
IMPROVEMENT_PLAN_TEMPLATE = """# {skill_name} - Improvement Plan

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Overall |
|---------|------|-------|---------|------|------|------|------|---------|
| {version} | {date} | - | Initial release | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure (0-100 scale)

## Active Work

No active improvements yet. Create GitHub Issues for planned work.

## Known Issues

None yet. Report issues at https://github.com/{repo}/issues

## Archive

For development history:
- Git commits: `git log --grep="{skill_name}"`
- Closed issues: https://github.com/{repo}/issues?q=label:skill:{skill_name}+is:closed
"""
```

**File:** `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/references/improvement_plan_best_practices.md`

**Major rewrite to document minimal format:**

1. Remove examples of detailed inline planning
2. Add examples of GitHub Issue-based planning
3. Show minimal IMPROVEMENT_PLAN.md format
4. Document label usage for skill vs repo vs multi-skill
5. Update pre-release checklist:
   - Create/update GitHub Issue
   - Run `evaluate_skill.py` and capture metrics
   - Update IMPROVEMENT_PLAN.md version history table with metrics
   - Reference issue in commit: `git commit -m "feat(skill): Description (#123)"`

### Phase 3: Implement Automation Scripts (from docs/lessons/improvement-plan-metrics-tracking.md)

**IMPORTANT:** All Python scripts MUST:
- Use PEP 723 inline metadata for dependencies
- Be invoked with `uv run` (not `python3` or direct execution)
- Follow this pattern:
  ```python
  # /// script
  # dependencies = ["package1", "package2"]
  # ///

  import package1
  # script code
  ```

**Priority 1: Update evaluate_skill.py**

**File:** `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/evaluate_skill.py`

**Add `--export-table-row` flag:**

```bash
uv run scripts/evaluate_skill.py . --export-table-row --version 2.0.0 --issue 123

# Output (ready to paste into IMPROVEMENT_PLAN.md):
| 2.0.0 | 2026-01-23 | [#123](https://github.com/user/repo/issues/123) | TypeScript validation | 67 | 90 | 100 | 100 | 89 |
```

This eliminates manual metric transcription errors.

**Priority 2: Create scripts/audit_improvements.py**

**File:** `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/audit_improvements.py`

**Purpose:** Detect when planned work is actually completed but not yet marked as such

```bash
uv run scripts/audit_improvements.py skills/omnifocus-manager

# Output:
# ✅ Issue #130: Enhanced ANSI support - COMPLETED
#    Evidence:
#    - scripts/ansi_parser.py exists (347 lines)
#    - Git commits: 3 commits reference #130
#    - Suggestion: Close issue and update IMPROVEMENT_PLAN.md
#
# 🟡 Issue #131: Zsh optimization - PARTIAL
#    Evidence:
#    - scripts/zsh_benchmark.py exists
#    - No completion marker found
#
# ❌ Issue #132: Database migration - NOT STARTED
#    No evidence found
```

**Priority 3: Create scripts/sync_improvement_plan.py** (Optional)

**Purpose:** Auto-update IMPROVEMENT_PLAN.md "Active Work" section from GitHub Issues

```bash
uv run scripts/sync_improvement_plan.py skills/omnifocus-manager

# Fetches open issues with label:skill:omnifocus-manager
# Updates "Active Work" section automatically
# Shows diff before applying
```

This keeps IMPROVEMENT_PLAN.md in sync with GitHub Issues (single source of truth).

### Phase 4: Audit and Create GitHub Issues for Current Work

**IMPORTANT:** Do NOT blindly create issues for every planned item. Many may already be implemented or need re-evaluation.

**For each skill with planned improvements:**

1. **Run audit_improvements.py first** (if available):
   ```bash
   uv run skills/skillsmith/scripts/audit_improvements.py skills/terminal-guru
   ```
   This detects what's actually completed vs still needed.

2. **For skills with MANY planned items (>10 items or >1000 lines):**
   - Create ONE consolidation issue to track all ideas
   - Example: "terminal-guru: Review and triage planned improvements"
   - Body: List all current planned items with checkboxes
   - Label: `skill:terminal-guru`, `type:triage`
   - Later, break into focused issues as priorities clarify

3. **For skills with FEW planned items (<10 items, clearly defined):**
   - Review each item manually
   - If already implemented: Skip (just update IMPROVEMENT_PLAN.md to completed)
   - If still needed: Create focused GitHub Issue
   - If unclear: Add to consolidation issue for triage

**Example for terminal-guru (2138 lines, many planned items):**

Create ONE consolidation issue:
```
Title: "terminal-guru: Review and triage 15 planned improvements"
Label: skill:terminal-guru, type:triage

Body:
Current IMPROVEMENT_PLAN.md lists 15 planned improvements. Need to:
- [ ] 1. Enhanced ANSI Color Support - Review if already implemented
- [ ] 2. Zsh Performance Optimization - Review if already implemented
- [ ] 3. Terminfo Database Validation - Review if still needed
- [ ] (etc for all 15)

Next steps:
1. Run audit_improvements.py to detect completed work
2. Review each item for current relevance
3. Create focused issues for confirmed priorities
4. Archive or remove obsolete items
```

**Example for swift-dev (130 lines, 3 clear items):**

Review each item individually:
- Item 1: "Add Swift 6 migration guide" → Already done? Check references/
- Item 2: "Improve error messages" → Still needed? Create Issue #135
- Item 3: "Add concurrency examples" → Obsolete? Remove from plan

### Phase 5: Standardize IMPROVEMENT_PLAN.md Format

**Affected files:**
- `/Users/gregwilliams/Documents/Projects/claude-mp/skills/terminal-guru/IMPROVEMENT_PLAN.md` (2138 lines → ~200 lines)
- `/Users/gregwilliams/Documents/Projects/claude-mp/skills/omnifocus-manager/IMPROVEMENT_PLAN.md` (1642 lines → ~200 lines)
- `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/IMPROVEMENT_PLAN.md` (674 lines → ~200 lines)
- `/Users/gregwilliams/Documents/Projects/claude-mp/skills/swift-dev/IMPROVEMENT_PLAN.md` (already small, adjust format)

**For each skill:**

1. **Extract Version History**
   - Keep version table with metrics (if available)
   - One row per released version
   - Add "Issue" column linking to GitHub Issue (if exists)

2. **Convert Planned Improvements → GitHub Issues**
   - Create GitHub Issue for each in-flight planned improvement
   - Copy detailed planning from IMPROVEMENT_PLAN.md into issue description
   - Add label: `skill:{name}`
   - Add tasks checklist in issue
   - Get issue number (e.g., #130)

3. **Update IMPROVEMENT_PLAN.md to Minimal Format**
   - Replace detailed planning section with "Active Work" table
   - List issue numbers and status only
   - Add "See GitHub Issues for details"

4. **Archive Old History (Optional)**
   - If version history is extensive (>50 versions), keep recent 10-20
   - Add "Archive" section pointing to git log

**Example Migration (terminal-guru):**

Before (2138 lines):
```markdown
#### 1. Enhanced ANSI Color Support

**Goal:** Improve color rendering...
(500 lines of detailed planning)

#### 2. Zsh Performance Optimization

**Goal:** Reduce startup time...
(400 lines of detailed planning)
```

After (~200 lines):
```markdown
## Active Work

- [#130](link): Enhanced ANSI color support (In Progress)
- [#131](link): Zsh performance optimization (Planning)

See GitHub Issues for detailed plans.
```

And create GitHub Issue #130:
```
Title: terminal-guru: Enhanced ANSI color support
Body: (paste the 500 lines of detailed planning from old IMPROVEMENT_PLAN.md)
```


## Handling Meta-Tools (skillsmith, marketplace-manager)

**Question:** Should skillsmith improvements follow "skill-level" or "repo-level" pattern?

**Answer:** Treat as skill-level, but acknowledge they affect the broader ecosystem.

**Workflow:**

1. Create GitHub Issue: "skillsmith: Add audit_improvements.py"
   - Label: `skill:skillsmith`, `type:tooling`
   - Body: Detailed planning
   - Tasks: Implementation checklist

2. Implementation commits:
   ```bash
   git commit -m "feat(skillsmith): Add audit script (#140)"
   ```

3. Update skillsmith/IMPROVEMENT_PLAN.md:
   ```markdown
   | 3.3.0 | 2026-01-23 | [#140](link) | Audit script for improvements | 60 | 92 | 100 | 100 | 88 |
   ```

4. If the change affects OTHER skills, add label: `scope:multi-skill`

5. If cross-skill pattern emerges, create `docs/lessons/improvement-audit-pattern.md`

**Key insight:** Even meta-tools follow the same workflow. Labels distinguish scope.

## Benefits of This Approach

### 1. Single Source of Truth
- GitHub Issues are canonical (for both planning AND tracking)
- No duplication between IMPROVEMENT_PLAN.md and issues
- Cross-machine accessible without git pull

### 2. Bounded IMPROVEMENT_PLAN.md Size
- ~100-300 lines (vs current 2000+)
- Scannable at a glance
- Focuses on "what changed" not "why we changed it" (that's in the issue)

### 3. Git as Archive
- Full history in `git log` (no need to duplicate in IMPROVEMENT_PLAN.md)
- Searchable: `git log --grep="omnifocus"`
- Detailed discussion in issue comments

### 4. Consistency Across Skills
- Same format for all skills
- Same workflow for repo-level and skill-level work
- Clear examples to follow

### 5. Better Collaboration
- Issues work across machines, operating systems
- Email notifications, mentions, discussion threads
- Task checklists for progress tracking

### 6. Portability Still Works
- Skills follow directory spec (works with Gemini experimental.skill)
- SKILL.md + references/ + scripts/ travel with skill
- IMPROVEMENT_PLAN.md stays excluded (dev artifact only)

## Critical Files to Modify

### Documentation Updates
1. `/Users/gregwilliams/Documents/Projects/claude-mp/WORKFLOW.md`
   - Clarify IMPROVEMENT_PLAN.md purpose (release notes + metrics)
   - Add skill vs repo decision tree
   - Strengthen GitHub Issues as source of truth
   - Simplify docs/plans/ guidance (optional/ephemeral)

### Skillsmith Template Updates
2. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/init_skill.py`
   - Update IMPROVEMENT_PLAN_TEMPLATE to minimal format
   - Add GitHub Issue workflow guidance

3. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/references/improvement_plan_best_practices.md`
   - Complete rewrite to document minimal format
   - Add GitHub Issue examples
   - Update pre-release checklist

### Skill Migrations (Largest First)
4. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/terminal-guru/IMPROVEMENT_PLAN.md`
   - Migrate from 2138 lines → ~200 lines
   - Create GitHub Issues for planned work
   - Keep version history table only

5. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/omnifocus-manager/IMPROVEMENT_PLAN.md`
   - Migrate from 1642 lines → ~200 lines
   - Create GitHub Issues for planned work

6. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/IMPROVEMENT_PLAN.md`
   - Migrate from 674 lines → ~200 lines
   - Create GitHub Issues for in-flight work

### Automation Scripts (New Files)
7. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/audit_improvements.py`
   - Detect completed work not yet marked
   - Check for evidence in scripts/, references/, git history

8. `/Users/gregwilliams/Documents/Projects/claude-mp/skills/skillsmith/scripts/evaluate_skill.py`
   - Add `--export-table-row` flag for easy metric capture

## Verification Steps

After implementation:

1. **Check IMPROVEMENT_PLAN.md sizes:**
   ```bash
   for skill in skills/*/IMPROVEMENT_PLAN.md; do
     echo "$skill: $(wc -l < "$skill") lines"
   done
   ```
   Target: All under 300 lines

2. **Verify GitHub Issues exist for active work:**
   ```bash
   gh issue list --label "skill:omnifocus-manager"
   gh issue list --label "skill:terminal-guru"
   gh issue list --label "scope:repo"
   ```

3. **Test evaluate_skill.py export:**
   ```bash
   cd skills/skillsmith
   uv run scripts/evaluate_skill.py . --export-table-row --version 3.3.0 --issue 140
   # Should output properly formatted table row
   ```

4. **Test audit_improvements.py:**
   ```bash
   uv run scripts/audit_improvements.py skills/omnifocus-manager
   # Should detect completed/partial/not-started improvements
   ```

5. **Validate template generation:**
   ```bash
   cd skills/skillsmith
   uv run scripts/init_skill.py test-skill
   # Check that skills/test-skill/IMPROVEMENT_PLAN.md uses minimal format
   ```

6. **Check docs/lessons/ usage:**
   - Should contain cross-skill learnings only
   - improvement-plan-metrics-tracking.md is a good example
   - No skill-specific release notes

## Resolved Questions

1. **Should we deprecate docs/plans/ entirely?**
   - **ANSWER: NO, keep docs/plans/** - its purpose is to prevent plans from being stashed outside the repo
   - This very plan (zazzy-tickling-coral.md) is currently in ~/.claude/plans/ (outside repo) - it should be moved to docs/plans/2026-01-23-skill-planning-consolidation.md
   - docs/plans/ keeps planning documents IN the repo where they're version controlled and accessible
   - **Recommendation:** Keep docs/plans/ for both simple and complex planning; deprecate ~/.claude/plans/ usage for project work

2. **What about docs/lessons/ for single-skill learnings?**
   - Currently improvement-plan-metrics-tracking.md is about skillsmith specifically
   - Should single-skill retrospectives be GitHub Issue comments instead?
   - **Recommendation:** docs/lessons/ for cross-skill patterns only; use GitHub Issue comments for skill-specific retrospectives

3. **How to handle version history with 50+ releases?**
   - Keep all versions in IMPROVEMENT_PLAN.md or archive old ones?
   - **Recommendation:** Keep all (grows slowly, ~2 lines per release, 100 releases = 200 lines)

4. **Should sync_improvement_plan.py auto-update or just show diff?**
   - Auto-update could be dangerous if issues have wrong labels
   - **Recommendation:** Show diff, require manual confirmation

## Success Criteria

1. ✅ All skills use consistent IMPROVEMENT_PLAN.md format (~100-300 lines)
2. ✅ GitHub Issues exist for all active work (labeled appropriately)
3. ✅ WORKFLOW.md clearly documents skill vs repo decision tree
4. ✅ Skillsmith generates new skills with minimal IMPROVEMENT_PLAN.md
5. ✅ evaluate_skill.py can export table rows (eliminates transcription errors)
6. ✅ audit_improvements.py detects completed work automatically
7. ✅ No confusion between planning locations (everything in GitHub Issues)

## Timeline Estimate

**Phase 1 (WORKFLOW.md documentation):** 30 min

**Phase 2 (Skillsmith template updates):** 1 hour

**Phase 3 (Automation scripts):**
- evaluate_skill.py update: 30 min
- audit_improvements.py: 2-3 hours
- sync_improvement_plan.py (optional): 2 hours

**Phase 4 (GitHub Issue creation & audit):** 2-3 hours (depends on number of planned improvements)

**Phase 5 (IMPROVEMENT_PLAN.md migrations):**
- terminal-guru: 1-2 hours
- omnifocus-manager: 1-2 hours
- skillsmith: 1 hour
- Other skills: 30 min each

**Total: 10-15 hours** for complete migration

## First Step: Move This Plan to docs/plans/

**Current location:** `~/.claude/plans/zazzy-tickling-coral.md` (outside repo)

**Target location:** `/Users/gregwilliams/Documents/Projects/claude-mp/docs/plans/2026-01-23-skill-planning-consolidation.md`

**Why:** This plan itself demonstrates the docs/plans/ paradox - it's currently stored outside the repo where it's not version controlled or accessible across machines. Moving it to docs/plans/ ensures:
- Plan is tracked in git
- Accessible across all machines via git pull
- Searchable in repo history
- Can be referenced from GitHub Issues

**After moving:**
- Create GitHub Issue: "repo: Consolidate skill planning workflow"
- Reference plan: "See docs/plans/2026-01-23-skill-planning-consolidation.md"
- Track implementation progress in issue

## Next Steps

1. ✅ Move this plan to docs/plans/2026-01-23-skill-planning-consolidation.md
2. ✅ Create GitHub Issue #6 for this workflow consolidation work
3. Start with Phase 1: Update WORKFLOW.md documentation
4. Phase 2: Update Skillsmith templates
5. Phase 3: Build automation scripts (audit_improvements.py, evaluate_skill.py updates)
6. Phase 4: Use automation to audit existing planned work
7. Phase 5: Migrate IMPROVEMENT_PLAN.md files using docs, templates, and tools
