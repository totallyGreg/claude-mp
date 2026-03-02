# AI Risk Mapper - Evaluation Quick Reference

**Date**: 2026-01-28 | **Status**: Complete | **Maturity**: ★★★☆☆ (3/5)

---

## 🎯 Critical Gaps (Fix First)

| Gap | Impact | Fix | Timeline |
|-----|--------|-----|----------|
| **Missing schemas** (frameworks.yaml, etc.) | HIGH | Update bundle to CoSAI commit 00e6dc4 | v2.0.1 (1 week) |
| **Keyword-based detection** (60-70% accuracy) | CRITICAL | Add semantic LLM analyzer | v2.1.0 (4 weeks) |
| **No automated tests** | CRITICAL | Build pytest suite (80%+ coverage) | v2.1.0 (3 weeks) |
| **No branch support** | MEDIUM | Add `--branch` flag to fetch script | v2.0.1 (1 week) |
| **No graph validation** | MEDIUM | Integrate CoSAI validation scripts | v2.1.0 (2 weeks) |

---

## 📊 Improvement Roadmap

```
v2.0.1 (1-2 weeks)          v2.1.0 (6-8 weeks)        v2.2.0 (8-10 weeks)
├─ Schema sync              ├─ Semantic analyzer      ├─ Visualization
├─ Branch support           ├─ Test coverage          ├─ Control tracker
└─ Offline validation       ├─ Graph validation       └─ Example systems
                            └─ Framework tracking
```

---

## ✨ New Slash Commands (Recommended)

### v2.1.0 (Next Priority)
```
/semantic-analyze <target>    # LLM-based risk detection
/validate-risks              # Validate risk mappings
/risk-graph                  # Show risk relationships
```

### v2.2.0 (Future)
```
/visualize-risks <file>      # Interactive dashboard
/track-controls              # Control implementation status
```

---

## 📈 Accuracy Target

| Phase | Method | Accuracy | False Positives |
|-------|--------|----------|-----------------|
| Current | Keyword patterns | 60-70% | 20-30% |
| v2.1.0 | Semantic (LLM) | 90-95% | <10% |
| v2.2.0 | Semantic + Graph | 95%+ | <5% |

---

## 🔄 CoSAI Sync Strategy

**Current Bundle**: Locked to commit 00e6dc4 (main, 2026-01-28)

**Recommended Sync**:
- **Frequency**: Monthly after CoSAI releases (bi-weekly cycle)
- **Branches**: Main (default, stable) + Develop (optional, pre-release)
- **Tracking**: Document commit hash in `assets/cosai-schemas/README.md`

**Available Scripts Not Yet Used**:
- `validate_riskmap.py` - Edge validation + graph generation
- `validate_control_risk_references.py` - Bidirectional mappings
- `validate_framework_references.py` - Framework constraints
- Component/Control/Risk graphs for visualization

---

## 📋 GitHub Issues

| Issue | Status | Plan |
|-------|--------|------|
| #2 | ✅ CLOSED | Phase 1 - Automation (v1.1.0) |
| #3 | ✅ CLOSED | Phase 2 - SKILL.md (v2.0.0) |
| #20 | 🔓 OPEN | Phase 3 - Semantic + Testing (v2.1.0+) |
| #X | 📝 TODO | Phase 3A - v2.0.1 schema sync |

---

## 📦 Missing from Bundle (v2.0.1)

**Schemas** (5 missing):
- `frameworks.schema.json`
- `actor-access.schema.json`
- `impact-type.schema.json`
- `lifecycle-stage.schema.json`
- `mermaid-styles.schema.json`

**YAML Data** (2 items):
- `frameworks.yaml` (NEW - critical)
- `personas.yaml` (UPDATE - add 7th persona)

---

## 🛠️ Implementation Priorities

### P0 (Critical - Week 1)
- [ ] Bundle missing schemas
- [ ] Add `--branch` flag
- [ ] Test offline mode

### P1 (High - Weeks 3-10)
- [ ] Semantic analyzer + API integration
- [ ] Test suite (pytest, 80%+ coverage)
- [ ] Graph validation integration
- [ ] Framework version tracking

### P2 (Medium - Weeks 11-20)
- [ ] Risk visualization dashboard
- [ ] Control implementation tracker
- [ ] Example systems library

---

## 💾 Key Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `scripts/fetch_cosai_schemas.py` | v2.0.1 | Add --branch, --include-frameworks |
| `assets/cosai-schemas/` | v2.0.1 | Add 5 missing schemas + yaml files |
| `scripts/analyze_risks.py` | v2.1.0 | Integrate semantic analyzer |
| `scripts/semantic_analyzer.py` | v2.1.0 | NEW - LLM analysis module |
| `tests/` | v2.1.0 | NEW - Test suite |
| `scripts/validate_risk_graph.py` | v2.1.0 | NEW - Graph validation |
| `SKILL.md` | v2.1.0 | Add semantic analysis examples |
| `IMPROVEMENT_PLAN.md` | All | Track versions |

---

## 📈 Success Metrics

**Maturity**: 3/5 (Current) → 4/5 (v2.1.0) → 4.5/5 (v2.2.0)

**Accuracy**: 60-70% (Current) → 90-95% (v2.1.0) → 95%+ (v2.2.0)

**Test Coverage**: 0% (Current) → 80%+ (v2.1.0) → 85%+ (v2.2.0)

---

## 🚀 Next Actions

1. **This Week**: Review detailed recommendations document
2. **Next Week**: Create GitHub Issue #X for v2.0.1
3. **Week 2-3**: Begin schema bundle updates
4. **Week 3-10**: Implement v2.1.0 features

---

## 📚 Reference Documents

- **Full Evaluation**: `docs/lessons/ai-risk-mapper-capability-evaluation.md`
- **Implementation Plan**: `docs/lessons/ai-risk-mapper-skillsmith-recommendations.md`
- **Summary**: `docs/lessons/ai-risk-mapper-evaluation-summary.md`
- **Version History**: `skills/ai-risk-mapper/IMPROVEMENT_PLAN.md`

---

**Evaluation by**: Claude Code
**Date**: 2026-01-28
**Time Investment**: Comprehensive (multi-agent analysis)
**Recommendation**: Ready for implementation planning
