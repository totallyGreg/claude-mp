# Plugin Quickstart: Your First OmniFocus Plugin in 5 Minutes

Get started with OmniFocus plugin development using the modular library system.

## What You'll Build

A simple plugin that shows today's tasks when clicked. You'll learn:
- Plugin bundle structure
- Using taskMetrics library
- Displaying results with alerts

**Time:** 5 minutes
**Difficulty:** Beginner
**Platform:** Mac + iOS

---

## Prerequisites

- OmniFocus installed
- Text editor
- Basic JavaScript knowledge (helpful but not required)

---

## Step 1: Create Plugin Structure (1 min)

Create a folder with the `.omnifocusjs` extension:

```bash
mkdir MyFirstPlugin.omnifocusjs
mkdir MyFirstPlugin.omnifocusjs/Resources
```

**Important:** `.omnifocusjs` is a bundle (directory), not a file. Finder shows it as a single icon, but it's actually a folder.

---

## Step 2: Create manifest.json (1 min)

Create `MyFirstPlugin.omnifocusjs/manifest.json`:

```json
{
  "identifier": "com.myname.my-first-plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "My first OmniFocus plugin",
  "label": "My First Plugin",
  "libraries": ["taskMetrics"],
  "actions": [
    {
      "identifier": "showToday",
      "label": "Show Today's Tasks"
    }
  ]
}
```

**Key parts:**
- `identifier`: Unique ID (reverse domain notation)
- `libraries`: Declares taskMetrics library for use
- `actions`: Menu items that appear in OmniFocus

---

## Step 3: Create Action Script (2 min)

Create `MyFirstPlugin.omnifocusjs/Resources/showToday.js`:

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Load taskMetrics library (declared in manifest)
        const metrics = this.plugIn.library("taskMetrics");

        // Get today's tasks
        const tasks = metrics.getTodayTasks();

        // Format message
        let message = `You have ${tasks.length} tasks today:\n\n`;

        if (tasks.length === 0) {
            message = "No tasks due or deferred to today!";
        } else {
            tasks.forEach((task, index) => {
                message += `${index + 1}. ${task.name}\n`;
                if (task.project) {
                    message += `   Project: ${task.project}\n`;
                }
            });
        }

        // Show alert
        const alert = new Alert("Today's Tasks", message);
        await alert.show();
    });

    action.validate = function(selection, sender) {
        return true; // Always available
    };

    return action;
})();
```

**What this does:**
1. Loads the taskMetrics library
2. Queries today's tasks
3. Formats results as text
4. Displays in an alert dialog

---

## Step 4: Install and Test (1 min)

**On Mac:**
1. Double-click `MyFirstPlugin.omnifocusjs`
2. Choose storage location (Local or iCloud)
3. Click "Install"
4. Open OmniFocus → Tools → My First Plugin → Show Today's Tasks

**On iOS:**
1. Transfer plugin to device (AirDrop, iCloud, etc.)
2. Tap the plugin file
3. Tap "Install"
4. Open OmniFocus → ≡ menu → Automation → Show Today's Tasks

**Expected result:** Alert shows your tasks for today!

---

## What You Just Learned

✅ Plugin bundle structure (`.omnifocusjs` directory + manifest + Resources)
✅ Using PlugIn.Library to load shared code
✅ Creating actions that appear in OmniFocus menu
✅ Displaying results with Alert dialogs
✅ Cross-platform compatibility (Mac + iOS)

---

## Next Steps

### Add More Features

**Show flagged tasks:**
```javascript
// In manifest.json, add another action:
{
  "identifier": "showFlagged",
  "label": "Show Flagged Tasks"
}

// Create Resources/showFlagged.js:
const tasks = metrics.getFlaggedTasks();
// ... rest similar to showToday.js
```

**Export to clipboard:**
```javascript
// In manifest.json:
"libraries": ["taskMetrics", "exportUtils"]

// In action:
const exporter = this.plugIn.library("exportUtils");
exporter.toClipboard(tasks, { format: 'markdown' });
```

### Explore Examples

**SimpleQuery plugin:** Complete working example
```
../assets/examples/plugins/SimpleQuery.omnifocusjs/
```

**See:**
- 3 actions using taskMetrics + exportUtils
- Alert dialogs
- Different query types

### Use More Libraries

**Available libraries:**
- `taskMetrics` - Query tasks (today, overdue, flagged, etc.)
- `exportUtils` - Export to JSON, CSV, Markdown, HTML
- `insightPatterns` - Detect patterns (stalled projects, overdue, etc.)
- `templateEngine` - Create tasks from templates
- `patterns` - Advanced workflows (batch operations, AI-ready)

**Declare in manifest.json:**
```json
"libraries": ["taskMetrics", "exportUtils", "insightPatterns"]
```

**Use in action:**
```javascript
const metrics = this.plugIn.library("taskMetrics");
const exporter = this.plugIn.library("exportUtils");
const insights = this.plugIn.library("insightPatterns");
```

---

## Common Patterns

### Form Input

Ask user for input:
```javascript
const form = new Form();
form.addField(new Form.Field.String("name", "Task Name", null));

const formPrompt = new FormPrompt("Create Task", form);
const result = await formPrompt.show("Create", "Cancel");

if (result) {
    const taskName = result.values.name;
    // Use taskName...
}
```

### Selection-Based Actions

Work with selected items:
```javascript
action.validate = function(selection, sender) {
    return selection.tasks.length > 0; // Only enable if tasks selected
};

// In action:
const selectedTask = selection.tasks[0];
console.log(`Selected: ${selectedTask.name}`);
```

### Error Handling

Handle errors gracefully:
```javascript
try {
    const tasks = metrics.getTodayTasks();
    // ... process tasks
} catch (error) {
    const alert = new Alert("Error", error.message);
    await alert.show();
}
```

---

## Troubleshooting

**Plugin doesn't appear in menu:**
- Check manifest.json is valid JSON (use a JSON validator)
- Verify file structure matches exactly (manifest.json at root, actions in Resources/)
- Restart OmniFocus completely

**"Library not found" error:**
- Make sure library name in manifest.json matches exactly
- Libraries are case-sensitive: `"taskMetrics"` not `"TaskMetrics"`

**Action is grayed out:**
- Check `validate()` function returns `true`
- Ensure you're not requiring selection when none exists

**Script errors:**
- Open Automation Console: View → Automation → Console (⌃⌥⌘I)
- Add `console.log()` statements for debugging
- Check for typos in library/function names

---

## Resources

### Documentation
- **Complete Plugin Guide:** `../plugin_development_guide.md`
- **Library Documentation:** `../../libraries/README.md`
- **Plugin API Reference:** `../plugin_api.md`
- **Example Plugins:** `../../assets/examples/plugins/`

### API References
- **OmniFocus API:** `../OmniFocus-API.md`
- **Omni Automation:** `../omnifocus_automation.md`
- **Shared Classes:** `../omni_automation_shared.md` (Alert, Form, FileSaver, etc.)

### External Resources
- [Omni Automation](https://omni-automation.com/omnifocus/)
- [Plug-In Library](https://omni-automation.com/omnifocus/actions.html)
- [OmniFocus Forums](https://discourse.omnigroup.com/c/omnifocus)

---

## What's Next?

**Beginner:**
- Try the examples in `../../assets/examples/plugins/`
- Modify this plugin to show overdue tasks
- Add export functionality

**Intermediate:**
- Use multiple libraries together
- Create multi-action plugins
- Add form inputs for user preferences

**Advanced:**
- Use patterns library for batch operations
- Integrate with insightPatterns for analysis
- Create plugins that compose multiple workflows

**Ready for more?** See the complete [Plugin Development Guide](../plugin_development_guide.md) for advanced topics.
