# Slack Web API Reference

## Canvas API

All canvas methods POST to `https://slack.com/api/<method>`. Both bot (`xoxb-`) and user (`xoxp-`) tokens are accepted. Canvas features require a **paid Slack plan**.

### Method Index

| Method | Description | Scope | Rate Tier |
|--------|-------------|-------|-----------|
| `canvases.create` | Create standalone canvas | `canvases:write` | Tier 2 (20+/min) |
| `canvases.delete` | Permanently delete a canvas | `canvases:write` | Tier 3 (50+/min) |
| `canvases.edit` | Update content or title | `canvases:write` | Tier 3 (50+/min) |
| `canvases.sections.lookup` | Find section IDs within a canvas | `canvases:read` | Tier 3 (50+/min) |
| `canvases.access.set` | Grant/change access for users or channels | `canvases:write` | Tier 3 (50+/min) |
| `canvases.access.delete` | Revoke access from users or channels | `canvases:write` | Tier 3 (50+/min) |
| `conversations.canvases.create` | Create a channel-pinned canvas tab | `canvases:write` | Tier 2 (20+/min) |

**CLI coverage:** `canvas read`, `canvas create`, `canvas update`, `canvas sections lookup`, `canvas probe`, `canvas rewrite`, `canvas delete`, `canvas channel-create`, `canvas access set/delete`.

**No read API exists.** There is no `canvases.read` or `canvases.get` method. `canvases.sections.lookup` returns section IDs only — not content. Reading canvas content relies on `files.info` → `url_private` (reliable for quip canvases; undocumented and workspace-dependent for new-type canvases).

---

### `canvases.create`

Create a standalone canvas owned by the calling user.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `title` | No | Canvas title |
| `document_content` | No | `{"type": "markdown", "markdown": "..."}` |
| `channel_id` | No | Auto-tab into this channel on create |

**Response:** `{"ok": true, "canvas_id": "F1234ABCD"}`

Canvas IDs use the `F`-prefix (same namespace as files).

**Key constraints:**
- `canvases.create` accepts large payloads (20KB+ tested) in a single call — no chunking needed
- Headings above H3 (`####`) cause `canvas_creation_failed` with "Unsupported heading depth (4)" — the CLI auto-downgrades H4+ to H3

**Notable errors:**

| Error | Meaning |
|-------|---------|
| `canvas_creation_failed` | Content format issue (e.g., unsupported heading depth) |
| `free_teams_cannot_create_standalone_canvases` | Free plan; use `conversations.canvases.create` instead |
| `canvas_disabled_user_team` | Canvas feature disabled for workspace |

---

### `canvases.delete`

Permanently delete a canvas. **Irreversible — no soft-delete or trash.**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `canvas_id` | Yes | F-prefixed canvas ID |

**Response:** `{"ok": true}`

To delete a single section (not the whole canvas), use `canvases.edit` with `"operation": "delete"` and a `section_id`.

---

### `canvases.edit`

Update content or rename an existing canvas.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `canvas_id` | Yes | F-prefixed canvas ID |
| `changes` | Yes | Array of change objects (see below) |

**Important:** Only one operation per API call is processed despite the array structure.

**Content operations:**

| Operation | Requires | Description |
|-----------|----------|-------------|
| `insert_at_end` | `document_content` | Append to canvas |
| `insert_at_start` | `document_content` | Prepend to canvas |
| `insert_after` | `section_id` + `document_content` | Insert after a section |
| `insert_before` | `section_id` + `document_content` | Insert before a section |
| `replace` | `document_content` (+ optional `section_id`) | Replace a section or full canvas |
| `delete` | `section_id` | Delete a specific section |
| `rename` | `title_content` (not `document_content`) | Rename the canvas title |

**Rename example** — uses `title_content`, not `document_content`, no `section_id`:
```json
{"canvas_id": "F0ABC123", "changes": [{"operation": "rename", "title_content": {"type": "markdown", "markdown": "New Title :white_check_mark:"}}]}
```

**Append example:**
```json
{"canvas_id": "F0ABC123", "changes": [{"operation": "insert_at_end", "document_content": {"type": "markdown", "markdown": "## New Section\n\nContent here."}}]}
```

**Per-operation size limit:** ~4KB per `canvases.edit` call. The CLI auto-chunks large appends across multiple calls.

**Response trust:** `{"ok": true}` is authoritative — the change was applied server-side. A verification read after a successful edit is unnecessary. Only read back if the call returned a non-ok response.

---

### `canvases.sections.lookup`

Find section IDs within a canvas. Required before positional edits (`insert_before`, `insert_after`, `replace`, `delete`).

| Parameter | Required | Description |
|-----------|----------|-------------|
| `canvas_id` | Yes | F-prefixed canvas ID |
| `criteria` | Yes | Filter object (see below) |

**`criteria` structure:**
```json
{"section_types": ["h1", "h2", "h3", "any_header"], "contains_text": "search text"}
```

Both fields are optional; combining them performs AND. `section_types` only filters heading-type sections — paragraphs, lists, etc. appear only when `section_types` is omitted.

**Response:** `{"ok": true, "sections": [{"id": "temp:C:<hex>"}]}`

Section IDs follow the pattern `temp:C:<hex-string>`.

---

### `canvases.access.set`

Grant or change access level for users or channels on a standalone canvas.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `canvas_id` | Yes | F-prefixed canvas ID |
| `access_level` | Yes | `read`, `write`, or `owner` |
| `channel_ids` | One of | Regular channel IDs only |
| `user_ids` | One of | User IDs |

**`access_level` values:**

| Level | Notes |
|-------|-------|
| `read` | Read-only |
| `write` | Read + write |
| `owner` | Transfer ownership — only valid with `user_ids`, same workspace only |

**Critical constraints:**
- `channel_ids` and `user_ids` are mutually exclusive — cannot pass both
- Only regular channels accepted — no DMs or MPDMs (use `user_ids` for individual DM participants)
- Channel-level permissions override user-level — you cannot exempt individual channel members
- Requires sharing the canvas link with the user directly before `user_ids` access takes effect

---

### `canvases.access.delete`

Revoke canvas access from users or channels. Only works on standalone canvases.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `canvas_id` | Yes | F-prefixed canvas ID |
| `channel_ids` | One of | Channels to remove |
| `user_ids` | One of | Users to remove |

**Constraints:** Same mutual exclusivity as `canvases.access.set`. Channel canvases return `canvas_not_found` — access is controlled by channel membership, not this API.

---

### `conversations.canvases.create`

Create a channel-pinned canvas tab for a channel. **Each channel can only have one.**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `channel_id` | Yes | Channel to attach canvas to |
| `document_content` | No | `{"type": "markdown", "markdown": "..."}` |
| `title` | No | Canvas title |

**Response:** `{"ok": true, "canvas_id": "F1234ABCD"}`

**Key constraints:**
- Calling again returns `channel_canvas_already_exists` — retrieve the existing canvas ID via `conversations.info` → `channel.properties.canvas`
- Creating with no `document_content` does not show the canvas icon in the channel header — content must be provided
- Access is controlled by channel membership — no separate sharing needed
- Cannot use `canvases.access.delete` on channel canvases

**Notable errors:**

| Error | Meaning |
|-------|---------|
| `channel_canvas_already_exists` | One already exists; use `conversations.info` to find its ID |
| `canvas_creation_failed` | Content format issue (same H4+ heading constraint applies) |

---

## `document_content` Format

Used in `canvases.create`, `canvases.edit`, and `conversations.canvases.create`:

```json
{"type": "markdown", "markdown": "# H1\n## H2\n### H3\n\nBold **text**, _italic_, ~~strike~~.\n\n- Bullet\n- [ ] Checklist\n\n| Col1 | Col2 |\n|------|------|\n| a    | b    |"}
```

**Supported:** Headings H1–H3 only (`####` causes `canvas_creation_failed`), bold, italic, strikethrough, bulleted/numbered lists, checklists (`- [ ]`/`- [x]`), code blocks, tables, links, emoji codes, @mentions.

---

## Files API (Quip Canvas Detection)

| Method | Purpose | Scopes | Key Parameters | Notes |
|--------|---------|--------|----------------|-------|
| `files.info` | Get file metadata | `files:read` | `file` | Returns `filetype` — `"quip"` means legacy canvas; provides `url_private` for HTML download |

Quip-type canvases return HTML via `url_private` (authenticated GET). The CLI converts this to markdown via a stdlib `HTMLParser` subclass.

---

## Conversation API

| Method | Purpose | Scopes | Key Parameters |
|--------|---------|--------|----------------|
| `conversations.replies` | Get thread replies | `channels:history` | `channel`, `ts`, `cursor`, `limit` |
| `conversations.history` | Get channel messages | `channels:history` | `channel`, `cursor`, `limit`, `oldest`, `latest` |

---

## Reactions API

| Method | Purpose | Scopes | Key Parameters |
|--------|---------|--------|----------------|
| `reactions.add` | Add emoji reaction | `reactions:write` | `channel`, `timestamp`, `name` |
| `reactions.remove` | Remove emoji reaction | `reactions:write` | `channel`, `timestamp`, `name` |

---

## Auth API

| Method | Purpose | Notes |
|--------|---------|-------|
| `auth.test` | Verify token | Works with GET or POST; returns workspace, user, team info |

---

## Enterprise Grid Notes

- All conversation endpoints require **POST with form-encoded body** — GET returns `not_authed`
- `auth.test` is the exception — works with any HTTP method
- JSON responses may contain control characters — use `strict=False` when parsing

---

## Rate Limit Tiers

| Tier | Rate | Canvas Endpoints |
|------|------|-----------------|
| Tier 2 | 20+/min | `canvases.create`, `conversations.canvases.create` |
| Tier 3 | 50+/min | `canvases.edit`, `canvases.delete`, `canvases.sections.lookup`, `canvases.access.*` |
| Tier 4 | 100+/min | `auth.test` |

On HTTP 429, check the `Retry-After` header for seconds to wait.

---

## Required Scopes Summary

| Scope | Operations |
|-------|-----------|
| `files:read` | Canvas type detection (`files.info`), quip HTML download |
| `canvases:read` | Section lookup (`canvases.sections.lookup`) |
| `canvases:write` | Canvas create, edit, delete, access management |
| `channels:history` | Thread replies, channel history |
| `reactions:write` | Add/remove reactions |
