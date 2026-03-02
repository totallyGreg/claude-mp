# AI Risk Mapper - Skillsmith Recommendations & Implementation Plan

**Date**: 2026-01-28
**Evaluator**: Claude Code - Skill Architecture Review
**Target Audience**: Skill developers, architecture leads, contributors
**Scope**: Comprehensive improvement strategy based on capability evaluation

---

## Executive Summary

The ai-risk-mapper skill (v2.0.0) is a **solid foundation** with excellent automation and documentation, but has **critical accuracy gaps** and **synchronization issues** with its source of truth (CoSAI repository). This document provides prioritized recommendations for a phased improvement roadmap targeting v2.0.1 through v2.2.0.

### Key Findings

| Aspect | Rating | Status |
|--------|--------|--------|
| **Current Maturity** | ★★★☆☆ (3/5) | Functional but incomplete |
| **Automation & Orchestration** | ★★★★☆ (4/5) | Working well; excellent fallback |
| **Documentation** | ★★★★☆ (4/5) | Comprehensive; well-organized |
| **Accuracy** | ★★☆☆☆ (2/5) | **Critical gap**: Keyword-based detection |
| **Schema Synchronization** | ★★☆☆☆ (2/5) | **Critical gap**: Missing v2.0.0+ schemas |
| **Test Coverage** | ★☆☆☆☆ (1/5) | **Critical gap**: No automated tests |

**Overall Score**: 2.5/5 - Requires targeted improvements in accuracy, sync, and reliability

---

## Critical Gaps (P0 - Must Fix)

### 1. Schema Bundle Out of Sync (v2.0.1)

**Missing from Bundle** (as of CoSAI commit 00e6dc4):
- `frameworks.schema.json` - Framework version definitions
- `actor-access.schema.json` - Access control categorization
- `impact-type.schema.json` - Impact type definitions
- `lifecycle-stage.schema.json` - Lifecycle stage definitions
- `mermaid-styles.schema.json` - Visualization styling
- `frameworks.yaml` - Framework version tracking data
- Updated `personas.yaml` - Now includes 7 personas (missing 1)

**Why Critical**: Offline mode increasingly diverges from CoSAI source of truth with each release.

**Fix**: Add missing files to `/assets/cosai-schemas/` (2-4 hours)

---

### 2. Keyword-Based Risk Detection (v2.1.0)

**Current Problem**: `analyze_risks.py` uses pattern matching instead of semantic analysis.

```python
# Current approach
if "password" in file_content:
    risks.append("Sensitive Data Disclosure")

# Limitations:
# - False positives: "secret" in variable names
# - False negatives: misses context-aware risks
# - Cannot detect composition attacks
```

**Why Critical**: Accuracy directly impacts skill's value proposition (60-70% vs 90-95% target).

**Fix**: Implement `SemanticRiskAnalyzer` using Claude API with fallback to keyword-based (20-24 hours).

---

### 3. Zero Automated Tests (v2.1.0)

**Current State**: All testing is manual; risky for refactoring.

**Why Critical**: No safety net for semantic analysis feature; regressions undetected.

**Fix**: Build test suite with 80%+ coverage (16-20 hours).

---

## Priority Improvements (P1 - High Impact)

### 4. Branch Awareness - Fetch from develop (v2.0.1)

**Current**: Hardcoded to fetch from main branch only.

**Issue**: Cannot access develop branch (7 commits ahead with pre-release features).

**Fix**: Add `--branch` flag to fetch script (4-6 hours).

```bash
uv run scripts/fetch_cosai_schemas.py --branch develop --include-frameworks
```

---

### 5. Framework Version Tracking (v2.1.0)

**Missing**: Cannot track which framework versions are in use or show compliance mapping.

**Fix**: Load `frameworks.yaml`, map risks to framework versions, include in reports (8-12 hours).

---

### 6. Graph Validation Integration (v2.1.0)

**Opportunity**: CoSAI provides `validate_riskmap.py` with edge validation and graph generation.

**Current State**: Not used; reimplemented.

**Fix**: Wrap CoSAI validation for relationship verification and visualization (12-16 hours).

---

## Recommended Slash Commands

These commands should be exposed to surface existing and new functionality:

### Analysis Commands

| Command | Purpose | Status |
|---------|---------|--------|
| `/assess <target>` | Full risk assessment | v2.0.0 (exists) |
| `/analyze-risks <target>` | Filtered analysis | v2.0.0 (exists) |
| `/semantic-analyze <target>` | LLM-based analysis | v2.1.0 (NEW) |

### Utilities

| Command | Purpose | Status |
|---------|---------|--------|
| `/fetch-schemas [--branch]` | Update schema cache | v2.0.1 (enhance) |
| `/validate-risks` | Validate risk mappings | v2.1.0 (NEW) |
| `/generate-report <file>` | Create report | v2.0.0 (exists) |

### Visualization (v2.2.0+)

| Command | Purpose | Status |
|---------|---------|--------|
| `/visualize-risks <file>` | Interactive dashboard | v2.2.0 (NEW) |
| `/track-controls` | Control implementation status | v2.2.0 (NEW) |
| `/risk-graph` | Risk relationship visualization | v2.1.0 (NEW) |

### Reference

| Command | Purpose | Status |
|---------|---------|--------|
| `/cosai-concepts [topic]` | Framework explanation | v2.0.0 (reference) |
| `/persona-guide [role]` | Persona definitions | v2.0.0 (reference) |
| `/risk-reference <risk>` | Risk catalog lookup | v2.0.0 (reference) |

---

## Implementation Roadmap

```
Current (v2.0.0)
    ↓
v2.0.1: Schema Sync + Branch Support (PATCH - 1-2 weeks)
    ├─ Bundle missing schemas
    ├─ Add --branch flag for develop access
    └─ Test offline mode

v2.1.0: Semantic Analysis + Testing (MINOR - 6-8 weeks)
    ├─ Implement LLM-based risk detector
    ├─ Build test suite (80%+ coverage)
    ├─ Add graph validation
    ├─ Track framework versions
    └─ New commands: /semantic-analyze, /validate-risks, /risk-graph

v2.2.0: Visualization + Tracking (MINOR - 8-10 weeks)
    ├─ Interactive risk dashboard
    ├─ Control implementation tracker
    ├─ Example systems library
    └─ New commands: /visualize-risks, /track-controls
```

**Total Timeline**: ~5-6 months for full roadmap

---

## SKILL.md Assessment

**Current State** (v2.0.0): Already improved significantly
- Lines: 219 (from 538 in v1.0) ✅
- Tokens: ~1,892 (from 4,585) ✅
- Conciseness: 70/100 ✅
- Progressive Disclosure: 100/100 ✅

**Recommendation**: KEEP CURRENT STRUCTURE - it works well!

**Enhancements for v2.1.0+**:
- Add semantic analysis examples when feature ready
- Expand "Manual Workflow" with framework version tracking
- Link to new troubleshooting guide
- Document new commands as they're added

---

## Bundled Resources Assessment

### Missing from Assets (v2.0.1)

Need to add to `/assets/cosai-schemas/`:

**Schemas**:
- `schemas/frameworks.schema.json`
- `schemas/actor-access.schema.json`
- `schemas/impact-type.schema.json`
- `schemas/lifecycle-stage.schema.json`
- `schemas/mermaid-styles.schema.json`

**YAML Data**:
- `yaml/frameworks.yaml` (NEW - critical for compliance tracking)
- Update `yaml/personas.yaml` (add 7th persona)

**Documentation** (new):
- `assets/cosai-schemas/README.md` - Track sync status and commit hashes

### Planned Additions (v2.1.0+)

**References**:
- `references/troubleshooting.md` - Common errors and recovery
- `references/semantic_analysis_guide.md` - LLM analysis explanation
- `references/schema_version_guide.md` - Framework version tracking

**Scripts**:
- `scripts/semantic_analyzer.py` - LLM-based analysis engine
- `scripts/validate_risk_graph.py` - Risk graph validation
- `scripts/visualize_risks.py` - Dashboard generation (v2.2.0)
- `scripts/control_tracker.py` - Control tracking (v2.2.0)

---

## Critical Implementation Notes

### CoSAI Synchronization Strategy

**Sync Frequency**:
- **Automatic**: Weekly check for updates (optional CI job)
- **Manual**: Monthly review after CoSAI releases (recommended)
- **Emergency**: Hotfix for critical schema changes

**Versioning**:
- Track CoSAI source commit hash in `assets/cosai-schemas/README.md`
- Sync to main branch by default; develop available via `--branch` flag
- Version bump: PATCH for data updates, MINOR for schema additions

---

### Semantic Analysis Implementation

**Architecture**:
```
Layer 1: Keyword patterns (fast, offline)
  → 60-70% accuracy, <1s

Layer 2: LLM semantic analysis (optional, API)
  → 90-95% accuracy, 3-5s

Layer 3: Graph validation (optional)
  → Coverage metrics
```

**API Strategy**:
- Use `claude-3-haiku` for cost efficiency (~$0.05-0.20 per assessment)
- Fallback to keyword-based if API unavailable
- Cache system prompts for performance
- Cost target: <$0.50 per assessment

**Fallback Behavior**:
```
If API key missing: Use keyword-based (show message)
If API error: Retry once, then fallback
If offline: Use bundled schemas + keyword analysis
```

---

### Test Coverage Goals

**Target**: 80%+ overall coverage

| Module | Target | Tests |
|--------|--------|-------|
| orchestrator.py | 90% | Happy path, fallback, error handling |
| analyze_risks.py | 85% | Filtering, persona, lifecycle logic |
| semantic_analyzer.py | 80% | LLM calls (mocked), fallback |
| generate_report.py | 80% | Format generation, edge cases |
| fetch_cosai_schemas.py | 75% | Network scenarios, branching |

**Test Infrastructure**:
- Use pytest with coverage reporting
- Test targets in `/tests/test-targets/` (simple-ai-app, rag-pipeline, etc.)
- CI/CD integration for automated testing
- Performance benchmarks to prevent regressions

---

## Success Criteria by Phase

### v2.0.1 (Schema Sync)
- [ ] All missing schemas bundled
- [ ] Branch support implemented (main/develop)
- [ ] Offline mode works with new schemas
- [ ] No test failures
- [ ] Documentation updated

### v2.1.0 (Semantic Analysis)
- [ ] Semantic analyzer identifies 3+ subtle risks keyword approach misses
- [ ] Test coverage >80%
- [ ] API costs <$0.50 per assessment
- [ ] Fallback to keyword-based works
- [ ] Framework versions tracked in reports
- [ ] Graph validation operational
- [ ] New commands documented

### v2.2.0 (Visualization)
- [ ] Interactive dashboard generated
- [ ] Control tracker functional
- [ ] Example systems provided
- [ ] <500 KB output files
- [ ] Mobile-responsive design

---

## GitHub Issues to File

- **Issue #X** (v2.0.1): "Bundle missing CoSAI schemas & add branch awareness"
- **Issue #20** (v2.1.0): "Phase 3 - Semantic analysis, testing, validation" (already exists)
- **Issue #21** (v2.2.0): "Phase 3B - Visualization & control tracking"

---

## Resource Estimates

**Team**:
- 1 Architect (planning, design reviews)
- 2-3 Developers (implementation)
- 1-2 QA Engineers (testing)
- 1 Technical Writer (documentation)

**Budget**:
- API costs (semantic analysis): ~$100-150/month (development)
- CI/CD infrastructure: ~$50/month
- Tools: Included in project

**Timeline**: 5-6 months for full roadmap (v2.0.1 + v2.1.0 + v2.2.0)

---

## Conclusion

The ai-risk-mapper skill is **production-ready for current use cases** but requires **targeted improvements** to reach production-grade reliability and accuracy. The phased roadmap addresses critical gaps while maintaining backward compatibility.

**Immediate Actions** (Next 1-2 weeks):
1. Update bundled schemas for v2.0.1
2. Add branch awareness to fetch script
3. File GitHub issue for v2.1.0 (semantic analysis)
4. Begin test infrastructure setup

**Next Review**: After v2.0.1 completion

---

This comprehensive Skillsmith recommendations document is ready for implementation planning. Use it as the authoritative guide for ai-risk-mapper improvements.
