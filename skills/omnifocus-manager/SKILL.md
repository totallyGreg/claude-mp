---
name: omnifocus-manager
description: Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA). This skill should be used when working with OmniFocus data, creating or modifying tasks, analyzing task lists, searching for tasks, or automating OmniFocus workflows. Triggers when user mentions OmniFocus, tasks, projects, GTD workflows, or asks to create, update, search, or analyze their task data.
metadata:
  version: 1.3.0
  author: totally-tools
  license: MIT
compatibility:
  platforms: [macos]
  requires:
    - OmniFocus 3 or 4
    - Python 3.6+ (for database queries)
    - macOS with automation permissions
---

# OmniFocus Manager

## Overview

Comprehensive OmniFocus automation through multiple complementary approaches:

1. **Omni Automation (JavaScript)** - Native, cross-platform automation (Mac + iOS)
2. **JXA (JavaScript for Automation)** - Full query and management via AppleScript API (Mac only)
3. **URL Scheme** - Simple task creation via omnifocus:// URLs (Mac + iOS)
4. **Database Queries (Python)** - Read-only database access (Mac only, requires permissions)

## When to Use This Skill

- User asks to query, search, or analyze their OmniFocus database
- User wants to create, update, or delete OmniFocus tasks
- User requests task reports, insights, or statistics
- User mentions OmniFocus, tasks, projects, contexts, tags, or GTD workflows
- User asks what tasks are due soon, flagged, or scheduled for today
- User wants to find specific tasks or projects
- User wants to complete or modify existing tasks

## Quick Decision Tree

1. **Cross-platform support needed (iOS/Mac)?**
   - YES → Use Omni Automation (`references/omni_automation.md`)
   - NO → Continue

2. **Reusable automation?**
   - YES → Create Omni Automation plug-in (`examples/`)
   - NO → Continue

3. **Querying/reading data?**
   - Use `scripts/manage_omnifocus.js` query commands (JXA)
   - See `references/jxa_commands.md` for complete command reference

4. **Creating/modifying data?**
   - Simple task creation → Use omnifocus:// URL scheme (`references/omnifocus_url_scheme.md`)
   - Complex operations → Use `scripts/manage_omnifocus.js` (JXA)
   - See `references/jxa_commands.md` for all management commands

5. **Last resort: Database queries**
   - ONLY use `scripts/query_omnifocus.py` if JXA cannot accomplish the task
   - Requires full disk access permissions
   - Read-only, Mac-only

## Core Capabilities

### Omni Automation (Recommended)

**Why:** Cross-platform, secure, native, reusable, AI-powered.

**Key Features:**
- Works on Mac, iOS, iPadOS
- Create plug-ins for reusable automation
- No file system permissions required
- Native OmniFocus JavaScript API
- **NEW:** Apple Foundation Models integration (OmniFocus 4.8+, macOS 15.2+)
  - Natural language task processing
  - Intelligent categorization and prioritization
  - Extract structured data from text
  - Smart task suggestions and analysis

**Resources:**
- Complete API reference: `references/omni_automation.md`
- **Apple Intelligence integration:** `references/foundation_models_integration.md`
- Example plug-ins: `examples/TodaysTasks.omnifocusjs`
- Installation guide: `examples/README.md`

**Quick Example:**
```javascript
// Get today's tasks
(() => {
    const doc = Application('OmniFocus').defaultDocument;
    const tasks = doc.flattenedTasks();
    return tasks.filter(t => !t.completed() && isDueToday(t));
})();
```

**AI-Powered Example:**
```javascript
// Auto-categorize task using Apple Intelligence
(async () => {
    const session = new LanguageModel.Session();
    const task = "Buy groceries and cook dinner";

    const result = await session.respondWithSchema(
        `Categorize: "${task}"`,
        { type: "object", properties: { category: { type: "string" } } }
    );

    console.log(result.category); // "personal"
})();
```

### JXA Query & Management

**Why:** Full AppleScript API access, secure, comprehensive.

**Common Queries:**
```bash
# Today's tasks
osascript -l JavaScript scripts/manage_omnifocus.js today

# Tasks due soon
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7

# Flagged tasks
osascript -l JavaScript scripts/manage_omnifocus.js flagged

# Search tasks
osascript -l JavaScript scripts/manage_omnifocus.js search --query "meeting"
```

**Task Management:**
```bash
# Create task
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task name" \
  --project "Project" \
  --due "2025-12-25"

# Update task
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due "2025-12-31"

# Complete task
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Task name"
```

**Complete command reference:** `references/jxa_commands.md`

### URL Scheme (Quick Capture & Embedding)

**Why:** Fastest for simple task creation, cross-platform, no permissions, embeddable in notes/documents.

**Common Use Cases:**
1. Quick task creation with one command
2. Creating clickable links in notes (Obsidian, Bear, etc.)
3. Meeting notes with action item templates
4. Daily note quick-capture links
5. Bulk task import via TaskPaper format

**Quick Actions:**

Create task:
```bash
open "omnifocus:///add?name=Task%20Name&note=Description&autosave=true"
```

Open perspective:
```bash
open "omnifocus:///flagged"
open "omnifocus:///forecast"
```

Bulk import (TaskPaper):
```bash
open "omnifocus:///paste?target=inbox&content=-%20Task%201%0A-%20Task%202"
```

**Embedding in Notes:**

Generate clickable Markdown links for notes:
```markdown
[Create daily review](omnifocus:///add?name=Daily%20Review&project=Admin&autosave=true)
[View Flagged](omnifocus:///flagged)
```

**URL Generation Helper:**

When generating URLs for users:
1. **Always URL-encode** - Use Python's `urllib.parse.quote()` or equivalent
2. **Use autosave=true** - Avoid confirmation dialogs for embedded links
3. **Include context** - Pre-fill project, tags, due dates when known
4. **Format as Markdown** - For easy embedding: `[Link text](url)`

Example generation:
```python
from urllib.parse import quote
name = quote("Review proposal")
project = quote("Work")
url = f"omnifocus:///add?name={name}&project={project}&autosave=true"
# Output as: [Create task](omnifocus:///add?name=Review%20proposal&project=Work&autosave=true)
```

**Complete reference:** `references/omnifocus_url_scheme.md`

**Key features in reference:**
- All parameters (name, note, project, tags, due, defer, flagged, repeat, etc.)
- Paste action for bulk TaskPaper import
- Built-in perspectives (inbox, flagged, forecast, projects, tags)
- Custom perspectives
- x-callback-url support
- Repeat rules (RRULE format)
- Embedding templates for notes

### Database Queries (Last Resort)

**Why:** Advanced SQL queries when JXA is insufficient.

**Usage:**
```bash
python3 scripts/query_omnifocus.py --list
python3 scripts/query_omnifocus.py --flagged
python3 scripts/query_omnifocus.py --custom-query "SELECT ..."
```

**Note:** Requires Full Disk Access permission. Use JXA when possible.

## Common Workflows

### "What should I work on today?"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

Or install the Today's Tasks plug-in: `examples/TodaysTasks.omnifocusjs`

### "Create a task for X"

**Quick (URL scheme):**
```bash
open "omnifocus:///add?name=Task%20Name&autosave=true"
```

**Embedded in notes (Markdown):**
```markdown
[Create task](omnifocus:///add?name=Task%20Name&project=Work&autosave=true)
```

**Bulk import (TaskPaper):**
```bash
open "omnifocus:///paste?target=inbox&content=-%20Task%201%0A-%20Task%202"
```

**Detailed (JXA):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Task name" \
  --project "Project" \
  --tags "tag1,tag2" \
  --due "2025-12-25"
```

### "What's due this week?"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
```

### "Find tasks about X"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "X"
```

### "Mark task Y as complete"

```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Y"
```

**More workflows:** See `references/workflows.md` for comprehensive workflow examples including:
- Daily planning routines
- Weekly/monthly reviews
- Project management
- Batch operations
- Integration with other tools

## Troubleshooting

### Permission Issues

**Automation Permission (for JXA):**
- System Settings → Privacy & Security → Automation
- Enable OmniFocus for your terminal app

**Full Disk Access (for Python database queries):**
- System Settings → Privacy & Security → Full Disk Access
- Add your terminal app

**Important:** Restart terminal completely after granting permissions.

### Common Errors

- **"Not authorized to send Apple events"** → Grant automation permission
- **"Database file not found"** → Grant Full Disk Access, verify OmniFocus version
- **"Multiple tasks found"** → Use task ID instead of name
- **"Invalid date format"** → Use ISO 8601: `YYYY-MM-DD`

**Complete troubleshooting guide:** `references/troubleshooting.md`

## Reference Documentation

All detailed documentation has been moved to references for better organization:

### Primary References

1. **`references/jxa_commands.md`** ⭐ - Complete JXA command reference
   - All query commands with parameters and examples
   - All task management commands (create, update, complete, delete)
   - Output formats and error handling
   - Command-line usage patterns

2. **`references/omni_automation.md`** - Omni Automation practical guide
   - Getting started and common patterns
   - Plug-in development workflow
   - Code examples and best practices
   - Use this for learning and implementation guidance

3. **`references/omni_automation_shared.md`** - Shared Omni Automation classes ⭐
   - Cross-app shared APIs (Alert, Form, FilePicker, etc.)
   - Works across OmniFocus, OmniGraffle, OmniOutliner, OmniPlan
   - User interaction (alerts, forms, dialogs)
   - File handling (FilePicker, FileSaver, FileWrapper)
   - Data processing (URL, XML, Pasteboard, Credentials)
   - Formatters (Date, Decimal, Duration)
   - System integration (Device, Notification, Speech, Timer)
   - **Use this for:** Building cross-platform plugins, user input, file operations, clipboard access

4. **`references/OmniFocus-API.md`** - Complete Omni Automation API reference
   - Official comprehensive API specification
   - Detailed class/method/property documentation
   - Use this for API lookup and detailed signatures
   - **Search patterns for common lookups:**
     - Task class: `grep -A 20 "^## Task" references/OmniFocus-API.md`
     - Project class: `grep -A 20 "^## Project" references/OmniFocus-API.md`
     - Document methods: `grep "function.*Document" references/OmniFocus-API.md`
     - Specific property: `grep -i "propertyName" references/OmniFocus-API.md`

5. **`references/foundation_models_integration.md`** ⭐ - Apple Intelligence integration
   - **NEW in OmniFocus 4.8+** - On-device AI for task automation
   - Natural language task processing with LanguageModel.Session
   - Intelligent categorization and prioritization
   - Extract structured data from text (JSON schemas)
   - Smart task suggestions and analysis
   - Complete examples: auto-tagging, meeting notes extraction, project structure analysis
   - Requirements: macOS 15.2+, iOS 18.2+, Apple Silicon/iPhone 15 Pro+
   - **Use this for:** AI-powered automation, intelligent task organization, natural language processing

6. **`references/workflows.md`** - Common workflow patterns
   - Daily/weekly/monthly planning
   - Project management workflows
   - Batch operations
   - Integration examples (Keyboard Maestro, Alfred, etc.)

7. **`references/omnifocus_url_scheme.md`** - URL scheme reference ⭐
   - Task creation with all parameters
   - Bulk TaskPaper import (paste action)
   - Built-in perspectives (inbox, flagged, forecast, etc.)
   - Custom perspectives
   - x-callback-url support
   - Repeat rules (RRULE format)
   - **Embedding in notes** - Templates for Markdown links
   - URL encoding and generation helpers
   - Cross-platform (Mac + iOS)

8. **`references/troubleshooting.md`** - Troubleshooting guide
   - Permission setup (step-by-step)
   - Common errors and solutions
   - Performance optimization
   - Debugging techniques

### Scripts

- **`scripts/manage_omnifocus.js`** - JXA automation (Mac)
- **`scripts/query_omnifocus.py`** - Database queries (Mac, requires permissions)

### Examples

- **`examples/TodaysTasks.omnifocusjs`** - Today's tasks plug-in
- **`examples/README.md`** - Plug-in installation guide

## Important Notes

### Omni Automation
- Cross-platform (Mac + iOS)
- No permissions required
- Native OmniFocus API
- Reusable plug-ins

### JXA (JavaScript for Automation)
- Mac only
- Requires automation permission
- Full AppleScript API access
- Both read and write operations

### URL Scheme
- Cross-platform (Mac + iOS)
- No permissions required
- Task creation with full parameters (tags, dates, repeat, etc.)
- Bulk import via TaskPaper format (paste action)
- Open perspectives (built-in and custom)
- Perfect for embedding in notes/documents
- x-callback-url support for automation workflows
- Cannot modify/delete existing tasks or query data

### Database Queries (Python)
- Use only when necessary
- Read-only
- Requires Full Disk Access
- Mac only

## Getting Help

Built-in help for all scripts:

```bash
# JXA help
osascript -l JavaScript scripts/manage_omnifocus.js help

# Python help
python3 scripts/query_omnifocus.py --help
```

## External Resources

- **Omni Automation:** [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- **OmniFocus URL Schemes:** [support.omnigroup.com/omnifocus-url-schemes](https://support.omnigroup.com/omnifocus-url-schemes/)
- **OmniFocus AppleScript:** [support.omnigroup.com/omnifocus-applescript](https://support.omnigroup.com/omnifocus-applescript/)
