# Improvement Plan: marketplace-manager - Hook Robustness

**Status:** implemented
**Created:** 2025-12-31T00:00:00Z
**Approved:** 2025-12-31T00:05:00Z
**Approved By:** User
**Implemented:** 2025-12-31T00:30:00Z
**Branch:** plan/marketplace-manager-hook-robustness-20251231
**Version:** v1

---

## Goal

Fix the outdated pre-commit hook installation and make the hook infrastructure robust, idempotent, and self-healing to prevent future breakage from skill renames or path changes.

---

## Current State

### Understanding

**Purpose:** Manages marketplace.json version syncing with skill versions via automated scripts and git hooks
**Domain:** Development tooling - version management and git automation
**Complexity:** Moderate (multiple scripts, git integration, cross-platform support)

### Analysis

**Strengths:**
- Comprehensive template with correct paths in `scripts/pre-commit.template`
- Auto-sync functionality works well
- Clear documentation in SKILL.md
- Good error handling and colored output

**Weaknesses:**
- Installed hook at `.git/hooks/pre-commit` has outdated path (`skill-creator` instead of `marketplace-manager`)
- No mechanism to detect or update outdated hooks
- Hardcoded paths make hooks brittle to skill renames
- Manual installation process prone to errors
- No validation to check hook health

**Opportunities:**
- Add installation script for idempotent hook setup
- Implement hook versioning for upgrade detection
- Use dynamic path discovery instead of hardcoded paths
- Add validation command to check hook status
- Self-healing capability when paths change

### Current Issues

**Problem 1: Outdated Installed Hook**
- `.git/hooks/pre-commit` references `skills/skill-creator/scripts/sync_marketplace_versions.py`
- Should reference `skills/marketplace-manager/scripts/sync_marketplace_versions.py`
- Causes warning: "sync_marketplace_versions.py not found, skipping version sync"

**Problem 2: No Update Mechanism**
- When skill is renamed or hook template changes, installed hooks become stale
- Users must manually discover and reinstall
- No detection or notification of outdated hooks

**Problem 3: Brittle Path Hardcoding**
- Hook relies on exact skill name in path
- Breaks on skill renames
- Not resilient to repository structure changes

---

## Proposed Changes

### Change 1: Fix Installed Hook Immediately

**Type:** ENHANCE
**What:** Reinstall pre-commit hook from correct template
**Why:** Resolve immediate issue blocking marketplace sync
**Impact:** Hook will work correctly, no more warnings

**Implementation:**
- Copy `skills/marketplace-manager/scripts/pre-commit.template` to `.git/hooks/pre-commit`
- Set executable permissions
- Test with dummy commit

### Change 2: Create Installation Script

**Type:** ENHANCE
**What:** Add `scripts/install_hook.sh` for idempotent hook installation
**Why:** Make installation and updates easy, reliable, and repeatable
**Impact:** Users can run script anytime to ensure hook is current

**Implementation:**
- Create `scripts/install_hook.sh` with:
  - Check if hook already installed
  - Compare installed version with template
  - Update if outdated or install if missing
  - Set permissions automatically
  - Provide clear feedback
  - Support `--force` flag to override checks
  - Support `--dry-run` to preview changes

### Change 3: Add Hook Versioning

**Type:** ENHANCE
**What:** Embed version marker in hook template and check on execution
**Why:** Detect outdated hooks and warn users to update
**Impact:** Self-awareness when hook is stale

**Implementation:**
- Add version comment at top of `scripts/pre-commit.template`:
  ```bash
  # marketplace-manager pre-commit hook v1.3.0
  ```
- Hook checks its own version and compares with template
- If outdated, print warning with update instructions
- Continue execution (graceful degradation)

### Change 4: Robust Path Discovery

**Type:** ENHANCE
**What:** Replace hardcoded paths with dynamic discovery using `find` command
**Why:** Make hook resilient to skill renames and repository structure changes
**Impact:** Hook survives skill renames without breaking

**Implementation:**
- Replace hardcoded sync script path with dynamic discovery
- Use `find` command to locate sync_marketplace_versions.py
- Fallback search if specific path not found
- Add validation that script was found before executing

### Change 5: Add Validation Command

**Type:** ENHANCE
**What:** Add `scripts/validate_hook.py` to check hook installation status
**Why:** Allow users and CI to verify hook is installed and up-to-date
**Impact:** Better visibility into hook health

**Implementation:**
- Create Python script that checks:
  - Is hook installed?
  - Does hook match template (content comparison)?
  - Is hook executable?
  - What version is installed?
  - Are required scripts present?
- Output format:
  - Human-readable summary for CLI
  - JSON format for CI/CD (`--json` flag)
- Exit codes:
  - 0: All checks pass
  - 1: Hook outdated or missing
  - 2: Critical error

### Change 6: Update Documentation

**Type:** ENHANCE
**What:** Update SKILL.md with new installation method
**Why:** Guide users to use the new, robust installation process
**Impact:** Better user experience, fewer manual errors

**Implementation:**
- Update "Git Integration" section in SKILL.md
- Replace manual `cp` commands with new script-based approach
- Document `--force` and `--dry-run` options
- Add troubleshooting section for hook issues

---

## Expected Outcome

### Success Criteria

- [x] Installed hook has correct paths (no more warnings)
- [x] `install_hook.sh` can be run multiple times safely (idempotent)
- [x] Hook auto-detects if it's outdated and warns user
- [x] Hook works even if skill is renamed
- [x] `validate_hook.py` accurately reports hook status
- [x] Documentation updated with new workflow
- [x] All changes tested with actual git commits

### Expected Benefits

- **Immediate:** Fix current warning and enable proper marketplace syncing
- **Robustness:** Hook survives skill renames and path changes
- **Maintainability:** Easy to update hooks across repositories
- **Visibility:** Clear status reporting for debugging
- **User Experience:** Simple, reliable installation process
- **Future-proof:** Self-healing capability reduces future breakage

---

## Actual Outcome

### Implementation Summary

All 6 proposed changes successfully implemented:

**✅ Change 1: Fixed Installed Hook**
- Ran `install_hook.sh` to update hook with v1.3.0
- Hook now references correct marketplace-manager paths
- No more "sync_marketplace_versions.py not found" warnings

**✅ Change 2: Created Installation Script**
- New `scripts/install_hook.sh` with 200+ lines
- Supports `--force`, `--dry-run` flags
- Idempotent - safe to run multiple times
- Auto-detects if update needed
- Clear colored output and feedback

**✅ Change 3: Added Hook Versioning**
- Hook template now includes version marker (v1.3.0)
- Hook checks its own version on execution
- Warns user if outdated with update instructions
- Graceful degradation continues execution

**✅ Change 4: Robust Path Discovery**
- Replaced hardcoded paths with dynamic `find` command
- Tries specific path first for performance
- Falls back to repository-wide search
- Validates scripts found before executing
- Resilient to skill renames

**✅ Change 5: Added Validation Command**
- New `scripts/validate_hook.py` (200+ lines)
- Checks: installed, executable, up-to-date, matches template
- Reports versions and identifies issues
- Supports both human-readable and JSON output
- Exit codes: 0 (pass), 1 (warning), 2 (error)

**✅ Change 6: Updated Documentation**
- Updated "Git Integration" section in SKILL.md
- Replaced manual `cp` with script-based installation
- Added hook features list with checkmarks
- Created comprehensive "Troubleshooting" section
- Documented all new commands and options

### Success Criteria Results

- [x] Installed hook has correct paths ✅ (verified with validate_hook.py)
- [x] `install_hook.sh` is idempotent ✅ (tested multiple runs)
- [x] Hook auto-detects outdated versions ✅ (version checking implemented)
- [x] Hook survives skill renames ✅ (dynamic path discovery)
- [x] `validate_hook.py` reports accurately ✅ (all checks pass)
- [x] Documentation updated ✅ (SKILL.md enhanced)
- [x] Tested with git commits ✅ (hook detected version mismatches)

### Actual Benefits Achieved

- ✅ **Immediate fix:** No more "skill-creator not found" warnings
- ✅ **Robustness:** Dynamic path discovery survives renames
- ✅ **Idempotency:** Safe to run install script multiple times
- ✅ **Visibility:** validate_hook.py provides clear status
- ✅ **User Experience:** Simple one-command installation
- ✅ **Future-proof:** Version checking prevents stale hooks
- ✅ **Self-healing:** Auto-detects and suggests updates

### Files Created/Modified

**Created:**
- `skills/marketplace-manager/scripts/install_hook.sh` (200+ lines)
- `skills/marketplace-manager/scripts/validate_hook.py` (200+ lines)

**Modified:**
- `skills/marketplace-manager/scripts/pre-commit.template` (added versioning, path discovery)
- `skills/marketplace-manager/SKILL.md` (updated installation, added troubleshooting)
- `.git/hooks/pre-commit` (updated to v1.3.0)

**Total:** 2 new files, 3 modified files, ~450 lines of new code

### Testing Results

**Installation testing:**
```bash
$ bash skills/marketplace-manager/scripts/install_hook.sh
✅ Hook installed successfully (v1.3.0)
```

**Validation testing:**
```bash
$ python3 skills/marketplace-manager/scripts/validate_hook.py
✅ All checks passed
  Installed: 1.3.0
  Template:  1.3.0
```

**Hook execution testing:**
- Hook correctly detects version mismatches
- Dynamic path discovery works (finds scripts even with skill renamed)
- Auto-sync functionality operational
- Graceful degradation on errors

### Notes

Hook successfully detects version mismatches during commits. During testing, discovered unrelated issue with helm-chart-developer missing version field - this validates that the hook is working correctly and catching real issues.

All expected outcomes achieved. Implementation complete and ready for merge.

---

## Revision History

### v1 (2025-12-31T00:00:00Z)
- Initial plan created from research findings
- Focus on fixing immediate issue and adding robustness
- Six proposed changes covering installation, versioning, path discovery, and validation

---

## Research Findings (Reference)

### Domain Classification

**Domain:** Development tooling - git automation and version management
**Complexity:** Moderate (scripting, git integration, cross-platform considerations)

**Special Considerations:**
- Must work reliably in git workflow (cannot break commits)
- Should degrade gracefully on errors
- Cross-platform compatibility (macOS, Linux)
- Idempotent operations essential for automation

### Best Practices for Domain

**Critical:**
- **Idempotency**: Installation scripts must be safely repeatable
- **Graceful degradation**: Hooks should warn but not block commits on non-critical errors
- **Path resilience**: Don't hardcode paths that can change
- **Version awareness**: Detect and handle outdated installations

**Important:**
- Clear error messages with actionable instructions
- Easy verification of correct installation
- Minimal dependencies (use shell/Python stdlib)
- Fast execution (pre-commit hooks delay workflow)

### Current Issues Discovered

1. **Outdated hook installed**: References `skill-creator` instead of `marketplace-manager`
2. **No update mechanism**: Stale hooks persist indefinitely
3. **Brittle paths**: Hardcoded skill name in paths
4. **No validation**: Can't verify hook health programmatically

---

*This plan was generated by skill-planner from comprehensive research findings.*
*All changes designed to make marketplace-manager hook infrastructure robust and self-healing.*
