# OmniFocus Manager Assets

Plugins, templates, and examples for OmniFocus automation.

## Directory

```
assets/
├── Attache.omnifocusjs/            # Primary AI plugin (daily/weekly reviews, analysis)
├── TreeExplorer.omnifocusjs/       # Hierarchy export (Markdown/JSON/OPML)
├── OFBundlePlugInTemplate.omnifocusjs/  # Official Omni Group template
├── plugin-templates/               # Generator templates (used by generate_plugin.js)
├── templates/                      # Task template definitions
├── examples/                       # Library usage examples
└── README.md
```

---

## Plugins

### Attache.omnifocusjs (v1.3.1)

The consolidated AI plugin for GTD in OmniFocus. Replaces the legacy AITaskAnalyzer, CompletedTasksSummary, Overview, and TodaysTasks plugins.

**Actions (9):**

| Action | Purpose |
|--------|---------|
| Attache: Daily Review | Completed work, today's tasks, deferred items, overdue triage |
| Attache: Weekly Review | Full GTD weekly review with Waiting For step |
| Attache: Analyze Selected | Per-task clarity scoring and improvements |
| Attache: Analyze Projects | Recursive folder/project analysis with health scoring |
| Attache: Analyze Hierarchy | System-wide GTD health assessment |
| Attache: Analyze Tasks | AI insights on today's and overdue tasks |
| Attache: Completed Summary | Completed task summary (today/yesterday/this week/this month) |
| Attache: System Setup | Initial system configuration and preference caching |
| Attache: Discover System | Auto-discover organizational structure |

**Libraries (9):** taskMetrics, exportUtils, foundationModelsUtils, folderParser, projectParser, taskParser, hierarchicalBatcher, systemDiscovery, preferencesManager

**Requirements:** OmniFocus 4.8+, macOS 26+ (Apple Intelligence), Apple Silicon

**Installation:** Double-click `Attache.omnifocusjs`

**Note:** The legacy `saveToFile` action from CompletedTasksSummary was deliberately not ported. Use the CLI instead: `ofo completed-today --markdown > summary.md`

---

### TreeExplorer.omnifocusjs (v1.0.0)

Hierarchy export utility -- exports OmniFocus structure as Markdown, JSON, or OPML.

**Actions (4):** Export JSON, Export Markdown, Export OPML, Reveal Selected

**Installation:** Double-click `TreeExplorer.omnifocusjs`

---

### OFBundlePlugInTemplate.omnifocusjs (v1.0)

**Official Omni Group plugin template** -- the base for all new plugins.

- Demonstrates correct `PlugIn.Library` pattern
- Shows proper manifest.json structure
- Includes localization support (en.lproj/)

**Usage:**
```bash
cp -R OFBundlePlugInTemplate.omnifocusjs MyPlugin.omnifocusjs
# Edit manifest.json, customize Resources/, double-click to install
```

---

## Templates

### Task Templates (`templates/task_templates.json`)

Reusable templates for common workflows: weekly review, meeting prep, project kickoff.

**Usage:**
```bash
const engine = loadLibrary('templateEngine.js');
engine.createFromTemplate(doc, 'weekly_review', {WEEK: '2025-W01'});
```

---

## Examples (`examples/`)

Demonstrates three library usage patterns:
1. **Standalone** -- Individual library functions
2. **JXA Scripts** -- Complete automation workflows
3. **Plugins** -- Reusable plugin actions

See `examples/README.md` for details.

---

## What to Use When

| Need | Use | Location |
|------|-----|----------|
| AI-powered daily/weekly GTD reviews | Attache plugin | `Attache.omnifocusjs` |
| Completed task summaries | Attache plugin | `Attache.omnifocusjs` (Completed Summary) |
| Project/hierarchy analysis | Attache plugin | `Attache.omnifocusjs` (Analyze Projects/Hierarchy) |
| Export hierarchy as Markdown/JSON | TreeExplorer plugin | `TreeExplorer.omnifocusjs` |
| Create from template | Template system | `templates/` |
| Build custom plugin | Official template | `OFBundlePlugInTemplate.omnifocusjs` |
| Learn library API | Examples | `examples/` |

---

## Plugin Development

- Start from `OFBundlePlugInTemplate.omnifocusjs` (never from scratch)
- Or use `node scripts/generate_plugin.js` for scaffolding from `plugin-templates/`
- Validate with `bash scripts/validate-plugin.sh`
- Always bump version in manifest.json on update
- Guide: `../references/omni_automation_guide.md`
- Foundation Models: `../references/foundation_models_integration.md`
