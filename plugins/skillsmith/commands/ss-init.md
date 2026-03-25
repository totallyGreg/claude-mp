Initialize a new skill from template.

**Before running this command**, complete the Use-Case Definition Form in `references/form_templates.md`. Defining 2-3 concrete use cases first produces a sharper description and avoids rebuilding the skill from scratch after evaluation.

Run the initialization command:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/skillsmith/scripts/init_skill.py $ARGUMENTS
```

Required arguments:
- `<skill-name>` - Name for the new skill (lowercase, hyphens only)
- `--path <directory>` - Output directory for the skill

Examples:
```
/ss-init my-new-skill --path ./skills
/ss-init pdf-editor --path /path/to/skills
```

The script creates:
- Skill directory with proper structure
- SKILL.md template with TODO placeholders
- Example scripts/, references/, and assets/ directories
- Example files that can be customized or deleted

After initialization, customize the generated files and run `/ss-validate` to verify structure.
