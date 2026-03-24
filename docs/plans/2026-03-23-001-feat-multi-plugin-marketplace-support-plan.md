---
title: "feat: multi-plugin marketplace support — structure detection, validation, and hooks"
type: feat
status: active
date: 2026-03-23
---

# feat: multi-plugin marketplace support — structure detection, validation, and hooks

## Overview

When a marketplace repo hosts multiple independent plugins that share the same `source: "./"`, `detect_version_changes.py` resolves all plugins to the same `plugin.json`, causing incorrect version enforcement. This plan adds structure detection, automated migration, documentation, and CI-mode support to marketplace-manager.

## Problem Statement / Motivation

**Real-world example:** The `airs-tme` marketplace has three plugins (airs-tme, pai-ops, prisma-airs) all using `source: "./"`. Changing `pai-ops` triggers a version check failure because `plugin.json` (which belongs to airs-tme) wasn't bumped — but it shouldn't need to be.

The root cause is structural: all three plugins resolve to the same `.claude-plugin/plugin.json` because they share the same source path. The proper fix is per-plugin isolation with independent `plugin.json` files.

**Proper structure:**
```
repo/
├── .claude-plugin/
│   └── marketplace.json  ← catalog only
├── plugins/
│   ├── airs-tme/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   ├── pai-ops/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   └── prisma-airs/
│       ├── .claude-plugin/plugin.json
│       └── skills/
```

## Proposed Solution

Three phases of work across documentation, detection/migration tooling, and hook/CI improvements.

### Phase 1: Structure Detection (`--check-structure`)

Add a `--check-structure` mode to `detect_version_changes.py` that:

1. Parses marketplace.json and groups plugins by resolved version source
2. Warns when multiple plugin entries resolve to the same `plugin.json`
3. Distinguishes valid patterns (single plugin with multiple skills) from anti-patterns (multiple plugins sharing a source)
4. Outputs actionable warnings with plugin names, resolved paths, and suggested fixes

**Anti-pattern definition:** Multiple distinct plugin entries in marketplace.json that resolve to the same version file. A single plugin entry with multiple skills (like terminal-guru) is valid.

**Key file:** `detect_version_changes.py:113-128` — `get_plugin_version_source()` needs a wrapper that groups by resolved path.

```python
# detect_version_changes.py — new function
def check_structure(repo_root, marketplace_data):
    """Detect structural anti-patterns in marketplace layout."""
    source_to_plugins = {}

    for plugin in marketplace_data.get('plugins', []):
        source = plugin.get('source', './')
        source_dir = (repo_root / source.lstrip('./')).resolve()
        version_file, _ = get_plugin_version_source(source_dir, plugin.get('skills', []))

        key = str(version_file) if version_file else str(source_dir)
        source_to_plugins.setdefault(key, []).append(plugin.get('name'))

    issues = []
    for path, plugins in source_to_plugins.items():
        if len(plugins) > 1:
            issues.append({
                'type': 'shared_version_source',
                'version_file': path,
                'plugins': plugins,
                'suggestion': f'Each plugin needs its own .claude-plugin/plugin.json'
            })

    return {'structure_issues': issues}
```

### Phase 2: Documentation

Update reference docs with:

1. **`references/plugin_marketplace_guide.md`** — Add "Single-Plugin vs Multi-Plugin Marketplace" section with:
   - Decision flowchart: when to use each pattern
   - Valid layout examples (single-plugin, multi-skill bundle, multi-plugin independent)
   - Anti-pattern examples (shared source with single plugin.json)

2. **`references/troubleshooting.md`** — Add entries for shared-source detection warnings

3. **SKILL.md** — Document `--check-structure` and `--ci` flags

### Phase 3: Hook + CI Improvements

**Pre-commit hook:**
- Add structure validation as an advisory warning (does not block commits)
- Print actionable message when shared-source anti-pattern detected
- Structure warnings are advisory locally, enforced in CI

**CI mode (`--ci` flag):**
- Always output JSON (machine-readable)
- Exit 1 for any structural or version issue
- Include `suggested_fixes` array in JSON output
- Intended to replace custom `check-version-bump.sh` scripts in external repos

```bash
# CI pipeline usage
uv run detect_version_changes.py --check-staged --ci
uv run detect_version_changes.py --check-structure --ci
```

### Optional: Automated Migration

Add `--migrate` capability (can be deferred to a follow-up issue):
- Creates `plugins/` subdirectories per plugin
- Moves skills using `git mv`
- Generates per-plugin `plugin.json` (version = max of bundled SKILL.md versions)
- Updates marketplace.json source paths
- Supports `--dry-run` for preview
- Fails gracefully if skills import shared resources outside their directory

## Technical Considerations

- **Version inheritance on migration:** New per-plugin `plugin.json` version should be `max(skill_versions)` — consistent with existing `sync_marketplace_versions.py` logic
- **Semver parser limitation:** Pre-release versions (1.0.0-rc1) parsed as 0.0.0 by `parse_semver()` — document this, stick to X.Y.Z
- **Hook severity:** Structure warnings are advisory (warn, don't block) in local hooks. CI mode (`--ci`) treats them as blocking
- **Existing three-layer defense:** Code fix + pre-commit hook + process reminder (from docs/solutions/logic-errors/multi-skill-plugin-version-sync.md) — this plan extends it with structure validation as a fourth layer

## System-Wide Impact

- **Interaction graph:** `detect_version_changes.py` is called by the pre-commit hook template → hook calls sync script if mismatches found → marketplace.json updated. Adding `--check-structure` is a new code path that doesn't interact with sync
- **Error propagation:** Structure warnings use the same exit code pattern (0=pass, 1=issues). CI mode unifies all checks into a single JSON result
- **State lifecycle risks:** Migration (`--migrate`) moves files via `git mv` — partial failure could leave repo in inconsistent state. Mitigated by dry-run default and atomic operations
- **API surface parity:** The `--ci` flag should work with all modes: `--check-staged --ci`, `--check-structure --ci`, and default mode `--ci`

## Acceptance Criteria

- [ ] `detect_version_changes.py --check-structure` detects shared-source anti-patterns
- [ ] Multiple plugins sharing `source: "./"` produces a clear warning with plugin names
- [ ] Single-plugin multi-skill bundles are NOT flagged as anti-patterns
- [ ] `--ci` flag outputs JSON with `structure_issues`, `suggested_fixes` arrays
- [ ] `--ci` flag returns exit 1 for any detected issue
- [ ] Pre-commit hook runs structure check as advisory warning (non-blocking)
- [ ] `plugin_marketplace_guide.md` documents single vs multi-plugin layouts with examples
- [ ] `troubleshooting.md` has entries for shared-source warnings
- [ ] SKILL.md documents new flags (`--check-structure`, `--ci`)
- [ ] Version bumped in SKILL.md and plugin.json
- [ ] Skillsmith evaluation score recorded

## Success Metrics

- External repos (airs-tme) can run `detect_version_changes.py --check-structure` and get actionable guidance
- CI pipelines can replace custom `check-version-bump.sh` with `detect_version_changes.py --ci`
- No false positives on valid multi-skill plugin bundles (terminal-guru pattern)

## Dependencies & Risks

- **Dependency:** Understanding of airs-tme repo structure for testing real-world scenarios
- **Risk:** Migration tooling could break repos with shared resources — mitigated by deferring `--migrate` to follow-up issue
- **Risk:** Hook version bump required for pre-commit template changes — existing `validate_hook.py` handles this

## Sources & References

### Internal References
- Issue: [#139](https://github.com/totallyGreg/claude-mp/issues/139)
- Version source resolution: `detect_version_changes.py:113-128`
- Multi-skill drift fix: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`
- Plugin structure conventions: `docs/lessons/skill-to-plugin-migration.md`

### External References
- Plugin structure spec: `references/plugin_marketplace_guide.md`
- Distribution workflow: `references/marketplace_distribution_guide.md`
