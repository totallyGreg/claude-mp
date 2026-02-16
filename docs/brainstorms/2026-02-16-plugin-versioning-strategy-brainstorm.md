---
date: 2026-02-16
topic: plugin-versioning-strategy
---

# Plugin Versioning Strategy

## What We're Building

A corrected versioning model for the marketplace-manager tooling that treats plugin versions as independent package release versions, not derivatives of skill versions. The current approach (plugin version = highest skill version) conflates two independent version tracks and creates false positives in the detect script.

## Why This Approach

**Approaches considered:**

1. **Plugin version = highest skill version** (current, rejected): Simple but wrong. Creates false positives when skills diverge (vault-architect 1.1.0 != pkm-plugin 1.5.0 flagged as mismatch). Conflates component identity with package identity.

2. **Plugin version = independent package release** (chosen): Follows the official plugin-dev three-level hierarchy. Plugin version is its own semver, bumped whenever any component changes. Marketplace mirrors plugin.json. Skill versions are informational at the plugin level.

3. **No plugin version, skills only** (rejected): Doesn't work for marketplace distribution where a single version represents the installable package.

## Key Decisions

- **Plugin version is independent**: Not computed from skill versions. Manually bumped by developer.
- **Bump type matches component**: If a skill does a minor bump, the plugin does a minor bump. If multiple components change, use the highest bump type.
- **marketplace.json mirrors plugin.json**: Sync script reads plugin.json, not SKILL.md, for the plugin version.
- **detect script warns only**: When component files are staged but plugin.json isn't bumped, warn the developer (non-blocking). Developer decides the version number.
- **Single-skill plugins auto-sync from SKILL.md**: For plugins where `skills: ["./"]` (skill IS the plugin), SKILL.md is the version source. No separate plugin.json needed.
- **Skill versions are informational**: Reported for visibility but not used to compute plugin version.

## Update Cascade

When the detect/sync scripts run, updates flow in this order:

```
1. Developer bumps component version (SKILL.md, agent, command)
2. Developer bumps plugin.json version
   (or auto-synced from SKILL.md for single-skill plugins)
3. sync script: plugin.json → marketplace.json
4. sync script: marketplace.json → README.md table
```

The pre-commit hook enforces steps 2-4 automatically:
- Step 2: Warns if plugin.json wasn't bumped (detect script)
- Step 3: Auto-syncs marketplace.json from plugin.json (sync script)
- Step 4: Auto-syncs README.md from marketplace.json (sync_readme)

## Plugin Type Matrix

| Plugin Type | Example | Version Source | Auto-sync? |
|-------------|---------|---------------|------------|
| Single-skill (`skills: ["./"]`) | helm-chart-developer, swift-dev | SKILL.md | Yes — SKILL.md → marketplace.json → README.md |
| Single-skill (in plugin dir) | skillsmith, omnifocus-manager | plugin.json | Yes — plugin.json → marketplace.json → README.md |
| Multi-skill | pkm-plugin, terminal-guru | plugin.json | Yes — plugin.json → marketplace.json → README.md |

**How to distinguish:** If `skills: ["./"]` and source points to a directory with SKILL.md at root, it's a single-skill-is-plugin. Otherwise, plugin.json is the source.

## Changes Required

### sync_marketplace_versions.py

- **Remove**: Multi-skill `_parse_semver` / `max()` highest-version computation
- **Change multi-skill logic**: Read version from `plugin.json` (not SKILL.md), sync to marketplace.json
- **Keep single-skill auto-sync**: For `skills: ["./"]` plugins, continue reading from SKILL.md
- **Add**: For plugins with `plugin.json`, read version from there as source of truth
- **Keep**: README.md sync via `sync_readme` (already works, reads from marketplace.json)
- **Add**: Informational report listing individual skill versions for multi-skill plugins

### detect_version_changes.py

- **Remove**: Default mode comparing individual skill versions against marketplace plugin version (the `detect_version_changes` function)
- **Replace with**: Check that marketplace.json plugin version matches plugin.json version (source of truth alignment)
- **Keep**: `--check-staged` mode (already correctly maps files to components and checks for bumps)
- **Enhance**: For multi-skill plugins in `--check-staged` mode, if any component file is staged, also check that plugin.json was bumped (warn, not block)
- **Add**: Informational reporting of individual skill version changes

### Pre-commit hook

- **No structural changes**: Hook calls detect and sync scripts. Behavior changes flow from script changes.

### WORKFLOW.md

- **Update**: Multi-skill plugin documentation to reflect independent versioning model
- **Update**: Release checklist — bump plugin.json, not just SKILL.md
- **Clarify**: Single-skill vs multi-skill flow differences

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| Warn or block when plugin.json not bumped? | Warn only. Developer decides version. |
| Single-skill plugins: sync from SKILL.md? | Yes. Skill IS the plugin for `skills: ["./"]`. |
| What about agents and commands without versions? | Agent/command file changes still trigger plugin.json bump warning. Only skills have independent versions. |

## Existing Issue Triage

Evaluated all open marketplace-manager issues against this design:

| Issue | Title | Verdict |
|-------|-------|---------|
| [#39](https://github.com/totallyGreg/claude-mp/issues/39) | Pre-commit hook should suggest plugin.json version bump | **Superseded by this design.** Covers all acceptance criteria and goes further. Close when new issue is created. |
| [#36](https://github.com/totallyGreg/claude-mp/issues/36) | Add version consistency validation hook | **Partially superseded.** Race condition (SKILL.md bumped in same commit) still affects single-skill plugins. Post-sync validation is a useful safety net. Fold into new issue as sub-task. |
| [#25](https://github.com/totallyGreg/claude-mp/issues/25) | Clarify relationship with plugin-dev | **Still relevant, low priority.** Documentation task. Quick win alongside versioning work. |
| [#30](https://github.com/totallyGreg/claude-mp/issues/30) | Fix migrate_to_plugin.py repo root detection | **Still relevant, low priority.** All current migrations done. Fix opportunistically. |
| [#18](https://github.com/totallyGreg/claude-mp/issues/18) | Add /evaluate-skill command and fix version shadowing | **Closed as resolved.** Shadowing fixed by terminal-guru v3.0.0 restructure. `/ss-evaluate` command exists. |

### Race Condition Detail (#36)

The race condition occurs when SKILL.md is bumped in the same commit as other changes:

1. Hook runs `detect` → sees old SKILL.md version (pre-stage)
2. Hook runs `sync` → syncs old version to marketplace.json
3. Commit includes new SKILL.md version
4. Result: marketplace.json has stale version

**With new model:**
- Multi-skill plugins: NOT affected (sync reads plugin.json, which is staged and has the new version)
- Single-skill `skills: ["./"]`: STILL affected (sync reads SKILL.md from disk, not staged content)
- Fix: post-sync validation step checks staged SKILL.md against just-synced marketplace.json

## Next Steps

- `/workflows:plan` for implementation details
- Create new GitHub issue referencing this brainstorm, superseding #39 and folding in #36
- Close #39 and #36 when new issue is created
