---
name: vault-architect
description: >
  This skill should be used when users ask to "create Obsidian templates", "create a template",
  "create a .base file", "design Bases queries", "set up vault structure",
  "configure Templater workflows", "set up daily weekly monthly rollup",
  "analyze vault organization", "configure Excalibrain", "build temporal rollup system",
  "update frontmatter schema", "fix vault organization", or "add metadata to templates".
  Architects new PKM structures and provides guidance for Templater, Bases, Chronos,
  and QuickAdd patterns. Particularly useful for creating automatic note organization systems,
  temporal rollup structures (daily to yearly), and maintaining job-agnostic organizational patterns.
  Do NOT use for maintaining or evolving existing vault content (metadata drift, duplicate notes,
  merges, link redirects, canvas generation — use vault-curator for those).
license: MIT
compatibility: Requires python3 and uv for script execution
metadata:
  version: "1.4.0"
  plugin: "pkm-plugin"
  stage: "3"
---

# Vault Architect

## Overview

Provide expert guidance for organizing and evolving Obsidian-based Personal Knowledge Management systems. Help users create efficient workflows for quick note capture with automatic organization through metadata, templates, and relationship queries.

**Scope boundary:** This skill creates *new* structures (templates, schemas, queries, rollups). For maintaining and evolving *existing* vault content (metadata drift, duplicates, merges, discovery, visualization), use the vault-curator skill.

## Vault Discovery

Before making structure recommendations, always discover the current vault state. This prevents redundant suggestions and grounds recommendations in what actually exists.

```bash
obsidian templates              # what templates already exist
obsidian tags all counts        # tag usage distribution
obsidian folders               # actual folder structure
uv run scripts/analyze_vault.py ${VAULT_PATH}   # full health check
```

Key signals to surface before recommending:
- **Existing templates** — avoid duplicating; refine or extend instead of creating new ones
- **Tag distribution** — identify overloaded or underused tags that indicate schema gaps
- **Orphan count** — high orphans suggest broken capture flows or missing MOC templates
- **fileClass distribution** — which note types are most numerous and need schema attention

If a `_vault-profile.md` exists in the vault root, read it first for accumulated context about conventions and past decisions.

## Core PKM Principles

1. **Quick Capture, Smart Organization** - Notes should be created quickly. Organization happens automatically through metadata and queries, not manual filing.
2. **Metadata Over Folders** - Use frontmatter properties and Bases queries for dynamic structure. Folders are for major grouping only.
3. **Automatic Aggregation** - Notes appear in relevant views through shared metadata (aliases, tags, properties) rather than manual linking.
4. **Progressive Disclosure** - Daily notes roll up to weekly, weekly to monthly, monthly to quarterly, quarterly to yearly.
5. **Job-Agnostic Structure** - Work notes should allow easy archiving when changing jobs while maintaining searchability.

## Core Capabilities

### 1. Vault Analysis and Recommendations

When asked to analyze a vault or suggest improvements:

1. **Understand Current Structure** - Ask about folder philosophy, review templates, identify metadata patterns, check .base files
2. **Analyze for Issues** - Use `scripts/analyze_vault.py` to find untagged notes, orphans, inconsistent frontmatter, duplicate titles, missing temporal links
3. **Provide Actionable Recommendations** - Suggest frontmatter improvements, Bases queries, template consolidation, folder refinements

### 2. Template Creation with Templater

Create templates that prompt for input, rename/move files automatically, set frontmatter, embed Bases views, and position the cursor.

**Key patterns:** `tp.system.prompt()` for input, `tp.file.rename()`/`tp.file.move()` for file management, `tp.date.now()` for dates, `tp.file.cursor()` for cursor placement.

**References:**
- `references/templater-api.md` - Complete API reference for all tp.* functions
- `references/templater-patterns.md` - Common patterns, advanced examples, and full meeting note template

### 3. Bases Query Design

Bases is the preferred method for creating dynamic relationships (replacing Dataview inline queries). Create `.base` files with properties, formulas, views, and filters.

Use templates from `assets/base-templates/` as starting points (related-files, temporal-rollup, terminology, customer-notes).

**References:**
- `references/bases-query-reference.md` - Complete query syntax, filters, and view types
- `references/bases-patterns.md` - Alias aggregation, temporal queries, relationship views, file type filtering

### 4. Frontmatter Schema Design

Design frontmatter with essential fields (title, aliases, tags, dates), relationship fields for Bases queries (customer, project, Week/Month/Quarter/Year links), and semantic fields for Excalibrain (parent, child, left-friend, right-friend).

Validate schemas with `scripts/validate_frontmatter.py`. Document conventions in the vault's System Guide.

**References:**
- `references/excalibrain-metadata.md` - Complete semantic field documentation

### 5. Timeline Visualization with Chronos

Visualize events, meetings, and projects on timelines using the Chronos plugin integrated with Bases. Events require `start` datetime; periods require `start` and `end`. Use `color` and `type` properties for visual/categorical grouping.

**References:**
- `references/chronos-syntax.md` - Event types, frontmatter integration, timeline patterns

### 6. Quick Capture and Automation with QuickAdd

QuickAdd (v2.12.0+) provides four choice types: Template, Capture, Macro, Multi. Supports format syntax (`{{VALUE}}`, `{{DATE}}`, `{{VDATE}}`, `{{FIELD}}`), case transforms, `.base` template insertion, Canvas capture, CLI automation, and AI integration.

**References:**
- `references/quickadd-patterns.md` - Complete reference: format syntax, all choice types, API, CLI, Canvas, Base workflows, and patterns

### 7. Temporal Rollup Systems

Create automatic aggregation: daily -> weekly -> monthly -> quarterly -> yearly. Each level embeds summaries from the level below via Bases queries and includes manual reflection sections (Wins/Challenges/Improvements).

**Key design:** Each note's frontmatter links to parent temporal notes (Week, Month, Quarter, Year). Bases queries filter by these links or date ranges.

### 8. Job-Agnostic Work Organization

Organize work notes to survive job changes. Keep company profiles separate from job-specific notes. Use consistent `employer` and `customer` fields. When changing jobs, archive the folder and update template paths.

**References:**
- `references/folder-structures.md` - Example vault organizations for different workflows

### 9. Vault System Documentation

Each vault should maintain a System Guide documenting: folder structure, metadata schema, template inventory, Bases queries, conventions, and migration history.

## Workflows

### Creating a New Template

1. Understand the use case (note type, storage, relationships)
2. Design frontmatter (required fields, relationship fields, semantic fields)
3. Write Templater logic (prompts, renaming, auto-movement)
4. Add content structure (Bases views, headings, cursor position)
5. Create/update corresponding Bases queries
6. Test with a sample note

### Analyzing and Improving Vault Organization

1. Understand current state (philosophy, structure, templates, queries)
2. Run `scripts/analyze_vault.py` for automated checks
3. Identify pain points (manual work, hard-to-find notes, inconsistencies)
4. Propose specific improvements (frontmatter, queries, templates, folders)
5. Implement incrementally, starting with highest-impact changes

### Workflow Lookup, Capture, and Refinement

**Before creating a workflow note, always check if one exists:**

```bash
obsidian search query="<topic>" limit=10
obsidian read file="Workflows"   # shows Workflows.base — scan Current Workflows view
```

Workflows are discovered by `900 📐Templates/970 Bases/Workflows.base` via any of:
- `file.folder == "700 Notes/Workflows"`
- `fileClass == "Workflow"`
- `tags.contains("workflow")`

**Creating a new workflow note:** use `900 📐Templates/910 File Templates/New Workflow.md` — prompts for title, auto-moves to `700 Notes/Workflows/`. Required fields: `status`, `type`, `parent`/`child`, `dependencies`, `fileClass: Workflow`. See `[[Capture to Review]]` as the canonical structure example.

## Cross-Skill Handoff

After architect work, offer curator follow-through to close the loop:
- **New template** → "Run schema drift check to migrate existing notes to this schema?"
- **New schema** → "Suggest missing properties on existing notes of this type?"
- **MOC template** → "Find orphaned notes to seed this MOC?"
- **Folder refinement** → "Generate canvas map to verify connections?"
- **QuickAdd workflow** → "Audit existing captures against this new workflow?"

## Resources

### scripts/
- `analyze_vault.py` - Vault analysis (untagged notes, orphans, inconsistencies)
- `validate_frontmatter.py` - Frontmatter validation against schema

### references/
- `templater-api.md` - Templater API reference
- `templater-patterns.md` - Templater code patterns and examples
- `bases-query-reference.md` - Bases query syntax reference
- `bases-patterns.md` - Bases query examples
- `excalibrain-metadata.md` - Excalibrain semantic relationship mapping
- `folder-structures.md` - Example vault organizations
- `chronos-syntax.md` - Chronos timeline syntax
- `quickadd-patterns.md` - QuickAdd complete reference (v2.12.0)

### assets/
- `base-templates/` - Starting .base files (related-files, temporal-rollup, terminology, customer-notes)

## Best Practices

1. **Start Simple** - Add complexity only when needed.
2. **Metadata is Key** - Good frontmatter enables automatic organization.
3. **Test Templates** - Create test notes to verify behavior.
4. **Document Conventions** - Maintain a System Guide in the vault.
5. **Incremental Migration** - Change patterns gradually.
6. **Leverage Aliases** - They enable powerful automatic aggregation.
7. **Embed Bases Views** - Bring organization to notes, not notes to folders.

## Common Anti-Patterns

1. **Manual Filing** - Don't rely on users to remember folder structures.
2. **Rigid Hierarchies** - Folders for broad categories only.
3. **Duplicate Information** - Use queries and embeds instead of copying.
4. **Hardcoded Paths** - Make templates adaptable for job changes.
5. **Inline Metadata** - Bases doesn't support dataview inline fields; use frontmatter.
6. **Ignoring Relationships** - Design for how notes connect, not just how they're filed.

---

When working with users, ask questions to understand their workflow before making recommendations. Every PKM system is personal — solutions should fit their thinking patterns, not impose rigid structure.
