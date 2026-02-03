# Reference Management Guide

## Introduction

Skillsmith uses a validation-based approach to reference management that maintains AgentSkills one-level reference architecture through contextual pointers in SKILL.md rather than intermediate catalog files.

**Why Validation-Based Management:**
- Maintains one-level reference chain (SKILL.md → reference files)
- References discovered in context where they're actually used
- Prevents orphaned references (files not mentioned anywhere)
- Keeps SKILL.md lean and within 500-line guideline
- Complies with AgentSkills spec: "Keep reference chains one-level deep"

**When to Use Reference Validation:**
- When adding new reference documentation
- After creating or moving reference files
- During skill validation and quality checks
- When reviewing skills for completeness

## Architecture: Contextual Pointers

### How It Works

Instead of creating a separate REFERENCE.md catalog, reference files are mentioned contextually in SKILL.md where they're relevant:

**Examples of contextual mentions:**
```markdown
- For complete frontmatter requirements, see `references/agentskills_specification.md`
- Use templates from `references/FORMS.md`
- See `references/improvement_plan_best_practices.md` for versioning strategy
```

**Benefits:**
1. **Contextual Discovery**: Agents learn about references when they need them
2. **One-Level Chain**: SKILL.md → reference files (no intermediate catalog)
3. **Natural Integration**: References tied to specific use cases in documentation
4. **Lean SKILL.md**: No table bloat from cataloging all references

### AgentSkills Spec Compliance

This approach follows the AgentSkills specification guideline:
> "Keep reference chains one-level deep from SKILL.md"

**Compliant architecture:**
```
SKILL.md (mentions references in context)
├─→ references/agentskills_specification.md
├─→ references/FORMS.md
├─→ references/improvement_plan_best_practices.md
└─→ references/... (direct reference)
```

**Non-compliant (previous approach):**
```
SKILL.md
└─→ references/REFERENCE.md (catalog)
    ├─→ references/agentskills_specification.md
    ├─→ references/FORMS.md
    └─→ ... (two-level chain)
```

## Adding New References

### Workflow

When adding a new reference file:

1. **Create the reference file** in `references/` directory:
   ```bash
   # Example: Adding API documentation
   touch references/api_docs.md
   # Write content to the file...
   ```

2. **Add contextual mention** in SKILL.md where relevant:
   ```markdown
   # In the section where APIs are discussed:
   For complete API specifications, see `references/api_docs.md`.
   ```

3. **Run validation** to confirm it's properly linked:
   ```bash
   python3 scripts/update_references.py .
   ```

4. **Expected output:**
   ```
   Validating reference mentions for /path/to/skill...

   Found 7 reference file(s)

   ✓ All 7 reference files are mentioned in SKILL.md
   ```

### Where to Mention References

**Good places for contextual mentions:**

1. **In relevant documentation sections:**
   ```markdown
   #### API Integration
   For complete endpoint specifications and schemas, see `references/api_docs.md`.
   ```

2. **In workflow instructions:**
   ```markdown
   - Use form templates from `references/FORMS.md`
   - Follow versioning strategy in `references/improvement_plan_best_practices.md`
   ```

3. **In feature descriptions:**
   ```markdown
   For AgentSkills compliance details, see `references/agentskills_specification.md`.
   ```

**Patterns to use:**
- `See \`references/filename.md\` for [purpose]`
- `Use [resource] from \`references/filename.md\``
- `[Topic] documentation in \`references/filename.md\``
- `For [detail], see \`references/filename.md\``

## Validation Process

### Running Validation

The `update_references.py` script validates that all reference files are mentioned in SKILL.md:

```bash
# Validate current skill
python3 scripts/update_references.py .

# Validate another skill
python3 scripts/update_references.py ../other-skill
```

### Validation Output

**All references mentioned (✓):**
```
Validating reference mentions for /path/to/skill...

Found 6 reference file(s)

✓ All 6 reference files are mentioned in SKILL.md
```

**Orphaned references detected (⚠️):**
```
Validating reference mentions for /path/to/skill...

Found 6 reference file(s)

⚠️  Warning: 2 reference file(s) not mentioned in SKILL.md:
  - integration_guide.md
  - research_guide.md

Consider adding contextual mentions in SKILL.md, such as:
  - 'See `references/filename.md` for details'
  - 'Use templates from `references/filename.md`'
  - 'API documentation in `references/filename.md`'
```

### Fixing Orphaned References

When orphaned references are detected:

1. **Review the reference file** to understand its purpose
2. **Find relevant section** in SKILL.md where it should be mentioned
3. **Add contextual mention** in that section
4. **Re-run validation** to confirm it's fixed

**Example:**

If `research_guide.md` is orphaned:

```markdown
# In SKILL.md, find the section about skill evaluation/research:

## Skill Evaluation

Skillsmith provides comprehensive evaluation capabilities to assess skills
and identify improvement opportunities. See `references/research_guide.md`
for detailed information on research tools and evaluation metrics.
```

## Validation Modes

### Default Mode: Validate Mentions

Scans references/ directory and validates all files are mentioned in SKILL.md:

```bash
python3 scripts/update_references.py .
```

### Detect Duplicates Mode

Detects similar references that may need consolidation:

```bash
python3 scripts/update_references.py . --detect-duplicates
```

**Output:**
```
Detecting consolidation opportunities...

Consolidation Opportunities Detected:

Cluster 1 (85% similar):
  - references/api_v1_docs.md
  - references/api_v2_docs.md
  Recommendation: Consider consolidating into single versioned API documentation

Cluster 2 (92% similar):
  - references/forms_old.md
  - references/FORMS.md
  Recommendation: Review for potential merge - high similarity detected
```

### Validate Structure Mode

Validates references/ directory structure per AgentSkills spec:

```bash
python3 scripts/update_references.py . --validate-structure
```

## Best Practices

### Contextual Integration

✅ **Good:**
```markdown
## API Integration

The skill supports RESTful API integration with OAuth2 authentication.
For complete endpoint specifications, request/response schemas, and
authentication flows, see `references/api_docs.md`.
```

❌ **Avoid:**
```markdown
## References

- See api_docs.md
- See FORMS.md
- See research_guide.md
```

### Mention Patterns

Use clear, descriptive patterns that explain WHY someone would read the reference:

✅ **Good:**
- "For complete API specifications, see `references/api_docs.md`"
- "Use form templates from `references/FORMS.md`"
- "For versioning strategy and best practices, see `references/improvement_plan_best_practices.md`"

❌ **Avoid:**
- "See api_docs.md" (lacks context)
- "More info in FORMS.md" (vague purpose)
- "Check research_guide.md" (unclear when to use it)

### Keep SKILL.md Lean

- Mention each reference once (avoid redundant mentions)
- Use concise mention patterns (don't copy content into SKILL.md)
- Trust agents to load references when they see contextual pointers

### Validation Workflow

Make validation part of your skill development workflow:

1. **After adding reference**: Run validation immediately
2. **Before committing**: Ensure all references are mentioned
3. **During reviews**: Check for orphaned references
4. **Periodic audits**: Re-run validation to catch drift

## Integration with Skillsmith Workflows

### Quick Updates

When skillsmith handles quick updates involving new references:

1. Skillsmith creates the reference file
2. Skillsmith adds contextual mention to SKILL.md
3. Skillsmith runs `update_references.py` to validate
4. Both reference file and updated SKILL.md are committed together

### Complex Improvements

When following the WORKFLOW.md pattern for complex improvements:

1. Planning phase identifies needed references
2. Implementation adds references and contextual mentions
3. Validation ensures all references are properly linked
4. Quality checks verify mentions are contextually appropriate

## Migration from REFERENCE.md

If your skill currently uses `references/REFERENCE.md` catalog:

1. **Read REFERENCE.md** to see what references exist
2. **Add contextual mentions** for each reference in SKILL.md
3. **Run validation** to confirm all are mentioned
4. **Delete REFERENCE.md** once validation passes
5. **Update .skillignore** if REFERENCE.md was listed there

**Example migration:**

```bash
# 1. Check current references
cat references/REFERENCE.md

# 2. Add contextual mentions in SKILL.md
# (edit SKILL.md to add mentions)

# 3. Validate all references are mentioned
python3 scripts/update_references.py .

# 4. Delete old catalog once validation passes
rm references/REFERENCE.md

# 5. Commit changes
git add SKILL.md references/
git commit -m "Migrate to validation-based reference management"
```

## FAQ

**Q: Do I need REFERENCE.md anymore?**

A: No. The validation-based approach eliminates the need for a separate catalog file. References are mentioned contextually in SKILL.md instead.

**Q: What if I have many references?**

A: Mention each reference once in the appropriate context. The validation script ensures none are orphaned, regardless of how many you have.

**Q: Can I mention a reference multiple times?**

A: Yes, but it's not necessary for validation. The script only checks that each reference is mentioned at least once. Multiple mentions are fine if contextually appropriate.

**Q: What if my reference file isn't mentioned anywhere?**

A: The validation script will report it as orphaned and suggest adding a contextual mention. This prevents "lost" references that agents can't discover.

**Q: Does this work with references in subdirectories?**

A: Currently, the script scans only `references/*.md` files (not subdirectories). Keep references flat in `references/` for best compatibility.

## Command Reference

```bash
# Validate reference mentions (default)
python3 scripts/update_references.py .

# Detect consolidation opportunities
python3 scripts/update_references.py . --detect-duplicates

# Validate directory structure
python3 scripts/update_references.py . --validate-structure

# Validate another skill
python3 scripts/update_references.py ../other-skill
```

## Related Documentation

- `references/agentskills_specification.md` - AgentSkills specification with reference architecture guidelines
- SKILL.md (lines 91-103) - References section with discovery guidance
