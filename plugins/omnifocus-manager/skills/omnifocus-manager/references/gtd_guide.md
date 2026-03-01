# GTD-to-OmniFocus Mapping

This reference maps GTD concepts to OmniFocus implementation. For pure GTD methodology and coaching, see the **gtd-coach** skill.

## Concept Mapping

| GTD Concept | OmniFocus Implementation |
|-------------|--------------------------|
| Inbox | Inbox (unprocessed items) |
| Projects | Projects (multi-step outcomes) |
| Next Actions | Available tasks (not blocked/deferred) |
| Contexts | Tags (`@home`, `@office`, `@phone`) |
| Waiting For | Tasks with `@waiting` tag |
| Someday/Maybe | On Hold project status or `@someday` tag |
| Reference | Notes field, or external system |
| Calendar | Due dates and defer dates |
| Areas of Focus | Folders (top-level organization) |
| Weekly Review | Review perspective + project review intervals |

## Automation Mapping

| GTD Phase | OmniFocus Command |
|-----------|-------------------|
| **Capture** | `open "omnifocus:///add?name=Item&autosave=true"` |
| **Capture (detailed)** | `osascript -l JavaScript scripts/manage_omnifocus.js create --name "Item"` |
| **Clarify (review inbox)** | `osascript -l JavaScript scripts/manage_omnifocus.js list --filter active` |
| **Organize (assign project)** | `osascript -l JavaScript scripts/manage_omnifocus.js update --name "Task" --project "Project"` |
| **Reflect (daily)** | `osascript -l JavaScript scripts/manage_omnifocus.js today` |
| **Reflect (weekly)** | `osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7` |
| **Engage (by context)** | `osascript -l JavaScript scripts/manage_omnifocus.js search --query "@office"` |
| **Engage (flagged)** | `osascript -l JavaScript scripts/manage_omnifocus.js flagged` |

## Key Perspectives for GTD

| Perspective | Purpose | Filter |
|-------------|---------|--------|
| Next Actions | "What can I do now?" | Status = Available, grouped by tag |
| Waiting For | Track delegated items | Tag = `@waiting` |
| Stalled Projects | Find stuck projects | Active projects with no available tasks |
| Project Dashboard | High-level overview | All active projects |

## GTD Coaching

For in-depth GTD methodology — five phases, next action clarity, weekly review checklists, horizons of focus, and system health coaching — use the **gtd-coach** skill.
