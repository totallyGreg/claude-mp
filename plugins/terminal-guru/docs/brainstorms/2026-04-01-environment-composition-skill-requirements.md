---
date: 2026-04-01
topic: environment-composition-skill
---

# Environment Composition Skill for terminal-guru

## Problem Frame

Development environments are assembled from multiple tools — tmux sessions (via sesh), claude CLI sessions, direnv environments, git worktrees — but each tool's lifecycle is managed independently. Setup requires manually composing these layers; teardown is ad-hoc, leading to stale sessions, lost AI context, accumulated worktrees, and outdated environment variables. There is no unified mental model or skill that guides composition and decomposition of these environments.

The Lens concept (borrowed from the user's Lensing idea) provides the organizing framework. A development environment is a composed Lens with four layers: Selection (what's included), Arrangement (how it's presented), Purpose (why it exists), and Activation (when to use it). The skill uses this framework internally and the agent applies it when suggesting tool combinations — but the framework lives in the skill, not in the Obsidian vault.

## Sesh as the Foundation Layer

Sesh (v2.24+) is the primary tool for environment management. Its config system (`sesh.toml`) already implements much of the Lens pattern natively:

| Lens Layer | Sesh Implementation |
|------------|-------------------|
| **Selection** | `path`, `[[wildcard]]` patterns, `sesh clone` |
| **Arrangement** | `[[window]]` definitions, `startup_command`, reusable named windows |
| **Purpose** | `[[session]]` names, git-aware naming strategy |
| **Activation** | Wildcard pattern matching, zoxide frecency, picker keybindings |

Key sesh capabilities the skill should leverage:
- **Wildcard configs** — Pattern-based templates (e.g., `~/projects/*` gets startup commands + window layouts automatically)
- **Config imports** — Split work/personal configs (`import = ["~/.config/sesh/work.toml"]`)
- **Startup commands** — Run commands on session creation (can launch `claude --resume`)
- **Reusable windows** — Named window definitions shared across sessions
- **`sesh clone`** — One-step clone + session creation
- **`sesh connect --root`** — Git worktree root navigation
- **Multiple pickers** — fzf, television (tv), gum, or built-in Bubble Tea picker

The skill's job is to teach users how to extend sesh's native capabilities with claude CLI, direnv, and worktrees — not to replace sesh's config system with a parallel one.

## Lens Composition in Practice

```
┌─────────────────────────────────────────────────────────┐
│                   Composed Environment                   │
│                     (Development Lens)                   │
├──────────────┬──────────────┬──────────────┬────────────┤
│  Selection   │ Arrangement  │   Purpose    │ Activation │
│              │              │              │            │
│ . sesh path/ │ . sesh       │ . Bug fix    │ . sesh     │
│   wildcard   │   windows    │ . Feature    │   wildcard │
│ . Git branch │ . sesh       │ . Review     │ . zoxide   │
│ . Worktree   │   startup_   │ . Customer   │   frecency │
│ . .envrc     │   command    │   support    │ . Picker   │
│   variables  │ . claude     │ . Exploration│   binding  │
│ . CLAUDE.md  │   session    │              │            │
│   config     │ . MCP        │              │            │
│              │   servers    │              │            │
└──────────────┴──────────────┴──────────────┴────────────┘
```

## Pattern Graduation Pipeline

Patterns move through three stages, mapped to the Lens lifecycle:

```
 Agent Suggests          User Saves             Proven Pattern
 (Composed)         →    (Emerging)         →   (Crystallized)

 Ad-hoc tool             .local.md +            Skill reference +
 combinations            sesh.toml              Obsidian Workflow
 suggested by            entries capture         note documents
 the agent               what works              the pattern
```

- **Composed** — The agent suggests a tool combination on the fly based on context (e.g., "You could add a `startup_command` to your sesh config that runs `claude --resume` to restore AI context alongside the terminal session")
- **Emerging** — The user saves patterns: sesh configs in `sesh.toml` for session layout, `.claude/terminal-guru.local.md` for composition preferences and proven combos
- **Crystallized** — Proven patterns graduate to skill references and are documented as Workflow notes in the Obsidian vault. The Lensing note links to this skill as a cross-tool implementation.

## Requirements

**Reference Material**

- R1. Claude CLI reference scoped to features that participate in environment composition: session management (`--resume`, `--continue`, session listing), project configuration (`CLAUDE.md`, `.claude/` directory, permissions), worktree integration, and MCP server configuration. Not a comprehensive CLI manual — only what the agent needs to suggest compositions.
- R2. Comprehensive sesh v2.24+ reference covering the full config system (`sesh.toml`): `[[session]]`, `[[wildcard]]`, `[[window]]`, `startup_command`, `preview_command`, config imports, `sesh clone`, `sesh connect --root`, naming strategies, caching, and picker integrations (fzf, television, gum, built-in). This is the foundation of environment composition and warrants thorough coverage.
- R3. direnv integration patterns as they relate to both sesh and claude CLI (environment variables flowing through tmux panes to agent context)

**Workflow Patterns**

- R4. Document combined setup patterns: sesh session creation + claude --resume for paired terminal/AI context restoration. Include how `startup_command` in sesh.toml can automate the claude CLI launch.
- R5. Document worktree composition: creating isolated git worktrees per tmux session for parallel feature work, each with its own claude session. Leverage `sesh connect --root` for navigation between worktrees.
- R6. Document teardown patterns: graceful shutdown sequences that preserve claude session state, clean worktrees, and kill tmux sessions without context loss
- R7. Document environment decay detection: identifying stale sessions, orphaned worktrees, outdated .envrc files

**Agent Behavior & sesh.toml as Local State**

- R8. The agent should suggest tool compositions based on the user's current context (project type, existing sessions, available tools), using the Lens layers as a mental checklist for what to compose. Suggestions should favor sesh-native solutions — outputting sesh.toml config snippets (`[[session]]`, `[[wildcard]]`, `startup_command` entries) that users add to their own sesh.toml.
- R9. ~~Local state file~~ Superseded: sesh.toml (`~/.config/sesh/sesh.toml`) naturally serves as the local state for environment composition. Users already maintain this file; no separate `.local.md` needed.
- R10. ~~Agent reads local state~~ Superseded: the agent suggests sesh.toml patterns; users iterate in sesh.toml directly. Proven patterns graduate to skill references.

**Skill Structure**

- R11. New skill directory at `plugins/terminal-guru/skills/environment-composition/` with SKILL.md and references
- R12. Skill triggers on: "set up dev environment", "compose environment", "create workspace", "teardown session", "clean up worktrees", "resume my session", "claude + tmux", "sesh config", "environment lens", "session template"
- R13. Cross-reference existing terminal-emulation tmux content rather than duplicating it. The general tmux session management reference stays in terminal-emulation; this skill owns sesh config patterns and multi-tool composition.
- R14. Update terminal-guru agent routing table to include environment-composition as a fourth skill
- R15. Update plugin.json description and version to reflect the new skill

## Success Criteria

- The agent can suggest relevant tool compositions when a user starts or resumes work, preferring sesh-native solutions
- Users learn to leverage sesh's config system (wildcards, windows, startup commands) as the primary environment management tool
- Teardown guidance prevents the three pain points: manual cleanup, context loss, environment drift
- Users iterate on their sesh.toml as the natural local state for environment composition
- Proven patterns have a clear path to graduate into skill references and Obsidian Workflow notes

## Scope Boundaries

- Not a general tmux tutorial — cross-reference terminal-emulation for that
- Not a claude CLI user manual — only features relevant to environment composition
- Does not implement automation scripts (documents patterns and commands for manual execution; helper scripts are a follow-up)
- Does not modify the Obsidian Lensing note — the Lensing note should link to this skill as an implementation; enhancements to the Lensing idea are welcome but happen separately
- Does not create sesh config files for the user — documents how to write them and the agent suggests configs

## Key Decisions

- **Sesh is the foundation, not a supplement**: Sesh's config system (`sesh.toml`) already implements most of the Lens pattern natively. The skill teaches users to extend sesh with claude CLI, direnv, and worktrees — not to build a parallel system.
- **New skill, not extending terminal-emulation**: The combined workflow patterns are a distinct capability. General tmux/sesh session management stays in terminal-emulation; multi-tool composition and sesh config mastery lives here.
- **Named "environment-composition"**: Broader than "claude-sessions" — captures the full composition pattern and is durable as tools evolve
- **Lensing borrowed, not validated**: The skill uses the four-layer Lens framework as internal structure. The Obsidian Lensing note links to this skill as a cross-tool implementation but the skill does not own Lensing validation.
- **Agent suggests, user discovers**: Instead of prescribing fixed workflows, the agent suggests compositions (favoring sesh-native solutions) and the user's local state captures what works. Best patterns graduate to references.
- **Claude CLI scoped to composition**: Reference covers only CLI features that participate in environment setup/resume/teardown, not a comprehensive manual.
- **Comprehensive sesh reference**: Unlike claude CLI (scoped), sesh gets thorough coverage because it is the foundational tool for environment management.
- **Picker flexibility**: Document fzf, television, gum, and built-in picker options. Don't prescribe one — let users choose via local state preferences.

## Dependencies / Assumptions

- sesh v2.24+ installed (confirmed: v2.24.2)
- claude CLI v2.x installed (confirmed: v2.1.81)
- direnv configured and working with tmux
- Existing tmux session management reference in terminal-emulation is accurate and current
- Plugin-settings pattern (`.claude/plugin-name.local.md` with YAML frontmatter) is established and documented in plugin-dev:plugin-settings skill
- User's Lensing note at `700 Notes/Ideas/Lensing` is the conceptual source; this skill borrows the framework

## Outstanding Questions

### Resolve Before Planning

(None — all product decisions resolved)

### Deferred to Planning

- [Affects R1][Needs research] What claude CLI features are available for programmatic session management (listing sessions, getting session IDs)? Verify via `claude --help` and docs.
- [Affects R4][Needs research] Can sesh `startup_command` reliably launch `claude --resume` with directory-based session matching?
- [Affects R6][Needs research] Can claude session state be reliably associated with a tmux session name or directory for automatic resume?
- [Affects R7][Technical] What tooling exists for detecting stale worktrees (`git worktree list --porcelain`) and orphaned tmux sessions?
- [Affects R9][Technical] What YAML frontmatter structure works best for storing composition preferences in `.local.md`? Check existing plugin-settings patterns.
- [Affects R14][Technical] What changes are needed in terminal-guru.md agent routing table for the fourth skill? Review current routing logic.

## Next Steps

→ `/ce:plan` for structured implementation planning
