---
name: Handoff Payload Schema
description: The 8-section Markdown structure for handoff payloads — what each section is for, how to populate it, and what to leave out.
load_when: Building a handoff payload (any transport); reviewing a received handoff for completeness; defining a custom schema variant for a domain-specific agent.
---

# Handoff Payload Schema

Every handoff — clipboard, file, tmux, or SendMessage — uses this 8-section Markdown structure. Sections appear in order. Omit optional sections only when genuinely empty (don't leave stubs).

## Why a schema at all

The receiver should be able to pick up productively without asking "what's going on" or "what have you tried." A consistent schema means:
- Receivers know where to look for what they need (Next steps for action, Decisions made for context)
- Senders have a checklist (forces explicit "what's blocked" / "what's settled" thinking)
- Schema-aware agents (archivist, attache) can extract specific sections programmatically

## The 8 sections

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

### 4. Open questions (optional)

Things the sender genuinely couldn't resolve and is handing over. Distinct from "Blocked" — these are decisions the receiver should make, not external waits.

```markdown
- Should the slash command default to opening $EDITOR for review, or send immediately?
- For multi-pane tmux:auto matches, prompt the user or always pick first?
```

### 5. Next steps (required)

**Ordered list.** Concrete, executable. The receiver should know exactly what to do first.

```markdown
1. Finish writing SKILL.md (in progress, see plugins/handoff/skills/handoff/)
2. Write payload-schema.md and tmux-targeting.md references
3. Run skillsmith evaluator; fix any score <85
4. Add plugin to marketplace.json; run sync
5. Commit + push
```

### 6. Quick-start commands (optional)

Commands the receiver can run immediately to inspect current state without spelunking. Especially valuable when the receiver is a fresh Claude with no session history.

```bash
git -C /Users/gregwilliams/Documents/Projects/claude-mp log --oneline -5
gh issue view 175
ls plugins/handoff/
```

### 7. Artifact references (optional)

File paths, URLs, commit SHAs, task IDs. **Links, never inline copies** — the receiver can read the source of truth.

```markdown
- Plan: /Users/gregwilliams/.claude/plans/plugins-archivist-take-a-look-replicated-quokka.md
- Issue: https://github.com/totallyGreg/claude-mp/issues/175
- Plugin manifest: plugins/handoff/.claude-plugin/plugin.json
- Latest commit: 305fa10
```

### 8. Receiver notes (optional)

Recipient-specific context. Set when the receiver is a known agent type and there's setup it needs to do.

```markdown
- You are archivist. Vault path is in ~/.claude/plugins/cache/totally-tools/archivist/1.26.0/.local.md
- The session log is open at <vault>/200 Daily/2026-06-04.md — append the handoff outcome there
```

## Anti-patterns

**Inline transcripts.** Do not paste large chunks of prior conversation. Use Artifact references to point at session files or `gh` commands. The point of handoff is summary, not replay.

**Empty stubs.** Omitting an optional section is better than `## Open questions\n\n_None._` Lower noise, higher signal.

**Implicit context.** Don't assume the receiver shares your jargon, paths, or aliases. If the project nickname is "claude-mp," say so once in Receiver notes or Goal.

**Mixing decisions with state.** "Decisions made" is for rejected alternatives. "Current state" is for what is. Don't conflate.

**Forgetting Quick-start commands when the receiver is in a different tmux pane.** That receiver has no shared context — Quick-start is the bridge.

## Schema extensions

The 8-section structure is the contract. Domain agents may add their own subsections within a section (e.g., archivist might add a "Vault context" subsection under Receiver notes), but the top-level 8 stay stable so consumers can rely on them.
