---
name: duplicates
description: Find similar or duplicate notes within a scope and guide consolidation — merge, alias, or create MOCs.
---

Invoke the archivist agent to find and consolidate duplicate notes.

The agent should:
1. Initialize normally (load skills, discover vault, ensure `_vault-profile.md` exists)
2. Run scope selection — ask the user which directory to scan
3. Run duplicate detection:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/find_similar_notes.py \
     ${VAULT_PATH} --scope "${SCOPE}"
   ```
4. Present groups by tier (Tier 1: identical titles first, then Tier 2: similar titles)
5. For each group, ask the user: merge / create MOC / mark aliases / skip
6. Execute chosen action with git checkpoint and dry-run first
