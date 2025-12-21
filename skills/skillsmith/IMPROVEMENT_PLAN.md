# Skillsmith - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the skillsmith skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.6.0 | TBD | Rename skill-creator to skillsmith |
| 1.4.1 | 2025-12-20 | Documentation improvements: plan mode guidance, init_skill.py path clarification, IMPROVEMENT_PLAN.md cleanup |
| 1.4.0 | 2025-12-01 | Added IMPROVEMENT_PLAN.md validation and guidance with enhanced validation script and best practices documentation |
| 1.3.0 | 2025-11-24 | Added IMPROVEMENT_PLAN.md as standard skill component with template generation and workflow integration |
| 1.2.0 | 2025-11-20 | Fixed script path detection with repository root auto-detection and improved error messages |
| 1.1.0 | 2025-11-20 | Added marketplace version sync automation with pre-commit hook |
| 1.0.0 | Initial | Initial skillsmith implementation with packaging and marketplace support |

## 🔮 Planned Improvements
> Last Updated: 2025-12-20

### High Priority - v1.6.0

#### Rename skill-creator to skillsmith

**Goal:** Rebrand skill to reflect customizations beyond original Claude examples

**Rationale:**
- Current name suggests generic template from Claude examples
- Significant enhancements made (IMPROVEMENT_PLAN.md structure, validation, automation)
- "skillsmith" better reflects the crafting/forging aspect of skill creation
- Establishes unique identity separate from upstream examples

**Scope of Changes:**

1. **Directory Structure**
   - Rename: `skills/skill-creator/` → `skills/skillsmith/`

2. **SKILL.md Frontmatter**
   - `name: skill-creator` → `name: skillsmith`
   - Update description to reference "skillsmith"
   - Version remains 1.4.0 (rename doesn't increment version)

3. **Marketplace Configuration** (`.claude-plugin/marketplace.json`)
   - Plugin name: `skill-creator` → `skillsmith`
   - Skills path: `./skills/skill-creator` → `./skills/skillsmith`
   - Update description if needed

4. **Documentation Updates**
   - `README.md`: Update skill name and references
   - `skills/README.md`: Update installation command and references
   - `paths-to-keep.txt`: Update directory name

5. **Self-Referential Documentation**
   - `IMPROVEMENT_PLAN.md`: Update title and all self-references
   - `references/improvement_plan_best_practices.md`: Update example references
   - `scripts/utils.py`: Update module docstring

6. **SKILL.md Content**
   - Update example commands showing script paths
   - Update any inline references to skill-creator

**Files to Modify (14 files):**
- Directory rename: `skills/skill-creator/` → `skills/skillsmith/`
- `skills/skillsmith/SKILL.md` - frontmatter name + path references
- `skills/skillsmith/IMPROVEMENT_PLAN.md` - title + self-references
- `skills/skillsmith/scripts/utils.py` - docstring
- `skills/skillsmith/references/improvement_plan_best_practices.md` - example references
- `.claude-plugin/marketplace.json` - plugin definition
- `README.md` - skill list
- `skills/README.md` - installation + references
- `paths-to-keep.txt` - directory name

**Migration Considerations:**

1. **Backward Compatibility**
   - Old installation command will break: `claude skill install totally-tools/skill-creator`
   - New command: `claude skill install totally-tools/skillsmith`
   - Document migration path for existing users

2. **Git History**
   - Use `git mv` to preserve file history
   - Single atomic commit for all changes

3. **Marketplace Transition**
   - Update marketplace.json before syncing
   - May need to deprecate old plugin or add redirect

4. **Testing Checklist**
   - Verify all scripts still run from new location
   - Test skill installation from marketplace
   - Validate SKILL.md renders correctly
   - Check all documentation links

**Success Criteria:**
- All references updated consistently
- No broken links in documentation
- Scripts run from new directory location
- Marketplace installation works with new name
- Git history preserved for all files
- No regression in functionality

**Estimated Effort:** 1-2 hours
**Risk Level:** Medium (many file changes, marketplace impact)
**Breaking Change:** Yes (installation command changes)

---

### High Priority

#### 1. Enhanced Skill Validation
**Goal:** Expand validation capabilities to catch more issues before packaging/deployment

**Planned Features:**
- Validate skill references in SKILL.md match actual files in scripts/, references/, assets/
- Check for broken internal links in markdown files
- Validate YAML frontmatter schema more strictly
- Ensure all bundled resources are properly referenced in SKILL.md
- Verify script files have proper shebangs and are executable
- Check for common anti-patterns (overly large SKILL.md, duplicated content)

**Implementation:**
- Enhance `scripts/quick_validate.py` with additional checks
- Add option for "strict" vs "lenient" validation modes
- Provide actionable error messages with suggestions

#### 2. Multi-Skill Version Management
**Goal:** Support skills with different versions within the same plugin

**Current Limitation:**
- sync_marketplace_versions.py assumes all skills in a plugin share the same version
- Uses the first skill's version for the entire plugin

**Proposed Solution:**
- Add option to specify version strategy: `first-skill`, `highest-version`, `manual`
- Document best practices for multi-skill plugin versioning
- Consider adding per-skill version tracking in marketplace.json (if schema supports)

#### 3. Skill Template Improvements
**Goal:** Make init_skill.py generate more useful templates

**Planned Enhancements:**
- Interactive mode: Ask questions about skill type and generate appropriate structure
- Multiple templates: basic, script-heavy, reference-heavy, asset-heavy
- Generate example .skillignore based on skill type
- Include common script patterns (argument parsing, error handling)
- Generate example reference markdown with proper structure

### Medium Priority

#### 4. Marketplace Analytics and Reporting
**Goal:** Help marketplace maintainers understand their plugin ecosystem

**Planned Features:**
- Script to analyze marketplace.json and generate reports:
  - Total skills, plugins, versions
  - Skills without versions
  - Version distribution (how many at v1.x, v2.x, etc.)
  - Detect potential issues (duplicate skills, missing descriptions)
  - Identify stale skills (no recent updates)
- Generate markdown report for README or documentation

#### 5. Skill Update Helper
**Goal:** Streamline the process of updating existing skills

**Planned Features:**
- Interactive update wizard: `scripts/update_skill.py <skill-name>`
  - Prompt for what changed (features, fixes, docs)
  - Suggest appropriate version bump (patch/minor/major)
  - Update version in SKILL.md frontmatter
  - Optionally add entry to CHANGELOG.md
  - Run validation and sync
- Integration with git workflow for atomic updates

#### 6. Better Documentation Generation
**Goal:** Auto-generate marketplace documentation from skills

**Planned Features:**
- Script to generate README sections from marketplace.json
- Create plugin catalog with descriptions and installation instructions
- Generate skill index with search/filter capabilities
- Output formats: Markdown, HTML, JSON for web integration

### Low Priority

#### 7. Skill Testing Framework
**Goal:** Enable automated testing of skills

**Conceptual Features:**
- Test harness for validating skill behavior
- Mock Claude environment for testing skill instructions
- Verify scripts execute correctly
- Check that references are readable and well-formed
- Automated regression testing on skill updates

**Challenges:**
- Skills are primarily instructional content, hard to test programmatically
- Would need to test that Claude can successfully execute instructions
- May require integration with Claude Code's testing infrastructure

#### 8. Skill Migration Tools
**Goal:** Help users migrate skills between formats or marketplaces

**Planned Features:**
- Convert standalone zip skills to marketplace format
- Migrate between marketplace structures
- Update skills to new schema versions
- Batch operations for marketplace reorganization

#### 9. Marketplace Dependency Management
**Goal:** Support skills that depend on other skills or external resources

**Conceptual Features:**
- Declare dependencies in SKILL.md frontmatter
- Validate dependencies exist in marketplace
- Suggest installation of dependent skills
- Version compatibility checking

**Challenges:**
- Would require schema changes to marketplace.json
- Complexity of dependency resolution
- May be better handled by Claude Code core functionality


## Enhancement Requests

### Community Feedback
*Track feature requests and suggestions from users here*

- **Request:** Add support for skill aliases or multiple names
  - **Status:** Under consideration
  - **Notes:** Would require marketplace.json schema changes

- **Request:** Skill usage analytics (how often skills are invoked)
  - **Status:** Deferred to Claude Code core team
  - **Notes:** Requires integration with Claude Code telemetry

## Technical Debt

### Code Quality
- Add comprehensive error handling to all Python scripts
- Improve test coverage (currently no automated tests)
- Standardize CLI argument parsing across scripts
- Add type hints to Python code (Python 3.8+)

### Documentation
- Create developer guide for contributing to skillsmith
- Document script API and internal functions
- Add more examples to references/plugin_marketplace_guide.md
- Create troubleshooting guide for common issues

### Infrastructure
- Set up CI/CD for validating skills on PR
- Automated testing of scripts
- Version compatibility matrix (which Claude Code versions support which features)

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.4.0 - IMPROVEMENT_PLAN.md Validation and Guidance (2025-12-01)

**Problem:**
The swift-dev skill v1.1.0 was completed with all implementation done, but the version history still showed "TBD" instead of the actual completion date. This indicated that while skillsmith instructs skills to update IMPROVEMENT_PLAN.md with dates, there was no validation to ensure this guidance was followed.

**Solution Implemented:**

1. **Enhanced Validation Script** (`scripts/quick_validate.py`):
   - Added `validate_improvement_plan()` function to check IMPROVEMENT_PLAN.md completeness
   - Detects "TBD" in version history for versions matching SKILL.md version (ERROR)
   - Warns about "TBD" in planned/future versions (acceptable)
   - Verifies SKILL.md version matches latest IMPROVEMENT_PLAN.md version
   - Checks that version history dates are in chronological order
   - Provides actionable error messages with file locations and line numbers
   - New CLI flag: `--check-improvement-plan` for targeted validation

2. **Enhanced SKILL.md Guidance** (Step 7: Iterate):
   - Added comprehensive **Pre-Release Checklist** with 9 steps
   - Emphasizes replacing "TBD" with actual date before release
   - Includes validation step in release workflow
   - Clear ordering: complete → document → validate → release

3. **Reference Documentation** (`references/improvement_plan_best_practices.md`):
   - Comprehensive guide (350+ lines) covering:
     - Version history maintenance workflow
     - TBD placeholder usage and when to replace
     - Common pitfalls with examples and fixes
     - Pre-release checklist
     - Real examples from skillsmith itself
   - Detailed workflow showing all phases: planning → implementation → completion → release

**Meta-Validation:**
Applied skillsmith to itself during implementation, demonstrating the self-referential nature of skill maintenance. Skillsmith now follows and validates its own guidance.

**Impact:**
- Skills can now validate their IMPROVEMENT_PLAN.md completeness before release
- Clear, actionable error messages guide developers to fix issues
- Prevents releasing skills with incomplete version history
- All future skills benefit from improved guidance and validation

**Files Changed:**
- `scripts/quick_validate.py` - Added IMPROVEMENT_PLAN.md validation logic (203 lines, +138)
- `SKILL.md` - Updated Step 7 with pre-release checklist
- `references/improvement_plan_best_practices.md` - New comprehensive guide

### v1.3.0 - IMPROVEMENT_PLAN.md Standardization (2025-11-24)

**Problem:**
- Skills lacked standardized way to track improvements and version history
- Design decisions not documented, making it hard for future maintainers to understand why changes were made
- No central place for planning and tracking enhancements

**Solution Implemented:**

1. **Added IMPROVEMENT_PLAN.md to skill structure**
   - Updated "Anatomy of a Skill" section in SKILL.md
   - Documented purpose, structure, and benefits
   - Added to recommended (not required) components

2. **Updated init_skill.py to generate template**
   - Comprehensive template with version history table
   - Sections for completed/planned improvements by priority
   - Enhancement requests and technical debt tracking
   - Contributing guidelines

3. **Integrated into workflow**
   - Added to Step 7 (Iterate) workflow
   - Document planned changes before implementation
   - Move to completed after implementation
   - Update version history with each release

4. **Updated .skillignore documentation**
   - Document that IMPROVEMENT_PLAN.md should be excluded from packages
   - Keep in version control for historical reference

**Impact:**
- Better institutional knowledge capture
- Clear improvement roadmap for each skill
- Historical context for design decisions
- Easier for new maintainers to understand skill evolution

**Files Changed:**
- `SKILL.md` - Added IMPROVEMENT_PLAN.md documentation in Anatomy, Step 3, and Step 7
- `scripts/init_skill.py` - Generate IMPROVEMENT_PLAN.md template
- `IMPROVEMENT_PLAN.md` - This entry

### v1.1.0 - Marketplace Version Sync Automation (2025-11-20)

**Problem:**
- When skills were updated with new versions in SKILL.md, the marketplace.json plugin versions didn't update automatically
- Manual version syncing was error-prone and easy to forget
- Packaging was emphasized over marketplace distribution, leading to zip file workflow confusion

**Solution Implemented:**

1. **Created `sync_marketplace_versions.py` script**
   - Automatically reads version from each skill's SKILL.md frontmatter
   - Updates corresponding plugin versions in marketplace.json
   - Supports dry-run mode for previewing changes
   - Location: `scripts/sync_marketplace_versions.py`

2. **Added Git pre-commit hook**
   - Automatically runs version sync before commits
   - Prevents commits with out-of-sync versions
   - Adds updated marketplace.json to the commit
   - Can be bypassed with `--no-verify` if needed
   - Location: `.git/hooks/pre-commit` (repository root)

3. **Updated SKILL.md documentation**
   - Reordered steps: Marketplace (Step 5) before Packaging (Step 6)
   - Added comprehensive Version Management section
   - Documented sync script and pre-commit hook setup
   - Added semantic versioning guidelines (patch/minor/major)
   - Clarified that zip packaging is optional and only for standalone distribution
   - Updated iteration workflow (Step 7) with version update guidance

**Impact:**
- Eliminates manual version sync errors
- Automates version management workflow
- Makes marketplace distribution the recommended default
- Clear guidance on when to use packaging vs marketplace

**Files Changed:**
- `scripts/sync_marketplace_versions.py` (new)
- `SKILL.md` (updated)
- `.git/hooks/pre-commit` (new, repository root)

### v1.0.0 - Initial Release
- Basic skill creation workflow
- SKILL.md template generation
- Packaging and validation scripts
- Marketplace integration documentation
- Progressive disclosure design principles

## Contributing

To suggest improvements to this skill:

1. Add enhancement requests to the "Enhancement Requests" section
2. Discuss technical approaches in "Planned Improvements"
3. Track implementation progress
4. Update "Completed Improvements" when done

## Notes

- This improvement plan should be excluded from skill packaging (see .skillignore)
- Update version history when making significant changes
- Link to relevant issues/PRs in your repository if applicable
