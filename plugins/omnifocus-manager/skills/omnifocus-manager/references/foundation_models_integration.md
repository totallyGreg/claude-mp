# Apple Foundation Models Integration

This reference explores potential integration points between OmniFocus automation and Apple's Foundation Models (Apple Intelligence) for enhanced task processing.

## Overview

Apple Foundation Models (Apple Intelligence) provide on-device AI capabilities for natural language processing, generation, and understanding. Integration with OmniFocus automation could enable:

- **Smart task creation** - Natural language → structured tasks
- **Intelligent template customization** - Context-aware task templates
- **Enhanced insight generation** - AI-powered pattern detection
- **Natural language queries** - Conversational task analysis

## Current Status

**Note:** As of December 2025, direct API access to Apple Foundation Models is limited. Integration strategies below are conceptual and may require:
- Future API releases
- Shortcuts app as intermediary
- AppleScript/JXA bridges
- Third-party frameworks

## Potential Integration Points

### 1. Natural Language Task Creation

**Concept:** Convert conversational input into structured OmniFocus tasks

**Example Input:**
```
"Remind me to call the dentist next Tuesday at 2pm about the crown,
and make sure I bring the insurance card"
```

**AI Processing:**
- Extract action: "call the dentist"
- Extract due date: "next Tuesday at 2pm"
- Extract note: "about the crown, bring insurance card"
- Suggest tags: @phone, @health
- Suggest project: "Health" or "Personal"

**Output:**
```javascript
// Omni Automation task creation
task.name = "Call dentist about crown";
task.dueDate = new Date("2025-12-29T14:00:00");
task.note = "Bring insurance card";
task.addTag("@phone");
task.addTag("@health");
```

**Implementation Approach:**
- User speaks/types natural language via Shortcuts
- Shortcuts invokes Foundation Models for parsing
- Shortcuts calls Omni Automation via URL scheme
- Task created with extracted structure

### 2. Context-Aware Template Customization

**Concept:** Adapt task templates based on project context

**Example:** "Create project kickoff for redesigning the website"

**AI Processing:**
- Recognize template: "project kickoff"
- Extract project context: "website redesign"
- Customize template tasks:
  - Generic: "Schedule kickoff meeting"
  - Customized: "Schedule website redesign kickoff meeting with design team"
  - Generic: "Define success criteria"
  - Customized: "Define website redesign success criteria (UX, performance, SEO)"

**Benefits:**
- Templates feel personalized, not robotic
- Reduces manual editing after template insertion
- Maintains template structure while adding context

**Implementation Approach:**
```javascript
// Omni Automation plugin + Shortcuts
async function customizeTemplate(templateName, context) {
    // Get base template
    const template = getTemplate(templateName);

    // Send to Shortcuts for AI customization
    const customized = await callShortcutWithAI({
        template: template,
        context: context
    });

    // Create tasks with customized content
    customized.tasks.forEach(t => createTask(t));
}
```

### 3. Intelligent Insight Generation

**Concept:** Use AI to detect patterns and generate actionable insights

**Current Approach (Rule-Based):**
```javascript
// Simple pattern detection
if (project.tasks.filter(t => !t.completed).length === 0) {
    insight = "Project has no next actions";
}
```

**AI-Enhanced Approach:**
```javascript
// AI analyzes task patterns
const projectData = {
    tasks: project.tasks.map(t => ({
        name: t.name,
        due: t.dueDate,
        tags: t.tags,
        completed: t.completed
    }))
};

const insight = await foundationModels.analyze(projectData, {
    prompt: "Analyze this project's task patterns and suggest GTD-aligned improvements"
});

// Result: "This project shows task accumulation without completion.
// Suggested actions: 1) Break large tasks into subtasks,
// 2) Review project scope, 3) Consider deferring low-priority items"
```

**Benefits:**
- Nuanced pattern recognition beyond simple rules
- Contextual recommendations
- Natural language insights

### 4. Natural Language Task Queries

**Concept:** Query tasks conversationally without building complex filters

**Example Queries:**
- "What do I need to do this week at home?"
- "Show me overdue tasks related to the marketing project"
- "What am I waiting for from Sarah?"

**AI Processing:**
- Parse intent (list tasks, filter criteria)
- Extract filters (time: "this week", location: "at home")
- Map to OmniFocus query
- Execute and return results

**Implementation:**
```javascript
async function naturalLanguageQuery(query) {
    // Send to Foundation Models for parsing
    const filters = await parseQuery(query);

    // Map to OmniFocus filters
    const tasks = omnifocus.defaultDocument.flattenedTasks().filter(t => {
        return meetsFilters(t, filters);
    });

    return formatResults(tasks);
}
```

### 5. Smart Task Prioritization

**Concept:** AI-suggested task ordering based on multiple factors

**Factors Analyzed:**
- Due dates and time sensitivity
- Task dependencies
- Historical completion patterns (what time of day/week works best)
- Energy level requirements (inferred from task content)
- Project importance

**Example:**
```
"Help me prioritize today's tasks"

AI Analysis:
1. "Call dentist" - Due today, quick (@phone), morning task
2. "Write proposal" - Due tomorrow, requires focus, current energy high
3. "Review emails" - No deadline, low energy ok, can defer
4. "Update slides" - Due next week, not urgent

Recommendation: Do #1 and #2 now, defer #3 to afternoon, #4 to tomorrow.
```

### 6. Template Discovery and Suggestion

**Concept:** AI identifies recurring patterns and suggests template creation

**Pattern Detection:**
```javascript
// Analyze task history
const analysis = await foundationModels.analyze(taskHistory, {
    prompt: "Identify recurring task patterns suitable for templates"
});

// Result: "You create 'Weekly planning' tasks every Sunday with similar
// subtasks. Consider creating a template."
```

**Auto-Generated Template:**
Based on pattern analysis, suggest template structure:
```javascript
{
    name: "Weekly Planning Template",
    tasks: [
        "Review last week's accomplishments",
        "Process inbox to zero",
        "Review upcoming deadlines",
        "Plan top 3 priorities for week"
    ],
    suggestedDeferDate: "every Sunday at 9:00 AM"
}
```

## Technical Implementation Strategies

### Strategy 1: Shortcuts as Bridge

**Architecture:**
```
OmniFocus (Omni Automation) ↔ Shortcuts App ↔ Foundation Models
```

**Workflow:**
1. Omni Automation plugin triggers Shortcuts
2. Shortcuts invokes Foundation Models API
3. Shortcuts returns processed data
4. Omni Automation creates/updates tasks

**Limitations:**
- Requires user interaction (Shortcuts permission)
- iOS/macOS only (Shortcuts dependency)

### Strategy 2: AppleScript/JXA Bridge

**Architecture:**
```
OmniFocus (JXA) → macOS Automation → Foundation Models → Return to JXA
```

**Workflow:**
```applescript
tell application "Shortcuts Events"
    run shortcut "Process Task with AI" with input taskData
end tell
```

**Limitations:**
- macOS only
- Requires Shortcuts automation setup

### Strategy 3: External Processing (Current Approach)

**Architecture:**
```
OmniFocus → Export data → Claude/AI → Generate automation → Import to OmniFocus
```

**Workflow:**
1. Export tasks via JXA or Python queries
2. Process with Claude or other AI
3. Generate Omni Automation plugin code
4. Install and run plugin

**Benefits:**
- Works today (no future API required)
- Flexible AI model selection
- Full control over processing

**Current Use:**
- This skill uses this approach
- Claude analyzes patterns and generates plugins
- User installs generated automation

## Example Use Cases

### Use Case 1: Meeting Prep Automation

**Input (Natural Language):**
"I have a client meeting with Acme Corp tomorrow at 10am"

**AI Processing:**
- Detect event type: client meeting
- Extract details: client name (Acme Corp), time (tomorrow 10am)
- Load meeting prep template
- Customize for client context

**Output (Tasks Created):**
- "Review Acme Corp account status" (due: today)
- "Prepare Acme Corp meeting agenda" (due: today)
- "Client meeting: Acme Corp" (due: tomorrow 10am, flagged)
- "Send Acme Corp meeting notes" (defer: tomorrow 11am)

### Use Case 2: Project Health Check

**Input:** User requests: "Analyze my projects"

**AI Processing:**
- Review all active projects
- Detect patterns:
  - Projects without next actions
  - Projects with many overdue tasks
  - Projects with no recent activity
  - Waiting items >30 days old

**Output (Insights):**
```
Project Health Report:

⚠️ Stalled Projects (3):
- "Website Redesign" - no next actions defined
- "Q1 Planning" - last activity 45 days ago
- "Vendor Search" - waiting on 3 items >30 days

✅ Healthy Projects (5):
- "Newsletter" - 3 next actions, on track
- "Product Launch" - active, due dates clear
...

Recommendations:
1. Add next actions to stalled projects or put on hold
2. Follow up on waiting items
3. Consider archiving inactive projects
```

### Use Case 3: Smart Daily Planning

**Input:** Morning routine: "Plan my day"

**AI Processing:**
- Analyze calendar (via Calendar app integration)
- Review OmniFocus tasks (due today, flagged, available)
- Consider time blocks between meetings
- Match tasks to available time slots

**Output:**
```
Your Day Plan:

8:00-9:00 AM (Before meetings):
- Process inbox (15 min)
- Review emails (@computer, low energy)

11:00-12:00 PM (Between meetings):
- Write proposal draft (@computer, high focus)

2:00-3:00 PM (Afternoon focus):
- Call dentist (@phone, quick)
- Review project status (@computer)

4:00-5:00 PM (End of day):
- Update task statuses
- Plan tomorrow

Flagged items carried over if time permits.
```

## Future Possibilities

As Apple Foundation Models APIs evolve, additional capabilities may include:

**Voice-First Task Management:**
- Speak to Siri: "Show my home tasks"
- Natural conversation: "What's next?" → AI suggests based on context

**Contextual Awareness:**
- Location: At @home → surface @home tasks
- Time of day: Morning → suggest high-energy tasks
- Calendar: Before meeting → suggest prep tasks

**Proactive Suggestions:**
- "You usually review email at 9am - want to do that now?"
- "Project X review is due this week - schedule time?"
- "Three tasks waiting >30 days - follow up?"

**Learning User Patterns:**
- Best task completion times
- Preferred task groupings
- Energy level throughout day
- Realistic time estimates

## Current Limitations

**API Access:**
- Limited public API for Foundation Models (as of Dec 2025)
- Shortcuts provides some access but requires user interaction
- No direct programmatic Foundation Models API

**Privacy:**
- On-device processing is ideal (Apple's approach)
- Task data is sensitive - prefer local processing
- Cloud AI (like Claude) requires data export

**Integration Complexity:**
- Omni Automation → Shortcuts → AI requires multiple hops
- Error handling across boundaries
- User permission requirements

## Recommended Approach (Today)

Until direct Foundation Models API is available:

**1. Use Claude (this skill) for:**
- Generating Omni Automation plugins based on patterns
- Creating custom perspectives
- Analyzing task data for insights
- Designing automation workflows

**2. Use Shortcuts for:**
- Simple natural language task capture
- Triggering Omni Automation plugins
- Basic AI integration via Shortcuts AI features

**3. Use Omni Automation for:**
- Executing generated automation
- Reusable plugins (token-efficient)
- Cross-platform support (Mac + iOS)

**Workflow:**
1. User describes need to Claude
2. Claude analyzes task patterns
3. Claude generates Omni Automation plugin
4. User installs and runs plugin
5. Plugin executes on-device (fast, private)

## Resources

**Skill References:**
- `omnifocus_automation.md` - OmniFocus Omni Automation API reference
- `omni_automation_shared.md` - Shared Omni Automation classes (Alert, Form, etc.)
- `OmniFocus-API.md` - Complete OmniFocus API specification

**External Resources:**
- Apple Intelligence overview: apple.com/apple-intelligence
- Apple Language Models: omni-automation.com/shared/alm.html
- Shortcuts app automation
- Omni Automation documentation: omni-automation.com
- AppleScript/JXA for macOS automation

**Note:** This reference will be updated as Apple releases Foundation Models APIs and integration methods evolve.
