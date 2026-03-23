# vault-architect

Vault Architect provides expert guidance for designing and evolving Obsidian-based Personal Knowledge Management systems. It solves the problem of vault sprawl and manual filing by helping users create automatic organization through metadata, Templater templates, and Bases queries. Use it when building new PKM structures from scratch or extending an existing vault with new note types, rollup systems, or relationship schemas. It is distinct from vault-curator, which handles maintenance of existing content — vault-architect focuses on creating the structures themselves.

## Capabilities

- Analyze vault organization and provide actionable recommendations using `scripts/analyze_vault.py`
- Design and generate Templater templates with automatic file renaming, movement, and frontmatter population
- Create Bases `.base` query files for dynamic relationships, temporal rollups, and cross-folder aggregation
- Design frontmatter schemas with relationship fields for Bases queries and semantic fields for Excalibrain
- Build temporal rollup systems (daily → weekly → monthly → quarterly → yearly) with embedded Bases views
- Configure QuickAdd workflows for quick capture, CLI automation, Canvas capture, and AI integration
- Establish job-agnostic work organization patterns that survive employer changes

## Current Metrics

*Last evaluated: 2026-03-22*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 98/100 | Excellent |
| Complexity | 80/100 | Good |
| Spec Compliance | 90/100 | Good |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **92/100** | **Good** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 1.3.0 | 2026-03-14 | - | Add Workflow Lookup, Capture, and Refinement section: vault discovery via Workflows.base, Workflow fileClass schema, Capture-to-Review pattern reference; add missing `compatibility` field | 83 | 80 | 90 | 100 | 100 | 89 |
| 1.2.0 | 2026-03-05 | - | SKILL.md restructure: 12 trigger phrases, conciseness fix, structural bug fix (#89) | 83 | 80 | 80 | 100 | 100 | 86 |
| 1.1.1 | 2026-03-05 | - | Comprehensive QuickAdd 2.12.0 reference, SKILL.md section update | 34 | 88 | 80 | 100 | 100 | 78 |
| 1.0.0 | 2025-12-15 | - | Initial release with core PKM guidance | - | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="vault-architect"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
