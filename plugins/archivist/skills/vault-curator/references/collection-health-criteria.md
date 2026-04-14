---
name: Collection Health Criteria
description: Documents what makes an Obsidian collection healthy, partial, or missing infrastructure — used by check_collection_health.py
load_when: Running collection health checks, scaffolding new collections, interpreting health check output
---

# Collection Health Criteria

**Load when:** Running `/collection` workflow, `/health` command, or interpreting output from `check_collection_health.py`.

## What is a Collection?

A **Collection** is a vault folder containing notes of the same conceptual type, organized with standardized infrastructure:

- A **folder note** at `<Folder>/<Folder>.md` — the collection's index and entry point
- A **Bases file** at `900 📐Templates/970 Bases/<Name>.base` — the canonical query view for the collection
- A **Bases embed** in the folder note: `![[<Name>.base#<View>]]` — connects the index to the query view
- **Member notes** sharing a consistent `fileClass` frontmatter property

## Candidate Detection

A folder qualifies as a **candidate collection** if it meets either condition:

1. **Has a folder note** — a file named the same as its parent folder (e.g., `700 Notes/Projects/Projects.md`)
2. **Has density + fileClass coverage** — contains ≥5 notes where ≥60% share the same `fileClass` value (threshold overridable with `--coverage-threshold`)

Folders are **excluded** from candidate detection if they:
- Start with `.` (hidden folders, e.g., `.obsidian`)
- Start with `_` (system folders)
- Contain "Template" in the name
- Contain 📐 emoji (infrastructure folders)

## Health Status Values

| Status | Meaning |
|--------|---------|
| `healthy` | All three infrastructure pieces present; no schema drift |
| `partial` | Infrastructure present but schema drift detected, OR exactly one infrastructure piece missing |
| `missing_infrastructure` | Two or more infrastructure pieces absent |

**Infrastructure pieces checked:**

| Piece | Field | How checked |
|-------|-------|-------------|
| Folder note | `has_folder_note` | `<folder>/<Name>.md` exists |
| Bases embed | `folder_note_embeds_bases` | Folder note body contains `![[*.base#...]]` |
| Bases file | `has_bases_file` | `900 📐Templates/970 Bases/<Name>.base` exists |

## Schema Drift Detection

Schema drift is counted when a frontmatter property is present in ≥50% of member notes but missing from at least one. The `schema_drift_issues` field counts the number of such properties.

Schema drift alone results in `partial` (not `missing_infrastructure`) when all three infrastructure pieces are present.

## Output Fields

| Field | Type | Description |
|-------|------|-------------|
| `folder` | string | Vault-relative path to the collection folder |
| `name` | string | Folder name (last path component) |
| `member_count` | int | Total `.md` files in the folder |
| `has_folder_note` | bool | Whether `<Name>.md` exists inside the folder |
| `folder_note_embeds_bases` | bool | Whether the folder note contains a `.base` embed |
| `has_bases_file` | bool | Whether a `.base` file exists at the expected path |
| `dominant_fileclass` | string\|null | Most common `fileClass` value among members |
| `fileclass_coverage_pct` | float | % of non-folder-note members sharing the dominant fileClass |
| `schema_drift_issues` | int | Number of properties present in ≥50% of notes but not all |
| `health` | string | `healthy` \| `partial` \| `missing_infrastructure` |
| `missing` | list | Infrastructure pieces absent: `folder_note`, `bases_embed`, `bases_file` |

## CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--scope <path>` | entire vault | Vault-relative folder to limit the scan |
| `--folder <path>` | all candidates | Check a single specific folder |
| `--dry-run` | false | Show candidate folders without running health checks |
| `--coverage-threshold <pct>` | 60 | Minimum fileClass coverage % for density-based candidate detection |

## Thresholds

| Threshold | Default | Overridable |
|-----------|---------|-------------|
| Minimum notes for density detection | 5 | No |
| fileClass coverage for density detection | 60% | Yes (`--coverage-threshold`) |
| Schema drift: property presence threshold | 50% | No |
| Bases file location | `900 📐Templates/970 Bases/` | No |

## Fix Priority

When collections are unhealthy, offer fixes in this order:

1. `missing: folder_note` → scaffold via Collection Setup workflow
2. `missing: bases_embed` → add `![[<Name>.base#<View>]]` embed to folder note (confirm first)
3. `missing: bases_file` → scaffold via Collection Setup workflow
4. `schema_drift_issues > 0` → run `detect_schema_drift.py --scope <folder>` and offer bulk property fixes

## Related Workflows

- [[collection]] — Full collection scaffolding workflow
- [[health]] — Vault health snapshot (runs collection health as a sub-check)
- [[drift]] — Schema drift detection (complement to collection health)
