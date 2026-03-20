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
