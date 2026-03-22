---
title: "feat: Full GTD-informed Attache audit + superseded asset cleanup"
type: feat
status: active
date: 2026-03-22
github_issue: "#127"
related_plans:
  - docs/plans/2026-03-08-feat-attache-omnifocus-unified-plugin-plan.md
  - docs/plans/2026-03-22-002-refactor-ofo-script-consolidation-gtd-coverage-plan.md
related_issues:
  - "#121"
  - "#125"
---

# feat: Full GTD-informed Attache Audit + Superseded Asset Cleanup

## Overview

Use the GTD-coach methodology to holistically evaluate Attache v1.3.0 as the consolidated OmniFocus AI plugin, compare it action-by-action and library-by-library against ALL legacy plugins (AITaskAnalyzer, CompletedTasksSummary, Overview, TodaysTasks), identify and port any missing functionality, then remove superseded bundles, orphaned scripts, and stale references.

The goal: Attache becomes a well-organized, best-of-breed tool for managing everything tracked by OmniFocus, with no functionality regressions from removed plugins.

## Problem Statement / Motivation

After the Attache v1.3.0 consolidation (#125), the repository still carries 4 superseded `.omnifocusjs` bundles (AITaskAnalyzer, CompletedTasksSummary, Overview, TodaysTasks) plus a test harness (ofocore-test). These create confusion about which plugin to use, inflate repo size, and risk divergent maintenance. Issue #127 gates removal on a thorough comparison, but the scope here is broader: use GTD methodology to ensure Attache covers all 5 GTD phases before declaring the consolidation complete.

## Proposed Solution

Three-phase approach: **Audit -> Port -> Clean**. Phases 1 and 2 are already complete (see analysis below). The remaining work is Phase 3: verify via `diff -r`, ratify the `saveToFile` decision, then remove and update docs.

### Phase 1: GTD-Informed Audit (Complete)

The GTD-coach skill's 5-phase framework confirms Attache + ofo CLI provide complete GTD coverage:

**GTD Coverage Matrix:**

| GTD Phase | Attache Action | ofo CLI | Coverage |
|-----------|---------------|---------|----------|
| Capture | -- | `ofo create` | CLI only |
| Clarify | -- | `ofo list inbox`, `ofo update` | CLI only |
| Organize | -- | `ofo update`, `ofo tag` | CLI only |
| Reflect (daily) | `dailyReview` | `ofo list today` | Both |
| Reflect (weekly) | `weeklyReview` | `gtd-queries.js stalled/waiting/neglected` | Both |
| Reflect (projects) | `analyzeProjects`, `analyzeHierarchy` | `ofo perspective` | Both |
| Engage | `analyzeSelected`, `analyzeTasksWithAI` | `ofo list overdue`, `ofo-tagged` | Both |
| System | `systemSetup`, `discoverSystem` | `ofo stats` | Both |
| Review | `completedSummary` | `ofo completed-today` | Both |

**Observation:** Capture/Clarify/Organize are correctly CLI-only (no plugin needed). Reflect and Engage have dual coverage. Attache's role is the AI-enhanced analysis layer atop the CLI's CRUD layer. This is architecturally sound per the "Perspectives over Scripts" principle.

**Known gap from existing plans:** `ofo list due-soon --days N` for weekly review Reflect phase (tracked in #121, not Attache's responsibility).

### Phase 2: Action-by-Action + Library Comparison (Complete)

#### Action Comparison: AITaskAnalyzer v3.6.0 vs Attache v1.3.0

| AITaskAnalyzer Action | Attache Action | Status |
|----------------------|----------------|--------|
| `analyzeTasksWithAI` | `analyzeTasksWithAI` | Migrated |
| `analyzeProjects` | `analyzeProjects` | Migrated |
| `analyzeSelectedTasks` | `analyzeSelected` | Migrated (renamed) |
| `analyzeHierarchy` | `analyzeHierarchy` | Migrated |
| `discoverSystem` | `discoverSystem` | Migrated |
| `dailyReview` | `dailyReview` | Migrated + enhanced (27% larger) |
| `weeklyReview` | `weeklyReview` | Migrated + enhanced (13% larger, +Waiting For) |
| `systemSetup` | `systemSetup` | Migrated |
| -- | `completedSummary` | New (absorbed from CompletedTasksSummary) |

**Result:** All 8 AITaskAnalyzer actions present in Attache. Attache adds 1 new action.

#### Absorbed Plugin Comparison

| Plugin | Actions | Absorbed Into | Gap? |
|--------|---------|--------------|------|
| CompletedTasksSummary v1.0.0 | `completedSummary`, `saveToFile` | `completedSummary` action | **YES -- `saveToFile` not ported** |
| Overview v1.0.1 | `overviewAction` | Folded into `dailyReview` | No |
| TodaysTasks v1.0.0 | `todaysTasksAction` | Folded into `dailyReview` | No |

#### Library Comparison

Both bundles share 9 identically-named libraries. Attache's copies are newer/enhanced:

| Library | AITaskAnalyzer Size | Attache Size | Delta |
|---------|-------------------|--------------|-------|
| `taskMetrics.js` | 3,584 B | 5,713 B | +59% (enhanced) |
| `preferencesManager.js` | 4,752 B | 5,654 B | +19% (enhanced) |
| `systemDiscovery.js` | 42,358 B | 43,439 B | +2% (updated) |
| `dailyReview.js` (action) | 7,640 B | 9,754 B | +27% (enhanced) |
| `weeklyReview.js` (action) | 21,383 B | 24,247 B | +13% (enhanced) |
| Others | identical | identical | 0% |

**Verification step:** Run `diff -r AITaskAnalyzer.omnifocusjs/Resources Attache.omnifocusjs/Resources` to confirm no AITaskAnalyzer-only improvements were missed.

### Phase 3: Verify, Remove + Update Docs (Remaining Work)

#### 3a. Ratify `saveToFile` Decision

CompletedTasksSummary's `saveToFile` action wrote markdown to disk via `FileSaver`. Attache's `completedSummary` only offers "Copy to Clipboard." **Confirm during execution** that this deliberate exclusion is acceptable.

**Recommendation:** Do NOT port `saveToFile` to Attache. Rationale:
- OmniFocus plugins have limited filesystem access (sandboxed)
- The ofo CLI provides `ofo completed-today --markdown` which can be piped to a file via shell redirection
- Clipboard + paste is the standard OmniFocus plugin pattern
- Adding file I/O to Attache violates KISS

Document this as a deliberate scope reduction in the assets README.

#### 3b. Remove Superseded Bundles

| Asset to Remove | Size | Reason |
|----------------|------|--------|
| `AITaskAnalyzer.omnifocusjs/` | 26 files | All actions/libraries present in Attache with enhancements |
| `CompletedTasksSummary.omnifocusjs/` | ~6 files | `completedSummary` absorbed; `saveToFile` deliberately not ported |
| `Overview.omnifocusjs/` | ~4 files | Folded into `dailyReview` |
| `TodaysTasks.omnifocusjs/` | ~4 files | Folded into `dailyReview` |
| `ofocore-test.omnifocusjs/` | ~4 files | One-time test harness, already passed |

#### 3c. Remove Orphaned Scripts

| Script to Remove | Reason |
|-----------------|--------|
| `test-plugin-libraries.js` | Tests AITaskAnalyzer libraries specifically |
| `validate-js-syntax.js` | Standalone validator, not referenced by any workflow |

#### 3d. Reference Sweep

After deletion, grep for all references to removed assets and update:

```bash
rg -l "AITaskAnalyzer|CompletedTasksSummary|Overview\.omnifocusjs|TodaysTasks|ofocore-test|test-plugin-libraries|validate-js-syntax" plugins/omnifocus-manager/
```

**Known stale references to fix:**

| File | What to Fix |
|------|------------|
| `assets/README.md` | Complete rewrite -- currently doesn't mention Attache at all |
| `references/foundation_models_integration.md` | Update code example paths from AITaskAnalyzer to Attache |
| `references/workflows.md` | Remove TodaysTasks reference |
| `references/omni_automation_guide.md` (lines 572, 602) | Fix wrong bundle ID: `com.totally-tools.attache` -> `com.totallytools.omnifocus.attache` |
| `SKILL.md` (line ~190) | Update "After installing Attache, you can remove..." to reflect that removal is done |

#### 3e. Rewrite Assets README

The assets README must be rewritten to reflect the post-cleanup state:

- **Attache** as the primary AI plugin (with action inventory)
- **TreeExplorer** as a standalone utility (explicitly retained)
- **OFBundlePlugInTemplate** as the official Omni Group template (explicitly retained)
- **plugin-templates/** for the generator workflow
- **examples/** for library usage patterns
- Document that `saveToFile` is deliberately not in Attache (use CLI + shell redirection)

## Technical Considerations

- **Verification before deletion:** Run `diff -r` on AITaskAnalyzer vs Attache Resources directories to confirm no divergent improvements exist in the old plugin
- **Plugin version bump:** Attache does NOT need a version bump for this work (no plugin code changes unless gap porting is needed)
- **Reference sweep thoroughness:** Use the lesson from `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` -- after any deletion, grep recursively and verify no stale paths remain
- **Coordination with #121:** That issue covers script consolidation (orphaned scripts like `ai-analyze.js`, `analyze_insights.js`, etc.) and `manage_omnifocus.js` migration. This plan covers plugin bundle removal. They touch overlapping docs (`assets/README.md`, `references/workflows.md`) but different primary artifacts. Sequence: this plan can run independently, but the assets README rewrite should be the final documentation pass

## System-Wide Impact

Low risk. Removed bundles are standalone OmniFocus plugins installed on-device -- they have no cross-dependencies with the ofo CLI, skills, or scripts. Removing source bundles from the repo doesn't affect already-installed instances. Verify `bash scripts/validate-plugin.sh` still passes on Attache after cleanup.

## Acceptance Criteria

### Functional Requirements

- [ ] GTD coverage matrix reviewed -- all 5 phases have appropriate tool coverage (Attache + ofo CLI)
- [ ] All 8 AITaskAnalyzer actions confirmed present in Attache (with enhancements)
- [ ] CompletedTasksSummary absorption verified (`completedSummary` action works, `saveToFile` deliberately excluded)
- [ ] Overview and TodaysTasks functionality confirmed folded into `dailyReview`
- [ ] `diff -r` confirms no AITaskAnalyzer-only library improvements lost
- [ ] 5 superseded `.omnifocusjs` bundles removed
- [ ] 2 orphaned scripts removed
- [ ] All stale references updated (grep returns zero matches for removed asset names)
- [ ] `references/omni_automation_guide.md` Attache bundle ID fixed
- [ ] Assets README rewritten with current plugin inventory
- [ ] SKILL.md updated to reflect cleanup is complete
- [ ] TreeExplorer.omnifocusjs and OFBundlePlugInTemplate.omnifocusjs confirmed retained and documented

### Quality Gates

- [ ] `bash scripts/validate-plugin.sh` passes on Attache.omnifocusjs
- [ ] `rg "AITaskAnalyzer|CompletedTasksSummary|Overview\.omnifocusjs|TodaysTasks|ofocore-test" plugins/omnifocus-manager/` returns only deliberate historical references (e.g., changelog entries)
- [ ] Skillsmith evaluation run on SKILL.md, score recorded in README.md

## Dependencies & Risks

- **Gate:** `diff -r` verification must pass before any bundle deletion (confirms no AITaskAnalyzer-only improvements lost)
- **Risk:** Stale references missed -- mitigated by recursive grep sweep + lesson from refinement doc
- **Coordination:** Issue #121 touches overlapping documentation. Not blocking, but avoid concurrent edits to the same files

## Sources & References

### Internal References

- Attache unified plan: `docs/plans/2026-03-08-feat-attache-omnifocus-unified-plugin-plan.md`
- Script consolidation plan: `docs/plans/2026-03-22-002-refactor-ofo-script-consolidation-gtd-coverage-plan.md`
- Refinement lessons (stale reference pattern): `docs/lessons/omnifocus-manager-refinement-2026-01-18.md`
- Assets README (stale): `plugins/omnifocus-manager/skills/omnifocus-manager/assets/README.md`
- GTD-coach skill: `plugins/omnifocus-manager/skills/gtd-coach/SKILL.md`
- SKILL.md supersession note: line ~190

### Related Work

- Issue #127: Remove superseded assets and orphaned scripts
- Issue #125: v9.3.0 -- native fields, Attache v1.2.0
- Issue #121: ofo script consolidation
