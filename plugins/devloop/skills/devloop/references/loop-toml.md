# loop.toml reference

The one copy of every name, cap and list the checks read. Unset keys take
the defaults below. `devloop.py --config <path>` reads a loop.toml kept
outside a repository (or set `$DEVLOOP_CONFIG`), so the checks can run
against a repository they must not write to.

## Contents

- [Top level](#top-level)
- [docs](#docs)
- [loop and review_due](#loop-and-review_due)
- [software](#software)
- [Where state lives](#where-state-lives)
- [Adopting in an existing repository](#adopting-in-an-existing-repository)

## Top level

| Key | Default | Meaning |
|-----|---------|---------|
| `schema` | `1` | Grammar version the documents follow. A plugin that reads another schema refuses rather than misreads |
| `kind` | `"none"` | `"software"` adds the software profile |
| `tier` | `1` | 0: AGENTS + INBOX · 1: + BACKLOG, PLAN, DECISIONS, LOOP · 2: + review gate, evals |
| `main` | `"main"` | The integration branch |
| `gate` | `""` | The one command "done" needs green; named in prompts and AGENTS.md |
| `areas` | `[]` | What a change is about; the only copy. Never re-cut |

## docs

| Key | Default |
|-----|---------|
| `agents`, `loop`, `backlog`, `inbox`, `plan`, `decisions` | `AGENTS.md`, `LOOP.md`, `BACKLOG.md`, `INBOX.md`, `PLAN.md`, `DECISIONS.md` |
| `stages_dir`, `backlog_dir`, `decisions_dir` | `stages`, `backlog`, `decisions` |
| `cap_bytes` | `20000` — every Markdown file's cap unless `caps` names it |
| `caps` | `{BACKLOG.md = 30000, PLAN.md = 24000, DECISIONS.md = 40000}`; `0` exempts. Setting it replaces the whole table |
| `exclude` | `[]` — globs the doc check skips (`.claude/*`, `node_modules` always) |
| `stage_terminal` | `shipped, superseded, deferred, won't fix, reference` |
| `area_exempt` | `[]` — stage files that aren't stages (reference notes) |

## loop and review_due

| Key | Default | Meaning |
|-----|---------|---------|
| `loop.max_now` | `3` | Items allowed in § Now |
| `loop.max_blocked_age_days` | `14` | A Blocked row older than this fails |
| `loop.backlog_pressure` | `0.6` | Share of BACKLOG's cap at which bug groups lead the ranking |
| `loop.placement` | `false` | A stage in Now needs a `**Placement:**` line |
| `review_due.max_age_days` | `7` | Days since the last review |
| `review_due.max_inbox` | `5` | Open captures |
| `review_due.release_tags` | `"v[0-9]*"` | `git describe --match` pattern for releases |

## software

| Key | Default | Meaning |
|-----|---------|---------|
| `bugfix_prefix` | `"bugfix/"` | Branches red-first and backlog-closed check |
| `tests` | `["tests/"]` | Path prefixes that are test files |
| `build` | `""` | Optional build before tests; `{scratch}` = a build dir outside the repo |
| `test` | `""` | Test command, run in a worktree; `{files}` or `{target}` and `{scratch}`. Empty: red-first checks shape only |
| `target_pattern` | `""` | Regex whose group 1 names a target, for `{target}` |
| `review_lines` | `150` | Changed code lines that make a review due |
| `review_code` | `[]` | Globs counted as code (tests never count) |
| `review_risk_paths` | `[]` | Path prefixes that always need review |
| `review_risk_content` | `[]` | Regexes; a changed code file matching one needs review |
| `evals_cases` | `"evals/cases.json"` | The case file |
| `evals_overlay` | `[]` | Configuration laid over old code (loop.toml always) |
| `evals_prose` | `[]` | Agent-facing prose whose change makes evals due |
| `evals_threshold` | `60` | Changed prose lines that make evals due |
| `evals_allowed_tools` | built-in list | The eval agent's `--allowedTools` |
| `evals_skip_arg` | `""` | How a case's `skip.pattern` reaches the test command |

## Where state lives

Outside the working tree, in `$XDG_CACHE_HOME/devloop/<repo>/` (default
`~/.cache/devloop/<repo>/`): `red-first/` worktree and build, `reviews/<tip>.md`,
`evals/<stamp>/` and `evals/results.jsonl`. Never in the repository, where a
project's own build scratch goes: an eval worktree there once landed inside
its own build directory.

`git config devloop.root` (per clone, not committed) points at the plugin so
git hooks and the gate can find the checks outside a Claude session. Init sets
it; the SessionStart hook refreshes it after a plugin update.

## Adopting in an existing repository

1. Write `loop.toml` by hand or with `/devloop-init`; init keeps every existing
   document. Name your existing files under `[docs]` instead of renaming them.
2. Put the Areas in `areas` and delete any other copy (a LOOP.md table, a
   script constant); the checks read only loop.toml.
3. Run `devloop.py --config <outside>/loop.toml check` first if the repository
   isn't yours to change yet, then move the file in.
4. Replace the repository's own copies of the checks with `devloop.py check` in
   its gate, in one commit, once the outputs match.
