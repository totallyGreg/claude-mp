# Slack Web API Reference

## Files API (Quip Canvas Detection)

| Method | Purpose | Scopes | Key Parameters | Notes |
|--------|---------|--------|----------------|-------|
| `files.info` | Get file metadata | `files:read` | `file` | Returns `filetype` — `"quip"` means legacy canvas; also provides `url_private` for HTML download |

Quip-type canvases return HTML via `url_private` (authenticated GET). The CLI converts this to markdown via a stdlib `HTMLParser` subclass.

## Canvas API (New-Type)

| Method | Purpose | Scopes | Key Parameters | Notes |
|--------|---------|--------|----------------|-------|
| `canvases.create` | Create standalone canvas | `canvases:write` | `title`, `document_content` | Returns `canvas_id` (F-prefixed) |
| `canvases.edit` | Update canvas content | `canvases:write` | `canvas_id`, `changes[]` | Operations: `insert_at_start`, `insert_at_end`, `insert_before`, `insert_after`, `replace`, `delete` |
| `canvases.delete` | Delete a canvas | `canvases:write` | `canvas_id` | Permanent deletion |
| `canvases.sections.lookup` | Find sections by criteria | `canvases:read` | `canvas_id`, `criteria` | Returns `section_id` values for targeted edits |
| `canvases.access.set` | Grant access to canvas | `canvases:write` | `canvas_id`, `access_level`, `channel_ids`/`user_ids` | Levels: `read`, `write` |
| `canvases.access.delete` | Revoke access | `canvases:write` | `canvas_id`, `channel_ids`/`user_ids` | — |
| `conversations.canvases.create` | Create channel-bound canvas | `canvases:write` | `channel_id`, `document_content` | Appears in channel canvas tab |

### Canvas Content Format

Canvas content uses markdown via the `document_content` object:

```json
{
  "type": "markdown",
  "markdown": "# Heading\n\nParagraph with **bold** and _italic_.\n\n- Bullet item\n- Another item"
}
```

Supported markdown: headings (`#`–`###`), bold, italic, strikethrough, bulleted/numbered lists, code blocks, tables, links, checklists (`- [ ]`/`- [x]`).

### Canvas Edit Operations

The `canvases.edit` endpoint accepts a `changes` array:

```json
{
  "canvas_id": "F0ABC123DEF",
  "changes": [
    {
      "operation": "insert_at_end",
      "document_content": {"type": "markdown", "markdown": "## Appended Section"}
    }
  ]
}
```

For positional operations (`replace`, `insert_before`, `insert_after`, `delete`), include `section_id` from a prior `canvases.sections.lookup` call.

## Conversation API

| Method | Purpose | Scopes | Key Parameters |
|--------|---------|--------|----------------|
| `conversations.replies` | Get thread replies | `channels:history` | `channel`, `ts`, `cursor`, `limit` |
| `conversations.history` | Get channel messages | `channels:history` | `channel`, `cursor`, `limit`, `oldest`, `latest` |

## Reactions API

| Method | Purpose | Scopes | Key Parameters |
|--------|---------|--------|----------------|
| `reactions.add` | Add emoji reaction | `reactions:write` | `channel`, `timestamp`, `name` |
| `reactions.remove` | Remove emoji reaction | `reactions:write` | `channel`, `timestamp`, `name` |

## Auth API

| Method | Purpose | Scopes | Notes |
|--------|---------|--------|-------|
| `auth.test` | Verify token | Any | Works with GET or POST; returns workspace, user, team info |

## Enterprise Grid Notes

- All conversation endpoints require **POST with form-encoded body**
- GET with query params returns `not_authed` on enterprise grids
- `auth.test` is the exception — works with any HTTP method
- JSON responses may contain control characters — use `strict=False` when parsing

## Rate Limit Tiers

| Tier | Rate | Endpoints |
|------|------|-----------|
| Tier 1 | 1 req/min | — |
| Tier 2 | 20 req/min | Most write endpoints |
| Tier 3 | 50 req/min | Most read endpoints |
| Tier 4 | 100+ req/min | `auth.test`, some metadata endpoints |

On HTTP 429, the `Retry-After` header indicates seconds to wait before retrying.

## Required Scopes Summary

| Scope | Operations |
|-------|-----------|
| `files:read` | Canvas type detection (files.info), quip HTML download |
| `canvases:read` | Canvas read (sections.lookup) — new-type canvases |
| `canvases:write` | Canvas create, edit, delete, access management |
| `channels:history` | Thread replies, channel history |
| `reactions:write` | Add/remove reactions |
