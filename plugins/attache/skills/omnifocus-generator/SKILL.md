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

This skill's references are flat (per AgentSkills spec: "Keep reference chains one-level deep from SKILL.md"). Each reference covers one topic and is loaded only when relevant — do not pre-read all of them.

| Reference | Use When |
|-----------|----------|
| `references/tasks_projects_tags.md` | Generating Task / Project / Tag / Folder CRUD code — check ofoCore exports first |
| `references/perspectives.md` | Generating perspective queries or configuring filter rules |
| `references/forms_ui.md` | Building Form, Alert, Picker, or TextField UI inside a plugin action |
| `references/foundation_models.md` | Using `LanguageModel.Session` / `Schema` / `GenerationOptions` for on-device AI; includes the Foundation Models task-organizer worked example |
| `references/files_export.md` | FileWrapper, FileType, FileSaver, JSON / CSV / TaskPaper / Markdown export |
| `references/localization.md` | `Resources/<locale>.lproj/*.strings` setup for action labels |
| `references/url_scheme_callbacks.md` | `omnifocus://` URLs, `omnijs-run`, `x-callback-url`, app-to-app, Shortcuts integration |
| `references/libraries_shared_code.md` | `PlugIn.Library` pattern; how to consume Attache's `ofoCore` library from a generated plugin |
| `references/settings_preferences.md` | `Settings`, `Preferences` (with IIFE footgun), `SyncedPreferences` |
| `references/outline_tree_ui.md` | `DocumentWindow.content` / `sidebar`, `Tree`, `TreeNode` — outline-based plugin actions |
| `references/capability_inventory.md` | Coverage map of `omni-automation.com` → local refs (covered / partial / missing). Read when you suspect a capability isn't documented locally. |
| `references/web_fetch_protocol.md` | One-off WebFetch contract for reaching out to `omni-automation.com` mid-task — URL template + prompt + token-cost reminder |
| `references/inventory_refresh_workflow.md` | Re-runnable workflow that refreshes `capability_inventory.md` (quarterly cadence or on-demand) |
| `references/channel_selection.md` | CLI vs Plugin action vs standalone plugin vs JXA — which channel for which use case |
| `references/code_generation_validation.md` | TypeScript validation rules + build pipeline (read before any generator changes) |
| `references/omni_automation_guide.md` | General plugin development patterns (legacy — content being absorbed into the topic-specific capability docs above) |
| `references/automation_best_practices.md` | Patterns and anti-patterns (legacy — content being absorbed) |

For the full OmniFocus Omni Automation API (Task, Project, Tag, Folder, Database class reference), see `../../omnifocus-core/references/omnifocus_api.md` — single source of truth, not duplicated here.
