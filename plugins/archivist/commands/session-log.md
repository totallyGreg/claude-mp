---
name: session-log
description: Manage a session log in your vault. Use "start" to open a session (daily note by default, or a new 🔬 Session note if a project is mentioned), "end" to finalize the session, or "recap" to append the latest Claude Code recap as bullets in the open log entry.
argument-hint: [start|end|recap]
---

Invoke the archivist agent to manage a session log. The argument is `$ARGUMENTS`.

**If the argument is `start`:**

First, determine whether a specific project was mentioned in the user's request.

**start — no project mentioned (default):**
1. Find today's daily note:
   ```bash
   obsidian search query="fileClass:journal" limit=1 sort=created
   ```
   If no result, open today's note by date so Obsidian creates it from the daily note template.
2. Store the returned path as `SESSION_LOG` for this session.
3. Append a session-start log entry to the `## Notes 📓` section:
   ```bash
   obsidian append path="$SESSION_LOG" content="\n### (log:: [[YYYY-MM-DD|YYYY-MM-DD ⏱HH:mm]]: {archivist} workflow-execution — Session started)"
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

---

**If the argument is `end`:**

1. Open the session note to make it the active file (required — Close Log operates on the active file):
   ```bash
   obsidian open path="$SESSION_LOG"
   ```
2. Close the last open `log::` entry as a Chronos range:
   ```bash
   obsidian quickadd:run choice="Close Log"
   ```
3. If `SESSION_LOG` is a session note (fileClass:session), update its frontmatter:
   ```bash
   obsidian property:set name="status" value="Done" path="$SESSION_LOG"
   obsidian property:set name="end" value="YYYY-MM-DDTHH:mm:00" path="$SESSION_LOG"
   ```
   Skip frontmatter updates for daily notes (fileClass:journal).
4. Report the closed session path, then clear `SESSION_LOG`.

---

**If the argument is `recap`:**

1. Read the most recent Claude Code `/recap` output from the current conversation context.
2. Format the recap as bullet points.
3. Append the bullets under the current open `log::` entry in SESSION_LOG:
   ```bash
   obsidian append path="$SESSION_LOG" content="\n- BULLET_1\n- BULLET_2"
   ```
4. Show the user the appended bullets and offer to edit any of them before they are finalized.

If SESSION_LOG is not set, inform the user that no session is active and suggest running `/session-log start` first.

---

**If no argument is provided:**

Ask the user what they'd like to do:
- **start** — begin a new session log (daily note, or project session note)
- **end** — close the current session log
- **recap** — append the latest recap as bullets in the open log

Then execute the appropriate workflow above.
