# Detailed Skill Creation & Editing Guide

This reference provides comprehensive guidance for Steps 4-6 of the skill creation process: editing the skill, validation, and iteration.

---

## Step 4: Edit the Skill (Detailed)

When editing the (newly-generated or existing) skill, remember that the skill is being created for another instance of Claude to use. Focus on including information that would be beneficial and non-obvious to Claude. Consider what procedural knowledge, domain-specific details, or reusable assets would help another Claude instance execute these tasks more effectively.

### Start with Reusable Skill Contents

To begin implementation, start with the reusable resources identified in Step 2: `scripts/`, `references/`, and `assets/` files. Note that this step may require user input. For example, when implementing a `brand-guidelines` skill, the user may need to provide brand assets or templates to store in `assets/`, or documentation to store in `references/`.

Also, delete any example files and directories not needed for the skill. The initialization script creates example files in `scripts/`, `references/`, and `assets/` to demonstrate structure, but most skills won't need all of them.

### Update SKILL.md

**Writing Style:** Write the entire skill using **imperative/infinitive form** (verb-first instructions), not second person. Use objective, instructional language (e.g., "To accomplish X, do Y" rather than "You should do X" or "If you need to do X"). This maintains consistency and clarity for AI consumption.

**Progressive Disclosure:** Keep SKILL.md lean (<500 lines). See `references/progressive_disclosure_discipline.md` before adding detailed content.

**Specification Compliance:** Ensure the skill follows AgentSkills specification requirements:
- Verify frontmatter contains required `name` and `description` fields
- Confirm `name` follows naming conventions (lowercase, alphanumeric, hyphens only)
- Keep `description` under 1024 characters with clear triggering keywords
- Keep SKILL.md body under 500 lines (move detailed content to references/)
- Use relative paths for all file references
- Maintain one-level-deep reference chains

See `references/agentskills_specification.md` for complete validation requirements.

To complete SKILL.md, answer the following questions:

1. What is the purpose of the skill, in a few sentences?
2. When should the skill be used?
3. In practice, how should Claude use the skill? All reusable skill contents developed in Step 2 should be referenced so that Claude knows how to use them.

---

## Step 5: Validate the Skill (Detailed)

Once the skill is ready, validate it to ensure it meets all requirements:

```bash
uv run scripts/evaluate_skill.py <skill-path> --quick
```

### What the Validation Evaluates

The validation checks:
- YAML frontmatter format and required fields
- Character limits (name ≤64 chars, description ≤1024 chars)
- Naming conventions (lowercase-with-hyphens)
- Line/token budgets (SKILL.md <500 lines recommended)
- Description completeness and quality
- File organization and resource references
- AgentSkills specification compliance

If validation fails, the tool will report the errors. Fix any validation errors and run validation again.

### Validation Gate: Strict vs Standard Mode

Validation provides two enforcement levels:

**Standard Mode (default):**
- Errors block skill completion (required fixes)
- Warnings are informational (recommended improvements)
- Developers can proceed despite warnings
- Use in: Development iterations

**Strict Mode (--strict flag):**
- Both errors AND warnings block skill completion
- Prevents quality regressions before release
- Designed for: Pre-release quality gates
- Prevents: Accidentally shipping low-quality documentation

Use strict mode when:
- Preparing release versions
- Running in CI/CD validation gates
- Quality expectations are high
- Before submission to marketplace

Example:
```bash
# Standard validation (warnings are OK)
uv run scripts/evaluate_skill.py skills/my-skill --quick

# Strict validation (warnings block completion)
uv run scripts/evaluate_skill.py skills/my-skill --quick --strict
```

For advanced validation options, see `references/validation_tools_guide.md`.

### Post-Validation Checklist

After validation passes:
- [ ] Test skill functionality end-to-end
- [ ] Verify bundled resources work correctly
- [ ] Update root README.md with skill version and changelog
- [ ] Optionally invoke marketplace-manager to publish skill

---

## Step 6: Iterate (Detailed)

After testing the skill, users may request improvements. Often this happens right after using the skill, with fresh context of how the skill performed.

### Iteration Workflow

1. **Use the skill on real tasks** - Get practical experience with the skill
2. **Notice struggles or inefficiencies** - Identify what didn't work well
3. **Identify improvements** - Determine what SKILL.md or bundled resources should change
4. **Make improvements directly** - For simple changes, update files directly
5. **Validate improvements** - Run quick validation to verify no regressions:
   ```bash
   uv run scripts/evaluate_skill.py <skill> --quick
   ```
6. **Pre-commit validation** - Before committing:
   - Run strict validation: `uv run scripts/evaluate_skill.py <skill> --quick --strict`
   - Fix any issues (errors or warnings in strict mode)
   - Re-run validation until all issues are resolved
7. **Update version** - Update the `metadata.version` field in YAML frontmatter:
   - **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation updates, minor improvements
   - **MINOR** (1.0.0 → 1.1.0): New features, new bundled resources, backward-compatible changes
   - **MAJOR** (1.0.0 → 2.0.0): Breaking changes, major rewrites, changed workflow
8. **Test again and commit** - Verify everything works and create commit
9. **Optionally sync to marketplace** - Use marketplace-manager if publishing

### For Complex Improvements

When improvements are substantial (multi-file changes, architectural decisions, etc.):
- Use WORKFLOW.md pattern: Create GitHub Issue → Add to IMPROVEMENT_PLAN.md → Plan in docs/plans/
- See `references/improvement_workflow_guide.md` for detailed improvement routing logic
- Research skill opportunities with `scripts/research_skill.py`

**Complex vs Simple Decision:**
- <50 lines of changes → Simple (direct improvement)
- >50 lines of changes → Complex (follow WORKFLOW.md pattern)
- Architectural changes → Complex (follow WORKFLOW.md pattern)
- Multi-skill impact → Complex (follow WORKFLOW.md pattern)

---

## Related Topics

For additional guidance on skill development:
- `agentskills_specification.md` - Complete specification requirements
- `progressive_disclosure_discipline.md` - Keeping SKILL.md lean and discoverable
- `validation_tools_guide.md` - Validation and metrics documentation
- `improvement_workflow_guide.md` - When to use direct vs WORKFLOW.md improvement patterns
- `python_uv_guide.md` - Python script best practices with PEP 723
