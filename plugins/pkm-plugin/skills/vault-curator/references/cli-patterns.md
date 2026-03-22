# CLI Gotchas for Vault Curator

For full command reference, use the `obsidian-cli` skill. These are vault-specific bugs and caveats.

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

## Safety Rules

- **`create overwrite` is destructive** — replaces entire file. Never pipe shell-processed content into it (empty output = wiped note). For partial updates, use Read + Edit tools on the vault file directly.
- **Always use `silent`** with `create` — prevents files opening in Obsidian UI (focus steal)
- **Always use `format=json`** for programmatic output parsing

## Fallback

CLI requires Obsidian desktop app to be running. If unavailable, fall back to Grep/Glob/Read tools on vault files at `/Users/totally/Notes/`.
