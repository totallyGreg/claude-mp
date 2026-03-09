---
description: Show and process OmniFocus inbox items
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/*)
---

<!--
/ofo:inbox - Show OmniFocus inbox items.
Fetches inbox count and items, presents each with a GTD clarify decision.
-->

Inbox items:
!`${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/ofo list inbox`

Present the inbox items above as a table: **Item | GTD Decision | Notes**

Apply the GTD clarify decision tree to each item:
- Actionable → Next Action (assign project) or Project (if multi-step)
- Not actionable → Someday/Maybe, Reference, or Trash

If inbox is empty, say: "Inbox is at zero. ✓"
