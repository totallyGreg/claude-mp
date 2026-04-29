# Agent Improvement Guide

How agentsmith delegates to plugin-dev for structural agent knowledge while focusing on quality evaluation.

## Delegation Model

Agentsmith is a thin quality wrapper — it measures agent effectiveness across 3 dimensions (trigger, prompt, coherence) but delegates all structural guidance to `plugin-dev:agent-development`. This separation keeps agentsmith focused on what no other tool covers.

| Concern | Owner | How |
|---------|-------|-----|
| Agent anatomy (frontmatter, tools, colors) | `plugin-dev:agent-development` | Structural best practices |
| Example block format and variety | agentsmith (Trigger dimension) | Scoring + coaching |
| System prompt quality | agentsmith (Prompt dimension) | Scoring + coaching |
| Description-body consistency | agentsmith (Coherence dimension) | Scoring + coaching |
| Frontmatter field validation | marketplace-manager hook | Pre-commit enforcement |

## Improvement Workflow

When `/as-improve` identifies quality gaps, the fix strategy depends on the dimension:

### Trigger Effectiveness Gaps

Low trigger scores usually mean:
- Too few `<example>` blocks (need 3+ with variety)
- Missing `<commentary>` explaining why the agent triggers
- No negative trigger clause ("Do NOT use for X")
- All examples use similar phrasing

For structural example writing guidance, invoke `plugin-dev:agent-development`.

### System Prompt Quality Gaps

Low prompt scores usually mean:
- No specific role definition in the opening paragraph
- Missing concrete responsibilities (need numbered/bulleted items)
- No step-by-step workflow documentation
- Missing quality constraints (MUST/NEVER/CRITICAL)
- Body too short (<200 words) or too long (>3000 words)

### Coherence Gaps

Low coherence scores usually mean:
- Description mentions capabilities the body doesn't cover
- Body sections have no corresponding examples
- Tools declared in frontmatter aren't referenced in the body
- Key terms drift between description and body

## Common Improvement Patterns

### Pattern: Thin Agent → Rich Agent

Starting point: minimal agent with 1-2 examples, short body, basic description.

1. Run `/as-evaluate` to identify weakest dimension
2. Add 2-3 diverse examples (explicit, proactive, edge-case types)
3. Expand body with concrete responsibilities and workflow steps
4. Add quality constraints and output format expectations
5. Re-evaluate to confirm improvement

### Pattern: Overtriggering Agent

Symptom: agent activates on unrelated queries.

1. Check trigger score — high example count but low specificity
2. Add negative trigger clause to description
3. Narrow example commentary to clarify boundaries
4. Ensure description has domain-specific terminology

### Pattern: Coherence Drift

Symptom: description promises capabilities the body doesn't deliver.

1. List all action verbs from example user messages
2. Check each verb has a corresponding body section
3. Add missing sections or remove undeliverable promises
4. Verify tool declarations match actual body references
