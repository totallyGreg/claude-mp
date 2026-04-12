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
  version: "1.9.0"
  plugin: "archivist"
  stage: "3"
---

# Vault Architect

Provide expert guidance for organizing and evolving Obsidian-based PKM systems. Creates *new* structures (templates, schemas, queries, rollups). For maintaining *existing* vault content (metadata drift, duplicates, merges, discovery, visualization), use vault-curator.

Principles: capture quickly, organize via metadata not folders, aggregate automatically through shared properties, roll up progressively (daily→weekly→monthly→yearly), design job-agnostically so work notes survive employer changes.

## Vault Discovery

Before making structure recommendations, always discover the current vault state. This prevents redundant suggestions and grounds recommendations in what actually exists.

> **CLI source:** `obsidian-cli` skill from the [obsidian-skills](https://github.com/kepano/obsidian-skills) marketplace. Parameter distinction: `path=exact/path.md` (vault-relative path) vs `file=name` (link-style resolution — use `file=` when resolving folder notes, e.g. `obsidian read file="Workflows"`). For bugs and fallback patterns, see `${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/references/cli-patterns.md`. Fallback: Glob/Grep/Read on vault files at `${VAULT_PATH}`.

```bash
obsidian templates              # what templates already exist
obsidian tags all counts        # tag usage distribution
obsidian folders               # actual folder structure
uv run scripts/analyze_vault.py ${VAULT_PATH}   # full health check
```

**Linter plugin config:** Read `.obsidian/plugins/obsidian-linter/data.json` at the vault root to discover active formatting rules before writing any note content or templates. Linter auto-reformats on save — notes written in violation will silently change, causing spurious git diffs and user confusion.

```bash
# Read active Linter rules
cat "${VAULT_PATH}/.obsidian/plugins/obsidian-linter/data.json"
```

Key rules to check and apply when writing vault content:
- `yaml-title-alias` — whether title aliases are auto-managed
- `yaml-key-sort` — expected frontmatter key ordering
- `trailing-spaces` — trailing whitespace handling
- `heading-blank-lines` — blank lines required before/after headings
- `paragraph-blank-lines` — blank lines between paragraphs
- `empty-line-around-code-blocks` — blank lines around fenced code blocks
- `yaml-timestamp-date-created`/`yaml-timestamp-date-modified` — auto-managed date fields

If the file does not exist, Linter is not installed — proceed with vault conventions only.

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

### 9. Collection Folder Pattern

A Collection Folder groups related notes of the same type under a folder with a folder note, a Bases view, and a Templater template. This is the standard unit for any repeating note type (Workflows, People, Ideas, Personas, etc.).

Every healthy collection has five parts: the folder, a folder note (`Folder/Folder.md`) that embeds the Bases view, member notes with a consistent `fileClass`, a Bases file at `900 📐Templates/970 Bases/<Name>.base`, and a Templater template at `900 📐Templates/910 File Templates/New <Type>.md`.

**References:**
- `references/collection-folder-pattern.md` — full anatomy, examples, and health signals

### 10. Vault System Documentation

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

### New Collection Setup

Scaffold a Collection Folder (a named folder for a repeating note type):

1. **Check existing state**: `obsidian read file="<Name>"`, `obsidian read path="900 📐Templates/970 Bases/<Name>.base"`, `obsidian templates`
2. **Design schema** — infer from existing notes or ask user for required fields
3. **Create Bases file** at `900 📐Templates/970 Bases/<Name>.base` — fileClass filter, named view, sorted by `file.mtime DESC`
4. **Create folder note** at `<Folder>/<Folder>.md` — description, schema table, `![[<Name>.base#<View>]]` embed
5. **Create Templater template** at `900 📐Templates/910 File Templates/New <Type>.md` — prompts, auto-move, required frontmatter
6. **Backfill fileClass** on existing members if needed (offer via curator)

After setup, offer: "Run collection health check to verify all parts are consistent?"

**Reference:** `references/collection-folder-pattern.md`

### Vault Profiling

Create or regenerate `_vault-profile.md` in the vault root. This profile provides accumulated context for all future archivist sessions — installed plugins, active fileClasses, folder philosophy, schema conventions, and directory trust levels.

**When triggered:** By the archivist agent during initialization when `_vault-profile.md` is absent or corrupted.

**Workflow:**

1. **Discover vault structure:**
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-architect/scripts/analyze_vault.py ${VAULT_PATH}
   obsidian folders
   obsidian templates
   obsidian tags all counts
   ```
   If `obsidian` CLI fails (app not running), fall back to Glob/Grep/Read on vault files.

2. **Discover installed plugins:**
   ```bash
   ls "${VAULT_PATH}/.obsidian/plugins/"
   ```

3. **Sample fileClass distribution:**
   ```bash
   grep -r "^fileClass:" "${VAULT_PATH}" --include="*.md" | sed 's/.*fileClass: *//' | sort | uniq -c | sort -rn
   ```
   Fall back to Grep tool if bash grep is unavailable.

4. **Read Linter config** (if installed):
   ```bash
   cat "${VAULT_PATH}/.obsidian/plugins/obsidian-linter/data.json"
   ```

5. **Analyze folder philosophy** — interpret top-level folder naming convention:
   - Numbered prefixes (e.g., `100`, `200`) → hierarchical organization
   - Emoji markers → functional categorization
   - Plain names → flat/ad-hoc structure

6. **Classify directory trust levels** — categorize each top-level directory:
   | Trust Level | Signals | Example |
   |-------------|---------|---------|
   | **automated/generated** | Names containing "Generated", "Output", "Auto" | `800 Generated/` |
   | **infrastructure** | Names containing "Template", "📐", "System", "Config" | `900 📐Templates/` |
   | **project-scoped** | Names containing "Project", work-related folders | `600 Projects/` |
   | **personal/guarded** | Names containing "Notes", "Journal", "Personal", "Private" | `700 Notes/` |

7. **Propose permission zones** based on folder analysis (see Unit 2 for zone storage):
   - Template/infrastructure folders → architect zones
   - Generated/output folders → designated output zones
   - Everything else → curator zones

8. **Present profile to user** for confirmation before saving.

9. **Write `_vault-profile.md`** to vault root with this structure:

   ```markdown
   ---
   last_updated: YYYY-MM-DD
   managed_by: archivist
   ---

   # Vault Profile

   ## Installed Plugins
   <!-- List of active community plugins -->

   ## Active fileClasses
   <!-- fileClass names with note counts -->

   ## Folder Structure & Philosophy
   <!-- Numbered/emoji convention explanation, top-level folder purposes -->

   ## Directory Trust Levels
   <!-- Each top-level directory with its trust classification -->

   ## Template Inventory
   <!-- Summary of templates in the templates directory -->

   ## Schema Conventions
   <!-- Known frontmatter patterns, naming conventions -->

   ## Linter Rules Summary
   <!-- Key active Linter rules affecting note formatting -->
   ```

   Each section heading is agent-managed. User-added sections (headings not in this list) are preserved during updates.

**On subsequent runs:** The archivist agent's Session Learning handles incremental updates. It diffs current vault state against the profile and updates specific sections by heading, preserving user-added sections.

**Edge cases:**
- Vault with minimal structure (few folders, no templates) → create profile with minimal content, don't pad empty sections
- `_vault-profile.md` exists but is corrupted (malformed YAML frontmatter) → regenerate from scratch, warn user
- Obsidian CLI unavailable → use file tools exclusively, note limitation in profile

### Cross-Skill Handoff

After architect work, offer curator follow-through to close the loop:
- **New collection created** → "Run collection health check to verify all members are consistent?"
- **New template** → "Run schema drift check to migrate existing notes to this schema?"
- **New schema** → "Suggest missing properties on existing notes of this type?"
- **MOC template** → "Find orphaned notes to seed this MOC?"
- **Folder refinement** → "Generate canvas map to verify connections?"
- **QuickAdd workflow** → "Audit existing captures against this new workflow?"

## Write Boundaries

Before writing to any path in the vault, check whether it falls within your allowed zones.

**How to check:** Read `${CLAUDE_PLUGIN_ROOT}/.local.md` and parse the `architect_write_zones:` field. This contains a comma-separated list of vault-relative directory paths. A write is allowed if the target path starts with any listed zone prefix. When multiple zones match, the most-specific (longest) prefix wins.

**Allowed writes:** Template directories, Bases files, script directories, vault infrastructure files (`_vault-profile.md`, system guides), and any path listed in `architect_write_zones`.

**Out-of-zone writes:** If the target path does not match any architect zone, **refuse the write** and suggest using vault-curator instead. Example: "This path is in a curator-managed zone. Use vault-curator to modify note content."

**No zones configured:** If `.local.md` has no zone fields, all writes require user confirmation (existing Bounded Autonomy behavior). Offer to run vault profiling to discover and configure zones.

**All writes require confirmation** — regardless of zone. The zone model determines *which skill* may write, not *whether* to confirm. Confirmation-free writes are deferred until hook-based enforcement is available.

<!-- v2 note: In future versions, this skill may run as an isolated subagent with restricted tools. Write boundaries documented here will become the subagent's tool restrictions. -->

## Design Principles

**Do:** Start simple — add complexity only when needed. Use frontmatter over folders for dynamic structure. Test templates with sample notes. Leverage aliases for automatic aggregation. Embed Bases views to bring organization to notes. Document conventions in a vault System Guide. Migrate patterns incrementally. **Link aggressively** — every reference to another vault entity uses `[[Target]]`, powering backlinks, graph discovery, and rename-safe updates. The `.base` file's default view is canonical for a type's schema; the fileClass note mirrors it.

**Avoid:** Manual filing (users forget folder structures). Rigid folder hierarchies. Duplicating information (use queries and embeds). Hardcoded paths (breaks on job change). Inline Dataview metadata (Bases requires frontmatter). Designing notes in isolation without considering relationships. **Backticked vault entity names** — `` `Workflow.md` `` in prose is a dead reference; `[[Workflow]]` is a living graph node.

For the full linking decision table and schema authority rules, see `vault-curator/references/linking-discipline.md`.

---

When working with users, ask questions to understand their workflow before making recommendations. Every PKM system is personal — solutions should fit their thinking patterns, not impose rigid structure.
