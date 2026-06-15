# Libraries and Shared Code

<!-- DRAFT — review during D2 integration -->

**What this covers:** `PlugIn.Library` pattern, `PlugIn.find()`, consuming `ofoCore` from a generated plugin, creating standalone shared libraries, and the `solitary-library` format.

**What this does NOT cover:** ofoCore function list (see `library_consumer_pattern.md`), System Map dependency (see `system_map_dependency.md`).

---

## 1. First-Stop Solution: Check `ofoCore`

If you need task/project/tag CRUD, `ofoCore` already has it. See `library_consumer_pattern.md` for the full exports table. The pattern in this doc is HOW to call it, not what it contains.

---

## 1a. Plugin Format Note

**`.omnifocusjs`** — OmniFocus-specific. Most generated plugins are this format.  
**`.omnijs`** — Works in ALL Omni apps (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan). Use this when your automation should be cross-app or distributable across the Omni suite.  

When consuming `ofoCore` (an OmniFocus library), the consumer must be `.omnifocusjs` since OmniFocus APIs like `flattenedTasks` are not available cross-app.

---

## 2. PlugIn.Library — The Sharing Mechanism

A `PlugIn.Library` is a JavaScript module declared in a plugin's manifest that other plugins can `find().library()`. Libraries must be wrapped in an IIFE and export an object:

```js
// Resources/myLibrary.js — IIFE wrap (build-attache.sh does this for ofoCore)
(function() {
  var myLibrary = new PlugIn.Library(new Version("1.0"));

  myLibrary.greet = function(name) {
    return "Hello, " + name;
  };

  return myLibrary;
})();
```

---

## 3. Consuming `ofoCore` from a Generated Plugin

The standard startup skeleton (auto-emitted by D8.5 for `requires: ["ofoCore"]`):

```js
// --- ofoCore dependency check ---
var attache = PlugIn.find("com.totallytools.omnifocus.attache");
if (!attache) {
  new Alert(
    "Attache Required",
    "This plugin requires the Attache plugin (v2.0+). Install it from the Attache repo."
  ).show();
  return;
}
var ofoCore = attache.library("ofoCore");
if (!ofoCore || typeof ofoCore.getTask !== "function") {
  new Alert(
    "Attache Out of Date",
    "The Attache 'ofoCore' library is missing required functions. Please update Attache."
  ).show();
  return;
}
// --- end dependency check ---

// Now use ofoCore
var taskData = ofoCore.getTask(taskId);
ofoCore.updateTask(taskId, {flagged: true});
ofoCore.tagTask(taskId, {add: ["@waiting"]});
```

---

## 4. PlugIn API Reference

```js
// Find a plugin by bundle identifier
var plugin = PlugIn.find("com.totallytools.omnifocus.attache");
// → PlugIn | null

// Access a library
var lib = plugin.library("ofoCore");
// → the library object returned from the library's IIFE | null

// Access an action
var action = plugin.action("myActionIdentifier");
// → PlugIn.Action | null

// Perform an action
action.perform();

// Plugin properties
plugin.identifier    // String: bundle ID
plugin.version       // Version
plugin.displayName   // String

// PlugIn.Action constructor (inside a plugin's action .js file)
var action = new PlugIn.Action(function(selection, sender) {
  // action body
  var tasks = selection.tasks;
});
action.validate = function(selection, sender) {
  // return true/false to enable/disable the action
  return selection.tasks.length > 0;
};

// PlugIn.Library constructor (inside a plugin's library .js file)
var lib = new PlugIn.Library(new Version("1.0.0"));
lib.myFunction = function() { ... };
return lib;  // must return the library object
```

**⚠️ Footguns:**
- `PlugIn.find()` returns **null** if the plugin is not installed. Always null-check before `.library()`.
- `plugin.library("name")` returns **null** if the library doesn't exist or throws at load time. Always null-check before calling functions.
- Libraries must NOT make API calls at the top level of their IIFE (outside functions). This causes all plugin actions to be disabled with no error. Common violation: `new Preferences()` at library top level.

---

## 5. Declaring Dependencies in manifest.json

Generated plugins that consume `ofoCore` should declare the dependency:

```json
{
  "identifier": "com.yourname.myplugin",
  "version": "1.0.0",
  "description": "Requires Attache plugin v2.0+ (ofoCore library)",
  "actions": [...]
}
```

No formal `requires` field exists in the manifest format; document in `description` and enforce with the startup check above.

---

## 6. Creating a Standalone PlugIn.Library (`solitary-library` format)

Use when you need reusable code across multiple generated plugins, but it doesn't belong in `ofoCore`:

```
myHelpers.omnifocusjs/
├── manifest.json
└── Resources/
    ├── myHelpers.js     ← the library
    └── en.lproj/
        └── manifest.strings
```

```json
// manifest.json for a library-only plugin
{
  "type": "com.omnigroup.omnifocus2.action",
  "identifier": "com.yourname.myhelpers",
  "version": "1.0.0",
  "description": "Shared helper library",
  "libraries": [
    {"identifier": "myHelpers"}
  ]
}
```

Consumer code:
```js
var helpers = PlugIn.find("com.yourname.myhelpers").library("myHelpers");
```

**When to create vs. add to ofoCore:** If the function would be useful to 2+ plugins OR the CLI, add to `ofoCore`. Otherwise inline in the plugin or create a standalone library. See `library_consumer_pattern.md` for the full decision rule.

---

## 7. SyncedPreferences Library (Special Case)

OmniFocus includes a `SyncedPreferences` plugin at a fixed bundle ID. Access it as a library:

```js
var syncedPrefs = PlugIn.find("com.omnigroup.omnifocus2.sharedsettings").library("SyncedPreferences");
// ⚠️ The plugin uses the project name "⚙️ Synced Preferences" (with emoji)
// ⚠️ Use folderNamed() + projectNamed(), not flattenedProjects.byName() — different search behavior
```

---

## 8. Reach-Out Trigger

PlugIn API is not on a dedicated omni-automation.com page. The full API is in `omnifocus_api.md` under `PlugIn`, `PlugIn.Action`, `PlugIn.Library`. No WebFetch needed — use the local reference.
