# Brainstorm: OmniFocus CLI via Omni Automation Script URLs

**Date:** 2026-03-09
**Status:** Draft
**Skill:** omnifocus-manager

## What We're Building

A thin `omnifocus` CLI wrapper that replaces the current JXA/osascript execution model with Omni Automation script URLs (`omnifocus://localhost/omnijs-run?script=...&arg=...`). The CLI will provide clean ergonomics for interacting with OmniFocus tasks and projects from Claude Code, similar to how the `obsidian` CLI interacts with a running Obsidian instance.

### Problems This Solves

1. **No reliable task completion** -- Both `complete` and `update --completed true` fail silently or with permissions errors via JXA. The Omni Automation API running inside OmniFocus has full access.
2. **Skill/script command mismatch** -- `ofo-info.md` references `task-info` but the actual JXA script command is `info`. A CLI wrapper eliminates this drift.
3. **Verbose invocation pattern** -- Every command currently requires `cd <plugin-root> && osascript -l JavaScript scripts/manage_omnifocus.js <action> --flags`. A CLI reduces this to `omnifocus info --id <id>`.
4. **No URL scheme handler** -- `omnifocus://` URLs require manual parsing in each skill. The CLI can handle them natively.

## Why This Approach

### Reusable Script Actions via URL

The `omnijs-run` URL scheme supports an `&arg=` parameter that enables **reusable scripts**: the script body is approved once by the user, and changing `&arg=` does not trigger re-approval. This means we can create a small set of stable "action scripts" (~5-8) that each get approved once, then the CLI passes task IDs and data as arguments.

**Key advantages over JXA/osascript:**
- Scripts run **inside OmniFocus** with full API access (no JXA permissions issues)
- Uses the modern Omni Automation API (cross-platform, direct property access)
- No JXA bridge -- scripts execute natively in OmniFocus's JavaScript context
- The `&arg=` pattern keeps scripts stable while data varies

**Trade-offs:**
- One-time per-script approval required (user must enable external scripts + approve each action script)
- Different API surface than JXA (`flattenedTasks` accessed differently, no `app.defaultDocument`)
- Fire-and-forget `open` command -- need a return mechanism for read operations

### Data Return Mechanism

For read operations (`info`, `search`, `today`), the script writes JSON to `Pasteboard.general.string`. The CLI reads via `pbpaste`. File I/O is not available due to OmniFocus sandboxing (confirmed by spike).

Results are transient -- they'll be routed to final destinations (Obsidian notes, Confluence pages, Asana tasks, etc.) by the calling context.

## Key Decisions

1. **Architecture**: Thin shell wrapper (bash/zsh script) that constructs `omnifocus://localhost/omnijs-run?script=<stable>&arg=<dynamic>` URLs and invokes via `open`
2. **Script stability**: Each action (info, complete, update, search, list, today, create) is a **fixed script** approved once. Variable data flows through `&arg=`
3. **Return values**: `Pasteboard.general.string` (only viable option -- OmniFocus is sandboxed). CLI reads via `pbpaste`.
4. **API research needed**: Must map current JXA API calls to equivalent Omni Automation API calls (different object model)
5. **URL parsing**: CLI natively handles `omnifocus:///task/<id>` and `omnifocus:///project/<id>` URL inputs

## Proposed CLI Interface (Core CRUD)

```bash
# Read operations (return JSON via temp file)
omnifocus info <id-or-url>
omnifocus search <query>
omnifocus today
omnifocus inbox
omnifocus flagged

# Write operations
omnifocus complete <id-or-url>
omnifocus create --name "Task" --project "Project" --tags "tag1,tag2"
omnifocus update <id> --name "New name" --due 2026-03-15

# URL handling (all commands accept omnifocus:// URLs)
omnifocus info omnifocus:///task/fGlMKV-Td3k
omnifocus complete omnifocus:///task/fGlMKV-Td3k

# Setup (one-time)
omnifocus setup    # triggers approval for all action scripts
```

## Action Scripts Inventory

Each script is a stable JavaScript body approved once. The `argument` parameter carries per-invocation data.

| Script | Purpose | Argument | Returns (via pasteboard) |
|--------|---------|----------|------------------------|
| `ofo-info` | Get task/project details | `{id: "<id>", type: "task\|project"}` | Task/project JSON |
| `ofo-complete` | Mark task complete | `{id: "<id>"}` | `{success: true, name: "...", completed: true}` |
| `ofo-update` | Update task properties | `{id: "<id>", name: "...", due: "...", ...}` | Updated task JSON |
| `ofo-search` | Search tasks | `{query: "..."}` | JSON array of matching tasks |
| `ofo-list` | List tasks with filters | `{filter: "inbox\|flagged\|today"}` | JSON array of tasks |
| `ofo-create` | Create new task | `{name: "...", project: "...", tags: [...]}` | Created task JSON with ID |

## Resolved Questions

1. **Attache plugin dependency** -- CLI should be standalone with no dependency on Attache. Shared libraries can be used by both CLI scripts and Attache if the pattern fits, but the CLI must work independently. Attache could adopt the same URL-based patterns later.
2. **Initial scope** -- Core CRUD only (~8 commands): info, complete, create, update, search, today, inbox, flagged. Get the architecture right first, expand later.
3. **Task lookup by ID** -- Use `flattenedTasks.find(t => t.id.primaryKey === id)`. The documented `byIdentifier()` is NOT available on the global `flattenedTasks` array.
4. **Task completion** -- Use `task.markComplete()`. This works with full permissions via script URLs (unlike JXA's `task.completed = true` which fails).
5. **File I/O** -- Not available. OmniFocus is sandboxed. Pasteboard is the only return mechanism.
6. **Named pasteboards** -- `Pasteboard.makeUnique()` exists in the API but unique pasteboards aren't readable from the CLI (`pbpaste` only reads the general pasteboard). Use `Pasteboard.general.string`.

## Prototype Spike Results (2026-03-09)

All three feasibility gates tested via live script URL execution:

| Gate | Result | Details |
|------|--------|---------|
| Find task by ID | PASS | `flattenedTasks.find(t => t.id.primaryKey === id)` works. Note: `byIdentifier()` is NOT available on the global `flattenedTasks` despite being documented. `byName()`, `find()`, `filter()` all work. |
| Mark task complete | PASS | `task.markComplete()` works with full permissions. No "Access not allowed" error like JXA. Confirmed task status changes to `completed: true`. |
| File I/O (temp file) | FAIL | `FileWrapper.write()` to `/tmp/` returns "You don't have permission." OmniFocus is sandboxed and cannot write to arbitrary filesystem paths. |

### API Mapping (JXA vs Omni Automation Script URLs)

| Operation | JXA (current, broken) | Omni Automation (working) |
|-----------|----------------------|--------------------------|
| Get global tasks | `app.defaultDocument.flattenedTasks` | `flattenedTasks` (global) |
| Find by ID | `flattenedTasks.byId(id)` | `flattenedTasks.find(t => t.id.primaryKey === id)` |
| Find by name | `flattenedTasks.whose({name: n})` | `flattenedTasks.byName(n)` |
| Get task ID | (JXA-specific) | `task.id.primaryKey` |
| Mark complete | `task.completed = true` (FAILS) | `task.markComplete()` (WORKS) |
| Write pasteboard | N/A | `Pasteboard.general.string = data` (WORKS) |
| Write temp file | N/A | `FileWrapper.write(url)` (SANDBOXED - FAILS) |

### Architectural Impact

**Pasteboard is the only return mechanism.** Since OmniFocus is sandboxed, the CLI must:
1. Script writes JSON to `Pasteboard.general.string`
2. CLI reads via `pbpaste`
3. CLI saves to temp file locally if persistence needed

This is acceptable -- the `open` + `pbpaste` round-trip is fast and reliable. Clipboard clobber is a minor concern mitigated by the transient nature of results.

## Open Questions

1. **Timing** -- After `open` fires the URL, how long until `pbpaste` has the result? Spike tests used manual approval so timing wasn't measured. Need to measure with auto-approved scripts.
2. **Migration path** -- What happens to the existing JXA scripts (manage_omnifocus.js, gtd-queries.js)? Are they deprecated, kept as fallback, or gradually replaced?
3. **CLI installation** -- Where does the `ofo` script live and how does it get on PATH? Symlink from plugin root? Homebrew-style install?
4. **Large result sets** -- Pasteboard has practical size limits. How does `ofo-list` handle 1836 tasks? May need server-side filtering to keep results small.

## Prior Art

Community CLI tools for OmniFocus -- none fully suitable but each offers insights:

| Tool | Approach | Insight |
|------|----------|---------|
| [ofocus](https://lobehub.com/skills/mike-north-ofocus-ofocus) | macOS CLI for task CRUD, projects, tags, perspectives | Closest to our goal. Study its API patterns and command design. |
| [OTask](https://github.com/ttscoff/OTask) | Ruby CLI, supports piped input as task notes | Piped input pattern worth adopting (e.g., `echo "notes" \| omnifocus create --name "Task"`) |
| [omnifocus-shell](https://github.com/mattmight/omnifocus-shell) | Shell tools using AppleScript | Validates shell wrapper approach; likely hits same JXA permission issues |
| [of-reader](https://github.com/grahl/of-reader) | Reads OmniFocus SQLite database directly | Read-only but avoids API entirely. Could inform a fallback read path. |
| [omnifocus-github](https://github.com/linclark/omnifocus-github) | Node.js GitHub-to-OmniFocus sync | Integration pattern relevant to our multi-tool workflow (Asana, Jira, etc.) |

**Key takeaway:** Most use AppleScript/JXA (same limitations we're hitting). `ofocus` is the most ambitious and worth studying for CLI design. None use Omni Automation script URLs -- this would be novel.

## Research References

- `plugins/omnifocus-manager/skills/omnifocus-manager/references/omnifocus_url_scheme.md` -- Existing URL scheme docs (lines 246-272 cover security friction)
- `plugins/omnifocus-manager/skills/omnifocus-manager/references/omni_automation_guide.md` -- Plugin lifecycle and API guide
- `https://omni-automation.com/script-url/index.html` -- Official script URL documentation
- `https://omni-automation.com/omnifocus/index.html` -- OmniFocus Omni Automation reference (needs research for 4.8+ API)
