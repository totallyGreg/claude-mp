# Available Scripts

All scripts use PEP 723 inline metadata for `uv run` compatibility. Run via:
`uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/<script> ${VAULT_PATH}`

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

## generate_canvas.py — Layout & Naming

**Layout:** Grid layout with file nodes for each note. Edges represent wikilinks between notes in scope. Color-coded by `fileClass` (Meeting=orange, Person=cyan, Project=green, Company=purple, MOC=yellow).

**Naming:** `_knowledge-map-YYYY-MM-DD.canvas` in the scoped directory. Numeric suffix appended if name exists. 50-node cap by default; folders with 4+ notes collapse into group nodes when exceeded.

**Options:** `--output <path>` to override destination; `--max-nodes <N>` to change node cap.
