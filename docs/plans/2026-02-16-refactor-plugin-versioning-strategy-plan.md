---
title: "refactor: Plugin Versioning Strategy"
type: refactor
date: 2026-02-16
brainstorm: docs/brainstorms/2026-02-16-plugin-versioning-strategy-brainstorm.md
supersedes: "#39, #36"
---

# refactor: Plugin Versioning Strategy

## Overview

Refactor marketplace-manager's version sync and detect scripts to treat plugin versions as independent package release versions. Currently the sync script derives plugin versions from SKILL.md (highest skill version for multi-skill plugins), but plugin.json is never read. This causes false positives in detection, stale marketplace versions, and confusion about which version is authoritative.

## Problem Statement / Motivation

Three concrete problems:

1. **detect_version_changes.py** compares individual skill versions against the plugin version in marketplace.json. For multi-skill plugins where skills have different versions, this always reports a mismatch (vault-architect 1.1.0 != pkm-plugin 1.5.0).

2. **sync_marketplace_versions.py** ignores plugin.json entirely. It reads SKILL.md versions and derives the plugin version. This means plugin.json is a dead field — developers bump it, but the sync pipeline overwrites marketplace.json with a SKILL.md-derived value.

3. **The pre-commit hook** stages marketplace.json but not README.md after sync, leaving a dirty working tree.

## Proposed Solution

### Version Source by Plugin Type

| Plugin Type | Detection | Version Source → marketplace.json |
|-------------|-----------|----------------------------------|
| Single-skill (`skills: ["./"]`) | SKILL.md bump check | SKILL.md → marketplace.json |
| Plugin with plugin.json | plugin.json bump check | plugin.json → marketplace.json |

**Rule:** If `source_dir / '.claude-plugin' / 'plugin.json'` exists, use it. Otherwise fall back to SKILL.md.

### Update Cascade

```
Component changes → developer bumps version source
  → sync: version source → marketplace.json
    → sync_readme: marketplace.json → README.md
      → hook stages: marketplace.json + README.md
```

## Technical Approach

### Task 1: Refactor sync_marketplace_versions.py

**Current behavior:** Reads SKILL.md for all plugins. Multi-skill plugins use `max(skill_versions)`.

**New behavior:**

```python
def get_plugin_version(source_dir, skills, plugin_name):
    """Determine version source and read version."""
    plugin_json = source_dir / '.claude-plugin' / 'plugin.json'

    if plugin_json.exists():
        # Plugin with plugin.json — it's the version source
        with open(plugin_json) as f:
            data = json.load(f)
        return data.get('version'), 'plugin.json', False

    # Single-skill with skills: ["./"] — SKILL.md is the version source
    if len(skills) == 1 and skills[0] == './':
        skill_md = source_dir / 'SKILL.md'
        if skill_md.exists():
            version, is_deprecated = extract_frontmatter_version(skill_md)
            return version, 'SKILL.md', is_deprecated

    return None, None, None
```

**Changes:**
- Remove `_parse_semver()` and multi-skill highest-version logic
- Remove `is_multi_skill` branching — replace with plugin.json existence check
- Add `get_plugin_version()` that checks plugin.json first, falls back to SKILL.md
- Keep informational reporting of individual skill versions for multi-skill plugins
- Keep `sync_readme` call and README.md sync

**Files:** `plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py`

### Task 2: Refactor detect_version_changes.py

**Default mode (no flags):** Currently compares each skill's SKILL.md version against the plugin version in marketplace.json. This produces false positives for multi-skill plugins.

**New default mode:** Compare the version source (plugin.json or SKILL.md) against marketplace.json. One check per plugin, not per skill.

```python
def detect_version_changes(repo_root, marketplace_data):
    for plugin in marketplace_data.get('plugins', []):
        source_dir = resolve_source_dir(repo_root, plugin)
        plugin_json = source_dir / '.claude-plugin' / 'plugin.json'

        if plugin_json.exists():
            # Compare plugin.json version vs marketplace version
            actual_version = read_plugin_json_version(plugin_json)
        else:
            # Single-skill: compare SKILL.md version vs marketplace version
            actual_version = read_skill_version(source_dir / 'SKILL.md')

        if actual_version != plugin.get('version'):
            mismatches.append(...)
```

**`--check-staged` mode:** Already correctly maps files to components. Enhancement: when any file under a multi-skill plugin is staged, also check if plugin.json was bumped (warn, not block).

**Cleanup:**
- Import shared functions from `utils.py` instead of duplicating
- Use `argparse` instead of manual `sys.argv` parsing
- Remove duplicate `find_repository_root()`, `read_skill_version()`, `extract_version_from_skill_md()`

**Files:** `plugins/marketplace-manager/skills/marketplace-manager/scripts/detect_version_changes.py`

### Task 3: Update pre-commit hook template

**Change:** After sync, stage both marketplace.json AND README.md.

```bash
# Current (line 88):
git add "$MARKETPLACE_JSON"

# New:
git add "$MARKETPLACE_JSON"
README_PATH="$REPO_ROOT/README.md"
if [ -f "$README_PATH" ] && git diff --name-only "$README_PATH" | grep -q "README.md"; then
    git add "$README_PATH"
fi
```

**Files:**
- `plugins/marketplace-manager/skills/marketplace-manager/scripts/pre-commit.template`
- `.git/hooks/pre-commit` (reinstall after template update)

### Task 4: Update WORKFLOW.md

- Update "Marketplace Sync" section to reflect plugin.json as version source
- Update multi-skill plugin documentation
- Clarify the update cascade: component → plugin.json → marketplace.json → README.md

**Files:** `WORKFLOW.md`

### Task 5: Update marketplace-manager SKILL.md

- Document the version source logic (plugin.json if exists, else SKILL.md)
- Update version to 2.3.0

**Files:** `plugins/marketplace-manager/skills/marketplace-manager/SKILL.md`

## Acceptance Criteria

### Functional Requirements

- [ ] `sync` reads plugin.json when it exists, falls back to SKILL.md for `skills: ["./"]`
- [ ] `sync` writes correct version to marketplace.json for all 9 plugins
- [ ] `detect` default mode: compares version source (plugin.json or SKILL.md) against marketplace.json — no false positives
- [ ] `detect --check-staged`: warns when plugin files changed but plugin.json not bumped
- [ ] Pre-commit hook stages both marketplace.json and README.md
- [ ] Single-skill plugins (helm-chart-developer, swift-dev) still auto-sync from SKILL.md
- [ ] Multi-skill plugins (pkm-plugin, terminal-guru) sync from plugin.json

### Quality Gates

- [ ] `uv run sync_marketplace_versions.py --dry-run` shows no mismatches after refactor
- [ ] `python3 detect_version_changes.py` exits 0 (no false positives)
- [ ] All 9 plugins pass version consistency check
- [ ] Skillsmith eval on marketplace-manager skill

## Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing sync behavior | Medium | High | Dry-run verification against all 9 plugins before/after |
| Hook template diverges from installed hook | Low | Medium | Reinstall hook after template update |
| Single-skill plugins without plugin.json break | Low | High | Explicit fallback to SKILL.md for `skills: ["./"]` |

## Edge Cases (from SpecFlow Analysis)

| Edge Case | Handling |
|-----------|----------|
| plugin.json doesn't exist (single-skill) | Fall back to SKILL.md |
| Version downgrade (2.0.0 → 1.9.0) | Warn but don't block (future enhancement) |
| New plugin without marketplace entry | Not in scope — existing `add_to_marketplace.py` handles this |
| `--no-verify` bypass | Not in scope — CI check is a future enhancement |
| Scripts modified inside skill | Treated as component change — triggers bump warning (current behavior, keep) |

## References & Research

### Internal References
- Brainstorm: `docs/brainstorms/2026-02-16-plugin-versioning-strategy-brainstorm.md`
- Solution doc: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Sync script: `plugins/marketplace-manager/skills/marketplace-manager/scripts/sync_marketplace_versions.py`
- Detect script: `plugins/marketplace-manager/skills/marketplace-manager/scripts/detect_version_changes.py`
- Hook template: `plugins/marketplace-manager/skills/marketplace-manager/scripts/pre-commit.template`
- WORKFLOW.md: lines 294-313 (Marketplace Sync), lines 320-339 (Release Checklist)

### Related Issues
- [#39](https://github.com/totallyGreg/claude-mp/issues/39): Pre-commit hook should suggest plugin.json version bump (superseded)
- [#36](https://github.com/totallyGreg/claude-mp/issues/36): Version consistency validation hook (folded in)
- [#50](https://github.com/totallyGreg/claude-mp/issues/50): Original marketplace sync workflow issue (closed)
- [#25](https://github.com/totallyGreg/claude-mp/issues/25): Clarify relationship with plugin-dev (separate, low priority)

### External References
- Plugin-dev manifest reference: `~/.claude/plugins/cache/claude-plugins-official/plugin-dev/*/skills/plugin-structure/references/manifest-reference.md`
- Plugin-dev versioning guidance: semver MAJOR.MINOR.PATCH, default 0.1.0
