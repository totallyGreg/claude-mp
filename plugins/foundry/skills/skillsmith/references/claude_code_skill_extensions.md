---
last_verified: 2026-10-18
sources:
  - type: web
    url: "https://code.claude.com/docs/en/skills"
    description: "Claude Code skills: frontmatter reference, listing cap, compaction"
  - type: web
    url: "https://code.claude.com/docs/en/sub-agents"
    description: "Subagent frontmatter; fields ignored for plugin agents"
  - type: web
    url: "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices"
    description: "Skill authoring best practices"
---

# Claude Code Skill Extensions

What Claude Code adds on top of the portable AgentSkills spec (`agentskills_specification.md`). Fields here work only in Claude Code. Other agents ignore them, and Claude Code ignores frontmatter fields it doesn't know.

## Frontmatter fields beyond the spec

| Field | Use it for |
|---|---|
| `when_to_use` | Trigger phrases and example requests. Appended to `description` in the skill listing |
| `argument-hint` | Autocomplete hint, e.g. `[issue-number]` |
| `arguments` | Named positional arguments for `$name` substitution |
| `disable-model-invocation: true` | Side-effect workflows (deploy, commit, publish) the user should trigger with `/name`. Also blocks preloading the skill into subagents |
| `user-invocable: false` | Background knowledge only Claude should load. Hides the skill from the `/` menu |
| `allowed-tools` / `disallowed-tools` | Pre-approve or remove tools for the turn that invokes the skill |
| `model`, `effort` | Override the model or effort level while the skill is active |
| `context: fork` + `agent` | Run the skill in a forked subagent (`background: false` to wait for it) |
| `hooks` | Hooks registered when the skill is invoked |
| `paths` | Glob patterns; auto-load only when working with matching files |
| `shell` | `bash` (default) or `powershell` for inline `` !`cmd` `` blocks |

`metadata` is free-form and Claude Code doesn't act on it; keep `metadata.version` as a quoted string.

## Description limits

- Spec: `description` ≤ 1,024 characters.
- Claude Code: `description` + `when_to_use` are truncated at **1,536 characters** in the skill listing. Put the key use case first.
- Write in third person. "I can help..." or "You can use this..." causes discovery problems because the description is injected into the system prompt.
- The house opener "This skill should be used when..." is valid but spends the first characters on boilerplate. Prefer "Does X. Use when users ask to ..." for new skills.

## Context budget

- The skill listing (all names + descriptions) costs context every turn. `/skill-doctor` shows per-skill cost and usage; `/doctor` estimates listing cost.
- After auto-compaction, Claude Code re-attaches the most recent invocation of each skill, **first 5,000 tokens each, 25,000 tokens shared**. Older skills drop first. This is another reason to keep SKILL.md lean.
- "Keep SKILL.md under 500 lines" and "<5,000 tokens" are spec guidance. Skillsmith's stricter token targets are house rules (see `progressive_disclosure_discipline.md`).

## Commands vs skills

`commands/*.md` is the older format and "still works"; it accepts the same frontmatter except `name` and `paths`. This marketplace keeps one skill per capability plus thin `commands/<verb>.md` wrappers (with `argument-hint` and `$ARGUMENTS`) exposed as `/plugin:verb`. Give commands names distinct from skill names (`ss-`, `as-`, `mp-` prefixes) so neither shadows the other.

## Plugin-shipped agents

Plugin agents ignore `hooks`, `mcpServers`, and `permissionMode` "for security reasons". Enforce boundaries with the agent's `tools` / `disallowedTools` list or with the plugin's own `hooks/hooks.json`. Agentsmith warns when a plugin agent sets an ignored field.

## Audit tools

| Tool | What it does |
|---|---|
| `claude plugin validate <dir> --strict` | Manifest, paths, hook quoting, reserved names |
| `/skill-doctor` | Per-skill context cost and usage |
| `/doctor prompt-audit` | Outdated or conflicting instructions in CLAUDE.md and skills |
| `/claude-api prompt-audit` | Instructions written for older models |
| `claude plugin eval` | Behavioural evals with/without the plugin (see #220) |
