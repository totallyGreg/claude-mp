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

**Score: 88/100** (Good) — 2026-03-22

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 95 | 77 | 80 | 100 | 100 |

## Version History

| Version | Date | Issue | Summary | Concs | Complx | Spec | Progr | Descr | Score |
|---------|------|-------|---------|-------|--------|------|-------|-------|-------|
| 3.0.0 | 2026-02-09 | [#40](https://github.com/totallyGreg/claude-mp/issues/40) | Split from terminal-guru monolith into focused zsh-dev skill within plugin | 80 | 78 | 80 | 100 | - | 81 |
| 2.1.0 | 2026-02-08 | #12 | Add zsh function patterns, completion guide, and Plugin Standard references | 33 | 66 | 80 | 100 | - | 69 |
| 2.0.0 | 2025-11-20 | - | Initial release with terminal diagnostics and zsh configuration support | 20 | 66 | 80 | 100 | - | 66 |

**Metric Legend:** Concs=Conciseness, Complx=Complexity, Spec=Spec Compliance, Progr=Progressive Disclosure, Descr=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="zsh-dev"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
