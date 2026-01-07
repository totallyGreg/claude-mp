# Marketplace Distribution Guide

This reference provides guidance on distributing skills via Claude Code plugin marketplace. Load this file when you need to publish skills to a marketplace or understand the distribution workflow.

---

## Overview

Skills can be distributed through the Claude Code plugin marketplace system, making them available for installation by other users. Skillsmith delegates all marketplace operations to the **marketplace-manager** skill, which handles versioning, validation, and publication.

---

## Distribution Workflow

### High-Level Process

1. **Create or improve skill** - Complete skill development (Steps 1-4)
2. **Validate skill** - Run `evaluate_skill.py` to ensure quality
3. **Invoke marketplace-manager** - Delegate to marketplace-manager skill
4. **Review marketplace changes** - marketplace-manager shows what will be committed
5. **Commit to marketplace** - Approve marketplace.json + skill commit
6. **Push to remote** - Optionally push to remote repository

### Detailed Workflow

#### Step 1: Prepare Skill for Distribution

Before distributing, ensure:
- [ ] Skill passes validation (`evaluate_skill.py`)
- [ ] SKILL.md is complete and accurate
- [ ] Version number is correct in `metadata.version`
- [ ] README.md includes skill in marketplace listing
- [ ] All bundled resources are tested and working

#### Step 2: Invoke marketplace-manager

Skillsmith automatically delegates to marketplace-manager when appropriate. You can also invoke directly:

```bash
# Via skillsmith (recommended)
User: "Publish skillsmith to marketplace"
→ Skillsmith delegates to marketplace-manager

# Direct invocation
/marketplace-manager add skills/my-skill/
```

#### Step 3: marketplace-manager Operations

marketplace-manager performs these operations automatically:

1. **Add skill to marketplace.json** (if new skill)
   - Creates plugin entry
   - Sets skill path
   - Initializes version

2. **Sync skill version to marketplace.json**
   - Reads version from SKILL.md `metadata.version`
   - Updates marketplace.json version field
   - Ensures consistency

3. **Validate marketplace structure**
   - Checks marketplace.json schema
   - Verifies all paths are valid
   - Confirms no duplicate entries

4. **Prepare commit**
   - Stages SKILL.md changes
   - Stages marketplace.json changes
   - Generates commit message

#### Step 4: Review and Commit

marketplace-manager asks: "Commit to marketplace?"

**Review checklist before approving:**
- [ ] Version number is correct
- [ ] Skill changes are accurate
- [ ] marketplace.json entry is correct
- [ ] Commit message is descriptive

If approved, marketplace-manager commits both files together.

#### Step 5: Push to Remote (Optional)

marketplace-manager asks: "Push to remote?"

**Options:**
- **Yes** - Push immediately to remote repository
- **No** - Keep changes local, push manually later

---

## marketplace-manager Capabilities

### Automatic Version Syncing

marketplace-manager keeps SKILL.md and marketplace.json versions synchronized:

```yaml
# SKILL.md frontmatter
metadata:
  version: "2.2.0"

# marketplace.json (auto-synced)
{
  "plugins": [
    {
      "name": "skillsmith",
      "version": "2.2.0"  ← Automatically synced
    }
  ]
}
```

### Git Integration

marketplace-manager handles all git operations:
- **Staging** - Both SKILL.md and marketplace.json
- **Committing** - Atomic commits with descriptive messages
- **Pushing** - Optional push to remote

**Example commit message:**
```
Add skillsmith v2.2.0 to marketplace

- Initial marketplace publication
- Skill creation and management tool
```

### Marketplace Validation

marketplace-manager validates marketplace structure:
- **Schema compliance** - marketplace.json follows required format
- **Path validation** - All skill paths exist and are valid
- **Duplicate detection** - No duplicate plugin entries
- **Version format** - Semantic versioning (MAJOR.MINOR.PATCH)

### Multi-Component Plugin Versioning

For plugins with multiple skills, marketplace-manager handles:
- **Individual skill versions** - Each skill has independent version
- **Plugin version** - Overall plugin version
- **Coordinated updates** - Update multiple skills in single commit

---

## Manual Operations

While skillsmith delegates to marketplace-manager, you can also perform manual operations:

### Add New Skill to Marketplace

```bash
/marketplace-manager add skills/new-skill/
```

marketplace-manager will:
1. Add skill to marketplace.json
2. Set initial version from SKILL.md
3. Ask to commit changes

### Update Skill Version

```bash
# Update version in SKILL.md first
vim skills/my-skill/SKILL.md
# Change metadata.version to new version

# Sync to marketplace
/marketplace-manager sync skills/my-skill/
```

### Validate Marketplace

```bash
/marketplace-manager validate
```

Checks marketplace.json for:
- Schema compliance
- Path validity
- Version consistency
- Duplicate entries

---

## marketplace.json Structure

### Required Format

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Owner Name",
    "email": "owner@example.com"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "version": "1.0.0",
      "source": "./path/to/plugin",
      "skills": ["./"]
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Marketplace name |
| `owner` | object | Marketplace owner information |
| `plugins` | array | List of plugins in marketplace |
| `plugins[].name` | string | Plugin name (for installation) |
| `plugins[].version` | string | Plugin version (semantic versioning) |
| `plugins[].source` | string | Path to plugin root (relative to marketplace root) |
| `plugins[].skills` | array | Paths to skill directories (relative to source) |

### Single-Skill Plugin

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "source": "./skills/my-skill",
  "skills": ["./"]
}
```

### Multi-Skill Plugin

```json
{
  "name": "my-plugin-bundle",
  "version": "1.0.0",
  "source": "./",
  "skills": [
    "./skill-one",
    "./skill-two",
    "./skill-three"
  ]
}
```

---

## Distribution Best Practices

### Before Distribution

1. **Validate thoroughly**
   ```bash
   python3 scripts/evaluate_skill.py skills/my-skill/ --validate-functionality
   ```

2. **Test locally**
   - Install skill locally
   - Test all workflows
   - Verify bundled resources work

3. **Update README.md**
   - Add skill to marketplace listing
   - Include version number
   - Describe key features

4. **Version appropriately**
   - New skill: Start with 1.0.0
   - Bug fix: PATCH bump (1.0.0 → 1.0.1)
   - New feature: MINOR bump (1.0.0 → 1.1.0)
   - Breaking change: MAJOR bump (1.0.0 → 2.0.0)

### After Distribution

1. **Verify installation**
   ```bash
   claude-code plugin install <marketplace>/<plugin-name>
   ```

2. **Test installed skill**
   - Invoke skill
   - Verify it works as expected

3. **Monitor usage**
   - Watch for issues
   - Respond to user feedback

4. **Maintain documentation**
   - Keep README.md updated
   - Document breaking changes
   - Provide migration guides

---

## Version Management

### Semantic Versioning

Skills should follow semantic versioning (MAJOR.MINOR.PATCH):

**MAJOR (X.0.0)**
- Breaking changes
- Incompatible workflow changes
- Removed features

**MINOR (x.X.0)**
- New features
- Backward-compatible enhancements
- New bundled resources

**PATCH (x.x.X)**
- Bug fixes
- Documentation updates
- Minor improvements

### Version Consistency

marketplace-manager ensures version consistency between:
- **SKILL.md metadata.version** - Source of truth
- **marketplace.json plugins[].version** - Auto-synced
- **README.md listing** - Should be updated manually

---

## Troubleshooting

### "marketplace-manager can't find my skill"

**Solution:** Verify skill path is correct:
```bash
# Check SKILL.md exists
ls skills/my-skill/SKILL.md

# Use absolute or relative path
/marketplace-manager add ./skills/my-skill/
```

### "Version sync failed"

**Solution:** Ensure version is in correct location:
```yaml
# Preferred location
metadata:
  version: "1.0.0"

# Also acceptable
version: "1.0.0"
```

### "marketplace.json validation failed"

**Solution:** Run validation to see specific errors:
```bash
/marketplace-manager validate
```

Common issues:
- Missing required fields
- Invalid version format (use X.Y.Z)
- Invalid skill paths
- Duplicate plugin names

### "Can't push to remote"

**Possible causes:**
- No remote configured
- Authentication required
- Branch protection rules

**Solution:**
```bash
# Check remote
git remote -v

# Manual push if needed
git push origin main
```

---

## Integration with Skillsmith Workflow

marketplace-manager integrates seamlessly with skillsmith workflows:

### Quick Update Workflow + Distribution

```
1. User: "Add reference file X to skillsmith"
2. Skillsmith: [Makes quick update, bumps version 2.2.0 → 2.2.1]
3. Skillsmith: "Ready to publish to marketplace?"
4. User: "Yes"
5. Skillsmith: [Invokes marketplace-manager]
6. marketplace-manager: [Syncs version, asks to commit]
7. User: [Approves]
8. marketplace-manager: [Commits SKILL.md + marketplace.json]
```

### Complex Improvement + Distribution

```
1. User: "Simplify skillsmith instructions"
2. Skillsmith: [Routes to skill-planner]
3. skill-planner: [Research, plan, implement]
4. Skillsmith: "Version bump? MINOR or MAJOR?"
5. User: "MAJOR - 2.2.0 → 3.0.0"
6. Skillsmith: [Updates version]
7. Skillsmith: "Ready to publish?"
8. User: "Yes"
9. Skillsmith: [Invokes marketplace-manager]
10. marketplace-manager: [Syncs, commits, pushes]
```

---

## Post-Validation Checklist

After validation passes, optionally distribute to marketplace:

**Post-Validation Checklist:**
- [ ] Update root README.md with version and changelog
- [ ] Optionally invoke marketplace-manager skill to publish

**To publish to marketplace:**
```bash
# Via skill invocation
/marketplace-manager add skills/my-skill/

# Via skillsmith delegation
User: "Publish my-skill to marketplace"
```

See **marketplace-manager** skill documentation for:
- Comprehensive marketplace operations
- Advanced versioning strategies
- Multi-skill plugin management
- Marketplace administration

---

## Related Skills

- **marketplace-manager** - Full marketplace operations and documentation
- **skillsmith** - Skill creation and improvement (delegates to marketplace-manager)
- **skill-planner** - Systematic improvement planning

---

## Related References

- `improvement_workflow_guide.md` - When marketplace distribution happens in workflows
- `validation_tools_guide.md` - Pre-distribution validation

---

*This guide describes marketplace distribution workflow. For comprehensive marketplace operations, see the marketplace-manager skill documentation.*
