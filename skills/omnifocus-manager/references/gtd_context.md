# GTD Context for OmniFocus

This reference provides GTD (Getting Things Done) methodology context to inform better insight generation and automation design in OmniFocus.

## Core GTD Principles

GTD is a five-phase workflow for managing commitments:

1. **Capture** - Collect everything that has your attention
2. **Clarify** - Process what it means and what to do about it
3. **Organize** - Put it where it belongs
4. **Reflect** - Review frequently
5. **Engage** - Simply do

## How OmniFocus Implements GTD

### Projects vs Tasks

**Projects** in GTD are any desired outcome requiring more than one action step.

- OmniFocus projects contain multiple tasks
- Single-action lists are projects with "single actions" type
- Active/On Hold/Completed/Dropped status tracks project lifecycle

### Contexts → Tags

**Contexts** define where/when/with what a task can be done.

- OmniFocus 3+ uses **tags** (formerly contexts)
- Examples: @home, @office, @computer, @phone, @errands
- Tags enable filtering: "show me what I can do @home"
- Multiple tags per task supported

### Next Actions

**Next Actions** are the immediate, physical, visible activities to move forward.

- Must be concrete and actionable (not "plan vacation" but "research flight prices")
- OmniFocus shows next actions via:
  - Available tasks (not blocked by dependencies)
  - Not deferred to future dates
  - In active projects
- Perspectives filter to show only next actions

### Waiting For

**Waiting For** tracks items delegated to others or blocked by external dependencies.

- Use a "Waiting For" tag in OmniFocus
- Include what you're waiting for in the task name: "Waiting: Bob's design review"
- Review regularly to follow up
- Custom perspective: Tasks with "Waiting For" tag

### Someday/Maybe

**Someday/Maybe** holds ideas you might do but not committed to.

- Use "On Hold" project status or "Someday" tag
- Review during weekly review
- Move to active when ready to commit

### Inbox

**Inbox** is the capture bucket for unprocessed items.

- All captured items start in OmniFocus inbox
- Processing: decide if actionable → project/task or reference
- Goal: inbox zero after processing

### Weekly Review

**Weekly Review** is the cornerstone of GTD.

OmniFocus weekly review checklist:
1. Get clear - process inbox to zero
2. Get current - review all projects and next actions
3. Get creative - review someday/maybe for activation

## GTD-Aligned Perspectives

Perspectives are saved filters/views essential for GTD:

### Forecast

- Shows tasks with due dates and calendar events
- Daily planning: "What must I do today?"

### Flagged

- High-priority items needing focus
- Quick access to critical tasks

### Review

- Projects needing review (by review frequency)
- Enables weekly/monthly review cycles

### Custom Perspectives (Examples)

**Next Actions by Context/Tag**
- Group by tag (@home, @office, @phone)
- Filter: Available tasks only
- Sort by due date

**Waiting For**
- Filter: Tasks with "Waiting For" tag
- Group by project
- Review regularly to follow up

**Stalled Projects**
- Projects with no next actions
- Indicates blocked or unclear projects
- Review and add next actions or put on hold

## Insight Generation with GTD

When analyzing tasks for insights, consider GTD patterns:

**Next Action Gaps:**
- Projects without available next actions are stalled
- Insight: "Project X has no next actions - add concrete steps or put on hold"

**Context Optimization:**
- Many tasks without context tags miss filtering opportunities
- Insight: "12 tasks have no tags - add @home/@office for better filtering"

**Waiting For Tracking:**
- Tasks waiting on others without "Waiting For" tag
- Insight: "Consider adding 'Waiting For' tag to delegation tasks"

**Overdue Clusters:**
- Many overdue tasks suggest planning issues
- Insight: "Project X has 15 overdue tasks - review project viability"

**Someday/Maybe Review:**
- Someday items never reviewed become cruft
- Insight: "20 on-hold projects not reviewed in 90 days - archive or activate?"

## Automation Aligned with GTD

### Plugin Ideas

**Weekly Review Assistant:**
- Guides through GTD weekly review process
- Shows inbox count, projects needing review, stalled projects
- Creates weekly review checklist

**Next Action Generator:**
- Analyzes projects without next actions
- Prompts for concrete next steps
- Ensures projects stay active

**Context Suggester:**
- Analyzes task content to suggest appropriate tags
- Improves context-based filtering

**Waiting For Tracker:**
- Shows all waiting items grouped by project
- Highlights items waiting >X days for follow-up

### Perspective Recommendations

Based on GTD workflow needs:

- **Daily Planning:** Today's due + flagged + deferred until today
- **Next Actions:** Available tasks grouped by tag
- **Waiting For:** Delegated/blocked tasks for follow-up
- **Projects Dashboard:** All active projects with status
- **Someday Review:** On-hold projects for periodic activation

## Common GTD Workflows in OmniFocus

### Processing Inbox

1. For each inbox item, ask: "Is it actionable?"
2. If no → delete, reference, or someday/maybe
3. If yes → is it a project (multi-step) or single task?
4. Add to appropriate project with next action
5. Add tags, due date (if deadline), defer date (if not ready yet)

### Daily Review

1. Check Forecast perspective (what's due today?)
2. Review Flagged (priorities)
3. Choose tasks from Next Actions by current context
4. Update completed tasks

### Weekly Review

1. Process inbox to zero
2. Review all projects for:
   - Next actions defined?
   - Still active or put on hold?
   - Progress made?
3. Review Waiting For (follow up)
4. Review Someday/Maybe (activate anything?)
5. Plan next week's focus

## References

- "Getting Things Done" by David Allen (GTD methodology)
- OmniFocus built-in perspectives align with GTD
- Custom perspectives enable personalized GTD implementation
