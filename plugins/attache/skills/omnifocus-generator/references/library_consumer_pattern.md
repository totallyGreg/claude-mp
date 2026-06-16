# Shared-Library Doctrine: Consume ofoCore

**The rule:** `ofoCore` is the shared library shipped with the Attache plugin. Every generated plugin that touches tasks, projects, tags, folders, or perspectives **MUST consume it** via `PlugIn.find(...).library("ofoCore")` rather than reimplementing CRUD. This eliminates per-plugin drift in behavior, error handling, and field shapes.

A second mandatory library applies to GTD-flavored plugins: `systemDiscovery` (the System Map producer/consumer). See `system_map_dependency.md` for that doctrine.

## The Pattern

Every generated plugin starts with this skeleton:

```js
(() => {
  // Required dependency: Attache plugin (provides ofoCore + systemDiscovery libraries)
  const attache = PlugIn.find("com.totallytools.omnifocus.attache");
  if (!attache) {
    new Alert("Attache Required",
              "This plugin requires the Attache plugin (v1.5+). " +
              "Install from <repo URL>.").show();
    return;
  }

  const ofoCore = attache.library("ofoCore");
  if (!ofoCore || typeof ofoCore.getTask !== "function") {
    new Alert("Attache Out of Date",
              "Attache 'ofoCore' library is missing required functions. " +
              "Please update Attache.").show();
    return;
  }

  // === Plugin logic from here ===
  const task = ofoCore.getTask({ id: someTaskId });
  if (!task.success) {
    new Alert("Lookup Failed", task.error).show();
    return;
  }
  console.log("Got task: " + task.task.name);
})()
```

The dual null-check (`!attache` then `!ofoCore || typeof ofoCore.X !== "function"`) is the safety net for two failure modes:
1. Attache plugin not installed → first check
2. Attache installed but at a version that predates a function you depend on → second check

## What ofoCore Exposes Today

Generated 2026-06-15 from `plugins/attache/skills/omnifocus-core/scripts/src/ofo-core.ts`. **Regenerate this table when `ofo-core.ts` changes** — see "Maintenance" below.

### Task CRUD
| Function | Signature | Purpose |
|---|---|---|
| `getTask({id, type?})` | type: 'task' \| 'project' \| 'tag' | Fetch by primary key; returns normalized shape |
| `completeTask({id})` | — | Safe complete via `markComplete()` |
| `dropTask({id, allOccurrences?})` | — | Drop single or all repeating occurrences |
| `createTask({name, project?, note?, flagged?, due?, defer?, estimate?, plannedDate?, tags?})` | — | Create in inbox or project |
| `updateTask({id, ...fields})` | — | Mutate name/note/dates/flagged/tags/project |
| `createBatch({items})` | — | Batch create (array of createTask args) |

### Project CRUD (D6.2 — new)
| `createProject({name, folder?, sequential?, note?, due?, defer?, flagged?, reviewInterval?})` | — | Create project at root or in folder |
| `updateProject({id, name?, note?, status?, folder?, due?, defer?, sequential?, flagged?})` | status: 'active' \| 'onHold' \| 'completed' \| 'dropped' | Mutate project |
| `markProjectReviewed({id, reviewDate?})` | — | Set `lastReviewDate` (advances `nextReviewDate`) |

### Queries
| `searchTasks({query, limit?})` | — | Search task name + note |
| `listTasks({filter, limit?, days?})` | filter: 'inbox'\|'flagged'\|'today'\|'overdue'\|'due-soon' | Built-in lists |
| `listFolders({includeProjects?})` | — | Folder hierarchy as tree (D6.2) |

### GTD-essential queries (D6.2 — System Map convention-dependent)
| `listWaitingFor({tag, ageThresholdDays?, limit?})` | **@requires** SystemMap.conventions.waitingTag | Tasks with waiting tag, optionally age-filtered |
| `listSomedayMaybe({tag?, folder?, limit?})` | **@requires** SystemMap.conventions.{somedayTag, somedayFolder} | Tasks in someday tag OR all tasks under someday folder's projects |
| `listNeglectedProjects({daysSinceModified?, limit?})` | — | Active projects not modified in N days (default 30) |
| `listRecentlyCompleted({sinceDate?, groupByTag?, limit?})` | — | Completed tasks since date; optional tag grouping |
| `listProjectsForReview({beforeDate?, limit?})` | — | Active/onHold projects with `nextReviewDate ≤ beforeDate` |

### Tag operations
| `tagTask({id, add?, remove?})` | — | Add/remove tags by name |
| `getTags()` | — | Full tag hierarchy as JSON |

### Perspectives
| `getPerspective({name? \| id?, limit?})` | — | Query a custom perspective |
| `configurePerspective({name? \| id?, rules?, aggregation?})` | — | Set filter rules |
| `getPerspectiveRules({name?})` | — | Get rules for one or all custom perspectives |

### Analytics / health
| `getStats()` | — | Counts: inbox, flagged, overdue, activeProjects, etc. |
| `getHealth()` | — | Inbox + overdue + flagged tasks in one call |
| `dumpDatabase()` | — | Snapshot of active tasks/projects/perspective names |
| `assessClarity({limit?})` | — | Tasks with lowest clarity score (no estimate/tags/project) |
| `stalledProjects({days?})` | — | Active projects with no available next action |

**29 functions total** as of v1.5.0. All return `OfoResult` shape: `{success: boolean, error?: string, ...}`.

## The Dependency Contract

A generated plugin that consumes `ofoCore` declares a runtime dependency on the Attache plugin. Document this:

1. In your plugin's `manifest.json` `description` field:
   > "Requires the Attache plugin (com.totallytools.omnifocus.attache) v1.5+ for the ofoCore library."

2. In your plugin's startup code: the dual null-check skeleton above. Don't just call `PlugIn.find(...).library(...).getTask(...)` and hope — that crashes with a confusing error.

3. In your plugin's README (if it has one): the install order. Users install Attache first, then your plugin.

## When to Add to ofoCore vs. Inline

**Rule of thumb:** If the function would be useful to **2+ plugins OR to the ofo CLI**, add it to `ofoCore`. Otherwise inline it.

Adding to `ofoCore` is a 4-step process:
1. Write the function in `plugins/attache/skills/omnifocus-core/scripts/src/ofo-core.ts` following the existing patterns (uses `normalizeTask`, returns `OfoResult`, errors as data).
2. Add an `OfoAction` value in `ofo-types.ts`, `ofo-contract.d.ts`, AND `ofo-core-ambient.d.ts` (all three need to match). The exhaustiveness check in `dispatch()` will error at compile time if you miss the switch case.
3. Add a `dispatch()` case.
4. Add a CLI command in `ofo-cli.ts` if shell access is wanted. Rebuild via `build-attache.sh` (D6.6).

Adding a function to `ofoCore` requires a bump of `ATTACHE_VERSION` in `systemDiscovery.ts` AND a manifest version bump (per memory: OmniFocus won't recognize updates without a version bump).

## Library Generation for Non-Attache Shared Code

If your generated plugin needs reusable code that doesn't belong in `ofoCore` (e.g., a domain-specific helper for a specific workflow), the `solitary-library` format produces a stand-alone `PlugIn.Library` that other plugins can `find().library()`. See `plugin_format_selection.md`.

Pattern: don't bloat `ofoCore` with one-off helpers; do bloat it with anything used twice.

## Anti-Patterns to Avoid

- **Reimplementing task CRUD inline.** If `ofoCore.createTask` exists, don't write `var t = new Task(...)` in your plugin. The library handles edge cases (plannedDate try/catch, tag-not-found warnings, etc.) you'll forget.
- **Skipping the null-check.** `PlugIn.find(...).library(...).getTask(...)` crashes if Attache isn't installed. Always assign and check.
- **Pinning to a specific Attache version via string compare.** Use the dual null-check pattern instead — it's resilient to version-string format changes.
- **Silently catching errors from ofoCore.** If `result.success === false`, surface `result.error` to the user. The error string is designed for human display.

## Maintenance

This doc's function table reflects `ofo-core.ts` as of the date in the section header. When `ofo-core.ts` changes:

1. Regenerate the table (manually grep for `function X(args: OfoArgs)` in `ofo-core.ts`).
2. Update the version note in "What ofoCore Exposes Today" header.
3. Bump the function count.

For the broader CLI surface expansion (commands beyond what this library exposes), see issue #141.

## Cross-References

- `system_map_dependency.md` — the OTHER mandatory library: `systemDiscovery` for GTD-flavored plugins
- `plugin_format_selection.md` — choosing between solitary / solitary-fm / bundle / solitary-library
- `validation_pipeline.md` — pre-emit + post-emit checks the generator runs on your code
- `../../omnifocus-core/scripts/src/ofo-core.ts` — the canonical source (read this if the table above looks stale)
