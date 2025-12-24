# Skillsmith Integration Guide

This guide provides detailed information about how Skillsmith coordinates with skill-planner and marketplace-manager to handle skill improvements and distribution.

## Architecture Overview

```
User Request → Skillsmith (Main Actor)
                    |
                    ├── Quick Update? → Handle Directly
                    |   ├── Make changes
                    |   ├── Auto PATCH version
                    |   └── Call marketplace-manager → Commit
                    |
                    └── Complex Update? → Invoke skill-planner
                        ├── skill-planner workflow (research → plan → approve → implement)
                        ├── Ask user: MINOR or MAJOR version?
                        └── Call marketplace-manager → Commit to plan branch
```

## Complexity Classification Criteria

### Quick Updates (Skillsmith Handles Directly)

**Characteristics:**
- Single concern, well-defined scope
- Low risk of introducing regressions
- Doesn't require systematic analysis or planning
- Can be completed in < 30 minutes
- Changes are additive rather than modifications

**Specific Examples:**

1. **Adding Reference Files**:
   - Adding new file to `references/` directory
   - Updating existing reference documentation
   - Adding examples or clarifications
   - **Detection**: File path contains `references/`, additive change

2. **Documentation Updates**:
   - Updating SKILL.md descriptions (< 50 line changes)
   - Fixing typos or broken links
   - Adding usage examples
   - Clarifying existing instructions
   - **Detection**: Only SKILL.md changed, < 50 lines affected

3. **Minor Bug Fixes**:
   - Fixing script syntax errors (< 20 lines)
   - Correcting metadata in frontmatter
   - Fixing broken file paths
   - **Detection**: Changes in scripts/ are < 20 lines, targeted fix

4. **Asset Updates**:
   - Adding files to `assets/` directory
   - Updating templates
   - Adding images or icons
   - **Detection**: File path contains `assets/`, additive change

**Automatic Detection Signals:**
- **File count**: 1 file modified = strong quick signal
- **Line delta**: < 50 lines = strong quick signal
- **Directory**: `references/`, `assets/` = moderate quick signal
- **Operation**: File addition = moderate quick signal
- **Scope keywords**: "add", "fix typo", "update docs" = moderate quick signal

**Version Bump**: Automatic PATCH (1.0.0 → 1.0.1)

---

### Complex Improvements (Delegate to skill-planner)

**Characteristics:**
- Multi-file or multi-concern changes
- Structural modifications to workflow or architecture
- Requires systematic analysis and metrics validation
- Benefits from planning and approval gates
- Moderate to high risk of regressions

**Specific Examples:**

1. **Restructuring SKILL.md**:
   - Moving sections for better progressive disclosure
   - Reorganizing workflow steps
   - Splitting content into multiple reference files
   - **Detection**: SKILL.md changes > 50 lines, structural keywords

2. **Adding New Scripts**:
   - Creating new Python/Bash scripts in `scripts/`
   - Adding new workflow automation
   - Implementing new features that require code
   - **Detection**: New file in `scripts/`, or existing script > 50 lines changed

3. **Workflow Changes**:
   - Modifying skill creation process steps
   - Changing integration patterns
   - Adding new phases or procedures
   - **Detection**: Keywords like "workflow", "process", "restructure"

4. **Multi-File Coordinated Changes**:
   - Updating SKILL.md + scripts + references together
   - Refactoring that spans multiple components
   - Breaking changes that affect multiple files
   - **Detection**: 2+ files modified, especially in different directories

5. **Breaking Changes**:
   - Changing skill behavior that affects existing users
   - Removing or renaming bundled resources
   - Modifying frontmatter schema
   - **Detection**: Keywords like "breaking", "remove", "rename"

**Automatic Detection Signals:**
- **File count**: 2+ files modified = strong complex signal
- **Line delta**: ≥ 50 lines in SKILL.md = strong complex signal
- **Directory**: Changes in `scripts/` = moderate complex signal
- **Operation**: Deletions, renames, moves = strong complex signal
- **Scope keywords**: "restructure", "refactor", "breaking" = strong complex signal

**Version Bump**: User selects MINOR (1.0.0 → 1.1.0) or MAJOR (1.0.0 → 2.0.0)

---

## Decision Algorithm

```python
def determine_complexity(request, analysis):
    """
    Determine if skill improvement is quick or complex.
    Returns: 'quick', 'complex', or 'ask_user'
    """

    # Explicit user override
    if "handle this quickly" in request or "quick update" in request:
        return 'quick'
    if "use planning" in request or "create a plan" in request:
        return 'complex'

    # Analyze change characteristics
    files_modified = analysis['files_modified']
    total_line_changes = analysis['total_line_changes']
    skill_md_line_changes = analysis['skill_md_line_changes']
    directories_affected = analysis['directories_affected']
    operations = analysis['operations']  # ['add', 'modify', 'delete', 'rename']
    scope_keywords = analysis['scope_keywords']

    # Strong complex signals
    if len(files_modified) >= 3:
        return 'complex'
    if 'delete' in operations or 'rename' in operations:
        return 'complex'
    if skill_md_line_changes >= 100:
        return 'complex'
    if any(kw in scope_keywords for kw in ['restructure', 'refactor', 'breaking']):
        return 'complex'
    if 'scripts/' in directories_affected and total_line_changes >= 50:
        return 'complex'

    # Strong quick signals
    if len(files_modified) == 1 and total_line_changes < 50:
        if directories_affected == {'references/'} or directories_affected == {'assets/'}:
            return 'quick'
        if operations == ['add']:
            return 'quick'

    # Moderate signals - ask user or use conservative default
    if len(files_modified) == 2 and total_line_changes < 50:
        return 'ask_user'  # "This could be handled quickly or with planning. Prefer: quick/planning?"

    # Conservative default: favor planning for ambiguous cases
    if total_line_changes >= 50 or len(files_modified) >= 2:
        return 'complex'

    return 'quick'
```

---

## User Override Patterns

### Forcing Quick Handling

**User says:**
- "Handle this quickly without planning"
- "Quick update: add X to Y"
- "Don't use planning for this"

**Skillsmith behavior:**
- Skips complexity analysis
- Proceeds directly with quick update workflow
- Still runs evaluate_skill.py for validation
- Still requires user approval for commits

### Forcing Systematic Planning

**User says:**
- "Create an improvement plan for X"
- "Use planning to restructure Y"
- "I want systematic planning for this change"

**Skillsmith behavior:**
- Skips complexity analysis
- Immediately invokes skill-planner
- Follows complete planning workflow
- User maintains full control over plan approval

---

## Integration Patterns

### Skillsmith → skill-planner

**Invocation Context:**
```
Skillsmith: "Invoking skill-planner for complex improvement to {skill-name}..."

Context passed to skill-planner:
- Skill name and path
- User's improvement goal
- Initial complexity analysis (why planning was chosen)
- Current skill version
```

**skill-planner Returns:**
```
Results returned to Skillsmith:
- Implementation complete: yes/no
- Changes made: list of modified files
- Before/after metrics
- Plan status: approved → implemented
- Plan branch: plan/{skill-name}-{desc}-{date}
```

**Skillsmith Next Actions:**
1. Reviews implementation results
2. Asks user: "Version bump? MINOR (new feature) or MAJOR (breaking change)?"
3. Updates metadata.version in SKILL.md
4. Calls marketplace-manager for version sync

### Skillsmith → marketplace-manager

**Invocation Context:**
```
Skillsmith: "Calling marketplace-manager to sync versions and commit changes..."

Context passed to marketplace-manager:
- Changed files: SKILL.md (and possibly others)
- New version in SKILL.md metadata
- Commit message context (what changed)
- Current branch (main or plan branch)
```

**marketplace-manager Actions:**
1. Runs sync_marketplace_versions.py
2. Updates marketplace.json with new version
3. Shows diff to user
4. Asks: "Commit these changes? [yes/no]"
5. If yes, commits SKILL.md + marketplace.json together
6. Asks: "Push to remote? [yes/no]"
7. If yes, pushes to remote repository

**marketplace-manager Returns:**
```
Results returned to Skillsmith:
- Sync status: success/failure
- Commit SHA (if committed)
- Files committed: list
- Push status: pushed/not-pushed
```

---

## Workflow Diagrams

### Quick Update Flow

```
1. User: "Add reference doc for API to skill X"
   ↓
2. Skillsmith analyzes complexity
   - Files: 1 (references/api_docs.md)
   - Lines: ~200 (new file)
   - Operation: add
   - Decision: QUICK
   ↓
3. Skillsmith handles directly
   - Reads current skill state
   - Creates references/api_docs.md
   - Updates SKILL.md to reference it (if needed)
   - Runs evaluate_skill.py
   ↓
4. Skillsmith auto-bumps version
   - Current: 1.2.0
   - New: 1.2.1 (PATCH)
   - Updates metadata.version in SKILL.md
   ↓
5. Skillsmith calls marketplace-manager
   - "Sync and commit skill X changes"
   ↓
6. marketplace-manager syncs marketplace.json
   - Detects version 1.2.0 → 1.2.1
   - Updates marketplace.json
   ↓
7. marketplace-manager asks user
   - "Commit these changes?" → YES
   - Commits: SKILL.md + marketplace.json
   - "Push to remote?" → YES
   - Pushes to origin/main
   ↓
8. Done! Quick update complete in ~3 user interactions
```

### Complex Improvement Flow

```
1. User: "Restructure skill-planner to improve progressive disclosure"
   ↓
2. Skillsmith analyzes complexity
   - Files: 1 (SKILL.md)
   - Lines: ~150 (restructuring)
   - Operation: modify (structural)
   - Keywords: "restructure"
   - Decision: COMPLEX
   ↓
3. Skillsmith informs user
   - "This requires systematic planning. Invoking skill-planner..."
   ↓
4. Skillsmith invokes skill-planner
   - Passes: skill-name, improvement goal, context
   ↓
5. skill-planner executes workflow
   - Phase 1: Research (runs research_skill.py)
   - Phase 2: Plan (creates PLAN.md in plan branch)
   - User can refine plan multiple times
   - Phase 3: Approve (user explicitly approves)
   - Phase 4: Implement (makes changes in plan branch)
   ↓
6. skill-planner returns to Skillsmith
   - Implementation complete
   - Before/after metrics
   - Plan branch: plan/skill-planner-progressive-20251223
   ↓
7. Skillsmith asks user for version
   - "Version bump? MINOR (new feature) or MAJOR (breaking)?"
   - User selects: MINOR
   - Skillsmith updates: 1.0.0 → 1.1.0
   ↓
8. Skillsmith calls marketplace-manager
   - "Sync and commit to plan branch"
   ↓
9. marketplace-manager syncs and commits
   - Updates marketplace.json: 1.0.0 → 1.1.0
   - Commits to plan branch
   - Asks about push → YES
   ↓
10. User tests changes in plan branch
    - Verifies improvements
    - Runs validation scripts
    ↓
11. User merges plan branch to main
    - git merge plan/skill-planner-progressive-20251223
    ↓
12. skill-planner detects merge
    - Archives PLAN.md to completed/
    - Updates plan status: completed
    ↓
13. Done! Complex improvement complete with full audit trail
```

---

## Error Handling

### Complexity Analysis Errors

**Scenario**: Skillsmith chooses quick but user expected planning

**User says:** "I wanted systematic planning for this"

**Skillsmith response:**
- "Understood. Switching to systematic planning."
- Invokes skill-planner with original request
- Notes for future: user's complexity preference

**Scenario**: Skillsmith chooses complex but change is actually simple

**User says:** "This is simple, handle it quickly"

**Skillsmith response:**
- "Understood. Handling directly without planning."
- Proceeds with quick update workflow
- Notes for future: refine detection thresholds

### Integration Failures

**Scenario**: skill-planner fails during implementation

**skill-planner returns:** Error message and partial state

**Skillsmith response:**
1. Reports error to user
2. Offers manual fallback: "Continue manually in plan branch?"
3. Preserves plan branch and state for debugging
4. Does NOT auto-bump version or call marketplace-manager

**Scenario**: marketplace-manager sync fails

**marketplace-manager returns:** Error (e.g., marketplace.json syntax error)

**Skillsmith response:**
1. Reports sync error to user
2. Suggests manual fix: "Check marketplace.json syntax"
3. Offers retry after manual fix
4. Does NOT commit if sync failed

---

## Best Practices

### For Quick Updates

1. **Always validate**: Run evaluate_skill.py even for trivial changes
2. **Conservative auto-PATCH**: Only auto-bump for truly safe changes
3. **Clear communication**: Tell user what changed and why version bumped
4. **Preserve audit trail**: Meaningful commit messages

### For Complex Improvements

1. **Don't rush approval**: Let skill-planner's approval gates work
2. **Respect user override**: If they want quick, trust their judgment
3. **Metrics matter**: Show before/after comparisons from evaluate_skill.py
4. **Plan branches are safe**: Encourage testing before merge

### For All Improvements

1. **User approval required**: Never auto-commit or auto-push without asking
2. **Explain decisions**: Tell user why quick vs. planning was chosen
3. **Allow override**: Always respect "handle this quickly" or "use planning"
4. **Progressive disclosure**: Move complexity details to this reference file

---

## Future Enhancements

### Machine Learning-Based Classification

Potential future improvement: Train on historical quick vs. complex decisions to improve automatic detection accuracy.

**Data to collect:**
- User's request text
- Actual changes made (files, lines, operations)
- Whether quick or complex was used
- Whether user overrode the decision
- Time to completion
- Regressions detected

### Hybrid Workflow

For changes that fall in the middle:
- Quick initial implementation
- Optional "Upgrade to planning" if issues found
- Lightweight review without full planning workflow

### Confidence Scores

Instead of binary quick/complex:
- Report confidence: "85% confident this is quick"
- Ask user when confidence < 70%
- Learn from user responses

---

## See Also

- **skill-planner** - Systematic planning workflow for complex improvements
- **marketplace-manager** - Version syncing and marketplace distribution
- **AgentSkills Specification** - `agentskills_specification.md` in this directory
- **Research Guide** - `research_guide.md` for evaluation tools and metrics
