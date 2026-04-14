---
name: workflows
description: Show Known Workflows and Workflow Candidates tables from the vault profile.
---

Invoke the archivist agent to display vault workflow intelligence from `_vault-profile.md`.

The agent should:
1. Initialize normally (load skills, discover vault, load `_vault-profile.md`)
2. Based on what is found in `_vault-profile.md`:

   **If the file exists and contains workflow tables:**
   - Extract and present the `## Known Workflows` table (named workflows with call counts, avg steps, last called date)
   - Extract and present the `## Workflow Candidates` table (novel requests not yet named)
   - Remind the user: candidates with 2+ occurrences can be promoted — offer to run the promotion workflow if any qualify

   **If `_vault-profile.md` is absent:**
   - Explain that vault profiling hasn't run yet and the workflow tables will be empty until it does
   - Offer to run vault profiling now to initialize the profile

   **If `_vault-profile.md` exists but has no workflow tables:**
   - Report that the tables are empty (common on a freshly profiled vault)
   - Explain that tables populate as workflows are used in sessions
   - Offer to run a workflow now to seed the Known Workflows table
