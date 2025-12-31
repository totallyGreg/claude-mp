# Code Generation Validation Guide

**Purpose:** Validation rules and checklist to prevent code generation errors when creating OmniFocus plugins.

**Last Updated:** 2025-12-31
**Target:** AI code generation for OmniFocus Omni Automation

---

## ⚠️ MANDATORY Pre-Generation Checklist

**BEFORE writing ANY plugin code, complete this checklist:**

### 1. Read Validation Documentation ✅
- [ ] Read this entire document (code_generation_validation.md)
- [ ] Read references/plugin_development_guide.md sections relevant to your code
- [ ] Understand official template patterns (OFBundlePlugInTemplate)

### 2. Verify Every API ✅
- [ ] List all classes to instantiate (PlugIn.Action, PlugIn.Library, Version, Alert, Form, etc.)
- [ ] Check constructor signatures in references/OmniFocus-API.md for EACH class
- [ ] Verify all properties/methods in references/api_quick_reference.md
- [ ] Confirm NOT using hallucinated APIs (Document.defaultDocument, Progress, etc.)

### 3. Verify PlugIn.Library Pattern (If Applicable) ✅
- [ ] Review official template: assets/OFBundlePlugInTemplate.omnifocusjs/Resources/
- [ ] Confirm pattern: `var lib = new PlugIn.Library(new Version("1.0"));`
- [ ] Confirm NOT using function constructor: `new PlugIn.Library(function() { ... })`
- [ ] Review existing libraries: taskMetrics.js, exportUtils.js

### 4. Verify Environment Globals ✅
- [ ] Using global variables: flattenedTasks, folders, projects, tags, inbox
- [ ] NOT using Document.defaultDocument (use globals instead)
- [ ] NOT using Node.js or browser APIs

### 5. Verify LanguageModel Schema (If Applicable) ✅
- [ ] Using LanguageModel.Schema.fromJSON() factory (NOT constructor)
- [ ] Using OmniFocus schema format (NOT JSON Schema format)
- [ ] Reviewed schema patterns in code_generation_validation.md Rule 5

### 6. Post-Generation Validation (REQUIRED) ✅
- [ ] Run `eslint_d` on all generated .js files
- [ ] Fix ALL eslint errors (zero errors required)
- [ ] Use vtsls LSP for semantic validation
- [ ] Fix ALL LSP errors and warnings
- [ ] Verify no warnings about undefined globals
- [ ] Confirm code matches validation patterns
- [ ] Test code actually runs in OmniFocus without errors

**Only proceed with code generation after ALL checkboxes completed.**

---

## Validation Philosophy

**80% Execute, 15% Compose, 5% Generate:**
- **Execute:** Use proven patterns from `../assets/examples/`
- **Compose:** Adapt examples to specific needs
- **Generate:** Only when no pattern exists (with full validation)

**Before generating ANY code:** Validate against this document.

---

## Rule 1: Verify API Existence

✅ **DO:**
```javascript
// Check api_quick_reference.md first
const tasks = flattenedTasks;  // Verified in quick reference
task.markComplete();            // Verified method exists
```

❌ **DON'T:**
```javascript
// Never assume an API exists
const progress = new Progress();  // Doesn't exist - hallucination!
doc.getAllTasks();                 // Doesn't exist - not in API
```

**Validation Steps:**
1. Check `api_quick_reference.md` for class/property/method
2. If not found, check `OmniFocus-API.md`
3. If still not found, **it doesn't exist** - don't use it

---

## Rule 2: Properties vs Methods

✅ **DO:**
```javascript
// Properties - direct access (no parentheses)
const name = task.name;
const completed = task.completed;
const dueDate = task.dueDate;

// Methods - function calls (with parentheses)
task.markComplete();
task.addTag(myTag);
project.markIncomplete();
```

❌ **DON'T:**
```javascript
// Don't call properties as functions
const name = task.name();         // ERROR! name is a property
const completed = task.completed(); // ERROR!

// Don't access methods without calling
const fn = task.markComplete;     // Gets function, doesn't execute
```

**How to Check:**
- `api_quick_reference.md` has separate tables for Properties vs Methods
- Properties table: No `()` in Example column
- Methods table: Has `()` in Example column

---

## Rule 3: JavaScript Syntax Rules

### Arrow Functions
✅ **DO:**
```javascript
// Arrow functions inherit 'this' automatically
tasks.forEach(task => {
    this.processTask(task);  // 'this' works automatically
});

// Or use regular function with .bind()
tasks.forEach(function(task) {
    this.processTask(task);
}.bind(this));
```

❌ **DON'T:**
```javascript
// NEVER use .bind(this) on arrow functions
tasks.forEach(task => {
    this.processTask(task);
}.bind(this));  // ERROR! Invalid syntax
```

### Async/Await
✅ **Supported:**
```javascript
const result = await session.respond("prompt");
const url = await saver.show();
```

### Modern JavaScript
✅ **Supported:**
- `const`, `let` (not `var`)
- Arrow functions
- Template literals
- Optional chaining `task?.name`
- Destructuring `const {name, note} = task;`

❌ **NOT Supported:**
- ES6 modules (`import`/`export`)
- Decorators
- Class private fields (`#field`)

---

## Rule 4: OmniFocus Environment Constraints

### Available Globals
✅ **Available:**
```javascript
// Database globals
flattenedTasks, flattenedProjects, folders, projects, tags, inbox, library

// Classes
Document, Task, Project, Folder, Tag
PlugIn, Version, Alert, Form
FileSaver, Pasteboard, Calendar
LanguageModel
```

❌ **NOT Available:**
```javascript
// Node.js modules
require(), module.exports, process, __dirname

// Browser APIs
window, document.querySelector(), localStorage, fetch()

// Non-existent OmniFocus APIs
Document.defaultDocument  // Use globals instead
Progress                  // Doesn't exist
FileType.fromExtension()  // Doesn't exist
```

### Plugin Structure
✅ **DO:**
```javascript
// PlugIn.Action for actions
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // Action code here
    });

    action.validate = function(selection, sender) {
        return true;
    };

    return action;
})();

// PlugIn.Library for shared code
(() => {
    var lib = new PlugIn.Library(new Version("1.0"));

    lib.myFunction = function() {
        // Library code
    };

    return lib;
})();
```

---

## Rule 5: LanguageModel.Schema Validation

### Schema Format
✅ **DO - Use OmniFocus Schema Format:**
```javascript
const schema = LanguageModel.Schema.fromJSON({
    name: "my-schema",
    properties: [
        {name: "field1"},
        {name: "field2", isOptional: true},
        {
            name: "tags",
            schema: {arrayOf: {constant: "tag"}}
        },
        {
            name: "priority",
            schema: {
                anyOf: [
                    {constant: "high"},
                    {constant: "low"}
                ]
            }
        }
    ]
});
```

❌ **DON'T - Use JSON Schema:**
```javascript
// This is JSON Schema - OmniFocus doesn't use it!
new LanguageModel.Schema({  // NOT a constructor!
    type: "object",
    properties: {
        field1: {type: "string"},
        tags: {type: "array", items: {type: "string"}}
    }
});
```

### Schema Patterns
| Pattern | OmniFocus Format | ❌ JSON Schema |
|---------|------------------|----------------|
| Object | `properties: [{name: "f"}]` | `type: "object"` |
| Array of strings | `{arrayOf: {constant: "s"}}` | `type: "array", items: {type: "string"}` |
| Array of objects | `{arrayOf: {properties: [...]}}` | `type: "array", items: {type: "object"}` |
| Enum | `{anyOf: [{constant: "a"}]}` | `enum: ["a", "b"]` |
| Optional | `{name: "f", isOptional: true}` | `required: ["f"]` |

---

## Rule 6: Defensive Programming

### Handle Optional Fields
✅ **DO:**
```javascript
// AI responses may omit optional fields
if (analysis.insights && analysis.insights.length > 0) {
    analysis.insights.forEach(i => console.log(i));
}

// Check nested properties
if (task.containingProject && task.containingProject.name) {
    console.log(task.containingProject.name);
}
```

❌ **DON'T:**
```javascript
// Assume fields always exist
analysis.insights.forEach(i => console.log(i));  // Crashes if undefined
const projectName = task.containingProject.name;  // Crashes if null
```

### Handle User Cancellation
✅ **DO:**
```javascript
const formResult = await form.show("Title", "OK");
if (!formResult) return;  // User cancelled

const url = await saver.show();
if (!url) return;  // User cancelled
```

---

## Common Error Patterns

### Error: "Can't find variable: X"
**Cause:** Using undefined global or typo
```javascript
// ❌ Wrong
FileTypes.Text        // FileTypes not a global
Document.defaultDocument  // Use flattenedTasks global instead

// ✅ Correct
flattenedTasks       // Database global
```

### Error: "X is not a function"
**Cause:** Calling a property as a function
```javascript
// ❌ Wrong
task.name()          // name is a property

// ✅ Correct
task.name            // Access property directly
task.markComplete()  // Call method with ()
```

### Error: "X is not a constructor"
**Cause:** Using `new` on non-constructor
```javascript
// ❌ Wrong
new LanguageModel.Schema({...})  // Not a constructor!

// ✅ Correct
LanguageModel.Schema.fromJSON({...})  // Factory method
```

### Error: "Exceeded model context window"
**Cause:** Prompt too long for Apple Foundation Models
```javascript
// ❌ Wrong
const prompt = JSON.stringify(allTasks, null, 2);  // Too verbose

// ✅ Correct
const summary = tasks.slice(0, 10).map(t => t.name).join('\n');  // Concise
```

---

## Pre-Generation Validation Checklist

Before suggesting any OmniFocus plugin code:

### API Validation
- [ ] All classes checked in `api_quick_reference.md`
- [ ] All methods checked in `api_quick_reference.md`
- [ ] All properties checked in `api_quick_reference.md`
- [ ] No hallucinated APIs (Progress, FileType.fromExtension, etc.)
- [ ] Global variables used correctly (flattenedTasks not Document.defaultDocument)

### Syntax Validation
- [ ] Properties accessed without `()`
- [ ] Methods called with `()`
- [ ] No `.bind(this)` on arrow functions
- [ ] Valid JavaScript (no syntax errors)
- [ ] Compatible with OmniFocus environment (no Node.js/Browser APIs)

### LanguageModel Validation (if using AI)
- [ ] Using `LanguageModel.Schema.fromJSON()` (not `new`)
- [ ] Schema uses OmniFocus format (not JSON Schema)
- [ ] Schema structure correct (properties array, arrayOf, anyOf)

### Safety Validation
- [ ] Defensive checks for optional fields
- [ ] User cancellation handled (form, file dialogs)
- [ ] Error handling in try/catch
- [ ] Prompt size reasonable (< 1000 tokens for AFM)

---

## Testing Procedure

### 1. Syntax Validation
```bash
# Use ESLint with OmniFocus globals
eslint_d plugin.js
```

### 2. OmniFocus Automation Console
1. Open OmniFocus
2. Automation → Console
3. Paste code
4. Run and check for errors

### 3. Plugin Installation
1. Copy `.omnifocusjs` to Plug-Ins folder
2. Restart OmniFocus
3. Check Automation → Configure Plug-Ins
4. Test all actions

---

## Code Generation Workflow

```
1. User Request
   ↓
2. Check Examples (../assets/examples/)
   - Found pattern? → Adapt and use ✅
   - No pattern? → Continue ↓
   ↓
3. Verify APIs (api_quick_reference.md)
   - All APIs exist? → Continue ↓
   - Missing API? → STOP - can't implement ❌
   ↓
4. Generate Code
   - Use correct syntax
   - Follow validation rules
   ↓
5. Validate (this document)
   - All checks pass? → Continue ↓
   - Failed checks? → Fix and re-validate ↓
   ↓
6. Suggest to User ✅
```

---

## Success Metrics

**Before v3.2.0:**
- Plugin generation success rate: 0%
- API hallucination: Common
- Syntax errors: Frequent

**After v3.2.0 (with this guide):**
- Plugin generation success rate: >90%
- API hallucination: Eliminated (validation layer)
- Syntax errors: Rare (checked before suggesting)

---

## See Also

- **Quick API Lookup:** `api_quick_reference.md`
- **Complete API:** `OmniFocus-API.md`
- **Working Examples:** `../assets/examples/code-generation-patterns/`
- **Plugin Guide:** `plugin_development_guide.md`

---

**Generated:** 2025-12-31
**Version:** 3.2.0
**Purpose:** Prevent code generation failures through systematic validation
