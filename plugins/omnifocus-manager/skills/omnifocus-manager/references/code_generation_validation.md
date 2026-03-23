# Code Generation Validation Guide

**Purpose:** Validation rules and checklist to prevent code generation errors when creating OmniFocus plugins.

**Last Updated:** 2025-12-31
**Target:** AI code generation for OmniFocus Omni Automation

> 🚨 **STOP: READ THIS BEFORE GENERATING ANY CODE**
>
> **Failure to follow this guide results in broken plugins that won't run in OmniFocus.**
>
> This document is MANDATORY reading before generating plugin code. The checklist below is not optional.
> Every checkbox must be completed BEFORE writing code. Skipping steps leads to:
> - Runtime errors ("undefined is not an object")
> - Hallucinated APIs that don't exist
> - Constructor errors and type mismatches
> - Plugins that fail to load
>
> **After reading this document:**
> 1. Complete the MANDATORY Pre-Generation Checklist below
> 2. Verify EVERY API in `api_quick_reference.md`
> 3. Run `eslint_d` and LSP validation (zero tolerance for errors)
> 4. Run `bash ../scripts/validate-plugin.sh <plugin-path>`
>
> **Do NOT proceed without completing the checklist.**

---

## ⚠️ MANDATORY Pre-Generation Checklist

**BEFORE writing ANY plugin code, complete this checklist:**

### 1. Read Validation Documentation ✅
- [ ] Read this entire document (code_generation_validation.md)
- [ ] Read references/plugin_development_guide.md sections relevant to your code
- [ ] Understand official template patterns (OFBundlePlugInTemplate)

### 2. Verify Every API ✅
- [ ] List all classes to instantiate (PlugIn.Action, PlugIn.Library, Version, Alert, Form, etc.)
- [ ] Check constructor signatures in references/omnifocus_api.md for EACH class
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

### 4a. Verify `this` Binding in Action IIFEs ✅
- [ ] `this.plugIn.library()` is only called inside the **action handler body** — the async function passed to `new PlugIn.Action(async function(selection, sender) { ... })`
- [ ] Standalone helper functions defined outside the action handler **cannot** use `this` — `this` is `undefined` in that context
- [ ] If a helper function needs a library reference, it must receive it as a **parameter** from the action body

```javascript
// ❌ WRONG — this is undefined inside standalone function
function aggregateInsights(results) {
    const lib = this.plugIn.library("folderParser"); // TypeError at runtime
}

// ✅ CORRECT — pass library reference as parameter
function aggregateInsights(results, folderParser) {
    const metrics = folderParser.aggregateMetrics(results);
}

// In action body (where this is correctly bound):
const folderParser = this.plugIn.library("folderParser");
const insights = aggregateInsights(results, folderParser);
```

Validated 2026-03-23: `analyzeHierarchy.js` `aggregateInsights()` crashed with TypeError until the `folderParser` parameter pattern was applied.

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
2. If not found, check `omnifocus_api.md`
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
```

> **Note on `FileType.fromExtension()`:** Available in Omni Automation plugin context (used in Attache `exportUtils.js`), but NOT available in JXA/osascript context. See `references/library_ecosystem.md` for Attache library reference.

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

- **API Reference:** `api_reference.md` - Complete API with quick lookup tables
- **Full API Spec:** `omnifocus_api.md` - Raw API specification
- **Working Examples:** `../assets/examples/` - Code patterns and templates
- **Omni Automation Guide:** `omni_automation_guide.md` - Plugin development

---

## Build-Time Validation Strategy

This section describes the automated validation pipeline used by the TypeScript generator (`scripts/generate_plugin.ts`). Understanding this strategy helps ensure plugins are valid by construction.

### Build-Time vs Run-Time Distinction

A critical concept is the separation of environments:

| Environment | Description | Available APIs |
|-------------|-------------|----------------|
| **Build-Time** | Where code is *generated* (Node.js) | TypeScript Compiler, ESLint, full Node.js |
| **Run-Time** | Where plugins *execute* (OmniFocus) | JavaScriptCore, Omni Automation APIs only |

**Strategy:** Leverage the powerful build-time environment to guarantee the code's correctness for the constrained run-time environment.

### Multi-Layered Validation Pipeline

The generator implements a two-layer validation strategy:

#### Layer 1: Static Validation (Pre-Runtime)

This layer catches >95% of errors before code is ever run.

```
1. Generator composes full plugin code in TypeScript
         ↓
2. TypeScript Compiler API type-checks against omnifocus.d.ts
         ↓
3. Type-checking fails? → STOP, report errors
         ↓
4. Type-checking passes → Emit JavaScript
         ↓
5. ESLint validates emitted JavaScript
         ↓
6. Lint errors? → STOP, report errors
         ↓
7. All passes → Plugin ready for installation
```

#### Layer 2: Runtime Testing (Essential)

Static analysis cannot catch all runtime-specific logic errors.

1. Install the generated plugin in OmniFocus
2. Test in Automation Console (`⌘⌥⇧C`)
3. Trigger actions from Automation menu
4. Verify end-to-end workflow

### TypeScript Compiler API Integration

The generator uses the TypeScript Compiler API to validate code:

```javascript
// Simplified generator validation logic
const program = ts.createProgram([generatedCode], compilerOptions);
const diagnostics = [
    ...program.getSyntacticDiagnostics(),
    ...program.getSemanticDiagnostics()
];

if (diagnostics.length > 0) {
    // Zero-tolerance: refuse to emit if any errors
    reportErrors(diagnostics);
    process.exit(1);
}
```

**What TypeScript catches:**
- Undefined APIs (hallucinated APIs like `Document.defaultDocument`, `Progress`)
- Type mismatches (passing function when Version expected)
- Incorrect constructor arguments
- Property/method confusion (calling property as method)
- Syntax errors

### ESLint Integration

After TypeScript validation passes, ESLint enforces style and best practices:

```bash
# The generator runs this automatically
eslint_d assets/GeneratedPlugin.omnifocusjs/Resources/*.js
```

**Key configuration:** The `eslint.config.js` defines OmniFocus globals (`flattenedTasks`, `Alert`, `PlugIn`, etc.) to prevent false `no-undef` errors.

### Why This Matters

| Without Validation | With Validation |
|--------------------|-----------------|
| Runtime crashes ("undefined is not an object") | Caught at build time |
| Hallucinated APIs | Type-checked against .d.ts |
| Property/method confusion | Semantic analysis catches |
| Plugin won't load | Validated before deployment |

### Using the Generator

```bash
# Generate with automatic validation
node scripts/generate_plugin.js --format solitary --name "My Plugin"

# What happens automatically:
# 1. Loads TypeScript template
# 2. Substitutes variables
# 3. Validates with TypeScript Compiler API
# 4. Runs ESLint
# 5. Only emits if ALL checks pass
```

**Zero-Tolerance Policy:** The generator refuses to emit JavaScript if ANY validation error is found.

---

---

## Attache Plugin @ts-check Gate (v9.4.0+)

All Attache plugin JS libraries (`Resources/*.js`) are now type-checked as part of the build pipeline using a dedicated TypeScript configuration. This catches type errors in the plugin code itself — not just the generated ofo-core output.

### Configuration Files

**`scripts/src/tsconfig.attache.json`** — runs `tsc --noEmit` against all Attache Resources:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "checkJs": true, "allowJs": true, "noEmit": true,
    "strict": false, "lib": ["ES2020"], "skipLibCheck": true
  },
  "files": [
    "../../typescript/omnifocus.d.ts",
    "../../typescript/omnifocus-extensions.d.ts",
    "ofo-contract.d.ts",
    "omni-attache-ambient.d.ts"
  ],
  "include": ["../../assets/Attache.omnifocusjs/Resources/*.js"]
}
```

**`scripts/src/omni-attache-ambient.d.ts`** — runtime patches not covered by the 2021 OmniFocus stubs:
- Optional args for `Console`, `Alert`, `Form.show/addField`
- `PlugIn.Library` index signature (`[key: string]: any`)
- `Project/Task.Status.name: string`
- Missing properties: `Task.dropped`, `Project.added`, `Project.lastReviewedDate`, `Folder.flattenedTasks`, `Device.name`
- `FileSaver.show()` with no-arg overload, `FileWrapper.fromString/write`
- `FileType.fromExtension(ext): TypeIdentifier`
- `folderNamed(name)` global function

> **`skipLibCheck: true`** is required to avoid conflicts between `ofo-core-ambient.d.ts` and `omnifocus-extensions.d.ts` (both declare a `tags` global with different types).

### Running the Gate

```bash
cd plugins/omnifocus-manager/skills/omnifocus-manager/scripts/src
npx tsc -p tsconfig.attache.json
# Must exit 0 before committing Attache JS changes
```

### Date Arithmetic Pattern

TypeScript's no-Date-arithmetic rule requires unary `+` when subtracting dates:

```javascript
// ❌ TypeScript error: Operator '-' cannot be applied to type 'Date'
const age = new Date() - task.added;

// ✅ Correct: coerce to number first
const age = +new Date() - +task.added;
```

### Form.Field.Option 6th Arg

The `nullOptionTitle` (6th constructor arg) is optional at runtime but required in the type stubs. Use `// @ts-ignore` when omitting it:

```javascript
// @ts-ignore — 6th arg (nullOptionTitle) is optional at runtime
const depthField = new Form.Field.Option("depth", "Label", values, labels, default);
```

---

## Build Pipeline: ofo-core (v9.4.0+)

### IIFE Footer Assertion (`build-plugin.sh`)

After compiling `ofo-core.ts → ofoCore.js`, the build script asserts every exported function exists at the top level of the IIFE:

```bash
for fn in getTask completeTask createTask updateTask searchTasks listTasks \
          getPerspective configurePerspective tagTask getTags createBatch \
          getPerspectiveRules dumpDatabase getStats assessClarity stalledProjects dispatch; do
  grep -q "^function ${fn}(" "${BUILT_JS}" || \
    { echo "ERROR: '${fn}' missing from IIFE exports"; exit 1; }
done
```

When adding a new exported function to `ofo-core.ts`, also add it to:
1. The `lib.<fn> = <fn>;` block in the IIFE footer (`build-plugin.sh`)
2. The assertion loop above
3. The `dispatch` switch in `ofo-core.ts`

### Shape Consistency Verification (`diff-task-shapes.js`)

Verifies that `getTask`, `searchTasks`, and `listTasks` all return identical field sets, preventing client-side field-set drift:

```bash
cd skills/omnifocus-manager
osascript -l JavaScript scripts/diff-task-shapes.js
# Should report: "All query functions return identical field sets"
```

Run after modifying `normalizeTask()` in `ofo-core.ts`.

### Shared Type Contract (`ofo-contract.d.ts`)

`scripts/src/ofo-contract.d.ts` defines the canonical `OfoTask` interface shared by both CLI (`ofo-cli.ts`) and plugin (`ofo-core.ts`). Serves as the single source of truth for the task shape. Also included in `tsconfig.attache.json` for Attache library type-checking.

---

**Generated:** 2026-01-17 | **Updated:** 2026-03-23
**Version:** 4.2.0
**Purpose:** Prevent code generation failures through systematic validation
