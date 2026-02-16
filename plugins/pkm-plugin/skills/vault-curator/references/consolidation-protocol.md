# Consolidation Protocol Reference

Guide for detecting duplicate notes, merging content, and redirecting links safely.

## Table of Contents

1. [Duplicate Detection](#duplicate-detection)
2. [Merge Actions](#merge-actions)
3. [Frontmatter Merge Semantics](#frontmatter-merge-semantics)
4. [Content Merge Strategy](#content-merge-strategy)
5. [Link Redirect Procedure](#link-redirect-procedure)
6. [Rollback Mechanism](#rollback-mechanism)
7. [Full Consolidation Flow](#full-consolidation-flow)

## Duplicate Detection

### Tiered Approach

Detection uses three tiers, each progressively more expensive:

**Tier 1: Likely Duplicates** (fast, O(n) title scan)
- Identical titles after normalization (lowercase, strip punctuation, collapse whitespace)
- Example: "Docker Setup" and "docker-setup" → likely duplicate
- Normalization: `re.sub(r'[^\w\s]', '', title.lower()).strip()`

**Tier 2: Possible Duplicates** (moderate, O(n) property scan)
- Title similarity >80% (SequenceMatcher ratio)
- OR identical tags + same folder
- OR identical fileClass + >50% shared properties
- Example: "Docker Setup Guide" and "Setting Up Docker" with same tags → possible duplicate

**Tier 3: LLM Judgment** (expensive, O(k) reads for top-k candidates only)
- Agent reads content of top candidates from Tiers 1-2
- Judges whether notes are truly duplicates, related, or distinct
- Only invoked when automated tiers produce ambiguous results
- Not implemented in scripts — the pkm-manager agent handles this interactively

### Detection Constraints

- **Scope required**: Always operate within a user-selected subdirectory
- **Cap at 20 groups**: Prevents overwhelming output; suggest narrowing scope if exceeded
- **Skip templates**: Exclude files in template directories
- **Skip canvas/base files**: Only scan `.md` files

### Output Format

```json
{
  "status": "success",
  "scope": "Work/Projects",
  "total_notes": 150,
  "groups": [
    {
      "tier": 1,
      "reason": "identical_title",
      "similarity": 1.0,
      "notes": [
        {"path": "Work/Projects/Docker Setup.md", "title": "Docker Setup", "fileClass": "Note"},
        {"path": "Work/Projects/docker-setup.md", "title": "docker-setup", "fileClass": "Note"}
      ]
    }
  ],
  "summary": {"tier1": 3, "tier2": 5, "total_groups": 8}
}
```

## Merge Actions

Per duplicate group, the user selects one action:

### Merge Content
- **When**: Notes are true duplicates with complementary content
- **Result**: Surviving note gets union of frontmatter + concatenated body
- **Link redirect**: All `[[deleted-note]]` → `[[surviving-note]]`
- **Deleted note**: Removed after link redirect

### Create MOC (Map of Content)
- **When**: Notes are related but distinct — consolidation means linking, not merging
- **Result**: New note created with links to both originals
- **No deletion**: Both original notes preserved
- **MOC naming**: `_MOC-{topic}.md` in same directory

### Mark Aliases
- **When**: Notes cover same topic from different angles — keep both, improve discoverability
- **Result**: Add Obsidian `aliases` property to both notes referencing the other's title
- **No deletion**: Both notes preserved

### Skip
- **When**: False positive or intentional duplicates
- **Result**: No changes

## Frontmatter Merge Semantics

When merging two notes (source → target):

### Property Resolution

| Source State | Target State | Result |
|-------------|-------------|--------|
| Has value | Missing | Copy from source |
| Missing | Has value | Keep target |
| Has value | Has value (same) | Keep as-is |
| Has value | Has value (different) | **Conflict** — prompt user |
| List value | List value | Union (deduplicated) |

### Conflict Resolution

For conflicting scalar values, present both to user:
```
Property 'type' conflict:
  Source (note-a.md): "meeting"
  Target (note-b.md): "standup"
  → Keep source / Keep target / Skip
```

### Special Properties

- `aliases`: Always union (append source title as alias)
- `fileClass`: Keep target's value (source is being absorbed)
- `tags`: Union, deduplicated
- `created`: Keep earliest date
- `modified`: Use current timestamp

## Content Merge Strategy

### Concatenation with Separator

```markdown
# [Surviving Note Title]

[Target note content - preserved as-is]

---

## Merged from: [[Source Note]]

[Source note content]
```

### Rules

1. Target content comes first (it's the "surviving" note)
2. Separator: `---` (horizontal rule)
3. Source header: `## Merged from: [[Source Note]]` for provenance
4. Preserve all headings, links, and formatting from both
5. Do not deduplicate content — let the user clean up later

## Link Redirect Procedure

After merging, redirect all vault-wide references to the deleted note:

### Scan Phase
1. Search vault for `[[deleted-note-title]]` in all `.md` files
2. Also search for `[[deleted-note-title|alias]]` (aliased links)
3. Report all affected files before making changes

### Replace Phase
1. Replace `[[deleted-note]]` → `[[surviving-note]]`
2. Replace `[[deleted-note|display]]` → `[[surviving-note|display]]`
3. Handle embeds: `![[deleted-note]]` → `![[surviving-note]]`
4. Preserve any display text after `|`

### Safety
- Always show affected files list before execution
- `--dry-run` mode shows replacements without writing
- Git commit before redirect operation
- Log all replacements for potential rollback

## Rollback Mechanism

### Pre-Operation Checkpoint

Before any destructive operation (merge or redirect):

```bash
cd ${VAULT_PATH}
git add -A
git commit -m "Pre-consolidation checkpoint: [scope description]"
git tag pre-consolidation-$(date +%Y%m%d-%H%M%S)
```

### Rollback

```bash
git reset --hard pre-consolidation-TIMESTAMP
```

### Non-Git Vaults

If vault is not a git repo:
1. Warn user that rollback will be manual
2. Create backup: `cp -r ${SCOPE_PATH} ${SCOPE_PATH}.bak`
3. Proceed only with explicit confirmation

## Full Consolidation Flow

The complete workflow orchestrated by pkm-manager:

```
1. Scope Selection
   → User selects subdirectory to analyze

2. Duplicate Detection
   → Run find_similar_notes.py on selected scope
   → Present grouped results (tier 1 first, then tier 2)

3. Per-Group Decision
   → For each group, user selects: merge / MOC / alias / skip
   → Agent may read content for Tier 3 judgment if requested

4. Pre-Operation Checkpoint
   → Git commit before any changes

5. Execute Actions
   → For merges: run merge_notes.py (--dry-run first)
   → For MOCs: create MOC note
   → For aliases: add alias properties

6. Link Redirect
   → Run redirect_links.py for merged notes (--dry-run first)
   → Show affected files, get confirmation
   → Execute redirects

7. Cleanup
   → Delete merged source notes (after redirect)
   → Verify no broken links remain

8. Summary
   → Report: X merged, Y MOCs created, Z aliases added, W skipped
   → List all modified files
```

## References

- Migration strategies: `references/migration-strategies.md`
- Obsidian aliases: https://help.obsidian.md/Linking+notes+and+files/Aliases
- Python SequenceMatcher: https://docs.python.org/3/library/difflib.html#difflib.SequenceMatcher
