# Approachable Concurrency (Swift 6.2+)

Swift 6.2 (Xcode 26) changed the defaults so that ordinary app code is single-threaded until it asks not to be. This is the baseline for new code on macOS 26/27; the older material in [swift_concurrency.md](swift_concurrency.md) still applies to the mechanics (tasks, actors, streams).

## Contents

- [The settings](#the-settings)
- [Default main-actor isolation](#default-main-actor-isolation)
- [nonisolated(nonsending) and @concurrent](#nonisolatednonsending-and-concurrent)
- [Isolated conformances](#isolated-conformances)
- [Choosing isolation per module](#choosing-isolation-per-module)
- [Migrating an existing Swift 6 codebase](#migrating-an-existing-swift-6-codebase)
- [Later releases](#later-releases)

## The settings

| Where | Setting | Effect |
|---|---|---|
| SwiftPM | `.defaultIsolation(MainActor.self)` | Unannotated declarations in the target are `@MainActor` |
| SwiftPM | `.enableUpcomingFeature("NonisolatedNonsendingByDefault")` | Nonisolated `async` functions run on the caller's actor |
| SwiftPM | `.enableUpcomingFeature("InferIsolatedConformances")` | A `@MainActor` type's protocol conformances are main-actor isolated |
| Xcode | `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` | Same as `.defaultIsolation(MainActor.self)` |
| Xcode | `SWIFT_APPROACHABLE_CONCURRENCY = YES` | Turns on the upcoming features above (and the ones Swift 6 mode already implies) |
| Compiler | `-default-isolation MainActor` | The underlying flag |

New Xcode 26+ app projects set both Xcode settings by default. Packages do not: add them per target.

`.defaultIsolation` needs `swift-tools-version: 6.2` or later.

## Default main-actor isolation

With `defaultIsolation(MainActor.self)`, every type, function and global without an explicit isolation is `@MainActor`. That removes most `@MainActor` annotations and most "main actor-isolated property can not be referenced from a nonisolated context" errors in UI code.

Opt out explicitly where code must not be main-actor bound:

```swift
nonisolated struct Chapter: Sendable, Codable {   // a plain value type, usable anywhere
    var title: String
    var start: Duration
}

actor TranscriptionEngine { … }                   // its own isolation
```

`nonisolated` can be applied to a type or extension (Swift 6.1+) so its members inherit it.

## nonisolated(nonsending) and @concurrent

Before 6.2, a nonisolated `async` function always hopped to the global concurrent executor. That meant an `async` helper called from the main actor silently ran off it — and every non-`Sendable` argument became an error.

With `NonisolatedNonsendingByDefault`, a nonisolated `async` function runs **on the caller's actor** (`nonisolated(nonsending)`). To leave the caller's actor deliberately, say so:

```swift
nonisolated enum Decoder {
    // Runs wherever the caller is. Fine for light work and awaiting other async APIs.
    static func header(of url: URL) async throws -> Header { … }

    // Always runs on the concurrent pool. Use for CPU-heavy or blocking-adjacent work.
    @concurrent
    static func decodeAll(_ url: URL) async throws -> [Frame] { … }
}
```

Rules of thumb:

- Reach for `@concurrent` when the work is measurably expensive, not by habit.
- Arguments and results of a `@concurrent` call cross an isolation boundary and must be `Sendable`.
- `Task.detached` is rarely needed now; `@concurrent` on a function says the same thing at the declaration.
- Never block inside the cooperative pool: no `DispatchSemaphore.wait`, `Process.waitUntilExit`, or synchronous `FileHandle.readDataToEndOfFile` in async code. Wrap blocking APIs in a continuation driven from a GCD queue or a dedicated thread.

## Isolated conformances

`InferIsolatedConformances` lets a main-actor type conform to a nonisolated protocol without marking every requirement `nonisolated`:

```swift
@MainActor final class PlayerModel: Equatable {   // conformance is @MainActor-isolated
    static func == (a: PlayerModel, b: PlayerModel) -> Bool { a.id == b.id }
    let id: UUID
}
```

The compiler then refuses to use that conformance off the main actor (for example from a `Sendable` generic context) instead of letting it race. Spell it explicitly with `extension PlayerModel: @MainActor Equatable` when inference isn't on.

## Choosing isolation per module

| Module kind | Default isolation | Why |
|---|---|---|
| App target, SwiftUI views, view models | `MainActor` | UI state is main-actor state; fewer annotations |
| Domain model / persistence | none (`nonisolated`) | Used from engines and views alike; value types + actors |
| Engines (media, network, indexing) | none | Actors own their state; `@concurrent` for heavy work |
| CLI executables | either | `MainActor` is simplest for a single-threaded tool |

Keep the dependency rule: a nonisolated core never imports the main-actor UI module.

## Migrating an existing Swift 6 codebase

1. Turn on `NonisolatedNonsendingByDefault` and `InferIsolatedConformances` first, one target at a time. Build with warnings as errors.
2. Expect behavior changes, not just diagnostics: a nonisolated `async` function that used to run off the main actor now runs on it. Profile anything that was relying on the hop; mark it `@concurrent`.
3. Add `defaultIsolation(MainActor.self)` to UI targets, then delete the now-redundant `@MainActor` annotations.
4. Track the escape hatches (`@unchecked Sendable`, `nonisolated(unsafe)`, `MainActor.assumeIsolated`, `@preconcurrency`) as a number that only falls; each needs a comment saying why it's safe.

## Later releases

- **Swift 6.4:** `defer` bodies can `await` (cleanup that needs async work runs on both return and throw); a `Task` closure whose thrown error is never observed now warns.
- Check the [Swift blog](https://www.swift.org/blog/) for anything newer before relying on memory.
