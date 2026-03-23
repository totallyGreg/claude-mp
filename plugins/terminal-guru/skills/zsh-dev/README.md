# zsh-dev

Zsh-dev is a focused skill for creating, testing, and optimizing Zsh shell configurations. It helps developers author autoload functions following established patterns, manage fpath and completion system setup, and safely experiment with configuration changes using a Python-based isolated testing framework. It also covers macOS keychain secret management via the `keychainctl` CLI, making it the go-to skill for both day-to-day zsh function authorship and deeper shell performance work.

## Capabilities

- Generate zsh autoload functions using established patterns (subcommand dispatchers, xargs modularity, keychain integration, async operations)
- Configure and troubleshoot fpath, compinit, and completion system setup
- Create isolated ZDOTDIR test environments to validate config changes without touching the live shell
- Run automated performance and plugin compatibility test suites and compare before/after results
- Store and retrieve macOS keychain secrets securely via `keychainctl` (get, set, rm, ls)
- Debug slow shell startup using profiling tools and apply lazy-loading optimizations
- Validate zsh function compliance with Plugin Standard conventions

## Current Metrics

*Last evaluated: 2026-03-22*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 95/100 | Excellent |
| Complexity | 77/100 | Fair |
| Spec Compliance | 80/100 | Good |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **88/100** | **Good** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 3.0.0 | 2026-02-09 | [#40](https://github.com/totallyGreg/claude-mp/issues/40) | Split from terminal-guru monolith into focused zsh-dev skill within plugin | 80 | 78 | 80 | 100 | - | 81 |
| 2.1.0 | 2026-02-08 | #12 | Add zsh function patterns, completion guide, and Plugin Standard references | 33 | 66 | 80 | 100 | - | 69 |
| 2.0.0 | 2025-11-20 | - | Initial release with terminal diagnostics and zsh configuration support | 20 | 66 | 80 | 100 | - | 66 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="zsh-dev"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
