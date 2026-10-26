---
name: swift-dev
description: Current Swift and Apple-platform practice for apps on macOS 26 and macOS 27 (Swift 6.2–6.4, Xcode 26/27) — approachable concurrency, Swift Testing, Liquid Glass, menu bar apps, toolchain, linting and release tooling. Use when asked to "set up a Swift project", "review this Swift code", "fix a Swift 6 concurrency error", "write Swift Testing tests", "adopt Liquid Glass", "build a menu bar app", "notarize a Mac app", "build with Command Line Tools only", or "migrate Objective-C to Swift". Do NOT use for Xcode-shipped SwiftUI or App Intents API detail when Apple's own Xcode skills are installed (use swiftui-specialist / app-intents-specialist), or for non-Swift languages.
metadata:
  version: "2.0.0"
license: MIT
compatibility: claude-code. Python scripts need python3; guidance targets Swift 6.2+ and macOS 26+.
---

# Swift Development

What "current" means for a Swift app today, and where the deeper guidance lives. Default to the baseline below unless the project says otherwise; when a project's own `AGENTS.md`/`CLAUDE.md` sets a rule, it wins.

## Baseline

| | Floor | Latest |
|---|---|---|
| macOS | 26 (Tahoe) | 27 |
| Xcode | 26.x (Swift 6.3) | 27.x (Swift 6.4, Apple silicon only) |
| Language mode | Swift 6, with approachable concurrency | |

Support the latest macOS and one back. Build a **deprecation canary** at the newest deployment target — deprecation warnings only fire at the target you build for, so the floor build is blind to them. Gate new APIs with `if #available(macOS 27, *)`; most 27 SwiftUI APIs do not back-deploy.

Before trusting a version-specific claim from memory, check [Swift.org](https://www.swift.org/blog/) or Apple's release notes with WebFetch. Details: [→ Version timeline](references/swift_language_features.md#swift-version-timeline)

## Project setup

```swift
// swift-tools-version: 6.2
import PackageDescription

// Swift 6 mode already includes the rest of approachable concurrency.
let approachableConcurrency: [SwiftSetting] = [
    .enableUpcomingFeature("NonisolatedNonsendingByDefault"),
    .enableUpcomingFeature("InferIsolatedConformances"),
]

let package = Package(
    name: "App",
    platforms: [.macOS(.v26)],
    targets: [
        // UI-facing targets: everything on the main actor unless it says otherwise.
        .target(name: "AppUI", swiftSettings: approachableConcurrency + [.defaultIsolation(MainActor.self)]),
        // Engines and models: nonisolated by default, actors where state is shared.
        .target(name: "Core", swiftSettings: approachableConcurrency),
    ]
)
```

App targets in Xcode: `SWIFT_APPROACHABLE_CONCURRENCY = YES`, `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`, `SWIFT_TREAT_WARNINGS_AS_ERRORS = YES`.

[→ Project tooling](references/project_tooling.md): pinned toolchain, `-warnings-as-errors`, `swift format` rules, build scratch outside iCloud, launching the right binary, notarization, CLT-only builds.

## Concurrency defaults

```swift
@Observable final class LibraryModel {          // main actor by default isolation
    var books: [Book] = []

    func reload() async throws {
        books = try await Catalog.scan(root)    // awaits off-actor work, resumes here
    }
}

enum Catalog {
    @concurrent                                 // explicitly off the caller's actor
    static func scan(_ root: URL) async throws -> [Book] { … }
}
```

- `async` functions run on the caller's actor (`nonisolated(nonsending)`); mark CPU-heavy work `@concurrent`.
- Actors for engines with mutable state; `Sendable` value types across boundaries; no `@unchecked Sendable` without a written reason.
- `Task.detached` and GCD are escapes, not defaults. Never block the cooperative pool (`waitUntilExit`, semaphores, synchronous pipe reads).

[→ Approachable concurrency](references/approachable_concurrency.md) · [→ Concurrency reference](references/swift_concurrency.md)

## Testing

Swift Testing (`import Testing`, `@Test`, `#expect`, `#require`) for all new tests; XCTest only for UI tests and performance `measure`. Swift 6.4 reports XCTest assertions inside Swift Testing (and the reverse), so migrate file by file.

- A test never reads ambient machine state (`UserDefaults.standard`, `~/Library`, the App Group container) — inject it.
- Never weaken an assertion to pass; never assert exact OS-formatted strings.

[→ Swift Testing](references/swift_testing.md) · [→ XCTest, doubles, UI tests](references/testing_strategies.md)

## macOS apps

Liquid Glass comes free with standard controls — don't paint materials over it. `MenuBarExtra`, `SMAppService` login items, `NSApp.activate()`, Icon Composer `.icon`, process handling, Gatekeeper.

[→ macOS 26/27 apps](references/macos_apps.md) · [→ SwiftUI components](references/swiftui_components.md) · [→ Frameworks](references/ios_macos_frameworks.md)

## Code quality

- Follow the [API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/). No `!`, `try!` or IUOs; early exits; value types first.
- `@Observable` over `ObservableObject`; async/await and `Observations` over Combine in new code.
- Prefer Apple frameworks before writing machinery; never name a type identically to an Apple class.
- Doc comments on public API; throw typed, actionable errors.

[→ Language features](references/swift_language_features.md) · [→ Design patterns](references/design_patterns.md)

## Reference library

| Reference | Covers |
|---|---|
| [approachable_concurrency.md](references/approachable_concurrency.md) | Swift 6.2+ isolation defaults, `@concurrent`, isolated conformances, migration |
| [swift_concurrency.md](references/swift_concurrency.md) | async/await, tasks, actors, Sendable, streams |
| [swift_testing.md](references/swift_testing.md) | `@Test`, `#expect`, parameterized tests, traits, seams, CLT caveats |
| [testing_strategies.md](references/testing_strategies.md) | XCTest, test doubles, UI and performance tests |
| [macos_apps.md](references/macos_apps.md) | macOS 26/27: Liquid Glass, menu bar, login items, activation, signing |
| [project_tooling.md](references/project_tooling.md) | Toolchain, lint, gates, run, release, CLT-only builds |
| [swift_language_features.md](references/swift_language_features.md) | Protocols, generics, errors, availability, version timeline |
| [swiftui_components.md](references/swiftui_components.md) | Views, navigation, state |
| [ios_macos_frameworks.md](references/ios_macos_frameworks.md) | SwiftData/Core Data, CloudKit, StoreKit 2, URLSession |
| [swift_package_manager.md](references/swift_package_manager.md) | Package.swift, resources, plugins |
| [design_patterns.md](references/design_patterns.md) | MVVM, DI, repository |
| [combine_framework.md](references/combine_framework.md) | Legacy Combine code |
| [server_side_frameworks.md](references/server_side_frameworks.md) | Vapor, Fluent, NIO |
| [objc_to_swift6_migration.md](references/objc_to_swift6_migration.md) · [objc_interop.md](references/objc_interop.md) | Objective-C migration and bridging (`scripts/migration_analyzer.py`) |

## Official sources

Fetch these rather than trusting memory for anything released after 2025: [Swift blog](https://www.swift.org/blog/) · [Swift Evolution](https://www.swift.org/swift-evolution/) · [Apple documentation](https://developer.apple.com/documentation/) · [Xcode release notes](https://developer.apple.com/documentation/xcode-release-notes).
