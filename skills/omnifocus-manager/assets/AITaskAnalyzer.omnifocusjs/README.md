# AI Task Analyzer - OmniFocus Plugin

Analyzes your today's and overdue tasks using **Apple Foundation Models (Apple Intelligence)** to provide intelligent insights about your workload, priorities, and actionable recommendations.

## Features

- 🎯 **Priority Recommendations**: AI-suggested top 3 tasks to tackle first with reasoning
- 📋 **Workload Analysis**: Assessment of whether your workload is manageable
- ⏰ **Overdue Insights**: Pattern detection in overdue tasks with recommendations
- ⏱️ **Time Management**: Suggested schedule based on estimated task durations
- ✅ **Action Items**: Immediate actions to improve your task management

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
   - Go to Tools → AI Task Analyzer
   - The plugin should appear in the menu

## Usage

### Running the Analysis

**Method 1: Via Tools Menu**
1. Open OmniFocus
2. Go to **Tools → AI Task Analyzer**
3. Wait for Apple Intelligence to analyze your tasks
4. Review the insights and recommendations

**Method 2: Via Automation Console**
1. Press **⌃⌥⌘I** to open the Automation Console
2. Type: `PlugIn.find("com.totallytools.omnifocus.ai-task-analyzer").action("analyzeTasksWithAI").perform()`
3. Press Enter

**Method 3: Via Keyboard Shortcut** (Optional)
1. Go to System Settings → Keyboard → Shortcuts → App Shortcuts
2. Add new shortcut for OmniFocus
3. Menu Title: "AI Task Analyzer"
4. Assign your preferred keyboard shortcut

### What Gets Analyzed

The plugin analyzes:
- **Today's Tasks**: Tasks due or deferred to today
- **Overdue Tasks**: Tasks with due dates in the past

For each task, it considers:
- Task name and project
- Due dates and times
- Flagged status
- Tags/contexts
- Estimated time duration
- How many days overdue (if applicable)

### Sample Output

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

## How It Works

### Technical Architecture

1. **Task Collection**: Retrieves today's and overdue tasks from OmniFocus using Omni Automation API
2. **Data Preparation**: Structures task data into JSON format with relevant metadata
3. **AI Analysis**: Sends data to Apple's on-device Language Model with a structured schema
4. **Result Parsing**: Parses JSON response containing insights and recommendations
5. **Display**: Formats and presents analysis in a user-friendly alert

### Privacy & Security

- **100% On-Device**: All AI processing happens locally on your device
- **No Cloud**: Your task data never leaves your Mac/iPhone/iPad
- **No Internet Required**: Works completely offline
- **Apple Privacy**: Leverages Apple's privacy-first AI architecture

### AI Prompt Design

The plugin uses a carefully crafted prompt that requests:
- GTD-aligned (Getting Things Done) recommendations
- Concise, actionable insights
- Pattern recognition in task behavior
- Practical time management suggestions

The response is requested in **structured JSON format** using `LanguageModel.Session.respondWithSchema()` for reliable parsing.

## Troubleshooting

### "No Apple Intelligence available"
- Ensure you have macOS 15.2+ or iOS 18.2+
- Verify you have Apple Silicon (M1/M2/M3/M4) or iPhone 15 Pro+
- Check System Settings → Apple Intelligence is enabled

### "Plugin not appearing in Tools menu"
- Reinstall by double-clicking the `.omnifocusjs` file
- Restart OmniFocus completely
- Check Console.app for any error messages

### "Analysis takes too long"
- Apple Intelligence processing can take 5-30 seconds
- First run may be slower as models initialize
- Ensure your device isn't in Low Power Mode

### "Error: Failed to analyze tasks"
- Verify OmniFocus 4.8+ is installed
- Check you have compatible OS version
- Try with fewer tasks (close some projects)

## Customization

### Modifying the Analysis

You can customize what the AI analyzes by editing the `analyzeTasksWithAI.js` file:

**Change the prompt** (line 89):
```javascript
const prompt = `Analyze these OmniFocus tasks and provide...`;
```

**Modify the schema** (line 107):
```javascript
const schema = {
    type: "object",
    properties: {
        // Add your own analysis fields here
    }
};
```

**Adjust task filters** (lines 22-44):
```javascript
// Example: Include next 3 days instead of just today
const threeDaysLater = new Date(today);
threeDaysLater.setDate(threeDaysLater.getDate() + 3);
```

## Best Practices

1. **Run Daily**: Best used as part of your morning planning routine
2. **Review Regularly**: Check for patterns in overdue tasks
3. **Act on Insights**: Don't just read - implement the recommendations
4. **Adjust Estimates**: Update task time estimates based on AI feedback
5. **Tag Consistently**: Better tags = better AI analysis

## GTD Integration

This plugin aligns with GTD (Getting Things Done) methodology:

- **Next Actions**: Identifies which tasks to do next
- **Context Awareness**: Considers tags/contexts in recommendations
- **Weekly Review**: Helps identify stalled projects and overdue items
- **Workload Management**: Assesses if you're overcommitted
- **Priority Clarity**: Removes ambiguity about what matters most

## Version History

### v1.0.0 (2025-12-22)
- Initial release
- Today's tasks analysis
- Overdue tasks insights
- Priority recommendations
- Workload assessment
- Time management suggestions
- GTD-aligned action items

## Support

For issues or questions:
- Check the [omnifocus-manager skill documentation](../../SKILL.md)
- Review [Apple Foundation Models reference](../../references/foundation_models_integration.md)
- Visit [omni-automation.com](https://omni-automation.com/omnifocus/) for Omni Automation docs

## License

MIT License - See skill directory for details

## Credits

Created by totally-tools using:
- Omni Automation API
- Apple Foundation Models (Apple Intelligence)
- OmniFocus 4.8+ integration
