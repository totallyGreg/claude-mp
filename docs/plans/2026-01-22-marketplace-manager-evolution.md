# Claude-MP Marketplace Evolution Plan

**Date**: 2026-01-22
**Focus**: marketplace-manager skill improvements for marketplace operations
**Repository**: Marketplace repository (not project repository)

## Executive Summary

The claude-mp repository is a **marketplace repository** where individual skills are distributed as independent plugins. This plan addresses critical marketplace distribution issues and enhances marketplace-manager with automation for common marketplace operations.

**Key Problems Identified:**
1. **Source path misconfiguration**: All plugins use `"source": "./"` causing users to install entire repository instead of individual skills
2. **No deprecation automation**: Removing skills requires manual marketplace.json edits and reference cleanup
3. **No bundling guidance**: No automation to determine when/how to create multi-skill bundles
4. **Code duplication accepted**: Skills need self-contained utils (marketplace plugins don't share code at runtime)

**Key Clarifications:**
- **IMPROVEMENT_PLAN.md**: Per-skill only (travels with skill), not repository-wide
- **GitHub Issues**: Source of truth for implementing changes (cross-machine, searchable, trackable)
- **skill-planner deprecation**: Superseded by WORKFLOW.md GitHub Issues pattern
- **Code duplication**: Acceptable for marketplace independence; use templates for consistency

## Current State Analysis

### Repository Structure
```
claude-mp/
├── skills/              (9 skills, each distributed independently)
│   ├── omnifocus-manager    (complex: 22 scripts, TypeScript validation)
│   ├── skillsmith           (meta-skill: creates/improves skills)
│   ├── marketplace-manager  (meta-skill: marketplace operations)
│   ├── skill-planner        (DEPRECATED: superseded by WORKFLOW.md)
│   └── [6 domain skills]    (terminal-guru, swift-dev, helm-chart-developer, etc.)
├── .claude-plugin/
│   └── marketplace.json     (CRITICAL ISSUE: incorrect source paths)
├── docs/
│   ├── lessons/         (post-work retrospectives)
│   └── plans/           (pre-work planning)
└── WORKFLOW.md          (GitHub Issues + IMPROVEMENT_PLAN.md pattern)
```

### Marketplace Distribution Model

**How plugins are installed:**
```json
{
  "name": "ai-risk-mapper",
  "source": "./",                      // ❌ WRONG: Entire repository
  "skills": ["./skills/ai-risk-mapper"]
}
```

When users install `ai-risk-mapper`, they currently get:
```
~/.claude/plugins/ai-risk-mapper/
├── skills/                    // ❌ All 9 skills directories
│   ├── ai-risk-mapper/        // ✅ What they wanted
│   ├── skillsmith/            // ❌ Unwanted nested skill
│   ├── omnifocus-manager/     // ❌ Unwanted nested skill
│   └── ... (7 more)           // ❌ Unwanted nested skills
├── docs/
├── .claude-plugin/
└── ... (entire repo)
```

**Result**: Nested skill confusion, bloated installations, all skills trigger when user wanted one.

### Critical Issues

#### Issue #1: Source Path Misconfiguration
**Problem**: All 9 plugins use `"source": "./"` (repository root)

**Impact**:
- Users installing one skill get all 9 skills
- Nested skill triggers when user didn't install them
- Bloated installations (entire repo for each skill)
- Confusion about which skill is "active"

**Root Cause**: marketplace.json incorrectly configured during initial setup

**Correct Structure**:
```json
{
  "name": "ai-risk-mapper",
  "source": "./skills/ai-risk-mapper",  // ✅ Just this skill
  "skills": ["./"]                       // ✅ Skill at source root
}
```

#### Issue #2: No Deprecation Automation
**Problem**: Removing skills requires manual:
- marketplace.json edits
- Finding all skills that reference deprecated skill
- Updating IMPROVEMENT_PLAN.md
- Moving/deleting skill files
- Updating documentation

**Impact**: Error-prone, time-consuming, inconsistent

**Need**: Automated deprecation workflow via marketplace-manager

#### Issue #3: No Bundling Logic/Automation
**Problem**: No guidance or automation for creating multi-skill bundles

**Example use case**: skill-development-toolkit combining:
- skillsmith (skill creation/improvement)
- marketplace-manager (marketplace operations)
- Shared commands (/validate-skill, /sync-versions)
- Shared hooks (pre-commit validation)

**Need**: marketplace-manager logic to recommend and create bundles

#### Issue #4: Code Duplication Pattern Unclear
**Problem**: Skills duplicate utils code, but no template/consistency mechanism

**Current Reality**:
- `skills/skillsmith/scripts/utils.py` (repo detection)
- `skills/marketplace-manager/scripts/utils.py` (repo detection)
- `skills/skill-planner/scripts/utils.py` (repo detection)
- ~100 lines duplicated across 3 skills

**Marketplace Context**: This is FINE! Plugins must be self-contained.

**Need**: Template generation so duplication is consistent

#### Issue #5: skill-planner Obsolete
**Problem**: skill-planner uses git branch workflow, conflicts with WORKFLOW.md GitHub Issues pattern

**Evidence**:
- Recent plans use `docs/plans/` + GitHub Issues (WORKFLOW.md)
- skill-planner's PLAN.md in git branches is unused
- Competing sources of truth (PLAN.md vs GitHub Issues)

**Decision**: Deprecate skill-planner, use WORKFLOW.md pattern exclusively

## Implementation Phases

### Phase 1: marketplace-manager Core Improvements (v1.4.0)

**Priority**: CRITICAL - Fixes distribution architecture
**Target Issues**: #1, #2, #3, #4
**Version Bump**: 1.3.0 → 1.4.0 (MINOR - new features)

#### Changes

**1. Fix Source Paths for All Plugins**
- **Script**: `scripts/fix_source_paths.py` (NEW)
- **Purpose**: Corrects `"source"` in marketplace.json for all plugins
- **Logic**:
  ```python
  # For each plugin in marketplace.json:
  # Before:
  {
    "source": "./",
    "skills": ["./skills/ai-risk-mapper"]
  }

  # After:
  {
    "source": "./skills/ai-risk-mapper",
    "skills": ["./"]
  }
  ```
- **Safety**: Creates backup of marketplace.json before modification
- **Validation**: Verifies each source path exists
- **Output**: Summary of changes made

**2. Add Deprecation Automation**
- **Script**: `scripts/deprecate_skill.py` (NEW)
- **Purpose**: Automated workflow for skill deprecation
- **Features**:
  ```bash
  uv run scripts/deprecate_skill.py \
    --skill skill-planner \
    --reason "Superseded by WORKFLOW.md GitHub Issues pattern" \
    --migration-notes "Use GitHub Issues + docs/plans/ instead"
  ```
- **Actions**:
  1. Remove skill from marketplace.json
  2. Scan all SKILL.md files for references to deprecated skill
  3. Report skills that reference it (manual update needed)
  4. Add deprecation entry to IMPROVEMENT_PLAN.md Completed table
  5. Generate GitHub issue template for cleanup tasks
  6. Create migration guide in docs/lessons/ if provided
- **Safety**: Dry-run mode, confirmation prompts
- **Output**: Checklist of manual cleanup tasks

**3. Add Marketplace Validation**
- **Script**: `scripts/validate_marketplace.py` (NEW)
- **Purpose**: Comprehensive marketplace.json validation
- **Checks**:
  - Source paths exist and are correct format
  - No duplicate skill names
  - All referenced skills have valid SKILL.md
  - Version format compliance (semver)
  - No broken cross-skill references
  - Detects nested skill issues (source path problems)
- **Integration**: Pre-commit hook (existing hook enhanced)
- **Output**: Human-readable report + JSON for CI

**4. Add Bundling Logic and Recommendations**
- **Script**: `scripts/analyze_bundling.py` (NEW)
- **Purpose**: Analyze skills and recommend bundling opportunities
- **Logic**:
  ```python
  # Analyzes:
  # 1. Skills in same category
  # 2. Skills with cross-references
  # 3. Skills always used together (based on descriptions)
  # 4. Skill dependencies (implicit from references)

  # Recommends:
  # - Which skills to bundle
  # - Bundle name and description
  # - Whether to keep individual distributions
  ```
- **Interactive Mode**: Ask user questions to guide bundling decision
- **Output**: Proposed marketplace.json entry for bundle

**5. Add Utils Template Generation**
- **Script**: `scripts/generate_utils_template.py` (NEW)
- **Purpose**: Generate consistent utils.py for new skills
- **Features**:
  ```bash
  uv run scripts/generate_utils_template.py --skill new-skill
  ```
- **Generates**: `skills/new-skill/scripts/utils.py` with:
  - Repository detection (`find_repo_root()`)
  - Standard error handling
  - Logging setup
  - Common path utilities
- **Template Source**: `scripts/templates/utils.py.template`
- **Accepts Duplication**: Each skill gets its own copy (self-contained)

**6. Update SKILL.md**
- **Section**: "Marketplace Operations" (NEW)
- **Documents**:
  - Fixing source paths
  - Deprecating skills
  - Validating marketplace
  - Creating bundles
  - Generating utils templates
- **Examples**: Real command invocations with expected output

**7. Update IMPROVEMENT_PLAN.md**
- Add Phase 1 improvements to Completed table
- Link to GitHub issue
- Document key changes

#### Success Criteria
- ✅ All 9 plugins use correct source paths (self-contained)
- ✅ Deprecation workflow documented and tested
- ✅ Marketplace validation prevents future source path errors
- ✅ Bundling logic can recommend skill-development-toolkit
- ✅ Utils template generation works for new skills

#### Files Modified/Created

**Modified**:
- `.claude-plugin/marketplace.json` - Fix source paths for all plugins
- `skills/marketplace-manager/SKILL.md` - Add marketplace operations section
- `skills/marketplace-manager/IMPROVEMENT_PLAN.md` - Track Phase 1 changes

**Created**:
- `skills/marketplace-manager/scripts/fix_source_paths.py`
- `skills/marketplace-manager/scripts/deprecate_skill.py`
- `skills/marketplace-manager/scripts/validate_marketplace.py`
- `skills/marketplace-manager/scripts/analyze_bundling.py`
- `skills/marketplace-manager/scripts/generate_utils_template.py`
- `skills/marketplace-manager/scripts/templates/utils.py.template`

#### Testing Plan
1. **Source path fix**: Run on test marketplace.json, verify correctness
2. **Deprecation**: Dry-run on skill-planner, verify detection of references
3. **Validation**: Run on current marketplace.json, verify nested skill detection
4. **Bundling**: Analyze current skills, verify skill-development-toolkit recommendation
5. **Utils generation**: Generate for test skill, verify template quality

---

### Phase 2: Deprecate skill-planner (v1.5.0)

**Priority**: HIGH - Cleanup obsolete skill
**Prerequisites**: Phase 1 complete (deprecation automation exists)
**Version Bump**: 1.4.0 → 1.5.0 (MINOR - marketplace change)

#### Process

**1. Create GitHub Issue**
```bash
gh issue create \
  --title "Deprecate skill-planner skill" \
  --body "**Reason**: Superseded by WORKFLOW.md GitHub Issues pattern

**Background**: skill-planner uses git branch workflow with PLAN.md files. WORKFLOW.md now standardizes on GitHub Issues as source of truth with docs/plans/ for pre-work design.

**Tasks**:
- [ ] Run deprecate_skill.py to remove from marketplace
- [ ] Update skillsmith SKILL.md (remove skill-planner references)
- [ ] Update skillsmith references/improvement_workflow_guide.md (remove delegation logic)
- [ ] Create docs/lessons/workflow-simplification.md
- [ ] git rm -r skills/skill-planner/
- [ ] Update marketplace-manager version to v1.5.0
- [ ] Two-commit release

**Migration Guide**: Use WORKFLOW.md pattern instead:
- Pre-work planning: docs/plans/
- Active tracking: GitHub Issues (source of truth)
- Per-skill history: IMPROVEMENT_PLAN.md table
" \
  --label "deprecation" \
  --assignee @me
```

**2. Run Deprecation Automation**
```bash
uv run skills/marketplace-manager/scripts/deprecate_skill.py \
  --skill skill-planner \
  --reason "Superseded by WORKFLOW.md GitHub Issues pattern" \
  --migration-notes "Use GitHub Issues + docs/plans/ instead of git branch PLAN.md workflow"
```

**3. Manual Cleanup (from generated checklist)**
- Update skillsmith SKILL.md (remove skill-planner references)
- Update skillsmith/references/improvement_workflow_guide.md (remove delegation)
- Create docs/lessons/workflow-simplification.md
- `git rm -r skills/skill-planner/` (no archive, just delete)
- Update marketplace-manager IMPROVEMENT_PLAN.md

**4. Two-Commit Release**

**Commit 1 - Implementation**:
```bash
git add \
  .claude-plugin/marketplace.json \
  skills/skillsmith/SKILL.md \
  skills/skillsmith/references/improvement_workflow_guide.md \
  docs/lessons/workflow-simplification.md
git commit -m "feat(marketplace-manager): Deprecate skill-planner skill

- Remove skill-planner from marketplace.json
- Update skillsmith to remove skill-planner delegation
- Document WORKFLOW.md as standard pattern
- See docs/lessons/workflow-simplification.md for rationale

Refs #XXX"

git rm -r skills/skill-planner
git commit -m "chore: Remove deprecated skill-planner

Refs #XXX"
```

**Commit 2 - Release**:
```bash
git add \
  skills/marketplace-manager/IMPROVEMENT_PLAN.md \
  skills/marketplace-manager/SKILL.md
git commit -m "chore: Release marketplace-manager v1.5.0

Closes #XXX"
```

#### Success Criteria
- ✅ skill-planner removed from marketplace.json
- ✅ skillsmith no longer references skill-planner
- ✅ Migration guide created in docs/lessons/
- ✅ skills/skill-planner/ deleted (git rm)
- ✅ GitHub issue closed

---

### Phase 3: skill-development-toolkit Bundle (v2.0.0)

**Priority**: MEDIUM - Enhanced developer experience
**Prerequisites**: Phase 1 complete (bundling automation exists)
**Version Bump**: marketplace-manager 1.5.0 → 2.0.0 (MAJOR - new bundle paradigm)

#### Analysis

**Use bundling analysis to decide:**
```bash
uv run skills/marketplace-manager/scripts/analyze_bundling.py \
  --candidates skillsmith marketplace-manager \
  --bundle-name skill-development-toolkit
```

**Expected recommendation**:
```json
{
  "name": "skill-development-toolkit",
  "description": "Complete toolkit for skill development including creation, improvement, validation, and marketplace management",
  "category": "development",
  "version": "1.0.0",
  "skills": [
    "./skills/skillsmith",
    "./skills/marketplace-manager"
  ],
  "commands": [
    "./.claude/commands/validate-skill.md",
    "./.claude/commands/sync-versions.md",
    "./.claude/commands/init-skill.md"
  ],
  "hooks": [
    "./.claude/hooks/pre-commit/sync-marketplace-versions.sh",
    "./.claude/hooks/pre-commit/validate-improvement-plan.sh"
  ]
}
```

#### Decision Logic (in marketplace-manager)

**When to recommend bundling:**
- Skills in same category AND
- Skills have cross-references (one invokes the other) OR
- Skills share common commands/hooks OR
- Skills are "always used together" for a workflow

**For skill-development-toolkit:**
- ✅ Same category (development)
- ✅ Cross-references (skillsmith uses marketplace-manager for version sync)
- ✅ Share commands (validate-skill, sync-versions)
- ✅ Always used together (skill creation → marketplace publishing)

**Should individual skills remain available?**
- YES: Keep skillsmith standalone (users may not need marketplace publishing)
- YES: Keep marketplace-manager standalone (marketplace-only operations)
- Bundle is for convenience, not exclusivity

#### Implementation

**1. Create Commands (Repository-Local Development Tools)**

These are NOT distributed with plugins, they're for developing the marketplace itself:

```bash
.claude/commands/
├── validate-skill.md        # Wraps evaluate_skill.py
├── sync-versions.md         # Wraps sync_marketplace_versions.py
└── init-skill.md            # Wraps generate_utils_template.py + skill scaffold
```

**2. Create Hooks (Repository-Local Automation)**

```bash
.claude/hooks/
├── pre-commit/
│   ├── sync-marketplace-versions.sh    # Auto-sync (already exists)
│   └── validate-improvement-plan.sh    # Validate table format
└── post-commit/
    └── update-github-issues.sh         # Sync commit → issue checkboxes
```

**3. Add Bundle to marketplace.json**

```json
{
  "plugins": [
    {
      "name": "skill-development-toolkit",
      "description": "Complete toolkit for skill development",
      "category": "development",
      "version": "1.0.0",
      "source": "./",
      "skills": [
        "./skills/skillsmith",
        "./skills/marketplace-manager"
      ],
      "commands": [
        "./.claude/commands/validate-skill.md",
        "./.claude/commands/sync-versions.md",
        "./.claude/commands/init-skill.md"
      ],
      "hooks": [
        "./.claude/hooks/pre-commit/sync-marketplace-versions.sh",
        "./.claude/hooks/pre-commit/validate-improvement-plan.sh"
      ]
    },
    {
      "name": "skillsmith",
      "description": "Guide for creating and improving effective skills",
      "category": "development",
      "version": "3.2.0",
      "source": "./skills/skillsmith",
      "skills": ["./"]
    },
    {
      "name": "marketplace-manager",
      "description": "Manages Claude Code plugin marketplace operations",
      "category": "development",
      "version": "2.0.0",
      "source": "./skills/marketplace-manager",
      "skills": ["./"]
    }
  ]
}
```

**4. Update marketplace-manager SKILL.md**
- Document bundling decision logic
- Explain skill-development-toolkit composition
- Guide users on when to install bundle vs individual skills

#### Success Criteria
- ✅ skill-development-toolkit bundle available in marketplace
- ✅ Individual skills still available
- ✅ Commands and hooks functional in bundle
- ✅ Bundling logic documented for future bundles

---

## Repository vs. Per-Skill IMPROVEMENT_PLAN.md

**Clarification**: IMPROVEMENT_PLAN.md is **per-skill only**, not repository-wide.

**Why:**
- Travels with skill when distributed
- Skill-specific improvement history
- Users installing a skill see its roadmap

**Repository-wide tracking:**
- GitHub Issues (source of truth)
- docs/lessons/ (cross-skill learnings)
- docs/plans/ (pre-work design, ephemeral)

**Example:**
```
skills/marketplace-manager/IMPROVEMENT_PLAN.md   ✅ Skill-specific
skills/skillsmith/IMPROVEMENT_PLAN.md            ✅ Skill-specific
IMPROVEMENT_PLAN.md (repository root)            ❌ Not needed
```

GitHub Issues handle cross-skill work (like marketplace evolution).

---

## Workflow Integration

**For marketplace-manager improvements:**

1. **Create GitHub Issue** (source of truth):
```bash
gh issue create \
  --title "marketplace-manager: Add deprecation automation (Phase 1)" \
  --body "See docs/plans/2026-01-22-marketplace-manager-evolution.md Phase 1"
```

2. **Update marketplace-manager/IMPROVEMENT_PLAN.md**:
```markdown
| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #XXX  | Critical | Add deprecation automation | In Progress |
```

3. **Implement** (reference issue in commits)

4. **Two-commit release**:
   - Commit 1: Implementation files
   - Commit 2: Version bump + IMPROVEMENT_PLAN.md update (move to Completed)

**For cross-skill work (like deprecating skill-planner):**

1. **Create GitHub Issue** (tracks all affected skills)
2. **Update affected IMPROVEMENT_PLAN.md files**:
   - marketplace-manager/IMPROVEMENT_PLAN.md (adds deprecation feature)
   - skillsmith/IMPROVEMENT_PLAN.md (removes skill-planner references)
3. **Close single issue** when all work complete

---

## Benefits Summary

### For Marketplace Users
- **Clean installations**: Get only the skill they requested
- **No nested confusion**: One skill per installation
- **Bundle option**: skill-development-toolkit for complete workflow

### For Marketplace Developers
- **Automated deprecation**: No manual marketplace.json edits
- **Validation**: Prevents source path errors before commit
- **Bundling guidance**: Automation recommends when to bundle
- **Template consistency**: Utils generation ensures patterns

### For Repository
- **Correct architecture**: Plugins properly isolated
- **WORKFLOW.md alignment**: One source of truth (GitHub Issues)
- **Simplified meta-skills**: skill-planner removed, WORKFLOW.md standard
- **DRY with independence**: Templates for consistency, duplication for self-containment

---

## Implementation Timeline

**Phase 1: marketplace-manager Core** (3-4 days)
- Day 1: Fix source paths, marketplace validation
- Day 2: Deprecation automation, bundling logic
- Day 3: Utils template generation, testing
- Day 4: Documentation, review

**Phase 2: Deprecate skill-planner** (1 day)
- Use Phase 1 automation to deprecate
- Update skillsmith references
- Document in lessons/

**Phase 3: skill-development-toolkit** (2 days)
- Create commands and hooks
- Add bundle to marketplace
- Test installation and usage

**Total: 6-7 days**

---

## Success Metrics

| Metric | Current | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|---------|---------------|---------------|---------------|
| Correct source paths | 0/9 (0%) | 9/9 (100%) | 9/8 (100%) | 9/8 (100%) |
| Nested skill issues | All plugins | None | None | None |
| Deprecation automation | Manual | Automated | Tested | Tested |
| Active planning paradigms | 2 (WORKFLOW.md + skill-planner) | 2 | 1 (WORKFLOW.md) | 1 |
| Bundled developer tools | None | None | None | 1 (toolkit) |

---

## Risk Mitigation

**Risk: Breaking existing installations**
- **Mitigation**: Source path fix is backward compatible, users re-install to get clean version

**Risk: Deprecation workflow bugs**
- **Mitigation**: Dry-run mode, comprehensive testing on skill-planner first

**Risk: Bundling complexity**
- **Mitigation**: Keep individual skills available, bundle is optional convenience

**Risk: Template staleness**
- **Mitigation**: Template is source of truth, periodically regenerate for existing skills

---

## Open Questions

1. **Does Claude Code marketplace support bundled commands/hooks?**
   - **Recommendation**: Implement and test; if unsupported, document as repository-local only

2. **Should source path fix be applied retroactively to published plugins?**
   - **Recommendation**: Yes, publish corrected versions, document in changelogs

3. **Should deprecated skills remain in git history or be completely removed?**
   - **Recommendation**: git rm (remove completely), history in commits is sufficient

---

## References

- **WORKFLOW.md**: GitHub Issues + IMPROVEMENT_PLAN.md pattern
- **Current marketplace.json**: `.claude-plugin/marketplace.json`
- **marketplace-manager skill**: `skills/marketplace-manager/SKILL.md`
- **skillsmith skill**: `skills/skillsmith/SKILL.md`
