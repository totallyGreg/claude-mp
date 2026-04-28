---
name: agentsmith
description: This skill should be used when users ask to "evaluate my agent", "improve agent quality", "agent metrics", "check agent description", "agent isn't triggering", "validate agent", "agent score", "as-evaluate", "as-improve", "agent quality", "fix agent description", or "why isn't my agent triggering". Provides agent quality evaluation with 3 scored dimensions and an improvement loop that orchestrates skillsmith and marketplace-manager. Do NOT use for skill evaluation — route to skillsmith instead. Do NOT use for agent creation — route to plugin-dev:agent-development instead.
metadata:
  author: J. Greg Williams
  version: "1.0.0"
compatibility: Requires python3 and uv for script execution
license: MIT
---

# Agentsmith

Evaluate and improve agent quality with automated scoring across 3 dimensions.

Agentsmith **orchestrates** existing tools — delegating skill evaluation to skillsmith and version management to marketplace-manager — while adding the quality dimensions that no other tool covers: trigger effectiveness, system prompt quality, and description-body coherence. Structural validation is enforced by marketplace-manager's pre-commit hook at commit time.

## Agent Quality Routing

| Task | Use |
|------|-----|
| Creating agents (anatomy, writing, examples) | `plugin-dev:agent-development` |
| Agent structural validation (frontmatter fields) | marketplace-manager pre-commit hook |
| **Evaluating agent quality** | **agentsmith** (this skill) |
| **Improving agent quality** | **agentsmith** (this skill) |
| Evaluating skill quality | `skillsmith` |
| Improving skill quality | `/ss-improve` |

## Evaluation Dimensions

Three quality dimensions, weighted to produce an overall 0-100 score:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Trigger Effectiveness | 35% | Example count and variety, commentary presence, negative triggers, phrasing variety, description specificity |
| System Prompt Quality | 35% | Role specificity, concrete responsibilities, step-by-step process, quality standards, output format, edge cases, word count sweet spot (500-3,000), structural organization |
| Coherence | 30% | Description-body alignment, body-example coverage, tool scope fitness, terminology consistency |

## Commands

| Command | Purpose |
|---------|---------|
| `/as-evaluate <agent-path>` | One-shot quality evaluation with dimension scores |
| `/as-improve <agent-path>` | Full improvement loop: evaluate → fix → re-evaluate → version bump → sync |

## Improvement Loop (`/as-improve`)

1. **Verify target** — redirect skills to `/ss-improve`, non-agent files to plugin-dev
2. **Remap installed paths** — resolve `~/.claude/plugins/` paths to source repo via marketplace.json
3. **Evaluate** — run `evaluate_agent.py --explain`, report top-3 quality gaps
4. **Evaluate sibling skills** — if the plugin has skills, run skillsmith eval on each
5. **Apply improvements** — fix top-3 gaps, referencing `plugin-dev:agent-development` for guidance
6. **Re-evaluate** — confirm improvement, block if regression detected
7. **Update README** — add version history row to plugin README.md
8. **Version bump** — bump `plugin.json` (agents inherit plugin version)
9. **Sync marketplace** — invoke `sync.py` to update marketplace.json

## Agent File Patterns

| Pattern | Example | Detection |
|---------|---------|-----------|
| Flat | `agents/archivist.md` | Single `.md` file with `<example>` blocks in description |
| Directory | `agents/skill-observer/AGENT.md` | `AGENT.md` inside a named subdirectory |

## Delegation Principle

Agentsmith evaluates **quality** — the dimensions that no other tool covers. It does NOT replicate:
- Structural validation (frontmatter fields, name formats) → marketplace-manager pre-commit hook
- Skill evaluation → skillsmith
- Agent creation guidance → plugin-dev:agent-development
- Version cascade → marketplace-manager sync.py

See `references/agent-quality-rubric.md` for the full scoring rubric with sub-metrics.
