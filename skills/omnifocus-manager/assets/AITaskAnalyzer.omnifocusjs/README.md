# AI Analyzer - OmniFocus Plugin

Comprehensive AI-powered analysis for OmniFocus using **Apple Foundation Models (Apple Intelligence)** with two powerful modes:

1. **Task Analyzer** - Daily task insights, priorities, and workload assessment
2. **Project Analyzer** - Recursive project hierarchy analysis with optional tagging and Markdown reports

## Features

### Task Analysis
- 🎯 **Priority Recommendations**: AI-suggested top 3 tasks to tackle first with reasoning
- 📋 **Workload Analysis**: Assessment of whether your workload is manageable
- ⏰ **Overdue Insights**: Pattern detection in overdue tasks with recommendations
- ⏱️ **Time Management**: Suggested schedule based on estimated task durations
- ✅ **Action Items**: Immediate actions to improve your task management

### Project Analysis (NEW in v2.0)
- 📊 **Recursive Folder Analysis**: Analyze entire folder hierarchies maintaining structure
- 🏗️ **Hierarchy Insights**: Evaluation of folder/project organization quality
- 🏥 **Project Health Assessment**: Overall health scoring with strengths and concerns
- 🚧 **Bottleneck Detection**: Identify stalled or problematic projects
- 🎯 **Priority Recommendations**: Areas needing immediate attention
- 📝 **Exposition Tagging**: Automatically tag projects lacking detail (optional)
- 📄 **Markdown Reports**: Export comprehensive analysis reports (optional)
- 📈 **Metrics Dashboard**: Detailed statistics on folders, projects, tasks, and tags

## Requirements

- **OmniFocus 4.8** or later
- **macOS 15.2+**, **iOS 18.2+**, or **iPadOS 18.2+**
- **Apple Silicon** (Mac) or **iPhone 15 Pro+** (for on-device AI processing)

## Installation

1. **Download the Plugin**:
   - Locate `AITaskAnalyzer.omnifocusjs` in your skill assets directory

2. **Install in OmniFocus**:
   - Double-click the `.omnifocusjs` file, OR
   - Drag and drop it onto the OmniFocus application icon, OR
   - In OmniFocus: File → Open → Select the plugin file

3. **Verify Installation**:
   - Go to Tools → AI Analyzer
   - You should see two options:
     - "Analyze My Tasks"
     - "Analyze Projects"

## Usage

### Task Analysis

**What It Analyzes:**
- Tasks due or deferred to today
- Overdue tasks
- Task metadata: projects, tags, due dates, estimates, flagged status

**How to Run:**

**Method 1: Via Tools Menu**
1. Open OmniFocus
2. Go to **Tools → AI Analyzer → Analyze My Tasks**
3. Wait for Apple Intelligence to analyze your tasks
4. Review the insights and recommendations

**Method 2: Via Automation Console**
```javascript
PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer")
  .action("analyzeTasksWithAI")
  .perform()
```

**Sample Output:**
```
📊 AI Analysis of Your Tasks

🎯 TOP PRIORITIES:
1. Call dentist about appointment
   → Time-sensitive, flagged, and only takes 5 minutes

2. Submit expense report
   → Due today with clear deadline, affects reimbursement

3. Review project proposal
   → High-impact decision needed before team meeting

📋 WORKLOAD: ✅ Manageable
You have 8 tasks totaling approximately 3 hours. This is realistic for today.

⏰ OVERDUE INSIGHTS:
Patterns:
• 3 waiting-on tasks are overdue - may need follow-up
• Personal errands tend to slip - consider time-blocking

Recommendations:
• Follow up on waiting items this morning
• Schedule 30min for personal tasks this afternoon

⏱️ SUGGESTED SCHEDULE:
• Morning (9-10am): Quick tasks (calls, emails)
• Mid-morning (10-12pm): Deep work (proposal review)
• Afternoon (2-3pm): Admin tasks (expense report)

✅ ACTION ITEMS:
• Start with the dentist call - quick win
• Block calendar time for proposal review
• Defer 2 low-priority tasks to tomorrow
```

### Project Analysis (NEW)

**What It Analyzes:**
- Selected folder and optionally all subfolders recursively
- All projects within the hierarchy
- Project types (Sequential/Parallel)
- Project status (Active/On Hold/Completed)
- Task statistics per project
- Tags, notes, due dates
- Projects lacking sufficient detail or next actions

**How to Run:**

**Method 1: Via Tools Menu**
1. Open OmniFocus
2. Go to **Tools → AI Analyzer → Analyze Projects**
3. Fill in the analysis form:
   - **Project Scope**: Describe your focus (e.g., "Q1 2025", "Work projects")
   - **Select Folder**: Choose which folder to analyze
   - **Include Subfolders**: Enable for recursive analysis
   - **Tag Projects**: Auto-tag projects needing more detail
   - **Generate Markdown**: Export detailed report to file
   - **Custom Focus**: Optional specific analysis angle
4. Click "Analyze"
5. Wait for AI analysis (may take 10-30 seconds)
6. Review results and optionally save Markdown report

**Method 2: Via Automation Console**
```javascript
PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer")
  .action("analyzeProjects")
  .perform()
```

**Analysis Form Fields:**

| Field | Description | Default |
|-------|-------------|---------|
| Project Scope | Time frame or focus area | Required |
| Select Folder | Root folder to analyze | First folder |
| Include Subfolders | Recursive analysis | ✅ True |
| Tag Projects | Add 'needs-exposition' tag | ❌ False |
| Generate Markdown | Export report to file | ✅ True |
| Custom Focus | Specific analysis angle | Optional |

**Sample Output:**

```markdown
# AI Project Analysis Report

**Generated:** 2025-12-27 10:30:00
**Scope:** Q1 2025 Work Projects
**Root Folder:** Work

## 📊 Project Metrics

**Folders & Projects:**
- Total Folders: 5
- Total Projects: 23
  - Active: 18
  - On Hold: 3
  - Completed: 2
  - Sequential: 8
  - Parallel: 15

**Tasks:**
- Total Tasks: 156
- Active: 89
- Completed: 67
- Flagged: 12
- Overdue: 7

**Health Indicators:**
- Projects without next actions: 4
- Projects without notes: 11
- Unique tags in use: 15

## 🏥 Project Health: Good

Overall structure is solid with good progress across most projects. 
Some attention needed on stalled initiatives.

**Strengths:**
- ✅ Good use of tags for context
- ✅ Most projects have clear next actions
- ✅ Completion rate is healthy (43%)

**Concerns:**
- ⚠️ 4 projects have no next actions defined
- ⚠️ 7 overdue tasks suggest scheduling issues
- ⚠️ 11 projects lack documentation/notes

## 🏗️ Hierarchy Insights

**Organization Quality:** Well-structured with logical groupings

**Suggestions:**
- Consider consolidating similar projects in Marketing folder
- Move completed projects to Archive folder
- Add project notes for context on newer initiatives

## 🚧 Bottlenecks & Issues

1. **Website Redesign**
   - Issue: Stalled for 3 weeks with no progress
   - Recommendation: Schedule planning meeting or put on hold

2. **Q1 Planning**
   - Issue: No next actions defined, due date approaching
   - Recommendation: Break down into concrete tasks immediately

## 🎯 Priority Recommendations

1. 🔴 **Overdue Tasks in Client Projects**
   High urgency - affects client deliverables and reputation

2. 🟡 **Projects Without Next Actions**
   Medium urgency - define next steps to maintain momentum

3. 🟢 **Documentation Gaps**
   Low urgency - add project notes during weekly review

## 📝 Projects Needing More Exposition

1. **Website Redesign**
   - Reason: No notes, unclear scope, stalled progress
   - ✅ Tagged with 'needs-exposition'

2. **New Hire Onboarding**
   - Reason: Sequential project with no documentation
   - ✅ Tagged with 'needs-exposition'

**Tagging Results:**
- Successfully tagged: 2
- Not found: 0
- Errors: 0

## ✅ Action Items

1. Schedule 30min planning session for Website Redesign project
2. Add next actions to all 4 stalled projects today
3. During weekly review: add notes to projects lacking context
4. Review and reschedule the 7 overdue tasks
5. Consider archiving completed projects to reduce clutter
```

## Analysis Workflow

The Project Analyzer follows this systematic workflow:

1. **Define Project Scope** - Clarify time frame and focus areas
2. **Identify and Select Folders** - Choose root folder for analysis
3. **Initial State Analysis** - Gather current metrics and statistics
4. **Recursive Analysis** - Traverse hierarchy maintaining structure
5. **Data Classification** - Categorize Folders, Projects, Tasks, Tags
6. **Tagging Decisions** - Optionally tag projects needing work
7. **Report Generation** - Create Markdown report with findings
8. **Documentation and Review** - Present results and export report

## Markdown Report Structure

When "Generate Markdown" is enabled, reports include:

- **Header**: Timestamp, scope, root folder
- **Metrics Dashboard**: Comprehensive statistics
- **Project Health**: Overall score with strengths/concerns
- **Hierarchy Insights**: Organization quality assessment
- **Bottlenecks**: Specific projects with issues
- **Priority Recommendations**: Urgency-ranked focus areas
- **Projects Needing Exposition**: List with tagging status
- **Action Items**: Concrete next steps

Reports are saved with filename: `OmniFocus_Analysis_[FolderName]_[Date].md`

## Tagging Projects

When "Tag projects needing exposition" is enabled:

1. AI identifies projects lacking:
   - Sufficient notes/documentation
   - Clear next actions
   - Adequate context
   - Progress/momentum

2. Plugin creates or finds tag: `needs-exposition`

3. Automatically tags identified projects

4. Report shows tagging results (success/failures)

5. Use tag in perspectives to review flagged projects

## How It Works

### Task Analysis Architecture

1. **Task Collection**: Retrieves today's and overdue tasks from OmniFocus
2. **Data Preparation**: Structures task data into JSON with metadata
3. **AI Analysis**: Sends to Apple's on-device Language Model
4. **Result Parsing**: Extracts structured insights (JSON schema)
5. **Display**: Formats and presents in user-friendly alert

### Project Analysis Architecture

1. **Form UI**: Interactive form for user configuration
2. **Folder Selection**: Dropdown of all folders with "All Projects" option
3. **Recursive Traversal**: Depth-first hierarchy analysis
4. **Metrics Calculation**: Aggregate statistics across hierarchy
5. **AI Analysis**: Structured schema request for insights
6. **Optional Tagging**: Add `needs-exposition` tag to flagged projects
7. **Report Generation**: Format comprehensive Markdown report
8. **File Export**: FileSaver API for Markdown document

### Privacy & Security

- **100% On-Device**: All AI processing happens locally
- **No Cloud**: Your data never leaves your device
- **No Internet Required**: Works completely offline
- **Apple Privacy**: Privacy-first AI architecture
- **No Data Collection**: Plugin stores nothing

### AI Prompt Design

**Task Analysis:**
- GTD-aligned recommendations
- Concise, actionable insights
- Pattern recognition in behavior
- Practical time management

**Project Analysis:**
- Comprehensive hierarchy evaluation
- Project health assessment
- Bottleneck identification
- Actionable improvement suggestions
- Exposition gap detection

Both use **structured JSON schemas** via `LanguageModel.Session.respondWithSchema()` for reliable parsing.

## Troubleshooting

### "No Apple Intelligence available"
- Ensure macOS 15.2+ or iOS 18.2+
- Verify Apple Silicon (M1/M2/M3/M4) or iPhone 15 Pro+
- Check System Settings → Apple Intelligence is enabled

### "Plugin not appearing in Tools menu"
- Reinstall by double-clicking `.omnifocusjs` file
- Restart OmniFocus completely
- Check Console.app for errors

### "Analysis takes too long"
- Apple Intelligence processing: 5-30 seconds normal
- First run may be slower (model initialization)
- Ensure device not in Low Power Mode
- Large hierarchies (100+ projects) may take longer

### "Error: Failed to analyze"
- Verify OmniFocus 4.8+ installed
- Check compatible OS version
- Try smaller folder selection
- Disable "Include Subfolders" for large hierarchies

### "FileSaver not working"
- Grant OmniFocus file access permissions
- Check disk space available
- Try different save location
- Verify file extension is .md

### "Tagging failed"
- Ensure OmniFocus has write permissions
- Check project IDs are valid
- Review Console.app for specific errors
- Some projects may be read-only

## Customization

### Modifying Task Analysis

Edit `Resources/analyzeTasksWithAI.js`:

**Change prompt** (line 89):
```javascript
const prompt = `Analyze these OmniFocus tasks...`;
```

**Modify schema** (line 107):
```javascript
const schema = {
    type: "object",
    properties: {
        // Add custom fields
    }
};
```

**Adjust filters** (lines 22-44):
```javascript
// Example: Next 3 days instead of today
const threeDaysLater = new Date(today);
threeDaysLater.setDate(threeDaysLater.getDate() + 3);
```

### Modifying Project Analysis

Edit `Resources/analyzeProjects.js`:

**Change analysis focus** (line 89):
```javascript
const basePrompt = `You are analyzing...
// Customize what AI should focus on
`;
```

**Modify schema** (line 120):
```javascript
const schema = {
    properties: {
        // Add/remove analysis fields
    }
};
```

**Change tag name** (line 318):
```javascript
let expositionTag = doc.tags.byName("your-custom-tag");
```

**Adjust metrics** (line 257):
```javascript
// Add custom metric calculations
```

## Best Practices

### Task Analysis
1. **Run Daily**: Part of morning planning routine
2. **Review Patterns**: Check for recurring overdue items
3. **Act on Insights**: Implement AI recommendations
4. **Update Estimates**: Refine based on AI feedback
5. **Tag Consistently**: Better tags = better analysis

### Project Analysis
1. **Weekly Reviews**: Run on major folders weekly
2. **Scope Appropriately**: Focus on relevant time frames
3. **Act on Tags**: Review `needs-exposition` projects
4. **Archive Reports**: Keep Markdown files for comparison
5. **Iterate**: Re-analyze after implementing changes
6. **Use Custom Focus**: Target specific concerns
7. **Compare Over Time**: Track improvement trends

## GTD Integration

### Task Analysis
- **Next Actions**: Identifies what to do next
- **Context Awareness**: Considers tags/contexts
- **Weekly Review**: Spots stalled items
- **Workload Management**: Assesses commitments
- **Priority Clarity**: Removes ambiguity

### Project Analysis
- **Project Review**: Systematic hierarchy evaluation
- **Stalled Project Detection**: Finds lacking next actions
- **Documentation**: Flags projects needing context
- **Organizational Health**: Assesses structure quality
- **Someday/Maybe**: Identifies candidates for deferral

## Version History

### v2.0.0 (2025-12-27)
- **NEW**: Project Analyzer with recursive folder analysis
- **NEW**: Folder selection with subfolder recursion
- **NEW**: Comprehensive metrics dashboard
- **NEW**: Project health scoring
- **NEW**: Hierarchy quality insights
- **NEW**: Bottleneck detection
- **NEW**: Optional `needs-exposition` tagging
- **NEW**: Markdown report generation with FileSaver
- **NEW**: Custom analysis focus field
- Updated manifest with dual actions
- Comprehensive documentation

### v1.0.0 (2025-12-22)
- Initial release
- Task analysis (today + overdue)
- Priority recommendations
- Workload assessment
- Time management suggestions
- GTD-aligned action items

## Support

For issues or questions:
- Check the [omnifocus-manager skill documentation](../../SKILL.md)
- Review [Apple Foundation Models reference](../../references/foundation_models_integration.md)
- Review [Omni Automation Shared API](../../references/omni_automation_shared.md) for Form, FileSaver, Alert APIs
- Visit [omni-automation.com](https://omni-automation.com/omnifocus/) for Omni Automation docs

## License

MIT License - See skill directory for details

## Credits

Created by totally-tools using:
- Omni Automation API
- Apple Foundation Models (Apple Intelligence)
- OmniFocus 4.8+ integration
- Form, Alert, FileSaver, FileWrapper APIs
