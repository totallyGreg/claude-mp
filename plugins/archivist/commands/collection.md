---
name: collection
description: Scaffold a new collection folder or audit an existing one — folder note, Bases view, Templater template, and member consistency.
---

Invoke the archivist agent to set up or audit a collection.

The agent should:
1. Initialize normally (load skills, discover vault, ensure `_vault-profile.md` exists)
2. Ask the user: "Create a new collection or audit an existing one?"
3. **New collection** — route to vault-architect's New Collection Setup workflow:
   - Check existing parts, design schema, create Bases file + folder note + Templater template
   - After setup, offer collection health check
4. **Audit existing** — route to vault-curator's Collection Health Check workflow:
   - Run: `bash uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/check_collection_health.py ${VAULT_PATH}`
   - Report health status per collection
   - Offer fixes for unhealthy collections (missing folder note, missing Bases embed, schema drift)
