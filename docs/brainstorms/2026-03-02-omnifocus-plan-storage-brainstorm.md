---
date: 2026-03-02
topic: omnifocus-plan-storage
status: brainstorm
relates-to: plugins/omnifocus-manager
---

# OmniFocus Plan Storage & AI Agent Task Tracking

## Problem

Plans created by Claude Code (via `/ce:plan`, brainstorms, etc.) currently live only as markdown in `docs/plans/` or as GitHub Issues. There's no bridge to OmniFocus for personal task management, prioritization across plans, or real-time completion tracking during implementation.

## Goal

Enable plans to be **optionally published to OmniFocus** as projects with subtasks, tagged with an `AI Agent` hierarchy, so that:
- Implementation progress is tracked in real-time as tasks complete
- All AI-managed work is queryable via a single tag for prioritization
- Storage destination is a conscious choice (GitHub Issues, OmniFocus, or markdown)

## Design Decisions

### 1. Storage Destination Prompt: Explicit Slash Command

**Choice:** A new `/publish-plan` command (not a hook) that you invoke after a plan is finalized.

**Rationale:** Gives full control over when and where a plan is published. Avoids false triggers from intermediate file writes.

**Flow:**
```
/ce:plan → writes docs/plans/2026-03-02-feat-foo-plan.md
           ↓
user reviews plan
           ↓
/publish-plan → prompts: GitHub Issue | OmniFocus Project | Both | Skip
           ↓
Creates target(s) with task breakdown from plan
```

**Where it lives:** New command in `omnifocus-manager` plugin (since it bridges to OmniFocus). Could also be a standalone command in a workflow plugin if we want it decoupled.

### 2. OmniFocus Project Structure: Grouped by Phase

**Choice:** Action groups within the project mirror plan phases.

**Example OmniFocus structure:**
```
📁 Project: "feat: Add LiteLLM skill"    [tagged: AI Agent]
  📂 Phase 1: Setup                       [tagged: AI Agent]
    ☐ Create skill directory structure     [tagged: AI Agent / Claude Code]
    ☐ Write SKILL.md with spec            [tagged: AI Agent / Claude Code]
  📂 Phase 2: Implementation              [tagged: AI Agent]
    ☐ Implement provider routing          [tagged: AI Agent / Claude Code]
    ☐ Add health check script             [tagged: AI Agent / Claude Code]
  📂 Phase 3: Validation                  [tagged: AI Agent]
    ☐ Run skillsmith evaluation           [tagged: AI Agent / Claude Code]
    ☐ Update IMPROVEMENT_PLAN.md          [tagged: AI Agent / Claude Code]
```

**JXA approach:** Use `Task` objects with child tasks (action groups) rather than separate projects. OmniFocus naturally groups these.

### 3. Completion Tracking: PostToolUse Hook with Script Fallback

**Primary: PostToolUse hook on TaskUpdate**

When Claude Code marks a task complete via `TaskUpdate`, a hook fires that:
1. Reads the task subject from hook input JSON
2. Searches OmniFocus for a matching task under AI Agent-tagged projects
3. Marks the OmniFocus task complete via JXA

**Hook input available:**
```json
{
  "tool_name": "TaskUpdate",
  "tool_input": {
    "taskId": "42",
    "status": "completed",
    "subject": "Create skill directory structure"
  }
}
```

**Matching strategy:** Match by task name (subject) within AI Agent-tagged projects. Names should be specific enough to avoid false matches.

**Fallback: Explicit script call**

If the hook approach proves unreliable (e.g., task names don't match exactly), the implementation skill can call:
```bash
osascript -l JavaScript scripts/manage_omnifocus.js complete \
  --search "Create skill directory structure" \
  --project "feat: Add LiteLLM skill"
```

**Research needed during planning:**
- Does `TaskUpdate` actually appear in PostToolUse matcher? (The tool list shows it should, but needs testing)
- How to handle fuzzy matching when plan task names differ slightly from TodoWrite subjects
- Whether to store OmniFocus task IDs in a session-local mapping file for reliable matching

### 4. Tag Structure: Nested AI Agent Hierarchy

**Choice:** `AI Agent` parent tag with child tags per agent/tool.

```
🏷 AI Agent                    ← parent tag, default for all AI work
  🏷 Claude Code               ← tasks managed by Claude Code
  🏷 Apple Intelligence        ← tasks delegated to local FM
  🏷 Ollama                    ← tasks for local LLM
```

**Default behavior:** If only `AI Agent` is specified (no child), prefer local execution (Apple FM / Ollama) first.

**Query patterns:**
- "Show all AI Agent work" → query parent tag (includes all children)
- "Show Claude Code tasks" → query specific child tag
- "Show unassigned AI work" → query parent tag, exclude child tags

**JXA for nested tags:**
```javascript
// Create nested tag structure
const aiAgent = app.Tag({ name: "AI Agent" });
doc.tags.push(aiAgent);
const claudeCode = app.Tag({ name: "Claude Code" });
aiAgent.tags.push(claudeCode); // nested under AI Agent
```

## Components to Build

### A. `/publish-plan` Slash Command

**Input:** Path to a plan document (or auto-detect from recent docs/plans/)
**Prompts:**
1. Storage destination: GitHub Issue | OmniFocus | Both | Skip
2. If OmniFocus: Confirm project name and folder
3. If GitHub: Confirm labels and milestone

**Parses plan document** for:
- Title → OmniFocus project name
- Phase headings → Action groups
- Task lists (- [ ]) → Subtasks
- Metadata (type, labels) → Tags

### B. `create_plan_project.js` JXA Script

New script in `omnifocus-manager/scripts/` that:
- Creates a project with action groups from parsed plan
- Tags everything with `AI Agent / Claude Code`
- Sets defer/due dates if specified in plan
- Returns created task IDs for hook matching

### C. PostToolUse Hook: `task-sync-hook.sh`

New hook in `omnifocus-manager/hooks/` that:
- Listens for `TaskUpdate` with `status: "completed"`
- Looks up matching OmniFocus task
- Marks it complete
- Outputs confirmation to transcript

### D. `query_ai_tasks.js` JXA Script

New script (or extension to `gtd-queries.js`) that:
- Lists all tasks/projects tagged `AI Agent`
- Groups by project and status
- Supports filtering by child tag (Claude Code, Ollama, etc.)
- Output formats: markdown table, JSON, clipboard

## Open Questions

1. **Plan document parsing:** Should the command parse markdown task lists directly, or require a structured YAML section in the plan frontmatter?

2. **Bidirectional sync:** If a task is completed in OmniFocus directly (not via Claude Code), should that be detectable? (Probably out of scope for v1)

3. **Session mapping:** Should we store a `{todoId: omnifocusTaskId}` mapping in a temp file during implementation sessions for reliable hook matching?

4. **Which plugin owns `/publish-plan`?** Options:
   - `omnifocus-manager` — natural home since it handles OmniFocus
   - New `workflow-bridge` plugin — if we want it decoupled from any single destination
   - `compound-engineering` — since it owns the plan workflow

5. **GitHub Issue creation:** Should `/publish-plan` also handle `gh issue create`, or delegate to existing workflow patterns?

## Non-Goals (v1)

- Bidirectional sync (OmniFocus → Claude Code)
- Automatic plan creation from OmniFocus projects
- Integration with GitLab (GitHub only for v1)
- Perspective creation (that's Pillar 2 of omnifocus-manager, separate effort)
