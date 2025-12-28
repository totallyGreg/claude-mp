# OmniFocus Plugin Bundle Structure

Complete reference for understanding, creating, and modifying OmniFocus Omni Automation plugin bundles (`.omnifocusjs`).

## Understanding .omnifocusjs Bundles

### What is a .omnifocusjs Bundle?

A `.omnifocusjs` file is **not a single file** — it's a **directory bundle** (also called a package), similar to macOS `.app` applications. macOS treats it as a single item in Finder, but it's actually a folder containing multiple files.

**Key Characteristics:**
- Directory disguised as a file in Finder (shows as single icon)
- Contains manifest.json, JavaScript files, and optional resources
- Can be opened in Finder with "Show Package Contents"
- Terminal and file tools treat it as a normal directory
- Cross-platform compatible (Mac, iOS, iPadOS)

### Bundle vs File Distinction

**In Finder:**
- Appears as single clickable icon with `.omnifocusjs` extension
- Double-clicking installs the plugin in OmniFocus
- Right-click → "Show Package Contents" reveals internal structure

**In Terminal / for Claude:**
- Is a directory, not a file
- Cannot use `Read` tool on the bundle path directly
- Must use `Read` with full paths to files inside: `Plugin.omnifocusjs/manifest.json`
- Can use `ls` or `Glob` to explore contents: `ls Plugin.omnifocusjs/`

## Standard Bundle Structure

### Required Structure

Every `.omnifocusjs` bundle must contain:

```
PluginName.omnifocusjs/
├── manifest.json          # REQUIRED: Plugin metadata and action definitions
└── Resources/             # REQUIRED: Directory containing action scripts
    ├── action1.js        # Action implementation file(s)
    └── action2.js        # Multiple actions supported
```

### Optional Files

Additional files can enhance plugin functionality and documentation:

```
PluginName.omnifocusjs/
├── manifest.json          # Required
├── Resources/             # Required
│   ├── action1.js
│   └── action2.js
├── README.md             # Optional: User documentation
├── INSTALL.md            # Optional: Installation instructions
├── LICENSE.txt           # Optional: License information
├── CHANGELOG.md          # Optional: Version history
└── assets/               # Optional: Images, icons, templates
    └── icon.png
```

### Directory Naming Conventions

**Bundle name:**
- Must end with `.omnifocusjs` extension
- Use PascalCase or kebab-case: `TaskAnalyzer.omnifocusjs` or `task-analyzer.omnifocusjs`
- Should be descriptive and unique

**Resources directory:**
- Must be named exactly `Resources/` (case-sensitive)
- Contains all JavaScript action files
- File names should match action identifiers (convention, not required)

## manifest.json Schema

### Complete Schema

```json
{
  "identifier": "com.author.plugin-name",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Brief description of what the plugin does",
  "label": "Plugin Name",
  "mediumLabel": "Plugin Name",
  "longLabel": "Plugin Full Name",
  "paletteLabel": "Plugin Name",
  "image": "icon-name",
  "actions": [
    {
      "identifier": "actionIdentifier",
      "label": "Action Name",
      "mediumLabel": "Action Name",
      "longLabel": "Action Full Name",
      "paletteLabel": "Action Name",
      "image": "icon-name"
    }
  ]
}
```

### Field Definitions

#### Top-Level Fields

**identifier** (required, string)
- Unique reverse-domain identifier
- Format: `com.author.plugin-name` or `com.organization.plugin-name`
- Must be globally unique
- Example: `"com.totallytools.omnifocus.ai-task-analyzer"`

**version** (required, string)
- Semantic versioning: `MAJOR.MINOR.PATCH`
- Example: `"1.0.0"`, `"2.1.3"`

**author** (required, string)
- Plugin creator name or organization
- Example: `"totally-tools"`, `"John Doe"`

**description** (required, string)
- Brief description of plugin functionality
- Displayed in plugin management UI
- Keep under 200 characters
- Example: `"Analyzes tasks using Apple Intelligence to provide insights"`

**label** (required, string)
- Short plugin name for menus
- Example: `"AI Analyzer"`

**mediumLabel** (optional, string)
- Medium-length name for toolbars
- Defaults to `label` if omitted
- Example: `"Analyze with AI"`

**longLabel** (optional, string)
- Full descriptive name
- Defaults to `label` if omitted
- Example: `"Analyze Tasks with Apple Intelligence"`

**paletteLabel** (optional, string)
- Name shown in automation palette
- Defaults to `label` if omitted
- Example: `"AI Analyzer"`

**image** (optional, string)
- SF Symbol name for plugin icon
- Browse symbols: https://developer.apple.com/sf-symbols/
- Example: `"brain.badge.waveform"`, `"chart.bar.doc.horizontal"`
- Defaults to generic icon if omitted

**actions** (required, array)
- Array of action definitions (at least one required)
- See "Action Fields" below

#### Action Fields

Each object in the `actions` array:

**identifier** (required, string)
- Unique action identifier within plugin
- Must match JavaScript filename in `Resources/` (convention)
- Example: `"analyzeTasksWithAI"` → `Resources/analyzeTasksWithAI.js`

**label** (required, string)
- Short action name for menus
- Example: `"Analyze My Tasks"`

**mediumLabel** (optional, string)
- Medium-length action name
- Defaults to `label` if omitted

**longLabel** (optional, string)
- Full descriptive action name
- Defaults to `label` if omitted

**paletteLabel** (optional, string)
- Name shown in automation palette
- Defaults to `label` if omitted

**image** (optional, string)
- SF Symbol name for action icon
- Can differ from plugin icon
- Defaults to plugin image if omitted

### Example Configurations

#### Minimal manifest.json

```json
{
  "identifier": "com.myname.simple-plugin",
  "version": "1.0.0",
  "author": "My Name",
  "description": "Simple example plugin",
  "label": "Simple Plugin",
  "actions": [
    {
      "identifier": "doSomething",
      "label": "Do Something"
    }
  ]
}
```

#### Full-featured manifest.json

```json
{
  "identifier": "com.totallytools.omnifocus.ai-analyzer",
  "version": "2.0.0",
  "author": "totally-tools",
  "description": "Analyzes tasks and projects using Apple Foundation Models (Apple Intelligence) to provide intelligent insights about workload, priorities, project health, and recommendations.",
  "label": "AI Analyzer",
  "mediumLabel": "Analyze with AI",
  "longLabel": "Analyze Tasks & Projects with Apple Intelligence",
  "paletteLabel": "AI Analyzer",
  "image": "brain.badge.waveform",
  "actions": [
    {
      "identifier": "analyzeTasksWithAI",
      "label": "Analyze My Tasks",
      "mediumLabel": "Analyze Tasks with AI",
      "longLabel": "Analyze My Tasks with Apple Intelligence",
      "paletteLabel": "AI Task Analyzer",
      "image": "brain.badge.waveform"
    },
    {
      "identifier": "analyzeProjects",
      "label": "Analyze Projects",
      "mediumLabel": "Analyze Projects with AI",
      "longLabel": "Analyze Project Hierarchy with Apple Intelligence",
      "paletteLabel": "AI Project Analyzer",
      "image": "chart.bar.doc.horizontal"
    }
  ]
}
```

#### Multi-action plugin

```json
{
  "identifier": "com.example.task-manager",
  "version": "1.2.0",
  "author": "Example Author",
  "description": "Comprehensive task management utilities",
  "label": "Task Manager",
  "image": "checklist",
  "actions": [
    {
      "identifier": "todaysTasks",
      "label": "Today's Tasks",
      "image": "calendar"
    },
    {
      "identifier": "flaggedTasks",
      "label": "Flagged Tasks",
      "image": "flag"
    },
    {
      "identifier": "overdueTasks",
      "label": "Overdue Tasks",
      "image": "exclamationmark.triangle"
    }
  ]
}
```

## Working with Plugin Bundles

### Detecting Plugin Bundles

**Check if path is a plugin:**
```bash
# Bash approach
if [[ "$path" == *.omnifocusjs ]]; then
    echo "This is a plugin bundle"
fi

# Or check if directory exists
if [ -d "path/to/Plugin.omnifocusjs" ]; then
    echo "Plugin bundle directory exists"
fi
```

**Using tools:**
```bash
# List all plugins in a directory
ls -d *.omnifocusjs

# Find all plugins recursively
find . -name "*.omnifocusjs" -type d
```

### Reading Files from Bundles

**IMPORTANT:** Cannot use `Read` tool on the bundle path directly. Must read individual files within the bundle.

**Correct approach:**
```python
# Read manifest.json
Read("/path/to/Plugin.omnifocusjs/manifest.json")

# Read action script
Read("/path/to/Plugin.omnifocusjs/Resources/analyzeTasksWithAI.js")

# Read README
Read("/path/to/Plugin.omnifocusjs/README.md")
```

**Incorrect approach:**
```python
# This will FAIL - .omnifocusjs is a directory, not a file
Read("/path/to/Plugin.omnifocusjs")  # ❌ ERROR
```

### Exploring Bundle Contents

**List files in bundle:**
```bash
# Basic listing
ls /path/to/Plugin.omnifocusjs/

# Detailed listing
ls -la /path/to/Plugin.omnifocusjs/

# Recursive listing
ls -R /path/to/Plugin.omnifocusjs/

# Tree view (if tree is installed)
tree /path/to/Plugin.omnifocusjs/
```

**Using Glob tool:**
```python
# Find all files in bundle
Glob(pattern="*", path="/path/to/Plugin.omnifocusjs/")

# Find all JavaScript files
Glob(pattern="**/*.js", path="/path/to/Plugin.omnifocusjs/")

# Find manifest
Glob(pattern="manifest.json", path="/path/to/Plugin.omnifocusjs/")
```

### Common Glob Patterns

```bash
# Find all .omnifocusjs bundles in current directory
**/*.omnifocusjs

# Find all manifest.json files
**/*.omnifocusjs/manifest.json

# Find all action scripts
**/*.omnifocusjs/Resources/*.js

# Find all README files in plugins
**/*.omnifocusjs/README.md
```

### Common Grep Patterns

```bash
# Search for specific identifier in all manifests
grep -r '"identifier"' **/*.omnifocusjs/manifest.json

# Search for action names
grep -r '"label"' **/*.omnifocusjs/manifest.json

# Search for version numbers
grep -r '"version"' **/*.omnifocusjs/manifest.json

# Search in action scripts
grep -r "LanguageModel" **/*.omnifocusjs/Resources/

# Search for specific function calls
grep -r "Document.defaultDocument" **/*.omnifocusjs/Resources/
```

## Creating Plugin Bundles

### Step-by-Step Creation Process

**1. Create bundle directory:**
```bash
mkdir PluginName.omnifocusjs
mkdir PluginName.omnifocusjs/Resources
```

**2. Create manifest.json:**
```bash
cat > PluginName.omnifocusjs/manifest.json << 'EOF'
{
  "identifier": "com.author.plugin-name",
  "version": "1.0.0",
  "author": "Author Name",
  "description": "Plugin description",
  "label": "Plugin Name",
  "actions": [
    {
      "identifier": "actionName",
      "label": "Action Name"
    }
  ]
}
EOF
```

**3. Create action script:**
```bash
cat > PluginName.omnifocusjs/Resources/actionName.js << 'EOF'
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        try {
            // Your code here
            const doc = Document.defaultDocument;

            // Show result
            const alert = new Alert("Success", "Action completed");
            alert.show();

        } catch (error) {
            console.error("Error:", error);
            const errorAlert = new Alert("Error", error.message);
            errorAlert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
EOF
```

**4. Create optional README:**
```bash
cat > PluginName.omnifocusjs/README.md << 'EOF'
# Plugin Name

Description of your plugin.

## Installation

Double-click the .omnifocusjs bundle to install.

## Usage

Describe how to use the plugin.
EOF
```

**5. Test installation:**
```bash
# Install by double-clicking in Finder, or:
open PluginName.omnifocusjs
```

### Adding Multiple Actions

To support multiple actions in one plugin:

**1. Update manifest.json actions array:**
```json
{
  "actions": [
    {
      "identifier": "action1",
      "label": "First Action"
    },
    {
      "identifier": "action2",
      "label": "Second Action"
    },
    {
      "identifier": "action3",
      "label": "Third Action"
    }
  ]
}
```

**2. Create corresponding scripts:**
```bash
# Create one .js file for each action
touch Resources/action1.js
touch Resources/action2.js
touch Resources/action3.js
```

**3. Implement each action:**
Each file should follow the same structure:
```javascript
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        // Unique implementation for this action
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### Best Practices for Plugin Organization

**Naming conventions:**
- Use clear, descriptive names for bundle and actions
- Match JavaScript filenames to action identifiers
- Use PascalCase for bundle names: `TaskAnalyzer.omnifocusjs`
- Use camelCase for action identifiers: `analyzeTasksWithAI`

**File organization:**
- Keep all JavaScript in `Resources/`
- Put documentation at bundle root
- Use `assets/` subdirectory for images, templates
- Keep manifest.json clean and readable

**Version management:**
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Document changes in CHANGELOG.md
- Update version in manifest.json for each release

**Documentation:**
- Always include README.md with usage instructions
- Document requirements (OS version, OmniFocus version)
- Provide examples of plugin usage
- Include troubleshooting section

## Action Script Structure

### Complete Template

```javascript
/**
 * Action Name - Brief description
 *
 * Detailed description of what this action does.
 *
 * Requirements:
 * - OmniFocus 3+
 * - macOS 10.15+ / iOS 13+
 */

(() => {
    // Define the action
    const action = new PlugIn.Action(async function(selection, sender) {
        try {
            // 1. Get document and data
            const doc = Document.defaultDocument;

            // 2. Process tasks/projects
            // Your logic here

            // 3. Show results
            const alert = new Alert("Title", "Message");
            alert.show();

        } catch (error) {
            // Error handling
            console.error("Error:", error);
            const errorAlert = new Alert(
                "Error",
                `Failed: ${error.message}`
            );
            errorAlert.show();
        }
    });

    // Validation function - controls when action is enabled
    action.validate = function(selection, sender) {
        // Return true to enable, false to disable
        return true;
    };

    // Return the action
    return action;
})();
```

### Plugin.Action Wrapper Pattern

Every action must be wrapped in the `PlugIn.Action` pattern:

```javascript
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        // Action implementation
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

**Parameters:**
- `selection`: Currently selected items in OmniFocus (tasks, projects, etc.)
- `sender`: The UI element that triggered the action

**Async support:**
```javascript
const action = new PlugIn.Action(async function(selection, sender) {
    // Can use await
    const result = await someAsyncOperation();
});
```

### Validation Function

Controls when the action is enabled/disabled:

```javascript
action.validate = function(selection, sender) {
    // Example: Only enable if tasks are selected
    return selection.tasks.length > 0;

    // Example: Only enable if projects are selected
    return selection.projects.length > 0;

    // Example: Always enable
    return true;

    // Example: Never enable (for testing)
    return false;
};
```

### Error Handling Patterns

**Basic error handling:**
```javascript
try {
    // Your code
} catch (error) {
    console.error("Error:", error);
    new Alert("Error", error.message).show();
}
```

**Detailed error handling:**
```javascript
try {
    // Your code
} catch (error) {
    console.error("Error:", error);
    const errorAlert = new Alert(
        "Error",
        `Failed to complete action: ${error.message}\n\nPlease check:\n• OmniFocus version\n• Permissions\n• Console for details`
    );
    errorAlert.show();
}
```

**Requirement checking:**
```javascript
try {
    // Check requirements
    if (!LanguageModel) {
        throw new Error("Requires OmniFocus 4.8+ and macOS 15.2+");
    }

    // Your code

} catch (error) {
    console.error("Error:", error);
    new Alert("Error", error.message).show();
}
```

### Common API Patterns

**Accessing document:**
```javascript
const doc = Document.defaultDocument;
```

**Getting tasks:**
```javascript
const allTasks = doc.flattenedTasks;
const activeTasks = allTasks.filter(t => !t.completed && !t.dropped);
```

**Getting projects:**
```javascript
const allProjects = doc.flattenedProjects;
const activeProjects = allProjects.filter(p => p.status === "active");
```

**Showing alerts:**
```javascript
const alert = new Alert("Title", "Message");
alert.show();
```

**Creating forms:**
```javascript
const form = new Form();
form.addField(new Form.Field.String("fieldName", "Label", "Placeholder"));
const result = await form.show("Form Title", "OK");
const value = result.values["fieldName"];
```

**Using Apple Intelligence:**
```javascript
const session = new LanguageModel.Session();
const response = await session.respondWithSchema(prompt, schema);
const result = JSON.parse(response);
```

See `omni_automation.md` and `omni_automation_shared.md` for complete API reference.

## Plugin Installation & Testing

### Installation Locations

**macOS:**
```
~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Library/Application Support/OmniFocus/Plug-Ins/
```

**iOS/iPadOS:**
- Managed through OmniFocus app (Automation → Plug-Ins)
- Can import from Files app or iCloud

### Installation Methods

**Method 1: Double-click (recommended for testing)**
```bash
open PluginName.omnifocusjs
```
OmniFocus will prompt to install.

**Method 2: Manual copy**
```bash
cp -r PluginName.omnifocusjs ~/Library/Group\ Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Library/Application\ Support/OmniFocus/Plug-Ins/
```

**Method 3: Via OmniFocus (iOS)**
1. Share .omnifocusjs bundle to device
2. Open in OmniFocus
3. Tap "Install"

### Testing During Development

**1. Install plugin:**
```bash
open PluginName.omnifocusjs
```

**2. Open OmniFocus Automation Console:**
- Press ⌃⌥⌘I (Control-Option-Command-I)
- Or: View → Automation → Console

**3. Test action manually:**
```javascript
PlugIn.find("com.author.plugin-name").action("actionIdentifier").perform()
```

**4. View console output:**
- Check for errors
- View console.log() output
- Debug issues

**5. Make changes:**
- Edit JavaScript files
- Save changes
- Restart OmniFocus to reload

**6. Repeat:**
- Test → Fix → Test cycle

### Troubleshooting

**Plugin doesn't appear in menu:**
- Check manifest.json is valid JSON (use `jq` or JSON validator)
- Verify file structure matches requirements
- Ensure `Resources/` directory exists and contains .js files
- Restart OmniFocus completely
- Check Console.app for error messages

**Action is disabled (grayed out):**
- Check `action.validate()` function returns true
- Verify requirements are met (selection, permissions, etc.)
- Test in Automation Console to see actual error

**Script errors:**
- Open Automation Console (⌃⌥⌘I)
- Look for JavaScript errors
- Check syntax and API usage
- Verify all required APIs are available

**Plugin won't install:**
- Ensure bundle name ends with `.omnifocusjs`
- Check manifest.json syntax
- Verify no duplicate identifiers with existing plugins
- Try manual installation to bypass double-click issues

## Modifying Existing Plugins

### Reading Plugin Contents

**1. Find plugin bundle:**
```bash
# In skill assets
ls skills/omnifocus-manager/assets/*.omnifocusjs

# In system location
ls ~/Library/Group\ Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Library/Application\ Support/OmniFocus/Plug-Ins/
```

**2. Read manifest:**
```python
Read("path/to/Plugin.omnifocusjs/manifest.json")
```

**3. List action scripts:**
```bash
ls path/to/Plugin.omnifocusjs/Resources/
```

**4. Read action script:**
```python
Read("path/to/Plugin.omnifocusjs/Resources/actionName.js")
```

### Making Changes

**1. Edit manifest.json:**
```python
# Read current manifest
manifest = Read("Plugin.omnifocusjs/manifest.json")

# Make changes
Edit("Plugin.omnifocusjs/manifest.json",
     old_string='...',
     new_string='...')
```

**2. Edit action scripts:**
```python
Edit("Plugin.omnifocusjs/Resources/actionName.js",
     old_string='...',
     new_string='...')
```

**3. Add new action:**
```bash
# Create new action script
Write("Plugin.omnifocusjs/Resources/newAction.js", content)

# Update manifest.json to include new action
Edit("Plugin.omnifocusjs/manifest.json", ...)
```

**4. Test changes:**
```bash
# Reinstall plugin
open Plugin.omnifocusjs

# Or restart OmniFocus to reload
```

### Version Updates

When modifying plugins:

**1. Update version in manifest.json:**
- Increment PATCH for bug fixes: 1.0.0 → 1.0.1
- Increment MINOR for new features: 1.0.0 → 1.1.0
- Increment MAJOR for breaking changes: 1.0.0 → 2.0.0

**2. Document changes:**
- Update README.md
- Update CHANGELOG.md (if present)
- Add version history comments

**3. Test thoroughly:**
- Verify all actions still work
- Test new functionality
- Check for errors in Console

## Complete Examples

See actual working examples in this skill:

**Example 1: Today's Tasks**
- Location: `assets/TodaysTasks.omnifocusjs`
- Shows tasks due or deferred today
- Demonstrates: Task filtering, date handling, Alert display

**Example 2: AI Task Analyzer**
- Location: `assets/AITaskAnalyzer.omnifocusjs`
- Multi-action plugin (task analysis + project analysis)
- Demonstrates: Apple Intelligence, Forms, FileSaver, structured schemas
- Complete documentation: `assets/AITaskAnalyzer.omnifocusjs/README.md`

## Related Documentation

- **Omni Automation API:** `omni_automation.md` - JavaScript API reference
- **Shared Classes:** `omni_automation_shared.md` - Alert, Form, FileSaver, etc.
- **Complete API Spec:** `OmniFocus-API.md` - Full OmniFocus API
- **Installation Guide:** `plugin_installation.md` - Installing and using plugins
- **Apple Intelligence:** `foundation_models_integration.md` - AI-powered automation
