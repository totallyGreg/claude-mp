---
title: "Multi-Skill Plugin Version Sync Silently Ignores Drift"
date: 2026-02-16
category: logic-errors
tags:
  - marketplace-manager
  - version-management
  - multi-skill-plugins
  - semver
  - pre-commit-hook
severity: high
component: plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py
symptom: "marketplace.json shows stale version for multi-skill plugins when any one skill version matches the plugin version"
root_cause: "Script used 'any match' logic instead of 'highest version' logic for multi-skill plugins"
status: resolved
issue: https://github.com/totallyGreg/claude-mp/issues/50
commit: 7f877df
---

# Multi-Skill Plugin Version Sync Silently Ignores Drift

## Problem

The `sync_marketplace_versions.py` script had incorrect logic for multi-skill plugins. When a plugin contained multiple skills with different versions (e.g., pkm-plugin with vault-architect at v1.1.0 and vault-curator at v1.4.0), the script checked if *any* skill version matched the plugin version. If vault-architect at 1.1.0 matched plugin.json at 1.1.0, the script printed "version matches at least one skill" and skipped the plugin — even though vault-curator was at 1.4.0. This caused marketplace.json to display stale versions for weeks.

**How it was caught:** During Phase 3 development (#46), the pre-commit hook warned about a version mismatch, but the plugin.json was at 1.1.0 while marketplace.json was at 1.3.0 and vault-curator was at 1.4.0. Debugging the confusion revealed the sync script's flawed logic.

## Root Cause

Lines 146-177 of `sync_marketplace_versions.py` (before fix):

```python
# BUG: Check if ANY skill matches the plugin version
if not any(v == current_plugin_version for _, v in skill_versions):
    print(f"Multi-skill plugin '{plugin_name}' version mismatch detected")
else:
    # SILENT PASS: One skill matches, skip entirely
    print(f"Plugin '{plugin_name}' version matches at least one skill")
continue  # Always skip multi-skill plugins (never auto-update)
```

For pkm-plugin with vault-architect=1.1.0 and vault-curator=1.4.0, plugin version=1.1.0:
1. `any(v == "1.1.0" for v in ["1.1.0", "1.4.0"])` returns `True`
2. `not True` = `False`, so the warning block is skipped
3. Prints "version matches at least one skill"
4. `continue` skips the plugin — vault-curator's 1.4.0 is silently ignored

## Solution

### 1. Added semver parser

```python
def _parse_semver(version_str):
    """Parse a semver string into a comparable tuple."""
    parts = version_str.split('.')
    result = []
    for part in parts[:3]:
        try:
            result.append(int(part))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)
```

### 2. Changed multi-skill logic to use highest version

```python
# FIXED: Find highest version across all skills
highest_version = max(
    (v for _, v in skill_versions),
    key=_parse_semver,
)

if highest_version != current_plugin_version:
    if mode == 'manual':
        # Warn with specific drift details
        print(f"Multi-skill plugin '{plugin_name}' version mismatch")
    else:
        # Auto mode: update to highest skill version
        plugin['version'] = highest_version
```

### 3. Added process guardrails

- **`.claude/CLAUDE.md`**: Added reminder to run skillsmith evaluation before committing skill changes
- **`WORKFLOW.md`**: Updated multi-skill documentation to reflect auto-update behavior

## Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Version comparison | Any skill matches plugin | Highest skill compared to plugin |
| Multi-skill auto-update | Never (always `continue`) | Updates to highest version |
| Example: vault-architect=1.1.0, vault-curator=1.4.0 | "matches at least one" (stays 1.1.0) | Updates plugin to 1.4.0 |
| Manual mode | Only warns when NO skill matches | Warns with all skill versions listed |

## Prevention

### Three-layer defense

1. **Code fix**: `max(versions, key=_parse_semver)` always selects the highest version. No silent pass possible.

2. **Pre-commit hook**: Automatically detects marketplace.json drift and runs sync before every commit. Even if the script had a bug, the detection layer (`detect_version_changes.py`) independently compares skill versions against marketplace.json.

3. **Process reminder**: `.claude/CLAUDE.md` instructs any workflow to run skillsmith evaluation before committing, ensuring version changes are intentional and documented.

### Verification

```bash
# Dry-run to verify sync behavior
uv run plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py --dry-run

# Expected for multi-skill plugins: shows highest version, not "matches at least one"
```

### Edge cases to watch

- **Pre-release versions** (e.g., "1.0.0-rc1"): `_parse_semver` treats non-numeric parts as 0. Two pre-release versions may compare as equal. Stick to X.Y.Z format.
- **Missing SKILL.md**: If a skill listed in marketplace.json lacks SKILL.md, it's silently skipped. The highest version is computed from available skills only.

## Related

- [Issue #50](https://github.com/totallyGreg/claude-mp/issues/50): Original issue that identified the problem but left multi-skill fix as "non-blocking"
- [Issue #48](https://github.com/totallyGreg/claude-mp/issues/48): vault-curator Phase 1 PR (affected by missing marketplace sync)
- [Issue #49](https://github.com/totallyGreg/claude-mp/issues/49): vault-curator Phase 2 PR (marketplace still not synced)
- `WORKFLOW.md` lines 294-313: Marketplace Sync section
- `WORKFLOW.md` lines 320-339: Skill Release Checklist
