# Skill Research & Analysis Guide

This guide covers skillsmith's deep research capabilities for understanding skills and identifying improvement opportunities. Research integrates with skill-planner for systematic skill improvement workflows.

## Research Capabilities

The research system conducts a multi-phase analysis to understand what a skill does, how well it's implemented, and how it can be improved.

**Available Research Phases:**

1. **Understand Intent** - Extract skill purpose, description, and usage patterns
2. **Identify Domain & Complexity** - Classify domain and assess complexity level
3. **Research Best Practices** - Identify domain-specific patterns (future enhancement)
4. **Find Similar Skills** - Learn from examples in repository (future enhancement)
5. **Analyze Implementation** - Calculate quality metrics and identify issues
6. **Check Spec Compliance** - Validate against Agent Skills specification
7. **Synthesize Findings** - Consolidate into prioritized recommendations (future enhancement)

## Quality Metrics

skillsmith calculates objective quality metrics for any skill:

**Conciseness Score (0-100)**
- Evaluates line count vs guidelines (500 max, 300 recommended)
- Evaluates token count vs guidelines (2000 max)
- Higher score = more concise

**Complexity Score (0-100)**
- Analyzes heading structure and nesting depth
- Counts sections and code blocks
- Higher score = simpler, clearer structure

**Spec Compliance Score (0-100)**
- Validates required frontmatter fields (name, description)
- Checks recommended fields (metadata, compatibility, license)
- Identifies violations and warnings
- Higher score = better adherence to Agent Skills spec

**Progressive Disclosure Score (0-100)**
- Evaluates proper use of bundled resources (scripts, references, assets)
- Checks for appropriate content separation
- Higher score = better information architecture

**Overall Score (0-100)**
- Weighted average of all metrics
- Provides single quality indicator

## Running Research

To analyze a skill:

```bash
python3 scripts/research_skill.py <skill-path> [--output research.json]
```

**Example:**
```bash
# Analyze skillsmith itself
python3 scripts/research_skill.py skills/skillsmith

# Save findings to JSON
python3 scripts/research_skill.py skills/omnifocus-manager --output research.json
```

**Output includes:**
- Domain classification and complexity assessment
- Current quality metrics with visual score bars
- Strengths, weaknesses, and opportunities
- Spec compliance violations and warnings
- Full metrics data in JSON format (if --output specified)

## Calculate Metrics Only

To calculate quality metrics without full research:

```bash
python3 scripts/calculate_metrics.py <skill-path> [--format json|text]
```

**Example output:**
```
Quality Metrics: skillsmith
Basic Metrics:
  SKILL.md: 491 lines, ~5290 tokens
  Scripts: 9 files, 2696 lines
  References: 2 files, 783 lines

Quality Scores:
  Conciseness:     [██░░░░░░░░] 26/100
  Complexity:      [████████░░] 80/100
  Spec Compliance: [███████░░░] 75/100
  Progressive:     [██████████] 100/100
  Overall:         [██████░░░░] 68/100
```

## Integration with skill-planner

Research findings integrate seamlessly with skill-planner for improvement workflows:

**Workflow:**
1. User: "I want to improve skillsmith"
2. skill-planner invokes skillsmith research
3. Research analyzes skill and identifies issues
4. skill-planner creates improvement plan with research findings
5. Plan includes baseline metrics and specific opportunities
6. User refines and approves plan
7. Implementation guided by objective metrics

**Benefits:**
- Data-driven improvement decisions
- Objective baseline for measuring progress
- Specific, actionable recommendations
- Before/after metrics comparison

## Research Output Format

Research generates structured JSON with all findings:

```json
{
  "timestamp": "2025-12-21T...",
  "skill_path": "skills/skillsmith",
  "phase1_intent": {
    "name": "skillsmith",
    "description": "...",
    "purpose": "...",
    "triggers": [...]
  },
  "phase2_domain": {
    "domain": "meta",
    "complexity": "Meta",
    "special_considerations": [...]
  },
  "phase5_implementation": {
    "metrics": { ... },
    "strengths": [...],
    "weaknesses": [...],
    "opportunities": [...]
  },
  "phase6_compliance": {
    "score": 75,
    "violations": [],
    "warnings": [...]
  }
}
```

This structured format enables programmatic consumption by skill-planner and other tools.

## Best Practices for Research

**When to research:**
- Before planning skill improvements
- After significant changes to validate quality
- Periodically to track skill health
- When skill feels bloated or unclear

**Interpreting metrics:**
- Overall < 60: Significant improvements needed
- Overall 60-79: Good quality, room for improvement
- Overall 80+: Excellent quality

**Focus areas by score:**
- Low conciseness: Move content to references/, simplify language
- Low complexity: Reduce nesting, simplify structure
- Low spec compliance: Fix frontmatter, follow guidelines
- Low progressive disclosure: Better separation of concerns

**Acting on findings:**
- Use skill-planner for systematic improvements
- Address violations before warnings
- Prioritize opportunities with highest impact
- Measure before/after to validate improvements
