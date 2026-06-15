# WebFetch Protocol for One-Off Capability Lookups

<!-- DRAFT — review during D2 integration -->

**Purpose:** When a `20_capabilities/*.md` doc says "if your specific case isn't covered here, fetch X" — this file defines the contract for that one-off fetch.

Use this protocol **sparingly** — each WebFetch costs tokens and time. If you find yourself fetching 3+ pages for a single plugin-building task, that's a signal to update the capability docs instead.

---

## When to Use

Use a one-off WebFetch when:
1. A capability doc explicitly tells you to ("reach-out trigger")
2. A specific class method isn't in the local docs and you need the exact signature
3. You're writing the inventory refresh workflow (see `inventory_refresh_workflow.md`)

Do NOT use when:
- You're looking for something that's clearly in `20_capabilities/*.md`
- You're tempted to "double-check" the local docs — trust them until you have evidence of drift
- The token budget for this generation task is already high

---

## Fetch Template

```
WebFetch https://omni-automation.com/omnifocus/<slug>.html
Prompt: "I'm building an OmniFocus plugin and need the exact API for [CLASS.METHOD].
List the full signature, parameters, return type, and any version requirements (iOS/macOS minimum, 
Apple Silicon, etc.). Show a brief usage example if available. Be concise — 100 words max."
```

For Foundation Models specifically:
```
WebFetch https://omni-automation.com/shared/alm.html
WebFetch https://omni-automation.com/shared/alm-schema.html
Prompt: "Extract the complete signature for [LanguageModel.Schema.fromJSON / Session.respondWithSchema / etc.]
including all schema element types (arrayOf, properties, anyOf, constant, referenceTo).
Show the JSON schema format with a one-line example."
```

---

## Known Good URLs (2026-06-15)

| Topic | URL |
|-------|-----|
| Task class | `https://omni-automation.com/omnifocus/task.html` |
| Project class | `https://omni-automation.com/omnifocus/project.html` |
| Tag class | `https://omni-automation.com/omnifocus/tag.html` |
| Folder class | `https://omni-automation.com/omnifocus/folder.html` |
| Database class | `https://omni-automation.com/omnifocus/database.html` |
| Perspective | `https://omni-automation.com/omnifocus/perspective.html` |
| FileWrapper | `https://omni-automation.com/omnifocus/filewrapper.html` |
| Settings | `https://omni-automation.com/omnifocus/settings.html` |
| ForecastDay | `https://omni-automation.com/omnifocus/forecast.html` |
| Document/App | `https://omni-automation.com/omnifocus/document.html` |
| TaskPaper | `https://omni-automation.com/omnifocus/taskpaper.html` |
| App-to-App | `https://omni-automation.com/omnifocus/app-to-app.html` |
| Full API ref | `https://omni-automation.com/omnifocus/OF-API.html` |
| LanguageModel | `https://omni-automation.com/shared/alm.html` |
| LM Schema | `https://omni-automation.com/shared/alm-schema.html` |

**Note:** Form, PlugIn, and Library API is NOT on omni-automation.com as a standalone page. Use `30_api_reference/omnifocus_api.md` for those classes.

---

## Token-Cost Reminder

Each WebFetch + processing costs roughly 1,000–3,000 tokens. For a plugin-building task, the budget is:

- **≤3 reference files** (~3KB each) before generating code
- **≤2 WebFetches** for gap-filling
- If you need more, that's a signal to update `20_capabilities/*.md` after the task

Record what you fetched and what you learned in the commit message so the docs can be improved.
