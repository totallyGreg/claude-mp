---
name: confluence-pages
metadata:
  version: 1.0.0
compatibility:
  min_claude_code_version: "1.0.0"
license: MIT
description: >-
  This skill should be used when creating, updating, or managing Confluence
  pages via the REST API. Supplements the official Atlassian plugin (which
  provides read/search but lacks page write operations). Triggers on "create
  confluence page", "update confluence page", "add confluence content",
  "build confluence layout", "configure confluence macro", "generate
  confluence page", "fix confluence page", "set up confluence page".
---

# Confluence Page Management

## Purpose

This skill fills the **write gap** in the official Atlassian plugin. The official plugin provides read/search via `atlassian:search-company-knowledge` but cannot create, update, move, or delete pages.

> **Rule:** Always check if an official Atlassian plugin skill can handle the request first. Only use this skill for page CRUD and storage format generation.

## Configuration

Set these variables before use (or define in a `.local.md` file):

| Variable | Description | Example |
|---|---|---|
| `CONFLUENCE_BASE_URL` | Instance base URL | `https://confluence.example.com` |
| `CONFLUENCE_TOKEN` | PAT or keychain key | `$(keychainctl get CLAUDE_CONFLUENCE)` |
| `CONFLUENCE_USER` | Your username | `jdoe` |
| `CONFLUENCE_SPACE` | Default space key | `~jdoe` |
| `CONFLUENCE_HOME_PAGE` | Personal home page ID | `559735676` |

```bash
CONFLUENCE_BASE_URL="https://confluence.example.com"
CONFLUENCE_TOKEN=$(keychainctl get CLAUDE_CONFLUENCE)
```

All API calls use Bearer auth:

```bash
curl -s \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  "$CONFLUENCE_BASE_URL/rest/api/..."
```

## API Operations

### Search (CQL)

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/search?cql=title+%7E+%22search+term%22&limit=10&expand=space,ancestors"
```

Common CQL: `title ~ "term"`, `space = "KEY" AND title ~ "term"`, `ancestor = PAGE_ID`, `type = page AND lastModified > now("-7d")`

### Get Page

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID?expand=body.storage,version"
```

### Create Page

```bash
cat > /tmp/confluence-page.json << 'EOF'
{
  "type": "page",
  "title": "Page Title",
  "space": { "key": "SPACE_KEY" },
  "ancestors": [{ "id": PARENT_PAGE_ID }],
  "body": {
    "storage": {
      "value": "<p>Content in storage format</p>",
      "representation": "storage"
    }
  }
}
EOF

curl -s -X POST \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/confluence-page.json \
  "$CONFLUENCE_BASE_URL/rest/api/content"
rm /tmp/confluence-page.json
```

### Update Page

**Must increment version number.** Fetch current version first.

```bash
cat > /tmp/confluence-update.json << 'EOF'
{
  "version": { "number": CURRENT_VERSION + 1, "message": "Update description" },
  "title": "Page Title",
  "type": "page",
  "body": {
    "storage": {
      "value": "<p>Updated content</p>",
      "representation": "storage"
    }
  }
}
EOF

curl -s -X PUT \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/confluence-update.json \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID"
rm /tmp/confluence-update.json
```

### Move Page

```bash
# Same space — change parent
curl -s -X PUT \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ancestors": [{"id": NEW_PARENT_PAGE_ID}]}' \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID"

# Different space — include space key and increment version
cat > /tmp/confluence-move.json << 'EOF'
{
  "version": { "number": CURRENT_VERSION + 1 },
  "title": "Page Title",
  "type": "page",
  "space": { "key": "NEW_SPACE_KEY" },
  "ancestors": [{ "id": NEW_PARENT_PAGE_ID }]
}
EOF

curl -s -X PUT \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/confluence-move.json \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID"
rm /tmp/confluence-move.json
```

### Delete Page

```bash
curl -s -X DELETE \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID"
```

## Storage Format

Page content uses Confluence Storage Format (XHTML with `ac:` namespace macros). See `references/storage-format.md` for the full macro reference including panels, status badges, code blocks, layouts, emoticons, and page trees.

Key rules:
- Use the Write tool to create temp JSON files for large payloads
- Escape special characters: `&amp;` `&ndash;` `&mdash;` `&bull;` `&rsquo;`
- Never use raw `&`, `–`, `—` in storage format

## Response Parsing

```bash
curl -s ... | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    base = d.get('_links',{}).get('base','')
    webui = d.get('_links',{}).get('webui','')
    print(f'OK — Page ID: {d[\"id\"]}, Version: {d.get(\"version\",{}).get(\"number\",\"?\")}, URL: {base}{webui}')
else:
    print(f'Error: {d.get(\"message\", json.dumps(d))}')
"
```

## Best Practices

1. **Draft in personal space first** — move to team space when ready
2. **Use temp files for payloads** — avoids shell quoting issues with XML
3. **Always fetch version before updating** — stale versions cause 409 conflicts
4. **Clean up temp files** — `rm /tmp/confluence-*.json` after API calls
5. **Use the official plugin for search** — `atlassian:search-company-knowledge` is better for finding pages
