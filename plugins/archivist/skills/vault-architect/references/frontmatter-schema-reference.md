---
name: Frontmatter Schema Reference
description: Documents fields and rules checked by validate_frontmatter.py — field types, severity levels, common violations, and remediation
load_when: Running frontmatter validation, interpreting validate_frontmatter.py output, designing new note schemas
---

# Frontmatter Schema Reference

**Load when:** Running the `/health` command, interpreting `validate_frontmatter.py` output, or designing frontmatter schemas for new note types.

## Overview

`validate_frontmatter.py` validates frontmatter in vault notes. Two operating modes:

- **Schema generation** (`--generate-schema`): Infers field types and usage percentages from existing notes; outputs a schema JSON file
- **Validation** (`--schema FILE`): Validates all notes against a provided schema JSON

Skips files with "Template" in the path and files starting with `_`. Only processes notes that have YAML frontmatter (delimited by `---`).

---

## Checks Performed

### Missing Required Fields

**Triggered by:** `--required <field1,field2,...>`

**What it checks:** Whether each note contains all explicitly required fields.

**Output field:** `missing_required` — list of `{note, missing: [fields]}` objects.

**Severity:** High — these fields are declared mandatory by the operator.

**Remediation:** Use `suggest_properties.py` to populate missing fields from peer analysis, or apply manually per note.

---

### Type Mismatches

**Triggered by:** `--schema FILE` when the schema declares field types.

**What it checks:** Whether each field's Python runtime type matches the schema-declared type.

**Type names used:** Python `type.__name__` values — `str`, `int`, `float`, `bool`, `list`, `NoneType`.

**Output field:** `type_mismatch` — list of `{note, field, expected, actual, value}` objects.

**Severity:** Medium — type mismatches break Bases queries and Metadata Menu plugin behavior.

**Common cause:** Dates stored as integers (`20260101`) instead of ISO strings (`"2026-01-01"`).

**Remediation:** Correct the field value in frontmatter. Obsidian Linter can enforce date string formats.

---

### Empty Values

**Always checked.**

**What it checks:** Fields present in frontmatter with value `''` (empty string) or `null`/`None`.

**Output field:** `empty_values` — list of `{note, field}` objects, summarized by field with counts.

**Severity:** Low — empty fields add noise to Bases views and may indicate incomplete captures.

**Remediation:** Populate the field or remove it from frontmatter if not applicable to this note type.

---

### Inconsistent Date Formats

**Always checked.**

**What it checks:** Fields with date-semantic names that don't start with `YYYY-MM-DD`.

**Fields checked:** `date`, `date created`, `date modified`, `created`, `modified`.

**Output field:** `inconsistent_dates` — list of `{note, field, value}` objects.

**Severity:** Medium — non-ISO dates break Bases date sorting and Chronos timeline integration.

**Remediation:** Standardize to `YYYY-MM-DD`. Obsidian Linter can automate date format normalization vault-wide.

---

### Duplicate Fields (Case Variations)

**Always checked.**

**What it checks:** Notes where the same logical field appears under multiple case variants (e.g., both `fileClass` and `fileclass` in the same note).

**Output field:** `duplicate_fields` — list of `{note, fields: [variants]}` objects.

**Severity:** High — YAML parsers typically keep only one variant; the other is silently discarded. Plugin behavior (Metadata Menu, Bases) depends on exact field name casing.

**Remediation:** Remove the non-canonical variant. Use Obsidian Linter to enforce consistent casing.

---

## Schema Generation

`--generate-schema` produces a schema JSON inferred from all notes:

```json
{
  "fields": {
    "fileClass": {
      "type": "str",
      "usage_count": 142,
      "percentage": 87.1,
      "examples": ["meeting", "project", "person"]
    }
  }
}
```

Use this to bootstrap a schema file. Review it, trim low-usage fields, then pass it back via `--schema` for ongoing validation.

---

## Canonical Field Names

These field names are used consistently across this vault:

| Field | Type | Description |
|-------|------|-------------|
| `fileClass` | string | Note type (links to Metadata Menu fileClass definition) |
| `tags` | list | Obsidian tags |
| `created` | string | ISO 8601 creation date: `YYYY-MM-DD` |
| `aliases` | list | Alternative names for wikilink resolution |
| `title` | string | Display title when different from filename |

**`fileClass` is the authoritative type field.** Variants `fileclass` and `FileClass` are non-canonical — flag them and normalize.

---

## Common Violations and Remediation

| Violation | Cause | Fix |
|-----------|-------|-----|
| `fileclass` instead of `fileClass` | Manual edit or template typo | Rename key in frontmatter |
| `created: 20260414` (integer) | Bare number without quotes | Change to `created: "2026-04-14"` |
| `tags: meeting` (string instead of list) | Obsidian auto-conversion | Change to `tags: [meeting]` |
| `aliases: []` (empty list) | Template placeholder not populated | Remove field or populate it |
| `date: null` | Templater variable not resolved | Check Templater configuration |
| Both `fileClass` and `fileclass` present | Copy-paste from different templates | Remove the non-canonical variant |

---

## Related Workflows

- `/health` — Runs `validate_frontmatter.py` as part of the full health snapshot
- `/drift` — Collection-scoped drift detection (complement to vault-wide validation)
- `suggest_properties.py` — Suggests missing properties per note based on peer analysis
