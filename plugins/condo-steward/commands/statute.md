---
description: Look up what Florida law says on a community-association topic (reserves, records, meetings, elections, assessments, fines, SIRS) with the professional to confirm it
argument-hint: <topic>
allowed-tools: Read, Glob, Grep, WebFetch
---

## Procedure

Arguments: `$ARGUMENTS`

1. Determine the association type: `community.toml → type` if present (condominium → Ch. 718, hoa → Ch. 720, cooperative → treat as 718). If unknown, ask — the answer differs.
2. Read the relevant section of the matching file under `${CLAUDE_PLUGIN_ROOT}/skills/condo-steward/references/florida/`:
   - governance, records, budgets, assessments, fines, meetings, elections → `ch718-condominiums.md` or `ch720-hoa.md`
   - structural reserves, inspections, 3+ story buildings → `sirs-milestone-inspections.md`
   - reserve math, year-end report contents → `fac-61b-financial-reporting.md`
3. Answer in this order:
   - the operative rule, with section number and the concrete thresholds (days, dollars, vote fraction);
   - how it applies to this community if numbers or facts are at hand (revenue tier, delinquency, building height);
   - what the community's own declaration/bylaws might change — say plainly if you have not seen them;
   - which professional must confirm before acting, and why (per `references/professional-escalation.md`).
4. Close with the "as of" date from the reference file and the official link (<https://www.leg.state.fl.us/statutes/>). If the topic is one the Legislature changed recently (reserves, SIRS, records website, board education, fines), say so explicitly and offer to fetch the current text.

Keep it to the question asked. Do not draft notices, liens, or fine letters — offer to outline the required contents for the attorney instead.
