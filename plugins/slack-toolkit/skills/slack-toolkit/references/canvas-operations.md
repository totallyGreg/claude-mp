# Canvas Operations Guide

## Size Limits

Slack's `canvases.edit` and `canvases.create` APIs have undocumented content size limits:

| Operation | Approximate Limit | Behavior on Exceed |
|-----------|-------------------|---------------------|
| `canvases.create` | ~4KB markdown | `canvas_creation_failed` error |
| `canvases.edit` (single change) | ~4KB markdown | `canvas_editing_failed` error |

The CLI auto-chunks content that exceeds these limits, splitting on paragraph boundaries (`\n\n`) to avoid breaking markdown structure.

## Quip vs New-Type Canvases

Slack has two incompatible canvas backends. The type is determined at the **workspace level** — not by which API you use. Some workspaces (particularly on Slack Enterprise Grid) route all canvas creation through the legacy Quip backend, even when using the `canvases.create` API.

| Aspect | Quip Canvas | New Canvas API |
|--------|------------|----------------|
| Detection | `files.info` returns `filetype: "quip"` | Any other filetype |
| Read method | `files.info` → `url_private` (HTML) | `canvases.sections.lookup` (markdown) |
| Write support | **Read-only** — `canvases.edit` fails or behaves unpredictably | Full CRUD via `canvases.edit` |
| Inline comments | Trapped in Quip's proprietary format — not accessible via API | Accessible as threaded messages |
| Content size | Single `canvases.create` call (~4KB limit) — no reliable append | Auto-chunked via `canvases.edit` appends |

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
- **Canvas create works** — but content is limited to ~4KB (single API call). Larger content is truncated with a warning
- **Canvas update (append/replace) does not work** — `canvases.edit` is not supported on quip canvases
- **Canvas rewrite does not help** — rewriting creates another quip canvas on the same workspace
- **To update content**: create a new canvas with the full updated content and retire the old one

The CLI auto-detects quip on read and transparently converts HTML to markdown. On create, it checks the result and warns if content was truncated due to quip limitations.

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

## Auto-Chunking

When content exceeds ~3KB, the CLI automatically:
1. Splits content on paragraph boundaries (`\n\n`)
2. Sends each chunk as a separate `insert_at_end` operation
3. Waits 1 second between chunks (rate limit courtesy)
4. Reports the number of chunks used in the JSON response: `{"ok": true, "chunks": 4}`

This applies to both `canvas create --content-file` and `canvas update --append-file`.
