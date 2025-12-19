---
name: omnifocus-manager
description: Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA). Use this skill when working with OmniFocus data, creating or modifying tasks, analyzing task lists, searching for tasks, or automating OmniFocus workflows. Trigger when user mentions OmniFocus, tasks, projects, GTD workflows, or asks to create, update, search, or analyze their task data.
version: 1.0.0
---

# OmniFocus Manager

## Overview

Enables comprehensive OmniFocus integration through two complementary approaches:

1. **Database Queries (Python)** - Read-only access for searching, analyzing, and reporting on OmniFocus data
2. **Task Management (JavaScript/JXA)** - Full CRUD operations to create, update, complete, and delete tasks

This hybrid approach provides both the power of direct database access for complex queries and the flexibility of the OmniFocus AppleScript API for task management.

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

1. **Is the user querying/reading data?**
   - Finding tasks, searching, analyzing → Use `query_omnifocus.py` (Python)
   - Generating reports, statistics → Use `query_omnifocus.py` (Python)

2. **Is the user creating/modifying data?**
   - Creating new tasks → Use `manage_omnifocus.js` (JXA)
   - Updating existing tasks → Use `manage_omnifocus.js` (JXA)
   - Completing tasks → Use `manage_omnifocus.js` (JXA)
   - Deleting tasks → Use `manage_omnifocus.js` (JXA)

## Querying OmniFocus Data

Use `scripts/query_omnifocus.py` for all read-only operations.

### Database Access

The Python script provides safe, read-only access to the OmniFocus SQLite database with automatic detection of OmniFocus 3 and 4 installations.

**Script location:** `scripts/query_omnifocus.py`

### Common Query Patterns

#### List Active Tasks
```bash
python3 scripts/query_omnifocus.py --tasks --filter active
```

Returns all incomplete tasks that are available to work on (not blocked or deferred to future).

#### Search for Tasks
```bash
python3 scripts/query_omnifocus.py --search "meeting"
```

Searches task names and notes for the specified term. Useful when user asks "find tasks about X" or "what meetings do I have?"

#### Tasks Due Soon
```bash
python3 scripts/query_omnifocus.py --due-soon --days 7
```

Shows tasks due within the next N days (default: 7). Perfect for "what's due this week?" queries.

#### Today's Tasks
```bash
python3 scripts/query_omnifocus.py --today
```

Shows tasks due today or deferred until today. Use when user asks "what's on my agenda?" or "what should I do today?"

#### Flagged Tasks
```bash
python3 scripts/query_omnifocus.py --flagged
```

Lists all flagged tasks. Use when user asks about priorities or important items.

#### List Projects
```bash
python3 scripts/query_omnifocus.py --projects
```

Shows all active projects with task counts. Can filter by folder:
```bash
python3 scripts/query_omnifocus.py --projects --folder "Work"
```

#### List Tags
```bash
python3 scripts/query_omnifocus.py --tags
```

Shows all available tags with task counts.

### Output Formats

**Human-readable (default):**
```bash
python3 scripts/query_omnifocus.py --tasks --filter active
```

**JSON output (for parsing/analysis):**
```bash
python3 scripts/query_omnifocus.py --tasks --filter active --json
```

Use JSON output when programmatically processing results or creating reports.

### Advanced Queries

For complex analysis, use custom SQL queries:

```bash
python3 scripts/query_omnifocus.py --custom-query "SELECT name, dateDue FROM Task WHERE flagged = 1"
```

Common custom query use cases:
- Counting tasks by project
- Finding overdue tasks
- Analyzing completion rates
- Custom filtering and grouping

**Note:** Custom queries require knowledge of the OmniFocus database schema. Key tables include `Task`, `ProjectInfo`, `Folder`, and `Context`.

### Database Location

The script auto-detects the OmniFocus database. If auto-detection fails, specify manually:

```bash
python3 scripts/query_omnifocus.py --tasks --db-path "/path/to/OmniFocus.sqlite"
```

Typical locations:
- OmniFocus 4: `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/com.omnigroup.OmniFocus4.MacOSX/OmniFocus.ofocus/OmniFocus.sqlite`
- OmniFocus 3: `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/com.omnigroup.OmniFocus3.MacOSX/OmniFocus.ofocus/OmniFocus.sqlite`

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

```bash
python3 scripts/query_omnifocus.py --today
```

Follow up with flagged tasks if today's list is empty:
```bash
python3 scripts/query_omnifocus.py --flagged
```

### "Create a task for X"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task from conversation" \
  --note "Generated from discussion with Claude on $(date +%Y-%m-%d)"
```

### "What's due this week?"

```bash
python3 scripts/query_omnifocus.py --due-soon --days 7
```

### "Find all tasks related to X project"

```bash
python3 scripts/query_omnifocus.py --search "X project"
```

Or query by project:
```bash
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT name, dateDue FROM Task WHERE containingProjectInfo IN (SELECT pk FROM ProjectInfo WHERE name LIKE '%X project%')"
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

### Database Access (Python)

- **Read-only:** The Python script never modifies the database
- **Safe:** Querying while OmniFocus is running is safe
- **Auto-detection:** Automatically finds OmniFocus 3 or 4 database
- **Permissions:** May require granting Terminal full disk access in System Preferences

### JXA Task Management (JavaScript)

- **Requires OmniFocus:** OmniFocus must be installed and accessible
- **Permissions:** May require granting Terminal automation permissions
- **Case-sensitive:** Project, folder, and tag names are case-sensitive
- **Real-time:** Changes are immediate and permanent
- **No undo:** Deletions cannot be reversed (consider completing instead)

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

For detailed information about the omnifocus:// URL scheme (legacy approach, now superseded by JXA for most use cases):

**See:** `references/omnifocus_url_scheme.md`

The URL scheme reference is maintained for compatibility and special cases, but JXA is preferred for task management.

## Resources

### scripts/

- **query_omnifocus.py** - Database query tool (Python)
  - Auto-detects OmniFocus database
  - Supports multiple query types and custom SQL
  - JSON and human-readable output

- **manage_omnifocus.js** - Task management tool (JXA)
  - Create, update, complete, delete tasks
  - Full access to OmniFocus AppleScript API
  - JSON output for all operations

Both scripts include built-in help:
```bash
python3 scripts/query_omnifocus.py --help
osascript -l JavaScript scripts/manage_omnifocus.js help
```

### references/

- **omnifocus_url_scheme.md** - Complete omnifocus:// URL scheme reference
  - All URL parameters and syntax
  - Examples for common patterns
  - URL encoding guidelines
  - Limitations and troubleshooting

Consult when dealing with URL scheme integrations or web-based automation.
