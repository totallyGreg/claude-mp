# AI Risk Mapper - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the ai-risk-mapper skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-01-07 | Initial release |

## 🔮 Planned Improvements
> Last Updated: 2026-01-22

**Note:** GitHub Issues are the canonical source of truth. See linked issues for detailed planning and task tracking.

### Active Improvements

| Issue | Priority | Title | Status |
|-------|----------|-------|--------|
| [#2](https://github.com/totallyGreg/claude-mp/issues/2) | Critical | Add workflow automation and offline support (v1.1.0) | Open |
| [#3](https://github.com/totallyGreg/claude-mp/issues/3) | High | Restructure SKILL.md for conciseness (v2.0.0) | Open |

#### [#2](https://github.com/totallyGreg/claude-mp/issues/2) Add Workflow Automation and Offline Support
**Goal:** Transform ai-risk-mapper from documentation-oriented to action-oriented automation skill

**Problem:**
- Skill invocation displays 539-line documentation instead of executing workflow
- SSL certificate failures block workflow (corporate proxies)
- No bundled offline schemas for graceful degradation
- No automatic orchestration of fetch → analyze → report workflow

**Proposed Solution:**
- Create `scripts/orchestrate_risk_assessment.py` orchestrator
- Bundle CoSAI schemas in `assets/cosai-schemas/` for offline mode
- Update `fetch_cosai_schemas.py` with SSL bypass + bundled fallback
- Update `SKILL.md` with orchestrator invocation as first action
- Add graceful manual analysis mode when automation unavailable

**Files to Create:**
- `scripts/orchestrate_risk_assessment.py` - Workflow orchestrator
- `assets/cosai-schemas/yaml/*.yaml` - 5 bundled YAML schemas
- `assets/cosai-schemas/schemas/*.json` - 5 bundled JSON schemas

**Files to Modify:**
- `scripts/fetch_cosai_schemas.py` - Add SSL bypass + bundled fallback
- `SKILL.md` - Add "When Invoked" section at top
- `IMPROVEMENT_PLAN.md` - Track completion

**Success Criteria:**
- ✅ Skill invocation automatically runs orchestrator
- ✅ SSL failures gracefully fallback to bundled schemas
- ✅ Complete workflow executes without manual intervention
- ✅ Manual mode available when automation fails

**Version Bump:** 1.0.0 → 1.1.0 (MINOR - new features, backward compatible)

**Plan:** See docs/plans/2026-01-22-ai-risk-mapper-automation-overhaul.md Phase 1

**Note:** Benefits from marketplace-manager evolution (#4) - clean source paths prevent nested skill issues

_For details, task checklists, and discussion, see the linked GitHub issues._

---

## Technical Debt

### Code Quality
- `analyze_risks.py` uses simplified keyword-based risk detection - should be enhanced with semantic analysis (See Planned Improvement #1)
- Scripts lack comprehensive error handling for network failures
- No automated tests for Python scripts

### Documentation
- Need usage examples with real codebases
- Should add troubleshooting guide
- Missing migration guide for existing security assessment workflows

## Enhancement Requests

*Track feature requests and suggestions from users here*

---

## ✅ Recent Improvements (Completed)
> Sorted by: Newest first

### v1.0.0 - Initial Release (2026-01-07)

**Initial Features:**
- Complete CoSAI Risk Map framework integration
- Automated risk analysis for AI systems
- Support for both Model Creator and Model Consumer personas
- Coverage of all 4 lifecycle stages (Data, Infrastructure, Model, Application)
- 25+ security risks from CoSAI catalog
- 30+ mitigation controls
- Multi-format report generation (Markdown, HTML, JSON)
- Compliance mapping to MITRE ATLAS, NIST AI RMF, OWASP Top 10, STRIDE
- Structured data collection forms

**Files Created:**
- `SKILL.md` - Comprehensive skill documentation with workflow-based structure (540 lines)
- `requirements.txt` - Python dependencies (PyYAML)
- `scripts/fetch_cosai_schemas.py` - CoSAI schema downloader and cache manager
- `scripts/analyze_risks.py` - Automated risk identification and assessment
- `scripts/generate_report.py` - Multi-format report generator
- `references/cosai_overview.md` - Framework introduction and methodology
- `references/personas_guide.md` - Model Creator vs Model Consumer responsibilities
- `references/schemas_reference.md` - JSON schema structures and validation rules
- `references/FORMS.md` - Structured data collection templates
- `assets/report_template.md` - Markdown report template

**Capabilities:**
- Fetch and cache CoSAI schemas from GitHub repository
- Analyze codebases, configurations, or system descriptions for AI security risks
- Filter by persona, lifecycle stage, and severity level
- Generate executive-ready security assessment reports
- Map identified risks to recommended controls
- Support compliance documentation for multiple frameworks

**Quality Metrics:**
- AgentSkills Spec Compliance: ✓ PASS
- Overall Quality Score: 67/100
- Progressive Disclosure: 100/100
- 3 automation scripts (1,017 lines Python)
- 4 reference documents (589 lines)
- 1 report template

**Design Decisions:**
- Workflow-based SKILL.md structure for sequential assessment process
- Separation of concerns: fetch → analyze → report workflow
- Local caching of CoSAI schemas for offline use
- Support for both automated and manual risk assessment
- Extensible architecture for custom risk definitions

## Contributing

To suggest improvements to this skill:

1. Add enhancement requests to the "Enhancement Requests" section
2. Discuss technical approaches in "Planned Improvements"
3. Track implementation progress
4. When complete, follow the Planned → Completed workflow:
   - Cut section from Planned Improvements
   - Update header: "### v{version} - {name} ({date})"
   - Paste at top of Recent Improvements (Completed)
   - Update version history table with actual date
   - Add implementation details

## Notes

- This improvement plan should be excluded from skill packaging (see .skillignore)
- Update "Last Updated" timestamp in Planned Improvements when making changes
- Update version history when releasing new versions
- Link to relevant issues/PRs in your repository if applicable
