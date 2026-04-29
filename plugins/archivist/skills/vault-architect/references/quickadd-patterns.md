---
last_verified: 2026-04-29
sources:
  - type: github
    repo: "chhoumann/quickadd"
    paths: ["src/"]
    description: "QuickAdd plugin source — choice types, macros, API"
  - type: web
    url: "https://quickadd.obsidian.guide"
    description: "Official QuickAdd documentation"
---

# QuickAdd Reference (v2.12.0)

Comprehensive reference for the QuickAdd Obsidian plugin. QuickAdd provides four choice types — Template, Capture, Macro, and Multi — that combine into powerful note creation and capture workflows.

- **Official Docs:** https://quickadd.obsidian.guide
- **Repository:** https://github.com/chhoumann/quickadd
- **Minimum Obsidian:** 1.11.4+ (1.12.2+ for CLI)

---

## Table of Contents

1. [Format Syntax](#format-syntax)
2. [Template Choices](#template-choices)
3. [Capture Choices](#capture-choices)
4. [Macro Choices](#macro-choices)
5. [Multi Choices](#multi-choices)
6. [Canvas Capture](#canvas-capture)
7. [Base File Workflows](#base-file-workflows)
8. [CLI Automation](#cli-automation)
9. [Inline Scripts](#inline-scripts)
10. [Global Variables](#global-variables)
11. [QuickAdd API](#quickadd-api)
12. [Suggester System](#suggester-system)
13. [Packages](#packages)
14. [Templater Integration](#templater-integration)
15. [PKM Workflow Patterns](#pkm-workflow-patterns)
16. [Troubleshooting](#troubleshooting)

---

## Format Syntax

QuickAdd tokens can be used in file names, capture formats, template content, and folder paths. All tokens use `{{TOKEN}}` syntax.

### Core Tokens

| Token | Description |
|-------|-------------|
| `{{VALUE}}` / `{{NAME}}` | User input prompt. If text is selected, uses selection. Interchangeable. |
| `{{DATE}}` | Current date in `YYYY-MM-DD`. Offset with `{{DATE+3}}` or `{{DATE+-3}}`. |
| `{{DATE:<format>}}` | Current date with Moment.js format. E.g. `{{DATE:YYYY-MM-DD HH:mm}}`. |
| `{{LINKCURRENT}}` | Wiki-link to the active note `[[current note]]`. |
| `{{FILENAMECURRENT}}` | Basename of the active note (no extension). |
| `{{TITLE}}` | Final rendered filename of the note being created/captured to. |
| `{{selected}}` | Current editor selection (empty if none). |
| `{{CLIPBOARD}}` | Current clipboard content. |
| `{{RANDOM:<length>}}` | Random alphanumeric string (1-100 chars). E.g. `{{RANDOM:6}}` -> `3YusT5`. |
| `{{MVALUE}}` | Opens math/LaTeX modal. Submit with Ctrl+Enter. |

### Variable Tokens

| Token | Description |
|-------|-------------|
| `{{VALUE:<name>}}` | Named variable. Prompted once, reused across macro steps with same name. Comma-separated values create a suggester. |
| `{{VALUE:<name>\|default:<val>}}` | Named variable with default value pre-populated in input. |
| `{{VALUE:<name>\|label:<text>}}` | Adds helper text below the prompt header. |
| `{{VALUE:<items>\|text:<labels>}}` | Decouples display from inserted value. E.g. `{{VALUE:a,b,c\|text:Alpha,Beta,Charlie}}` shows labels, inserts values. |
| `{{VALUE:<items>\|custom}}` | Allows custom typed input in addition to listed options. |
| `{{VALUE:<name>\|type:multiline}}` | Forces multi-line textarea for this token. |
| `{{VALUE:<name>\|case:<style>}}` | Case transform. Styles: `kebab`, `snake`, `camel`, `pascal`, `title`, `lower`, `upper`, `slug`. |

Options can be combined: `{{VALUE:title|label:Post Title|case:kebab|default:My Post}}`

**Case transform example:**
```
Input: "My New Blog Post"
{{VALUE:title}}              -> My New Blog Post
{{VALUE:title|case:kebab}}   -> my-new-blog-post
{{VALUE:title|case:snake}}   -> my_new_blog_post
{{VALUE:title|case:pascal}}  -> MyNewBlogPost
{{VALUE:title|case:slug}}    -> my-new-blog-post (filename-safe)
```

### Date Variable Token

| Token | Description |
|-------|-------------|
| `{{VDATE:<name>, <format>}}` | Prompted date with natural language support. E.g. "today", "next monday", "+7 days". Short aliases: `t` (today), `tm` (tomorrow), `yd` (yesterday). |
| `{{VDATE:<name>, <format>\|<default>}}` | With default value. E.g. `{{VDATE:date,YYYY-MM-DD\|today}}`. |

Reuse same variable with different formats:
```
{{VDATE:date,YYYY}}/{{VDATE:date,MM}}/{{VDATE:date,DD}}
```
Prompts once, formats three ways.

### Field Suggestion Token

| Token | Description |
|-------|-------------|
| `{{FIELD:<name>}}` | Suggests existing values for a YAML field from your vault. |
| `{{FIELD:<name>\|folder:<path>}}` | Filter suggestions to files in a folder. |
| `{{FIELD:<name>\|tag:<tag>}}` | Filter to files with a specific tag. |
| `{{FIELD:<name>\|inline:true}}` | Include Dataview inline fields (`field:: value`). |
| `{{FIELD:<name>\|inline:true\|inline-code-blocks:ad-note}}` | Include inline fields inside specific fenced block types. |
| `{{FIELD:<name>\|exclude-folder:<path>}}` | Exclude files in folder. |
| `{{FIELD:<name>\|exclude-tag:<tag>}}` | Exclude files with tag. |
| `{{FIELD:<name>\|default:<val>}}` | Prepend a default suggestion. |
| `{{FIELD:<name>\|default:<val>\|default-empty:true}}` | Default only when no matches found. |

Filters combine: `{{FIELD:status|folder:projects|tag:active|exclude-folder:archive}}`

### Other Tokens

| Token | Description |
|-------|-------------|
| `{{TEMPLATE:<path>}}` | Include a template file. Supports Templater syntax. Also supports `.base` files. |
| `{{MACRO:<name>}}` | Execute a macro and insert its return value. |
| `{{MACRO:<name>\|label:<text>}}` | Macro with custom label for the export picker. |
| `{{GLOBAL_VAR:<name>}}` | Insert a global variable snippet (case-insensitive lookup). |

---

## Template Choices

Template choices create new notes from template files.

### Required Setting

- **Template Path** - Path to template file (`.md`, `.canvas`, or `.base`). Vault-relative.

### Optional Settings

| Setting | Description |
|---------|-------------|
| File Name Format | Dynamic name using format syntax. E.g. `{{DATE:YYYY-MM-DD}} {{VALUE}}` |
| Create in folder | Destination folder(s). Multiple folders = suggester prompt. |
| Append link | Link from current note to new note. Modes: required, skip-if-no-active, disabled. |
| Link placement | Replace selection, after selection, end of line, new line. |
| Increment file name | Add number suffix if file exists (`note` -> `note1`). |
| Open | Open created file. Optional: new tab with split direction. |

### File Already Exists Behavior

When the target file exists, QuickAdd prompts:
- **Append to bottom** / **Append to top** - Add template content
- **Overwrite** - Replace file content
- **Increment** - Create with number suffix
- **Nothing** - Open existing file without changes

### Example: Meeting Note Template Choice

```
Choice name: "New Meeting Note"
Type: Template
Template path: Templates/meeting.md
File name format: {{DATE:YYYY-MM-DD}} {{VALUE:title}}
Create in folder: 700 Notes/Meetings/
Append link: Enabled (skip if no active file)
Open: Yes
```

---

## Capture Choices

Capture choices append content to existing files without leaving your current view.

### Capture Target

Set via **Capture To** field or enable **Capture to active file**.

| Target | Behavior |
|--------|----------|
| File name | Captures to that specific file. Supports format syntax. |
| Folder path | Shows file picker for that folder. |
| `#tag` | Shows picker for files with that tag. |
| Empty or `/` | Shows picker for all vault files. |
| `.canvas` file | Canvas capture (see [Canvas Capture](#canvas-capture)). |

File extensions: `.md` is default if omitted. Explicit `.md` and `.canvas` are preserved. `.base` is **not** supported as a direct capture target.

### Capture Options

| Option | Description |
|--------|-------------|
| Create file if not exists | Creates file, optionally from a template. |
| Task | Format captured text as a checkbox task. |
| Selection as value | Follow global, use selection, or ignore selection for `{{VALUE}}`. |
| Write position | Top, bottom, after line, or cursor-based modes. |
| Append link | Link to active note. Same three modes as Template choices. |
| Capture format | Mini-template for captured content. Default: `{{VALUE}}`. |

### Insert After

Insert content after a matched line (typically a heading).

**Blank lines after match:**
- **Auto (headings only)** - Skip blank lines only after ATX headings (default)
- **Always skip** - Skip all blank lines after match
- **Never skip** - Insert immediately after matched line

**Sub-options:**
- **Insert at end of section** - Place at end of section instead of right after heading
- **Consider subsections** - Treat subsections as part of the parent section
- **Create line if not found** - Create the heading if missing (at start, end, or cursor)

### Example: Daily Journal Capture

```
Choice name: "Quick Log"
Type: Capture
Capture to: {{DATE:YYYY-MM-DD}}
Folder: Daily Notes/
Create if not exists: Yes
Insert after: ## Notes
Insert at end of section: Yes
Capture format: - {{DATE:HH:mm}} {{VALUE}}
```

Result in daily note:
```markdown
## Notes

- 14:30 Had meeting with customer about Q2 goals
- 15:45 Reviewed PR #42 for auth module
```

### Example: Capture with Mixed Input Types

```
Capture format:
- {{VALUE:Title|label:Title}} ({{VALUE:Priority|case:lower}})
{{VALUE:Body|type:multiline|label:Details}}
```

Prompts for a single-line title, a priority value, and a multi-line body.

---

## Macro Choices

Macros chain multiple commands into automated workflows. They are the most powerful QuickAdd feature.

### Command Types

| Command | Description |
|---------|-------------|
| Obsidian Command | Run any registered command |
| Editor Commands | Copy, Cut, Paste, Paste with format, Select active line, Select link on active line |
| User Script | Run a `.js` file from your vault |
| Nested Choice | Execute another QuickAdd choice |
| Wait | Delay in milliseconds |
| AI Assistant | Execute AI prompts |
| Open File | Open files with format syntax support |
| Conditional | Branch execution based on variable comparison or script result |

**Cursor Navigation Commands (new in 2.12.0):**
- Move cursor to file start / file end
- Move cursor to line start / line end

### User Scripts

Scripts live in `.js` files inside your vault (not in `.obsidian` or dot-prefixed folders).

```javascript
module.exports = async (params) => {
    const { app, quickAddApi, variables } = params;

    const name = await quickAddApi.inputPrompt("Project name:");
    variables.projectName = name;
    variables.slug = name.toLowerCase().replace(/\s+/g, '-');
};
```

### Variables Between Commands

Variables set in scripts are available to subsequent macro steps:
- In templates: `{{VALUE:projectName}}`
- In file names: `Projects/{{VALUE:slug}}`

**Prompt control:**
- `undefined` or `null` -> will prompt user for input
- `""` (empty string) -> will NOT prompt, inserts empty
- Any other value -> will NOT prompt, inserts value

### Conditional Commands

Branch macro execution without JavaScript:

- **Variable mode** - Compare a variable using equals, contains, less/greater than, or truthiness
- **Script mode** - Run a `.js` file that returns `true`/`false`
- **Then/Else branches** - Each branch is a full command sequence

### Macro Settings

- **Run on Plugin Load** - Auto-run macro when Obsidian starts

### Abort Behavior

Macros stop automatically on:
- User pressing Escape/Cancel in any prompt
- Unhandled script errors
- Explicit `params.abort()` call

---

## Multi Choices

Multi choices are purely organizational — folders of other choices. They create nested menus in the QuickAdd command palette.

```
Multi: "Work"
  ├── Template: "New Meeting Note"
  ├── Capture: "Quick Log"
  └── Multi: "Projects"
      ├── Template: "New Project"
      └── Capture: "Project Update"
```

---

## Canvas Capture

QuickAdd 2.12.0 supports two Canvas capture workflows.

### 1. Capture to Selected Card

Enable **Capture to active file** while a Canvas is active with one card selected.

Supported targets:
- Text cards
- File cards pointing to Markdown notes

### 2. Capture to Specific Canvas Node

With **Capture to active file** off, point **Capture To** at a `.canvas` file and set **Target canvas node**.

### Write Position Support

| Mode | Canvas Support |
|------|---------------|
| Top of file | Yes |
| Bottom of file | Yes |
| After line... | Yes |
| At cursor | No |
| New line above/below cursor | No |

QuickAdd preserves Obsidian's tab-indented `.canvas` formatting to reduce whitespace diffs.

---

## Base File Workflows

QuickAdd 2.12.0 treats `.base` files as first-class citizens.

### Template Choices with .base

Template choices can create `.base` files directly. Set the template path to a `.base` file and the created file will also be `.base`.

### Inserting Base Content into Markdown Notes

Use `{{TEMPLATE:...}}` in a Capture format to insert `.base` content into the active markdown note:

````markdown
## Related Notes

```base
{{TEMPLATE:Templates/MOC Related Notes.base}}
```
````

This is the key workflow: keep a reusable Base definition in `Templates/` and stamp it into notes on demand. The Base query resolves in the context of the note it's embedded in, so `this.file` points to the target note.

### Example: MOC Related Notes Capture

1. Create `Templates/MOC Related Notes.base`:
```yaml
filters:
  and:
    - 'file.ext == "md"'
    - "file.hasLink(this.file)"
    - "file.path != this.file.path"
views:
  - type: table
    name: Related notes
```

2. Create a Capture choice:
   - Capture to active file: On
   - Write position: Top
   - Capture format:

````markdown
## Related Notes

```base
{{TEMPLATE:Templates/MOC Related Notes.base}}
```

Context: {{VALUE}}
````

3. Run while an MOC note is active. The Base view shows notes linking to that MOC.

### Important Distinctions

- **Template choices** can create `.base` files directly
- **Capture choices** cannot write to `.base` files as destinations
- **Capture choices** can insert `.base` template content into Markdown notes via `{{TEMPLATE:...}}`

---

## CLI Automation

QuickAdd 2.12.0 registers native Obsidian CLI handlers (requires Obsidian 1.12.2+).

### Commands

| CLI Command | Description |
|-------------|-------------|
| `quickadd` / `quickadd:run` | Execute a choice |
| `quickadd:list` | List available choices |
| `quickadd:check` | Check if a choice can run |

### Examples

```bash
# Run a choice
obsidian vault=dev quickadd choice="Daily log"

# List all Capture choices
obsidian vault=dev quickadd:list type=Capture

# Check if a choice is runnable
obsidian vault=dev quickadd:check choice="Daily log"
```

### Passing Variables

```bash
# Named variable
obsidian vault=dev quickadd choice="New Project" value-name="My Project"

# Key-value params
obsidian vault=dev quickadd choice="Quick Log" value="Meeting notes"

# JSON variables
obsidian vault=dev quickadd choice="Template" vars='{"project":"QuickAdd","priority":"high"}'
```

### Behavior

- CLI runs are **non-interactive** by default — missing inputs return structured JSON instead of prompts
- Multi choices are still interactive and cannot run via CLI
- `quickadd:list` includes nested choices inside multis

### Shell Script Integration

```bash
#!/bin/bash
# Daily standup automation
DATE=$(date +%Y-%m-%d)
obsidian vault=work quickadd choice="Daily Standup" \
  value-date="$DATE" \
  value-status="In progress"
```

---

## Inline Scripts

Inline JavaScript in Template and Capture formats. Use the `js quickadd` language tag (not just `js`).

````markdown
```js quickadd
const input = await this.quickAddApi.inputPrompt("Enter text:");
return `Processed: ${input}`;
```
````

### Key Rules

- Return type must be a string
- `this.quickAddApi` provides the full API
- `this.variables` for variable handoff to formatter
- Inline scripts execute **before** `{{VALUE}}` token substitution — do not use `{{VALUE}}` inside script string literals

### Example: Phone Number to Link

````markdown
```js quickadd
const raw = await this.quickAddApi.inputPrompt("Phone number");
if (!raw) return "";
const digits = raw.replace(/[^0-9+]/g, "");
return `[${raw}](tel:${digits})`;
```
````

---

## Global Variables

Vault-scoped reusable snippets. Configure in Settings > QuickAdd > Global Variables.

### Setup

Define name-value pairs. Values can contain QuickAdd tokens.

```
Name: MyProjects
Value: {{VALUE:Inbox,Work,Personal,Archive}}
```

### Usage

```markdown
Project: {{GLOBAL_VAR:MyProjects}}
Path: Projects/{{GLOBAL_VAR:MyProjects}}/{{DATE:YYYY}}/
```

- Token matching is case-insensitive
- Globals can reference other globals (nesting depth limited to 5)
- Globals expand early, so tokens inside them are processed by subsequent passes
- Autocomplete triggers when typing `{{GLOBAL_VAR:`

---

## QuickAdd API

Available in user scripts (`params.quickAddApi`), inline scripts (`this.quickAddApi`), and from other plugins (`app.plugins.plugins.quickadd.api`).

### User Input Methods

```javascript
// Single-line input
const name = await quickAddApi.inputPrompt("Name:", "placeholder", "default");

// Multi-line input
const body = await quickAddApi.wideInputPrompt("Description:");

// Yes/No confirmation
const ok = await quickAddApi.yesNoPrompt("Continue?", "Extra details");

// Info dialog
await quickAddApi.infoDialog("Done", ["Line 1", "Line 2"]);

// Suggester (select from list)
const pick = await quickAddApi.suggester(
    ["Display A", "Display B"],  // what user sees
    ["value_a", "value_b"]       // what gets returned
);

// Suggester with custom input allowed
const tag = await quickAddApi.suggester(
    ["#work", "#personal"],
    ["#work", "#personal"],
    "Select or type new tag",
    true  // allowCustomInput
);

// Suggester with custom rendering
const item = await quickAddApi.suggester(
    values, values, "Pick one", false,
    { renderItem: (value, el) => {
        el.createEl('div', { text: value });
    }}
);

// Checkbox (multiple selection)
const features = await quickAddApi.checkboxPrompt(
    ["Option A", "Option B", "Option C"],
    ["Option A"]  // pre-selected
);
```

### Multi-Input Forms

Collect multiple inputs in a single modal:

```javascript
const values = await quickAddApi.requestInputs([
    { id: "title", label: "Title", type: "text", defaultValue: "Untitled" },
    { id: "due", label: "Due Date", type: "date", dateFormat: "YYYY-MM-DD" },
    { id: "status", label: "Status", type: "dropdown",
      options: ["Todo", "Doing", "Done"] },
    { id: "tags", label: "Tags", type: "suggester",
      options: ["work", "personal", "urgent"],
      suggesterConfig: { multiSelect: true } },
    { id: "notes", label: "Notes", type: "textarea" },
    { id: "priority", label: "Priority", type: "field-suggest" }
]);
```

Field types: `text`, `textarea`, `dropdown`, `date`, `field-suggest`, `suggester`.

### Execute Choices Programmatically

```javascript
await quickAddApi.executeChoice("Create Meeting Note", {
    meetingTitle: "Project Review",
    attendees: "John, Jane",
    value: "Agenda content"  // maps to {{VALUE}}
});
```

### Utility Module

```javascript
const clip = await quickAddApi.utility.getClipboard();
await quickAddApi.utility.setClipboard("new content");
const sel = quickAddApi.utility.getSelection();  // sync, returns "" if none
```

### Date Module

```javascript
quickAddApi.date.now();                    // "2026-03-05"
quickAddApi.date.now("YYYY-MM-DD HH:mm"); // "2026-03-05 14:30"
quickAddApi.date.now("YYYY-MM-DD", 7);    // 7 days from now
quickAddApi.date.tomorrow("dddd");         // "Friday"
quickAddApi.date.yesterday();              // "2026-03-04"
```

### Field Suggestions Module

```javascript
// Get all values for a field
const statuses = await quickAddApi.fieldSuggestions.getFieldValues("status");

// With filters
const types = await quickAddApi.fieldSuggestions.getFieldValues("type", {
    folder: "projects",
    tags: ["active"],
    includeInline: true,
    includeInlineCodeBlocks: ["ad-note"]
});

// Clear cache after bulk updates
quickAddApi.fieldSuggestions.clearCache("status");
```

### AI Module

```javascript
const result = await quickAddApi.ai.prompt(
    "Summarize: " + content,
    "gpt-4",
    {
        variableName: "summary",
        shouldAssignVariables: true,
        modelOptions: { temperature: 0.3, max_tokens: 150 },
        systemPrompt: "You are a note summarizer."
    }
);
// result.summary contains the response

// Available models
const models = quickAddApi.ai.getModels();

// Token counting
const count = quickAddApi.ai.countTokens(text, "gpt-4");

// Request logs (in-memory, up to 25 entries)
const logs = quickAddApi.ai.getRequestLogs(10);
const last = quickAddApi.ai.getLastRequestLog();
quickAddApi.ai.clearRequestLogs();
```

### Cancellation Handling

All prompt methods reject with `MacroAbortError` on user cancellation. Letting it bubble stops the macro automatically. Catch only if you need cleanup:

```javascript
try {
    const input = await quickAddApi.inputPrompt("Enter value:");
} catch (error) {
    if (error?.name === "MacroAbortError") {
        // Optional cleanup before macro stops
        return;
    }
    throw error;
}
```

---

## Suggester System

The QuickAdd suggester provides context-aware search when selecting files, tags, and content.

### Special Search Modes

| Prefix | Searches |
|--------|----------|
| `#` | Tags in vault |
| `[[` | Files in vault |
| `[[#` | Headings in vault |
| `[[#^` | Block references |
| `./` | Current folder |
| `../` | Parent folder |

---

## Packages

Export and import QuickAdd configurations as `.quickadd.json` packages.

### Export

Settings > QuickAdd > Export package. Select choices to include — dependencies and scripts are bundled automatically.

### Import

Settings > QuickAdd > Import package. For each choice: Import (new), Overwrite (replace), Duplicate (keep both), or Skip.

Asset paths can be adjusted during import. QuickAdd updates references automatically.

---

## Templater Integration

QuickAdd augments Templater — both syntaxes work in the same template file.

### QuickAdd Variables + Templater Syntax

```markdown
---
title: "{{VALUE}}"
date: {{DATE:YYYY-MM-DD}}
---

# {{VALUE}}

Created by: <% tp.system.clipboard() %>
Last modified: <% tp.date.now("YYYY-MM-DD HH:mm") %>
```

### Macro with Templater Step

In a macro, add a **Nested Choice** step pointing to a Template choice. The Template choice processes Templater syntax in the template file. Variables set in earlier macro steps are available via `{{VALUE:variableName}}`.

### Accessing QuickAdd API from Templater

```javascript
<%*
const quickAddApi = app.plugins.plugins.quickadd.api;
const result = await quickAddApi.inputPrompt("Enter value:");
tR += result;
%>
```

---

## PKM Workflow Patterns

### Pattern 1: Quick Meeting Log to Daily Note

**Type:** Capture

```
Capture to: {{DATE:YYYY-MM-DD}}
Folder: Daily Notes/
Insert after: ## Notes
Insert at end of section: Yes
Capture format: ### (log:: {{TIME:HH:mm ZZ}}: {{VALUE}})
```

### Pattern 2: Template Menu with Case Transforms

**Type:** Multi > Template choices

```
Multi: "New Note"
  ├── Meeting Note
  │   Template: Templates/meeting.md
  │   File name: {{DATE:YYYY-MM-DD}} {{VALUE:title|case:title}}
  │   Folder: Meetings/
  ├── Project Note
  │   Template: Templates/project.md
  │   File name: {{VALUE:name|case:title}}
  │   Folder: Projects/
  └── Blog Post
      Template: Templates/blog.md
      File name: {{DATE:YYYY-MM-DD}}-{{VALUE:title|case:slug}}
      Folder: Blog/
```

### Pattern 3: Capture with Context Link

```
Capture format:
## {{DATE:YYYY-MM-DD HH:mm}}

**Context:** {{LINKCURRENT}}

{{VALUE}}

---
```

### Pattern 4: Multi-Step Project Creation Macro

**Macro steps:**
1. User Script - collect project name, set variables
2. Nested Choice - Template: create project note
3. Nested Choice - Template: create project tasks note
4. Obsidian Command - open file explorer
5. Open File - open project note

```javascript
// Step 1 script
module.exports = async ({ quickAddApi, variables }) => {
    const name = await quickAddApi.inputPrompt("Project name:");
    variables.projectName = name;
    variables.slug = name.toLowerCase().replace(/\s+/g, '-');
    variables.created = quickAddApi.date.now("YYYY-MM-DD");
};
```

### Pattern 5: Quick Task with Field Suggestions

```
Capture format:
- [ ] {{VALUE:task}} | priority:: {{FIELD:priority|default:medium}} | due:: {{VDATE:due,YYYY-MM-DD|tomorrow}}
```

### Pattern 6: Insert Base View into Active Note

**Type:** Capture (to active file)

````markdown
Capture format:
## {{VALUE:Section Title|label:Heading for the Base section}}

```base
{{TEMPLATE:Templates/Related Notes.base}}
```
````

### Pattern 7: CLI-Driven Daily Standup

```bash
#!/bin/bash
obsidian vault=work quickadd choice="Daily Log" \
  value="Standup: $(date +%H:%M)"
```

### Pattern 8: AI-Assisted Note Summarization

**Macro steps:**
1. User Script - get selection, call AI, set summary variable
2. Nested Choice - Capture: insert summary below current section

```javascript
module.exports = async ({ quickAddApi, variables }) => {
    const text = quickAddApi.utility.getSelection();
    if (!text) {
        await quickAddApi.infoDialog("Error", "Select text to summarize.");
        return;
    }
    const { summary } = await quickAddApi.ai.prompt(
        "Summarize concisely:\n\n" + text,
        "gpt-4",
        { variableName: "summary", modelOptions: { temperature: 0.3 } }
    );
    variables.summary = summary;
};
```

### Pattern 9: Conditional Macro Branch

**Macro with conditional command:**
- Condition: variable `taskType` equals `"meeting"`
- Then: Run "Create Meeting Note" choice
- Else: Run "Create Task Note" choice

No JavaScript required for simple branching.

---

## Troubleshooting

### Capture not inserting at correct location

1. Check **Write position** setting (top, bottom, after line, cursor)
2. If using **Insert after**, verify the heading text matches exactly
3. Check **Blank lines after match** setting
4. Enable **Create line if not found** if the heading may not exist

### Variables not expanding

```markdown
{{VALUE}}       # Correct
{VALUE}         # Wrong - missing outer braces
{{ VALUE }}     # Wrong - no spaces allowed
```

### Template choice creating file in wrong location

- If **Create in folder** is off, check whether **File name format** already contains a full path — QuickAdd no longer duplicates folder prefixes (fixed in 2.12.0)

### Macro variables not passing between steps

- `{{VALUE}}` / `{{NAME}}` are scoped per template step
- Use `{{VALUE:sharedName}}` to share one prompt across macro steps
- Variable names are case-sensitive

### Canvas capture aborting

- Ensure exactly one card is selected
- Selected card must be a text card or file card pointing to Markdown
- Do not use cursor-based write modes with Canvas

### Scripts not appearing in picker

- Scripts must be `.js` files in vault
- Must NOT be in `.obsidian/` or any dot-prefixed folder
- Use `_quickadd/` not `.quickadd/` for script folders

### Inline script not executing

- Use `js quickadd` language tag, not `js`
- `return` a string value to insert content
- Do not rely on `{{VALUE}}` inside JavaScript string literals

---

## Version History Highlights

### 2.12.0 (2026-03-05)
- `.base` templates as first-class Template choices
- `{{TEMPLATE:...}}` supports `.base` files in Capture formats
- Canvas capture (selected card and specific node)
- Obsidian CLI handlers (`quickadd`, `quickadd:list`, `quickadd:check`)
- `{{VALUE:...|text:...}}` for label/value separation
- Macro cursor navigation commands
- AI request logs API

### 2.11.0 (2026-02-08)
- `|case:<style>` transforms (8 styles)
- Smarter capture target resolution
- Case-insensitive alias matching

### 2.10.0 (2026-01-28)
- `|type:multiline` per-token
- `|label:` and `|default:` options
- `{{VDATE:...}}` native date picker
- `requestInputs()` multi-field modal API
- SecretStorage for API keys
- `quickAddApi.getSelection()`
- Inline insert-after mode
