# Progressive Disclosure Discipline

This guide prevents common anti-patterns when creating or improving skills. Load this when editing SKILL.md or considering where to place new content.

## The Three-Question Test

Before adding content to SKILL.md, answer these questions in order:

### 1. Does something else already trigger this?
- **If validation enforces it** → Don't document it in SKILL.md
- **If a reference covers it** → Point to reference, don't duplicate
- **If multiple places mention it** → Consolidate to single source

**Example violation:** Adding "For Python scripts, load python_uv_guide.md" to Step 6 when validation already triggers this.

**Fix:** Trust the enforcement mechanism. Don't add redundant documentation.

### 2. Could this live in references/ instead?
- **If it's >3 paragraphs** → Probably belongs in references/
- **If it has examples, syntax, troubleshooting** → Definitely references/
- **If it's optional/contextual detail** → References/

**Example violation:** Adding Python PEP 723 syntax examples, version pinning rules, and troubleshooting directly in SKILL.md's Scripts section.

**Fix:** One-line mention + pointer: "Python scripts: MUST use PEP 723. See `references/python_uv_guide.md`"

### 3. Is this core to the skill's workflow?
- **If agents need it every time** → SKILL.md
- **If agents need it sometimes** → References/
- **If agents rarely need it** → Consider if it belongs at all

**Example violation:** Adding bash script best practices to a skill that primarily deals with Python.

**Fix:** Only document what's central to the skill's purpose.

## Anti-Patterns to Avoid

### ❌ Documentation Bloat
**Symptom:** SKILL.md growing beyond 500 lines with detailed how-to content

**Cause:** Inlining detailed guidance instead of pointing to references

**Fix:** Move detailed content to references/, keep SKILL.md as a workflow map

### ❌ Redundant Triggers
**Symptom:** Multiple places telling agent to load the same reference

**Cause:** Lack of trust in existing enforcement mechanisms

**Fix:** Document trigger once (preferably in validation/enforcement layer)

### ❌ Duplicate Information
**Symptom:** Same information in SKILL.md and references/

**Cause:** Fear that agents won't discover the reference

**Fix:** Single source of truth in references/, brief pointer in SKILL.md

### ❌ Premature Detail
**Symptom:** Adding comprehensive guidance before it's proven necessary

**Cause:** Trying to anticipate every edge case upfront

**Fix:** Start minimal, add detail only when actual usage reveals gaps

## The Progressive Disclosure Stack

Use this hierarchy for content placement:

```
SKILL.md (Level 1)
├─ What: Skill purpose and triggering conditions
├─ When: Usage scenarios
├─ How: High-level workflow steps
└─ Pointers: "See references/X for Y"

references/ (Level 2)
├─ Detailed how-to guides
├─ Syntax and examples
├─ Troubleshooting
├─ Best practices
└─ Edge cases

Validation/Enforcement (Level 3)
├─ Automatic checking
├─ Error messages with guidance
└─ Triggers for loading references
```

**Rule:** Information flows DOWN the stack, never up.
- Don't pull reference detail into SKILL.md
- Don't duplicate enforcement logic in documentation

## Content Placement Decision Tree

```
                    New content to add
                           ↓
                Is it enforced by validation?
                    ↙YES        NO↘
            Don't document    Is it >3 paragraphs?
            (trust validation)    ↙YES    NO↘
                          references/    Is it needed every time?
                                            ↙YES        NO↘
                                      SKILL.md    references/
```

## Real Examples from Skillsmith

### ✅ Good: Python Script Requirement
**SKILL.md:** "Python scripts: MUST use PEP 723. See `references/python_uv_guide.md`"

**Why good:**
- One line in SKILL.md
- Enforcement via validation
- Comprehensive details in reference
- No redundant triggers

### ❌ Bad: Inline Python Best Practices (initial attempt)
**Attempted:** Adding 40-line section with PEP 723 syntax, examples, version pinning rules in SKILL.md

**Why bad:**
- Bloats SKILL.md with optional detail
- Information better suited for references/
- Violates progressive disclosure

**Fix:** Moved to `references/python_uv_guide.md`, added one-line pointer

### ✅ Case Study: Skillsmith Content Consolidation (Phase 3)

**Situation:** Skill creation Steps 4-6 had 116 lines of detailed guidance in SKILL.md (editing, validation, iteration)

**Problem:**
- SKILL.md was 309 lines (exceeds 250 recommended)
- Detailed guidance bloated the main workflow
- Conciseness score: 64/100 (needed improvement)

**Solution:**
1. Created new reference: `references/skill_creation_detailed_guide.md` (220 lines)
2. Consolidated Steps 4-6 editing, validation, and iteration guidance
3. Replaced detailed sections with brief summaries + reference pointers
4. Maintained complete information (nothing lost, just reorganized)

**Results:**
- **SKILL.md:** 309 → 227 lines (-26%)
- **Tokens:** 4057 → 3093 (-24%)
- **Conciseness:** 64 → 81/100 (+26%)
- **Overall:** 89 → 93/100 (+4.5%)
- **Progressive Disclosure:** 100/100 (maintained)
- **Spec Compliance:** 100/100 (maintained)

**Key insight:** Progressive disclosure isn't about losing information—it's about putting it where agents can find it when needed, keeping the core workflow lean and discoverable.

## Maintenance Principle

**When improving skills:**
1. Start by reading existing content
2. Ask: "Where does this naturally fit in the stack?"
3. Prefer references/ over SKILL.md for new detail
4. Consolidate if information is scattered
5. Remove redundancy when found

**Remember:** Lean SKILL.md with smart references beats comprehensive inline documentation.
