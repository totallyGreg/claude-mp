---
title: "OmniFocus Manager: Automation Decision Framework, JXA Validation Gaps, and Self-Improvement Loops"
date: 2026-03-02
category: agent-design
tags:
  - omnifocus-manager
  - agent-routing
  - jxa-validation
  - skillsmith
  - reference-placement
  - self-improvement
severity: high
component: plugins/omnifocus-manager
symptom: |
  Long debugging cycles (issue #76) when JXA bugs recur; reference files created in wrong
  directories during debugging; no mechanism to prevent repeating the same JXA API mistakes
root_cause: |
  1. JXA scripts have no build-time validation (only Omni Automation plugins do)
  2. Reference files created during debugging cycles land in code directories (scripts/libraries/jxa/)
     instead of the references/ directory — Skillsmith does not enforce placement
  3. No self-evaluation loop exists to trigger compound-engineering skills after failures
status: documented
issue: https://github.com/totallyGreg/claude-mp/issues/76
related_lessons:
  - docs/lessons/omnifocus-manager-refinement-2026-01-18.md
related_brainstorms:
  - docs/brainstorms/2026-02-28-omnifocus-manager-query-pipeline-brainstorm.md
  - docs/brainstorms/2026-03-02-omnifocus-automation-channel-framework-brainstorm.md
---

# OmniFocus Manager: Automation Decision Framework, JXA Validation Gaps, and Self-Improvement Loops

## Summary

This document examines three interconnected design questions for the omnifocus-manager plugin:
1. **How the agent decides what automation to build** — the routing and classification system
2. **How JavaScript is built and validated** — the asymmetric validation pipeline and its gaps
3. **How the agent can evaluate itself after failures** — the missing self-improvement loop

Issue #76 is the concrete example: a cycle of debugging JXA bugs (`addTag()`, `whose()[0]`, `clearTags()`) where a `JXA_API_REFERENCE.md` was created in `scripts/libraries/jxa/` (wrong location) instead of `references/`. Skillsmith should have caught this placement violation.

---

## 1. How the Agent Decides What Automation to Build

### Two-Level Classification

The omnifocus-agent uses a two-level intent classification system:

**Level 1: Skill Routing (omnifocus-agent.md)**

```
User Request
├─ Pure GTD methodology? ("What makes a good next action?")
│  └─ Route: gtd-coach skill only (no execution)
├─ Pure OmniFocus execution? ("Show overdue tasks")
│  └─ Route: omnifocus-manager skill only
└─ Hybrid? ("Help me do my weekly review")
   └─ Route: Both skills — methodology first, execution supporting
```

**Level 2: Execution Classification (SKILL.md STEP 1)**

Within omnifocus-manager, a binary keyword scan determines the execution path:

```
Keywords "create plugin" / "make plugin" / "generate plugin"
  └─ Classification: PLUGIN GENERATION → mandatory 5-step workflow

All other requests
  └─ Classification: QUERY/EXECUTION → run existing scripts directly
```

### The 80/15/5 Execution-First Rule

The skill explicitly prioritizes existing code over generation:

| Priority | Frequency | Action |
|----------|-----------|--------|
| Execute existing scripts | 80% | `manage_omnifocus.js`, `gtd-queries.js` |
| Compose from libraries | 15% | `taskMetrics.js` + `exportUtils.js` + patterns |
| Generate novel code | 5% | Full 5-step TypeScript → validate → ESLint workflow |

### What Signals New Code Generation?

The agent generates new plugin code only when:
1. Request contains explicit "create/build/generate plugin" keywords
2. No existing script covers the use case after checking `scripts/libraries/omni/`
3. Format is selected based on requirements (`solitary`, `solitary-fm`, `bundle`, `solitary-library`)

**What blocks generation:**
- Hallucinated APIs (TypeScript validator catches these)
- Missing TypeScript validation pass
- User did not explicitly request a plugin (queries use existing scripts)

### Routing Matrix

| Request Type | Script/Method | Trigger |
|---|---|---|
| Query tasks | `manage_omnifocus.js today/overdue/flagged` | "show", "what", "list" |
| GTD diagnostics | `gtd-queries.js --action system-health` | "stalled", "waiting", "health" |
| Mutation/creation | `manage_omnifocus.js create/update` | "create", "complete", "clear" |
| Quick capture | `omnifocus:///add?name=...` URL | Cross-platform, no JXA needed |
| Novel plugin | `generate_plugin.js --format <X>` | "create plugin" keywords |
| GTD coaching | gtd-coach skill (no scripts) | Methodology, principles |

### Current Gap: No Intermediate Classification

The binary classification (query vs. plugin generation) has no middle ground for:
- "Build me a JXA script to…" — should route to JXA script composition, not plugin generator
- "Automate this recurring task" — unclear whether to use cron + JXA or an Omni Automation plugin
- "Can I improve an existing script?" — no classification path for script modification

---

## 2. How JavaScript Is Built and Validated

### Two Environments, One Asymmetric Pipeline

The plugin ecosystem runs in two fundamentally different JavaScript environments:

| Environment | Runtime | API Syntax | Validated? |
|---|---|---|---|
| **Omni Automation** | Inside OmniFocus (Mac + iOS) | Properties: `task.name`, `flattenedTasks` | ✅ YES — TypeScript + ESLint |
| **JXA** | `osascript -l JavaScript` (Mac only) | Methods: `task.name()`, `flattenedTasks()` | ❌ NO — runtime only |

### Omni Automation: Fortress Validation

Plugin code goes through a rigorous build-time pipeline:

```
TypeScript template
    ↓
TypeScript Compiler API validates against omnifocus.d.ts
    ↓ (fails? STOP — zero tolerance)
Emit JavaScript
    ↓
ESLint validates with OmniFocus globals defined
    ↓ (fails? STOP — zero tolerance)
Plugin ready for installation
```

This catches 95%+ of errors before any code runs in OmniFocus:
- Hallucinated APIs (e.g., `Document.defaultDocument`, `Progress`)
- Property/method confusion (`task.name()` vs `task.name`)
- Constructor errors (`new LanguageModel.Schema()` vs `LanguageModel.Schema.fromJSON()`)

### JXA: Validation Blind Spot

The JXA libraries (`taskQuery.js`, `taskMutation.js`) have **no equivalent validation**:
- No TypeScript definitions for the AppleScript bridge API
- No ESLint rules for JXA-specific patterns
- No mandatory pre-generation checklist (that exists in `code_generation_validation.md` is Omni Automation only)
- Bugs only surface at runtime inside OmniFocus

This asymmetry is the structural cause of issue #76.

### Issue #76: The JXA Bugs That Recurred

Three JXA bugs were fixed in v6.0.1 (`bc83991`):

**Bug 1: `task.addTag(tag)` — "Can't convert types" error**
- ❌ Wrong: `task.addTag(tag)` (Omni Automation pattern)
- ✅ Correct: `app.add(tag, { to: task.tags })` (AppleScript bridge pattern)
- Affected 5 instances in `manage_omnifocus.js`, 2 in `taskMutation.js`, others in templates

**Bug 2: `whose()[0]` throws on empty results**
- ❌ Wrong: `doc.flattenedTags.whose({ name: "x" })[0]` (assumes exists)
- ✅ Correct: Check `.length > 0` before indexing
- This was the root cause of `create --tags "NewTag" --create-tags` failures — the tag lookup threw before creation code could run

**Bug 3: `task.clearTags()` — not supported**
- ❌ Wrong: `task.clearTags()`
- ✅ Correct: Iterate and `app.remove(tag, { from: task.tags })`

**Why these bugs recurred:** No validation system enforced the correct JXA AppleScript bridge patterns. The `code_generation_validation.md` checklist covers Omni Automation only.

### The Reference Placement Problem

During the issue #76 debugging cycle, a `JXA_API_REFERENCE.md` was created inside `scripts/libraries/jxa/` instead of `references/`. This is a structural violation with two consequences:

1. **Discoverability**: Developers looking in `references/` for JXA API docs won't find it
2. **Validation pipeline isolation**: API references in `scripts/` are not connected to any validation tooling — they become orphaned documentation

The correct structure is:
```
skills/omnifocus-manager/
├── references/
│   ├── jxa_guide.md            ← JXA API docs live HERE
│   └── jxa_api_reference.md    ← Any new JXA reference goes HERE
└── scripts/
    └── libraries/
        └── jxa/
            ├── taskQuery.js    ← Code lives here
            └── taskMutation.js ← Code lives here
```

SKILL.md must mention any reference file added to `references/`, following the Skillsmith spec:
> ❌ Bad: Reference files exist in `references/` but aren't mentioned in SKILL.md
> ✅ Good: Each reference file mentioned contextually where relevant in SKILL.md

---

## 3. How the Agent Can Evaluate Itself After Failures

### What's Currently Missing

The plugin currently has no self-improvement mechanism. After a failure:
- User must manually identify the bug
- User manually reports via GitHub issue
- Agent generates a fix but doesn't analyze why it failed
- Same mistake can recur in other files (issue #76 affected 9+ instances across multiple files)

### The Proposed Self-Improvement Loop

When a JXA script or plugin generation fails, the agent should trigger a recovery sequence:

```
Runtime Failure Detected
    ↓
1. DIAGNOSE — analyze error message against known patterns
   (e.g., "Can't convert types" → known JXA addTag() bug)
    ↓
2. CLASSIFY failure type:
   ├─ Known JXA pattern? → Apply fix from references/jxa_guide.md
   ├─ Omni Automation API error? → Re-run TypeScript validation pipeline
   └─ Novel error? → Invoke compound-engineering:ce:compound to document
    ↓
3. FIX across all affected files (not just the one that failed)
    ↓
4. DOCUMENT — add pattern to references/troubleshooting.md
    ↓
5. PREVENT — update jxa_guide.md with explicit anti-pattern entry
```

### Where compound-engineering Skills Fit

After a failure loop like issue #76, these skills should be invoked:

| Skill | When to Invoke | Outcome |
|---|---|---|
| `ce:compound` | After any multi-file debugging cycle | Structured `docs/solutions/` document capturing problem + fix |
| `code-reviewer` | After JXA bug fix is applied | Verify fix was applied consistently across all files |
| `pattern-recognition-specialist` | After recurring bug category found | Identify all instances of the anti-pattern |
| `skillsmith` | When reference file is in wrong location | Enforce placement and SKILL.md linkage |

### What Skillsmith Should Enforce

Skillsmith currently validates structure but does not enforce **reference file placement** during debugging/creation sessions. The missing check:

```
When a new .md file is created anywhere in a skill directory:
  IF path contains scripts/ or assets/ AND content looks like API documentation
    WARN: "Reference documentation should go in references/, not scripts/"
    PROMPT: "Add to references/ and link from SKILL.md?"
```

This would have caught the `scripts/libraries/jxa/JXA_API_REFERENCE.md` placement during issue #76.

Additionally, when a reference file IS added to `references/`, Skillsmith should verify:
- [ ] File appears in SKILL.md's "Reference Documentation" section
- [ ] File is mentioned contextually where relevant (e.g., "See `references/jxa_api_reference.md` for JXA patterns")

### Immediate Improvements for omnifocus-manager

**Short-term (no new tooling required):**
1. Move any JXA API reference content into `references/jxa_guide.md` (or a new `references/jxa_api_reference.md`)
2. Add explicit anti-pattern table to `references/jxa_guide.md`:

   | JXA Pattern | Omni Automation Lookalike | Why It Breaks |
   |---|---|---|
   | `app.add(tag, { to: task.tags })` | `task.addTag(tag)` | AppleScript bridge, not native JS |
   | `whose({...}).length > 0` before `[0]` | Direct array indexing | `whose()[0]` throws on empty |
   | `app.remove(tag, { from: task.tags })` | `task.clearTags()` | clearTags() not supported in JXA |

3. Add a `SKILL.md` compliance check to `scripts/test-queries.sh`:
   ```bash
   # Verify all references/ files are mentioned in SKILL.md
   for ref in references/*.md; do
     basename=$(basename "$ref")
     grep -q "$basename" SKILL.md || echo "WARNING: $basename not mentioned in SKILL.md"
   done
   ```

**Medium-term (Skillsmith integration):**
1. Add JXA validation to the generation pipeline — at minimum, an ESLint pass with JXA-specific globals
2. Create `references/jxa_api_reference.md` consolidating correct JXA patterns for `app.add()`, `app.remove()`, `app.delete()`, `whose()` safety, constructor patterns
3. Extend `code_generation_validation.md` with a JXA-specific section

**Long-term (agent autonomy):**
1. After any JXA failure, auto-invoke `ce:compound` to document the issue
2. Post-fix, auto-invoke `code-reviewer` to check fix consistency across all files
3. Add `pattern-recognition-specialist` to the standard debugging workflow for issues tagged `plugin:omnifocus-manager`

---

## Lessons for Future Development

### Lesson 1: Reference files go in `references/`, code goes in `scripts/`

The Skillsmith specification is clear:
- `references/` — documentation loaded into context as needed
- `scripts/` — executable code

During a debugging cycle, if you create a markdown file documenting API patterns, it is a **reference**, not code. It goes in `references/` and must be linked from SKILL.md.

### Lesson 2: JXA and Omni Automation are different APIs — document them separately

Both APIs run JavaScript in the OmniFocus ecosystem but the syntax is different:
- JXA: AppleScript bridge — properties are method calls, collections are functions
- Omni Automation: Native JavaScript — properties are direct, collections are properties

This distinction must be explicitly visible in SKILL.md routing, not just buried in reference files.

### Lesson 3: Validation gaps predict where bugs will cluster

The issue #76 bugs (addTag, whose, clearTags) all lived in JXA code — the unvalidated half of the system. When you see a validation asymmetry, bugs will accumulate in the unvalidated zone. Add validation or add anti-patterns to references.

### Lesson 4: Multi-file bugs require multi-file fixes

The `addTag()` bug appeared in 9 instances across 5 files. A fix in one file without searching all files leaves the system in a half-fixed state. After any API correction, run:
```bash
grep -r "addTag\|clearTags\|whose(" plugins/omnifocus-manager/skills/omnifocus-manager/scripts/ \
  --include="*.js" -l
```
Then verify each result uses the correct JXA pattern.

### Lesson 5: The compound-engineering loop is the self-improvement mechanism

The compound-engineering skills (`ce:compound`, `code-reviewer`, `pattern-recognition-specialist`) are the existing self-improvement infrastructure. The gap is not that these tools don't exist — it's that they aren't invoked automatically after debugging cycles. The trigger condition should be: any issue that requires fixes across more than 2 files.
