# Obsidian CLI Patterns for Curator Workflows

The installed obsidian-cli skills provide safe CLI usage patterns for vault curation.

## Property Commands

```bash
obsidian properties path=<path> format=tsv           # list all properties
obsidian property:read name=<key> path=<path>        # read one property
obsidian property:set name=<key> value=<val> path=<path>  # set property
```

## Search Commands

```bash
obsidian search query="<text>" path=<folder> format=json matches  # scoped search with context
```

## Structure Commands

```bash
obsidian folders                                      # list all folders
obsidian files folder=<path> ext=md                   # list files in folder
obsidian orphans                                      # files with no incoming links
obsidian backlinks path=<path> counts                 # incoming links with counts
```

## Tag Commands

```bash
obsidian tags all counts sort=count                   # vault-wide tags by frequency
obsidian tag name=<tag>                               # files with specific tag
```

## File Creation

```bash
# WARNING: folder= parameter in create is broken — files land at vault root
# Always use create + move:
obsidian create "Note Title" silent                        # creates at vault root
obsidian move file="Note Title.md" to="Folder/SubFolder"  # moves to correct location
```

## Reading Notes

```bash
obsidian read file="Note Name"                          # read by wikilink name
obsidian read path="folder/note.md"                     # read by exact path
```

## Appending Content

```bash
obsidian append file="Note Name" content="New content"  # append to end
obsidian append path="folder/note.md" content="New content"
```

To insert content after a specific heading, use `obsidian append` with the note path, then use the Read tool to verify placement. For precise insertion at a specific location within a note, read the file with the Read tool, then use the Edit tool to insert content at the exact position.

**Pattern — Append CLI output to a note:**
```bash
OUTPUT=$(some-command --markdown)
obsidian append path="folder/note.md" content="$OUTPUT"
```

## File Updates

```bash
# WARNING: obsidian file is READ-ONLY — content and overwrite params are silently ignored
# WRONG — appears to succeed but file contents are unchanged:
obsidian file path="note.md" overwrite content="updated content" silent

# CORRECT — use create with overwrite to update file content:
obsidian create path="note.md" overwrite content="updated content" silent
```

## Safety Rules

- **`obsidian create overwrite` is destructive** — it replaces the entire file. If the content pipeline fails (e.g., a sed error produces empty output), the note is wiped. **Never pipe untransformed or shell-processed content into `obsidian create overwrite`.** For inserting content at a specific location, use the Read tool + Edit tool on the vault file directly.
- **`obsidian file` is read-only** — `content` and `overwrite` params are silently ignored; use `obsidian create ... overwrite` for content writes (with the above caveat)
- **`folder=` in `create` is unreliable** — always use `create` + `move` instead
- Always use `silent` flag with `create` (prevents opening files in UI)
- Always use `format=json` for programmatic output
- Use `tasks all todo` not `tasks todo` (latter defaults to active file)
- Use `tags all counts` not `tags counts` (latter defaults to active file)
- CLI requires Obsidian desktop app to be running

See installed `obsidian-cli` skills for the full gotcha list.

## Fallback

If CLI is unavailable (Obsidian not running), use Grep/Glob/Read for file operations.
