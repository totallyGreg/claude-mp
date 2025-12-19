# OmniFocus URL Scheme Reference

Complete reference for the `omnifocus://` URL scheme for automating OmniFocus tasks and actions.

## Base URL Format

```
omnifocus:///action?parameter1=value1&parameter2=value2
```

## Actions

### 1. Add Task (`add`)

Create a new task in OmniFocus.

**Basic Syntax:**
```
omnifocus:///add?name=Task Name
```

**Available Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `name` | string | Task name (required) | `Call John` |
| `note` | string | Task note/description | `Discuss project timeline` |
| `project` | string | Project name | `Work Projects` |
| `tags` | string | Comma-separated tag names | `phone,urgent` |
| `context` | string | Context name (legacy, use tags instead) | `phone` |
| `folder` | string | Folder name for the project | `Personal` |
| `due` | ISO8601 date | Due date | `2025-12-25` or `2025-12-25T14:00:00` |
| `defer` | ISO8601 date | Defer date (start date) | `2025-12-20` |
| `estimate` | duration | Time estimate | `30m`, `2h`, `1h30m` |
| `flagged` | boolean | Flag the task | `true` or `false` |
| `autosave` | boolean | Save without confirmation | `true` or `false` |
| `attach` | URL | Attach file or URL | File path or web URL |

**Examples:**

Simple inbox task:
```
omnifocus:///add?name=Buy%20groceries
```

Task with project and due date:
```
omnifocus:///add?name=Review%20proposal&project=Work&due=2025-12-25
```

Task with multiple tags and note:
```
omnifocus:///add?name=Call%20dentist&tags=phone,health&note=Schedule%20annual%20checkup
```

Flagged task with estimate:
```
omnifocus:///add?name=Write%20report&project=Work&flagged=true&estimate=2h
```

Task with attachment:
```
omnifocus:///add?name=Review%20document&attach=file:///Users/username/Documents/report.pdf
```

Complete task with all parameters:
```
omnifocus:///add?name=Project%20Review&project=Q4%20Planning&folder=Work&tags=meeting,important&due=2025-12-30T14:00:00&defer=2025-12-28&estimate=1h30m&flagged=true&note=Prepare%20slides%20and%20metrics&autosave=true
```

### 2. Open Perspective (`perspective`)

Open a specific perspective.

**Syntax:**
```
omnifocus:///perspective?name=Perspective Name
```

**Examples:**

```
omnifocus:///perspective?name=Forecast
omnifocus:///perspective?name=Flagged
omnifocus:///perspective?name=Projects
```

### 3. Search (`search`)

Perform a search in OmniFocus.

**Syntax:**
```
omnifocus:///search?q=search term
```

**Examples:**

```
omnifocus:///search?q=meeting
omnifocus:///search?q=project:Work
```

### 4. Show Item (`task` or `project`)

Open a specific task or project by ID.

**Syntax:**
```
omnifocus:///task/TASK_ID
omnifocus:///project/PROJECT_ID
```

The ID is the `persistentIdentifier` from the database.

**Examples:**

```
omnifocus:///task/abc123xyz
omnifocus:///project/proj456def
```

## URL Encoding

All parameter values must be URL-encoded. Common characters that need encoding:

| Character | Encoded As |
|-----------|------------|
| Space | `%20` or `+` |
| `&` | `%26` |
| `=` | `%3D` |
| `#` | `%23` |
| `/` | `%2F` |
| `?` | `%3F` |
| Newline | `%0A` |

**Python encoding example:**
```python
from urllib.parse import quote

task_name = "Review Q4 Report & Metrics"
encoded = quote(task_name)  # "Review%20Q4%20Report%20%26%20Metrics"
```

## Date Formats

OmniFocus accepts dates in ISO 8601 format:

- Date only: `YYYY-MM-DD` (e.g., `2025-12-25`)
- Date and time: `YYYY-MM-DDTHH:MM:SS` (e.g., `2025-12-25T14:30:00`)
- With timezone: `YYYY-MM-DDTHH:MM:SS±HH:MM` (e.g., `2025-12-25T14:30:00-08:00`)

**Examples:**

```
omnifocus:///add?name=Meeting&due=2025-12-25
omnifocus:///add?name=Call&due=2025-12-25T10:00:00
omnifocus:///add?name=Deadline&due=2025-12-31T17:00:00-05:00
```

## Time Estimates

Format: `<number><unit>` where unit is `m` (minutes) or `h` (hours)

**Examples:**

- `30m` = 30 minutes
- `2h` = 2 hours
- `1h30m` = 1 hour 30 minutes
- `90m` = 90 minutes (equivalent to 1h30m)

## Best Practices

### 1. Use Autosave for Automated Workflows

When creating tasks programmatically, use `autosave=true` to skip confirmation:

```
omnifocus:///add?name=Auto%20Task&autosave=true
```

### 2. Provide Context with Notes

Include notes to provide context, especially for auto-generated tasks:

```
omnifocus:///add?name=Follow%20up&note=Generated%20from%20conversation%20with%20Claude%20on%202025-12-19
```

### 3. Use Tags for Organization

Tags (formerly contexts) help organize and filter tasks:

```
omnifocus:///add?name=Email%20team&tags=computer,work,communication
```

### 4. Set Defer Dates for Future Tasks

Use defer dates to prevent tasks from cluttering your view until needed:

```
omnifocus:///add?name=Monthly%20review&defer=2025-12-31&due=2026-01-05
```

### 5. Combine with Database Queries

Use the query script to check existing tasks before creating duplicates:

```bash
# Check if task already exists
python3 scripts/query_omnifocus.py --search "Monthly review"

# Then create if needed
open "omnifocus:///add?name=Monthly%20review&project=Admin"
```

## Common Patterns

### Quick Inbox Capture
```
omnifocus:///add?name=Task%20Name&autosave=true
```

### Work Task with Context
```
omnifocus:///add?name=Task%20Name&project=Work%20Project&tags=computer,office&due=2025-12-30
```

### Flagged High-Priority Task
```
omnifocus:///add?name=Urgent%20Task&flagged=true&due=2025-12-25&tags=urgent
```

### Task with Detailed Note
```
omnifocus:///add?name=Research%20Topic&note=Key%20points%3A%0A-%20Point%201%0A-%20Point%202%0A-%20Point%203&project=Learning
```

### Recurring Task Setup
For recurring tasks, create the first instance and set recurrence manually in OmniFocus:
```
omnifocus:///add?name=Weekly%20Review&project=Admin&due=2025-12-22T09:00:00&note=Set%20to%20repeat%20weekly
```

## Limitations

1. **Cannot modify existing tasks**: The URL scheme can only create new tasks, not edit existing ones
2. **Cannot delete tasks**: Use AppleScript or the OmniFocus UI for deletions
3. **Cannot set repeat rules**: Repeat/recurrence must be set in the OmniFocus UI
4. **Limited project/folder creation**: Projects and folders must already exist
5. **No bulk operations**: Each URL creates one task only

## Troubleshooting

### URLs Not Working

1. **Check URL encoding**: Ensure all special characters are properly encoded
2. **Verify parameter names**: Parameter names are case-sensitive
3. **Test in browser**: Try opening the URL in Safari/browser first
4. **Check OmniFocus is installed**: URL scheme requires OmniFocus to be installed
5. **Use autosave=false for testing**: See the preview dialog to catch errors

### Tasks Not Appearing in Expected Location

1. **Verify project/folder names**: They must match exactly (case-sensitive)
2. **Check tags exist**: Unknown tags may be created automatically
3. **Review defer dates**: Tasks with future defer dates won't appear until that date

### Date Format Issues

1. **Use ISO 8601**: Always use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
2. **Include timezone if needed**: Add `±HH:MM` suffix for timezone-specific times
3. **Avoid relative dates**: URL scheme doesn't support "tomorrow" or "+3d"

## Advanced Usage

### Creating Task Hierarchies

Create parent task first, then reference it:
```
# Create project/parent task
omnifocus:///add?name=Big%20Project&note=Parent%20task

# Create subtasks with the same project
omnifocus:///add?name=Subtask%201&project=Big%20Project
omnifocus:///add?name=Subtask%202&project=Big%20Project
```

### Integration with Shell Scripts

```bash
#!/bin/bash
# Create OmniFocus task from shell

TASK_NAME="My Task"
PROJECT="Work"
DUE_DATE="2025-12-25"

# URL encode and open
ENCODED_NAME=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$TASK_NAME'))")
open "omnifocus:///add?name=$ENCODED_NAME&project=$PROJECT&due=$DUE_DATE&autosave=true"
```

### Keyboard Maestro Integration

Use Keyboard Maestro to create custom shortcuts:
```applescript
set theURL to "omnifocus:///add?name=Quick%20Task&autosave=true"
open location theURL
```

## Resources

- [OmniFocus URL Schemes Documentation](https://support.omnigroup.com/omnifocus-url-schemes/)
- [OmniFocus AppleScript Documentation](https://support.omnigroup.com/omnifocus-applescript/)
- [Automation with OmniFocus](https://www.omnigroup.com/blog/tags/automation)

## Version Compatibility

This reference covers:
- OmniFocus 3 for Mac
- OmniFocus 4 for Mac
- OmniFocus for iOS (most parameters supported)

Note: Some parameters may vary between versions. Test with your specific OmniFocus version.
