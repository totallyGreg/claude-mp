# AI Risk Mapper Plugin

Identify, analyze, and mitigate security risks in AI systems using the CoSAI (Coalition for Secure AI) Risk Map framework.

## Installation

Add to your Claude Code plugins or install via the marketplace.

## Commands

Interactive commands for querying the CoSAI risk database:

| Command | Purpose |
|---------|---------|
| `/arm-risk-search <query>` | Search risks by keyword |
| `/arm-control-search <query>` | Search controls by keyword |
| `/arm-controls-for-risk <id>` | Get controls for a specific risk |
| `/arm-persona-profile <id>` | Get risk profile for a persona |
| `/arm-gap-analysis <id>` | Assess control coverage gaps |
| `/arm-framework-map <id>` | Map risk to compliance frameworks |
| `/arm-actor-access [level]` | Show risks by threat actor access level |

All commands support `--offline` flag to use bundled schemas.

### Examples

```bash
/arm-risk-search injection
/arm-gap-analysis DP --implemented controlTrainingDataSanitization
/arm-framework-map PIJ --framework mitre-atlas --offline
```

## Skills

### ai-risk-mapper

Triggers on requests like:
- "Analyze security risks in my AI application"
- "Generate a CoSAI risk assessment for this codebase"
- "What AI security risks apply to my RAG pipeline?"

The skill runs automated assessments and generates comprehensive reports aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, and STRIDE frameworks.

## Resources

- **CoSAI Framework**: https://github.com/cosai-oasis/secure-ai-tooling
- **Bundled schemas**: Offline-capable with cached CoSAI data in `assets/cosai-schemas/`

## Version

4.0.0

## Skill: ai-risk-mapper

### Current Metrics

**Score: 100/100** (Perfect) — 2026-05-06

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 100 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 5.2.2 | 2026-05-06 | - | Add actor access level CLI, reference guide, and /arm-actor-access command; parse actorAccess field in core_analyzer | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.2.1 | 2026-05-06 | - | Re-bundle offline schemas from upstream main (e01f684): 10 YAML + 13 JSON schemas, 28 camelCase risks, new externalReferences/persona-site-data schemas | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.2.0 | 2026-05-06 | - | Provenance on all 7 refs, negative trigger, offload examples to refs, full-audit refresh: externalReferences + eu-ai-act + strict mapping patterns from upstream Apr 30 commit | 100 | 100 | 100 | 100 | 100 | 100 |
| 5.1.1 | 2026-04-28 | [#165](https://github.com/totallyGreg/claude-mp/issues/165) | Refresh references via /ss-refresh: risk IDs migrated to camelCase (28 total, 2 new), provenance frontmatter added, last_verified updated | 100 | 88 | 100 | 100 | 100 | 97 |
| 5.1.0 | 2026-03-05 | [#85](https://github.com/totallyGreg/claude-mp/issues/85) | Sync upstream: bundle 3 YAML enum files + riskmap.schema.json (9+11), fix deprecated persona refs in docs, add deprecation warning in CLI, add commit-hash README | 98 | 88 | 100 | 100 | - | 97 |
| 5.0.0 | 2026-02-25 | [#56](https://github.com/totallyGreg/claude-mp/issues/56) | Refresh CoSAI upstream data: 8-persona model (ISO 22989), fix lifecycle/impact parsing bugs, add frameworks.yaml, rewrite exploration guide and personas guide | 98 | 88 | 100 | 100 | - | 93 |
| 4.0.1 | 2026-02-04 | - | Fix: use absolute paths with ${CLAUDE_PLUGIN_ROOT} in SKILL.md | 98 | 88 | 100 | 100 | - | 97 |
| 4.0.0 | 2026-02-04 | [#31](https://github.com/totallyGreg/claude-mp/issues/31) | Migrate to standalone plugin structure, add 6 slash commands | 100 | 88 | 100 | 100 | - | 97 |
| 3.0.1 | 2026-01-29 | - | Fix: rename FORMS.md→forms.md, add .skillignore | 98 | 88 | 100 | 100 | - | 97 |
| 3.0.0 | 2026-01-28 | - | Merge cosai-risk-analyzer: core_analyzer.py (30+ query methods), 6 CLI commands, gap analysis, persona profiles, exploration_guide.md | 60+ | 70 | ✓ | 100 | - | 77+ |
| 2.0.0 | 2026-01-28 | [#3](https://github.com/totallyGreg/claude-mp/issues/3) | Restructure SKILL.md for conciseness: 539→219 lines, 4585→1892 tokens, action-oriented format, workflow_guide.md reference | 60+ | 70 | ✓ | 100 | - | 77 |
| 1.1.0 | 2026-01-28 | [#2](https://github.com/totallyGreg/claude-mp/issues/2) | Add workflow automation, orchestrator script, bundled schemas, SSL offline fallback | 23 | 70 | ✓ | 100 | - | 71 |
| 1.0.0 | 2026-01-07 | - | Initial release with CoSAI framework integration, risk analysis, and multi-format reporting | 23 | 65 | ✓ | 100 | - | 67 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

