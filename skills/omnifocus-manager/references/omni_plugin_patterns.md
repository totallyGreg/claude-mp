# Omni Automation Plugin Patterns

Advanced patterns for Omni Automation plugins that apply across all Omni applications (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan).

## Plugin Formats

### 1. Solitary Action Plugin (Single File)

Best for: Simple one-off automation, single action, no shared code needed.

**File:** `MyPlugin.omnijs` (or `.omnifocusjs` for OmniFocus-only)

```javascript
/*{
    "type": "action",
    "targets": ["omnifocus"],
    "author": "Your Name",
    "identifier": "com.yourcompany.pluginname",
    "version": "1.0",
    "description": "What the plugin does",
    "label": "Menu Label",
    "shortLabel": "Short",
    "mediumLabel": "Medium Label",
    "paletteLabel": "Palette Label",
    "image": "list.bullet"
}*/
(() => {
    const action = new PlugIn.Action(function(selection, sender) {
        // Action code here
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### 2. Solitary Library Plugin (Single File)

Best for: Reusable utility functions shared across plugins.

**File:** `MyLibrary.omnijs`

```javascript
/*{
    "type": "library",
    "targets": ["omnifocus"],
    "identifier": "com.yourcompany.libraryname",
    "version": "1.0"
}*/
(() => {
    const lib = new PlugIn.Library(new Version("1.0"));

    lib.myFunction = function(param) {
        return result;
    };

    return lib;
})();
```

### 3. Bundle Plugin (Folder Structure)

Best for: Multiple actions, shared libraries, localization, complex workflows.

```
MyPlugin.omnifocusjs/
├── manifest.json
└── Resources/
    ├── action1.js
    ├── action2.js
    ├── myLibrary.js
    └── en.lproj/
        ├── manifest.strings      # Plugin display name
        ├── action1.strings       # Action 1 labels
        └── action2.strings       # Action 2 labels
```

**manifest.json:**
```json
{
  "identifier": "com.yourcompany.pluginname",
  "version": "1.0.0",
  "defaultLocale": "en",
  "author": "Your Name",
  "description": "Plugin description",
  "image": "brain.head.profile",
  "actions": [
    {"identifier": "action1", "image": "list.bullet"},
    {"identifier": "action2", "image": "chart.bar"}
  ],
  "libraries": [
    {"identifier": "myLibrary"}
  ]
}
```

**manifest.strings:**
```
"com.yourcompany.pluginname" = "My Plugin Display Name";
```

**action1.strings:**
```
"label" = "Action Menu Label";
"shortLabel" = "Short";
"mediumLabel" = "Medium Label";
"longLabel" = "Full Long Label for Action";
"paletteLabel" = "Palette Label";
```

---

## Cross-Plugin Calling

Call actions from other installed plugins.

### Finding Plugins

```javascript
// Get all installed plugin identifiers
var pluginIDs = PlugIn.all.map(plugin => plugin.identifier);
console.log(pluginIDs.join("\n"));

// Find a specific plugin
var plugin = PlugIn.find("com.example.myplugin");
if (plugin === null) {
    throw new Error("Plugin not installed.");
}

// Get action names from a plugin
var actionNames = plugin.actions.map(action => action.name);
console.log(actionNames);
```

### Validating Before Calling

```javascript
function validatePlugInAction(pluginID, actionName) {
    var plugin = PlugIn.find(pluginID);
    if (plugin === null) {
        throw new Error("Plugin not installed.");
    }

    var actionNames = plugin.actions.map(action => action.name);
    if (actionNames.indexOf(actionName) === -1) {
        throw new Error(`Action "${actionName}" is not in the plugin.`);
    }

    return plugin.action(actionName).validate();
}
```

### Executing Plugin Actions

```javascript
function performPlugInAction(pluginID, actionName) {
    var plugin = PlugIn.find(pluginID);
    if (plugin === null) {
        throw new Error("Plugin not installed.");
    }

    var actionNames = plugin.actions.map(action => action.name);
    if (actionNames.indexOf(actionName) === -1) {
        throw new Error(`Action "${actionName}" is not in the plugin.`);
    }

    if (plugin.action(actionName).validate()) {
        plugin.action(actionName).perform();
    } else {
        throw new Error(`The action "${actionName}" is not validated to execute.`);
    }
}

// Usage
performPlugInAction("com.example.myplugin", "myActionName");
```

### Handling External Calls

When a plugin action is called from a script (not menu/toolbar), `selection` is undefined:

```javascript
const action = new PlugIn.Action(function(selection, sender) {
    // Handle external calling
    if (typeof selection === 'undefined') {
        // Generate selection from document state
        let nodes = document.editors[0].selectedNodes;
        let selectedItems = nodes.map(node => node.object);
    } else {
        let selectedItems = selection.tasks; // or selection.items
    }

    // Action code using selectedItems...
});

action.validate = function(selection, sender) {
    if (typeof selection === 'undefined') {
        // External call - check document state
        return document.editors[0].selectedNodes.length > 0;
    }
    return selection.tasks.length > 0;
};
```

---

## Sender Parameters

The `sender` parameter tells you how the action was invoked and allows dynamic UI updates.

### Sender Types

- `MenuItem` - Action invoked from menu
- `ToolbarItem` - Action invoked from toolbar
- `undefined` - Action invoked from remote script

### Dynamic Menu/Toolbar Labels

```javascript
action.validate = function(selection, sender) {
    if (selection.tasks.length === 1) {
        var task = selection.tasks[0];
        var isFlagged = task.flagged;

        if (sender instanceof MenuItem) {
            sender.label = isFlagged ? 'Remove Flag' : 'Add Flag';
            sender.image = Image.symbolNamed(isFlagged ? 'flag.slash' : 'flag');
        } else if (sender instanceof ToolbarItem) {
            sender.label = isFlagged ? 'Unflag' : 'Flag';
            sender.toolTip = isFlagged ? 'Click to remove flag' : 'Click to add flag';
            sender.image = Image.symbolNamed(isFlagged ? 'flag.slash' : 'flag');
        }
        return true;
    }

    // Default state
    if (sender) {
        sender.label = 'Toggle Flag';
        sender.image = Image.symbolNamed('flag.filled.and.flag.crossed');
        if (sender instanceof ToolbarItem) {
            sender.toolTip = 'Select a single task to toggle flag';
        }
    }
    return false;
};
```

### Sender Properties

**MenuItem:**
- `label` - Menu item text
- `image` - Menu item icon (Image object)

**ToolbarItem:**
- `label` - Toolbar button label
- `image` - Toolbar button icon
- `toolTip` - Tooltip text on hover

---

## Preferences API

Store and retrieve plugin settings that persist across sessions.

### Basic Usage

```javascript
// Declare at plugin scope (outside action function)
var preferences = new Preferences(); // Uses plugin ID automatically

// Or with custom identifier
var preferences = new Preferences("com.custom.identifier");

console.log(preferences.identifier); // Logs the identifier
```

### Reading Values

```javascript
// Read typed values (returns null if not set)
var stringVal = preferences.readString("myStringKey");
var numberVal = preferences.readNumber("myNumberKey");
var boolVal = preferences.readBoolean("myBoolKey");
var dateVal = preferences.readDate("myDateKey");
```

### Writing Values

```javascript
// Write values (type is preserved)
preferences.write("myStringKey", "Hello World");
preferences.write("myNumberKey", 42);
preferences.write("myBoolKey", true);
preferences.write("myDateKey", new Date());
```

### Removing Values

```javascript
preferences.remove("myKey");
```

### Complete Example: Counter with Reset

```javascript
/*{
    "type": "action",
    "targets": ["omnifocus"],
    "identifier": "com.example.counter",
    "version": "1.0",
    "label": "Counter Example",
    "image": "number.circle"
}*/
(() => {
    // Preferences at plugin scope
    var preferences = new Preferences();

    const action = new PlugIn.Action(function(selection, sender) {
        // Control key resets counter
        if (app.controlKeyDown) {
            var alert = new Alert("Reset Counter?", "This will reset the count to 0.");
            alert.addOption("Reset");
            alert.addOption("Cancel");
            alert.show(buttonIndex => {
                if (buttonIndex === 0) {
                    preferences.write("count", 0);
                }
            });
        } else {
            // Increment counter
            var count = preferences.readNumber("count") || 0;
            count += 1;
            preferences.write("count", count);

            var alert = new Alert("Counter", `Count: ${count}`);
            alert.show();
        }
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();
```

### Form State Persistence

Save form values so they persist between uses:

```javascript
// Read previous values or use defaults
var lastChoice = preferences.readNumber("formChoice") || 0;
var lastName = preferences.readString("formName") || "";

// ... show form with these values ...

// After form submission, save values
preferences.write("formChoice", form.values.choice);
preferences.write("formName", form.values.name);
```

---

## Validation Patterns

### OS Version Check (Apple Foundation Models)

```javascript
action.validate = function(selection, sender) {
    // Require macOS 26+ for Apple Foundation Models
    return (Device.current.operatingSystemVersion.atLeast(new Version("26")));
};
```

### Selection-Based Validation

```javascript
action.validate = function(selection, sender) {
    // Require at least one task selected
    return selection.tasks.length > 0;
};

// Combined: selection AND OS version
action.validate = function(selection, sender) {
    return (selection.tasks.length > 0) &&
        (Device.current.operatingSystemVersion.atLeast(new Version("26")));
};
```

### Always Enabled

```javascript
action.validate = function(selection, sender) {
    return true;
};
```

---

## Localization

Bundle plugins can use `.strings` files for multilingual support.

### Directory Structure

```
MyPlugin.omnifocusjs/
└── Resources/
    ├── myAction.js
    ├── en.lproj/
    │   ├── manifest.strings
    │   └── myAction.strings
    ├── de.lproj/
    │   ├── manifest.strings
    │   └── myAction.strings
    └── ja.lproj/
        ├── manifest.strings
        └── myAction.strings
```

### manifest.json

Must include `defaultLocale`:

```json
{
  "identifier": "com.example.plugin",
  "defaultLocale": "en",
  "actions": [{"identifier": "myAction", "image": "star"}]
}
```

### .strings File Format

Uses Apple `.strings` format:

```
"key" = "value";
```

**manifest.strings:**
```
"com.example.plugin" = "My Plugin Name";
```

**myAction.strings:**
```
"label" = "Action Label";
"shortLabel" = "Short";
"mediumLabel" = "Medium Label";
"longLabel" = "Full Long Label";
"paletteLabel" = "Palette";
```

---

## Modifier Keys

Check if modifier keys are held during action execution:

```javascript
const action = new PlugIn.Action(function(selection, sender) {
    if (app.controlKeyDown) {
        // Control key behavior (reset, alternate action)
    } else if (app.optionKeyDown) {
        // Option key behavior
    } else if (app.shiftKeyDown) {
        // Shift key behavior
    } else if (app.commandKeyDown) {
        // Command key behavior
    } else {
        // Normal behavior
    }
});
```

---

## Format Selection Guide

| Use Case | Format | Why |
|----------|--------|-----|
| Quick automation | Solitary Action | Single file, easy to share |
| Utility functions | Solitary Library | Reusable across plugins |
| Multiple related actions | Bundle | Organized, shared libraries |
| Needs localization | Bundle | Only bundles support .lproj |
| Foundation Models | Bundle (recommended) | Better organization for complex AI logic |
| User preferences | Either | Preferences API works in both |
| Large/complex plugin | Bundle | Libraries, multiple actions, localization |

---

## External Resources

- [Omni Automation Plugins](https://omni-automation.com/plugins/index.html)
- [Cross-Plugin Calling](https://omni-automation.com/plugins/calling.html)
- [Sender Parameters](https://omni-automation.com/plugins/sender.html)
- [Plugin Preferences](https://omni-automation.com/plugins/preferences.html)
- [Action Validation](https://omni-automation.com/plugins/validate.html)
- [Apple Foundation Models](https://omni-automation.com/shared/alm-plug-in-00.html)
