---
title: "feat: Add slack-toolkit Python CLI for Slack API access"
type: feat
status: completed
date: 2026-03-25
origin: docs/brainstorms/2026-03-12-slack-toolkit-skill-brainstorm.md (from airs/claude-skills repo)
supersedes: airs/claude-skills/docs/plans/2026-03-12-001-feat-slack-toolkit-skill-plan.md
---

# feat: Add slack-toolkit Python CLI for Slack API access

## Overview

Implement `slacker.py` — a stdlib-only Python CLI for the existing `plugins/slack-toolkit/` plugin. The plugin scaffolding (plugin.json, SKILL.md, api-reference.md, README.md) already exists; only the CLI implementation and marketplace registration remain.

## Problem Frame

The official Slack MCP plugin (`slackapi/slack-mcp-plugin`) has two issues:

1. **MCP unavailability**: Remote server at `mcp.slack.com` requires OAuth + workspace admin approval; not always connected
2. **Missing operations**: No Canvas read/update (only create), no reactions (confirmed: "the MCP tools can't add reactions")

A live session (2026-03-26) attempting to read canvas `F0ANA2K9QAU` revealed a third issue: **two distinct canvas types** exist in Slack with incompatible APIs, and neither the MCP plugin nor the existing SKILL.md documentation accounts for this.

## Requirements Trace

- R1. Canvas read works for both legacy quip-type and new Canvas API canvases
- R2. Canvas create produces new canvases via `canvases.create`
- R3. Canvas update works via `canvases.edit` (new-type canvases; quip compatibility TBD)
- R4. Reactions can be added and removed
- R5. Thread retrieval with cursor-based pagination
- R6. Channel history retrieval with cursor-based pagination
- R7. Slack URL parsing to channel + timestamp
- R8. All operations use POST with form-encoded body (enterprise grid compatible)
- R9. Stdlib-only Python with PEP 723 metadata (zero external dependencies)
- R10. Token resolution: env var first, `keychainctl` fallback
- R11. Plugin registered in marketplace.json

## Scope Boundaries

- No message sending, search, or user profile operations (MCP covers these)
- No Canvas delete (low value, high risk)
- No interactive OAuth flow (tokens come from env vars or keychain)
- No quip canvas in-place updates — use `canvas rewrite` to migrate quip canvases to proper new-type format

## Context & Research

### Relevant Code and Patterns

- **Plugin scaffolding already exists**: `plugins/slack-toolkit/` has plugin.json (v1.0.0), SKILL.md, api-reference.md, README.md — scripts dir is empty
- **Python CLI pattern**: ai-risk-mapper scripts use PEP 723 (`# /// script`), argparse, `uv run`, stderr for errors (see `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/cli_risk_search.py`)
- **marketplace.json**: at `.claude-plugin/marketplace.json` — slack-toolkit is NOT yet listed; needs entry with `source: "./plugins/slack-toolkit"`, `category: "productivity"`
- **SKILL.md conventions**: frontmatter with name, metadata.version, description; CLI reference with subcommand tables; references dir for supplementary docs

### Enterprise Grid Constraints (from CLAUDE.md)

All conversation endpoints require POST with form-encoded body — GET returns `not_authed` on enterprise grids. `auth.test` is the exception. JSON responses may contain control characters requiring `strict=False`.

## Key Technical Decisions

- **Single CLI over multiple scripts**: One `slacker.py` with argparse subcommands. Avoids duplicating token resolution logic. Follows ai-risk-mapper precedent.
- **Python over bash**: Document review identified 3 blockers in the original bash plan: `$@` arg collision, `curl -H` token exposure in `ps aux`, inability to read `Retry-After` header. Python stdlib resolves all three.
- **Stdlib-only**: No external dependencies. Uses `urllib.request`, `html.parser`, `json`, `argparse`. PEP 723 declares zero deps.
- **Dual canvas read path**: Detect canvas type via `files.info` filetype, then route to quip (HTML download + conversion) or new Canvas API (`canvases.sections.lookup`).
- **New-type only for writes**: `canvas create` and `canvas update` always use the `canvases.*` API, ensuring proper canvas type. To "rewrite" a quip canvas, create a new proper-type canvas with the content. This prevents perpetuating the legacy format.
- **HTML→markdown via stdlib**: Use `html.parser.HTMLParser` subclass to convert quip HTML to markdown. Must handle tables, headings, lists, code blocks, bold/italic, links.

## Open Questions

### Resolved During Planning

- **Why not use html2text?** Requires external dependency, violating R9 (stdlib-only). stdlib `html.parser` is sufficient for the limited HTML subset Slack canvases produce.
- **Which token for canvas read?** User token (`xoxp-`) — requires `files:read` scope for quip-type and `canvases:read` for new-type. Bot tokens (`xoxb-`) cannot be granted `canvases:read`/`canvases:write` scopes — canvas ops must enforce user token.
- **How to handle quip canvas writes?** Dual-path read, new-type only write. All creates and updates go through `canvases.*` API to ensure proper canvas type. To rewrite a quip canvas, create a new canvas with the converted content. This avoids perpetuating the legacy quip format.
- **`canvases.sections.lookup` criteria structure?** Accepts `section_types` (array: `"h1"`, `"h2"`, `"h3"`, `"any_header"`) and `contains_text` (substring match). Returns temporary section IDs with `temp:` prefix.
- **`canvases.edit` on quip canvases?** Confirmed: does not work. Returns `canvas_not_found` or `invalid_canvas`. Quip canvases are read-only via the API — use `canvas rewrite` to migrate.
- **Canvas API content-type?** Canvas endpoints (`canvases.*`) use `application/json` with JSON body, unlike conversation endpoints which require `application/x-www-form-urlencoded`. `slacker.py` needs two request methods: `slack_post()` (form-encoded) and `slack_json()` (JSON body).
- **Tables in Canvas API markdown?** Not supported in the markdown subset for API-created canvases. Tables exist only in quip-type canvases (HTML). This means `canvas create` and `canvas rewrite` output will render tables as text, not pipe-delimited tables.

### Deferred to Implementation

- **HTML edge cases**: Exact HTML structures Slack uses for nested lists, code blocks with language hints, and complex table layouts. Will be resolved by testing against real canvases.

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification.*

```
slacker.py
├── Token resolution (env var → keychainctl → prefix validation → auth.test)
├── slack_post(method, token, **params) → dict    # POST form-encoded (conversation endpoints)
├── slack_json(method, token, payload) → dict     # POST JSON (canvas endpoints)
├── slack_download(url, token) → str              # Authenticated GET for url_private
├── HtmlToMarkdown(HTMLParser)                     # Converts quip HTML → markdown
│
├── canvas read <id>
│   ├── files.info → check filetype
│   ├── if quip: slack_download(url_private) → HtmlToMarkdown → stdout
│   └── if canvas: canvases.sections.lookup → format sections → stdout
├── canvas create <title> [--content/--content-file]
│   └── canvases.create with document_content
├── canvas update <id> [--append/--replace]
│   └── canvases.edit with changes array
│
├── react/unreact <channel> <ts> <emoji>
│   └── reactions.add / reactions.remove
├── thread <channel> <ts> [--limit]
│   └── conversations.replies with cursor pagination
├── history <channel> [--limit]
│   └── conversations.history with cursor pagination
└── parse-url <url>
    └── Regex extract channel + timestamp conversion
```

## Implementation Units

- [ ] **Unit 1: Core CLI framework + token resolution**

  **Goal:** Establish the CLI entry point with argparse, token resolution, and the shared `slack_post()` / `slack_download()` helpers.

  **Requirements:** R8, R9, R10

  **Dependencies:** None

  **Files:**
  - Create: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - PEP 723 header with zero dependencies
  - argparse with subparsers for each command group
  - Token resolution: check env var → `keychainctl get` fallback → validate prefix (`xoxp-`/`xoxb-`) → `auth.test` on first use
  - `slack_post()`: POST form-encoded via `urllib.request` for conversation/file endpoints
  - `slack_json()`: POST JSON via `urllib.request` for canvas endpoints (`canvases.*`)
  - Both: `json.loads(strict=False)`, check `ok` field, raise on error
  - `slack_download()`: authenticated GET via `urllib.request` for `url_private` content
  - 429 retry: read `Retry-After` from response headers, sleep, retry once
  - Canvas commands must enforce user token (`xoxp-`) — bot tokens lack canvas scopes
  - Exit codes: 0=success, 1=usage, 2=auth, 3=API, 4=rate-limited

  **Patterns to follow:**
  - `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/cli_risk_search.py` — PEP 723, argparse, stderr errors
  - `plugins/skillsmith/skills/skillsmith/scripts/evaluate_skill.py` — complex subcommand structure

  **Test scenarios:**
  - Missing token → exit 2 with stderr message
  - Invalid prefix (e.g., `xoxs-`) → exit 2
  - `auth.test` failure → exit 2 with API error detail
  - Successful POST returns parsed JSON
  - HTTP 429 → retry after `Retry-After` seconds

  **Verification:**
  - `python3 slacker.py --help` shows all subcommands
  - `python3 slacker.py canvas read F0TEST` with valid token reaches the API (may fail on bad ID, but proves token flow works)

- [ ] **Unit 2: HTML→markdown converter**

  **Goal:** Convert quip canvas HTML to clean markdown using stdlib only.

  **Requirements:** R1, R9

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - Subclass `html.parser.HTMLParser` as `HtmlToMarkdown`
  - Track element stack for context-aware conversion
  - Handle: `<h1>`–`<h3>` → `#`–`###`, `<b>`/`<strong>` → `**`, `<i>`/`<em>` → `_`, `<code>` → backticks, `<a href>` → `[text](url)`, `<ul>/<ol>/<li>` → bullets/numbers, `<table>/<tr>/<td>` → pipe-delimited markdown tables, `<hr>` → `---`, `<p>` → double newline
  - Slack canvas tables use simple `<table><tr><td>` without `<thead>/<th>` — first row becomes header with separator

  **Patterns to follow:**
  - stdlib `html.parser` documentation
  - Real canvas HTML from session (canvas `F0ANA2K9QAU` provides test data)

  **Test scenarios:**
  - Simple heading + paragraph HTML → clean markdown
  - Table with 3 columns → pipe-delimited markdown table with header separator
  - Nested bold/italic inside table cells
  - Code blocks with backtick content
  - Empty cells and special characters (`&amp;`, `&lt;`)

  **Verification:**
  - Convert the HTML from canvas `F0ANA2K9QAU` and compare to expected markdown output
  - Tables render correctly when pasted into a markdown preview

- [ ] **Unit 3: Canvas read (dual-path)**

  **Goal:** Implement `canvas read` that works for both quip and new Canvas API canvases.

  **Requirements:** R1, R8

  **Dependencies:** Unit 1, Unit 2

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - Call `files.info` with `file=<canvas_id>` to get metadata
  - Check `filetype` field:
    - `quip` → download `url_private` via `slack_download()` → pipe through `HtmlToMarkdown` → output markdown
    - Other → call `canvases.sections.lookup` with canvas_id and criteria → format sections as markdown
  - Output unified markdown to stdout regardless of type
  - Required scopes: `files:read` (quip), `canvases:read` (new)

  **Test scenarios:**
  - Read quip canvas `F0ANA2K9QAU` → returns clean markdown with tables
  - Read new-type canvas (create one first via Unit 4) → returns markdown sections
  - Non-existent canvas ID → exit 3 with API error
  - Canvas without read permission → exit 3 with `not_allowed`

  **Verification:**
  - `python3 slacker.py canvas read F0ANA2K9QAU` returns readable markdown
  - Output can be piped to a file and opened as valid markdown

- [ ] **Unit 4: Canvas create + update**

  **Goal:** Implement `canvas create` and `canvas update` subcommands.

  **Requirements:** R2, R3

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - `canvas create <title>`: accept `--content "markdown"` or `--content-file /path`, call `canvases.create` with `document_content: {type: "markdown", markdown: content}`. Always produces new-type canvases.
  - `canvas update <id>`: accept `--append "markdown"` (insert_at_end) or `--replace <section_id> --content "markdown"` (replace), call `canvases.edit` with changes array. Only works on new-type canvases.
  - `canvas rewrite <id>`: read a quip canvas (via Unit 3), create a new proper-type canvas with the converted markdown content. Output the new canvas ID. This is the migration path for legacy canvases.
  - If `canvas update` is called on a quip canvas, warn the user and suggest `canvas rewrite` instead.

  **Test scenarios:**
  - Create canvas with inline content → returns new canvas ID (new-type)
  - Create canvas from file → reads file, creates canvas
  - Append to new-type canvas → content appears at end
  - Replace section in new-type canvas → content updated
  - Update on quip canvas → warns user, suggests rewrite
  - Rewrite quip canvas → creates new canvas with converted content

  **Verification:**
  - Created canvas visible in Slack with correct content
  - Updated canvas shows changes in Slack

- [ ] **Unit 5: Reactions**

  **Goal:** Implement `react` and `unreact` subcommands.

  **Requirements:** R4

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - `react <channel> <ts> <emoji>` → `reactions.add`
  - `unreact <channel> <ts> <emoji>` → `reactions.remove`
  - Emoji name without colons (e.g., `thumbsup` not `:thumbsup:`)
  - Required scope: `reactions:write`

  **Test scenarios:**
  - Add reaction to a message → reaction appears
  - Remove reaction → reaction removed
  - Already-reacted → API returns `already_reacted` (handle gracefully)
  - Invalid emoji name → exit 3

  **Verification:**
  - Reaction visible on message in Slack after `react`
  - Reaction removed after `unreact`

- [ ] **Unit 6: Thread + history + URL parsing**

  **Goal:** Implement thread retrieval, channel history, and URL parsing.

  **Requirements:** R5, R6, R7

  **Dependencies:** Unit 1

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/scripts/slacker.py`

  **Approach:**
  - `thread <channel> <ts>`: `conversations.replies` with cursor-based pagination, `--limit N` (default 200, cap 1000)
  - `history <channel>`: `conversations.history` with cursor pagination, `--limit N` (default 100, cap 1000)
  - `parse-url <url>`: regex to extract channel and timestamp from Slack URL formats; timestamp: strip `p` prefix, insert `.` before last 6 digits
  - `--bot` flag to use bot token instead of user token
  - Output: JSON array of messages to stdout

  **Test scenarios:**
  - Thread with >200 messages → pagination collects all
  - Thread with 0 replies → returns parent message only
  - `--limit 5` → returns at most 5 messages
  - URL with `thread_ts` query param → extracts parent TS
  - URL without thread → extracts message TS
  - Invalid URL format → exit 1

  **Verification:**
  - Thread retrieval returns all messages in order
  - `parse-url` output matches expected channel + timestamp

- [ ] **Unit 7: SKILL.md + api-reference.md updates**

  **Goal:** Update existing docs to reflect dual canvas types, actual CLI invocation paths, and scope requirements.

  **Requirements:** R1 (documentation)

  **Dependencies:** Units 1–6

  **Files:**
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/SKILL.md`
  - Modify: `plugins/slack-toolkit/skills/slack-toolkit/references/api-reference.md`

  **Approach:**
  - Add dual canvas type documentation to SKILL.md (quip vs new Canvas API)
  - Add `files.info` and `files:read` scope to api-reference.md
  - Update CLI invocation examples to use `${CLAUDE_PLUGIN_ROOT}` prefix
  - Document the `--bot` flag
  - Add `canvases.sections.lookup` criteria findings from testing
  - Note quip canvas update limitations if discovered

  **Test scenarios:**
  - SKILL.md under 300 lines and under 2000 tokens
  - All CLI subcommands documented with examples

  **Verification:**
  - SKILL.md accurately reflects implemented behavior
  - No undocumented subcommands or flags

- [ ] **Unit 8: Marketplace registration**

  **Goal:** Add slack-toolkit to marketplace.json.

  **Requirements:** R11

  **Dependencies:** Units 1–7

  **Files:**
  - Modify: `.claude-plugin/marketplace.json`

  **Approach:**
  - Add entry: `{name: "slack-toolkit", description: "...", category: "productivity", version: "1.0.0", author: {...}, source: "./plugins/slack-toolkit"}`
  - Bump marketplace metadata.version if needed

  **Patterns to follow:**
  - Existing entries in marketplace.json (e.g., omnifocus-manager, pkm-plugin)

  **Verification:**
  - `jq '.plugins[] | select(.name == "slack-toolkit")' .claude-plugin/marketplace.json` returns the entry

## System-Wide Impact

- **Interaction graph:** SKILL.md trigger conditions must deconflict with the official Slack MCP plugin. The skill should only activate when MCP is unavailable or for Canvas/reaction operations MCP cannot perform.
- **Token exposure:** `slacker.py` keeps tokens in-process via `urllib.request` — no subprocess exposure. Tokens are never logged to stdout.
- **API surface parity:** Thread and history operations overlap with MCP's `slack_read_thread`/`slack_read_channel`. The `--bot` flag covers both token types.
- **Rate limiting:** Single 429 retry with `Retry-After` header. Hard cap at 1000 messages prevents runaway pagination. No concurrent API calls.

## Risks & Dependencies

| Risk | Impact | Mitigation |
|------|--------|------------|
| Token lacks Canvas scopes | Canvas operations fail | Verify scopes early with `auth.test`; document required scopes |
| Two canvas types require dual read path | Increased implementation complexity | Detect via `files.info` filetype; both paths share the same output format |
| Quip HTML→markdown fidelity | Tables or nested content may lose formatting | Test against real canvases; the HTML subset is limited |
| `canvases.sections.lookup` criteria unclear | Read may not return expected sections | Defer to implementation; test with real canvases |
| Quip canvas rewrite loses original URL/references | Users sharing the old canvas link won't see the new one | Output both old and new IDs; user can manually redirect |
| Rate limiting on pagination | Operations fail mid-page | 429 retry + hard cap at 1000 messages |

## Sources & References

- **Origin brainstorm:** airs/claude-skills/docs/brainstorms/2026-03-12-slack-toolkit-skill-brainstorm.md
- **Document review:** 5-agent review identified 3 P0 blockers in original bash plan
- **Python CLI pattern:** `plugins/ai-risk-mapper/skills/ai-risk-mapper/scripts/cli_risk_search.py`
- **Credential pattern:** `skills/confluence-pages/SKILL.md`
- **Official Slack MCP plugin:** `github.com/slackapi/slack-mcp-plugin` — tool catalog and gap analysis
- **Enterprise grid patterns:** user's `.claude/CLAUDE.md` (Slack API section)
- **Canvas dual-type discovery (2026-03-26):** Live session reading canvas `F0ANA2K9QAU` — discovered quip-type canvases use `files.info` + `url_private` (HTML), not `canvases.*` API
