---
title: "feat(skillsmith): Pass 2 — qualitative conciseness checks + skill-observer fix"
type: feat
status: active
date: 2026-03-22
---

# feat(skillsmith): Pass 2 — Qualitative Conciseness Checks + Skill-Observer Fix

## Overview

Two remaining open issues against skillsmith. Both are self-contained and ship together in one PR.

- **#96**: `evaluate_skill.py` conciseness score is purely quantitative — it cannot flag legacy sections, inline-redundant content, or duplicated reference material. These inflations are invisible to the evaluator even when a human reviewer can spot them immediately.
- **#115**: The `skill-observer` agent fails when invoked directly because plugin cache files at `~/.claude/plugins/cache/` are blocked at the path-permissions level. The existing `ss-observe.md` command already sidesteps this by using a Python subprocess (`analyze_transcript.py`), but the agent's own AGENT.md gives no guidance on this limitation.

---

## Issue #96 — Qualitative Conciseness Checks

### What to add

A new function `check_qualitative_conciseness(skill_path, skill_content)` called from `calculate_all_metrics()`. Its findings are appended to the conciseness dict under a new key `qualitative_warnings: [str]` and surfaced only in `--explain` mode (no score change in v1 — measure first, penalize later).

**File:** `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py`

### Three detectors

#### 1. Legacy section detector

Scan each line of `skill_content` for keywords that signal stale content that should be collapsed or removed:

```python
LEGACY_MARKERS = [
    r'\blegacy\b',
    r'\bdeprecated\b',
    r'prefer .+ instead',
    r'use .+ instead',
    r'old approach',
]
```

For each match, record the line number and a snippet. Emit one warning per block (not per line — group consecutive matches).

Example output:
```
⚠ Qualitative: "legacy JXA commands" block (~27 lines, starting line 84) — consider collapsing to a one-line reference
```

#### 2. Inline-redundant content detector

Detect patterns where a content block of 5+ lines is followed within 3 lines by a reference pointer like `See references/X.md` or `Full guide in references/`. This indicates content that should have been fully offloaded but wasn't.

```python
# Pseudocode
for i, line in enumerate(lines):
    if re.search(r'[Ss]ee `?references/', line) or re.search(r'[Ff]ull guide in `?references/', line):
        # Count non-empty lines in the N lines before this one
        preceding = [l for l in lines[max(0,i-8):i] if l.strip()]
        if len(preceding) >= 5:
            emit warning at line i
```

Example output:
```
⚠ Qualitative: Inline block before "See references/troubleshooting.md" (~8 lines, line 142) — offload to references/ or remove inline content
```

#### 3. Reference duplication detector

For each `references/*.md` file, extract its H2/H3 headings and any table row content (first column). Check if any of those strings appear verbatim in `skill_content`. Flag matches that appear in blocks of 3+ consecutive lines (to avoid false positives from single shared terms).

```python
for ref_file in (skill_path / 'references').glob('*.md'):
    ref_headings = extract_headings(ref_file.read_text())
    for heading in ref_headings:
        if heading in skill_content:
            emit warning: f"Content from {ref_file.name} appears duplicated in SKILL.md: '{heading}'"
```

Keep this conservative — only flag exact heading matches, not partial strings. This avoids false positives while catching the most obvious copy-paste duplication.

### Integration points

**In `calculate_all_metrics()`** (after conciseness score is computed):

```python
conciseness['qualitative_warnings'] = check_qualitative_conciseness(skill_path, body)
```

**In `print_explain_output()`** — append after the existing "To improve:" block for conciseness:

```python
qual_warnings = conc.get('qualitative_warnings', [])
if qual_warnings:
    print("  Qualitative findings (not scored — informational):")
    for w in qual_warnings:
        print(f"    {w}")
```

### Acceptance criteria

- [ ] Legacy/deprecated section markers detected and reported under `--explain`
- [ ] Inline content before "See references/X.md" detected when block ≥ 5 lines
- [ ] Reference heading duplication flagged (exact match, 3+ consecutive lines)
- [ ] No false positives on skillsmith's own SKILL.md (score and output unchanged)
- [ ] No score change — qualitative findings are informational only in v1

---

## Issue #115 — Skill-Observer: Context-Aware Analysis + Cache Permissions

### Root cause recap

Two distinct problems:

1. **Missing context input**: `ss-observe` only accepts a session ID/path. When a user invokes it mid-session with an observation ("I noticed the skill didn't remind Claude to run eval before committing"), that context is lost. The observation should act as a **focusing lens** on the transcript — narrowing which skill and failure mode to investigate — not replace the transcript analysis. The transcript remains the ground truth for *what actually happened*; the user's words clarify *what to look for*.

2. **Agent cache permissions**: When `skill-observer` is invoked as an Agent tool call, reads of `~/.claude/plugins/cache/` are denied at the path level in background/auto mode. The existing `ss-observe.md` sidesteps this via a Python subprocess, but gives no guidance on the limitation.

### Fix

Three changes:

#### A. Update ss-observe.md with context-aware input handling

**File:** `plugins/skillsmith/commands/ss-observe.md`

Update `$ARGUMENTS` handling to accept an optional natural-language observation alongside the session ID, and support being invoked with no session ID (defaults to current/most-recent session):

```markdown
## Input

`$ARGUMENTS` may be:
- A session ID or path (UUID or `.jsonl`)
- A natural-language observation ("I noticed X")
- Both: `<session-id> -- I noticed X`
- Empty: defaults to the current session (most recent JSONL for this project)

## Step 1: Resolve session

If `$ARGUMENTS` includes a session ID or path, use it. Otherwise:
```bash
ls -lt ~/.claude/projects/-Users-totally-Documents-Projects-claude-mp/*.jsonl | head -1
```
Use the most recent file as the session to analyze.

## Step 2: Extract user observation (if any)

If `$ARGUMENTS` contains natural-language context, extract it as a **gap hint**. Pass it to `analyze_transcript.py` as a `--hint` argument so the analysis focuses on that failure mode.

## Step 3: Run analysis

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/agents/skill-observer/scripts/analyze_transcript.py \
  --session <resolved-session> \
  [--hint "<user observation>"] \
  [--skill <skill-name>]
```

## Step 4: Report and offer improve cycle

Report the gap analysis. If gaps are found, offer:
- `/ss-improve <skill-path>` to fix the top gap immediately
- Or defer to a future session
```

Update `argument-hint` frontmatter: `argument-hint: [session-id | observation | both]`

**Note on automatic triggering:** This command can be invoked programmatically (e.g., by a hook after N skill failures in a session) with the failure context passed as the hint. The observe→improve cycle can be fully automated when warranted.

#### B. Update analyze_transcript.py to accept --hint

**File:** `plugins/skillsmith/agents/skill-observer/scripts/analyze_transcript.py`

Add `--hint <text>` argument. When provided, prepend it to the analysis prompt:
```
User observed: "<hint>"
Focus the gap analysis on failures related to this observation.
```
This keeps transcript analysis as the ground truth while using the hint to prioritize findings.

#### C. Add a Limitations section to AGENT.md

**File:** `plugins/skillsmith/agents/skill-observer/AGENT.md`

```markdown
## Limitations

**Plugin cache reads may be blocked in background/auto permission mode.**

When invoked as an Agent tool call, reads under `~/.claude/plugins/cache/` are blocked by path-level permissions — preventing the agent from mapping gaps to installed plugin source files.

**Workaround:** Use `/ss-observe` instead of invoking this agent directly. It runs `analyze_transcript.py` as a subprocess with full filesystem access, supports both session-ID and natural-language hint input, and can be triggered automatically by hooks.
```

### Acceptance criteria

- [ ] `/ss-observe` with no arguments defaults to the current (most-recent) session
- [ ] `/ss-observe I noticed X` analyzes the current session with X as a focusing hint
- [ ] `/ss-observe <session-id> -- I noticed X` combines both inputs
- [ ] `analyze_transcript.py` accepts `--hint` and surfaces hint-relevant gaps first
- [ ] Observe→improve cycle prompt offered when gaps are found
- [ ] AGENT.md documents the cache limitation and `/ss-observe` as the workaround

---

## Implementation Order

1. **#115-A/C** — `ss-observe.md` input handling + AGENT.md docs (low risk, no Python)
2. **#115-B** — `analyze_transcript.py --hint` argument (small Python change, isolated)
3. **#96** — `check_qualitative_conciseness()` in `evaluate_skill.py` (most logic, needs validation)

## Files Changed

| File | Change |
|------|--------|
| `commands/ss-observe.md` | Context-aware input handling, default-to-current-session, observe→improve prompt |
| `agents/skill-observer/AGENT.md` | Add Limitations section |
| `agents/skill-observer/scripts/analyze_transcript.py` | Add `--hint` argument |
| `evaluate_skill.py` | Add `check_qualitative_conciseness()` + integrate into metrics + explain output |
| `skills/skillsmith/SKILL.md` | No change expected (SKILL.md already passes 100/100) |

## Risks

- **False positives in detector #3** (duplicate headings): scoped to exact matches only; H2/H3 headings are specific enough that false positives are unlikely. Validate against omnifocus-manager which was the motivating example.
- **Regex performance on large reference dirs**: iterate once per reference file, not per line of SKILL.md. Acceptable for files of this size.
- **Regression on skillsmith's own score**: run full eval before committing.

## Sources

- Issue #96: qualitative conciseness — `evaluate_skill.py` conciseness section (~line 700)
- Issue #115: agent permissions — `agents/skill-observer/AGENT.md`, `commands/ss-observe.md`
- Motivating example: omnifocus-manager SKILL.md (48 lines of trimmable content not flagged)
