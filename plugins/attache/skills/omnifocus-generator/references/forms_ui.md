# Forms and UI Interaction

<!-- DRAFT — review during D2 integration -->

**What this covers:** Form class, Form.Field subtypes, Alert, FilePicker, FileSaver — all UI primitives for collecting user input or presenting information in OmniFocus plugins.

**What this does NOT cover:** Foundation Models (AI prompting). See `04_foundation_models.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

ofoCore does not wrap UI classes — these must be used directly. Form, Alert, FilePicker, and FileSaver are all available natively in any Omni Automation plugin action context.

---

## 2. Form — Collecting User Input

```js
var form = new Form();

// Add fields (order determines display order)
form.addField(new Form.Field.String("fieldKey", "Label", "default value"));
form.addField(new Form.Field.Checkbox("enableX", "Enable X", false));
form.addField(new Form.Field.Date("dueDate", "Due Date", null));
form.addField(new Form.Field.Option("priority", "Priority", ["High","Normal","Low"], "Normal"));
form.addField(new Form.Field.MultipleOptions("tags", "Tags", ["@waiting","@next"], null));

// Optional validation
form.validate = function(formObj) {
  if (!formObj.values["fieldKey"]) return false;
  return true;
};

// Show (returns Promise)
return form.show("Dialog Title", "Confirm").then(function(formResult) {
  var name = form.values["fieldKey"];
  var checked = form.values["enableX"];
});
```

### Form.Field Subtypes

| Class | Constructor | Notes |
|-------|-------------|-------|
| `Form.Field.String` | `(key, label, value?)` | Text input; value is default |
| `Form.Field.Password` | `(key, label)` | Masked text input |
| `Form.Field.Checkbox` | `(key, label, value?)` | Boolean toggle; value is default state |
| `Form.Field.Date` | `(key, label, value?, formatter?)` | Date picker |
| `Form.Field.Option` | `(key, label, options, value?)` | Single-select dropdown; options: String[] |
| `Form.Field.MultipleOptions` | `(key, label, options, value?)` | Multi-select list; value: String[] initial selection |

**⚠️ Key behaviors:**
- `form.values` — populated after `form.show()` resolves; keyed by the field key string
- `form.fields` — the added fields array
- `form.validate` — function(form) → Boolean; called on Confirm button press; return false to keep form open
- The `form.show()` promise rejects if the user cancels — always handle rejection

### Cancel Handling

```js
form.show("Title", "OK").then(function(result) {
  // User confirmed
  var value = form.values["myField"];
}).catch(function() {
  // User cancelled — do nothing or clean up
});
```

---

## 3. Alert — Information / Options

```js
var alert = new Alert("Title", "Message body");
alert.addOption("Yes");
alert.addOption("No");
alert.show(function(optionIndex) {
  if (optionIndex === 0) { /* Yes */ }
});

// Or promise-based
alert.show(null).then(function(optionIndex) { ... });
```

If no options are added, a default "OK" option is shown automatically.

---

## 4. FilePicker — Open a File

```js
var picker = new FilePicker();
picker.message = "Choose a file to import";
picker.multiple = false;
picker.folders = false;
picker.types = [new FileType("com.taskpaper.text")];  // optional filter

picker.show().then(function(urls) {
  if (urls.length > 0) {
    URL.fetch(urls[0]).then(function(data) {
      var text = data.toString();
    });
  }
});
```

---

## 5. FileSaver — Save a File

```js
var saver = new FileSaver();
saver.message = "Save export";
saver.prompt = "Save";
saver.nameLabel = "File name:";
saver.types = [new FileType("public.plain-text")];

// fileWrapper must be a FileWrapper.withContents(name, data)
saver.show(fileWrapper).then(function(savedURL) {
  // file saved to savedURL
});
```

---

## 6. Common Patterns

### Task name + tag picker

```js
var form = new Form();
form.addField(new Form.Field.String("name", "Task name", ""));
var tagNames = flattenedTags.map(function(t) { return t.name; });
form.addField(new Form.Field.Option("tag", "Tag", tagNames, tagNames[0]));
form.validate = function(f) { return f.values["name"].length > 0; };
form.show("Add Task", "Create").then(function() {
  var task = new Task(form.values["name"], inbox.ending);
  var tag = flattenedTags.byName(form.values["tag"]);
  if (tag) task.addTag(tag);
  database.save();
});
```

### Confirmation dialog before destructive operation

```js
var alert = new Alert("Drop project?", "This cannot be undone.");
alert.addOption("Drop");
alert.addOption("Cancel");
alert.show(function(idx) {
  if (idx === 0) {
    project.status = Project.Status.Dropped;
    database.save();
  }
});
```

---

## 7. Reach-Out Trigger

Form and Alert are not on omni-automation.com as standalone pages. The full API is in `30_api_reference/omnifocus_api.md` under `Form`, `Form.Field`, `Alert`, `FilePicker`, `FileSaver`. No WebFetch needed.
