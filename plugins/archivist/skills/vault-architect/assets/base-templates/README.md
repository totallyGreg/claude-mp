# Base Templates

This directory contains starter `.base` files for common Obsidian PKM scenarios.

## Using These Templates

1. Copy the desired `.base` file to your vault's Bases folder (typically in your Templates or a dedicated Bases folder)
2. Customize the properties, filters, and views to match your vault's structure and metadata
3. Embed views in your notes using: `![[filename.base#ViewName]]`

## Available Templates

### related-files.base

**Purpose:** Show all notes that link to the current note (backlinks)

**Use in:** Any note where you want to see related content

**Embed as:**
```markdown
## Related Notes
![[related-files.base#Related Files]]
```

### temporal-rollup.base

**Purpose:** Aggregate daily notes into weekly/monthly summaries

**Use in:**
- Weekly notes (shows all daily notes from that week)
- Monthly notes (shows all daily notes from that month)
- Daily notes (shows all notes created today)

**Requirements:**
- Daily notes must have `Week` and `Month` properties linking to their week/month notes
- Daily notes must have `wins`, `challenges`, `improvements` properties for rollup display

**Embed as:**
```markdown
## This Week's Daily Notes
![[temporal-rollup.base#This Week]]

## This Month's Daily Notes
![[temporal-rollup.base#This Month]]

## Notes Created Today
![[temporal-rollup.base#Today]]
```

### terminology.base

**Purpose:** Automatic aggregation of terms by shared abbreviation

**Use in:**
- Abbreviation notes (to show all terms with that abbreviation)
- Terminology index notes

**Requirements:**
- Term notes must have the abbreviation in their `aliases` property
- Abbreviation note is named exactly as the abbreviation appears in aliases
- Term notes should have a `summary` property describing the term

**Example:**
```yaml
# In term note: "Application Programming Interface.md"
---
aliases: [API]
summary: A set of protocols for building software applications
---

# In abbreviation note: "API.md"
---
title: API
---
# API

![[terminology.base#Terms with Context]]
```

### customer-notes.base

**Purpose:** Organize work notes by customer/company

**Use in:**
- Company/customer profile notes
- Work dashboard notes
- Project notes

**Requirements:**
- Meeting and project notes must have `customer` property linking to company note
- Work notes should be tagged with `meeting`, `work`, or stored in "Work" folder
- Folder structure includes "Work" prefix (adjust filter if different)

**Embed as:**
```markdown
# In company note
## Recent Meetings
![[customer-notes.base#Customer Meetings]]

## All Notes
![[customer-notes.base#Customer Notes]]

# In work dashboard
## All Work Activity
![[customer-notes.base#All Work Notes]]
```

## Customization Tips

### Adjusting Folder Paths

If your folders are named differently, update the filter:

```yaml
# Change this:
file.folder.startsWith("700 Notes")

# To this:
file.folder.startsWith("Your/Folder/Path")
```

### Adding Properties

To display additional metadata:

1. Add to `properties` section:
```yaml
properties:
  note.your_property:
    displayName: Your Property Name
```

2. Add to `order` section:
```yaml
order:
  - file.name
  - your_property  # Add your property here
```

3. Optionally add to `sort`:
```yaml
sort:
  - property: note.your_property
    direction: ASC
```

### Changing Column Widths

Adjust `columnSize` to fit your screen:

```yaml
columnSize:
  file.name: 300  # Pixels
  note.summary: 600
```

### Filtering by Multiple Tags

Use `or` for flexible categorization:

```yaml
filters:
  or:
    - file.tags.contains("meeting")
    - file.tags.contains("call")
    - file.tags.contains("sync")
```

## Combining Templates

You can combine multiple views in one `.base` file. For example, merge `related-files.base` and `customer-notes.base` into a master `Notes.base` with all views:

```yaml
views:
  - name: Related Files
    # ... related files config

  - name: Customer Meetings
    # ... customer meetings config

  - name: Customer Notes
    # ... customer notes config
```

Then embed specific views as needed:
```markdown
![[Notes.base#Related Files]]
![[Notes.base#Customer Meetings]]
```

## Troubleshooting

### View shows no results

1. Check that filter properties match your frontmatter exactly (case-sensitive)
2. Verify folder paths are correct
3. Test with a simpler filter (e.g., just one condition) to isolate issue
4. Ensure notes have required properties in frontmatter

### Properties not displaying

1. Use `note.propertyname` for custom frontmatter properties
2. Use `file.propertyname` for built-in properties
3. Check spelling matches frontmatter exactly

### Links not working in embeds

Make sure to use the exact view name from the `name:` field when embedding:
```markdown
![[filename.base#Exact View Name]]
```

## Next Steps

1. Copy a template to your vault
2. Customize paths and properties
3. Test with a few notes
4. Refine filters and display
5. Document in your vault's System Guide
