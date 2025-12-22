# OmniFocus Database Schema Reference

Complete SQLite database schema documentation for OmniFocus 3 and 4, enabling custom queries for advanced analysis.

## Overview

OmniFocus stores all data in a SQLite database. This reference documents the schema to enable custom SQL queries for analytics and reporting.

**Database Location:**
- OmniFocus 4: `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Data/OmniFocus.ofocus/OmniFocus.sqlite`
- OmniFocus 3: `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus3/Data/OmniFocus.ofocus/OmniFocus.sqlite`

**Important:** Always use read-only access. Never modify the database directly.

## Core Tables

### Task Table

The main table containing all tasks and projects (projects are tasks with children).

**Key Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `persistentIdentifier` | TEXT | Unique ID for the task |
| `name` | TEXT | Task name |
| `note` | TEXT | Task note/description |
| `dateAdded` | REAL | When task was created (Unix timestamp) |
| `dateModified` | REAL | Last modification time |
| `dateCompleted` | REAL | When task was completed |
| `dateDue` | REAL | Due date |
| `dateDefer` | REAL | Defer/start date |
| `estimatedMinutes` | INTEGER | Time estimate in minutes |
| `flagged` | INTEGER | 1 if flagged, 0 otherwise |
| `blocked` | INTEGER | 1 if blocked, 0 otherwise |
| `next` | INTEGER | 1 if this is the next available task |
| `repetitionRule` | TEXT | Recurrence pattern |
| `containingProjectInfo` | TEXT | Parent project ID |
| `parent` | TEXT | Parent task ID (for subtasks) |
| `rank` | INTEGER | Sort order |
| `sequential` | INTEGER | 1 if children are sequential |
| `inInbox` | INTEGER | 1 if in inbox |
| `dropped` | INTEGER | 1 if dropped |

**Unix Timestamp Conversion:**

OmniFocus stores dates as Unix timestamps (seconds since 1970-01-01). Convert them:

```sql
-- To readable date
SELECT datetime(dateDue, 'unixepoch') as due_date FROM Task;

-- Compare with current time
SELECT * FROM Task WHERE dateDue < strftime('%s', 'now');

-- Date range
SELECT * FROM Task
WHERE dateDue >= strftime('%s', '2025-12-01')
  AND dateDue < strftime('%s', '2026-01-01');
```

### Tag Table

Contains all tags (formerly called "contexts").

| Column | Type | Description |
|--------|------|-------------|
| `persistentIdentifier` | TEXT | Unique ID |
| `name` | TEXT | Tag name |
| `active` | INTEGER | 1 if active, 0 if on hold/dropped |
| `parent` | TEXT | Parent tag ID (for nested tags) |
| `rank` | INTEGER | Sort order |
| `hidden` | INTEGER | 1 if hidden |

### Folder Table

Contains project folders.

| Column | Type | Description |
|--------|------|-------------|
| `persistentIdentifier` | TEXT | Unique ID |
| `name` | TEXT | Folder name |
| `active` | INTEGER | 1 if active |
| `parent` | TEXT | Parent folder ID (for nested folders) |
| `rank` | INTEGER | Sort order |

## Relationship Tables

### TaskTag Table

Many-to-many relationship between tasks and tags.

| Column | Type | Description |
|--------|------|-------------|
| `task` | TEXT | Task ID (foreign key to Task.persistentIdentifier) |
| `tag` | TEXT | Tag ID (foreign key to Tag.persistentIdentifier) |

## Common Queries

### Active Tasks

```sql
SELECT persistentIdentifier, name, dateDue
FROM Task
WHERE dateCompleted IS NULL
  AND dropped = 0
  AND blocked = 0
ORDER BY dateDue;
```

### Today's Tasks

```sql
SELECT name, dateDue
FROM Task
WHERE dateCompleted IS NULL
  AND dropped = 0
  AND (
    (dateDue >= strftime('%s', 'now', 'start of day')
     AND dateDue < strftime('%s', 'now', 'start of day', '+1 day'))
    OR
    (dateDefer >= strftime('%s', 'now', 'start of day')
     AND dateDefer < strftime('%s', 'now', 'start of day', '+1 day'))
  )
ORDER BY dateDue;
```

### Overdue Tasks

```sql
SELECT name, datetime(dateDue, 'unixepoch') as due_date
FROM Task
WHERE dateCompleted IS NULL
  AND dropped = 0
  AND dateDue < strftime('%s', 'now')
ORDER BY dateDue;
```

### Flagged Tasks

```sql
SELECT name, dateDue, containingProjectInfo
FROM Task
WHERE dateCompleted IS NULL
  AND flagged = 1
ORDER BY dateDue;
```

### Tasks by Tag

```sql
SELECT t.name, tag.name as tag_name
FROM Task t
JOIN TaskTag tt ON t.persistentIdentifier = tt.task
JOIN Tag tag ON tt.tag = tag.persistentIdentifier
WHERE t.dateCompleted IS NULL
  AND tag.name = 'urgent'
ORDER BY t.name;
```

### Tasks by Project

```sql
-- Get project tasks
SELECT t.name, t.dateDue
FROM Task t
WHERE t.containingProjectInfo = '[PROJECT_ID]'
  AND t.dateCompleted IS NULL
ORDER BY t.rank;
```

### Completed Tasks This Week

```sql
SELECT name, datetime(dateCompleted, 'unixepoch') as completed_date
FROM Task
WHERE dateCompleted >= strftime('%s', 'now', 'weekday 0', '-7 days')
  AND dateCompleted < strftime('%s', 'now')
ORDER BY dateCompleted DESC;
```

### Completed Tasks This Month

```sql
SELECT name, datetime(dateCompleted, 'unixepoch') as completed_date
FROM Task
WHERE dateCompleted >= strftime('%s', 'now', 'start of month')
  AND dateCompleted < strftime('%s', 'now', '+1 month', 'start of month')
ORDER BY dateCompleted DESC;
```

## Analytics Queries

### Task Completion Rate

```sql
SELECT
  COUNT(*) FILTER (WHERE dateCompleted IS NOT NULL) as completed,
  COUNT(*) FILTER (WHERE dateCompleted IS NULL AND dropped = 0) as remaining,
  COUNT(*) as total
FROM Task
WHERE inInbox = 0;  -- Exclude inbox
```

### Tasks by Tag Count

```sql
SELECT
  tag.name,
  COUNT(tt.task) as task_count
FROM Tag tag
LEFT JOIN TaskTag tt ON tag.persistentIdentifier = tt.tag
LEFT JOIN Task t ON tt.task = t.persistentIdentifier
WHERE t.dateCompleted IS NULL
  AND t.dropped = 0
GROUP BY tag.name
ORDER BY task_count DESC;
```

### Average Completion Time

```sql
SELECT
  AVG(dateCompleted - dateAdded) / 86400.0 as avg_days_to_complete
FROM Task
WHERE dateCompleted IS NOT NULL
  AND dateAdded IS NOT NULL;
```

### Tasks Due Soon by Project

```sql
SELECT
  containingProjectInfo,
  COUNT(*) as task_count,
  MIN(datetime(dateDue, 'unixepoch')) as earliest_due
FROM Task
WHERE dateCompleted IS NULL
  AND dropped = 0
  AND dateDue BETWEEN strftime('%s', 'now')
                  AND strftime('%s', 'now', '+7 days')
GROUP BY containingProjectInfo
ORDER BY earliest_due;
```

### Productivity Metrics

```sql
-- Tasks completed per day in last 30 days
SELECT
  date(dateCompleted, 'unixepoch') as completion_date,
  COUNT(*) as tasks_completed
FROM Task
WHERE dateCompleted >= strftime('%s', 'now', '-30 days')
GROUP BY completion_date
ORDER BY completion_date DESC;
```

### Estimate Accuracy

```sql
-- Compare estimates to actual completion time (requires tracking)
SELECT
  estimatedMinutes,
  AVG(dateCompleted - dateAdded) / 60.0 as avg_actual_minutes,
  COUNT(*) as count
FROM Task
WHERE dateCompleted IS NOT NULL
  AND estimatedMinutes IS NOT NULL
  AND estimatedMinutes > 0
GROUP BY estimatedMinutes
ORDER BY estimatedMinutes;
```

### Stalled Projects

```sql
-- Projects with no recent activity
SELECT
  persistentIdentifier,
  name,
  datetime(dateModified, 'unixepoch') as last_modified
FROM Task
WHERE inInbox = 0
  AND dateCompleted IS NULL
  AND dateModified < strftime('%s', 'now', '-30 days')
  AND (SELECT COUNT(*) FROM Task child
       WHERE child.parent = Task.persistentIdentifier) > 0
ORDER BY dateModified;
```

## Advanced Patterns

### Recursive Task Hierarchy

```sql
-- Get all subtasks recursively
WITH RECURSIVE subtasks AS (
  -- Base case: top-level task
  SELECT persistentIdentifier, name, parent, 0 as level
  FROM Task
  WHERE persistentIdentifier = '[TASK_ID]'

  UNION ALL

  -- Recursive case: children
  SELECT t.persistentIdentifier, t.name, t.parent, st.level + 1
  FROM Task t
  INNER JOIN subtasks st ON t.parent = st.persistentIdentifier
)
SELECT * FROM subtasks
ORDER BY level, name;
```

### Task Age Distribution

```sql
SELECT
  CASE
    WHEN (strftime('%s', 'now') - dateAdded) / 86400 < 7 THEN '< 1 week'
    WHEN (strftime('%s', 'now') - dateAdded) / 86400 < 30 THEN '1-4 weeks'
    WHEN (strftime('%s', 'now') - dateAdded) / 86400 < 90 THEN '1-3 months'
    ELSE '> 3 months'
  END as age_bracket,
  COUNT(*) as count
FROM Task
WHERE dateCompleted IS NULL
  AND dropped = 0
GROUP BY age_bracket;
```

### Tags with Most Overdue Tasks

```sql
SELECT
  tag.name,
  COUNT(t.persistentIdentifier) as overdue_count
FROM Tag tag
JOIN TaskTag tt ON tag.persistentIdentifier = tt.tag
JOIN Task t ON tt.task = t.persistentIdentifier
WHERE t.dateCompleted IS NULL
  AND t.dateDue < strftime('%s', 'now')
GROUP BY tag.name
ORDER BY overdue_count DESC
LIMIT 10;
```

## Best Practices

### Always Use Read-Only Mode

```python
import sqlite3
conn = sqlite3.connect('file:OmniFocus.sqlite?mode=ro', uri=True)
```

### Handle NULL Values

```sql
-- Use COALESCE for NULL handling
SELECT name, COALESCE(dateDue, 0) as due_date
FROM Task;

-- Or use IS NULL checks
WHERE dateDue IS NOT NULL
```

### Use Proper Date Comparisons

```sql
-- Correct: compare timestamps
WHERE dateDue < strftime('%s', 'now')

-- Incorrect: mixing types
WHERE dateDue < date('now')  -- Wrong!
```

### Index Usage

The database has indexes on frequently queried columns. Use them:

```sql
-- Good: uses index on dateCompleted
WHERE dateCompleted IS NULL

-- Good: uses index on persistentIdentifier
WHERE persistentIdentifier = 'abc123'

-- Less efficient: full table scan
WHERE name LIKE '%meeting%'
```

### Limit Results

```sql
-- Always limit when exploring
SELECT * FROM Task LIMIT 100;

-- Use LIMIT with ORDER BY for top N
SELECT * FROM Task
ORDER BY dateDue
LIMIT 10;
```

## Accessing the Database

### From Python

```python
import sqlite3

# Read-only connection
db_path = "~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Data/OmniFocus.ofocus/OmniFocus.sqlite"
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cursor = conn.cursor()

# Execute query
cursor.execute("SELECT name, dateDue FROM Task WHERE flagged = 1")
for row in cursor.fetchall():
    print(row)

conn.close()
```

### From Command Line

```bash
# Using sqlite3
sqlite3 ~/Library/Group\ Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Data/OmniFocus.ofocus/OmniFocus.sqlite \
  "SELECT name FROM Task LIMIT 10;"

# Read-only mode
sqlite3 -readonly OmniFocus.sqlite "SELECT COUNT(*) FROM Task;"
```

### Using the Included Script

```bash
# Use the provided Python script
python3 scripts/query_omnifocus.py --custom-query "SELECT name FROM Task LIMIT 10"
```

## Schema Exploration

### List All Tables

```sql
SELECT name FROM sqlite_master
WHERE type='table'
ORDER BY name;
```

### Describe Table Structure

```sql
PRAGMA table_info(Task);
```

### View Indexes

```sql
SELECT name, tbl_name, sql
FROM sqlite_master
WHERE type='index'
ORDER BY tbl_name, name;
```

### Sample Data

```sql
-- See example data from each table
SELECT * FROM Task LIMIT 5;
SELECT * FROM Tag LIMIT 5;
SELECT * FROM TaskTag LIMIT 5;
```

## Troubleshooting

### "Database is locked"

- Close OmniFocus before querying
- Or use read-only mode (Python script does this automatically)

### "Permission denied"

- Grant Full Disk Access to Terminal (System Settings → Privacy & Security)

### "No such table"

- Verify database path
- Check OmniFocus version (3 vs 4 have different paths)

### Empty results

- Check NULL handling
- Verify date timestamp format
- Test with simpler query first

## Version Differences

### OmniFocus 3 vs 4

Schema is mostly compatible, but:
- Database path differs (see Overview)
- Some column names may vary slightly
- Always test queries with your specific version

### Schema Changes

The schema may change between OmniFocus updates. Use:

```sql
PRAGMA user_version;  -- Check schema version
```

## Resources

- **SQLite Documentation:** [sqlite.org/docs.html](https://sqlite.org/docs.html)
- **Date/Time Functions:** [sqlite.org/lang_datefunc.html](https://sqlite.org/lang_datefunc.html)
- **Query Optimization:** [sqlite.org/queryplanner.html](https://sqlite.org/queryplanner.html)

## Warning

**Never modify the database directly.** OmniFocus maintains complex internal state and constraints. Direct modifications can corrupt your database. Use the AppleScript API (JXA) or Omni Automation for all write operations.
