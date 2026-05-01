# Plugin Templates

**⚠️ DO NOT MODIFY THESE TEMPLATES MANUALLY**

These templates are used by `scripts/generate_plugin.js` with variable substitution. Modifying templates directly can break plugin generation.

## Usage

To create a plugin, use the generator:

```bash
node scripts/generate_plugin.js --format <format> --name "<name>"
```

The generator automatically:
1. Loads the appropriate template
2. Substitutes variables ({{PLUGIN_NAME}}, {{IDENTIFIER}}, etc.)
3. Validates TypeScript against `typescript/omnifocus.d.ts`
4. Creates working plugin files

## Available Templates

### Solitary Formats (single-file plugins)

**`solitary-action/`** - Basic action plugin
```bash
node scripts/generate_plugin.js --format solitary --name "My Plugin"
```
- Single .omnijs file
- One action only
- No Foundation Models support
- Lightweight and simple

**`solitary-action-fm/`** - Action with Foundation Models
```bash
node scripts/generate_plugin.js --format solitary-fm --name "AI Analyzer"
```
- Single .omnijs file
- Includes Foundation Models (Apple Intelligence) integration
- Requires: OmniFocus 4.8+, macOS 15.2+, Apple Silicon
- Icon: apple.intelligence

**`solitary-library/`** - Reusable library
```bash
node scripts/generate_plugin.js --format solitary-library --name "MyUtilities"
```
- Library plugin for code reuse
- Can be imported by other plugins
- No actions, just shared functions

### Bundle Formats (multi-action plugins)

**`query-simple/`** - Simple query template
```bash
node scripts/generate_plugin.js --format bundle --template query-simple --name "Task Tools"
```
- Multiple actions in Resources/ folder
- Localization support (en.lproj/)
- Shared libraries between actions
- Uses Alert for display

**`stats-overview/`** - Statistics dashboard template
```bash
node scripts/generate_plugin.js --format bundle --template stats-overview --name "Dashboard"
```
- Statistics and metrics display
- Multiple related actions
- Complex plugin with resources

## Template Variables

Templates use these substitution variables:

- `{{PLUGIN_NAME}}` - Plugin display name
- `{{IDENTIFIER}}` - Reverse domain identifier (e.g., com.user.omnifocus.myplugin)
- `{{AUTHOR}}` - Plugin author
- `{{DESCRIPTION}}` - Plugin description
- `{{ACTION_ID}}` - Action identifier (camelCase)
- `{{ACTION_LABEL}}` - Action label
- `{{ICON}}` - SF Symbol icon name

## Validation

After generation, all plugins are automatically validated:

```bash
# Automatic during generation (TypeScript validation)
node scripts/generate_plugin.js --format solitary --name "Test"

# Manual validation (comprehensive checks)
bash scripts/validate-plugin.sh <plugin-path>
```

Validation includes:
- TypeScript type-checking against OmniFocus API
- Manifest structure verification
- Action/library file existence
- JavaScript linting (eslint_d or osascript)
- API anti-pattern detection

## Modifying Templates

**If you need to modify a template:**

1. Create a backup first
2. Test modifications with validation before committing
3. Update this README if template structure changes
4. Document new variables if added

**Common modification points:**
- Action logic in template files
- Default icon choices
- Manifest metadata structure

## Library Composition

To compose workflows using existing libraries, see:
- `../../scripts/libraries/omni/` - Reusable libraries (taskMetrics, exportUtils, patterns, etc.)
- `../../scripts/libraries/README.md` - Library documentation and usage patterns

Generated plugins in `../` are outputs from the generator, not reference materials.

## Documentation

For more information:
- `../../references/omni_automation_guide.md` - Plugin development guide
- `../../references/code_generation_validation.md` - Validation rules
- `../../typescript/README.md` - TypeScript validation setup
- `../../SKILL.md` - Complete skill documentation
