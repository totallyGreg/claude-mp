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

### Guard hook (Claude Code)

Permission rules turned out too weak to block destructive Obsidian CLI calls: a `*` in the middle
of a Bash rule matches one space-free token (verified 2026-10-16), and `obsidian vault=X delete`
puts an option before the subcommand. `hooks/obsidian_guard.py` parses commands with a quote-aware
tokenizer and denies `delete` and `create … overwrite`, asks for `move` and for `rm`/`mv` on vault
paths. It reuses `vault-write`'s config loader for the vault path.

### Other harnesses

Pi (and anything else) calls the same binary through a `~/bin/vault-write` shim that resolves the
latest installed plugin version. Config path override: `ARCHIVIST_LOCAL_MD`.

### Config location and vault discovery (#217, #218)

The config held both write policy and vault facts, lived in the versioned plugin cache (so an
update dropped it), and its zones were typed from `_vault-profile.md` prose that had lost the
folders' emoji (`500 Cycles` for `500 ♽ Cycles`), which silently refused every daily-note write.

- **Policy vs facts.** The config keeps policy only: `vault_path` and the zones. Facts about the
  vault go in `_vault-profile.md` (in the vault, shared across machines) or are read from Obsidian's
  own settings. `daily_notes_path` and `templates_path` were never read by anything; removed.
- **Location.** `$ARCHIVIST_LOCAL_MD`, then `${XDG_CONFIG_HOME:-~/.config}/archivist/local.md`,
  then a legacy `.local.md` in any installed plugin version (reported as `legacy`). Not
  `${CLAUDE_PLUGIN_DATA}`: that variable isn't exported to the Bash tool and is Claude Code-only,
  and Pi needs the same file. Outside the vault, so a vault write can't widen its own zones; the
  agent's Write tool asks before changing it.
- **`vault-write config`** prints the config in use, each zone that doesn't exist with a
  `did_you_mean` (closest real folder), and the daily-notes folder and filename format from
  Periodic Notes (if enabled) or the core Daily notes plugin. `/session-log` resolves today's note
  by name with that format (its old `fileClass:journal` search errors on the current CLI), since
  templates can move notes out of the configured folder.

## Out of scope (follow-ups)

- Multi-vault `vaults:` profiles in `.local.md` (CLI refuses them for now).
- Mermaid render check.
