# Archivist role split (#175 alpha.2/3, bundles #224)

Decisions and evidence are recorded on #175 (cost spike results and the 2026-10-18 decisions comment).

## Shape

| Agent | Model | Tools | Writes |
|---|---|---|---|
| `archivist` (curator) | `claude-haiku-5-5` | Read, Grep, Glob, Bash, Agent, AskUserQuestion, SendMessage | `vault-write` and the guarded `obsidian` CLI only |
| `archivist-architect` | `claude-sonnet-5-5` | Read, Grep, Glob, Bash, Edit, Write, AskUserQuestion, SendMessage | Edit/Write inside any write zone (hook-enforced; folder notes live in content zones); `vault-write` |

- Each agent preloads its own skill via `skills:` instead of reading both SKILL.md files at startup.
- The curator hands templates, Bases, schemas and Vault Profiling to the architect as a nested subagent.
- `/vault` → curator. `/vault architect` → architect.
- The name `archivist` is kept, because attache, foundry and terminal-guru reference `archivist:archivist`.

## Enforcement (code, not prose)

1. **`obsidian_guard.py` (Bash):**
   - CLI writes need `vault=<name>`, where the name equals the config vault's folder name (Obsidian names a vault after its folder).
   - `base:create` → ask.
2. **New `vault_file_guard.py` (PreToolUse on Write|Edit|NotebookEdit)**, for a file inside the vault:
   - `agent_type == "archivist:archivist-architect"`: no decision inside the write zones (the same set `vault-write` uses); deny outside them.
   - Anything else, including the main thread: ask, with a pointer to the archivist and `vault-write`.
   - Files outside the vault: no decision.
3. **`vault-write`:**
   - `config` reports `vault_name`.
   - Non-markdown files skip the markdown lint.
   - `.canvas` must parse as JSON.

## Agent prompts

- **Lazy init.**
  - Always: `vault-write config`, then confirm `obsidian vault=<name> vault` reports the config's path (stop on mismatch).
  - Profile and Quick Vault Signals only when the task needs them. Batch signal commands into one Bash call.
- **Every CLI call passes `vault=<name>`.** Today's daily note comes from `daily:path`.
- **Drop the copies of skill workflows.** The skills already document them; the agents keep only routing, policy and handoffs.
- **Permissions setup check:** if Claude Code denies a `vault-write` or `obsidian` call, print the README's allow rules block and stop. The agent never edits settings.

## Out of scope

- Scripts that write directly (`redirect_links.py`, `merge_notes.py` without `--no-write`, `generate_canvas.py` without `--no-write`) bypass `vault-write` zones. That is pre-existing behaviour; track it separately.
- `.local.md` deprecation (alpha 2.0.0 final) and the optional local Pi reader tier.

## Verification

- Guard, file-guard and vault-write tests.
- `claude plugin validate --strict`.
- agentsmith on both agents; skillsmith on both skills.
- Headless smoke test with `--plugin-dir` against the real vault, read-only: curator narrow question + architect read-only question; confirm the curator has no Edit/Write.
