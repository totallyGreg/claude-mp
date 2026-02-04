# Skill to Plugin Migration: Understanding the Evolution

## Overview

This document explains the journey from a standalone **skill** to a **plugin** containing skills, commands, agents, and infrastructure. It compares the official Anthropic plugin-dev toolkit with your skillsmith + marketplace-manager approach.

---

## Part 1: The Three Evolution Stages

### Stage 1: Standalone Skill

**What it is:**
- A single `.md` file with YAML frontmatter + domain knowledge
- Example: `skills/omnifocus-manager/SKILL.md`

**Structure:**
```
skill-name/
├── SKILL.md                 # Metadata + documentation
├── references/              # Detailed guides (loaded on demand)
├── scripts/                 # Helper utilities
├── examples/                # Usage examples
└── assets/                  # Output templates
```

**Capabilities:**
- ✅ Share domain knowledge with Claude
- ✅ Provide reference documentation
- ✅ Progressive disclosure (lean SKILL.md + detailed references)
- ❌ No slash commands
- ❌ No agents
- ❌ No hooks
- ❌ No MCP integration

**When to use:**
- Pure knowledge/methodology skills
- Guiding skills (like skillsmith itself)
- Reference libraries

**Your examples:**
- skillsmith/skill/
- marketplace-manager/skill/
- ai-risk-mapper/skill/

---

### Stage 2: Plugin with Skills + Commands

**What it is:**
- A plugin directory structure containing:
  - One or more skills
  - Slash commands that wrap scripts
  - Commands call Python/Bash for automation

**Structure:**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/                # Slash command definitions (.md files)
│   ├── command-1.md
│   ├── command-2.md
│   └── command-3.md
├── skills/
│   └── skill-name/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── assets/
└── scripts/                 # Shared utilities
    ├── main_script.py
    ├── helper.py
    └── utils.py
```

**Capabilities:**
- ✅ All Stage 1 capabilities
- ✅ Slash commands for user-facing interface
- ✅ Python/Bash scripts for automation
- ✅ Namespace organization (`/ss-*`, `/mp-*`)
- ✅ Plugin versioning in manifest
- ❌ No agents
- ❌ No hooks
- ❌ No MCP integration

**When to use:**
- Automating repeatable workflows
- Providing user commands
- Distributing as a single plugin unit
- Multi-command toolkits

**Your examples:**
- **skillsmith** (v4.0.0)
  - 4 commands: `/ss-init`, `/ss-validate`, `/ss-evaluate`, `/ss-research`
  - 7 scripts: init_skill.py, evaluate_skill.py, research_skill.py, etc.
  - 1 bundled skill with 11 references

- **marketplace-manager** (v2.0.0)
  - 5 commands: `/mp-sync`, `/mp-status`, `/mp-add`, `/mp-list`, `/mp-validate`
  - 12 scripts: add_to_marketplace.py, sync_marketplace_versions.py, etc.
  - 1 bundled skill with 4 references

---

### Stage 3: Plugin with Skills + Commands + Agents

**What it is:**
- A plugin containing:
  - Skills (domain knowledge)
  - Commands (user-facing interfaces)
  - Agents (autonomous orchestrators)
  - Hooks (event-driven automation)
  - MCP servers (external integrations)

**Structure:**
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (includes agent list)
├── commands/                # User commands (.md files)
├── agents/                  # Autonomous agents (.md files)
│   ├── agent-1.md
│   └── agent-2.md
├── skills/
│   └── skill-name/
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── assets/
├── hooks/
│   └── hooks.json           # Event handlers (PreToolUse, PostToolUse, etc.)
├── .mcp.json                # MCP server definitions
└── scripts/                 # Shared utilities
```

**Agent example from official plugin-dev:**
```yaml
name: agent-creator
description: Creates new agents from descriptions using AI-assisted generation
model: sonnet
color: blue
tools: [Write, Read, Grep, Glob]
```

**Capabilities:**
- ✅ All Stage 1 + Stage 2 capabilities
- ✅ Agents for autonomous orchestration
- ✅ Agents can use all Claude Code tools (not just skills)
- ✅ Event-driven hooks (PreToolUse, PostToolUse, Stop, Notification, etc.)
- ✅ MCP server integration (stdio, SSE, HTTP, WebSocket)
- ✅ Plugin becomes a complete development platform

**When to use:**
- Complex workflows requiring reasoning/autonomy
- Coordinating multiple systems
- Event-driven automation
- Integrating external services via MCP
- Building specialized development platforms

**Official plugin-dev examples:**
- **agent-creator**: AI-assisted generation of agent markdown files
- **skill-reviewer**: Quality review of skills (autonomous analysis)
- **plugin-validator**: Comprehensive plugin validation (autonomous checking)

---

## Part 2: Your Current Position

### What You've Built: Stage 2

Your skillsmith and marketplace-manager are **Stage 2 plugins**:

```
skillsmith (v4.0.0)
├── 4 slash commands (/ss-init, /ss-validate, /ss-evaluate, /ss-research)
├── 7 Python scripts (evaluation engine, research, validation)
├── 1 bundled skill with 11 reference documents
└── ❌ No agents, hooks, or MCP servers
```

```
marketplace-manager (v2.0.0)
├── 5 slash commands (/mp-sync, /mp-status, /mp-add, /mp-list, /mp-validate)
├── 12 Python scripts (marketplace operations, version syncing, migration)
├── 1 bundled skill with 4 reference documents
└── ❌ No agents, hooks, or MCP servers
```

### Why Stage 2 Works Well

**Strengths of your current approach:**
1. **Focused responsibility**: Each plugin does one thing well
2. **User-discoverable**: Slash commands are easy to find (`/ss-*`, `/mp-*`)
3. **Deterministic**: Scripts provide reliable, reproducible automation
4. **Maintainable**: Clear separation between knowledge (skill) and automation (scripts)
5. **Testable**: Each script can be tested independently

**Limitations:**
- Some workflows require multiple commands to complete (e.g., improve skill → validate → sync → commit)
- No autonomous decision-making (user must invoke each command manually)
- No event-driven automation
- No external service integration via MCP

---

## Part 3: The Official Plugin-Dev Approach (Stage 3)

### What plugin-dev Provides

**7 Specialized Skills:**
1. **Hook Development** - Event-driven automation patterns
2. **MCP Integration** - External service/tool integration
3. **Plugin Structure** - Directory layout and organization
4. **Plugin Settings** - Configuration management patterns
5. **Command Development** - Slash command best practices
6. **Agent Development** - Creating autonomous agents
7. **Skill Development** - Progressive disclosure methodology

**3 Specialized Agents:**
1. **agent-creator** - AI-assisted agent generation (takes your description → generates agent markdown with system prompt)
2. **skill-reviewer** - Autonomous quality review (analyzes skill structure, description, disclosure)
3. **plugin-validator** - Comprehensive validation (checks manifest, components, security)

**1 Main Command:**
- **/plugin-dev:create-plugin** - 8-phase guided workflow for building complete plugins

### Key Difference: Agent-Driven

Official plugin-dev **uses agents to help you build plugins**:

```
/plugin-dev:create-plugin
    ↓
Phase 1: Discovery (asks questions)
    ↓
Phase 2: Component Planning
    ↓
Phase 3: Detailed Design
    ↓
Phase 4: Structure Creation (creates directories)
    ↓
Phase 5: Component Implementation
    ├─ Uses agent-creator for agent definitions
    ├─ Uses skill-reviewer for skill validation
    └─ Uses plugin-validator for structure checking
    ↓
Phase 6-8: Testing, Validation, Documentation
```

### Automation Pattern in plugin-dev

**AI-Assisted Agent Generation:**
```
User: "Create an agent that reviews code for security issues"
    ↓
agent-creator (agent)
    ├─ Understands: autonomy, reasoning, specialized expertise
    ├─ Generates: YAML frontmatter + system prompt (~1000 words)
    ├─ Includes: trigger examples, model choice, tool selection
    └─ Outputs: agent-security-reviewer.md ready to use
```

**vs. Your Approach:**

In skillsmith/marketplace-manager, agents would be optional future feature:
```
Hypothetical /ss-create-agent <description>
    ├─ Calls: create_agent.py script
    ├─ Takes: parameter from user
    └─ Returns: Generated agent markdown (same outcome, different path)
```

---

## Part 4: Migration Path - How to Evolve Your Plugins

### From Stage 2 to Stage 3: Adding Agents

**Decision Point: When do you need agents?**

You should add agents to skillsmith or marketplace-manager when:
- ✅ Users need **orchestration** (multiple steps with reasoning)
- ✅ You want **autonomy** (system makes decisions, not user-driven)
- ✅ You have **complex analysis** (can't be done with deterministic scripts)
- ✅ You want to **guide creative tasks** (agent helps user design solutions)

**Examples for your ecosystem:**

**Example 1: Skillsmith Agent**
```yaml
name: skill-architect
description: |
  Autonomous skill architect that reviews your skill idea,
  recommends bundled references, suggests command structure,
  and creates an improvement plan.

  Example trigger: "I want to create a skill for X"

model: sonnet
tools: [Read, Glob, Grep, Write]
color: purple
```

When invoked, this agent would:
- Analyze the skill idea
- Suggest reference documentation structure
- Recommend commands if applicable
- Create IMPROVEMENT_PLAN.md template
- Propose next steps

**Example 2: Marketplace-Manager Agent**
```yaml
name: plugin-recommender
description: |
  Recommends plugin bundling strategy based on skill affinities.
  Analyzes your skills and suggests which should be grouped together
  in a single plugin vs separate plugins.

  Example trigger: "Which skills should I bundle together?"

model: sonnet
tools: [Read, Glob, Grep]
color: orange
```

When invoked, this agent would:
- Read all SKILL.md files
- Calculate affinity scores
- Analyze cross-references
- Suggest bundling strategies
- Explain tradeoffs

### Implementation Steps for Stage 3 Migration

**Step 1: Create Agent Definition Files**
```bash
# In your plugin directory
mkdir -p agents/
cat > agents/agent-name.md << 'EOF'
---
name: agent-name
description: |
  What this agent does.

  Example trigger: "User request"
model: sonnet
tools: [Read, Write, Glob, Grep]
color: blue
---

## System Prompt

You are a specialized agent for...
[1000-2000 words of system prompt]
EOF
```

**Step 2: Update plugin.json**
```json
{
  "metadata": {
    "name": "skillsmith",
    "version": "5.0.0",
    "agents": [
      "agent-name"
    ]
  }
}
```

**Step 3: Test the Agent**
- Invoke via `/skillsmith:agent-name`
- Verify triggering words work
- Check tool usage and outputs

**Step 4: Add to IMPROVEMENT_PLAN.md**
- Document new agent in version history
- Link GitHub issue if this was tracked work
- Update metrics if applicable

### Reusing plugin-dev's Agent-Creation Pattern

Instead of building agents from scratch, you could:

1. **Use plugin-dev's agent-creator**
```bash
/plugin-dev:agent-creator
# Describe what agent you want
# agent-creator generates the markdown for you
```

2. **Reference plugin-dev's system prompts**
   - Study agent-creator.md system prompt in `/Users/totally/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/agents/`
   - Use similar patterns for your own agents

3. **Follow agent-development skill guidelines**
   - Read `/Users/totally/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/agent-development/SKILL.md`
   - Learn system prompt design patterns
   - Apply to your domain

---

## Part 5: Skill → Plugin → Plugin with Agents Journey

### Real Example: omnifocus-manager Evolution

**Starting point (Stage 1):**
```
skills/omnifocus-manager/
├── SKILL.md          # "Here's how to query OmniFocus via JXA"
├── references/       # Database schema, JXA API docs
└── examples/         # Query examples
```

**Next step (Stage 2):**
```
plugins/omnifocus-manager/
├── .claude-plugin/plugin.json
├── commands/
│   ├── task-search.md          # /omnifocus:task-search
│   ├── task-create.md          # /omnifocus:task-create
│   └── task-update.md          # /omnifocus:task-update
├── skills/omnifocus-manager/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
│       ├── jxa_query.js        # JXA helper functions
│       ├── parse_response.py
│       └── utils.py
└── scripts/
    └── omnifocus-cli.py        # Main script wrapper
```

**Future (Stage 3 - optional):**
```
plugins/omnifocus-manager/
├── [all Stage 2 files above]
├── agents/
│   ├── task-architect.md       # Plans complex task hierarchies
│   └── workflow-optimizer.md   # Suggests task organization
├── hooks/
│   └── hooks.json              # Auto-save results to OmniFocus
└── .mcp.json                   # OmniFocus as MCP server?
```

### Benefits at Each Stage

| Stage | Benefit | When to Move | Cost |
|-------|---------|--------------|------|
| **1: Skill** | Easy to create, pure knowledge | Always start here | Limited interface |
| **2: Plugin+Commands** | User-discoverable automation, namespace | Adding repeatable workflows | Need scripts |
| **3: Plugin+Agents** | Autonomous orchestration, reasoning | Complex multi-step workflows | Larger complexity |

---

## Part 6: Comparing the Two Approaches

### Official plugin-dev (Anthropic's Toolkit)

**Strengths:**
- ✅ Comprehensive guidance on hooks, MCP, agents
- ✅ AI-assisted generation (agent-creator generates agents for you)
- ✅ Full lifecycle support (create → validate → test → deploy)
- ✅ 7 detailed skills covering all plugin aspects
- ✅ Proven patterns from official ecosystem

**Role:**
- **"How do I build plugins?"** → Use plugin-dev
- **"What are the component options?"** → Read plugin-dev skills
- **"Create a new agent for me"** → Use agent-creator

**Best for:**
- Users new to plugin development
- Understanding plugin architecture
- AI-assisted agent generation
- Following official patterns

### Your skillsmith + marketplace-manager (Domain-Specific Toolkit)

**Strengths:**
- ✅ Focused on skill quality improvement (evaluate_skill.py)
- ✅ Automated version management (sync_marketplace_versions.py)
- ✅ Plugin distribution workflows (marketplace operations)
- ✅ Quality gates and metrics tracking
- ✅ Integrated with your repository workflow

**Role:**
- **"How do I improve this skill?"** → Use skillsmith
- **"How do I distribute skills?"** → Use marketplace-manager
- **"What quality metrics should I track?"** → See skillsmith evaluation

**Best for:**
- Maintaining existing skills
- Quality improvement cycles
- Distribution and marketplace management
- Metrics-driven development

### Complementary, Not Competing

```
User has skill idea
    ↓
USE plugin-dev's skill-development skill
to understand WHAT a skill is and how to structure it
    ↓
CREATE basic skill (Stage 1)
    ↓
USE your skillsmith
to validate quality and get improvement suggestions
    ↓
EVOLVE to plugin with commands (Stage 2)
USE your marketplace-manager
to publish and manage versions
    ↓
WANT autonomous orchestration? (Stage 3)
USE plugin-dev's agent-development skill
or agent-creator to add agents
```

---

## Part 7: Roadmap for Your Ecosystem

### Short-term (What You Have)

✅ **skillsmith** - Skill creation and quality framework
✅ **marketplace-manager** - Distribution and versioning
✅ **ai-risk-mapper** - Security analysis
✅ **gateway-proxy** - Infrastructure routing

All are **Stage 2 plugins**: Skills + Commands

### Medium-term (Consider Adding)

**Option A: Stay Stage 2 (Recommended)**
- Continue focusing on command-driven interfaces
- Improve integration between skillsmith and marketplace-manager
- Add `/ss-publish` command to chain them
- Document the workflow

**Option B: Add Agents for Orchestration**
- Create skillsmith agent for autonomous skill architecture recommendations
- Create marketplace-manager agent for bundling recommendations
- Create plugin-validator-style agent for your plugins
- Reference official plugin-dev's agent patterns

**Option C: Partial Stage 3**
- Add hooks for pre-commit automation (pre-publish validation)
- Add MCP integration for external tools (Git, package managers)
- Stay command-driven but add event automation

### Long-term (Evolution)

**If the ecosystem grows:**
- Consider merging skillsmith + marketplace-manager into unified plugin-dev-style toolkit
- But keep them separate as long as they serve different purposes
- Add agent companions for autonomy when needed

---

## Conclusion

**Your plugins are at Stage 2, and that's perfectly appropriate for your use case.**

The official plugin-dev (Stage 3) provides comprehensive guidance for building plugin infrastructure. Your skillsmith and marketplace-manager provide specialized domain knowledge for skill quality and distribution—they fill a gap that plugin-dev doesn't address.

**The migration path is clear:**
- **Stage 1** (Skill): Pure knowledge
- **Stage 2** (Plugin + Commands): Your current ecosystem
- **Stage 3** (Plugin + Agents + Hooks + MCP): Optional future expansion

**Most valuable next step:** Don't migrate to Stage 3 yet. Instead:
1. Better document the Stage 2 integration between your two plugins
2. Create `/ss-publish` command to chain skillsmith → marketplace-manager → git
3. Reference official plugin-dev when users need agents or hooks
4. Revisit Stage 3 if you identify workflows that need autonomous orchestration
