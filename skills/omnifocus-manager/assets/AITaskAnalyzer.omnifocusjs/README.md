# AI Analyzer - OmniFocus Plugin

Comprehensive AI-powered analysis for OmniFocus using **Apple Foundation Models (Apple Intelligence)** with four powerful modes:

1. **Task Analyzer** - Daily task insights, priorities, and workload assessment
2. **Project Analyzer** - Recursive project hierarchy analysis with optional tagging and Markdown reports
3. **Selected Task Analyzer** - Detailed per-task analysis with clarity scoring and improvement suggestions
4. **Hierarchical Analyzer** (NEW in v3.2) - Configurable depth analysis with GTD-aligned insights across your entire system

## Features

### Task Analysis (All Today's & Overdue Tasks)
- 🎯 **Priority Recommendations**: AI-suggested top 3 tasks to tackle first with reasoning
- 📋 **Workload Analysis**: Assessment of whether your workload is manageable
- ⏰ **Overdue Insights**: Pattern detection in overdue tasks with recommendations
- ⏱️ **Time Management**: Suggested schedule based on estimated task durations
- ✅ **Action Items**: Immediate actions to improve your task management
- 📋 **Copy to Clipboard**: Export analysis results for reference

### Selected Task Analysis (NEW in v2.1)
- 🎯 **Clarity Scoring**: Rate each task's clarity on a 1-10 scale
- 📝 **Name Suggestions**: AI-recommended improvements to task names
- 🏷️ **Tag Recommendations**: 2-3 relevant tags based on task content
- ⚡ **Priority Assessment**: High/medium/low priority for each task
- ⏱️ **Time Estimates**: AI-suggested completion time in minutes
- 💡 **Specific Improvements**: Actionable suggestions to enhance each task
- ❓ **Missing Information**: Identifies gaps that would help complete tasks
- 📋 **Copy to Clipboard**: Export detailed analysis for all selected tasks

### Project Analysis (NEW in v2.0)
- 📊 **Recursive Folder Analysis**: Analyze entire folder hierarchies maintaining structure
- 🏗️ **Hierarchy Insights**: Evaluation of folder/project organization quality
- 🏥 **Project Health Assessment**: Overall health scoring with strengths and concerns
- 🚧 **Bottleneck Detection**: Identify stalled or problematic projects
- 🎯 **Priority Recommendations**: Areas needing immediate attention
- 📝 **Exposition Tagging**: Automatically tag projects lacking detail (optional)
- 📄 **Markdown Reports**: Export comprehensive analysis reports (optional)
- 📈 **Metrics Dashboard**: Detailed statistics on folders, projects, tasks, and tags

### Hierarchical Analysis (NEW in v3.2)
- 🔧 **Configurable Depth Levels**: Choose analysis scope (Folders Only / Folders + Projects / Complete Hierarchy)
- 📊 **Organizational Health Scoring**: Assess folder structure quality, balance, and GTD alignment (1-10 score)
- 🌊 **Flow & Bottleneck Detection**: Identify stalled projects, missing next actions, and progress blockers
- ⚖️ **Workload Distribution Analysis**: Evaluate task distribution, overcommitment, and capacity balance
- 🔍 **Review Quality Assessment**: Detect neglected areas, aging tasks, and review gaps
- 📝 **Task Clarity Scoring**: Assess individual task actionability and GTD next action quality
- 🎯 **GTD Alignment Score**: Overall system health score based on Getting Things Done principles
- 🧩 **Composable Parser Architecture**: Modular analysis using folderParser, projectParser, and taskParser libraries
- 📦 **Hierarchical Batching**: Smart context window management for large hierarchies
- 📄 **Comprehensive Markdown Reports**: Detailed multi-level analysis with executive summary
- 💾 **Export Options**: Save to file or copy to clipboard

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
   - You should see four options:
     - "Analyze My Tasks"
     - "Analyze Projects"
     - "Analyze Selected"
     - "Analyze Hierarchy"

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

### Selected Task Analysis (NEW in v2.1)

**What It Analyzes:**
- 1-5 tasks that you select in OmniFocus
- Deep analysis of each task individually
- Task metadata: name clarity, project context, tags, dates, estimates
- Opportunities for improvement and missing information

**How to Run:**

**Method 1: Via Tools Menu**
1. Select 1-5 tasks in OmniFocus (inbox, project, or perspective)
2. Go to **Tools → AI Analyzer → Analyze Selected**
3. Wait for Apple Intelligence to analyze each task
4. Review detailed per-task feedback
5. Optionally copy results to clipboard

**Method 2: Via Automation Console**
```javascript
PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer")
  .action("analyzeSelectedTasks")
  .perform()
```

**Sample Output:**
```
TASK: Review Q1 budget proposal

Clarity Score: 6/10

Suggested Name:
→ Review and approve Q1 2025 marketing budget proposal

Priority: HIGH

Est. Time: 45 minutes

Suggested Tags:
  • finance
  • review-needed
  • Q1-planning

Improvements:
  • Add specific deadline or review date
  • Specify what aspects need review (total amount, line items, etc.)
  • Include stakeholders who need to sign off

Missing Information:
  • Who submitted the proposal?
  • What's the approval deadline?
  • Are there specific concerns to watch for?

========================================

TASK: Call dentist

Clarity Score: 9/10

Priority: MEDIUM

Est. Time: 5 minutes

Suggested Tags:
  • phone
  • personal
  • health

Improvements:
  • Add phone number to task note for quick access
  • Specify reason for call (appointment, question, etc.)

Missing Information:
  • What's the purpose of the call?
```

**Usage Tips:**
- Analyze unclear tasks to improve actionability
- Use before weekly review to refine task descriptions
- Copy results and paste into task notes for reference
- Apply suggested tags to improve organization
- Use estimates to better plan your day

### Project Analysis (NEW in v2.0)

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

### Hierarchical Analysis (NEW in v3.2)

**What It Analyzes:**
- Configurable depth: Folders only, Folders + Projects, or Complete Hierarchy including tasks
- System-wide organizational structure and GTD health
- Flow analysis across all projects
- Task quality and workload distribution across your entire system

**How to Run:**

**Method 1: Via Tools Menu**
1. Open OmniFocus
2. Go to **Tools → AI Analyzer → Analyze Hierarchy**
3. Fill in the configuration form:
   - **Analysis Depth**: Choose scope
     - **Folders Only** - Quick organizational structure analysis
     - **Folders + Projects** - Standard analysis with flow/bottleneck detection
     - **Complete Hierarchy** - Deep analysis including task quality
   - **Starting Folder**: Select specific folder or "All Folders"
   - **Include Subfolders Recursively**: Enable for complete hierarchy (default: true)
   - **Generate Markdown Report**: Create formatted report (default: true)
   - **Save Report to File**: Export to file vs. clipboard (default: false)
4. Click "Analyze"
5. Wait for AI analysis (10-60 seconds depending on hierarchy size)
6. Review comprehensive report with GTD-aligned insights

**Method 2: Via Automation Console**
```javascript
PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer")
  .action("analyzeHierarchy")
  .perform()
```

**Depth Level Guide:**

| Depth Level | Analyzes | Use When | Analysis Time |
|-------------|----------|----------|---------------|
| Folders Only | Organizational structure, folder metrics | Quick system health check | 10-20 seconds |
| Folders + Projects | + Flow analysis, bottlenecks, stalled projects | Weekly review, comprehensive overview | 20-40 seconds |
| Complete Hierarchy | + Task quality, workload, clarity scoring | Deep GTD audit, quarterly review | 40-60 seconds |

**Sample Output:**

```markdown
# OmniFocus Hierarchical Analysis Report

**Generated:** 2026-01-10 14:30:00
**Scope:** All Folders
**Depth:** Folders + Projects

---

## Executive Summary

**Overall GTD Alignment Score:** 7.2/10

**Scope:**
- Total Folders: 8
- Total Projects: 47
- Overall Completion Rate: 43%

**Key Findings:**
- Organizational Health: 8.0/10
- Stalled Projects: 3
- Healthy Projects: 32

---

## 1. Organizational Health (Folders)

**Score:** 8.0/10

**Strengths:**
- ✅ Clear separation between work and personal areas
- ✅ Logical folder grouping by life area
- ✅ Balanced project distribution

**Concerns:**
- ⚠️ "Personal" folder has lower completion rate (35%)
- ⚠️ "Someday" folder not reviewed recently (90+ days)

**Recommendations:**
1. Review and prune stalled personal projects
2. Schedule monthly review for Someday/Maybe items
3. Consider archiving completed projects from 2025

---

## 2. Flow & Bottlenecks (Projects)

**Healthy Projects:** 32
**Stalled Projects:** 3

### Bottlenecks Detected:

**1. Website Redesign** (ID: abc123)
- Issue: No available next actions
- Days Stalled: 12
- Recommendation: Add concrete next action or put project on hold

**2. Q1 Planning** (ID: def456)
- Issue: Overdue task accumulation (8 overdue tasks)
- Recommendation: Reschedule with realistic dates or split into smaller milestones

**3. Newsletter Setup** (ID: ghi789)
- Issue: Missing context (no project note)
- Recommendation: Define clear completion criteria and success metrics

### Priority Projects:

**1. Client Proposal** 🔴 High Urgency
- Due in 3 days with several tasks remaining

**2. Team Onboarding** 🟡 Medium Urgency
- Blocking other team members, needs next actions defined

---

## 3. GTD Alignment

**Score:** 7.2/10

**Strengths:**
- Good folder structure supporting contexts
- Most projects have defined next actions
- Regular use of tags for filtering

**Improvements Needed:**
- Add project notes to 5 projects lacking context
- Increase review frequency (30+ days on some projects)
- Clarify vague task language

---

Generated by AITaskAnalyzer v3.2.0
Powered by Apple Foundation Models (on-device AI)
```

**Usage Tips:**
- Run **Folders Only** for quick daily/weekly system health checks
- Use **Folders + Projects** during weekly reviews to identify bottlenecks
- Run **Complete Hierarchy** quarterly for comprehensive GTD audit
- Export reports to track improvement trends over time
- Focus on GTD Alignment Score as your north star metric
- Use bottleneck and priority recommendations as action items

**Context Window Management:**
The hierarchical batcher intelligently splits large hierarchies into batches:
- Folder level: ~20,000 characters per batch
- Project level: ~18,000 characters per batch
- Task level: Maximum 15 tasks per project

This ensures analysis stays within Apple Foundation Models context limits even for very large OmniFocus databases.

**Architecture:**
The Hierarchical Analyzer uses four composable parser libraries:
- `folderParser.js` - Extract folder metrics and hierarchy
- `projectParser.js` - Parse projects with GTD health indicators
- `taskParser.js` - Assess task clarity and actionability
- `hierarchicalBatcher.js` - Manage context windows and AI prompts

This modular design allows for flexible, maintainable analysis at any depth level.

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

### Hierarchical Analysis Architecture

1. **Configuration Form**: User selects depth level, folder scope, and export options
2. **Composable Parsing**: Parse hierarchy to selected depth using modular parser libraries
   - `folderParser.js` - Extract folder metrics and health indicators
   - `projectParser.js` - Parse projects with GTD health assessment
   - `taskParser.js` - Assess task clarity and actionability
3. **Hierarchical Batching**: Create context-friendly batches by level
   - Folder level: Aggregate metrics batches (~20K chars)
   - Project level: Per-folder project batches (~18K chars)
   - Task level: Per-project task batches (max 15 tasks)
4. **Level-by-Level AI Analysis**: Process batches sequentially
   - Generate GTD-aligned prompts for each level
   - Apply level-specific JSON schemas for structured output
   - Aggregate insights across all batches
5. **Insight Aggregation**: Combine results from all levels
   - Organizational health from folder analysis
   - Flow/bottlenecks from project analysis
   - Workload distribution from task analysis
   - Calculate overall GTD alignment score
6. **Report Generation**: Create comprehensive Markdown report with executive summary
7. **Export**: Save to file or copy to clipboard

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

### v3.2.0 (2026-01-10)
- **NEW**: Hierarchical Analyzer action for system-wide analysis with configurable depth
- **NEW**: Four composable parser libraries (folderParser, projectParser, taskParser, hierarchicalBatcher)
- **NEW**: Configurable analysis depth levels (Folders Only / Folders + Projects / Complete Hierarchy)
- **NEW**: Organizational health scoring (1-10) for folder structure assessment
- **NEW**: Flow and bottleneck detection across all projects
- **NEW**: Workload distribution analysis for task balance
- **NEW**: Task clarity scoring with GTD actionability assessment
- **NEW**: GTD Alignment Score - overall system health metric
- **NEW**: Hierarchical batching for context window management (supports large hierarchies)
- **NEW**: Level-by-level AI analysis with GTD-aligned prompts
- **NEW**: Comprehensive Markdown reports with executive summary
- **NEW**: Export to file or clipboard options
- **IMPROVED**: Modular architecture with composable parser libraries
- **IMPROVED**: Smart batch splitting for Foundation Model context limits
- Enhanced documentation with depth level guides and usage tips

### v3.0.0 (2025-12-31)
- **FIXED**: Corrected all library files to use proper OFBundlePlugInTemplate patterns
- **FIXED**: Changed library pattern from incorrect `new PlugIn.Library(function() {...})` to correct `new PlugIn.Library(new Version("3.0"))`
- **IMPROVED**: Added libraries declaration to manifest.json following official Omni Group template structure
- **CLEANED**: Removed development artifacts (TESTING.md, TROUBLESHOOTING.md, validate-structure.sh, test-libraries.js)
- **NOTE**: For plugin development and testing tools, see the omnifocus-manager skill's `assets/development-tools/` directory

### v2.1.0 (2025-12-28)
- **NEW**: Selected Task Analyzer action for detailed per-task analysis
- **NEW**: Clarity scoring (1-10) for individual tasks
- **NEW**: Task name improvement suggestions
- **NEW**: Per-task tag recommendations and priority assessment
- **NEW**: Missing information detection per task
- **NEW**: Copy to Clipboard option for all analyzers
- Enhanced Task Analyzer with clipboard export
- Limit selected task analysis to 5 tasks for performance
- Updated documentation with new analyzer workflow

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
