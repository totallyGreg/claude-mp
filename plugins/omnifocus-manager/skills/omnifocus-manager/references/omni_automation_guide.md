# OmniFocus Omni Automation Guide

This is the complete guide to creating cross-platform plugins for OmniFocus using the Omni Automation framework. It covers everything from creating your first simple plugin to advanced development patterns.

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

## 2. Quick Start: Your First Plugin in 5 Minutes

This tutorial will guide you through creating a simple "Hello World" style plugin that shows today's tasks.

### Step 1: Create the Plugin Bundle

An OmniFocus plugin is a special folder (called a "bundle") with a `.omnifocusjs` extension.

In your terminal, create the necessary folders:
```bash
mkdir MyFirstPlugin.omnifocusjs
mkdir MyFirstPlugin.omnifocusjs/Resources
```

### Step 2: Create the `manifest.json` File

This file describes your plugin's metadata. Create the following file at `MyFirstPlugin.omnifocusjs/manifest.json`:

```json
{
  "identifier": "com.myname.my-first-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A plugin to show today's tasks.",
  "label": "My First Plugin",
  "actions": [
    {
      "identifier": "showToday",
      "label": "Show Today's Tasks"
    }
  ]
}
```

### Step 3: Create the Action Script

This is the JavaScript code that will run. Create the file `MyFirstPlugin.omnifocusjs/Resources/showToday.js`:

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // This is where your action's logic goes.
        // For this example, we will just show a simple alert.
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

### Step 4: Install and Test

*   **On macOS**: Simply find `MyFirstPlugin.omnifocusjs` in Finder and double-click it. OmniFocus will ask you to install it.
*   **On iOS**: Transfer the `.omnifocusjs` bundle to your device (e.g., via iCloud Drive or AirDrop) and tap on it in the Files app.

Once installed, you can run your plugin from the **Automation** menu in OmniFocus.

## 3. Understanding Plugin Bundles

A plugin is a directory with a specific structure.

*   `.omnifocusjs`: For plugins specific to OmniFocus.
*   `.omnijs`: For plugins that can work across multiple Omni apps.

**Standard Bundle Structure:**

```
MyPlugin.omnifocusjs/
├── manifest.json         # REQUIRED: Metadata, actions, libraries.
└── Resources/            # REQUIRED: Scripts and other resources.
    ├── action1.js       # Code for the action with identifier "action1".
    ├── action2.js
    └── myLibrary.js     # A library specific to this plugin.
```

## 4. The Omni Automation API: Core Concepts

### The `PlugIn.Action` Object

Every user-facing action is a `PlugIn.Action`. The constructor takes a function that is executed when the action is run.

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    // `selection` contains the items (tasks, projects) the user has selected.
    // `sender` identifies what UI element triggered the action.
});
```

### The `validate` Function

The `validate` function is critical. It runs before showing the menu item and determines if the action should be enabled (and can dynamically change its appearance).

```javascript
action.validate = function(selection, sender) {
    // Only enable the action if at least one task is selected.
    return selection.tasks.length > 0;
};
```

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

## 5. Using and Creating Libraries

Libraries allow you to reuse code across different actions and plugins.

### Using an Existing Library

1.  **Declare it in `manifest.json`**:
    ```json
    {
      "libraries": ["taskMetrics"]
    }
    ```
2.  **Load it in your action script**:
    ```javascript
    const metrics = this.plugIn.library("taskMetrics");
    const tasks = metrics.getTodayTasks();
    ```

### Creating a New Library

You can create your own library file within your plugin's `Resources` folder.

**`MyPlugin.omnifocusjs/Resources/myHelpers.js`**:
```javascript
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    lib.formatDate = function(date) {
        return date.toLocaleDateString();
    };

    return lib;
})();
```
Declare it in your manifest (`"libraries": ["myHelpers"]`) to use it.

## 6. Advanced Plugin Patterns

### Plugin Formats

*   **Solitary Action**: A single `.omnijs` file containing both the manifest (as a header comment) and the code. Good for simple, single-purpose actions.
*   **Solitary Library**: A single `.omnijs` file that defines a library.
*   **Bundle**: The folder structure (`.omnifocusjs`) we've been using. Best for plugins with multiple actions, libraries, or localization.

### Storing Preferences

Use the `Preferences` class to save settings for your plugin.

```javascript
// Declare at the plugin scope
var preferences = new Preferences(); // Automatically uses your plugin's identifier

// In your action:
var count = preferences.readNumber("executionCount") || 0;
count++;
preferences.write("executionCount", count);
new Alert("Info", `This action has been run ${count} times.`).show();
```

### Localization

Bundles support localization by adding `.lproj` directories inside `Resources`.

`MyPlugin.omnifocusjs/Resources/`
*   `en.lproj/`
    *   `manifest.strings`
    *   `myAction.strings`
*   `de.lproj/`
    *   `manifest.strings`
    *   `myAction.strings`

The `.strings` files contain key-value pairs for translating labels.

## 7. Installation and Distribution

*   **Installation**: Double-click the `.omnifocusjs` bundle on Mac or tap it in the Files app on iOS.
*   **Distribution**: Zip the bundle (`zip -r MyPlugin.zip MyPlugin.omnifocusjs`) and share it. Include a `README.md` with instructions.

## 8. Validation and Testing

*   **Manual Testing**: Run the plugin in OmniFocus. Check for different selections and edge cases.
*   **Automation Console**: Open with `View > Automation > Console` (`^⌥⌘C`). You can run JavaScript snippets here to test parts of your plugin, inspect objects, and debug issues.
*   **Linting**: Use a linter like ESLint with a proper configuration to catch syntax errors and undefined variables before you even run the code.

For a complete set of validation rules, refer to `javascript_generation_guide.md`.

This guide provides the foundation for building powerful, cross-platform OmniFocus plugins. For a complete, exhaustive list of all available classes and methods, see `api_reference.md`.
