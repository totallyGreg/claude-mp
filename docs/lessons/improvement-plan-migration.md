# IMPROVEMENT_PLAN.md Migration Guide

**Date:** 2026-01-18
**Status:** Active

## Overview

This guide documents the migration from verbose IMPROVEMENT_PLAN.md format to a lightweight table-based format that emphasizes GitHub Issues as the source of truth.

## Why We Changed

### Problems with Old Format

**Duplication:**
- Detailed planning lived in both IMPROVEMENT_PLAN.md and (ideally) GitHub Issues
- Required updating multiple places when plans changed
- Information often got out of sync

**Verbosity:**
- Each improvement had lengthy sections (Goal, Problem, Proposed Solution, etc.)
- File became difficult to scan quickly
- Hard to see overall skill evolution at a glance

**Unclear Source of Truth:**
- Was IMPROVEMENT_PLAN.md the source of truth, or GitHub Issues?
- Cross-machine work required copying context between files
- Discussion and task tracking scattered across files

### Benefits of New Format

**Single Source of Truth:**
- GitHub Issues are canonical
- IMPROVEMENT_PLAN.md reflects issue state (simple summary)
- No duplication of detailed planning

**Scannable:**
- Table format shows all planned/completed work at a glance
- Easy to see version history and progression
- Quick overview of what's in flight

**Better Collaboration:**
- GitHub Issues accessible from any machine
- Native task tracking with checkboxes
- Discussion and timeline in one place
- Email notifications and mentions

**Easier Maintenance:**
- Update issue once, table reflects it
- Simple row addition/update for releases
- Historical record still preserved in Completed table

## Format Comparison

### Old Format (Verbose)

```markdown
## 🔮 Planned Improvements
> Last Updated: 2026-01-15

**Note:** Planned improvements are tracked by NUMBER, not version.

### High Priority

#### 1. Add TypeScript Validation
**GitHub Issue**: #126
**Goal:** Validate plugin code before execution to catch errors early

**Problem:**
- Currently no validation of TypeScript code
- Errors only discovered at runtime
- Poor developer experience

**Proposed Solution:**
- Integrate TypeScript compiler API
- Validate on plugin load
- Provide helpful error messages

**Files to Modify:**
- `scripts/validate_plugin.py` - Add TS validation
- `SKILL.md` - Update documentation

**Success Criteria:**
- All invalid TS code caught before execution
- Clear error messages with line numbers
- Validation time < 500ms

### Medium Priority

#### 2. Improve Error Reporting
...
```

### New Format (Table)

```markdown
## 🔮 Planned Improvements

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #126  | High     | TypeScript validation | In Progress |
| #127  | Medium   | Improve error reporting | Open |

_For details, see linked GitHub issues._

**To add new improvements:**
1. Create GitHub issue with task checklist
2. Add row to this table with issue number
3. Update Status as work progresses (Open → In Progress → see Completed)

## ✅ Completed Improvements

| Version | Date | Issue | Title | Key Changes |
|---------|------|-------|-------|-------------|
| v2.2.0  | 2026-01-18 | #125 | Database query optimization | • Added connection pooling<br>• Implemented query caching<br>• Reduced query time by 60% |
| v2.1.0  | 2026-01-15 | #120 | Add task filtering | • Filter by project and context<br>• Support multiple filter criteria<br>• See docs/lessons/filtering-patterns.md |

_For implementation details, see closed issues and docs/lessons/._
```

**Key Differences:**
- Planned: Simple 4-column table (Issue, Priority, Title, Status)
- Completed: 5-column table with Key Changes (2-3 bullets)
- Detailed planning lives in GitHub Issues
- Complex retrospectives link to docs/lessons/

## Migration Strategy

### Recommended Approach (Hybrid)

**For new improvements:** Use table format exclusively

**For historical entries:** Keep as-is (optional: move to "Archive" section)

This hybrid approach:
- Requires minimal work (only new entries use tables)
- Preserves historical context
- Provides clean migration path

### Full Migration (Optional)

Convert all entries to table format:

1. **Planned Improvements:**
   - Create GitHub issue for each planned item
   - Add row to Planned table with issue number
   - Delete verbose sections

2. **Completed Improvements:**
   - Extract key changes (2-3 bullets) from each verbose entry
   - Create row in Completed table with version, date, issue (if exists), and key changes
   - Move detailed retrospectives to docs/lessons/ if needed
   - Add "Archive" section at bottom with original verbose entries for reference

## Migration Examples

### Example 1: Skillsmith (Hybrid Approach)

**Before Migration:**
```markdown
## 🔮 Planned Improvements

#### 1. Improve Skill Template
**Goal:** Make default skill template more helpful
**Problem:** New skills start with too much boilerplate
...
```

**After Migration (Hybrid):**
```markdown
## 🔮 Planned Improvements

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #130  | High     | Improve skill template | Planning |

_For details, see linked GitHub issues._

## ✅ Completed Improvements

| Version | Date | Issue | Title | Key Changes |
|---------|------|-------|-------|-------------|
| v2.0.0  | 2026-01-18 | #128 | Add PEP 723 validation | • Validate Python scripts use inline metadata<br>• Check uv compatibility field<br>• Provide migration guidance |

## Archive (Pre-Table Format)

### v1.9.0 - Enhanced Documentation (2026-01-10)
**Initial Features:**
- Improved SKILL.md examples
- Added references/python_uv_guide.md
...
```

### Example 2: OmniFocus-Manager (Full Migration)

**Before Migration:**
```markdown
## ✅ Recent Improvements (Completed)

### v4.4.0 - Deterministic Plugin Generation (2026-01-18)
**Changes:**
- Made plugin generation deterministic with sorted keys
- Improved reliability for version control
...

### v4.3.0 - System Discovery (2026-01-17)
**Changes:**
- Added automatic JXA system discovery
- TypeScript validation for generated plugins
...
```

**After Migration:**
```markdown
## ✅ Completed Improvements

| Version | Date | Issue | Title | Key Changes |
|---------|------|-------|-------|-------------|
| v4.4.0  | 2026-01-18 | #135 | Deterministic plugin generation | • Sorted JSON keys for consistent output<br>• Improved git diff reliability<br>• Reduced merge conflicts |
| v4.3.0  | 2026-01-17 | #134 | System discovery + TS validation | • Automatic JXA discovery<br>• TypeScript validation<br>• See docs/lessons/ts-validation-learnings.md |
| v4.2.0  | 2026-01-15 | #132 | Consolidate references | • Reduced SKILL.md from 800 to 400 lines<br>• Moved content to references/<br>• Improved progressive disclosure |

_For implementation details, see closed issues and docs/lessons/._
```

## Step-by-Step Migration

### For Individual Skills

1. **Create GitHub Issues (if not exists):**
   ```bash
   # For each planned improvement
   gh issue create --title "skill-name: Improvement Title" \
     --body "**Goal**: Brief description

   **Tasks**:
   - [ ] Task 1
   - [ ] Task 2

   See IMPROVEMENT_PLAN.md (old entry) for detailed context"
   ```

2. **Update IMPROVEMENT_PLAN.md:**
   - Add Planned Improvements table at top
   - Add Completed Improvements table below it
   - Move old entries to "Archive" section (or delete if redundant)

3. **Populate Tables:**
   - Planned: Copy issue numbers from GitHub
   - Completed: Extract key changes (2-3 bullets) from old entries

4. **Validate:**
   ```bash
   uv run skills/skillsmith/scripts/evaluate_skill.py skills/skill-name --quick --check-improvement-plan
   ```

### For New Skills

New skills automatically use table format when created with updated `init_skill.py`:

```bash
uv run skills/skillsmith/scripts/init_skill.py my-new-skill
```

Generated IMPROVEMENT_PLAN.md will have table structure already in place.

## Validation

The updated `evaluate_skill.py` validates both formats:

**Old format:** Checks Version History table for TBD dates and version consistency

**New format:** Validates:
- Planned table has Issue, Priority, Title, Status columns
- Completed table has Version, Date, Issue, Title, Key Changes columns
- Issue numbers use #XXX format
- Tables are well-formed

Run validation:
```bash
# Quick validation (structure only)
uv run skills/skillsmith/scripts/evaluate_skill.py skills/skill-name --quick --check-improvement-plan

# Full validation
uv run skills/skillsmith/scripts/evaluate_skill.py skills/skill-name
```

## Best Practices

### Writing Key Changes

Keep bullets compact but informative:

**Good:**
```markdown
• Added connection pooling for 60% faster queries
• Implemented caching with 10-minute TTL
• See docs/lessons/db-optimization.md
```

**Too Verbose:**
```markdown
• Added connection pooling. This was a major improvement because previously we were creating a new connection for every query, which was very slow. Now we maintain a pool of 10 connections that are reused, which reduces query time by approximately 60% in our benchmarks.
```

**Too Terse:**
```markdown
• Performance improvements
• Bug fixes
```

### Linking to docs/lessons/

For complex work with important learnings:

1. Create detailed retrospective in `docs/lessons/<topic>.md`
2. Reference it in Key Changes column: "See docs/lessons/topic.md"
3. This keeps table compact while preserving deep context

### Issue Management

**When creating issues:**
- Use consistent title format: `skill-name: Feature Name`
- Add task checklist in issue body
- Reference any docs/plans/ files
- Assign to yourself with `--assignee @me`

**When closing issues:**
- Use commit message: `chore: Release skill-name vX.Y.Z\n\nCloses #123`
- GitHub automatically closes issue and links it
- Move from Planned → Completed table in same commit

## Troubleshooting

### Issue: Old verbose entries taking up space

**Solution:** Move to Archive section or delete if redundant:

```markdown
## Archive (Pre-Table Format)

<details>
<summary>Historical verbose entries (pre-2026-01-18)</summary>

### v1.0.0 - Initial Release (2025-12-01)
...
</details>
```

### Issue: Can't find GitHub issue number

**Solution:** Search closed issues or create new issue retroactively:

```bash
# Search for closed issues
gh issue list --state closed --search "keyword"

# Create retroactive issue
gh issue create --title "skill-name: Past Feature" \
  --body "Retroactive issue for tracking v1.2.0 changes" \
  --label "retroactive"
```

### Issue: Table not rendering properly

**Solution:** Ensure proper markdown table syntax:
- Each row starts and ends with `|`
- Header separator uses `|---|---|`
- No extra spaces breaking alignment

```markdown
| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| #123  | High     | Feature | Open |
```

## References

- `/WORKFLOW.md` - Complete workflow documentation
- `skills/skillsmith/scripts/init_skill.py` - Generates new table format
- `skills/skillsmith/scripts/evaluate_skill.py` - Validates both formats
- `.claude/CLAUDE.md` - Project-level workflow instructions

## Questions?

For questions about migration:
1. Check `/WORKFLOW.md` for workflow details
2. Look at recently migrated skills for examples
3. Run validation with `--check-improvement-plan` flag
