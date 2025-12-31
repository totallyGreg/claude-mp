# Improvement Plan: marketplace-manager - Hook Robustness

**Status:** draft
**Created:** 2025-12-31T00:00:00Z
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

- [ ] Installed hook has correct paths (no more warnings)
- [ ] `install_hook.sh` can be run multiple times safely (idempotent)
- [ ] Hook auto-detects if it's outdated and warns user
- [ ] Hook works even if skill is renamed
- [ ] `validate_hook.py` accurately reports hook status
- [ ] Documentation updated with new workflow
- [ ] All changes tested with actual git commits

### Expected Benefits

- **Immediate:** Fix current warning and enable proper marketplace syncing
- **Robustness:** Hook survives skill renames and path changes
- **Maintainability:** Easy to update hooks across repositories
- **Visibility:** Clear status reporting for debugging
- **User Experience:** Simple, reliable installation process
- **Future-proof:** Self-healing capability reduces future breakage

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
