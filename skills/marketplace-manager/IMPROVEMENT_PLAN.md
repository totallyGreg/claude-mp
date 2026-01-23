# Marketplace Manager - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the marketplace-manager skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.4.0 | 2026-01-22 | Core marketplace operations automation: source path fixes, deprecation, bundling, templates |
| 1.3.0 | 2026-01-07 | Critical bug fixes: utils.py dependency, schema compliance, metadata.version parsing |
| 1.1.0 | 2025-12-22 | Added plugin versioning strategies, validation command, pre-commit hook |
| 1.0.0 | 2025-12-21 | Initial release |

## 🔮 Planned Improvements
> Last Updated: 2026-01-22

**Note:** Planned improvements are tracked by NUMBER, not version. Version numbers are only assigned when releasing.

### Critical Priority (Blocking Issues)

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| [#5](https://github.com/totallyGreg/claude-mp/issues/5) | High | Deprecate skill-planner skill (v1.5.0) | In Progress |

#### [#5](https://github.com/totallyGreg/claude-mp/issues/5) Deprecate skill-planner Skill (IN PROGRESS)
**Goal:** Remove obsolete skill-planner skill from marketplace

**Problem:**
- skill-planner uses git branch workflow (PLAN.md in branches)
- Conflicts with WORKFLOW.md GitHub Issues pattern (current standard)
- Competing sources of truth (PLAN.md vs GitHub Issues)
- skill-planner unused - recent plans use docs/plans/ + GitHub Issues

**Prerequisites:**
- Issue #4 must be complete (deprecation automation must exist)

**Proposed Solution:**
- Run deprecation automation to remove from marketplace.json
- Update skillsmith to remove skill-planner references
- Create migration guide in docs/lessons/
- Delete skills/skill-planner/ (git rm, no archive)

**Files to Modify:**
- `.claude-plugin/marketplace.json` - Remove skill-planner
- `skills/skillsmith/SKILL.md` - Remove skill-planner references
- `skills/skillsmith/references/improvement_workflow_guide.md` - Remove delegation logic
- `skills/marketplace-manager/IMPROVEMENT_PLAN.md` - Track completion
- `skills/skillsmith/IMPROVEMENT_PLAN.md` - Document removal

**Files to Create:**
- `docs/lessons/workflow-simplification.md` - Migration guide

**Files to Delete:**
- `skills/skill-planner/` - Entire directory (git rm)

**Success Criteria:**
- ✅ skill-planner removed from marketplace
- ✅ skillsmith no longer references skill-planner
- ✅ Single source of truth: WORKFLOW.md pattern only

**Version Bump:** 1.4.0 → 1.5.0 (MINOR - marketplace change)

**Plan:** See docs/plans/2026-01-22-marketplace-manager-evolution.md Phase 2

### Resolved Issues (Kept for Reference)

#### Document "strict" Field in References (RESOLVED - NOT AN ISSUE)
**Goal:** Document the "strict" field which is part of official plugin specification

**Resolution:**
- The "strict" field is documented in official Claude Code plugin reference at https://code.claude.com/docs/en/plugins-reference
- Field is valid and should be retained in `add_to_marketplace.py` (line 111)
- Currently set to `false` by default which is appropriate
- Reference documentation updated with official plugin reference content

**Status:** No changes needed - field is valid and properly used

**Note:** For complete "strict" field documentation, consult official docs at https://code.claude.com/docs/en/plugins-reference

### Medium Priority

#### 8. Enhanced Reference Documentation
**Goal:** Ensure reference docs exactly match official specifications

**Problem:**
- `references/plugin_marketplace_guide.md` may be out of sync with official docs
- Missing some advanced configuration options
- Need examples for all plugin organization strategies
- Should include troubleshooting section

**Proposed Solution:**
- Update `references/plugin_marketplace_guide.md` with:
  - Complete field reference table (all required/optional fields)
  - All three plugin organization strategies with examples
  - Progressive disclosure design explanation
  - Bundled resources structure (scripts, references, assets)
  - Validation rules and requirements
  - Troubleshooting common issues
  - Migration guide for old marketplace formats
- Add references to official schema URL
- Include examples from actual totally-tools marketplace

**Files to Modify:**
- `references/plugin_marketplace_guide.md`

**Success Criteria:**
- Reference doc contains all official spec requirements
- Examples match current totally-tools marketplace structure
- Troubleshooting section covers common issues
- Document validates and renders correctly

#### 9. Add Category Validation
**Goal:** Validate plugin categories against standard list

**Problem:**
- `category` field is optional but should use standard values
- No validation of category names
- Typos or custom categories may reduce discoverability
- No guidance on which category to choose

**Proposed Solution:**
- Define standard categories:
  - `development`: Development tools, programming, code quality
  - `productivity`: Task management, workflow automation
  - `documentation`: Writing, documentation tools, content creation
  - `data`: Data analysis, databases, analytics
  - `automation`: Process automation, workflow tools
  - `utilities`: General-purpose utilities
- Add category validation to `add_to_marketplace.py`
- Allow custom categories with warning
- Add `--category` flag with autocomplete suggestions
- Document category guidelines in SKILL.md

**Files to Modify:**
- `scripts/add_to_marketplace.py` (add category validation)
- `SKILL.md` (document standard categories)

**Success Criteria:**
- Standard categories defined and documented
- Validation warns about non-standard categories
- Clear guidance on category selection
- Existing custom categories still work (backward compatible)

#### 10. Improve Error Messages and User Guidance
**Goal:** Make scripts more user-friendly with better error messages

**Problem:**
- Some error messages are technical and unclear
- Missing suggestions for how to fix issues
- No examples in error output
- Path resolution errors can be confusing

**Proposed Solution:**
- Enhance error messages to include:
  - Clear explanation of what went wrong
  - Suggested fix or next steps
  - Example of correct format/usage
  - Relevant documentation links
- Add "Did you mean...?" suggestions for common typos
- Show example commands in error output
- Improve path resolution error messages with actual vs expected paths

**Files to Modify:**
- All three scripts (error message improvements throughout)

**Success Criteria:**
- Users can understand and fix errors without reading docs
- Error messages include actionable next steps
- Examples shown in context
- Reduced user confusion and support requests

### Low Priority

#### 11. Add JSON Schema Validation
**Goal:** Validate marketplace.json against official JSON schema

**Problem:**
- Scripts validate individual fields but not full schema compliance
- No integration with official schema at `https://anthropic.com/claude-code/marketplace.schema.json`
- Manual validation required for full compliance
- Schema changes may break compatibility

**Proposed Solution:**
- Add optional JSON schema validation using `jsonschema` Python package
- Fetch schema from official URL or use local copy
- Validate marketplace.json structure against schema
- Add `--validate-schema` flag to commands
- Make schema validation optional (don't require jsonschema package)

**Files to Modify:**
- All scripts (add optional schema validation)
- Add schema validation helper function

**Success Criteria:**
- Optional schema validation available when jsonschema installed
- Validates against official schema URL
- Clear error messages for schema violations
- Graceful fallback if jsonschema not installed

#### 12. Add Marketplace Export/Import
**Goal:** Support exporting and importing marketplace configurations

**Problem:**
- No easy way to duplicate marketplace structures
- Cannot export/import plugin configurations
- Manual copying error-prone
- Difficult to share marketplace templates

**Proposed Solution:**
- Add `export` command to save marketplace or plugin to file
- Add `import` command to load from exported file
- Support exporting:
  - Entire marketplace
  - Single plugin
  - Plugin template (without skills)
- JSON format for exports
- Merge or replace options for imports

**Files to Modify:**
- `scripts/add_to_marketplace.py` (add export/import commands)

**Success Criteria:**
- Can export marketplace to JSON file
- Can import marketplace from JSON file
- Can export/import individual plugins
- Merge and replace modes both work

---

## Technical Debt

### Code Quality
- TODO: Track code quality issues

### Documentation
- TODO: Track documentation gaps

## Enhancement Requests

*Track feature requests and suggestions from users here*

---

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.4.0 - Core Marketplace Operations Automation (2026-01-22)

**Major Features:**

1. **Source Path Architecture Fix (Issue [#4](https://github.com/totallyGreg/claude-mp/issues/4))**
   - Fixed `create_plugin()` in add_to_marketplace.py to automatically use correct source paths
   - Changed all 9 plugins from incorrect pattern (`source: "./", skills: ["./skills/NAME"]`)
     to correct pattern (`source: "./skills/NAME", skills: ["./"]`)
   - Updated validation, sync, and detection scripts to resolve paths relative to source
   - Eliminates nested skill confusion from full repository installation
   - New plugins automatically use correct format

2. **Deprecation Automation**
   - Created `scripts/deprecate_skill.py` (371 lines)
   - Removes plugin from marketplace.json with confirmation prompts
   - Scans all SKILL.md files for references to deprecated skill
   - Reports which skills need manual updates (with line numbers)
   - Creates optional migration guide in `docs/lessons/`
   - Generates detailed cleanup checklist
   - Dry-run mode for safe preview
   - Tested on skill-planner: found 2 skill references successfully

3. **Bundling Analysis Engine**
   - Created `scripts/analyze_bundling.py` (484 lines)
   - Calculates affinity scores (0-100) for all skill pairs
   - Scoring: same category (+30), cross-references (+40), bidirectional (+20), similar descriptions (+10)
   - Interactive mode for guided bundle creation
   - JSON output for programmatic use
   - Correctly recommends skillsmith + marketplace-manager bundle (80/100 score)
   - Provides bundle name and description suggestions

4. **Utils Template Generation**
   - Created `scripts/generate_utils_template.py` (165 lines)
   - Created `scripts/templates/utils.py.template` (137 lines)
   - Generates consistent utils.py for new skills
   - Replaces `{SKILL_NAME}` placeholder
   - Ensures code duplication consistency while maintaining self-contained plugins
   - Includes: `find_repo_root()`, `get_repo_root()`, `print_verbose_info()`, `validate_repo_structure()`

5. **Comprehensive Documentation**
   - Added 162-line "Marketplace Operations" section to SKILL.md
   - Documents all three automation tools with usage examples
   - Real command examples and output
   - Best practices for deprecation, bundling, and template generation
   - Marketplace-specific context (self-contained plugin rationale)

**Quality Metrics:**
- Overall quality score: 75/100 (from skillsmith evaluation)
- Progressive disclosure: 100/100
- AgentSkills spec compliance: 90/100 (PASS)
- Total automation code: 1,157 lines

**Files Modified:**
- `.claude-plugin/marketplace.json` - Fixed source paths for all 9 plugins
- `scripts/add_to_marketplace.py` - Fixed create_plugin(), validation logic
- `scripts/sync_marketplace_versions.py` - Source path resolution
- `scripts/detect_version_changes.py` - Source path resolution
- `SKILL.md` - Added Marketplace Operations section (162 lines)
- `IMPROVEMENT_PLAN.md` - Tracked completion

**Files Created:**
- `scripts/deprecate_skill.py` - Deprecation automation
- `scripts/analyze_bundling.py` - Bundling recommendations
- `scripts/generate_utils_template.py` - Utils generation
- `scripts/templates/utils.py.template` - Utils template
- `docs/plans/2026-01-22-marketplace-manager-evolution.md` - Phase 1 plan
- `docs/plans/2026-01-22-ai-risk-mapper-automation-overhaul.md` - ai-risk-mapper plan

**Impact:**
- ✅ All plugins now install only their individual skill directories
- ✅ Deprecation workflow ready for skill-planner removal (Phase 2)
- ✅ Bundling logic recommends skill-development-toolkit
- ✅ Template generation ensures consistent utility code
- ✅ Comprehensive documentation for all new operations

**Version Bump:** 1.3.0 → 1.4.0 (MINOR - new features, backward compatible)

**Related Issues:** [#4](https://github.com/totallyGreg/claude-mp/issues/4) (Complete), [#5](https://github.com/totallyGreg/claude-mp/issues/5) (Unblocked)

### v1.3.0 - Critical Bug Fixes (2026-01-07)

**Critical Bug Fixes:**

1. **Fixed Missing utils.py Dependency (Issue #1)**
   - Added `scripts/utils.py` module with shared utility functions
   - Implemented `get_repo_root()` for repository root detection
   - Implemented `print_verbose_info()` for verbose output
   - Implemented `validate_repo_structure()` for repository validation
   - All scripts now execute without ImportError
   - Repository root detection works correctly across different working directories

2. **Fixed Incorrect marketplace.json Schema (Issue #2)**
   - Updated `load_marketplace()` to use correct top-level structure
   - Updated `init_marketplace()` to generate compliant marketplace.json
   - Changed from nested `metadata.version`/`metadata.description` to top-level `version`/`description`
   - Now complies with official schema at https://anthropic.com/claude-code/marketplace.schema.json
   - Generated marketplace.json files validate against official schema

3. **Fixed metadata.version Parsing (Issue #4)**
   - Rewrote `extract_frontmatter_version()` in sync_marketplace_versions.py
   - Now correctly parses nested `metadata.version` field (Agent Skills spec preferred format)
   - Falls back to deprecated top-level `version` field for backward compatibility
   - Warns users when deprecated `version` field is used
   - Skills using either version format now sync correctly

**Files Modified:**
- `scripts/sync_marketplace_versions.py` - Fixed metadata.version parsing (lines 23-70)
- `scripts/add_to_marketplace.py` - Fixed marketplace.json schema (lines 28-56)

**Files Created:**
- `scripts/utils.py` - Shared utility functions (3,853 bytes)

**Impact:**
- All critical blocking issues resolved
- Scripts now fully functional and spec-compliant
- Marketplace.json files validate against official schema
- Supports both old and new version field formats

### v1.1.0 - Plugin Versioning & Validation (2025-12-22)

**Major Features:**
1. **Plugin Versioning Strategy (Improvement #5)**
   - Added `--mode` flag to sync script (auto/manual)
   - Auto mode: auto-updates single-skill plugins
   - Manual mode: warns about mismatches, requires manual plugin version updates
   - Multi-skill plugin support with version mismatch detection
   - Prevents silent versioning issues in multi-component plugins

2. **Comprehensive Validation Command (Improvement #6)**
   - New `validate` subcommand in add_to_marketplace.py
   - Validates marketplace.json schema compliance
   - Checks semantic versioning format (X.Y.Z)
   - Validates skill directory and SKILL.md existence
   - Detects duplicate plugin names
   - Checks frontmatter metadata completeness
   - Outputs text or JSON format for CI/CD integration

3. **Pre-Commit Hook Template (Improvement #7)**
   - Created `scripts/pre-commit.template`
   - Auto-detects version mismatches before commits
   - Auto-syncs marketplace.json in auto mode
   - Stages updated marketplace.json automatically
   - Provides clear colored output
   - Allows bypass with `--no-verify`

**Documentation Updates:**
- Added comprehensive versioning strategies section to SKILL.md
- Documented auto vs manual mode usage
- Added plugin versioning decision guide
- Updated references/plugin_marketplace_guide.md with versioning guidance
- Added single-skill vs multi-component plugin best practices

**Files Modified:**
- `scripts/sync_marketplace_versions.py` - Added mode parameter, multi-skill support
- `scripts/add_to_marketplace.py` - Added validate command, validation functions
- `SKILL.md` - Added versioning strategies and workflows
- `references/plugin_marketplace_guide.md` - Added versioning guidance

**Files Created:**
- `scripts/pre-commit.template` - Git pre-commit hook

### v1.0.0 - Initial Release (2025-12-21)

**Initial Features:**
- Marketplace.json management scripts
- Version syncing between SKILL.md and marketplace.json
- Add/create plugin commands
- List marketplace contents
- Update marketplace metadata

**Files Created:**
- `SKILL.md` - Main skill definition
- `scripts/add_to_marketplace.py` - Marketplace management
- `scripts/sync_marketplace_versions.py` - Version synchronization
- `scripts/detect_version_changes.py` - Version mismatch detection
- `references/plugin_marketplace_guide.md` - Official plugin reference

## Contributing

To suggest improvements to this skill:

1. Add enhancement requests to the "Enhancement Requests" section
2. Discuss technical approaches in "Planned Improvements"
3. Track implementation progress
4. When complete, follow the Planned → Completed workflow:
   - Cut section from Planned Improvements
   - Update header: "### v{version} - {name} ({date})"
   - Paste at top of Recent Improvements (Completed)
   - Update version history table with actual date
   - Add implementation details

## Notes

- This improvement plan should be excluded from skill packaging (see .skillignore)
- Update "Last Updated" timestamp in Planned Improvements when making changes
- Update version history when releasing new versions
- Link to relevant issues/PRs in your repository if applicable
