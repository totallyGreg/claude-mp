# Omni Automation Plug-In Examples

This directory contains example Omni Automation plug-ins for OmniFocus that demonstrate common automation patterns.

## Available Plug-Ins

### Today's Tasks (TodaysTasks.omnifocusjs)

Shows all tasks that are due or deferred to today, grouped by project. Provides a quick overview of what needs to be worked on today.

**Features:**
- Displays tasks due today
- Displays tasks deferred until today
- Groups tasks by project
- Shows flagged status
- Shows due times for tasks with specific times
- Excludes completed and dropped tasks

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

See the [Omni Automation Reference](../references/omni_automation.md) for complete documentation on creating custom plug-ins.

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

- **Omni Automation Documentation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **Plug-In Library:** [omni-automation.com/omnifocus/actions.html](https://omni-automation.com/omnifocus/actions.html)
- **Reference Guide:** [../references/omni_automation.md](../references/omni_automation.md)

## License

These example plug-ins are provided as-is for educational purposes. Feel free to use, modify, and distribute them as needed.
