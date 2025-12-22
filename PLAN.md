# Improvement Plan: omnifocus-manager - Insights & Automation Focus

**Status:** draft
**Created:** 2025-12-22T13:32:00Z
**Approved:** (pending)
**Implemented:** (pending)
**Completed:** (pending)

**Branch:** plan/omnifocus-manager-insights-automation-20251222
**Version:** v1

---

## Goal

Transform omnifocus-manager from a command-line interface tool into an intelligent OmniFocus assistant that:
1. **Surfaces insights** - Analyzes tasks/projects to provide actionable intelligence
2. **Creates reusable automations** - Builds Omni Automation plugins (not repeated queries)
3. **Designs custom perspectives** - Enables consistent, purposeful views of task data
4. **Suggests optimizations** - Proactively identifies automation opportunities

Supporting context: GTD methodology knowledge informs better insight generation and automation design.

---

## Current State

### Understanding

**Purpose:** Cross-platform OmniFocus automation via Omni Automation, JXA, and database queries
**Domain:** productivity
**Complexity:** Meta

**Current Approach:**
- Hybrid automation: Python database queries (read) + JXA task management (write)
- Omni Automation documented but not positioned as primary approach
- Command-line interface pattern (execute queries, return data)
- No insight generation or proactive analysis
- No perspective creation guidance
- No automation opportunity detection

### Metrics (Baseline)

```
SKILL.md: 645 lines
Tokens: ~4637
References: 2 files, 891 lines
Scripts: 2 files, 1250 lines
Assets: 0
Nesting depth: 4

Conciseness:     [██░░░░░░░░] 17/100  ⚠️ Far exceeds guidelines
Complexity:      [█████░░░░░] 46/100  ⚠️ Overly complex structure
Spec Compliance: [███████░░░] 65/100  ⚠️ Missing metadata fields
Progressive:     [██████████] 100/100 ✓ Excellent separation
Overall:         [██████░░░░] 56/100  ⚠️ Needs improvement
```

### Analysis

**Strengths:**
- Excellent progressive disclosure (100/100) - scripts and references properly separated
- Comprehensive Omni Automation reference documentation exists
- Solid technical foundation with multiple automation approaches (JXA, Python, URL schemes, Omni Automation)
- Has IMPROVEMENT_PLAN.md with some relevant ideas already identified

**Weaknesses:**
- Poor conciseness (17/100) - SKILL.md is bloated with 645 lines and 4637 tokens vs 500/2000 guidelines
- Overly complex structure (46/100) - deep nesting, too many sections
- Missing spec compliance (65/100) - deprecated frontmatter fields
- No insight generation - just executes commands and returns data
- Token-expensive pattern - emphasizes repeated direct queries instead of reusable plugins
- No perspective creation guidance
- No proactive automation suggestions
- GTD mentioned in triggers but no actual GTD knowledge provided

**Opportunities:**
- Move detailed command examples to references/ to slim down SKILL.md
- Simplify heading structure and reduce nesting
- Add insight generation capabilities
- Shift to plugin-first approach for token efficiency
- Add perspective creation workflows
- Integrate GTD knowledge as supporting context for better insights
- Enable Apple Foundation Models integration for intelligent task processing
- Create task template system

### Spec Compliance

**Violations:** 0

**Warnings:** 4
- Missing recommended frontmatter field: metadata
- Missing recommended frontmatter field: compatibility
- Missing recommended frontmatter field: license
- Using deprecated 'version' field; use 'metadata.version' instead

---

## Proposed Changes

### Change 1: Add Insight Generation Capabilities

**Type:** ENHANCE
**What:** Transform skill from passive interface to active intelligence system

**Why:**
- Current skill only executes queries and returns raw data
- Users want actionable intelligence, not just task lists
- Analyzing patterns reveals blockers, priorities, and optimization opportunities

**Impact:**
- Enables "what should I focus on?" intelligence
- Surfaces hidden patterns (recurring blockers, overdue trends, underutilized projects)
- Provides recommendations based on task state analysis

**Implementation:**
- Add `scripts/analyze_insights.js` - Omni Automation plugin that analyzes task patterns
- Add `references/insight_patterns.md` - Common patterns to detect and what they mean
- Update SKILL.md with insight generation workflows:
  - "Show me blockers" → analyze dependencies and waiting-for items
  - "What's falling through cracks?" → identify stale projects and overdue clusters
  - "Optimize my workflow" → suggest perspective/automation opportunities
- Examples of insights:
  - "You have 12 tasks waiting on others - consider a 'Waiting For' perspective"
  - "Project X has 15 overdue tasks - needs review or date adjustment"
  - "You create 'Weekly planning' tasks manually - I can create a template plugin"

### Change 2: Shift to Plugin-First Approach

**Type:** RESTRUCTURE
**What:** Position Omni Automation plugins as primary automation method, direct queries as secondary

**Why:**
- Creating reusable plugins is far more token-efficient than repeated queries
- Plugins work cross-platform (Mac + iOS) unlike JXA
- User's stated goal: create automations where useful, not run queries repeatedly
- Current skill buries Omni Automation under JXA/Python approaches

**Impact:**
- Massive token savings - create plugin once, use forever
- Better cross-platform support
- Aligns with user's actual workflow needs

**Implementation:**
- Restructure SKILL.md decision tree to lead with plugins:
  - "Need to do this repeatedly? → Create Omni Automation plugin"
  - "One-off analysis? → Use JXA query"
- Add `examples/plugin-templates/` with starter templates:
  - `insight-analyzer-template.omnifocusjs`
  - `perspective-builder-template.omnifocusjs`
  - `task-template-template.omnifocusjs`
- Create plugin creation workflow in SKILL.md:
  1. Identify repeated task pattern
  2. Use template to scaffold plugin
  3. Customize logic
  4. Install and test
- Move JXA/Python to "Advanced: Direct Queries" section

### Change 3: Add Perspective Creation Guidance

**Type:** ENHANCE
**What:** Enable custom perspective design for consistent task viewing

**Why:**
- Perspectives are core to effective OmniFocus usage
- User specifically wants "perspectives for viewing things consistently"
- Current skill has zero perspective creation guidance
- GTD methodology relies heavily on perspectives (next actions, waiting for, etc.)

**Impact:**
- Users can create purpose-built views
- Supports GTD workflow implementation
- Enables consistent task review processes

**Implementation:**
- Add `references/perspective_creation.md`:
  - How perspectives work (rules, grouping, sorting)
  - Common perspective patterns (by tag, by due date, by project status)
  - GTD-aligned perspectives (next actions, waiting for, someday/maybe)
  - How to create via OmniFocus UI (can't script perspective creation currently)
- Add perspective design workflow to SKILL.md:
  1. Identify what you need to see consistently
  2. Define rules (tags, due dates, project states)
  3. Choose grouping/sorting
  4. Create in OmniFocus UI following reference guide
- Add example perspective configs:
  - Next Actions by Context
  - Review by Project Status
  - Waiting For tracking
  - Overdue with escalation

### Change 4: Add GTD Knowledge as Supporting Context

**Type:** ENHANCE
**What:** Add GTD methodology reference to inform better insights and automation

**Why:**
- GTD principles help identify what insights are valuable (e.g., next actions vs any actions)
- Understanding GTD workflow helps suggest better automations
- Informs perspective design (GTD relies on specific views)
- Not primary focus but critical supporting knowledge

**Impact:**
- Better insight relevance (understand what users need to see)
- More effective automation suggestions (aligned with GTD workflow)
- Helps users implement GTD methodology in OmniFocus

**Implementation:**
- Add `references/gtd_context.md` (concise, focused on OmniFocus implementation):
  - Core GTD principles (collect, process, organize, review, do)
  - How OmniFocus implements GTD (projects, tags/contexts, perspectives, review)
  - Common GTD workflows in OmniFocus
  - How insights should align with GTD (e.g., "next actions" not "all tasks")
- Update SKILL.md to reference GTD when relevant:
  - Insight generation considers GTD workflow
  - Perspective examples follow GTD patterns
  - Automation suggestions aligned with GTD needs
- Keep GTD as supporting context, not primary content

### Change 5: Add Task Template System

**Type:** ENHANCE
**What:** Create system for reusable task patterns via Omni Automation plugins

**Why:**
- User mentioned "task templates or integrating with Apple's Foundation Models"
- Repeated task patterns (weekly review, meeting prep) waste time
- Templates ensure consistency

**Impact:**
- Faster task creation for common patterns
- Consistency in recurring workflows
- Foundation for Foundation Models integration (templates + AI customization)

**Implementation:**
- Add `examples/templates/` with template plugins:
  - `weekly-review-template.omnifocusjs` - Creates GTD weekly review checklist
  - `meeting-prep-template.omnifocusjs` - Standard meeting preparation tasks
  - `project-kickoff-template.omnifocusjs` - New project setup checklist
- Each template is an Omni Automation plugin that:
  - Prompts for variables (project name, date, etc.)
  - Creates structured task hierarchy
  - Sets appropriate tags, due dates, defer dates
- Add template creation workflow to SKILL.md:
  1. Identify recurring task pattern
  2. Use template starter (in examples/)
  3. Customize task structure
  4. Add variable prompts
  5. Install as plugin
- Future enhancement: Use Foundation Models to customize templates based on context

### Change 6: Simplify SKILL.md Structure

**Type:** RESTRUCTURE
**What:** Move detailed command-line examples to references, focus SKILL.md on workflows

**Why:**
- 645 lines is far beyond 500-line guideline
- 4637 tokens exceeds 2000-token guideline
- Extensive JXA/Python command examples belong in references/
- SKILL.md should guide workflows, not document every CLI flag

**Impact:**
- Conciseness: 17 → ~75 (target 300 lines, 1500 tokens)
- Complexity: 46 → ~75 (reduce nesting, simplify structure)
- Faster loading, easier scanning

**Implementation:**
- Create `references/jxa_commands.md` - move all JXA command examples and flags
- Create `references/python_queries.md` - move all Python query examples
- Slim SKILL.md to:
  - **When to Use** (5-10 lines)
  - **Decision Tree** (plugin-first approach, 15 lines)
  - **Insight Generation** (workflows, 30 lines)
  - **Creating Plugins** (workflow, 40 lines)
  - **Perspective Design** (workflow, 30 lines)
  - **Task Templates** (workflow, 25 lines)
  - **Advanced: Direct Queries** (brief pointer to references, 10 lines)
  - **Resources** (list references and examples, 10 lines)
- Reduce nesting from 4 levels to max 3
- Use tables/lists instead of verbose text where possible

### Change 7: Fix Spec Compliance

**Type:** ENHANCE
**What:** Update frontmatter to follow Agent Skills specification

**Why:**
- Using deprecated 'version' field
- Missing recommended metadata fields
- Improves marketplace compatibility

**Impact:**
- Spec Compliance: 65 → 100
- Better tool support
- Professional polish

**Implementation:**
- Update SKILL.md frontmatter:
  ```yaml
  ---
  name: omnifocus-manager
  description: Interface with OmniFocus to surface insights, create reusable automations and perspectives, and suggest workflow optimizations. Use when analyzing tasks, building plugins, designing perspectives, or identifying automation opportunities. Trigger when user mentions OmniFocus, task insights, automation creation, or perspective design.
  metadata:
    version: 1.1.0
    compatibility: "OmniFocus 3.14+, macOS 12+, iOS 16+"
    license: MIT
  ---
  ```
- Remove old 'version' field

### Change 8: Enable Apple Foundation Models Integration (Future Prep)

**Type:** ENHANCE
**What:** Prepare foundation for Apple Intelligence integration in task processing

**Why:**
- User specifically mentioned "integration with Apple's Foundation Models"
- Foundation Models can enhance template customization
- Could power smarter insight generation
- Future-proofs the skill

**Impact:**
- Enables AI-powered task processing (future)
- Foundation for intelligent template customization
- Smarter insight generation potential

**Implementation:**
- Add `references/foundation_models_integration.md`:
  - Overview of Apple Foundation Models capabilities
  - Potential integration points:
    - Template customization based on context
    - Natural language task creation → structured tasks
    - Intelligent insight generation
    - Pattern detection in task data
  - Example workflows (conceptual for now)
  - Technical approach (AppleScript → Shortcuts → Foundation Models)
- Add placeholder in SKILL.md mentioning future Foundation Models integration
- Note: Full implementation pending Foundation Models API availability

---

## Expected Outcome

### Metrics (After)

```
SKILL.md: ~300 lines (-345, -53%)
Tokens: ~1500 (-3137, -68%)
References: 6 files (+4), ~1800 lines (+909)
Scripts: 3 (+1), ~1500 lines (+250)
Assets: 3 template plugins (+3)
Nesting depth: 3 (-1)

Conciseness:     [████████░░] 75/100 (+58)
Complexity:      [████████░░] 75/100 (+29)
Spec Compliance: [██████████] 100/100 (+35)
Progressive:     [██████████] 100/100 (maintained)
Overall:         [█████████░] 87/100 (+31)
```

### Success Criteria

- [ ] SKILL.md under 350 lines and 1800 tokens
- [ ] Insight generation capabilities demonstrated with examples
- [ ] Omni Automation plugins positioned as primary approach
- [ ] Perspective creation workflow documented
- [ ] GTD context reference created (concise, supporting role)
- [ ] At least 3 working template plugins in examples/
- [ ] All spec compliance warnings resolved
- [ ] Overall quality score above 85/100

### Expected Benefits

- **Token Efficiency:** Users create plugins once instead of running queries repeatedly
- **Actionable Intelligence:** Skill provides insights and recommendations, not just data
- **Cross-Platform:** Omni Automation works on Mac + iOS
- **GTD-Aligned:** Insights and perspectives support GTD methodology
- **Automation Discovery:** Proactively suggests optimization opportunities
- **Future-Ready:** Foundation Models integration prepared
- **Professional Quality:** Spec compliant, well-structured

---

## Actual Outcome (After Implementation)

*(To be filled in during implementation)*

### Metrics (Actual)

```
(Pending implementation)
```

### Comparison to Expected

**Better than expected:**
- (TBD)

**As expected:**
- (TBD)

**Worse than expected:**
- (TBD)

### Success Criteria Results

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Notes

(Implementation notes will be added here)

---

## Revision History

### v1 (2025-12-22T13:32:00Z)
- Initial plan created from research findings
- Focused on insights/automation primary, GTD supporting
- 8 proposed changes addressing core gaps

---

## Research Findings (Reference)

### Domain Classification

**Domain:** productivity
**Complexity:** Meta
**Special Considerations:**
- Contains executable scripts - ensure proper error handling
- Contains reference files - check for duplication with SKILL.md
- Meta skill - must align with Agent Skills specification

### Current Implementation Gaps

**No Insight Generation:**
- Current skill executes queries but doesn't analyze or recommend
- Missing pattern detection (blockers, trends, optimization opportunities)
- No "what should I focus on?" intelligence

**Token-Expensive Pattern:**
- Emphasizes direct queries over reusable plugins
- Users pay token cost repeatedly for same operations
- Omni Automation plugins buried, should be primary

**Limited Creation Support:**
- No perspective creation guidance (user's stated need)
- Task templates mentioned in old IMPROVEMENT_PLAN but not implemented
- No automation opportunity detection

**GTD Knowledge Missing:**
- Mentioned in trigger but not provided
- Reduces insight relevance (don't know what "next action" means)
- Can't suggest GTD-aligned perspectives without understanding GTD

### Consolidation Opportunities

**1. RESTRUCTURE: Move Examples to References**
- Rationale: SKILL.md contains 400+ lines of command examples that belong in references/
- Benefit: Dramatically improves conciseness score and readability
- Impact: High - single biggest improvement opportunity

**2. ENHANCE: Insight Generation Layer**
- Rationale: Transform from passive interface to active intelligence
- Benefit: Provides value users can't easily get elsewhere
- Impact: High - differentiates skill from raw OmniFocus access

**3. RESTRUCTURE: Plugin-First Approach**
- Rationale: Aligns with user's stated goals and token efficiency
- Benefit: Massive token savings, better UX, cross-platform
- Impact: High - changes fundamental usage pattern

---

*This plan was generated by skill-planner from comprehensive research findings.*
*All metrics and recommendations based on Agent Skills specification and domain best practices.*
