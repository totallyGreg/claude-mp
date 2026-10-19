---
name: vault
description: Start a PKM session with the archivist for your Obsidian vault — organizing notes, checking health, fixing metadata, finding duplicates, generating canvases, or designing templates and Bases (`/vault architect`).
argument-hint: "[architect] [what to work on]"
---

Arguments: `$ARGUMENTS`

- If the first word is `architect`, spawn the `archivist:archivist-architect` agent with the rest of the arguments as its task (templates, Bases, schemas, collections, vault profiling).
- Otherwise spawn the `archivist:archivist` agent (the curator). Tell it this is a `/vault` session, so it runs Quick Vault Signals. If arguments were given, they are what to work on; otherwise it surfaces the top 2–3 issues and asks what to focus on.

Relay the agent's result. Send follow-up vault work to the same agent with SendMessage.
