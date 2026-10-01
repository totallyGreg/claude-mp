#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Claude Code Stop hook for a teammate session: don't end a turn without replying.

A local model often finishes a cross-session task, writes the answer in its own
transcript, and stops — the lead never sees it. This hook finds the latest
<cross-session-message> in the transcript (a prompt, or a task queued mid-turn)
and, if no SendMessage to a named session followed it, blocks the stop with an
instruction to send the reply. It blocks once per *task*: a second block for the
same task is skipped, so a model that still won't reply can't loop forever. (It
used to skip whenever stop_hook_active was set — once per turn — which let a task
queued mid-turn, after the guard had already fired for the previous one, go
unanswered: 09-30 long-session test, task 5.)

Installed only on teammate sessions, via `claude --settings` in claude_team.sh.
"""
import json
import re
import sys

event = json.load(sys.stdin)

rows = []
with open(event["transcript_path"]) as f:
    for line in f:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue

FROM_NAME = re.compile(r'<cross-session-message[^>]*from-name="([^"]+)"')


def task_sender(row: dict) -> str | None:
    """The from-name of a cross-session task carried by this row, if any."""
    texts = []
    if row.get("type") == "user":
        content = (row.get("message") or {}).get("content")
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, list):
            texts += [b.get("text", "") for b in content if b.get("type") == "text"]
    if row.get("type") == "attachment":
        attachment = row.get("attachment") or {}
        if attachment.get("type") == "queued_command":
            texts.append(str(attachment.get("prompt", "")))
    for text in texts:
        if m := FROM_NAME.search(text):
            return m.group(1)
    return None


last_task, sender = -1, None
for i, row in enumerate(rows):
    if name := task_sender(row):
        last_task, sender = i, name
if sender is None:
    sys.exit(0)

for row in rows[last_task + 1:]:
    if row.get("type") != "assistant":
        continue
    for block in (row.get("message") or {}).get("content") or []:
        if block.get("type") == "tool_use" and block.get("name") == "SendMessage":
            if (block.get("input") or {}).get("to") not in (None, "", "main"):
                sys.exit(0)

# Already blocked once for this task? Let it stop rather than loop.
for row in rows[last_task + 1:]:
    attachment = row.get("attachment") or {}
    if attachment.get("type") == "hook_blocking_error" and "You have not replied" in json.dumps(attachment):
        sys.exit(0)

print(json.dumps({
    "decision": "block",
    "reason": (
        f'You have not replied to "{sender}". Call the SendMessage tool now with '
        f'to="{sender}" and your result as the message. Text in your own transcript never '
        'reaches the lead.'
    ),
}))
