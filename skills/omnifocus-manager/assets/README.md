# OmniFocus Manager Assets

Ready-to-use plugins, templates, and examples for OmniFocus automation.

## Overview

This directory contains:

```
assets/
├── AITaskAnalyzer.omnifocusjs/  # AI-powered task analysis plugin
├── TodaysTasks.omnifocusjs/     # Simple today's tasks plugin
├── templates/                    # Task template definitions
├── examples/                     # Library usage examples (NEW)
└── README.md                     # This file
```

---

## Plugins

### AITaskAnalyzer.omnifocusjs

**AI-powered task analysis plugin** using Apple Foundation Models integration (designed for future API).

**Features:**
- Analyze today's tasks with AI insights
- Analyze selected tasks
- Analyze projects for patterns
- Export analysis results

**Requirements:**
- OmniFocus 4.8+
- macOS 15.2+ / iOS 18.2+ / iPadOS 18.2+ (for future Foundation Models)
- Apple Silicon (Mac) or iPhone 15 Pro+ (for future Foundation Models)

**Installation:** Double-click `AITaskAnalyzer.omnifocusjs`

**Documentation:**
- Complete guide: `../references/plugin_installation.md`
- Foundation Models: `../references/foundation_models_integration.md`

**Version:** 2.2.1 (uses rule-based patterns, designed for future AI enhancement)

---

### TodaysTasks.omnifocusjs

**Simple reference plugin** showing today's tasks grouped by project.

**Features:**
- One-click view of today's tasks
- Groups by project
- Shows flagged status
- Shows due times

**Installation:** Double-click `TodaysTasks.omnifocusjs`

**Use Case:** Quick daily review, reference implementation for simple plugins

**Version:** 1.0.0

---

## Templates

### Task Templates (`templates/task_templates.json`)

**Reusable task templates** for common workflows.

**Available Templates:**
- `weekly_review` - GTD weekly review checklist
- `meeting_prep` - Meeting preparation tasks
- `project_kickoff` - New project kickoff checklist

**Usage:**
```bash
# Via script
osascript ../scripts/create_from_template.js weekly_review

# Via template engine library
const engine = loadLibrary('templateEngine.js');
engine.createFromTemplate(doc, 'weekly_review', {WEEK: '2025-W01'});
```

**Format:**
```json
{
  "template_name": {
    "name": "Task name with {{VARIABLE}}",
    "note": "Optional note",
    "project": "Project name",
    "tags": ["tag1", "tag2"],
    "estimate": "30m",
    "flagged": true
  }
}
```

**Documentation:** `../references/workflows.md` (template workflows section)

---

## Examples (NEW)

### Complete Usage Examples (`examples/`)

**Demonstrates all three library usage patterns:**
1. **Standalone** - Individual library functions (3 examples)
2. **JXA Scripts** - Complete automation workflows (4 examples)
3. **OmniFocus Plugins** - Reusable plugin actions (3 examples)

**Quick Start:**
```bash
# Standalone: Learn individual library
osascript examples/standalone/query-today.js

# JXA Script: Complete workflow
./examples/jxa-scripts/check-today.js

# Plugin: Install and use
# Double-click examples/plugins/SimpleQuery.omnifocusjs
```

**See:** `examples/README.md` for complete documentation

---

## What to Use When

| Need | Use | Location |
|------|-----|----------|
| AI-powered task analysis | AITaskAnalyzer plugin | `AITaskAnalyzer.omnifocusjs` |
| Quick today's tasks view | TodaysTasks plugin | `TodaysTasks.omnifocusjs` |
| Create from template | Template system | `templates/` + scripts |
| Learn library API | Standalone examples | `examples/standalone/` |
| Complete automation workflow | JXA script examples | `examples/jxa-scripts/` |
| Build custom plugin | Plugin examples | `examples/plugins/` |

---

## Using Assets in Skill

The omnifocus-manager skill uses these assets for **execution-first architecture:**

### Low-Cost Execution (Most Common)
```
User: "Show me today's tasks"
Skill: Executes TodaysTasks plugin or queries via script
       Returns results to user
Token Cost: Low (execution only)
```

### Medium-Cost Composition
```
User: "Create a weekly review plugin"
Skill: Composes from examples/plugins/SimpleQuery.omnifocusjs
       Uses libraries from ../libraries/
       Customizes for user needs
Token Cost: Medium (composition + minor generation)
```

### High-Cost Generation (Rare)
```
User: "Create completely novel automation"
Skill: Generates from scratch
       Offers to add to asset library
Token Cost: High (full generation)
```

**Goal:** 80% execution, 15% composition, 5% generation

---

## Modifying Assets

All assets are fully editable:

### Plugins
1. Right-click `.omnifocusjs` bundle
2. Select "Show Package Contents"
3. Edit `manifest.json` or `Resources/*.js` files
4. Restart OmniFocus

### Templates
1. Edit `templates/task_templates.json` directly
2. Save and use immediately

### Examples
1. Copy example to your location
2. Modify for your needs
3. Test and iterate

---

## Creating New Assets

**Recommended Workflow:**

1. **Start with examples** - Copy closest example
2. **Use libraries** - Compose from `../libraries/`
3. **Test thoroughly** - Verify all actions work
4. **Document** - Add comments and usage notes
5. **Version** - Update version in manifest.json
6. **Share** (optional) - Contribute back to skill

**Template for New Plugin:**
```bash
# Copy example structure
cp -R examples/plugins/SimpleQuery.omnifocusjs MyPlugin.omnifocusjs

# Edit manifest
# Edit actions in Resources/
# Test by double-clicking to install
```

---

## Version Management

**Plugins:**
- Update `version` in manifest.json
- Follow semantic versioning (major.minor.patch)
- Breaking changes → major version bump

**Templates:**
- No formal versioning (JSON format)
- Document changes in comments

**Examples:**
- Update in-place (teaching resources, not runtime dependencies)
- Note version in comments if using specific OmniFocus features

---

## Testing Assets

### Plugins
- Install in OmniFocus (double-click)
- Test all actions
- Check with/without selection
- Verify on Mac + iOS (if targeting both)

### Templates
- Create tasks using script/library
- Verify all fields populate correctly
- Test variable substitution

### Examples
- Run each example
- Verify output matches documentation
- Check error handling

---

## Resources

**Plugin Development:**
- Complete guide: `../references/plugin_development_guide.md`
- Plugin API: `../references/plugin_api.md`
- Installation guide: `../references/plugin_installation.md`

**Library Usage:**
- Library overview: `../libraries/README.md`
- JXA guide: `../references/jxa_api_guide.md`
- Examples guide: `examples/README.md`

**References:**
- OmniFocus API: `../references/OmniFocus-API.md`
- URL scheme: `../references/omnifocus_url_scheme.md`
- Automation guide: `../references/omnifocus_automation.md`
- Foundation Models: `../references/foundation_models_integration.md`

---

## Contributing

When adding new assets:

1. **Follow existing patterns** - Match structure of similar assets
2. **Use modular libraries** - Compose from `../libraries/` where possible
3. **Document thoroughly** - Comments, README sections, usage examples
4. **Test on target platforms** - Mac and/or iOS as appropriate
5. **Version appropriately** - Semantic versioning for plugins

**Promotion Criteria:**
- Novel generated code that solved a real problem
- Reusable across multiple users/use cases
- Well-tested and documented
- Demonstrates library capabilities

---

## License

Part of the omnifocus-manager skill. See parent directory for license information.
