# swift-dev

A skill for expert guidance across the full spectrum of Swift development — from building declarative SwiftUI interfaces and adopting modern concurrency (async/await, actors) to deploying server-side APIs with Vapor and modernizing legacy Objective-C codebases to Swift 6. Use it when you need idiomatic, production-ready Swift code that leverages type safety, protocol-oriented design, and Apple platform frameworks. It covers Swift 5.0–6.0 with version-annotated guidance and live documentation fetching via WebFetch.

## Capabilities

- Build declarative SwiftUI interfaces with state management, navigation, animations, and performance-optimized layouts
- Apply modern Swift concurrency patterns (async/await, actors, TaskGroups, structured concurrency) across iOS, macOS, watchOS, and tvOS
- Integrate Apple platform frameworks including Core Data, CloudKit, StoreKit 2, URLSession, and Combine
- Develop and deploy server-side Swift services using Vapor, Fluent ORM, and Swift NIO with PostgreSQL/Redis/MongoDB
- Migrate Objective-C codebases to Swift 6 using a phased strategy with automated analysis via `scripts/migration_analyzer.py`
- Apply architectural patterns (MVVM, Dependency Injection, Repository, Coordinator) and enforce testability with XCTest

## Current Metrics

*Last evaluated: 2026-03-22*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 98/100 | Excellent |
| Complexity | 80/100 | Good |
| Spec Compliance | 80/100 | Good |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 30/100 | Needs work |
| **Overall** | **82/100** | **Good** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 1.2.0 | 2025-01-25 | #19 | Conciseness refactoring: SKILL.md reduced 70% (897→272 lines), all 11 reference files integrated | 82 | 80 | 80 | 100 | - | 84 |
| 1.1.0 | 2025-12-01 | - | Enhanced Objective-C to Swift 6 migration support, improved tooling and dedicated migration guide | - | - | - | - | - | - |
| 1.0.0 | - | - | Initial swift-dev skill with broad coverage of Swift development topics | - | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="swift-dev"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
