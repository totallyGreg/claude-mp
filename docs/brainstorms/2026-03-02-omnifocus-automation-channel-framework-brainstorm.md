---
date: 2026-03-02
topic: omnifocus-automation-channel-framework
related_solutions:
  - docs/solutions/agent-design/omnifocus-manager-automation-decision-framework.md
related_brainstorms:
  - docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md
---

# OmniFocus Automation Channel Framework

## What We're Building

A **channel selection layer (Pillar 0)** for the omnifocus-manager skill that teaches the agent to choose the right automation method for every request, validate any JavaScript it generates, and promote successful novel compositions into the system for future reuse.

The current skill uses three automation channels (JXA, omnifocus:// URL scheme, Omni Automation plugins) but a fuller set of five exists — including Apple Shortcuts and Omni-links — with no routing logic between any of them. The agent defaults to JXA scripts for nearly everything. This brainstorm addresses the full lifecycle: classify → select channel → compose or execute → validate → promote pattern.

---

## Why This Approach (Approach C: Iterative Pillar Enhancement)

Three approaches were considered:

- **A (Conservative):** Add a routing table and anti-pattern lint to SKILL.md. Fast but channels stay siloed.
- **B (Architectural):** Full channel-agnostic abstraction with shared primitives. Correct but high investment, JXA type definitions don't exist yet.
- **C (Iterative, chosen):** Add Pillar 0 channel selection, build validation layers incrementally, expand self-improvement loop to capture both bugs and capability gaps. Follows existing pillar architecture, ships value at each step.

A critical behavioral requirement not captured in existing docs: when a request isn't yet scripted, the agent should **compose from existing primitives, execute with validation, then promote the successful pattern** — either as a CLI command, slash command, or SKILL.md entry. This is the self-improvement loop applied to capability gaps, not just bug fixes.

---

## Key Decisions

### 1. Automation Channel Selection (Pillar 0)

Add an explicit pre-classification step before the existing Level 2 execution classification. Five automation channels are available, each with a distinct trade-off profile:

| Dimension | JXA (osascript) | omnifocus:// URL | Omni Automation Plugin | Apple Shortcuts | Omni-links |
|---|---|---|---|---|---|
| Device reach | Mac only | Mac + iOS | Mac + iOS | Mac + iOS + iPadOS | Mac + iOS (Connected Folders) |
| Operation type | Read + Write + Query | Create/Navigate/Script | Read + Write + UI-integrated | Read + Write + Triggers | Navigation/Reference only |
| Embeddability | Not embeddable | Embeddable in Obsidian | Not embeddable | Shareable links | Embeddable in Obsidian |
| Security gate | None (osascript) | ⚠️ Requires user approval on first run; may be disabled by default | None (installed) | System trust | None |
| Validation | Three-layer (see below) | Omni Automation fortress (for omnijs-run scripts) | Fortress (TypeScript + ESLint) | Fortress (same runtime) | N/A |

**Security note:** URL-embedded Omni Automation scripts (`omnifocus:///omnijs-run?script=...`) require explicit user approval per script/app pairing and may be disabled by default. Installed plugins bypass this entirely. This means Obsidian query links have friction that installed plugins do not.

**Decision tree** (iOS branch uses priority order — first match wins):
```
Does this need to work on iPhone/iPad?          (default: NO — assume Mac unless stated)
  └─ YES — check in priority order:
      1. Reference/navigation only (open and show a task or document)?
             → Omni-link (omni:///...) or omnifocus:///perspective/<name>
      2. Workflow trigger needed (Focus mode, location, time, Siri)?
             → Apple Shortcuts (Omni Automation Script action)
      3. Needs to be an embeddable link in Obsidian?
             → omnifocus:// URL scheme (⚠️ user approval required for script URLs)
               Escalation: URL-encoded script → named plugin → named perspective
      4. Otherwise:
             → Omni Automation plugin (installed, no security friction, cross-device)
  └─ NO (Mac only)
      └─ Is there an existing JXA script for this? → Run it
      └─ Otherwise → Compose from JXA library primitives; write net-new code if no
                     primitive covers the need → validate → promote
```

### 2. URL and Omni-link Types for Obsidian Embedding

Four link types can be embedded in Obsidian notes:

- **Omni-links:** `omni:///doc/...` — cross-device document/item references using Connected Folders. Lowest friction; no security approval needed.
- **Navigation links:** `omnifocus:///task/<id>` or `omnifocus:///perspective/<name>` — open and show a specific item
- **Query links:** `omnifocus:///omnijs-run?script=...` — runs an Omni Automation script inline. **⚠️ Requires user approval on first run per app pairing; may be disabled by default.** Prefer named perspective links or installed plugin calls for recurring queries.
- **Action links:** `omnifocus:///add?...` — create operations; no approval needed for add-only actions

Complexity escalation path for query links: `URL-encoded script → named Omni Automation plugin action → named perspective`. Each step reduces URL length and eliminates the security approval requirement.

Each type should have a documented template in `references/omnifocus_url_scheme.md` with Obsidian markdown embedding patterns.

### 3. Three-Layer JXA Validation Pipeline

All JXA scripts (generated or modified) must pass validation in sequence before running against live data:

1. **Anti-pattern ESLint** — catches known bad patterns (addTag(), clearTags(), whose()[0] indexing) via custom ESLint rules or a dedicated `validate-jxa-patterns.js` checker
2. **JXA type definitions** — TypeScript definitions for the AppleScript bridge API (does not exist yet; create as `typescript/jxa.d.ts` following the model of `typescript/omnifocus.d.ts`)
3. **Parse-and-report gate** — applies to **newly generated mutation code only**, not to established scripts or installed plugins. Static analysis identifies all write operations in the new code and presents them for confirmation before the first execution. Once a script passes validation and is promoted (added to CLI or installed as a plugin), subsequent invocations run without re-validation.

Read-only operations: require layers 1-2. New mutation code: requires all three, once at generation time.

### 4. Compose-Execute-Promote Loop (Core Behavior)

When a request isn't covered by existing scripts:

```
Novel request detected
  ↓
1. COMPOSE — assemble from existing library primitives per channel:
   - JXA: taskQuery.js / taskMutation.js functions
   - URL: omnifocus:// URL templates in references/omnifocus_url_scheme.md
   - Omni Automation: generate_plugin.js templates
   If no primitives cover the need, write net-new code for the appropriate channel
  ↓
2. VALIDATE — run three-layer pipeline appropriate to channel
  ↓
3. EXECUTE — run against live data with user confirmation for mutations
  ↓
4. PROMOTE — if successful, formalize the pattern:
   a. Add as a named CLI command in manage_omnifocus.js or gtd-queries.js
   b. Define as a slash command (if frequently reused)
   c. Add to SKILL.md routing table
   d. Document in references/ if it exposes new API patterns
  ↓
5. CAPTURE — invoke ce:compound to document the composition pattern
```

The promotion step is what distinguishes this from ad-hoc scripting — every successful novel composition leaves the system better than it found it.

### 5. Self-Improvement Loop (Expanded)

The self-improvement loop from the solutions doc is expanded to cover four trigger conditions:

| Trigger | Action |
|---|---|
| **Script bug** (runtime JXA/Omni error) | Diagnose → fix across all files → update references/jxa_guide.md anti-patterns → invoke code-reviewer |
| **Routing failure** (wrong channel selected, misclassified intent) | Log → adjust Pillar 0 decision tree → update SKILL.md routing table |
| **Stale GTD patterns** (inbox growing, projects without next actions, skipped reviews) | Surface in weekly review → suggest corrective actions → log to references/troubleshooting.md |
| **Novel composition** (new pattern discovered) | Promote → document → invoke ce:compound |

The loop always ends with documentation — either in `references/` for operational patterns or `docs/solutions/` for complex multi-step problems.

### 6. Relationship to pkm-manager

Out of scope for this work. Obsidian integration here is limited to URL scheme links embedded in Obsidian markdown. Cross-plugin coordination (e.g., creating an OmniFocus task from an Obsidian note) is deferred to a future "attaché" coordinator agent.

---

## Resolved Questions

- **JXA TypeScript definitions scope:** Comprehensive — cover the full AppleScript bridge API. Check existing community work first (e.g., [Tatsh/jxa-types](https://github.com/Tatsh/jxa-types)) before writing from scratch. Do not reinvent what exists.

- **Promotion mechanism:** Use `ce:compound` to document the novel pattern. The agent should have promotion criteria: one-time use → SKILL.md routing note; repeatedly needed → CLI command in `manage_omnifocus.js`; workflow-level → slash command. All SKILL.md changes must be validated with skillsmith before committing.

- **omnijs-run URL limit:** Treat URL complexity as a known promotion path: `URL-encoded script → named Omni Automation plugin action → named OmniFocus perspective`. Complex queries escalate through this progression. A named perspective is the end state — it can be called via URL, used in a plugin, and embedded in Obsidian notes.

- **Parse-and-report for new mutation code:** Applies at generation time only — not as a runtime gate on established scripts or plugins. When the agent generates new mutation code, static analysis identifies all write operations and presents them for confirmation before the first run. Once the code is validated and promoted, it runs without re-validation.

---

## Channels to Research in Planning

Three channels identified during brainstorming that need deeper investigation before the decision tree can be considered complete:

- **Apple Shortcuts** — runs Omni Automation scripts cross-device (Mac + iOS + iPadOS), supports Personal Automation triggers (Focus modes, location, time), bi-directional data flow. Reference: https://omni-automation.com/shortcuts/index.html
- **Voice Control** — Omni Automation integration for hands-free GTD input. Reference: https://omni-automation.com/voice-control/index.html
- **URL script security model** — full specification of which URL actions require approval and under what conditions. Reference: https://omni-automation.com/script-url/security.html

---

## Next Steps

→ `/ce:plan` for implementation details, starting with Pillar 0 channel selection matrix and the anti-pattern ESLint rules (the two lowest-risk, highest-value items)
