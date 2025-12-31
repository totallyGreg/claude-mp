# GTD with OmniFocus: Complete Guide

**Navigation hub** for Getting Things Done (GTD) methodology implementation in OmniFocus.

---

## What is GTD?

**Getting Things Done (GTD)** is a productivity methodology created by David Allen. It provides a systematic approach to managing commitments, projects, and tasks through five core phases:

1. **Capture** - Collect everything that has your attention
2. **Clarify** - Process what it means and what to do about it
3. **Organize** - Put it where it belongs
4. **Reflect** - Review frequently
5. **Engage** - Simply do

OmniFocus was specifically designed to implement GTD principles, making it the perfect tool for this methodology.

---

## Quick Decision Tree

**START HERE: What do you need?**

### I want to understand GTD concepts
👉 **[GTD Context Guide](gtd_context.md)** - Brief GTD principles overview
- Core GTD principles (5 steps)
- How OmniFocus implements GTD (projects, tags, perspectives)
- GTD-aligned perspectives
- Insight generation with GTD awareness
- ~200 lines, quick read

### I want to implement GTD in OmniFocus
👉 **[GTD Methodology Guide](gtd_methodology.md)** - Complete implementation guide
- Detailed walkthrough of each GTD step
- OmniFocus-specific workflows for each phase
- GTD perspectives with automation examples
- Project planning templates
- Weekly and daily review processes
- Common pitfalls and solutions
- ~570 lines, comprehensive

### I want practical workflows and automation
👉 **[Workflows Guide](workflows.md)** - Ready-to-use automation patterns
- Daily planning routines
- Task creation patterns
- Review workflows (weekly, monthly)
- Project management automation
- Context-based workflows
- Shell script integration examples
- ~400 lines, practical

---

## Documentation Map

### Quick Reference (5-10 minutes)

**[GTD Context](gtd_context.md)**
- What: Brief principles overview
- For: Understanding GTD basics
- For: Context for automation design
- Size: ~200 lines

### Complete Guide (30-60 minutes)

**[GTD Methodology](gtd_methodology.md)**
- What: Full implementation guide
- For: Setting up GTD in OmniFocus
- For: Understanding each GTD phase deeply
- Size: ~570 lines

### Practical Automation (15-30 minutes)

**[Workflows](workflows.md)**
- What: Ready-to-use automation patterns
- For: Daily/weekly automation setup
- For: Shell script integration
- Size: ~400 lines

---

## Common Use Cases

### "I'm new to GTD and want to get started"

**Path:**
1. Read [GTD Context](gtd_context.md) - Understand the basics (10 min)
2. Read [GTD Methodology](gtd_methodology.md) - Learn implementation (30 min)
3. Start with **Capture** and **Inbox Processing** sections
4. Add one GTD phase per week until all five are in place

**Key principle:** Start small, build the habit, expand gradually.

### "I know GTD but need OmniFocus-specific implementation"

**Path:**
1. Skim [GTD Context](gtd_context.md) - See OmniFocus mapping (5 min)
2. Deep dive [GTD Methodology](gtd_methodology.md) - Full implementation (30 min)
3. Focus on "How OmniFocus Implements GTD" sections
4. Set up perspectives from examples

**Key sections:**
- Projects vs Tasks
- Contexts → Tags
- Next Actions
- Waiting For
- Weekly Review

### "I want to automate my GTD workflows"

**Path:**
1. Review [Workflows](workflows.md) - Find relevant patterns (15 min)
2. Copy and customize automation examples
3. Set up daily/weekly automation scripts

**Popular automations:**
- Morning planning dashboard
- Weekly review helper
- Context-based task lists
- Bulk operations for maintenance

### "I need insight into my GTD system health"

**Path:**
1. Read [GTD Context](gtd_context.md) - "Insight Generation with GTD" section
2. Use insight patterns from [GTD Methodology](gtd_methodology.md) - "Common Pitfalls" section
3. Run analysis: `python3 scripts/analyze_insights.py`

**Common insights:**
- Stalled projects (no next actions)
- Over-committed (too many active projects)
- Neglected reviews (projects not reviewed recently)
- Context gaps (tasks without tags)

### "I want to set up weekly review automation"

**Path:**
1. Read [GTD Methodology](gtd_methodology.md) - "Weekly Review Template" section
2. Copy automation from [Workflows](workflows.md) - "Weekly Review" section
3. Customize for your needs
4. Schedule via cron or run manually

**Components:**
- Inbox processing
- Project review
- Waiting For follow-up
- Someday/Maybe review

---

## GTD Phases in OmniFocus

### 1. Capture

**What:** Collect everything that has your attention

**OmniFocus tools:**
- Quick entry (⌃⌥Space on Mac)
- Inbox (unprocessed items)
- URL scheme for external capture
- Email to OmniFocus

**Automation:**
```bash
# Quick capture via URL
open "omnifocus:///add?name=Task&autosave=true"

# Detailed capture via JXA
osascript -l JavaScript scripts/manage_omnifocus.js create --name "Task"
```

**Learn more:** [GTD Methodology](gtd_methodology.md#1-capture)

### 2. Clarify

**What:** Process what each item means and what to do about it

**OmniFocus workflow:**
- Review inbox daily
- Ask: Is it actionable?
- If yes: Define next action, project, context
- If no: Delete, reference, or someday/maybe

**Decision tree:**
```
Is it actionable?
├─ NO → Delete / Reference / Someday/Maybe
└─ YES → Is it multi-step (project)?
    ├─ YES → Create project + tasks
    └─ NO → Single task
```

**Learn more:** [GTD Methodology](gtd_methodology.md#2-clarify)

### 3. Organize

**What:** Put items where they belong

**OmniFocus structure:**
- **Folders** - Areas of responsibility (Personal, Work)
- **Projects** - Outcomes requiring multiple steps
- **Tags** - Contexts (where/when/with what)
- **Perspectives** - Saved filtered views

**Learn more:** [GTD Methodology](gtd_methodology.md#3-organize)

### 4. Reflect

**What:** Review regularly to stay current

**Review frequencies:**
- **Daily** - Today's tasks, flagged items (5-10 min)
- **Weekly** - All projects, waiting for, someday/maybe (1 hour)
- **Monthly** - Areas of responsibility (30 min)
- **Quarterly** - Goals and vision (1 hour)

**Automation support:**
```bash
# Daily review
osascript -l JavaScript scripts/manage_omnifocus.js today

# Weekly review helper
python3 scripts/weekly_review.py
```

**Learn more:** [GTD Methodology](gtd_methodology.md#4-reflect)

### 5. Engage

**What:** Choose what to do based on context, time, energy, priority

**OmniFocus tools:**
- Context/tag-based perspectives
- Forecast (what's due)
- Flagged (priorities)
- Custom perspectives

**Decision factors:**
1. **Context** - Where am I? What tools do I have?
2. **Time** - How much time do I have?
3. **Energy** - How much mental/physical energy?
4. **Priority** - What's most important?

**Learn more:** [GTD Methodology](gtd_methodology.md#5-engage)

---

## GTD + Automation Architecture

### Low-Cost Operations (Execute Existing)

**Use when:** Daily/weekly routine operations

**Examples:**
- Query today's tasks
- Check flagged items
- Weekly review report
- Context-based task lists

**Tools:**
- Shell scripts with JXA
- Scheduled automation (cron)
- Alfred workflows

**See:** [Workflows Guide](workflows.md)

### Medium-Cost Operations (Compose Patterns)

**Use when:** Setting up new GTD workflows

**Examples:**
- Custom review routines
- Project templates
- Insight detection
- Batch operations

**Tools:**
- Modular libraries (taskQuery, taskMutation)
- Pattern composition
- Template engine

**See:** [Libraries README](../libraries/README.md)

### High-Cost Operations (Novel Generation)

**Use when:** Creating entirely new GTD patterns

**Examples:**
- Custom GTD adaptations
- Unique workflow combinations
- Organization-specific processes

**Tools:**
- Full code generation
- Custom plugin development
- Advanced automation

**See:** [Plugin Development Guide](plugin_development_guide.md)

---

## GTD Perspectives in OmniFocus

### Built-in Perspectives

**Inbox**
- Unprocessed items
- Goal: Process to zero daily
- See: [Workflows - Processing Inbox](workflows.md#processing-inbox)

**Forecast**
- Due dates + calendar events
- Daily planning view
- See: [GTD Context - Forecast](gtd_context.md#forecast)

**Flagged**
- High-priority items
- Quick access to critical tasks
- See: [GTD Context - Flagged](gtd_context.md#flagged)

**Projects**
- All active projects
- Weekly review starting point
- See: [GTD Methodology - Project Planning](gtd_methodology.md#project-planning-with-omnifocus)

**Tags**
- Context-based filtering
- Where/when/with what
- See: [GTD Context - Contexts → Tags](gtd_context.md#contexts--tags)

### Custom Perspectives

**Next Actions**
- Available tasks (not blocked/deferred)
- Grouped by tag
- See: [GTD Context - Next Actions](gtd_context.md#next-actions)

**Waiting For**
- Delegated/blocked items
- Follow-up tracking
- See: [GTD Context - Waiting For](gtd_context.md#waiting-for)

**Stalled Projects**
- Projects without next actions
- Needs clarification
- See: [GTD Context - Stalled Projects](gtd_context.md#stalled-projects)

**Someday/Maybe**
- Ideas for future
- Reviewed during weekly review
- See: [GTD Context - Someday/Maybe](gtd_context.md#somedaymaybe)

---

## Resources

### Books and Methodology

- **"Getting Things Done" by David Allen** - Original GTD methodology
- **"Making It All Work" by David Allen** - Advanced GTD
- **"Ready for Anything" by David Allen** - GTD principles collection

### OmniFocus Resources

- **OmniFocus GTD Setup Guide:** [support.omnigroup.com/omnifocus-gtd](https://support.omnigroup.com/omnifocus-gtd/)
- **OmniFocus Forums:** [discourse.omnigroup.com](https://discourse.omnigroup.com/)
- **GTD Weekly Review:** [gettingthingsdone.com/weekly-review](https://gettingthingsdone.com/weekly-review/)

### Skill Documentation

**GTD Implementation:**
- [GTD Context](gtd_context.md) - Brief principles
- [GTD Methodology](gtd_methodology.md) - Complete guide
- [Workflows](workflows.md) - Automation patterns

**Automation Tools:**
- [JXA API Guide](jxa_api_guide.md) - Command-line automation
- [Plugin Development Guide](plugin_development_guide.md) - OmniFocus plugins
- [Libraries README](../libraries/README.md) - Modular libraries

**Examples:**
- [Assets Examples](../assets/examples/README.md) - Working code examples
- [Quickstarts](quickstarts/) - 5-minute tutorials

---

## GTD Principles Summary

### Core Concepts

**Open Loops**
- Anything that has your attention but isn't where it belongs
- Goal: Capture all open loops in trusted system

**Mind Like Water**
- Mental clarity from having everything out of your head
- Achieved through complete capture and regular review

**Next Actions**
- Physical, visible activities that move things forward
- Must be concrete: "Call John about Q4 budget" not "Budget stuff"

**Projects**
- Any outcome requiring more than one action step
- All projects need defined next actions

**Contexts**
- Filters based on where/when/with what you can do tasks
- Examples: @home, @office, @phone, @computer

**Weekly Review**
- Cornerstone of GTD
- Get clear → Get current → Get creative
- Non-negotiable for system trust

### GTD Workflow

```
Capture → Clarify → Organize → Reflect → Engage
   ↑                                        ↓
   └────────────────────────────────────────┘
```

**Success criteria:**
- Everything out of your head
- Inbox processed regularly
- All projects have next actions
- Weekly review is routine
- System is trusted

---

## Quick Links

**Getting Started:**
- [GTD Context](gtd_context.md) - Start here for overview
- [GTD Methodology](gtd_methodology.md) - Then read for implementation

**Practical Automation:**
- [Workflows](workflows.md) - Ready-to-use scripts
- [JXA Quickstart](quickstarts/jxa_quickstart.md) - 5-minute tutorial
- [Libraries README](../libraries/README.md) - Modular tools

**Advanced Topics:**
- [Plugin Development](plugin_development_guide.md) - Create custom plugins
- [Foundation Models Integration](foundation_models_integration.md) - AI-powered insights
- [Database Schema](database_schema.md) - Direct database queries

---

## What's Next?

### Beginner
1. Read [GTD Context](gtd_context.md) - Understand principles
2. Set up basic capture workflow
3. Start processing inbox daily
4. Add one GTD phase per week

### Intermediate
1. Read [GTD Methodology](gtd_methodology.md) - Full implementation
2. Set up all five GTD phases
3. Establish weekly review routine
4. Create custom perspectives

### Advanced
1. Automate reviews with [Workflows](workflows.md)
2. Create custom plugins
3. Integrate with other tools
4. Optimize for your specific needs

**Remember:** GTD is a practice, not a destination. Start simple, build habits, refine continuously.
