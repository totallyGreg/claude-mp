# Plan: Human-useful, auto-maintained plugin READMEs in skillsmith

**Date:** 2026-07-23
**Skill:** `plugins/foundry/skills/skillsmith`
**Type:** feat (MINOR — new backward-compatible capabilities)
**Status:** Proposed — awaiting approval to implement

## Problem

The plugin-level README should let a newcomer understand, at a glance, **what the plugin is, what's in it, and how to install/use it** — and stay accurate as components change. Today:

- The `## Components` inventory (skills / agents / commands / hooks) is **hand-maintained** in each plugin README → drifts as components are added/renamed/re-described.
- There is **no Install/Quickstart guidance** — a reader can't tell how to add or invoke the plugin.
- `--export-table-row` accepts **any** version, including PATCH → Version History accumulates noise. (Confirmed friction, report `2026-07-23-183506-62264`: 11 patch rows had to be hand-consolidated in commit `ebea875`.)
- Component edits trigger quick *evals* via hooks, but nothing keeps the README inventory in sync.

## Source signals

- **Friction 2026-07-23** (`misleading-skill`): MINOR-only Version History not enforced. Proposed refuse-PATCH / auto-fold / audit. → Workstream B.
- **Friction 2026-06-10** (`misleading-skill`): agent confabulated eval scores without running the tool. **Out of scope** here (agent-enforcement problem, not README) — noted for a separate track.
- **Issue #152**: plugin-structure validation gap (missing `plugin.json`). Adjacent; not blocking.
- No existing open issue covers plugin-README usability → this plan seeds a new tracking issue.

## Design decisions (confirmed with user)

1. **Version history:** refuse PATCH by default **and** auto-fold into the parent MINOR row when it exists; `--allow-patch` override; add `--check-version-history` audit.
2. **Examples:** auto-generate the component *inventory* inside an autogen fence; hand-authored examples live **outside** the fence and are preserved verbatim (same idempotency model as `### Current Metrics`).
3. **Auto-update trigger:** **warn only** — hooks detect a component edit and print "Components section may be stale — run `/ss-...` to refresh." No surprise writes.
4. **Orientation (added):** README must open with what-it-does + what's-inside + Install/Quickstart before the inventory.

## Defined plugin-README section list (the standard skillsmith enforces/generates)

Ordered, top to bottom:

1. **Title + one-line description** — what the plugin does (from `plugin.json` `description`).
2. **What's inside** — 1–3 sentence overview + at-a-glance counts (N skills, N agents, N commands, N hooks).
3. **Install** — marketplace add + enable steps (generated; see below).
4. **Quickstart / Usage** — the handful of most common entry points (top commands / agent invocation), hand-authored zone with a generated fallback.
5. **Components** *(autogen fence)* — Skills / Agents / Commands / Hooks tables, each row = name + brief description (first sentence of the component's frontmatter `description`).
6. **Examples** *(hand-authored, preserved)* — per-component usage examples where complexity warrants.
7. **Changelog** *(plugin-level, MINOR-only)* — plugin-wide changes.
8. **Per-skill sections** — `## Skill: <name>` → `### Current Metrics` + `### Version History` (MINOR-only), unchanged from today.

## Workstreams

### A. Components + orientation generator (`--update-components`)
New mode in `evaluate_skill.py` (or a dedicated `generate_plugin_readme.py` sharing `utils.py`):
- Locate plugin root from a skill/plugin path (reuse existing plugin-root discovery).
- Read `plugin.json` for name/description/version.
- Scan `skills/*/SKILL.md`, `agents/*.md` (or `agents/*/`), `commands/*.md`, `hooks/hooks.json`; extract `name` + **first sentence** of `description`.
- Render "What's inside" counts, Install, and the Components tables into an autogen-fenced block:
  `<!-- BEGIN AUTOGEN: components -->` … `<!-- END AUTOGEN: components -->`.
- Replace only the fenced block; preserve everything outside it (Quickstart, Examples, Changelog, per-skill sections).
- If the fence is absent, insert it in the correct position per the section order.

### B. MINOR-only Version History enforcement
In `--export-table-row`:
- Detect PATCH (`z != 0` in `x.y.z`).
- If a parent `x.y.0` row exists in the target README → **auto-fold**: emit an updated parent row with the patch note appended (dated sub-bullet), not a new row.
- If no parent row and no `--allow-patch` → **refuse** with the friction-report remediation message.
- `--allow-patch` overrides (documented as not recommended).
- New `--check-version-history <readme>` flag: scan the table, list stray patch rows, exit non-zero in CI mode.

### C. Warn-only staleness hook
- Extend `on-skill-edit.sh` / `on-agent-edit.sh` (and add command coverage) to detect component add/rename/description change and print a stale-Components advisory. No file writes.

### D. Docs, template, self-application
- Update `references/plugin_readme_template.md` to the 8-section standard (fence markers, Install, Quickstart).
- Update `SKILL.md` Step 6 to document `--update-components`, MINOR-only behavior, `--check-version-history`.
- Apply the new standard to `plugins/foundry/README.md` as the first consumer (dogfood).
- Add tests in `tests/test_evaluate_skill.py`: PATCH refusal, auto-fold, fence idempotency, component extraction.

## Acceptance criteria

- `--update-components` regenerates the fenced inventory + Install + counts and preserves all hand-authored zones.
- `--export-table-row --version x.y.z` (patch) refuses or auto-folds; MINOR still emits a row; `--allow-patch` overrides.
- `--check-version-history` flags stray patch rows.
- Component-edit hook prints a stale advisory, writes nothing.
- foundry README shows Title → What's inside → Install → Quickstart → Components(autogen) → Examples → Changelog → per-skill.
- skillsmith self-eval stays ≥ current (100/100); new tests pass.

## Out of scope

- Agent eval-score confabulation (friction 2026-06-10) — separate agent-enforcement track.
- Issue #152 plugin.json validation — adjacent, tracked separately.

## Rollout

Per repo workflow: create GitHub tracking issue (source of truth) → implement A–D → skillsmith eval → MINOR version bump (`SKILL.md` + `plugin.json`) → `--update-readme` metrics + MINOR Version History row → `sync.py` marketplace.
