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

## Fallback

CLI requires Obsidian desktop app to be running. If unavailable, fall back to Grep/Glob/Read tools on vault files at `${VAULT_PATH}`.
