---
name: confluence-pages
metadata:
  version: 1.0.0
description: >-
  This skill should be used when creating, updating, moving, or deleting
  Confluence pages via the REST API. Supplements the official Atlassian plugin
  (which provides read/search via `atlassian:search-company-knowledge` but
  lacks page write operations). Triggers on "create confluence page", "update
  confluence page", "move page", "add confluence content", "confluence storage
  format", "confluence macro", "write to confluence", "publish to confluence",
  or "confluence page layout".
---

# Confluence Page Management

## Purpose

This skill fills the **write gap** in the official Atlassian plugin. The official plugin provides:

| Official Plugin Skill | Capability |
|---|---|
| `atlassian:search-company-knowledge` | Search Confluence & Jira (read-only) |
| `atlassian:capture-tasks-from-meeting-notes` | Create Jira tasks from notes |
| `atlassian:triage-issue` | Search/create Jira bugs |
| `atlassian:spec-to-backlog` | Read Confluence → create Jira epics |
| `atlassian:generate-status-report` | Read Jira → write one specific report |

**This skill adds:** create, update, move, and delete Confluence pages with rich formatting.

> **Rule:** Always check if an official Atlassian plugin skill can handle the request first. Only use this skill for operations the plugin cannot perform (page CRUD, storage format generation, page moves).

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

### Search for Pages (CQL)

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/search?cql=title+%7E+%22search+term%22&limit=10&expand=space,ancestors"
```

Common CQL patterns:
- `title ~ "search term"` — fuzzy title match
- `title = "Exact Title"` — exact title match
- `space = "KEY" AND title ~ "term"` — within a space
- `ancestor = PAGE_ID` — children of a page
- `type = page AND lastModified > now("-7d")` — recent pages

### Get Page Content

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID?expand=body.storage,version"
```

**Important:** Always fetch the current version number before updating.

### Get Child Pages

```bash
curl -s -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID/child/page?limit=25&expand=version"
```

### Create Page

Write the JSON payload to a temp file (recommended for large pages to avoid shell quoting issues):

```bash
# Write payload to temp file
cat > /tmp/confluence-page.json << 'EOF'
{
  "type": "page",
  "title": "Page Title",
  "space": { "key": "SPACE_KEY" },
  "ancestors": [{ "id": PARENT_PAGE_ID }],
  "body": {
    "storage": {
      "value": "<p>HTML storage format content here</p>",
      "representation": "storage"
    }
  }
}
EOF

# Create the page
curl -s -X POST \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d @/tmp/confluence-page.json \
  "$CONFLUENCE_BASE_URL/rest/api/content"

# Clean up
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

Move a page to a new parent (same or different space):

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $CONFLUENCE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ancestors": [{"id": NEW_PARENT_PAGE_ID}]}' \
  "$CONFLUENCE_BASE_URL/rest/api/content/PAGE_ID"
```

To move to a different space, include the space key:

```bash
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

## Confluence Storage Format Reference

All page content uses Confluence Storage Format (XHTML with `ac:` namespace macros). **Always use the Write tool to create a temp JSON file** rather than inline heredocs for large payloads.

### Text & Structure

```xml
<h2>Heading</h2>
<p>Paragraph with <strong>bold</strong>, <em>italic</em>, and <code>code</code>.</p>
<ul><li>Bullet item</li></ul>
<ol><li>Numbered item</li></ol>
<hr />
<table><tbody>
  <tr><th>Header</th><th>Header</th></tr>
  <tr><td>Cell</td><td>Cell</td></tr>
</tbody></table>
```

**Special characters:** Use `&amp;` `&ndash;` `&mdash;` `&bull;` `&rsquo;` `&ldquo;` `&rdquo;` — never raw `&`, `–`, `—`, etc.

### Panel Macro (colored box with title)

```xml
<ac:structured-macro ac:name="panel" ac:schema-version="1">
  <ac:parameter ac:name="bgColor">#f0f5ff</ac:parameter>
  <ac:parameter ac:name="titleBGColor">#0052CC</ac:parameter>
  <ac:parameter ac:name="titleColor">#ffffff</ac:parameter>
  <ac:parameter ac:name="title">Panel Title</ac:parameter>
  <ac:parameter ac:name="borderStyle">solid</ac:parameter>
  <ac:parameter ac:name="borderColor">#0052CC</ac:parameter>
  <ac:rich-text-body><p>Content here</p></ac:rich-text-body>
</ac:structured-macro>
```

### Info / Note / Warning / Tip Panels

```xml
<!-- Info (blue) -->
<ac:structured-macro ac:name="info" ac:schema-version="1">
  <ac:parameter ac:name="icon">true</ac:parameter>
  <ac:parameter ac:name="title">Info Title</ac:parameter>
  <ac:rich-text-body><p>Informational content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Note (yellow) -->
<ac:structured-macro ac:name="note" ac:schema-version="1">
  <ac:parameter ac:name="title">Note Title</ac:parameter>
  <ac:rich-text-body><p>Note content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Warning (red) -->
<ac:structured-macro ac:name="warning" ac:schema-version="1">
  <ac:parameter ac:name="title">Warning Title</ac:parameter>
  <ac:rich-text-body><p>Warning content</p></ac:rich-text-body>
</ac:structured-macro>

<!-- Tip (green) -->
<ac:structured-macro ac:name="tip" ac:schema-version="1">
  <ac:parameter ac:name="title">Tip Title</ac:parameter>
  <ac:rich-text-body><p>Tip content</p></ac:rich-text-body>
</ac:structured-macro>
```

### Status Macro (colored badge)

```xml
<ac:structured-macro ac:name="status" ac:schema-version="1">
  <ac:parameter ac:name="colour">Green</ac:parameter>
  <ac:parameter ac:name="title">ACTIVE</ac:parameter>
</ac:structured-macro>
```

Colors: `Green`, `Blue`, `Red`, `Yellow`, `Purple`, `Grey`

### Expand Macro (collapsible section)

```xml
<ac:structured-macro ac:name="expand" ac:schema-version="1">
  <ac:parameter ac:name="title">Click to expand</ac:parameter>
  <ac:rich-text-body><p>Hidden content</p></ac:rich-text-body>
</ac:structured-macro>
```

### Code Block

```xml
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:parameter ac:name="title">Code Title</ac:parameter>
  <ac:plain-text-body><![CDATA[echo "hello world"]]></ac:plain-text-body>
</ac:structured-macro>
```

Languages: `bash`, `python`, `java`, `javascript`, `json`, `yaml`, `xml`, `sql`, `go`, `ruby`, `html`, `css`, `none`

### Table of Contents

```xml
<ac:structured-macro ac:name="toc" ac:schema-version="1">
  <ac:parameter ac:name="maxLevel">3</ac:parameter>
</ac:structured-macro>
```

### Layout Sections

```xml
<!-- Single column -->
<ac:layout><ac:layout-section ac:type="single"><ac:layout-cell>
  <p>Full width content</p>
</ac:layout-cell></ac:layout-section></ac:layout>

<!-- Two equal columns -->
<ac:layout><ac:layout-section ac:type="two_equal">
  <ac:layout-cell><p>Left column</p></ac:layout-cell>
  <ac:layout-cell><p>Right column</p></ac:layout-cell>
</ac:layout-section></ac:layout>

<!-- Three equal columns -->
<ac:layout><ac:layout-section ac:type="three_equal">
  <ac:layout-cell><p>Col 1</p></ac:layout-cell>
  <ac:layout-cell><p>Col 2</p></ac:layout-cell>
  <ac:layout-cell><p>Col 3</p></ac:layout-cell>
</ac:layout-section></ac:layout>

<!-- Sidebar layouts -->
<!-- ac:type options: two_left_sidebar, two_right_sidebar -->
```

Multiple layout sections can be stacked within a single `<ac:layout>` tag.

### Emoticon

```xml
<ac:emoticon ac:name="blue-star" />
<ac:emoticon ac:name="green-star" />
<ac:emoticon ac:name="warning" />
<ac:emoticon ac:name="tick" />
<ac:emoticon ac:name="cross" />
<ac:emoticon ac:name="information" />
```

### Recently Updated Macro

```xml
<ac:structured-macro ac:name="recently-updated" ac:schema-version="1" />
```

### Page Tree & Search

```xml
<ac:structured-macro ac:name="pagetree" ac:schema-version="1" />
<ac:structured-macro ac:name="pagetreesearch" ac:schema-version="1" />
```

### Children Display

```xml
<ac:structured-macro ac:name="children" ac:schema-version="1">
  <ac:parameter ac:name="all">true</ac:parameter>
  <ac:parameter ac:name="sort">title</ac:parameter>
</ac:structured-macro>
```

### Excerpt

```xml
<ac:structured-macro ac:name="excerpt" ac:schema-version="1">
  <ac:parameter ac:name="hidden">true</ac:parameter>
  <ac:rich-text-body><p>This text can be included on other pages</p></ac:rich-text-body>
</ac:structured-macro>
```

### Link to Another Confluence Page

```xml
<ac:link><ri:page ri:content-title="Page Title" ri:space-key="SPACEKEY" /><ac:plain-text-link-body><![CDATA[Display Text]]></ac:plain-text-link-body></ac:link>
```

### User Mention

```xml
<ac:link><ri:user ri:username="USERNAME" /></ac:link>
```

## Best Practices

1. **Draft in personal space first** — create pages under your personal space, then move to the team space when ready
2. **Use temp files for payloads** — avoids shell quoting nightmares with storage format XML
3. **Always fetch version before updating** — stale version numbers cause 409 conflicts
4. **Clean up temp files** — always `rm /tmp/confluence-*.json` after API calls
5. **Validate JSON before sending** — use `python3 -m json.tool < /tmp/confluence-page.json` to check
6. **Parse responses** — pipe through `python3 -c "import sys,json; ..."` for clean output
7. **Use the official plugin for search** — `atlassian:search-company-knowledge` is better for finding pages; this skill is for writing

## Response Parsing

```bash
# Parse create/update response
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

## Common Workflows

### Create a Documentation Page

1. Search for existing pages to avoid duplicates
2. Find the target parent page ID
3. Create page in personal space
4. Review the page in browser
5. Move to team space when ready

### Update an Existing Page

1. Fetch page with `?expand=body.storage,version`
2. Note the current version number
3. Modify the storage format content
4. PUT with version number incremented by 1

### Move Page to Team Space

1. Fetch current page version
2. PUT with new space key and ancestor (parent page ID)
3. Version must be incremented
