---
name: omnifocus-manager
description: Interface with OmniFocus to surface insights, create reusable automations and perspectives, and suggest workflow optimizations. Use when analyzing tasks, building plugins, designing perspectives, or identifying automation opportunities. Trigger when user mentions OmniFocus, task insights, automation creation, or perspective design.
metadata:
  version: 1.1.0
  compatibility: "OmniFocus 3.14+, macOS 12+, iOS 16+"
  license: MIT
---

# OmniFocus Manager

Intelligent interface to OmniFocus that surfaces insights, creates reusable automations, and designs custom perspectives.

## When to Use

- Analyze task patterns and surface actionable insights
- Create Omni Automation plugins for repeated workflows
- Design custom perspectives for consistent task views
- Suggest automation opportunities based on usage patterns
- Build task templates for recurring processes

## Core Workflows

### 1. Insight Generation

Analyze OmniFocus data to surface patterns and recommendations.

**Workflow:**
```
User: "What's falling through the cracks in my tasks?"
→ Run scripts/analyze_insights.js (Omni Automation)
→ Detect patterns: stalled projects, aging waiting items, overdue accumulation
→ Return: Actionable insights + recommendations
```

**Common Insights:**
- **Blockers:** Stalled projects (no next actions), aging waiting items
- **Health Issues:** Overdue accumulation, inbox overflow, missing context tags
- **Opportunities:** Repeated manual tasks →  template suggestions, frequent filters → perspective recommendations

**Implementation:**
- Use `scripts/analyze_insights.js` for pattern detection
- See `references/insight_patterns.md` for complete pattern catalog
- Insights include GTD-aligned recommendations (see `references/gtd_context.md`)

**Example:**
```javascript
// Run insight analyzer (Omni Automation console: ⌃⌥⌘I)
// Paste scripts/analyze_insights.js content
// Returns formatted report with blockers, health issues, opportunities
```

### 2. Create Reusable Automations (Plugin-First Approach)

Build Omni Automation plugins for repeated tasks instead of one-off queries.

**When to Create Plugin:**
- Repeated analysis (weekly review, daily planning)
- Task pattern creation (meeting prep, project kickoff)
- Recurring insights (stalled project check)

**When to Use Direct Query:**
- One-off data lookup
- Quick debugging
- Ad-hoc analysis

**Plugin Creation Workflow:**
1. Identify repeated pattern
2. Draft Omni Automation JavaScript
3. Test in console (View → Automation → Console, ⌃⌥⌘I)
4. Save as .omnifocusjs bundle
5. Install by double-clicking
6. Access via Tools → [Plugin Name]

**Example Templates:**
- `examples/templates/weekly-review-template.omnifocusjs` - GTD weekly review checklist
- `examples/templates/meeting-prep-template.omnifocusjs` - Meeting preparation tasks
- See `references/omni_automation.md` for complete API reference

**Benefits:**
- Token-efficient (create once, use forever)
- Cross-platform (Mac + iOS)
- Shareable and reusable

### 3. Design Custom Perspectives

Create saved views for consistent task filtering and organization.

**Perspective Design Workflow:**
1. Identify need: "What do I need to see consistently?"
2. Define filters: Which tasks? (status, tags, due dates)
3. Choose grouping: By project? By tag? By due date?
4. Select sorting: Due date? Added date? Priority?
5. Create in OmniFocus UI (Window → Perspectives, ⌘0)

**GTD-Aligned Examples:**
- **Next Actions by Context:** Filter available tasks, group by tag (@home, @office)
- **Waiting For:** Tasks with "Waiting For" tag, sorted by age
- **Stalled Projects:** Projects without available next actions
- **Due This Week:** Tasks due within 7 days, grouped by due date

**Note:** Perspectives cannot be created via scripting - must use OmniFocus UI.

**See:** `references/perspective_creation.md` for step-by-step guide and pattern library

### 4. Suggest Automation Opportunities

Proactively identify workflow optimization opportunities.

**Pattern Detection:**
- Repeated task names → "Create template plugin?"
- Frequent manual filtering → "Custom perspective would help"
- Projects without next actions → "Weekly review automation"
- Many untagged tasks → "Batch tagging script?"

**Workflow:**
```
Analyze usage patterns
→ Detect inefficiency
→ Suggest: Plugin, perspective, or workflow change
→ Optionally: Generate automation code
```

**Example:**
```
Pattern: User creates "Weekly planning" tasks 8 times
→ Insight: "Repeated manual task detected"
→ Suggestion: "Create weekly-review template plugin?"
→ If yes: Generate plugin code from template
```

### 5. Build Task Templates

Reusable patterns for recurring task structures.

**Template System:**
- Omni Automation plugins that prompt for variables
- Create structured task hierarchies
- Set appropriate tags, dates, relationships

**Workflow:**
```
1. User: "I need a project kickoff template"
2. Draft plugin with prompts (project name, outcome, stakeholders)
3. Generate task structure based on inputs
4. Install plugin → reusable via Tools menu
```

**Example Use:**
```
User: "Create project kickoff for website redesign"
→ Run project-kickoff-template plugin
→ Prompts for: project name, desired outcome, folder
→ Creates: 8 kickoff tasks (scope, stakeholders, timeline, etc.)
→ Customized with project context
```

## Automation Approaches (Priority Order)

### 1. Omni Automation (Primary - Reusable Plugins)

**Use When:** Repeated workflows, cross-platform needs, shareable automation

**Advantages:**
- Cross-platform (Mac + iOS)
- Reusable plugins
- No file permissions required
- Token-efficient

**Access:**
- Console: View → Automation → Console (⌃⌥⌘I)
- Plugins: Install .omnifocusjs files

**References:**
- API: `references/omni_automation.md`
- Examples: `examples/` directory

### 2. Direct Queries (Secondary - One-Off Analysis)

**Use When:** Quick lookup, debugging, ad-hoc analysis

**JXA (Mac):**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js [command]
```

**Python (Mac, read-only):**
```bash
python3 scripts/query_omnifocus.py [options]
```

**References:**
- JXA commands: `scripts/manage_omnifocus.js --help`
- Python queries: `scripts/query_omnifocus.py --help`
- Detailed examples: See script files directly or backup SKILL.md.backup

### 3. URL Scheme (Quick Task Creation)

**Use When:** Simple task creation, external integration

```bash
open "omnifocus:///add?name=Task&note=Note&autosave=true"
```

**Reference:** `references/omnifocus_url_scheme.md`

## GTD Context (Supporting Knowledge)

GTD methodology informs better insights and automation design.

**Key Concepts:**
- **Next Actions:** Concrete, actionable tasks (not vague "deal with X")
- **Contexts/Tags:** Where/when tasks can be done (@home, @office, @phone)
- **Projects:** Desired outcomes requiring >1 action
- **Waiting For:** Delegated/blocked items needing follow-up
- **Weekly Review:** Regular review of all projects and next actions

**How This Informs Skill:**
- Insights detect "next action gaps" (projects without concrete next steps)
- Perspectives align with GTD views (next actions by context, waiting for)
- Templates follow GTD patterns (weekly review checklist)
- Recommendations use GTD language

**Full Reference:** `references/gtd_context.md`

## Perspective Creation Guide

**Step-by-Step:**
1. Window → Perspectives → Show Perspectives (⌘0)
2. Click + to create new
3. Configure filters (status, tags, dates, projects)
4. Set grouping (project, tag, due date, or none)
5. Choose sorting (due date, added date, flagged)
6. Save and assign keyboard shortcut

**Pattern Library:** `references/perspective_creation.md`

## Future: Foundation Models Integration

**Potential Integration Points:**
- Natural language → structured tasks
- Context-aware template customization
- AI-enhanced insight generation
- Smart task prioritization

**Current Status:** Conceptual - awaiting Apple Foundation Models API

**Full Reference:** `references/foundation_models_integration.md`

## Resources

**Scripts:**
- `scripts/analyze_insights.js` - Pattern detection and insight generation
- `scripts/manage_omnifocus.js` - JXA task management (Mac)
- `scripts/query_omnifocus.py` - Database queries (Mac, legacy)

**References:**
- `references/omni_automation.md` - Complete Omni Automation API guide
- `references/insight_patterns.md` - Pattern catalog with detection logic
- `references/perspective_creation.md` - Step-by-step perspective design
- `references/gtd_context.md` - GTD methodology for OmniFocus
- `references/omnifocus_url_scheme.md` - URL scheme reference
- `references/foundation_models_integration.md` - Future AI integration concepts

**Examples:**
- `examples/TodaysTasks.omnifocusjs` - Today's task viewer plugin
- `examples/templates/weekly-review-template.omnifocusjs` - GTD weekly review
- `examples/templates/meeting-prep-template.omnifocusjs` - Meeting preparation
- `examples/README.md` - Plugin installation guide

**External:**
- Omni Automation: [omni-automation.com/omnifocus](https://omni-automation.com/omnifocus/)
- OmniFocus Field Guide: Perspectives chapter
- GTD Methodology: "Getting Things Done" by David Allen

## Quick Reference

| Need | Approach | Tool |
|------|----------|------|
| Analyze patterns | Run insight analyzer | `scripts/analyze_insights.js` |
| Repeated workflow | Create plugin | Omni Automation console |
| Custom view | Design perspective | OmniFocus UI (⌘0) |
| One-off query | Direct query | JXA or Python scripts |
| Quick task | URL scheme | `omnifocus:///add?...` |
| Task template | Build plugin | Template examples |

## Important Notes

**Plugin-First Philosophy:**
- Create reusable plugins for repeated tasks
- Saves tokens, works offline, cross-platform
- Direct queries are secondary (one-off use only)

**Perspective Limitations:**
- Cannot be created via scripting
- Must use OmniFocus UI
- Design workflows are documented in references

**GTD as Context:**
- Not the primary focus
- Informs better insights and recommendations
- See `references/gtd_context.md` for details

**Token Efficiency:**
- Prefer plugins over repeated queries
- Load references only when needed
- Scripts can execute without reading into context
