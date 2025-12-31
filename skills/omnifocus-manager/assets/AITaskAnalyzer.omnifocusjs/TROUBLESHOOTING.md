# AITaskAnalyzer Plugin Troubleshooting Guide

## Quick Diagnosis

If the plugin isn't working, follow these steps in order:

### Step 1: Verify Installation

```bash
# Check if plugin bundle exists and has correct structure
ls -la ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/

# Should show: com.totallytools.omnifocus.ai-task-analyzer.omnifocusjs
```

### Step 2: Complete Uninstall and Reinstall

**CRITICAL:** Manifest changes require complete uninstall/reinstall.

1. **Uninstall old version:**
   ```bash
   # Remove from OmniFocus Plug-Ins directory
   rm -rf ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/*ai-task-analyzer*

   # Also check and remove from old locations if they exist
   rm -rf ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/*Analyze*Tasks*
   ```

2. **Quit OmniFocus completely:**
   ```bash
   killall OmniFocus
   ```

3. **Reinstall fresh copy:**
   ```bash
   open /Users/totally/Documents/Projects/claude-mp/skills/omnifocus-manager/assets/AITaskAnalyzer.omnifocusjs
   ```

4. **In the installation dialog:**
   - Choose "Install Plug-In"
   - Verify the identifier shows: `com.totallytools.omnifocus.ai-task-analyzer`
   - Choose installation location (recommend "This Mac" or "All Macs")

5. **Restart OmniFocus:**
   - Quit completely (Cmd+Q)
   - Relaunch

### Step 3: Verify Plugin Loaded

1. **Check Automation Console:**
   - Open OmniFocus
   - Press `Cmd+Opt+Ctrl+C` to open Automation Console
   - Run this command:
     ```javascript
     PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer")
     ```
   - Should return: `[PlugIn: AI Analyzer]` (not null)

2. **List all plugins:**
   ```javascript
   PlugIn.all.map(p => p.identifier)
   ```
   - Should include: `"com.totallytools.omnifocus.ai-task-analyzer"`

3. **Check actions:**
   ```javascript
   const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
   plugin.actions.map(a => a.name)
   ```
   - Should return: `["Analyze My Tasks", "Analyze Projects", "Analyze Selected"]`

### Step 4: Test Action Execution

1. **Check if action is visible in menu:**
   - Automation menu should show "AI Analyzer" submenu
   - Should contain 3 actions

2. **Run simplest test:**
   - In Automation Console, run:
     ```javascript
     const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
     const action = plugin.actions[0]; // First action
     action.validate(window.document.selection, null)
     ```
   - Should return: `true`

3. **Test action directly:**
   ```javascript
   const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
   const action = plugin.actions[0];
   action.perform(window.document.selection, null)
   ```
   - Should execute the action

### Step 5: Check for Errors

1. **Enable error logging:**
   - In Automation Console, check for any error messages
   - Errors will appear in red

2. **Common errors and fixes:**

   | Error | Cause | Fix |
   |-------|-------|-----|
   | `null` when finding plugin | Plugin not installed or identifier wrong | Complete uninstall/reinstall |
   | `PlugIn.find(...) is null` | Identifier mismatch | Verify manifest.json has `com.totallytools.omnifocus.ai-task-analyzer` |
   | `undefined is not an object` | API usage error | Check if using properties (no parens) correctly |
   | `LanguageModel is not defined` | macOS version too old | Requires macOS 15.2+ |
   | Action not in menu | manifest.json/file mismatch | Verify action identifiers match filenames |

## Common Issues

### Issue 1: Plugin Shows Old Identifier

**Symptoms:**
- PlugIn.find() with new identifier returns null
- Old identifier still works

**Cause:**
- Cached old version not fully removed

**Fix:**
1. Completely quit OmniFocus
2. Remove ALL versions from Plug-Ins directory:
   ```bash
   ls ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/
   # Remove anything related to AI analyzer
   rm -rf ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/*ai*
   rm -rf ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/Plug-Ins/*Analyze*
   ```
3. Clear preferences (optional, nuclear option):
   ```bash
   defaults delete com.omnigroup.OmniFocus4 PlugInRegistry
   ```
4. Restart Mac (ensures all caches cleared)
5. Reinstall fresh

### Issue 2: Actions Don't Appear in Menu

**Symptoms:**
- Plugin found via PlugIn.find()
- Actions array is not empty
- But actions don't show in Automation menu

**Cause:**
- Action identifiers in manifest.json don't match JavaScript filenames

**Verification:**
```bash
# List action files
ls -1 Resources/*.js

# Should show:
# analyzeTasksWithAI.js
# analyzeProjects.js
# analyzeSelectedTasks.js

# Check manifest identifiers match
grep "identifier" manifest.json
```

**Fix:**
- Ensure exact filename matches (case-sensitive)
- No `.js` extension in manifest identifiers
- Each action file must return a PlugIn.Action instance

### Issue 3: Apple Intelligence Not Available

**Symptoms:**
- Plugin loads
- Action runs
- But fails with "LanguageModel is not defined" or similar

**Requirements Check:**
```javascript
// Run in Automation Console
Device.macOSVersion  // Should be >= 15.2
Device.iOSVersion    // Should be >= 18.2 (on iOS)

// Check if LanguageModel is available
typeof LanguageModel !== 'undefined'  // Should be true
```

**Fix:**
- Update to macOS 15.2+ or iOS 18.2+
- Ensure Apple Silicon or iPhone 15 Pro+
- Enable Apple Intelligence in System Settings

### Issue 4: File Permission Errors

**Symptoms:**
- Plugin won't install
- "Permission denied" errors

**Fix:**
```bash
# Ensure plugin bundle has correct permissions
chmod -R 755 /Users/totally/Documents/Projects/claude-mp/skills/omnifocus-manager/assets/AITaskAnalyzer.omnifocusjs

# Verify ownership
ls -la /Users/totally/Documents/Projects/claude-mp/skills/omnifocus-manager/assets/AITaskAnalyzer.omnifocusjs
```

## Validation Checklist

Before reporting an issue, verify:

- [ ] manifest.json identifier is `com.totallytools.omnifocus.ai-task-analyzer`
- [ ] All action files exist in Resources/ directory
- [ ] Action filenames match manifest identifiers exactly
- [ ] Plugin completely uninstalled before reinstalling
- [ ] OmniFocus fully quit and relaunched
- [ ] PlugIn.find() returns the plugin (not null)
- [ ] macOS 15.2+ or iOS 18.2+ for AI features
- [ ] No error messages in Automation Console

## Debug Commands

### List All Installed Plugins

```javascript
PlugIn.all.forEach(p => {
    console.log(`${p.displayName} (${p.identifier}) v${p.versionString}`);
});
```

### Inspect Specific Plugin

```javascript
const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
console.log("Identifier:", plugin.identifier);
console.log("Version:", plugin.versionString);
console.log("Author:", plugin.author);
console.log("Actions:", plugin.actions.map(a => a.name));
console.log("Libraries:", plugin.libraries.map(l => l.name));
```

### Test Action Validation

```javascript
const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
const selection = window.document.selection;

plugin.actions.forEach(action => {
    const isValid = action.validate(selection, null);
    console.log(`${action.name}: ${isValid ? "✅ Valid" : "❌ Invalid"}`);
});
```

### Check Document API Access

```javascript
const doc = Document.defaultDocument;
console.log("Tasks:", typeof doc.flattenedTasks);  // Should be "object" (array)
console.log("Task count:", doc.flattenedTasks.length);
```

## Getting Help

If still not working after following this guide:

1. **Collect diagnostic info:**
   ```javascript
   // Run in Automation Console and save output
   const plugin = PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer");
   console.log("Plugin found:", plugin !== null);
   console.log("macOS version:", Device.macOSVersion);
   console.log("LanguageModel available:", typeof LanguageModel !== 'undefined');
   console.log("Actions count:", plugin ? plugin.actions.length : "N/A");
   ```

2. **Check Console.app:**
   - Open Console.app
   - Filter for "OmniFocus"
   - Look for errors during plugin loading

3. **Report issue with:**
   - Exact error message
   - Diagnostic output from above
   - macOS version
   - OmniFocus version
   - Steps to reproduce

## Related Documentation

- [Plugin Structure](../../references/omnifocus_plugin_structure.md)
- [Plugin API Reference](../../references/plugin_api.md)
- [Plugin Installation Guide](../../references/plugin_installation.md)
