# Archivist guards its roles itself, in any harness

Status: in progress. Decisions made 2026-11-10 and 2026-11-15 (§ Decisions); upstream review 2026-11-15 (§ Upstream alignment). Task 1 done (2026-11-11); tasks 2–5 open. Branch `feature/pi-agents` (uncommitted work, see § What happens to the branch).
Issue: [#258](https://github.com/totallyGreg/claude-mp/issues/258).
Builds on: `2026-10-18-001-feat-archivist-role-split-plan.md` (#175), `2026-10-16-001-feat-archivist-vault-write-plan.md`.

## Goal

The archivist's agents run in Pi as well as Claude Code, with exactly the permissions their role needs to do the work, and nothing that can break the vault.

"Breaking the vault" includes edits Obsidian doesn't know about. A file changed behind Obsidian's back (a heredoc, `sed`, a raw file write that renames or moves a note) skips Obsidian's automatic link updates, which leaves dangling links. So **the right tool is part of the permission**:

- Note writes go through `vault-write`.
- Anything Obsidian must track (rename, move, delete, properties, links) goes through the `obsidian` CLI.
- Nothing else.

## Design constraint: one archivist, thin harness adapters

The archivist is the vault's arbiter in every harness. Claude Code and Pi must understand it the same way, by reading the same files, not by keeping their own copies.

| Layer | Lives in | Written once? |
|---|---|---|
| **Teaches:** agents, skills, references, vault profile | `agents/*.md`, `skills/`, `_vault-profile.md`, `local.md` | Yes. Pi agents are *generated* from `agents/*.md` (`pi_agents.py`) and load the same skills |
| **Decides:** zones, roles, merge preservation, audit | `bin/vault-write`, `hooks/*.py`, `check_merge_preserved.py` | Yes. Both harnesses call this code |
| **Translates:** a harness's tool call → the code above, with the role set | Claude Code: `hooks/hooks.json`. Pi: `pi/extensions/*.ts` | One adapter per harness, no logic in it |

**Rule:** anything that decides or teaches lives once in the archivist. An adapter may only translate a tool call and set the role. Vault knowledge or a policy check written in `pi/`, in `pi_agents.py` or in TypeScript belongs in the archivist instead.

What this means for this plan:
- Tasks 2 and 4 are archivist work, not Pi work. Claude's archivist agents get the same shell policy and audit.
- Only task 3 is Pi-specific, and it makes the Pi adapter *smaller*. It removes the `vault_write`/`vault_stat` extension tools, which give `vault-write` a second interface that the skills don't teach, and the "No shell" / "extension tools" lines of the generated "Running in Pi" note.
- `pi_agents.py` stays in local-inference: it converts any plugin's agents and holds no archivist logic.
- The "Running in Pi" note may only list what Pi lacks. It never restates archivist instructions.

## Problem

The curator/architect split is enforced by Claude Code hooks, not by the archivist:

- `bin/vault-write` doesn't know who calls it. It checks every write against the **union** of all zone keys, so a curator can write `900 📐Templates` through it.
- The role exists only in `hooks/vault_file_guard.py` and `hooks/obsidian_guard.py` (`agent_type`), and only where Claude Code runs them.

Evidence from running the archivist in Pi on a local model (2026-11-10, sandbox copy of the vault):

| Run | What happened |
|---|---|
| Pi + vault-curator skill, file tools only | Merge done in 74 s; edited the canvas the Claude archivist was barred from; silently reworded one line ("AI services" → "LLM services") |
| Pi archivist subagent + guard extension (`pi/extensions/guard.ts`) | Guard decisions matched Claude's; the merge check refused 5 drafts that dropped text. vault-write needed a `base` hash Pi couldn't get, so the agent worked around it with a new note, then hung on `contact_supervisor` |
| Same, with `vault_stat` added | After the archivist's writes were refused, the **parent** session delegated to pi-subagents' builtin `worker` (bash, no guard): heredoc over the note, `sed` on the canvas, a typo ("vLLV"), a report claiming success |

## Decisions (2026-11-10)

1. **Curator zones:** the curator writes only to the zones the profile marks as curator zones (`curator_write_zones`, plus `designated_output_zones`). It never writes to architect zones.
2. **No MCP server.** The `obsidian` CLI stays the agents' tool for vault operations, as decided in #175, with `vault-write` for note content.
3. **The aim** is the archivist's agents running in a Pi harness with the permissions their work needs, without breaking anything. It is not about guarding the user's own sessions.
4. **Bash in the vault is blocked**, except the two guarded tools (`obsidian`, `vault-write`). Using the right tool with the right permissions is the point.

## Decisions (2026-11-15), for task 2

5. **"In the vault"** means the working directory is inside the vault, or any argument or redirection target resolves inside it. The working directory matters for Pi, which may be launched from the vault.
6. **The archivist's own scripts are allowed** alongside `obsidian` and `vault-write`: a command that runs a script under the archivist plugin dir (e.g. `merge_notes.py`, `redirect_links.py`, `generate_canvas.py`). Those scripts already write only through `vault-write` (`test_scripts_write_path.py`), and the guard passes the role to them.
7. **Read-only shell commands in the vault are denied** too (`cat`, `grep`, `ls` on vault paths): reads go through the harness's own read/grep/find tools, or `obsidian` read commands, as § 1 says. Stricter, but one rule with no list of "safe" commands to maintain.
8. **Delete asks** (§ 1), instead of today's deny. In Pi it still blocks, because a subagent has nobody to answer.

## Upstream alignment (obsidian-skills 1.2.0, Obsidian CLI 1.15.1; reviewed 2026-11-15)

The pattern is upstream's own. The `obsidian-cli` skill says to use `rename`/`move`, not `mv` or `eval`, so Obsidian updates links. It also says `content=` corrupts backslashes and shouldn't carry more than ~4 KB, so a note body should be written to the file directly. That split is § 1: the CLI for what Obsidian tracks, `vault-write` (the guarded direct write, which upstream has no equivalent of) for bodies. The references were refreshed to match (`cli-patterns.md`, `bases-query-reference.md`; branch `bugfix/archivist-cli-refresh`). What it adds to this plan:

- **Plugin-registered write commands bypass the zone check today**, in Claude Code too. `obsidian_guard.py` zone-checks only `create`/`append`/`prepend`/`property:*`/task updates. `templater:create-from-template file=…` and the QuickAdd commands need only `vault=` first. Task 2 zone-checks `file=` and a QuickAdd `vars.path` (how `logEntries` is told its target), for every caller. A QuickAdd run without `vars.path` asks: the choice decides where it writes, and for `quickadd:run-template` `path=` is the template, not the output.
- **The sandbox blocks the CLI.** The `obsidian` CLI talks to the app over a unix socket, and `agent_sandbox.sh` allows none. A Pi archivist under `pi_sandboxed.sh` can't run `obsidian`. Task 3 runs the Pi archivist **outside** the sandbox, with the guard as its boundary (it never needs the sandbox's build/test freedom), unless the parity test shows a reason to open the socket instead.
- **`move`/`rename` can block on a dialog** when Settings → Files and links → *Automatically update internal links* is off (`alwaysUpdateLinks` missing or false in `.obsidian/app.json`). An agent, or a Pi subagent, hangs. `move`/`rename` already ask, so the guard adds that warning to the reason when the setting is off; in Pi the ask blocks.
- **Rule for choosing the tool**, already in `cli-patterns.md`: CLI for properties, move/rename/delete, Templater/QuickAdd creation and short appends without backslashes; `vault-write` for any body, section, merge, or content with backslashes or over ~4 KB. `vault-write` must not grow CLI features.

## Design

### 1. Role policy, in the archivist's code

| Operation | Tool | curator | architect |
|---|---|---|---|
| read, search, backlinks, Bases queries | harness read/grep/find; `obsidian` read commands | yes | yes |
| hash and zone of a note | `vault-write stat` | yes | yes |
| write note content | `vault-write apply` | curator zones + output zones | architect zones (folder notes in content zones too, per #175) |
| properties, rename, move, links | `obsidian` CLI write commands | curator zones | architect zones |
| merge, redirect links, canvas generation | curator scripts → vault-write | yes, curator zones | — (curator's job) |
| delete a note | `obsidian` CLI to Obsidian's trash | asks the user | asks the user |
| any other shell command, or a raw file write in the vault | — | **no** | **no** (architect Edit/Write only inside architect zones) |

The zones stay in `local.md`. The new part is the mapping from role to zone keys, held next to `ZONE_KEYS` in `bin/vault-write`. Both guard hooks import it, so the rules exist once.

### 2. vault-write knows the role

- `--role curator|architect` on `apply` and `force`, defaulting to `ARCHIVIST_ROLE`. With neither set, the curator's rules apply, the narrower of the two.
- Zone check per role (§ 1). A refusal names the role and its zones.
- `apply --merged-from <note>...` runs `check_merge_preserved.py` first and refuses a merge that drops or rewords source text.
- The curator scripts (`merge_notes.py`, `redirect_links.py`, `generate_canvas.py`) pass the role through `_vault_write.py`.

### 3. The guards decide by role, and each harness runs them

The guards are the existing Python files, made role-aware. A harness's job is only to call them and pass the role:

- **`obsidian_guard.py` (shell commands).** In the vault, a command is allowed only if it is an `obsidian` or `vault-write` call.
  - `obsidian` write commands are checked against the role's zones; delete asks.
  - `vault-write` gets the role's `--role` added or checked.
  - Everything else is denied, including pipes and redirections that write files.
- **`vault_file_guard.py` (Edit/Write):** the architect inside architect zones is allowed; everything else in the vault is denied for archivist roles (use vault-write).
- **Claude Code:** unchanged wiring (`hooks/hooks.json`). `agent_type` gives the role.
- **Pi:** one small extension, `archivist/pi/extensions/guard.ts`, which the generated archivist agents load.
  - On `tool_call` for `bash`, `edit` or `write`, it sends the call to the same two Python guards with the agent's role, and blocks on deny. Pi has no prompts in a subagent, so "ask" blocks too, with the reason.
  - No zone logic in TypeScript.

### 4. Agents that can't route around the archivist

- The generated Pi agents (`pi_agents.py`) set `allowedAgents` to the archivist's own agents only. A Pi archivist run is started as the `archivist` agent itself (`pi --agent`-style launch, or a parent whose only delegate is `archivist`), never from a general parent that can fall back to the builtin `worker`.
- `disableBuiltins` (or `agentOverrides.worker.disabled`) in the Pi project settings of the vault removes the builtin `worker`/`scout` there, so nothing in a vault session has unguarded bash.
- The curator → architect handoff stays: Claude's Agent tool; Pi's nested `subagent` limited to `archivist-architect`.

### 5. Detection: `vault-write audit`

- Every vault-write write appends to a ledger (path, role, hash before and after, time) in `${XDG_STATE_HOME:-~/.local/state}/archivist/ledger.jsonl`. `obsidian` CLI writes are recorded by the guard.
- `vault-write audit --since <time>` lists vault files changed since then (git working tree and commits) that no ledger entry explains.
- It runs after every agent run and in the health check. It is how a bypass in any harness gets found, as the `worker` heredoc would have been.

## What happens to the branch (`feature/pi-agents`, uncommitted)

| File | Fate |
|---|---|
| `check_merge_preserved.py` + its test | Keep; vault-write calls it (§ 2) |
| `pi/extensions/guard.ts` (+ role entry files) | Keep and extend: add `bash` → `obsidian_guard.py`; drop `vault_write`/`vault_stat` tools once bash allows the two guarded CLIs |
| `pi_agents.py` | Keep; Bash maps to Pi `bash` (guarded) instead of being dropped; `allowedAgents` only the plugin's agents |
| vault-curator docs (protocol rule 6, SKILL merge step, available-scripts) | Keep; point at `vault-write --merged-from` |
| local-inference SKILL "Plugin agents as Pi subagents" | Keep; reword once the guard lands |

## Tasks

1. **Done (b336c16).** Role policy + role-aware `vault-write` (`--role`, per-role zones, `--merged-from`), with tests both ways: curator refused in architect zones, and the reverse.
2. **Done (2026-11-15).** Role-aware `obsidian_guard.py`:
   - **Archivist roles:** only `obsidian`, `vault-write` and the archivist's own scripts in the vault (decisions 5–7); zones from `vault-write`'s `role_zones()`; `--role` or `ARCHIVIST_ROLE=` naming another role denied (checked, not added: vault-write's default is the narrower curator); `$(…)`/backticks and unexpandable variables denied; delete asks, `permanent` denied.
   - **Every caller:** `templater:create-from-template file=` and QuickAdd `vars.path` zone-checked, other QuickAdd runs ask; `move`/`rename` warn when `alwaysUpdateLinks` is off; quoted heredoc bodies are text, not commands, unless fed to a shell or interpreter.
   - **Known limit:** code that builds a vault path at run time (`python3 -c` with `os.path.join`) isn't seen; task 4's audit catches it.
   - Tests both ways (60 new; 254 pass), plus every documented archivist command checked against the real config. vault-architect's setup steps moved from `cat`/`ls`/`grep` on the vault to the read tools and `plugins:enabled`; the curator's delete step from `rm` to `obsidian delete`.
3. **Done (2026-11-15).** Pi extension:
   - `guard.ts` replaces Pi's `bash` with one that sends each command to `obsidian_guard.py` (role as `agent_type`, Pi's `cwd`) inside `execute`, so the checked command is the one that runs. Its `spawnHook` gives commands what Claude Code gives a plugin's Bash: `CLAUDE_PLUGIN_ROOT`, `bin/` on PATH, and `ARCHIVIST_ROLE`. `edit`/`write` still go to `vault_file_guard.py`. Ask blocks, with a "stop and report" reason.
   - `vault_write`/`vault_stat` dropped. (The old `vault_write` never passed `--role`, so the Pi architect wrote as the curator.)
   - `pi_agents.py` maps Bash to `bash` only when the agent's extension adds a guarded one; 3 tests. local-inference SKILL: run the archivist outside `pi_sandboxed.sh`; disable builtins in the vault.
   - Checked by loading `guard.ts` through jiti against Pi 1.5.2's `createBashTool`, both roles, real config: same decisions as Claude Code; env present.
   - The vault's `.pi/settings.json` sets `{"subagents": {"disableBuiltins": true}}` (created 2026-11-15, with the user's approval). A live Pi run on the local model is task 5.
4. Ledger + `vault-write audit`, with a test that a direct file write shows up and a vault-write write doesn't.
5. Parity test: the same consolidation on the sandbox vault in Claude Code and in Pi. It passes when:
   - the merged note passes `check_merge_preserved.py`;
   - the canvas write (outside curator zones) is refused in both harnesses;
   - a deliberate `sed`/heredoc bypass is denied in both;
   - `vault-write audit` is clean after each run.

## Verification

- Unit tests: vault-write roles, the obsidian guard's command allowlist, the audit, the merge check.
- `claude plugin validate --strict`; agentsmith on both agents; skillsmith on vault-curator, vault-architect and local-inference.
- The parity test (task 5).
