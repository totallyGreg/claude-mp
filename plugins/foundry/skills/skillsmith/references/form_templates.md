# Form Templates

This file contains structured templates for common skill development workflows.

## Use-Case Definition Form

**Complete this before running `/ss-init`.** Define 2-3 concrete use cases to validate the skill is worth building and to generate an accurate description.

For each use case, fill out:

```
Use Case: [short name]
Trigger: User says "[exact phrase that should invoke this skill]"
Steps: 1. [what Claude does first]
       2. [what Claude does next]
       3. [what Claude does last]
Result: [concrete output or outcome the user receives]
```

**Questions to answer before scaffolding:**

- **Problem without the skill:** What does Claude do (or fail to do) today when this trigger fires?
- **Required tools/MCP:** Which tools does this skill need (Bash, Read, Write, specific MCP servers)?
- **Success criteria:** How will you know the skill is working correctly?

**Example (well-formed):**

```
Use Case: Review a pull request
Trigger: User says "review this PR" or "review PR #123"
Steps: 1. Fetch PR diff and changed files
       2. Analyze for bugs, style issues, and test coverage
       3. Post structured review comment grouped by severity
Result: A formatted review comment posted to the PR

Problem without skill: Claude reads the PR but writes an unstructured wall of text
Required tools: Bash (gh pr diff), Read (source files)
Success criteria: Review comment has severity grouping and actionable suggestions
```

Once you have 2-3 use cases filled out, proceed to the Skill Proposal Form below, then run `/ss-init`.

---

## Skill Proposal Form

Use this template when proposing a new skill for review:

**Skill Name:** [lowercase-with-hyphens]
**Domain:** [e.g., development, productivity, documentation]
**Description:** [1-2 sentence summary]
**Target Users:** [who will use this skill]
**Key Capabilities:**
- Capability 1
- Capability 2
- Capability 3

**Required References:** [domain knowledge files needed]
**Required Scripts:** [automation scripts needed]
**Required Assets:** [templates, files, etc.]

---

## Improvement Request Form

Use this template when requesting skill improvements:

**Skill:** [skill-name]
**Improvement Type:** [feature | bug-fix | optimization | documentation]
**Current Behavior:** [describe current state]
**Desired Behavior:** [describe desired state]
**Priority:** [low | medium | high]
**Complexity:** [quick-update | complex]

**Affected Files:**
- File 1
- File 2

**Reference Updates Needed:** [yes/no - which references?]
**Script Changes Needed:** [yes/no - which scripts?]

---

## Research Analysis Template

Use this structure for documenting skill research findings:

**Skill Analyzed:** [skill-name]
**Analysis Date:** [YYYY-MM-DD]
**Analyzer:** [name]

**Metrics:**
- Conciseness: [score/100]
- Complexity: [score/100]
- Spec Compliance: [score/100]
- Progressive Disclosure: [score/100]
- Overall: [score/100]

**Strengths:**
- Strength 1
- Strength 2

**Weaknesses:**
- Weakness 1
- Weakness 2

**Recommendations:**
1. Recommendation 1
2. Recommendation 2

**References Review:**
- Total references: [count]
- Well documented: [yes/no]
- Consolidation needed: [yes/no]
