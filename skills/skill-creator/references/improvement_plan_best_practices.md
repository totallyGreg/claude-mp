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
3. 🔮 Planned Improvements - What's coming next
4. Technical Debt / Enhancement Requests - Informs future planning
5. ✅ Recent Improvements (Completed) - Detailed history at bottom
6. Contributing / Notes

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

**Correct usage:**
```markdown
## Planned Improvements

### High Priority - v1.5.0

...planned features...

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Feature X enhancement |  ← Acceptable (not released yet)
| 1.4.0 | 2025-12-01 | Completed feature |    ← Has date (released)
```

**Incorrect usage:**
```markdown
## Recent Improvements (Completed)

### v1.5.0 - Feature X Enhancement

...implementation complete...

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Feature X enhancement |  ← ERROR: Completed but still TBD!
```

**Rule:** If a version is in "Recent Improvements (Completed)", it MUST have an actual date in the version history table.

## Planned → Completed Workflow

When completing a planned improvement, follow this simple 5-step workflow:

### Step 1: Cut from Planned Improvements
Locate the entire section for the improvement in "🔮 Planned Improvements" and cut it.

### Step 2: Update Header with Date
Change the header format:
- **From**: `### High Priority - v1.5.0: Feature Name`
- **To**: `### v1.5.0 - Feature Name (2025-12-20)`

### Step 3: Paste at Top of Completed
Paste the section at the **TOP** of "✅ Recent Improvements (Completed)". This automatically maintains chronological order (newest first).

### Step 4: Update Version History Table
Find the version entry in the Version History table and replace "TBD" with the actual completion date:
- **From**: `| 1.5.0 | TBD | Feature Name |`
- **To**: `| 1.5.0 | 2025-12-20 | Feature Name |`

### Step 5: Enhance with Implementation Details
Update the content:
- Change "**Proposed Solution:**" → "**Solution Implemented:**"
- Change "**Files to Modify:**" → "**Files Changed:**"
- Add "**Impact:**" section describing user-facing benefits

**This workflow is intentionally simple**: cut, update header, paste at top, update table, enhance details. No complex reorganization needed.

### Workflow Example

#### Phase 1: Planning
```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Enhanced validation coverage |  ← TBD is fine here
| 1.4.0 | 2025-12-01 | Previous release |

## 🔮 Planned Improvements
> Last Updated: 2025-12-15

### High Priority - v1.5.0: Enhanced Validation

**Goal:** Improve validation coverage
...detailed plan...
```

#### Phase 2: Implementation
During implementation, the version stays in "Planned Improvements" with "TBD".

#### Phase 3: Completion
Move to "Recent Improvements (Completed)":

```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | TBD | Enhanced validation coverage |  ← Still TBD until release
| 1.4.0 | 2025-12-01 | Previous release |

## 🔮 Planned Improvements
> Last Updated: 2025-12-15

...future items...

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.5.0 - Enhanced Validation (2025-12-15)

**Goal:** Improve validation coverage
...implementation details...

**Files Changed:**
- scripts/validator.py
```

#### Phase 4: Release
**Before updating SKILL.md version:**

1. Replace "TBD" with completion date in Version History table:
```markdown
## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.5.0 | 2025-12-15 | Enhanced validation coverage |  ← Date added!
| 1.4.0 | 2025-12-01 | Previous release |
```

2. Update "Last Updated" in Planned Improvements section:
```markdown
## 🔮 Planned Improvements
> Last Updated: 2025-12-15
```

3. Update SKILL.md frontmatter:
```yaml
---
name: my-skill
version: 1.5.0  ← Updated from 1.4.0
---
```

4. Run validation:
```bash
python3 scripts/quick_validate.py --check-improvement-plan .
```

5. Sync and commit

## Common Pitfalls

### 1. Forgetting to Replace TBD

**Problem:**
```markdown
# SKILL.md
version: 1.5.0

# IMPROVEMENT_PLAN.md
| 1.5.0 | TBD | Description |
```

**Detection:**
```bash
$ python3 scripts/quick_validate.py --check-improvement-plan .

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
$ python3 scripts/quick_validate.py --check-improvement-plan .

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
$ python3 scripts/quick_validate.py --check-improvement-plan .

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

- [ ] Implementation complete and tested
- [ ] **Cut** improvement section from "🔮 Planned Improvements"
- [ ] **Update** header with completion date: `### v{version} - {name} (YYYY-MM-DD)`
- [ ] **Paste** at TOP of "✅ Recent Improvements (Completed)"
- [ ] **Enhance** content:
  - Change "Proposed Solution" → "Solution Implemented"
  - Change "Files to Modify" → "Files Changed"
  - Add "Impact" section
- [ ] **Update** version history table: Replace "TBD" with actual date (YYYY-MM-DD)
- [ ] **Update** "Last Updated" in Planned Improvements section
- [ ] **Update** version in SKILL.md frontmatter
- [ ] Run validation: `python3 scripts/quick_validate.py --check-improvement-plan <skill-path>`
- [ ] Fix any validation errors
- [ ] Sync marketplace (if applicable): `python3 scripts/sync_marketplace_versions.py`
- [ ] Commit and push changes

## Example: skill-creator v1.4.0

The skill-creator skill follows these best practices itself. See `skills/skill-creator/IMPROVEMENT_PLAN.md` for a real example:

**Planned Phase:**
- v1.4.0 added to "Planned Improvements" with detailed goals
- Version history shows: `| 1.4.0 | TBD | IMPROVEMENT_PLAN.md validation |`

**Implementation Phase:**
- Work on features while version stays in "Planned"
- TBD remains in version history

**Completion Phase:**
- Move v1.4.0 to "Recent Improvements (Completed)" with (2025-12-01) date
- Replace TBD: `| 1.4.0 | 2025-12-01 | IMPROVEMENT_PLAN.md validation |`
- Update SKILL.md: `version: 1.4.0`
- Run validation on itself
- Release!

## Validation Commands

**Basic skill validation:**
```bash
python3 scripts/quick_validate.py skills/my-skill
```

**With IMPROVEMENT_PLAN.md checking:**
```bash
python3 scripts/quick_validate.py --check-improvement-plan skills/my-skill
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
