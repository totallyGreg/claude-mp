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

## Conclusion

The omnifocus-manager skill evolved organically from v1.0 to v4.3.0, accumulating technical debt along the way. The main issue: **agents skip critical steps because workflow is buried and enforcement is weak**.

**Root cause:** Skill diverged from Agent Skill specifications over time.

**Solution:** Deterministic workflow with impossible-to-miss structure.

**For skillsmith:** Enforce these patterns from the start to prevent drift.
