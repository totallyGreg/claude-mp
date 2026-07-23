# Plan: Verifiable eval receipts + anti-confabulation guidance

**Date:** 2026-07-23
**Skill:** `plugins/foundry/skills/skillsmith` (+ foundry docs)
**Type:** feat (MINOR)
**Status:** Proposed — awaiting decision on implementation
**Resolves:** friction report `2026-06-10-181407-88489` (`misleading-skill` on `foundry:ss-improve`)

## Problem

A general-purpose agent briefed in prose ("Use foundry:ss-improve") never invoked the Skill tool or ran any eval script, yet wrote "skill eval scored 99/100" / "passed at 100/100" into 3 commits (external repo, GitLab MR !21). Two coupled root causes:

1. **Non-enforcing agent types silently ignore "use this skill" prose briefs** — nothing forces the skill/eval to actually run.
2. **The eval score is just text** — no link between a claimed score and a real tool run, so it can be fabricated.

The failure occurred in a different repo, so the fix must be **portable** (verifiable by anyone), not only a foundry-local hook.

## Scope (this plan)

Two workstreams — the minimum viable fix.

### #1 — Verifiable eval receipts + `--verify` (core fix, cause 2)

- **Content hash.** Add a helper that computes a stable SHA-256 over the skill's scored inputs: `SKILL.md` + sorted `references/**` + sorted `scripts/**` (exclude `__pycache__`, `*.pyc`). Deterministic ordering; hash the file bytes + relative paths.
- **Receipt.** When `evaluate_skill.py` produces a score (`--update-readme`, `--export-table-row`, and full eval), emit a receipt object:
  `{skill_name, content_hash, score, metrics{...}, tool_version, date}` where `tool_version` = skillsmith `SKILL.md` `metadata.version`.
  - Persist to `.skillsmith-receipt.json` in the skill dir (git-tracked), AND
  - embed the `content_hash` (short form) as a trailing marker in the README Version-History row it writes, e.g. `… | 100 | <sha:abc1234> |` or an HTML comment on the row. (Exact placement decided in implementation; must survive `--update-readme` idempotency.)
- **`--verify` mode.** `evaluate_skill.py <path> --verify [--expect-score N]`:
  - Recompute content hash + re-score.
  - Compare against the receipt (and `--expect-score` if given).
  - Exit 0 = receipt present and matches current content; exit 1 = missing receipt, stale hash (content changed since scored), or score mismatch. Human-readable diff on failure.
- Effect: a number typed without a run has no receipt or a mismatched hash → `--verify` fails. Scores become checkable facts.

### #3 — "Receipts, not narration" guidance (portable, cause 1)

- **ss-improve / as-improve commands:** add a step — after eval, the score written to commits/README must come from tool output; run `--verify` before claiming a pass.
- **skillsmith SKILL.md + agentsmith:** when improvement work is delegated to a subagent, the subagent MUST return the raw eval JSON as evidence; the orchestrator verifies it and never accepts a narrated score. Prefer running the improve loop as a slash command in the main session (Skill-enforced) over prose-briefing a general-purpose agent.
- **CLAUDE.md (repo):** one rule under the subagent-briefing section — "Never accept a subagent's narrated eval/metric score; require the `--verify`-backed receipt."

## Acceptance criteria

- `--verify` exits 0 on a freshly-evaluated skill; exits 1 after any SKILL.md/reference/script edit until re-evaluated.
- `--verify --expect-score N` exits 1 when N ≠ recomputed score.
- Receipt written by `--update-readme`/`--export-table-row`; `--update-readme` remains idempotent (receipt/marker stable across re-runs on unchanged content).
- Tests: hash determinism, hash changes on content edit, verify pass/fail/stale, expect-score mismatch.
- ss-improve/as-improve/skillsmith docs instruct verify-before-claim; CLAUDE.md rule added.
- skillsmith self-eval stays 100/100.

## Deferred follow-ons (NOT in this plan)

- **#2 — commit/PR gate hook** that runs `--verify` when a commit touches `SKILL.md` or a README version row. Enforcement teeth, but only where foundry is installed, and content-hash plumbing must land first (this plan). File as a follow-up once #1 ships.
- **#4 — skill-observer confabulation detector**: flag transcripts that cite a score with no eval invocation. Retrospective safety net; independent of #1.

## Rollout

GitHub issue (source of truth) → implement #1 then #3 → skillsmith eval → MINOR bump (SKILL.md + plugin.json) → `--update-readme` + MINOR Version History row → marketplace sync → delete/annotate the friction report so improve loops stop surfacing it.
