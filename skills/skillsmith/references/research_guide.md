# Skill Research & Analysis Guide

This guide covers skillsmith's comprehensive evaluation and research capabilities for assessing skills, verifying improvements, and identifying enhancement opportunities.

## Overview of Tools

skillsmith provides two complementary tools for skill analysis:

1. **evaluate_skill.py** - Comprehensive evaluation combining metrics, spec validation, comparison, and functionality testing (primary tool)
2. **research_skill.py** - Deep multi-phase research for understanding and planning improvements

## Comprehensive Evaluation (evaluate_skill.py)

The `evaluate_skill.py` script is the primary tool for skill assessment, combining all evaluation capabilities.

### Features

**Baseline Metrics**
- Calculates all quality scores (conciseness, complexity, spec compliance, progressive disclosure)
- Provides detailed breakdowns and visual score bars
- Identifies specific issues, violations, and warnings

**Comparison Mode**
- Compare improved skill against original version
- Calculate score deltas for all metrics
- Verify improvements and identify regressions
- Confirm overall quality increased

**Spec Validation**
- Complete AgentSkills specification compliance checking
- Validates naming conventions (lowercase, alphanumeric, hyphens only)
- Checks frontmatter completeness and format
- Verifies file references use relative paths
- Confirms progressive disclosure adherence

**Functionality Testing**
- Validates skill can be loaded properly
- Checks that scripts are executable with proper shebangs
- Verifies references are readable and appropriately sized
- Measures load time performance
- Reports overall functionality status

**Metadata Storage**
- Optionally stores evaluation metrics in SKILL.md frontmatter
- Tracks metrics over time
- Enables metric-based quality gates

### Usage

```bash
# Basic evaluation with metrics and spec validation
python3 scripts/evaluate_skill.py <skill-path>

# Compare improved vs original
python3 scripts/evaluate_skill.py <improved-path> --compare <original-path>

# With functionality validation
python3 scripts/evaluate_skill.py <skill-path> --validate-functionality

# Store metrics in SKILL.md
python3 scripts/evaluate_skill.py <skill-path> --store-metrics

# Full evaluation with all options
python3 scripts/evaluate_skill.py <skill-path> \
  --compare <original-path> \
  --validate-functionality \
  --store-metrics \
  --format json \
  --output evaluation.json
```

### Example Output

```
============================================================
Skill Evaluation: skillsmith
============================================================

Basic Metrics:
  SKILL.md: 321 lines, ~4039 tokens
  Scripts: 8 files, 3088 lines
  References: 3 files, 1133 lines
  Assets: 0 files

Quality Scores:
  Conciseness:     [█████████░░░░░░░░░░░] 47/100
  Complexity:      [██████████████████░░] 90/100
  Spec Compliance: [████████████████████] 100/100
  Progressive:     [████████████████████] 100/100
  Overall:         [████████████████░░░░] 84/100

AgentSkills Spec Compliance: ✓ PASS

============================================================
Comparison with Original
============================================================

Score Changes:
  conciseness: ↑ +15 points
  complexity: ↑ +10 points
  spec_compliance: → +0 points
  progressive_disclosure: ↑ +5 points
  overall: ↑ +12 points

✓ Improvements:
  - conciseness: +15 points
  - complexity: +10 points

Verified Better: ✓ YES

============================================================
Functionality Validation
============================================================

Loading: ✓ PASS (0.03ms)

Scripts (7):
  ✓ scripts/evaluate_skill.py
  ✓ scripts/research_skill.py
  ...

References (3):
  ✓ references/research_guide.md (5.23 KB)
  ✓ references/agentskills_specification.md (10.09 KB)
  ...

Overall Functional: ✓ YES
```

### When to Use evaluate_skill.py

- **Before and after improvements** - Verify enhancements actually improved quality
- **Pre-distribution validation** - Ensure skill meets AgentSkills specification
- **Quality assessment** - Get comprehensive view of skill health
- **Version comparison** - Compare different skill versions objectively
- **Functionality verification** - Ensure bundled resources work correctly
- **Quick checks** - Fast evaluation with comprehensive results

## Research Capabilities (research_skill.py)

The research system conducts a multi-phase analysis to understand what a skill does, how well it's implemented, and how it can be improved.

**Available Research Phases:**

1. **Understand Intent** - Extract skill purpose, description, and usage patterns
2. **Identify Domain & Complexity** - Classify domain and assess complexity level
3. **Research Best Practices** - Identify domain-specific patterns (future enhancement)
4. **Find Similar Skills** - Learn from examples in repository (future enhancement)
5. **Analyze Implementation** - Uses evaluate_skill.py to calculate quality metrics and identify issues
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

### Running Research

To conduct deep research analysis:

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

### When to Use research_skill.py

- **Planning major improvements** - Understanding skill architecture and opportunities
- **Unfamiliar skills** - Learning what a skill does and how it's structured
- **Refactoring decisions** - Identifying technical debt and improvement areas
- **Integration with skill-planner** - Providing research data for systematic improvement workflows

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
