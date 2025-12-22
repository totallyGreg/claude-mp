# Marketplace Manager - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the marketplace-manager skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.1.0 | 2025-12-22 | Added plugin versioning strategies, validation command, pre-commit hook |
| 1.0.0 | 2025-12-21 | Initial release |

## 🔮 Planned Improvements
> Last Updated: 2025-12-22

**Note:** Planned improvements are tracked by NUMBER, not version. Version numbers are only assigned when releasing.

### Critical Priority (Blocking Issues)

#### 1. Missing utils.py Dependency
**Goal:** Fix broken scripts by adding missing utils.py module

**Problem:**
- All three scripts (`add_to_marketplace.py`, `sync_marketplace_versions.py`, `detect_version_changes.py`) import from `utils` module
- The `utils.py` file does not exist in `scripts/` directory
- Scripts will fail immediately on execution with ImportError
- This is a critical blocker preventing any script functionality

**Proposed Solution:**
- Copy `utils.py` from `skills/skillsmith/scripts/utils.py` to `skills/marketplace-manager/scripts/utils.py`
- Verify all imported functions are present: `get_repo_root`, `print_verbose_info`, `validate_repo_structure`
- Test all three scripts to ensure they run without import errors

**Files to Modify:**
- Create: `scripts/utils.py` (copy from skillsmith)

**Success Criteria:**
- All three scripts execute without ImportError
- Repository root detection works correctly
- Verbose mode displays path information
- Validation checks work as expected

#### 2. Fix add_to_marketplace.py Incorrect Schema
**Goal:** Correct marketplace.json structure to match official schema

**Problem:**
- Line 31 in `add_to_marketplace.py` creates incorrect structure:
  ```python
  "metadata": {"description": "", "version": "1.0.0"}
  ```
- Official schema requires top-level fields:
  ```json
  {
    "version": "1.0.0",
    "description": "..."
  }
  ```
- This violates the official marketplace.json schema at `https://anthropic.com/claude-code/marketplace.schema.json`
- Marketplaces created with this script will be non-compliant

**Proposed Solution:**
- Update `load_marketplace()` function (lines 21-33):
  ```python
  return {
      "name": "",
      "version": "1.0.0",
      "description": "",
      "owner": {"name": "", "email": ""},
      "plugins": [],
  }
  ```
- Update `init_marketplace()` function (lines 46-56):
  ```python
  marketplace_data = {
      "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
      "name": name,
      "version": "1.0.0",
      "description": description,
      "owner": {"name": owner_name, "email": owner_email},
      "plugins": [],
  }
  ```
- Update all references from `metadata.description` and `metadata.version` to top-level fields
- Lines to modify: 31, 48, 121, 122, 203-229

**Files to Modify:**
- `scripts/add_to_marketplace.py` (lines 31, 48, 121-122, 203-229)

**Success Criteria:**
- `init` command creates marketplace.json with correct top-level structure
- All metadata operations work with top-level version and description
- Generated marketplace.json validates against official schema
- Existing valid marketplace.json files are not corrupted

#### 3. Document "strict" Field in References (RESOLVED - NOT AN ISSUE)
**Goal:** Document the "strict" field which is part of official plugin specification

**Resolution:**
- The "strict" field is documented in official Claude Code plugin reference at https://code.claude.com/docs/en/plugins-reference
- Field is valid and should be retained in `add_to_marketplace.py` (line 111)
- Currently set to `false` by default which is appropriate
- Reference documentation updated with official plugin reference content

**Status:** No changes needed - field is valid and properly used

**Note:** For complete "strict" field documentation, consult official docs at https://code.claude.com/docs/en/plugins-reference

#### 4. Fix sync_marketplace_versions.py metadata.version Parsing
**Goal:** Support both metadata.version and deprecated version fields correctly

**Problem:**
- `extract_frontmatter_version()` function (lines 23-52) only looks for top-level `version:` field
- Line 44 regex: `r'^version:\s*([^\n]+)'` cannot parse nested `metadata.version`
- Skills using correct `metadata.version` format (as per Agent Skills spec) will not be detected
- Script claims to support metadata.version but doesn't actually parse it

**Proposed Solution:**
- Rewrite `extract_frontmatter_version()` to use same parsing logic as `detect_version_changes.py` (lines 77-102)
- Parse both nested `metadata.version` (preferred) and top-level `version` (deprecated)
- Return tuple: `(version_string, is_deprecated)` for better reporting
- Add warning when deprecated `version` field is used

**Files to Modify:**
- `scripts/sync_marketplace_versions.py` (lines 23-52, function rewrite)
- Update caller (line 114) to handle tuple return value

**Success Criteria:**
- Correctly extracts version from `metadata.version` field
- Falls back to deprecated `version` field if metadata.version not found
- Warns users when deprecated version field is used
- All skills in marketplace sync correctly regardless of version field format


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

**Bug Fixes:**
- Critical issues #1-4 resolved in v1.0.1 (utils.py, schema fixes, metadata.version parsing)

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
