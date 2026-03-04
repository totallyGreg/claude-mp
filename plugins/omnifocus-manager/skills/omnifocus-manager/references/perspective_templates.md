# GTD Perspective Templates

Canonical GTD perspective configurations using OmniFocus v4.2+ `archivedFilterRules` API.

## How to Use These Templates

### One-Time Setup (per perspective)
1. In OmniFocus: **Perspectives → +** to create a blank perspective
2. Name it to match the template (e.g., "Next Actions")
3. Apply the template using `perspective-config.js`

### Applying a Template
```bash
cd plugins/omnifocus-manager/skills/omnifocus-manager
osascript -l JavaScript scripts/perspective-config.js \
  --action apply-template --name "Next Actions" --template next-actions
```

### Modifying a Perspective
```bash
# Show current rules
osascript -l JavaScript scripts/perspective-config.js \
  --action show --name "Next Actions"

# Apply custom rules (JSON)
osascript -l JavaScript scripts/perspective-config.js \
  --action apply --name "Next Actions" \
  --rules '[{"actionAvailability":"available"},{"actionHasAnyOfTags":["TAG_ID"]}]'

# Reset to a template
osascript -l JavaScript scripts/perspective-config.js \
  --action apply-template --name "Next Actions" --template next-actions
```

---

## Template Library

### 1. Next Actions (`next-actions`)

**Purpose:** See all available next actions grouped by context tag. The core GTD "what can I do right now?" view.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionAvailability": "available" },
    { "projectStatus": "active" }
  ],
  "aggregation": "all"
}
```

**Notes:** Shows only truly actionable tasks — available (not blocked, not deferred to future) in active projects. Group by tag in OmniFocus UI for context-based selection.

---

### 2. Waiting For (`waiting-for`)

**Purpose:** Track all delegated items and items blocked on external input. Sorted by age to surface stale items.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionAvailability": "remaining" },
    { "actionHasAnyOfTags": ["WAITING_TAG_ID"] }
  ],
  "aggregation": "all"
}
```

**Notes:** Replace `WAITING_TAG_ID` with the actual tag ID. The script resolves tag names to IDs automatically. Use `actionAvailability: "remaining"` (not "available") to include deferred waiting items.

---

### 3. Flagged + Available (`flagged-available`)

**Purpose:** High-priority items you've flagged that are actually actionable right now.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionAvailability": "available" },
    { "actionFlagged": true }
  ],
  "aggregation": "all"
}
```

**Notes:** Combines flagged status with availability — only shows flagged items you can act on now (not blocked or deferred).

---

### 4. Stalled Projects (`stalled-projects`)

**Purpose:** Find active projects with no available next actions. Essential for weekly review.

**Filter rules:**
```json
{
  "filterRules": [
    { "projectStatus": "active" },
    { "projectHasNoAvailableActions": true }
  ],
  "aggregation": "all"
}
```

**Notes:** Projects without next actions are "stalled" — they need attention to define the next physical action.

---

### 5. Due This Week (`due-this-week`)

**Purpose:** See everything due in the next 7 days to plan and prioritize.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionAvailability": "remaining" },
    { "actionDueSoon": 7 }
  ],
  "aggregation": "all"
}
```

**Notes:** Uses "remaining" (not "available") to include blocked items that are due — you need to unblock them. `actionDueSoon` value is days from today.

---

### 6. Someday/Maybe (`someday-maybe`)

**Purpose:** Review deferred possibilities and on-hold projects during weekly review.

**Filter rules:**
```json
{
  "filterRules": [
    { "projectStatus": "onHold" }
  ],
  "aggregation": "all"
}
```

**Notes:** On-hold projects are the OmniFocus equivalent of GTD's Someday/Maybe list. Review during weekly review to promote or drop.

---

### 7. Recently Completed (`recently-completed`)

**Purpose:** Review accomplishments for daily standup, weekly review, or journaling.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionCompletedWithinDays": 7 }
  ],
  "aggregation": "all"
}
```

**Notes:** Shows tasks completed in the last 7 days. Useful for building momentum and tracking output.

---

### 8. Overdue (`overdue`)

**Purpose:** Surface all past-due items for immediate triage — reschedule, complete, or drop.

**Filter rules:**
```json
{
  "filterRules": [
    { "actionAvailability": "remaining" },
    { "actionOverdue": true }
  ],
  "aggregation": "all"
}
```

**Notes:** Overdue items need decisions: do it now, change the date, or drop it. Maintaining zero overdue is a GTD health signal.

---

## Filter Rule Reference

### Availability Filters
| Rule Key | Values | Description |
|----------|--------|-------------|
| `actionAvailability` | `"available"`, `"remaining"`, `"completed"` | Task availability status |

### Status Filters
| Rule Key | Values | Description |
|----------|--------|-------------|
| `projectStatus` | `"active"`, `"onHold"`, `"completed"`, `"dropped"` | Project status filter |
| `actionFlagged` | `true`, `false` | Flagged state |
| `actionOverdue` | `true` | Past due date |

### Tag Filters
| Rule Key | Values | Description |
|----------|--------|-------------|
| `actionHasAnyOfTags` | `["tagID1", "tagID2"]` | Task has any of these tags |
| `actionHasAllOfTags` | `["tagID1", "tagID2"]` | Task has all of these tags |
| `actionHasNoTags` | `true` | Task has no tags assigned |

### Time Filters
| Rule Key | Values | Description |
|----------|--------|-------------|
| `actionDueSoon` | `<days>` (integer) | Due within N days |
| `actionCompletedWithinDays` | `<days>` (integer) | Completed within N days |

### Project Filters
| Rule Key | Values | Description |
|----------|--------|-------------|
| `projectHasNoAvailableActions` | `true` | Active projects with no next actions |

### Aggregation
| Value | Meaning |
|-------|---------|
| `"all"` | All rules must match (AND) |
| `"any"` | Any rule can match (OR) |
| `"none"` | No rules should match (NOT) |

---

## Custom Perspective Design

When creating a perspective from plain English, map the request to filter rules:

| User Says | Filter Rules |
|-----------|-------------|
| "tasks I can do right now" | `actionAvailability: "available"` |
| "everything that's due" | `actionOverdue: true` |
| "things I'm waiting on" | `actionHasAnyOfTags: [waitingTagId]` |
| "flagged items" | `actionFlagged: true` |
| "stalled projects" | `projectStatus: "active"` + `projectHasNoAvailableActions: true` |
| "completed last week" | `actionCompletedWithinDays: 7` |
| "deferred possibilities" | `projectStatus: "onHold"` |
| "tasks at home" | `actionHasAnyOfTags: [homeTagId]` |
| "due this week" | `actionDueSoon: 7` |
