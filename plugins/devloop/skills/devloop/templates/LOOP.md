# The development loop

How work moves from a capture to a shipped change, and how it is ranked.
{{agents}} carries the loop in one line; the devloop checks enforce this
file, and loop.toml holds the names, caps and Areas they read.

## Steps

| Step | What happens, and what changes hands |
|------|--------------------------------------|
| **Capture** | `/capture <text>` → [{{inbox}}]({{inbox}}) § Open, stamped with branch + SHA, committed alone. Never triage here |
| **Triage** | Each Open line → one [{{backlog}}]({{backlog}}) § Work item (into the group one branch would fix it with) or § Blocked / Questions, with a priority and an Area — or [{{decisions}}]({{decisions}}) § Rejected Ideas with the reason. Delete the line from the inbox. A move, not a document |
| **Review** | Due once a release ships, a week passes, or the inbox holds five captures — the session start says so until it's done. `/review-backlog`: verify each item against git and the code, delete what's fixed, regroup, re-rank, set `Reviewed:`, and hand the person only the decisions that are theirs |
| **Plan** | Rewrite § Now (three at most; one may be an **Itch**). Now #1 is the top of `devloop rank`, or says why not (`**Chosen** — <reason> —`). Re-read § Blocked: unblock, split, or drop with a reason |
| **Build** | **Done in one sitting:** a branch; the backlog line is the brief; delete the line in the commit that finishes it. **Handed off or spanning sessions:** a `{{stages_dir}}/s<N>-<slug>.md` brief (`**Status:**`, `**Area:**`, scope, gate, a `## Steps` checklist when it has more than one step) and a [{{plan}}]({{plan}}) row whose Why says why, never how far |
| **Ship** | `{{gate}}` green, the end-to-end check shown, not described. A finished step is ticked in its stage's `## Steps` in the commit that finishes it; the last box ticked means `**Status:** shipped`, the row out of the plan and out of Now, in the same commit. What no automated check can reach goes to § Verify, with why |
| **Compound** | A finding that changes another stage's premise → amend that stage in the same commit. A direction settled → a decision. A rule worth keeping → {{agents}}, one line naming its enforcer — a check, a hook, or the eval that guards it |

**Priority is what it costs to leave the item undone**, one scale for
everything: **P0** losing data or trust now · **P1** blocks something being
done now · **P2** needed, but workable around · **P3** polish, or
eventually. The plan's order stays the dependency sequence; priority says
how much it matters. Work finished from any list leaves that list in the
commit that finished it — a "done" note on a line is not done.

**The commit is the postmortem.** The title says what changed; the body
says what was actually wrong and how it was found. There is no
resolved-issues file.

**Prefer mechanism over prose.** A rule in a sentence gets missed; a check
that fails cannot be. Evals guard only judgment, and each finding they make
becomes a check.

## Areas

Every stage and backlog item carries Areas from loop.toml's `areas` — what
a change is *about*. Never re-cut; the checks reject an unknown one. Two or
more on one item is a signal the work is harder than it looks.
