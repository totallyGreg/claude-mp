---
name: marketplace-manager
description: This skill should be used when managing Claude Code plugin marketplace operations including version syncing, skill publishing, and marketplace.json maintenance. Supports programmatic invocation by other skills for automated version management. Use when adding skills to marketplace, updating skill versions, syncing marketplace.json, or managing plugin distributions.
metadata:
  version: "1.4.0"
compatibility: Requires git repository with .claude-plugin/marketplace.json
---

# Marketplace Manager

Manages Claude Code plugin marketplace operations with automatic version detection and syncing.

## About Marketplaces

A Claude Code plugin marketplace enables easy skill distribution and installation. Users can install skills using:

```bash
/plugin marketplace add username/repository
/plugin install plugin-name@marketplace-name
```

## When to Use

Use marketplace-manager when:
- Adding new skills to marketplace.json
- Updating skill versions in marketplace
- Syncing versions between SKILL.md and marketplace.json
- Detecting version mismatches
- Managing plugin metadata
- Validating marketplace structure

## Programmatic Invocation

marketplace-manager can be invoked programmatically by other skills (e.g., Skillsmith) for automated version management and git operations.

**When Called by Skillsmith:**
1. Skillsmith completes skill changes (quick update or complex implementation)
2. Skillsmith calls marketplace-manager: "Sync versions and commit these changes"
3. marketplace-manager runs sync_marketplace_versions.py
4. marketplace-manager updates marketplace.json with new skill version
5. marketplace-manager asks user: "Commit these changes? [yes/no]"
6. On approval, commits both SKILL.md and marketplace.json together
7. marketplace-manager asks user: "Push to remote? [yes/no]"
8. Returns commit SHA and status to Skillsmith

**Workflow Integration:**
- **Quick updates**: Skillsmith → marketplace-manager → commit (single flow)
- **Complex updates**: skill-planner → Skillsmith → marketplace-manager → commit to plan branch
- **Manual fallback**: Users can always run scripts directly

**Commands Used:**
```bash
# Sync versions (auto-detects changes)
python3 scripts/sync_marketplace_versions.py

# Preview changes first
python3 scripts/sync_marketplace_versions.py --dry-run

# Detect mismatches
python3 scripts/detect_version_changes.py
```

## Core Functionality

### Automatic Version Detection

marketplace-manager automatically detects when skill versions change and prompts to sync marketplace.json.

**Detection triggers:**
- After skill edits when metadata.version or version field changes
- Before git commits (via pre-commit hook)
- When explicitly checking sync status

### Version Syncing

Keeps marketplace.json versions synchronized with skill SKILL.md frontmatter:

```bash
# Sync all skill versions to marketplace
python3 scripts/sync_marketplace_versions.py

# Preview changes without saving
python3 scripts/sync_marketplace_versions.py --dry-run
```

**Sync process:**
1. Scans all skills in marketplace.json
2. Reads version from each skill's SKILL.md frontmatter
3. Compares with marketplace.json plugin version
4. Updates marketplace.json if mismatch detected
5. Reports all changes made

**Version field priority:**
- First checks `metadata.version` (Agent Skills spec)
- Falls back to `version` (deprecated but supported)
- Reports warning if using deprecated field

### Adding Skills to Marketplace

Use the add_to_marketplace.py script to add skills:

```bash
# List current marketplace contents
python3 scripts/add_to_marketplace.py list

# Add skill to existing plugin
python3 scripts/add_to_marketplace.py add-skill <skill-path> --plugin <plugin-name>

# Create new plugin with skill
python3 scripts/add_to_marketplace.py create-plugin <plugin-name> --skill <skill-path>
```

**Script features:**
- Auto-detects repository root (works from any directory)
- Validates skill structure before adding
- Updates marketplace.json atomically
- Supports verbose output for debugging

### Marketplace Structure

**Key principles:**
- Plugin versions should match skill versions (see "Version Management" section)
- Use sync script to maintain synchronization
- Each plugin can contain multiple related skills
- Skills are referenced by relative paths from marketplace root

For complete marketplace.json schema reference and field documentation, see `references/plugin_marketplace_guide.md`.

## Marketplace Operations

The marketplace-manager skill provides three powerful automation tools for managing your plugin marketplace.

### Deprecating Skills

Use `deprecate_skill.py` to safely remove skills from your marketplace with automated cleanup guidance:

```bash
# Dry-run to preview changes
python3 scripts/deprecate_skill.py --skill skill-name \
  --reason "Superseded by new-skill" \
  --migration-notes "Use new-skill instead" \
  --dry-run

# Actually deprecate (with confirmation prompt)
python3 scripts/deprecate_skill.py --skill skill-name \
  --reason "Superseded by new-skill" \
  --migration-notes "Use new-skill instead"

# Auto-confirm for scripted workflows
python3 scripts/deprecate_skill.py --skill skill-name \
  --reason "No longer maintained" \
  --yes
```

**What it does:**
1. Removes plugin from marketplace.json
2. Scans all SKILL.md files for references to deprecated skill
3. Reports which skills reference the deprecated skill (with line numbers)
4. Creates migration guide in `docs/lessons/` (optional)
5. Generates cleanup checklist saved to `deprecate-{skill}-checklist.txt`

**Cleanup checklist includes:**
- Skills that reference the deprecated skill (need manual updates)
- Command to delete skill files (`git rm -r skills/{skill}/`)
- Reminder to commit changes
- User notification steps (if applicable)

**Example output:**
```
📦 Found plugin: skill-planner v1.1.0
   Description: Manages improvement planning lifecycle...
   Source: ./skills/skill-planner

🔍 Scanning for references to 'skill-planner'...

⚠️  Found 2 skill(s) with references:
   • marketplace-manager (4 reference(s))
   • skillsmith (2 reference(s))

📋 Deprecation Plan:
   1. Remove 'skill-planner' from marketplace.json
   2. Reason: Superseded by WORKFLOW.md GitHub Issues pattern
   3. Create migration guide in docs/lessons/
   4. Report 2 skill(s) that need manual updates
```

### Analyzing Bundling Opportunities

Use `analyze_bundling.py` to discover which skills should be bundled together as multi-skill plugins:

```bash
# Analyze and show recommendations
python3 scripts/analyze_bundling.py

# Output as JSON for programmatic use
python3 scripts/analyze_bundling.py --format json

# Interactive bundling workflow
python3 scripts/analyze_bundling.py --interactive

# Adjust minimum affinity score threshold
python3 scripts/analyze_bundling.py --min-score 30
```

**Affinity scoring** (0-100 scale):
- Same category: +30 points
- Cross-references: +40 points
- Bidirectional references: +20 bonus points
- Similar descriptions: +10 points

**What it analyzes:**
1. Skills by category grouping
2. Cross-skill references in SKILL.md files
3. Pairwise bundling affinity scores
4. Recommended bundle names and descriptions

**Example output:**
```
Bundling Recommendations
======================================================================

1. Bundle: skillsmith + marketplace-manager
   Affinity Score: 80/100
   Reasons:
     • Both in 'development' category
     • skillsmith references marketplace-manager

   Suggested Bundle:
     Name: skill-development-toolkit
     Description: Combines skillsmith, marketplace-manager for integrated workflow
```

**Creating bundles:**

Once you've identified a good bundling opportunity:

```bash
# Create multi-skill bundle
python3 scripts/add_to_marketplace.py create-plugin skill-development-toolkit \
  "Integrated toolkit for skill development and marketplace management" \
  --skills ./skills/skillsmith ./skills/marketplace-manager
```

**Bundling considerations:**
- Keep individual plugin distributions for users who only need one skill
- Bundle tightly-coupled skills (frequent cross-references)
- Bundle skills in same category with complementary functionality
- Consider user experience: is the bundle more useful than individual skills?

### Generating Utils Templates

Use `generate_utils_template.py` to create consistent utils.py files for new skills:

```bash
# Generate utils.py for a new skill
python3 scripts/generate_utils_template.py --skill my-new-skill

# Overwrite existing utils.py (use carefully)
python3 scripts/generate_utils_template.py --skill existing-skill --force

# Generate with verbose output
python3 scripts/generate_utils_template.py --skill my-skill --verbose
```

**What it generates:**

The template includes standard utility functions:
- `find_repo_root()` - Auto-detect repository root
- `get_repo_root()` - Get repo root with verbose mode
- `print_verbose_info()` - Display path resolution details
- `validate_repo_structure()` - Check repository structure

**Template customization:**

Edit `scripts/templates/utils.py.template` to add skill-specific utilities. The template uses `{SKILL_NAME}` placeholder which gets replaced during generation.

**Why code duplication?**

In marketplace context, plugins must be self-contained for independent distribution. Users install individual skills, so each needs its own utils.py. Templates ensure this duplication is **consistent** across all skills.

**Usage in skill scripts:**

```python
#!/usr/bin/env python3
from utils import get_repo_root

repo_root = get_repo_root(args.path, verbose=args.verbose)
marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
```

## Git Integration

### Pre-Commit Hook

Auto-sync marketplace.json before commits:

```bash
# Install or update pre-commit hook (recommended)
bash skills/marketplace-manager/scripts/install_hook.sh

# Verify installation
python3 skills/marketplace-manager/scripts/validate_hook.py

# Preview changes without installing
bash skills/marketplace-manager/scripts/install_hook.sh --dry-run

# Force reinstall
bash skills/marketplace-manager/scripts/install_hook.sh --force
```

**Hook features:**
- ✅ **Idempotent installation** - Safe to run multiple times
- ✅ **Version detection** - Warns when hook is outdated
- ✅ **Robust path discovery** - Survives skill renames
- ✅ **Auto-sync** - Updates marketplace.json automatically
- ✅ **Graceful degradation** - Warns but doesn't block commits

**Hook behavior:**
- Detects version mismatches before commit
- Automatically updates marketplace.json
- Adds marketplace.json to commit
- Prevents commit if sync fails
- Can be bypassed with `git commit --no-verify`

### Workflow Integration

marketplace-manager integrates with skill-planner workflow:

**After skill improvement:**
1. skill-planner completes implementation
2. Skill version updated in SKILL.md
3. marketplace-manager detects mismatch
4. Prompts: "Skill version changed. Sync marketplace.json?"
5. User confirms or manually syncs
6. marketplace.json updated automatically
7. Changes committed together

## Version Management

### Semantic Versioning

Follow semantic versioning for all skills and plugins:
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes
- **MINOR** (1.0.0 → 1.1.0): New features, backward-compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation

### Plugin Versioning Strategies

marketplace-manager supports two versioning modes for different plugin architectures:

**Auto Mode (Default - Recommended for Single-Skill Plugins)**
- Automatically syncs plugin version from skill version
- Best for plugins with one skill
- Plugin version always matches skill version
- Simple and automatic
- Usage: `python3 scripts/sync_marketplace_versions.py`

**Manual Mode (Recommended for Multi-Component Plugins)**
- Plugin version managed independently from component versions
- Required for plugins with multiple skills, MCP servers, LSP servers, hooks, or agents
- Sync script detects mismatches and warns without auto-updating
- Developer manually bumps plugin version based on changes
- Usage: `python3 scripts/sync_marketplace_versions.py --mode=manual`

**Choosing a Strategy:**
- **Single component** → Use auto mode
- **Multiple components** → Use manual mode
- **When in doubt** → Use manual mode for conscious version control

### Multi-Component Plugin Versioning

For plugins containing multiple components (skills, MCP servers, etc.):

**Problem with auto-sync:**
- Plugin v1.5.0 with skill-a v1.5.0 and skill-b v1.2.0
- Update skill-b to v1.3.0
- Auto-sync would keep plugin at v1.5.0 (no update signal!)

**Manual versioning workflow:**
1. Update component and bump its version
2. Run: `python3 scripts/sync_marketplace_versions.py --mode=manual`
3. Script warns about version mismatch
4. Decide appropriate plugin version bump (major/minor/patch)
5. Manually update plugin version in marketplace.json
6. Commit component + marketplace.json together

**Plugin version decision guide:**
- **MAJOR**: Any component has breaking changes
- **MINOR**: Any component adds new features
- **PATCH**: Any component fixes bugs only

### Update Workflow

**Single-skill plugin workflow:**
1. Make changes to SKILL.md or bundled resources
2. Update `metadata.version` in SKILL.md frontmatter
3. Test changes thoroughly
4. Run sync script: `python3 scripts/sync_marketplace_versions.py`
5. Commit SKILL.md and marketplace.json together
6. Push changes

**Multi-component plugin workflow:**
1. Make changes to component(s)
2. Update `metadata.version` in component's SKILL.md
3. Test changes thoroughly
4. Run sync script: `python3 scripts/sync_marketplace_versions.py --mode=manual`
5. Review warnings about version mismatches
6. Manually update plugin version in marketplace.json
7. Commit component files + marketplace.json together
8. Push changes

**Automated workflow (with pre-commit hook):**
1. Make changes and update version
2. Git add and commit
3. Hook auto-detects mismatch
4. Hook auto-syncs marketplace.json (auto mode) or warns (manual mode)
5. Hook adds marketplace.json to commit if updated
6. Commit proceeds automatically

## Best Practices

**Version Management:**
1. Always update skill version when making changes
2. Use `metadata.version` (not deprecated `version`)
3. Follow semantic versioning guidelines
4. Choose appropriate versioning mode (auto for single-skill, manual for multi-component)
5. Sync marketplace.json before pushing
6. Include both files in same commit
7. For multi-component plugins, manually control plugin version

**Plugin Organization:**
1. **Prefer single-skill plugins** for simplicity and automatic versioning
2. Use multi-skill plugins only for tightly coupled components
3. Use descriptive plugin names
4. Set appropriate categories
5. Document changes in IMPROVEMENT_PLAN.md

**Component Organization:**
1. Group related skills into plugins only if they're always used together
2. Consider separate plugins for independently versioned components
3. For plugins with skills + MCP servers + hooks, use manual versioning mode
4. Keep component versions independent within multi-component plugins

**Automation:**
1. Install pre-commit hook for auto-sync
2. Run validation before pushing
3. Use --dry-run to preview changes
4. Check sync status regularly

**Troubleshooting:**
- If auto-detection fails, use `--path` flag
- Use `--verbose` to debug path resolution
- Check for `.git` or `.claude-plugin` directories
- Ensure you're in repository when running scripts

## Troubleshooting

For detailed troubleshooting guidance on hook issues, script problems, path resolution, and validation errors, see `references/troubleshooting.md`.

## Advanced Topics

For comprehensive marketplace distribution guidance, see:

- **`references/marketplace_distribution_guide.md`** - Complete distribution workflow, best practices, troubleshooting

## See Also

- **skillsmith** - Creates and improves skills
- **skill-planner** - Plans skill improvements
- [THREE_SKILL_ARCHITECTURE.md](../../THREE_SKILL_ARCHITECTURE.md) - Complete system design
