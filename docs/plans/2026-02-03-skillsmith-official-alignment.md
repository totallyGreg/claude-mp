# Skillsmith Alignment with Official Anthropic Plugin-Dev Patterns

**Date:** 2026-02-03
**GitHub Issue:** [#33](https://github.com/totallyGreg/claude-mp/issues/33)
**Epic:** Align skillsmith with official plugin-dev patterns while preserving unique metrics/automation
**Status:** Planning
**Owner:** skillsmith

## Executive Summary

Skillsmith was created (v1.0-4.0) before the official Anthropic plugin-dev toolkit existed. Now that plugin-dev is the canonical pattern library, this epic ensures skillsmith:

1. **Implements** official AgentSkills spec patterns (already done)
2. **Aligns** skillsmith SKILL.md with official documentation style
3. **References** official plugin-dev examples and patterns
4. **Preserves** unique skillsmith capabilities (metrics, automation, research)
5. **Extends** official patterns with tooling integration

**Key Insight:** Skillsmith is NOT behind official—it's ahead. This is about making that explicit and connecting the two ecosystems.

---

## Current State (v4.0.0)

### Strengths
- ✅ Automated validation system (vs official's manual checklist)
- ✅ 4-dimension metrics (conciseness, complexity, spec compliance, progressive disclosure)
- ✅ Improvement verification (before/after comparison)
- ✅ Multi-phase skill research capability
- ✅ Python PEP 723 validation
- ✅ Marketplace integration patterns
- ✅ IMPROVEMENT_PLAN.md tracking system
- ✅ 11 comprehensive reference files

### Gaps
- ❌ Description lacks specific trigger phrases (uses general categories)
- ❌ No error/success example pairs in documentation
- ❌ No quick reference skill templates (minimal/standard/complete)
- ❌ Limited cross-references to official plugin-dev examples
- ❌ No "Mistakes to Avoid" explicit section
- ❌ Missing formal validation checklist in SKILL.md
- ❌ No description quality metrics in evaluation system

---

## Target State (v5.0.0)

### Phase 1: Documentation Alignment (Weeks 1-2)

**1.1 Update Skillsmith Description**
- Current: "users want to create, validate, evaluate, research, analyze, or improve skills"
- Target: Explicit trigger phrases users actually say
  ```
  This skill should be used when users ask to:
  - "create a skill"
  - "validate a skill for quality"
  - "evaluate skill improvements"
  - "research skill opportunities"
  - "improve skill quality"
  - "sync skill to marketplace"
  ```
- Impact: Better triggering, clearer intent
- Files: skillsmith/SKILL.md frontmatter
- Effort: 30 minutes

**1.2 Add "Common Mistakes" Subsection**
- Extract from scattered references into SKILL.md
- Format: Mistake → Why bad → How to fix
- Examples:
  - Weak trigger descriptions
  - Bloated SKILL.md (should be <500 lines)
  - Second-person writing ("You should...")
  - Missing or orphaned references
- Files: skillsmith/SKILL.md, references/common_mistakes.md (new)
- Effort: 2 hours

**1.3 Create Quick Reference Templates**
- Three skill patterns:
  1. **Minimal** - <100 lines, single-topic skill (e.g., reference-only skill)
  2. **Standard** - 150-300 lines, well-structured with 2-3 references
  3. **Complete** - 250-400 lines, comprehensive with bundled resources
- Show frontmatter, body structure, reference organization for each
- Files: skillsmith/SKILL.md "Quick Reference" section, assets/templates/
- Effort: 4 hours

**1.4 Add Cross-References to Official Examples**
- Reference actual plugin-dev skills:
  - hook-development - Best progressive disclosure example
  - agent-development - Good system prompt structure
  - plugin-settings - Excellent reference organization
  - command-development - Clear trigger phrase examples
- Add callout: "Study these official examples for best practices"
- Files: skillsmith/SKILL.md, references/skill_creation_detailed_guide.md
- Effort: 2 hours

**1.5 Create Error/Success Example Pairs**
- Show bad descriptions alongside good descriptions
- Show bad SKILL.md structure vs good structure
- Show bad reference organization vs good organization
- Files: skillsmith/SKILL.md, references/example_pairs.md (new)
- Effort: 3 hours

**Subtotal Phase 1: ~12 hours**

---

### Phase 2: Validation Integration (Week 3)

**2.1 Map Manual Checklist to Automated Validation**
- Create table in SKILL.md:
  - Official pattern → Skillsmith automation
  - Example: "Has name/description fields" → Automated in quick validation
  - Example: "Uses third-person description" → Automated in spec validation
  - Example: "References are real files" → Automated in file validation
- Files: skillsmith/SKILL.md, references/validation_tools_guide.md (update)
- Effort: 3 hours

**2.2 Add Formal Validation Checklist to SKILL.md**
- Adapt official's 24-point checklist
- Add notation: [AUTO], [MANUAL], [HYBRID]
- Explain which evaluate_skill.py mode covers each item
- Files: skillsmith/SKILL.md "Validation Checklist" section
- Effort: 2 hours

**2.3 Enhance evaluate_skill.py with Description Quality**
- New metric: Description Quality Score (0-100)
  - Trigger phrases present? (+40 points)
  - Third-person format? (+30 points)
  - Specific vs generic? (+20 points)
  - Under 1024 chars? (+10 points)
- Add to `--export-table-row` output
- Include in overall score? (Decision: Yes, at 0.10 weight)
- Files: evaluate_skill.py, references/validation_tools_guide.md
- Effort: 6 hours

**2.4 Add Trigger Phrase Validation**
- New check: Does description contain concrete trigger phrases?
- Detect patterns: "create X", "validate Y", "configure Z", "analyze A"
- Warning if only generic terms found
- Add `--check-triggers` flag to quick validation
- Files: evaluate_skill.py (validate_description_quality function)
- Effort: 4 hours

**Subtotal Phase 2: ~15 hours**

---

### Phase 3: Tooling Enhancement (Week 3-4)

**3.1 Enhance init_skill.py with Templates**
- Add interactive template selection:
  ```
  What type of skill are you creating?
  1. Minimal (reference-only, <100 lines)
  2. Standard (well-structured, 150-300 lines)
  3. Complete (comprehensive, 250-400 lines)
  ```
- Generate SKILL.md with appropriate structure
- Pre-populate frontmatter with examples
- Files: skillsmith/scripts/init_skill.py
- Effort: 4 hours

**3.2 Add --explain Mode to Validation**
- Shows WHY a metric scored what it did
- Explains what would improve the score
- Example output:
  ```
  Conciseness Score: 80/100

  Why: SKILL.md is 235 lines (good! under recommended 300)

  To improve to 85+:
  - Move sections "Advanced Topics" → reference file
  - Consider condensing examples section

  Reference: See progressive_disclosure_discipline.md
  ```
- Files: evaluate_skill.py (explain_metric function)
- Effort: 5 hours

**3.3 Create Description Quality Report**
- Detailed feedback on description quality
- Shows trigger phrases found
- Suggests improvements
- Examples of strong descriptions
- Files: evaluate_skill.py (description_quality_report function)
- Effort: 3 hours

**3.4 Add Comparison to Official Patterns**
- New `--compare-to-official` flag
- Shows how skill aligns with official patterns
- Highlights areas of agreement/divergence
- Files: evaluate_skill.py (compare_to_official function)
- Effort: 4 hours

**Subtotal Phase 3: ~16 hours**

---

### Phase 4: Documentation & Release (Week 4)

**4.1 Update skillsmith README**
- Add "Alignment with Official Patterns" section
- Create comparison matrix
- Show how skillsmith extends official patterns
- Files: skillsmith/README.md or skillsmith/SKILL.md
- Effort: 3 hours

**4.2 Update Integration Guide**
- Expand integration_guide.md with official pattern references
- Show how skillsmith + plugin-dev work together
- Files: skillsmith/references/integration_guide.md
- Effort: 2 hours

**4.3 Create Migration Guide**
- For users coming from official plugin-dev
- "What skillsmith adds beyond official patterns"
- How to use both together
- Files: skillsmith/references/migration_from_plugin_dev.md (new)
- Effort: 2 hours

**4.4 Update IMPROVEMENT_PLAN.md**
- Add completed work to version history
- Document metrics changes
- Link to GitHub issue
- Bump version to 5.0.0
- Files: skillsmith/IMPROVEMENT_PLAN.md
- Effort: 1 hour

**4.5 Release & Sync to Marketplace**
- Create release commit
- Tag v5.0.0
- Use marketplace-manager to sync
- Files: All above
- Effort: 1 hour

**Subtotal Phase 4: ~9 hours**

---

## Total Effort Estimate

| Phase | Subtotal | Notes |
|-------|----------|-------|
| Phase 1: Documentation | 12 hours | Writing, examples, references |
| Phase 2: Validation | 15 hours | Code, testing, integration |
| Phase 3: Tooling | 16 hours | Script enhancement, new features |
| Phase 4: Release | 9 hours | Documentation, release process |
| **TOTAL** | **52 hours** | ~1 week full-time, 2-3 weeks part-time |

---

## Success Criteria

### Phase 1 Complete
- [ ] Description has 6+ specific trigger phrases
- [ ] SKILL.md includes "Common Mistakes" section
- [ ] Three skill templates documented
- [ ] Cross-references to 4+ official plugin-dev skills
- [ ] Bad/good example pairs created

### Phase 2 Complete
- [ ] Validation checklist in SKILL.md
- [ ] Manual/Auto/Hybrid notation for each item
- [ ] Description Quality Score (0-100) calculated
- [ ] Trigger phrase validation working
- [ ] All checks pass `--strict` mode

### Phase 3 Complete
- [ ] Template selection in init_skill.py working
- [ ] `--explain` mode provides helpful feedback
- [ ] Description quality report generated
- [ ] `--compare-to-official` shows alignment
- [ ] New validations don't break existing workflows

### Phase 4 Complete
- [ ] README updated with alignment section
- [ ] Integration guide expanded
- [ ] Migration guide for plugin-dev users created
- [ ] IMPROVEMENT_PLAN.md updated
- [ ] v5.0.0 released to marketplace

---

## Implementation Notes

### Keep Skillsmith's Unique Value

**DO NOT remove or deprecate:**
- Metrics system (official doesn't have this)
- Improvement verification (unique to skillsmith)
- Research & analysis capability (unique to skillsmith)
- Python PEP 723 validation (extends official spec)
- Marketplace integration (unique to skillsmith)
- IMPROVEMENT_PLAN tracking (unique to skillsmith)

**DO enhance connections to official patterns:**
- Reference official plugin-dev examples frequently
- Make AgentSkills spec compliance explicit
- Show how skillsmith automation implements official checklist
- Position as "Official patterns + Metrics + Automation"

### Reference File Changes

**Create new:**
- `references/common_mistakes.md` - Extracted/expanded from scattered notes
- `references/example_pairs.md` - Bad/good description pairs with explanation
- `references/migration_from_plugin_dev.md` - For official plugin-dev users

**Update existing:**
- `references/skill_creation_detailed_guide.md` - Add official pattern references
- `references/validation_tools_guide.md` - Add description quality scoring section
- `references/agentskills_specification.md` - Map to automation

**Keep as-is (unique value):**
- `references/python_uv_guide.md`
- `references/improvement_workflow_guide.md`
- `references/improvement_plan_best_practices.md`
- `references/research_guide.md`
- `references/integration_guide.md`
- `references/reference_management_guide.md`

### Script Changes

**evaluate_skill.py enhancements:**
- `validate_description_quality()` - New function for trigger phrase analysis
- `explain_metric()` - New function for detailed score explanation
- `description_quality_report()` - New function for comprehensive feedback
- `compare_to_official()` - New function for pattern alignment
- Update `calculate_overall_score()` - Include description quality at 0.10 weight
- Update `print_evaluation_text()` - Show description quality prominently

**init_skill.py enhancements:**
- Interactive template selection
- Pre-populate with template examples
- Generate appropriate directory structure
- Add comments for each template level

### Testing Strategy

1. **Unit tests** for new validation functions
2. **Integration tests** for evaluate_skill.py enhancements
3. **Regression tests** to ensure existing validations still work
4. **Manual testing** with various skill examples:
   - Minimal skills
   - Standard skills
   - Complete skills
   - Skills with problems (for evaluation)

---

## Risk Mitigation

### Risk: Breaking existing evaluate_skill.py users
**Mitigation:**
- Add new metrics without removing old ones
- Keep `--quick` mode unchanged
- Make description quality optional flag initially
- Provide migration guide in release notes

### Risk: Too much change in SKILL.md
**Mitigation:**
- Keep SKILL.md lean (<300 lines)
- Move detailed content to references
- Use callouts for important sections
- Don't duplicate official patterns—reference instead

### Risk: Validation too strict
**Mitigation:**
- Introduce checks as warnings first
- Add `--explain` mode to help users understand
- `--strict` mode for pre-release only
- Provide clear improvement guidance

### Risk: Integration with official patterns unclear
**Mitigation:**
- Explicit comparison matrix in SKILL.md
- "Alignment with Official Patterns" section
- Cross-references throughout
- Migration guide for plugin-dev users

---

## Success Metrics

After v5.0.0 release:
- [ ] skillsmith SKILL.md scores 85+/100 in its own evaluation
- [ ] All 24 official validation checklist items documented in SKILL.md
- [ ] 10+ cross-references to official plugin-dev skills
- [ ] 3 skill templates available for quick reference
- [ ] Description Quality Score implemented and documented
- [ ] Zero regressions in existing validation functionality
- [ ] Plugin-dev users can easily understand how to use skillsmith

---

## Timeline

```
Week 1 (Feb 3-7):
  Mon-Tue: Phase 1.1-1.2 (Description, Common Mistakes)
  Wed-Thu: Phase 1.3-1.4 (Templates, Cross-references)
  Fri:     Phase 1.5 (Error/Success pairs) + Testing

Week 2 (Feb 10-14):
  Mon-Tue: Phase 2.1-2.2 (Checklist mapping, validation)
  Wed-Thu: Phase 2.3 (Description Quality Score)
  Fri:     Phase 2.4 (Trigger validation) + Testing

Week 3 (Feb 17-21):
  Mon-Tue: Phase 3.1-3.2 (Template enhancement, --explain mode)
  Wed-Thu: Phase 3.3-3.4 (Quality report, official comparison)
  Fri:     Phase 3 testing

Week 4 (Feb 24-28):
  Mon-Tue: Phase 4.1-4.3 (Documentation, migration guide)
  Wed:     Phase 4.4-4.5 (Release prep, IMPROVEMENT_PLAN update)
  Thu-Fri: Release v5.0.0, marketplace sync, validation
```

---

## References

- Official plugin-dev location: `/Users/totally/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/`
- Gap analysis: `/Users/totally/Documents/Projects/claude-mp/docs/lessons/plugin-integration-and-architecture.md`
- Skillsmith v4.0.0: `/Users/totally/Documents/Projects/claude-mp/plugins/skillsmith/`
- GitHub issues: Track work with issue labels `skillsmith:alignment`, `skillsmith:v5.0.0`
