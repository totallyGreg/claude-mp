# Omni Automation Plug-In Installation & Usage Guide

Comprehensive guide for installing, using, and creating Omni Automation plug-ins for OmniFocus.

## Understanding .omnifocusjs Bundles

**CRITICAL:** `.omnifocusjs` files are **directory bundles**, not single files.

### What is a Bundle?

A `.omnifocusjs` bundle is a directory that appears as a single file in Finder, similar to macOS `.app` applications. Understanding this distinction is essential for working with plugins programmatically.

**In Finder:**
- Appears as a single clickable icon
- Has `.omnifocusjs` extension
- Double-clicking installs the plugin
- Right-click → "Show Package Contents" reveals the internal structure

**In Terminal / for Claude:**
- Is actually a **directory**, not a file
- Contains multiple files: `manifest.json`, `Resources/`, etc.
- Cannot be read directly with Read tool (will fail with "is a directory" error)
- Must read individual files within the bundle

### Navigating Bundles

**Correct approach for reading bundle files:**
```bash
# Read the manifest
Read("/path/to/Plugin.omnifocusjs/manifest.json")

# Read an action script
Read("/path/to/Plugin.omnifocusjs/Resources/actionName.js")

# Read documentation
Read("/path/to/Plugin.omnifocusjs/README.md")
```

**Incorrect approach:**
```bash
# This will FAIL - cannot read a directory
Read("/path/to/Plugin.omnifocusjs")  # ❌ ERROR: Is a directory
```

**Exploring bundle contents:**
```bash
# List files in bundle
ls /path/to/Plugin.omnifocusjs/

# List with details
ls -la /path/to/Plugin.omnifocusjs/

# Recursive listing
ls -R /path/to/Plugin.omnifocusjs/

# Using Glob tool
Glob(pattern="*", path="/path/to/Plugin.omnifocusjs/")
Glob(pattern="**/*.js", path="/path/to/Plugin.omnifocusjs/")
```

### Bundle Structure

Standard `.omnifocusjs` bundle structure:
```
PluginName.omnifocusjs/          # Bundle directory
├── manifest.json                 # Required: Plugin metadata
├── Resources/                    # Required: Action scripts directory
│   ├── action1.js               # Action implementation files
│   └── action2.js
├── README.md                    # Optional: Documentation
├── INSTALL.md                   # Optional: Installation guide
└── [other files]                # Optional: Additional resources
```

For complete details on bundle structure, manifest.json schema, creating plugins, and working with bundles, see `omnifocus_plugin_structure.md`.

## Overview

This skill provides two ready-to-use Omni Automation plug-ins in the `assets/` directory that demonstrate common automation patterns. These serve as both functional tools and templates for creating custom automation.

## Available Plug-Ins

### Today's Tasks (`assets/TodaysTasks.omnifocusjs`)

Shows all tasks that are due or deferred to today, grouped by project. Provides a quick overview of what needs to be worked on today.

**Features:**
- Displays tasks due today
- Displays tasks deferred until today
- Groups tasks by project
- Shows flagged status
- Shows due times for tasks with specific times
- Excludes completed and dropped tasks

**Location:** `assets/TodaysTasks.omnifocusjs`

### AI Task Analyzer (`assets/AITaskAnalyzer.omnifocusjs`)

AI-powered task analysis using Apple Foundation Models (Apple Intelligence) to provide intelligent insights about your workload, priorities, and actionable recommendations.

**Features:**
- Priority recommendations with reasoning
- Workload assessment
- Overdue task pattern detection
- Time management suggestions
- GTD-aligned action items

**Requirements:**
- OmniFocus 4.8+
- macOS 15.2+ / iOS 18.2+ / iPadOS 18.2+
- Apple Silicon (Mac) or iPhone 15 Pro+

**Location:** `assets/AITaskAnalyzer.omnifocusjs`

**Documentation:** See `foundation_models_integration.md` for complete Apple Intelligence integration details

## Installation

### macOS

1. **Double-click the plug-in:**
   - Simply double-click the `.omnifocusjs` folder
   - OmniFocus will prompt to install the plug-in
   - Click "Install"

2. **Manual installation:**
   - Copy the `.omnifocusjs` folder to:
     ```
     ~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Library/Application Support/OmniFocus/Plug-Ins/
     ```
   - Restart OmniFocus

### iOS/iPadOS

1. **Share the plug-in:**
   - Compress the `.omnifocusjs` folder as a ZIP
   - Share to your iOS device (AirDrop, iCloud, email, etc.)
   - Tap the ZIP file
   - Tap "Share" → "OmniFocus"
   - Tap "Install"

2. **Via Files app:**
   - Save the `.omnifocusjs` folder to iCloud Drive
   - Open OmniFocus on iOS
   - Go to Automation → Plug-Ins
   - Tap "+" to add a plug-in
   - Navigate to the folder and select it

## Usage

### Running a Plug-In

**macOS:**
- Menu: Tools → [Plug-In Name]
- Keyboard: Assign a keyboard shortcut in System Preferences
- Toolbar: Add plug-in to toolbar (View → Customize Toolbar)

**iOS/iPadOS:**
- Tap the "≡" menu
- Scroll to "Automation"
- Tap the plug-in name

### Modifying Plug-Ins

All plug-ins are fully editable. To customize:

1. Right-click the `.omnifocusjs` folder
2. Select "Show Package Contents"
3. Edit `Resources/[action-name].js` with your preferred editor
4. Save changes
5. Restart OmniFocus to reload

## Creating Your Own Plug-Ins

For comprehensive documentation on creating custom plug-ins, see:
- **`omnifocus_plugin_structure.md`** - Complete bundle structure, manifest.json schema, action templates, and step-by-step creation guide
- **`omni_automation.md`** - JavaScript API reference and patterns
- **`omni_automation_shared.md`** - UI components (Alert, Form, FileSaver, etc.)

Or use the available plug-ins in `assets/` as templates.

### Basic Structure

```
MyPlugin.omnifocusjs/
├── manifest.json          # Plug-in metadata
└── Resources/
    └── myAction.js        # Action script
```

### manifest.json Template

```json
{
  "identifier": "com.yourname.pluginname",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "What your plug-in does",
  "label": "Plugin Name",
  "actions": [
    {
      "identifier": "actionIdentifier",
      "label": "Action Name"
    }
  ]
}
```

### Action Script Template

```javascript
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        try {
            // Your automation code here
            const doc = Document.defaultDocument;
            const tasks = doc.flattenedTasks;

            // Process tasks...

            // Show results
            const alert = new Alert("Title", "Message");
            alert.show();

        } catch (error) {
            console.error("Error:", error);
            new Alert("Error", error.message).show();
        }
    });

    action.validate = function(selection, sender) {
        return true; // Return false to disable the action
    };

    return action;
})();
```

## Debugging

### Console Access

**macOS:**
- View → Automation → Console (⌃⌥⌘I)
- Type JavaScript and press Enter
- View console.log() output

**iOS:**
- Not available (use Alerts for debugging)

### Common Issues

1. **Plug-in doesn't appear:**
   - Check file structure matches the template
   - Verify manifest.json is valid JSON
   - Restart OmniFocus

2. **Script errors:**
   - Check the Console for error messages
   - Verify JavaScript syntax
   - Add try/catch blocks for better error handling

3. **Action is disabled:**
   - Check the validate() function
   - Ensure it returns true when the action should be available

## Resources

### Skill References

- **Omni Automation Guide:** See `omni_automation.md` - Complete API reference and practical examples
- **Apple Intelligence Integration:** See `foundation_models_integration.md` - AI-powered automation with Apple Foundation Models
- **Shared Classes Reference:** See `omni_automation_shared.md` - Cross-platform shared APIs (Alert, Form, FilePicker, etc.)

### External Documentation

- **Omni Automation Documentation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **Plug-In Library:** [omni-automation.com/omnifocus/actions.html](https://omni-automation.com/omnifocus/actions.html)
- **Official API Reference:** See `OmniFocus-API.md` for complete OmniFocus API specification

## License

These example plug-ins are provided as-is for educational purposes. Feel free to use, modify, and distribute them as needed.
