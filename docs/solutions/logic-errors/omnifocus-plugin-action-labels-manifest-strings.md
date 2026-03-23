---
title: OmniFocus Plugin Action Labels — manifest.strings is the Source of Truth
tags: [omnifocus, omni-automation, plugin, manifest, localization]
date: 2026-03-23
---

## Problem

After updating `manifest.json` action `label` fields (e.g. `"label": "Attache: Clarify Tasks"`), the OmniFocus Automation menu continued to show the raw camelCase identifier names (`analyzeSelected`, `analyzeHierarchy`, etc.) even after uninstalling and reinstalling the plugin.

## Root Cause

OmniFocus reads Automation Menu display names from `Resources/en.lproj/manifest.strings`, **not** from the `label` field in `manifest.json`. The `label` field in `manifest.json` is effectively unused for menu display. Without entries in `manifest.strings`, actions fall back to their `identifier` values.

## Fix

Add one line per action to `Resources/en.lproj/manifest.strings`:

```
"com.your.bundle.id" = "Plugin Name";
"actionIdentifier.label" = "Display Label";
```

**Attache example (`en.lproj/manifest.strings`):**

```
"com.totallytools.omnifocus.attache" = "Attache";
"dailyReview.label" = "Attache: Daily Review";
"weeklyReview.label" = "Attache: Weekly Review";
"analyzeSelected.label" = "Attache: Clarify Tasks";
"analyzeHierarchy.label" = "Attache: Project Health";
"completedSummary.label" = "Attache: Wins Report";
"systemSetup.label" = "Attache: Setup";
"discoverSystem.label" = "Attache: Map System";
```

Key: `"<identifier>.label"` — the identifier must match the `identifier` field in `manifest.json`, not the filename.

## Why `manifest.json` Labels Exist

The `label` field in `manifest.json` appears to be used by the Omni Automation framework for programmatic access (e.g. `action.label`) and possibly future API use, but is not surfaced in the OmniFocus Automation menu. Always treat `manifest.strings` as the display source of truth.

## Prevention

- When adding a new action to a bundle plugin, add its `.label` entry to `manifest.strings` at the same time as the `manifest.json` entry.
- The SKILL.md plugin generation workflow Step 4.5 now includes this check.
- The `omni_automation_guide.md` Quick Diagnostic section documents this symptom.

## Validated

2026-03-23 against OmniFocus 4 on macOS 26. Affected: Attache v1.4.0 (PR #133 / fix commit `41d9c2d`).
