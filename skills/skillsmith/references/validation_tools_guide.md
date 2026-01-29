# Skill Validation & Analysis Tools Guide

This reference provides comprehensive documentation for skillsmith's validation and analysis tools. Load this file when you need detailed guidance on using `evaluate_skill.py` or `research_skill.py`.

---

## Overview

**`evaluate_skill.py` is the primary tool** for all skill validation and evaluation. Other scripts are either deprecated or serve specialized purposes.

| Script | Status | Purpose |
|--------|--------|---------|
| `evaluate_skill.py` | **PRIMARY** | All validation and evaluation |
| `init_skill.py` | Active | Create new skills from template |
| `research_skill.py` | Experimental | Deep research (40% complete) |
| `validate_workflow.py` | **DEPRECATED** | Use evaluate_skill.py directly |
| `audit_improvements.py` | **DEPRECATED** | Only works with old format |
| `update_references.py` | Active | Reference duplicate detection |

---

## Command Mapping

Use this table to determine which command to run based on what you want to do:

| You want to... | Command |
|----------------|---------|
| Quick structure check | `uv run scripts/evaluate_skill.py <path> --quick` |
| Full quality metrics | `uv run scripts/evaluate_skill.py <path>` |
| Pre-release validation | `uv run scripts/evaluate_skill.py <path> --quick --strict` |
| Validate IMPROVEMENT_PLAN | `uv run scripts/evaluate_skill.py <path> --quick --check-improvement-plan` |
| Compare skill versions | `uv run scripts/evaluate_skill.py <path> --compare <original>` |
| Test scripts/references work | `uv run scripts/evaluate_skill.py <path> --validate-functionality` |
| Get version table row | `uv run scripts/evaluate_skill.py <path> --export-table-row --version X.Y.Z` |
| Create a new skill | `uv run scripts/init_skill.py <skill-name>` |
| Find duplicate references | `uv run scripts/update_references.py <path> --detect-duplicates` |

### Natural Language Triggers

These phrases should trigger skillsmith and the appropriate command:

| User Says | Maps To |
|-----------|---------|
| "validate a skill" / "check skill structure" | `--quick` |
| "evaluate a skill" / "get skill metrics" | (no flags - comprehensive) |
| "strict validation" / "release check" | `--quick --strict` |
| "research a skill" / "analyze a skill" | `research_skill.py` (experimental) |
| "create a skill" / "init a skill" | `init_skill.py` |

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

### Strict Mode (Validation Gate)

Strict mode treats warnings as errors, creating a validation gate for pre-release quality assurance:

```bash
# Strict quick validation (warnings block completion)
uv run scripts/evaluate_skill.py <skill-path> --quick --strict

# Strict mode with IMPROVEMENT_PLAN checking
uv run scripts/evaluate_skill.py <skill-path> --quick --strict --check-improvement-plan
```

#### When to Use Strict Mode

Use `--strict` flag when:
- **Pre-release validation** - Before bumping version and releasing
- **CI/CD gates** - Automated pipelines checking skill quality
- **Marketplace submission** - Before publishing to marketplace
- **Team standards** - When project requires high documentation quality

Strict mode is **not** needed for:
- Development iterations (standard mode is faster)
- Minor bug fixes (use standard mode if no quality regressions)
- Quick sanity checks (standard mode is sufficient)

#### Error Deferral Workflow

When strict mode reports issues you want to defer:

1. Acknowledge the issues (don't ignore them)
2. Create a GitHub issue for the deferred work
3. Document the deferral in your IMPROVEMENT_PLAN.md
4. Later: Complete the deferred work in a follow-up phase

Example workflow:
```bash
# Strict validation finds issues
uv run scripts/evaluate_skill.py skills/my-skill --quick --strict

# If issues exist that you want to defer:
# 1. Create GitHub issue
gh issue create --title "my-skill: Fix documentation issues"
# Output: Created issue #456

# 2. Document in IMPROVEMENT_PLAN.md Active Work section:
# - [#456](link): Fix documentation issues (Planning)

# 3. Later: Complete the deferred work and run strict validation again
uv run scripts/evaluate_skill.py skills/my-skill --quick --strict
```

### When to Use Quick Mode

Quick mode (`--quick`) is optimized for speed and minimal output. Use it for:

- **Pre-commit hooks** - Fast validation before commits
- **CI/CD validation gates** - Automated pipeline checks
- **Quick sanity checks** - During development iterations
- **IMPROVEMENT_PLAN validation** - Before release (with `--check-improvement-plan`)
- **Strict validation** - With `--strict` flag for pre-release gates
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

---

## Validation Rules and Metrics (Phase 2 Enhancement)

This section documents the improved validation rules implemented in Phase 2 of Issue #8.

### Directory Name Resolution

**Bug fixed:** Path('.').name returning empty string on current directory

**Solution:** Use `Path(skill_path).resolve().name` to properly resolve all path formats:
- Absolute paths: `/Users/user/projects/skill-name`
- Relative paths: `skills/skill-name`
- Current directory: `.` (now properly resolves to actual directory name)

**Verification:**
- All three formats resolve to the same directory name
- No false validation failures from empty directory names

### Reference File Validation

Enhanced validation for reference files with deterministic checks:

**Checks Implemented:**

1. **Missing referenced files** (ERROR)
   - Referenced files must exist in `references/` directory
   - Pattern: Backtick-wrapped paths only: `` `references/filename.md` ``
   - Non-backtick examples are documentation, not requirements

2. **Orphaned reference files** (WARNING)
   - Files in `references/` directory should be mentioned in SKILL.md
   - Helps identify obsolete or forgotten documentation

3. **File naming conventions** (WARNING)
   - Reference files must use snake_case: `lowercase_with_underscores.md`
   - Prevents issues with case-sensitive file systems

4. **Absolute paths** (ERROR)
   - No absolute paths allowed (e.g., `/Users/...`, `/home/...`, `C:\...`)
   - Use relative paths: `references/filename.md`

### Conciseness Scoring (Improved)

**Scoring factors:**

1. **Line-based scoring (0-50 points)** - Tiered approach:
   - ≤150 lines: 50 points (Excellent)
   - 150-250 lines: 48 points (Very good - recommended range)
   - 250-350 lines: 45 points (Good - slightly over)
   - 350-500 lines: 40 points (Acceptable)
   - 500-750 lines: 25 points (Poor)
   - >750 lines: 0-10 points (Very poor - way over)

2. **Token-based scoring (0-50 points)** - Stricter limits:
   - ≤1500 tokens: 50 points
   - 1500-2000 tokens: 45 points (max recommended)
   - 2000-3000 tokens: 30 points
   - >3000 tokens: 0-30 points (degrades further)

3. **Reference offloading bonus (+5 points)**
   - Awarded when skill has >500 lines in reference files
   - Incentivizes progressive disclosure principle

**Combined score:** min(100, line_score + token_score + reference_bonus)

**Determinism:** Same metrics always produce same score (no randomness)

### Metrics Interpretation Guide

| Metric | Good Range | Warning Range | Problem Range |
|--------|-----------|----------------|---------------|
| Conciseness | 70+ | 50-70 | <50 |
| Complexity | 80+ | 60-80 | <60 |
| Spec Compliance | 100 | 95-99 | <95 |
| Progressive | 100 | 90-99 | <90 |
| Overall | 90+ | 80-90 | <80 |

### Test Coverage

Phase 2 includes comprehensive test suite covering:
- Directory name detection (absolute, relative, `.` paths)
- Reference validation (missing, orphaned, misspelled files)
- Conciseness scoring (deterministic tiered scoring)
- Spec compliance (naming, limits, requirements)
- Validation determinism (same input = same output)

**Test status:** 12/12 tests passing ✅

**Test file location:** `tests/test_evaluate_skill.py`

---

## Related References

- `research_guide.md` - Detailed research phase documentation
- `agentskills_specification.md` - Specification compliance details
- `improvement_workflow_guide.md` - When to validate in improvement workflows

---

*This guide provides comprehensive documentation for skillsmith's validation and analysis tools. For script-specific details, see the script source code comments.*
