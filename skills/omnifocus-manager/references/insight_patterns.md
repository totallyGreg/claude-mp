# OmniFocus Insight Patterns

This reference documents common patterns to detect in OmniFocus data and what they reveal about task management health.

## Pattern Categories

Insights fall into these categories:
1. **Blockers** - What's preventing progress
2. **Health Issues** - Signs of poor task management
3. **Optimization Opportunities** - Ways to improve workflow
4. **GTD Alignment** - How well following GTD principles

## Blocker Patterns

### Pattern: Stalled Projects

**Detection:**
- Active project with zero available (next) actions
- All tasks either completed, blocked by dependencies, or deferred to future

**What It Means:**
- Project is stuck - can't make progress
- Unclear what to do next
- Possibly waiting on external input

**Insight Message:**
```
"Project 'Website Redesign' has no next actions. This project is stalled.

Suggested actions:
- Add concrete next action(s)
- If waiting on someone, add 'Waiting For' tag
- If not ready to work on, put project On Hold"
```

**Code Detection:**
```javascript
const availableTasks = project.tasks.filter(t =>
    !t.completed() &&
    t.taskStatus() === Task.Status.Available
);

if (project.status() === Project.Status.Active && availableTasks.length === 0) {
    return {
        type: "BLOCKER",
        pattern: "Stalled Project",
        project: project.name(),
        recommendation: "Add next action or put On Hold"
    };
}
```

### Pattern: Waiting For Items (Aging)

**Detection:**
- Tasks with "Waiting For" tag that haven't been updated in >30 days
- Indicates items waiting on others that may need follow-up

**What It Means:**
- External dependencies not followed up
- Risk of forgetting delegated items
- May indicate blocked progress

**Insight Message:**
```
"5 tasks tagged 'Waiting For' are older than 30 days:
- 'Waiting: Design mockups from Sarah' (45 days)
- 'Waiting: Budget approval from finance' (38 days)
...

Consider following up or re-evaluating these blocked items."
```

### Pattern: Dependency Chains

**Detection:**
- Multiple tasks in sequence where each blocks the next
- Long chains indicate potential bottlenecks

**What It Means:**
- Project may move slowly due to sequential dependencies
- Consider parallelizing work where possible

**Insight Message:**
```
"Project 'Product Launch' has a 7-task dependency chain.
If any task is delayed, all downstream tasks are blocked.

Consider:
- Which tasks could run in parallel?
- Can dependencies be reduced?
- Add buffer time to avoid cascade delays"
```

## Health Issue Patterns

### Pattern: Overdue Accumulation

**Detection:**
- Many overdue tasks (>10) in a project
- Due dates consistently in the past

**What It Means:**
- Unrealistic planning or scope creep
- Due dates used as "wish dates" not deadlines
- Project may need re-scoping

**Insight Message:**
```
"Project 'Q4 Planning' has 15 overdue tasks (oldest: 45 days overdue).

This suggests:
- Due dates may not be realistic deadlines
- Project scope may be too large
- Consider reviewing project viability

Recommendations:
- Reschedule tasks with realistic dates
- Drop low-priority tasks
- Split into smaller projects"
```

### Pattern: Inbox Overflow

**Detection:**
- Inbox has >20 unprocessed items
- Items aging in inbox >7 days

**What It Means:**
- Capture is happening but processing is not
- Violates GTD principle of processing to zero
- Risk of losing track of commitments

**Insight Message:**
```
"Inbox contains 32 items, oldest added 12 days ago.

This indicates processing is falling behind capture.

Schedule time to:
1. Process all inbox items (15-30 min)
2. Add to projects or delete
3. Aim for inbox zero daily"
```

### Pattern: Tag-less Tasks

**Detection:**
- Many tasks (>15) without any tags/contexts
- Limits ability to filter by location/context

**What It Means:**
- Missing context information
- Can't use context-based perspectives effectively
- Harder to filter "what can I do now?"

**Insight Message:**
```
"47 tasks have no tags assigned.

Adding tags enables better filtering:
- @home - tasks to do at home
- @office - work tasks
- @computer - requires computer
- @phone - calls to make

Consider creating 'Next Actions by Context' perspective to see value of tagging."
```

### Pattern: Someday/Maybe Neglect

**Detection:**
- On Hold projects that haven't been reviewed in >90 days
- Someday/Maybe list growing without review

**What It Means:**
- Someday items becoming forgotten cruft
- Not following GTD weekly review of Someday/Maybe

**Insight Message:**
```
"18 On Hold projects haven't been reviewed in over 90 days.

Someday/Maybe items need periodic review:
- Still interested? Move to Active
- No longer relevant? Archive/Delete
- Not ready yet? Keep On Hold

Add to next weekly review agenda."
```

## Optimization Opportunities

### Pattern: Repeated Manual Tasks

**Detection:**
- Similar task names created repeatedly
- Examples: "Weekly planning", "Process inbox", "Team meeting prep"

**What It Means:**
- Opportunity for task template or repeating task
- Time wasted recreating same task structure

**Insight Message:**
```
"Detected recurring pattern: 'Weekly planning' tasks created 8 times in last 2 months.

Optimization opportunity:
- Create weekly repeating task, or
- Create task template plugin

Would you like help creating a template?"
```

### Pattern: Perspective Opportunity

**Detection:**
- User frequently creates similar ad-hoc filters
- Example: repeatedly viewing "tasks at @home" or "overdue items"

**What It Means:**
- Common view that deserves a dedicated perspective
- Time wasted recreating same filter

**Insight Message:**
```
"Detected frequent filtering by '@home' tag.

Consider creating custom perspective:
- Name: 'Next Actions at Home'
- Filter: Tag = @home, Status = Available
- Keyboard shortcut: ⌘1 for quick access

This saves time vs manual filtering."
```

### Pattern: Underutilized Features

**Detection:**
- No use of deferred dates (everything starts now)
- No time estimates (can't gauge workload)
- No review frequencies set on projects

**What It Means:**
- Missing productivity features
- Could improve planning and workload awareness

**Insight Message:**
```
"0 tasks use defer dates. Defer dates hide tasks until you're ready to work on them.

Example use cases:
- Task for next week? Defer to Monday
- Follow-up in 3 days? Defer to then
- Reduces noise in task lists

Try adding defer dates to future tasks."
```

### Pattern: Flag Overuse/Underuse

**Detection (Overuse):**
- >30% of tasks are flagged
- Flags lose meaning when overused

**Detection (Underuse):**
- <5% of tasks flagged
- Missing quick priority indicator

**What It Means:**
- Flags should highlight true priorities
- Too many = everything is important = nothing is
- Too few = not using priority system

**Insight Message (Overuse):**
```
"45 of 120 tasks (37%) are flagged.

When most tasks are flagged, flags lose their purpose.

Guidelines:
- Flag <10% of tasks (only top priorities)
- Use for 'must do today' items
- Unflag when completed or priority drops

Review flagged tasks and unflag non-critical items."
```

## GTD Alignment Patterns

### Pattern: Next Action Clarity

**Detection:**
- Task names are vague: "Deal with X", "Figure out Y", "Think about Z"
- Not concrete, physical, visible actions

**What It Means:**
- Violates GTD next action principle
- Tasks are unclear, lead to procrastination
- Should be specific and actionable

**Insight Message:**
```
"Detected vague task names:
- 'Deal with email backlog' → not a concrete action
- 'Think about vacation' → what's the actual next action?

GTD next actions should be specific:
- 'Deal with email backlog' → 'Process 20 oldest emails in inbox'
- 'Think about vacation' → 'Research flight prices to Hawaii'

Concrete actions are easier to start and complete."
```

### Pattern: Project Without Purpose

**Detection:**
- Project note field is empty
- No clear outcome defined

**What It Means:**
- Unclear why project exists
- Hard to know when it's "done"
- GTD: projects need clear desired outcome

**Insight Message:**
```
"5 active projects have no project note/outcome defined.

GTD principle: Projects should have clear desired outcome.

Example:
- Project: 'Website Redesign'
- Outcome: 'New website live with improved UX, faster load times, mobile responsive'

This clarifies when the project is complete and guides next actions."
```

### Pattern: Missing Weekly Review

**Detection:**
- No project review frequencies set
- Projects not reviewed regularly
- "Last Reviewed" dates >30 days old

**What It Means:**
- Not following GTD weekly review
- Projects drift without regular attention

**Insight Message:**
```
"12 projects haven't been reviewed in over 30 days.

GTD weekly review is essential:
- Review all projects weekly
- Ensure next actions are defined
- Update status/priorities

Set review frequency:
- Right-click project → Review → Set review frequency
- Recommended: Weekly for active projects"
```

## Composite Patterns (Multiple Signals)

### Pattern: Project Death Spiral

**Detection (Multiple Signals):**
- Overdue tasks accumulating
- No next actions defined
- Not reviewed in >30 days
- Tasks being deferred repeatedly

**What It Means:**
- Project is failing but not officially abandoned
- Consuming mental energy without progress

**Insight Message:**
```
"Warning: Project 'Learn Spanish' shows multiple warning signs:
- 8 overdue tasks
- No available next actions
- Last reviewed 47 days ago
- Tasks deferred 4+ times

This project may be in a 'death spiral'.

Recommendation:
- Re-commit (add next actions, review regularly), or
- Move to Someday/Maybe, or
- Drop the project entirely

Zombie projects drain energy without providing value."
```

### Pattern: Thriving Project

**Detection (Positive Signals):**
- Regular task completion
- Always has 2-5 next actions
- Reviewed on schedule
- No overdue accumulation

**What It Means:**
- Healthy project execution
- Good example to learn from

**Insight Message:**
```
"✓ Project 'Newsletter Production' shows excellent health:
- Reviewed weekly (last: 2 days ago)
- Maintains 3 next actions consistently
- Tasks completed on time
- No overdue accumulation

This project demonstrates good task management.
Consider applying similar patterns to other projects."
```

## Seasonal Patterns

### Pattern: Friday Task Pile-Up

**Detection:**
- Many tasks deferred to Friday
- Friday has 3x more tasks than other days

**What It Means:**
- Procrastination pattern
- Unrealistic expectations for Friday productivity

**Insight Message:**
```
"Pattern detected: 15 tasks deferred to this Friday vs 5/day earlier in week.

This creates unrealistic Friday workload.

Consider:
- Distribute tasks across week
- Friday is often low-energy day
- Some tasks could start earlier in week"
```

### Pattern: Monday Morning Overload

**Detection:**
- Many tasks with Monday 9am due dates
- Weekend task accumulation

**What It Means:**
- Trying to do too much Monday morning
- May create stressful week start

**Insight Message:**
```
"18 tasks due Monday at 9am.

This creates overwhelming week start.

Recommendation:
- Spread tasks across Monday-Tuesday
- Prioritize top 3 for Monday morning
- Defer lower priority to later in week"
```

## Code Integration Examples

### Insight Runner (Omni Automation)

```javascript
function analyzeTaskPatterns() {
    const insights = [];
    const doc = Application('OmniFocus').defaultDocument;

    // Check each pattern
    insights.push(...detectStalledProjects(doc));
    insights.push(...detectOverdueAccumulation(doc));
    insights.push(...detectInboxOverflow(doc));
    insights.push(...detectTaglessTasksPattern(doc));

    return insights;
}

function detectStalledProjects(doc) {
    const insights = [];
    const projects = doc.flattenedProjects().filter(p =>
        p.status() === Project.Status.Active
    );

    projects.forEach(project => {
        const available = project.tasks().filter(t =>
            !t.completed() && t.taskStatus() === Task.Status.Available
        );

        if (available.length === 0 && project.tasks().length > 0) {
            insights.push({
                type: "BLOCKER",
                severity: "HIGH",
                pattern: "Stalled Project",
                project: project.name(),
                message: `Project '${project.name()}' has no next actions.`,
                recommendation: "Add concrete next action or put On Hold"
            });
        }
    });

    return insights;
}
```

## Insight Presentation

Format insights for actionable output:

```
========================================
OmniFocus Health Report
========================================

BLOCKERS (2):
⚠️ Project 'Website Redesign' has no next actions
   → Add next action or put On Hold

⚠️ 5 waiting items >30 days old
   → Follow up or re-evaluate

HEALTH ISSUES (3):
⚠️ Inbox has 32 unprocessed items (oldest: 12 days)
   → Schedule processing time

⚠️ 47 tasks without tags
   → Add context tags for better filtering

⚠️ Project 'Q4 Planning' has 15 overdue tasks
   → Reschedule or re-scope project

OPPORTUNITIES (2):
💡 Recurring 'Weekly planning' tasks detected
   → Create template to save time

💡 Frequent '@home' filtering detected
   → Create custom perspective

========================================
Overall Health: 6.5/10
Next Steps: Address blockers first
========================================
```

## Using Insights

**Daily Review:**
- Run insight analysis
- Address high-severity blockers
- Note optimization opportunities

**Weekly Review:**
- Review all insight categories
- Track patterns over time
- Adjust workflows based on insights

**Automation:**
- Create Omni Automation plugin for automatic analysis
- Schedule weekly insight report
- Email or notification with findings
