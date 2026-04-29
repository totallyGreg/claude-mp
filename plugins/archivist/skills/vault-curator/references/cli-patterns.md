---
last_verified: 2026-04-28
sources:
  - type: github
    repo: "kepano/obsidian-skills"
    paths: ["skills/obsidian-cli/", "skills/obsidian-markdown/", "skills/obsidian-bases/", "skills/json-canvas/", "skills/defuddle/"]
    description: "All 5 obsidian-skills the archivist delegates to — track for new capabilities"
---

# CLI Gotchas for Vault Curator

For full command reference, use the `obsidian-cli` skill from the [obsidian-skills](https://github.com/kepano/obsidian-skills) marketplace. These are vault-specific bugs, caveats, and decision rules.

## CLI vs File Tools

**Use CLI** when you need Obsidian's index or app features:
search, backlinks, links, tags, tasks, properties, bases, templates, outline, orphans, unresolved links

**Use file tools** (Read/Write/Edit/Grep/Glob on `${VAULT_PATH}`) for:
simple file read/write, bulk text replacement, grep across files — no app dependency

Rule of thumb: if Obsidian's index adds value, use CLI. If it's plain text manipulation, use file tools.

## Known Bugs

- **`folder=` in `create` is broken** — files land at vault root regardless. Always use `create` + `move`:
  ```bash
  obsidian create name="Note Title" silent
  obsidian move file="Note Title.md" to="Folder/SubFolder"
  ```

- **`obsidian file` is read-only** — `content` and `overwrite` params are silently ignored with no error. To update file content, use `create` with `overwrite`:
  ```bash
  # WRONG — silently does nothing:
  obsidian file path="note.md" overwrite content="updated content" silent

  # CORRECT:
  obsidian create path="note.md" overwrite content="updated content" silent
  ```

- **`tasks todo` defaults to active file** — use `tasks all todo` for vault-wide task queries
- **`tags counts` defaults to active file** — use `tags all counts` for vault-wide tag counts

## Gotchas

- **`create` doesn't auto-create directories** — use `mkdir -p` via Bash first if the parent folder doesn't exist
- **`create` with `template=` may ignore `path=`** — the file lands in the template's configured folder. Always verify the actual path with `obsidian search` or `obsidian files` after template-based creation
- **`format=json matches`** returns `[{"file":"path","matches":[{"line":N,"text":"..."}]}]` — prefer this over plain `format=json` for programmatic search

## Base Files

**Always check `900 📐Templates/970 Bases/` before creating a new `.base` file.** If a base for that fileClass or topic already exists, add views to it — do not create a duplicate.

All canonical base files live in `970 Bases/`. A base co-located with notes (e.g. inside a collection folder) is a sign something went wrong.

**Base filter scoping:** Obsidian Bases defaults to the embedding note's folder when no explicit folder is set. Always use `or` with both an explicit folder path and a `fileClass` filter to ensure vault-wide results when embedded anywhere:

```yaml
filters:
  or:
    - file.folder == "700 Notes/Ideas💡"
    - fileClass == "Idea"
```

## File Relocation

**Always use `obsidian move` to relocate files** — never recreate + delete, never shell `mv`.

`obsidian move` updates all wikilink references throughout the vault atomically. Recreate + delete leaves references stale. Shell `mv` bypasses Obsidian's index entirely.

```bash
obsidian move file="Note Title.md" to="New/Folder"
```

## Safety Rules

- **`create overwrite` is destructive** — replaces entire file. Never pipe shell-processed content into it (empty output = wiped note). For partial updates, use Read + Edit tools on the vault file directly.
- **Always use `silent`** with `create` — prevents files opening in Obsidian UI (focus steal)
- **Always use `format=json`** for programmatic output parsing

## Error Handling

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| `obsidian version` fails | CLI not installed or not on PATH | Fall back to file tools |
| Command hangs or times out | Obsidian app not running | Start Obsidian or use file tools |
| "Unknown command" | CLI version too old | Run `obsidian help` to check available commands |
| Empty results from search/tags | Vault index not ready | Wait a moment, retry, or use Grep as fallback |

## Graph Traversal Commands

Use these for authoring, discovery, and health workflows. They require Obsidian's index (CLI must be running).

| Command | Returns |
|---------|---------|
| `obsidian backlinks file="<name>"` | All notes linking TO this file |
| `obsidian links file="<name>"` | All outgoing links FROM this file |
| `obsidian unresolved` | Broken wikilinks vault-wide (add `sources=true` for source files) |
| `obsidian orphans` | Files with no incoming links — MOC candidates or deletable |
| `obsidian deadends` | Files with no outgoing links — cross-referencing candidates |

**When to use:**
- **Before authoring** a note: `backlinks` to understand what already connects to a target
- **After rename / `obsidian move`**: `unresolved sources=true` to catch any broken references
- **Health check**: `orphans` for MOC gap analysis; `deadends` for under-connected notes
- **Discovery**: `links` to map a note's connection footprint before consolidating or moving it

See `references/linking-discipline.md` for the full linking rationale and decision table.

## Fallback

CLI requires Obsidian desktop app to be running. If unavailable, fall back to Grep/Glob/Read tools on vault files at `${VAULT_PATH}`.
