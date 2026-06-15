# Perspectives and Forecast

<!-- DRAFT — review during D2 integration -->

**What this covers:** Perspective.BuiltIn, Perspective.Custom, ForecastDay, and window-level perspective navigation.

**What this does NOT cover:** Task filtering logic, Forms for perspective-driven UI. See `tasks_projects_tags.md`, `forms_ui.md`.

---

## 1. First-Stop Solution: Check `ofoCore`

```js
var ofoCore = PlugIn.find("com.totallytools.omnifocus.attache").library("ofoCore");
```

ofoCore currently exposes `ofo perspective <name>` CLI to switch perspectives. If you only need to read the current perspective, use `document.windows[0].perspective` directly. ofoCore does not currently expose ForecastDay — use native API below.

---

## 2. Native Omni Automation Classes

### Perspective.BuiltIn

Read-only class properties — the built-in OmniFocus views:

```js
Perspective.BuiltIn.Flagged          // Flagged items
Perspective.BuiltIn.Forecast         // Upcoming due items
Perspective.BuiltIn.Inbox            // Inbox of tasks
Perspective.BuiltIn.Nearby           // Map (iOS only)
Perspective.BuiltIn.Projects         // Library of projects
Perspective.BuiltIn.Review           // Projects needing review
Perspective.BuiltIn.Search           // Transient (user is searching)
Perspective.BuiltIn.Tags             // Tag hierarchy
Perspective.BuiltIn.all              // Array of all built-in perspectives
Perspective.BuiltIn.name             // Localized name (instance)
```

### Perspective.Custom

User-defined perspectives:

```js
// Lookup
Perspective.Custom.all                        // Array of all custom perspectives
Perspective.Custom.byName("My View")          // → Perspective.Custom | null
Perspective.Custom.byIdentifier("com.x.y")   // → Perspective.Custom | null

// Properties
perspective.name                              // String (read-only)
perspective.identifier                        // String (read-only)
perspective.iconColor                         // Color | null
perspective.archivedFilterRules               // JSON archive of filter rules
perspective.archivedTopLevelFilterAggregation // "all" | "any" | "none"

// Export
perspective.fileWrapper()                     // → FileWrapper (archived)
perspective.writeFileRepresentationIntoDirectory(url)
```

### Window + Perspective Navigation

```js
var win = document.windows[0];
win.perspective                // Perspective.BuiltIn | Perspective.Custom
```

### ForecastDay (v4+)

Access the Forecast calendar view programmatically:

```js
// Requires Forecast perspective to be currently active
var win = document.windows[0];

var day = win.forecastDayForDate(new Date());  // → ForecastDay

// ForecastDay properties (read-only)
day.date              // Date
day.kind              // ForecastDay.Kind
day.badgeCount        // Number (available tasks)
day.deferredCount     // Number (deferred tasks)
day.name              // String (localized day name)
day.badgeKind()       // → ForecastDay.Status

// Selecting forecast days
win.selectForecastDays([day1, day2]);          // First only on iOS

// ForecastDay.Kind enum
ForecastDay.Kind.Day            // Specific day in grid
ForecastDay.Kind.Today          // Today
ForecastDay.Kind.FutureMonth    // Month within next year
ForecastDay.Kind.Past           // All past days
ForecastDay.Kind.DistantFuture  // More than a year from now
ForecastDay.Kind.all            // Array of all kinds

// ForecastDay.Status enum (badge state)
ForecastDay.Status.Available        // Tasks present, none overdue
ForecastDay.Status.DueSoon          // Tasks present, at least one due soon
ForecastDay.Status.NoneAvailable    // No available tasks
ForecastDay.Status.Overdue          // Tasks present, at least one overdue
ForecastDay.Status.all

// Class-level option
ForecastDay.badgeCountsIncludeDeferredItems = true;  // include unavailable in count
```

**⚠️ Footgun:** `win.forecastDayForDate()` throws if the Forecast perspective is not currently showing. Always guard:

```js
if (win.perspective === Perspective.BuiltIn.Forecast) {
  var day = win.forecastDayForDate(targetDate);
}
```

---

## 3. Common Patterns

### Switch to a perspective:

```js
// Via ofo CLI (preferred for agent-led work):
// ofo perspective Forecast

// Via Omni Automation (for plugin UI context):
// OmniFocus doesn't expose a direct "show perspective" method —
// use URL scheme: open("omnifocus:///perspective/Forecast")
```

### Read tasks for a custom perspective:

Custom perspectives filter tasks via `archivedFilterRules` (opaque JSON). To get tasks *as they appear* in a perspective, the only reliable approach is showing the perspective and reading `selection` or `flattenedTasks` filtered by the visible scope. There is no API to evaluate perspective filter rules programmatically.

### Export a custom perspective:

```js
var p = Perspective.Custom.byName("My GTD View");
if (p) {
  var fw = p.fileWrapper();  // → FileWrapper containing the perspective data
}
```

---

## 4. Reach-Out Trigger

For ForecastDay full reference or perspective filter rule format:

```
WebFetch https://omni-automation.com/omnifocus/forecast.html
WebFetch https://omni-automation.com/omnifocus/perspective.html
Prompt: "I need [specific method/property] full signature including version requirements."
```
