---
name: obsidian-pkm-manager
description: Expert guidance for managing Obsidian-based Personal Knowledge Management (PKM) systems. This skill should be used when organizing, optimizing, or evolving note-taking workflows in Obsidian, including template creation with Templater, relationship management with Bases, vault structure analysis, frontmatter design, and metadata strategies. Particularly useful for creating automatic note organization systems, temporal rollup structures (daily to yearly), and maintaining job-agnostic organizational patterns.
metadata:
  version: "1.0.0"
---

# Obsidian PKM Manager

## Overview

Provide expert guidance for organizing and evolving Obsidian-based Personal Knowledge Management systems. Help users create efficient workflows for quick note capture with automatic organization through metadata, templates, and relationship queries.

## Core PKM Principles

When working with PKM systems, prioritize these principles:

1. **Quick Capture, Smart Organization** - Notes should be created quickly with minimal friction. Organization happens automatically through metadata and queries, not manual filing.

2. **Metadata Over Folders** - Use frontmatter properties and Bases queries to create dynamic structure rather than rigid folder hierarchies. Folders are for major grouping only (e.g., separating work from personal, or archiving old companies).

3. **Automatic Aggregation** - Design systems where notes automatically appear in relevant views through shared metadata (aliases, tags, properties) rather than manual linking.

4. **Progressive Disclosure** - Daily notes roll up to weekly, weekly to monthly, monthly to quarterly, quarterly to yearly. Each level provides increasing abstraction while preserving detail through embedded queries.

5. **Job-Agnostic Structure** - Work-related notes should be organized to allow easy archiving when changing jobs while maintaining searchability and relationship integrity.

## When to Use This Skill

Use this skill when users ask for help with:

- Organizing or reorganizing their Obsidian vault structure
- Creating or improving Templater templates
- Designing frontmatter schemas and metadata strategies
- Building Bases queries and relationship views
- Setting up temporal rollup systems (daily → weekly → monthly)
- Analyzing vault consistency and suggesting improvements
- Migrating from Dataview to Bases
- Understanding Excalibrain metadata requirements
- Creating automatic note categorization systems
- Designing job-agnostic work note structures

## Core Capabilities

### 1. Vault Analysis and Recommendations

When asked to analyze a vault or suggest improvements:

1. **Understand Current Structure**
   - Ask about their folder organization philosophy
   - Review existing templates to understand their note types
   - Identify metadata patterns in use
   - Check for .base files and understand their queries

2. **Analyze for Issues**
   - Use `scripts/analyze_vault.py` to find:
     - Untagged notes
     - Orphaned files (no links in or out)
     - Inconsistent frontmatter patterns
     - Duplicate or similar note titles
     - Missing temporal links (daily notes without week/month references)

3. **Provide Actionable Recommendations**
   - Suggest specific frontmatter improvements
   - Recommend Bases queries for automatic organization
   - Identify opportunities for template consolidation
   - Propose folder structure refinements based on their workflow

### 2. Template Creation with Templater

When helping create or improve templates:

**Key Templater Patterns:**

```javascript
// Prompt user for input
const value = await tp.system.prompt("Question?", defaultValue);

// Rename current file
await tp.file.rename(newName);

// Move file to folder
await tp.file.move("folder/path/" + fileName);

// Get date in specific format
tp.date.now("YYYY-MM-DD", offset, reference, referenceFormat)

// Include another template
tp.file.include("[[Template Name]]")

// Set cursor position
tp.file.cursor(1)

// Focus editor
app.workspace.activeLeaf.view.editor?.focus();
```

**Template Structure Best Practices:**

1. **File Movement Logic** - Templates should:
   - Prompt for essential information first
   - Rename the file based on user input
   - Move to the appropriate folder automatically
   - Use consistent naming patterns

2. **Frontmatter Design**
   - Include `aliases` for alternative names/abbreviations
   - Add `tags` for categorical organization
   - Set `date created` and `date modified` for temporal tracking
   - Add relationship properties for Bases queries
   - Use `fileClass` for broad categorization

3. **Dynamic Content**
   - Embed Bases views using `![[BaseName.base#ViewName]]`
   - Include reusable template fragments
   - Position cursor at natural starting point

**Example: Meeting Note Template Pattern**

```markdown
<%*
const meetingTitle = await tp.system.prompt("Meeting title?", tp.file.title);
const customer = await tp.system.suggester(
  (item) => item,
  ["Customer A", "Customer B", "Customer C"]
);
const projectFolder = "700 Notes/Work Notes/";
await tp.file.move(projectFolder + tp.date.now("YYYY-MM-DD") + " " + meetingTitle);
-%>
---
title: <% meetingTitle %>
date: <% tp.file.creation_date() %>
customer: [[<% customer %>]]
tags: [meeting, work]
aliases:
  - <% tp.date.now("YYYY-MM-DD") %> <% meetingTitle %>
---
# <% meetingTitle %>

Customer: [[<% customer %>]]
Date: <% tp.date.now("YYYY-MM-DD") %>

## Notes

<% tp.file.cursor(1) %>

## Action Items

- [ ]

![[Notes.base#Related Files]]
```

See `references/templater-patterns.md` for more examples and advanced patterns.

### 3. Bases Query Design

Bases is the preferred method for creating dynamic relationships (replacing Dataview inline queries).

**Core Bases Concepts:**

- **Properties** - Define which file properties to display (e.g., `file.name`, `file.tags`, `note.summary`)
- **Formulas** - Calculated values (e.g., `file.backlinks.map(value.asFile())`)
- **Views** - Tables with filters, sorting, and column configuration
- **Filters** - Query logic to select notes (e.g., `file.tags.contains("term")`)

**Common Bases Patterns:**

See `references/bases-patterns.md` for detailed examples including:
- Automatic alias aggregation (showing all terms with same abbreviation)
- Temporal queries (all notes from this week/month)
- Relationship views (all meetings for a customer)
- File type filtering and organization

**Creating a New .base File:**

Use templates from `assets/base-templates/` as starting points:
- `related-files.base` - Generic backlinks view
- `temporal-rollup.base` - Daily → weekly → monthly queries
- `terminology.base` - Alias-based aggregation
- `customer-notes.base` - Work note organization

### 4. Frontmatter Schema Design

When designing or improving frontmatter schemas:

**Essential Fields:**
- `title` - Clear, human-readable title
- `aliases` - Alternative names, abbreviations, dates
- `tags` - Categorical organization (use `/` for hierarchy)
- `date created` / `date modified` - Temporal tracking

**Relationship Fields:**
- Use for Bases queries
- Link to related notes: `customer: [[Customer Name]]`
- Multiple links: `projects: [[[Project A]], [[Project B]]]`
- Temporal hierarchy: `Week`, `Month`, `Quarter`, `Year`

**Semantic Fields (for Excalibrain):**
- `parent` - Parent concept/category
- `child` - Sub-concepts
- `left-friend` - Related concepts (same category)
- `right-friend` - Related concepts (different category)

See `references/excalibrain-metadata.md` for complete semantic field documentation.

**Field Consistency:**
- Use consistent field names across templates
- Document your schema in vault's "System Guide" note
- Validate with `scripts/validate_frontmatter.py`

### 5. Temporal Rollup Systems

Creating automatic aggregation from daily → weekly → monthly → quarterly → yearly:

**Design Pattern:**

Each level embeds summaries from the level below using Bases queries or dataviewjs:

```markdown
## Weekly Thoughts
![[Logs.base#This Week]]

### Distilled Thoughts
[Manual reflection on the week]
```

**Key Implementation Details:**

1. **Temporal Links in Frontmatter**
   - Daily notes link to: Week, Month, Quarter, Year
   - Weekly notes link to: Month, Quarter, Year
   - Monthly notes link to: Quarter, Year

2. **Query Patterns**
   - Filter by date range: `where date >= startOf('week')`
   - Filter by linked property: `where Week == [[2025-W50]]`
   - Sort by date for chronological display

3. **Reflection Sections**
   - Each level has both automated rollup AND manual reflection
   - Wins/Challenges/Improvements pattern works well
   - Embed specific sections from lower levels: `![[2025-12-15#Key Events]]`

See existing templates for patterns:
- `910 File Templates/🌄 New Day.md`
- `910 File Templates/🗓 New Week.md`
- `910 File Templates/📅 New Month.md`

### 6. Job-Agnostic Work Organization

For organizing work notes that survive job changes:

**Recommended Structure:**

```
700 Notes/
├── Companies/           # Company profiles (persist across jobs)
│   └── CustomerName.md  # Company info, relationships, history
├── CurrentJob Notes/    # All notes for current employment
│   ├── Customers/       # Customer project notes
│   ├── Meetings/        # Meeting notes
│   ├── Projects/        # Project documentation
│   └── People/          # Colleague notes
└── ArchivedJob Notes/   # Previous employment (read-only)
    └── 2020-2023 PreviousCompany/
```

**Key Principles:**

1. **Separation** - Keep company profiles separate from job-specific notes
2. **Linking** - Meeting notes link to company profiles: `customer: [[CompanyName]]`
3. **Archiving** - When changing jobs, rename folder to indicate dates
4. **Metadata** - Use consistent `employer` field in frontmatter for filtering

**Template Updates:**

When changing jobs, update templates to point to new work folder:
- Search for hardcoded folder paths (e.g., "700 Notes/PAN Notes/")
- Replace with new company name
- Consider using Templater suggester for multi-employer scenarios

### 7. Vault System Documentation

Each vault should maintain a "System Guide" that documents:

- Current folder structure and philosophy
- Active metadata schema (all properties in use)
- Template inventory and usage
- Bases queries and their purposes
- Conventions (naming, tagging, linking)
- Migration history (e.g., Dataview → Bases transition)

**Location Recommendation:** `900 📐Templates/PKM-System-Guide.md`

**Update Triggers:**
- New template created
- Frontmatter schema changes
- Folder structure reorganization
- New organizational pattern adopted

The skill can help create this guide by analyzing the vault and documenting current patterns.

## Workflow: Creating a New Template

When a user wants to create a new template:

1. **Understand the Use Case**
   - What type of note is this?
   - What information needs to be captured?
   - Where should it be stored?
   - What relationships does it have?

2. **Design the Frontmatter**
   - Required fields: title, aliases, tags, dates
   - Relationship fields for Bases queries
   - Semantic fields if using Excalibrain
   - Type-specific fields (e.g., `customer`, `summary`, `priority`)

3. **Write Templater Logic**
   - Prompts for essential information
   - File renaming logic
   - Auto-movement to correct folder
   - Dynamic alias generation

4. **Add Content Structure**
   - Embed relevant Bases views
   - Include common headings
   - Add template fragments if needed
   - Set cursor position

5. **Create or Update Bases Query**
   - Does this note type need a new .base file?
   - Should it appear in existing queries?
   - Update filters to include new tags/properties

6. **Test and Iterate**
   - Create a test note with the template
   - Verify auto-movement and renaming
   - Check that Bases queries display correctly
   - Refine based on actual usage

## Workflow: Analyzing and Improving Vault Organization

When a user wants to improve their vault:

1. **Understand Current State**
   - Ask about their organizational philosophy
   - Review folder structure
   - Examine representative templates
   - Check existing Bases queries

2. **Run Analysis**
   - Use `scripts/analyze_vault.py` for automated checks
   - Review git status for frequently modified areas
   - Look for patterns in note creation

3. **Identify Pain Points**
   - Where is manual work happening that could be automated?
   - Are notes hard to find or categorize?
   - Is the structure fighting their workflow?
   - Are there inconsistencies in metadata?

4. **Propose Improvements**
   - Specific frontmatter additions
   - New or updated Bases queries
   - Template consolidation or creation
   - Folder structure adjustments
   - Workflow simplifications

5. **Implement Incrementally**
   - Start with highest-impact changes
   - Update templates first
   - Add new Bases queries
   - Migrate existing notes gradually
   - Document changes in System Guide

## Resources

### scripts/
- `analyze_vault.py` - Analyze vault for common issues (untagged notes, orphans, inconsistencies)
- `validate_frontmatter.py` - Check frontmatter against schema

### references/
- `templater-patterns.md` - Common Templater code patterns and examples
- `bases-patterns.md` - Example Bases queries for various use cases
- `excalibrain-metadata.md` - Excalibrain semantic relationship mapping
- `folder-structures.md` - Example vault organizations for different workflows

### assets/
- `base-templates/` - Starting .base files for common scenarios
  - `related-files.base`
  - `temporal-rollup.base`
  - `terminology.base`
  - `customer-notes.base`
- `templater-snippets/` - Reusable Templater code blocks

## Best Practices

1. **Start Simple** - Don't over-engineer. Add complexity only when needed.
2. **Metadata is Key** - Good frontmatter enables automatic organization.
3. **Test Templates** - Always create test notes to verify template behavior.
4. **Document Conventions** - Maintain a System Guide in the vault.
5. **Incremental Migration** - When changing patterns, migrate gradually.
6. **Leverage Aliases** - They enable powerful automatic aggregation.
7. **Embed Bases Views** - Bring organization to notes, not notes to folders.
8. **Temporal Hierarchy** - Day → Week → Month → Quarter → Year creates reviewable history.

## Common Anti-Patterns to Avoid

1. **Manual Filing** - Don't rely on users to remember folder structures.
2. **Rigid Hierarchies** - Folders should be broad categories, not detailed organization.
3. **Duplicate Information** - Use queries and embeds instead of copying content.
4. **Hardcoded Paths** - Make templates adaptable for job changes or reorganization.
5. **Inline Metadata** - Bases doesn't support dataview inline fields; use frontmatter.
6. **Ignoring Relationships** - Design for how notes connect, not just how they're filed.

## Examples

### Example 1: User wants meeting notes to link to customers

**Question to Ask:**
"Do you have a Customer/Company template already? Should meeting notes link to a company profile or directly to project notes?"

**Recommendation:**
Create two-level structure:
1. Company profile in `700 Notes/Companies/` (persistent)
2. Meeting note in `700 Notes/Work Notes/Meetings/` (job-specific)

Meeting frontmatter includes:
```yaml
customer: [[CompanyName]]
project: [[ProjectName]]
```

Company profile embeds:
```markdown
![[Notes.base#Company Meetings]]
```

Where `Notes.base` has a view filtering for `customer == [[this.file.name]]`

### Example 2: User has inconsistent tagging

**Run Analysis:**
```bash
python3 scripts/analyze_vault.py /path/to/vault --check-tags
```

**Findings:**
- 47 notes use `#meeting`, 23 use `#meetings`
- 15 notes in "Meetings" folder have no tag
- Tag hierarchy inconsistent: some use `work/meeting`, others `meeting/work`

**Recommendation:**
1. Standardize on `#meeting` (singular)
2. Update templates to use consistent tag
3. Use Bases filter: `file.folder.contains("Meetings") OR file.tags.contains("meeting")`
4. Document convention in System Guide

### Example 3: User wants to create abbreviation/term system

**Review Existing Pattern:**
User has working system where:
- Abbreviation notes in `700 Notes/Terminology/`
- Each term that shares abbreviation has it in `aliases`
- Bases query shows all terms with matching alias

**Enhancement:**
Create template that:
1. Prompts for abbreviation
2. Creates note named for abbreviation
3. Embeds Bases view: `![[Terminology.base#Terms with Context]]`
4. Bases filter: `aliases == [[this.file.name]]`

This automatically aggregates all terms sharing that abbreviation.

---

When working with users, ask questions to understand their workflow before making recommendations. Every PKM system is personal, so solutions should fit their thinking patterns, not impose a rigid structure.
