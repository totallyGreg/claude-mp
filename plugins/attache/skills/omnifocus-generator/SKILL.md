---
name: omnifocus-generator
description: |
  This skill should be used when creating OmniFocus Automation plugins (.omnifocusjs), JXA scripts for OmniFocus, or OmniFocus automation artifacts. Triggers when user asks "create OmniFocus plugin", "generate OmniFocus plugin", "build .omnifocusjs", "build OmniFocus automation", "build JXA script for OmniFocus", "create OmniFocus action", or "make OmniFocus plugin".

  Do NOT trigger for: "create a plugin" without OmniFocus context (ask for clarification), "create a Claude plugin" (use plugin-dev skill), "install a plugin" (use omnifocus-core skill), "show tasks" or "analyze" (use omnifocus-core skill).

  WORKFLOW: 1) CLASSIFY query vs plugin 2) SELECT format (solitary/solitary-fm/bundle/solitary-library) 3) COMPOSE from libraries 4) GENERATE via `node scripts/generate_plugin.js` - NEVER Write/Edit tools 5) VALIDATE via `bash scripts/validate-plugin.sh` 6) TEST in OmniFocus.
license: MIT
metadata:
  version: 1.0.0
  author: totally-tools
compatibility:
  platforms: [macos]
  requires:
    - OmniFocus 3 or 4
    - Node.js 18+ (for TypeScript plugin generation)
    - macOS with automation permissions
---

# OmniFocus Plugin Generator

## CRITICAL: Plugin Generation Workflow

**If user requests "create OmniFocus plugin" or "make OmniFocus plugin", follow these EXACT steps:**

### STEP 1: CLASSIFY
```
Keywords in request → Classification:
- "create OmniFocus plugin", "make OmniFocus plugin", "generate OmniFocus plugin" → PLUGIN GENERATION (continue to step 2)
- "create structured project", "project with action groups", "bulk create" → DEFER to omnifocus-core (manage_omnifocus.js bulk-create)
- "build JXA script for OmniFocus", "write an OmniFocus script" → CHECK omnifocus-core ofo CLI first; if covered → defer; if not → JXA COMPOSITION; NEVER write ad-hoc inline scripts
- "automate this", "recurring task" → CHANNEL SELECTION (see references/channel_selection.md)
- "improve script", "fix script" → SCRIPT MODIFICATION (read existing, modify, validate)
- "show me", "what tasks", "analyze" → DEFER to omnifocus-core (query/execution)
```

### STEP 2: SELECT FORMAT
```
- Single action, no AI     → --format solitary
- Single action, with AI   → --format solitary-fm
- Multiple actions         → --format bundle --template <name>
- Library for reuse        → --format solitary-library
```

### STEP 3: GENERATE (TypeScript validation automatic)
```bash
node scripts/generate_plugin.js --format <FORMAT> --name "<NAME>"
```
**RED FLAG:** If about to use Write or Edit tool for .js/.omnijs files → STOP, use generator instead
**RED FLAG:** If about to write an inline Omni Automation script → STOP. Check if omnifocus-core ofo CLI covers it first. Structured project with action groups needed? → defer to omnifocus-core `manage_omnifocus.js bulk-create`.

### STEP 4: VALIDATE (Always run)
```bash
bash scripts/validate-plugin.sh <generated-plugin-path>
```

### STEP 4.5: BUMP VERSION + STRINGS
1. Bump the version in the `.omnifocusjs` manifest — OmniFocus won't reload without a version change.
2. For **bundle plugins**: each action needs `Resources/en.lproj/<identifier>.strings`.

### STEP 5: REPORT
```
Plugin generated: <path>
Validation: PASSED → Ready for installation
open <path>   # OmniFocus prompts for install location
```

See `references/code_generation_validation.md` for TypeScript validation details.

## Reference Documentation

- `references/code_generation_validation.md` - TypeScript validation rules, build pipeline
- `references/omni_automation_guide.md` - Plugin development patterns
- `references/automation_best_practices.md` - Patterns and anti-patterns
- `references/channel_selection.md` - Mac vs iOS routing, library composition
