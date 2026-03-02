# Implementation Plan: ai-risk-mapper Slash Commands

**Issue**: #31 - Break out CLI tools as slash commands (v4.0.0)
**Related**: #22 (LLM semantic analysis), #23 (test coverage)

## Overview

Migrate the 6 CLI tools from the ai-risk-mapper skill to proper slash commands in `plugins/ai-risk-mapper/commands/`. This improves discoverability and provides a consistent invocation pattern.

## Commands to Create

| Command | Script | Purpose |
|---------|--------|---------|
| `/risk-search` | `cli_risk_search.py` | Search risks by keyword |
| `/control-search` | `cli_control_search.py` | Search controls by keyword |
| `/controls-for-risk` | `cli_controls_for_risk.py` | Get controls for a specific risk ID |
| `/persona-profile` | `cli_persona_profile.py` | Get persona risk profile |
| `/gap-analysis` | `cli_gap_analysis.py` | Assess control coverage gaps |
| `/framework-map` | `cli_framework_map.py` | Map risk to compliance frameworks |

## Implementation Steps

### Step 1: Create Command Files

Create 6 command markdown files in `plugins/ai-risk-mapper/commands/`:

#### 1.1 risk-search.md
```markdown
Search CoSAI risks by keyword.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_risk_search.py $ARGUMENTS
```

Arguments:
- `<query>` - Search term (required)
- `--offline` - Use bundled schemas instead of fetching

Examples:
```
/risk-search injection
/risk-search "data poisoning" --offline
/risk-search training
```

Report the matching risks with their IDs, categories, personas, and control counts.
```

#### 1.2 control-search.md
```markdown
Search CoSAI controls by keyword.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_control_search.py $ARGUMENTS
```

Arguments:
- `<query>` - Search term (required)
- `--offline` - Use bundled schemas

Examples:
```
/control-search validation
/control-search "access control" --offline
```

Report matching controls with their IDs, descriptions, and applicable risks.
```

#### 1.3 controls-for-risk.md
```markdown
Get all controls that mitigate a specific risk.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_controls_for_risk.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., DP, PIJ, ADI)
- `--offline` - Use bundled schemas

Examples:
```
/controls-for-risk DP
/controls-for-risk PIJ --offline
```

Report all applicable controls for the specified risk with descriptions.
```

#### 1.4 persona-profile.md
```markdown
Get the risk profile for a specific persona.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_persona_profile.py $ARGUMENTS
```

Arguments:
- `<persona-id>` - Persona identifier (required)
  - `personaModelCreator` - Organizations training/fine-tuning models
  - `personaModelConsumer` - Organizations deploying pre-trained models
- `--offline` - Use bundled schemas

Examples:
```
/persona-profile personaModelCreator
/persona-profile personaModelConsumer --offline
```

Report all risks relevant to the persona with categories and severity.
```

#### 1.5 gap-analysis.md
```markdown
Assess control coverage gaps for a specific risk.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_gap_analysis.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., DP, PIJ)
- `--implemented <control-ids>` - Space-separated list of implemented controls
- `--offline` - Use bundled schemas

Examples:
```
/gap-analysis DP --implemented controlTrainingDataSanitization
/gap-analysis PIJ --implemented controlInputValidation controlOutputFiltering --offline
```

Report coverage percentage, implemented controls, missing controls, and prioritized recommendations.
```

#### 1.6 framework-map.md
```markdown
Map a risk to external compliance frameworks.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_framework_map.py $ARGUMENTS
```

Arguments:
- `<risk-id>` - Risk identifier (required, e.g., PIJ, DP)
- `--framework <name>` - Filter by framework (optional)
  - `mitre-atlas` - MITRE ATLAS techniques
  - `nist-ai-rmf` - NIST AI Risk Management Framework
  - `owasp-llm` - OWASP Top 10 for LLM
- `--offline` - Use bundled schemas

Examples:
```
/framework-map PIJ
/framework-map PIJ --framework mitre-atlas
/framework-map DP --framework owasp-llm --offline
```

Report all framework mappings for the specified risk with technique IDs and descriptions.
```

### Step 2: Update SKILL.md

Update the Interactive Exploration section in `plugins/ai-risk-mapper/skills/ai-risk-mapper/SKILL.md` to reference the new slash commands instead of `uv run` invocations:

**Before:**
```markdown
| `/risk-search <query>` | Search risks by keyword | `uv run scripts/cli_risk_search.py "injection"` |
```

**After:**
```markdown
| `/risk-search <query>` | Search risks by keyword | Search for injection-related risks |
```

### Step 3: Optional - Add Orchestrator Command

Consider adding `/risk-assess` command for the orchestrator:

#### risk-assess.md
```markdown
Run a full AI security risk assessment on a target.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/orchestrate_risk_assessment.py $ARGUMENTS
```

Arguments:
- `--target <path>` - Target to analyze (file, directory, or description)
- `--output-dir <path>` - Output directory for reports (default: ./risk-assessment-output)
- `--offline` - Use bundled schemas

Examples:
```
/risk-assess --target ./my-ai-app
/risk-assess --target ./architecture.md --output-dir ./security-review
```

Runs the full risk assessment workflow and generates a comprehensive report.
```

### Step 4: Version Bump

Update version in `plugin.json` and SKILL.md metadata:
- Current: 3.0.1
- New: 4.0.0 (MAJOR - breaking change to user interaction pattern)

### Step 5: Update IMPROVEMENT_PLAN.md

Add entry documenting the v4.0.0 release with slash commands.

### Step 6: Test Commands

Test each command works correctly:
```bash
/risk-search injection
/control-search validation
/controls-for-risk DP
/persona-profile personaModelCreator
/gap-analysis PIJ --implemented controlInputValidation
/framework-map PIJ --framework mitre-atlas
```

## File Changes Summary

| File | Action |
|------|--------|
| `commands/risk-search.md` | Create |
| `commands/control-search.md` | Create |
| `commands/controls-for-risk.md` | Create |
| `commands/persona-profile.md` | Create |
| `commands/gap-analysis.md` | Create |
| `commands/framework-map.md` | Create |
| `commands/risk-assess.md` | Create (optional) |
| `skills/ai-risk-mapper/SKILL.md` | Update command table |
| `.claude-plugin/plugin.json` | Update version to 4.0.0 |
| `skills/ai-risk-mapper/IMPROVEMENT_PLAN.md` | Add v4.0.0 entry |

## Success Criteria

- [ ] All 6 CLI tools have corresponding slash commands
- [ ] Commands appear in `/help` output when plugin is loaded
- [ ] `$ARGUMENTS` properly passes user input to scripts
- [ ] `${CLAUDE_PLUGIN_ROOT}` correctly resolves to plugin directory
- [ ] `--offline` flag works for all commands
- [ ] SKILL.md updated to reference slash commands
- [ ] Version bumped to 4.0.0

## Considerations

1. **Backward Compatibility**: The CLI scripts remain unchanged, so direct `uv run` invocations still work
2. **LLM Integration (#22)**: Commands could later gain `--semantic` flag when v3.1.0 ships
3. **Test Coverage (#23)**: Command invocations should be included in integration tests
4. **Naming Convention**: Commands use plugin-agnostic names (not prefixed with `arm-` or similar) since they're scoped to the plugin
