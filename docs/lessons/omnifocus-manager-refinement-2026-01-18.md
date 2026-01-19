# Refinement Errors - Lessons for Skillsmith

This document captures errors and missteps found during omnifocus-manager v4.4.0 refinement to improve skillsmith guidance for future skill development.

**Date:** 2026-01-18
**Skill:** omnifocus-manager
**Version:** v4.3.0 → v4.4.0
**Primary Issue:** Agents skip critical workflow steps despite instructions

---

## Organization Violations (Agent Skill Specification)

### Error 1: Validation tools in wrong directory

**What was wrong:**
- Validation tools in `assets/development-tools/` instead of `scripts/`
- Scripts: `validate-plugin.sh`, `test-plugin-libraries.js`, `validate-js-syntax.js`
- Violates Agent Skill spec: Executable tools belong in `scripts/`

**Agent Skill Specification:**
> **scripts/** - Self-contained executable code
> - When to include: Same code written repeatedly, deterministic behavior needed, complex algorithms
> - Requirements: Self-contained, handle dependencies gracefully, include error handling

**Why this matters:**
- Assets should be output resources (templates, images), not execution tools
- Creates confusion about where to find executable tools
- Violates progressive disclosure (unclear organization)

**Skillsmith improvement:**
- Enforce `scripts/` directory for ALL executables during skill creation
- Validation check: Flag executable files in `assets/` directory
- Template should include pre-created `scripts/` directory structure

### Error 2: Scattered script organization

**What was wrong:**
- No clear indication of which script is the "primary tool"
- Validation tools separate from generation tools
- No README explaining script organization

**Why this matters:**
- Agents don't know which tool to use first
- Workflow tools should be grouped together
- Lack of documentation creates guesswork

**Skillsmith improvement:**
- Template should include `scripts/README.md` explaining each script's purpose
- Support for marking "primary tools" in some way (naming, documentation)
- Encourage grouping related tools

---

## Progressive Disclosure Failures

### Error 3: Critical workflow buried in middle of SKILL.md

**What was wrong:**
- Plugin generation workflow started at line 98 (not line 23-30)
- Critical "MANDATORY PLUGIN GENERATION WORKFLOW" appeared AFTER "What This Skill Does"
- Agents scan from top; buried content gets skipped

**Agent Skill Specification:**
> **Progressive Disclosure Architecture**
> - Level 1 - Metadata (~100 tokens): `name` + `description` always loaded
> - Level 2 - Instructions (<5000 tokens recommended): Full SKILL.md body loaded when skill activates
> - Rule: Keep SKILL.md under 500 lines; move detailed content to references/

**Why this matters:**
- Agents scan content sequentially
- Critical workflow must be impossible to miss
- First 50-100 lines define agent behavior

**Solution implemented:**
- Moved workflow immediately after frontmatter (now starts at line 23)
- Added "⚡ CRITICAL" visual marker
- Workflow appears BEFORE explanatory content

**Skillsmith improvement:**
- Template structure should enforce workflow-first layout
- Critical workflows should appear in first 100 lines
- Provide SKILL.md template with sections in correct order:
  1. Frontmatter
  2. Title
  3. CRITICAL workflows (if applicable)
  4. Purpose/capabilities
  5. Decision trees
  6. References

### Error 4: Redundant workflow documentation

**What was wrong:**
- Two sections describing same workflow:
  - "MANDATORY PLUGIN GENERATION WORKFLOW" (lines 98-166)
  - Scattered workflow steps in decision tree
- Creates confusion about which is authoritative
- Wastes tokens loading duplicate information

**Why this matters:**
- Agents may follow wrong version
- Maintenance burden (must update multiple places)
- Violates DRY principle in documentation

**Solution implemented:**
- Consolidated into single CRITICAL workflow at top
- Other sections reference the authoritative workflow
- Single source of truth

**Skillsmith improvement:**
- Validate SKILL.md for duplicate content
- Encourage single authoritative workflow with references
- Template should demonstrate proper cross-referencing

---

## Enforcement Gaps

### Error 5: "MANDATORY" steps that sound optional

**What was wrong:**
- Section titled "MANDATORY PLUGIN GENERATION WORKFLOW" but no enforcement
- "### VALIDATE PLUGINS" sounds like a suggestion
- No self-check mechanism for compliance
- Passive language: "After any plugin changes, run..."

**Why this matters:**
- Agents interpret as optional unless strongly enforced
- "MANDATORY" loses meaning without accountability
- Need active voice and compliance checks

**Solution implemented:**
- Added "COMPLIANCE SELF-CHECK" with checkboxes
- Changed language to active enforcement:
  - "MANDATORY - Always run"
  - "Zero tolerance"
  - "If you skipped ANY step above, you did it wrong"
- Added self-verification requirement

**Skillsmith improvement:**
- Template should include enforcement language patterns:
  - "CRITICAL", "MANDATORY", "Zero tolerance"
  - Self-check checklists for critical workflows
  - Active voice commands: "DO X" not "X should be done"
- Provide examples of strong vs weak enforcement language

### Error 6: Lack of RED FLAG warnings

**What was wrong:**
- No explicit warnings against anti-patterns
- Didn't warn: "If you're about to use Write/Edit for plugins → STOP"
- No "STOP if you're doing this" language
- Agents would use Write/Edit tools instead of generator

**Why this matters:**
- Agents need explicit warnings about wrong approaches
- Proactive prevention better than reactive correction
- Visual markers (🚫, ❌, ⚠️) increase visibility

**Solution implemented:**
- Added: "**🚫 RED FLAG:** If about to use Write or Edit tool for .js/.omnijs files → STOP"
- Explicit STOP command before suggesting correct approach
- Visual emoji markers for immediate recognition

**Skillsmith improvement:**
- Template should include RED FLAG section for common mistakes
- Provide patterns for anti-pattern warnings
- Encourage use of visual markers (🚫, ⚠️, ❌, ✅)

---

## Reference Chain Issues

### Error 7: Tool paths changed but references not updated

**What was wrong:**
- Validation tools moved but references still pointed to old locations
- 5 files had stale paths to `assets/development-tools/`:
  - SKILL.md (frontmatter)
  - code_generation_validation.md
  - AITaskAnalyzer.omnifocusjs/README.md
  - IMPROVEMENT_PLAN.md
  - validation-README.md

**Why this matters:**
- Broken references create confusion
- Agents can't find tools
- Wastes time troubleshooting non-existent paths

**Solution implemented:**
- Updated all references to `scripts/validate-plugin.sh`
- Used grep to find all occurrences systematically
- Updated historical documentation (IMPROVEMENT_PLAN.md)

**Skillsmith improvement:**
- Reference validation during skill updates
- Check for broken file paths before releasing
- Automated reference checking tool
- Warning when moving/renaming frequently-referenced files

### Error 8: References not contextual to workflow

**What was wrong:**
- Validation documentation in separate file (`code_generation_validation.md`)
- No inline reference at decision point in workflow
- Agents had to remember to check validation rules separately

**Why this matters:**
- References should be contextual (appear when needed)
- Inline references reduce cognitive load
- "Just-in-time" information delivery more effective

**Solution implemented:**
- Added validation references directly in CRITICAL workflow
- "See X for details" at point of use
- Quick reference format in decision tree

**Skillsmith improvement:**
- Encourage inline references at decision points
- Progressive disclosure: summary in SKILL.md, details in references/
- Template demonstrates contextual referencing

---

## Progressive Disclosure Violations

### Error 9: Large SKILL.md with details belonging in references/

**What was wrong:**
- SKILL.md 327 lines (within limit but unnecessarily large)
- Workflow details duplicated in multiple places
- Examples inline instead of in references/
- TypeScript validation details should be in references/

**Agent Skill Specification:**
> - Rule: Keep SKILL.md under 500 lines
> - Before adding content to SKILL.md: "Could this live in references/ instead?"
> - If it's >3 paragraphs → Probably references/

**Why this matters:**
- Larger files = more tokens loaded every time
- Detailed content slows down quick reference
- SKILL.md should be decision-making guide, not encyclopedia

**Solution implemented:**
- Removed redundant 68-line workflow section
- Added concise "Why TypeScript Validation is Mandatory" (17 lines)
- References point to detailed guides

**Skillsmith improvement:**
- Stricter enforcement of content placement rules
- Automated check: Warn if SKILL.md > 400 lines
- Template shows clear examples of what belongs where
- Decision tree in skillsmith: "SKILL.md vs references/ vs assets/"

---

## Feature Status Ambiguity

### Error 10: Incomplete features presented as current capabilities

**What was wrong:**
- Foundation Models integration described as working capability
- Conflation of:
  - AITaskAnalyzer plugin (✅ working, uses Foundation Models)
  - patterns.js library (`callFoundationModel` commented out, placeholder)
- No clear status markers (Stable, Experimental, Planned)

**Why this matters:**
- Agents don't know what's actually usable
- Creates false expectations
- Wastes time trying to use incomplete features

**Solution implemented:**
- Added "Why TypeScript Validation is Mandatory" explaining automatic validation
- Will add feature status tracking in future improvements
- Clarified AITaskAnalyzer as working example

**Skillsmith improvement:**
- Feature status tracking system:
  - ✅ Stable - Production ready
  - ⚠️ Experimental - Works but may change
  - 🔮 Planned - Future feature
- Template includes status section
- Validate that all mentioned features have status markers

---

## Summary of Improvements for Skillsmith

### 1. Directory Organization
- ✅ Enforce `scripts/` for all executables
- ✅ Add validation for files in wrong directories
- ✅ Template with pre-created directory structure
- ✅ Include `scripts/README.md` in template

### 2. SKILL.md Structure
- ✅ Workflow-first template layout
- ✅ Critical workflows in first 100 lines
- ✅ Single source of truth (no duplication)
- ✅ Progressive disclosure validation (warn if >400 lines)

### 3. Enforcement Language
- ✅ Template with enforcement patterns:
  - CRITICAL, MANDATORY, Zero tolerance
  - COMPLIANCE SELF-CHECK checklists
  - 🚫 RED FLAG warnings
  - Active voice commands
- ✅ Examples of strong vs weak language

### 4. Reference Management
- ✅ Automated reference checking
- ✅ Contextual references (inline at decision points)
- ✅ Validation before file moves/renames

### 5. Feature Status Tracking
- ✅ Status markers (✅ Stable, ⚠️ Experimental, 🔮 Planned)
- ✅ Template includes status section
- ✅ Validate all features have status

### 6. Content Placement Decision Tree
```
Before adding to SKILL.md, ask:
1. Does something else already trigger this?
   → Don't duplicate (trust enforcement)
2. Could this live in references/ instead?
   → If >3 paragraphs → references/
3. Is this core to workflow?
   → Core workflow → SKILL.md
   → Optional detail → references/
   → Rarely needed → Consider removing
```

---

## Testing Recommendations

After implementing these skillsmith improvements:

1. **Test with real skill creation:**
   - Create new skill using improved template
   - Verify directory structure enforced
   - Check workflow appears in first 100 lines

2. **Test with skill updates:**
   - Modify existing skill
   - Verify reference validation catches broken paths
   - Check duplicate content detection works

3. **Test enforcement:**
   - Verify RED FLAG warnings prevent wrong approaches
   - Check COMPLIANCE SELF-CHECK is intuitive
   - Ensure active voice commands are clear

4. **Measure effectiveness:**
   - Do agents skip fewer critical steps?
   - Are workflows easier to follow?
   - Is content placement clearer?

---

## Release Process Failures (Post-Commit Verification)

After commit 3c3b40e claimed to implement v4.4.0, post-commit verification revealed several failures in the release process itself.

### Error 11: Version bump not applied

**What was wrong:**
- Commit message claimed "v4.4.0"
- IMPROVEMENT_PLAN.md version history table listed v4.4.0
- But SKILL.md still showed `version: 4.3.0` in two places (frontmatter and footer)

**Why this matters:**
- Version is the canonical identifier for skill state
- Discrepancy between commit message and actual version creates confusion
- Cannot verify what version is actually deployed

**Skillsmith improvement:**
- Version bump should be part of release checklist
- Consider automated version validation before commit
- Release script could verify version consistency across files

### Error 12: Moved files not tested after move

**What was wrong:**
- `validation-README.md` moved from `assets/development-tools/` to `scripts/`
- Internal relative paths still referenced old locations:
  - `../omnifocus-manager/assets/development-tools/validate-plugin.sh`
  - `../../references/plugin_development_guide.md`
- Nobody ran the commands in the README to verify they worked

**Why this matters:**
- Moving files breaks relative paths
- Documentation becomes misleading
- Users following instructions hit errors

**Skillsmith improvement:**
- After moving files, test any commands/paths they contain
- Automated path validation in moved files
- Release checklist: "Did you test all moved files?"

### Error 13: validate-plugin.sh had silent failure

**What was wrong:**
- TypeScript path was `../../typescript` (wrong)
- Should have been `../typescript` (sibling to scripts/)
- Script silently skipped TypeScript validation with a warning
- Bug existed since the file was moved but was never caught

**Why this matters:**
- Silent failures hide broken functionality
- Validation that doesn't run provides false confidence
- Path bugs after file moves are common

**Skillsmith improvement:**
- Test validation scripts on real plugins after any changes
- Consider failing loudly instead of warning and continuing
- Path validation: verify referenced directories exist

### Error 14: Redundant documentation moved instead of deleted

**What was wrong:**
- `validation-README.md` duplicated content already in SKILL.md
- Was moved to `scripts/` when it should have been deleted
- Nothing referenced it; served no purpose
- Had 7+ broken path references after move

**Why this matters:**
- Cruft accumulates if not actively removed
- Moving redundant files wastes effort maintaining them
- "Where should this go?" is wrong question; ask "Is this needed?"

**Skillsmith improvement:**
- Before moving files, ask: "Is this file even necessary?"
- Check if content is duplicated elsewhere
- Check if anything references the file
- Delete redundant documentation, don't relocate it

### Error 15: No post-commit verification

**What was wrong:**
- Commit claimed "Update all references (5 files) to new paths"
- This was not verified by actually running the tools
- `validate-plugin.sh` was broken and nobody noticed
- Validation-README.md had broken paths and nobody noticed

**Why this matters:**
- Claims in commit messages must be verifiable
- "Update all references" requires testing, not just editing
- Without verification, bugs ship as "fixes"

**Skillsmith improvement:**
- Release checklist: Run affected tools after changes
- For validation tooling changes: test on a real plugin
- Don't trust "find and replace" - verify functionality

---

## Summary: Release Process Improvements

### Pre-Release Checklist
- [ ] Version bumped in ALL locations (frontmatter + footer)
- [ ] All moved files tested (commands, paths work)
- [ ] Redundant files deleted, not moved
- [ ] Validation scripts tested on real plugins
- [ ] Reference paths verified (not just edited)

### Questions Before Moving Files
1. Is this file even necessary?
2. Does anything reference it?
3. Is content duplicated elsewhere?
4. If moving: did I update internal paths?
5. If moving: did I test commands in the file?

---

## Conclusion

The omnifocus-manager skill evolved organically from v1.0 to v4.3.0, accumulating technical debt along the way. The main issue: **agents skip critical steps because workflow is buried and enforcement is weak**.

**Root cause:** Skill diverged from Agent Skill specifications over time.

**Solution:** Deterministic workflow with impossible-to-miss structure.

**For skillsmith:** Enforce these patterns from the start to prevent drift.

**Additional lesson from v4.4.0 release:** Release process itself needs verification. Commit messages claiming changes were made doesn't mean they were made correctly. Post-commit verification caught 5 additional errors that shipped in the "fix" commit.
