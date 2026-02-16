---
name: vault-curator
description: >
  This skill should be used when users ask to "migrate vault notes", "extract meeting from log",
  "import calendar event", "detect schema drift", "find orphaned notes", "consolidate notes",
  "find duplicates", "suggest properties", "what metadata am I missing", "find related notes",
  "show knowledge map", or "generate canvas". Curates and evolves existing vault content through
  pattern detection, migration workflows, metadata intelligence, and programmatic manipulation.
metadata:
  version: "1.2.0"
  plugin: "pkm-plugin"
  stage: "3"
compatibility: Requires python3.11+ and uv for script execution. Obsidian CLI 1.12+ for intelligence workflows.
---

# Vault Curator

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

## Core Principles

1. **Evolution Over Revolution** - Migrate gradually. Test on small batches first.
2. **Validation Before Execution** - Always dry-run first. Show what would change.
3. **Rollback Readiness** - Git commit before operations. Enable reverting.
4. **Pattern Recognition** - Discover existing patterns before suggesting changes.
5. **Incremental Improvement** - Small, testable changes compound better than large restructuring.

## Obsidian CLI Integration

The installed obsidian-cli skills provide safe CLI usage patterns. Key commands for curator workflows:

```bash
# Properties (metadata workflows)
obsidian properties path=<path> format=tsv           # list all properties
obsidian property:read name=<key> path=<path>        # read one property
obsidian property:set name=<key> value=<val> path=<path>  # set property

# Search (scoped operations)
obsidian search query="<text>" path=<folder> format=json matches  # scoped search with context

# Structure (scope selection)
obsidian folders                                      # list all folders
obsidian files folder=<path> ext=md                   # list files in folder
obsidian orphans                                      # files with no incoming links
obsidian backlinks path=<path> counts                 # incoming links with counts

# Tags
obsidian tags all counts sort=count                   # vault-wide tags by frequency
obsidian tag name=<tag>                               # files with specific tag
```

**Safety:** Always use `silent` flag with `create`. Always use `format=json` for programmatic output. See installed `obsidian-cli` skills for full gotcha list.

**Fallback:** If CLI is unavailable (Obsidian not running), use Grep/Glob/Read for file operations.

## Migration Workflows

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

## Metadata Workflows

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

## Pattern Detection

### Find Orphaned Notes

```bash
obsidian orphans                    # CLI: files with no incoming links
# OR fallback:
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_orphans.py ${VAULT_PATH}
```

### Detect Note Clusters

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_note_clusters.py ${VAULT_PATH}
```

Uses link analysis to identify groups of highly interconnected notes.

## Python Script Patterns

All scripts follow PEP 723 inline metadata:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
#   "python-frontmatter>=1.0.0",
# ]
# ///
```

**Requirements:**
1. **PEP 723 Header** - inline dependencies for `uv run`
2. **Path Validation** - security check (no system directories)
3. **JSON Output** - structured output to stdout
4. **Error Handling** - graceful failures with error JSON
5. **`--dry-run` flag** - for destructive operations

Run via: `uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/<script> ${VAULT_PATH}`

## Available Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `extract_section_to_meeting.py` | Extract meeting from daily note log | Stable |
| `suggest_properties.py` | Suggest missing properties for a note | Stable |
| `detect_schema_drift.py` | Find metadata inconsistencies across fileClass | Stable |
| `find_orphans.py` | Find notes with no links | Planned |
| `find_note_clusters.py` | Identify interconnected note groups | Planned |
| `merge_notes.py` | Merge duplicate notes | Planned |
| `redirect_links.py` | Vault-wide wikilink replacement | Planned |
| `generate_canvas.py` | Generate canvas maps | Planned |
