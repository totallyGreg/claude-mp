# Inventory Refresh Workflow

<!-- DRAFT — review during D2 integration -->

**Purpose:** Re-runnable workflow for an agent to refresh `capability_inventory.md` from omni-automation.com. Run quarterly or when a specific capability gap is suspected. Do NOT run during normal plugin-building work — read `capability_inventory.md` instead.

**Executed by:** Research Agent (Phase 1 agent) or any agent re-running the refresh. Results land in `capability_inventory.md`.

---

## Workflow Steps

### STEP 1 — Fetch the index

```
WebFetch https://omni-automation.com/omnifocus/
Prompt: "Extract every top-level topic link on this OmniFocus automation index page. 
For each link provide: the link text/title and the full href URL. 
Output as JSON array of {title, url} objects."
```

**Important:** The navigation is JavaScript-driven (`javascript:void(0)`). The index page itself contains very few real hrefs. Proceed to STEP 2 using the known URL pattern.

**Known working URL pattern:** `https://omni-automation.com/omnifocus/<slug>.html`

**Plugin format note:** `.omnijs` runs in ALL Omni apps. `.omnifocusjs` is OmniFocus-specific. Most topics on omni-automation.com apply to both formats unless marked OmniFocus-only.

**Full sidebar topic list (from index.html):**
The Big Picture, Application, Document, Window|Selection, Perspective, Outline, Forecast, FileWrapper, eMail, Database, Arrays, Database Object, Settings, Finding Items, Folders, Projects, Tasks, Repeating Tasks, Attachments, File Links, Notifications, Tasks to Projects, Tags, Text, Style, App-to-App, Shortcuts Integration, TaskPaper, QR Codes, Scripting Dictionary, Automation Tutorial, Automation Controls, Plug-In Collection, Plug-In Generator, Shared Classes & Methods, Plug-Ins, Actions, Action Forms, Libraries

**Confirmed working topic slugs (as of 2026-06-15, rounds 1+2):**
- `task.html` — Task class (full details) 
- `project.html` — Project class (full details)
- `tag.html` — Tag class (full details, includes v4.0+/v4.7+ members)
- `folder.html` — Folder class (full details)
- `database.html` — Database class (full details)
- `perspective.html` — Perspective.BuiltIn + Perspective.Custom
- `filewrapper.html` — FileWrapper + FileWrapper.Type
- `settings.html` — Settings class
- `forecast.html` — ForecastDay + ForecastDay.Kind + ForecastDay.Status
- `document.html` — Document + Application
- `outline.html` — **DocumentWindow, Tree, TreeNode** (outline view API — NEW)
- `database-object.html` — **DatabaseObject, ObjectIdentifier, DatedObject, ActiveObject** (class hierarchy — NEW)
- `text.html` — **Text, Text.Range, Text.Position, Text.FindOption, TextComponent** (rich text API — NEW)
- `style.html` — **Style, Style.Attribute** (30+ style attributes — NEW)
- `app-to-app.html` — Cross-app URL schemes
- `taskpaper.html` — TaskPaper integration
- `task-to-project.html` — Task→Project conversion pattern + Task.Notification.Kind constants
- `qr-code.html` — QR code (sparse, no API)
- `setup.html` — Automation UI config (no API)
- `big-picture.html` — Architectural overview
- `automation-new.html` — Window inspector/sidebar visibility
- `OF-API.html` — Comprehensive class overview (canonical quick reference)
- `tutorial/index.html` — Tutorial index (8 sections)
- `tutorial/plug-in.html` — PlugIn.Action tutorial
- `task-to-project.html` — Conversion pattern
- `../shared/alm.html` — LanguageModel.Session (Foundation Models)
- `../shared/alm-schema.html` — LanguageModel.Schema + GenerationOptions
- `../shortcuts/index.html` — Apple Shortcuts integration summary
- `../ofac/index.html` — Plug-In Template Generator (UI tool)

**404'd slugs — do NOT retry without finding evidence the page exists:**
- Plural forms: `tasks.html`, `projects.html`, `tags.html`, `folders.html`
- PlugIn dedicated pages: `plug-ins.html`, `plugins.html`, `plugin.html`, `plug-in.html`
- `plug-in-action.html`, `plug-in-library.html`, `libraries.html`, `library.html`
- Form pages: `form.html`, `action-form.html`, `action-forms.html`, `forms.html`, `input-form.html`
- `url-scheme.html`, `url-schemes.html`, `file-link.html`, `file-links.html`
- `repeating-tasks.html`, `repeating-task.html`, `repeating.html`
- `email.html`, `e-mail.html`, `notification.html`, `notifications.html`, `task-notification.html`
- `attachment.html`, `attachments.html`, `arrays.html`, `finding-items.html`
- `shortcuts.html`, `tasks-to-projects.html`, `text-style.html`
- `languagemodel-classes.html`, `languagemodel.html`

**Topics NOT found as standalone pages (use local `30_api_reference/omnifocus_api.md`):**
Arrays (FolderArray/TaskArray/etc.), Repeating Tasks (Task.RepetitionRule), Attachments, File Links, Notifications (Task.Notification), Tasks-to-Projects conversion, eMail class, Plug-Ins, PlugIn.Action, Action Forms (Form class), Libraries (PlugIn.Library), Finding Items — all thoroughly covered in `omnifocus_api.md`.

### STEP 2 — Fetch each known topic page

For each confirmed slug:

```
WebFetch https://omni-automation.com/omnifocus/<slug>.html
Prompt: "List every class, property, method, and function documented on this page.
For each item: class name, member name, type (property/method/function/constructor), 
and a one-line description. Output as JSON array of 
{class, member, type, description}."
```

Batch up to 5 pages per round. Cache is 15 minutes — re-fetch only if content seems stale.

For Foundation Models (special case):
```
WebFetch https://omni-automation.com/shared/alm.html
WebFetch https://omni-automation.com/shared/alm-schema.html
```

### STEP 3 — Aggregate into capability table

Produce a single table:

| class | member | type | description | source-url | local-coverage |
|-------|--------|------|-------------|------------|----------------|

`local-coverage` values:
- `covered` — documented in one of the local `20_capabilities/*.md` or `30_api_reference/` files
- `partial` — mentioned but not with full signature/description
- `missing` — not referenced anywhere locally

Sort the table: `missing` rows first, then `partial`, then `covered`.

### STEP 4 — Compare against local refs

For each `(class, member)` row, grep under:
- `plugins/attache/skills/omnifocus-generator/references/20_capabilities/`
- `plugins/attache/skills/omnifocus-core/references/omnifocus_api.md` (the canonical reference)

Mark coverage accordingly.

### STEP 5 — Write capability_inventory.md

Write to `50_external/capability_inventory.md` with:
1. Timestamp (`generatedAt: ISO8601`)
2. Source commit hash (`sourceCommit: <hash>`)
3. The capability table sorted by coverage
4. A TODO list: capability docs that should be added/expanded (for `missing`/`partial` rows judged high-value)

### STEP 6 — Surface gaps as follow-up issues

For any `missing` rows judged high-value, draft issue titles and labels (`attache`, `references`, `omnifocus-api`). Do NOT file them — hand the list back to the human or implementation agent.

---

## Anti-Patterns

- **DO NOT** read every topic page during normal plugin-building work. Read `capability_inventory.md` and the relevant `20_capabilities/*.md` docs instead.
- **DO NOT** inline the full inventory into `00_index.md`. It lives here and is referenced from the capability map only as a fallback.
- **DO NOT** fetch the same URL twice in one run. The 15-minute cache handles it if you use the same URL string.
- **DO NOT** retry 404'd slugs without first finding evidence that the page exists (e.g., a link from another page).

---

## Refresh Cadence

- **Quarterly** (roughly): run the full workflow
- **On-demand**: when a specific capability is suspected missing and `20_capabilities/*.md` doesn't cover it
- **Never**: during normal plugin generation work — too expensive in tokens
