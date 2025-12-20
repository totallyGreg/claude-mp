---
name: omnifocus-manager
description: Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA). Use this skill when working with OmniFocus data, creating or modifying tasks, analyzing task lists, searching for tasks, or automating OmniFocus workflows. Trigger when user mentions OmniFocus, tasks, projects, GTD workflows, or asks to create, update, search, or analyze their task data.
version: 1.0.0
---

# OmniFocus Manager

## Overview

Enables comprehensive OmniFocus integration through four complementary approaches, listed in order of preference:

1. **Omni Automation (JavaScript)** - Native, cross-platform automation within OmniFocus (Mac + iOS)
2. **JXA (JavaScript for Automation)** - Full query and management capabilities via OmniFocus AppleScript API (Mac only)
3. **URL Scheme** - Simple task creation via omnifocus:// URLs (Mac + iOS)
4. **Database Queries (Python)** - Read-only database access (Mac only, requires permissions)

This multi-approach strategy provides security, cross-platform support, and comprehensive automation capabilities.

## When to Use This Skill

- User asks to query, search, or analyze their OmniFocus database
- User wants to create, update, or delete OmniFocus tasks
- User requests task reports, insights, or statistics
- User mentions OmniFocus, tasks, projects, contexts, tags, or GTD workflows
- User asks what tasks are due soon, flagged, or scheduled for today
- User wants to find specific tasks or projects
- User wants to complete or modify existing tasks

## Quick Start

**Decision Tree:**

1. **Does the user need cross-platform support (iOS/Mac)?**
   - YES → Use Omni Automation (plug-ins or scripts)
   - NO → Continue to step 2

2. **Is this a reusable automation task?**
   - YES → Create an Omni Automation plug-in
   - NO → Continue to step 3

3. **Is the user querying/reading data?**
   - Finding tasks, searching, analyzing → Use `manage_omnifocus.js` query commands (JXA)
   - Generating reports, statistics → Use `manage_omnifocus.js` query commands (JXA)
   - Alternative: Use Omni Automation scripts for cross-platform compatibility

4. **Is the user creating/modifying data?**
   - Simple task creation → Use omnifocus:// URL scheme (fastest, cross-platform)
   - Complex task creation/updates → Use `manage_omnifocus.js` create/update commands (JXA)
   - Alternative: Use Omni Automation for cross-platform or plug-in-based automation

5. **Last resort: Database queries**
   - ONLY use `query_omnifocus.py` (Python) if JXA or Omni Automation cannot accomplish the task
   - Requires full disk access permissions
   - Read-only, Mac-only

## Omni Automation (Recommended)

Omni Automation is OmniFocus's modern, cross-platform automation framework. It's the preferred approach for most automation tasks.

### Why Omni Automation?

- **Cross-platform:** Works on both Mac and iOS/iPadOS
- **Secure:** No file system permissions required
- **Native:** Runs directly within OmniFocus
- **Reusable:** Create plug-ins that can be shared and reused
- **Well-documented:** Comprehensive API and examples

### Quick Examples

**Query Today's Tasks:**
```javascript
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const tasks = doc.flattenedTasks();
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    return tasks.filter(t =>
        !t.completed() &&
        t.dueDate() >= today &&
        t.dueDate() < tomorrow
    ).map(t => t.name());
})();
```

**Create a Task:**
```javascript
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const task = new Task("Buy groceries");
    task.dueDate = new Date("2025-12-25");
    task.flagged = true;
    doc.inboxTasks.push(task);
    return "Created: " + task.name();
})();
```

### Installing Example Plug-Ins

The skill includes example plug-ins in the `examples/` directory:

1. **Today's Tasks** - Shows tasks due or deferred to today
   - Double-click `examples/TodaysTasks.omnifocusjs` to install
   - Access via Tools → Today's Tasks

For more examples and complete documentation, see:
- **Reference:** `references/omni_automation.md`
- **Examples:** `examples/README.md`
- **Official Docs:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)

## Querying OmniFocus Data (JXA)

Use `scripts/manage_omnifocus.js` for querying tasks on Mac via JXA (JavaScript for Automation).

**Script location:** `scripts/manage_omnifocus.js`

### Why JXA for Queries?

- **Secure:** Uses OmniFocus AppleScript API (no file system permissions required)
- **Complete:** Access to all task properties and metadata
- **Fast:** Direct API access without database parsing
- **Reliable:** Works across OmniFocus 3 and 4 without path detection issues

### Common Query Commands

#### Today's Tasks
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

Shows tasks due today or deferred until today. Use when user asks "what's on my agenda?" or "what should I do today?"

**Output:** JSON with task details (name, project, due date, tags, etc.)

#### List Active Tasks
```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active
```

Returns all incomplete tasks that are available to work on (not blocked or deferred to future).

**Filters:** `active`, `completed`, `dropped`, `all`

#### Tasks Due Soon
```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

Shows tasks due within the next N days (default: 7). Perfect for "what's due this week?" queries.

#### Flagged Tasks
```bash
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

Lists all flagged tasks. Use when user asks about priorities or important items.

#### Search for Tasks
```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

Searches task names and notes for the specified term. Useful when user asks "find tasks about X" or "what meetings do I have?"

### Output Format

All query commands return JSON output:

```json
{
  "success": true,
  "count": 3,
  "tasks": [
    {
      "id": "abc123",
      "name": "Task name",
      "project": "Project name",
      "dueDate": "2025-12-20T17:00:00.000Z",
      "flagged": false,
      "tags": ["tag1", "tag2"],
      "note": "Task notes"
    }
  ]
}
```

Use `jq` or JSON parsing tools to format or filter the output:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js today | jq '.tasks[] | .name'
```

## Managing OmniFocus Tasks

Use `scripts/manage_omnifocus.js` for creating, updating, completing, and deleting tasks.

### JavaScript for Automation (JXA)

The JXA script provides full access to the OmniFocus AppleScript API, enabling operations that are impossible with database queries or URL schemes.

**Script location:** `scripts/manage_omnifocus.js`

**Execution:** All JXA commands use `osascript -l JavaScript`

### Creating Tasks

#### Simple Inbox Task
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create --name "Call dentist"
```

Creates a task in the inbox with just a name.

#### Task with Project
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Review proposal" \
  --project "Work"
```

Adds task to an existing project. If project doesn't exist, add `--create-project` flag:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "New task" \
  --project "New Project" \
  --create-project
```

#### Task with Due Date
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Submit report" \
  --due "2025-12-25"
```

Use ISO 8601 date format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`

#### Task with Tags
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Call client" \
  --tags "phone,urgent"
```

Comma-separated tag list. Add `--create-tags` to auto-create missing tags.

#### Flagged Task
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Important task" \
  --flagged
```

#### Task with Note
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Research topic" \
  --note "Key points to investigate: API design, performance, security"
```

#### Task with Time Estimate
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Write documentation" \
  --estimate "2h30m"
```

Format: `30m`, `2h`, or `1h30m`

#### Complete Task Creation Example
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Project kickoff meeting" \
  --project "Q4 Planning" \
  --tags "meeting,important" \
  --due "2025-12-30T14:00:00" \
  --defer "2025-12-28" \
  --estimate "1h30m" \
  --note "Prepare slides and metrics" \
  --flagged \
  --create-project \
  --create-tags
```

### Updating Tasks

Update tasks by name or ID. If multiple tasks share the same name, use `--id` instead of `--name`.

#### Update Task Name
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Old name" \
  --new-name "New name"
```

#### Update Due Date
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due "2025-12-31"
```

Clear due date:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due clear
```

#### Update Project
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project "Different Project"
```

Move to inbox:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project inbox
```

#### Update Tags
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --tags "new,tags,here"
```

Clear all tags:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --tags ""
```

#### Update Multiple Properties
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --new-name "Updated name" \
  --due "2025-12-31" \
  --flagged \
  --note "Updated note text"
```

### Completing Tasks

```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Task to complete"
```

Use `--id` for tasks with duplicate names:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --id "abc123xyz"
```

### Deleting Tasks

```bash
osascript -l JavaScript scripts/manage_omnifocus.js delete --name "Task to delete"
```

**Warning:** Deletion is permanent. Consider completing tasks instead when possible.

### Getting Task Information

Retrieve detailed information about a task:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Task name"
```

Returns JSON with:
- Task ID
- Name, note
- Completion status
- Due and defer dates
- Flag status
- Time estimate
- Project
- Tags

Useful for:
- Checking task details before updating
- Getting task ID for operations requiring unique identification
- Verifying task existence

### Handling Duplicate Task Names

If multiple tasks share the same name, the script will return an error listing all matching tasks with their IDs and projects:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Meeting"
```

Output:
```json
{
  "success": false,
  "error": "Multiple tasks found",
  "tasks": [
    { "id": "abc123", "name": "Meeting", "project": "Work" },
    { "id": "def456", "name": "Meeting", "project": "Personal" }
  ]
}
```

Then use the specific ID:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update --id "abc123" --due "2025-12-31"
```

## Combining Read and Write Operations

### Workflow: Check Before Creating

Before creating a task, check if it already exists:

```bash
# Search for existing task
python3 scripts/query_omnifocus.py --search "Monthly review"

# If not found, create it
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Monthly review" \
  --project "Admin" \
  --due "2026-01-05"
```

### Workflow: Update Based on Query Results

Find tasks, then update them:

```bash
# Find flagged tasks
python3 scripts/query_omnifocus.py --flagged --json > flagged.json

# Parse results and update specific tasks
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --id "task-id-from-json" \
  --due "2025-12-31"
```

### Workflow: Complete Overdue Tasks

```bash
# Find overdue tasks (custom query)
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT persistentIdentifier, name FROM Task WHERE dateDue < $(date +%s) AND dateCompleted IS NULL"

# Complete them
osascript -l JavaScript scripts/manage_omnifocus.js complete --id "task-id"
```

### Workflow: Generate Report and Create Follow-ups

```bash
# Get project statistics
python3 scripts/query_omnifocus.py --projects --json > projects.json

# Analyze in Python, then create tasks for projects needing attention
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Review project X" \
  --tags "review,weekly"
```

## Common Use Cases

### "What should I work on today?"

**JXA (Recommended):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

**Omni Automation (Cross-platform):**
- Install and run the Today's Tasks plug-in from `examples/TodaysTasks.omnifocusjs`
- Or use the Omni Automation console with the script from `references/omni_automation.md`

Follow up with flagged tasks if today's list is empty:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

### "Create a task for X"

**URL Scheme (Fastest, cross-platform):**
```bash
open "omnifocus:///add?name=Task%20from%20conversation&note=Generated%20by%20Claude&autosave=true"
```

**JXA (More control):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task from conversation" \
  --note "Generated from discussion with Claude on $(date +%Y-%m-%d)"
```

### "What's due this week?"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

### "Find all tasks related to X project"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "X project"
```

### "Mark task Y as complete"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Y"
```

### "Change the due date for task Z"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Z" \
  --due "2025-12-31"
```

## Important Notes

### Omni Automation

- **Cross-platform:** Works on Mac, iOS, and iPadOS
- **Secure:** No file system permissions required
- **Plug-ins:** Reusable automation that can be shared
- **Console:** Access via View → Automation → Console (⌃⌥⌘I)
- **Well-documented:** Comprehensive API at omni-automation.com

### JXA (JavaScript for Automation)

- **Mac only:** Uses AppleScript bridge
- **Requires OmniFocus:** OmniFocus must be installed and accessible
- **Permissions:** May require granting Terminal automation permissions
- **Case-sensitive:** Project, folder, and tag names are case-sensitive
- **Real-time:** Changes are immediate and permanent
- **No undo:** Deletions cannot be reversed (consider completing instead)
- **Both read and write:** Can query and modify tasks

### URL Scheme

- **Cross-platform:** Works on Mac and iOS
- **Simple:** Great for quick task creation
- **Limited:** Cannot query or modify existing tasks
- **No permissions:** No special permissions required
- **Autosave:** Use `autosave=true` for automated workflows

### Database Access (Python) - Last Resort

- **Use only when necessary:** JXA and Omni Automation should be preferred
- **Read-only:** The Python script never modifies the database
- **Permissions:** Requires granting Terminal full disk access
- **Mac only:** Not available on iOS
- **Path issues:** May fail to auto-detect database location
- **Security risk:** Direct file system access

### Date Formats

Always use ISO 8601 format:
- Date only: `2025-12-25`
- Date and time: `2025-12-25T14:30:00`
- With timezone: `2025-12-25T14:30:00-08:00`

### Permissions

First time running these scripts may prompt for permissions:

1. **Full Disk Access** (for Python database queries)
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add Terminal (or your terminal app)

2. **Automation** (for JXA task management)
   - System Preferences → Security & Privacy → Privacy → Automation
   - Allow Terminal to control OmniFocus

## Reference Documentation

The skill includes comprehensive documentation for all automation approaches:

### Primary References (Recommended First)

1. **`references/omni_automation.md`** - Complete Omni Automation guide
   - Cross-platform JavaScript API
   - Plug-in development
   - Code examples and patterns
   - Best practices

2. **`scripts/manage_omnifocus.js`** - JXA automation tool (Mac)
   - Query commands: today, list, due-soon, flagged, search
   - Task management: create, update, complete, delete
   - Full AppleScript API access
   - JSON output

3. **`references/omnifocus_url_scheme.md`** - URL scheme reference
   - Quick task creation
   - Cross-platform (Mac + iOS)
   - No permissions required
   - Cannot query existing tasks

### Secondary References

4. **`scripts/query_omnifocus.py`** - Database query tool (legacy)
   - Use only when JXA/Omni Automation cannot accomplish the task
   - Requires full disk access permissions
   - May have path detection issues

### Examples

- **`examples/TodaysTasks.omnifocusjs`** - Example Omni Automation plug-in
  - Install by double-clicking
  - Shows today's tasks grouped by project
  - Fully editable and customizable

- **`examples/README.md`** - Plug-in installation and development guide

## Resources

All scripts include built-in help:

```bash
# JXA help
osascript -l JavaScript scripts/manage_omnifocus.js help

# Python help (legacy)
python3 scripts/query_omnifocus.py --help
```

### External Resources

- **Omni Automation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **Omni Automation Tutorial:** [omni-automation.com/omnifocus/tutorial](https://omni-automation.com/omnifocus/tutorial/)
- **Omni Automation Plug-Ins:** [omni-automation.com/omnifocus/actions.html](https://omni-automation.com/omnifocus/actions.html)
- **OmniFocus URL Schemes:** [support.omnigroup.com/omnifocus-url-schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- **OmniFocus AppleScript:** [support.omnigroup.com/omnifocus-applescript](https://support.omnigroup.com/omnifocus-applescript/)
