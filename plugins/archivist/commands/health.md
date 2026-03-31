---
name: health
description: Run a vault health snapshot — orphan count, collection health, schema drift signals, and top issues.
---

Invoke the archivist agent to run a vault health check.

The agent should:
1. Initialize normally (load skills, discover vault, ensure `_vault-profile.md` exists)
2. Run a comprehensive health snapshot:
   - Orphan count: `bash obsidian orphans`
   - Collection health: `bash uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/check_collection_health.py ${VAULT_PATH}`
   - Vault analysis: `bash uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-architect/scripts/analyze_vault.py ${VAULT_PATH}`
3. Summarize findings as a prioritized list of issues
4. Offer to fix the top issues or dive deeper into any area
