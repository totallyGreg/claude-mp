# OmniFocus Plugin Development Tools

Tools for validating, testing, and debugging OmniFocus plugins during development.

## Overview

These tools help ensure your plugin works correctly **before** installing it in OmniFocus:

```
development-tools/
├── README.md                    # This file
├── validate-plugin.sh           # Structure and manifest validation
└── test-plugin-libraries.js     # Library testing (pre-installation)
```

## When to Use These Tools

**Pre-Installation (Before `open MyPlugin.omnifocusjs`):**
1. Run `validate-plugin.sh` - Checks structure, manifest, file organization
2. Run `test-plugin-libraries.js` - Tests libraries can be loaded

**Post-Installation (After installing in OmniFocus):**
1. Test actions in Automation Console (see Plugin Development Guide)
2. Verify plugin functionality
3. Follow testing procedures in [Plugin Development Guide](../../references/plugin_development_guide.md#validation--testing)

## Quick Start

```bash
# Navigate to your plugin directory
cd /path/to/MyPlugin.omnifocusjs

# 1. Validate plugin structure
bash ../omnifocus-manager/assets/development-tools/validate-plugin.sh .

# 2. Test libraries (if your plugin has libraries)
osascript -l JavaScript ../omnifocus-manager/assets/development-tools/test-plugin-libraries.js .

# 3. If all checks pass, install
open MyPlugin.omnifocusjs
```

---

## Tool Reference

### validate-plugin.sh

**Purpose:** Validates plugin structure and manifest before installation.

**Usage:**
```bash
bash validate-plugin.sh /path/to/Plugin.omnifocusjs
```

**Checks performed:**
- ✅ manifest.json is valid JSON
- ✅ Required manifest fields present (identifier, version, author, etc.)
- ✅ Action identifiers match .js filenames in Resources/
- ✅ Library declarations match library files
- ✅ No invalid file structures

**Exit codes:**
- `0` - All checks passed
- `1` - Validation failed (see error output)

**Example output:**
```
✅ manifest.json is valid JSON
✅ Plugin version: 1.0.0
✅ All action files exist
✅ Plugin structure valid
=== All Structure Checks Passed! ===
```

---

### test-plugin-libraries.js

**Purpose:** Tests that plugin libraries can be loaded before installation.

**Usage:**
```bash
osascript -l JavaScript test-plugin-libraries.js /path/to/Plugin.omnifocusjs
```

**Tests performed:**
- Library files can be read
- Libraries use correct structure
- Library functions are defined
- Basic export functionality works

**Note:** This simulates library loading but cannot fully test runtime behavior. Full testing requires installation in OmniFocus.

**Example output:**
```
=== Testing Plugin Libraries ===

Test 1: Loading myLibrary library...
✅ myLibrary library loaded successfully
   Functions: functionA, functionB, functionC

=== All Tests Passed! ===
```

**For complete testing procedures, see:**
- [Plugin Development Guide - Validation & Testing](../../references/plugin_development_guide.md#validation--testing)
- [Plugin Development Guide - Distribution Checklist](../../references/plugin_development_guide.md#distribution-checklist)

---

## Workflow Integration

### Development Workflow

```
1. Create/modify plugin
   ↓
2. Run validate-plugin.sh
   ├─ PASS → Continue
   └─ FAIL → Fix errors, repeat step 2
   ↓
3. Run test-plugin-libraries.js (if plugin has libraries)
   ├─ PASS → Continue
   └─ FAIL → Fix library issues, repeat step 3
   ↓
4. Review plugin-checklist.md
   ├─ All checks pass → Continue
   └─ Missing steps → Complete, repeat step 4
   ↓
5. Install in OmniFocus: open MyPlugin.omnifocusjs
   ↓
6. Test in OmniFocus Automation Console
   ↓
7. Test all actions in OmniFocus
   ↓
8. Ready for distribution!
```

### CI/CD Integration

```bash
#!/bin/bash
# Example CI script

set -e  # Exit on error

echo "Validating plugin structure..."
bash tools/validate-plugin.sh MyPlugin.omnifocusjs

echo "Testing libraries..."
osascript -l JavaScript tools/test-plugin-libraries.js MyPlugin.omnifocusjs

echo "All pre-installation checks passed!"
```

---

## Common Issues Caught by These Tools

**validate-plugin.sh catches:**
- Invalid JSON in manifest.json
- Missing required manifest fields
- Action files that don't match manifest declarations
- Library files that don't match manifest declarations
- Incorrect file organization

**test-plugin-libraries.js catches:**
- Libraries that fail to load
- Missing library functions
- Syntax errors in library code
- Export structure issues

**plugin-checklist.md helps catch:**
- Actions that don't appear in menu
- Libraries that return null at runtime
- Actions that crash on execution
- Missing validation logic
- Incomplete error handling

---

## Best Practices

### Always Validate Before Installing

```bash
# DON'T do this:
open MyPlugin.omnifocusjs  # Install without checking

# DO this:
bash validate-plugin.sh MyPlugin.omnifocusjs && \\
  open MyPlugin.omnifocusjs
```

### Automate Validation

Add to your build script:
```bash
#!/bin/bash
# build.sh

# Validate before distribution
bash development-tools/validate-plugin.sh MyPlugin.omnifocusjs

if [ $? -eq 0 ]; then
    echo "Creating distribution package..."
    zip -r MyPlugin.zip MyPlugin.omnifocusjs
else
    echo "Validation failed. Fix errors before distributing."
    exit 1
fi
```

### Keep Tools Updated

These tools evolve with OmniFocus API changes. Pull updates regularly:
```bash
cd skills/omnifocus-manager
git pull origin main
```

---

## Limitations

**What these tools CAN'T test:**
- Actual OmniFocus API behavior (requires installation)
- Action validation logic (requires OmniFocus runtime)
- User interaction flows
- Cross-platform compatibility (Mac vs iOS)
- Performance under load

**For complete testing:** Always install and test in actual OmniFocus environment.

---

## Related Documentation

- [Plugin Development Guide](../../references/plugin_development_guide.md)
- [Plugin Installation](../../references/plugin_installation.md)
- [OFBundlePlugInTemplate](../OFBundlePlugInTemplate.omnifocusjs/) - Official template
- [Plugin Quickstart](../../references/quickstarts/plugin_quickstart.md)

---

## Troubleshooting

### "validate-plugin.sh: command not found"

**Solution:** Use full path or make executable:
```bash
chmod +x validate-plugin.sh
./validate-plugin.sh MyPlugin.omnifocusjs
```

### "Permission denied" when running scripts

**Solution:** Grant execute permission:
```bash
chmod +x *.sh
chmod +x *.js
```

### Tests pass but plugin fails in OmniFocus

**Possible causes:**
1. Runtime API differences (validate manifest)
2. OmniFocus version mismatch (check compatibility)
3. Library loading issues (test in Automation Console)
4. Action validation logic errors (review action code)

**Next steps:** Test in OmniFocus Automation Console following plugin-checklist.md procedures.

---

## Contributing

When improving these tools:

1. **Maintain backward compatibility** - Don't break existing workflows
2. **Add tests for new checks** - Validate new validation logic
3. **Document new features** - Update this README
4. **Test on actual plugins** - Validate against OFBundlePlugInTemplate and production plugins

---

## License

Part of the omnifocus-manager skill. See parent directory for license information.
