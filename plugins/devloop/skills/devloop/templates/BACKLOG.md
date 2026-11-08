# {{project}} — Backlog

**This file owns:** everything that could be worked on and isn't a
specified stage yet — bugs, improvements, blocked items and open questions
— plus **Now**, the handful of things the current session is for.
**Do not put here:** the stage queue ([{{plan}}]({{plan}})); raw captures
([{{inbox}}]({{inbox}})); what was fixed (the commit that fixed it).

**§ Work grammar** (the devloop loop check, so the gate): one line per
item, detail in `{{backlog_dir}}/<slug>.md`. Groups run by priority, then
oldest first, and so do their items — nothing old sinks.

    ### <Group> — P<n> · since <oldest item's date>
    - **P<n>** bug|improvement `<Area, Area>` · <date first seen> · **Title** — sentence. <optional ↗ link>

Reviewed: {{today}}

## Now

Three at most, from the top of `devloop rank`; one may be an **Itch**.

## Work

## Verify

A check no automated test can do, one line each, oldest first, saying why:

    - **Subject** · <date added> · what to check — no test: <why>.

## Blocked

Re-read every review. A row leaves by being unblocked, split, or dropped
with a reason — never by sitting.

| Item | Blocked on | What would unblock it | Last checked |
|------|-----------|----------------------|--------------|

## Questions
