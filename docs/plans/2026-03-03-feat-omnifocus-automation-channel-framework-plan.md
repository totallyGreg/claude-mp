---
title: "OmniFocus Automation Channel Framework"
type: feat
status: active
date: 2026-03-03
deepened: 2026-03-03
origin: docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md
---

# OmniFocus Automation Channel Framework

## Enhancement Summary

**Deepened on:** 2026-03-03
**Research agents used:** 10 (architecture-strategist, agent-native-reviewer, pattern-recognition-specialist, security-sentinel, code-simplicity-reviewer, kieran-typescript-reviewer, best-practices-researcher, + 3 web research agents)

### Key Improvements
1. **Added "Skill Purpose" framing** — this is about quickly providing OmniFocus value, not building validation infrastructure
2. **Renamed "Pillar 0" to "Channel Selection Layer"** — avoids conflating routing infrastructure with capability pillars
3. **Reordered Phase 1** — channel selection (capability improvement) comes first; anti-pattern checker (guardrail) comes second
4. **Added Phase 0: Fix existing anti-pattern instances** — 10+ `.addTag()` instances still exist in codebase
5. **Marked Phase 2 as "Optional — Deferred"** — implement when novel JXA generation becomes frequent enough that regex is insufficient
6. **Added agent capability parity table** — distinguishes what the agent can *execute* vs. *prepare* per channel
7. **Added community JXA type references** — [JXA-userland/JXA](https://github.com/JXA-userland/JXA) and [Tatsh/jxa-types](https://github.com/Tatsh/jxa-types) as starting points for Phase 2
8. **Simplified Phases 3-4** — distilled from formal phases to SKILL.md instructions

### New Risks Discovered
- **Autonomous SKILL.md modification** is the primary architectural risk — self-modifying instruction set with no semantic validation (architecture-strategist, security-sentinel)
- **`loadLibrary()` uses `eval()` with path construction** — needs path validation and library allowlist (security-sentinel)
- **`whose()[0]` may produce false positives** — JXA lazy evaluation means `[0]` returns `undefined` rather than throwing in some contexts (pattern-recognition)

---

## Skill Purpose

The omnifocus-manager skill exists to **quickly provide value for OmniFocus-related tasks** — querying tasks, running GTD diagnostics, managing projects, and generating plugins when needed. Channel selection and validation are guardrails that support this purpose, not the primary deliverable. Script generation and reuse matter, but only when existing commands don't cover the request.

## Overview

Add a **Channel Selection Layer** to the omnifocus-manager skill that routes requests to the right automation method, and add a lightweight anti-pattern checker to catch known JXA bugs when generating scripts.

The current system has a binary classification (query vs. plugin generation) with no intermediate routing and no JXA validation. This creates recurring bugs (issue #76: `addTag()`, `whose()[0]`, `clearTags()`) and limits the agent to Mac-only JXA when cross-platform channels exist.

This plan implements capabilities across two phases plus a prerequisite:
1. **Phase 0** — Fix existing anti-pattern bugs in the codebase (prerequisite)
2. **Phase 1** — Channel Selection Layer + anti-pattern checker + security hardening
3. **Phase 2 (Optional — Deferred)** — JXA type definitions for generation-time validation

Phase 2 should be implemented when novel JXA code generation becomes frequent enough that Phase 1's regex checker is insufficient. Until then, Phase 0+1 provide the primary value.

Phases 3-4 from the original brainstorm (compose-execute-promote loop, self-improvement loop) are distilled into lightweight SKILL.md instructions added during Phase 1, not separate implementation phases.

## Problem Statement / Motivation

Three structural problems drive this work:

**1. No channel routing.** Five automation channels exist (JXA, omnifocus:// URL, Omni Automation plugins, Apple Shortcuts, Omni-links), but the agent defaults to JXA for nearly everything. Cross-platform requests get Mac-only solutions. Obsidian embedding opportunities are missed.

**2. JXA has no validation.** Omni Automation plugins pass through a TypeScript + ESLint fortress. JXA scripts have zero build-time validation — bugs only surface at runtime. Issue #76 documented three recurring JXA bugs (`addTag()`, `whose()[0]`, `clearTags()`) that affected 9+ instances across 5 files. **These bugs still exist in the codebase** — the v6.0.1 fix was incomplete. (see brainstorm: Decision 3)

**3. No self-improvement mechanism.** When the agent discovers a novel composition or encounters a failure, that knowledge dies with the session. There's no mechanism to promote successful patterns into the system or prevent recurring mistakes. (see brainstorm: Decision 4, Decision 5)

## Proposed Solution

**Approach C: Iterative Pillar Enhancement** (see brainstorm: "Why This Approach"), simplified based on deepening research. The simplicity reviewer identified that Phases 3-4 were over-engineered for a ~2,700-line JXA codebase. The core value is in the channel matrix and anti-pattern checker (Phase 1) and type definitions (Phase 2). Compose-execute-promote and self-improvement behaviors are captured as SKILL.md instructions rather than formal implementation phases.

## Technical Approach

### Architecture

The Channel Selection Layer inserts before the existing Level 2 execution classification. It is a **routing layer**, not a capability pillar — the existing four-pillar numbering (Query, Perspectives, GTD Coaching, Plugins) is preserved.

```
User Request
  ↓
Level 1: Skill Routing (omnifocus-agent.md)
  ├─ Pure GTD? → gtd-coach only
  ├─ Pure OmniFocus? → omnifocus-manager
  └─ Hybrid? → Both skills
  ↓
NEW → Channel Selection Layer (SKILL.md routing table)
  ├─ iOS needed? → Omni-link / Plugin / URL / Shortcuts (priority order)
  └─ Mac only? → Existing JXA → Compose from primitives if needed
  ↓
Level 2: Execution Classification (existing, extended)
  ├─ "create plugin" keywords → Plugin generation workflow
  ├─ "build JXA script" → NEW: JXA composition workflow
  └─ All other → Query/execution with existing scripts
```

### Research Insights: Naming Convention

**Why "Channel Selection Layer" not "Pillar 0"** (architecture-strategist, pattern-recognition):
- Pillars are capability domains (things the system can do). Channel selection is routing infrastructure (how the system decides).
- "Pillar 0" in a 1-indexed system creates numbering confusion.
- The plan's own architecture diagram positions this as a routing step between levels, not a peer of Pillars 1-4.
- Recommended SKILL.md heading: "Channel Selection (Pre-Pillar Routing)"

### Research Insights: Agent Capability Parity by Channel

The agent operates from a macOS CLI. Not all channels have equal execution capability (agent-native-reviewer):

| Channel | Agent Can Execute | Agent Can Prepare | Key Limitation |
|---|---|---|---|
| **JXA** (osascript) | Full read + write | Full generation | Mac only |
| **omnifocus:// URL** | Fire-and-forget (`open`) | Full generation | Cannot read results; no feedback loop |
| **Omni Automation Plugin** | Cannot invoke installed plugins from CLI | Full generation + installation | User must trigger from OmniFocus UI |
| **Apple Shortcuts** | Run existing (`shortcuts run`) | Generate Omni Automation script code only | Cannot create/modify shortcuts programmatically |
| **Omni-links** | Generate link text | Full generation | Cannot verify Connected Folders setup |

**Implication for decision tree:** For iOS/cross-platform requests, the agent should frame its output as "preparation" (generating artifacts for user setup) not "execution." The decision tree should explicitly note which channels the agent can execute vs. prepare.

### Research Insights: Apple Shortcuts Integration

(from web research of omni-automation.com/shortcuts/)

**Two Shortcuts actions exist:**
1. **"Omni Automation Script" action** — embeds inline JavaScript, has full input/output data flow, runs on Mac + iOS + iPadOS. This is the primary integration point.
2. **"Omni Automation Plug-In" action** — runs installed plugin by name but has no input/output. Limited utility for data pipelines.

**Input types:** String, Number, Array (List), Dictionary, Date (as ISO 8601 string), Files, Primary Keys.
**Output:** Result of last expression, returned as String/Number/Array/Dictionary.

**Available triggers:** Focus mode, time of day, location, app open/close, Wi-Fi, Bluetooth, NFC, Siri, widget.

**Critical constraint:** Shortcuts cannot be created programmatically. The agent can generate the Omni Automation script code, but the user must create the shortcut manually in the Shortcuts app. Downloadable `.shortcut` template files are possible but require manual authoring.

**Bidirectional communication:** Plugins can call Shortcuts via `URL.fromString("shortcuts://run-shortcut?name=...").call(successFn, errorFn)` using x-callback-url.

### Research Insights: URL Scheme Security Model

(from web research of omni-automation.com/script-url/security.html)

**Two-gate security system for `omnijs-run` URLs:**
1. **Gate 1 (global toggle):** External scripts are **disabled by default**. User must enable in Automation Configuration.
2. **Gate 2 (per-script approval):** Each script/sending-app pairing requires one-time approval. User must scroll through entire script code before "Allow" button enables. Approval persists permanently until manually cleared.

**Security friction by URL type:**

| URL Type | Example | Security Friction |
|---|---|---|
| Navigation | `omnifocus:///task/<id>` | **None** |
| Perspective | `omnifocus:///perspective/Forecast` | **None** |
| Add/Create | `omnifocus:///add?name=Task&autosave=true` | **None** |
| Script (omnijs-run) | `omnifocus:///omnijs-run?script=...` | **HIGH** — two gates, disabled by default |
| Installed plugin | `.omnifocusjs` bundle | **None** — completely exempt |

**Key finding:** The `argument` parameter allows reusable script templates — the script body is approved once, and changing `&arg=` data does not trigger re-approval.

**Escalation path validated:** URL-encoded script → named Omni Automation plugin → named perspective. Each step genuinely reduces friction.

---

### Implementation Phases

#### Phase 0: Fix Existing Anti-Pattern Bugs (Prerequisite)

**Goal:** Fix the 10+ anti-pattern instances still in the codebase. The original plan incorrectly assumed these were fixed in v6.0.1.

**Research finding (simplicity-reviewer, pattern-recognition):** The codebase currently contains:
- **10 instances** of `.addTag()` across 5 files (manage_omnifocus.js, taskMutation.js, create_from_template.js, patterns.js, templateEngine.js)
- **2 instances** of `.clearTags()` across 2 files
- **5 instances** of unguarded `.whose()[0]` across 3 files

**Tasks:**

1. **Search and fix all `.addTag()` instances** — Replace with `app.add(tag, { to: task.tags })` pattern
2. **Search and fix all `.clearTags()` instances** — Replace with loop using `app.remove(tag, { from: task.tags })`
3. **Evaluate `.whose()[0]` instances** — Note: pattern-recognition found that JXA `whose()` returns a lazy specifier where `[0]` returns `undefined` on empty results (not throw). The existing `findOrCreateTag` function at `taskMutation.js:53` checks `if (tag)` after `whose()[0]`, which is actually safe. Evaluate each instance individually — only flag instances that do NOT check for null/undefined after indexing.
4. **Note on scope:** `.addTag()` in `scripts/libraries/omni/patterns.js` and `templateEngine.js` may be Omni Automation context (where `addTag()` IS valid), not JXA. Verify before changing.

**Success criteria:**
- [ ] Zero `.addTag()` instances in JXA files (`scripts/libraries/jxa/`, `scripts/manage_omnifocus.js`, `scripts/gtd-queries.js`)
- [ ] Zero `.clearTags()` instances in JXA files
- [ ] All `.whose()[0]` usages have null/undefined guards

**Estimated scope:** 5-7 files modified

---

#### Phase 1: Foundation — Channel Selection + Anti-Pattern Checker + Security Hardening

**Goal:** Help the skill route requests to the right channel quickly, and add a lightweight guardrail to catch known JXA bugs when generating scripts.

**Tasks:**

1. **Add Channel Selection matrix to SKILL.md** — The highest-value item. Insert into the Quick Decision Tree section using "Channel Selection (Pre-Pillar Routing)" as the heading. Include:
   - Agent capability parity table (execute vs. prepare per channel)
   - Decision tree with iOS/Mac branching
   - Explicit note that iOS routing is "preparation" not "execution"
   - Security friction table for URL types
   - Route only to channels that currently exist (JXA, Omni Automation plugins). Add extension points for URL scheme, Shortcuts, and Omni-links without pre-building routing logic.
   - **SKILL.md placement:** The existing plugin generation workflow occupies lines 1-95. Channel selection goes into the Quick Decision Tree section (line ~142). Add a brief (3-line) pointer in the first 20 lines.

2. **Add intermediate classification to Level 2** — Close the gap identified in the solutions doc:
   - "Build me a JXA script to…" → JXA composition workflow (not plugin generator)
   - "Automate this recurring task" → Channel selection consultation
   - "Improve an existing script" → Script modification workflow

3. **Update `references/omnifocus_url_scheme.md`** — Add Obsidian embedding patterns with security friction annotations:
   - Omni-links: `omni:///doc/...` (cross-device, zero friction)
   - Navigation links: `omnifocus:///task/<id>` (zero friction)
   - Perspective links: `omnifocus:///perspective/<name>` (zero friction, **preferred for queries**)
   - Action links: `omnifocus:///add?...` (zero friction)
   - Script links: `omnifocus:///omnijs-run?script=...` (**HIGH friction — disabled by default, two-gate approval**)
   - Escalation path: script URL → named plugin → named perspective (each reduces friction)
   - `argument` parameter for reusable script templates (one-time approval)

4. **Create `scripts/validate-jxa-patterns.js`** — A lightweight checker (~60 lines) that scans JXA source for known anti-patterns. Use a JSON-driven configuration for double duty as validation rules AND documentation source:

   **Anti-pattern configuration (`scripts/jxa-antipatterns.json`):**
   ```json
   {
     "antipatterns": [
       {
         "id": "no-addtag",
         "pattern": "\\.addTag\\(",
         "severity": "error",
         "message": "Use app.add(tag, { to: task.tags() }) instead of .addTag()",
         "reference": "references/jxa_guide.md#adding-tags"
       },
       {
         "id": "no-cleartags",
         "pattern": "\\.clearTags\\(",
         "severity": "error",
         "message": "clearTags() not supported in JXA. Iterate with app.remove().",
         "reference": "references/jxa_guide.md#removing-tags"
       },
       {
         "id": "no-document-default",
         "pattern": "Document\\.defaultDocument",
         "severity": "error",
         "message": "Use app.defaultDocument instead of Document.defaultDocument"
       }
     ],
     "blocked_always": [
       {
         "id": "no-eval",
         "pattern": "\\beval\\s*\\(",
         "severity": "error",
         "message": "eval() is blocked in generated JXA code"
       },
       {
         "id": "no-function-constructor",
         "pattern": "new\\s+Function\\s*\\(",
         "severity": "error",
         "message": "Function constructor is blocked in generated JXA code"
       },
       {
         "id": "no-nstask",
         "pattern": "\\$\\.NSTask|doShellScript",
         "severity": "error",
         "message": "System-level APIs (NSTask, doShellScript) are blocked in generated code"
       },
       {
         "id": "no-nsurlsession",
         "pattern": "\\$\\.NSURLSession",
         "severity": "error",
         "message": "Network access (NSURLSession) is blocked in generated code"
       }
     ]
   }
   ```

   **Note on `whose()[0]`:** Removed from the regex anti-pattern list because pattern-recognition found it produces false positives — JXA lazy evaluation returns `undefined` rather than throwing. This pattern is better caught by TypeScript type definitions (Phase 2) using `JXASpecifierList<T>` that doesn't extend `Array`.

   Input: JS file path or directory. Output: JSON array of violations with line numbers, pattern name, and fix suggestion.

   **Research insight (best-practices-researcher):** Use the JSON config as a triple-duty file — validation rules, auto-generated reference tables, and documentation source. The checker script is ~60 lines of Node.js.

5. **Add `loadLibrary()` path validation** (security-sentinel):
   ```javascript
   function loadLibrary(relativePath) {
       if (relativePath.includes('..') || relativePath.startsWith('/')) {
           throw new Error('Invalid library path: ' + relativePath);
       }
       // ... existing code ...
   }
   ```
   Add this guard to `manage_omnifocus.js`, `gtd-queries.js`, and any other scripts using `loadLibrary()`.

6. **Add ObjC bridge import constraint to SKILL.md** (security-sentinel):
   > "Generated JXA code MUST NOT use `$.NSTask`, `doShellScript`, `$.NSURLSession`, or import Objective-C frameworks beyond `Foundation` and `stdlib`."

7. **Add composition and self-improvement instructions to SKILL.md** — Distill Phases 3-4 into lightweight instructions:
   - "For requests not covered by existing commands, compose from `taskQuery.js` and `taskMutation.js` library functions."
   - "After fixing any JXA API bug, search all files in `scripts/` and `scripts/libraries/jxa/` for the same pattern and fix every instance."
   - "All SKILL.md routing changes require user approval."

8. **Integrate validate-jxa-patterns.js into test-queries.sh** — Run anti-pattern checker as part of existing smoke tests.

**Success criteria:**
- [ ] `validate-jxa-patterns.js` catches `.addTag()`, `.clearTags()`, `Document.defaultDocument`, `eval()`, `$.NSTask`, `doShellScript`
- [ ] Running against current codebase (after Phase 0 fixes) produces zero violations
- [ ] JSON anti-pattern config serves as both validation rules and documentation source
- [ ] `loadLibrary()` rejects paths containing `..` or absolute paths
- [ ] SKILL.md channel selection matrix includes agent capability parity table
- [ ] Level 2 classification handles "build JXA script" and "automate recurring task"
- [ ] `test-queries.sh` includes JXA anti-pattern validation
- [ ] URL scheme reference includes security friction annotations

**Estimated scope:** 5 files modified (SKILL.md, test-queries.sh, omnifocus_url_scheme.md, manage_omnifocus.js loadLibrary, gtd-queries.js loadLibrary), 2 files created (validate-jxa-patterns.js, jxa-antipatterns.json)

---

#### Phase 2: JXA Type Definitions (Optional — Deferred)

**Goal:** Close the JXA validation gap with TypeScript type definitions that catch the issue #76 class of bugs at generation time.

**When to implement:** When novel JXA code generation becomes frequent enough that Phase 1's regex anti-pattern checker is insufficient — i.e., bugs are appearing that aren't in the known anti-pattern list. For the current 80/15/5 execution-first model (80% existing scripts, 15% compose from libraries, 5% novel code), Phase 1 is likely sufficient.

**Why it's still worth planning:** The three issue #76 bugs each required multi-file fixes and debugging cycles. TypeScript catches these at write time with zero runtime cost. The ~150-line investment prevents a *class* of bugs, not individual bugs. When novel JXA generation increases, this becomes high-value.

### Research Insights: JXA Type Definition Strategy

(from kieran-typescript-reviewer, JXA type definitions research, best-practices-researcher)

**Limited community work exists.** Check these before writing from scratch:
- [JXA-userland/JXA](https://github.com/JXA-userland/JXA) — community JXA utilities and type examples
- [Tatsh/jxa-types](https://github.com/Tatsh/jxa-types) — JXA type definitions attempt

Neither provides complete OmniFocus-specific AppleScript bridge types, but they may offer a starting point for the generic JXA runtime (`Application()`, `ObjC.import`, `$` bridge). OmniFocus-specific interfaces (`JXATask`, `JXAProject`, etc.) will need to be written from scratch.

**Core TypeScript challenge:** JXA properties are both getters (method call: `task.name()`) and setters (assignment: `task.name = "new"`). TypeScript cannot model both on the same identifier. **Resolution:** Type properties as methods (`name(): string`) for reads. Accept false positives on writes; use a `jxaSet()` helper or `// @ts-ignore` for property assignment.

**File naming:** Use `jxa-omnifocus.d.ts` (not `jxa.d.ts`) — these types are OmniFocus-specific, not generic JXA.

**Minimum viable scope (7 interfaces, ~150 lines):**

1. **`Application()` function declaration** — `Application("OmniFocus")` returns `JXAApplication`
2. **`JXAApplication`** — `defaultDocument`, `add()`, `remove()`, `delete()`, `Task()`, `Tag()`, `Project()` factory methods. **Critically: NO `addTag`, `clearTags`, `removeTags` methods.** Their absence IS the bug prevention.
3. **`JXADocument`** — `flattenedTasks`, `flattenedProjects`, `flattenedTags`, `inboxTasks` as `JXASpecifierList<T>`
4. **`JXASpecifierList<T>`** — Custom type that does NOT extend `Array<T>`. Has `.length`, `[index]`, `.whose()`, `.byId()`, `.byName()`, `push()`. No `.map()`, `.filter()`, `.forEach()`. The `noUncheckedIndexedAccess` tsconfig flag makes `list[0]` return `T | undefined`, forcing null checks.
5. **`JXATask`** — Properties as methods: `id(): string`, `name(): string`, `completed(): boolean`, etc. **Deliberately omits `addTag()`, `clearTags()`, `removeTags()`** — if called, TypeScript errors immediately.
6. **`JXATag`** — `name(): string`, `tasks(): JXATask[]`, `status()`, etc.
7. **`JXAProject`** — `name(): string`, `tasks(): JXATask[]`, `status()`, etc.

Plus minimal ObjC bridge types (`$`, `ObjC.import`, `$.NSString`, `$.NSFileManager` — only classes actually used).

**Tasks:**

1. **Create `typescript/jxa-omnifocus.d.ts`** — 7 interfaces as described above. Must NOT share type names with existing `omnifocus.d.ts` (use `JXA` prefix).

2. **Create `scripts/validate-jxa-types.js`** — TypeScript Compiler API validation for JXA files:
   - Uses `ts.createProgram()` with `allowJs: true`, `checkJs: true`, `noEmit: true`
   - Validates against `jxa-omnifocus.d.ts`
   - Reports type errors with file, line, and fix suggestion
   - Filters to only JXA file errors (not .d.ts noise)

3. **Create `scripts/validate-jxa-mutations.js`** — Regex-based mutation detection (Layer 3) using curated list of JXA write operations:
   - `app.add(`, `app.remove(`, `app.delete(`
   - Property assignments (`.name =`, `.dueDate =`, `.flagged =`, `.completed =`)
   - `.markComplete(`, `.markIncomplete(`
   - Output: structured report of write operations for user confirmation

4. **Create `scripts/validate-jxa.sh`** — Pipeline wrapper that chains all three layers:
   ```bash
   validate-jxa.sh <file-or-directory> [--mutation]
   ```
   - Layer 1: Anti-pattern detection (validate-jxa-patterns.js) — FAIL = exit 1
   - Layer 2: TypeScript type-check (validate-jxa-types.js) — FAIL = exit 2
   - Layer 3: Mutation detection (validate-jxa-mutations.js, only with `--mutation`) — informational exit 3
   - Mirrors existing `validate-plugin.sh` UX (colored output, check marks, error counts)

**Success criteria:**
- [ ] `jxa-omnifocus.d.ts` covers all patterns used in `taskQuery.js` and `taskMutation.js`
- [ ] Type checking errors on `task.addTag(tag)` (method doesn't exist on `JXATask`)
- [ ] Type checking errors on `task.clearTags()` (method doesn't exist on `JXATask`)
- [ ] `JXASpecifierList<T>` does not extend `Array` — no `.map()`, `.filter()` available
- [ ] `validate-jxa-mutations.js` correctly identifies write operations
- [ ] `validate-jxa.sh` runs all layers sequentially with fail-fast behavior
- [ ] Existing JXA scripts pass all layers without false positives

**Estimated scope:** 4 files created (jxa-omnifocus.d.ts, validate-jxa-types.js, validate-jxa-mutations.js, validate-jxa.sh), 1 file modified (SKILL.md validation section)

**Dependency:** Phase 1 (validate-jxa-patterns.js and jxa-antipatterns.json must exist)

---

## Alternative Approaches Considered

(see brainstorm: "Why This Approach")

**Approach A (Conservative):** Add a routing table and anti-pattern lint to SKILL.md. Fast but channels stay siloed — no composition, no promotion, no self-improvement. Would not prevent issue #76 class of bugs.

**Approach B (Full Architectural):** Channel-agnostic abstraction with shared primitives. Correct but requires JXA type definitions (which don't exist) as a prerequisite for everything. High investment before any value ships.

**Approach C (Chosen: Iterative Pillar Enhancement, simplified):** Phase 0 fixes existing bugs. Phase 1 adds channel routing and anti-pattern checker. Phase 2 adds type definitions. Compose-execute-promote and self-improvement captured as SKILL.md instructions, not formal phases. Ships value at each step.

**Simplification rationale (code-simplicity-reviewer):** The original 4-phase plan created 4-5 new files of validation infrastructure for a codebase of ~2,700 lines across 4 JXA library files. The simplified plan creates 2 files in Phase 1 (checker + config) and 4 files in Phase 2 (types + validators + pipeline wrapper), with the most impactful work (fixing existing bugs) as a prerequisite phase.

## System-Wide Impact

### Interaction Graph

```
User request
  → omnifocus-agent.md (Level 1 routing)
    → SKILL.md Channel Selection (NEW: routing layer, NOT a pillar)
      → SKILL.md Level 2 (execution classification, MODIFIED: new intermediate categories)
        → scripts/manage_omnifocus.js (MODIFIED Phase 0: anti-pattern fixes)
        → scripts/gtd-queries.js (existing, unchanged)
        → scripts/validate-jxa.sh (NEW Phase 2: validation before novel code)
        → scripts/generate_plugin.js (existing, unchanged)
```

### Error Propagation

- **JXA validation failure (Layer 1):** Anti-pattern detected → agent auto-corrects the pattern and retries validation. If correction fails, abort and report to user.
- **JXA type check failure (Layer 2):** Type error → agent reports error with fix suggestion. Does not auto-correct (type errors may indicate deeper logic issues).
- **Mutation detection (Layer 3):** Informational — presents write operations for user review. Does not block execution. **Exception:** destructive operations (`app.delete()`) always require explicit confirmation regardless of script's promotion status.
- **Runtime error after validation:** Agent diagnoses, fixes across all files (grep for same pattern), updates `jxa-antipatterns.json` and `references/jxa_guide.md`.

### Research Insight: Security Considerations

(security-sentinel)

**loadLibrary() uses eval() with path construction (HIGH severity):**
- `loadLibrary()` reads a file from disk and `eval()`s it. Path constructed from CWD + relative path.
- All call sites currently use hardcoded paths (not user-supplied), so risk is mitigated.
- Phase 1 adds path validation to reject `..` traversal and absolute paths.
- Future: consider a library allowlist (only `taskQuery.js`, `taskMutation.js`, `argParser.js`, `dateUtils.js`).

**ObjC bridge scope (HIGH severity for generated code):**
- JXA scripts run with full user privileges via the ObjC bridge (`$.NSFileManager`, `$.NSTask`, etc.)
- Generated code must be constrained: only `Foundation` and `stdlib` ObjC imports permitted.
- Phase 1 adds `$.NSTask`, `doShellScript`, `$.NSURLSession` to the blocked-always anti-pattern list.

**SKILL.md self-modification (MEDIUM severity):**
- All SKILL.md modifications require user approval (no autonomous routing notes).
- This addresses the architecture-strategist's concern about unbounded state drift from individually-correct modifications that collectively produce unexpected routing behavior.

### State Lifecycle Risks

- **Promotion partial failure:** Execution succeeds but SKILL.md update fails skillsmith validation → execution result is still valid, user can retry SKILL.md update. No data loss risk.
- **Validation state tracking:** "Established" vs. "newly generated" is determined by presence in SKILL.md routing table (not a persisted state). No stale state risk.

### Research Insight: Mutation Confirmation Calibration

(agent-native-reviewer)

Destructive-action confirmation should be separated from validation-gate bypass:

| Mutation Type | Novel Code | Established Code |
|---|---|---|
| Read-only query | No gate | No gate |
| Property update (1-3 tasks) | Log only | No gate |
| Property update (4+ tasks) | Confirm with summary | Log only |
| Destructive (delete, complete) | Always confirm | Always confirm |
| Bulk destructive (5+ deletes) | Always confirm + show list | Always confirm + show list |

This aligns with existing `omnifocus-agent.md` bounded autonomy policy (lines 176-180): "Always ask user confirmation before running destructive operations."

### Integration Test Scenarios

1. **Channel routing for iOS request:** "Show overdue tasks on my iPhone" → should route to Omni Automation plugin preparation (generate + install instructions), NOT JXA
2. **Anti-pattern detection:** Generate JXA with `task.addTag(tag)` → validate-jxa-patterns.js catches it → agent auto-corrects to `app.add(tag, { to: task.tags })`
3. **Type error detection (Phase 2):** Generate JXA with `task.clearTags()` → TypeScript errors because `clearTags` is not on `JXATask` interface
4. **Security blocked pattern:** Generate JXA with `$.NSTask` → validate-jxa-patterns.js catches it as blocked-always
5. **loadLibrary path validation:** Call `loadLibrary('../../etc/passwd')` → rejected by path validation
6. **Verify-after-action for URL scheme:** Agent opens `omnifocus:///add?name=Task` → runs JXA query to confirm task exists

## Acceptance Criteria

### Functional Requirements

- [ ] Channel selection decision tree routes iOS requests to preparation workflows (not execution)
- [ ] Channel selection defaults to Mac/JXA for unspecified platform (per brainstorm)
- [ ] Agent capability parity table distinguishes execute vs. prepare per channel
- [ ] `validate-jxa-patterns.js` catches all anti-patterns in `jxa-antipatterns.json`
- [ ] `validate-jxa-patterns.js` catches blocked-always patterns (`eval`, `$.NSTask`, `doShellScript`)
- [ ] `jxa-omnifocus.d.ts` deliberately omits `addTag`, `clearTags`, `removeTags` from `JXATask`
- [ ] `JXASpecifierList<T>` does not extend `Array` — enforces `.length` check before indexing
- [ ] `loadLibrary()` rejects path traversal attempts
- [ ] All SKILL.md modifications require user approval (no autonomous changes)
- [ ] Destructive operations always require confirmation regardless of script promotion status

### Non-Functional Requirements

- [ ] No changes to existing `manage_omnifocus.js` or `gtd-queries.js` except Phase 0 anti-pattern fixes and `loadLibrary()` hardening
- [ ] Validation scripts run in < 5 seconds for any single JXA file
- [ ] All SKILL.md changes pass skillsmith evaluation

### Quality Gates

- [ ] Each phase has independent value — can ship Phase 0+1 without Phase 2
- [ ] `test-queries.sh` includes JXA anti-pattern validation after Phase 1
- [ ] Skillsmith evaluation run before each phase commit
- [ ] IMPROVEMENT_PLAN.md updated with version entry for each phase

## Success Metrics

- **Issue #76 class bugs:** Zero instances in codebase after Phase 0. Zero recurrence after Phase 2 (TypeScript catches them at generation time).
- **Channel routing accuracy:** Agent routes iOS requests to preparation workflows (manual verification with 5 test requests)
- **Security posture:** Zero `eval`/`$.NSTask`/`doShellScript` in generated code; `loadLibrary()` path validation in place

## Dependencies & Prerequisites

| Dependency | Phase | Status | Risk |
|---|---|---|---|
| Issue #76 anti-pattern instances exist | Phase 0 | **Requires fixing** | HIGH — 10+ `.addTag()` instances still in codebase |
| `test-queries.sh` exists | Phase 1 | Exists | Low |
| Community JXA type definitions | Phase 2 | Partial — [JXA-userland/JXA](https://github.com/JXA-userland/JXA), [Tatsh/jxa-types](https://github.com/Tatsh/jxa-types) exist as starting points | Medium — OmniFocus-specific interfaces (~150 lines) still needed |
| `omnifocus.d.ts` exists | Phase 2 | Exists | None — pattern to follow for jxa-omnifocus.d.ts |
| skillsmith available | All | Exists | None |

## Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| `.addTag()` instances in Omni Automation files are valid (not bugs) | Medium | Low | Verify each instance's context (JXA vs Omni Automation) before fixing. Files in `scripts/libraries/omni/` likely use valid Omni Automation API. |
| JXA type definitions have false positives on property writes | High | Low | Use `// @ts-ignore` for writes or a `jxaSet()` helper function. Accept this tradeoff — read-side catches are the priority. |
| `whose()[0]` regex produces false positives | High | Low | Removed from regex checker. Caught by `JXASpecifierList<T>` type in Phase 2 instead (no Array indexing methods). |
| Anti-pattern checker has false positives in comments/strings | Low | Low | Skip lines starting with `//` or `*`. Accept remaining edge cases. |
| SKILL.md grows too large with channel matrix | Medium | Medium | Channel details go in `references/`. SKILL.md gets decision tree only (< 20 lines). |
| `loadLibrary()` hardening breaks existing callers | Low | High | All existing callers use hardcoded relative paths without `..` — validation won't affect them. |

## Future Considerations

- **Voice Control** — Not researched. Reference: https://omni-automation.com/voice-control/index.html
- **pkm-manager coordination** — Out of scope (see brainstorm: Decision 6). Cross-plugin coordination deferred to a future "attache" coordinator agent.
- **Promotion to standalone scripts** — If compose-execute-promote patterns emerge organically, formalize the promotion path to standalone scripts in `scripts/` (not modification of `manage_omnifocus.js`).
- **Error classification** — If the same error types recur, consider adding a formal taxonomy to `omnifocus-agent.md`.

## Documentation Plan

| Phase | Documents Updated |
|---|---|
| Phase 0 | `manage_omnifocus.js`, `taskMutation.js`, other JXA files with anti-pattern fixes, IMPROVEMENT_PLAN.md |
| Phase 1 | SKILL.md (channel matrix, intermediate classification, composition/self-improvement instructions, security constraints), `references/omnifocus_url_scheme.md` (Obsidian patterns, security friction), IMPROVEMENT_PLAN.md |
| Phase 2 | SKILL.md (validation section), `references/jxa_guide.md` (anti-pattern table), IMPROVEMENT_PLAN.md |

## Open Questions (Resolved)

These were identified during spec flow analysis and have been resolved by deepening research:

1. **iOS context detection signals** — Only explicit keywords ("iPhone", "iPad", "iOS", "mobile") trigger iOS path. Contextual clues do not. **Resolved: confirmed as default.**
2. **Omni Automation Plugin vs. Apple Shortcuts tiebreaker** — Prefer Omni Automation plugin (agent can generate + install) unless user mentions automation triggers ("when I arrive", "at 9am", "during Focus mode") which require Shortcuts. **Resolved: Shortcuts cannot be created programmatically, so Omni Automation plugin is always preferred for agent-executable workflows.**
3. **Established script classification** — A script is "established" if it appears in SKILL.md's Quick Decision Tree section AND exists in `scripts/`. **Resolved: confirmed. Destructive-action confirmation survives promotion status.**
4. **URL security warning** — Prefer named perspective or installed plugin over `omnijs-run` URLs. If URL is required, note: "External scripts are disabled by default. User must enable in Automation Configuration, then approve each script on first use." **Resolved: two-gate system fully documented.**

## Sources & References

### Origin

- **Brainstorm document:** [docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md](docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md) — Key decisions: Approach C (iterative), five-channel decision tree, three-layer JXA validation, compose-execute-promote loop, expanded self-improvement loop
- **Solutions document:** [docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md](docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md) — Issue #76 root cause analysis, JXA validation gap documentation, self-improvement loop proposal

### Internal References

- SKILL.md: `plugins/omnifocus-manager/skills/omnifocus-manager/SKILL.md` — current routing logic, Quick Decision Tree
- omnifocus-agent.md: `plugins/omnifocus-manager/agents/omnifocus-agent.md` — Level 1 routing, intent classification, bounded autonomy policy
- validate-plugin.sh: `plugins/omnifocus-manager/skills/omnifocus-manager/scripts/validate-plugin.sh` — existing Omni Automation validation (pattern for validate-jxa.sh)
- omnifocus.d.ts: `plugins/omnifocus-manager/skills/omnifocus-manager/typescript/omnifocus.d.ts` — existing Omni Automation types (pattern for jxa-omnifocus.d.ts, must NOT share type names)
- jxa_guide.md: `plugins/omnifocus-manager/skills/omnifocus-manager/references/jxa_guide.md` — JXA patterns and anti-patterns
- omnifocus_url_scheme.md: `plugins/omnifocus-manager/skills/omnifocus-manager/references/omnifocus_url_scheme.md` — URL scheme reference

### External References (from deepening research)

- Apple Shortcuts integration: https://omni-automation.com/shortcuts/index.html — Omni Automation Script action, data flow, triggers
- URL script security model: https://omni-automation.com/script-url/security.html — Two-gate system, per-script approval, disabled by default
- JXA community types: https://github.com/JXA-userland/JXA — JXA utilities and type examples (Phase 2 starting point)
- JXA type definitions: https://github.com/Tatsh/jxa-types — Community JXA type definitions attempt (Phase 2 starting point)

### Institutional Learnings

- `docs/lessons/omnifocus-manager-refinement-2026-01-18.md` — Critical workflows in first 100 lines, reference placement, enforcement language
- `docs/lessons/skill-to-plugin-migration.md` — Three-stage plugin evolution
- `docs/lessons/plugin-integration-and-architecture.md` — Plugin integration patterns, skillsmith workflow

### Related Work

- Issue #76: JXA bugs that recurred — the concrete motivation for this work
- Issue #63: Two-track vision (Pillar 2: Perspectives) — parallel work, no dependency
