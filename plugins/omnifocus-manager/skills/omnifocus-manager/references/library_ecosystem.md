# Library Ecosystem (`scripts/libraries/omni/`)

Undeployed `PlugIn.Library` files available for use inside OmniFocus feature plugins alongside ofoCore. Load via `this.plugIn.library("name")` after declaring in `manifest.json` libraries array.

## Libraries

### `taskMetrics`
Data collection: `collectAllMetrics`, `getTodayTasks`, `getOverdueTasks`, `getUpcomingTasks(days)`, `getTasksByTag(name)`, `getTasksByProject(name)`, `getSummaryStats`, `normalizeTask`, `WAITING_PATTERNS`.

**Single-pass collector:** `collectAllMetrics()` buckets inbox/today/overdue/flagged/completedToday/deferredToday in one `flattenedTasks` pass — 4–5x faster than calling individual methods on large databases. Prefer it over multiple calls when multiple categories are needed.

**Canonical waiting-for patterns:** `lib.WAITING_PATTERNS = ["waiting", "delegated", "pending", "w:"]` is exported as a constant. Any action or library that detects waiting-for items must reference this — do not hardcode local arrays. `systemDiscovery.js` uses `WAITING_PREFIXES` aligned to this list.

```javascript
const metrics = this.plugIn.library("taskMetrics");
const all = metrics.collectAllMetrics(); // { inbox: [], today: [], overdue: [], ... }

function isWaitingFor(task) {
    const names = task.tags.map(t => t.name.toLowerCase());
    return names.some(n => metrics.WAITING_PATTERNS.some(p => n.includes(p)));
}
```

**ofoCore overlap:** basic filters (`today`, `overdue`, `flagged`) are covered by `ofoCore.listTasks({filter})`. Unique to taskMetrics: `collectAllMetrics` single-pass, `getUpcomingTasks(days)`, `getTasksByTag`, `getTasksByProject`, richer `normalizeTask` (includes `added`, `modified`, `taskStatus`, estimate aggregation), `WAITING_PATTERNS` constant. Prefer ofoCore for basic queries; use taskMetrics when you need upcoming-N-days, tag/project-scoped lists, or the canonical waiting-for patterns.

### `exportUtils`
Export data to multiple formats and destinations.
- `toClipboard(data, {format})` — copy JSON/CSV/Markdown/HTML to clipboard
- `toFile(data, {format, path})` — write to file
- No ofoCore overlap — ofoCore returns structured JSON; exportUtils handles formatting and delivery.

### `insightPatterns`
Pattern detection and analysis on top of raw OmniFocus data.
- `detectStalledProjects(doc)` — projects with no available next actions
- `detectOverloaded(doc)` — projects/tags with excessive task accumulation
- `generateInsights(doc)` — combined insight report with cause and recommendation fields

Richer than `ofoCore.getStats()` which returns counts only. No ofoCore overlap.

### `patterns`
MCP-ready high-level orchestration patterns.
- `queryAndExport({query, export})` — query tasks then export in one call
- `queryAndAnalyzeWithAI({query, prompt})` — query + AI analysis
- `batchUpdate({filter, updates})` — batch mutations

Depends on taskMetrics + exportUtils + insightPatterns. All four must be deployed together. Designed for direct use in OmniFocus plugin actions or future MCP server tool definitions.

### `completedTasksFormatter`
Formats completed-task arrays as grouped Markdown (grouped by project).
- `formatAsMarkdown(tasks)` → formatted string with date header and project sections

Takes task objects as input (does not query OmniFocus directly). Intended for use inside plugin actions that already have the task array (e.g. from `ofoCore.listTasks` or Attache's daily review). Different from the CLI's `ofo completed-today --markdown` which handles query + format in one step.

### `templateEngine`
Template-driven bulk task creation.
- `loadTemplates(path)` — load template definitions from JSON file
- `fillTemplate(template, vars)` — substitute `{{VAR}}` placeholders
- `createFromTemplate(doc, templateName, vars)` — create tasks/projects from a named template

ofoCore's `createBatch` handles raw array creation; templateEngine adds the template management layer above it.

### `treeBuilder`
Build and export tree structures from OmniFocus hierarchies (1103 lines).
- `buildTreeFromDatabase({includeMetrics})` — folder/project/task tree from database
- `buildTreeFromWindow(window, type)` — tree from OF4 window content or sidebar
- `exportToMarkdown(tree)`, `exportToJSON(tree)`, `exportToOPML(tree)` — format conversion
- `revealNodes(window, ids)` — programmatic tree navigation (OF4)

No ofoCore overlap. Highest-complexity library; only needed when hierarchical structure or OPML export is required.

## Deployment Notes

These libraries are not deployed as part of the standard ofo-core plugin. To use them in a feature plugin:

1. Copy desired library files into the plugin bundle's `Resources/` directory
2. Declare in `manifest.json` under `"libraries"`: `["ofoCore", "taskMetrics", ...]`
3. Load in action scripts: `const metrics = this.plugIn.library("taskMetrics");`

For plugins that load ofoCore, prefer `ofoCore.listTasks` for basic queries and fall back to taskMetrics only for the unique functions listed above.
