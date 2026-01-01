# OmniFocus Plugin Development Guide

Complete guide to creating, distributing, and maintaining OmniFocus plugins using the modular library system.

> ⚠️ **CRITICAL: Plugin Code Generation Rules**
>
> Before generating ANY plugin code, you MUST:
> 1. **Read `code_generation_validation.md`** - Complete MANDATORY pre-generation checklist
> 2. **Use global variables** - `flattenedTasks`, `flattenedProjects`, `folders`, `flattenedTags`, `inbox`
> 3. **NEVER use `Document.defaultDocument`** - This API doesn't exist in Omni Automation
> 4. **Verify ALL APIs in `api_quick_reference.md`** - No hallucinated APIs
> 5. **Run eslint_d validation** - Zero tolerance for linting errors
>
> **Common anti-patterns to avoid:**
> - ❌ `Document.defaultDocument` → ✅ Use global variables
> - ❌ `new Progress()` → ✅ Class doesn't exist
> - ❌ `FileType.fromExtension()` → ✅ Method doesn't exist
> - ❌ `new LanguageModel.Schema()` → ✅ Use `LanguageModel.Schema.fromJSON()`
>
> **After code generation:**
> - Run `eslint_d` on all .js files (must return zero errors)
> - Use vtsls LSP for semantic validation
> - Run `bash ../assets/development-tools/validate-plugin.sh <plugin-path>`
>
> **See:** [Code Generation Validation Guide](code_generation_validation.md) for complete workflow

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding Plugin Bundles](#understanding-plugin-bundles)
3. [Creating Your First Plugin](#creating-your-first-plugin)
4. [Plugin API Reference](#plugin-api-reference)
5. [Using Shared Libraries](#using-shared-libraries)
6. [Advanced Features](#advanced-features)
7. [Installation & Distribution](#installation--distribution)
8. [Validation & Testing](#validation--testing)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Want to create your first plugin in 5 minutes?**

See: [Plugin Quickstart Guide](quickstarts/plugin_quickstart.md)

The quickstart covers:
- Creating basic plugin structure
- Using taskMetrics library
- Installing and testing

**For complete details, continue reading this guide.**

---

## Official Plugin Template Reference

### OFBundlePlugInTemplate.omnifocusjs

Location: `../assets/OFBundlePlugInTemplate.omnifocusjs/`

**Purpose:** Official Omni Group template demonstrating correct plugin patterns and API usage.

**Use this template as:**
- **Reference** for correct PlugIn.Library patterns
- **Example** of proper manifest.json structure
- **Guide** for library declarations and action implementations
- **Starting point** (optional) - can copy and customize, or create from scratch following these patterns

**Two approaches to plugin creation:**

**Approach 1: Create from scratch** (following template patterns)
- Understand the patterns from OFBundlePlugInTemplate
- Create your own structure
- Implement using the same API patterns
- Test to ensure correctness

**Approach 2: Copy and customize** (faster start)
```bash
# Copy template as base
cp -R assets/OFBundlePlugInTemplate.omnifocusjs MyPlugin.omnifocusjs

# Customize manifest.json and actions
# Keep the patterns, change the functionality
```

**Key Patterns from Official Template:**

**Library Pattern:**
```javascript
// From OFBundlePlugInTemplate/Resources/allDateLibrary.js
(() => {
	var lib = new PlugIn.Library(new Version("1.1"));

	lib.dateOccursToday = function(dateToCheck) {
		// implementation
	};

	return lib;
})();
```

❌ **WRONG - Common Mistakes:**

```javascript
// Constructor takes Version, NOT a function
new PlugIn.Library(function() { ... })  // ERROR! Type mismatch
new PlugIn.Library(async function() { ... })  // ERROR! Type mismatch

// Use 'var lib', not 'const myLib' or other names
const foundationModelsUtils = new PlugIn.Library(...)  // WRONG!
var lib = new PlugIn.Library(...)  // CORRECT!
```

**Why these patterns fail:**
- PlugIn.Library constructor signature: `new PlugIn.Library(version: Version)` (OmniFocus-API.md:1769)
- Passing a function instead of Version object causes "invalid instance" error
- Always use `var lib` pattern for consistency with official templates

**Manifest with Library Declaration:**
```json
{
  "identifier": "com.omni-automation.of.omnifocus-bundle-example",
  "libraries": [
    {"identifier": "allDateLibrary"}
  ],
  "actions": [...]
}
```

**The key:** Follow the API correctly as demonstrated in OFBundlePlugInTemplate, whether you copy it or create from scratch.

---

## Understanding Plugin Bundles

### What is a Plugin Bundle?

An OmniFocus plugin is a **directory bundle** with a `.omnifocusjs` or `.omnijs` extension.

**CRITICAL:** `.omnifocusjs` files are **directories**, not single files.

**In Finder:**
- Appears as a single clickable icon
- Has `.omnifocusjs` extension
- Double-clicking installs the plugin
- Right-click → "Show Package Contents" reveals internal structure

**In Terminal:**
- Is actually a **directory**
- Contains multiple files: `manifest.json`, `Resources/`, etc.
- Cannot be read directly (will fail with "is a directory" error)
- Must read individual files within the bundle

### Extension Types

**Application-Specific Extensions:**
- `.omnifocusjs` - OmniFocus only
- `.omniplanjs` - OmniPlan only
- `.omnigrafflejs` - OmniGraffle only
- `.omnioutlinerjs` - OmniOutliner only

**Generic Extension:**
- `.omnijs` - Works across all Omni applications

**When to use each:**

**Use `.omnifocusjs` when:**
- Creating plugins for OmniFocus only
- Want simplified installation (double-click)
- Using OmniFocus-specific APIs

**Use `.omnijs` when:**
- Creating cross-application plugins
- Sharing code across Omni apps
- Using only shared Omni Automation APIs (Alert, Form, etc.)

### Bundle Structure

Standard plugin bundle structure:

```
PluginName.omnifocusjs/          # Bundle directory
├── manifest.json                 # Required: Plugin metadata
├── Resources/                    # Required: Action scripts
│   ├── action1.js               # Action implementations
│   ├── action2.js
│   └── lib/                     # Optional: Plugin-specific libraries
│       └── helpers.js
├── README.md                    # Optional: Documentation
└── LICENSE                      # Optional: License information
```

**Required files:**
- `manifest.json` - Plugin metadata and configuration
- `Resources/` - Directory containing action scripts

**Optional but recommended:**
- `README.md` - Installation and usage instructions
- `LICENSE` - License terms
- `Resources/lib/` - Plugin-specific helper libraries

### Navigating Bundles

**Correct approach:**
```bash
# Read manifest
cat PluginName.omnifocusjs/manifest.json

# Read action script
cat PluginName.omnifocusjs/Resources/action.js

# List contents
ls -la PluginName.omnifocusjs/
```

**Incorrect approach:**
```bash
# This FAILS - cannot read a directory
cat PluginName.omnifocusjs  # ❌ ERROR
```

---

## Creating Your First Plugin

### Step 1: Create Bundle Structure

```bash
mkdir MyPlugin.omnifocusjs
mkdir MyPlugin.omnifocusjs/Resources
```

### Step 2: Create manifest.json

**Minimal manifest:**

```json
{
  "identifier": "com.myname.my-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Plugin description",
  "label": "My Plugin",
  "actions": [
    {
      "identifier": "myAction",
      "label": "My Action"
    }
  ]
}
```

**Complete manifest with all options:**

```json
{
  "identifier": "com.myname.my-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Comprehensive plugin demonstrating all features",
  "label": "My Plugin",
  "mediumLabel": "Plugin",
  "shortLabel": "Plug",
  "paletteLabel": "My Plugin Name",
  "image": "checkmark.circle",
  "libraries": ["taskMetrics", "exportUtils"],
  "actions": [
    {
      "identifier": "action1",
      "label": "First Action",
      "mediumLabel": "Action 1",
      "shortLabel": "A1",
      "paletteLabel": "First",
      "image": "1.circle"
    },
    {
      "identifier": "action2",
      "label": "Second Action",
      "mediumLabel": "Action 2",
      "shortLabel": "A2"
    }
  ]
}
```

**manifest.json Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `identifier` | Yes | Unique ID (reverse domain: `com.author.plugin-name`) |
| `version` | Yes | Semantic version (`major.minor.patch`) |
| `author` | Yes | Plugin author name |
| `description` | Yes | Brief description of functionality |
| `label` | Yes | Full plugin name (shown in menus) |
| `mediumLabel` | No | Medium-length name (toolbar) |
| `shortLabel` | No | Abbreviated name (compact views) |
| `paletteLabel` | No | Name in command palette |
| `image` | No | SF Symbol name for icon |
| `libraries` | No | Array of PlugIn.Library names to load |
| `actions` | Yes | Array of action definitions |

**Action Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `identifier` | Yes | Action ID (matches `.js` filename) |
| `label` | Yes | Action name in menus |
| `mediumLabel` | No | Medium-length action name |
| `shortLabel` | No | Abbreviated action name |
| `paletteLabel` | No | Name in command palette |
| `image` | No | SF Symbol for action icon |

### Step 3: Create Action Script

Create `Resources/myAction.js`:

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Action implementation here

        // Example: Show alert
        const alert = new Alert("Hello", "Plugin is working!");
        await alert.show();
    });

    action.validate = function(selection, sender) {
        // Return true to enable action, false to disable
        return true;
    };

    return action;
})();
```

**Key components:**

1. **IIFE wrapper:** `(() => { ... })()` - Isolates scope
2. **PlugIn.Action:** Creates action object
3. **async function:** Action implementation (can use await)
4. **validate function:** Controls when action is enabled
5. **return action:** Must return the action object

### Step 4: Install and Test

**macOS:**
1. Double-click `MyPlugin.omnifocusjs`
2. Choose storage location
3. Click "Install"
4. Test: Tools → My Plugin → My Action

**iOS:**
1. Transfer to device (AirDrop, iCloud)
2. Tap plugin file
3. Tap "Install"
4. Test: ≡ menu → Automation → My Action

---

## Plugin API Reference

### PlugIn Object

The `PlugIn` object is available globally in action scripts.

#### Properties

```javascript
PlugIn.identifier        // Plugin identifier from manifest
PlugIn.version          // Plugin version
PlugIn.author           // Plugin author
PlugIn.description      // Plugin description
PlugIn.label            // Plugin label
```

#### Methods

**this.plugIn.library(name)**

Load a PlugIn.Library declared in manifest.json.

```javascript
// In manifest.json: "libraries": ["taskMetrics"]

// In action:
const metrics = this.plugIn.library("taskMetrics");
const tasks = metrics.getTodayTasks();
```

**this.plugIn.action(identifier)**

Get reference to another action in the plugin.

```javascript
const otherAction = this.plugIn.action("otherActionId");
// Can access properties but not invoke directly
```

**this.plugIn.resourceNamed(filename)**

Get path to resource file in plugin bundle.

```javascript
const configPath = this.plugIn.resourceNamed("config.json");
// Returns: URL object to Resources/config.json
```

### PlugIn.Action

Create actions that appear in OmniFocus menus.

#### Constructor

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    // Action implementation
    // selection: Current selection object
    // sender: UI element that triggered action
});
```

#### Methods

**action.validate(selection, sender)**

Controls when action is enabled/disabled.

```javascript
action.validate = function(selection, sender) {
    // Return true to enable, false to disable

    // Example: Only enable if tasks are selected
    return selection.tasks.length > 0;

    // Example: Only enable if exactly one project selected
    return selection.projects.length === 1;

    // Example: Always available
    return true;
};
```

**Common validation patterns:**

```javascript
// Tasks selected
selection.tasks.length > 0

// Projects selected
selection.projects.length > 0

// Tags selected
selection.tags.length > 0

// Exactly one item selected
selection.tasks.length === 1

// No selection required
true

// Complex condition
selection.tasks.length > 0 && selection.tasks.every(t => !t.completed)
```

### Selection Object

The `selection` parameter provides access to selected items.

#### Properties

```javascript
selection.window          // Current window
selection.document        // Current document
selection.tasks          // Array of selected tasks
selection.projects       // Array of selected projects
selection.tags           // Array of selected tags
selection.folders        // Array of selected folders
selection.inbox          // Inbox tasks (if inbox selected)
selection.library        // Entire database (if library selected)
```

#### Examples

```javascript
// Get first selected task
const task = selection.tasks[0];

// Process all selected tasks
selection.tasks.forEach(task => {
    console.log(task.name);
});

// Get selected project
const project = selection.projects[0];

// Check if inbox is selected
if (selection.inbox) {
    // Process inbox tasks
}
```

### Document Object

Access the OmniFocus database.

```javascript
// From selection
const doc = selection.document;

// From Application
const doc = Document.defaultDocument;
```

#### Properties

```javascript
doc.flattenedTasks       // All tasks (flattened hierarchy)
doc.flattenedProjects    // All projects (flattened)
doc.flattenedTags        // All tags (flattened)
doc.flattenedFolders     // All folders (flattened)
doc.inboxTasks          // Tasks in inbox
doc.projects            // Top-level projects
doc.tags                // Top-level tags
doc.folders             // Top-level folders
```

#### Methods

```javascript
// Find by ID
doc.flattenedTasks.byId("task-id")
doc.flattenedProjects.byId("project-id")

// Filter
doc.flattenedTasks.whose({ name: "Task name" })
doc.flattenedProjects.whose({ status: Project.Status.Active })
```

### Task Object

Represents an OmniFocus task.

#### Properties

```javascript
task.id                  // Unique ID
task.name               // Task name
task.note               // Task note
task.completed          // Boolean: Is completed?
task.completionDate     // Date completed
task.dropped            // Boolean: Is dropped?
task.flagged            // Boolean: Is flagged?
task.dueDate            // Due date
task.deferDate          // Defer date
task.estimatedMinutes   // Time estimate
task.taskStatus         // Status enum
task.tags               // Array of tags
task.containingProject  // Parent project
task.tasks              // Subtasks (if task group)
task.addedDate          // When task was created
task.modifiedDate       // When last modified
```

#### Methods

```javascript
task.addTag(tag)         // Add tag to task
task.removeTag(tag)      // Remove tag
task.clearTags()         // Remove all tags
task.markComplete()      // Mark complete
task.markIncomplete()    // Mark incomplete
task.drop()              // Drop task
```

### Project Object

Represents an OmniFocus project.

#### Properties

```javascript
project.id               // Unique ID
project.name            // Project name
project.note            // Project note
project.status          // Status enum (Active, OnHold, Completed, Dropped)
project.tasks           // Top-level tasks
project.containingFolder // Parent folder
project.dueDate         // Project due date
project.deferDate       // Project defer date
project.flagged         // Boolean: Is flagged?
project.sequential      // Boolean: Sequential or parallel?
```

#### Enums

```javascript
Project.Status.Active
Project.Status.OnHold
Project.Status.Completed
Project.Status.Dropped
```

### Tag Object

Represents an OmniFocus tag (context).

#### Properties

```javascript
tag.id                   // Unique ID
tag.name                // Tag name
tag.status              // Status enum
tag.parent              // Parent tag (for nested tags)
tag.tags                // Child tags
tag.tasks               // Tasks with this tag
tag.projects            // Projects with this tag
tag.availableTasks      // Available tasks with tag
tag.remainingTasks      // Remaining tasks with tag
```

---

## Using Shared Libraries

### Loading Libraries

Declare libraries in manifest.json:

```json
{
  "libraries": ["taskMetrics", "exportUtils", "insightPatterns"]
}
```

Load in action script:

```javascript
const metrics = this.plugIn.library("taskMetrics");
const exporter = this.plugIn.library("exportUtils");
const insights = this.plugIn.library("insightPatterns");
```

### Available Libraries

See `../../libraries/README.md` for complete documentation.

**taskMetrics** - Query operations
```javascript
const metrics = this.plugIn.library("taskMetrics");

metrics.getTodayTasks()
metrics.getOverdueTasks()
metrics.getFlaggedTasks()
metrics.getAvailableTasks()
metrics.getUpcomingTasks(days)
metrics.getTasksByTag(tagName)
metrics.getTasksByProject(projectName)
metrics.getSummaryStats()
```

**exportUtils** - Export to formats
```javascript
const exporter = this.plugIn.library("exportUtils");

exporter.toClipboard(data, { format: 'json' })
await exporter.toFile(data, { format: 'markdown', filename: 'export.md' })
exporter.toJSON(data, pretty)
exporter.toCSV(data)
exporter.toMarkdown(data, options)
exporter.toHTML(data)
```

**insightPatterns** - Pattern detection
```javascript
const insights = this.plugIn.library("insightPatterns");

insights.detectStalledProjects(doc)
insights.detectWaitingForAging(doc)
insights.detectOverdueAccumulation(doc)
insights.detectInboxOverflow(doc)
insights.generateInsights(doc, options)
insights.formatReport(insightsResult)
```

**templateEngine** - Template system
```javascript
const engine = this.plugIn.library("templateEngine");

engine.loadTemplates(path)
engine.createFromTemplate(doc, "template-name", variables)
engine.listTemplates()
engine.getTemplateInfo(templateName)
```

**patterns** - Advanced workflows ⭐
```javascript
const patterns = this.plugIn.library("patterns");

// MCP-ready functions with JSON I/O
await patterns.queryAndAnalyzeWithAI(config)
await patterns.queryAndExport(config)
await patterns.batchUpdate(config)
await patterns.periodicReview(config)
await patterns.detectPatterns(config)
```

### Creating Plugin-Specific Libraries

For code used only within your plugin:

**1. Create library file:**

`Resources/lib/myHelpers.js`:

```javascript
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    lib.formatDate = function(date) {
        return date.toLocaleDateString();
    };

    lib.calculateDaysUntil = function(date) {
        const now = new Date();
        const diff = date - now;
        return Math.ceil(diff / (1000 * 60 * 60 * 24));
    };

    return lib;
})();
```

**2. Declare in manifest:**

```json
{
  "libraries": ["myHelpers"]
}
```

**3. Use in actions:**

```javascript
const helpers = this.plugIn.library("myHelpers");
const formatted = helpers.formatDate(new Date());
```

---

## Advanced Features

### Form Input

Collect user input with forms:

```javascript
const form = new Form();

// Text field
form.addField(new Form.Field.String(
    "taskName",           // Field ID
    "Task Name",          // Label
    "Default value"       // Initial value (or null)
));

// Checkbox
form.addField(new Form.Field.Checkbox(
    "flagged",
    "Flag this task",
    false                 // Initial state
));

// Option picker
form.addField(new Form.Field.Option(
    "priority",
    "Priority",
    ["Low", "Medium", "High"],  // Options
    "Medium",                     // Selected
    "Medium"                      // Default
));

// Date picker
form.addField(new Form.Field.Date(
    "dueDate",
    "Due Date",
    new Date(),           // Initial date
    null                  // Formatter (optional)
));

// Show form
const formPrompt = new FormPrompt("Create Task", form);
const result = await formPrompt.show("Create", "Cancel");

if (result) {
    const values = result.values;
    console.log(values.taskName);
    console.log(values.flagged);
    console.log(values.priority);
    console.log(values.dueDate);
}
```

### Alert Dialogs

Show messages to users:

```javascript
// Simple alert
const alert = new Alert("Title", "Message");
await alert.show();

// Alert with options
const alert = new Alert("Confirm", "Are you sure?");
alert.addOption("Yes");
alert.addOption("No");
const buttonIndex = await alert.show();

if (buttonIndex === 0) {
    // User clicked "Yes"
} else {
    // User clicked "No"
}

// Multi-option alert
const alert = new Alert("Choose Action", "What would you like to do?");
alert.addOption("Export");
alert.addOption("Delete");
alert.addOption("Cancel");
const choice = await alert.show();

switch (choice) {
    case 0: // Export
        break;
    case 1: // Delete
        break;
    case 2: // Cancel
        break;
}
```

### File Operations

Save and load files:

```javascript
// Save file
const fileSaver = new FileSaver();
fileSaver.nameLabel = "Export OmniFocus Data";
fileSaver.types = [FileType.fromExtension("json")];
fileSaver.defaultFileName = "export.json";

const url = await fileSaver.show();
if (url) {
    const data = JSON.stringify(tasks, null, 2);
    const wrapper = FileWrapper.fromString(url.toString(), data);
    wrapper.write(url);
}

// Load file
const filePicker = new FilePicker();
filePicker.types = [FileType.fromExtension("json")];

const urls = await filePicker.show();
if (urls.length > 0) {
    const url = urls[0];
    const wrapper = FileWrapper.withContents(url);
    const contents = wrapper.stringContents;
    const data = JSON.parse(contents);
}
```

### Clipboard Operations

Copy/paste data:

```javascript
// Copy to clipboard
Pasteboard.general.string = "Text to copy";

// Read from clipboard
const clipboardText = Pasteboard.general.string;

// Copy complex data
const tasks = metrics.getTodayTasks();
const markdown = exporter.toMarkdown(tasks);
Pasteboard.general.string = markdown;
```

### Conditional Logic

Enable actions based on conditions:

```javascript
action.validate = function(selection, sender) {
    // Only enable if tasks selected and none completed
    return selection.tasks.length > 0 &&
           selection.tasks.every(t => !t.completed);
};

action.validate = function(selection, sender) {
    // Only enable on specific day of week
    const dayOfWeek = new Date().getDay();
    return dayOfWeek === 0; // Sunday only
};

action.validate = function(selection, sender) {
    // Only enable if specific tag exists
    const tags = Document.defaultDocument.flattenedTags;
    return tags.some(t => t.name === "review");
};
```

### Error Handling

Handle errors gracefully:

```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    try {
        const metrics = this.plugIn.library("taskMetrics");
        const tasks = metrics.getTodayTasks();

        if (tasks.length === 0) {
            throw new Error("No tasks found for today");
        }

        // Process tasks...

    } catch (error) {
        const alert = new Alert("Error", error.message);
        await alert.show();
        console.error("Action failed:", error);
    }
});
```

---

## Installation & Distribution

### Installation Methods

#### macOS

**Method 1: Double-Click (Recommended)**
1. Locate plugin in Finder
2. Double-click `.omnifocusjs` file
3. Installation dialog appears
4. Choose storage location:
   - **Local:** This Mac only
   - **iCloud:** Synced across devices
5. Click "Install"

**Method 2: Drag to Automation Configuration**
1. Open OmniFocus
2. Menu: Tools → Automation → Configure (⌃⌥⌘A)
3. Drag `.omnijs` file into dialog
4. Plugin installs

**Method 3: Manual Installation**
1. Copy plugin to:
   ```
   ~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/
   Library/Application Support/OmniFocus/Plug-Ins/
   ```
2. Restart OmniFocus

#### iOS/iPadOS

**Method 1: Tap to Install**
1. Transfer plugin to device (AirDrop, iCloud, email)
2. Tap plugin file in Files app
3. Installation dialog appears
4. Choose storage location
5. Tap "Install"

**Method 2: Files App**
1. Open Files app
2. Navigate to: On My iPad → OmniFocus → Plug-Ins
   (Or: iCloud Drive → OmniFocus → Plug-Ins)
3. Drag plugin file into Plug-Ins folder
4. Open OmniFocus

### Uninstallation

#### macOS

**Via Automation Configuration:**
1. Tools → Automation → Configure (⌃⌥⌘A)
2. Right-click plugin
3. Select "Move to Trash"

**Manual:**
1. Navigate to plugin location
2. Delete `.omnifocusjs` folder
3. Restart OmniFocus

#### iOS

**Swipe to Delete:**
1. Open OmniFocus
2. Tap ≡ menu → Automation
3. Swipe left on plugin
4. Tap "Delete"

**Via Files App:**
1. Navigate to plugin location
2. Long-press plugin
3. Tap "Delete"

### Distribution

**Share your plugin:**

1. **ZIP the bundle:**
   ```bash
   zip -r MyPlugin.zip MyPlugin.omnifocusjs
   ```

2. **Include documentation:**
   - README.md with installation instructions
   - LICENSE file
   - Example screenshots

3. **Version properly:**
   - Update version in manifest.json
   - Follow semantic versioning
   - Document changes

4. **Test on target platforms:**
   - Mac (different macOS versions)
   - iOS/iPadOS if applicable

5. **Distribute via:**
   - GitHub repository
   - Omni Automation website
   - Direct download link
   - Plugin marketplace (if available)

### Distribution Checklist

**Before releasing your plugin, ensure:**

**Code Quality:**
- [ ] All code follows patterns from OFBundlePlugInTemplate
- [ ] No hardcoded paths or user-specific data
- [ ] Error handling for all failure cases
- [ ] Console logging removed or made conditional
- [ ] Code is commented where non-obvious

**Testing:**
- [ ] Tested on all target platforms (Mac/iOS)
- [ ] All actions tested in Automation Console
- [ ] Libraries load without errors
- [ ] Actions execute without crashes
- [ ] Tested with various selection types
- [ ] No console errors during normal operation

**Documentation:**
- [ ] README.md included with installation instructions
- [ ] Usage examples provided
- [ ] Requirements clearly stated (OmniFocus version, macOS/iOS version)
- [ ] Known limitations documented
- [ ] LICENSE file included

**Manifest:**
- [ ] Version number updated
- [ ] Author name correct
- [ ] Description is clear and accurate
- [ ] All library declarations present and correct
- [ ] All action identifiers match filenames

**Files to EXCLUDE from distribution:**
- [ ] Remove development artifacts (TESTING.md, validation scripts, etc.)
- [ ] Remove .DS_Store files
- [ ] Remove temporary/backup files
- [ ] Keep only: manifest.json, Resources/, README.md, LICENSE

**Version Management:**
- [ ] Follow semantic versioning (major.minor.patch)
- [ ] Document changes in README or CHANGELOG
- [ ] Tag release in version control (if using Git)

---

## Validation & Testing

### Pre-Installation Checklist

- [ ] manifest.json is valid JSON
- [ ] All required manifest fields present
- [ ] Action identifiers match .js filenames
- [ ] All library names spelled correctly
- [ ] Bundle structure is correct

### Post-Installation Checklist

- [ ] Plugin appears in Tools menu
- [ ] All actions appear in menu
- [ ] Actions enable/disable correctly
- [ ] No console errors
- [ ] Works on Mac (if targeting Mac)
- [ ] Works on iOS (if targeting iOS)

### Testing in Automation Console

**Open Automation Console:** `Cmd+Opt+Ctrl+C`

**Test 1: Find Your Plugin**
```javascript
const plugin = PlugIn.find('com.yourname.your-plugin');
console.log('Plugin found:', plugin !== null);
console.log('Version:', plugin.versionString);
console.log('Actions:', plugin.actions.map(a => a.name));
console.log('Libraries:', plugin.libraries.map(l => l.name));
```

**Expected output:**
```
Plugin found: true
Version: 1.0.0
Actions: ["Action Name 1", "Action Name 2"]
Libraries: ["libraryName"]
```

**Test 2: Load Libraries**
```javascript
const plugin = PlugIn.find('com.yourname.your-plugin');
const myLibrary = plugin.library('libraryName');
console.log('Library type:', typeof myLibrary);
console.log('Functions:', Object.keys(myLibrary));
```

**Expected:** Library should be object with your functions listed.

**Test 3: Test Library Functions**
```javascript
const plugin = PlugIn.find('com.yourname.your-plugin');
const myLibrary = plugin.library('libraryName');

// Test a specific function
const result = myLibrary.someFunction();
console.log('Result:', result);
```

**Test 4: List and Validate Actions**
```javascript
const plugin = PlugIn.find('com.yourname.your-plugin');
const selection = document.windows[0].content.selection;

plugin.actions.forEach((action, i) => {
    const isValid = action.validate(selection, null);
    console.log(`${i}: ${action.name} (${isValid ? 'enabled' : 'disabled'})`);
});
```

**Test 5: Execute Action**
```javascript
const plugin = PlugIn.find('com.yourname.your-plugin');
const selection = document.windows[0].content.selection;

// Execute first action
plugin.actions[0].perform(selection, null);
```

### Testing Actions

**Test validation logic:**
```javascript
// Test with no selection
// Test with single task selected
// Test with multiple tasks selected
// Test with project selected
// Test with mixed selection (tasks + projects)
```

**Test error cases:**
```javascript
// What if library not available?
// What if network fails?
// What if user cancels?
// What if no tasks match criteria?
```

**Console debugging:**
```javascript
console.log("Debug:", variable);
console.error("Error:", error);
console.warn("Warning:", message);
```

View console: View → Automation → Console (⌃⌥⌘I)

### Testing Checklist

**Before releasing:**
- [ ] Plugin installs without errors
- [ ] All actions appear in Automation menu
- [ ] Actions enable/disable based on selection correctly
- [ ] Libraries load successfully (test in console)
- [ ] Library functions return expected types
- [ ] Actions execute without crashes
- [ ] Error messages are helpful and specific
- [ ] Tested on target platforms (Mac/iOS)
- [ ] Console shows no unexpected errors
- [ ] Manifest version number updated

---

## Best Practices

### Code Organization

**Good:**
```javascript
// Clear, single responsibility
const action = new PlugIn.Action(async function(selection, sender) {
    const tasks = getTasks(selection);
    const report = formatReport(tasks);
    await displayReport(report);
});

function getTasks(selection) { /* ... */ }
function formatReport(tasks) { /* ... */ }
async function displayReport(report) { /* ... */ }
```

**Bad:**
```javascript
// Everything in one function
const action = new PlugIn.Action(async function(selection, sender) {
    // 200 lines of code...
});
```

### Error Messages

**Good:**
```javascript
throw new Error("No tasks found matching filter 'today'");
```

**Bad:**
```javascript
throw new Error("Error"); // Too vague
```

### Library Usage

**Good:**
```javascript
// Declare dependencies in manifest
"libraries": ["taskMetrics"]

// Load only what you need
const metrics = this.plugIn.library("taskMetrics");
```

**Bad:**
```javascript
// Copy-paste library code into action
// Duplicates code, hard to maintain
```

### Validation

**Good:**
```javascript
action.validate = function(selection, sender) {
    // Clear, specific condition
    return selection.tasks.length > 0 &&
           selection.tasks.every(t => !t.completed);
};
```

**Bad:**
```javascript
action.validate = function(selection, sender) {
    return true; // Always enabled, even when it shouldn't be
};
```

---

## Troubleshooting

### Plugin doesn't appear

**Symptoms:** Plugin missing from Tools menu

**Solutions:**
- Verify manifest.json is valid JSON (use jsonlint.com)
- Check bundle structure (manifest at root, actions in Resources/)
- Restart OmniFocus completely
- Check Console for errors (⌃⌥⌘I)
- Verify identifier is unique

### Action is grayed out

**Symptoms:** Action appears but is disabled

**Solutions:**
- Check validate() function returns true
- Verify selection requirements
- Test with different selections
- Add console.log() to validate()

### Library not found

**Symptoms:** "Library not found" error

**Solutions:**
- Verify library name in manifest.json
- Check spelling (case-sensitive)
- Ensure library is installed globally (for shared libs)
- For plugin-specific libs, check Resources/lib/ exists

### Script errors

**Symptoms:** Actions fail silently or with errors

**Solutions:**
- Open Console (⌃⌥⌘I) for error messages
- Add try/catch blocks
- Add console.log() for debugging
- Test each function separately
- Verify API usage matches documentation

### iOS compatibility issues

**Symptoms:** Works on Mac but not iOS

**Solutions:**
- Avoid Mac-only APIs
- Test file operations carefully
- Use Omni Automation APIs (not JXA)
- Test on actual device, not just Mac

### Performance issues

**Symptoms:** Actions are slow

**Solutions:**
- Use flattenedTasks instead of iterating hierarchy
- Filter early, process less data
- Batch operations when possible
- Profile with console.time/timeEnd
- Consider async operations

---

## Resources

### Documentation

**Core Guides:**
- [Plugin Quickstart](quickstarts/plugin_quickstart.md) - 5-minute tutorial
- [Library Documentation](../../libraries/README.md) - All available libraries
- [Example Plugins](../../assets/examples/plugins/) - Working examples

**API References:**
- [OmniFocus API](OmniFocus-API.md) - Complete API specification
- [Omni Automation](omnifocus_automation.md) - Omni Automation overview
- [Shared Classes](omni_automation_shared.md) - Alert, Form, FileSaver, etc.

**Advanced Topics:**
- [Foundation Models Integration](foundation_models_integration.md) - AI integration (future)
- [URL Scheme](omnifocus_url_scheme.md) - Deep linking
- [Workflows](workflows.md) - Common automation patterns

### External Resources

- [Omni Automation](https://omni-automation.com/omnifocus/)
- [Plug-In Library](https://omni-automation.com/omnifocus/actions.html)
- [OmniFocus Forums](https://discourse.omnigroup.com/c/omnifocus)
- [AppleScript Reference](https://support.omnigroup.com/omnifocus-applescript-reference/)

---

## What's Next?

**Beginner:**
- Follow [Plugin Quickstart](quickstarts/plugin_quickstart.md)
- Study examples in `../../assets/examples/plugins/`
- Modify examples for your needs

**Intermediate:**
- Use multiple libraries together
- Create multi-action plugins
- Add forms and user input

**Advanced:**
- Use patterns library for complex workflows
- Create plugin-specific libraries
- Integrate with external services
- Contribute plugins to community

**Need help?** Check the [troubleshooting section](#troubleshooting) or ask in the OmniFocus forums.
