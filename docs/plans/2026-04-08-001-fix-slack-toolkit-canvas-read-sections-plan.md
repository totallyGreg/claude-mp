---
title: "fix: Correct canvas read path and expose sections lookup as first-class command"
type: fix
status: active
date: 2026-04-08
---

# fix: Correct canvas read path and expose sections lookup as first-class command

## Overview

`slacker.py canvas read` is broken for new-type (non-quip) canvases. Its non-quip path calls `canvases.sections.lookup` expecting content, but the API only returns section IDs — content is always silently empty. Separately, `canvases.sections.lookup` has no dedicated CLI command, forcing callers to recreate canvases wholesale instead of editing sections in place.

This plan fixes the read path and properly exposes section lookup as a first-class command to enable atomic section edits. Several related improvements landed in the same session (delete, channel-create, access set/delete, comprehensive api-reference) and are committed alongside these changes.

## Problem Frame

Two distinct bugs sharing the same root cause — `canvases.sections.lookup` was misused as a content-read mechanism instead of being correctly exposed as a section-discovery tool:

1. **Broken read:** `cmd_canvas_read` branches on filetype. The quip path works (downloads HTML via `url_private`, converts to markdown). The non-quip path calls `canvases.sections.lookup` with `criteria: {}`, reads `section.get("markdown")` which is never present, and silently emits nothing. A `url_private` fallback exists in the code but is gated behind an API error that never fires.

2. **Missing command:** There is no `canvas sections lookup` command, so callers have no way to discover section IDs for targeted `canvases.edit` operations. The only workaround has been creating entire new canvases.

**Verified from Slack API docs (fetched 2026-04-08):**
- No `canvases.read` or `canvases.get` API exists
- `canvases.sections.lookup` response: `{"ok": true, "sections": [{"id": "temp:C:<hex>"}]}` — IDs only, no content
- `files.info` + `url_private` is the only mechanism for reading canvas content; documented working for quip canvases; behavior for new-type canvases is undocumented

## Requirements Trace

- R1. `canvas read` must not silently emit nothing for new-type canvases
- R2. `canvas read` must try `url_private` regardless of canvas type before failing
- R3. When `url_private` is absent or non-functional, `canvas read` must fail with a clear, honest error and emit available metadata as JSON
- R4. `canvas sections lookup` must be a first-class CLI command exposing the full `canvases.sections.lookup` criteria
- R5. The atomic edit workflow (lookup section → replace section) must be documented clearly
- R6. Documentation must not claim `canvases.sections.lookup` returns content

## Scope Boundaries

- Does not add a canvas export/download feature beyond what `url_private` provides
- Does not implement content parsing for non-HTML `url_private` responses beyond emitting raw content with a warning
- Does not change any of the other new commands added in this session (delete, channel-create, access set/delete)

## Context & Research

### Relevant Code and Patterns

- `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py` — `cmd_canvas_read` (lines ~403–444), `_downgrade_headings` helper, `slack_download`, `HtmlToMarkdown`
- `plugins/slack-toolkit/skills/slack-toolkit/SKILL.md` — Canvas CLI reference section
- `plugins/slack-toolkit/skills/slack-toolkit/references/api-reference.md` — Canvas API method table
- `plugins/slack-toolkit/skills/slack-toolkit/references/canvas-operations.md` — Size limits, quip vs new-type, update patterns

### Verified API Facts

- `canvases.sections.lookup` valid `criteria` fields: `section_types` (`h1`, `h2`, `h3`, `any_header`) and `contains_text`. Both optional; combined as AND.
- `canvases.sections.lookup` response contains only `id` per section — no text, markdown, or content of any kind
- `files.info` → `url_private` is the only documented path to canvas content
- New-type canvas `url_private` behavior: undocumented, must be treated as speculative until tested against a real workspace

### Related Session Work (Landing in Same Commit)

- `_downgrade_headings` extracted as shared helper (already done)
- `canvas delete`, `canvas channel-create`, `canvas access set/delete` commands (already done)
- Comprehensive `api-reference.md` with all 7 Canvas API methods (already done)

## Key Technical Decisions

- **Unify read path around `url_private`:** Remove the filetype branch entirely for content fetching. Call `files.info`, extract `url_private`, attempt download regardless of filetype. Let content format (HTML vs other) determine parsing, not filetype label.
- **Content format detection by inspection:** If content starts with `<`, route through `HtmlToMarkdown`. Otherwise emit raw with a warning. This handles both quip and any future non-HTML format transparently.
- **Honest failure with metadata JSON:** When `url_private` is absent, print a clear error to stderr and emit a JSON object with available metadata (canvas_id, title, filetype, permalink) to stdout so callers can still identify the canvas.
- **`canvas sections lookup` as a sibling subcommand:** Add it at the same level as `read`, `create`, `update`, etc. under `canvas`. Arguments: positional `canvas_id`, optional `--section-types` (nargs=`+`), optional `--contains-text`. Output: JSON array of section IDs.

## Open Questions

### Resolved During Planning

- **Does `canvases.sections.lookup` return content?** No — confirmed from official Slack API docs. Response is `{"sections": [{"id": "..."}]}` only.
- **Should we keep the filetype check at all?** Keep it for metadata/logging (emit filetype in the honest-failure JSON), but do not use it to gate the `url_private` attempt.
- **What `nargs` for `--section-types`?** Use `nargs='+'` matching the `--channel-ids`/`--user-ids` pattern already in the file.

### Deferred to Implementation

- **Does new-type canvas `url_private` return HTML or something else?** Cannot know without running against a real workspace. Implementation should handle both cases and log what was received.
- **Is `url_private` present in `files.info` for all new-type canvas workspaces?** Unknown. Implementation must handle its absence gracefully per R3.

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

**Revised `canvas read` decision flow:**

```
files.info(canvas_id)
  → url_private present?
      No  → stderr: "No read API available for this canvas type"
           → stdout: JSON {canvas_id, title, filetype, permalink}
           → exit(EXIT_API)
      Yes → slack_download(url_private)
           → content starts with '<'?
               Yes → html_to_markdown(content) → print
               No  → stderr: warn "unknown format, emitting raw (filetype: <X>)"
                   → stdout: content as-is
```

**New `canvas sections lookup` command:**

```
canvas sections lookup <canvas_id> [--section-types h1 h2 ...] [--contains-text TEXT]
  → build criteria dict from args (omit keys with no value)
  → canvases.sections.lookup(canvas_id, criteria)
  → stdout: JSON {"sections": [{"id": "..."}]}
```

**Atomic edit workflow (enabled by new command):**

```
canvas sections lookup F123 --section-types h2 --contains-text "Status"
  → {"sections": [{"id": "temp:C:abc123"}]}

canvas update F123 --replace temp:C:abc123 --content-file new-status.md
  → {"ok": true}
```

## Implementation Units

- [ ] **Unit 1: Fix `cmd_canvas_read` — unify around `url_private`**

**Goal:** Remove the broken `canvases.sections.lookup` read path; replace with a `url_private`-first approach that works for both quip and new-type canvases, fails honestly when `url_private` is absent.

**Requirements:** R1, R2, R3

**Dependencies:** None

**Files:**
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

**Approach:**
- Replace the entire else-branch (lines ~421–444) with the unified `url_private` flow
- Remove filetype-based branching for content fetching; keep `filetype` variable only for error/metadata output
- Detect content format by inspecting first character rather than trusting filetype label
- Emit JSON metadata on honest failure so callers have the canvas title and permalink

**Patterns to follow:**
- `slack_download` and `html_to_markdown` are already correct — reuse unchanged
- `HtmlToMarkdown` parser handles quip HTML — no changes needed there
- Error output pattern: stderr message + stdout JSON + `sys.exit(EXIT_API)` (see `cmd_canvas_create` error handling)

**Test scenarios:**
- Happy path: quip canvas with `url_private` returning HTML → stdout is markdown
- Happy path: new-type canvas with `url_private` returning HTML → stdout is markdown (same path)
- Edge case: new-type canvas with `url_private` returning non-HTML content → stderr warning, stdout raw content
- Error path: `files.info` returns no `url_private` → stderr error + stdout JSON metadata + exit(EXIT_API)
- Edge case: empty canvas (url_private returns empty body) → stdout empty string, no crash

**Verification:**
- `canvas read` on a known quip canvas produces readable markdown
- `canvas read` on a canvas with no `url_private` prints a meaningful error and JSON metadata, exits non-zero
- The broken `canvases.sections.lookup` call is absent from `cmd_canvas_read`

---

- [ ] **Unit 2: Add `canvas sections lookup` command**

**Goal:** Expose `canvases.sections.lookup` as a first-class CLI command so callers can discover section IDs for targeted `canvases.edit` operations without recreating canvases.

**Requirements:** R4, R5

**Dependencies:** None (can land in any order with Unit 1)

**Files:**
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

**Approach:**
- Add `cmd_canvas_sections_lookup(args)` function
- Build `criteria` dict from args — include `section_types` only if provided, include `contains_text` only if provided (omit empty keys, not send empty values to API)
- Call `slack_post_json("canvases.sections.lookup", token, {"canvas_id": ..., "criteria": ...})`
- Print result JSON to stdout
- Add `canvas sections` as a nested subparser group with `lookup` as its subcommand, following the `canvas access` pattern already in the file
- Parser: `canvas_id` positional, `--section-types nargs='+'` with choices `[h1, h2, h3, any_header]`, `--contains-text`

**Patterns to follow:**
- `canvas access` nested subparser pattern (already in `build_parser()`)
- `slack_post_json` call pattern from `cmd_canvas_create`, `cmd_canvas_channel_create`
- `--channel-ids nargs='+'` argument pattern from `cmd_canvas_access_set`

**Test scenarios:**
- Happy path: lookup with `--section-types h2` → stdout JSON with section IDs
- Happy path: lookup with `--contains-text "Status"` → returns matching sections
- Happy path: no criteria → returns all discoverable sections
- Edge case: canvas with no matching sections → `{"sections": []}` (not an error)
- Error path: invalid canvas_id → `slack_post_json` exits via EXIT_API

**Verification:**
- `slacker.py canvas sections --help` shows `lookup` subcommand
- `slacker.py canvas sections lookup F123 --section-types h2` returns JSON with `sections` array
- Section IDs returned are usable with `canvas update --replace`

---

- [ ] **Unit 3: Update documentation**

**Goal:** Remove false claims about `canvases.sections.lookup` as a read mechanism; document the actual read limitation and the correct atomic edit workflow.

**Requirements:** R5, R6

**Dependencies:** Units 1 and 2 (document what actually exists)

**Files:**
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/SKILL.md`
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/references/api-reference.md`
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/references/canvas-operations.md`
- Modify: `plugins/slack-toolkit/README.md`

**Approach:**

*SKILL.md:*
- Add `canvas sections lookup` to the Canvas CLI reference with usage example
- Add the atomic edit workflow example (lookup → replace)
- Update `canvas read` docs to describe the `url_private` approach and honest-failure behavior
- Remove any remaining text implying sections.lookup returns content

*api-reference.md:*
- Add a "Canvas Read Limitation" note: no official read API exists; `url_private` via `files.info` is the only mechanism; new-type canvas behavior is undocumented
- Clarify `canvases.sections.lookup` purpose: section ID discovery for targeted edits only

*canvas-operations.md:*
- Add a "Reading Canvas Content" section explaining the limitation, the `url_private` mechanism, and what to expect for quip vs new-type canvases

**Test scenarios:**
- Test expectation: none — documentation change only

**Verification:**
- `canvas read` docs accurately describe what the command does and when it fails
- `canvas sections lookup` appears in SKILL.md CLI reference
- No remaining references to `canvases.sections.lookup` as a content source

---

- [ ] **Unit 4: Skillsmith eval, version bump, and marketplace sync**

**Goal:** Record all changes in the skill's version history, bump to 1.5.0, and sync the marketplace.

**Requirements:** Plugin validation workflow (from memory/feedback)

**Dependencies:** Units 1, 2, 3

**Files:**
- Modify: `plugins/slack-toolkit/skills/slack-toolkit/SKILL.md` (version)
- Modify: `plugins/slack-toolkit/.claude-plugin/plugin.json` (version)
- Modify: `plugins/slack-toolkit/README.md` (version history rows for 1.3.0, 1.4.0, 1.5.0)
- Modify: `.claude-plugin/marketplace.json`

**Approach:**
- Run `uv run .../evaluate_skill.py ... --explain` to verify 98/100 holds
- Run `uv run .../evaluate_skill.py ... --update-readme` to refresh Current Metrics
- Run `uv run .../evaluate_skill.py ... --export-table-row --version 1.5.0` for the version row
- Bump `metadata.version` in SKILL.md and `version` in plugin.json to `1.5.0` (MINOR — new capability: sections lookup command; fix: canvas read unified path)
- Add version rows for 1.3.0 and 1.4.0 (already landed but not yet committed) and 1.5.0
- Run `python3 scripts/sync.py` to sync marketplace.json
- Commit all changes across the full session (1.3.0 bug fix, 1.4.0 new commands, 1.5.0 read fix + sections lookup)

**Test scenarios:**
- Test expectation: none — version/metadata change only

**Verification:**
- SKILL.md and plugin.json both show `1.5.0`
- marketplace.json shows `slack-toolkit: 1.5.0`
- Skillsmith eval score is 98/100 or better

## System-Wide Impact

- **Interaction graph:** No callbacks or middleware affected — slacker.py is a standalone CLI
- **Error propagation:** `canvas read` failure now exits via `EXIT_API` with JSON metadata on stdout; callers checking exit code will correctly detect failure
- **API surface parity:** `canvas sections lookup` output format (JSON with `sections` array) matches the raw Slack API response — no transformation needed
- **Unchanged invariants:** All existing commands (`read` for quip, `create`, `update`, `rewrite`, `probe`, `delete`, `channel-create`, `access set/delete`) are unchanged in behavior
- **Integration coverage:** The `canvas sections lookup → canvas update --replace` workflow crosses two commands; verify the section ID format returned by lookup is accepted by update's `--replace` argument

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| New-type canvas `url_private` returns non-HTML content | Detect by inspection, emit raw with warning — honest and non-crashing |
| New-type canvas has no `url_private` at all | Honest failure path (R3) handles this explicitly |
| `canvases.sections.lookup` with empty criteria times out or errors on large canvases | Accept Slack rate/error behavior; `slack_post_json` exits cleanly via EXIT_API |
| Breaking change: `canvas read` now exits non-zero when it previously silently succeeded | Previous silent-empty behavior was already broken — honest failure is strictly better |

## Sources & References

- Slack Canvas API docs: https://docs.slack.dev/reference/methods?family=canvases (verified 2026-04-08)
- `canvases.sections.lookup` response: `{"ok": true, "sections": [{"id": "temp:C:<hex>"}]}` — IDs only
- Related session work: `canvas delete`, `canvas channel-create`, `canvas access set/delete` (already implemented, same commit)
