# Improvement Plan: omnifocus-manager - Mandatory Pre-Code-Generation Validation

**Status:** implemented
**Created:** 2025-12-31T15:27:26Z
**Implemented:** 2025-12-31T16:00:00Z
**Branch:** plan/omnifocus-manager-improvement-20251231
**Version:** v2

---

## Goal

Prevent API misuse errors (like PlugIn.Library constructor) by:
1. Fixing incorrect PlugIn.Library pattern in existing documentation
2. Enforcing mandatory validation workflows BEFORE any plugin code generation

**Root Cause Analysis:**
1. **Documentation inconsistency**: plugin_development_guide.md shows TWO different patterns (correct at line 72, incorrect at line 680)
2. **No enforcement**: Validation patterns exist but no mandatory workflow gates
3. **Passive language**: SKILL.md says "follow these requirements" instead of "MUST complete validation"

---

## Current State

### Understanding

**Purpose:** Query and manage OmniFocus tasks through database queries and JavaScript for Automation (JXA)
**Domain:** Task management automation, OmniFocus plugin development
**Complexity:** High - requires knowledge of multiple APIs (Omni Automation, JXA, AppleScript)

### Metrics (Baseline)

```
SKILL.md: 496 lines
Tokens: ~4485
References: 20 files, 13676 lines
Scripts: 6
Nesting depth: 3

Conciseness:     [█████░░░░░] 25/100
Complexity:      [████████░░] 83/100
Spec Compliance: [█████████░] 90/100
Progressive:     [██████████] 100/100
Overall:         [███████░░░] 74/100
```

### Critical Issues Found

**Issue 1: Inconsistent PlugIn.Library Patterns in plugin_development_guide.md**

✅ **Correct pattern (line 72)** - From official template:
```javascript
var lib = new PlugIn.Library(new Version("1.1"));
```

❌ **Incorrect pattern (line 680)** - Contradicts API spec:
```javascript
const myHelpers = new PlugIn.Library(function() {
    const lib = this;
```

**Why This Causes Errors:**
- According to OmniFocus-API.md:1769, constructor signature is `new PlugIn.Library(version: Version)`
- Passing a function instead of Version causes: "Attempted to invoke function... with invalid instance"
- This is exactly the error we encountered with foundationModelsUtils.js

**Issue 2: No Mandatory Validation Workflow**
- SKILL.md says "follow these critical requirements" (passive)
- No enforcement gates before code generation
- code_generation_validation.md has correct patterns but isn't required reading

###Metrics Analysis

**Conciseness (25/100) - LOW**
- SKILL.md at size limit: 496/500 lines
- Cannot add mandatory workflow without removing content
- Solution: Move detailed examples to existing references/, add concise workflow

**Spec Compliance (90/100) - GOOD**
- Only missing: license field in frontmatter
- Easy fix: add `license: MIT` to SKILL.md

---

## Proposed Changes

### Change 1: Fix Incorrect PlugIn.Library Pattern in plugin_development_guide.md

**Type:** FIX (Critical)
**What:** Replace incorrect pattern at line 680 with correct pattern matching official template.

**Why:** Current pattern contradicts OmniFocus API specification and causes constructor errors.

**Impact:**
- Eliminates source of confusion
- Aligns with official template (line 72)
- No metric impact (fixing existing content)

**Implementation:**
```diff
- (() => {
-     const myHelpers = new PlugIn.Library(function() {
-         const lib = this;
-
-         lib.formatDate = function(date) {
-             return date.toLocaleDateString();
-         };
-
-         lib.calculateDaysUntil = function(date) {
-             const now = new Date();
-             const diff = date - now;
-             return Math.ceil(diff / (1000 * 60 * 60 * 24));
-         };
-
-         return lib;
-     });
-
-     return myHelpers;
- })();

+ (() => {
+     var lib = new PlugIn.Library(new Version("1.0"));
+
+     lib.formatDate = function(date) {
+         return date.toLocaleDateString();
+     };
+
+     lib.calculateDaysUntil = function(date) {
+         const now = new Date();
+         const diff = date - now;
+         return Math.ceil(diff / (1000 * 60 * 60 * 24));
+     };
+
+     return lib;
+ })();
```

### Change 2: Add Prominent Anti-Pattern Warning

**Type:** ENHANCE
**What:** Add explicit ❌ WRONG section immediately after the correct pattern in plugin_development_guide.md.

**Why:** Make it impossible to miss the incorrect pattern. Show what NOT to do.

**Impact:** +15 lines to plugin_development_guide.md

**Implementation:**
Add after line 76 (correct pattern example):
```markdown
❌ **WRONG - Common Mistakes:**

```javascript
// Constructor takes Version, NOT a function
new PlugIn.Library(function() { ... })  // ERROR! Type mismatch
new PlugIn.Library(async function() { ... })  // ERROR! Type mismatch

// Use 'var lib', not 'const myLib' or other names
const foundationModelsUtils = new PlugIn.Library(...)  // WRONG!
var lib = new PlugIn.Library(...)  // CORRECT!
```

**Why these patterns fail:**
- PlugIn.Library constructor signature: `new PlugIn.Library(version: Version)` (OmniFocus-API.md:1769)
- Passing a function instead of Version object causes "invalid instance" error
- Always use `var lib` pattern for consistency with official templates
```

### Change 3: Add Pre-Code-Generation Checklist to code_generation_validation.md

**Type:** ENHANCE
**What:** Add mandatory checklist at TOP of code_generation_validation.md.

**Why:** Creates explicit validation gate that must be completed before any code generation.

**Impact:** +30 lines to code_generation_validation.md (acceptable - reference file)

**Implementation:**
Add at top of file (after purpose/updated metadata):
```markdown
---

## ⚠️ MANDATORY Pre-Generation Checklist

**BEFORE writing ANY plugin code, complete this checklist:**

### 1. Read Validation Documentation ✅
- [ ] Read this entire document (code_generation_validation.md)
- [ ] Read references/plugin_development_guide.md sections relevant to your code
- [ ] Understand official template patterns (OFBundlePlugInTemplate)

### 2. Verify Every API ✅
- [ ] List all classes to instantiate (PlugIn.Action, PlugIn.Library, Version, Alert, Form, etc.)
- [ ] Check constructor signatures in references/OmniFocus-API.md for EACH class
- [ ] Verify all properties/methods in references/api_quick_reference.md
- [ ] Confirm NOT using hallucinated APIs (Document.defaultDocument, Progress, etc.)

### 3. Verify PlugIn.Library Pattern (If Applicable) ✅
- [ ] Review official template: assets/OFBundlePlugInTemplate.omnifocusjs/Resources/
- [ ] Confirm pattern: `var lib = new PlugIn.Library(new Version("1.0"));`
- [ ] Confirm NOT using function constructor: `new PlugIn.Library(function() { ... })`
- [ ] Review existing libraries: taskMetrics.js, exportUtils.js

### 4. Verify Environment Globals ✅
- [ ] Using global variables: flattenedTasks, folders, projects, tags, inbox
- [ ] NOT using Document.defaultDocument (use globals instead)
- [ ] NOT using Node.js or browser APIs

### 5. Verify LanguageModel Schema (If Applicable) ✅
- [ ] Using LanguageModel.Schema.fromJSON() factory (NOT constructor)
- [ ] Using OmniFocus schema format (NOT JSON Schema format)
- [ ] Reviewed schema patterns in code_generation_validation.md Rule 5

**Only proceed with code generation after ALL checkboxes completed.**

---
```

### Change 4: Add Mandatory Validation Workflow to SKILL.md

**Type:** RESTRUCTURE
**What:** Replace passive "Generating plugin code" section (lines 92-124) with mandatory validation workflow.

**Why:** Enforce pre-generation validation. Change from "follow these" to "MUST complete".

**Impact:** -35 lines from SKILL.md (move examples to references/), +20 lines for workflow = NET -15 lines

**Implementation:**

**Remove from SKILL.md (lines 92-124):**
- Detailed API examples
- Property vs method examples
- Common pitfalls list

**Replace with (lines 92-110):**
```markdown
## Plugin Code Generation (MANDATORY WORKFLOW)

**⚠️ CRITICAL:** Never generate plugin code without completing this workflow.

### BEFORE Code Generation

**Step 1: Complete Pre-Generation Checklist (REQUIRED)**
1. Open `references/code_generation_validation.md`
2. Read the "MANDATORY Pre-Generation Checklist" at top
3. Complete ALL checkbox items before proceeding

**Step 2: Verify Constructor Patterns (REQUIRED)**
1. For PlugIn.Library: Review `assets/OFBundlePlugInTemplate.omnifocusjs/Resources/` patterns
2. Confirm: `var lib = new PlugIn.Library(new Version("1.0"));`
3. For other classes: Check constructor signature in `references/OmniFocus-API.md`

**Step 3: Verify APIs (REQUIRED)**
1. Check EVERY API in `references/api_quick_reference.md`
2. Verify properties (no `()`) vs methods (with `()`)
3. Use global variables (flattenedTasks, folders) NOT Document.defaultDocument

### AFTER Code Generation

**Step 4: Validate Generated Code**
1. Run `eslint_d` on all .js files
2. Verify no hallucinated APIs
3. Confirm correct constructor patterns

**Complete documentation:**
- Validation rules: `references/code_generation_validation.md`
- Plugin patterns: `references/plugin_development_guide.md`
- API reference: `references/OmniFocus-API.md`, `references/api_quick_reference.md`
```

### Change 5: Add License Field to SKILL.md

**Type:** FIX
**What:** Add `license: MIT` to SKILL.md frontmatter.

**Why:** Improves spec compliance from 90/100 to 100/100.

**Impact:** +1 line, spec compliance +10 points

**Implementation:**
Add after metadata section in frontmatter:
```yaml
license: MIT
```

### Change 6: Add LSP and Linter Validation to Post-Generation Workflow

**Type:** ENHANCE
**What:** Mandate eslint_d AND vtsls (JavaScript LSP) validation for ALL generated plugin code.

**Why:**
- ESLint catches syntax errors, undefined globals, hallucinated APIs
- vtsls (JavaScript LSP) provides additional type checking and semantic validation
- Two-layer validation significantly reduces runtime failures

**Impact:** +15 lines to SKILL.md mandatory workflow section

**Implementation:**

Update "AFTER Code Generation" section in SKILL.md Change 4 to:
```markdown
### AFTER Code Generation (MANDATORY VALIDATION)

**Step 4: Validate with ESLint and LSP**
1. Run `eslint_d` on ALL generated .js files (syntax, style, undefined globals)
2. Use vtsls LSP for semantic validation (type checking, API correctness)
3. Fix ALL errors before proceeding (zero tolerance)
4. Verify no hallucinated APIs
5. Confirm correct constructor patterns

**ESLint validation (REQUIRED):**
```bash
# From omnifocus-manager directory
eslint_d assets/YourPlugin.omnifocusjs/Resources/*.js

# Must return zero errors before code is acceptable
```

**LSP validation (REQUIRED):**
- vtsls provides JavaScript language server validation
- Catches type mismatches, incorrect API usage, semantic errors
- Integrates with editor (VSCode, Neovim, etc.) for real-time validation
- Run validation before finalizing code

**What ESLint catches:**
- Undefined globals (hallucinated APIs like `Document.defaultDocument`, `Progress`)
- Syntax errors (`.bind(this)` on arrow functions)
- Style violations
- Unreachable code

**What vtsls LSP catches:**
- Type mismatches (passing function when Version expected)
- Incorrect constructor arguments
- Property/method confusion (calling property as method)
- Semantic errors not caught by ESLint
```

**Also update code_generation_validation.md checklist:**

Add to bottom of "MANDATORY Pre-Generation Checklist":
```markdown
### 6. Post-Generation Validation (REQUIRED) ✅
- [ ] Run `eslint_d` on all generated .js files
- [ ] Fix ALL eslint errors (zero errors required)
- [ ] Use vtsls LSP for semantic validation
- [ ] Fix ALL LSP errors and warnings
- [ ] Verify no warnings about undefined globals
- [ ] Confirm code matches validation patterns
- [ ] Test code actually runs in OmniFocus without errors
```

---

## Expected Outcome

### Metrics (After)

```
SKILL.md: 480 lines (-16, -3.2%)
Tokens: ~4200 (-285, -6.4%)
References: 20 files (no change), 13750 lines (+74)
Scripts: 6 (no change)
Nesting depth: 3 (no change)

Conciseness:     [██████░░░░] 30/100 (+5) ✓ improvement
Complexity:      [████████░░] 83/100 (no change)
Spec Compliance: [██████████] 100/100 (+10) ✓ improvement
Progressive:     [██████████] 100/100 (no change)
Overall:         [████████░░] 80/100 (+6) ✓ improvement
```

### Success Criteria

- [ ] Incorrect PlugIn.Library pattern removed from plugin_development_guide.md:680
- [ ] Correct pattern with anti-pattern warning added to plugin_development_guide.md
- [ ] Pre-generation checklist added to code_generation_validation.md (top of file)
- [ ] Mandatory validation workflow added to SKILL.md with imperative language
- [ ] License field added to SKILL.md frontmatter
- [ ] ESLint and vtsls LSP validation mandated in post-generation workflow
- [ ] eslint_d and vtsls validation examples added to SKILL.md and code_generation_validation.md
- [ ] SKILL.md reduced by 15+ lines (remove examples, add concise workflow)
- [ ] All code examples validate with eslint_d AND vtsls (zero errors)
- [ ] Conciseness score improves to 30+ (currently 25)
- [ ] Spec compliance score reaches 100 (currently 90)
- [ ] Overall score improves to 80+ (currently 74)

### Expected Benefits

- **Eliminates confusion**: No more conflicting patterns in documentation
- **Prevents hallucination**: Mandatory checklist forces validation, ESLint catches undefined globals
- **Two-layer validation**: ESLint (syntax/style) + vtsls LSP (semantics/types) catches more errors
- **Catches errors early**: Validation before code reaches runtime
- **Clearer workflow**: Step-by-step gates with "MUST" language
- **Better metrics**: Improved conciseness and spec compliance
- **Maintainability**: Correct patterns throughout documentation
- **Quality assurance**: Zero-error policy enforced by tooling

---

## Revision History

### v2 (2025-12-31)
- Removed redundant new reference file (use existing plugin_development_guide.md)
- Added fix for incorrect pattern at plugin_development_guide.md:680
- Added anti-pattern warnings to prevent future errors
- Streamlined SKILL.md by removing detailed examples (keep in references/)

### v1 (2025-12-31)
- Initial plan created from evaluation findings
- Proposed new reference file (later removed in v2 - redundant)

---

*This plan was generated using skillsmith evaluation and error analysis.*
*Root cause: Documentation inconsistency + no validation enforcement.*
*Solution: Fix incorrect patterns + add mandatory workflow gates.*
