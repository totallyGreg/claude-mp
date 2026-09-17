---
description: Record a board or owner question in the community's private ledger, answer it, and promote generalizable answers back toward the skill
argument-hint: <question> | answer <id> | list | promote <id>
allowed-tools: Bash(uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/*), Read, Glob, AskUserQuestion
---

## Procedure

Arguments: `$ARGUMENTS`

The ledger lives in the community project (`questions/ledger.jsonl`, or `questions_file` in `community.toml`). It is private; nothing is written into the plugin.

1. **New question** (`/condo-steward:ask <question>`): first try to answer it — check `references/common-questions.md`, the statements, and the Florida references. Then record it regardless of outcome so the board keeps a memory:

   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/scripts/questions.py add "<question>" [--by <role>] [--tag <topic>]
   ```

   If you answered it, immediately record the answer (step 2). If not, leave it open and say what would be needed (a document, a professional, more data).

2. **Answer** (`/condo-steward:ask answer <id>`): record the answer with its sources (statement period, reference file and section, statute link). If the *question* would apply to any community, give its community-neutral form with `--general` — that is what makes it promotable:

   ```bash
   uv run …/questions.py answer <id> "<answer>" --source "<source>" [--source …] [--general "<neutral question>"]
   ```

3. **List** (`/condo-steward:ask list`): `questions.py list --open` (default) or `--generalizable` to see promotion candidates. Render the markdown table the script prints.

4. **Promote** (`/condo-steward:ask promote <id>`): `questions.py promote <id> --target common-questions|florida|friction`. The script only **prints** a candidate. Review it with the user, strip anything community-specific, and then either place it in the plugin repo yourself (if the user maintains the plugin) or hand it to `/foundry:ss-wtf` as a friction report. After placing, `questions.py mark <id> --promoted-to "<file#anchor>"`.

Account numbers are masked on the way into the ledger; owner names are not — do not put them in questions or answers.
