# Skill Improvement Workflow Guide

This reference provides detailed guidance on how skillsmith routes and handles skill improvement requests. Load this file when you need to understand the improvement workflow in depth or when implementing complex skill improvements.

---

## Overview

Skillsmith is the main entry point for all skill-related work and intelligently routes improvement requests based on complexity. This guide explains how skillsmith determines whether to handle improvements directly or use the WORKFLOW.md pattern for complex changes.

---

## Improvement Routing Logic

### Quick Updates (Handled Directly by Skillsmith)

Quick updates are simple, low-risk changes that skillsmith handles directly without requiring a GitHub Issue or planning document.

**Qualifying Changes:**
- Adding reference files to `references/`
  - Validates reference structure
  - Detects consolidation opportunities
  - Both reference file and validation included in commit
- Updating SKILL.md documentation (< 50 line changes)
- Adding examples, clarifications, or fixing typos
- Minor script fixes (< 20 lines)
- Single file, single concern, low risk changes

**Version Handling:**
- Automatic PATCH bump (e.g., 1.0.0 → 1.0.1)
- No user input required for version number

**Workflow:**
1. Skillsmith analyzes the request and determines it's quick
2. Reads current skill state to understand context
3. Makes the requested changes directly
4. Runs `evaluate_skill.py` to verify no regressions
5. Automatically bumps `metadata.version` to next PATCH
6. Asks user: "Commit these changes?"
7. On approval, commits changes
8. Optionally invokes marketplace-manager to sync marketplace.json

---

### Complex Improvements (WORKFLOW.md Pattern)

Complex improvements require systematic planning and follow the WORKFLOW.md pattern with GitHub Issues as the source of truth.

**Qualifying Changes:**
- Restructuring SKILL.md sections (> 50 lines)
- Adding new scripts or significant script modifications
- Changing workflow procedures or processes
- Multi-file coordinated changes
- Breaking changes or major refactors

**Version Handling:**
- User selects MINOR (1.0.0 → 1.1.0) for new features
- User selects MAJOR (1.0.0 → 2.0.0) for breaking changes

**Workflow:**
1. Skillsmith analyzes the request and determines it's complex
2. Informs user: "This requires systematic planning. Following WORKFLOW.md pattern..."
3. Create GitHub Issue with task checklist:
   - Use `gh issue create` with comprehensive task list
   - Link to any planning docs in `docs/plans/`
   - Add appropriate labels (enhancement, breaking-change, etc.)
4. Add to skill's IMPROVEMENT_PLAN.md table:
   - Add row to "Planned Improvements" section
   - Link to GitHub Issue (source of truth)
   - Mark status as "Open"
5. Create planning document in `docs/plans/` if needed:
   - Name format: `YYYY-MM-DD-skill-name-feature.md`
   - Ephemeral - can be deleted after completion
   - Referenced from GitHub Issue
6. Implement changes:
   - Research current state (using `research_skill.py`)
   - Make changes following the plan
   - Check off tasks in GitHub Issue as completed
7. Skillsmith asks user: "Version bump? MINOR (new feature) or MAJOR (breaking)?"
8. Updates `metadata.version` based on user selection
9. Update IMPROVEMENT_PLAN.md:
   - Move from Planned to Completed section
   - Add completion date and summary
10. Close GitHub Issue when all work is complete

---

## Automatic Detection Criteria

Skillsmith analyzes requests using these heuristics to determine routing:

### File Count
- **1 file** = Likely quick update
- **2+ files** = Likely complex improvement

### Line Changes
- **< 50 lines** = Quick update
- **≥ 50 lines** = Complex improvement

### Scope
- **Documentation/references** = Quick update
- **Structure/workflow changes** = Complex improvement

### Impact
- **Additive** (adding new content) = Quick update
- **Modifications** (changing existing behavior) = Complex improvement

---

## User Override Options

Users can override automatic detection using explicit phrases:

### Force Quick Handling
Say any of these to skip planning for a complex change:
- "handle this quickly"
- "quick update"
- "don't plan this"
- "do this directly"

### Force Planning
Say any of these to force systematic planning for a simple change:
- "use planning"
- "create a plan"
- "create a GitHub Issue"
- "plan this improvement"

---

## Version Bump Guidelines

### MAJOR (X.0.0)
Increment major version for breaking changes:
- Changed workflow that breaks existing usage patterns
- Removed or renamed core features
- Major architectural rewrites
- Incompatible API changes

**Example:** 1.0.0 → 2.0.0

### MINOR (x.X.0)
Increment minor version for new features:
- New bundled resources (scripts, references, assets)
- New functionality or capabilities
- Backward-compatible enhancements
- Significant documentation improvements

**Example:** 1.0.0 → 1.1.0

### PATCH (x.x.X)
Increment patch version for fixes and minor updates:
- Bug fixes
- Documentation updates
- Minor improvements
- Typo corrections
- Reference additions

**Example:** 1.0.0 → 1.0.1

**Note:** PATCH bumps are automatic for quick updates. MINOR and MAJOR bumps require user selection.

---

## Integration with Other Skills

### WORKFLOW.md Pattern

The WORKFLOW.md pattern is used for complex improvements and provides:
- GitHub Issues as source of truth
- IMPROVEMENT_PLAN.md table for tracking
- Ephemeral planning docs in `docs/plans/`
- Task checklists in issues
- Cross-machine accessibility

**When to use:**
- Complex changes requiring research
- Multi-file coordinated changes
- Breaking changes or refactors
- When user explicitly requests planning

### marketplace-manager Integration

marketplace-manager is optionally invoked for publishing:
- Syncing version between SKILL.md and marketplace.json
- Committing skills to marketplace
- Pushing to remote repositories
- Managing multi-skill plugin versions

**When to use:**
- After completing improvements
- When ready to publish to marketplace
- For version synchronization

---

## Complexity Classification Examples

### Quick Update Examples

**Example 1: Add reference file**
```
User: "Add a reference file for API schemas"
→ Quick: Single file, additive, documentation
→ Automatic PATCH bump: 1.0.0 → 1.0.1
```

**Example 2: Fix typo**
```
User: "Fix the typo in SKILL.md line 42"
→ Quick: Single file, < 50 lines, low risk
→ Automatic PATCH bump: 1.1.0 → 1.1.1
```

**Example 3: Add example**
```
User: "Add an example showing how to use research_skill.py"
→ Quick: Single file, additive, documentation
→ Automatic PATCH bump: 2.0.0 → 2.0.1
```

### Complex Improvement Examples

**Example 1: Restructure workflow**
```
User: "Simplify the skill creation process to 5 steps instead of 6"
→ Complex: Structure change, > 50 lines, workflow modification
→ Use WORKFLOW.md pattern (GitHub Issue + IMPROVEMENT_PLAN.md + docs/plans/)
→ User selects MINOR or MAJOR: 1.0.0 → 2.0.0 (breaking workflow)
```

**Example 2: Add new script**
```
User: "Add a script to automatically generate skill documentation"
→ Complex: New script, multi-file (script + SKILL.md docs)
→ Use WORKFLOW.md pattern (GitHub Issue + planning doc)
→ User selects MINOR: 1.0.0 → 1.1.0 (new feature)
```

**Example 3: Major refactor**
```
User: "Refactor the validation system to use a plugin architecture"
→ Complex: Multi-file, breaking change, architectural
→ Use WORKFLOW.md pattern with detailed planning in docs/plans/
→ User selects MAJOR: 1.5.0 → 2.0.0 (breaking change)
```

---

## Best Practices

### For Quick Updates
1. Keep changes focused on a single concern
2. Verify no regressions with `evaluate_skill.py`
3. Let automatic PATCH bumping handle versioning
4. Commit promptly after validation passes

### For Complex Improvements
1. Create GitHub Issue with clear improvement goals and task checklist
2. Add to IMPROVEMENT_PLAN.md table linking to issue
3. Create planning doc in docs/plans/ if needed for design work
4. Check off tasks in GitHub Issue as you complete them
5. Choose appropriate version bump (MINOR vs MAJOR)

### For Users
1. Trust automatic routing for most changes
2. Override only when you have specific workflow preferences
3. Prefer planning for changes you're uncertain about
4. Let skillsmith handle version numbering

---

## Troubleshooting

### "I want this planned but skillsmith handled it directly"

**Solution:** Use override phrase:
```
User: "Use planning - add comprehensive testing documentation"
```

### "This seems too simple for planning"

**Solution:** Use override phrase:
```
User: "Handle this quickly - restructure the examples section"
```

### "How do I know if my change is quick or complex?"

**Reference:** Use the automatic detection criteria above:
- 1 file + < 50 lines + additive = Quick
- 2+ files OR ≥ 50 lines OR modifications = Complex

### "What if I disagree with the version bump?"

**For quick updates:**
- PATCH bumps are automatic
- If you want MINOR/MAJOR, say "use planning" to force complex workflow

**For complex improvements:**
- Skillsmith asks you to select MINOR or MAJOR
- Provide your preferred version when prompted

---

## Related Skills

- **WORKFLOW.md** - Repository-wide workflow pattern (GitHub Issues + IMPROVEMENT_PLAN.md)
- **marketplace-manager** - Publishing and version synchronization
- **research_skill.py** - Deep skill analysis (used for complex improvements)
- **evaluate_skill.py** - Validation and metrics (used in both workflows)

---

*This guide describes the routing logic and improvement workflows for skillsmith. For general skill creation guidance, see SKILL.md.*
