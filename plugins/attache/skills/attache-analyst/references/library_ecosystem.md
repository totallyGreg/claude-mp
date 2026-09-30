# Library Ecosystem (Attache Plugin)

All libraries are compiled from TypeScript sources in `scripts/src/attache/*.ts` and bundled into `Attache.omnifocusjs`. Load via `this.plugIn.library("name")` inside action scripts.

## Architecture

```
Attache.omnifocusjs (com.totallytools.omnifocus.attache)
├── Core Layer
│   ├── ofoCore       ← CRUD, dispatch, normalizeTask, computeStats
│   ├── taskMetrics   ← single-pass collector, WAITING_PATTERNS
│   └── exportUtils   ← format conversion, clipboard/file export
├── Analytics Layer
│   ├── taskParser         ← task clarity scoring
│   ├── projectParser      ← stalled project detection
│   ├── folderParser       ← folder hierarchy analysis
│   ├── insightPatterns    ← pattern detection, GTD insights
│   ├── hierarchicalBatcher ← batch task creation
│   ├── systemDiscovery    ← GTD system pattern detection
│   └── preferencesManager ← device-scoped preferences
├── AI Layer
│   └── foundationModelsUtils ← Apple Intelligence wrapper
└── Actions (JS)
    └── dailyReview, weeklyReview, analyzeSelected, etc.
```

## Library Cross-Reference Pattern

Libraries are self-contained IIFEs — they **cannot** load other libraries. Only action scripts can call `this.plugIn.library()`. When a library needs another library's function, the action passes it as a parameter:

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    const core = this.plugIn.library("ofoCore");
    const metrics = this.plugIn.library("taskMetrics");
    const all = metrics.collectAllMetrics(core);  // metrics calls core.normalizeTask()
});
```

## Libraries

### `ofoCore` (TypeScript — `scripts/src/ofo-core.ts`)
CLI dispatch layer. 17 named exports: `getTask`, `completeTask`, `createTask`, `updateTask`, `searchTasks`, `listTasks`, `getPerspective`, `configurePerspective`, `tagTask`, `getTags`, `createBatch`, `getPerspectiveRules`, `dumpDatabase`, `getStats`, `assessClarity`, `stalledProjects`, `dispatch`.

Canonical `normalizeTask()` returns 16-field `OfoTask` with Date objects (JSON.stringify auto-converts for CLI).

### `taskMetrics` (TypeScript — `scripts/src/attache/taskMetrics.ts`)
Data collection. Functions accept `core` parameter for `normalizeTask` delegation.
- `collectAllMetrics(core)` — single-pass bucket: inbox/today/overdue/flagged/completedToday/deferredToday
- `getTodayTasks(core)`, `getOverdueTasks(core)`, `getFlaggedTasks(core)` — filtered queries
- `getCompletedToday()`, `getCompletedThisWeek()`, `getCompletedThisMonth()` — completed task queries
- `getOnHoldProjects()` — stale on-hold projects
- `WAITING_PATTERNS` — canonical `["waiting", "delegated", "pending", "w:"]`

### `exportUtils` (TypeScript — `scripts/src/attache/exportUtils.ts`)
Export data to multiple formats and destinations.
- `toClipboard(data, {format})` — copy JSON/CSV/Markdown/HTML to clipboard
- `toFile(data, {format, path})` — write to file

### `insightPatterns` (TypeScript — `scripts/src/attache/insightPatterns.ts`)
Pattern detection and analysis.
- `detectStalledProjects(doc)` — projects with no available next actions
- `detectOverloaded(doc)` — excessive task accumulation
- `generateInsights(doc)` — combined insight report

### `taskParser` (TypeScript — `scripts/src/attache/taskParser.ts`)
Enhanced task parsing with clarity assessment and GTD metrics.

### `projectParser` (TypeScript — `scripts/src/attache/projectParser.ts`)
Project parsing with metrics and GTD health indicators.

### `folderParser` (TypeScript — `scripts/src/attache/folderParser.ts`)
Folder hierarchy analysis with recursive subfolder parsing.

### `hierarchicalBatcher` (TypeScript — `scripts/src/attache/hierarchicalBatcher.ts`)
Hierarchical batch operations for large data processing within Foundation Model context windows.

### `systemDiscovery` (TypeScript — `scripts/src/attache/systemDiscovery.ts`)
GTD system pattern detection. 1189 lines — most complex library.
- `discoverSystem({depth, waitingPatterns})` — rule-based + optional AI system discovery
- `calculateGTDHealth(rawData)` — 5-phase GTD health scoring
- `toMarkdown(systemMap)` / `toJSON(systemMap)` — formatted output

### `preferencesManager` (TypeScript — `scripts/src/attache/preferencesManager.ts`)
Device-scoped preferences using OmniFocus Preferences API.

### `foundationModelsUtils` (TypeScript — `scripts/src/attache/foundationModelsUtils.ts`)
Apple Intelligence wrapper for Foundation Models on-device inference.
- `isAvailable()` — check LanguageModel API availability
- `createSession(systemPrompt)` — create FM session
- `showUnavailableAlert()` — standard error alert

## Build Pipeline

```bash
npm run build        # Compiles ofoCore + 10 libraries + copies 7 actions → Attache.omnifocusjs
npm run deploy       # open ../../attache-analyst/scripts/build/Attache.omnifocusjs (the canonical built bundle)
```

All libraries are compiled from TypeScript via `tsconfig.attache-libs.json`. The build script validates IIFE structure for every compiled library.
