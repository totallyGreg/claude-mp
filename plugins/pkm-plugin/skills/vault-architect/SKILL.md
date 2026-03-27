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
  version: "1.5.0"
  plugin: "pkm-plugin"
  stage: "3"
---

# Vault Architect

Provide expert guidance for organizing and evolving Obsidian-based PKM systems. Creates *new* structures (templates, schemas, queries, rollups). For maintaining *existing* vault content (metadata drift, duplicates, merges, discovery, visualization), use vault-curator.

Principles: capture quickly, organize via metadata not folders, aggregate automatically through shared properties, roll up progressively (daily→weekly→monthly→yearly), design job-agnostically so work notes survive employer changes.

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

1. **Discover first** — run before asking the user anything:
   ```bash
   obsidian templates && obsidian tags all counts && obsidian folders
   uv run scripts/analyze_vault.py ${VAULT_PATH}
   ```
2. Identify pain points from observed data (orphans, schema gaps, missing templates)
3. Ask about philosophy and priorities only after surfacing findings
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

### Cross-Skill Handoff

After architect work, offer curator follow-through to close the loop:
- **New template** → "Run schema drift check to migrate existing notes to this schema?"
- **New schema** → "Suggest missing properties on existing notes of this type?"
- **MOC template** → "Find orphaned notes to seed this MOC?"
- **Folder refinement** → "Generate canvas map to verify connections?"
- **QuickAdd workflow** → "Audit existing captures against this new workflow?"

## Design Principles

**Do:** Start simple — add complexity only when needed. Use frontmatter over folders for dynamic structure. Test templates with sample notes. Leverage aliases for automatic aggregation. Embed Bases views to bring organization to notes. Document conventions in a vault System Guide. Migrate patterns incrementally.

**Avoid:** Manual filing (users forget folder structures). Rigid folder hierarchies. Duplicating information (use queries and embeds). Hardcoded paths (breaks on job change). Inline Dataview metadata (Bases requires frontmatter). Designing notes in isolation without considering relationships.

---

When working with users, ask questions to understand their workflow before making recommendations. Every PKM system is personal — solutions should fit their thinking patterns, not impose rigid structure.
