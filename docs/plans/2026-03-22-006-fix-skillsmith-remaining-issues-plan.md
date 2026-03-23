---
title: "fix(skillsmith): resolve remaining open issues"
type: fix
status: active
date: 2026-03-22
---

# fix(skillsmith): Resolve Remaining Open Issues

## Overview

Six open GitHub issues remain against the skillsmith plugin. This plan assesses their current relevance, confirms what has already been addressed, and provides a prioritized implementation path for what remains.

## Issue Triage

### ✅ Partially Addressed

| Issue | Status | What's Done | What Remains |
|-------|--------|-------------|--------------|
| #110: Auto-detect and migrate IMPROVEMENT_PLAN.md | Partial | `ss-improve` Step 0b migrates on touch | `evaluate_skill.py` has no warning; 9 skills still have `IMPROVEMENT_PLAN.md` |
| #81: Full evaluation before committing | Partial | `ss-improve` uses full eval (no `--quick --strict`); Step 6 loop updated | No explicit commit-gate note in SKILL.md; no PostToolUse hook |

### 🔴 Still Open

| Issue | Type | Summary |
|-------|------|---------|
| #82 | bug | Orphan detection misses `[Title](references/file.md)` markdown link syntax |
| #108 | enhancement | `ss-improve` doesn't auto-patch missing recommended frontmatter (`license`, `compatibility`) |
| #96 | enhancement | Conciseness score is purely quantitative; misses legacy/duplicate/redundant content |
| #115 | bug | skill-observer agent blocked from reading plugin cache files (path-level permission issue) |

---

## Proposed Solution

Implement in two passes: **Pass 1** — bugs and quick wins; **Pass 2** — qualitative enhancements.

---

## Pass 1: Bugs & Quick Wins (Issues #82, #108, #110 remainder, #81 remainder)

### Fix #82 — Orphan detection regex (evaluate_skill.py)

**File:** `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

Current patterns (lines ~1437–1443):
```python
patterns = [
    f'`references/{ref}`',
    f'references/{ref}',
    f'`{ref}`',
]
```

Missing: `[Any Text](references/filename.md)` and `[Any Text](references/filename.md)` inside bold `**[...](...)**`.

**Fix:** Add a regex pattern for markdown link syntax:
```python
import re

def _ref_is_mentioned(skill_content: str, ref: str) -> bool:
    patterns = [
        f'`references/{ref}`',
        f'references/{ref}',
        f'`{ref}`',
    ]
    if any(p in skill_content for p in patterns):
        return True
    # markdown link: [any text](references/filename.md) or (references/filename.md)
    return bool(re.search(rf'\(references/{re.escape(ref)}\)', skill_content))
```

Replace the `is_mentioned` check in `check_references()` to call `_ref_is_mentioned()`.

### Fix #108 — Auto-patch missing frontmatter fields (ss-improve)

**File:** `plugins/skillsmith/commands/ss-improve.md`

Add a new **Step 0c** between the current Step 0b and Step 1:

```markdown
## Step 0c: Auto-patch missing recommended frontmatter

Run:
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/evaluate_skill.py $ARGUMENTS --explain
```

If the output identifies missing recommended frontmatter fields (`license`, `compatibility`):
1. Apply sensible defaults — do NOT silently apply wrong values:
   - `license: MIT` (confirm with user if license file exists and differs)
   - `compatibility: claude-code` (adjust if skill has Python scripts → append "Requires uv for Python script execution")
2. Patch `SKILL.md` frontmatter with the Edit tool
3. Note: these are worth +3–6 pts per field pair; document the delta in Step 4
```

### Fix #110 remainder — evaluate_skill.py IMPROVEMENT_PLAN.md warning

**File:** `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

In the spec compliance section, add a check:
```python
# Check for legacy IMPROVEMENT_PLAN.md without README.md
improvement_plan = skill_path / 'IMPROVEMENT_PLAN.md'
readme = skill_path / 'README.md'
if improvement_plan.exists() and not readme.exists():
    warnings.append(
        "IMPROVEMENT_PLAN.md found without README.md — "
        "run /ss-improve to migrate (or: mv IMPROVEMENT_PLAN.md → README.md format)"
    )
```

Also: audit the 9 skills that still carry `IMPROVEMENT_PLAN.md` (see list below) and migrate them via `/ss-improve`.

**Skills with IMPROVEMENT_PLAN.md (no README.md):**
- `plugins/gateway-manager/skills/agentgateway/`
- `plugins/gateway-manager/skills/kgateway/`
- `plugins/marketplace-manager/skills/marketplace-manager/`
- `plugins/pkm-plugin/skills/vault-architect/`
- `plugins/pkm-plugin/skills/vault-curator/`
- `plugins/terminal-guru/skills/zsh-dev/`
- `plugins/terminal-guru/skills/signals-monitoring/`
- `plugins/ai-risk-mapper/skills/ai-risk-mapper/`
- `skills/swift-dev/`

### Fix #81 remainder — Explicit commit gate in SKILL.md

**File:** `plugins/skillsmith/skills/skillsmith/SKILL.md`

In Step 6, add an explicit pre-commit note after the re-evaluate block:

```markdown
> **Before committing any skill improvement**, run the full evaluation (no flags) and confirm
> no score regressed. This is the project-level gate from `CLAUDE.md`. `--quick` is for
> development iteration only — it does not produce the metrics captured in README.md Version History.
```

Optionally, evaluate adding a `hooks.json` PostToolUse hook that auto-runs `--quick` when any `SKILL.md` is saved via Edit/Write (non-blocking, informational). See issue #81 comment for full hook scope.

---

## Pass 2: Qualitative Enhancements (Issues #96, #115)

### Enhancement #96 — Qualitative conciseness checks

**File:** `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

Add a `check_qualitative_conciseness(skill_path, skill_content)` function that runs after the quantitative conciseness score. It should:

1. **Legacy section detection** — regex scan for lines containing `legacy`, `prefer X instead`, `deprecated`, `⚠️ Old`. Emit a warning per matched section with estimated line count.
2. **Inline content with trailing "See references/X.md"** — detect patterns like a block of 5+ lines followed by `See references/` or `Full guide in references/`. Warn that the inline block should be moved.
3. **Duplicate content detection** — for each `references/*.md` file, extract headers/tables; check if any are reproduced verbatim (or near-verbatim) in SKILL.md. Flag the line range.
4. **Orphan regex fix** (from #82) is a prerequisite for this — solve #82 first.

Qualitative findings are surfaced as `--explain` warnings only (no score penalty in v1 — measure first, penalize later).

**Also fix orphan regex for condensed multi-link lines:**
```markdown
[A](references/a.md), [B](references/b.md)
```
The `re.search` fix from #82 covers this automatically since it searches for each ref by pattern, not line structure.

### Bug #115 — skill-observer plugin cache permissions

**Root cause:** The agent has `tools: ["Read", "Bash", "Grep", "Glob"]` declared, but plugin cache files at `~/.claude/plugins/cache/` are blocked at the path-permissions level (not tool-level) in background/auto mode.

**Options (ordered by effort):**

| Option | Approach | Effort |
|--------|----------|--------|
| A | Parent session pre-reads cache files and injects content into agent prompt | Low — no AGENT.md changes |
| B | Document the limitation + add foreground-first guidance to AGENT.md | Low |
| C | Add `allowedPaths` or equivalent field to AGENT.md frontmatter (if spec supports it) | Medium — needs spec research |
| D | Route skill-observer through `ss-observe` command which pre-reads files and passes them | Medium |

**Recommended (Pass 2):**
- Implement Option A/D: update `ss-observe.md` to pre-read the relevant SKILL.md and reference files from plugin cache, then pass content inline to the agent prompt.
- Implement Option B: add a "Limitations" section to AGENT.md noting the plugin cache path issue and the workaround.

---

## Acceptance Criteria

### Pass 1
- [ ] `evaluate_skill.py` orphan detection matches `[Title](references/file.md)` syntax (closes #82)
- [ ] `ss-improve` auto-patches `license` and `compatibility` frontmatter with sensible defaults (closes #108)
- [ ] `evaluate_skill.py` emits warning when `IMPROVEMENT_PLAN.md` exists without `README.md` (closes #110)
- [ ] SKILL.md Step 6 explicitly documents full-evaluation-before-commit requirement (closes #81)
- [ ] All 9 legacy-format skills migrated to README.md format
- [ ] Eval score for skillsmith itself does not regress

### Pass 2
- [ ] Qualitative conciseness checks detect legacy/duplicate/inline-redundant content and surface via `--explain` (closes #96)
- [ ] `ss-observe` pre-reads plugin cache files before launching agent, resolving blocked reads (closes #115)
- [ ] AGENT.md documents limitation + workaround

---

## Dependencies & Risks

- **#82 is a prerequisite for #96** — fix orphan detection before adding qualitative checks that rely on reference file scanning
- **`evaluate_skill.py` changes** must not regress existing scores for any skill in the repo; run eval on all skills with IMPROVEMENT_PLAN.md after changes
- **Issue #115 path-permissions** may be a platform-level constraint in Claude Code background agents — investigate before building workaround

---

## Sources & References

- Issue #82: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py:1430–1454`
- Issue #108: `plugins/skillsmith/commands/ss-improve.md`
- Issue #110: `plugins/skillsmith/commands/ss-improve.md` (Step 0b already exists)
- Issue #81: `plugins/skillsmith/skills/skillsmith/SKILL.md` Step 6
- Issue #96: `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` (conciseness section)
- Issue #115: `plugins/skillsmith/agents/skill-observer/AGENT.md` (tools declared, path permissions remain)
- Related: Issues #81, #82, #96, #108, #110, #115
