# Files and Export

<!-- DRAFT — review during D2 integration -->

**What this covers:** FileWrapper, FilePicker, FileSaver, `document.makeFileWrapper()`, TaskPaper export, JSON/CSV/Markdown export patterns.

**What this does NOT cover:** UI dialogs beyond FilePicker/FileSaver. See `03_forms_ui.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

ofoCore does not currently wrap file export. Use native APIs directly.

---

## 2. FileWrapper

Represents a file or directory in memory. Used for reading/writing content.

```js
// Create from data
var data = Data.fromString("task content here");
var wrapper = FileWrapper.withContents("export.txt", data);

// Directory wrapper
var dir = new FileWrapper.withContents("bundle", null);   // pseudo-directory
// (In practice: use FileSaver to save a single FileWrapper)

// Properties
wrapper.filename           // String (actual name from last read)
wrapper.preferredFilename  // String (preferred write name)
wrapper.type               // FileWrapper.Type (File, Directory, Link)
wrapper.contents           // Data | null (if type is File)
wrapper.children           // FileWrapper[] (if type is Directory)
wrapper.destination        // URL | null (if type is Link)

// Methods
wrapper.filenameForChild(child)   // → String | null
wrapper.childNamed("name")        // → FileWrapper | null (for Directory type)
```

**FileWrapper.Type enum:**
```js
FileWrapper.Type.File        // Regular file
FileWrapper.Type.Directory   // Directory with children
FileWrapper.Type.Link        // Symbolic link
```

---

## 3. Export from OmniFocus Document

```js
// Export the current document as TaskPaper text
document.makeFileWrapper("export", "com.taskpaper.text").then(function(wrapper) {
  var text = wrapper.contents.toString();
  // text: full TaskPaper export
});

// Export as OmniFocus 2 file format
document.makeFileWrapper("export", "com.omnigroup.omnifocus2").then(function(wrapper) {
  // wrapper: binary OmniFocus file
});

// writableTypes: list all export format identifiers
var formats = document.writableTypes;
```

**Common export type identifiers:**
- `"com.taskpaper.text"` — TaskPaper plain text
- `"com.omnigroup.omnifocus2.export-filetype.plain-text"` — OmniFocus plain text export
- `"com.omnigroup.omnifocus2"` — OmniFocus native format
- `"public.plain-text"` — Generic plain text

---

## 4. FilePicker and FileSaver

See `03_forms_ui.md` for usage. Quick reference:

```js
// Open picker
var picker = new FilePicker();
picker.types = [new FileType("com.taskpaper.text")];
picker.show().then(function(urls) { ... });

// Save
var saver = new FileSaver();
saver.show(fileWrapper).then(function(savedURL) { ... });
```

---

## 5. TaskPaper Import/Export Patterns

### Import TaskPaper into inbox:

```js
var picker = new FilePicker();
picker.types = [new FileType("com.taskpaper.text")];
picker.show().then(function(urls) {
  URL.fetch(urls[0]).then(function(data) {
    var text = data.toString();
    var tasks = Task.byParsingTransportText(text);
    // tasks: Task[] — already added to inbox
    database.save();
  });
});
```

### Export selected tasks as TaskPaper:

```js
var tasks = selection.tasks;
database.copyTasksToPasteboard(tasks, Pasteboard.general);
// Pasteboard now contains TaskPaper text — user can paste elsewhere
```

---

## 6. JSON/CSV Export Patterns (Manual)

OmniFocus has no built-in JSON export. Build it from task properties:

```js
// JSON export of project tasks
function exportProjectJSON(project) {
  var rows = project.flattenedTasks.map(function(t) {
    return {
      id: t.id.primaryKey,
      name: t.name,
      note: t.note,
      dueDate: t.dueDate ? t.dueDate.toISOString() : null,
      completed: t.completed,
      tags: t.tags.map(function(g) { return g.name; })
    };
  });
  return JSON.stringify(rows, null, 2);
}

// CSV export
function exportProjectCSV(project) {
  var header = "id,name,dueDate,completed,tags\n";
  var rows = project.flattenedTasks.map(function(t) {
    return [
      t.id.primaryKey,
      '"' + t.name.replace(/"/g, '""') + '"',
      t.dueDate ? t.dueDate.toISOString() : "",
      t.completed,
      '"' + t.tags.map(function(g) { return g.name; }).join(";") + '"'
    ].join(",");
  });
  return header + rows.join("\n");
}

// Write to clipboard for paste into spreadsheet
Pasteboard.general.string = exportProjectCSV(project);
```

---

## 7. Reach-Out Trigger

```
WebFetch https://omni-automation.com/omnifocus/filewrapper.html
WebFetch https://omni-automation.com/omnifocus/taskpaper.html
Prompt: "I need the full signature for [method]. Include version requirements."
```
