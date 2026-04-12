# Canvas Operations Guide

## Reading Canvas Content

There is no official `canvases.read` or `canvases.get` API. The only mechanism is `files.info` → `url_private`:

| Canvas type | `url_private` content | Readable? |
|-------------|----------------------|-----------|
| Quip (`filetype: "quip"`) | HTML | ✅ Yes — CLI converts to markdown via HTMLParser |
| New-type (other filetypes) | Unknown / not documented | ❓ Workspace-dependent — may work, may return nothing |

`canvases.sections.lookup` is **not** a read mechanism — it returns section IDs only (no text or markdown). It exists to find section IDs for targeted `canvases.edit` operations.

When `url_private` is absent or the canvas type is not supported, `canvas read` exits non-zero and emits a JSON object with available metadata (`canvas_id`, `title`, `filetype`, `permalink`).

---

## Size Limits

Slack's `canvases.edit` API has an undocumented per-operation content size limit:

| Operation | Approximate Limit | Behavior on Exceed |
|-----------|-------------------|---------------------|
| `canvases.create` | No practical limit (20KB+ tested successfully) | N/A |
| `canvases.edit` (single change) | ~4KB markdown | `canvas_editing_failed` error |

`canvases.create` sends the full content in a single call — no chunking is needed or used.

## Heading Depth Constraint

Slack Canvas only supports headings up to H3 (`###`). H4+ headings (`####`, `#####`, etc.) cause `canvas_creation_failed` with the error: `Unsupported heading depth (4)`.

The CLI automatically downgrades H4+ headings to H3 with a warning to stderr. This applies to `canvas create` only — `canvas update` (append/replace) passes content through unchanged, so avoid H4+ in append content too.

## Quip vs New-Type Canvases

Slack has two incompatible canvas backends. The type is determined at the **workspace level** — not by which API you use. Some workspaces (particularly on Slack Enterprise Grid) route all canvas creation through the legacy Quip backend, even when using the `canvases.create` API.

| Aspect | Quip Canvas | New Canvas API |
|--------|------------|----------------|
| Detection | `files.info` returns `filetype: "quip"` | Any other filetype |
| Read method | `files.info` → `url_private` (HTML) | `canvases.sections.lookup` (markdown) |
| Write support | **Read-only** — `canvases.edit` fails or behaves unpredictably | Full CRUD via `canvases.edit` |
| Inline comments | Trapped in Quip's proprietary format — not accessible via API | Accessible as threaded messages |
| Content size | Single `canvases.create` call — no reliable append | Auto-chunked via `canvases.edit` appends |

### Quip Detection Reliability

The `filetype: "quip"` check (via `files.info`) is a **pre-flight heuristic**, not a gate. Some canvases carry `filetype: "quip"` metadata but still accept `canvases.edit` calls successfully — particularly canvases created via `conversations.canvases.create` or through migration workflows. The CLI emits a warning *before* attempting the edit, not after. If the subsequent call returns `{"ok": true}`, the update succeeded regardless of the warning. Treat `{"ok": true}` as authoritative.

### Detecting Workspace Canvas Type

Use `canvas probe` to determine what type of canvases your workspace produces **before** creating content:

```bash
slacker.py canvas probe
```

This creates a tiny test canvas, checks its filetype, deletes it, and reports:

```json
{
  "workspace_canvas_type": "quip",
  "canvases_edit_supported": false,
  "chunked_create_supported": false,
  "warning": "This workspace routes canvases.create through legacy Quip backend..."
}
```

### Implications for Quip Workspaces

On quip workspaces:
- **Canvas read works fine** — the CLI auto-detects quip and converts HTML to markdown
- **Canvas create works** — single API call, no size limit. H4+ headings are auto-downgraded to H3 with a warning
- **Canvas update (append/replace) does not work** — `canvases.edit` is not supported on quip canvases
- **Canvas rewrite does not help** — rewriting creates another quip canvas on the same workspace
- **To update content**: create a new canvas with the full updated content and retire the old one

The CLI auto-detects quip on read and transparently converts HTML to markdown.

## Atomic Section Edits

To edit a specific section in place without recreating the whole canvas:

```bash
# Step 1: find the section ID
slacker.py canvas sections lookup F0ABC123 --section-types h2 --contains-text "Status"
# → {"ok": true, "sections": [{"id": "temp:C:abc123def456..."}]}

# Step 2: replace it atomically
slacker.py canvas update F0ABC123 --replace temp:C:abc123def456... --content-file updated-section.md
```

`--section-types` accepts: `h1`, `h2`, `h3`, `any_header`. `--contains-text` substring-matches within sections. Both filters are optional and combine as AND. Results contain only section IDs — there is no content in the response.

---

## Update Operations

### Append (most common)

```bash
# Inline content (small additions only — shell escaping breaks on backticks/code blocks)
slacker.py canvas update <canvas_id> --append "## New Section"

# From file (recommended for any content with code blocks or special characters)
slacker.py canvas update <canvas_id> --append-file /path/to/content.md
```

Always prefer `--append-file` over inline `--append` when content contains:
- Code blocks (triple backticks)
- Shell special characters (`$`, `!`, backticks)
- Tables with pipes
- Multi-line content

### Replace Section

```bash
# Get section IDs first
slacker.py canvas read <canvas_id>

# Replace a specific section
slacker.py canvas update <canvas_id> --replace <section_id> --content "## Updated"
slacker.py canvas update <canvas_id> --replace <section_id> --content-file /path/to/content.md
```

### Full Canvas Replacement

There is no single "replace all" API operation. To replace entire canvas content:

1. Create a new canvas with the updated content: `slacker.py canvas create "Title" --content-file updated.md`
2. The old canvas remains unchanged (can be deleted manually if needed)

## Auto-Chunking (append only)

Auto-chunking applies only to `canvas update --append-file`, not to `canvas create`. When appending large content:

1. Splits content on paragraph boundaries (`\n\n`)
2. Sends each chunk as a separate `insert_at_end` operation (~4KB per chunk)
3. Waits 1 second between chunks (rate limit courtesy)
4. Reports the number of chunks used in the JSON response: `{"ok": true, "chunks": 4}`
