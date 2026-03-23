---
title: OmniFocus Plugin Action Labels — Per-Action .strings Files Required
tags: [omnifocus, omni-automation, plugin, manifest, localization]
date: 2026-03-23
---

## Problem

After updating `manifest.json` action `label` fields (e.g. `"label": "Attache: Clarify Tasks"`), the OmniFocus Automation menu continued to show the raw camelCase identifier names (`analyzeSelected`, `analyzeHierarchy`, etc.) even after uninstalling and reinstalling the plugin.

## Root Cause

OmniFocus reads Automation Menu action display names from **per-action `.strings` files** (`Resources/en.lproj/<identifier>.strings`), **not** from the `label` field in `manifest.json` and **not** from `manifest.strings`.

- `manifest.json` `label` field — used by Omni Automation framework for programmatic access (`action.label`); NOT surfaced in the Automation Menu
- `en.lproj/manifest.strings` — controls the **plugin submenu name only** (the top-level grouping label)
- `en.lproj/<identifier>.strings` — controls the **action's display label** in the Automation Menu

Without a per-action `.strings` file, OmniFocus falls back to the raw `identifier` value (camelCase).

## Fix

Create one `.strings` file per action in `Resources/en.lproj/`:

```
// Resources/en.lproj/myAction.strings
"label" = "My Action Label";
"shortLabel" = "My Action Label";
"mediumLabel" = "My Action Label";
"longLabel" = "My Action Label";
```

The filename must match the action's `identifier` field in `manifest.json` (not the filename of the action script).

**Attache example — files created:**

```
Resources/en.lproj/manifest.strings          → "Attache" (plugin submenu name only)
Resources/en.lproj/dailyReview.strings       → "Attache: Daily Review"
Resources/en.lproj/weeklyReview.strings      → "Attache: Weekly Review"
Resources/en.lproj/analyzeSelected.strings   → "Attache: Clarify Tasks"
Resources/en.lproj/analyzeHierarchy.strings  → "Attache: Project Health"
Resources/en.lproj/completedSummary.strings  → "Attache: Wins Report"
Resources/en.lproj/systemSetup.strings       → "Attache: Setup"
Resources/en.lproj/discoverSystem.strings    → "Attache: Map System"
```

Each `.strings` file contains all four label keys:

```
"label" = "Attache: Daily Review";
"shortLabel" = "Attache: Daily Review";
"mediumLabel" = "Attache: Daily Review";
"longLabel" = "Attache: Daily Review";
```

## Why `manifest.json` Labels Exist

The `label` field in `manifest.json` appears to be used by the Omni Automation framework for programmatic access (e.g. `action.label`) and possibly future API use, but is not surfaced in the OmniFocus Automation menu. Always treat per-action `.strings` files as the display source of truth.

## Prevention

- When adding a new action to a bundle plugin, create its `en.lproj/<identifier>.strings` file at the same time as the `manifest.json` entry.
- The SKILL.md plugin generation workflow Step 4.5 now includes this check.
- The `omni_automation_guide.md` Quick Diagnostic section documents this symptom.

## Validated

2026-03-23 against OmniFocus 4 on macOS 26. Affected: Attache v1.4.0 (PR #133 / fix commit `ab8f405`).
