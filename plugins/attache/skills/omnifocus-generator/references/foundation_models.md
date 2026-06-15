# Foundation Models (LanguageModel API)

<!-- DRAFT — review during D2 integration -->

**What this covers:** On-device Apple Foundation Models via `LanguageModel.Session`, `LanguageModel.Schema`, and `LanguageModel.GenerationOptions`. Includes a worked walkthrough for D5 (Organize Project Tasks via Foundation Models).

**What this does NOT cover:** Cloud LLMs, Forms (UI collection), ofoCore task CRUD. See `03_forms_ui.md`, `01_tasks_projects_tags.md`.

---

## 1. System Requirements

- macOS 26+ / iOS 26+ / iPadOS 26+ / visionOS 26+
- Apple Silicon (on-device inference)
- OmniFocus 4.8+ (or OmniOutliner 6.0+)

**Always gate on availability.** Foundation Models are NOT available on Intel Macs or older OS.

---

## 2. First-Stop Solution: Check `ofoCore`

ofoCore does not wrap Foundation Models — use the native `LanguageModel` API directly. ofoCore handles task I/O (get/update/tag); Foundation Models handles reasoning.

---

## 3. LanguageModel API

### Session — Text Responses

```js
var session = new LanguageModel.Session();

// Unstructured text response
session.respond("Summarize these tasks: ...").then(function(text) {
  // text: human-readable string
});
```

### Session — Structured JSON Responses

```js
var schema = LanguageModel.Schema.fromJSON({
  properties: [
    {name: "groupings", schema: {
      arrayOf: {
        schema: {
          properties: [
            {name: "category"},
            {name: "taskIds", schema: {arrayOf: {type: "string"}}},
            {name: "suggestedTag"},
            {name: "rationale", isOptional: true}
          ]
        }
      }
    }}
  ]
});

var options = new LanguageModel.GenerationOptions();
options.maximumResponseTokens = 4096;   // null = unrestricted

session.respondWithSchema(prompt, schema, options).then(function(jsonStr) {
  var result = JSON.parse(jsonStr);
  // result.groupings: [{category, taskIds, suggestedTag, rationale?}]
});
```

---

## 4. LanguageModel.Schema

All schemas are created via `LanguageModel.Schema.fromJSON(jsonObject)`.

### Schema Elements

| Element | Format | Example |
|---------|--------|---------|
| `arrayOf` | `{type: "string"|"integer"|"decimal"}` with optional `minimum`/`maximum` | `{arrayOf: {type: "string", minimum: 1, maximum: 10}}` |
| `properties` | `[{name, description?, isOptional?, schema?}]` | `[{name: "title"}, {name: "priority", isOptional: true}]` |
| `anyOf` | `[{constant: "value"}]` — enum constraint | `[{constant: "high"}, {constant: "low"}]` |
| `constant` | `{constant: "fixed value"}` | `{constant: "Terrestrial"}` |
| `referenceTo` | `{referenceTo: "schema-name"}` | Recursive schemas |

### Naming a schema (for `referenceTo`):

```js
var stepSchema = LanguageModel.Schema.fromJSON({
  name: "step-schema",
  properties: [{name: "action"}, {name: "result"}]
});
```

### Common schema patterns:

**Array of strings:**
```js
LanguageModel.Schema.fromJSON({arrayOf: {type: "string"}})
```

**Object with typed array property:**
```js
LanguageModel.Schema.fromJSON({
  properties: [
    {name: "tags", schema: {arrayOf: {type: "string"}}},
    {name: "confidence", schema: {anyOf: [{constant: "high"}, {constant: "low"}]}}
  ]
})
```

**⚠️ Footgun:** Do NOT use `new LanguageModel.Schema(...)`. Use `LanguageModel.Schema.fromJSON(...)` exclusively.

---

## 5. LanguageModel.GenerationOptions

```js
var options = new LanguageModel.GenerationOptions();
options.maximumResponseTokens = 2048;   // truncates early without error if reached
// options.maximumResponseTokens = null;  // no limit (default)
```

Pass as third argument to `respondWithSchema`. Pass `null` for defaults.

---

## 6. Worked Example: Organize Project Tasks via Foundation Models

**This is the D5 acceptance test walkthrough.** A fresh agent reading only this doc + `08_libraries_shared_code.md` + `40_patterns/library_consumer_pattern.md` + `10_decision_framework/plugin_format_selection.md` should be able to build the plugin end-to-end.

### Step 1: Channel Selection

Decision tree → standalone `.omnifocusjs` (not Attache — too specialized; not frequent enough for Attache menu).  
Format → `solitary-fm` (Foundation Models required → macOS 26+ only, ok for this specialized tool).

### Step 2: Library Consumption

This plugin depends on Attache's `ofoCore`. Use it for all task I/O.

```js
var attache = PlugIn.find("com.totallytools.omnifocus.attache");
if (!attache) {
  new Alert("Attache Required", "Install the Attache plugin first.").show();
  return;
}
var ofoCore = attache.library("ofoCore");
if (!ofoCore || typeof ofoCore.getTask !== "function") {
  new Alert("Update Attache", "ofoCore library is outdated.").show();
  return;
}
```

### Step 3: Read System Map for Convention Tags

This plugin organizes tasks and may suggest tags — it needs to know what tags the user actually uses.

```js
var smTask = flattenedTasks.find(function(t) { return t.name === "Attache System Map"; });
if (!smTask) {
  new Alert("System Map Missing", "Run: ofo system-map --refresh").show();
  return;
}
var sm = JSON.parse(smTask.note || "{}");
var userTags = [].concat(
  (sm.tags && sm.tags.categories && sm.tags.categories.contexts) || [],
  (sm.tags && sm.tags.categories && sm.tags.categories.status) || []
);
```

### Step 4: Selection Input

```js
var project = selection.projects[0];
if (!project) {
  var task = selection.tasks[0];
  project = task ? task.containingProject : null;
}
if (!project) {
  new Alert("No project selected", "Select a project or a task within a project.").show();
  return;
}
```

### Step 5: Read Tasks

```js
var tasks = project.flattenedTasks.filter(function(t) {
  return !t.completed && !t.dropped;
});
var taskData = tasks.map(function(t) {
  return {id: t.id.primaryKey, name: t.name, note: t.note};
});
```

### Step 6: Build Prompt and Schema

```js
var availableTags = userTags.length > 0
  ? "Available tags: " + userTags.join(", ")
  : "Suggest appropriate tags.";

var prompt = [
  "You are organizing a project's tasks into thematic groups.",
  "Project: " + project.name,
  availableTags,
  "Tasks: " + JSON.stringify(taskData),
  "Group these tasks by theme. For each group, suggest one tag from the available tags (or propose a new one if none fit)."
].join("\n");

var schema = LanguageModel.Schema.fromJSON({
  properties: [{
    name: "groupings",
    schema: {
      arrayOf: {
        schema: {
          properties: [
            {name: "category", description: "Theme name"},
            {name: "taskIds", schema: {arrayOf: {type: "string"}}},
            {name: "suggestedTag", description: "Tag to apply"},
            {name: "rationale", isOptional: true}
          ]
        }
      }
    }
  }]
});
```

### Step 7: Invoke the Model

Batch if task list > 50 (token budget).

```js
var options = new LanguageModel.GenerationOptions();
options.maximumResponseTokens = 4096;

var session = new LanguageModel.Session();
return session.respondWithSchema(prompt, schema, options).then(function(jsonStr) {
  var result = JSON.parse(jsonStr);
  return applyGroupings(result.groupings, ofoCore);
});
```

### Step 8: Preview and Apply

```js
function applyGroupings(groupings, ofoCore) {
  // Build preview form
  var form = new Form();
  var summary = groupings.map(function(g) {
    return g.category + " (" + g.taskIds.length + " tasks) → @" + g.suggestedTag;
  }).join("\n");
  form.addField(new Form.Field.Checkbox("apply", "Apply these groupings?", true));

  return form.show("Review AI Suggestions\n" + summary, "Apply").then(function() {
    if (!form.values["apply"]) return;
    groupings.forEach(function(g) {
      g.taskIds.forEach(function(id) {
        var tag = flattenedTags.byName(g.suggestedTag)
          || new Tag(g.suggestedTag, database.tags.ending);
        ofoCore.tagTask(id, {add: [g.suggestedTag]});
      });
    });
    database.save();
  });
}
```

### Step 9: Validate and Install

```bash
bash plugins/attache/skills/omnifocus-generator/scripts/validate-plugin.sh ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/Plug-Ins/of-organize-with-fm.omnifocusjs
```

Bump version in `manifest.json`. Double-click to install, or copy to Plug-Ins directory.

### References used by this walkthrough

- `08_libraries_shared_code.md` — PlugIn.Library consumption pattern
- `40_patterns/library_consumer_pattern.md` — ofoCore null-check skeleton  
- `40_patterns/system_map_dependency.md` — System Map consumption pattern
- `10_decision_framework/plugin_format_selection.md` — why `solitary-fm`
- `03_forms_ui.md` — Form API for preview step

---

## 7. Reach-Out Trigger

For Foundation Models API details beyond what's here:

```
WebFetch https://omni-automation.com/shared/alm.html
WebFetch https://omni-automation.com/shared/alm-schema.html
Prompt: "I need [specific method / schema element] full specification including examples."
```
