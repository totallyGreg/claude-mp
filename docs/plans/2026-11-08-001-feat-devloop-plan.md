# devloop: a development loop for any git repository agents work in

Status: built, 2026-11-08, on `feature/devloop` (devloop 0.1.0); not merged.
Issue: not filed. The draft is below, for the user to file.

Exploration and evidence: the vault brainstorm "AI-native SDLC vs
AudiobookOCD loop" (`800 Generated/820 Brainstorms/`). This plan is the
definition; the brainstorm is the history and is not updated to match.
Reference implementation, read-only: `~/Documents/Projects/AudiobookOCD`
(AGENTS.md, LOOP.md, `Scripts/`, `.githooks/`, `.claude/`, `evals/`;
commit bodies 282ab4e..fee218e say why each piece exists and what broke).

## Draft issue

**Title:** `devloop: new plugin — a capture-to-ship loop with checks, for any git repository agents work in`

**Body:**
- Package AudiobookOCD's development loop as a plugin, with a core and a `software` profile. The design is in docs/plans/2026-11-08-001-feat-devloop-plan.md.
- [ ] Core skill, `init`, `/capture`, `/review-backlog`
- [ ] Core checks (loop, ranking, review-due) reading `loop.toml`
- [ ] Hooks (no-blanket-add, SessionStart nudges)
- [ ] `software` profile (red-first, backlog-closed, review gate, evals)
- [ ] Adopted in two real repositories: one software, one not

## Scope (decided 2026-11-08; confirmed by the user before the build)

**For:** any git repository where agents do the work: code,
infrastructure, documentation.

**Not for:** life admin and tasks, which live in OmniFocus through
attache, or vault work, which goes through archivist. Git is what makes
the loop enforceable: diffs, commits as postmortems, hooks. Without a
repository, the rules turn back into prose.

**Shape:** a **core**, plus **profiles** switched on in `loop.toml`.
`software` is the only profile now. Others, such as infrastructure or
writing, wait until a second kind of repository has shown what it needs
(YAGNI). The seam exists from the start.

## Design rules

1. **Mechanism over prose.** Every rule that git or a script can check
   ships as a check or a hook. Prose carries only judgment and reasons.
2. **One always-loaded page.** AGENTS.md is the index, the commands, and
   one line per rule naming its enforcer. A size cap enforces it. The
   detail goes to on-demand documents listed in the index. A rule that
   must hold stays on the page or becomes a check: moving it out loses it
   (AudiobookOCD acf6a88 → 0ab0d04).
3. **The documents are the interface between agents and the person.**
   Each step of the loop ends in a committed file the next step reads.
4. **The commit is the postmortem.** No resolved-issues file.
5. **Evals guard only judgment.** Each eval finding becomes a
   deterministic check, so the eval set shrinks. They run on a large
   change to the agent-facing prose, never in the gate.
6. **A hook or nudge never fails a session start.** A check fails the
   gate. A due item nudges.
7. **Configuration, not copies.** Checks run from `${CLAUDE_PLUGIN_ROOT}`
   and read `loop.toml`. Nothing is copied into the repository except the
   documents it owns.

## Core (any repository)

| Component | Kind | From (AudiobookOCD) | Generalized by |
|---|---|---|---|
| The loop's procedures and reasons | skill | LOOP.md, AGENTS.md § The loop | Wording, without project specifics |
| `init` | skill or command | (none; new) | Asks for kind, gate command and Areas; writes the documents and `loop.toml` |
| `/capture` | command + script | `.claude/commands/capture.md`, `Scripts/capture.sh` | INBOX path from config |
| `/review-backlog` | command | `.claude/commands/review-backlog.md` | Document names from config |
| Loop check | script (gate) | `Scripts/check-loop.py` | Areas, caps and file names from config |
| Ranking | script | `Scripts/ranking.py` | As is |
| Review due | SessionStart nudge | `Scripts/review-due.py` | Thresholds from config |
| Doc index and size cap | script (gate) | `Scripts/check-docs.sh` (steps 4–5) | Caps from config; the Areas read once, from `loop.toml` |
| No blanket staging | PreToolUse hook | `Scripts/no-blanket-add.py` | As is |
| Dashboard | script, optional | `Scripts/dashboard.py`, `dashboard_view.py` | Tier 2 |

**Documents `init` writes:**
- AGENTS.md: one page, holding the index, the commands, rules with enforcers, the loop in one line per step;
- LOOP.md;
- BACKLOG.md: Now, Work groups, Blocked, Questions, Verify;
- INBOX.md;
- PLAN.md;
- DECISIONS.md with `decisions/`.

The grammars are the ones AudiobookOCD's `check-loop.py` enforces.

## `software` profile

| Component | Kind | From | Generalized by |
|---|---|---|---|
| Red first | script (gate) | `Scripts/check-red-first.py` | Test paths, build command and test command from config; the Swift calls become one example |
| Backlog closed | script (gate) | `Scripts/check-backlog-closed.py` | Branch prefix and item grammar from config |
| Review needed | script | `Scripts/review-needed.py` | Line limit, code globs and risk patterns from config |
| Review runner | script | `Scripts/review.sh` | As is (`claude -p` with read-only tools, findings saved by tip SHA) |
| Review gate | commit-msg hook | `.githooks/commit-msg` | Main branch name from config |
| Evals | script + case file | `Scripts/evals.py`, `evals/cases.json` | Overlay list, test runner and results path from config; the case format kept |
| Evals due | SessionStart nudge | `Scripts/evals-due.py` | Prose globs and threshold from config |

Leave these out; they're AudiobookOCD's: MetricKit and dSYMs, container
paths, mise `SCRATCH` naming, Swift and Xcode calls, the Areas list. Each
can appear as a commented example in the generated `loop.toml`.

## `loop.toml` (sketch; the build settles it)

```toml
kind = "software"            # profiles on top of the core: "software" | none
main = "main"
gate = "mise run gate"       # the one command "done" needs

[docs]                       # names, so an existing repository can keep its own
agents = "AGENTS.md"         # size cap below
loop = "LOOP.md"
backlog = "BACKLOG.md"
inbox = "INBOX.md"
plan = "PLAN.md"
cap_bytes = 20000

areas = ["Identity", "Sources", "..."]   # the one copy

[review_due]
max_age_days = 7
max_inbox = 5

[software]                   # only with kind = "software"
tests = ["Tests/"]
build = "swift build --build-tests"
test = "swift test --skip-build --filter {target}"
review_lines = 150
review_risk = ["replaceItemAt", "removeItem\\(at", "Models/"]
evals_prose = ["AGENTS.md", "LOOP.md", ".claude/commands"]
evals_threshold = 60
```

## Tiers (what `init` turns on)

- **0, any repository:** AGENTS.md, INBOX, `/capture`, the gate command, no-blanket-add.
- **1, multi-month work:** BACKLOG plus the loop check, ranking, review-due, PLAN, DECISIONS.
- **2, when it earns it:** the dashboard and the `software` profile's review gate and evals.

## Acceptance

1. The skillsmith evaluation passes with `--strict`, `mp-validate` passes, and the README carries the release record (WORKFLOW.md).
2. `init` in an empty scratch repository writes the documents and `loop.toml`, and every core check passes there. The output is shown, not described.
3. The checks pass against AudiobookOCD's own documents, given a `loop.toml` written for it. That proves the generalization is faithful, and AudiobookOCD can switch to the plugin later.
4. **Not part of this build:** adoption in a second, non-software repository (such as homestack-2026) proves the core is general. It's recorded as the next step.

## Not in scope

- Writing the infrastructure or writing profiles.
- Moving AudiobookOCD onto the plugin: a separate change in that repository.
- Changing archivist's or attache's task models.
- The Obsidian-versus-repository documentation drift. The rule for this plugin: the repository is the definition, and the vault links to it.
