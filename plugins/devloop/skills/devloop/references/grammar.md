# Document grammars, priority and ranking

The loop check (`devloop.py check --only loop`) enforces these. Each rule is
one that prose alone kept missing in AudiobookOCD, where it was built; the
reason is given so an agent can tell a rule's intent from its letter.

## Contents

- [The documents](#the-documents)
- [BACKLOG § Work](#backlog--work)
- [BACKLOG § Now](#backlog--now)
- [Verify, Blocked, Questions](#verify-blocked-questions)
- [PLAN and stages](#plan-and-stages)
- [INBOX](#inbox)
- [Priority](#priority)
- [Ranking](#ranking)
- [AGENTS.md](#agentsmd)

## The documents

| Document | Owns | Tier |
|----------|------|------|
| AGENTS.md | The index, the commands, one line per rule naming its enforcer | 0 |
| INBOX.md | Untriaged captures under `## Open` | 0 |
| BACKLOG.md | `Reviewed:`, § Now, § Work, § Verify, § Blocked, § Questions | 1 |
| `backlog/<slug>.md` | One item's detail, linked from its line, deleted with the fix | 1 |
| PLAN.md | § Remaining work: the ordered stage queue | 1 |
| `stages/s<N>-<slug>.md` | One stage's brief: `**Status:**`, `**Area:**`, `## Steps` | 1 |
| DECISIONS.md, `decisions/` | Decisions and rejected ideas; append-only | 1 |
| LOOP.md | The loop step by step, for people and agents | 1 |

**The commit is the postmortem**, so there is no resolved-issues file: what
was wrong and how it was found go in the fix's commit body.

## BACKLOG § Work

```
### <Group> — P<n> · since <YYYY-MM-DD>
- **P<n>** bug|improvement `Area, Area` · <YYYY-MM-DD> · **Title** — sentence. [↗](backlog/x.md)
```

- One line per item. Detail goes to `backlog/<slug>.md`; a continuation line
  fails. Paragraphs can't be ranked by a script or scanned by an agent.
- Every Area is in `loop.toml` `areas`.
- A group's heading carries its highest item priority and its oldest date.
- Groups run by priority, then oldest first; items inside likewise. An
  appended list buries whatever has waited longest under whatever was worked
  on last.
- A group is what one branch would fix: a shared file, cause or surface.

## BACKLOG § Now

- At most `loop.max_now` (3) numbered items; at most one `**Itch**`
  (something wanted for its own sake, named so it doesn't pose as the ranking).
- Now #1 names the top of `devloop.py rank` — a stage by its ID, a group by
  its bold `**Title**` — or starts `**Chosen** — <reason> —` or `**Itch** —`.
  One next suggestion, unless blockers, priority or choice reorganize it.
- A Now line naming a stage with `## Steps` names an open step: `S7 step 2`.
- `Reviewed: YYYY-MM-DD` sits above § Now; `/review-backlog` sets it.

## Verify, Blocked, Questions

- § Verify: `- **Subject** · <date> · what to check — no test: <why>.` One
  line each, oldest first. A check a test can do ships as a test instead.
- § Blocked: a table whose last column is the date last checked. A row older
  than `loop.max_blocked_age_days` fails: unblock it, split it, or drop it.
- § Questions: free-form, for the person.

## PLAN and stages

- PLAN § Remaining work is a table `| P | Area | Stage | Title | Why |`; the
  first column is P0–P3; the Stage cell links `[S7](stages/s7-x.md)`; a Why
  containing `**Blocked**` leaves the row out of the ranking.
- The Why says why the stage exists, never how far it has got. Progress lives
  in one place, the stage file's `## Steps`:
  `- [ ] 1. Title` / `- [x] 2. Title — <commit or version>`. Three copies of
  progress drifted apart the day a step merged.
- A Status line carries no step progress. All boxes ticked → `**Status:**
  shipped`, the PLAN row and Now item gone, in the same commit.
- Every stage file has `**Area:**` from `areas` (except `docs.area_exempt`).
- With `loop.placement = true`, a stage in Now has `**Placement:**` saying
  where its code goes, decided when the brief is read, not found at the gate.

## INBOX

Captures sit under `## Open`, newest first:
`- **YYYY-MM-DD** · `branch @sha` — text`. A struck (`~~`) or `**done**` line
fails: triage deletes the line, it doesn't annotate it.

## Priority

What it costs to leave the item undone; one scale for bugs, improvements and
stages. **P0** losing data or trust now · **P1** blocks something being done
now · **P2** needed, but workable around · **P3** polish, or eventually.
PLAN's order stays the dependency sequence; priority says how much it matters.

## Ranking

Candidates are PLAN's unblocked stages and § Work's groups. Order: priority;
within it stages first (in PLAN order), then groups oldest first. **Under
pressure** — BACKLOG at `loop.backlog_pressure` of its size cap — groups with
bugs lead their priority (most bugs, then most items), then stages, then
groups without bugs: with a stage always queued, bugs otherwise moved only
when someone overrode the ranking.

## AGENTS.md

The one page loaded every session. Index, commands, rules — each rule one
line naming its enforcer (a check, a hook, or the eval that guards it). Its
size cap (`docs.cap_bytes`) keeps it one page. A rule that must hold stays on
the page or becomes a check: moving it to an on-demand document loses it.
Every tracked Markdown file is listed here or in a sub-index (DECISIONS for
`decisions/`, BACKLOG for `backlog/`, PLAN or a terminal Status for `stages/`).
