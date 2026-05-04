---
name: attache-analyst
description: |
  This skill should be used when analyzing OmniFocus system structure, discovering workflow patterns, running AI-enhanced GTD coaching, or learning the user's tool stack. Triggers when user asks "analyze my OmniFocus", "discover my system", "what's my structure", "AI coaching", "project health analysis", "system insights", "learn my workflow", "understand my patterns", "suggest improvements", "what tools do I use", or "update my tool stack".

  Do NOT trigger for: "show tasks" or "check inbox" (use omnifocus-core), "create OmniFocus plugin" (use omnifocus-generator), "what makes a good next action" (use gtd-coach for pure methodology).

  This skill is read-only against OmniFocus. It discovers patterns, infers structure, and persists learned insights via the Attache preferenceManager. It can read and update vault tool notes (status, usage patterns) via the archivist agent.
license: MIT
metadata:
  version: 1.0.0
  author: totally-tools
compatibility:
  platforms: [macos]
  requires:
    - OmniFocus 4.8+ (for Foundation Models actions)
    - macOS 26+ with Apple Silicon (for on-device AI)
---

# Attache Analyst

System learning, pattern detection, and AI-enhanced coaching for the Attache agent.

## Capabilities

### System Discovery
Discover the user's OmniFocus structure using hybrid rule-based and Foundation Models inference.

```bash
# Install/update the Attache plugin
open assets/Attache.omnifocusjs

# Trigger system discovery (writes System Map to task note)
SCRIPT='var p=PlugIn.find("com.totallytools.omnifocus.attache");var lib=p.library("systemDiscovery");var map=lib.discoverSystem({depth:"full"});var t=flattenedTasks.filter(function(t){return t.name==="Attache System Map"});if(t.length>0){t[0].note=JSON.stringify(map);Pasteboard.general.string="System Map updated v"+map.attacheVersion}else{Pasteboard.general.string="Task not found"}'
open "omnifocus://localhost/omnijs-run?script=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.stdin.read().strip()))" <<< "$SCRIPT")"
```

**System Map fields:**
- `tags.categories.contexts[]` — GTD context tags
- `tags.categories.people[]` — waiting/delegation tags
- `tags.categories.status[]` — someday/on-hold tags
- `tags.categories.duration[]` — duration/effort tags
- `tags.categories.schedulingContext[]` — time-of-day/week tags
- `structure.topLevelFolders[]` — folder names and inferred types
- `tasks.dataQuality.percentWithDuration` — derive durationModel

### Pattern Inference
The TypeScript libraries in `scripts/src/attache/` provide:

| Library | Purpose |
|---------|---------|
| `systemDiscovery.ts` | Hybrid pattern detection + FM semantic understanding |
| `taskMetrics.ts` | Single-pass task data collection |
| `projectParser.ts` | Folder/project type inference |
| `folderParser.ts` | Folder categorization |
| `insightPatterns.ts` | GTD health scoring, semantic patterns |
| `hierarchicalBatcher.ts` | Token budget management for batching |
| `foundationModelsUtils.ts` | FM availability, error handling, schema |
| `preferencesManager.ts` | Persistent user preference storage |
| `exportUtils.ts` | Data export and formatting |

### Tool Stack Awareness
Read the vault's `Tools.base` to discover the user's full tool landscape:
- Parse tool categories, statuses (Use/Trial/Assess/Hold), and host relationships
- Build a tool registry mapping tools to agents
- Update tool note usage patterns when observed

**Access via archivist agent** — do not read vault files directly.

### Attache Plugin (On-Device AI)
The `Attache.omnifocusjs` plugin provides 9 on-device AI actions:
- Daily and weekly GTD reviews
- Project analysis and health scoring
- System discovery with persistent memory
- Completed task summaries

Build: `bash scripts/build-attache.sh`

## Boundaries

- **Read-only** against OmniFocus data — never create, update, or delete tasks
- **Persist** learned patterns only via preferenceManager (non-invasive)
- **Defer** task mutations to omnifocus-core skill
- **Defer** plugin creation to omnifocus-generator skill

## Reference Documentation

- `references/foundation_models_integration.md` — Apple Intelligence API details
- `references/library_ecosystem.md` — Attache library architecture and overlap guide
- `references/insight_patterns.md` — GTD health scoring patterns
