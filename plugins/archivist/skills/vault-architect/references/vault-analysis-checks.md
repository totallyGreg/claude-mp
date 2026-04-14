---
name: Vault Analysis Checks
description: Documents each check run by analyze_vault.py — what is detected, what output fields mean, and how to interpret results
load_when: Running /health command, interpreting analyze_vault.py output, explaining vault issues to user
---

# Vault Analysis Checks

**Load when:** Running the `/health` command or interpreting output from `analyze_vault.py`.

## Overview

`analyze_vault.py` runs structural checks on the vault and returns a JSON report (via `--json`). Five checks are available; all five run by default. Each check is independent and can be run individually with a flag.

**Scope:** Skips files with "Template" in the path and files starting with `_`. Does not use `python-frontmatter` — uses a simple `key: value` line parser, so complex YAML may not parse correctly.

---

## Checks

### 1. Untagged Notes (`--check-tags`)

**What it detects:** Notes with no tags — neither a `tags:` frontmatter property nor any inline `#tag` in the body.

**Output field:** `untagged` — list of vault-relative paths.

**Interpretation:** Untagged notes are undiscoverable by tag-based views and harder to classify. Prioritize folders with heavy active use.

**Remediation:** Use `suggest_properties.py` to suggest tags from content and peer notes.

---

### 2. Orphaned Notes (`--check-orphans`)

**What it detects:** Notes with **no outgoing wikilinks AND no incoming wikilinks** — neither referenced by nor referencing other notes.

**Definition of "orphan":** Both `links_out` (wikilinks the note contains) and `links_in` (wikilinks from other notes pointing here) are empty.

**Output field:** `orphans` — list of vault-relative paths.

**Interpretation:** Orphans are isolated from the knowledge graph. They won't appear in backlinks panes or graph views. Common causes: imported notes, stale drafts, capture-only notes never elaborated.

**Remediation:** Run `find_related.py` on orphans to find link candidates. Consider adding to a MOC or deleting if truly stale.

**Note on resolution:** Orphan detection matches by note `stem` (filename without extension). Two notes in different folders with the same stem are treated as the same link target — this is consistent with how Obsidian resolves unqualified wikilinks.

---

### 3. Frontmatter Consistency (`--check-frontmatter`)

**What it detects:** Properties present in >50% of all notes but missing from at least one note.

**Output fields:**
- `common_fields` — list of field names used in >50% of notes
- `missing_common_fields` — map of `{field: [paths of notes missing it]}`

**Interpretation:** A field in >50% of notes is treated as a vault-level standard. Missing notes represent schema drift. This is a broad vault-wide check — for collection-scoped drift, use `detect_schema_drift.py`.

**Remediation:** Use `suggest_properties.py` per note, or batch-apply via property update commands.

---

### 4. Temporal Links (`--check-temporal`)

**What it detects:** Daily notes missing `Week:` or `Month:` frontmatter links.

**Daily note identification:** A note is treated as daily if any of these are true:
- `tags` frontmatter contains "daily" (case-insensitive)
- Body contains `#daily`
- Filename matches `YYYY-MM-DD` pattern

**Output field:** `missing_temporal_links` — list of `{note, missing: ["Week", "Month"]}` objects.

**Interpretation:** Temporal links connect daily notes to week/month rollup notes, enabling Chronos timeline views and period-based Bases filtering. Missing links break temporal navigation.

**Remediation:** Use the Chronos workflow to generate rollup notes and backfill missing links.

---

### 5. Duplicate Titles (`--check-duplicates`)

**What it detects:** Notes with identical or near-identical titles after stripping non-alphanumeric characters and lowercasing.

**Output field:** `potential_duplicates` — map of `{normalized_title: [vault-relative paths]}`.

**Interpretation:** "Potential" because normalization may over-match (e.g., "Project A" and "Project A (archived)" normalize differently, but "Daily Standup" and "DailyStandup" match). Treat as candidates requiring review.

**Remediation:** Use `/duplicates` → `find_similar_notes.py` for semantic similarity confirmation, then the merge workflow to consolidate confirmed duplicates.

---

## Output Structure

```json
{
  "untagged": ["path/to/note.md"],
  "orphans": ["path/to/isolated.md"],
  "common_fields": ["fileClass", "tags", "created"],
  "missing_common_fields": {
    "fileClass": ["path/note1.md", "path/note2.md"]
  },
  "missing_temporal_links": [
    {"note": "2026-01-15.md", "missing": ["Week"]}
  ],
  "potential_duplicates": {
    "projectmeeting": ["Projects/Meeting.md", "Notes/Project Meeting.md"]
  }
}
```

## Limitations

- Orphan detection is name-based (stem), not path-based — consistent with Obsidian's wikilink resolution
- Frontmatter parser is line-based (`key: value`), not full YAML — complex values (nested objects, multiline strings, quoted strings) may not parse correctly
- Temporal link check only looks for `Week` and `Month` keys — other temporal fields (Quarter, Year) are not checked
- This is a vault-wide structural check; for collection-level health, use `check_collection_health.py`

## Related Commands

- `/health` — Runs this script as part of a full health snapshot
- `/duplicates` — Deeper duplicate analysis using semantic similarity
- `/drift` — Collection-scoped schema drift detection
