---
last_verified: 2026-11-09
sources:
  - type: github
    repo: "clairefro/obsidian-plugin-chronos"
    paths: ["README.md"]
    description: "Chronos Timeline 5.1.3: chronos block syntax, flags, Bases view"
---

# Chronos Timeline Syntax

Chronos Timeline (5.x, needs Obsidian 1.13+) draws timelines from `chronos` code blocks and from Bases views.

## `chronos` blocks

The first character of each line sets the item type:

| Line | Item | Notes |
|---|---|---|
| `- [Date] Name \| Description` | Event | single date or range |
| `@ [Date~Date] Name` | Period | must be a range; shaded background |
| `* [Date] Name \| Description` | Point | single moment |
| `= [Date] Name` | Marker | must be a single date; vertical line |
| `# text` | Comment | ignored |
| `> FLAG` | Flag | one per line, case-insensitive |

```chronos
> NOTODAY
@ [2026-01~2026-03] #blue {Project} Q1 build
- [2026-01-15] {Project} Kickoff | [[Kickoff meeting]]
- [2026-02-01~2026-02-14] #green {Team} Sprint 1
* [2026-03-31] Launch
= [2026-03-01] Code freeze
```

### Dates

- **Format:** `YYYY-MM-DDThh:mm:ss`. Only the year is required: `[2026]`, `[2026-02]`, `[2026-02-28T14:30]`. Hours are 24-hour.
- **Ranges use a tilde, not a hyphen:** `[2024-02-28~2024-05-11]`. Start must come first.
- **BCE:** a minus sign, `[-550~-20]`.
- **Ongoing:** a range with no end, `[2026-11-01~]`, runs to today.

### Modifiers (events and periods)

`- [Date] #color {Group} Name | Description`: color first, then group, both between the date and the name.

- **Colors:** `#red`, `#orange`, `#yellow`, `#green`, `#blue`, `#purple`, `#pink`, `#cyan`. Without one, the theme color is used.
- **Groups** `{Name}` make swimlanes. Names are case-sensitive and may contain spaces.

### Links

A wikilink in the name or the description makes the item clickable. In the name the path is visible; in the description it's hidden. Chronos uses the first link in an item, and `[[note#section]]` works. Links work on events, points and periods.

Renaming a note does not reliably update links inside `chronos` blocks. Link by plain note name rather than an alias.

### Flags

| Flag | Effect |
|---|---|
| `> NOTODAY` | hide the today line |
| `> HEIGHT 300` | fixed height in px |
| `> ORDERBY start\|-content` | stack order; fields `start`, `end`, `content`, `color`, `description`; `-` for descending (slow with many items) |
| `> DEFAULTVIEW 2020\|2026` | initial visible range |
| `> GAP 10\|30` | horizontal\|vertical gap in px (`> GAP 20`, `> GAP \|30`) |
| `> AXIS top` | axis at the top (default bottom) |
| `> ROUNDED` / `> NOROUNDED` | rounded range ends |
| `> TRANSLUCENT` / `> NOTRANSLUCENT` | borderless, semi-transparent items |
| `> OVERFLOWTITLES` / `> NOOVERFLOWTITLES` | long range titles run past the box (on by default) |
| `> UTC` / `> NOUTC` | dates as UTC (default) or local time |
| `> ALIGN left\|center\|right` | item text alignment |

Precedence: plugin defaults < plugin settings < flags. If a flag and its `NO` form both appear, the later line wins.

## Bases view

Add a view of type **Chronos Timeline** to a `.base`. Any note with a `start` property shows; notes without one are ignored.

| Property | Required | Values |
|---|---|---|
| `start` | yes | a Chronos date (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`, optional `THH:mm[:ss]`) |
| `end` | no | a Chronos date |
| `content` | no | item title (defaults to the note name) |
| `type` | no | `event`, `point`, `period` or `marker`. Defaults to `point`, or `event` when there is an `end` or `start` ends in `~` |
| `color` | no | a color name above, without `#`, or a hex code |
| `description` | no | hover text; a YAML list is joined |
| `group` | no | swimlane, if no Bases "Group by" is set |

- **`type` is the item shape, not a category.** For categories, use a `group` property or the Bases **Group by** (Sort menu). The "no group" row always sits at the bottom.
- **Property names are mapped, not fixed:** each view's **Item Property Sources** chooses which note property feeds `start`, `end`, `color` and the rest. New views take the defaults set in the plugin's settings, and Bases formulas can supply any value (e.g. a group from `file.folder`).
- **Date formats:** the view also reads `2026/10/14`, `2026.10.14`, `2026-10-14 12:00`, ISO with `Z` (the time zone is ignored), `Oct 14, 2026` and `14/10/2026`. Ambiguous dates like `03/04/2026` are not guessed.
- **Bad values:** notes with an unreadable `start`, or an `end` before the `start`, are skipped. A collapsed warning above the timeline lists them.

## Display settings

Plugin settings → **Display**: round range ends (off), overflow range titles (on), axis position (bottom), item gap (20/20), translucent items (off), use UTC (on, recommended), item alignment (left). Each has a matching flag.

The timeline options button (lower left) exports PNG or SVG, copies a shareable link, or copies the timeline as Markdown.

## Troubleshooting

- **Range draws as a point or fails:** a hyphen instead of `~` between dates.
- **Bases item missing:** no `start`, or `start` can't be read. Check the skipped-notes warning.
- **Items not grouped:** `type` was used for categories. Use `group` or Group by.
- **A day off for historical dates:** UTC is off. Turn it on or add `> UTC`.
