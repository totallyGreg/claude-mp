# OmniFocus Workflows

Common workflows and use case patterns for working with OmniFocus automation.

## Overview

This guide provides end-to-end workflows combining query and management operations for common OmniFocus tasks.

## Daily Planning Workflows

### "What should I work on today?"

**Approach 1: JXA (Recommended for Mac)**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

**Approach 2: Omni Automation (Cross-platform)**
- Install and run the Today's Tasks plug-in from `examples/TodaysTasks.omnifocusjs`
- Or use the Omni Automation console with the script from `references/omni_automation.md`

**Follow-up:** If today's list is empty, check flagged tasks:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

### Morning Planning Routine

```bash
# 1. Check today's tasks
osascript -l JavaScript scripts/manage_omnifocus.js today > today.json

# 2. Check what's due soon
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 3

# 3. Review flagged priorities
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

## Task Creation Workflows

### "Create a task for X"

**Quick capture (URL Scheme - fastest, cross-platform):**
```bash
open "omnifocus:///add?name=Task%20from%20conversation&note=Generated%20by%20Claude&autosave=true"
```

**With more control (JXA):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task from conversation" \
  --note "Generated from discussion with Claude on $(date +%Y-%m-%d)"
```

**With full details:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "New feature request" \
  --project "Development" \
  --tags "feature,backlog" \
  --note "User requested feature X with requirements Y" \
  --estimate "4h"
```

### Create Task from Email/Note

```bash
# Extract details and create task
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Follow up: Meeting with John" \
  --project "Work" \
  --tags "email,follow-up" \
  --due "2025-12-25" \
  --note "Key points from email:
- Discuss Q4 roadmap
- Review budget proposal
- Schedule team meeting"
```

## Review Workflows

### Weekly Review

**1. Review inbox:**
```bash
# Get inbox tasks
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.project == null or .project == "")'
```

**2. Review projects:**
```bash
# Search for stalled projects (requires custom query)
python3 scripts/query_omnifocus.py --projects
```

**3. Review upcoming:**
```bash
# What's due in the next 7 days
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

**4. Review waiting for:**
```bash
# Search for "waiting" tagged tasks
osascript -l JavaScript scripts/manage_omnifocus.js search --query "waiting"
```

### Monthly Review

```bash
# 1. Completed tasks this month
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT name, project FROM Task
   WHERE dateCompleted >= strftime('%s', 'now', 'start of month')
   AND dateCompleted < strftime('%s', 'now')"

# 2. Projects with no activity
python3 scripts/query_omnifocus.py --projects

# 3. Create next month's recurring tasks
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Monthly Review - $(date -v+1m +%B)" \
  --project "Admin" \
  --due "$(date -v+1m -v1d +%Y-%m-%d)" \
  --tags "review,monthly"
```

## Project Management Workflows

### "What's due this week?"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

**Format output:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7 | \
  jq -r '.tasks[] | "[\(.dueDate)] \(.name) (\(.project // "Inbox"))"'
```

### "Find all tasks related to X project"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "X project"
```

**Or filter by project:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.project == "X project")'
```

## Task Maintenance Workflows

### "Mark task Y as complete"

**By name:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Y"
```

**By ID (for duplicates):**
```bash
# Find task ID first
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Y"

# Complete using ID
osascript -l JavaScript scripts/manage_omnifocus.js complete --id "abc123"
```

### "Change the due date for task Z"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Z" \
  --due "2025-12-31"
```

### Reschedule overdue tasks

```bash
# 1. Find overdue tasks
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT persistentIdentifier, name, dateDue FROM Task
   WHERE dateDue < strftime('%s', 'now')
   AND dateCompleted IS NULL"

# 2. Update each task (requires ID from step 1)
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --id "task-id" \
  --due "2025-12-31"
```

## Combined Read/Write Workflows

### Check Before Creating

Avoid creating duplicate tasks by checking first:

```bash
# Search for existing task
osascript -l JavaScript scripts/manage_omnifocus.js search --query "Monthly review"

# If not found, create it
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Monthly review" \
  --project "Admin" \
  --due "2026-01-05"
```

### Update Based on Query Results

Find tasks, then update them:

```bash
# Find flagged tasks
osascript -l JavaScript scripts/manage_omnifocus.js flagged > flagged.json

# Parse results and update specific tasks
cat flagged.json | jq -r '.tasks[] | .id' | while read id; do
  osascript -l JavaScript scripts/manage_omnifocus.js update \
    --id "$id" \
    --due "2025-12-31"
done
```

### Complete Batch of Tasks

```bash
# Find tasks matching criteria
osascript -l JavaScript scripts/manage_omnifocus.js search --query "old-project" > tasks.json

# Complete them all
cat tasks.json | jq -r '.tasks[] | .id' | while read id; do
  osascript -l JavaScript scripts/manage_omnifocus.js complete --id "$id"
done
```

### Generate Report and Create Follow-ups

```bash
# Get project statistics
python3 scripts/query_omnifocus.py --projects --json > projects.json

# Analyze in Python or jq, then create tasks for projects needing attention
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Review project X" \
  --tags "review,weekly" \
  --note "Project has 15 tasks with no recent activity"
```

## Context-Based Workflows

### Work from specific context/location

```bash
# Find tasks by tag
osascript -l JavaScript scripts/manage_omnifocus.js search --query "@office"

# Or use database query for tag-based filtering
python3 scripts/query_omnifocus.py --tags
```

### Energy-based task selection

```bash
# High energy: Find complex tasks
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.estimatedMinutes >= 60)'

# Low energy: Find quick tasks
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.estimatedMinutes <= 30)'
```

## Automation Integration Workflows

### Shell Script Integration

```bash
#!/bin/bash
# Daily planning script

echo "=== Today's Tasks ==="
osascript -l JavaScript scripts/manage_omnifocus.js today | \
  jq -r '.tasks[] | "• \(.name) (\(.project // "Inbox"))"'

echo ""
echo "=== Due This Week ==="
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7 | \
  jq -r '.tasks[] | "• \(.name) - Due: \(.dueDate)"'
```

### cron/launchd Automation

```bash
# Add to crontab for daily morning summary
0 9 * * * osascript -l JavaScript /path/to/scripts/manage_omnifocus.js today | \
  mail -s "Today's Tasks" user@example.com
```

### Keyboard Maestro Integration

**Create task from clipboard:**
```applescript
set taskName to the clipboard
do shell script "osascript -l JavaScript scripts/manage_omnifocus.js create --name " & quoted form of taskName
```

### Alfred Workflow

**Quick capture:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "{query}" \
  --autosave
```

## Migration and Bulk Operations

### Import tasks from file

```bash
# Read tasks from CSV/JSON and create them
cat tasks.csv | while IFS=',' read name project due; do
  osascript -l JavaScript scripts/manage_omnifocus.js create \
    --name "$name" \
    --project "$project" \
    --due "$due"
done
```

### Bulk tag addition

```bash
# Add tag to all tasks in a project
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq -r '.tasks[] | select(.project == "Marketing") | .id' | \
  while read id; do
    osascript -l JavaScript scripts/manage_omnifocus.js update \
      --id "$id" \
      --tags "marketing,active"
  done
```

### Archive completed tasks

```bash
# Get completed tasks from last month
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT name, project, dateCompleted FROM Task
   WHERE dateCompleted >= strftime('%s', 'now', '-1 month', 'start of month')
   AND dateCompleted < strftime('%s', 'now', 'start of month')" \
  --json > completed_last_month.json
```

## Best Practices

### Always validate before bulk operations

```bash
# Preview what will be affected
osascript -l JavaScript scripts/manage_omnifocus.js search --query "old" | \
  jq '.tasks | length'

# Confirm count looks right, then proceed with bulk operation
```

### Use IDs for reliability

```bash
# Get ID first
TASK_ID=$(osascript -l JavaScript scripts/manage_omnifocus.js info --name "Important Task" | \
  jq -r '.task.id')

# Use ID for subsequent operations
osascript -l JavaScript scripts/manage_omnifocus.js update --id "$TASK_ID" --flagged
```

### Combine approaches for best results

- **Quick capture:** URL scheme (fastest)
- **Detailed creation:** JXA (full control)
- **Complex queries:** Python database queries (SQL power)
- **Cross-platform:** Omni Automation (Mac + iOS)

### Error handling in scripts

```bash
# Check for success before continuing
RESULT=$(osascript -l JavaScript scripts/manage_omnifocus.js create --name "Test")
if echo "$RESULT" | jq -e '.success' > /dev/null; then
  echo "Task created successfully"
else
  echo "Error creating task: $(echo "$RESULT" | jq -r '.error')"
fi
```
