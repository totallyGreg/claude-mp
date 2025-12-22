# JXA Command Reference

Complete reference for `scripts/manage_omnifocus.js` - JavaScript for Automation commands for querying and managing OmniFocus tasks.

## Overview

The JXA script provides full access to the OmniFocus AppleScript API, enabling both queries and task management operations.

**Script location:** `scripts/manage_omnifocus.js`

**Execution:** All commands use `osascript -l JavaScript`

**Output:** JSON format for all operations

## Query Commands

### Today's Tasks

Shows tasks due today or deferred until today.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

**Use when:** User asks "what's on my agenda?" or "what should I do today?"

**Output:** JSON with task details (name, project, due date, tags, etc.)

### List Active Tasks

Returns all incomplete tasks that are available to work on (not blocked or deferred to future).

```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active
```

**Filters:** `active`, `completed`, `dropped`, `all`

**Examples:**
```bash
# Active tasks only (default)
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active

# All tasks including completed
osascript -l JavaScript scripts/manage_omnifocus.js list --filter all

# Completed tasks only
osascript -l JavaScript scripts/manage_omnifocus.js list --filter completed

# Dropped tasks only
osascript -l JavaScript scripts/manage_omnifocus.js list --filter dropped
```

### Tasks Due Soon

Shows tasks due within the next N days (default: 7).

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

**Use when:** User asks "what's due this week?" or "what's coming up?"

**Examples:**
```bash
# Next 7 days (default)
osascript -l JavaScript scripts/manage_omnifocus.js due-soon

# Next 3 days
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 3

# Next 30 days
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 30
```

### Flagged Tasks

Lists all flagged tasks.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

**Use when:** User asks about priorities or important items.

### Search for Tasks

Searches task names and notes for the specified term.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Use when:** User asks "find tasks about X" or "what meetings do I have?"

**Examples:**
```bash
# Search for "meeting"
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"

# Search for "project review"
osascript -l JavaScript scripts/manage_omnifocus.js search --query "project review"
```

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

**Processing output with jq:**
```bash
# Get just task names
osascript -l JavaScript scripts/manage_omnifocus.js today | jq '.tasks[] | .name'

# Get tasks with due dates
osascript -l JavaScript scripts/manage_omnifocus.js due-soon | jq '.tasks[] | {name, dueDate}'

# Count flagged tasks
osascript -l JavaScript scripts/manage_omnifocus.js flagged | jq '.count'
```

## Task Management Commands

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

**Date format:** ISO 8601: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`

**Examples:**
```bash
# Date only
--due "2025-12-25"

# Date and time
--due "2025-12-25T14:00:00"

# With timezone
--due "2025-12-25T14:00:00-08:00"
```

#### Task with Tags

```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Call client" \
  --tags "phone,urgent"
```

Comma-separated tag list. Add `--create-tags` to auto-create missing tags:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Call client" \
  --tags "phone,urgent" \
  --create-tags
```

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

**Format:** `30m`, `2h`, or `1h30m`

**Examples:**
```bash
--estimate "30m"      # 30 minutes
--estimate "2h"       # 2 hours
--estimate "1h30m"    # 1 hour 30 minutes
--estimate "90m"      # 90 minutes (same as 1h30m)
```

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

**Clear due date:**
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

**Move to inbox:**
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

**Clear all tags:**
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

**Use ID for duplicate names:**
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

**Returns JSON with:**
- Task ID
- Name, note
- Completion status
- Due and defer dates
- Flag status
- Time estimate
- Project
- Tags

**Use when:**
- Checking task details before updating
- Getting task ID for operations requiring unique identification
- Verifying task existence

### Handling Duplicate Task Names

If multiple tasks share the same name, the script will return an error listing all matching tasks with their IDs and projects:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Meeting"
```

**Output:**
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

**Then use the specific ID:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js update --id "abc123" --due "2025-12-31"
```

## Important Notes

### JXA Requirements

- **Mac only:** Uses AppleScript bridge
- **Requires OmniFocus:** OmniFocus must be installed and accessible
- **Permissions:** May require granting Terminal automation permissions
- **Case-sensitive:** Project, folder, and tag names are case-sensitive
- **Real-time:** Changes are immediate and permanent
- **No undo:** Deletions cannot be reversed (consider completing instead)
- **Both read and write:** Can query and modify tasks

### Date Formats

Always use ISO 8601 format:
- Date only: `2025-12-25`
- Date and time: `2025-12-25T14:30:00`
- With timezone: `2025-12-25T14:30:00-08:00`

### Permissions

First time running these scripts may prompt for permissions:

**Automation Permission (required for JXA):**
- System Preferences → Security & Privacy → Privacy → Automation
- Allow Terminal to control OmniFocus

## Getting Help

All commands include built-in help:

```bash
osascript -l JavaScript scripts/manage_omnifocus.js help
```

## Examples

### Check task details before updating
```bash
# Get task info
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Meeting"

# Update the task
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --id "abc123" \
  --due "2025-12-31"
```

### Create task in new project with tags
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "New feature implementation" \
  --project "Q1 Development" \
  --tags "coding,high-priority" \
  --due "2026-01-15" \
  --estimate "8h" \
  --create-project \
  --create-tags
```

### Complete multiple tasks
```bash
# Get today's tasks
osascript -l JavaScript scripts/manage_omnifocus.js today > tasks.json

# Complete each one (requires parsing JSON and looping)
cat tasks.json | jq -r '.tasks[] | .id' | while read id; do
  osascript -l JavaScript scripts/manage_omnifocus.js complete --id "$id"
done
```
