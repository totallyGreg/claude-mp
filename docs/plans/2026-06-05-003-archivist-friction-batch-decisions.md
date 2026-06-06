---
title: "decisions: archivist friction batch — orchestrator hygiene + upstream team-infra"
type: decision-log
status: decided
date: 2026-06-05
decided_date: 2026-06-06
source_plan: "docs/plans/2026-06-05-002-feat-archivist-friction-fix-plan.md"
reports: "2026-06-05-193627-77219, 77259, 77267, 77202, 77210"
---

# decisions: archivist friction batch — orchestrator hygiene + upstream team-infra

## Decisions (2026-06-06)

| Pass | Decision | Landed in |
|------|----------|-----------|
| E (3 rules) | **Accepted — all three added** to `~/.claude/CLAUDE.md` as `## Research Summarization — Epistemic Hygiene`. Original intent was to embed these in attache's agent definition (attache as main orchestrator), but main Claude retained orchestrator role for this batch — so the rules live in CLAUDE.md where they govern main Claude's behavior. | `~/.claude/CLAUDE.md` |
| E-companion | **Accepted** — added to `~/.claude/CLAUDE.md` as `## Subagent Invocation — Briefing Hygiene`. Complements main plan's A2 (Subagent Input Volume Guard, which hardens the receiver) by codifying the orchestrator-side discipline. | `~/.claude/CLAUDE.md` |
| F (77202 + 77210) | **Option 2: Workaround note** added to `~/.claude/CLAUDE.md` as `## Team Mode — Stuck Teammate Workaround` covering `tmux capture-pane` inspection. Includes "review periodically" note — revisit when harness ships fixes or a better pattern emerges. Upstream issue filing deferred (no current access). | `~/.claude/CLAUDE.md` |

## Follow-ups

- **attache scope review** ([#177](https://github.com/totallyGreg/claude-mp/issues/177)): expand attache's agent description so it auto-routes for broader research/summarization/improvement-orchestration domains (not just productivity/GTD). Today, attache only triggers on productivity intent, so main Claude handled this plugin-improvement batch end-to-end with attache idle as a teammate. Issue #177 carries the full proposal (role framing, new triggers, two architectural follow-ons on handoff routing and lead-transfer patterns).
- **Periodic harness review:** Pass F workaround is a band-aid. Set a reminder to revisit the `tmux capture-pane` workaround when CC harness gets updates around team-mode message delivery or stuck-teammate detection.

## Why this doc exists

The companion plan (`2026-06-05-002-feat-archivist-friction-fix-plan.md`) implements four passes of archivist-specific fixes (A–D). These are surgical agent-prompt and script edits scoped to the archivist plugin and the handoff plugin.

This document carries the **non-archivist decisions** that surfaced in the same friction batch:

- **Pass E** — three CLAUDE.md epistemic-hygiene rules for research summarization. These affect every Claude Code session in the repo, not just archivist, so they belong in a separate decision venue with their own review path.
- **Pass F** — two upstream Claude Code harness issues (silent teammate-message drops; no auto-detection of stuck/errored teammates). These are not fixable in this repo.

Splitting these out keeps the implementation plan focused on what can ship via the four passes, and gives the CLAUDE.md / upstream items their own decision and tracking surface.

---

## Pass E — CLAUDE.md: Research Summarization Epistemic Hygiene

**Reports:** 77219 (permalink stripping), 77259 (unverified capability claims), 77267 (scope overgeneralization)

**Root cause:** The orchestrator wrote a meeting briefing by summarizing source material without preserving source URLs, without verifying both ends of a compatibility claim, and without checking the scope of a cited thread before generalizing it.

**Proposed CLAUDE.md additions (three rules):**

```markdown
## Research Summarization — Epistemic Hygiene

1. **Preserve source URLs inline.** When summarizing cited material that includes
   URLs or permalinks (Slack threads, Confluence pages, GitHub issues), keep the
   URL inline in the output — do not degrade to channel name, page title, or
   section heading only. Format: `[#channel-or-title](url)`.

2. **Hedge unverified compatibility claims.** "X maps cleanly onto Y" is a
   capability/fit claim. Before writing it as fact, verify both ends: read the
   source artifact and the target platform's constraints. If either end is
   unverified: rephrase as a hypothesis ("X appears to map onto Y based on...
   — needs verification against Y's schema") or as a question.

3. **Scope-check before generalizing.** Before citing a discussion or issue as
   evidence for a broad claim, verify the original source's scope covers the
   claim. A thread in `#help-gcs-torque` about GCS-tenant access errors is not
   evidence for a universal LaaS concern unless the thread explicitly generalizes.
```

**Open question for Greg:** add all three, add two (which two?), or defer pending further evidence.

**Known limitation — inheritance.** These rules live in CLAUDE.md. CLAUDE.md is loaded into orchestrators but may not propagate to subagent invocations in all contexts. If subagent-level hygiene is also needed, consider duplicating the rules into the archivist's Write Path (where they would be enforced at write time) or replacing them with mechanical checks (e.g., "before writing a meeting note, count source URLs in input vs. output — if output has fewer, prompt user").

---

## Pass E-companion — orchestrator-side input-volume rule

**Why it's here, not in the main plan:** the main plan's Pass A / A2 ("Subagent Input Volume Guard") hardens the *receiver* (archivist). The complementary fix is an orchestrator-side rule so the same hygiene applies to every subagent invocation — vault-curator-as-subagent, attache-as-teammate, future subagents.

**Proposed CLAUDE.md addition (one rule):**

```markdown
## Subagent Invocation — Briefing Hygiene

When spawning a subagent (via the Agent tool or as a team teammate), pass a
**task-scoped briefing** — never the full context history. A task-scoped
briefing contains:

- File paths the subagent should read or write
- Operations to perform (create, update, append, set frontmatter, query, etc.)
- Verbatim content to write, if any

Do NOT include research summaries, raw log dumps, infrastructure descriptions,
or other narrative context that the subagent does not need to execute the
specific operations. Content density at this scale can trip upstream safety
classifiers and produces brittle, hard-to-debug subagent behavior.
```

**Open question for Greg:** add this rule alongside the three epistemic-hygiene rules above, or treat it as a separate decision (it has a different origin — Pass A2 hardening + report 77154 — even though it's CLAUDE.md-shaped).

---

## Pass F — Upstream Claude Code team-infra issues

**Reports:** 77202 (substantive teammate messages silently dropped), 77210 (no auto-detection of stuck/errored teammates)

### 77202 — Message dropping

Substantive teammate messages (long markdown-formatted replies) arrived as `idle_notification` system pings only — the body was dropped. Manual `tmux capture-pane` workaround was required.

**Reproducer:** send a long markdown message via `SendMessage`; check whether the receiving Claude's reply arrives as `teammate-message` or only as `idle_notification`.

### 77210 — Stuck teammate cleanup

When a teammate hits a blocking error (e.g., Vertex API rejection), it emits idle pings indefinitely with no self-cleanup. The orchestrator must manually send a `shutdown_request`. Fix would require the harness to detect N consecutive idle-only turns with no progress and auto-quarantine.

### Decision options for Greg

1. **File an issue** against the Claude Code harness repo (if access).
2. **Add a workaround note** to `CLAUDE.md`: "if a teammate goes quiet, use `tmux capture-pane` to inspect its buffer." This is a band-aid but reduces lost work.
3. **File here as a tracked known limitation** in `docs/lessons/` so future team-mode work can defend against it.

77202 is labeled "blocker" in the source report — accepting it as "not fixable here" is appropriate if no upstream access exists, but a workaround note in CLAUDE.md and/or a `docs/lessons/` entry is the minimum durable response.

---

## Tracking

Once Greg decides on Pass E and Pass F, this document becomes the source of truth for those decisions. Update the frontmatter `status:` from `pending` to `decided`, record the decisions inline, and link to any resulting CLAUDE.md edits or GitHub issues.
