---
last_verified: 2026-10-18
sources:
  - type: github
    repo: "kepano/obsidian-skills"
    paths: ["skills/obsidian-cli/", "skills/obsidian-markdown/", "skills/obsidian-bases/", "skills/json-canvas/", "skills/defuddle/"]
    description: "All 5 obsidian-skills the archivist delegates to — track for new capabilities"
  - type: web
    url: "https://obsidian.md/help/cli"
    description: "Official Obsidian CLI reference"
  - type: github
    repo: "rokokol/obsidian-cli-skill"
    paths: ["SKILL.md"]
    description: "Community CLI skill with measured gotchas (forum.obsidian.md/t/119334)"
---

# CLI Gotchas for Vault Curator

Checked against `obsidian help` on Obsidian 1.14.4 (macOS). For the full command list run `obsidian help` or `obsidian help <command>`. The [obsidian-skills](https://github.com/kepano/obsidian-skills) `obsidian-cli` skill also covers it. This file lists vault-specific caveats and decision rules.

## CLI vs File Tools

**Use CLI** when you need Obsidian's index or app features:
search, backlinks, links, tags, tasks, properties, bases, templates, outline, orphans, unresolved links

**Use file tools** (Read/Grep/Glob on `${VAULT_PATH}`) for reading and grepping. Write note content with `vault-write`, not Write/Edit.

Rule of thumb: if Obsidian's index adds value, use CLI. If it's plain text, use file tools.

## Read the Output, Not the Exit Status

- **Errors exit 0.** Failures print `Error: …` on stdout and still exit 0 (`Error: File "x.md" not found.`, `Error: Command "x" not found.`). Treat any output starting with `Error:` as a failure.
- **A missing or mistyped target falls back to the open note.** `obsidian read pth="x.md"` silently drops `pth=` and reads whatever note is open in Obsidian. On a write, that edits the wrong note.
  - Always pass `path=` (exact vault path) for writes.
  - The archivist guard hook denies `create`, `append`, `prepend`, `property:set`, `property:remove` and task updates that lack `path=`, or whose path is outside the write zones.
- **`file=` resolves like a wikilink; `path=` is exact.** Prefer `path=` whenever you know it.

## Writes

| Need | Use |
|---|---|
| Note content (new note, whole note, one section) | `vault-write apply` (zones, compare-and-swap, lint, snapshot) |
| One frontmatter value | `obsidian property:set path="…" name=… value=…` (zone-checked by the guard) |
| A list property | add `type=list` (otherwise the value is stored as text); commas can't be escaped inside a list value |
| Append a line to today's daily note | `obsidian daily:append content="…"` |
| Move or rename a note | `obsidian move path="…" to="…"` / `obsidian rename path="…" name=…`. The guard asks first |

- **`create … overwrite` is denied** by the guard. Use `vault-write apply` (whole note or `--section`). Outside the archivist, `content=` turns `\n` into newlines and empty shell output wipes the note.
- **`create` opens nothing by default.** `open`/`newtab` are opt-in. The old `silent` flag is gone, and an unknown flag is silently ignored.
- **`create` has no `folder=`.** Pass the full `path=` instead. Parent folders may need to exist first.
- **`create` with `template=` may ignore `path=`.** The file lands in the template's configured folder. Verify with `obsidian files folder=…` afterwards.
- **`template:insert` writes into the open note.** The guard asks first.
- **`eval` and `dev:cdp` are denied.** They run arbitrary code and bypass every write rule.
- **A note open with unsaved edits** can conflict with an external write. Write notes the user isn't editing, or ask them to save first.

## Listings

- **Vault-wide is the default** for `tasks`, `tags` and `properties`. Add `active` to scope to the open note, or `path=` / `file=` for one note. (The old `tasks all` / `tags all` forms are gone.)
- **Bound big listings.**
  - Use `total` for a count first, then `limit=` on `search` / `search:context`.
  - `search:context` on a broad query can return megabytes.
- **`search:context format=json`** returns `[{"file": …, "matches": [{"line": N, "text": …}]}]`. Use it for programmatic search.
- **`format=json`** where offered (`backlinks`, `tags`, `tasks`, `unresolved`, `bookmarks`, `base:query`). `properties` takes `format=json|yaml|tsv`.

## Shell Usage

- **Loops: redirect stdin.** The CLI reads stdin, so inside `while read …; do obsidian …; done` it swallows the rest of the input and the loop stops after one pass. Use `obsidian … </dev/null`.
- **Wrappers are fine.** `timeout 10 obsidian …` is still checked by the guard hook.
- **First call to an idle app** can report `Command … not found` while plugins load. Make one cheap call (`obsidian vault`) before a batch.

## Base Files

**Always check `900 📐Templates/970 Bases/` before creating a new `.base` file.** If a base for that fileClass or topic already exists, add views to it. Do not create a duplicate.

All canonical base files live in `970 Bases/`. A base co-located with notes (e.g. inside a collection folder) is a sign something went wrong.

**Base filter scoping:** Obsidian Bases defaults to the embedding note's folder when no explicit folder is set. To get vault-wide results wherever the base is embedded, always combine an explicit folder path and a `fileClass` filter with `or`:

```yaml
filters:
  or:
    - file.folder == "700 Notes/Ideas💡"
    - fileClass == "Idea"
```

## File Relocation

**Use `obsidian move` / `obsidian rename` to relocate files**, never recreate + delete, never shell `mv`. They update wikilinks vault-wide. Recreate + delete leaves references stale, and shell `mv` bypasses Obsidian's index. Both need the user's approval (the guard asks).

```bash
obsidian move path="Inbox/Note Title.md" to="New/Folder"
```

## Error Handling

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| `The CLI is unable to find Obsidian` | Obsidian app not running | Ask the user to open it, or fall back to file tools for reads |
| Output starts with `Error:` (exit 0) | Bad path, unknown command, missing plugin | Treat as failure; check the path with `obsidian files` |
| `Command "x" not found` | Typo, CLI too old, or plugin not loaded yet | `obsidian help`; retry once after a warm-up call |
| Result is about the wrong note | Missing/mistyped `path=` fell back to the open note | Re-run with an exact `path=` |
| Empty results from search/tags | Index not ready | Wait, retry, or use Grep as fallback |

## Graph Traversal Commands

Use these for authoring, discovery, and health workflows. They need Obsidian's index (the app must be running).

| Command | Returns |
|---------|---------|
| `obsidian backlinks path="<path>"` | All notes linking TO this file |
| `obsidian links path="<path>"` | All outgoing links FROM this file |
| `obsidian unresolved verbose` | Broken wikilinks vault-wide, with source files |
| `obsidian orphans` | Files with no incoming links: MOC candidates or deletable |
| `obsidian deadends` | Files with no outgoing links: cross-referencing candidates |

**Caveats before treating a list as a repair queue:**
- Sample a few entries first.
- Links inside fenced code blocks don't count.
- Unlinked mentions never appear.
- Some alias links can show as unresolved, so cross-check against `obsidian aliases verbose`.

**When to use:**
- **Before authoring** a note: `backlinks` to understand what already connects to a target.
- **After a move or rename**: `unresolved verbose` to catch broken references.
- **Health check**: `orphans` for MOC gap analysis; `deadends` for under-connected notes.
- **Discovery**: `links` to map a note's connections before consolidating or moving it.

See `references/linking-discipline.md` for the full linking rationale and decision table.

## Fallback

The CLI needs the Obsidian desktop app running. If it's unavailable, read with Grep/Glob/Read on `${VAULT_PATH}` and write with `vault-write` (it doesn't need the app).
