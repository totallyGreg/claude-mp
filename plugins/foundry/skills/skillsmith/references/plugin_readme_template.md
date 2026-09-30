# Plugin README Template and Authoring Guide

A plugin README should let a newcomer understand — at a glance — **what the plugin is, what's in it, and how to install and use it**, and stay accurate as components change. It combines **auto-generated** blocks (component inventory, install, metrics) with **hand-authored** prose (quickstart, examples) that is preserved across regeneration.

Per-skill metrics live in the **plugin-level README.md** (`plugins/<plugin>/README.md`), not in skill directories. Each skill's metrics live under a `## Skill: <name>` section.

## Defined section order

A plugin README has these sections, top to bottom:

1. **Title + one-line description** — what the plugin does.
2. **What's inside** *(autogen)* — overview + at-a-glance counts.
3. **Install** *(autogen)* — marketplace add + install commands.
4. **Quickstart / Usage** *(hand-authored)* — the few most common entry points.
5. **Components** *(autogen)* — Skills / Agents / Commands / Hooks tables.
6. **Examples** *(hand-authored, optional)* — per-component usage where complexity warrants.
7. **Changelog** *(hand-authored)* — plugin-wide version history.
8. **Per-skill sections** — `## Skill: <name>` → `### Current Metrics` + `### Version History`.

## When to update

- **Component inventory + install + counts**: `uv run scripts/evaluate_skill.py <skill-or-plugin-path> --update-components` — regenerates the autogen blocks; preserves everything outside the fences.
- **Skill metrics**: `uv run scripts/evaluate_skill.py <skill-path> --update-readme` — updates `### Current Metrics` in the correct `## Skill:` section.
- **Add a version row**: `uv run scripts/evaluate_skill.py <skill-path> --export-table-row --version X.Y.0` and paste into `### Version History`.
- **Audit version history**: `uv run scripts/evaluate_skill.py <skill-path> --check-version-history` — flags stray PATCH rows.

## Autogen fences

Auto-generated content lives between markers. **Never hand-edit inside a fence** — regeneration overwrites it. Put hand-authored content (Quickstart, Examples) *outside* the fences; it is preserved verbatim.

```markdown
# {plugin-name}

{One-line description.}

{Optional hand-authored intro paragraph.}

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

{Plugin description.}

**At a glance:** N skills · N agents · N commands · N hooks

## Install

```
/plugin marketplace add {owner}/{repo}
/plugin install {plugin}@{marketplace}
```
<!-- END AUTOGEN:overview -->

## Quickstart

{Hand-authored — the handful of commands or agent invocations a new user runs first.}

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (N)
| Skill | Description |
|-------|-------------|
| `name` | {first sentence of the skill's tagline/description} |

### Agents (N)
| Agent | Description |
|-------|-------------|

### Commands (N)
| Command | Description |
|---------|-------------|

### Hooks (N)
| Hook | Trigger | Purpose |
|------|---------|---------|
<!-- END AUTOGEN:components -->

## Examples

{Hand-authored, optional — usage examples for the more complex components.}

## Changelog

| Version | Changes |
|---------|---------|
| X.Y.0 | {What changed} |

## Skill: {skill-name}

### Current Metrics

**Score: X/100** (Excellent) — YYYY-MM-DD

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| X | X | X | X | X |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| X.Y.0 | YYYY-MM-DD | [#N](url) | {What changed and why} | X | X | X | X | X | X |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)
```

## Authoring notes

### Autogen blocks (`--update-components`)
- **Do not hand-edit inside the fences** — run `--update-components` to refresh.
- Descriptions come from each component's frontmatter `description` (first sentence). Commands without a `description` fall back to the first prose paragraph of the body — so give every command a `description` for the cleanest output.
- First-time insertion: an existing `## Components` section is replaced in place; on a fresh README the blocks are inserted before `## Changelog` / `## Skill:`.

### Skill sections
- One `## Skill: <name>` section per skill; `<name>` is the skill directory name.
- Single-skill plugins still use `## Skill:` for consistency.

### Current Metrics (### level)
- **Auto-managed** — run `--update-readme`; do not hand-edit.
- **Interpretation**: Excellent (≥95), Good (≥80), Fair (≥60), Needs work (<60).
- Plugin README is the sole metrics record; do not write metrics to SKILL.md frontmatter.

### Version History (### level) — MINOR-only convention
- **MINOR-only**: rows use `x.Y.0` versions. PATCH releases are folded into their parent MINOR row, not added as new rows — this keeps the release cadence readable.
- `--export-table-row --version x.y.z` (a PATCH) **refuses** by default and, when the parent `x.y.0` row exists, **auto-folds** the patch into it (updating date/metrics, appending a `+vx.y.z` marker). Pass `--allow-patch` to force a standalone row (not recommended).
- Use `--check-version-history` in CI or before a release to catch stray patch rows.
- **Newest first**; all metric columns required (use `-` when unavailable).

### Changelog (## level)
- Plugin-level history (distinct from per-skill metrics history): new skills, reorganizations, hooks added.

## Idempotency guarantee

`--update-components` only rewrites content between the `overview` and `components` fences. `--update-readme` only rewrites the `### Current Metrics` subsection of the targeted `## Skill:` section. All other content — Quickstart, Examples, Changelog, other skill sections, and any hand-edited prose — is preserved verbatim.
