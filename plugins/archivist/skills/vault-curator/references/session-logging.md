# Session Logging Reference

## Canonical Log Entry Format

Defined in `[[Insert Log]]` (`900 📐Templates/910 File Templates/918 Snippet Templates/Insert Log.md`). Short form:
```
### (log:: [[YYYY-MM-DD|YYYY-MM-DD ⏱HH:mm]]: {group} phase — entry text)
```
- `{group}` = optional Chronos swim lane tag for the workstream/topic, NOT agent identity
- `phase` = optional prefix: `discovery`, `decision`, `resolution`, `blocked`
- Wikilink `[[Note Name]]` for file-ops and discoveries to create backlinks

## Entry Operations

All entry operations dispatch through QuickAdd → `logEntries.js`:
```bash
obsidian quickadd:run choice="logEntries" vars='{"action":"ACTION", "path":"$SESSION_LOG", ...}'
```

| Action | What it does |
|--------|-------------|
| `create` | Insert new timestamped log entry (`subject` var) |
| `close` | Stamp `~HH:mm` on last open entry |
| `read` | Show parsed entry details (`selector` var) |
| `enrich` | Rewrite heading with phase/outcome (`phase`, `outcome` vars) |
| `update` | Insert content under an entry (`content`, `selector` vars) |

## `/session-log start`

**Default (no project mentioned):** Use today's daily note as the session log.
1. Find today's daily note:
   ```bash
   obsidian search query="fileClass:journal" limit=1 sort=created
   ```
   If no result, open today's note by date so Obsidian creates it from the daily note template.
2. Store the returned path as `SESSION_LOG`; report it to the user.
3. Create a session-start entry:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"Session started"}'
   ```

**With project mentioned:** Create a dedicated session note.
1. Invoke the New Session template:
   ```bash
   obsidian templater:create-from-template template="900 📐Templates/910 File Templates/🔬 New Session.md" file="800 Generated/temp-session.md"
   ```
2. After user completes Obsidian prompts, find the resulting note:
   ```bash
   obsidian search query="fileClass:session status:\"In Progress\"" limit=1 sort=created
   ```
3. Store the returned path as `SESSION_LOG`.

**With specific note path or obsidian:// URL:**
1. Decode the path from the URL if needed (`%20` → space).
2. Verify the note exists by reading it.
3. Store the path as `SESSION_LOG`.
4. Create a session-start entry via `logEntries` create action.

## `/session-log resume`

Reconnects a new Claude Code conversation to an existing in-progress session note.

1. **Ask** for the session note location (obsidian:// URL, vault-relative path, or title).
2. **Resolve** — URL: decode `file=` param. Title: search `fileClass:session status:"In Progress"`, let user pick if multiple. Path: use directly.
3. **Validate** — read the note, confirm `fileClass: session` or `journal`, status not `Done`, has `log::` entries.
4. **Store** as `SESSION_LOG`.
5. **Brief the user** — last entry, current Findings/Next Steps, `summary:` value, open entry count.
6. **Create a resume entry:**
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"Session resumed"}'
   ```

## Checkpoint Entries (during session)

Write at major decisions and workflow boundaries — **not** after every tool call:
```bash
obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"{group} phase — DESCRIPTION"}'
```

Entry types: `decision`, `file-operation`, `workflow-execution`, `discovery`, `resolution`.

**Progressive updates:** After each resolution entry, update `summary:` in frontmatter. After a blocked entry, set `status: Blocked`.

## `/session-log recap`

1. Read the most recent `/recap` output from conversation context.
2. Format as bullets and insert under the open entry:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"update","path":"$SESSION_LOG","selector":"open","content":"- BULLET_1\n- BULLET_2"}'
   ```
3. Show the appended bullets to the user and offer to edit before finalizing.

## `/session-log pause`

Rolls up work-so-far for cold re-engagement. Session stays `In Progress`.

1. **Close** the open entry via `logEntries` close action.
2. **Read** all entries via `obsidian read` to see full content.
3. **Bulk enrich** unenriched entries — infer phase/outcome from body content and apply via `logEntries` enrich action.
4. **Write** incremental Findings and Next Steps to note sections above the Log (rough/additive).
5. **Update** `summary:` in frontmatter.
6. **Create** a pause entry: `"subject":"pause — Session paused"`.
7. Leave `status: In Progress` and `end:` empty.

## `/session-log end`

Full session close — synthesize everything and finalize.

**Close Log mechanics:** "Close Log" is a QuickAdd Macro wrapping a single UserScript (`900 📐Templates/Scripts/closeLog.js`). It scans the **active file** for the last open `log::` entry (one with `⏱HH:mm` but no `~HH:mm`) and appends the current time. The active-file requirement is why step 1 is mandatory.

1. Bring session note to front:
    ```bash
   obsidian open path="$SESSION_LOG"
    ```
2. Close the last open entry:
    ```bash
   obsidian quickadd:run choice="Close Log"
    ```
3. If session note (fileClass:session), update frontmatter:
    ```bash
   obsidian property:set name="status" value="Done" path="$SESSION_LOG"
   obsidian property:set name="end" value="YYYY-MM-DDTHH:mm:00" path="$SESSION_LOG"
   obsidian property:set name="summary" value="<final one-line summary>" path="$SESSION_LOG"
    ```
   Skip frontmatter updates for daily notes (fileClass:journal).
4. **Synthesize** — write definitive Goal, Findings, Outcome, Next Steps (replaces pause rough notes).
5. **Create** a session-end entry: `"subject":"resolution — Session end — <summary>"`.
6. Report the closed session path, then clear `SESSION_LOG`.

## Abnormal Termination (SubagentStop hook)

If archivist exits without `/session-log end` and `SESSION_LOG` is set:
```bash
obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"abnormal-termination — session ended unexpectedly"}'
```
If session note (fileClass:session), also set:
```bash
obsidian property:set name="status" value="Interrupted" path="$SESSION_LOG"
```
