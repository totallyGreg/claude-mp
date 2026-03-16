---
title: "fix: Document obsidian file command is read-only (#103)"
type: fix
status: completed
date: 2026-03-16
---

# fix: Document obsidian file command is read-only (#103)

The `obsidian file` command silently accepts `content` and `overwrite` parameters but never writes content. It returns metadata as if the operation succeeded, creating a silent failure mode that is particularly harmful for agents iterating on documents.

## Acceptance Criteria

- [x] New "File Updates" section in `references/cli-patterns.md` showing WRONG (`obsidian file ... content=`) vs CORRECT (`obsidian create ... overwrite content=`) pattern
- [x] New bullet in cli-patterns.md Safety Rules: **`obsidian file` is read-only** -- `content`/`overwrite` params silently ignored
- [x] pkm-manager.md agent safety rules updated with matching bullet
- [x] Version bump to 1.5.3 in SKILL.md frontmatter
- [x] IMPROVEMENT_PLAN.md version history updated with skillsmith eval score
- [x] Skillsmith evaluation passes (no regression from 90/100 baseline)

## Context

- **Issue:** [#103](https://github.com/totallyGreg/claude-mp/issues/103)
- **Precedent:** v1.5.2 documented `folder=` gotcha using same WARNING/CORRECT code block pattern
- **Files to modify:**
  - `plugins/pkm-plugin/skills/vault-curator/references/cli-patterns.md` -- add File Updates section + Safety Rules bullet
  - `plugins/pkm-plugin/agents/pkm-manager.md` -- add safety rule bullet (lines 91-97 area)
  - `plugins/pkm-plugin/skills/vault-curator/SKILL.md` -- version bump to 1.5.3
  - `plugins/pkm-plugin/skills/vault-curator/IMPROVEMENT_PLAN.md` -- version history entry
- **Workaround:** Use `obsidian create path="..." overwrite content="..." silent` instead of `obsidian file`

## Sources

- Related issue: [#103](https://github.com/totallyGreg/claude-mp/issues/103)
- Precedent commit: `1873ed7` (v1.5.2 folder= gotcha)
