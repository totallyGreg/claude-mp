---
title: "feat: Add WTF (Work the Foundry) friction reporter skill"
type: feat
status: active
date: 2026-05-08
deepened: 2026-05-08
---

# feat: Add WTF (Work the Foundry) friction reporter skill

## Summary

Add a lightweight, proactive friction-reporting skill to the foundry plugin. WTF captures "this should've been easier" moments as structured markdown files in a gitignored `.local/agent-issues/` directory, feeding accumulated friction into the existing skillsmith/agentsmith improve workflows so fixes are informed by real pain.

---

## Problem Frame

When Claude encounters broken tools, misleading skills, bad docs, or unnecessary trial-and-error during normal work, it grinds through the problem and moves on. The friction is never captured. Later, when a skill or agent is improved via `/ss-improve` or `/as-improve`, the improvement loop only has structural analysis (skill-observer gap reports) and evaluation scores — it has no record of *what actually hurt* during real usage. WTF closes this feedback loop.

The concept originates from a "Code with Claude" conference talk proposing a "Work on The Factory" skill where agents proactively file dev-experience friction. This plan adapts that concept for the foundry plugin ecosystem.

---

## Requirements

- R1. Claude must be able to proactively file friction reports during normal work without explicit user instruction
- R2. Friction reports must be persisted durably across sessions (not ephemeral stdout)
- R3. Reports must carry structured metadata: type (skill/agent/tool/workflow), name (plugin:skill-name), category, description, project path, session ID, and ISO-8601 date
- R4. The storage mechanism must NEVER expose friction data publicly (claude-mp is a public repo)
- R5. `/ss-improve` and `/as-improve` must be able to query accumulated friction for the skill/agent being improved
- R6. Users must be able to explicitly file friction via `/ss-wtf` command

### Deferred Requirements

- R7. (Deferred) A PostToolUse hook to nudge Claude when it detects repeated failures — ship without it first; add if the proactive SKILL.md trigger proves insufficient in practice

---

## Scope Boundaries

- WTF captures and stores friction — it does NOT analyze or fix it (that's skillsmith/agentsmith's job)
- No new Python evaluation scripts — the submit mechanism is a bash script writing files to a directory
- No GitHub Issues integration for friction reports (security: public repo would expose sensitive data)
- No cross-repo friction aggregation — reports are scoped to the claude-mp working tree
- Friction reports are *input* to improve workflows, not a replacement for them
- No PostToolUse hook in v1 — the proactive SKILL.md description is the trigger mechanism; hook deferred until real-world usage shows it's needed

### Deferred to Follow-Up Work

- **Vault integration**: Surfacing friction reports in the Obsidian vault (linked to agent/skill notes, viewable in Bases views) — requires a separate brainstorm (`/ce-brainstorm`) touching archivist, vault schema, and the agent/skill note structure
- **PostToolUse nudge hook**: If Claude grinds through friction without self-reporting, add a hook on Bash failures to inject a nudge (see deferred R7)
- **Friction burndown dashboard**: A `/ss-wtf-status` command showing accumulated friction by skill/agent with trends
- **Automated triage routing**: Hook that auto-routes high-frequency friction to the correct improve workflow

---

## Context & Research

### Relevant Code and Patterns

- `plugins/foundry/hooks/scripts/on-skill-edit.sh` — canonical hook script template (JSON stdin, python3 parsing, exit codes 0/2) for when deferred hook is implemented
- `plugins/foundry/commands/ss-improve.md` — skillsmith improve workflow (where friction query integrates at Step 0d)
- `plugins/foundry/commands/as-improve.md` — agentsmith improve workflow (where friction query integrates at Step 0b)
- `plugins/foundry/agents/skill-observer/` — structural gap detection (complementary, not overlapping)
- `.gitignore` — will need a `.local/` entry to keep friction reports out of git

### Institutional Learnings

- **Delegation principle** (agentsmith memory): WTF should *capture* friction and let existing tools *analyze* it. Don't replicate skillsmith/agentsmith evaluation logic.
- **Workflow simplification** (`docs/lessons/workflow-simplification.md`): A previous git-branch workflow (skill-planner) was deprecated for being too ceremonious. WTF avoids this by using a simple gitignored directory — no branches, no tags, no plumbing. Keep the interaction surface minimal.
- **Multi-skill plugin version sync** (`docs/solutions/`): Automated tools that silently pass are dangerous. WTF must always surface detected friction, never silently skip.
- **Self-improvement loop gap** (`docs/solutions/agent-design/`): No mechanism currently exists for agents to prevent repeating mistakes. WTF + improve workflow integration is the first step toward closing this loop.

---

## Key Technical Decisions

- **Gitignored `.local/` directory** (not a git branch, not GitHub Issues): R4 requires friction data stay private. A `.local/agent-issues/reports/` directory is gitignored, durable across sessions, and requires zero git ceremony. The original conference talk used git plumbing for cross-branch isolation — we don't need that since friction is a simple append-only log. A directory achieves the same durability and privacy in ~10 lines vs. ~200 lines of git plumbing. (Scope guardian review confirmed this simplification.)
- **Proactive trigger via skill description** (not hook-based detection): The SKILL.md description tells Claude "Use PROACTIVELY" — Claude's own judgment decides when friction is worth reporting. Hook deferred to follow-up work.
- **Inline friction query in improve commands** (no standalone query script): Only two consumers exist (`ss-improve`, `as-improve`), both doing the same simple `find` + `grep` filter. A standalone `query-issues.sh` would be a premature abstraction for hypothetical future consumers. Inline the query directly.
- **Metadata schema uses YAML frontmatter**: Consistent with SKILL.md/AGENT.md patterns in this repo. Enables `grep`/`rg` queries by field.
- **Command prefix `ss-wtf`**: Groups with skillsmith commands since friction reports primarily feed skill/agent improvement. The `wtf` part is the memorable shorthand.

---

## Open Questions

### Resolved During Planning

- **Where do friction reports live?**: In `.local/agent-issues/reports/` within the claude-mp repo, gitignored. Durable, private, zero ceremony.
- **How does Claude know which skill/agent is causing friction?**: Claude always knows what it's doing. The SKILL.md instructs Claude to include the active skill/agent name, type, and category in the report metadata.
- **Why not a git branch?**: The scope guardian review showed git plumbing is 20x the complexity for the same guarantees. A gitignored directory is the right abstraction for an append-only log with no versioning, rollback, or history requirements.
- **Why no hook in v1?**: The proactive SKILL.md description and the hook are redundant triggers. Ship the simpler mechanism first; add the hook if proactive triggering proves insufficient.

### Deferred to Implementation

- **Friction report filename collision**: Reports need unique filenames. Timestamp + PID or short random suffix should suffice, but exact format TBD.

---

## Output Structure

```
plugins/foundry/skills/wtf/
  SKILL.md                    # Proactive trigger description + submit instructions
  scripts/
    submit-issue.sh           # Write friction report to .local/agent-issues/reports/
plugins/foundry/commands/
  ss-wtf.md                   # Explicit user-facing friction filing command
.local/agent-issues/reports/  # Gitignored friction report storage (created at runtime)
```

---

## High-Level Technical Design

> *This illustrates the intended approach and is directional guidance for review, not implementation specification. The implementing agent should treat it as context, not code to reproduce.*

```
Normal work session
  │
  ├─ Claude hits friction ──────────────────┐
  │  (proactive, via SKILL.md trigger)      │
  │                                         ▼
  │                              ┌─────────────────────┐
  │                              │   submit-issue.sh    │
  │                              │                      │
  │                              │  mkdir -p .local/... │
  │                              │  write YAML+markdown │
  │                              │  to reports/ dir     │
  │                              └──────────┬───────────┘
  │                                         │
  │                                         ▼
  │                              .local/agent-issues/reports/
  │                              (gitignored, never committed)
  │                              ┌─────────────────────┐
  │                              │ 2026-05-08-a1b2.md  │
  │                              │ 2026-05-09-c3d4.md  │
  │                              └──────────┬───────────┘
  │                                         │
  Later: /ss-improve <skill>                │
  │                                         │
  ├─ Step 0d: inline grep/find ◄────────────┘
  │  filter by name == <skill>
  │
  ▼
  Friction context added to improve loop
```

---

## Implementation Guidance

**Use foundry's own tools to build this skill.** WTF lives inside the foundry plugin — its creation should be guided by the same tooling it will eventually report friction about:

- **U1 (submit script)**: Standard bash — no foundry tooling applies here.
- **U2 (SKILL.md)**: Use `/ss-init` to scaffold the skill with correct structure, then iterate with `evaluate_skill.py --explain` during authoring to hit quality targets. Do not write SKILL.md freehand and evaluate after the fact.
- **U6 (metadata)**: Run the full `/ss-improve` loop as the quality gate, not a bare eval check. This exercises the same improve workflow that U4/U5 are modifying.

This is eating-your-own-dog-food by design — and notably, the kind of friction that WTF itself would eventually catch if someone built a foundry skill without using foundry tools.

---

## Implementation Units

### U1. Create `submit-issue.sh` script

**Goal:** Write a bash script that creates a friction report file in `.local/agent-issues/reports/`.

**Requirements:** R2, R4

**Dependencies:** None

**Files:**
- Create: `plugins/foundry/skills/wtf/scripts/submit-issue.sh`

**Approach:**
- Accept structured arguments: `--type`, `--name`, `--category`, `--description`, `--project`, `--session`
- Determine the repo root via `git rev-parse --show-toplevel`
- `mkdir -p "$repo_root/.local/agent-issues/reports"`
- Generate a markdown file with YAML frontmatter from the arguments, adding ISO-8601 date automatically
- Filename format: `YYYY-MM-DD-HHMMSS-$$` (timestamp + PID for uniqueness)
- Write the file to the reports directory
- Ensure `.local/` is in `.gitignore` (check and append if missing)
- Exit 0 on success with confirmation to stdout, exit 1 on failure with error to stderr
- Script must be executable and work from any directory within the repo

**Patterns to follow:**
- Existing hook scripts in `plugins/foundry/hooks/scripts/` for bash style (`set -uo pipefail`)

**Test scenarios:**
- Happy path: Script creates a report file with correct YAML frontmatter and description content
- Happy path: Multiple invocations create separate files without collision
- Edge case: Script creates `.local/agent-issues/reports/` directory on first invocation
- Edge case: Script appends `.local/` to `.gitignore` if not already present
- Error path: Script exits with error when run outside a git repository
- Error path: Script exits with error when required `--description` argument is missing

**Verification:**
- Report files appear in `.local/agent-issues/reports/` with valid YAML frontmatter
- `.local/` appears in `.gitignore`
- `git status` does not show the reports directory (gitignored)

---

### U2. Create WTF SKILL.md

**Goal:** Write the proactive skill definition that triggers Claude to self-report friction during normal work.

**Requirements:** R1, R3

**Dependencies:** U1

**Files:**
- Create: `plugins/foundry/skills/wtf/SKILL.md`

**Approach:**
- Description uses "Use PROACTIVELY" phrasing to trigger self-invocation
- Keep the skill body ultra-lightweight — just enough to instruct Claude on:
  1. When to file (friction categories: bad-docs, broken-tool, misleading-skill, missing-prereq, auth-failure, flaky, other)
  2. How to call `submit-issue.sh` (argument format)
  3. What metadata to include (all R3 fields)
  4. How to identify the active skill/agent (Claude's own context awareness)
- No references/ directory needed — the skill is intentionally minimal
- Explicitly instruct Claude to continue its current task after filing — friction reporting is a side-effect, not a workflow interruption
- Target: under 80 lines total to minimize context weight

**Patterns to follow:**
- Proactive skill description pattern (similar to `coding-standards:coding-standards` which says "Proactively apply when implementing features")
- Foundry SKILL.md frontmatter format (name, description, metadata with version, compatibility, license)

**Test scenarios:**
- Happy path: Skill description contains "PROACTIVELY" and lists all friction categories
- Happy path: Skill body includes `submit-issue.sh` invocation instructions with all R3 metadata fields
- Edge case: Skill instructs Claude to continue working after filing (not interrupt the task)

**Verification:**
- `evaluate_skill.py` runs without errors on the new skill
- Skill body is under 80 lines
- All R3 metadata fields are documented in the skill instructions

---

### U3. Create `/ss-wtf` slash command

**Goal:** Provide an explicit user-facing command for friction reporting and review.

**Requirements:** R6

**Dependencies:** U1, U2

**Files:**
- Create: `plugins/foundry/commands/ss-wtf.md`

**Approach:**
- Accept optional `$ARGUMENTS` as a description of the friction
- If no arguments, prompt Claude to ask the user what went wrong
- Gather context: active skill/agent (from conversation), project path, session ID
- Call `submit-issue.sh` with the gathered metadata
- Report what was filed and where (directory path, filename)
- Support `$ARGUMENTS` of "list" or "show" to list accumulated friction reports via `find` + frontmatter parsing

**Patterns to follow:**
- `/ss-observe` command format (YAML frontmatter with name, description, argument-hint)
- Existing `ss-*` command naming convention

**Test scenarios:**
- Happy path: `/ss-wtf "the archivist skill didn't handle empty vaults"` files a report with correct metadata
- Happy path: `/ss-wtf list` shows accumulated friction reports with summary info
- Edge case: `/ss-wtf` with no arguments prompts for description interactively
- Edge case: `/ss-wtf list` with no reports shows "No friction reports found"

**Verification:**
- Command frontmatter has correct name, description, and argument-hint fields
- Command references `${CLAUDE_PLUGIN_ROOT}` for script paths

---

### U4. Integrate friction query into `/ss-improve`

**Goal:** Add a friction-check step to the skillsmith improvement workflow so accumulated friction reports inform improvements.

**Requirements:** R5

**Dependencies:** U1

**Files:**
- Modify: `plugins/foundry/commands/ss-improve.md`

**Approach:**
- Add a new **Step 0d** after existing Step 0c (auto-patch frontmatter), before Step 1 (evaluate)
- Step 0d: Find friction reports matching the target skill name using inline `find` + `grep`:
  ```
  find "$repo_root/.local/agent-issues/reports" -name "*.md" -exec grep -l "name:.*<skill-name>" {} \;
  ```
- If matching reports found: read and summarize them as "Friction context" before the evaluation — these are real user pain points to prioritize
- If no reports found or directory doesn't exist: skip silently
- The friction context is *advisory* — it informs which improvements to prioritize, not which scores to chase

**Patterns to follow:**
- Step 0b/0c pattern in existing ss-improve (conditional steps with silent skip)

**Test scenarios:**
- Happy path: When friction reports exist for the skill, they appear as context before Step 1 evaluation
- Happy path: When no friction reports exist, Step 0d is skipped silently with no output
- Edge case: When `.local/agent-issues/reports/` directory doesn't exist, Step 0d is skipped silently

**Verification:**
- `/ss-improve` for a skill with accumulated friction shows the friction context
- `/ss-improve` for a skill without friction proceeds normally (no regression)

---

### U5. Integrate friction query into `/as-improve`

**Goal:** Add the same friction-check step to the agentsmith improvement workflow.

**Requirements:** R5

**Dependencies:** U1

**Files:**
- Modify: `plugins/foundry/commands/as-improve.md`

**Approach:**
- Add a new **Step 0b** (between existing Step 0a and Step 1) that queries friction reports with `find` + `grep` for the agent name
- Same pattern as U4 — advisory friction context, silent skip when empty

**Patterns to follow:**
- U4 implementation in ss-improve

**Test scenarios:**
- Happy path: When friction reports exist for the agent, they appear as context before Step 1 evaluation
- Happy path: When no friction reports exist, the step is skipped silently

**Verification:**
- `/as-improve` for an agent with accumulated friction shows the friction context
- `/as-improve` for an agent without friction proceeds normally

---

### U6. Update foundry plugin metadata and documentation

**Goal:** Register the new skill and command in the foundry plugin documentation.

**Requirements:** None (housekeeping)

**Dependencies:** U1–U5

**Files:**
- Modify: `plugins/foundry/README.md`
- Modify: `plugins/foundry/.claude-plugin/plugin.json` (version bump)
- Modify: `.claude-plugin/marketplace.json` (version sync)
- Modify: `.gitignore` (ensure `.local/` entry)

**Approach:**
- Add `## Skill: wtf` section to foundry README.md with Current Metrics and initial Changelog entry
- Update Components section: Skills count (3 → 4), Commands count (14 → 15)
- Follow the two-commit release strategy from WORKFLOW.md:
  - First commit: all implementation files (U1–U5)
  - Second commit: version bump in plugin.json, README.md changelog entry, marketplace.json sync

**Patterns to follow:**
- Existing `## Skill: skillsmith` section format in foundry README.md
- Two-commit release strategy from WORKFLOW.md

**Test scenarios:**
Test expectation: none — documentation and metadata update only.

**Verification:**
- `evaluate_skill.py` runs successfully on the new skill
- `validate.py` passes on marketplace.json
- README.md stays within bounded size

---

## System-Wide Impact

- **Interaction graph:** WTF touches the improve workflows (`ss-improve`, `as-improve`) at a single well-defined insertion point (new Step 0d/0b). No hooks are modified in v1.
- **Error propagation:** `submit-issue.sh` failures are informational (exit 1 + stderr), never blocking. Improve workflow friction queries skip silently on any error. WTF must never interrupt the user's primary task.
- **State lifecycle risks:** The `.local/agent-issues/reports/` directory accumulates reports indefinitely. No cleanup mechanism is included in v1 — this is a conscious choice to avoid premature pruning. Burndown/cleanup is deferred.
- **Security invariant:** The `.local/` directory is gitignored and never committed. Friction reports may contain project paths, error messages, and other context that must not be public. The `.gitignore` entry is the critical security control — `submit-issue.sh` verifies it exists and appends it if missing.
- **Unchanged invariants:** Existing hooks continue to function identically. Existing improve workflows behave identically when no friction reports exist (silent skip).

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| **Security: friction reports accidentally committed** | `.local/` in `.gitignore`; `submit-issue.sh` verifies and auto-appends the entry. Pre-commit hook would catch if `.gitignore` is bypassed. |
| **Context weight: SKILL.md loaded unnecessarily** | Keep SKILL.md under 80 lines. The proactive trigger description is the primary cost — worth it for the feedback loop it enables. |
| **Noise: too many friction reports filed** | SKILL.md instructs Claude to file only when friction matches a defined category and is actionable. |
| **Directory cleanup: reports accumulate indefinitely** | Acceptable in v1. Reports carry dates for manual cleanup. Burndown mechanism deferred. |
| **Proactive trigger insufficient** | If Claude doesn't self-trigger enough, the deferred PostToolUse hook (R7) can be added as a follow-up. |

---

## Documentation / Operational Notes

- `.local/agent-issues/reports/` will appear on disk but not in `git status` — document this in the skill README so users aren't surprised
- Reports can be manually reviewed: `ls .local/agent-issues/reports/` and `cat` individual files
- To clear accumulated friction: `rm .local/agent-issues/reports/*.md`

---

## Follow-On: Vault Integration Brainstorm

The user has identified a desire to surface friction reports in the Obsidian vault, connecting to existing agent/skill notes, workflow documentation, and Bases views. This requires a separate brainstorm (`/ce-brainstorm`) covering:

- How friction notes relate to agent/skill notes (wikilink structure)
- Whether the vault is a *view layer* over the `.local/` directory or the *primary store*
- Bases view design for friction burndown
- Archivist integration for reading/writing friction notes
- The coupling between foundry (claude-mp repo) and the vault (separate system)

This is explicitly deferred from the current plan to keep the core WTF skill self-contained.

---

## Sources & References

- Conference talk slide: "wtf — Work on The Factory" (Code with Claude, 2026)
- `docs/lessons/workflow-simplification.md` — Prior art on git-branch workflows (validates simplicity-first approach)
- `docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md` — Self-improvement loop gap analysis
- `docs/solutions/logic-errors/multi-skill-plugin-version-sync.md` — Silent failure anti-pattern
