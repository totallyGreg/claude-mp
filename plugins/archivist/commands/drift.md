---
name: drift
description: Detect schema drift for a fileClass — find inconsistent properties, type mismatches, and naming issues across notes.
---

Invoke the archivist agent to run schema drift detection.

The agent should:
1. Initialize normally (load skills, discover vault, ensure `_vault-profile.md` exists)
2. Ask the user which fileClass to check (e.g., Meeting, Person, Project) and what scope to use
3. Run drift detection:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/detect_schema_drift.py \
     ${VAULT_PATH} --file-class <class> --scope "${SCOPE}"
   ```
4. Present the drift report — missing properties, type mismatches, naming issues
5. Offer to fix issues with user confirmation (batch property updates)
