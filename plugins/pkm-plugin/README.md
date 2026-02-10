# PKM Plugin

Personal Knowledge Management expert for Obsidian vaults with autonomous orchestration.

## Usage

Ask Claude to help with Obsidian PKM tasks. The `pkm-manager` agent will orchestrate vault analysis, template creation, and system optimization.

**Examples:**
- "Analyze my vault and suggest improvements"
- "Create a customer meeting note template"
- "Help me set up a temporal rollup system"

## Configuration

Copy `.local.md.example` to `.local.md` and set your vault path:

```markdown
vault_path: /Users/username/Documents/MyVault
```

## Skill Documentation

See `skills/obsidian-pkm-manager/SKILL.md` for comprehensive PKM guidance (481 lines).

Progressive disclosure:
- `SKILL.md` - Core capabilities and workflows
- `references/` - Detailed guides (Templater patterns, Bases queries, etc.)
- `scripts/` - Python analysis tools
- `assets/` - Template examples

## Version

1.0.0

## License

MIT
