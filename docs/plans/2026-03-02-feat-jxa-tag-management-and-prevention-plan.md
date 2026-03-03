---
title: "JXA Bug Prevention and Tag Hierarchy Management"
type: feat
status: active
date: 2026-03-02
issue: 76
---

# JXA Bug Prevention and Tag Hierarchy Management

## Overview

Issue #76 has three layers of work: (1) preventing the class of JXA bugs that shipped in earlier versions, (2) adding tag hierarchy management commands to `manage_omnifocus.js`, and (3) enabling programmatic tag restructuring based on the OmniFocus Tagsonomy Report.

The Part 1 bugs (wrong constructors, broken `addTag`) were fixed in v6.0.1 (commit `bc83991`), but nothing prevents the same mistakes from recurring. The JXA scripting bridge has no type checking, and syntactically valid JavaScript can be semantically wrong for OmniFocus.

## Problem Statement

### Prevention Gap

JXA has no linting, no type checking, and no compile-time validation. The bugs that shipped in v6.0.1 were:
- `app.defaultDocument.Project()` instead of `app.Project()` — valid JS, wrong OmniFocus API
- `project.addTag()` instead of the `flattenedTasks.whose({id})` workaround — valid method, wrong object type

These were only caught by runtime errors. There is no reference document, no smoke test for tag operations, and no guard against repeating them.

### Missing Tag Commands

`manage_omnifocus.js` has 16 commands but none for managing tags themselves. Tags can only be created as a side effect of task creation. There is no way to rename, move, delete, or list tags programmatically.

### Tagsonomy Restructuring Need

An audit of OmniFocus tags (see `[[OmniFocus Tagsonomy Report]]` in Obsidian) identified structural issues: "Anywhere" is overloaded, state tags are scattered, orphaned top-level tags lack grouping, and 11+ tags have 0 tasks. Restructuring requires the tag management commands from Part 2.

## Proposed Solution

### Phase 1: JXA Prevention Infrastructure

#### 1a. JXA API Reference Document

Create `scripts/libraries/jxa/JXA_API_REFERENCE.md` documenting correct patterns:

```markdown
# OmniFocus JXA API Quick Reference

## Constructors (MUST use app.*, NEVER app.defaultDocument.*)
- `app.Task({name: "..."})` — create task object
- `app.Project({name: "..."})` — create project object
- `app.Tag({name: "..."})` — create tag object
- `app.Folder({name: "..."})` — create folder object

## Adding to document
- `doc.inbox.tasks.push(task)` — add task to inbox
- `doc.folders.push(folder)` — add folder to root
- `doc.tags.push(tag)` — add tag to root
- `parentTag.tags.push(childTag)` — nest tag under parent

## Tag Operations
- `task.addTag(tag)` — tag a task (works on tasks only)
- `task.removeTag(tag)` — untag a task
- `task.clearTags()` — remove all tags from task
- `tag.name = "New"` — rename tag (preserves associations)
- `parentTag.tags.push(tag)` — reparent tag (preserves associations)
- `app.delete(tag)` — delete tag (NOT tag.delete())

## Workarounds
- Projects are tasks internally: `doc.flattenedTasks.whose({id: project.id()})[0]`
- Use this workaround for addTag/removeTag on projects

## Lookup
- `doc.flattenedTags.whose({name: "..."})[0]` — find tag by exact name
- `doc.flattenedTags()` — all tags flattened
- `tag.tags()` — direct children of a tag
- `tag.flattenedTags()` — all descendants of a tag
- `tag.remainingTaskCount()` — tasks still open
- `tag.availableTaskCount()` — tasks available now
```

#### 1b. Smoke Tests for Tag Operations

Add tag operation tests to `test-queries.sh`:

```bash
# Phase 3: Tag operation tests
echo "=== Phase 3: Tag Operations ==="

# Test: Create tag, verify, rename, verify, delete
TEST_TAG_NAME="__smoke_test_tag_$(date +%s)"
# create
run_test "create-tag" "manage_omnifocus.js create --name '__smoke_task' --tags '$TEST_TAG_NAME' --create-tags"
# list and verify
run_test "list-tags" "manage_omnifocus.js list-tags"
# rename
run_test "rename-tag" "manage_omnifocus.js rename-tag --name '$TEST_TAG_NAME' --new-name '${TEST_TAG_NAME}_renamed'"
# delete task, then delete tag
run_test "cleanup" "manage_omnifocus.js delete --name '__smoke_task'"
run_test "delete-tag" "manage_omnifocus.js delete-tag --name '${TEST_TAG_NAME}_renamed'"
```

#### 1c. Constructor Validation Comment Block

Add a compliance comment at the top of `manage_omnifocus.js`:

```javascript
/**
 * JXA COMPLIANCE NOTES — READ BEFORE EDITING
 *
 * 1. Constructors: Use app.Tag(), app.Project(), app.Task()
 *    NEVER app.defaultDocument.Tag() — causes -1700 error
 *
 * 2. Tag operations on projects: Use flattenedTasks workaround
 *    NEVER project.addTag() — causes -1700 error
 *
 * 3. Deleting objects: Use app.delete(obj)
 *    NEVER obj.delete() for tags
 *
 * 4. whose() returns array-like: [0] may be undefined, not null
 *
 * See: scripts/libraries/jxa/JXA_API_REFERENCE.md
 */
```

### Phase 2: Tag Management Commands

Add four new commands to `manage_omnifocus.js` following the existing dispatch pattern.

#### 2a. `list-tags` (read-only)

```javascript
// In switch block:
case 'list-tags':
    result = listTags(app, args);
    break;

// Handler:
function listTags(app, args) {
    const doc = app.defaultDocument;
    function buildTree(tags, depth) {
        let results = [];
        for (const t of tags) {
            results.push({
                id: t.id(),
                name: t.name(),
                depth: depth,
                remainingTasks: t.remainingTaskCount(),
                availableTasks: t.availableTaskCount(),
                childCount: t.tags().length
            });
            if (t.tags().length > 0) {
                results = results.concat(buildTree(t.tags(), depth + 1));
            }
        }
        return results;
    }
    const tree = buildTree(doc.tags(), 0);
    return JSON.stringify({ success: true, action: 'list-tags', tagCount: tree.length, tags: tree });
}
```

**Args:** `--flat` (optional, returns flattenedTags instead of tree)

#### 2b. `rename-tag`

```javascript
function renameTag(app, args) {
    const doc = app.defaultDocument;
    const tag = doc.flattenedTags.whose({ name: args.name })[0];
    if (!tag) throw new Error('Tag not found: ' + args.name);
    const oldName = tag.name();
    tag.name = args['new-name'];
    return JSON.stringify({
        success: true, action: 'rename-tag',
        oldName: oldName, newName: args['new-name'],
        taskCount: tag.remainingTaskCount()
    });
}
```

**Args:** `--name` (required), `--new-name` (required)

#### 2c. `move-tag`

```javascript
function moveTag(app, args) {
    const doc = app.defaultDocument;
    const tag = doc.flattenedTags.whose({ name: args.name })[0];
    if (!tag) throw new Error('Tag not found: ' + args.name);

    if (args.parent) {
        // Move under existing parent (create if --create-tags)
        let parent = doc.flattenedTags.whose({ name: args.parent })[0];
        if (!parent && args['create-tags']) {
            parent = app.Tag({ name: args.parent });
            doc.tags.push(parent);
        }
        if (!parent) throw new Error('Parent tag not found: ' + args.parent);
        parent.tags.push(tag);
        return JSON.stringify({
            success: true, action: 'move-tag',
            tag: args.name, newParent: args.parent,
            taskCount: tag.remainingTaskCount()
        });
    } else if (args.root) {
        // Move to top level
        doc.tags.push(tag);
        return JSON.stringify({
            success: true, action: 'move-tag',
            tag: args.name, newParent: '(root)',
            taskCount: tag.remainingTaskCount()
        });
    } else {
        throw new Error('Must specify --parent <name> or --root');
    }
}
```

**Args:** `--name` (required), `--parent` (move under this tag), `--root` (move to top level), `--create-tags` (create parent if missing)

#### 2d. `delete-tag`

```javascript
function deleteTag(app, args) {
    const doc = app.defaultDocument;
    const tag = doc.flattenedTags.whose({ name: args.name })[0];
    if (!tag) throw new Error('Tag not found: ' + args.name);

    const remaining = tag.remainingTaskCount();
    if (remaining > 0 && !args.force) {
        throw new Error('Tag "' + args.name + '" has ' + remaining +
            ' remaining tasks. Use --force to delete anyway.');
    }

    const childCount = tag.tags().length;
    if (childCount > 0 && !args.force) {
        throw new Error('Tag "' + args.name + '" has ' + childCount +
            ' child tags. Use --force to delete anyway.');
    }

    app.delete(tag);
    return JSON.stringify({
        success: true, action: 'delete-tag',
        deleted: args.name,
        tasksAffected: remaining
    });
}
```

**Args:** `--name` (required), `--force` (delete even with tasks/children)

#### 2e. Argument Parser Updates

In `argParser.js`, add to boolean flags array:
- `flat`, `root`, `force`

#### 2f. Help Text Updates

Add to `printHelp()`:

```
Tag Management:
    list-tags    List all tags with hierarchy and task counts
    rename-tag   Rename a tag (preserves task associations)
    move-tag     Move a tag under a new parent or to root
    delete-tag   Delete a tag (fails if tasks remain unless --force)
```

### Phase 3: Validation and Testing

1. Run `validate-js-syntax.js` on all modified files
2. Run updated `test-queries.sh` with Phase 3 tag tests
3. Manual verification: create, rename, move, delete a test tag — confirm task associations preserved
4. Version bump to 6.1.0

## Acceptance Criteria

- [ ] JXA_API_REFERENCE.md exists and documents correct constructor/method patterns
- [ ] Compliance comment block at top of manage_omnifocus.js
- [ ] `list-tags` returns full hierarchy with task counts
- [ ] `rename-tag` renames without losing task associations
- [ ] `move-tag` reparents under new parent or to root without losing task associations
- [ ] `delete-tag` refuses to delete tags with tasks unless `--force`
- [ ] `delete-tag` refuses to delete tags with children unless `--force`
- [ ] Smoke tests cover tag create/rename/move/delete lifecycle
- [ ] `printHelp()` updated with new commands
- [ ] `argParser.js` updated with new boolean flags
- [ ] All files pass `validate-js-syntax.js`

## Dependencies & Risks

- **Risk:** `app.delete(tag)` behavior with child tags — need to verify if it cascades or orphans children. Test with a throwaway tag first.
- **Risk:** `parentTag.tags.push(tag)` for reparenting — need to verify this removes from old parent automatically or if explicit removal is needed.
- **Risk:** Tag name uniqueness — OmniFocus allows duplicate tag names at different levels. `flattenedTags.whose({name})` may match multiple. Consider `--id` flag as alternative identifier.
- **Dependency:** OmniFocus must be running with Automation permission for smoke tests.

## Files to Modify

- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/manage_omnifocus.js` — add 4 commands + compliance header
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/jxa/argParser.js` — add boolean flags
- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/test-queries.sh` — add Phase 3 tag tests
- `plugins/omnifocus-manager/skills/omnifocus-manager/IMPROVEMENT_PLAN.md` — update version history

## Files to Create

- `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/jxa/JXA_API_REFERENCE.md`

## Sources & References

- **Tagsonomy audit:** `[[OmniFocus Tagsonomy Report]]` in Obsidian vault
- **Existing patterns:** `manage_omnifocus.js:77-115` (command dispatch), `taskMutation.js:76-112` (nested tag creation)
- **Lessons learned:** `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` (release process failures, path validation)
- **Issue:** #76
