# Linking Discipline in Obsidian Vaults

Every reference to another vault entity in authored content should be a wikilink. This powers backlinks, graph discovery, rename-safe updates, and agent navigation across sessions.

## The Rule

**Default to `[[Target]]` for any vault entity reference.** Use backticks only for code identifiers, shell commands, YAML property keys, and CLI argument paths.

## Why It Matters

- **Backlinks** — `[[Target]]` creates a reverse edge visible in Obsidian's Backlinks pane and queryable via `obsidian backlinks file="Target"`. Backticks create nothing.
- **Graph discoverability** — the node graph shows connected clusters only from wikilinks. Backtick references are invisible to the graph.
- **Rename-safe** — `obsidian move` updates wikilinks vault-wide atomically. Backticked filenames become dead references silently.
- **Single source of truth** — linking to a canonical note means a reader can navigate there. The `.base` file's default view is the authoritative schema definition for a type; the fileClass note mirrors it.
- **Agent navigation** — future archivist sessions can traverse the graph via `obsidian backlinks`/`links` to find context, but only for edges that exist as wikilinks.

## Decision Table

| Reference kind | Correct | Incorrect |
|---|---|---|
| fileClass note | `[[Meeting]]` | `` `Meeting` `` or `` `Meeting.md` `` |
| Base file | `[[Meetings.base]]` | `` `Meetings.base` `` |
| Template | `[[🛠 New Meeting]]` | `` `New Meeting` `` |
| Folder note | `[[700 Notes/Workflows]]` | `` `700 Notes/Workflows/` `` |
| Any other vault note | `[[Canvas Types]]` | `` `Canvas Types.md` `` |
| CLI command in prose | `` `obsidian backlinks file="X"` `` | `[[X]]` inside code context |
| YAML property key | `` `fileClass` `` | `[[fileClass]]` |
| YAML property value (literal) | `` `workflow` `` | `[[workflow]]` |
| Code block / shell example | keep as code | — |

**The `` `fileClass:` `` / `[[Value]]` pattern:** In headings and prose that identify a note type, use backticks for the property key and a wikilink for the value that names a fileClass. Example: `` `fileClass:` [[Meeting]] ``.

## Schema Authority in a Post-Bases Vault

The `.base` file's **default view** is the canonical definition of a note type — its properties and their types live there. The metadata-menu fileClass note (typically in `900 📐Templates/920 File Classes/`) is a backing layer that mirrors the Base.

**Drift resolution:** When a Base and its fileClass note disagree, the Base wins. Propose updates to the fileClass note to match.

**Linking convention:** When prose references a type, link the Base first, fileClass second:
- `[[Meetings.base]]` — schema definition
- `[[Meeting]]` — metadata-menu backing (editor pickers, field ordering)

**Workflow:** Change the Base's default view → update the fileClass YAML to match → never the reverse.

## Graph CLI Commands

Use these to surface connections during authoring and discovery sessions:

```bash
# Who links to this note?
obsidian backlinks file="Types of Notes"

# What does this note link to?
obsidian links file="Types of Notes"

# Broken wikilinks vault-wide (with source files)
obsidian unresolved sources=true

# Notes with no incoming links (orphans — MOC candidates or deletable)
obsidian orphans

# Notes with no outgoing links (dead-ends — cross-referencing candidates)
obsidian deadends
```

**When to use each:**

| Command | When |
|---|---|
| `backlinks` | Before authoring: understand what already references a target. After rename: check coverage. |
| `links` | When reviewing a note: map its connection footprint. |
| `unresolved` | Health checks, post-rename cleanup, after bulk file moves. |
| `orphans` | Health checks, MOC gap analysis, pre-archival review. |
| `deadends` | Cross-referencing candidates: notes that exist but don't participate in the graph. |

## Anti-Patterns

**Before-state (do not produce):**

```markdown
## Workflow Notes (`fileClass: workflow`)
...
### Views: `Workflows.base`
```

**After-state (target pattern):**

```markdown
## Workflow Notes (`fileClass:` [[Workflow]])
...
### Views: [[Workflows.base]]
```

**Canonical example:** `700 Notes/Notes/Types of Notes.md` in the user's vault demonstrates the full target pattern — registry table columns (fileClass, Folder, Template, Base), section headings, and inline Views references all use `[[...]]`.

## Common Mistakes

- Using backticks around `.base` filenames in the Views line of a type section
- Using backticks for fileClass values in section headings instead of wikilinks
- Referencing templates by descriptive name in prose without linking to the template note
- Referencing folder paths with trailing slashes instead of linking to the folder note
