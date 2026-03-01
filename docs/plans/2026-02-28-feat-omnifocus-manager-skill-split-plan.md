# Plan: Split omnifocus-manager into Two Skills + Agent

## Context

Issue #63 describes a four-pillar vision for the omnifocus-manager plugin. The current monolithic skill (v4.5.0, eval 84/100) mixes pure GTD methodology with OmniFocus-specific execution. Splitting into two skills + an orchestrating agent enables: tool-agnostic GTD coaching, focused OmniFocus execution, and intelligent routing between them.

## Architecture

```
plugins/omnifocus-manager/
├── agents/
│   └── omnifocus-agent.md          # NEW - orchestrates both skills
├── skills/
│   ├── gtd-coach/                  # NEW - pure GTD methodology
│   │   ├── SKILL.md
│   │   ├── IMPROVEMENT_PLAN.md
│   │   └── references/
│   │       └── gtd_methodology.md
│   └── omnifocus-manager/          # REFINED - OmniFocus execution
│       ├── SKILL.md                # Modified
│       ├── IMPROVEMENT_PLAN.md     # Modified
│       ├── references/
│       │   ├── gtd_guide.md        # Rewritten (166 → ~50 lines)
│       │   ├── insight_patterns.md # Minor edit (add header)
│       │   └── (13 others unchanged)
│       ├── scripts/                # Unchanged
│       ├── assets/                 # Unchanged
│       └── typescript/             # Unchanged
└── .claude-plugin/
    └── plugin.json                 # Version bump to 5.0.0
```

## Issue #63 Pillar Mapping

| Pillar | Skill | Description |
|--------|-------|-------------|
| 1. Query | omnifocus-manager | JXA/Omni Automation live queries |
| 2. Perspectives | omnifocus-manager | Programmatic perspective creation |
| 3. GTD Coaching | gtd-coach | Pure methodology coaching |
| 4. Plugins+FM | omnifocus-manager | Plugin generation, Apple Intelligence |
| Routing | omnifocus-agent | Intent classification, skill composition |

## Implementation Steps

### Step 1: Create gtd-coach skill

- [ ] **Create:** `plugins/omnifocus-manager/skills/gtd-coach/SKILL.md` (~150-200 lines)
  - Frontmatter with trigger phrases: "GTD principles", "what makes a good next action", "project vs action", "how to do weekly review", "capture clarify organize", "horizons of focus"
  - Pure GTD methodology: 5 phases, core concepts, coaching areas
  - Tool-agnostic — references OmniFocus as one implementation option
  - No scripts, no automation commands

- [ ] **Create:** `plugins/omnifocus-manager/skills/gtd-coach/references/gtd_methodology.md` (~120 lines)
  - Extract pure GTD content from current `references/gtd_guide.md`
  - Remove all OmniFocus automation examples (osascript, URL schemes)
  - Sections: 5 phases deep dive, project vs action clarity, next action specificity, weekly review checklist, system health principles, horizons of focus

- [ ] **Create:** `plugins/omnifocus-manager/skills/gtd-coach/IMPROVEMENT_PLAN.md`
  - Version 1.0.0, link to #63

### Step 2: Refine omnifocus-manager skill

- [ ] **Rewrite:** `references/gtd_guide.md` (166 → ~50 lines)
  - Concise GTD-to-OmniFocus mapping table only
  - Links to gtd-coach for full methodology
  - Automation mapping (GTD phase → OmniFocus command)

- [ ] **Edit:** `references/insight_patterns.md`
  - Add 3-line header linking to gtd-coach for GTD principles

- [ ] **Edit:** `SKILL.md` (~330 → ~350 lines)
  - Update description to mention gtd-coach for methodology
  - Add four-pillar framing section (from #63)
  - Insert concise "GTD in OmniFocus" mapping table
  - Update decision tree item #4: route GTD questions to gtd-coach
  - CRITICAL: Plugin generation workflow (lines 21-78) stays UNCHANGED
  - All library composition, automation approaches sections stay

- [ ] **Edit:** `IMPROVEMENT_PLAN.md`
  - Add version 5.0.0 entry, link to #63

### Step 3: Create omnifocus-agent

- [ ] **Create:** `plugins/omnifocus-manager/agents/omnifocus-agent.md` (~200-250 lines)
  - Follow `plugins/pkm-plugin/agents/pkm-manager.md` pattern
  - Frontmatter with examples showing routing decisions
  - Intent classification logic:

  | User Intent | Routes To |
  |-------------|-----------|
  | "What makes a good next action?" | gtd-coach only |
  | "Show overdue tasks" | omnifocus-manager only |
  | "My inbox has 47 items, help" | gtd-coach (methodology) then omnifocus-manager (execution) |
  | "Build a plugin to summarize work" | omnifocus-manager (Pillar 4) |
  | "Help me do my weekly review" | Both — gtd-coach walks checklist, omnifocus-manager runs queries |

  - Loads skill docs on-demand: `${CLAUDE_PLUGIN_ROOT}/skills/*/SKILL.md`
  - Runs scripts directly: `osascript -l JavaScript ${CLAUDE_PLUGIN_ROOT}/skills/omnifocus-manager/scripts/...`
  - Workflow orchestration for each pillar

### Step 4: Update plugin metadata

- [ ] **Edit:** `.claude-plugin/plugin.json`
  - Bump version 4.4.0 → 5.0.0 (major: architectural change)
  - Add keywords: "gtd", "agent"

### Step 5: Validate and record scores

- [ ] Run skillsmith eval on gtd-coach (target 80+)
- [ ] Run skillsmith eval on omnifocus-manager (target 80+)
- [ ] Record eval scores in both IMPROVEMENT_PLAN.md files
- [ ] Update #63 with implementation summary

## Files Summary

| Action | File | Notes |
|--------|------|-------|
| CREATE | `skills/gtd-coach/SKILL.md` | ~150-200 lines, pure GTD |
| CREATE | `skills/gtd-coach/references/gtd_methodology.md` | ~120 lines, tool-agnostic |
| CREATE | `skills/gtd-coach/IMPROVEMENT_PLAN.md` | v1.0.0 |
| CREATE | `agents/omnifocus-agent.md` | ~200-250 lines, routing agent |
| REWRITE | `skills/omnifocus-manager/references/gtd_guide.md` | 166 → ~50 lines |
| EDIT | `skills/omnifocus-manager/references/insight_patterns.md` | Add 3-line header |
| EDIT | `skills/omnifocus-manager/SKILL.md` | Add pillars, mapping table, update routing |
| EDIT | `skills/omnifocus-manager/IMPROVEMENT_PLAN.md` | Add v5.0.0 entry |
| EDIT | `.claude-plugin/plugin.json` | Version bump to 5.0.0 |

**Unchanged:** All 13 other reference files, all scripts, all assets, all TypeScript files.

## Verification

1. Both skills pass skillsmith eval at 80+
2. Plugin generation workflow (CRITICAL section) unchanged and functional
3. Agent correctly routes example queries from #63
4. `omnifocus-manager` works standalone (not agent-dependent)
5. `gtd-coach` contains zero OmniFocus-specific automation
