---
name: vault-curator
description: >
  This skill should be used when users ask to "analyze vault metadata",
  "check for schema drift", "fix duplicate notes", "update note properties",
  "generate canvas", "improve vault connections", "create discovery view",
  "validate frontmatter consistency", "build knowledge map",
  "check for orphaned notes", or "analyze note relationships".
  Also handles: "find duplicates", "merge notes", "redirect links",
  "suggest properties", "show connections", "extract meeting from log",
  "migrate vault notes", "visualize my notes", "show me a map",
  "update this note", "write to vault", or "create a note from URL".
  Curates and evolves existing vault content through pattern detection, migration workflows,
  metadata intelligence, consolidation, discovery, visualization, and direct vault writes.
  Do NOT use for creating new templates, schemas, Bases queries, or vault structures
  (use vault-architect for those).
metadata:
  version: "1.9.1"
  plugin: "pkm-plugin"
  stage: "3"
license: MIT
compatibility: Requires python3.11+ and uv for script execution. Obsidian CLI 1.12+ for intelligence workflows.
---

# Vault Curator

Curate and evolve vault content through pattern detection, metadata intelligence, consolidation, discovery, and visualization. Principles: evolve gradually (test on small batches), validate before executing (dry-run first), checkpoint with git before operations, discover existing patterns before suggesting changes.

## Scope Selection

All intelligence workflows (metadata, consolidation, discovery, visualization) begin with scope selection. Large vaults (7K+ files) require scoped operations.

**Workflow:**

1. **Discover vault structure** using CLI or file tools:
   ```bash
   obsidian folders                          # CLI: list all vault folders
   # OR fallback:
   tree -L 2 -d ${VAULT_PATH}               # file tools: directory tree
   ```

2. **Present choices** via AskUserQuestion with top-level directories

3. **User selects scope** (or types a path directly)

4. **Scope all operations** to the selected path for the rest of the session

**Quick path:** If the user mentions a specific topic ("my Docker notes"), use CLI search to find the relevant directory before presenting choices:
```bash
obsidian search query="Docker" format=json   # find matching notes/folders
```

**Edge cases:**
- **Empty scope** (no markdown files): Inform user, suggest broadening
- **Whole vault** requested: Warn about file count, require explicit confirmation
- **Obsidian CLI unavailable**: Fall back to `tree` + Glob/Grep for structure discovery

**CLI delegation:** `obsidian-cli` (operations), `obsidian-markdown` (content), `obsidian-bases` (`.base` files), `json-canvas` (`.canvas` files). To update note content, use `obsidian create path="..." overwrite content="..." silent` (`obsidian file` is read-only). See `references/cli-patterns.md` for bugs. Fallback: markdown-oxide LSP (if available via Neovim), then Grep/Glob/Read.

**Opportunistic drift detection:** When frontmatter is sampled during any operation, watch for obvious inconsistencies — competing property names (`url`/`site`/`urls`), mixed-case `fileClass` values, YAML corruption artifacts. Offer: "I noticed schema drift in `<folder>` — run detection before continuing?"

## Migration & Metadata Workflows

### Meeting Extraction from Logs

When asked to extract meeting information from daily notes or inline logs:

1. **Parse Selection** using script:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/extract_section_to_meeting.py \
     ${VAULT_PATH} "${CURRENT_NOTE}" "${SELECTED_TEXT}"
   ```
2. **Infer Metadata** - time from log syntax, company from folder path, attendees from inline fields
3. **Prompt for Missing Data** - title, scope, attendees, meeting type
4. **Create Meeting Note** using template, replace selection with wikilink

**See:** `references/migration-strategies.md` for extraction patterns

### Calendar Import and Person Matching

Import calendar events → match attendees to Person notes → infer company → create meeting note.

**See:** `references/migration-strategies.md` for calendar import patterns

### Vault Migration Patterns

Migrate existing notes to new schemas:

1. **Dry-Run First** - Show planned changes, get approval
2. **Batch Validation** - Test on 5-10 notes, verify Bases queries work
3. **Rollback Strategy** - Git commit before migration, reverse script available

Common migrations: add scope to meetings, consolidate Dataview to Bases.

**See:** `references/migration-strategies.md` for comprehensive patterns

### Property Suggestions

When asked "what properties should this note have?" or "suggest metadata":

1. **Select scope** (or use current note's folder/fileClass)
2. **Analyze peer notes** - scan notes with same fileClass or in same folder
3. **Identify gaps** - find common properties the target note is missing
4. **Present suggestions** with rationale ("87% of Meeting notes have 'scope'")
5. **Apply with confirmation** - user approves per property

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/suggest_properties.py \
  ${VAULT_PATH} "${NOTE_PATH}"
```

Returns JSON with suggestions and confidence scores.

### Schema Drift Detection

When asked to "detect schema drift" or "find inconsistent metadata":

1. **Select scope** and target fileClass (e.g., Meeting, Person, Project)
2. **Scan all notes** of that fileClass within scope
3. **Report inconsistencies**:
   - Missing required properties
   - Inconsistent property types (string vs array)
   - Naming convention mismatches (camelCase vs kebab-case)
4. **Suggest standardization** with specific fixes

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/detect_schema_drift.py \
  ${VAULT_PATH} --file-class Meeting --scope "${SCOPE_PATH}"
```

### Property Bulk Updates

When asked to batch update frontmatter:

1. **Collect target notes** within scope
2. **Validate changes on sample** (5-10 notes)
3. **Apply with progress tracking** and error logging
4. **Git commit before and after**

**Safety:** Always validate vault path. Preserve YAML formatting. Handle missing properties gracefully.

## Consolidation Workflows

Consolidation detects duplicates, merges notes, and redirects links. All operations require user confirmation and git checkpoint before execution.

**See:** `references/consolidation-protocol.md` for full merge semantics, conflict resolution, and rollback procedures.

### Find Similar Notes

Detect duplicates within a scope using tiered detection:

1. **Select scope** (required)
2. **Run detection**:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_similar_notes.py \
     ${VAULT_PATH} --scope "${SCOPE_PATH}"
   ```
3. **Present groups** — Tier 1 (identical titles) first, then Tier 2 (similar titles, matching tags)
4. **Per-group decision**: merge / create MOC / mark aliases / skip

### Merge Notes

Merge source note into target (surviving) note:

1. **Git checkpoint** before merge
2. **Dry-run first**:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/merge_notes.py \
     ${VAULT_PATH} --source "${SOURCE}" --target "${TARGET}" --dry-run
   ```
3. **Review** frontmatter changes (added, conflicts, merged lists) and content append
4. **Resolve conflicts** — present each to user for decision
5. **Execute merge** (remove `--dry-run`)

### Redirect Links

After merge, redirect all vault-wide references from deleted note to surviving note:

1. **Dry-run first**:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/redirect_links.py \
     ${VAULT_PATH} --old "${OLD_NAME}" --new "${NEW_NAME}" --dry-run
   ```
2. **Review** affected files and replacement counts
3. **Execute redirect** (remove `--dry-run`)
4. **Delete source note** only after redirect is confirmed

## Discovery Workflows

Discovery workflows surface connections, suggest links, and generate views that help users navigate large vaults.

### Related Note Finding

When asked "find related notes", "show connections", or "what links to this":

1. **Select scope** (or use current note's folder)
2. **Run discovery**:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_related.py \
     ${VAULT_PATH} "${NOTE_PATH}" --scope "${SCOPE_PATH}" --top 10
   ```
3. **Present results** with explanations of why each note is related:
   - Shared properties (fileClass, scope, project) — strongest signal
   - Shared wikilink targets — indicates topical overlap
   - Shared tags — broad topical connection
   - Folder proximity — structural relationship
4. **Offer to add wikilinks** to connect related notes (with user confirmation)

### Progressive Discovery Views

When asked "show discovery view" or "organize notes by depth":

1. **Select scope** (required)
2. **Determine hierarchy** from note metadata:
   - **Entry points**: Notes with `noteType: MOC` or `fileClass: MOC` (Maps of Content, overviews)
   - **Detailed notes**: Notes with specific `fileClass` values (Meeting, Project, Person, etc.)
   - **Raw captures**: Notes without `fileClass`/`noteType`, or with `fileClass: Capture`/`Log`
3. **Generate `.base` file** using obsidian-bases skill knowledge:
   ```json
   {
     "name": "Discovery View - [Scope]",
     "filters": [{"property": "file.folder", "op": "starts-with", "value": "[scope]"}],
     "groups": [{"property": "noteType", "direction": "asc"}],
     "columns": ["file", "noteType", "fileClass", "tags", "file.ctime"]
   }
   ```
4. **Save `.base` file** in the scoped directory (e.g., `_discovery-view.base`)
5. **Document the hierarchy model**: explain what each tier means for the user's vault

### Auto-Linking Suggestions

When asked "suggest links", "what should I link", or "improve connections":

1. **Select scope** (or use current note's folder/fileClass)
2. **Analyze metadata patterns** across scoped notes:
   - Find notes with similar tags but no wikilinks between them
   - Identify notes that share `scope` or `project` properties but aren't linked
   - Detect notes frequently co-referenced (both linked from the same third note)
3. **Suggest tag additions** based on peer analysis:
   - "Notes in this folder commonly use tags X, Y — consider adding to these notes"
4. **Suggest Bases formulas** for automatic views:
   - "Create a Bases view filtering by `fileClass=Meeting` + `scope=[[Project]]` to see all related meetings"
5. **Present suggestions** with rationale, apply tag/property changes with confirmation

### Canvas Map Generation

When asked "show me a map", "generate canvas", "visualize my notes", or "show knowledge map":

1. **Select scope** (required)
2. **Generate canvas**:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/generate_canvas.py \
     ${VAULT_PATH} --scope "${SCOPE_PATH}" --dry-run
   ```
3. **Review dry-run output** — confirm node count, edge count, clustering
4. **Execute** (remove `--dry-run`) to write `.canvas` file

**Layout:** Grid layout with file nodes for each note. Edges represent wikilinks between notes in scope. Color-coded by `fileClass` (Meeting=orange, Person=cyan, Project=green, Company=purple, MOC=yellow).

**Naming:** `_knowledge-map-YYYY-MM-DD.canvas` in the scoped directory. Leading underscore keeps it sorted above content notes. If a canvas with that name exists, a numeric suffix is appended.

**Limits:**
- **50-node cap** (default) — keeps canvases readable in Obsidian
- **Clustering:** When notes exceed the cap, folders with 4+ notes are collapsed into group nodes containing their sub-notes
- **Zero relationships:** Canvas is still generated (shows notes without edges) with a message suggesting wikilinks

**Options:**
- `--output <name>` — custom canvas filename
- `--max-nodes <n>` — adjust the clustering threshold

### Pattern Detection

- **Orphaned notes**: `obsidian orphans` — files with no incoming links
- **Note clusters**: `find_related.py --scope` — groups of related notes within a directory

**See:** `references/available-scripts.md` for full script inventory
