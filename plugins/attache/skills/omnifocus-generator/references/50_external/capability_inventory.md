# OmniFocus Omni Automation Capability Inventory

**Generated:** 2026-06-15T00:00:00Z  
**Method:** Phase 1 Research Agent — fetched omni-automation.com topic pages (two rounds; full sidebar mapped)  
**Source:** https://omni-automation.com/omnifocus/index.html (navigation JS-driven; individual pages fetched by slug)  
**Local comparison base:** `omnifocus-core/references/omnifocus_api.md` + `omnifocus-generator/references/20_capabilities/`

**Plugin format note:** `.omnijs` files run in ALL Omni apps (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan). `.omnifocusjs` files are OmniFocus-specific. The generator skill primarily targets `.omnifocusjs` but can generate `.omnijs` for cross-app automation. The capability docs below apply to `.omnifocusjs` unless noted.

---

## Summary (Round 2 — Full Sidebar Mapped)

**Sidebar topics confirmed:** The Big Picture, Application, Document, Window|Selection, Perspective, Outline, Forecast, FileWrapper, eMail, Database, Arrays, Database Object, Settings, Finding Items, Folders, Projects, Tasks, Repeating Tasks, Attachments, File Links, Notifications, Tasks to Projects, Tags, Text, Style, App-to-App, Shortcuts Integration, TaskPaper, QR Codes, Scripting Dictionary, Automation Tutorial, Automation Controls, Plug-In Collection, Plug-In Generator, Shared Classes & Methods, Plug-Ins, Actions, Action Forms, Libraries

| Status | Count |
|--------|-------|
| `covered` | ~180 (core Task/Project/Tag/Database/Folder in omnifocus_api.md) |
| `partial` | ~30 (advanced classes in omnifocus_api.md without capability-doc patterns) |
| `missing` | ~20 (LanguageModel, ForecastDay, Tree/TreeNode, Text/Style, new v4.x members) |

**Topics with no findable standalone page (covered by omnifocus_api.md instead):**  
Arrays, Repeating Tasks, Attachments, File Links, Notifications, Tasks to Projects, eMail, Plug-Ins, Actions, Action Forms, Libraries, Finding Items — these are all covered in the local `30_api_reference/omnifocus_api.md`.

---

## Missing / Partial Coverage (Priority Order)

| class | member | type | description | source-url | local-coverage |
|-------|--------|------|-------------|------------|----------------|
| `LanguageModel.Session` | `constructor` | constructor | Creates AFM communication session | https://omni-automation.com/shared/alm.html | **missing** |
| `LanguageModel.Session` | `respond` | method | Text response to natural language prompt → Promise\<String\> | https://omni-automation.com/shared/alm.html | **missing** |
| `LanguageModel.Session` | `respondWithSchema` | method | Structured JSON response via schema → Promise\<String\> | https://omni-automation.com/shared/alm.html | **missing** |
| `LanguageModel.Schema` | `fromJSON` | class function | Create schema from JSON object representation | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.Schema` | `arrayOf` | schema element | Array of typed items (string/integer/decimal) with min/max | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.Schema` | `properties` | schema element | Named properties with optional/description/schema nesting | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.Schema` | `anyOf` | schema element | Constrain value to one of a set of constants | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.Schema` | `referenceTo` | schema element | Recursive schema reference by name | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.GenerationOptions` | `constructor` | constructor | New instance with default settings | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `LanguageModel.GenerationOptions` | `maximumResponseTokens` | property | Max tokens for AFM response (null = unrestricted) | https://omni-automation.com/shared/alm-schema.html | **missing** |
| `ForecastDay` | `badgeCount` | property | Count of available tasks on this day (read-only) | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `ForecastDay` | `date` | property | Date this forecast day represents (read-only) | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `ForecastDay` | `deferredCount` | property | Count of remaining deferred tasks (read-only) | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `ForecastDay` | `kind` | property | Classification (Day/Today/FutureMonth/Past/DistantFuture) | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `ForecastDay` | `badgeKind` | method | Returns ForecastDay.Status for this day | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `ForecastDay` | `badgeCountsIncludeDeferredItems` | class property | Whether badges include unavailable items | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `Window` | `forecastDayForDate` | method | Returns ForecastDay for date (requires Forecast perspective active) | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `Window` | `selectForecastDays` | method | Selects specified forecast days | https://omni-automation.com/omnifocus/forecast.html | **missing** |
| `Window` | `contentTree` | property | Hierarchical node tree of window content area | https://omni-automation.com/omnifocus/automation-new.html | **missing** |
| `Window` | `sidebarTree` | property | Hierarchical node tree of window sidebar | https://omni-automation.com/omnifocus/automation-new.html | **missing** |
| `Window` | `inspectorVisible` | property | Controls inspector panel visibility | https://omni-automation.com/omnifocus/automation-new.html | **missing** |
| `Window` | `sidebarVisible` | property | Controls sidebar panel visibility | https://omni-automation.com/omnifocus/automation-new.html | **missing** |
| `Node` | *(class)* | class | Wrapper for DatedObject in hierarchical outline structures | https://omni-automation.com/omnifocus/automation-new.html | **missing** |
| `Tag` | `childrenAreMutuallyExclusive` | property | Only one child tag assignable simultaneously (v4.7+) | https://omni-automation.com/omnifocus/tag.html | **missing** |
| `Tag` | `forecastTag` | class property | Returns the Forecast Tag if assigned, else null | https://omni-automation.com/omnifocus/tag.html | **partial** |
| `Tag` | `moveTasks` | method | Reorders tasks within tag to specified location | https://omni-automation.com/omnifocus/tag.html | **missing** |
| `Tag` | `beginningOfTasks` | property | Location before all tag tasks | https://omni-automation.com/omnifocus/tag.html | **missing** |
| `Tag` | `beforeTask` | method | Location before specified task in tag | https://omni-automation.com/omnifocus/tag.html | **missing** |
| `Task` | `plannedDate` | property | Intention to work on task on planned date (v4.7+) | https://omni-automation.com/omnifocus/task.html | **missing** |
| `Task` | `effectivePlannedDate` | property | Computed planned date from container (v4.7+) | https://omni-automation.com/omnifocus/task.html | **missing** |
| `Task` | `afterTag` | method | Location after existing tag in task's tags (v4.0+) | https://omni-automation.com/omnifocus/task.html | **partial** |
| `Task` | `beforeTag` | method | Location before existing tag in task's tags (v4.0+) | https://omni-automation.com/omnifocus/task.html | **partial** |
| `Task` | `moveTag` | method | Moves associated tag within task's tag list (v4.0+) | https://omni-automation.com/omnifocus/task.html | **partial** |
| `Task` | `moveTags` | method | Moves list of tags within task's tag list (v4.0+) | https://omni-automation.com/omnifocus/task.html | **partial** |
| `Database` | `objectForURL` | method | Returns DatabaseObject for URL if exists (v4.5+) | https://omni-automation.com/omnifocus/database.html | **partial** |
| `Folder` | `byIdentifier` | class function | Returns Folder with specified identifier or null | https://omni-automation.com/omnifocus/folder.html | **partial** |
| `DocumentWindow` | `content` | property | Tree of nodes for window content area | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `DocumentWindow` | `sidebar` | property | Tree of nodes for window sidebar | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `DocumentWindow` | `focus` | property | Folders/Projects limiting sidebar display (OF4 iOS) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `DocumentWindow` | `selectObjects` | method | Clear selection and select given objects if in current perspective | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `rootNode` | property | Root TreeNode of the outline (read-only) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `selectedNodes` | property | List of selected TreeNodes in display order (read-only) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `nodeForObject` | method | Returns TreeNode for an object, or null | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `nodesForObjects` | method | Returns array of TreeNodes for objects currently in tree | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `reveal` | method | Ensures ancestor nodes of specified nodes are expanded | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `select` | method | Selects visible TreeNodes (optionally extending existing selection) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `copyNodes` | method | Writes serialized nodes to pasteboard | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `Tree` | `paste` | method | Creates items from serialized nodes on pasteboard at location | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `object` | property | Model object (Task/Project/Tag/Folder) wrapped by this node | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `isSelected` | property | Set to select node; no effect if not revealed | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `children` | property | Array of visible child nodes | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `expand` | method | Expand node (recursively if completely=true) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `collapse` | method | Collapse node (recursively if completely=true) | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `TreeNode` | `apply` | method | Calls function for each node recursively | https://omni-automation.com/omnifocus/outline.html | **missing** |
| `DatabaseObject` | `id` | property | ObjectIdentifier for this object (read-only) | https://omni-automation.com/omnifocus/database-object.html | **partial** |
| `DatabaseObject` | `url` | property | URL linking to this database object (read-only) | https://omni-automation.com/omnifocus/database-object.html | **missing** |
| `ObjectIdentifier` | `primaryKey` | property | Unique string key for use with byIdentifier() | https://omni-automation.com/omnifocus/database-object.html | **partial** |
| `ObjectIdentifier` | `objectClass` | property | Constructor for instances of the identified class | https://omni-automation.com/omnifocus/database-object.html | **missing** |
| `DatedObject` | `added` | property | Date first saved (read/write before first save) | https://omni-automation.com/omnifocus/database-object.html | **partial** |
| `DatedObject` | `modified` | property | Date of most recent modification | https://omni-automation.com/omnifocus/database-object.html | **partial** |
| `ActiveObject` | `active` | property | Whether object is active or dropped | https://omni-automation.com/omnifocus/database-object.html | **missing** |
| `ActiveObject` | `effectiveActive` | property | True if object AND all containers are active | https://omni-automation.com/omnifocus/database-object.html | **missing** |
| `Text` | `string` | property | Plain string content (read-write) | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Text` | `style` | property | Style instance for this text (read-only) | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Text` | `attributeRuns` | property | Contiguous blocks with same style | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Text` | `find` | method | Find string occurrence; returns Text.Range or null | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Text` | `replace` | method | Replace sub-range with passed text | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Text` | `append` | method | Append text object to receiver | https://omni-automation.com/omnifocus/text.html | **missing** |
| `Style` | `fontFillColor` | property | Color used to fill text | https://omni-automation.com/omnifocus/style.html | **missing** |
| `Style` | `get` | method | Retrieve attribute value by Style.Attribute key | https://omni-automation.com/omnifocus/style.html | **missing** |
| `Style` | `set` | method | Set attribute value by Style.Attribute key | https://omni-automation.com/omnifocus/style.html | **missing** |
| `Style.Attribute` | *(30+ attributes)* | class properties | FontFamily, FontSize, FontItalic, FontWeight, Link, ParagraphLineSpacing, BackgroundColor, UnderlineStyle, etc. | https://omni-automation.com/omnifocus/style.html | **missing** |
| `Task.Notification.Kind` | `Absolute` | class property | Absolute-date notification | https://omni-automation.com/omnifocus/task-to-project.html | **partial** |
| `Task.Notification.Kind` | `DueRelative` | class property | Due-relative notification offset | https://omni-automation.com/omnifocus/task-to-project.html | **partial** |

---

## Covered Classes (from omnifocus_api.md)

All of the following are documented in the existing `30_api_reference/omnifocus_api.md`:

| class | local-coverage |
|-------|----------------|
| `Alert` | covered |
| `Application` | covered |
| `ApplyResult` | covered |
| `Database` | covered |
| `DatabaseDocument` | covered |
| `Document` | covered |
| `Email` | covered |
| `FilePicker` | covered |
| `FileSaver` | covered |
| `FileWrapper` + `FileWrapper.Type` | covered |
| `Folder` + `Folder.Status` | covered |
| `Form` + `Form.Field.*` | covered |
| `Inbox` | covered |
| `Library` (OmniFocus top-level container) | covered |
| `Perspective.BuiltIn` | covered |
| `Perspective.Custom` | covered |
| `PlugIn` + `PlugIn.Action` + `PlugIn.Library` | covered |
| `Project` + `Project.ReviewInterval` + `Project.Status` | covered |
| `Selection` | covered |
| `Settings` | covered |
| `Tag` + `Tag.Status` | covered (base — missing v4.0+/v4.7+ members) |
| `Tags` (top-level container) | covered |
| `Task` + `Task.Status` + `Task.RepetitionRule` + `Task.Notification` | covered (base — missing v4.0+/v4.7+ members) |
| `TaskArray`, `FolderArray`, `ProjectArray`, `TagArray`, `SectionArray` | covered |
| `URL` | covered |
| `Version` | covered |
| `Window` + `Selection` | covered (base — missing contentTree/sidebarTree) |

---

## High-Value Gaps — Recommended Follow-Up Issues

1. **Foundation Models (LanguageModel)** — `missing` across all local refs. 
   High value: required for `solitary-fm` plugins, D5 walkthrough, growing use case.
   Suggested issue: `feat(references): add LanguageModel capability doc (D5/D4 gap)` labels: `attache`, `references`, `omnifocus-api`

2. **ForecastDay API** — `missing` locally. 
   Medium value: needed for Forecast perspective automation.
   Suggested issue: `feat(references): document ForecastDay class in 02_perspectives.md`

3. **Window.contentTree / sidebarTree / Node** — `missing` locally.
   Medium value: needed for outline-based plugins, tree navigation.
   Suggested issue: `feat(references): document Window tree API (contentTree, Node) in 20_capabilities`

4. **Tag v4.0+/v4.7+ members** — `partial` in omnifocus_api.md, `missing` from capability docs.
   Medium value: tag ordering important for organization plugins.
   Suggested issue: `fix(references): document Tag.moveTag, tag.beginningOfTasks, childrenAreMutuallyExclusive`

5. **Task plannedDate (v4.7+)** — `missing` locally.
   Low-medium value: useful for Forecast/planned-date plugins.
   Suggested issue: `fix(references): add Task.plannedDate to 01_tasks_projects_tags.md`

---

## TODO for Capability Docs

After Phase 2 creates the `20_capabilities/` docs:
- `04_foundation_models.md` — must cover full LanguageModel.Session + Schema (missing)
- `02_perspectives.md` — must cover ForecastDay API (missing)
- `01_tasks_projects_tags.md` — must note v4.0+ tag ordering methods (partial)
- New entry in `00_index.md` capability map row for ForecastDay and Window tree API
