# OmniFocus Omni Automation Guide

This is the complete guide to creating cross-platform plugins for OmniFocus using the Omni Automation framework. It covers everything from creating your first simple plugin to advanced development patterns.

## Quick Diagnostic: Plugin Not Working?

Use this before reading anything else.

**All actions disabled (grayed out), even ones that should always be available:**
→ A library IIFE is throwing at load time. Most common cause: `new Preferences()` at library IIFE top level.
→ Check every `PlugIn.Library` file for top-level API calls outside functions.
→ Node syntax check won't catch this — the error is runtime, OmniAutomation-specific.

**Plugin name shows as `com.your.bundle.id` in Automation Menu:**
→ Missing `Resources/en.lproj/manifest.strings`. Create it with:
  `"com.your.bundle.id" = "Your Plugin Name";`

**Action names show as camelCase identifiers (e.g. `analyzeSelected`) instead of labels:**
→ `manifest.json` `label` fields are NOT used for Automation Menu display.
→ Action labels must be declared in `Resources/en.lproj/manifest.strings`:
  ```
  "analyzeSelected.label" = "Attache: Clarify Tasks";
  "analyzeHierarchy.label" = "Attache: Project Health";
  ```
→ Pattern: `"<identifier>.label" = "<display label>";` — one line per action.
→ Validated 2026-03-23 against OmniFocus 4 on macOS 26.

**"Preferences objects may only be constructed when loading a plug-in":**
→ `new Preferences()` or `new Preferences(null)` called in library context.
→ Use lazy init with explicit bundle ID (see Storing Preferences).

**"Project not found" when using SyncedPreferences:**
→ Wrong project name. The SyncedPreferences plugin uses `"⚙️ Synced Preferences"` (with emoji), inside a folder of the same name.
→ Use `folderNamed(name)` + `folder.projectNamed(name)`, not `flattenedProjects.byName(name)`.
→ See Integrating with SyncedPreferences below.

**Action works on Mac but not iOS (or vice versa):**
→ Check `Device.current.operatingSystemVersion` gate — version numbers differ by platform.
→ Check for Mac-only APIs (`Application`, JXA globals, etc.).

---

## 1. What is Omni Automation?

Omni Automation is OmniFocus's modern, device-independent JavaScript automation framework. It is the recommended way to build reusable, integrated automation for OmniFocus.

Unlike older methods like JXA, Omni Automation:

*   **Works on both macOS and iOS/iPadOS**.
*   Runs natively inside the OmniFocus application.
*   Uses a clean, modern JavaScript API with direct property access (e.g., `task.name`).
*   Supports creating **Plug-Ins** that appear directly in the OmniFocus "Automation" menu.
*   Integrates with iOS features like the Shortcuts app.

**When to Use Omni Automation:**
*   For creating reusable plugins and actions.
*   When you need automation that works on both Mac and iOS.
*   For tasks triggered by the user from within the OmniFocus interface.

---

## 2. Plugin Loading Lifecycle

Understanding the exact execution order is essential for diagnosing issues. This was validated empirically against OmniFocus 4 on macOS 26 (2026-03-08).

```
── Plugin load (on OmniFocus startup or plugin install) ──────────────────────

  manifest.json parsed
  └── en.lproj/manifest.strings read → sets Automation Menu display name
      (missing = falls back to bundle identifier, NOT bundle filename)

  Action file IIFEs execute  (Resources/myAction.js outer IIFE)
  ├── new PlugIn.Action(asyncFn) registered  ← asyncFn body NOT run yet
  ├── action.validate registered             ← NOT called yet
  └── new Preferences()  ← SAFE here (action file scope = plugin load time)

  Library file IIFEs execute  (Resources/myLibrary.js outer IIFE)
  ├── new PlugIn.Library(...) registered
  ├── lib.method = function() { ... }  ← method bodies NOT run yet
  └── new Preferences()  ← FATAL: silently disables ALL plugin actions
                                     even validate() { return true }

── Automation Menu rendered ───────────────────────────────────────────────────

  action.validate(selection, sender) called for each action
  └── should be pure: check selection, OS version, return bool
      do NOT call this.plugIn.library() here

── User triggers action ───────────────────────────────────────────────────────

  action handler (async function) executes
  └── this.plugIn.library("name")  ← library method called NOW
      └── new Preferences("com.explicit.id")  ← SAFE inside functions
```

### Key Rules from the Lifecycle

| Location | `new Preferences()` | `new Preferences("id")` | `this.plugIn.library()` |
|---|---|---|---|
| Action file IIFE top level | ✅ Safe | ✅ Safe | ✅ Safe |
| Action handler (`async fn`) | ❌ Throws | ✅ Safe | ✅ Safe |
| Library file IIFE top level | ❌ Throws + **disables all actions** | ❌ Same | — |
| Library method body | ❌ Throws | ✅ Safe | — |

---

## 3. Quick Start: Your First Plugin in 5 Minutes

This tutorial will guide you through creating a simple "Hello World" style plugin that shows today's tasks.

### Step 1: Create the Plugin Bundle

An OmniFocus plugin is a special folder (called a "bundle") with a `.omnifocusjs` extension.

In your terminal, create the necessary folders:
```bash
mkdir MyFirstPlugin.omnifocusjs
mkdir MyFirstPlugin.omnifocusjs/Resources
mkdir -p MyFirstPlugin.omnifocusjs/Resources/en.lproj
```

### Step 2: Create the `manifest.json` File

This file describes your plugin's metadata. Create the following file at `MyFirstPlugin.omnifocusjs/manifest.json`:

```json
{
  "identifier": "com.myname.my-first-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A plugin to show today's tasks.",
  "actions": [
    {
      "identifier": "showToday",
      "label": "Show Today's Tasks"
    }
  ]
}
```

### Step 3: Create the Localization File

This controls how the plugin name appears in the Automation Menu.

`MyFirstPlugin.omnifocusjs/Resources/en.lproj/manifest.strings`:
```
"com.myname.my-first-plugin" = "My First Plugin";
```

### Step 4: Create the Action Script

This is the JavaScript code that will run. Create the file `MyFirstPlugin.omnifocusjs/Resources/showToday.js`:

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // This is where your action's logic goes.
        const alert = new Alert("Hello from My First Plugin!", "The plugin is working correctly.");
        await alert.show();
    });

    // The validate function controls when the action is available in the menu.
    // Returning true makes it always available.
    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### Step 5: Install and Test

*   **On macOS**: Simply find `MyFirstPlugin.omnifocusjs` in Finder and double-click it. OmniFocus will ask you to install it.
*   **On iOS**: Transfer the `.omnifocusjs` bundle to your device (e.g., via iCloud Drive or AirDrop) and tap on it in the Files app.

Once installed, you can run your plugin from the **Automation** menu in OmniFocus.

---

## 4. Understanding Plugin Bundles

A plugin is a directory with a specific structure.

*   `.omnifocusjs`: For plugins specific to OmniFocus.
*   `.omnijs`: For plugins that can work across multiple Omni apps.

**Standard Bundle Structure:**

```
MyPlugin.omnifocusjs/
├── manifest.json                    # REQUIRED: metadata, actions, libraries
└── Resources/
    ├── en.lproj/
    │   ├── manifest.strings         # REQUIRED for Automation Menu name
    │   ├── myAction.strings         # Optional: action label overrides
    │   └── myLibrary.strings        # Optional: library string overrides
    ├── myAction.js                  # Action (identifier matches manifest)
    └── myLibrary.js                 # Library (identifier matches manifest)
```

**manifest.json fields:**

```json
{
  "identifier": "com.vendor.plugin-name",   // bundle ID — used for Preferences scoping
  "version": "1.0.0",
  "defaultLocale": "en",
  "author": "Name",
  "description": "...",
  "image": "sf-symbol-name",                // optional plugin icon
  "actions": [
    {
      "identifier": "actionName",           // matches Resources/actionName.js
      "label": "Action Label",              // shown in menu (overridden by .strings)
      "image": "sf-symbol-name"             // optional action icon
    }
  ],
  "libraries": [
    { "identifier": "libraryName" }         // matches Resources/libraryName.js
  ]
}
```

**There is no top-level `name` field.** The Automation Menu display name comes from `en.lproj/manifest.strings`, not from the bundle filename or a `name` key.

---

## 5. The Omni Automation API: Core Concepts

### The `PlugIn.Action` Object

Every user-facing action is a `PlugIn.Action`. The constructor takes a function that is executed when the action is run.

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // `selection` contains the items (tasks, projects) the user has selected.
        // `sender` identifies what UI element triggered the action.
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### The `validate` Function

The `validate` function runs before showing the menu item and determines if the action should be enabled.

```javascript
action.validate = function(selection, sender) {
    // Only enable the action if at least one task is selected.
    return selection.tasks.length > 0;
};
```

**validate rules:**
- Keep it pure and fast — it runs every time the menu renders
- Do NOT call `this.plugIn.library()` inside validate
- Do NOT do async work inside validate
- Return a plain boolean

### Accessing OmniFocus Data

*   **Globals**: The API provides global variables for accessing your database. **Always prefer these**.
    *   `flattenedTasks`: A flat array of all tasks.
    *   `flattenedProjects`: A flat array of all projects.
    *   `flattenedTags`: A flat array of all tags.
    *   `inbox`: An array of tasks in the inbox.
*   **Selection**: The `selection` object passed to your action contains what the user has currently selected (`selection.tasks`, `selection.projects`, etc.).

**Anti-Pattern to Avoid**: Never use `Document.defaultDocument`. This is from the older JXA/AppleScript API and does not exist in the modern Omni Automation environment.

### Properties vs. Methods

A common source of errors is confusing properties and methods.

*   **Properties** are accessed directly: `const name = task.name;`
*   **Methods** must be called with `()`: `task.markComplete();`

Refer to the `api_reference.md` for a definitive list.

---

## 6. Using and Creating Libraries

Libraries allow you to reuse code across different actions within a plugin.

### Using a Library

1.  **Declare it in `manifest.json`**:
    ```json
    { "libraries": [{ "identifier": "taskMetrics" }] }
    ```
2.  **Load it inside your action handler** (not in validate):
    ```javascript
    const action = new PlugIn.Action(async function(selection, sender) {
        const metrics = this.plugIn.library("taskMetrics");
        const tasks = metrics.getTodayTasks();
    });
    ```

### Creating a Library

```javascript
// Resources/myHelpers.js
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    lib.formatDate = function(date) {
        return date.toLocaleDateString();
    };

    return lib;
})();
```

**Library IIFE rules:**
- Only `new PlugIn.Library(...)` and `lib.method = function() {}` assignments belong at IIFE top level
- No API calls (Preferences, flattenedTasks, Alert, etc.) at IIFE top level — they disables all actions silently
- All real work goes inside `lib.method` function bodies

### Cross-Plugin Library Loading (validated Mac + iPhone, 2026-03-22)

A plugin action can load a library from a **different installed plugin** using `PlugIn.find()`. This is the mechanism that allows feature plugins (Attache, future plugins) to use `ofoCore` as a shared data access layer.

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    // 1. Null-guard — REQUIRED before any ofoCore call
    const corePlugin = PlugIn.find("com.totally-tools.ofo-core");
    if (!corePlugin) {
        new Alert("Missing dependency", "ofo-core.omnifocusjs must be installed.").show();
        return;
    }
    const ofoCore = corePlugin.library("ofoCore");

    // 2. Use named functions directly (no magic strings needed)
    const stats  = ofoCore.getStats();                         // fast counts
    const tasks  = ofoCore.listTasks({ filter: 'flagged' });   // normalized task objects
    const search = ofoCore.searchTasks({ query: 'meeting' });
    const dump   = ofoCore.dumpDatabase();                     // full snapshot (capped 500 tasks)

    // dispatch() still works for backward compat, but prefer named functions:
    // const result = ofoCore.dispatch({ action: "ofo-list", filter: "flagged" });
});
```

**Available named functions** (all validated Mac + iPhone, 2026-03-22):
`getTask`, `searchTasks`, `listTasks`, `completeTask`, `createTask`, `updateTask`, `tagTask`, `getTags`, `getPerspective`, `configurePerspective`, `getPerspectiveRules`, `createBatch`, `dumpDatabase`, `getStats`

See `CONTRIBUTING.md` → "Writing a New Feature Plugin" for the complete pattern including error handling.

**Confirmed behaviours:**
- `PlugIn.find("bundle.id")` returns the plugin object on both Mac and iPhone ✓
- `.library("libName")` loads and returns the library on both platforms ✓
- Library methods execute with full OmniFocus API access (`flattenedTasks`, etc.) ✓
- Validated with cross-plugin library loading test calling `ofo-core.omnifocusjs` — all three steps passed on iPhone (2026-03-22)

**Required null-guard pattern** — always guard against the dependency not being installed:
```javascript
const corePlugin = PlugIn.find("com.totally-tools.ofo-core");
if (!corePlugin) {
    new Alert("ofo-core required", "Install ofo-core.omnifocusjs to use this plugin.").show();
    return;
}
const ofoCore = corePlugin.library("ofoCore");
// Wrap calls in try/catch — named functions don't have dispatch-level error wrapping
try {
    const tasks = ofoCore.listTasks({ filter: 'today' });
} catch (e) {
    new Alert("Error", String(e)).show();
}
```

---

## 7. Advanced Plugin Patterns

### Plugin Formats

*   **Solitary Action**: A single `.omnijs` file containing both the manifest (as a header comment) and the code. Good for simple, single-purpose actions.
*   **Solitary Library**: A single `.omnijs` file that defines a library.
*   **Bundle**: The folder structure (`.omnifocusjs`) we've been using. Best for plugins with multiple actions, libraries, or localization.

### Storing Preferences

Use the `Preferences` class to persist settings between runs. The correct pattern depends on where you're calling from.

**In an action file** (safe at IIFE top level):
```javascript
(() => {
    const prefs = new Preferences(); // auto-scopes to plugin bundle ID

    const action = new PlugIn.Action(async function(selection, sender) {
        const count = prefs.readNumber("runCount") || 0;
        prefs.write("runCount", count + 1);
    });

    return action;
})();
```

**In a library file** (lazy init required — NEVER at IIFE top level):
```javascript
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    // Lazy: constructed on first call, not at IIFE evaluation time
    let _prefs = null;
    function getPrefs() {
        if (!_prefs) _prefs = new Preferences("com.your.bundle.id");
        return _prefs;
    }

    lib.readSetting = function(key) {
        return getPrefs().readString(key);
    };

    lib.writeSetting = function(key, value) {
        getPrefs().write(key, value);
    };

    return lib;
})();
```

**Rules (validated 2026-03-08):**
- Library IIFE top level: `new Preferences()` and `new Preferences(null)` both **silently disable ALL plugin actions**
- Library method bodies: `new Preferences("explicit.bundle.id")` works; no-arg and null still throw
- Action file IIFE top level: `new Preferences()` (no arg) works fine
- Always use an explicit bundle ID string inside libraries

### Localization

Bundles support localization by adding `.lproj` directories inside `Resources`.

**`manifest.strings` is required for the Automation Menu plugin name.** Without it OmniFocus shows the bundle identifier.

```
// Resources/en.lproj/manifest.strings
"com.your.bundle.identifier" = "Your Plugin Name";
```

Each action's menu label can be overridden with a matching `.strings` file:

```
// Resources/en.lproj/myAction.strings
"label" = "My Action";
"shortLabel" = "My Action";
"mediumLabel" = "My Action";
"longLabel" = "My Action";
```

Actions can also use a `"label"` key in `manifest.json` as a shortcut — but `manifest.strings` for the plugin name is always required separately.

### Integrating with SyncedPreferences

The [SyncedPreferences plugin](https://github.com/KaitlinSalzke/SyncedPreferences) (com.KaitlinSalzke.SyncedPrefLibrary) provides cross-device preference sync by storing JSON in OmniFocus task notes.

**Actual storage structure** (do not assume — confirmed from source, 2026-03-08):
```
Folder: "⚙️ Synced Preferences"        ← emoji prefix, NOT plain "Synced Preferences"
└── Project: "⚙️ Synced Preferences"   ← same name as folder, inside it
    └── Task: "<your-identifier>"      ← task.note contains JSON preferences
```

**Correct lookup — use folder + project traversal:**
```javascript
const SYNCED_PREFS_NAME = "⚙️ Synced Preferences";

function getSyncedProject() {
    const folder = folderNamed(SYNCED_PREFS_NAME) || new Folder(SYNCED_PREFS_NAME);
    return folder.projectNamed(SYNCED_PREFS_NAME) || new Project(SYNCED_PREFS_NAME, folder);
}

function getPrefTask(identifier) {
    const project = getSyncedProject();
    return project.taskNamed(identifier) || new Task(identifier, project);
}
```

**Wrong approaches that silently fail:**
```javascript
// WRONG: flattenedProjects.byName() doesn't match the emoji name reliably
const project = flattenedProjects.byName("Synced Preferences");

// WRONG: missing emoji — project is named "⚙️ Synced Preferences"
const project = flattenedProjects.byName("Synced Preferences");
```

**Hybrid persistence pattern** (local cache + synced store):
```javascript
// Fast reads from local Preferences, authoritative writes to task note
lib.read = function() {
    const cached = getPrefs().readString("myKey");
    if (cached) { try { return JSON.parse(cached); } catch {} }
    const task = getPrefTask("My Identifier");
    if (!task || !task.note) return null;
    try {
        const data = JSON.parse(task.note);
        getPrefs().write("myKey", task.note); // populate local cache
        return data;
    } catch { return null; }
};

lib.write = function(data) {
    const json = JSON.stringify(data);
    getPrefTask("My Identifier").note = json;
    getPrefs().write("myKey", json);
};
```

---

## 8. Installation and Distribution

*   **Installation**: Double-click the `.omnifocusjs` bundle on Mac or tap it in the Files app on iOS.
*   **Installed location (macOS)**: `~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/Plug-Ins/`
*   **Distribution**: Zip the bundle (`zip -r MyPlugin.zip MyPlugin.omnifocusjs`) and share it. Include a `README.md` with instructions.

---

## 9. Validation and Testing

*   **Syntax check**: `node --check Resources/myFile.js` — catches syntax errors but NOT OmniAutomation runtime errors.
*   **Automation Console**: Open with `View > Automation > Console` (`^⌥⌘C`). Run JavaScript snippets here to test parts of your plugin, inspect objects, and see runtime errors.
*   **All actions grayed out**: open the Console immediately — there will be a load-time error logged there.
*   **Linting**: Use ESLint to catch undefined variables and style issues before running.

For a complete set of validation rules, refer to `javascript_generation_guide.md`.

---

## 10. Calling Plugins Externally

**Source:** <https://omni-automation.com/plugins/calling.html>

Installed plugin actions can be called from external scripts (including `omnijs-run` script URLs). This means the `ofo` CLI or any script URL can invoke Attache actions or any installed plugin — with zero extra approval if the calling script is already approved.

### Finding Installed Plugins

```javascript
// List all installed plugin identifiers
var pluginIDs = PlugIn.all.map(plugin => plugin.identifier);
console.log(pluginIDs.join("\n"));

// Find a specific plugin
var plugin = PlugIn.find("com.your.bundle.id");
```

### Listing Actions in a Plugin

```javascript
var plugin = PlugIn.find("com.your.bundle.id");
if (plugin) {
    var actionNames = plugin.actions.map(action => action.name);
    console.log(actionNames);
}
```

### Executing a Plugin Action

```javascript
function performPlugInAction(pluginID, actionName) {
    var plugin = PlugIn.find(pluginID);
    if (!plugin) throw new Error("Plug-in not installed.");
    var action = plugin.action(actionName);
    if (!action) throw new Error("Action not found: " + actionName);
    if (action.validate()) {
        action.perform();
    } else {
        throw new Error("Action not validated to execute.");
    }
}

// Example: call an Attache action
performPlugInAction("com.totallytools.omnifocus.attache", "dailyReview");
```

### Handling External Calls in Your Actions

When called externally, the `selection` parameter is `undefined`. Actions that depend on selection must handle this:

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    if (typeof selection === 'undefined') {
        // Called externally — generate selection manually or skip
        var tasks = flattenedTasks.filter(t => t.flagged && !t.completed);
    } else {
        var tasks = selection.tasks;
    }
    // action code...
});

action.validate = function(selection) {
    if (typeof selection === 'undefined') return true;
    return selection.tasks.length > 0;
};
```

### Integration with ofo CLI

The `ofo` CLI can invoke installed plugin actions via script URLs:

```bash
# Script URL that calls an installed plugin action (approved once)
SCRIPT='var p = PlugIn.find("com.totallytools.omnifocus.attache"); if(p){ p.action("dailyReview").perform(); Pasteboard.general.string = JSON.stringify({success: true}); }'
```

This is useful when:
- The plugin action has complex logic you don't want to duplicate in a standalone script
- The plugin is already installed (zero friction vs. script URL approval)
- You want to trigger on-device AI analysis (Attache) from Claude Code

**Official docs:** <https://omni-automation.com/plugins/calling.html>

---

## 11. Promises and Async Patterns

**Official docs:** <https://omni-automation.com/plugins/promises.html>

Omni Automation uses JavaScript Promises for operations that involve user interaction (forms, alerts) or asynchronous processing. Plugin actions should use `async/await` or `.then()` chains.

### Why Async Matters

JavaScript does not pause for user interactions. Without promises, a script that shows an alert and then logs a result will log *before* the user dismisses the alert.

### Alert with Promise

```javascript
// Wrong — logs immediately, doesn't wait for user
new Alert("Title", "Message").show();
console.log("User dismissed");  // runs before dismissal

// Correct — waits for user interaction
var alertPromise = new Alert("Title", "Message").show();
alertPromise.then(function(buttonIndex) {
    console.log("User chose option:", buttonIndex);
});
```

### Form with Promise

```javascript
var form = new Form();
form.addField(new Form.Field.String("name", "Task Name", null));

var formPromise = form.show("Enter details", "OK");

formPromise.then(function(filledForm) {
    var name = filledForm.values["name"];
    new Task(name, inbox.ending);
});

formPromise.catch(function(err) {
    console.error("User cancelled");
});
```

### Async/Await in Plugin Actions

Plugin action handlers can be `async` functions, enabling cleaner syntax:

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    var alert = new Alert("Confirm", "Complete selected tasks?");
    alert.addOption("Yes");
    alert.addOption("No");
    var choice = await alert.show();
    if (choice === 0) {
        selection.tasks.forEach(t => t.markComplete());
    }
});
```

### Relevance to ofo CLI

The `ofo` action scripts (in `scripts/omni-actions/`) are synchronous — they run, write to pasteboard, and exit. They do NOT use promises because:
- No user interaction is needed (no forms or alerts)
- The CLI polls for results via pasteboard, not via promise resolution
- Script URLs execute and complete in a single pass

If you need to build action scripts that show forms or alerts, use the promise pattern above. But for CLI-driven automation, keep scripts synchronous.

---

## 12. Script Security

**Official docs:** <https://omni-automation.com/script-url/security.html>

External scripts (sent via `omnijs-run` URLs from other applications) are subject to OmniFocus's security system. Installed plugins are NOT affected.

### Two-Gate Security Model

**Gate 1 — Global Toggle (off by default):**
- macOS: Automation menu > Plug-Ins... > Security tab > enable external scripts
- iOS/iPadOS: Settings > Configure Plug-Ins > Security > enable external scripts
- This only controls scripts from external apps. Installed plugins always work.

**Gate 2 — Per-Script Approval (one-time):**
- Each unique script/sending-app pairing must be approved once
- The approval dialog shows the full script code
- User must **scroll to the bottom** before "Run Script" enables (security measure to encourage review)
- Optional: "Automatically run this script when sent by this or any other unknown application" checkbox auto-approves all future scripts from any source
- Once approved, the script runs silently on subsequent invocations

### How Approval Persists

OmniFocus tracks approved scripts by their **script body + sending application** pair:
- Same script from same app → approved, no prompt
- Same script from different app → requires separate approval
- Modified script body from same app → requires new approval
- Same script with different `&arg=` data → approved (argument is not part of the approval key)

This is why the `ofo` CLI uses stable script files with variable `&arg=` data — the script body never changes, so approval is truly one-time.

### Resetting Approvals

macOS: Automation menu > Plug-Ins... > Security tab > "Clear Approved Scripts"

This forces re-approval of all previously approved scripts. Useful if you've modified action script files and need OmniFocus to re-evaluate them.

### What's NOT Affected by Script Security

- Installed Omni Automation plugins (`.omnifocusjs` bundles) — always trusted
- Scripts in the Automation Console — always trusted
- Plugin actions called via `PlugIn.find(id).action(name).perform()` — trusted if the calling context is trusted
- Navigation URLs (`omnifocus:///task/<id>`) — no script execution
- Add URLs (`omnifocus:///add?name=...`) — built-in action, no script

See `omnifocus_url_scheme.md` for the complete ofo setup guide and security friction table.

---

This guide provides the foundation for building powerful, cross-platform OmniFocus plugins. For a complete, exhaustive list of all available classes and methods, see `api_reference.md` or the [official API](https://omni-automation.com/omnifocus/OF-API.html).
