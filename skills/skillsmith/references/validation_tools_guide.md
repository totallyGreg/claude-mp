# Skill Validation & Analysis Tools Guide

This reference provides comprehensive documentation for skillsmith's validation and analysis tools. Load this file when you need detailed guidance on using `evaluate_skill.py` or `research_skill.py`.

---

## Overview

Skillsmith provides two primary tools for skill validation and analysis:

1. **evaluate_skill.py** - Unified validation and evaluation tool
2. **research_skill.py** - Deep multi-phase research analysis

These tools help assess skills, verify improvements, and identify enhancement opportunities throughout the skill development lifecycle.

---

## evaluate_skill.py

Unified skill validation and evaluation tool with two modes: **quick validation** (fast, structure-only) and **comprehensive evaluation** (metrics, spec validation, comparison, functionality testing).

### Features

#### Quick Validation Mode
Fast structural validation for pre-commit hooks and CI/CD pipelines:
- YAML frontmatter format checking
- Required fields validation (name, description)
- Character limits (name ≤64 chars, description ≤1024 chars)
- Naming conventions (lowercase-with-hyphens)
- Version field presence (in metadata or frontmatter)
- IMPROVEMENT_PLAN.md completeness checking (optional)

#### Comprehensive Evaluation Mode
Full quality assessment with detailed metrics:
- **Baseline metrics** - Calculates quality scores:
  - Conciseness (token/word count relative to recommendations)
  - Complexity (structural depth, nesting levels)
  - Spec compliance (AgentSkills specification adherence)
  - Progressive disclosure (metadata vs body vs resources distribution)
- **Comparison mode** - Compare improved skill against original
- **Spec validation** - Complete AgentSkills specification compliance
- **Functionality testing** - Validates resources are accessible:
  - SKILL.md can be loaded
  - Scripts are executable
  - References are readable
  - Assets exist and are accessible
- **Metadata storage** - Optionally store metrics in SKILL.md frontmatter

### Usage

#### Basic Usage

```bash
# Quick validation (fast, structure-only)
python3 scripts/evaluate_skill.py <skill-path> --quick

# Quick validation with IMPROVEMENT_PLAN check
python3 scripts/evaluate_skill.py <skill-path> --quick --check-improvement-plan

# Basic evaluation with metrics and spec validation
python3 scripts/evaluate_skill.py <skill-path>
```

#### Advanced Usage

```bash
# Compare improved vs original skill
python3 scripts/evaluate_skill.py <skill-path> --compare <original-path>

# With functionality validation
python3 scripts/evaluate_skill.py <skill-path> --validate-functionality

# Store metrics in SKILL.md metadata
python3 scripts/evaluate_skill.py <skill-path> --store-metrics

# Full evaluation with all options and JSON output
python3 scripts/evaluate_skill.py <skill-path> \
  --compare <original-path> \
  --validate-functionality \
  --format json

# Save results to file
python3 scripts/evaluate_skill.py <skill-path> --output results.json
```

### When to Use Quick Mode

Quick mode (`--quick`) is optimized for speed and minimal output. Use it for:

- **Pre-commit hooks** - Fast validation before commits
- **CI/CD validation gates** - Automated pipeline checks
- **Quick sanity checks** - During development iterations
- **IMPROVEMENT_PLAN validation** - Before release (with `--check-improvement-plan`)
- **Structural validation only** - When metrics aren't needed

**Performance:** Quick mode completes in <1 second for most skills.

### When to Use Comprehensive Mode

Comprehensive mode (default) provides detailed analysis. Use it for:

- **Before and after improvements** - Verify enhancements with metrics
- **AgentSkills spec compliance** - Full specification validation
- **Quality assessment** - Comprehensive quality metrics
- **Version comparison** - Compare different skill versions
- **Functionality testing** - Verify resource accessibility
- **Detailed analysis** - When you need full metrics and insights

**Performance:** Comprehensive mode typically completes in 2-5 seconds.

### Output Formats

#### Text Format (Default)

Human-readable output with sections:
```
=== Skill Evaluation ===
Name: skillsmith
Version: 2.2.0
Status: ✅ PASS

Metrics:
- Conciseness: 8.5/10
- Complexity: 7.2/10
- Spec Compliance: 9.1/10
...
```

#### JSON Format

Machine-readable output for scripting:
```bash
python3 scripts/evaluate_skill.py <skill-path> --format json
```

```json
{
  "skill_name": "skillsmith",
  "version": "2.2.0",
  "status": "pass",
  "metrics": {
    "conciseness": 8.5,
    "complexity": 7.2,
    "spec_compliance": 9.1
  },
  ...
}
```

### Exit Codes

- **0** - All checks passed
- **1** - Validation failed (errors found)
- **2** - Critical error (file not found, malformed YAML, etc.)

### Common Use Cases

#### Use Case 1: Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run quick validation before allowing commit
python3 scripts/evaluate_skill.py skills/my-skill/ --quick

if [ $? -ne 0 ]; then
  echo "❌ Skill validation failed. Fix errors before committing."
  exit 1
fi
```

#### Use Case 2: Verify Improvement

```bash
# Before making changes
python3 scripts/evaluate_skill.py skills/my-skill/ --output before.json

# ... make improvements ...

# After making changes, compare
python3 scripts/evaluate_skill.py skills/my-skill/ \
  --compare before.json \
  --output after.json

# Review improvements
diff before.json after.json
```

#### Use Case 3: CI/CD Pipeline

```yaml
# .github/workflows/validate-skills.yml
- name: Validate Skills
  run: |
    python3 scripts/evaluate_skill.py skills/*/ --quick --format json
```

---

## research_skill.py

Deep multi-phase research analysis tool for understanding skills and identifying improvement opportunities.

### Features

#### 7-Phase Research Workflow

1. **Intent Analysis** - Understand skill purpose and goals
2. **Domain Classification** - Identify domain and complexity level
3. **Best Practices** - Domain-specific best practices and patterns
4. **Similar Skills** - Find related skills for comparison
5. **Implementation Analysis** - Examine current implementation
6. **Compliance Check** - Verify AgentSkills specification adherence
7. **Recommendations** - Suggest improvements and enhancements

#### Analysis Capabilities

- **Strengths identification** - What the skill does well
- **Weaknesses identification** - Areas needing improvement
- **Opportunities identification** - Enhancement possibilities
- **Domain classification** - Categorize skill domain
- **Complexity assessment** - Evaluate implementation complexity
- **Integration points** - WORKFLOW.md pattern compatibility

### Usage

#### Basic Usage

```bash
# Full research analysis
python3 scripts/research_skill.py <skill-path>

# Save research to file
python3 scripts/research_skill.py <skill-path> --output research.json
```

#### Advanced Options

```bash
# Focus on specific phases
python3 scripts/research_skill.py <skill-path> --phases intent,domain,recommendations

# Generate comparison report
python3 scripts/research_skill.py <skill-path> --compare <other-skill-path>

# Output as markdown
python3 scripts/research_skill.py <skill-path> --format markdown --output RESEARCH.md
```

### When to Use

Research analysis is valuable when:

- **Planning major improvements** - Before significant changes
- **Understanding unfamiliar skills** - Learning existing skills
- **Identifying refactoring opportunities** - Finding enhancement areas
- **Preparing for GitHub Issues** - Pre-planning research for WORKFLOW.md pattern
- **Domain analysis** - Understanding skill categorization
- **Competitive analysis** - Comparing with similar skills

### Output Format

#### Phase-by-Phase Report

```markdown
# Skill Research Analysis: skillsmith

## Phase 1: Intent Analysis
Purpose: Skill creation and management tool
Goals:
- Simplify skill creation workflow
- Provide validation and evaluation
...

## Phase 2: Domain Classification
Domain: Development Tools
Complexity: High
...

## Phase 7: Recommendations
- Reduce SKILL.md to <500 lines
- Extract routing logic to references
...
```

### Integration with WORKFLOW.md Pattern

research_skill.py is used during complex improvements following the WORKFLOW.md pattern:

```
User: "Improve the skillsmith skill"
→ Skillsmith identifies as complex improvement
→ Skillsmith runs research_skill.py for baseline analysis
→ Research findings inform GitHub Issue creation
→ Issue includes baseline metrics and opportunities
→ IMPROVEMENT_PLAN.md updated with research context
→ Implementation proceeds with data-driven approach
```

---

## Comparison: evaluate_skill.py vs research_skill.py

| Aspect | evaluate_skill.py | research_skill.py |
|--------|-------------------|-------------------|
| **Purpose** | Validate and measure | Understand and analyze |
| **Speed** | Fast (1-5 seconds) | Slower (10-30 seconds) |
| **Output** | Metrics and pass/fail | Insights and recommendations |
| **When** | After changes, validation | Before changes, planning |
| **Scope** | Structural and quantitative | Contextual and qualitative |
| **Integration** | CI/CD, pre-commit hooks | WORKFLOW.md pattern (GitHub Issues) |

---

## Validation Workflows

### Workflow 1: Quick Development Iteration

```bash
# 1. Make changes to skill
vim skills/my-skill/SKILL.md

# 2. Quick validation
python3 scripts/evaluate_skill.py skills/my-skill/ --quick

# 3. Fix any errors
# ... fix errors ...

# 4. Commit
git add skills/my-skill/
git commit -m "Update skill documentation"
```

### Workflow 2: Major Improvement with Metrics

```bash
# 1. Baseline evaluation
python3 scripts/evaluate_skill.py skills/my-skill/ --output baseline.json

# 2. Research for improvement ideas
python3 scripts/research_skill.py skills/my-skill/ --output research.md

# 3. Make improvements based on research
# ... implement changes ...

# 4. Compare with baseline
python3 scripts/evaluate_skill.py skills/my-skill/ \
  --compare baseline.json \
  --validate-functionality

# 5. Verify improvements
# Check that metrics improved
```

### Workflow 3: Pre-release Validation

```bash
# 1. Comprehensive evaluation
python3 scripts/evaluate_skill.py skills/my-skill/ \
  --validate-functionality \
  --check-improvement-plan \
  --store-metrics

# 2. Verify IMPROVEMENT_PLAN completeness
# Ensure version history is updated

# 3. Final quality check
python3 scripts/evaluate_skill.py skills/my-skill/ --quick

# 4. Ready for release
# All validations passed
```

---

## Metrics Interpretation

### Conciseness Score

**Range:** 0-10 (higher is better)

- **9-10**: Excellent - Lean, focused content
- **7-8**: Good - Reasonable length
- **5-6**: Fair - Could be more concise
- **<5**: Poor - Too verbose or redundant

**Factors:**
- SKILL.md line count vs 500 line recommendation
- Token count vs 5000 token recommendation
- Metadata size vs 100 token recommendation

### Complexity Score

**Range:** 0-10 (lower is better for simplicity)

- **0-3**: Simple - Easy to understand
- **4-6**: Moderate - Balanced complexity
- **7-8**: Complex - Dense content
- **9-10**: Very Complex - May need simplification

**Factors:**
- Nesting depth in SKILL.md structure
- Number of bundled resources
- Cross-references between files

### Spec Compliance Score

**Range:** 0-10 (higher is better)

- **9-10**: Excellent - Fully compliant
- **7-8**: Good - Minor issues
- **5-6**: Fair - Some violations
- **<5**: Poor - Major spec violations

**Factors:**
- Required fields present
- Naming conventions followed
- File organization compliance
- Progressive disclosure adherence

---

## Troubleshooting

### "evaluate_skill.py says missing version but I have one"

**Solution:** Check version field location:
```yaml
# Preferred location (in metadata)
metadata:
  version: "1.0.0"

# Also acceptable (top-level)
version: "1.0.0"
```

### "Quick mode passes but comprehensive mode fails"

**Reason:** Quick mode only checks structure, comprehensive mode validates functionality.

**Solution:** Run with `--validate-functionality` to see specific errors:
```bash
python3 scripts/evaluate_skill.py <skill-path> --validate-functionality
```

### "research_skill.py takes too long"

**Solution:** Focus on specific phases:
```bash
# Just get recommendations (Phase 7 only)
python3 scripts/research_skill.py <skill-path> --phases recommendations
```

### "Metrics don't make sense"

**Solution:** Compare with baseline using --compare:
```bash
# Establish baseline first
python3 scripts/evaluate_skill.py <skill-path> --output baseline.json

# Compare after changes
python3 scripts/evaluate_skill.py <skill-path> --compare baseline.json
```

---

## Best Practices

### For evaluate_skill.py

1. **Use quick mode during development** - Fast feedback loop
2. **Use comprehensive mode before commits** - Catch all issues
3. **Store metrics for tracking** - Monitor quality over time
4. **Compare before/after improvements** - Verify enhancements
5. **Integrate into CI/CD** - Automated quality gates

### For research_skill.py

1. **Run before major changes** - Informed improvement planning
2. **Save research output** - Reference during implementation
3. **Review all 7 phases** - Comprehensive understanding
4. **Link in GitHub Issues** - Include research findings in issue body
5. **Use for learning** - Understand unfamiliar skills

---

## Related References

- `research_guide.md` - Detailed research phase documentation
- `agentskills_specification.md` - Specification compliance details
- `improvement_workflow_guide.md` - When to validate in improvement workflows

---

*This guide provides comprehensive documentation for skillsmith's validation and analysis tools. For script-specific details, see the script source code comments.*
