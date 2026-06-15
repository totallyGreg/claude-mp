# URL Schemes and Callbacks

<!-- DRAFT — review during D2 integration -->

**What this covers:** `omnifocus://` URL schemes, `omnijs-run` script URL pattern, `x-callback-url` protocol, cross-app automation URLs, and how the `ofo` CLI uses script URLs.

**What this does NOT cover:** Apple Shortcuts (see JXA channel). FileWrapper export. See `05_files_export.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

The `ofo` CLI uses the `omnijs-run` pattern internally. For agent-driven work, always prefer `ofo` CLI over hand-crafting script URLs. Only use script URLs directly when building a plugin that must fire into OmniFocus from an external app or URL scheme.

---

## 2. OmniFocus URL Scheme

### Navigation URLs (fire-and-forget, no callback)

```
omnifocus:///                            → open OmniFocus
omnifocus:///inbox                       → show Inbox
omnifocus:///flagged                     → show Flagged
omnifocus:///perspective/Projects        → show named perspective
omnifocus:///task/<primaryKey>           → navigate to task
omnifocus:///add?name=<encoded>&note=<encoded>&due=<ISO8601>   → add task
omnifocus:///search?q=<encoded>          → search
```

From Omni Automation:
```js
URL.fromString("omnifocus:///perspective/Forecast").open();
```

From shell:
```bash
open "omnifocus:///perspective/Forecast"
```

---

## 3. omnijs-run Script URL

The `ofo` CLI's core mechanism: run Omni Automation JavaScript inside OmniFocus.

```
omnifocus://localhost/omnijs-run?script=<URL-encoded-JS>&arg=<URL-encoded-JSON>
```

**Architecture:**
```
Shell (ofo CLI)
  → Reads stable .js file from scripts/omni-actions/
  → URL-encodes script body (approved once per unique script content)
  → JSON-encodes argument data (changes freely via &arg=)
  → open "omnifocus://localhost/omnijs-run?script=...&arg=..."
  → OmniFocus executes JS with full Omni Automation API access
  → Script writes JSON result to Pasteboard.general.string
  → CLI reads via pbpaste (sentinel-based polling)
  → CLI outputs JSON to stdout
```

**Key constraint:** Script body is URL-encoded and hashed by OmniFocus. Changing the script requires user re-approval. The `arg` parameter changes freely without re-approval. Keep logic in `arg`, keep script stable.

---

## 4. x-callback-url

For bidirectional communication where OmniFocus calls back to another app:

```
omnifocus://x-callback-url/add?name=<encoded>&x-success=<success-url>&x-cancel=<cancel-url>
```

From within a plugin (calling OmniPlan, for example):
```js
var callbackURL = URL.fromString("omniplan://x-callback-url/action?param=value&x-success=" + 
  encodeURIComponent("omnifocus://localhost/omnijs-run?script=" + encodeURIComponent(callbackScript)));
callbackURL.open();
```

**Practical usage:** Rarely needed in agent workflows. Primarily for Shortcuts integration or OmniPlan cross-referencing.

---

## 5. App-to-App Automation

Cross-app automation where one Omni app invokes another:

```js
// From OmniFocus plugin: send data to OmniPlan
var tasks = selection.tasks.map(function(t) {
  return {
    OFtaskTitle: t.name,
    OFtaskNote: t.note + "\n" + "omnifocus:///task/" + t.id.primaryKey,
    OFtaskDueDate: t.dueDate ? t.dueDate.toISOString() : null
  };
});

// Using Application.tellFunction() pattern
// (See OF-API.html for Application.tellFunction signature)
```

---

## 6. Database.objectForURL (v4.5+)

Navigate from a URL back to a database object:

```js
var url = URL.fromString("omnifocus:///task/abc123def456");
var obj = database.objectForURL(url);   // → DatabaseObject | null (Task, Project, Tag, Folder)
if (obj instanceof Task) {
  // obj is the task
}
```

---

## 7. Common Patterns

### Open a task URL from a plugin:

```js
var taskURL = URL.fromString("omnifocus:///task/" + task.id.primaryKey);
taskURL.open();
```

### Create a task via URL from shell:

```bash
open "omnifocus:///add?name=Review%20PR&due=2026-06-20T17:00:00"
```

### From Omni Automation (inside plugin):

```js
URL.fromString("omnifocus:///add?name=" + encodeURIComponent("New Task")).open();
// Note: this fires and forgets — no confirmation task was created
```

---

## 8. Reach-Out Trigger

URL schemes are documented in the Omni developer docs, not primarily on omni-automation.com:

```
WebFetch https://omni-automation.com/omnifocus/app-to-app.html
Prompt: "List all URL scheme patterns documented. Include x-callback-url parameters."
```

Also: `https://inside.omnifocus.com/url-schemes` (external; the Omni official URL scheme reference).

---

## 9. Apple Shortcuts Integration

OmniFocus supports Shortcuts via the **Omni Automation Script Action** (macOS Monterey+, iOS, iPadOS):

- Runs an Omni Automation script inside OmniFocus from a Shortcut
- Pass text, OmniFocus object references, or file attachments in/out
- The Shortcut can pass the current OmniFocus selection into the script
- Same script works across iOS, iPadOS, and macOS

**From a plugin action, launch a Shortcut:**
```js
URL.fromString("shortcuts://run-shortcut?name=" + encodeURIComponent("My Shortcut")).open();
```

**Plugin format for Shortcuts:** `.omnijs` scripts (cross-app) can be invoked via Shortcuts' Script Action. `.omnifocusjs` plugin actions can be invoked via the Plug-In Action in Shortcuts. For JXA/`osascript`-based Shortcuts (legacy), see `gtd-queries.js` — that channel is retained only for Shortcuts that must use `osascript`.

```
WebFetch https://omni-automation.com/shortcuts/index.html
Prompt: "List all Shortcuts integration capabilities. What URL schemes and action types are supported?"
```
