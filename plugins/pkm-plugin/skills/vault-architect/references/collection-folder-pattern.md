# Collection Folder Pattern

A **Collection Folder** is the standard structural unit for a named note type in this vault. It groups related notes under a single folder and provides the infrastructure to browse, filter, and maintain them consistently.

## Anatomy

Every Collection Folder has four parts:

```
700 Notes/
└── Workflows/                       ← 1. Folder (plural noun)
    ├── Workflows.md                 ← 2. Folder note (same name as folder)
    ├── Capture to Review.md         ← 3. Member notes
    ├── Weekly Review.md
    └── ...

900 📐Templates/
├── 910 File Templates/
│   └── New Workflow.md              ← 4. Templater template
└── 970 Bases/
    └── Workflows.base               ← 5. Bases file (same name as folder)
```

### 1. Folder

Named after the note type in plural form (e.g., `Workflows`, `People`, `Ideas`, `Personas`). Member notes live directly in this folder or in subfolders if the collection is large enough to warrant further grouping.

### 2. Folder Note

A note named identically to the folder (e.g., `Workflows/Workflows.md`). This is the **home page** for the collection — the first place users navigate to understand the note type and browse its members.

**Standard structure:**

```markdown
---
fileClass: Folder
---

Brief prose description of what these notes are, how they're used, and any
conventions specific to this type.

## Schema

| Property | Type | Description |
|----------|------|-------------|
| status   | text | e.g. active, archived |
| ...      | ...  | ...                   |

## Notes

![[Workflows.base#All Workflows]]
```

**Rules:**
- `---` on line 1, no leading blank lines
- `fileClass: Folder` (prevents this note from appearing in the member Bases view)
- One embedded Bases view using the collection's named view: `![[CollectionName.base#View Name]]`
- Schema table documents the expected frontmatter for member notes

### 3. Member Notes

Notes living inside the folder. They should share a consistent `fileClass` value (e.g., `fileClass: Workflow`) and a common frontmatter schema.

Minimum required fields for all members:
- `fileClass: <TypeName>` — identifies membership and enables Bases filtering
- Any fields surfaced in the Bases view (title, status, tags, etc.)

### 4. Templater Template

Located at `900 📐Templates/910 File Templates/New <TypeName>.md`. Prompts for required fields, auto-renames and moves the file to the collection folder, positions the cursor. See `references/templater-patterns.md` for patterns.

### 5. Bases File

Located at `900 📐Templates/970 Bases/<CollectionName>.base`. Contains at minimum one named view that queries all members. The view should:

- Filter by `fileClass` (preferred) or folder path (acceptable fallback)
- Include at least: `file.name`, relevant status/type fields, `file.mtime`
- Be sorted by modification date descending by default

**Canonical filter (prefer fileClass):**

```yaml
views:
  - type: table
    name: All Workflows
    filters:
      note.fileClass == "Workflow"
    order:
      - file.name
      - note.status
      - file.mtime
    sort:
      - property: file.mtime
        direction: DESC
```

**Fallback filter (folder path):**

```yaml
filters:
  file.folder.startsWith("700 Notes/Workflows")
```

## Known Collection Folders in This Vault

| Folder | Folder Note | Bases File | fileClass |
|--------|-------------|------------|-----------|
| `700 Notes/Workflows` | `Workflows.md` | `Workflows.base` | `Workflow` |
| `700 Notes/People` | `People.md` | `People.base` | `Person` |
| `700 Notes/Ideas` | `Ideas.md` | `Ideas.base` | `Idea` |
| `700 Notes/Personas` | `Personas.md` | `Personas.base` | `Persona` |

## Health Signals

A healthy collection has all of the following:

- [ ] Folder note exists at `<Folder>/<Folder>.md`
- [ ] Folder note embeds the Bases view (`![[CollectionName.base#...]]`)
- [ ] Bases file exists at `900 📐Templates/970 Bases/<CollectionName>.base`
- [ ] Bases file has at least one named view scoped to this collection
- [ ] Member notes share a consistent `fileClass`
- [ ] Schema drift is below 20% (i.e., ≥80% of members have each expected property)
- [ ] Templater template exists at `900 📐Templates/910 File Templates/New <TypeName>.md`

Use `check_collection_health.py` (vault-curator) to audit these signals automatically.

## When to Create a New Collection

Create a Collection Folder when:
- You have ≥5 notes of the same conceptual type and expect more
- You want to browse or filter these notes as a group
- You want consistent metadata across these notes

Do **not** create a Collection Folder for:
- One-off or ad-hoc notes without a repeating pattern
- Notes that are better organized by temporal rollup (use Temporal Rollup instead)
- Notes that belong to multiple categories (use tags + Bases instead)

## Setup Workflow

See vault-architect SKILL.md → "New Collection Setup" for the step-by-step creation workflow.
