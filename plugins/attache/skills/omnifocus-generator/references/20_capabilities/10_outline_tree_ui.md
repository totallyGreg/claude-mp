# Outline, Tree, and Window Selection API

<!-- DRAFT — review during D2 integration -->

**What this covers:** `DocumentWindow`, `Tree`, `TreeNode` — the programmatic interface to the OmniFocus outline view and sidebar. Selection manipulation, node traversal, expand/collapse.

**What this does NOT cover:** Task/Project/Tag data model (see `01_tasks_projects_tags.md`), Perspectives (see `02_perspectives.md`).

---

## 1. First-Stop Solution: Check `ofoCore`

ofoCore does not currently expose Tree/TreeNode. Use native API directly. For most agent-driven work, operating on `flattenedTasks` / `flattenedProjects` is sufficient without needing Tree. Tree is primarily useful for plugin actions that need to mirror what the user sees, select specific items in the UI, or traverse the visible outline structure.

---

## 2. DocumentWindow

The window object exposed as `document.windows[0]` in `.omnifocusjs` plugins:

```js
var win = document.windows[0];

win.perspective    // Perspective.BuiltIn | Perspective.Custom (current view)
win.selection      // Selection object (tasks, projects, folders, tags selected)
win.content        // Tree — outline content area nodes
win.sidebar        // Tree — sidebar nodes
win.focus          // Array of Folder/Project limiting sidebar (OF4 iOS/iPad)

// Select specific objects in the current perspective
win.selectObjects([task1, project2]);  // clears current selection first
```

---

## 3. Tree

A `Tree` wraps the visible outline or sidebar. You get it from `win.content` or `win.sidebar`.

```js
var tree = win.content;

tree.rootNode                         // TreeNode — root (read-only)
tree.selectedNodes                    // TreeNode[] — current selection (read-only)

tree.nodeForObject(task)              // → TreeNode | null
tree.nodesForObjects([task1, task2])  // → TreeNode[] (only those in tree)
tree.reveal([node1, node2])           // expand ancestors so nodes are visible
tree.select([node1, node2], false)    // select; pass true to extend selection

// Clipboard operations
tree.copyNodes([node1], Pasteboard.general)
tree.paste(Pasteboard.general, node.after)
```

---

## 4. TreeNode

A `TreeNode` wraps a model object (Task, Project, Folder, Tag) within the visible outline.

```js
var node = tree.nodeForObject(myTask);

// Navigation
node.object          // The wrapped model object (Task | Project | Folder | Tag)
node.parent          // TreeNode | null (null if root)
node.rootNode        // Root TreeNode of this tree
node.children        // TreeNode[] — visible children (filtered/sorted by perspective)
node.childCount      // Number
node.childAtIndex(0) // → TreeNode
node.level           // Nesting level (0 = root)
node.index           // Index among siblings

// State
node.isExpanded      // Boolean (read-only)
node.isRevealed      // Boolean — true if all ancestors are expanded
node.isSelected      // Boolean (set to true to select)
node.isSelectable    // Boolean (read-only)
node.isRootNode      // Boolean
node.canExpand       // Boolean
node.canCollapse     // Boolean
node.isNoteExpanded  // Boolean — inline note expansion state

// Expand/collapse
node.expand(false)          // expand this node only
node.expand(true)           // expand this node and all descendants
node.collapse(false)
node.collapse(true)
node.reveal()               // expand all ancestors

// Note expansion
node.expandNote(false)      // expand inline note for this node
node.collapseNote(false)

// Traverse
node.apply(function(n) {
  console.log(n.object.name);   // called for this node and all descendants
});
```

---

## 5. Common Patterns

### Get the currently selected task(s):
```js
// Preferred: use selection directly (no Tree needed)
var tasks = selection.tasks;

// Via Tree (when you need node-level info):
var nodes = win.content.selectedNodes;
var tasks = nodes.map(function(n) { return n.object; })
  .filter(function(o) { return o instanceof Task; });
```

### Select a specific task programmatically:
```js
var task = Task.byIdentifier("abc123");
win.selectObjects([task]);

// Or via Tree:
var node = win.content.nodeForObject(task);
if (node) {
  win.content.reveal([node]);
  win.content.select([node], false);
}
```

### Traverse all visible outline nodes:
```js
win.content.rootNode.apply(function(node) {
  if (node.object instanceof Task) {
    console.log(node.level + ": " + node.object.name);
  }
});
```

### Expand all items in view:
```js
win.content.rootNode.expand(true);  // recursively expand everything
```

---

## 6. Plugin Format Note

`.omnifocusjs` — OmniFocus specific. The Tree/TreeNode/DocumentWindow API is OmniFocus-only.  
`.omnijs` — Cross-app (OmniFocus, OmniGraffle, OmniOutliner, OmniPlan). Outline API in `.omnijs` uses different classes per app; do not use OmniFocus-specific tree methods in cross-app scripts.

---

## 7. Reach-Out Trigger

```
WebFetch https://omni-automation.com/omnifocus/outline.html
Prompt: "I need the full signature for [DocumentWindow.selectObjects / Tree.select / TreeNode.apply etc.] including all parameters."
```
