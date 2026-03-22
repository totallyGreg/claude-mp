# Apple Foundation Models Integration

Practical reference for using `LanguageModel` API inside OmniFocus Omni Automation plugins.

## Hard Boundary: Omni Automation Only

Foundation Models (`LanguageModel.Session`) are **only available inside Omni Automation plugins** (`.omnifocusjs`). They are **not** available in JXA scripts run via `osascript -l JavaScript`. These are different runtimes with different APIs — this is not a configuration issue.

Rule: if a task can be done deterministically (counts, dates, filtering, pattern detection), use JXA (`gtd-queries.js`, `manage_omnifocus.js`). If it requires language understanding or generation, use a Foundation Models plugin action.

## Platform Requirements

- OmniFocus 4.8+
- macOS 26+ / iOS 26+ (actual floor used in plugin `validate()` functions)
- Apple Silicon (Mac) or iPhone 15 Pro+ (iOS)
- Apple Intelligence enabled in System Settings → Apple Intelligence & Siri

**Note on versions:** The existing `foundationModelsUtils.js` mentions macOS 15.2+ as a requirement, but actual plugin `validate()` functions use `Device.current.operatingSystemVersion.atLeast(new Version("26"))`. Use macOS 26 as the safe floor in new code.

## Availability Check Pattern

Do not rely on `action.validate` to grey out FM actions — you cannot reliably detect whether Apple Intelligence is enabled without attempting to use it. Instead, always return `true` from `validate` and surface errors at runtime via Alert.

```javascript
// In foundationModelsUtils library
lib.isAvailable = function() {
    if (typeof LanguageModel === 'undefined') return false;
    if (typeof LanguageModel.Session === 'undefined') return false;
    return true;
};

// In action.validate
action.validate = function(selection) {
    // Check OS version as a proxy for FM availability
    return Device.current.operatingSystemVersion.atLeast(new Version("26"));
};
```

Always wrap session usage in `try/catch` and show an Alert on failure regardless of the validate check.

## Core API

### `LanguageModel.Session`

```javascript
const session = new LanguageModel.Session();
```

Two instance methods:

**`respond(prompt)`** → `Promise<String>`
Returns a conversational text response. Use for free-form output.

**`respondWithSchema(prompt, schema, generationOptions)`** → `Promise<String>`
Returns a JSON string conforming to the provided schema. `generationOptions` can be `null`.

### `LanguageModel.GenerationOptions`

Optional parameter to `respondWithSchema`. Controls sampling behavior.

```javascript
const opts = new LanguageModel.GenerationOptions();
// opts properties vary — pass null if defaults are acceptable
const response = await session.respondWithSchema(prompt, schema, opts);
```

### Parsing the Response

`respondWithSchema` returns a JSON string. Parse it directly:

```javascript
const response = await session.respondWithSchema(prompt, schema, null);
const result = JSON.parse(response);
```

For `respond()` (unstructured), if you asked for JSON in the prompt, extract it from backtick blocks:

```javascript
const openingTag = "```json";
const start = response.indexOf(openingTag) + openingTag.length;
const end = response.indexOf("```", start);
const json = JSON.parse(response.substring(start, end).trim());
```

## `LanguageModel.Schema.fromJSON()` Reference

This is the most complex part of the API. Schemas are constructed from a JSON descriptor, not a class hierarchy.

### Basic object with properties

```javascript
const schema = LanguageModel.Schema.fromJSON({
    name: "result-schema",
    properties: [
        { name: "summary" },
        { name: "score" }
    ]
});
```

### Property with description

Adding `description` guides the model toward the intended value:

```javascript
{ name: "priorityTask", description: "The single most important task to do first" }
```

### Nested object

```javascript
{
    name: "workloadAnalysis",
    schema: {
        name: "workload-schema",
        properties: [
            { name: "isManageable" },
            { name: "summary" }
        ]
    }
}
```

### Array of strings (`arrayOf` + `constant`)

```javascript
{
    name: "recommendations",
    schema: { arrayOf: { constant: "recommendation" } }
}
```

The string `"recommendation"` is an arbitrary label; the model generates string values.

### Array of objects (`arrayOf` with schema)

```javascript
{
    name: "priorities",
    description: "Top tasks to tackle first",
    schema: {
        arrayOf: {
            name: "priority-item",
            properties: [
                { name: "taskName" },
                { name: "reason" }
            ]
        }
    }
}
```

### Array with maximum length

```javascript
{
    name: "topActions",
    schema: {
        arrayOf: { constant: "action" },
        maximumElements: 3
    }
}
```

### Enum (`anyOf`)

```javascript
{
    name: "urgency",
    schema: {
        anyOf: ["high", "medium", "low"]
    }
}
```

### Optional property

```javascript
{ name: "note", isOptional: true }
```

### Complete example (from `analyzeTasksWithAI.js`)

```javascript
const schema = LanguageModel.Schema.fromJSON({
    name: "analysis-schema",
    properties: [
        {
            name: "priorityRecommendations",
            description: "Top 3 tasks to tackle first",
            schema: {
                arrayOf: {
                    name: "priority-item",
                    properties: [
                        { name: "taskName" },
                        { name: "reason" }
                    ]
                }
            }
        },
        {
            name: "workloadAnalysis",
            schema: {
                name: "workload-schema",
                properties: [
                    { name: "isManageable" },
                    { name: "summary" },
                    { name: "concerns", schema: { arrayOf: { constant: "concern" } } }
                ]
            }
        },
        {
            name: "actionItems",
            description: "Immediate actions to take",
            schema: { arrayOf: { constant: "action" } }
        }
    ]
});
```

## Async Action Pattern

All actions using Foundation Models must be declared `async`. Wrap all FM calls in `try/catch`.

```javascript
(() => {
    const action = new PlugIn.Action(async function(selection, sender) {
        // 1. Check availability
        const fmUtils = this.plugIn.library("foundationModelsUtils");
        if (!fmUtils.isAvailable()) {
            fmUtils.showUnavailableAlert();
            return;
        }

        try {
            // 2. Create session
            const session = new LanguageModel.Session();

            // 3. Build prompt from OmniFocus data
            const prompt = `...`;

            // 4. Define schema
            const schema = LanguageModel.Schema.fromJSON({ ... });

            // 5. Call FM
            const response = await session.respondWithSchema(prompt, schema, null);
            const result = JSON.parse(response);

            // 6. Use result
            new Alert("Analysis", result.summary).show();

        } catch (err) {
            new Alert(err.name, err.message).show();
        }
    });

    action.validate = function(selection) {
        return Device.current.operatingSystemVersion.atLeast(new Version("26"));
    };

    return action;
})();
```

## Per-Call Session Pattern (Multi-Step Workflows)

For workflows that call FM multiple times (e.g., weekly review with multiple steps), create a new session per call. Sessions are not reused across steps.

```javascript
// Step 1
const session1 = new LanguageModel.Session();
const step1Result = JSON.parse(await session1.respondWithSchema(prompt1, schema1, null));

// Step 2 — new session
const session2 = new LanguageModel.Session();
const step2Result = JSON.parse(await session2.respondWithSchema(prompt2, schema2, null));
```

## Context Limits

The practical context limit is not publicly documented. Observed behavior:
- Existing actions batch at 10 tasks maximum per FM call
- Larger inputs may produce incomplete or truncated responses
- For project sweeps or batch analysis, chunk by project or folder

## When to Use FM vs. Deterministic JXA

| Question | Use |
|---|---|
| How many tasks are overdue? | JXA (`gtd-queries.js --action overdue`) |
| Which projects are stalled? | JXA (`gtd-queries.js --action stalled-projects`) |
| What should I prioritize today? | FM (judgment required) |
| Rename this task to be clearer | FM (language understanding required) |
| What effort tag fits this action? | FM (semantic judgment) |
| Is my inbox count healthy? | JXA (numeric threshold) |
| What does this project need next? | FM (context + structure reasoning) |

## References

- `assets/Attache.omnifocusjs/Resources/foundationModelsUtils.js` — availability utility library
- `assets/Attache.omnifocusjs/Resources/analyzeTasksWithAI.js` — Schema.fromJSON() example
- `assets/Attache.omnifocusjs/Resources/dailyReview.js` — GenerationOptions, anyOf enum usage
- `assets/Attache.omnifocusjs/Resources/weeklyReview.js` — per-call session pattern
- `references/omni_automation_shared.md` — Alert, Form, Pasteboard, PlugIn.Library API
- [omni-automation.com/shared/alm.html](https://www.omni-automation.com/shared/alm.html) — canonical LanguageModel API docs
