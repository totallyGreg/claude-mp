---
last_verified: 2026-11-09
sources:
  - type: github
    repo: "zsviczian/kplex"
    paths: ["README.md", "docs/ONTOLOGY_PAIRS.md", "skill.md"]
    description: "K-Plex 0.4.3: ontology roles, configurable fields, paired fields, ExcaliBrain import"
---

# K-Plex Ontology

K-Plex (by zsviczian, the successor to ExcaliBrain) draws the notes around the current one by the meaning of each relationship. In the **Compass** view, parents sit north, children south, friends and previous notes west, challengers and next notes east; siblings get their own area. It reads relationships from frontmatter, inline `field:: [[Note]]` fields (Dataview not required), ordinary links, folders, tags, URLs and dates. The Markdown files are the only store: there is no separate edge database.

## Roles

| Role | Compass | API role | Meaning |
|---|---|---|---|
| Parent | north | `parent` | origin, broader topic, "part of" |
| Child | south | `child` | narrower topic, where an idea leads |
| Friend | west | `left` | related, supporting |
| Challenger | east | `right` | contradicts, transforms |
| Previous | west | `previous` | comes before in a sequence |
| Next | east | `next` | comes after in a sequence |
| Hidden | — | — | hides a connection without removing its links |

## Field names are configured per vault

Which property names map to which role is a setting, not a fixed list. Before designing fields, read the vault's actual lists:

- **Read** `.obsidian/plugins/k-plex/data.json` (read-only). In 0.4.3 the role lists are the keys `parents`, `children`, `friends`, `leftFriends`, `rightFriends`, `previous` and `next`.
- **Names are normalized:** K-Plex matches a note's field to the lists by normalized name, so `Parent Name` and `parent-name` are one field (case, spaces and hyphens don't matter). A lowercase `parent` in a note is read through the `Parent` entry. Manage ontology refuses to add a spelling that normalizes to a field already listed; changing that entry's spelling is a rename of the same field.
- **Unassigned fields:** Settings → K-Plex → Ontology → Manage ontology → **Unassigned** shows properties found in notes that have no role.
- **Changes are the user's:** K-Plex's own agent guidance forbids editing `data.json`. Propose the change and let the user make it in Manage ontology.
- **Prefer the agent API** (below) for reads; `data.json` is the fallback when K-Plex isn't running.

Fresh installs pair Parent/Child, Parents/Children, up/down, u/d, North/South, Previous/Next, West/East, w/e and Before/After. An ExcaliBrain import keeps ExcaliBrain's assignments instead.

## Agent API

K-Plex exposes `window.kplexApi.v1` through `obsidian eval`. The archivist guard denies every other `eval`, so a call must have exactly one of these two shapes, with the vault first and a plain-data argument (keys, double-quoted strings, numbers, `true`/`false`/`null`, arrays and objects; no variables, calls or template strings):

```sh
obsidian vault="<vault_name>" eval 'code=JSON.stringify(window.kplexApi.v1.ontology())'
obsidian vault="<vault_name>" eval 'code=(async()=>JSON.stringify(await window.kplexApi.v1.ontologyDocuments({field:"parent",limit:40})))()'
```

| Method | Use | Guard |
|---|---|---|
| `capabilities`, `status`, `coverage` | what this K-Plex supports; indexing state | normal permissions |
| `ontology`, `ontologyGuide` | exact fields, roles, pairs, descriptions | normal permissions |
| `search`, `node`, `neighbors` | find a note; its parents, children, friends (`role: parent\|child\|left\|right\|previous\|next`) | normal permissions |
| `evidence` | why two notes are connected (property, inline field, link, folder, tag) | normal permissions |
| `ontologyDocuments` (async) | notes that use a field, paged with `cursor` | normal permissions |
| `inspectOntologyOccurrences` (async) | exact positions of fields in one saved note, YAML and inline | normal permissions |
| `previewOntologyConfiguration` | plan an ontology change; saves nothing | normal permissions |
| `applyOntologyConfiguration` (async) | save a previewed change | asks the user |

- **Check the envelope:** `ok`, then `coverage` and `truncated`. Results come from K-Plex's index and may be partial: an empty or short result never proves a field is unused. Use the archivist's full scans for completeness.
- **The CLI can print `Error:` with exit code 0,** and may prefix the JSON with `=>`.
- **K-Plex writes no notes.** Note edits go through `vault-write`; the API only changes K-Plex's own settings, by preview then apply, after the user approves the preview.

## Declaring relationships

```yaml
---
parent: "[[Programming Languages]]"
related:
  - "[[TypeScript]]"
  - "[[Python]]"
---
```

```markdown
replies to:: [[Note A]]
```

- **One end is enough:** a relationship declared on either note shows from both. K-Plex never writes the reciprocal property.
- **Paired fields** (Manage ontology → pair) give the inverse a label from the other end, e.g. `replies to` / `replied by`. Pairing never rewrites notes.
- **Values** are wikilinks, quoted in YAML; lists for several targets.

## Designing a relationship schema

1. Read the vault's role lists (above) and the conventions note, if the vault has one.
2. Use one canonical field per role and record it in the vault's conventions note. Prefer a name already in the lists; a new name needs the user to add it in Manage ontology.
3. For sequences (meetings, versions, steps), use the Previous/Next fields. For rollups (day → Week → Month), the Parent list often already holds `Week`, `Month`, `Quarter` and `Year`.
4. Check each field the schema uses against the lists, and report any that K-Plex won't read.

## Edits from the canvas

Dragging a note into a relationship area writes the property into the note directly, appended at the end of its properties. Those are the user's own edits. Agents still write through `vault-write`.

## Migrating from ExcaliBrain

- **Import:** Settings → K-Plex → Compatibility → **Import ExcaliBrain settings** (also offered automatically while ExcaliBrain runs). It brings the ontology and the node and link styling.
- **Both can run** during the move.
- **After importing,** check Manage ontology → **Unassigned** for fields the notes use that have no role. Case variants of an assigned field aren't gaps.
