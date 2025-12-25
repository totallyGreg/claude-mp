# Omni Automation Shared Classes & Methods

Complete reference for shared classes and methods that work across all Omni Automation apps: OmniFocus, OmniGraffle, OmniOutliner, and OmniPlan.

## Overview

To ensure a consistent scripting experience across all Omni applications, certain Omni Automation objects and methods are shared and work uniformly in each app. These shared APIs provide common functionality for alerts, file handling, data processing, and system integration.

**Source:** [omni-automation.com/shared](https://omni-automation.com/shared/index.html)

## Core Shared Classes

### Alert

Dialog and notification functionality for user interaction.

**Common Uses:**
- Display information to users
- Get user confirmations
- Show error messages
- Present choices with buttons

**Example:**
```javascript
const alert = new Alert("Task Complete", "Your task has been processed successfully.");
alert.addOption("OK");
alert.show();
```

**Documentation:** [omni-automation.com/shared/alert](https://omni-automation.com/shared/alert.html)

### Form

Interactive forms for collecting structured user input.

**Common Uses:**
- Collect multiple fields of input
- Create plugin configuration dialogs
- Build data entry interfaces
- Get user preferences

**Example:**
```javascript
const form = new Form();
form.addField(new Form.Field.String("name", "Task Name"));
form.addField(new Form.Field.Date("due", "Due Date"));
const formObject = await form.show("Create Task", "OK");
```

**Documentation:** [omni-automation.com/shared/form](https://omni-automation.com/shared/form.html)

### FilePicker

File selection dialogs for opening files.

**Common Uses:**
- Let users select files to import
- Choose documents to attach
- Pick images or media files
- Select multiple files

**Example:**
```javascript
const picker = new FilePicker();
picker.types = [FileTypes.Text, FileTypes.PDF];
const urls = await picker.show();
```

**Documentation:** [omni-automation.com/shared/filepicker](https://omni-automation.com/shared/filepicker.html)

### FileSaver

File saving dialogs for exporting data.

**Common Uses:**
- Export data to files
- Save generated reports
- Create backups
- Export task lists

**Example:**
```javascript
const saver = new FileSaver();
saver.nameLabel = "Export tasks as:";
const url = await saver.show();
// Write data to url
```

**Documentation:** [omni-automation.com/shared/filesaver](https://omni-automation.com/shared/filesaver.html)

### FileWrapper

File wrapper objects for handling file data.

**Common Uses:**
- Read file contents
- Create attachments
- Handle binary data
- Process file metadata

**Documentation:** [omni-automation.com/shared/filewrapper](https://omni-automation.com/shared/filewrapper.html)

### Color

Color management and manipulation.

**Common Uses:**
- Set tag colors
- Define custom colors
- Convert color formats
- Apply styling

**Example:**
```javascript
const red = Color.RGB(1.0, 0.0, 0.0);
const blue = Color.blue;
const custom = Color.RGB(0.5, 0.3, 0.8, 1.0);
```

**Documentation:** [omni-automation.com/shared/color](https://omni-automation.com/shared/color.html)

### URL

URL handling, components, fetching, and callbacks.

**Features:**
- **URL.Components** - Parse and build URLs
- **URL.Fetch** - Download content from URLs
- **URL.Call** - Handle URL callbacks
- **URL.Bookmarks** - Manage file bookmarks
- **URL.OmniLinks** - Create links between Omni apps

**Common Uses:**
- Parse URL parameters
- Fetch web content
- Create custom URL schemes
- Handle x-callback-url patterns

**Example:**
```javascript
// Parse URL
const components = URL.Components.fromString("omnifocus:///task/abc123");

// Fetch web content
const request = URL.FetchRequest.fromString("https://api.example.com/data");
const response = await request.fetch();

// Open URL
URL.fromString("https://example.com").open();
```

**Documentation:** [omni-automation.com/shared/url](https://omni-automation.com/shared/url.html)

### Pasteboard

Clipboard access for reading and writing data.

**Common Uses:**
- Copy task data to clipboard
- Paste content into tasks
- Share data between apps
- Export formatted text

**Example:**
```javascript
// Copy to clipboard
Pasteboard.general.string = "Task data";

// Read from clipboard
const clipboardText = Pasteboard.general.string;
```

**Documentation:** [omni-automation.com/shared/pasteboard](https://omni-automation.com/shared/pasteboard.html)

### Calendar

Calendar integration and date operations.

**Common Uses:**
- Access calendar events
- Schedule tasks around meetings
- Check availability
- Integrate with Calendar app

**Documentation:** [omni-automation.com/shared/calendar](https://omni-automation.com/shared/calendar.html)

### Device

Device information and capabilities.

**Common Uses:**
- Detect platform (macOS vs iOS)
- Check device capabilities
- Adapt UI for device type
- Platform-specific features

**Example:**
```javascript
const isIOS = Device.current.iOS;
const isMac = Device.current.macOS;
const deviceName = Device.current.name;
```

**Documentation:** [omni-automation.com/shared/device](https://omni-automation.com/shared/device.html)

### Notification

System notification display.

**Common Uses:**
- Show completion notifications
- Alert user of background events
- Remind about tasks
- Provide status updates

**Example:**
```javascript
const notification = new Notification("Task Complete", "Your weekly review is finished.");
notification.show();
```

**Documentation:** [omni-automation.com/shared/notification](https://omni-automation.com/shared/notification.html)

### Speech (TTS)

Text-to-speech functionality.

**Common Uses:**
- Read task names aloud
- Provide audio feedback
- Accessibility features
- Voice notifications

**Example:**
```javascript
Speech.speak("You have 5 tasks due today");
```

**Documentation:** [omni-automation.com/shared/speech](https://omni-automation.com/shared/speech.html)

### Timer

Timing and scheduling functionality.

**Common Uses:**
- Delay execution
- Schedule recurring actions
- Implement timeouts
- Rate limiting

**Example:**
```javascript
const timer = new Timer();
timer.interval = 5.0; // seconds
timer.action = () => {
    console.log("5 seconds elapsed");
};
timer.schedule();
```

**Documentation:** [omni-automation.com/shared/timer](https://omni-automation.com/shared/timer.html)

## Data Processing

### Data

Data object handling and conversion.

**Common Uses:**
- Convert between data formats
- Handle binary data
- Base64 encoding/decoding
- Data serialization

**Documentation:** [omni-automation.com/shared/data](https://omni-automation.com/shared/data.html)

### XML

XML parsing and generation.

**Common Uses:**
- Parse XML responses
- Generate XML data
- Process structured data
- API integration

**Example:**
```javascript
const xmlString = "<tasks><task>Buy groceries</task></tasks>";
const xmlDoc = XML.parse(xmlString);
const tasks = xmlDoc.rootElement.children;
```

**Documentation:** [omni-automation.com/shared/xml](https://omni-automation.com/shared/xml.html)

### Credentials

Authentication and credential management.

**Common Uses:**
- Store API keys securely
- Manage passwords
- OAuth token handling
- Secure credential storage

**Documentation:** [omni-automation.com/shared/credentials](https://omni-automation.com/shared/credentials.html)

## Formatters

### DateFormatter

Format dates for display.

**Example:**
```javascript
const formatter = Formatter.Date.withStyle(Formatter.Date.Style.short);
const dateString = formatter.stringFromDate(new Date());
```

**Documentation:** [omni-automation.com/shared/dateformatter](https://omni-automation.com/shared/dateformatter.html)

### DecimalFormatter

Format numbers and decimals.

**Common Uses:**
- Format currency
- Display percentages
- Round numbers
- Localized number formatting

**Documentation:** [omni-automation.com/shared/decimalformatter](https://omni-automation.com/shared/decimalformatter.html)

### DurationFormatter

Format time durations.

**Common Uses:**
- Display task estimates
- Format elapsed time
- Show remaining time
- Duration calculations

**Documentation:** [omni-automation.com/shared/durationformatter](https://omni-automation.com/shared/durationformatter.html)

## Geometric Objects

### Point

2D point representation.

**Properties:**
- `x` - X coordinate
- `y` - Y coordinate

**Documentation:** [omni-automation.com/shared/point](https://omni-automation.com/shared/point.html)

### Size

2D size representation.

**Properties:**
- `width` - Width value
- `height` - Height value

**Documentation:** [omni-automation.com/shared/size](https://omni-automation.com/shared/size.html)

### Rect

2D rectangle representation.

**Properties:**
- `origin` - Point (x, y)
- `size` - Size (width, height)

**Documentation:** [omni-automation.com/shared/rect](https://omni-automation.com/shared/rect.html)

## Array Extensions

Enhanced array methods for data manipulation.

**Common Uses:**
- Filter and transform arrays
- Find elements
- Sort data
- Array operations

**Documentation:** [omni-automation.com/shared/array](https://omni-automation.com/shared/array.html)

## Date Extensions

Enhanced date methods and utilities.

**Common Uses:**
- Date arithmetic
- Date comparisons
- Format dates
- Extract components

**Documentation:** [omni-automation.com/shared/date](https://omni-automation.com/shared/date.html)

## Share Panel

System share sheet integration.

**Common Uses:**
- Share task data via email
- Export to other apps
- Send to Messages
- AirDrop content

**Example:**
```javascript
const sharePanel = new SharePanel();
sharePanel.items = [taskData];
await sharePanel.show();
```

**Documentation:** [omni-automation.com/shared/sharepanel](https://omni-automation.com/shared/sharepanel.html)

## Audio

Sound playback functionality.

**Common Uses:**
- Play completion sounds
- Audio feedback
- Alert sounds
- Custom audio cues

**Documentation:** [omni-automation.com/shared/audio](https://omni-automation.com/shared/audio.html)

## File Types

Predefined file type constants.

**Common Types:**
- `FileTypes.Text` - Plain text files
- `FileTypes.PDF` - PDF documents
- `FileTypes.Image` - Image files
- `FileTypes.Audio` - Audio files
- `FileTypes.Video` - Video files

**Documentation:** [omni-automation.com/shared/filetypes](https://omni-automation.com/shared/filetypes.html)

## Best Practices

### Cross-App Compatibility

When writing Omni Automation scripts that work across multiple apps:

1. **Use shared classes** instead of app-specific APIs when possible
2. **Test on all target platforms** (macOS, iOS, iPadOS)
3. **Handle platform differences** with Device detection
4. **Provide fallbacks** for platform-specific features

**Example:**
```javascript
// Check platform before using platform-specific features
if (Device.current.iOS) {
    // iOS-specific code
} else if (Device.current.macOS) {
    // macOS-specific code
}
```

### Error Handling

Always wrap shared API calls in try-catch blocks:

```javascript
try {
    const picker = new FilePicker();
    const urls = await picker.show();
    // Process files
} catch (error) {
    const alert = new Alert("Error", error.message);
    alert.show();
}
```

### User Interaction

Use appropriate UI elements for different scenarios:

- **Alert** - Simple messages and confirmations
- **Form** - Structured data collection
- **FilePicker/FileSaver** - File operations
- **Notification** - Background or non-blocking updates

### Data Validation

Validate user input from Forms:

```javascript
const form = new Form();
form.addField(new Form.Field.String("email", "Email"));

const formObject = await form.show("Enter Email", "Submit");
const email = formObject.values["email"];

if (!email.includes("@")) {
    const alert = new Alert("Invalid Email", "Please enter a valid email address");
    alert.show();
    return;
}
```

## Common Patterns

### Confirmation Dialog

```javascript
const alert = new Alert("Confirm Action", "Are you sure you want to delete this task?");
alert.addOption("Delete");
alert.addOption("Cancel");
const choice = await alert.show();

if (choice === 0) {
    // User chose Delete
    deleteTask();
}
```

### Input Form

```javascript
const form = new Form();
form.addField(new Form.Field.String("name", "Task Name", null));
form.addField(new Form.Field.Date("due", "Due Date", new Date()));
form.addField(new Form.Field.Option("priority", "Priority", ["High", "Medium", "Low"], null, "Medium"));

const formObject = await form.show("New Task", "Create");
console.log(formObject.values);
```

### File Export

```javascript
const saver = new FileSaver();
saver.nameLabel = "Save report as:";
saver.types = [FileTypes.Text];

const url = await saver.show();
if (url) {
    const wrapper = FileWrapper.withContents("report.txt", Data.fromString(reportText));
    wrapper.write(url);
}
```

### Clipboard Operations

```javascript
// Copy formatted task list to clipboard
const taskList = tasks.map(t => `• ${t.name}`).join("\n");
Pasteboard.general.string = taskList;

const notification = new Notification("Copied", `${tasks.length} tasks copied to clipboard`);
notification.show();
```

## Integration with Apple Foundation Models

When using Apple Foundation Models (LanguageModel.Session) with shared classes:

```javascript
// Get AI analysis
const session = new LanguageModel.Session();
const analysis = await session.respond("Analyze this task data...");

// Show results in Alert
const alert = new Alert("AI Analysis", analysis);
alert.show();

// Or save to file
const saver = new FileSaver();
const url = await saver.show();
if (url) {
    const wrapper = FileWrapper.withContents("analysis.txt", Data.fromString(analysis));
    wrapper.write(url);
}
```

## Resources

- **Main Documentation:** [omni-automation.com/shared](https://omni-automation.com/shared/index.html)
- **OmniFocus Specific:** See `omni_automation.md` in this directory
- **Apple Foundation Models:** See `foundation_models_integration.md` in this directory
- **Examples:** See `assets/` directory for plug-in templates and `plugin_installation.md` for installation guide

## See Also

- `omni_automation.md` - OmniFocus-specific Omni Automation reference
- `foundation_models_integration.md` - Apple Intelligence integration
- `jxa_commands.md` - JXA command reference (alternative to Omni Automation)
