# System Map Dependency (Doctrine)

**The rule:** Any generated plugin that does GTD-flavored coaching, querying, or organization MUST consume the Attache System Map. It is the single source of truth for the user's conventions (waiting tag, someday folder, default context tag, duration model). Do NOT hardcode conventions like `@waiting` or `Someday/Maybe` — those break on every user with a different setup.

See `../../attache-analyst/references/system_map_schema.md` for the schema (v1) and `system_map.schema.json` for the JSON Schema validator.

## When This Applies

Your generated plugin needs the System Map if it does any of:

- Lists "waiting for" items (needs `conventions.waitingTag`)
- Lists "someday/maybe" items (needs `conventions.somedayTag` AND/OR `somedayFolder`)
- Coaches on duration estimates (needs `durationModel`)
- Uses the user's actual context tags in UI prompts (needs `tags.categories.contexts` + `conventions.defaultContextTag`)
- Surfaces neglected projects, completed work by category, or review-due projects

If your plugin only does generic task CRUD (create, complete, update by ID), you don't need the System Map — use `ofoCore` alone (see `library_consumer_pattern.md`).

## The Consumer Pattern

Every System Map-aware plugin starts with this skeleton:

```js
(() => {
  // CONSTANT: bump when the System Map schema version changes you've validated against.
  const EXPECTED_SCHEMA_VERSION = 1;

  // Locate the System Map task (canonical storage: task note in OmniFocus)
  const SYSTEM_MAP_TASK_NAME = "Attache System Map";
  const candidates = flattenedTasks.filter(t => t.name === SYSTEM_MAP_TASK_NAME);
  if (candidates.length === 0) {
    new Alert("System Map Missing",
              "Run `ofo system-map --refresh` to discover your OmniFocus organization.").show();
    return;
  }
  const smTask = candidates[0];

  // Parse the note as JSON
  let sm;
  try {
    sm = JSON.parse(smTask.note || "{}");
  } catch (e) {
    new Alert("System Map Corrupt",
              "Run `ofo system-map --refresh` to regenerate.").show();
    return;
  }

  // Schema version contract:
  //   - Lower version: error and exit (we depend on fields the cached map doesn't have)
  //   - Higher version: warn and proceed (forward-compatible; some new fields ignored)
  if (typeof sm.schemaVersion !== "number") {
    new Alert("System Map Schema Unknown",
              "The cached map predates schema versioning. Run `ofo system-map --refresh`.").show();
    return;
  }
  if (sm.schemaVersion < EXPECTED_SCHEMA_VERSION) {
    new Alert("System Map Schema Stale",
              "Cached map is v" + sm.schemaVersion + " but this plugin needs v" + EXPECTED_SCHEMA_VERSION +
              ". Run `ofo system-map --refresh`.").show();
    return;
  }
  if (sm.schemaVersion > EXPECTED_SCHEMA_VERSION) {
    console.log("System Map schema v" + sm.schemaVersion + " is newer than expected v" +
                EXPECTED_SCHEMA_VERSION + "; proceeding (some fields may be ignored).");
  }

  // === Plugin logic from here ===
  const waitingTag = sm.conventions.waitingTag;
  if (!waitingTag) {
    new Alert("Convention Not Set",
              "Your System Map has no waitingTag. Tag at least one task with a waiting-style tag " +
              "(e.g. @waiting) and run `ofo system-map --refresh`.").show();
    return;
  }
  // ... use waitingTag to query, organize, coach, etc.
})()
```

## Finding the System Map Task

The canonical storage is the note field of a task named **"Attache System Map"** at the root of the user's OmniFocus database. To find it:

```js
const candidates = flattenedTasks.filter(t => t.name === "Attache System Map");
if (candidates.length === 0) {
  // Map not yet created — instruct user to refresh
}
const smTask = candidates[0];
```

**Why not `flattenedTasks.byName(...)`?** `TaskArray.byName` does exist (see `api_gaps.md`), but using `.filter` returns ALL matches — useful for detecting duplicates. If you want only the first match, `byName` is fine; just null-check the result.

## Schema Version Contract

`sm.schemaVersion` is a hard contract. Your plugin should declare which version it was written against (`EXPECTED_SCHEMA_VERSION`) and:

| Cached version | Plugin action |
|---|---|
| Missing (`typeof !== "number"`) | Error: predates versioning, force refresh |
| Lower than expected | Error: missing fields the plugin needs, force refresh |
| Equal to expected | Proceed normally |
| Higher than expected | Warn, proceed; ignore unknown fields |

**Never silently default** when a convention is missing. The whole point of the System Map is to eliminate guessing — if `conventions.waitingTag` is null, surface that to the user and instruct them to refresh (after they tag some tasks).

## Drift Awareness

If your plugin runs on a schedule or as a long-running action, consider checking drift before reading the map:

```js
// Optional: check age before relying on cached data
const generatedAt = new Date(sm.generatedAt);
const ageDays = (Date.now() - generatedAt.getTime()) / 86400000;
if (ageDays > 30) {
  new Alert("System Map Is " + Math.floor(ageDays) + " Days Old",
            "Consider running `ofo system-map --refresh` for current conventions.").show();
  // Decision: hard-block or warn-and-proceed depends on your plugin's risk tolerance
}
```

`ofo system-map --drift-check` performs a richer check (tag/folder count delta, broken convention, schema mismatch). See `../../attache-analyst/references/system_map_schema.md` "Drift Detection" for full signals.

## What This Doctrine Buys You

- **Per-user portability.** Your plugin works for anyone whose System Map is current, regardless of their tag naming or folder structure.
- **No silent failures.** Missing convention → explicit error pointing at the fix (`ofo system-map --refresh`).
- **Forward-compat.** Schema v2/v3 additions don't break your v1-aware plugin.
- **One source of truth.** When the user reorganizes, they refresh once; every plugin gets the new conventions.

## Cross-References

- `library_consumer_pattern.md` — `systemDiscovery` is listed as the SECOND mandatory library (after `ofoCore`) for GTD-flavored plugins
- `../../attache-analyst/references/system_map_schema.md` — full schema, convention resolution rules, drift detection signals
- `../../attache-analyst/references/system_map.schema.json` — JSON Schema (draft 2020-12) for machine validation
