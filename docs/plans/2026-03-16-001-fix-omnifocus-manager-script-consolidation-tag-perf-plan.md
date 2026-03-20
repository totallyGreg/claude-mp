---
title: "fix: omnifocus-manager script consolidation, tag query performance, and architecture clarity"
type: fix
status: active
date: 2026-03-16
issues: ["#98", "#101"]
origin: "800 Generated/820 Brainstorms/2026-03-16-omnifocus-manager-plugin-clarity-brainstorm.md"
---

# fix: omnifocus-manager Script Consolidation, Tag Query Performance, and Architecture Clarity

## Overview

Three improvements to the `omnifocus-manager` Claude Code plugin:

1. **#98 — Heredoc dispatcher**: Merge 7 separate Omni Automation `.js` files into a single inlined heredoc in `scripts/ofo`, eliminating the one-time `ofo setup` requirement
2. **#101 — Tag query performance**: Replace `doc.flattenedTasks()` full scan with `tag.tasks()` direct lookup in `taskQuery.js`; add `/ofo-tagged` lightweight command
3. **Architecture clarity**: Update `omnifocus-agent` description to reflect cross-tool orchestration scope; add bridge pattern to new `CONTRIBUTING.md`

## Problem Statement

### #98 — Setup Friction
`run_action()` in `scripts/ofo` reads each command's `.js` file from `scripts/omni-actions/` at runtime, URL-encodes it, and opens `omnifocus://localhost/omnijs-run?script=...`. OmniFocus fingerprints each unique script, so a fresh install requires `ofo setup` to pre-approve all 7 scripts individually.

With a single inlined script, OmniFocus's one-time approval fires on the first `ofo` command ever run — no setup step needed.

### #101 — Tag Query Performance
`taskQuery.js` `getTasksByTagGrouped()` and `searchTasksByTag()` both use `doc.flattenedTasks()` (full database scan) to find tasks with a given tag. Routing through `omnifocus-manager:omnifocus-agent` adds ~8 minutes of subagent overhead on top of the scan.

Measured: ~490,000ms via agent vs ~870ms via direct JXA with `tag.tasks()`.

### Architecture Boundary Confusion
No documentation defines where new repeatable logic should live (ofo CLI vs Attache plugin). `omnifocus-agent` description understates its cross-tool role (Obsidian export, Claude Code task execution).

## Proposed Solution

### #98 — Single Heredoc Dispatcher

Replace `run_action()` to build and pass the entire Omni Automation JS inline as a bash heredoc. The JS dispatcher routes on an `action` field in the JSON argument:

```javascript
// Inlined in scripts/ofo as a heredoc — single script, one approval
var arg = JSON.parse(document.windows[0].selectedTab.evaluateJavaScript("document.__ofoArg") || '{}');
switch (arg.action) {
  case 'info':    return ofoInfo(arg);
  case 'complete': return ofoComplete(arg);
  // ... etc
}
```

**Variable data** continues to flow through the `&arg=` JSON parameter, unchanged from current behavior.

Remove `cmd_setup()` entirely — no longer needed.

### #101 — Direct Tag Lookup

Replace `doc.flattenedTasks()` iteration with direct `tag.tasks()` calls:

```javascript
// BEFORE (full scan — O(n) over all tasks)
var tasks = doc.flattenedTasks().filter(t => matchTagIds.includes(t.tags[0]?.id));

// AFTER (direct lookup — O(k) where k = tasks with this tag)
var parentTag = doc.flattenedTags.whose({ name: tagName })[0]; // guard: check .length > 0
var tasks = parentTag.tasks();
// For child tags: iterate parentTag.flattenedTags() and collect .tasks() from each
```

Add `/ofo-tagged <tag>` slash command that calls `gtd-queries.js` via `osascript` directly, bypassing the agent for interactive use.

### Architecture: CONTRIBUTING.md + Agent Description

New `CONTRIBUTING.md` at repo root documents the bridge pattern: ofo CLI scripts are source of truth; when logic is repeatable/codifiable AND useful inside OmniFocus natively, it is also surfaced in Attache assets.

Update `omnifocus-agent.md` description to reflect orchestration role across tools.

## Technical Considerations

### #98 — Heredoc Size and URL Encoding
Current `run_action()` URL-encodes the `.js` file content. Inlining all 7 scripts (~several hundred lines combined) into a single heredoc increases the URL length. OmniFocus's `omnijs-run` URL handler should handle this, but it warrants testing across the largest script (likely `ofo-create.js` or `ofo-list.js`).

**Mitigation:** Minify whitespace in the heredoc. Test with `ofo list` (largest result set) and `ofo create` (most complex args) first.

### #101 — Child Tag Traversal
The current implementation resolves child tags via `doc.flattenedTags.whose()` then builds a `matchTagIds` set. With `tag.tasks()`, we need to:
1. Get `parentTag.tasks()` — tasks with the tag directly
2. Iterate `parentTag.flattenedTags()` — child tags — and collect `.tasks()` from each

This preserves existing grouping behavior while eliminating the full scan.

**Empty tag guard (from institutional learnings):** Always check `.length > 0` before indexing `whose()` results:
```javascript
var tags = doc.flattenedTags.whose({ name: tagName })();
if (!tags.length) return { error: "Tag not found: " + tagName };
var parentTag = tags[0];
```

### #101 — Routing Bypass for Fast Queries
For `/ofo-tagged` command, call `gtd-queries.js` via `osascript` directly in the command, not through the `omnifocus-manager:omnifocus-agent`. This is already the pattern used in `/ofo-health`, `/ofo-today` and others.

### #98 — `ofo-expound` Missing Action (Side Note)
Research found `ofo-expound.md` references `--action list-tags` which does not exist in `gtd-queries.js`. This is a pre-existing bug outside scope, but worth noting for a follow-up issue.

## Implementation Phases

### Phase 1: #101 — Tag Query Fix (Lower Risk, Higher Value)
Fix first since it's a pure improvement with no structural changes.

1. **Fix `taskQuery.js`** — Replace `doc.flattenedTasks()` with `tag.tasks()` in both:
   - `searchTasksByTag` (line 310)
   - `getTasksByTagGrouped` (line 357)
   - Add `.length > 0` guard on `whose()` results (line 342 and equivalent in `searchTasksByTag`)
   - Update child-tag traversal to use `parentTag.flattenedTags()` + `.tasks()` per child

2. **Add `--action tagged-tasks` to `gtd-queries.js`** — New action that accepts `--tag <name>` and returns tasks grouped by project, formatted for interactive display

3. **Create `commands/ofo-tagged.md`** — Lightweight command invoking `gtd-queries.js --action tagged-tasks` directly via osascript

4. **Run JXA validator** — `node scripts/validate-jxa-patterns.js` on modified `taskQuery.js`

5. **Test** — Query `"AI Agent 🤖"` tag directly and via `/ofo-work` to verify timing improvement

### Phase 2: #98 — Heredoc Dispatcher
Structural change — do after Phase 1 to keep diffs clean.

1. **Combine all 7 `.js` files** from `scripts/omni-actions/` into a single dispatcher function (bash heredoc variable in `scripts/ofo`)

2. **Update `run_action()`** — Pass the heredoc instead of reading from file. Route on `action` field in arg JSON.

3. **Remove `cmd_setup()`** function and its `case` entry from the main dispatcher

4. **Delete `scripts/omni-actions/`** directory

5. **Update `SKILL.md`** — Remove "Run `scripts/ofo setup` once..." from Quick Decision Tree (line 97) and any other setup references

6. **Test** — Fresh approval: run any `ofo` command on a machine where OmniFocus hasn't seen the new script. Verify single approval dialog fires. Run `ofo info`, `ofo list`, `ofo create`, `ofo complete` end-to-end.

### Phase 3: Architecture Clarity

1. **Update `omnifocus-agent.md` description** — Change lines 5-8 to reflect cross-tool orchestration

2. **Create `CONTRIBUTING.md`** at repo root — Document the bridge pattern, SOLID principles, workflow references

3. **Version bump** — Increment `omnifocus-manager` plugin version for Phase 1+2 changes; run skillsmith eval

## Acceptance Criteria

### #98
- [ ] `ofo setup` command is removed (deleted from `ofo` script and SKILL.md)
- [ ] `scripts/omni-actions/` directory is deleted
- [ ] First `ofo` command on a fresh OmniFocus install triggers exactly one approval dialog
- [ ] All commands (`info`, `complete`, `create`, `update`, `search`, `list`, `perspective`) work end-to-end
- [ ] SKILL.md no longer mentions setup prerequisite

### #101
- [ ] `searchTasksByTag` uses `tag.tasks()` — no `flattenedTasks()` call
- [ ] `getTasksByTagGrouped` uses `tag.tasks()` — no `flattenedTasks()` call
- [ ] Empty tag name returns graceful error (no array-index-out-of-bounds)
- [ ] `/ofo-work` with `"AI Agent 🤖"` tag resolves in under 5 seconds
- [ ] `/ofo-tagged <tag>` command works and bypasses agent routing
- [ ] JXA validator passes on modified `taskQuery.js`

### Architecture
- [ ] `omnifocus-agent.md` description mentions Obsidian export and Claude Code task execution as use cases
- [ ] `CONTRIBUTING.md` exists at repo root with bridge pattern documented
- [ ] Skillsmith eval run and score recorded in IMPROVEMENT_PLAN.md

## Files to Change

| File | Change |
|---|---|
| `skills/omnifocus-manager/scripts/ofo` | Phase 1: none; Phase 2: heredoc dispatcher + remove `cmd_setup` |
| `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js` | Phase 1: replace `flattenedTasks()` with `tag.tasks()`; add `.length` guard |
| `skills/omnifocus-manager/scripts/gtd-queries.js` | Phase 1: add `tagged-tasks` action |
| `plugins/omnifocus-manager/commands/ofo-tagged.md` | Phase 1: new file |
| `skills/omnifocus-manager/scripts/omni-actions/` | Phase 2: delete directory |
| `skills/omnifocus-manager/SKILL.md` | Phase 2: remove setup references; Phase 3: version bump |
| `agents/omnifocus-agent.md` | Phase 3: update description |
| `CONTRIBUTING.md` | Phase 3: new file at repo root |

## Dependencies & Risks

| Risk | Mitigation |
|---|---|
| Heredoc URL length exceeds OmniFocus limit | Test with largest script first; minify whitespace |
| `tag.tasks()` JXA API differs from Omni Automation | Confirm JXA syntax (`parentTag.tasks()`) with validate-jxa-patterns.js |
| Child-tag grouping behavior changes | Verify `/ofo-work` still groups AI Agent subtags correctly |
| `whose()` returning empty throws on index | Add `.length > 0` guard per institutional learnings |

## Sources & References

### Origin
- **Brainstorm document:** `800 Generated/820 Brainstorms/2026-03-16-omnifocus-manager-plugin-clarity-brainstorm.md` — Key decisions carried forward: (1) bridge pattern = ofo scripts → Attache; (2) agent slug unchanged, description updated; (3) #98 and #101 are independent phases

### Internal References
- `skills/omnifocus-manager/scripts/ofo:56-93` — current `run_action()` reads from `omni-actions/`
- `skills/omnifocus-manager/scripts/ofo:240-271` — `cmd_setup()` to be removed
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js:310` — `searchTasksByTag` full scan
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js:357` — `getTasksByTagGrouped` full scan
- `skills/omnifocus-manager/scripts/libraries/jxa/taskQuery.js:342` — `whose()` index without length guard
- `agents/omnifocus-agent.md:5-8` — description field to update

### Institutional Learnings
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — JXA API asymmetry, `whose()[0]` throws on empty, AppleScript bridge patterns
- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — Script organization, path management, release process verification

### Related Issues
- #98: ofo: consolidate 6 action scripts into single dispatcher
- #101: feat: direct JXA path for tag queries — bypass agent overhead

### Side Note (Out of Scope)
- `ofo-expound.md` references `--action list-tags` which does not exist in `gtd-queries.js` — file a follow-up issue
