---
title: "feat: /of:plan and /of:work commands + OmniFocus task-sync hook"
type: feat
status: completed
date: 2026-03-02
origin: docs/brainstorms/2026-03-02-omnifocus-plan-storage-brainstorm.md
labels: plugin:omnifocus-manager
---

# feat: /of:plan and /of:work commands + OmniFocus task-sync hook

## Overview

Create a two-way bridge between Claude Code plans and OmniFocus task management:

1. **Push:** `/of:plan` publishes plan documents to OmniFocus as projects with phased action groups tagged `AI Agent / Claude Code`
2. **Pull:** `/of:work` reads an OmniFocus AI Agent project and executes tasks step-by-step, marking each complete
3. **Auto-sync:** A PostToolUse hook marks OmniFocus tasks complete when Claude Code's `TaskUpdate` fires during any implementation session

## Problem Statement / Motivation

Plans created via `/ce:plan` currently live as markdown in `docs/plans/` or as GitHub Issues. There is no bridge to OmniFocus for:
- Personal task management and prioritization across multiple AI-driven plans
- Real-time implementation progress tracking
- Unified querying of all AI-managed work

(see brainstorm: `docs/brainstorms/2026-03-02-omnifocus-plan-storage-brainstorm.md`)

## Proposed Solution

### Component A: `/of:plan` Command

A new slash command at `plugins/omnifocus-manager/commands/of-plan.md` that:

1. Accepts a plan file path (or auto-detects from most recent `docs/plans/`)
2. Prompts user for destination: **GitHub Issue | OmniFocus Project | Both | Skip**
3. If OmniFocus: Claude parses the plan markdown to extract phases and tasks, then calls a new `bulk-create` action in `manage_omnifocus.js`
4. If GitHub: calls `gh issue create` with plan content
5. If Both: creates both, stores GitHub issue URL in OmniFocus project note

**Plan parsing strategy:** Claude (in the command prompt) reads the plan and extracts structure. No standalone parser needed (KISS). Claude emits a JSON structure that `bulk-create` consumes:

```json
{
  "project": "feat: Add LiteLLM skill",
  "note": "Plan: docs/plans/2026-03-02-feat-litellm-plan.md\nIssue: https://github.com/...",
  "tags": ["AI Agent", "Claude Code"],
  "sequential": false,
  "groups": [
    {
      "name": "Phase 1: Setup",
      "sequential": true,
      "tasks": [
        { "name": "Create skill directory structure" },
        { "name": "Write SKILL.md with spec" }
      ]
    },
    {
      "name": "Phase 2: Implementation",
      "sequential": false,
      "tasks": [
        { "name": "Implement provider routing" },
        { "name": "Add health check script" }
      ]
    }
  ]
}
```

### Component B: `bulk-create` Action in manage_omnifocus.js

A new action that accepts the JSON structure above (via `--json-file <path>` or `--json <string>`) and creates the entire project tree in a **single JXA invocation**. This avoids the 10-40s latency of sequential `osascript` calls.

**Implementation:** Add to `manage_omnifocus.js` alongside existing actions. Uses `findOrCreateProject`, `findOrCreateTag` from `taskMutation.js`. Creates parent tasks for action groups, child tasks for items.

**Returns:** A mapping of task names to OmniFocus task IDs for the mapping file (see Component D).

### Component C: PostToolUse Hook — `omnifocus-task-sync`

A new hook at `plugins/omnifocus-manager/hooks/hooks.json` + `plugins/omnifocus-manager/hooks/omnifocus-task-sync.sh`.

**Hook config** (`hooks/hooks.json`):
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "TaskUpdate",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/omnifocus-task-sync.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

**Hook script behavior:**
1. Read JSON from stdin, extract `tool_input.status` and `tool_input.subject`
2. If status is not `"completed"`, exit 0 immediately
3. Check if OmniFocus is running (`pgrep -x OmniFocus`); if not, log and exit 0
4. Scan `.claude/omnifocus-maps/*.json` for a matching task name → OmniFocus task ID
5. If mapping exists: complete by ID (deterministic)
6. If no mapping: fall back to name search within AI Agent-tagged projects, case-insensitive substring match
7. If zero or multiple matches: log warning, exit 0 (do not block Claude)
8. Mark matched task complete via `osascript` / `manage_omnifocus.js complete --id <id>`

**Error handling:**
- All errors logged to stderr (captured by Claude Code transcript) and `/tmp/claude-omnifocus-hook.log`
- Exit 0 on all paths (never block Claude Code)
- Pre-check OmniFocus availability before JXA calls

### Component D: Plan-to-OmniFocus Mapping File

When `/of:plan` creates the OmniFocus project, it writes a mapping file to a **project-local** directory (not `/tmp`) so it survives across sessions:

```
.claude/omnifocus-maps/<plan-filename>.json
```

Example: `.claude/omnifocus-maps/2026-03-02-feat-litellm-plan.json`

```json
{
  "project_id": "abc123",
  "project_name": "feat: Add LiteLLM skill",
  "plan_path": "docs/plans/2026-03-02-feat-litellm-plan.md",
  "tasks": {
    "Create skill directory structure": "omnifocus-task-id-1",
    "Write SKILL.md with spec": "omnifocus-task-id-2"
  }
}
```

This enables deterministic ID-based matching in the hook, eliminating the fuzzy name-matching problem. The hook scans all files in `.claude/omnifocus-maps/` to find a matching task name, so it works regardless of which session created the mapping.

**Note:** Add `.claude/omnifocus-maps/` to `.gitignore` — these are local-only files.

### Component E: `/of:work` Command (Agent-Driven Execution from OmniFocus)

A new slash command at `plugins/omnifocus-manager/commands/of-work.md` that provides the OmniFocus-specific entry point for agent-driven task execution.

**How it relates to `/ce:work`:**
- `/ce:work` is the universal "work on a plan" command (from `compound-engineering`). It already accepts markdown plan files and GitHub Issues as sources.
- `/of:work` is the OmniFocus-specific shortcut that queries AI Agent-tagged projects directly from OmniFocus and drives execution from there.
- Both can work on the same underlying plan — `/of:work` just starts from OmniFocus as the task source.

**Flow:**

```
User: /of:work
Claude: [queries OmniFocus for AI Agent projects]
        "Found 3 AI Agent projects:
         1. feat: Add LiteLLM skill (3/7 complete)
         2. fix: Weekly review CWD (0/4 complete)
         3. refactor: Extract tag utilities (5/5 complete)
         Which project would you like to work on?"
User: 1
Claude: [reads project tasks, finds next incomplete task]
        [reads linked plan file from project note for context]
        "Next task: Implement provider routing"
        [implements task]
        [marks complete in OmniFocus directly via manage_omnifocus.js complete --id]
        "Task complete. Next: Add health check script. Continue?"
```

**Alternatively, pass a project name directly:** `/of:work "feat: Add LiteLLM skill"` skips the selection prompt.

**Key design decisions:**
- Sequential by default (respects OmniFocus project ordering)
- Reads plan file from project note for implementation context
- Creates a mapping file (`.claude/omnifocus-maps/`) on first run if one doesn't exist
- Each task completion is explicit — Claude marks it done only after verifying the work
- Marks OmniFocus tasks complete directly via `manage_omnifocus.js complete --id` (no dependency on the hook)

**How the three completion paths work together:**

| Path | Who drives | How OF tasks complete | When to use |
|------|-----------|----------------------|-------------|
| `/of:work` | OmniFocus project is the task source | Direct `complete --id` call per task | Working from OmniFocus queue |
| `/ce:work` on published plan | Plan doc is the task source | PostToolUse hook intercepts `TaskUpdate` | Working from plan doc, OF syncs automatically |
| Ad-hoc Claude session | No formal task source | PostToolUse hook (best effort name match) | Just working — OF syncs if it can |

### Component F: `ai-agent-tasks` Query (can ship independently)

Extend `gtd-queries.js` with a new action `ai-agent-tasks` that:
- Lists all tasks/projects tagged `AI Agent` (or any child tag)
- Groups by project and completion status
- Shows progress (e.g., "3/7 tasks complete")
- Supports `--tag` filter for specific child tags (e.g., `--tag "Claude Code"`)

Also add a `searchTasksByTag` function to `taskQuery.js` library (needed by both this query and the hook's fallback matching).

## Technical Considerations

### Tag Structure (from brainstorm)

Nested tags under `AI Agent`:
```
AI Agent (parent)
  ├── Claude Code
  ├── Apple Intelligence
  └── Ollama
```

The existing `findOrCreateTag` in `taskMutation.js` creates flat top-level tags only. The `bulk-create` action needs to **extend** this with nested tag support — finding or creating a parent tag, then pushing child tags to the parent's `tags` collection. This is new JXA work (not already supported).

### Hook as First in Repository

This is the **first hook** in the entire repo. Precedent matters:
- Follow `plugin-dev:hook-development` skill guidance (per WORKFLOW.md line 358)
- Use `${CLAUDE_PLUGIN_ROOT}` for portable paths
- Keep the hook script simple and defensive
- Add `components.hooks` to `plugin.json` manifest

### Performance

- **Bulk create** in single JXA invocation: ~1-3s for a typical plan (vs 10-40s sequential)
- **Hook latency:** ~0.5-1s per completion event (pre-check + JXA call). Non-blocking, so no impact on Claude Code responsiveness.
- **Query latency:** `ai-agent-tasks` uses `flattenedTags.whose()` which is fast in OmniFocus

### Edge Cases

| Scenario | Handling |
|----------|----------|
| Plan has no task lists | Warn user, create project with plan title as single task |
| OmniFocus not running when hook fires | `pgrep` check, skip silently |
| Task name mismatch | Mapping file provides ID-based matching; fuzzy fallback |
| Multiple plans with similar tasks | Scoped by mapping files; fallback search limited to AI Agent projects |
| Project with same name exists | Warn user, offer to append or create new |
| Duplicate hook fires (task already complete) | `task.completed = true` is idempotent in OmniFocus |

### Out of Scope (v1)

- Automatic OmniFocus → Claude Code sync (task changes in OF don't push to Claude; `/of:work` pulls on demand)
- Creating OmniFocus tasks for ad-hoc `TaskCreate` calls during implementation
- Updating plan markdown when tasks complete
- GitLab integration (GitHub only)
- Perspective creation (separate Pillar 2 effort)

## Acceptance Criteria

### /of:plan Command
- [x] Command at `plugins/omnifocus-manager/commands/of-plan.md` with correct frontmatter
- [x] Prompts user for destination: GitHub Issue | OmniFocus Project | Both | Skip
- [x] Parses plan phases and task lists from markdown
- [x] Creates OmniFocus project with action groups via `bulk-create`
- [x] Tags all tasks with `AI Agent / Claude Code` (nested)
- [x] Creates GitHub Issue via `gh issue create` when selected
- [x] Stores GitHub issue URL in OmniFocus project note when "Both" selected
- [x] Writes mapping file to `.claude/omnifocus-maps/` for hook matching

### bulk-create Action
- [x] New action in `manage_omnifocus.js` accepting JSON structure
- [x] Creates project, action groups, and tasks in single JXA invocation
- [x] Returns mapping of task names to OmniFocus IDs
- [x] Creates nested tags (`AI Agent / Claude Code`) via `findOrCreateTag`
- [x] Handles existing project name (warn, don't silently duplicate)

### PostToolUse Hook
- [x] Hook config at `plugins/omnifocus-manager/hooks/hooks.json`
- [x] Hook script at `plugins/omnifocus-manager/hooks/omnifocus-task-sync.sh`
- [x] Filters for `TaskUpdate` with `status: "completed"` only
- [x] Uses `.claude/omnifocus-maps/` mapping files for ID-based matching (primary)
- [x] Falls back to name search within AI Agent-tagged projects (secondary)
- [x] Pre-checks OmniFocus availability via `pgrep`
- [x] Logs to stderr and `/tmp/claude-omnifocus-hook.log`
- [x] Never blocks Claude Code (always exit 0)

### /of:work Command
- [x] Command at `plugins/omnifocus-manager/commands/of-work.md` with correct frontmatter
- [x] Accepts optional project name argument (skips selection if provided)
- [x] Queries OmniFocus for AI Agent-tagged projects with completion progress
- [x] Prompts user to select a project (if no argument given)
- [x] Reads project tasks in order, presents next incomplete task
- [x] Implements/verifies each task, marks complete in OmniFocus directly via `complete --id`
- [x] Reads linked plan file from project note for implementation context
- [x] Creates/updates mapping file in `.claude/omnifocus-maps/`

### ai-agent-tasks Query
- [x] New action in `gtd-queries.js`
- [x] New `searchTasksByTag` function in `taskQuery.js`
- [x] Lists all AI Agent-tagged tasks grouped by project
- [x] Shows completion progress per project
- [x] Supports `--tag` filter for child tags

### Infrastructure
- [x] `components.hooks` added to `plugin.json`
- [x] Nested tag creation tested (AI Agent / Claude Code)
- [x] Smoke test updated (`test-queries.sh`) for new actions
- [x] SKILL.md updated with new capabilities

## Implementation Phases

### Phase 1: Foundation (scripts + query)
1. Extend `findOrCreateTag` in `taskMutation.js` with nested tag support (parent/child)
2. Add `searchTasksByTag` to `taskQuery.js`
3. Add `ai-agent-tasks` action to `gtd-queries.js`
4. Add `bulk-create` action to `manage_omnifocus.js`
5. Update `test-queries.sh` smoke test
6. Test: manually create an AI Agent project with nested tags, query it

### Phase 2: Command (`/of:plan`)
1. Create `commands/of-plan.md` with frontmatter
2. Implement plan parsing instructions in command body
3. Wire up OmniFocus creation (calls `bulk-create`)
4. Wire up GitHub Issue creation (calls `gh issue create`)
5. Write mapping file to `.claude/omnifocus-maps/`; add directory to `.gitignore`
6. Test: publish a real plan to OmniFocus, verify mapping file created

### Phase 3: Agent Execution (`/of:work`)
1. Create `commands/of-work.md` with frontmatter
2. Implement project selection flow (query → prompt → select)
3. Implement task-by-task execution loop with OmniFocus completion
4. Wire up plan file context reading from project note
5. Test: run `/of:work` against a published project, verify step-by-step execution

### Phase 4: Hook (task-sync)
1. Create `hooks/hooks.json` with PostToolUse config
2. Create `hooks/omnifocus-task-sync.sh` script
3. Add `components.hooks` to `plugin.json`
4. Test standalone: `echo '{"tool_name":"TaskUpdate",...}' | ./hooks/omnifocus-task-sync.sh`
5. Test integrated: run `/ce:work` on a published plan, verify OmniFocus tasks complete

### Phase 5: Polish
1. Run skillsmith evaluation
2. Update SKILL.md with new capabilities
3. Update IMPROVEMENT_PLAN.md with version entry
4. Bump version in plugin.json

## Dependencies & Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PostToolUse hook doesn't receive TaskUpdate tool_name | Low | Critical | Test with echo hook first; the plugin-dev docs confirm matcher supports tool names |
| Mapping files accumulate in .claude/omnifocus-maps/ | Low | Low | Clean up when OmniFocus project is completed; files are small |
| JXA bulk-create fails partway through | Low | Medium | Wrap in try/catch, return partial results with error details |
| Nested tag creation has JXA quirks | Medium | Low | Test independently first; `findOrCreateTag` already exists |

## Sources & References

### Origin
- **Brainstorm document:** [docs/brainstorms/2026-03-02-omnifocus-plan-storage-brainstorm.md](docs/brainstorms/2026-03-02-omnifocus-plan-storage-brainstorm.md) — Key decisions: explicit slash command (not hook trigger), grouped-by-phase structure, nested AI Agent tag hierarchy, PostToolUse hook with script fallback

### Internal References
- Command pattern: `plugins/omnifocus-manager/commands/weekly-review.md`
- Task management: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/manage_omnifocus.js`
- JXA libraries: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/libraries/jxa/taskMutation.js`
- GTD queries: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/gtd-queries.js`
- Hook development: `plugin-dev:hook-development` skill
- Sync defense pattern: `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`

### Lessons Applied
- Script organization: validation tools in `scripts/`, not `assets/` (from `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`)
- Three-layer defense for sync: algorithm + detection + process (from `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md`)
- Progressive disclosure: critical workflows in first 100 lines (from refinement lessons)
- Hook verification: consult `plugin-dev:hook-development` before committing (from WORKFLOW.md)
