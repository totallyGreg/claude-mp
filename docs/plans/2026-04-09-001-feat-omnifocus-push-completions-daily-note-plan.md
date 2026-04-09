---
title: "feat: Push OmniFocus Completions to Obsidian Daily Note"
type: feat
status: deferred
date: 2026-04-09
origin: "conversation — design paused pending vault structure research"
---

# feat: Push OmniFocus Completions to Obsidian Daily Note

## Problem Frame

OmniFocus has a `ofo completed-today --markdown` CLI command that formats today's completions for Obsidian. The missing piece is delivery to the daily note. A naive `obsidian://advanced-uri?mode=append` approach was prototyped but stopped — it breaks note structure and weekly aggregation.

## Vault Research (2026-04-09)

### Daily Note Structure

**Template:** `900 📐Templates/910 File Templates/🌄 New Day.md`
**Path pattern:** `500 ♽ Cycles/520 🌄 Days/YYYY/YYYY-MM-DD.md`

**Heading order:**
1. `# 🌎 <date>` — title + journal-nav code block
2. Callout — `Gratitude::`, `Desired Outcome::`, `![[Notes.base#📆 Todays Meeting Notes]]`
3. `## 📓 Journal` — main capture area
4. `## 🔗 Notes & References`
5. `## 🌒 Evening Wind Down`
6. `# Summary 🏁` — included via `tp.file.include("[[Daily Summary 🏁]]")`

**Relevant frontmatter:**
- `wins` — plain YAML string (not list); filled manually; rendered in `# Summary 🏁` via `=this.wins`
- `challenges`, `gratitude`, `improvements` — same pattern
- `journal: "☀️Periodic daily"` — **load-bearing discriminator** for Bases queries; must never be corrupted
- `Week: [[2026-W15]]` — connects daily note to week note in `Logs.base#Week Logs`

**No existing "Completed Today" section** — any machine-written section would be new.

### Weekly Aggregation Mechanism

**Template:** `900 📐Templates/910 File Templates/🗓 New Week.md`
**Path pattern:** `500 ♽ Cycles/530 🗓 Weeks/YYYY-WNN.md` (no leading zero: `2026-W7` not `2026-W07`)

**`Logs.base#Week Logs`** (primary daily rollup):
- Filter: `journal == "☀️Periodic daily"` AND `file.hasLink(this)` (daily note has `Week: [[YYYY-WNN]]`)
- Columns: `file.name`, `log`, `wins`, `challenges`
- Sorted by `journal-date` ASC

**Key insight:** The weekly Bases view surfaces the `wins` frontmatter property — **not body content**. Task completions written to the body are invisible in the weekly rollup unless the user opens each daily note individually.

## Design Options

### Option A — Write to `wins` frontmatter only
- **Delivery:** Advanced URI `frontmatterKey=wins&data=<formatted-string>`
- **Weekly visibility:** ✅ Automatic via `Logs.base#Week Logs`
- **Idempotency:** ✅ Property set overwrites previous value
- **Format:** ⚠️ Plain YAML string — multi-task list needs compact format (e.g., `"ProjectA: Task1, Task2 | ProjectB: Task3"` or simple newline-separated)
- **Risk:** Overwrites any manually written wins entry

### Option B — Add dedicated `## ✅ Completed Today` body section
- **Delivery:** Advanced URI with `heading=✅ Completed Today` (requires heading to exist) or append with marker
- **Weekly visibility:** ❌ Body content not surfaced in `Logs.base`
- **Idempotency:** Requires owned-section strategy (timestamp subheading, or clear+rewrite)
- **Format:** ✅ Full markdown with `### Project Name` subheadings and `- [x]` items
- **Risk:** Low — isolated section, no frontmatter touch

### Option C — Both (recommended)
- Write a compact summary to `wins` frontmatter (weekly rollup)
- Write a detailed list to a `## ✅ Completed Today` body section (daily detail)
- Each write is idempotent independently

**`wins` format for option C:**
`"12 tasks: ProjectA (3), ProjectB (5), No Project (4)"` — count-only summary fits YAML string cleanly and is readable in the Bases column view.

## Idempotency Strategy (for body section)

Advanced URI does not support section-replace natively. Options:

1. **Timestamp subheading** — append `### Completions as of HH:MM` each run; multiple runs create multiple timestamped snapshots (acceptable for on-demand use, noisy for scheduled)
2. **obsidian-linter / custom plugin** — can find-and-replace sections; adds a dependency
3. **Direct file write via shell** — read the file, find the section, replace it, write back; bypasses URI scheme entirely; requires vault path + file path resolution; more reliable for idempotency
4. **Run once at EOD** — if the plugin is only triggered manually at end of day, idempotency is less critical and simple append is acceptable with a guard (`## ✅ Completed Today` heading existence check)

Option 3 (direct file write) combined with the `ofo completed-today --markdown` output is the cleanest implementation path and avoids Advanced URI limitations.

## Existing Scaffold

**Plugin file:** `plugins/omnifocus-manager/skills/omnifocus-manager/assets/PushCompletionstoDailyNote.omnifocusjs`

This is a working solitary plugin scaffold with:
- Manifest: `com.totallytools.omnifocus.pushcompletionstodailynote` v1.0
- Completion query logic (group by project, `- [x]` format)
- `URL.fromString(obsidianUrl).open()` delivery stub

The OmniFocus-side logic is sound. The delivery mechanism needs to be replaced with the chosen idempotency strategy before installation.

**Alternatively:** The `ofo completed-today --markdown` CLI command already produces formatted output. The plugin may only need to call that (via pasteboard) and handle Obsidian delivery — avoiding duplicating the OmniFocus query logic.

## Deferred Decisions

1. **Trigger model** — OmniFocus plugin action (manual), scheduled ofo CLI call, or both?
2. **`wins` format** — count summary vs task names vs project breakdown?
3. **Body section idempotency** — direct file write vs timestamp subheading vs run-once-at-EOD?
4. **Attache integration** — fold Obsidian push into `completedSummary` (Wins Report) action rather than a separate plugin?

## Implementation Units (when resumed)

- [ ] **Unit 1:** Decide trigger model and idempotency strategy (deferred decisions above)
- [ ] **Unit 2:** Implement `wins` frontmatter write (compact summary format)
- [ ] **Unit 3:** Implement body section write with chosen idempotency strategy
- [ ] **Unit 4:** Wire up `ofo completed-today --markdown` as data source (avoid duplicate query logic)
- [ ] **Unit 5:** Test end-to-end — daily note structure intact, weekly Bases rollup shows wins

## References

- Vault template: `900 📐Templates/910 File Templates/🌄 New Day.md`
- Weekly Bases: `Logs.base#Week Logs` (filter: `journal == "☀️Periodic daily"` + `file.hasLink`)
- Existing scaffold: `assets/PushCompletionstoDailyNote.omnifocusjs`
- Related CLI: `scripts/ofo completed-today --markdown`
- Advanced URI docs: `obsidian://advanced-uri` — supports `frontmatterKey`, `heading`, `mode=append/prepend/overwrite`
