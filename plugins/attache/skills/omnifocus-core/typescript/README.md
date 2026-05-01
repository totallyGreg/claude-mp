# TypeScript Development Environment for OmniFocus Plugins

This directory contains TypeScript type definitions and configuration for developing OmniFocus plugins with full LSP support (autocomplete, type-checking, and error detection).

## Contents

- **omnifocus.d.ts** (1,698 lines) - Official TypeScript definitions for OmniFocus API (from Omni Automation, generated 2021-06-06)
- **omnifocus-extensions.d.ts** - Extended definitions for newer APIs added after 2021, including:
  - `LanguageModel` (Apple Foundation Models / Apple Intelligence, OmniFocus 4.8+)
  - Additional type refinements for `Selection`, `MenuItem`, `ToolbarItem`
- **tsconfig.json** - TypeScript compiler configuration (ES7 target)
- **example-plugin.ts** - Sample plugin demonstrating TypeScript development workflow

## Usage

### For Plugin Generation (Automated)

The TypeScript generator (`scripts/generate_plugin.ts`) automatically uses these definitions to validate plugins during generation. No manual setup required.

### For Manual Development (Optional)

If you want to manually write plugins in TypeScript with LSP support:

#### 1. Prerequisites

Install TypeScript and TypeScript Language Server:

```bash
# Install Node.js first (if not already installed)
# Download from https://nodejs.org

# Install TypeScript globally
sudo npm install -g typescript

# Install TypeScript Language Server
sudo npm install -g typescript-language-server
```

#### 2. Editor Setup

**VSCode / Cursor:**
- TypeScript LSP works automatically
- Open a .ts file in this directory to get autocomplete and type-checking

**BBEdit 14+:**
- Configure LSP support for TypeScript
- See: https://omni-automation.com/typescript/bbedit.html

**Vim/Neovim (with vtsls):**
- Already configured if using Claude Code
- LSP will provide autocomplete and diagnostics

#### 3. Development Workflow

```bash
# 1. Write plugin in TypeScript with .ts extension
nano MyPlugin.ts

# 2. TypeScript LSP provides:
#    - Autocomplete for OmniFocus API (flattenedTasks, Alert, etc.)
#    - Type-checking (catches errors like task.name() instead of task.name)
#    - Inline documentation from .d.ts files

# 3. When ready, rename .ts to .omnijs for deployment
mv MyPlugin.ts MyPlugin.omnijs

# 4. Install in OmniFocus
cp MyPlugin.omnijs ~/Library/Application\ Scripts/com.omnigroup.OmniFocus3/Plug-Ins/
```

## TypeScript Plugin Structure

```typescript
/*{
  "type": "action",
  "targets": ["omnifocus"],
  "author": "Your Name",
  "identifier": "com.yourname.plugin-id",
  "version": "1.0",
  "description": "Plugin description",
  "label": "Menu Label",
  "shortLabel": "Short",
  "paletteLabel": "Palette Label",
  "image": "list.bullet"
}*/
(() => {
  const action = new PlugIn.Action(async function(selection: Selection, sender: MenuItem | ToolbarItem) {
    // Type-safe code with LSP validation
    const tasks: Array<Task> = flattenedTasks;

    // LSP catches errors:
    // ✅ task.name (correct - property)
    // ❌ task.name() (error - not a function)

    // Autocomplete suggests:
    // task.<TAB> → name, note, completed, dueDate, markComplete(), etc.

    new Alert("Title", `Found ${tasks.length} tasks`).show();
  });

  action.validate = function(selection: Selection, sender: MenuItem | ToolbarItem): boolean {
    return true;
  };

  return action;
})();
```

## Type Definition Coverage

### Core Classes (omnifocus.d.ts)
- ✅ `Alert`, `Application`, `Calendar`, `Console`
- ✅ `Database`, `Document`, `FilePicker`, `FileSaver`, `FileWrapper`
- ✅ `Folder`, `FolderArray`, `Form`, `Formatter`
- ✅ `PlugIn`, `Project`, `ProjectArray`, `Selection`
- ✅ `Settings`, `Style`, `Tag`, `TagArray`, `Task`, `TaskArray`
- ✅ `Version`, `Window`, and many more

### Extended APIs (omnifocus-extensions.d.ts)
- ✅ `LanguageModel.GenerationOptions`
- ✅ `LanguageModel.Schema` (with `fromJSON()` factory method)
- ✅ `LanguageModel.Session` (with `respond()` and `respondWithSchema()`)
- ✅ Type refinements for `Selection`, `MenuItem`, `ToolbarItem`

### Global Variables
All OmniFocus globals are defined:
- `flattenedTasks`, `flattenedProjects`, `flattenedFolders`, `flattenedTags`
- `folders`, `projects`, `tags`, `inbox`, `library`

## Benefits of TypeScript Development

### 1. API Error Prevention
```typescript
// ❌ Python generator would create this without validation:
const name = task.name();  // ERROR: name is a property, not a method

// ✅ TypeScript LSP catches this immediately:
const name: string = task.name;  // Correct
```

### 2. Autocomplete
Type any OmniFocus object followed by `.` and get instant suggestions:
```typescript
task.     // → name, note, completed, dueDate, markComplete(), addTag(), etc.
project.  // → name, status, tasks, markComplete(), etc.
```

### 3. Documentation
Hover over any API to see inline documentation from .d.ts files:
```typescript
LanguageModel.Schema.fromJSON  // Shows full JSDoc with examples
```

### 4. Refactoring Safety
Rename variables, extract functions, and reorganize code with confidence—TypeScript ensures type correctness.

## Limitations

1. **No Transpilation**: TypeScript is used only for validation and autocomplete, not compilation. You write .ts files and rename to .omnijs—no build step needed.

2. **OmniFocus Runtime**: OmniFocus runs JavaScript (ES7), not TypeScript. The .d.ts files are for development only.

3. **Type Definitions Age**: `omnifocus.d.ts` was generated in 2021. Newer APIs are manually added to `omnifocus-extensions.d.ts`.

## Updating Type Definitions

To add definitions for new OmniFocus APIs:

1. Check official API docs: https://omni-automation.com/omnifocus/
2. Add definitions to `omnifocus-extensions.d.ts` (not omnifocus.d.ts)
3. Follow existing patterns (classes, namespaces, methods)
4. Test with example code to ensure LSP works correctly

## Resources

- **Official TypeScript Guide**: https://omni-automation.com/typescript/
- **OmniFocus API Reference**: https://omni-automation.com/omnifocus/
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/handbook/
- **Validation Guide**: `/references/code_generation_validation.md`

## Generator Integration

The TypeScript generator (`/scripts/generate_plugin.ts`) uses these definitions to:

1. **Validate templates during generation** using TypeScript Compiler API
2. **Catch API errors before file creation** (zero-tolerance validation)
3. **Generate type-safe plugins** that work on first deployment
4. **Eliminate API hallucinations** through compile-time checking

See `/scripts/README.md` for generator documentation.

---

**Last Updated**: 2026-01-02
**OmniFocus Version**: 4.8+ (with Foundation Models support)
**TypeScript Version**: ES7 target
