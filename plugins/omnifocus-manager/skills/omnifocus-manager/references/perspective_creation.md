# OmniFocus Perspective Creation Guide

Perspectives are saved views that filter and organize tasks according to specific criteria. They're essential for consistent task management and GTD workflow implementation.

## What Are Perspectives?

Perspectives combine:
- **Filters** - Which tasks to show (rules)
- **Grouping** - How to organize displayed tasks
- **Sorting** - Order within groups
- **Display options** - What information to show

## Built-In Perspectives

OmniFocus includes several standard perspectives:

**Inbox** - Unprocessed captured items
**Projects** - Hierarchical project view
**Tags** - Tasks organized by tag
**Forecast** - Due dates + calendar events
**Flagged** - High-priority flagged items
**Nearby** - Location-based tasks (iOS)
**Review** - Projects needing review

## Creating Custom Perspectives

**Note:** Perspectives cannot be created via scripting. They must be created through the OmniFocus UI.

### Basic Workflow

1. **Window → Perspectives → Show Perspectives** (⌘0)
2. Click **+** to create new perspective
3. Configure filters, grouping, sorting
4. Save and assign keyboard shortcut

### Perspective Components

#### 1. Filter Rules

Define which tasks to include:

**Status Filters:**
- Available (not blocked, not deferred to future)
- Remaining (not completed)
- Completed
- Dropped

**Attribute Filters:**
- Flagged
- Due soon (within X days)
- Deferred to today or earlier
- Has attachments
- Has notes

**Hierarchy Filters:**
- Project status (Active, On Hold, Completed, Dropped)
- In specific project/folder
- Has/lacks specific tags
- Top-level items only (no subtasks)

**Compound Rules:**
- Combine with AND/OR logic
- Example: "Available AND Flagged AND Tag contains @home"

#### 2. Grouping

Organize tasks by:

**Project-based:**
- Project
- Folder
- Project hierarchy (shows full tree)

**Tag-based:**
- Tag
- First tag (if multiple tags)

**Time-based:**
- Due date
- Defer date
- Added date

**Status-based:**
- Flagged
- Completion status

**Custom:**
- None (flat list)

#### 3. Sorting

Order within groups:

- Due date (earliest first)
- Defer date
- Added date (newest/oldest first)
- Flagged (flagged items first)
- Project (alphabetical)
- Title (alphabetical)
- Manual (drag to reorder)

#### 4. Display Options

Control what's visible:

- Show/hide completed tasks
- Show/hide deferred tasks
- Show/hide projects
- Badge count (number of items in perspective)

## GTD-Aligned Perspective Examples

### Next Actions by Context

**Purpose:** See actionable tasks grouped by where/how you can do them

**Filters:**
- Status: Available
- Status: Remaining
- Project: Active

**Grouping:** Tag
**Sorting:** Due date
**Display:** Hide completed, hide deferred

**Usage:** Daily task selection - "What can I do @home right now?"

### Waiting For

**Purpose:** Track items delegated or blocked by others

**Filters:**
- Status: Remaining
- Tag: Contains "Waiting For"

**Grouping:** Project
**Sorting:** Added date (oldest first)
**Display:** Show notes (to see who/what waiting for)

**Usage:** Regular follow-up on delegated items

### Project Dashboard

**Purpose:** Overview of all active projects and their status

**Filters:**
- Project: Active
- Top-level items only (show projects, not tasks)

**Grouping:** Folder
**Sorting:** Project name
**Display:** Show project review dates

**Usage:** Weekly review, strategic planning

### Due This Week

**Purpose:** See upcoming deadlines to plan ahead

**Filters:**
- Status: Remaining
- Due: Within 7 days

**Grouping:** Due date
**Sorting:** Due date
**Display:** Show defer dates

**Usage:** Weekly planning, deadline awareness

### Stalled Projects

**Purpose:** Find projects without next actions

**Filters:**
- Project: Active
- Does not have: Available tasks

**Grouping:** Folder
**Sorting:** Project name

**Usage:** Weekly review to identify blocked projects needing attention

### Quick Entry

**Purpose:** Process tasks quickly without project context

**Filters:**
- Context: Inbox
- OR Added: Today

**Grouping:** None
**Sorting:** Added date (newest first)

**Usage:** Quick capture and processing

### Focus: High Priority

**Purpose:** What needs focus right now

**Filters:**
- Status: Available
- Status: Remaining
- (Flagged OR Due: Today OR Due: Overdue)

**Grouping:** Due date
**Sorting:** Flagged (flagged first), then due date

**Usage:** Daily priority focus

## Advanced Perspective Patterns

### Time-Block Planning

Create perspectives for different times of day:

**Morning Actions:**
- Filter: Tag contains "@morning" OR Tag contains "@home"
- Due: Today or earlier
- Time: Before 12:00 PM (requires OmniFocus Pro)

**Afternoon Work:**
- Filter: Tag contains "@office" OR Tag contains "@computer"
- Time: 12:00 PM - 6:00 PM

### Energy-Based Views

Match tasks to energy levels:

**High Energy:**
- Tag: "@focus" OR "@creative"
- Estimated duration: >30 minutes

**Low Energy:**
- Tag: "@admin" OR "@quick"
- Estimated duration: <15 minutes

### Review Cycles

Different review frequencies:

**Daily Review:**
- Show: Due today + flagged + deferred to today
- Purpose: Start-of-day planning

**Weekly Review:**
- Projects: Review frequency = weekly
- Purpose: GTD weekly review process

**Monthly Review:**
- Projects: Review frequency = monthly
- Purpose: Strategic review

## Perspective Design Workflow

When creating a new perspective, follow this process:

### Step 1: Identify the Need

Ask:
- What do I need to see consistently?
- When do I need this view?
- What decisions does this view support?

Examples:
- "I need to see what I can do at home"
- "I need to follow up on waiting items weekly"
- "I need to plan my day each morning"

### Step 2: Define Filter Rules

Determine which tasks should appear:
- What status? (Available, Remaining, etc.)
- Which projects? (Active only, or include On Hold?)
- Which tags? (Specific contexts or all?)
- Time constraints? (Due soon, deferred to today?)

### Step 3: Choose Grouping

How should tasks be organized:
- By project (see all tasks in same project together)
- By tag (see all @home tasks together)
- By due date (see what's due when)
- Flat list (no grouping)

### Step 4: Select Sorting

Order within groups:
- Due date (most common - see deadlines)
- Added date (useful for Waiting For - oldest first)
- Flagged (priorities at top)

### Step 5: Configure Display

What to show/hide:
- Hide completed (unless reviewing accomplishments)
- Hide deferred (unless planning future)
- Show notes (useful for Waiting For details)

### Step 6: Test and Iterate

Use the perspective:
- Does it show what you need?
- Is anything missing?
- Is there too much noise?
- Refine filters/grouping as needed

## Keyboard Shortcuts

Assign shortcuts for frequent perspectives:

- **⌘1** - Next Actions by Context
- **⌘2** - Flagged
- **⌘3** - Waiting For
- **⌘4** - Due This Week

Configure in: Preferences → Shortcuts → Perspectives

## Perspective Best Practices

### Keep It Simple

- Start with few filters, add complexity only if needed
- Too many filters = empty perspectives
- Simpler perspectives are easier to maintain

### Name Clearly

- Use action-oriented names: "Next Actions" not "Tasks"
- Indicate purpose: "Waiting For" not "External Dependencies"
- Keep names short for UI space

### Regular Review

- Unused perspectives = clutter
- Archive perspectives that don't serve current workflow
- Update perspectives as workflow evolves

### Avoid Duplication

- Don't create similar perspectives
- Use tags/filters effectively to consolidate views
- Example: Instead of separate "@home" and "@office" perspectives, use one "Next Actions" perspective grouped by tag

### Badge Counts

- Enable badge counts for actionable perspectives
- Helps gauge workload at a glance
- Disable for reference perspectives (reduces noise)

## Integration with Insights

When analyzing task patterns, perspective recommendations can help:

**Pattern:** Many tasks without tags
→ **Insight:** "12 tasks lack tags. Create 'Next Actions by Context' perspective to see value of tagging"

**Pattern:** Items waiting >30 days
→ **Insight:** "5 waiting items >30 days. Create 'Waiting For' perspective to track follow-ups"

**Pattern:** Projects without next actions
→ **Insight:** "3 stalled projects found. Create 'Stalled Projects' perspective for weekly review"

**Pattern:** Frequent overdue adjustments
→ **Insight:** "Many due date changes. Create 'Due This Week' perspective for better planning"

## Platform Differences

### macOS

- Full perspective editing capabilities
- Keyboard shortcuts
- Window-based perspective switcher

### iOS/iPadOS

- Can use perspectives created on Mac (via sync)
- Limited perspective editing on iOS
- Tap perspective name to switch
- Sidebar shows perspective list

### Cross-Platform Strategy

- Create perspectives on Mac
- Test on iOS to ensure mobile usability
- Consider touch-friendly grouping (larger tap targets)
- Sync automatically maintains consistency

## Resources

- OmniFocus Built-in Perspectives (starting point)
- View → Customize Toolbar (add perspective switcher)
- Window → Perspectives → Show Perspectives (⌘0) (manage all perspectives)
- Official OmniFocus field guide: perspectives chapter
