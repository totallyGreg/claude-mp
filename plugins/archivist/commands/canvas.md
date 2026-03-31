---
name: canvas
description: Generate a knowledge map canvas for a scope — visualize notes and their connections as an Obsidian canvas file.
---

Invoke the archivist agent to generate a knowledge map canvas.

If an argument is provided, use it as the scope path directly (skip scope selection).

The agent should:
1. Initialize normally (load skills, discover vault, ensure `_vault-profile.md` exists)
2. Run scope selection (or use the provided argument as scope)
3. Generate canvas with dry-run first:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/vault-curator/scripts/generate_canvas.py \
     ${VAULT_PATH} --scope "${SCOPE}" --dry-run
   ```
4. Review node/edge counts with user
5. Execute (remove `--dry-run`) to write the `.canvas` file
6. Report canvas path and stats
