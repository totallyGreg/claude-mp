# archivist: `vault-write` — write safety in code, for every harness

Issue: #215

## Problem

The archivist's write protections (zones, "never `create overwrite`", stop on first denial) live in
prompt text. They only apply when the archivist agent runs in Claude Code, and the only permission
rule for vault access, `Bash(obsidian:*)`, auto-allows `obsidian delete` and `obsidian create …
overwrite`. Meanwhile routine operations prompt, drift checks and post-write verification are done
by hand, and nothing catches Dataview-breaking inline code.

## Decision

One small CLI, `vault-write`, shipped in the plugin's `bin/` (Claude Code puts plugin `bin/` on the
Bash tool's `PATH`, so permission rules can match a bare, version-independent command). The CLI
enforces policy in code; agents decide *what* to write, the CLI decides *whether* it may be written.

| Subcommand | Does | Permission rule (user settings) |
|---|---|---|
| `stat <note>` | hash (raw + stable), line count, exists | allow |
| `check <file>` | lint only | allow |
| `apply <note> --from <file\|-> [--base H] [--section HEADING]` | zone check → compare-and-swap → lint → git snapshot → atomic write → verify → JSON | allow |
| `force …` | as `apply`, but may skip the base and zone checks | ask |

Not provided: delete, move, bulk edits. Those stay human-approved through the Obsidian app or an
explicitly approved command.

### Guarantees

1. **Zones** — the target must sit under a zone from `.local.md` (`architect_write_zones`,
   `curator_write_zones`, `designated_output_zones`), compared per path component after Unicode NFC
   normalization. Zones that don't exist on disk are reported as warnings.
2. **Compare-and-swap** — writing over an existing note requires `--base`, the hash from `stat`. It
   matches either the raw hash or the *stable* hash (trailing whitespace stripped, frontmatter keys
   in `ignore_drift_keys` dropped; default `date modified`), so a linter save doesn't count as drift
   but a real edit does.
3. **Lint** (errors block): unclosed code fences; inline code starting with `=` or `$=` (Dataview
   executes it). Warnings: wikilinks that resolve to no file.
4. **Snapshot** — before writing, if the note has uncommitted changes, commit exactly that path in
   the vault's git repo, so every write is one `git checkout <sha> -- <path>` away from undone.
   No git repo → `apply` refuses; `force` warns and continues.
5. **Atomic write + verify** — temp file in the same directory, `os.replace`, read back, compare.
6. **Section patches** — `--section` replaces one heading's section (to the next heading of the same
   or higher level, ignoring `#` lines inside code fences); the base hash still covers the whole note.

### Writes go to the file, not through the Obsidian CLI

`obsidian create … content=` interprets `\n` escapes in its argument and needs the app running, so
it can't write arbitrary content byte-exactly. `vault-write` writes the file directly; Obsidian
picks up external changes. This departs from the owner's "use the Obsidian CLI" rule for agents, on
purpose: the CLI is the controlled channel now.

### Other harnesses

Pi (and anything else) calls the same binary through a `~/bin/vault-write` shim that resolves the
latest installed plugin version. Config path override: `ARCHIVIST_LOCAL_MD`.

## Out of scope (follow-ups)

- `.local.md` lives in the versioned plugin cache and is lost on update (should move to
  `${CLAUDE_PLUGIN_DATA}`).
- Multi-vault `vaults:` profiles in `.local.md` (CLI refuses them for now).
- Mermaid render check.
