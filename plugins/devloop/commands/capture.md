---
description: Capture an idea or bug into the repo's INBOX without breaking stride
argument-hint: <the idea or bug, in your own words>
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/devloop/scripts/devloop.py:*), Read
---

Capture this into the inbox, then get straight back to what we were doing:

$ARGUMENTS

Run `"${CLAUDE_PLUGIN_ROOT}"/skills/devloop/scripts/devloop.py capture "<text>"` with
the text above, lightly cleaned up: fix obvious typos and expand shorthand into a
sentence a reader will still understand in six months. Do **not** editorialize,
reword the substance, or add analysis; the user's phrasing is the record.

- **Do not triage.** Don't decide where it belongs, check for duplicates, open the
  backlog or plan, investigate, or propose a fix. Triage is a separate pass; mixing
  it into capture makes capture expensive enough to skip.
- **Do not commit by hand.** The script commits the inbox alone; if it says it
  couldn't, commit that one file by itself.
- If it looks like an existing Open line, capture it anyway and mention the overlap
  in one sentence.
- Confirm in one line what was captured. Nothing more — the user is mid-task.

If `$ARGUMENTS` is empty, ask what to capture in one short question.
