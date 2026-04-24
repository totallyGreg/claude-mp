---
name: session-log
description: Manage a session log in your vault. Use "start" to open a session (daily note by default, or a new 🔬 Session note if a project is mentioned), "resume" to reconnect to an existing session, "pause" to roll up progress for cold re-engagement, "end" to finalize the session, or "recap" to append the latest Claude Code recap as bullets in the open log entry.
argument-hint: [start|resume|pause|end|recap]
---

Invoke the archivist agent to manage a session log. The argument is `$ARGUMENTS`.

## logEntries.js

All entry operations dispatch through QuickAdd's `logEntries` choice:

```bash
obsidian quickadd:run choice="logEntries" vars='{"action":"ACTION", ...}'
```

| Action | Vars | What it does |
|--------|------|-------------|
| `create` | `subject, path?` | Insert new timestamped log entry |
| `close` | `path?, endTime?` | Stamp `~HH:mm` on last open entry |
| `read` | `selector?, path?` | Show parsed entry details |
| `enrich` | `selector?, phase?, outcome?, group?, path?` | Rewrite heading with dimensions |
| `update` | `selector?, content, position?, path?` | Insert content under an entry |

- `path` — vault-relative path; defaults to active file if omitted
- `selector` — `'latest'`, `'open'`, `'HH:mm'`, or `-1`/`-2`; defaults to `'latest'`
- `position` — `'append'` (default) or `'prepend'`
- When vars include values (e.g., `phase`, `subject`), prompts are skipped
- Without `action` var, an interactive picker is shown

---

**If the argument is `start`:**

First, determine whether a specific project was mentioned in the user's request.

**start — no project mentioned (default):**
1. Find today's daily note:
   ```bash
   obsidian search query="fileClass:journal" limit=1 sort=created
   ```
   If no result, open today's note by date so Obsidian creates it from the daily note template.
2. Store the returned path as `SESSION_LOG` for this session.
3. Create a session-start log entry:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"Session started"}'
   ```
4. Report the session log path to the user.

**start — project mentioned:**
1. Invoke the New Session template (Obsidian UI handles all interactive prompts; `tp.file.move()` places the note in the correct folder automatically):
   ```bash
   obsidian templater:create-from-template template="900 📐Templates/910 File Templates/🔬 New Session.md" file="800 Generated/temp-session.md"
   ```
2. Inform the user: "Complete the prompts in Obsidian, then confirm here when done."
3. Wait for user confirmation, then find the resulting note:
   ```bash
   obsidian search query="fileClass:session status:\"In Progress\"" limit=1 sort=created
   ```
4. Store the returned path as `SESSION_LOG` and report it to the user.

**start — user provides a specific note path or obsidian:// URL:**
1. Decode the path from the URL if needed (e.g., `%20` → space).
2. Verify the note exists by reading it.
3. Store the path as `SESSION_LOG`.
4. Create a session-start log entry:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"Session started"}'
   ```
5. Report the session log path to the user.

---

**If the argument is `resume`:**

Resume reconnects a new Claude Code conversation to an existing in-progress session note.

1. **Ask for the session note location** — prompt the user for an `obsidian://` URL, vault-relative path, or note title.

2. **Resolve the path:**
   - URL: decode the `file=` parameter (`%20` → space)
   - Title: search and let user pick if multiple results:
     ```bash
     obsidian search query="fileClass:session status:\"In Progress\" TITLE" limit=5 sort=modified
     ```
   - Path: use directly

3. **Validate** — read the note, confirm it has `fileClass: session` (or `journal`), `status` is not `Done`, and has existing `log::` entries. Report any issues.

4. **Store as `SESSION_LOG`.**

5. **Brief the user** — summarize: last entry, current Findings/Next Steps, `summary:` value, number of open entries.

6. **Create a resume entry:**
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"Session resumed"}'
   ```

---

**If the argument is `pause`:**

Pause rolls up work-so-far for cold re-engagement. The session stays `In Progress`.

1. **Close the open entry:**
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"close","path":"$SESSION_LOG"}'
   ```

2. **Read all entries** to understand work completed:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"read","path":"$SESSION_LOG","selector":"latest"}'
   ```
   Also read the full note content via `obsidian read` to see all entry bodies.

3. **Bulk enrich** — for each entry without phase/outcome, infer from body content:
   - Phase keywords: "root cause"/"traced"/"found" → `discovery`; "fix"/"commit" → `implementation`; "test"/"verify" → `testing`; "blocked"/"waiting" → `blocked`; "decided"/"chose" → `decision`
   - Outcome keywords: "fixed"/"resolved" → `resolved`; "merged"/"deployed" → `shipped`; "blocked"/"can't" → `blocked`; "partial"/"WIP" → `partial`
   - Apply each:
     ```bash
     obsidian quickadd:run choice="logEntries" vars='{"action":"enrich","path":"$SESSION_LOG","selector":"HH:mm","phase":"PHASE","outcome":"OUTCOME"}'
     ```

4. **Write incremental Findings and Next Steps** — synthesize from entries and write to the note sections above the Log using Edit tool. These are rough/additive — will be refined at end.

5. **Update running summary** in frontmatter:
   ```bash
   obsidian property:set name="summary" value="<one-line current state>" path="$SESSION_LOG"
   ```

6. **Create a pause entry:**
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"pause — Session paused"}'
   ```

7. Leave `status: In Progress` and `end:` empty. Report the pause to the user.

---

**If the argument is `end`:**

End is the full session close — synthesize everything and finalize.

1. **Close the open entry** (same as pause step 1).

2. **Read all entries** (same as pause step 2).

3. **Bulk enrich** all unenriched entries (same as pause step 3).

4. **Close all remaining open entries** — repeat until no open entries remain:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"close","path":"$SESSION_LOG"}'
   ```
   Run multiple times if needed — each call closes one open entry.

5. **Synthesize structured sections** — review ALL entries and write definitive content to the note sections above the Log (replaces any rough notes from pause):
   - **Goal** — from session start context and early entries
   - **Findings** — from discovery/resolution entries (permanent learnings)
   - **Outcome** — what was achieved, shipped, decided
   - **Next Steps** — outstanding work, follow-ups, open questions

6. **Update frontmatter:**
   ```bash
   obsidian property:set name="status" value="Done" path="$SESSION_LOG"
   obsidian property:set name="end" value="YYYY-MM-DDTHH:mm:00" path="$SESSION_LOG"
   obsidian property:set name="summary" value="<final one-line summary>" path="$SESSION_LOG"
   ```
   Skip frontmatter updates for daily notes (fileClass:journal).

7. **Create a session-end entry:**
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"create","path":"$SESSION_LOG","subject":"resolution — Session end — <summary>"}'
   ```

8. Report the closed session path, then clear `SESSION_LOG`.

### Linking convention

All references to external artifacts in log entries, Findings, Outcome, and Next Steps **must be full hyperlinks**:
- GitLab issues: `[#23](https://code.pan.run/org/repo/-/issues/23)`
- Merge requests: `[MR !17](https://code.pan.run/org/repo/-/merge_requests/17)`
- Slack threads: `[C0AV8KQFLQH](https://panw-global.slack.com/archives/C0AV8KQFLQH)`

### Entry close convention

All log entries must be closed with `~HH:mm` end times. Open entries render as infinite time blocks in the Chronos timeline.

---

**If the argument is `recap`:**

1. Read the most recent Claude Code `/recap` output from the current conversation context.
2. Format the recap as bullet points.
3. Insert the bullets under the current open entry:
   ```bash
   obsidian quickadd:run choice="logEntries" vars='{"action":"update","path":"$SESSION_LOG","selector":"open","content":"- BULLET_1\n- BULLET_2"}'
   ```
4. Show the user the appended bullets and offer to edit any of them before they are finalized.

If SESSION_LOG is not set, inform the user that no session is active and suggest running `/session-log start` first.

---

**If no argument is provided:**

Ask the user what they'd like to do:
- **start** — begin a new session log (daily note, or project session note)
- **resume** — reconnect to an existing in-progress session note
- **pause** — roll up progress for cold re-engagement (session stays In Progress)
- **end** — full close: enrich entries, synthesize sections, finalize frontmatter
- **recap** — append the latest recap as bullets in the open log

Then execute the appropriate workflow above.
