---
name: collection
description: Scaffold a new collection folder or audit an existing one — folder note, Bases view, Templater template, and member consistency.
argument-hint: "[folder-path]"
---

Invoke the archivist agent to set up or audit a collection.

The agent should:
1. Initialize (config + vault identity; read `_vault-profile.md` only if this workflow needs it)
2. If a folder path was given (`$ARGUMENTS`): audit it when it exists, offer to create it when it doesn't. Otherwise ask: "Create a new collection or audit an existing one?"
3. **New collection** — hand off to `archivist:archivist-architect` (New Collection Setup):
   - Check existing parts, design schema, create Bases file + folder note + Templater template
   - After setup, offer collection health check
4. **Audit existing** — route to vault-curator's Collection Health Check workflow:
   - Run: `bash uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/check_collection_health.py ${VAULT_PATH}`
   - Report health status per collection
   - Offer fixes for unhealthy collections (missing folder note, missing Bases embed, schema drift)
