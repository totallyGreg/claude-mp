# Channel Selection Guide

Before choosing a script or plugin, determine which automation channel to use.

**Default: Mac/JXA.** Only consider other channels when the user explicitly mentions iOS, iPhone, iPad, or mobile.

## Agent Capability by Channel

| Channel | Agent Executes | Agent Prepares | Limitation |
|---|---|---|---|
| **ofo CLI** (script URLs) | Full read + write via pasteboard | Stable action scripts | Requires one-time script approval; pasteboard return only |
| **JXA** (osascript) | Advanced queries (GTD diagnostics, perspectives) | Full generation | Mac only; `task.completed=true` fails via Apple Events |
| **Omni Automation Plugin** | Cannot invoke from CLI | Full generation + install | User triggers from OmniFocus UI |
| **omnifocus:// URL** (native) | Fire-and-forget (`open`) | Full generation | No result feedback (add, navigate, search only) |
| **Apple Shortcuts** | Run existing only | Generate script code | Cannot create shortcuts programmatically |
| **Omni-links** | N/A | Generate link text | Navigation/reference only |

## Decision Tree

```
Is this a task CRUD operation? (info, complete, create, update, search, list)
  YES → Use ofo CLI: scripts/ofo <command>
        Handles omnifocus:// URL parsing, returns JSON via pasteboard
  NO → Is this a Mac-only request? (DEFAULT — assume yes unless user says otherwise)
    YES → Use JXA scripts (gtd-queries.js for diagnostics, perspective-config.js for perspectives)
          If no existing script covers it, compose from taskQuery.js / taskMutation.js
    NO (user mentions iPhone/iPad/iOS/mobile) →
      1. Reference/navigation only? → Generate omnifocus:// perspective or task link
      2. Needs trigger (time, location, Focus mode)? → Generate Omni Automation script code + setup instructions for Apple Shortcuts
      3. Otherwise → Generate Omni Automation plugin (cross-device, no security friction)
      NOTE: For iOS requests, the agent PREPARES artifacts — the user completes setup.
```

## URL Scheme Security Friction

| URL Type | Friction | Use When |
|---|---|---|
| `omnifocus:///task/<id>` | None | Navigation links in Obsidian |
| `omnifocus:///perspective/<name>` | None | Query links — **preferred** |
| `omnifocus:///add?name=...` | None | Quick capture (no ID returned) |
| `omnifocus:///omnijs-run?script=...&arg=...` | **One-time** (per stable script) | ofo CLI uses this with `&arg=` for reusable approved scripts |

The `&arg=` parameter makes script URLs practical: the script body is approved once, and variable data (task IDs, filters) flows through `&arg=` without re-approval. The `ofo` CLI wraps this pattern with 6 stable action scripts.

See `omnifocus_url_scheme.md` for full URL scheme documentation and Obsidian embedding patterns.

## JXA Safety Rules

- Generated JXA code MUST NOT use `$.NSTask`, `doShellScript`, `$.NSURLSession`, or import ObjC frameworks beyond `Foundation` and `stdlib`.
- For requests not covered by existing commands, compose from `taskQuery.js` and `taskMutation.js` library functions.
- After fixing any JXA API bug, search all files in `scripts/` and `scripts/libraries/jxa/` for the same pattern and fix every instance.
- All SKILL.md routing changes require user approval.
- Run `node scripts/validate-jxa-patterns.js scripts/libraries/jxa/` to check for known anti-patterns.

## Library Composition

**PHILOSOPHY:** Compose from libraries BEFORE generating new code.

### Available Libraries (`scripts/libraries/omni/`)

| Library | Functions |
|---------|-----------|
| `taskMetrics.js` | getTodayTasks, getOverdueTasks, getCompletedToday, getFlaggedTasks |
| `exportUtils.js` | toJSON, toCSV, toMarkdown, toHTML, toClipboard, toFile |
| `completedTasksFormatter.js` | formatAsMarkdown (with project grouping) |
| `patterns.js` | queryAndAnalyzeWithAI, queryAndExport, batchUpdate |
| `insightPatterns.js` | detectStalledProjects, detectWaitingForAging |
| `treeBuilder.js` | OmniFocus 4 tree API support (v4.1+) |

### Usage in Bundle Plugins

Declare in manifest.json:
```json
{
  "libraries": [
    { "identifier": "taskMetrics" },
    { "identifier": "exportUtils" }
  ]
}
```

Use in actions:
```javascript
const metrics = this.plugIn.library('taskMetrics');
const tasks = metrics.getTodayTasks();
```

See `scripts/libraries/README.md` for complete library documentation.

## Automation Approach Summary

| Approach | Platform | Use For |
|----------|----------|---------|
| **Omni Automation** | Mac + iOS | Reusable plugins, cross-platform |
| **JXA** | Mac only | Scripts, scheduled tasks, external automation |
| **URL Scheme** | Mac + iOS | Quick capture, embedding in notes |
| **Database** | Mac only | Complex SQL queries (last resort) |
