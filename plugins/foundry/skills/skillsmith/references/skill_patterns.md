---
last_verified: 2026-04-28
sources:
  - type: web
    url: "https://www.anthropic.com/engineering/claude-code-best-practices"
    description: "Anthropic's Complete Guide to Building Skills for Claude"
---

# Skill Patterns

Five proven behavioral patterns from Anthropic's "Complete Guide to Building Skills for Claude." Use these to choose the right architectural shape for a skill before writing SKILL.md.

These describe **runtime behavior** — how the skill orchestrates tools and steps. They are distinct from the four structural patterns in `init_skill.py`'s scaffold template (Workflow-Based, Task-Based, Reference/Guidelines, Capabilities-Based), which describe how SKILL.md is organized.

---

## Pattern 1: Sequential Workflow Orchestration

**When to use:** The skill executes a fixed, ordered sequence of steps where each step's output feeds the next. The user provides a trigger; the skill handles the full pipeline.

**Structural signal:**
- SKILL.md defines numbered steps with clear handoffs
- Each step references a specific script or tool
- Error handling defined per step (what to do if step N fails)

**Example trigger:** "run the full deployment pipeline for this service"

**Real-skill examples in this repo:**
- `skillsmith` — Step 1 → 2 → 3 → 4 → 5 → 6 skill development loop
- `ce-work` — Phase 1 (setup) → Phase 2 (execute) → Phase 3 (quality) → Phase 4 (ship)

**Design guidance:** Define each step's input, output, and failure path explicitly. Skills that try to sequence too many steps in SKILL.md become brittle — move step logic to scripts and reference them.

---

## Pattern 2: Multi-MCP Coordination

**When to use:** The skill needs to combine data or capabilities from two or more MCP servers (e.g., a database MCP + a communication MCP, or a search MCP + a code MCP).

**Structural signal:**
- `allowed-tools` or `compatibility` frontmatter lists multiple MCP servers
- SKILL.md describes which MCP handles which concern
- References document each MCP's relevant endpoints or capabilities

**Example trigger:** "search our internal docs and file a Jira ticket summarizing findings"

**Real-skill examples in this repo:**
- `obsidian-cli` combined with filesystem operations (read vault + write back)
- `compound-engineering` routing to `context7` (docs MCP) alongside Bash/filesystem tools

**Design guidance:** Define a clear ownership boundary — each MCP should own a distinct concern. If two MCPs overlap on the same data, document the precedence rule in SKILL.md.

---

## Pattern 3: Iterative Refinement

**When to use:** The skill improves an artifact over multiple passes — each pass analyzes the current state, makes a targeted change, and re-evaluates. The loop continues until a quality threshold is met.

**Structural signal:**
- SKILL.md defines an explicit loop: Evaluate → Fix → Re-evaluate
- Stopping condition is measurable (score threshold, no more errors, user approval)
- References contain the evaluation rubric

**Example trigger:** "keep improving this skill until it scores above 80"

**Real-skill examples in this repo:**
- `skillsmith` Step 6 loop: `--explain` → fix → `--update-readme` → sync
- `compound-engineering:design-iterator` — screenshot → analyze → improve → repeat
- `compound-engineering:ce-review` — review → address → re-review

**Design guidance:** Define the termination condition clearly. Unbounded loops should have a maximum iteration count or an explicit user check-in point. Store intermediate state in a file (not memory) so the loop is resumable.

---

## Pattern 4: Context-Aware Tool Selection

**When to use:** The skill receives ambiguous input and must diagnose or classify it before choosing which tools or sub-skills to invoke. The routing decision is based on observed context, not fixed workflow.

**Structural signal:**
- SKILL.md contains a routing table or decision tree
- Multiple tool paths exist; the skill selects based on input signals
- References document each tool path's trigger conditions

**Example trigger:** "fix this problem" (where "problem" could be a test failure, a lint error, a type error, or a runtime crash)

**Real-skill examples in this repo:**
- `terminal-guru` — diagnoses symptom (garbled chars vs. slow startup vs. SSH display) then routes to `terminal-emulation`, `zsh-dev`, or `signals-monitoring`
- `skillsmith` routing table — routes to `plugin-dev:skill-development` vs. `skillsmith` vs. `marketplace-manager` based on task type
- `compound-engineering:ce-work` — chooses inline vs. serial subagents vs. parallel subagents based on task count and dependency graph

**Design guidance:** Make the routing logic visible in SKILL.md — a table or decision tree is better than prose. If the classification step is complex, it belongs in a reference or script, not inline in SKILL.md.

---

## Pattern 5: Domain-Specific Intelligence

**When to use:** The skill encodes deep knowledge about a specific domain (a methodology, a protocol, an internal system) that Claude would not apply correctly without explicit guidance. The skill's value is in the domain model, not the tool orchestration.

**Structural signal:**
- References contain the domain model, terminology, and rules
- SKILL.md focuses on *how to apply* the domain knowledge, not on tool mechanics
- Descriptions include domain-specific trigger phrases that only a domain practitioner would recognize

**Example trigger:** "do my weekly GTD review" or "map the risk surface of this LLM pipeline"

**Real-skill examples in this repo:**
- `omnifocus-manager:gtd-coach` — encodes GTD methodology (capture, clarify, organize, reflect, engage)
- `ai-risk-mapper` — encodes CoSAI framework for AI security risk assessment
- `obsidian:obsidian-markdown` — encodes Obsidian Flavored Markdown conventions (wikilinks, callouts, properties)

**Design guidance:** Put the domain model in `references/` — SKILL.md should be readable by a domain practitioner as a "how this skill applies the domain." If someone who knows the domain finds the skill's behavior surprising, the domain model is incomplete.

---

## Choosing a Pattern

Most skills are primarily one pattern with elements of another. Common combinations:

| Primary | Often combined with | Why |
|---------|-------------------|-----|
| Sequential | Domain-specific | Domain rules govern each step |
| Iterative | Context-aware | Each iteration re-diagnoses before acting |
| Multi-MCP | Sequential | MCP calls happen in a defined order |
| Context-aware | Domain-specific | Domain knowledge informs routing decisions |

If a skill doesn't fit clearly into any pattern, it may be doing too many things — consider splitting it.
