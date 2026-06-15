# Attache System Map — Schema Contract (v1)

The **Attache System Map** is a JSON document that captures the user's OmniFocus organizational conventions: tag taxonomy, folder structure, GTD-essential conventions (waiting tag, someday folder, etc.), data quality signals, and duration model. It is the single source of truth that all D6 GTD queries and gtd-coach data-grounded coaching depend on.

This doc is the contract. Consumers MUST validate against `system_map.schema.json` (companion file in this directory) before reading fields they depend on.

## Storage Convention

The System Map is stored as JSON-encoded text in the `note` field of a task named **"Attache System Map"** at the root of the user's OmniFocus database.

- Producer: `systemDiscovery.discoverSystem({depth})` library function, invoked by the `discoverSystem` action in `Attache.omnifocusjs` OR by `ofo system-map --refresh` (D7.3 CLI).
- Consumer: `ofo` CLI dispatch layer (D6 GTD queries), gtd-coach pre-flight check (D6.4 STEP 0), generated plugins (D7.7 system_map_dependency.md).
- Refresh cadence: on demand via the refresh CLI, or auto-prompted when drift is detected (D7.4).

## Top-Level Fields (schema v1)

```ts
interface SystemMap {
  // ──────── Versioning ────────
  schemaVersion: 1;                          // const — consumers compare and refuse mismatched schemas
  attacheVersion: string;                    // version of the Attache plugin that produced this map (e.g., "1.4.4")
  generatedAt: string;                       // ISO-8601 timestamp of last discoverSystem() call
  discoveryMode: 'rules-only' | 'rules-plus-fm'; // whether Foundation Models was available at discovery time
  discoveryDepth: 'quick' | 'full';          // discoverSystem() depth argument (full includes task sample)
  aiEnhanced: boolean;                       // true if discoverWithAI() was layered on top

  // ──────── Resolved Conventions (the GTD-essential block) ────────
  conventions: {
    waitingTag: string | null;               // name of the Waiting-For tag (e.g., "@waiting")
    somedayTag: string | null;               // name of the Someday/Maybe tag (e.g., "@someday")
    somedayFolder: string | null;            // name of the Someday/Maybe folder (e.g., "Someday Maybe")
    waitingForFolder: string | null;         // name of the Waiting-For folder (if folder-based)
    defaultContextTag: string | null;        // most-used context tag (e.g., "@computer")
  };

  // ──────── Tag Taxonomy ────────
  tags: {
    totalTags: number;
    taxonomyStyle: 'flat' | 'hierarchical' | 'mixed';
    categories: {
      contexts: TagEntry[];                  // @home, @computer, @phone, @errands
      people: TagEntry[];                    // delegated/waiting tags (e.g., "Waiting:Sarah")
      status: TagEntry[];                    // hold/someday/maybe/review
      energy: TagEntry[];                    // high/medium/low/quick/deep
      duration: TagEntry[];                  // 15min/30min/1hr/2hr (task duration estimates)
      schedulingContext: TagEntry[];         // morning/afternoon/evening/weekend (when-to-work)
      time: TagEntry[];                      // legacy: union of duration + schedulingContext (kept for backward compat)
      areas: TagEntry[];                     // top-level life areas if tagged
      uncategorized: TagEntry[];             // tags that didn't match any pattern
    };
    categoryCounts: Record<string, number>;
    conventions: {                           // raw pattern signals (input to conventions.* resolution above)
      usesAtPrefix: boolean;
      usesColonNesting: boolean;
      usesEmoji: boolean;
      usesCamelCase: boolean;
      averageNameLength: number;
    };
  };

  // ──────── Folder Structure ────────
  structure: {
    folderDepth: number;                     // max nesting depth
    totalFolders: number;
    totalProjects: number;
    totalActiveTasks: number | null;         // null in quick mode
    topLevelFolders: Array<{
      name: string;
      inferredType: 'area' | 'archive' | 'someday' | 'reference' | 'general';
      confidence: 'high' | 'medium' | 'low';
      projectCount: number;
      activeProjectCount: number;
      subfolderCount: number;
      aiInferredType?: string;               // present only if aiEnhanced
      aiConfidence?: 'high' | 'medium' | 'low';
      aiReasoning?: string;
    }>;
  };

  // ──────── Projects ────────
  projects: {
    total: number;
    active: number;
    onHold: number;
    completed: number;
    dropped: number;
    stalled: number;                         // active projects with no available next actions
    overdue: number;
    typeBreakdown: {
      sequential: number;
      parallel: number;
      singleAction: number;
    };
  };

  // ──────── Tasks (full mode only) ────────
  tasks: {
    total: number;
    active: number;
    inInbox: number;
    flagged: number;
    overdue: number;
    dataQuality: {
      percentWithDuration: number;           // 0-100 — drives durationModel
      percentWithTags: number;               // 0-100
      percentWithDueDate: number;            // 0-100
      percentWithProject: number;            // 0-100 — % of tasks assigned to a project (vs inbox-only)
    };
  } | null;                                  // null when depth === 'quick'

  // ──────── Derived Duration Model ────────
  durationModel: 'native' | 'tags' | 'mixed' | 'none';
  // Resolution from tasks.dataQuality.percentWithDuration (see "Convention Resolution Rules" below):
  //   >= 50% → 'native'        (user reliably uses estimatedMinutes)
  //   10-49% → 'mixed'         (user uses native estimates AND duration tags)
  //   1-9%   → 'tags'          (estimates are rare; rely on duration tags if present)
  //   0%     → 'none'          (user has no duration practice — coach to start one)
  // When tasks is null (quick mode), durationModel is omitted.

  // ──────── GTD Health (informational; not a contract field for D6 queries) ────────
  gtdHealth: {
    overallScore: number;                    // 0-10 weighted across phases
    phases: {
      collection: { score: number; inboxSize: number; assessment: string };
      clarifying: { score: number; taskClarity: number; assessment: string };
      organizing: { score: number; folderStructure: string; assessment: string };
      reviewing: { score: number; stalledProjects: number; assessment: string };
      engaging: { score: number; nextActionAvailability: number; assessment: string };
    };
  };

  // ──────── Recommendations (informational) ────────
  recommendations: Array<{
    area: 'inbox' | 'projects' | 'durations' | 'tags' | 'due-dates' | 'contexts' | string;
    severity: 'high' | 'medium' | 'low';
    finding: string;
    suggestion: string;
  }>;
}

interface TagEntry {
  tag: string;
  usage: number;            // task count using this tag
  meaning: string | null;   // human-readable hint inferred from pattern
  hasChildren: boolean;
}
```

## Convention Resolution Rules

`conventions.*` fields are derived from `tags.categories.*` and `structure.topLevelFolders`. The producer (`systemDiscovery.discoverSystem`) computes them once at discovery time. Consumers MUST read from `conventions.*` rather than re-deriving — this prevents inconsistency.

| Field | Resolution rule |
|---|---|
| `conventions.waitingTag` | First tag in `tags.categories.people` whose name matches `/wait/i`. Fallback: first in `status` matching `/wait/i`. Fallback: `null`. |
| `conventions.somedayTag` | First tag in `tags.categories.status` whose name matches `/someday\|maybe/i`. Fallback: `null`. |
| `conventions.somedayFolder` | First folder in `structure.topLevelFolders` whose `inferredType === 'someday'`. Fallback: first whose `name` matches `/someday\|maybe/i`. Fallback: `null`. |
| `conventions.waitingForFolder` | First folder in `structure.topLevelFolders` whose `name` matches `/wait/i`. Most users tag-based, not folder-based — usually `null`. |
| `conventions.defaultContextTag` | The tag in `tags.categories.contexts` with the highest `usage` count. Fallback: `null`. |

`null` is a meaningful value — it means *"this convention does not exist in this user's setup."* Downstream queries handle null by emitting a structured error to the CLI (per D6.3 resolution chain: explicit flag → System Map convention → structured error pointing to `ofo system-map --refresh`).

## Forward-Compatibility Rule

When adding fields → bump `schemaVersion` by 1 and update this doc.
When removing or renaming fields → bump `schemaVersion` AND publish a migration note inline below.
Old consumers MUST detect a higher `schemaVersion` than expected and either:
- Read only the fields they recognize (best effort), OR
- Emit a warning: *"System Map produced by newer Attache (schemaVersion=N); some fields may not be understood. Consider upgrading consumers."*

## Migration Notes

(None yet — schema is at v1.)

## See Also

- `system_map.schema.json` — JSON Schema for machine validation
- Plan: `plugins/attache/docs/plans/2026-06-15-001-attache-references-routing-plan.md` D7.2
- Producer: `plugins/attache/skills/attache-analyst/scripts/src/attache/systemDiscovery.ts`
- Consumer doctrine: `plugins/attache/skills/omnifocus-generator/references/system_map_dependency.md` (D7.7)
- CLI: `ofo system-map [--show | --refresh | --drift-check | --validate]` (D7.3)
- Drift detection: `ofo system-map --drift-check` reasons defined in this doc's "Drift Detection" section below.

## Drift Detection

The `ofo system-map --drift-check` command (D7.4) checks the live OmniFocus database against the cached System Map and returns `{stale: bool, reasons: string[], lastRefresh: ISO}`. Signals:

| Signal | Threshold | Reason string |
|---|---|---|
| Schema mismatch | Map's `schemaVersion` < current expected | `"schema-stale: map vN, current schema vM"` |
| Age | `generatedAt` older than `ATTACHE_MAP_MAX_AGE_DAYS` (default 30) | `"age-stale: refreshed N days ago"` |
| Tag-count delta | Current `flattenedTags.length` vs `Σ(tags.categories.*.length)` differs by > 10% | `"tag-drift: N tags added/removed since last refresh"` |
| Folder-count delta | Current top-level folder count vs `structure.topLevelFolders.length` differs by > 10% | `"folder-drift: top-level folder count changed"` |
| Broken convention | `conventions.waitingTag` (or any other named convention) no longer exists in `flattenedTags.byName` | `"convention-broken: waitingTag 'X' no longer exists"` |

Drift is information, not failure — the command exits 0 with `stale: true`. Consumers decide whether to refresh or warn-and-proceed.
