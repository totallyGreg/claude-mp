# Canvas Operations Guide

## Size Limits

Slack's `canvases.edit` and `canvases.create` APIs have undocumented content size limits:

| Operation | Approximate Limit | Behavior on Exceed |
|-----------|-------------------|---------------------|
| `canvases.create` | ~4KB markdown | `canvas_creation_failed` error |
| `canvases.edit` (single change) | ~4KB markdown | `canvas_editing_failed` error |

The CLI auto-chunks content that exceeds these limits, splitting on paragraph boundaries (`\n\n`) to avoid breaking markdown structure.

## Quip vs New-Type Canvases

| Aspect | Quip Canvas | New Canvas API |
|--------|------------|----------------|
| Detection | `files.info` returns `filetype: "quip"` | Any other filetype |
| Read method | `files.info` → `url_private` (HTML) | `canvases.sections.lookup` (markdown) |
| Write support | Read-only — cannot update via API | Full CRUD via `canvases.edit` |
| Migration | Use `canvas rewrite` to create new-type copy | Already new-type |

The CLI auto-detects canvas type on read and converts quip HTML to markdown transparently. For updates, quip canvases must first be rewritten to new-type via `canvas rewrite`.

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
