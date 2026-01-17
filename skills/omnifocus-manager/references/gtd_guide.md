# The OmniFocus GTD Guide

This guide provides a complete overview of the Getting Things Done (GTD) methodology and how to implement it effectively within OmniFocus using automation.

## 1. What is GTD?

**Getting Things Done (GTD)** is a productivity methodology created by David Allen. It provides a systematic approach to managing commitments, projects, and tasks through five core phases:

1.  **Capture** - Collect everything that has your attention.
2.  **Clarify** - Process what it means and what to do about it.
3.  **Organize** - Put it where it belongs.
4.  **Reflect** - Review frequently.
5.  **Engage** - Simply do.

OmniFocus was specifically designed to implement GTD principles, making it the perfect tool for this methodology.

### Core Concepts

*   **Open Loops**: Anything that has your attention but isn't where it belongs. The goal is to capture all open loops in a trusted system.
*   **Mind Like Water**: A state of mental clarity achieved by getting everything out of your head and into your system.
*   **Next Actions**: The immediate, physical, visible activities required to move a project forward. They must be concrete (e.g., "Call John about Q4 budget," not "Budget stuff").
*   **Projects**: Any desired outcome that requires more than one action step.
*   **Contexts**: Filters based on the tool, location, or person required to complete a task (e.g., `@home`, `@office`, `@phone`). In OmniFocus, these are implemented as **Tags**.
*   **Weekly Review**: The cornerstone of GTD. A dedicated time to get clear, get current, and get creative, ensuring the system remains trusted and up-to-date.

## 2. How OmniFocus Implements GTD

OmniFocus maps directly to GTD concepts:

*   **Projects vs. Tasks**: In GTD, a **Project** is any outcome requiring multiple steps. OmniFocus projects contain these steps as **Tasks**.
*   **Contexts → Tags**: GTD "Contexts" are implemented as **Tags** in OmniFocus 3 and later.
*   **Next Actions**: OmniFocus identifies "Next Actions" as tasks that are **Available** (not blocked or deferred).
*   **Waiting For**: This is managed using a specific "Waiting For" tag to track delegated items.
*   **Someday/Maybe**: Ideas you aren't committed to can be managed with an "On Hold" project status or a "Someday" tag.
*   **Inbox**: The **Inbox** is the central capture bucket for all new, unprocessed items.

## 3. The Five Steps of GTD: Implementation Guide

This section provides a detailed walkthrough of implementing each GTD phase in OmniFocus with automation examples.

### Step 1: Capture

Collect everything that has your attention immediately. Don't worry about organization at this stage.

**Automation Tools:**

*   **Quick Capture (URL Scheme):** The fastest way to get an idea into OmniFocus.
    ```bash
    open "omnifocus:///add?name=Quick%20idea&note=Details&autosave=true"
    ```
*   **Detailed Capture (JXA):** For when you need to add more detail from the command line.
    ```bash
    osascript -l JavaScript scripts/manage_omnifocus.js create \
      --name "New item" \
      --note "Context and details"
    ```

### Step 2: Clarify

Process what each captured item means and what to do about it. For each item in your inbox, ask: "Is it actionable?"

*   **If NO**: Trash it, file it as a reference, or move it to a Someday/Maybe list.
*   **If YES**:
    *   Does it take less than 2 minutes? Do it now.
    *   Is it a single task? Add it to a project or list.
    *   Is it a multi-step outcome? Create a new **Project**.

**Automation Tools:**

```bash
# Review inbox items
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active | \
  jq '.tasks[] | select(.project == null or .project == "")'

# Move a task to a project
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --project "Project name"

# Add a due date
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task name" \
  --due "2025-12-31"
```

### Step 3: Organize

Put your processed items where they belong.

*   **Folders**: For broad areas of responsibility (e.g., "Personal," "Work").
*   **Projects**: For specific outcomes requiring multiple tasks.
*   **Tags**: For the context needed to do a task (e.g., `@computer`, `@phone`, `@errands`, `@waiting`).

**Automation Tools:**

```bash
# Create a new project with tags and a defer date
osascript -l JavaScript scripts/manage_omnifocus.js create \
  --name "Project planning" \
  --project "Work Projects" \
  --tags "planning,office" \
  --defer "2025-12-20" \
  --create-project
```

### Step 4: Reflect

Review your system regularly to keep it current and trusted.

*   **Daily Review (5-10 mins)**: Check today's tasks, flagged items, and upcoming deadlines.
*   **Weekly Review (1 hour)**: A non-negotiable process to review all projects, "Waiting For" items, and the "Someday/Maybe" list.

**Automation Tools:**

```bash
# Daily Review: See what's on your plate today
osascript -l JavaScript scripts/manage_omnifocus.js today

# Weekly Review Helper Script
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
```

### Step 5: Engage

Choose what to do based on your context, time, energy, and priorities.

**Automation Tools:**

```bash
# Engage by Context: Show tasks I can do at the office
osascript -l JavaScript scripts/manage_omnifocus.js search --query "@office"

# Engage by Energy: Find quick, low-energy tasks
osascript -l JavaScript scripts/manage_omnifocus.js list | \
  jq '.tasks[] | select(.estimatedMinutes <= 30)'

# Engage by Priority: See what's flagged
osascript -l JavaScript scripts/manage_omnifocus.js flagged
```

## 4. GTD Perspectives in OmniFocus

Perspectives are saved, filtered views that are essential for an effective GTD system. While they must be created in the OmniFocus UI, scripts can recommend them.

*   **Next Actions**: Shows all available tasks, grouped by tag. The core "what can I do now?" view.
*   **Waiting For**: Shows all tasks tagged `@waiting`, so you can follow up.
*   **Stalled Projects**: Shows active projects that have no available "Next Actions."
*   **Project Dashboard**: A high-level view of all active projects.

## 5. Common Pitfalls and Best Practices

*   **Over-Organization**: Don't spend more time organizing than doing. Keep your system simple.
*   **Neglecting the Review**: The Weekly Review is essential. If you don't do it, you'll stop trusting your system.
*   **Vague Next Actions**: A task like "Plan vacation" is not a next action. "Research flights to Hawaii" is. Be specific.
*   **Trust Your System**: Capture everything immediately and process it regularly. Don't keep mental lists.

This consolidated guide provides a single, authoritative source for implementing GTD with OmniFocus.
