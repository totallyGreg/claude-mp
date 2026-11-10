# Available Scripts

All scripts use PEP 723 inline metadata for `uv run` compatibility. Run via:
`uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/<script> ${VAULT_PATH}`

**Writes go through `vault-write`.**
- `merge_notes.py`, `redirect_links.py` and `generate_canvas.py` write through `bin/vault-write` (via `_vault_write.py`). They get the same zone check, drift check against what they read, lint or JSON validation, and git snapshot as the CLI.
- They refuse a vault other than the configured one.
- `--dry-run` previews the change. `--no-write` returns the content for the agent to apply with `vault-write apply`.
- Every other script only reads.

| Script | Purpose |
|--------|---------|
| `extract_section_to_meeting.py` | Extract meeting from daily note log |
| `suggest_properties.py` | Suggest missing properties for a note |
| `detect_schema_drift.py` | Find metadata inconsistencies across fileClass |
| `find_related.py` | Find notes related by tags, properties, links, proximity |
| `find_similar_notes.py` | Detect duplicate/similar notes within scope |
| `merge_notes.py` | Merge two notes (frontmatter union + content concat) |
| `redirect_links.py` | Vault-wide wikilink replacement after merge |
| `generate_canvas.py` | Generate JSON Canvas maps of note relationships |
| `check_collection_health.py` | Audit Collection Folder Pattern health (folder note, Bases file, schema drift) |
| `check_stale_names.py` | Count live mentions of renamed things (`formerly:` registry); baseline only falls |
| `noise_counts.py` | Orphans, broken Week links, stale names, unmapped link fields; baselines in the profile's `## Noise`, only fall |

## find_related.py — Relatedness Signals

Results are ranked by signal strength:
- **Shared properties** (`fileClass`, `scope`, `project`) — strongest signal
- **Shared wikilink targets** — indicates topical overlap
- **Shared tags** — broad topical connection
- **Folder proximity** — structural relationship

## check_collection_health.py — Output Fields

| Field | Meaning |
|-------|---------|
| `has_folder_note` | `<Folder>/<Folder>.md` exists |
| `folder_note_embeds_bases` | Folder note contains `![[...base#...]]` |
| `has_bases_file` | `900 📐Templates/970 Bases/<Name>.base` exists |
| `dominant_fileclass` | Most common `fileClass` among members |
| `schema_drift_issues` | Count of drift issues (from drift analysis) |
| `health` | `healthy` \| `partial` \| `missing_infrastructure` |

## check_stale_names.py — Rename Ratchet

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/check_stale_names.py \
  ${VAULT_PATH} [--update-baseline] [--repo <path>] [--exempt <prefix>] [--all]
```

- **Registry:** every `formerly:` value in vault frontmatter, mapped to the note that declares it. Put the same names in `aliases` so old links and searches resolve. Never list a name that is still valid for something else; every legitimate use would count.
- **History, not counted:** files named with a leading `YYYY-MM-DD`, folders whose name contains "archive", version-history table rows (`| 1.2.0 | …`), notes with `historical: true` (records kept as written), the canonical note's own frontmatter, and `--exempt` prefixes.
- **Ratchet:** for the vault, the baseline is the `stale_names` row of the profile's `## Noise` section (see noise_counts.py). The older `--update-baseline` file, `$XDG_STATE_HOME/archivist/stale-names.json`, still works but `/health` no longer uses it.
- **Repo mode:** `--registry <repo>/.stale-names.json` needs no vault (a pre-commit hook, CI). The file holds `names` (old → new), `exempt` prefixes and `baseline`; it scans git-tracked files under its own directory and `--update-baseline` lowers `baseline` in place. The vault scan stays a full walk, since new notes are often uncommitted.
- **Status:** `no-registry`, `first-run`, `ok`, `improved` (exit 0); `regressed` (exit 1).
- **Fixing hits:** propose one replacement per mention; confirm before editing user-written notes; work a few files per session, largest name first.

## noise_counts.py — Noise Ratchet

```bash
obsidian vault="<vault_name>" orphans | uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/noise_counts.py \
  ${VAULT_PATH} --orphans - [--exclude <folder>]... [--days <folder>] [--link-exempt <field>]...
```

- **Counts:** `orphans` (.md only, minus excluded folders and daily notes), `broken_week_links` (daily notes `YYYY-MM-DD.md` whose `Week` link names no note), `stale_names` (same rules as check_stale_names.py), `unmapped_link_fields` ((note, field) pairs where a frontmatter field holds a `[[link]]` but K-Plex gives the field no role; names match as K-Plex matches them; skipped when `.obsidian/plugins/k-plex/data.json` is absent). The output's `unmapped_link_fields_top` lists the ten commonest such fields, the place to start. `broken_frontmatter`: notes outside the excluded folders whose frontmatter Obsidian can't read (YAML that doesn't parse to a mapping, or a vault-write frontmatter rule fails), so every view and K-Plex sees none of their properties; `broken_frontmatter_first` lists the first ten paths; `--list` adds `broken_frontmatter_all`, every path, for a repair batch.
- **The profile is the record:** `## Noise` in `_vault-profile.md` holds `Orphans exclude:`, `Daily notes:` and `Link fields exempt:` (backticked folders or fields; exempt fields are links K-Plex is not meant to draw, such as a Bases-only link) and a table with each count's baseline, last value and definition. `--exclude`, `--days` and `--link-exempt` replace those settings, for the first run.
- **Ratchet:** a lower count becomes the baseline; a higher one is `regressed` (exit 1) and the baseline stays.
- **Read-only:** it prints `section`; write it with `vault-write apply _vault-profile.md --base <hash> --section "## Noise"`.

## generate_canvas.py — Layout & Naming

**Layout:** Grid layout with file nodes for each note. Edges represent wikilinks between notes in scope. Color-coded by `fileClass` (Meeting=orange, Person=cyan, Project=green, Company=purple, MOC=yellow).

**Naming:** `_knowledge-map-YYYY-MM-DD.canvas` in the scoped directory. Numeric suffix appended if name exists. 50-node cap by default; folders with 4+ notes collapse into group nodes when exceeded.

**Options:** `--output <path>` to override destination; `--max-nodes <N>` to change node cap.
