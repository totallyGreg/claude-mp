# GTD Methodology for OmniFocus

Complete guide to implementing Getting Things Done (GTD) methodology using OmniFocus automation.

## Overview

GTD (Getting Things Done) is a productivity methodology by David Allen. This guide shows how to implement GTD principles using OmniFocus and the automation tools in this skill.

## The Five Steps of GTD

### 1. Capture

Collect everything that has your attention.

**OmniFocus Implementation:**

**Quick Capture (URL Scheme):**
```bash
open "omnifocus:///add?name=Quick%20idea&note=Details&autosave=true"
```

**Detailed Capture (JXA):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "New item" \
  --note "Context and details"
```

**Best Practices:**
- Capture immediately when something comes to mind
- Don't worry about organization during capture
- Use inbox liberally
- Add context in notes if helpful

### 2. Clarify

Process what each item means and what to do about it.

**Decision Tree:**

```
Is it actionable?
├─ NO → Reference, trash, or someday/maybe
└─ YES → Is it a project (multiple steps)?
    ├─ YES → Create project with tasks
    └─ NO → Single task
        ├─ < 2 minutes → Do it now
        ├─ Can delegate → Assign or create "waiting for" task
        └─ Defer → Schedule or add to appropriate project
```

**OmniFocus Workflow:**

```bash
# Review inbox
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.project == null or .project == "")'

# Move task to project
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project "Project name"

# Add due date
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due "2025-12-31"

# Add context tags
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --tags "office,computer"
```

### 3. Organize

Put items where they belong.

**GTD Organization in OmniFocus:**

**Folders:**
- Personal
- Work
- Someday/Maybe
- Reference

**Projects:**
- Active projects (outcomes requiring multiple steps)
- Single Action Lists (related one-off tasks)

**Tags (Contexts):**
- `@office` - Must be at office
- `@home` - Can do at home
- `@computer` - Requires computer
- `@phone` - Phone calls
- `@errands` - Out and about
- `@waiting` - Waiting for someone/something
- `@agenda-[person]` - Topics to discuss with someone

**Automation for Organization:**

```bash
# Create project structure
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Project planning" \
  --project "Work Projects" \
  --tags "planning,office" \
  --defer "2025-12-20" \
  --create-project

# Tag tasks by context
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Call client" \
  --tags "phone,work"
```

### 4. Reflect

Review regularly to stay current.

**Daily Review:**

```bash
# Morning: What's on deck today?
osascript -l JavaScript scripts/manage_omnifocus.js today

# Check flagged priorities
osascript -l JavaScript scripts/manage_omnifocus.js flagged

# Review upcoming deadlines
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 3
```

**Weekly Review Checklist:**

1. **Get Clear:**
   ```bash
   # Empty inbox
   osascript -l JavaScript scripts/manage_omnifocus.js list | \
     jq '.tasks[] | select(.project == null)'
   ```

2. **Get Current:**
   ```bash
   # Review all projects
   python3 scripts/query_omnifocus.py --projects

   # Check calendar for next week
   osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7
   ```

3. **Get Creative:**
   - Review someday/maybe
   - Brainstorm new projects
   - Update project plans

**Automation Script for Weekly Review:**

```bash
#!/bin/bash
echo "=== Weekly Review ==="
echo ""
echo "1. Inbox Items:"
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq -r '.tasks[] | select(.project == null) | "  • \(.name)"'
echo ""
echo "2. Due This Week:"
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7 | \
  jq -r '.tasks[] | "  • \(.name) - \(.dueDate)"'
echo ""
echo "3. Flagged Tasks:"
osascript -l JavaScript scripts/manage_omnifocus.js flagged | \
  jq -r '.tasks[] | "  • \(.name)"'
```

### 5. Engage

Choose what to do based on context, time, energy, and priority.

**Context-Based Selection:**

```bash
# Show tasks for current context
osascript -l JavaScript scripts/manage_omnifocus.js search --query "@office"

# Or by tag
python3 scripts/query_omnifocus.py --tags
```

**Energy-Based Selection:**

```bash
# High energy: complex tasks (>1 hour)
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq '.tasks[] | select(.estimatedMinutes >= 60)'

# Low energy: quick tasks (<30 min)
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq '.tasks[] | select(.estimatedMinutes <= 30)'
```

**Priority-Based Selection:**

```bash
# Flagged tasks (high priority)
osascript -l JavaScript scripts/manage_omnifocus.js flagged

# Due soon
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 2
```

## GTD Perspectives in OmniFocus

### Today Perspective

**What:** Tasks due or available today

**Automation:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js today
```

Or use the plug-in: `examples/TodaysTasks.omnifocusjs`

### Next Actions Perspective

**What:** All available tasks (not blocked, not future)

**Automation:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active
```

### Waiting For Perspective

**What:** Tasks you're waiting on from others

**Setup:**
- Use `@waiting` tag
- Add person's name in task title or note

**Automation:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js search --query "@waiting"
```

### Someday/Maybe Perspective

**What:** Ideas and projects you might do later

**Setup:**
- Create "Someday/Maybe" folder
- Put projects on hold
- Use `@someday` tag

**Review during weekly review:**
```bash
python3 scripts/query_omnifocus.py --projects | \
  jq '.projects[] | select(.status == "on hold")'
```

## Project Planning with OmniFocus

### Project Template

When creating a new project:

1. **Define outcome** - What does "done" look like?
2. **Brainstorm** - What needs to happen?
3. **Organize** - Sequential or parallel?
4. **Next actions** - What's the immediate next step?

**Automation Example:**

```bash
# Create project with initial tasks
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Launch new website" \
  --note "Outcome: Live website by Q1 2026" \
  --create-project

# Add first tasks
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Research hosting providers" \
  --project "Launch new website" \
  --tags "research,computer" \
  --estimate "2h"

osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Create site wireframes" \
  --project "Launch new website" \
  --tags "design,computer" \
  --estimate "4h"
```

### Sequential vs. Parallel Projects

**Sequential:** Tasks must be done in order
- Set project to sequential in OmniFocus
- Only first incomplete task is "available"

**Parallel:** Tasks can be done in any order
- All tasks are available immediately
- More flexible but requires more decision-making

**When to use sequential:**
- Steps build on each other
- Can't start next step until previous is done
- Example: "1. Research → 2. Draft → 3. Review → 4. Publish"

**When to use parallel:**
- Independent tasks
- Can tackle in any order
- Example: Multiple articles for a blog

## GTD Horizons of Focus

### Runway (Next Actions)

Current tasks you can do now.

```bash
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active
```

### 10,000 feet (Projects)

Current projects with outcomes.

```bash
python3 scripts/query_omnifocus.py --projects
```

### 20,000 feet (Areas of Responsibility)

Use folders to represent areas:
- Health
- Finance
- Relationships
- Career
- Personal Development

### 30,000+ feet (Goals, Vision, Purpose)

Review higher levels during quarterly reviews.

## Common GTD Workflows in OmniFocus

### Processing Inbox

```bash
# Daily: Review and process inbox
# For each item:
# 1. What is it?
# 2. Is it actionable?
# 3. What's the next action?
# 4. Move to appropriate project or complete

# View inbox
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq '.tasks[] | select(.project == null)'

# Process each item (move to project, add context, etc.)
```

### Weekly Review Template

**Friday or Monday - 1 hour dedicated time**

1. **Get Clear (15 min)**
   - Process inbox to zero
   - Process notes and reading inbox
   - Empty mind capture lists

2. **Get Current (30 min)**
   - Review calendar (past and future)
   - Review all project lists
   - Update project next actions
   - Review "waiting for" list
   - Review upcoming deadlines

3. **Get Creative (15 min)**
   - Review someday/maybe
   - Think of new projects
   - Reflect on bigger picture

**Automation Support:**

```bash
# Weekly review script
echo "=== Inbox ==="
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq -r '.count as $count | "Items to process: \($count)"'

echo "=== This Week ==="
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 7 | \
  jq -r '.count as $count | "Due this week: \($count)"'

echo "=== Projects to Review ==="
python3 scripts/query_omnifocus.py --projects | \
  jq -r '.projects[] | .name'
```

### Daily Planning Workflow

**Morning (5-10 minutes):**

```bash
# 1. Review today's tasks
osascript -l JavaScript scripts/manage_omnifocus.js today

# 2. Check calendar

# 3. Review flagged priorities
osascript -l JavaScript scripts/manage_omnifocus.js flagged

# 4. Choose 3 most important tasks for today
# Flag them or add to "Today" tag
```

**End of Day (5 minutes):**

```bash
# 1. Complete finished tasks
osascript -l JavaScript scripts/manage_omnifocus.js complete --name "Task name"

# 2. Capture anything new
# 3. Review tomorrow's tasks
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 1
```

## Best Practices

### 1. Trust Your System

- Capture everything immediately
- Process inbox regularly (daily)
- Keep system current through weekly review
- Use the system - don't rely on memory

### 2. Start Small

- Begin with basic capture and inbox processing
- Add projects as you identify outcomes
- Gradually add tags/contexts
- Don't over-organize initially

### 3. Two-Minute Rule

If it takes less than 2 minutes, do it immediately:

```bash
# Don't create these tasks - just do them
- Reply to quick emails
- File a document
- Make a quick phone call
```

### 4. Context Tags

Create contexts that match your real life:

```bash
# Location-based
@home, @office, @car, @town

# Tool-based
@computer, @phone, @online

# Energy-based
@high-energy, @low-energy

# People-based
@agenda-boss, @agenda-spouse
```

### 5. Project Status

- **Active:** Working on now (limit to 5-7 projects)
- **On Hold:** Can't work on yet (waiting for something)
- **Completed:** Achieved the outcome
- **Dropped:** No longer relevant

### 6. Review Frequency

- **Daily:** Today tasks, flagged items
- **Weekly:** All projects, waiting for, someday/maybe
- **Monthly:** Areas of responsibility
- **Quarterly:** Goals and higher horizons

## Automation Templates

### Morning Dashboard

```bash
#!/bin/bash
echo "============================================"
echo "Good Morning! Here's your day:"
echo "============================================"
echo ""
echo "Today's Tasks:"
osascript -l JavaScript scripts/manage_omnifocus.js today | \
  jq -r '.tasks[] | "  [ ] \(.name)"'
echo ""
echo "Due Soon:"
osascript -l JavaScript scripts/manage_omnifocus.js due-soon --days 3 | \
  jq -r '.tasks[] | "  ⚠ \(.name) - Due: \(.dueDate)"'
echo ""
echo "Flagged Priorities:"
osascript -l JavaScript scripts/manage_omnifocus.js flagged | \
  jq -r '.tasks[] | "  ⭐ \(.name)"'
echo "============================================"
```

### Project Review Helper

```bash
# Show projects needing review
python3 scripts/query_omnifocus.py --projects | \
  jq -r '.projects[] | "Project: \(.name)\n  Tasks: \(.tasks_count)\n  Status: \(.status)\n"'
```

## Resources

- **GTD Book:** "Getting Things Done" by David Allen
- **OmniFocus GTD Setup:** [support.omnigroup.com/omnifocus-gtd](https://support.omnigroup.com/omnifocus-gtd/)
- **GTD Forums:** [discourse.omnigroup.com](https://discourse.omnigroup.com/)
- **GTD Weekly Review:** [gettingthingsdone.com/weekly-review](https://gettingthingsdone.com/weekly-review/)

## Common Pitfalls

### 1. Over-Organization

**Problem:** Spending more time organizing than doing.

**Solution:** Keep it simple. Start with basics: inbox, projects, basic tags.

### 2. Neglecting Review

**Problem:** System becomes stale and untrusted.

**Solution:** Schedule weekly review like any other appointment. Make it non-negotiable.

### 3. Too Many Active Projects

**Problem:** Overwhelming list, nothing moves forward.

**Solution:** Limit to 5-7 active projects. Move others to "On Hold" or "Someday/Maybe".

### 4. Not Capturing Everything

**Problem:** Still keeping mental lists, system incomplete.

**Solution:** Make capture frictionless. Use quick capture tools. Build the habit.

### 5. Unclear Next Actions

**Problem:** Tasks like "Plan website" are too vague.

**Solution:** Always define concrete, physical next actions: "Email John for website requirements".

## GTD + OmniFocus: The Perfect Match

OmniFocus was designed for GTD. This skill enhances that with automation:

- **Capture:** Quick entry via URL scheme or JXA
- **Clarify:** Update tasks with projects, tags, dates
- **Organize:** Flexible folder, project, tag structure
- **Reflect:** Automated review lists and reports
- **Engage:** Context-based filtered views

Use the automation to support GTD, not replace it. The methodology comes first; automation makes it easier.
