# Handoff Payload Schema

## When to load this

Building any handoff payload (any transport); reviewing a received handoff for completeness; defining a custom schema variant for a domain-specific agent.

## Why a schema at all

The receiver should be able to pick up productively without asking "what's going on" or "what have you tried." A consistent schema means:
- Receivers know where to look for what they need (Next steps for action, Decisions made for context)
- Senders have a checklist (forces explicit "what's blocked" / "what's settled" thinking)
- Schema-aware agents (archivist, attache) can extract specific sections programmatically

## The structure

Four required sections appear in order, followed by an optional free-form "Additional context" section. Omit the optional section entirely when there's nothing useful to add — do not write empty stubs.

### 1. Goal (required)

**One sentence.** What is the receiver being asked to do or continue?

Good: *"Continue the v2.0 design conversation for the archivist plugin — finalize the four open design questions and write a kickoff plan for alpha.1."*

Bad: *"Help with archivist."* (vague — what specifically?)

Bad: *"Continue."* (no scope — continue what?)

### 2. Current state (required)

**5–15 bullets.** Snapshot of where things stand. Three categories worth covering when each applies:
- **Done**: what's completed and committed
- **In flight**: what's partially done — be specific about what's left
- **Blocked**: what's stuck and why

```markdown
- Done: v1.26.0 released and pushed (commits 409fa47, 2fc2300, 305fa10)
- Done: GitHub issue #175 created with full v2.0 design under archivist v2.0 milestone
- In flight: handoff plugin scaffolding (plugin.json + script done; SKILL.md in progress)
- Blocked: tmux-send in terminal-guru not yet implemented — v0.2 of handoff depends on it
```

### 3. Decisions made (required)

The choices the sender made — especially **rejected alternatives**. Prevents the receiver from relitigating settled questions.

```markdown
- Two-path delivery (SendMessage for teammates, tmux for separate processes) — rejected single-path file-only because SendMessage is more secure and lower-latency when available
- Plugin name `handoff` — rejected `relay` (less clear), `agent-comms` (overpromises)
- Markdown payload only for v0.1 — rejected JSON because no real consumer needs it yet
```

### 4. Next steps (required)

**Ordered list.** Concrete, executable. The receiver should know exactly what to do first.

```markdown
1. Finish writing SKILL.md (in progress, see plugins/handoff/skills/handoff/)
2. Write payload-schema.md and tmux-targeting.md references
3. Run skillsmith evaluator; fix any score <85
4. Add plugin to marketplace.json; run sync
5. Commit + push
```

### 5. Additional context (optional)

A single free-form section for whatever the receiver genuinely needs that doesn't fit the four required sections. Include only what's actually useful. Common contents (use the subheadings or skip them — whatever reads cleanest for this specific handoff):

**Quick-start commands** — what the receiver can run immediately to inspect state without spelunking:

```bash
git -C /Users/gregwilliams/Documents/Projects/claude-mp log --oneline -5
gh issue view 175
ls plugins/handoff/
```

**Artifact references** — file paths, URLs, commit SHAs, task IDs. Links, never inline copies:

```markdown
- Plan: /Users/gregwilliams/.claude/plans/plugins-archivist-take-a-look-replicated-quokka.md
- Issue: https://github.com/totallyGreg/claude-mp/issues/175
- Latest commit: 305fa10
```

**Open questions** — things the sender genuinely couldn't resolve and is handing over (distinct from "Blocked" — these are decisions for the receiver, not external waits):

```markdown
- Should the slash command default to opening $EDITOR for review, or send immediately?
```

**Receiver-specific context** — when the receiver is a known agent type and there's setup it needs to do:

```markdown
- You are archivist. Vault path is in ~/.claude/plugins/cache/totally-tools/archivist/1.26.0/.local.md
- The session log is open at <vault>/200 Daily/2026-06-04.md — append the handoff outcome there
```

Use what helps; omit what doesn't. If nothing here is genuinely useful, omit the whole section.

## Anti-patterns

**Inline transcripts.** Do not paste large chunks of prior conversation. Use artifact references to point at session files or `gh` commands. The point of handoff is summary, not replay.

**Empty stubs.** Omitting Additional context is better than `## Additional context\n\n_None._` Lower noise, higher signal.

**Implicit context.** Don't assume the receiver shares your jargon, paths, or aliases. If the project nickname is "claude-mp," say so once in Additional context or Goal.

**Mixing decisions with state.** "Decisions made" is for rejected alternatives. "Current state" is for what is. Don't conflate.

**Forgetting quick-start commands when the receiver is in a different tmux pane.** That receiver has no shared context — quick-start is the bridge. Surface them under Additional context.

## Schema extensions

The four required sections + Additional context structure is the contract. Domain agents may add their own subsections within Additional context (e.g., archivist might add a "Vault context" subsection), but the four required top-level sections stay stable so consumers can rely on them.
