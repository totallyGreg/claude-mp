# swift-dev

<!-- BEGIN AUTOGEN:overview (managed by skillsmith --update-components; edits overwritten) -->
## What's inside

Current Swift practice for macOS 26/27 apps (Swift 6.2-6.4, Xcode 26/27): approachable concurrency, Swift Testing, Liquid Glass, menu bar apps, toolchain, lint and release tooling

**At a glance:** 1 skill

## Install

```
/plugin marketplace add totallyGreg/claude-mp
/plugin install swift-dev@totally-tools
```
<!-- END AUTOGEN:overview -->

<!-- BEGIN AUTOGEN:components (managed by skillsmith --update-components; edits overwritten) -->
## Components

### Skills (1)

| Skill | Description |
|-------|-------|
| `swift-dev` | What "current" means for a Swift app today, and where the deeper guidance lives. |
<!-- END AUTOGEN:components -->

## Skill: swift-dev

Pull it into Swift projects so code and tooling follow current practice for apps supporting macOS 26 and 27. SKILL.md states the baseline; references carry the depth. Version-specific claims are checked against Swift.org and Apple's notes, not memory.

### Capabilities

- Approachable concurrency setup (`defaultIsolation(MainActor.self)`, `NonisolatedNonsendingByDefault`, `InferIsolatedConformances`), `@concurrent` and `nonisolated(nonsending)`
- Swift Testing first (`@Test`, `#expect`, parameterized tests, traits, seams); XCTest for UI and performance tests
- macOS 26/27 apps: Liquid Glass, macOS 27 SwiftUI changes, `MenuBarExtra`, `SMAppService`, `NSApp.activate()`, Icon Composer, process handling, Gatekeeper
- Tooling: pinned toolchain, warnings as errors, `swift format`, build scratch outside iCloud, merge gate and deprecation canary, launching the right binary, notarization
- Command Line Tools–only builds and their verified limits
- Legacy and adjacent: Combine, Vapor, Objective-C migration

### Current Metrics

**Score: 98/100** (Excellent) — 2026-10-26

| Concs | Complx | Spec | Progr | Descr |
|-------|--------|------|-------|-------|
| 100 | 90 | 100 | 100 | 100 |

### Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 2.0.0 | 2026-10-26 | - | Rebaselined on Swift 6.2–6.4 / macOS 26–27: approachable concurrency, Swift Testing, macOS apps, project tooling and CLT-only references; SKILL.md 263→113 lines | 100 | 90 | 100 | 100 | 100 | 98 |
| 1.2.0 | 2025-01-25 | #19 | Conciseness refactoring: SKILL.md reduced 70% (897→272 lines), all 11 reference files integrated | 82 | 80 | 80 | 100 | - | 84 |
| 1.1.0 | 2025-12-01 | - | Enhanced Objective-C to Swift 6 migration support, improved tooling and dedicated migration guide | - | - | - | - | - | - |
| 1.0.0 | - | - | Initial swift-dev skill with broad coverage of Swift development topics | - | - | - | - | - | - |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)
