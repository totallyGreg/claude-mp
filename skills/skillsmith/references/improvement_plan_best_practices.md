# IMPROVEMENT_PLAN.md Best Practices

## Overview

The IMPROVEMENT_PLAN.md file is a living document that tracks your skill's evolution, planned improvements, and design decisions. It provides historical context for maintainers and helps organize development efforts.

**Purpose:**
- Track version history with dates and descriptions (most relevant - at top)
- Plan future enhancements organized by priority (forward-looking)
- Document completed improvements with implementation details (historical - at bottom)
- Capture design decisions and rationale
- Identify and track technical debt

**Recommended Structure (most relevant first):**
1. Overview
2. Version History - Quick reference, always at top
3. 🔮 Planned Improvements - What's coming next (tracked by NUMBER, not version)
4. Technical Debt / Enhancement Requests - Informs future planning
5. ✅ Recent Improvements (Completed) - Detailed history at bottom (tracked by VERSION)
6. Contributing / Notes

## Version Management Strategy

### Key Principle: Planned by Number, Released by Version

**IMPORTANT:** There's a critical distinction between planning and releasing:

- **🔮 Planned Improvements**: Track by NUMBER (1, 2, 3...), organized by priority
  - No version numbers assigned yet
  - Flexible - can be reordered, combined, or split
  - Example: "#### 1. Enhanced Skill Validation"

- **✅ Recent Improvements (Completed)**: Track by VERSION (v1.5.0, v1.4.0...)
  - Version assigned at release time
  - Permanent - part of version history
  - Example: "### v1.5.0 - Enhanced Skill Validation (2025-12-20)"

**Why this matters:**
- You might plan 5 improvements but not know which will be v1.6.0 vs v1.7.0
- Some improvements might be combined into a single release
- Others might be split across multiple releases
- Version numbers are only assigned when you actually release

### Version Decision Tree

Before starting work, ask: **Does this work warrant a version bump?**

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
         │  → Increment patch version
         │
         ├─ MINOR (1.4.0 → 1.5.0)
         │  - New features
         │  - Enhancements to existing features
         │  - Substantial documentation additions
         │  → Increment minor version
         │
         └─ MAJOR (1.4.0 → 2.0.0)
            - Breaking changes
            - Skill renames
            - Major restructuring
            → Increment major version
```

### Two-Commit Strategy (Recommended)

For any work that warrants a version bump, use this two-commit approach:

#### Commit 1: Implementation Only

```bash
# 1. Add improvement to IMPROVEMENT_PLAN.md Planned section (by NUMBER)
# Example: "#### 1. Enhanced Skill Validation"
# NO version number assigned yet

# 2. Implement the changes
# Edit SKILL.md content, scripts, references, etc.

# 3. Commit implementation (without version bump)
git add skills/my-skill/
git commit -m "feat: Add enhanced validation feature"

# SKILL.md version stays at current (e.g., 1.4.0)
# IMPROVEMENT_PLAN.md shows numbered planned improvement
# Marketplace.json unchanged
```

#### Commit 2: Release (When Ready)

```bash
# 1. Decide on version number based on decision tree
# Example: Enhanced validation is a new feature → v1.5.0 (minor)

# 2. Follow pre-release checklist:

# a) Move improvement from Planned to Completed in IMPROVEMENT_PLAN.md
#    - Cut from "🔮 Planned Improvements" (numbered section)
#    - Update header: "#### 1. Enhanced..." → "### v1.5.0 - Enhanced... (2025-12-20)"
#    - Paste at TOP of "✅ Recent Improvements (Completed)"
#    - Add to version history table: | 1.5.0 | 2025-12-20 | Description |

# b) Update SKILL.md frontmatter version
version: 1.5.0

# c) Run validation
python3 scripts/evaluate_skill.py --quick --check-improvement-plan skills/my-skill

# d) Sync marketplace (if using pre-commit hook, this happens automatically)
python3 scripts/sync_marketplace_versions.py

# 3. Commit release
git add skills/my-skill/IMPROVEMENT_PLAN.md
git add skills/my-skill/SKILL.md
git add .claude-plugin/marketplace.json
git commit -m "chore: Release my-skill v1.5.0"

# 4. Push to remote
git push
```

### Example: Full Workflow

**Planning Phase:**
```markdown
## 🔮 Planned Improvements
> Last Updated: 2025-12-20

### High Priority

#### 1. Enhanced Skill Validation
**Goal:** Expand validation capabilities
**Planned Features:**
- Validate skill references
- Check for broken links
...
```

**After Implementation Commit:**
- SKILL.md: `version: 1.4.0` (unchanged)
- IMPROVEMENT_PLAN.md: Still shows "#### 1. Enhanced..." in Planned
- Code changes committed

**After Release Commit:**
```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | 2025-12-20 | Enhanced skill validation |  ← Added
| 1.4.0 | 2025-12-01 | Previous release |

## 🔮 Planned Improvements
> Last Updated: 2025-12-20

### High Priority

#### 2. Multi-Skill Version Management  ← Now #1 is gone
...

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.5.0 - Enhanced Skill Validation (2025-12-20)  ← Moved here

**Goal:** Expand validation capabilities
...
```

- SKILL.md: `version: 1.5.0` (updated)
- marketplace.json: `version: 1.5.0` (synced)

### Benefits of Two-Commit Strategy

1. **Clear Separation**: Implementation vs release are distinct
2. **Flexible Timing**: Can implement now, release later
3. **Easy Rollback**: Can revert release commit without losing implementation
4. **Batch Releases**: Combine multiple improvements into one release
5. **Clean History**: Git history clearly shows what changed vs when it was released

### When to Use Single Commit

Single commit is acceptable for:
- Trivial patches (typo fixes)
- Urgent bug fixes that need immediate release
- Very small improvements where implementation = release

But when in doubt, use two commits.

## Version History Maintenance

### When to Add New Versions

Add a new version entry when you:
1. **Plan a new release** - Add with "TBD" date in "Planned Improvements"
2. **Complete implementation** - Move to "Recent Improvements (Completed)"
3. **Finalize for release** - Replace "TBD" with actual date, update SKILL.md version

### Version History Table Format

```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.4.0 | 2025-12-01 | Added IMPROVEMENT_PLAN.md validation and guidance |
| 1.3.0 | 2025-11-24 | IMPROVEMENT_PLAN.md standardization |
| 1.2.0 | 2025-11-20 | Repository root auto-detection |
| 1.1.0 | 2025-11-20 | Marketplace version sync automation |
| 1.0.0 | Initial | Initial skill implementation |
```

**Best Practices:**
- Order newest versions first (descending)
- Use YYYY-MM-DD date format
- Use "Initial" for first version date
- Keep descriptions concise (one line)
- Use "TBD" only for planned/in-progress versions

### TBD Placeholder Usage

**RECOMMENDED: Don't use TBD at all**

With the numbered approach for planned improvements, you typically don't need TBD:

```markdown
## 🔮 Planned Improvements
> Last Updated: 2025-12-20

### High Priority

#### 1. Enhanced Skill Validation  ← No version number yet
**Goal:** Expand validation capabilities
...

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.4.0 | 2025-12-01 | Current release |  ← No TBD needed
```

**If you must use TBD** (e.g., you've committed to a specific version for a planned feature):

```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Feature X enhancement |  ← Acceptable (not released yet)
| 1.4.0 | 2025-12-01 | Completed feature |    ← Has date (released)
```

**NEVER do this:**
```markdown
## ✅ Recent Improvements (Completed)

### v1.5.0 - Feature X Enhancement

...implementation complete...

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Feature X enhancement |  ← ERROR: Completed but still TBD!
```

**Rule:** If a version is in "Recent Improvements (Completed)", it MUST have an actual date in the version history table.

## Planned → Completed Workflow

When completing a planned improvement and releasing a new version, follow this workflow:

### Step 1: Decide Version Number
Use the Version Decision Tree to determine the appropriate version number based on the change type (patch/minor/major).

### Step 2: Cut from Planned Improvements
Locate the entire numbered section for the improvement in "🔮 Planned Improvements" and cut it.

### Step 3: Update Header with Version and Date
Change the header format:
- **From**: `#### 1. Enhanced Skill Validation` (numbered, no version)
- **To**: `### v1.5.0 - Enhanced Skill Validation (2025-12-20)` (versioned with date)

### Step 4: Paste at Top of Completed
Paste the section at the **TOP** of "✅ Recent Improvements (Completed)". This automatically maintains chronological order (newest first).

### Step 5: Add to Version History Table
Add the new version to the version history table:
- **Add**: `| 1.5.0 | 2025-12-20 | Enhanced skill validation |`
- Place at top of table (newest first)

**Note:** If you previously added an entry with TBD, replace it:
- **From**: `| 1.5.0 | TBD | Feature Name |`
- **To**: `| 1.5.0 | 2025-12-20 | Feature Name |`

### Step 6: Enhance with Implementation Details
Update the content:
- Change "**Proposed Solution:**" → "**Solution Implemented:**"
- Change "**Files to Modify:**" → "**Files Changed:**"
- Add "**Impact:**" section describing user-facing benefits

### Step 7: Update SKILL.md and Sync
- Update version in SKILL.md frontmatter
- Run validation: `python3 scripts/evaluate_skill.py --quick --check-improvement-plan`
- Sync marketplace (automatic with pre-commit hook)

**This workflow is intentionally simple**: decide version, cut, update header, paste at top, add to table, enhance details, update SKILL.md. No complex reorganization needed.

### Workflow Example

#### Phase 1: Planning
```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.4.0 | 2025-12-01 | Current release |  ← No future versions yet

## 🔮 Planned Improvements
> Last Updated: 2025-12-15

### High Priority

#### 1. Enhanced Skill Validation  ← Numbered, not versioned

**Goal:** Improve validation coverage
**Planned Features:**
- Validate skill references
- Check for broken links
...
```

#### Phase 2: Implementation
During implementation:
- Code changes are made
- Improvement stays numbered in "Planned Improvements"
- SKILL.md version stays at 1.4.0
- Commit implementation: `git commit -m "feat: Add enhanced validation"`

#### Phase 3: Release
When ready to release, follow the 7-step workflow:

1. **Decide version**: Enhanced validation is a new feature → v1.5.0 (minor bump)
2. **Cut** numbered improvement from Planned section
3. **Update header**: `#### 1. Enhanced...` → `### v1.5.0 - Enhanced... (2025-12-15)`
4. **Paste** at top of Completed section
5. **Add to version history** table
6. **Enhance** with implementation details
7. **Update SKILL.md** and sync

**After release commit:**

```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | 2025-12-15 | Enhanced validation coverage |  ← Added
| 1.4.0 | 2025-12-01 | Previous release |

## 🔮 Planned Improvements
> Last Updated: 2025-12-15

### High Priority

#### 1. Multi-Skill Version Management  ← Next improvement (renumbered from 2)
...

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.5.0 - Enhanced Skill Validation (2025-12-15)  ← Moved here with version

**Goal:** Improve validation coverage

**Solution Implemented:**
...

**Files Changed:**
- scripts/validator.py

**Impact:**
- Better validation coverage
...
```

**SKILL.md:**
```yaml
---
name: my-skill
version: 1.5.0  ← Updated from 1.4.0
---
```

**marketplace.json:** (synced automatically via pre-commit hook)
```json
{
  "version": "1.5.0"
}
```

## Common Pitfalls

### 1. Using Version Numbers in Planned Improvements

**Problem:**
```markdown
## 🔮 Planned Improvements

### High Priority - v1.6.0  ← ERROR: Planned improvements shouldn't have versions

#### Enhanced Validation
...
```

**Solution:**
```markdown
## 🔮 Planned Improvements

### High Priority

#### 1. Enhanced Validation  ← Correct: Numbered, not versioned
...
```

**Why this matters:**
- Version numbers should only be assigned when releasing
- Planned improvements may be combined, split, or reordered
- This prevents version confusion and orphaned version numbers

### 2. Forgetting to Replace TBD (if you use it)

**Problem:**
```markdown
# SKILL.md
version: 1.5.0

# IMPROVEMENT_PLAN.md
| 1.5.0 | TBD | Description |
```

**Detection:**
```bash
$ python3 scripts/evaluate_skill.py --quick --check-improvement-plan .

❌ Version 1.5.0 in SKILL.md shows 'TBD' in IMPROVEMENT_PLAN.md
   → Replace 'TBD' with completion date (YYYY-MM-DD) before release
   → File: IMPROVEMENT_PLAN.md line 123
```

**Fix:** Replace TBD with actual date before updating SKILL.md version

### 2. Mismatched Versions

**Problem:**
```markdown
# SKILL.md
version: 1.5.0

# IMPROVEMENT_PLAN.md - Version History
| 1.4.0 | 2025-12-01 | Latest entry |
```

**Detection:**
```bash
$ python3 scripts/evaluate_skill.py --quick --check-improvement-plan .

⚠️  SKILL.md version (1.5.0) differs from latest IMPROVEMENT_PLAN.md version (1.4.0)
   → This may be intentional if you haven't updated IMPROVEMENT_PLAN.md yet
```

**Fix:** Add v1.5.0 entry to version history table

### 3. Non-Chronological Dates

**Problem:**
```markdown
| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | 2025-11-01 | Newer version |  ← Older date
| 1.4.0 | 2025-12-01 | Older version |  ← Newer date
```

**Detection:**
```bash
$ python3 scripts/evaluate_skill.py --quick --check-improvement-plan .

⚠️  Version history dates may not be in chronological order
   → Consider ordering newest versions first
```

**Fix:** Ensure dates descend (newest → oldest)

### 4. Completed Section Without Date

**Problem:**
```markdown
## Recent Improvements (Completed)

### v1.5.0 - Enhanced Validation

Completed all implementation...

## Version History

| 1.5.0 | TBD | Description |  ← Still TBD despite completion
```

**Best Practice:** When moving an improvement to "Completed", add the completion date in both:
- Section header: `### v1.5.0 - Enhanced Validation (2025-12-15)`
- Version history: Replace TBD with actual date

## Pre-Release Checklist

Before releasing a new version, follow the Planned → Completed workflow:

- [ ] **Implementation complete** and tested
- [ ] **Decide version number** using the Version Decision Tree (patch/minor/major)
- [ ] **Cut** numbered improvement section from "🔮 Planned Improvements"
- [ ] **Update** header with version and date: `#### 1. Name` → `### v{version} - Name (YYYY-MM-DD)`
- [ ] **Paste** at TOP of "✅ Recent Improvements (Completed)"
- [ ] **Add to version history** table: `| {version} | YYYY-MM-DD | Description |`
- [ ] **Enhance** content:
  - Change "Proposed Solution" → "Solution Implemented"
  - Change "Files to Modify" → "Files Changed"
  - Add "Impact" section
- [ ] **Update** "Last Updated" in Planned Improvements section
- [ ] **Update** version in SKILL.md frontmatter
- [ ] **Run validation**: `python3 scripts/evaluate_skill.py --quick --check-improvement-plan <skill-path>`
- [ ] **Fix** any validation errors
- [ ] **Sync marketplace**: Automatic via pre-commit hook (or run `python3 scripts/sync_marketplace_versions.py`)
- [ ] **Commit** release: `git commit -m "chore: Release v{version}"`
- [ ] **Push** changes

## Example: skillsmith v1.5.0

The skillsmith skill follows these best practices itself. See `skills/skillsmith/IMPROVEMENT_PLAN.md` for a real example:

**Planning Phase:**
- Two improvements planned (numbered, not versioned):
  - IMPROVEMENT_PLAN.md restructuring
  - Skillsmith rename
- No version numbers assigned yet

**Implementation Phase (2 commits):**
- Commit 1: Implemented IMPROVEMENT_PLAN.md restructuring
- Commit 2: Implemented skillsmith rename
- Both improvements stayed numbered in Planned section
- SKILL.md stayed at v1.4.0

**Release Phase (1 commit):**
- Decided to combine both into v1.5.0 (minor bump - new features + breaking change)
- Removed both numbered improvements from Planned
- Created single v1.5.0 completed entry documenting both changes
- Added to version history: `| 1.5.0 | 2025-12-20 | IMPROVEMENT_PLAN.md restructuring and rename to skillsmith |`
- Updated SKILL.md: `version: 1.5.0`
- Synced marketplace
- Committed release

**Key Lesson:**
Multiple planned improvements can be combined into a single release version when appropriate.

## Validation Commands

**Basic skill validation:**
```bash
python3 scripts/evaluate_skill.py --quick skills/my-skill
```

**With IMPROVEMENT_PLAN.md checking:**
```bash
python3 scripts/evaluate_skill.py --quick --check-improvement-plan skills/my-skill
```

**Expected output (all good):**
```
Skill is valid!

✓ IMPROVEMENT_PLAN.md is complete and consistent
```

**Expected output (needs fix):**
```
Skill is valid!

❌ Version 1.5.0 in SKILL.md shows 'TBD' in IMPROVEMENT_PLAN.md
   → Replace 'TBD' with completion date (YYYY-MM-DD) before release
   → File: IMPROVEMENT_PLAN.md line 123
```

## Summary

### Key Principles

1. **Structure**: Version History (top) → 🔮 Planned → Technical Debt → ✅ Completed (bottom)
2. **Use TBD** for planned/in-progress versions in version history table
3. **Follow 5-step workflow** when completing: Cut → Update header → Paste at top → Update table → Enhance
4. **Replace TBD** when moving to completed AND before updating SKILL.md version
5. **Update "Last Updated"** in Planned Improvements when making changes
6. **Validate before release** with `--check-improvement-plan`
7. **Keep dates chronological** (newest first in both table and completed section)
8. **Use emoji indicators**: 🔮 for Planned, ✅ for Completed

### Simple Workflow

**Completing an improvement is intentionally simple:**
- Cut from Planned Improvements
- Update header with date
- Paste at top of Recent Improvements (Completed)
- Update version history table
- Enhance with implementation details

This ensures your skill's development history is clear, complete, and consistent, while making the transition from planned to completed straightforward.
