# AITaskAnalyzer Troubleshooting Guide

## Fixed Issues (v3.0)

### Issue 1: Syntax Error - `.bind(this)` on Arrow Functions ✅ FIXED

**Error Message:**
```
SyntaxError: Unexpected token '.'. Expected ')' to end an argument list.
/Users/*/Plug-Ins/AITaskAnalyzer.omnifocusjs/Resources/exportUtils.js:139:0
```

**Root Cause:**
Arrow functions were using `.bind(this)` which is invalid JavaScript syntax. Arrow functions inherit `this` lexically and cannot be bound.

**Fix:**
Removed `.bind(this)` from all arrow functions in exportUtils.js (3 locations: lines 139, 294, 306).

**Validation:**
```bash
eslint_d assets/AITaskAnalyzer.omnifocusjs/Resources/exportUtils.js
```

---

### Issue 2: Runtime Error - `doc.flattenedTasks` is undefined ✅ FIXED

**Error Message:**
```
Failed to analyze tasks: undefined is not an object (evaluating 'doc.flattenedTasks')
```

**Root Cause:**
Code was using `Document.defaultDocument.flattenedTasks`, but `flattenedTasks` is not a property of the Document class. It's a property of the Database class, exposed as a **global variable** in OmniFocus Omni Automation.

**Incorrect Pattern (WRONG):**
```javascript
const doc = Document.defaultDocument;
const tasks = doc.flattenedTasks;  // ❌ Error: Document doesn't have flattenedTasks
```

**Correct Pattern (RIGHT):**
```javascript
const tasks = flattenedTasks;  // ✅ Global variable from Database
```

**Files Fixed:**
- `taskMetrics.js` - Changed all 3 functions (getTodayTasks, getOverdueTasks, getFlaggedTasks)
- `analyzeProjects.js` - Changed getAllFolders() and "All Projects" handling

**OmniFocus Global Variables:**

OmniFocus exposes these Database properties as global variables:

- `flattenedTasks` - All tasks in the database
- `flattenedProjects` - All projects in the database
- `flattenedFolders` - All folders in the database
- `flattenedTags` - All tags in the database
- `folders` - Top-level folders
- `projects` - Top-level projects
- `tags` - Top-level tags
- `inbox` - Inbox tasks
- `library` - Library sections

**Reference:**
- OmniFocus API: Database class properties
- Official Template: `OFBundlePlugInTemplate.omnifocusjs/Resources/addFolderForEachMonth.js` (uses `folders` global)

---

### Issue 3: LanguageModel.Schema Constructor Error ✅ FIXED

**Error Message:**
```
Failed to analyze tasks: CallbackObject is not a constructor
(evaluating 'new LanguageModel.Schema({...})')
```

**Root Cause:**
`LanguageModel.Schema` is **not a constructor** - it's a factory class. The OmniFocus API uses a custom schema format, not JSON Schema.

**Incorrect Pattern (WRONG):**
```javascript
// ❌ WRONG - LanguageModel.Schema is not a constructor
const schema = new LanguageModel.Schema({
    type: "object",
    properties: {
        field: { type: "string" }
    }
});
```

**Correct Pattern (RIGHT):**
```javascript
// ✅ CORRECT - Use LanguageModel.Schema.fromJSON()
const schema = LanguageModel.Schema.fromJSON({
    name: "my-schema",
    properties: [
        {name: "field"}
    ]
});
```

**OmniFocus Schema Format:**

The OmniFocus schema format is different from JSON Schema:

**Objects with properties:**
```javascript
LanguageModel.Schema.fromJSON({
    name: "person-schema",
    properties: [
        {name: "firstName"},
        {name: "lastName"},
        {name: "age", isOptional: true}
    ]
})
```

**Arrays of strings:**
```javascript
{
    name: "tags",
    schema: {arrayOf: {constant: "tag"}}
}
```

**Arrays of objects:**
```javascript
{
    name: "items",
    schema: {
        arrayOf: {
            name: "item-schema",
            properties: [
                {name: "title"},
                {name: "description"}
            ]
        }
    }
}
```

**Enums:**
```javascript
{
    name: "priority",
    schema: {
        anyOf: [
            {constant: "high"},
            {constant: "medium"},
            {constant: "low"}
        ]
    }
}
```

**Files Fixed:**
- `analyzeTasksWithAI.js` - Converted complex nested schema
- `analyzeSelectedTasks.js` - Converted task analysis schema with enums
- `analyzeProjects.js` - Converted multi-level nested schema

**Reference:**
- OmniFocus API: `LanguageModel.Schema.fromJSON()` documentation
- Official examples in OmniFocus-API.md lines 1437-1483

---

## Installation & Testing

### Installation Steps

1. **Remove Old Version:**
   - Open OmniFocus
   - Automation → Configure Plug-Ins
   - Find "AITaskAnalyzer" and click the "-" button
   - Confirm deletion

2. **Install Fixed Version:**
   ```bash
   # Copy plugin to OmniFocus Plug-Ins folder
   cp -r assets/AITaskAnalyzer.omnifocusjs ~/Library/Mobile\ Documents/iCloud~com~omnigroup~OmniFocus/Documents/Plug-Ins/
   ```

3. **Verify Installation:**
   - Restart OmniFocus (Cmd+Q, then reopen)
   - Automation → Configure Plug-Ins
   - Verify "AI Task Analyzer" appears in the list
   - Check that all 3 actions are listed:
     - Analyze Selected Tasks
     - Analyze Tasks with AI
     - Analyze Projects

### Testing Actions

#### Test 1: Analyze Selected Tasks
1. Select 1-5 tasks in OmniFocus
2. Automation → AI Task Analyzer → Analyze Selected Tasks
3. Verify: AI analysis appears with clarity scores and recommendations
4. Expected: No errors, structured analysis output

#### Test 2: Analyze Tasks with AI
1. Automation → AI Task Analyzer → Analyze Tasks with AI
2. Verify: Analysis of today's and overdue tasks
3. Expected: Priority recommendations, workload analysis, insights
4. If no tasks: "No tasks found for today or overdue" message

#### Test 3: Analyze Projects
1. Automation → AI Task Analyzer → Analyze Projects
2. Select a folder to analyze
3. Verify: Project analysis with insights and recommendations
4. Expected: Structured analysis of projects in selected folder

---

## Development & Validation

### ESLint Validation

The plugin uses ESLint v9 with flat config for validation.

**Validate All Files:**
```bash
cd /path/to/omnifocus-manager
eslint_d assets/AITaskAnalyzer.omnifocusjs/Resources/*.js
```

**ESLint Configuration:**
- File: `eslint.config.js`
- Includes OmniFocus global variables (PlugIn, Alert, Form, etc.)
- Includes Database globals (flattenedTasks, folders, inbox, etc.)
- No output = all files valid

### Plugin Structure Validation

**Validate Plugin Structure:**
```bash
cd assets/AITaskAnalyzer.omnifocusjs
bash validate-structure.sh
```

**Expected Output:**
```
✅ manifest.json exists
✅ Resources/ directory exists
✅ All action files exist
✅ All library files exist
✅ All actions referenced in manifest
✅ Version matches across all files
```

---

## Requirements

### System Requirements
- OmniFocus 4.8 or later
- macOS 15.2+ or iOS 18.2+ or later
- Apple Silicon (M1/M2/M3) or iPhone 15 Pro+ for on-device AI

### Dependencies
- Apple Foundation Models (LanguageModel API)
- On-device AI processing (no network required)

### Limitations
- Maximum 5 tasks for "Analyze Selected Tasks" (performance)
- AI analysis can take 5-30 seconds depending on task complexity
- Requires local AI processing capability (not available on Intel Macs)

---

## Common Errors

### Error: "Apple Foundation Models not available"

**Symptoms:**
```
Error: Apple Foundation Models not available.
Requires OmniFocus 4.8+ and macOS/iOS 26+.
```

**Solutions:**
1. Verify OmniFocus version: 4.8 or later required
2. Verify macOS version: 15.2+ required
3. Verify hardware: Apple Silicon or iPhone 15 Pro+ required
4. Check: Settings → Apple Intelligence → On-Device AI enabled

### Error: Plugin doesn't appear in Automation menu

**Symptoms:**
- AITaskAnalyzer not listed in Automation → Configure Plug-Ins
- Actions don't appear in Automation menu

**Solutions:**
1. Check installation location:
   ```bash
   ls -la ~/Library/Mobile\ Documents/iCloud~com~omnigroup~OmniFocus/Documents/Plug-Ins/
   ```
2. Verify folder name ends with `.omnifocusjs`
3. Check manifest.json syntax (valid JSON)
4. Restart OmniFocus completely (Cmd+Q, reopen)
5. Check Console.app for plugin loading errors

### Error: "Please select at least one task"

**Symptoms:**
```
Error: Please select at least one task to analyze.
```

**Solution:**
This is expected behavior for "Analyze Selected Tasks" action. Select 1-5 tasks first.

### Error: "Please select 5 or fewer tasks"

**Symptoms:**
```
Error: Please select 5 or fewer tasks. AI analysis can take time for multiple tasks.
```

**Solution:**
This is a performance limitation. Select 5 or fewer tasks. Use "Analyze Tasks with AI" action for bulk analysis of today's/overdue tasks.

---

## API Reference Corrections

### WRONG: Using Document.defaultDocument

```javascript
// ❌ INCORRECT
const doc = Document.defaultDocument;
const tasks = doc.flattenedTasks;
const folders = doc.folders;
```

### RIGHT: Using Global Variables

```javascript
// ✅ CORRECT
const tasks = flattenedTasks;
const allFolders = folders;
const inboxTasks = inbox;
```

### Available OmniFocus Globals

**Database Collections:**
- `flattenedTasks` - TaskArray (all tasks)
- `flattenedProjects` - ProjectArray (all projects)
- `flattenedFolders` - FolderArray (all folders)
- `flattenedTags` - TagArray (all tags)

**Top-Level Collections:**
- `folders` - FolderArray (root folders only)
- `projects` - ProjectArray (root projects only)
- `tags` - Tags (root tags only)
- `inbox` - Inbox (inbox tasks)
- `library` - Library (folders & projects)

**Classes:**
- `Document`, `PlugIn`, `Version`, `Alert`, `Form`
- `Task`, `Project`, `Folder`, `Tag`
- `FileSaver`, `FileWrapper`, `FileType`
- `Pasteboard`, `Calendar`, `Formatter`
- `LanguageModel` (Apple Foundation Models)

---

## Debugging

### Enable Console Logging

Add logging to plugin actions:

```javascript
console.log("Debug info:", variable);
console.error("Error occurred:", error);
```

View logs:
1. Open Console.app
2. Filter: Process = "OmniFocus"
3. Run plugin action
4. Check console output

### Check Plugin Loading

Console.app filter:
```
process:OmniFocus category:plugins
```

Look for:
- Plugin load events
- Syntax errors
- Missing files
- Manifest validation errors

### Test in Automation Console

OmniFocus → Automation → Console

Test code directly:
```javascript
// Test flattenedTasks global
console.log("Task count:", flattenedTasks.length);

// Test library global
console.log("Library functions:", this.plugIn.library("taskMetrics"));
```

---

## Version History

### v3.0.0 (2025-12-31)
**Major Fixes - Plugin Now Works:**
- ✅ Fixed: `.bind(this)` on arrow functions (exportUtils.js lines 139, 294, 306)
- ✅ Fixed: `Document.defaultDocument` → Use global variables (taskMetrics.js, analyzeProjects.js)
- ✅ Fixed: `new LanguageModel.Schema()` → `LanguageModel.Schema.fromJSON()` (all 3 AI actions)
- ✅ Converted: All JSON Schema formats to OmniFocus custom schema format
- ✅ Added: ESLint validation with all OmniFocus globals (classes and database properties)
- ✅ Added: Comprehensive TROUBLESHOOTING.md with all fixes documented

**What Changed:**
- All syntax errors resolved
- All runtime API errors resolved
- All Apple Foundation Model schema errors resolved
- Plugin loads and runs successfully

### v2.x.x (Previous)
- ⚠️ Known issues: Multiple critical errors
- ⚠️ Syntax errors: `.bind(this)` on arrow functions
- ⚠️ Runtime errors: `Document.defaultDocument.flattenedTasks` undefined
- ⚠️ Schema errors: `LanguageModel.Schema` not a constructor
- ⚠️ Plugin fails to load or run any actions

---

## Getting Help

### Plugin Issues
1. Check this TROUBLESHOOTING.md for known issues
2. Validate plugin structure: `bash validate-structure.sh`
3. Check ESLint: `eslint_d Resources/*.js`
4. Review Console.app logs

### OmniFocus API Questions
- Official API: https://omni-automation.com/omnifocus/
- OmniFocus Forums: https://discourse.omnigroup.com/c/omnifocus

### Development Questions
- omnifocus-manager skill: See SKILL.md and references/
- ESLint config: See eslint.config.js for globals

---

**Last Updated:** 2025-01-XX
**Plugin Version:** 3.0.0
**OmniFocus Version Required:** 4.8+
