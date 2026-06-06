---
title: "fix: archivist friction batch — 2026-06-05 session reports"
type: fix
status: active
date: 2026-06-05
reports: "2026-06-05-193627-* (14 reports) + 2026-06-05-205418-20194.md (reproducer)"
---

# fix: archivist friction batch — 2026-06-05 session reports

## Overview

Fifteen friction reports were filed during and after a `Labs as a Service` vault session (plus a reproducer from a subsequent terminal-guru vault-update session). This plan covers the four implementable passes (A–D) that ship as archivist-, vault-curator-, vault-architect-, and handoff-side edits. All passes target existing files with surgical edits; no new files are created.

Passes A–D cover: archivist agent denial-recovery + subagent input-volume guard + meeting routing (4 agent-level reports), vault-curator role-boundary enforcement + quality hardening (3 skill reports), vault-architect notation canon (1 skill report), and handoff script regex + filter implementation (2 script/skill reports).

**Non-archivist decisions split out.** Three reports (77219, 77259, 77267) describe orchestrator-level epistemic-hygiene failures that map to CLAUDE.md changes, and two reports (77202, 77210) describe upstream Claude Code harness gaps. These are not archivist-specific and have their own decision venue at `docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md` (see "Related upstream issues" near the end of this plan).

## Problem Frame

| Report | Topic | Pass | Target | Severity |
|--------|-------|------|--------|----------|
| 76995 | Vault Read denials despite fix | A | `agents/archivist.md` §Denial Handling | blocker |
| 205418-20194 | Denial-recovery omits settings.json allowlist | A | `agents/archivist.md` §Denial Handling | friction |
| 77154 | Context dump triggers Vertex AI rejection | A | `agents/archivist.md` §Initialization | blocker |
| 77178 | Meeting actions not routed to OmniFocus/Asana | A | `agents/archivist.md` §Post-Workflow | friction |
| 77074 | Curator invents undefined fileClass | B | `skills/vault-curator/SKILL.md` §Write Quality Gate | friction |
| 77122 | Entity mentions not wikilinked | B | `skills/vault-curator/SKILL.md` §Write Quality Gate | friction |
| 77162 | Curator creates fileClass (architect territory) | B | `skills/vault-curator/SKILL.md` §Write Boundaries | friction |
| 77170 | Vault notation inconsistency — 3 competing styles | C | `skills/vault-architect/SKILL.md` §Design Principles | nit |
| 77186 | Handoff regex rejects `/` in tmux session names | D | `skills/handoff/scripts/handoff` line 122 | blocker |
| 77194 | `--filter` can't disambiguate multiple claude panes | D | `skills/handoff/SKILL.md` §Tmux Transport | friction |

The following five reports surfaced in the same batch but are not archivist-specific. They are tracked in the sister decision-log doc (`docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md`) and are not implementation targets in this plan:

| Report | Topic | Tracked in | Notes |
|--------|-------|------------|-------|
| 77219 | Slack permalinks stripped during summarization | Sister doc — Pass E | CLAUDE.md change |
| 77259 | Unverified capability assertions in briefings | Sister doc — Pass E | CLAUDE.md change |
| 77267 | Scope-bounded source overgeneralized | Sister doc — Pass E | CLAUDE.md change |
| 77202 | Substantive teammate messages silently dropped | Sister doc — Pass F | Upstream Claude Code harness |
| 77210 | No auto-detection of stuck/errored teammates | Sister doc — Pass F | Upstream Claude Code harness |

## Requirements Trace

- R1. AGENT.md Denial Handling explicitly surfaces `settings.json` allowlist as recovery option (reports 76995, 205418-20194)
- R2. AGENT.md Initialization rejects orchestrator context dumps when spawned as subagent (report 77154)
- R3. AGENT.md Post-Workflow offers OmniFocus/Asana routing after meeting extraction (report 77178)
- R4. vault-curator validates `fileClass:` values against `_vault-profile.md` Active fileClasses before writing (report 77074)
- R5. vault-curator resolves entity mentions to wikilinks; surfaces unresolvable entities before writing (report 77122)
- R6. vault-curator explicitly rejects schema-creation requests and routes to vault-architect (report 77162)
- R7. vault-architect canonizes one notation system for action items, decisions, and status in Design Principles (report 77170)
- R8. handoff script regex allows `/` in tmux session names AND rejects path-traversal-shaped targets (report 77186)
- R9. handoff script gains `--filter-address <regex>` flag and documents combined `--filter` / `--filter-address` use (report 77194)

Requirements R10 and R11 — CLAUDE.md epistemic-hygiene rules and upstream team-infra escalations — are tracked in the sister decision-log doc (`docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md`) and are not in this plan's scope.

## Scope Boundaries

- Does NOT touch `_vault-profile.md` format — fileClass validation reads the existing `## Active fileClasses` section (Pass B / C may optionally tighten the architect-side template shape; not required for this plan)
- Does NOT change agent model, tools list, or color
- Does NOT create new reference files inside the plugins — all in-plugin changes are edits to existing SKILL.md sections or AGENT.md sections. (One new repo-level doc is created at `docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md` to carry the non-archivist decisions split out of this plan.)
- Does NOT fix the teammate message drop (report 77202) — that is upstream harness code, tracked in the sister decision-log doc
- Does NOT fix auto-detection of stuck teammates (report 77210) — same reason
- CLAUDE.md changes are NOT in this plan — they are tracked in the sister decision-log doc as separate decisions
- **Pass independence:** Passes A, C, and D are independent and can be executed in any order or split across sessions. Pass B sub-items (B1, B2, B3) all edit `vault-curator/SKILL.md` and share a single skill-score gate (≥96) — execute all three in one editing session before running `/ss-improve`, or treat them as one logical pass for scheduling purposes.

## Context & Research

### Baseline Scores (pre-work)

| Component | Score | Last Evaluated |
|-----------|-------|----------------|
| archivist agent | 93 (trigger 93, prompt 95, coherence 93) | 2026-06-04 |
| vault-architect SKILL | 94 | 2026-04-28 |
| vault-curator SKILL | 96 | 2026-05-03 |
| handoff SKILL | 98 | 2026-06-04 |

### Relevant Files

- `plugins/archivist/agents/archivist.md` — agent system prompt; §Initialization (lines ~100–166), §Denial Handling (lines ~192–208), §Post-Workflow (lines ~388–414)
- `plugins/archivist/skills/vault-curator/SKILL.md` — §Vault Write Quality Gate (lines 63–70), §Write Boundaries (lines 83–87)
- `plugins/archivist/skills/vault-architect/SKILL.md` — §Design Principles (lines 326–330)
- `plugins/handoff/skills/handoff/scripts/handoff` — explicit-target regex at line 122; pane-discovery filter at lines 105–108
- `plugins/handoff/skills/handoff/SKILL.md` — §Tmux Transport: What to Know
- `plugins/handoff/skills/handoff/references/tmux-targeting.md` — pane discovery algorithm documentation

### Related Reports

- Report 205418-20194 is the reproducer for 76995: the same Read-denial pathology hit the terminal-guru vault-update session. The reproducer adds the crucial detail that recovery guidance must distinguish two failure modes — the durable `~/.claude/settings.json` allowlist (Mode 1) and the session-restart path for cached in-session denials (Mode 2). A1's rewrite labels both modes explicitly.
- Reports 77074 and 77162 are the same root cause (curator role boundary): curator accepted a fileClass that wasn't in the vault's schema (inventing one) and accepted architect-territory schema creation requests. Both B fixes go in the same editing session.
- Reports 77219, 77259, 77267 share one root cause (orchestrator epistemic hygiene) and map to a CLAUDE.md block tracked in the sister decision-log doc (`docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md`), not in this plan.

---

## Implementation Phases

### Pass A — archivist AGENT.md: Denial Recovery + Context Guard + Meeting Routing

**Target:** `plugins/archivist/agents/archivist.md`

#### A1. Denial Recovery — settings.json allowlist (reports 76995, 205418-20194)

**Current state (§Denial Handling, lines ~192–208):**
The section stops on first denial and tells the user to "approve when prompted again" or "restart session." It does not mention adding a durable Read allowlist entry to `~/.claude/settings.json`.

**Proposed change — append to the Denial Handling section, structured by failure mode:**

```
### When Read denials persist

The Read tool can fail in two distinct modes; each has a different recovery
path. Apply the mode that matches the observed symptom.

**Mode 1 — You expect this path to be writable in future sessions.**

Add a durable allow entry in `~/.claude/settings.json` under the
`permissions.allow` array. Entries are strings of the form
`Tool(arg-pattern)`:

```json
{
  "permissions": {
    "allow": [
      "Read(/absolute/path/to/vault/**)"
    ]
  }
}
```

Alternatively, add the entry to the project's `.claude/settings.json` scoped
to this vault session. The entry takes effect for *future* prompts; existing
in-session denials are not retroactively cleared by this edit.

**Mode 2 — A deny is cached in the current session and no UI prompt is
appearing.**

This pattern is observed empirically but not yet root-caused to a specific
harness mechanism. The only reliable recovery is to restart the Claude Code
session and approve the Read prompt when it surfaces. A `settings.json` entry
alone will not clear an already-cached in-session deny.

If you want both immediate recovery and durable coverage, apply Mode 1 first
(so the next session loads with the entry pre-approved) and then restart per
Mode 2.
```

**Eval criteria:**
- Agent score ≥ 93 (no regression)
- Denial-recovery prose contains the `permissions.allow` schema and a verifiable JSON example matching the live `~/.claude/settings.json` format
- The two failure modes are labeled and described independently; Mode 2 is marked "observed empirically, not yet root-caused"
- `/as-improve` confirm: prompt quality sub-score does not drop

#### A2. Subagent Input Volume Guard (report 77154)

**Current state (§Initialization, lines ~101–166):**
No instruction about what content to accept or reject when spawned as a subagent. This allowed an orchestrator to pass research data + internal infrastructure details that accumulated enough content density to trigger Vertex AI's safety classifier (request `req_vrtx_011CbkGyVpK7npatDmYFCRUe`).

**Framing — defense-in-depth, not the primary fix:**

The underlying cause is orchestrator behavior — the orchestrator should not pass full context history to a subagent. This guard hardens the *receiver* (archivist) so the failure can't recur even when an orchestrator misbehaves, but the same hygiene must apply to every subagent invocation, not just archivist. A complementary orchestrator-side rule belongs in a separate venue (see "Related upstream issues" below, where Pass E and Pass F are tracked) so it covers vault-curator-as-subagent, attache-as-teammate, and any future subagent the same way.

**Proposed change — add as a new "Subagent Input Volume Guard" block in §Write Path (near lines ~188–192):**

```
### Subagent Input Volume Guard (defense-in-depth)

When spawned as a subagent (not via an interactive session), refuse oversized
briefings before initialization. Use an operational trigger, not category
labels — category labels like "research summaries" or "narrative context" are
subjective and cause both false-positive refusals on legitimate large
briefings AND false-negative passes on real dumps. The trigger:

  IF message exceeds ~2000 tokens AND fewer than 2 explicit file paths are
  present in the message, treat the input as an oversized briefing.

Response when the trigger fires — prefer the soft-confirm path first:

  "I see ~N tokens of content and few file paths. Should I write this
  verbatim as content, or treat it as context for a write I should plan?
  If neither — please resend a task-scoped briefing (paths + operations +
  content)."

If the orchestrator's reply doesn't resolve the ambiguity (or it doesn't
reply at all), refuse:

  "I need a task-scoped briefing (paths + operations + content). Please
  resend with only what's needed for the file operations."

A well-formed briefing — file paths + operations (create / update / append /
set frontmatter / etc.) + verbatim content to write — passes through
unchanged at any length, because the path count is the dominant signal. The
guard is a backstop; the primary fix for repeated trips of this guard is
upstream orchestrator behavior.
```

**Eval criteria:**
- Agent score ≥ 93 (no regression)
- System prompt quality sub-score does not drop
- New block present and findable under "subagent" or "volume guard"
- Smoke test: spawn archivist with a 5000-token message + 0 file paths → soft-confirm fires, then refuse on ambiguous reply
- Smoke test: spawn archivist with a 5000-token message + 3 file paths + clear operations → guard does NOT fire (well-formed briefing passes)
- Framing note documents that the guard is defense-in-depth and that the orchestrator-side rule lives in the separate decision-log doc

#### A3. Meeting Actions → OmniFocus/Asana Routing (report 77178)

**Current state (§Post-Workflow Cross-Skill Handoff table, lines ~392–413):**
The table lists curator→architect and architect→curator handoffs (both within-archivist). Meeting Extraction is curator territory, but the offered next-action (`attache:attache`) is neither curator nor architect — it doesn't fit the existing two-skill symmetry.

**Proposed change — introduce a third table for external-system handoffs:**

Add a new section titled "External-System Handoffs" beneath the two existing Cross-Skill Handoff tables in §Post-Workflow. Use the same "Completed | Offer" two-column shape, attributed to the curator side:

```
### External-System Handoffs

| Completed (curator) | Offer (next) |
|---------------------|--------------|
| Meeting Extraction completed | "Action items or decisions were captured. Route to the task system? `attache:attache` can push to OmniFocus (personal) or Asana (team). Meeting notes are evidence; the task system is the system of record." |
```

(Alternative considered: extend the existing tables' title from "Cross-Skill Handoff" to "Post-Workflow Handoffs" and broaden to cover non-architect destinations. Rejected: the within-archivist semantic of "Cross-Skill" is useful as a category and the new external-system table provides a cleaner home for future destinations such as Slack notifications or external API calls.)

**Eval criteria:**
- Agent score ≥ 93 (no regression)
- New "External-System Handoffs" section present in §Post-Workflow
- Row appears under "Completed (curator)" (correct directional attribution)

---

### Pass B — vault-curator SKILL.md: Role Boundary + Quality Enforcement

**Target:** `plugins/archivist/skills/vault-curator/SKILL.md`

#### B1. fileClass Validation Gate (report 77074)

**Current state (§Vault Write Quality Gate, lines 63–70):**
Items 1–5 cover frontmatter position, linter compliance, wikilinks, create-overwrite safety, and read-before-write. No check against the vault's declared fileClass registry.

**Freshness and parsing contracts (resolves two architectural questions left open by the report):**

- **Freshness:** archivist's Initialization reads `_vault-profile.md` once at session start. If vault-architect registers a new fileClass mid-session, the in-context snapshot is stale and B1 would reject a valid write. To avoid this, **the curator re-reads `_vault-profile.md` from disk before each fileClass check** (one Read per write — cheap). Do not rely on the cached parent-agent context for this gate.
- **Parsing:** the architect template renders `## Active fileClasses` without a canonical shape. Define one parse contract: **extract the first column of a markdown table under the heading; if the heading is a bulleted list instead, take the first capitalized token on each `-` line; if neither shape parses, skip the gate and emit a one-line warning** ("fileClass validation skipped — `_vault-profile.md` `## Active fileClasses` is empty or unparseable"). Pair this with a follow-up tightening on the architect side (see C1's architect-template work) to mandate the table shape going forward, so the parser eventually has a single contract.

**Proposed change — add item 6 to the Write Quality Gate list:**

```
6. **fileClass validation** — when `fileClass:` is present in content being
   written:

   a. Re-read `_vault-profile.md` from disk (do not rely on the cached
      session-init copy — the architect may have registered new fileClasses
      mid-session).
   b. Parse `## Active fileClasses`:
        - if rendered as a markdown table, extract the first column
        - else if rendered as a `-` bulleted list, take the first capitalized
          token on each line
        - else emit warning: "fileClass validation skipped —
          `_vault-profile.md` `## Active fileClasses` is empty or unparseable"
          and proceed with the write.
   c. If the value appears in the parsed set, allow the write.
   d. If the value is absent:
      - Refuse the write.
      - Surface the gap: "fileClass `<value>` is not in the vault's Active
        fileClasses registry. Consult vault-architect to register it before
        writing, or choose an existing fileClass: [list]."
      - Never invent a fileClass to complete a write.
```

**Eval criteria:**
- Skill score ≥ 96 (no regression)
- Item 6 present in Write Quality Gate with explicit freshness (re-read from disk) and parsing (table-first, bullet-fallback, warn-and-skip) contracts
- `/ss-improve` confirm: Conceptual sub-score should improve (closes a documented gap)
- Integration smoke test (sandbox vault): architect registers fileClass `X` mid-session; curator immediately writes a note with `fileClass: X` → write succeeds (validates the freshness contract)
- Parse test (sandbox vault): `## Active fileClasses` rendered as a bulleted list with extra prose → curator parses the capitalized first-tokens and accepts a write whose fileClass matches; warns gracefully when the section is empty

#### B2. Entity Mention → Wikilink Check (report 77122)

**Current state (§Vault Write Quality Gate, item 3, line 68):**
"Wikilinks over backticks — use `[[Target]]` for all vault entity references." This rule is weak: it governs formatting style but doesn't require checking that plain-text entity mentions could be wikilinks.

**Design note:** This is a **flag-don't-resolve quality gate that composes upstream obsidian-cli primitives** — it does not roll a parallel entity resolver. The obsidian CLI already provides wikilink-style name resolution (`file=<name>` resolves like a wikilink, alias-aware), an `obsidian search` primitive, and an `obsidian aliases` primitive. Curator's job is to *flag* unlinked proper nouns and let the user decide, using those primitives for the cheap confirmation pass — not to scan-and-rewrite the entire content body.

**Proposed change — extend item 3 or add as item 3a:**

```
3a. **Entity wikilink check** — before writing, scan the proposed content
    for capitalized proper-noun phrases that are NOT already wikilinked.
    Bound the scan to keep it fast and avoid prompt storms:

    - Skip content inside code fences (``` ```), inline code (`...`), and
      YAML frontmatter — capitalized tokens in those regions are not entity
      mentions.
    - Skip sentence-initial single capitalized words and common acronyms
      (API, JSON, YAML, HTTP, URL) via a stop-list.
    - Prefer multi-word proper-noun phrases (`Prisma AIRS Team`,
      `Labs as a Service`) over single-word candidates; these are less
      likely to be false positives.
    - Cap candidates per write at ~20. If the scan exceeds the cap, surface
      a single summary ("Found 35 capitalized phrases. Show first 20 or
      skip the check for this write?") rather than continuing.

    For each surviving candidate, run a single batch existence check using
    `obsidian search query="<phrase>"` (or `obsidian aliases` for known
    alias-aware matches). At the end of the scan, surface unresolved or
    multi-match candidates to the user in one consolidated message:

      "These mentions may want to be wikilinks:
         - 'Prisma AIRS Team' — no vault note found (write as plain text,
           create a stub, or specify a target?)
         - 'AIRS' — matches 3 notes (specify which, or leave plain?)
       Reply with link decisions or 'skip all' to proceed unchanged."

    The user (who knows which 'AIRS' is meant) makes the call; curator
    rewrites only the mentions the user confirms.

    Do NOT scan-and-rewrite autonomously. Do NOT issue one search per
    candidate inline (the per-candidate prompt would convert one write into
    dozens of confirmations).
```

**Eval criteria:**
- Skill score ≥ 96 (no regression)
- Item 3a present and explicitly composes obsidian-cli primitives (`search`, `aliases`) rather than reimplementing them
- Item 3a bounds the scan (code-fence skip, stop-list, multi-word preference, ~20 cap) and consolidates user-facing prompts into one end-of-scan message
- Smoke test (sandbox vault): write a 500-word note with 30 capitalized phrases — the gate runs in a single batch, surfaces one consolidated prompt, and never blocks per-candidate

#### B3. Schema-Change Guard (report 77162)

**Current state (§Write Boundaries, lines 83–87):**
The section covers zone-based write permission checks but does not block schema-creation requests (new fileClasses, new folder conventions, new templates).

**Proposed change — add a block to §Write Boundaries before the out-of-zone paragraph:**

```
**Schema-change guard** — before accepting any request, check whether it
involves:
- Defining or registering a new fileClass
- Establishing a new folder naming convention
- Designing a new template schema or Bases view from scratch

These are architect-territory. Refuse immediately and route explicitly:
  "Creating a new fileClass/folder convention/template schema is vault-architect
   work. I can handle content migration and metadata backfill after the architect
   establishes the schema."
Do NOT attempt the operation, even partially.
```

**Eval criteria:**
- Skill score ≥ 96 (no regression)
- Schema-change guard block present in §Write Boundaries
- Negative trigger in frontmatter `description:` already covers architect boundary — verify it's still consistent

---

### Pass C — vault-architect SKILL.md: Canonical Notation

**Target:** `plugins/archivist/skills/vault-architect/SKILL.md`

#### C1. Notation Hygiene for New Templates (report 77170)

**Current state (§Design Principles, lines 326–334):**
Design Principles cover linking discipline, folder philosophy, and aggregation patterns. No guidance on canonical notation for action items in templates. This leaves new templates inconsistent (numbered emoji lists vs bullet emoji vs markdown task lists).

**Scope note:** Report 77170 is a "nit" — one observation of notation inconsistency. The fix is **template hygiene for new work**, not a vault-wide retrofit policy. A vault-wide migration mandate exceeds the report's evidence base; if a stronger need emerges later, the canon can be expanded then.

**Proposed change — add to §Design Principles "Do:" list:**

```
**Notation hygiene for new templates** — when designing or revising a template,
pick one consistent notation for action items and document the choice in the
vault's System Guide. For action lists, prefer Obsidian-native markdown task
syntax: `- [ ]` (open) and `- [x]` (done) render as checkboxes in Obsidian core.
Extended task-state markers (`[/]`, `[?]`, `[!]`) depend on the Tasks community
plugin and may not render in vaults without it — only adopt them after
verifying the target vault has the plugin installed. Do NOT proactively
retrofit existing notes; existing inconsistency is acceptable until the user
requests cleanup.
```

**Also add to §Vault System Documentation (near end of section 10):**

```
- **Notation Conventions** — the notation choice used in this vault's new
  templates (see Design Principles). Record the chosen markers here so future
  template work is consistent. Plugin dependencies (e.g., Tasks plugin for
  extended task states) belong on this line.
```

**Eval criteria:**
- Skill score ≥ 94 (no regression; nit-level change unlikely to lift score)
- Notation hygiene block present in Design Principles "Do:" list
- Block restricts canonical markers to Obsidian-native `[ ]`/`[x]` unless plugin compatibility is verified
- System Guide section includes "Notation Conventions" entry

---

### Pass D — handoff Script + SKILL.md: Tmux Targeting Fixes

**Target:** `plugins/handoff/skills/handoff/scripts/handoff` + `plugins/handoff/skills/handoff/SKILL.md` + `plugins/handoff/skills/handoff/references/tmux-targeting.md`

#### D1. Regex — Allow `/` in Session Names; Reject Path-Shaped Targets (report 77186)

**Current state (script line 122):**
```bash
if [[ "$target" =~ ^[A-Za-z0-9_-]+:[0-9]+\.[0-9]+$ ]]; then
```
The session-name capture group `[A-Za-z0-9_-]+` does not allow `/`. tmux permits `/` in session names (common: `airs/something`, `project/feature`), causing handoff to reject valid explicit targets.

**Proposed change — broaden the regex *and* reject path-traversal shapes:**

A naive broadening to `^[A-Za-z0-9_./-]+:[0-9]+\.[0-9]+$` would admit pathological inputs like `../../../etc/passwd:0.0`, `./../session:1.0`, and leading-dash strings like `-/-:0.0` (which can be misparsed as flags by downstream tools). Use a tighter regex that disallows leading `-`, leading/trailing `/`, and embedded `..` / `./` sequences, plus a follow-up substring check:

```bash
# Anchored: first char must be alnum or underscore (no leading -, /, .).
if [[ "$target" =~ ^[A-Za-z0-9_][A-Za-z0-9_./-]*:[0-9]+\.[0-9]+$ ]]; then
  # Reject path-traversal-shaped session names.
  session_name="${target%%:*}"
  if [[ "$session_name" == *..* || "$session_name" == */./* || "$session_name" == */ ]]; then
    die "invalid tmux target: $target (session name contains path-traversal characters)"
  fi
  ...
```

Also update the error message in `die "invalid tmux target: $target …"` to explicitly state the accepted shape, and update `scripts/handoff --help` (sed block lines 3–28) to note that session names may contain `.`, `-`, `_`, `/` but must not begin with `-` or contain `..`.

**Eval criteria:**
- Skill score ≥ 98 (no regression)
- `echo "" | scripts/handoff --to tmux:airs/something:1.0 --filter '.*'` exits with code 2 (not code 1 / invalid-target) — i.e., fails at pane-lookup, not at regex validation
- Unit test: `echo "" | scripts/handoff --to tmux:../../../etc/passwd:0.0 --filter '.*'` exits with code 1 (invalid target) and the error message names the path-traversal reason
- Unit test: `echo "" | scripts/handoff --to tmux:-foo:0.0 --filter '.*'` exits with code 1 (leading dash rejected)
- Regex change present at line 122 with the traversal-check block immediately following

#### D2. `--filter-address` Flag for Pane Disambiguation (report 77194)

**Current state:**
The `--filter` flag (script lines 105–108) greps for the pattern against `pane_current_command` only (after the tab in the `list-panes` output). When multiple panes are running `claude`, `--filter claude` matches all of them and the script picks the first one — defeating the disambiguation feature the flag is supposed to provide. The documented workaround (use `--to tmux:<addr>` explicitly after running `tmux list-panes`) re-introduces the friction `--filter` was meant to eliminate.

**Proposed change — promote address-side filter as the primary fix:**

Add a `--filter-address <regex>` flag that greps the *address portion* (before the tab in the `list-panes` output), allowing `--filter-address "airs/something"` to target a specific session. The implementation is mechanically symmetric to the existing `--filter`:

```bash
# In the pane-discovery block (lines 105–108):
# Existing: filter on pane_current_command (after the tab)
candidates=$(tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}	#{pane_current_command}' \
  | awk -F'	' -v addr_filter="$filter_address" -v cmd_filter="$filter" '
      (addr_filter == "" || $1 ~ addr_filter) &&
      (cmd_filter == ""  || $2 ~ cmd_filter)
    { print $1 }')
```

Add CLI parsing for `--filter-address`, update `scripts/handoff --help` (sed block lines 3–28), and document both flags' interaction (combined filters AND together).

**Documentation update — `skills/handoff/SKILL.md` §Tmux Transport: What to Know**, add after the current `--filter claude` example:

```
**Disambiguating multiple claude panes:** when several panes run `claude`, use
`--filter-address <regex>` to pin by pane address. Example: `--filter claude
--filter-address "airs/something"` targets the claude pane in the
`airs/something` session. Combined filters AND together. Use
`tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}\t#{pane_current_command}'`
to see all available addresses.
```

In `references/tmux-targeting.md` (the pane discovery algorithm section), update the algorithm description to cover both filter axes.

**Eval criteria:**
- Skill score ≥ 98 (no regression)
- Script supports `--filter-address <regex>` and AND-composes with `--filter`
- Integration test: two panes running `claude`, one in session `a`, one in session `b` — `--filter claude --filter-address "^b:"` resolves to the pane in session `b`
- SKILL.md and references/tmux-targeting.md documentation updated to cover both filter axes

---

## Related upstream issues

Five reports from the same friction batch are **not** addressed by this plan; they have their own decision and tracking venue at `docs/plans/2026-06-05-003-archivist-friction-batch-decisions.md`:

- **Pass E (CLAUDE.md epistemic-hygiene rules)** — reports 77219, 77259, 77267. Three proposed rules for research summarization (preserve source URLs inline, hedge unverified compatibility claims, scope-check before generalizing). These are global cross-agent policy and warrant their own review path independent of the per-skill prompt edits in this plan. Decision pending Greg's input.
- **Pass E-companion (orchestrator-side input-volume rule)** — pairs with this plan's Pass A2 receiver-side guard. The sister doc tracks the orchestrator-side rule so the receiver and orchestrator sides of the same hygiene concern stay co-located. Decision pending.
- **Pass F (upstream Claude Code harness)** — reports 77202 (substantive teammate messages silently dropped) and 77210 (no auto-detection of stuck teammates). Not fixable in this repo; the sister doc tracks the escalation options (file an upstream issue / add a `CLAUDE.md` workaround note / record as a `docs/lessons/` known limitation). 77202 is labeled "blocker" — at minimum the workaround note or lessons entry is appropriate.

---

## Verification Plan

### Pass A — archivist agent
- Run `/as-improve` on `agents/archivist.md`
- Confirm overall score ≥ 93 (no regression from 93 baseline)
- System prompt quality sub-score must not drop below 95
- Smoke test (A1 Mode 1): "I expect this vault path to be readable in future sessions" → agent response shows the `permissions.allow` schema with `Read(/abs/path/**)` string entries
- Smoke test (A1 Mode 2): "I'm getting Read denied for vault path X and no prompt is appearing in this session" → agent recommends restart and explains that `settings.json` alone won't help in-session
- Smoke test (A2 trigger): spawn archivist via Agent tool with ~5000-token message + 0 file paths → soft-confirm fires, then refuse on ambiguous reply
- Smoke test (A2 negative): spawn archivist with ~5000-token message + 3 file paths + clear operations → guard does NOT fire (well-formed briefing passes)
- Smoke test (A3): meeting-extraction workflow completes → agent surfaces the External-System Handoffs offer to route via `attache:attache`

### Pass B — vault-curator
- Run `/ss-improve` on `skills/vault-curator/SKILL.md`
- Confirm score ≥ 96 (no regression)
- Smoke test (B1 absent value): ask curator to write `fileClass: Plan` when `Plan` is not in `_vault-profile.md` → refuses, names the gap
- Smoke test (B1 freshness): in the sandbox vault, architect registers fileClass `X` mid-session; curator immediately writes a note with `fileClass: X` → write succeeds (validates re-read-from-disk contract)
- Smoke test (B1 parsing): sandbox vault's `## Active fileClasses` rendered as a bulleted list with extra prose → curator parses the capitalized first-tokens; if empty, emits the documented warning and proceeds
- Smoke test (B2 scan): write a 500-word note with ~30 capitalized phrases — the gate runs in a single batch, surfaces one consolidated prompt, and never blocks per-candidate
- Smoke test (B3): ask curator to create a new fileClass → refuses, routes to architect

### Pass C — vault-architect
- Run `/ss-improve` on `skills/vault-architect/SKILL.md`
- Confirm score ≥ 94 (no regression; nit-level change)
- Manual check: notation hygiene block present in Design Principles "Do:" list
- Manual check: block restricts canonical markers to `[ ]`/`[x]` unless plugin compatibility is verified
- Manual check: System Guide "Notation Conventions" entry references plugin dependencies

### Pass D — handoff
- Unit test: `echo "" | bash -c 'source scripts/handoff; [[ "airs/something:1.0" =~ ^[A-Za-z0-9_][A-Za-z0-9_./-]*:[0-9]+\.[0-9]+$ ]] && echo pass || echo fail'` → `pass`
- Unit test (traversal): `echo "" | scripts/handoff --to tmux:../../../etc/passwd:0.0 --filter '.*'` → exits code 1 (invalid target), error names path-traversal reason
- Unit test (leading dash): `echo "" | scripts/handoff --to tmux:-foo:0.0 --filter '.*'` → exits code 1 (leading dash rejected)
- Integration: `echo "test payload" | scripts/handoff --to tmux:airs/something:1.0 --filter '.*'` → exits code 2 (pane not found), not code 1 (invalid target)
- Integration (D2): two panes running `claude`, one in session `a`, one in session `b` — `--filter claude --filter-address "^b:"` resolves to the pane in session `b`
- Run `/ss-improve` on `skills/handoff/SKILL.md`
- Confirm score ≥ 98 (no regression)
- Doc check: SKILL.md §Tmux Transport documents combined `--filter` / `--filter-address` use; `references/tmux-targeting.md` covers both filter axes

---

## Risks & Open Questions

- **Risk: A2 input-volume guard misclassifies a legitimate large briefing as a dump.** Mitigation: the trigger uses two AND-composed signals (token count AND low file-path count), and the soft-confirm path fires before refusal so the orchestrator can clarify intent in one turn. Well-formed briefings with explicit file paths pass through at any length because the path count is the dominant signal. Interactive sessions (non-subagent) are unaffected.
- **Risk: B1 fileClass gate fails when `_vault-profile.md` is absent or its `## Active fileClasses` section is empty/unparseable.** Mitigation: explicit "skip gate and warn" fallback for both cases; the curator emits a one-line warning and proceeds with the write rather than blocking. The freshness contract (re-read from disk per write) eliminates the stale-context failure mode flagged in pre-review.
- **Risk: D1 tighter regex still admits unusual valid tmux session names** (e.g., names containing `+` or whitespace). Mitigation: those names require explicit `--to tmux:<address>` targeting and the user can escape via tmux's native quoting. The traversal-rejection block closes the dangerous-input class; future widening can land via a follow-up if a real friction report surfaces.
- **Open: B2 stop-list and cap calibration.** The proposed ~20-candidate cap and the common-acronym stop-list (`API`, `JSON`, `YAML`, `HTTP`, `URL`) are starting points. After Pass B ships, monitor the rate of "skip-all" replies in the consolidated end-of-scan prompt — if users routinely skip-all, the heuristic is too coarse and needs revision.
- **Open: C1 architect-side template tightening.** B1's parse contract is more reliable if the architect template mandates a markdown-table shape for `## Active fileClasses`. Consider a follow-up architect-side change that prescribes the table shape and includes a one-line migration note. Tracked as a Pass C follow-up; not blocking.
- **Open: External-system handoffs beyond meeting extraction.** A3 introduces the "External-System Handoffs" table for the meeting → attache routing. If other curator workflows surface external destinations (e.g., write-to-Slack, push-to-Notion), the table should grow. No need to anticipate now — add rows as workflows emerge.

Non-archivist risks and open questions (CLAUDE.md hygiene, upstream harness escalation) are tracked in the sister decision-log doc.
