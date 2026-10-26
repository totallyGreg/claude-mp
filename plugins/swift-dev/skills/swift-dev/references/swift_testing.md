# Swift Testing

The default test framework for new Swift code (Xcode 16+, Swift 6+). XCTest remains for UI automation and `measure` performance tests — see [testing_strategies.md](testing_strategies.md).

## Contents

- [Basics](#basics)
- [Expectations](#expectations)
- [Parameterized tests](#parameterized-tests)
- [Traits](#traits)
- [Async code and confirmations](#async-code-and-confirmations)
- [Exit tests and attachments](#exit-tests-and-attachments)
- [Test seams](#test-seams)
- [Rules that keep a suite trustworthy](#rules-that-keep-a-suite-trustworthy)
- [Running](#running)
- [Mixing with XCTest](#mixing-with-xctest)
- [Command Line Tools only](#command-line-tools-only)

## Basics

```swift
import Testing
@testable import Core

@Suite("Chapter parsing")
struct ChapterParserTests {
    let parser = ChapterParser()          // fresh instance per test — no setUp needed

    @Test func parsesNumberedTitle() throws {
        let chapter = try #require(parser.parse("Chapter 12: The Return"))
        #expect(chapter.number == 12)
        #expect(chapter.title == "The Return")
    }
}
```

- A suite is any type; each `@Test` runs on a new instance. Use `init` for setup and `deinit` (make the suite a `final class` or actor) for teardown.
- Tests run **in parallel by default**, in random order. Shared mutable state between tests is a bug.
- Raw identifiers (Swift 6.2) allow readable names: ``@Test func `rejects an empty title`() ``.

## Expectations

| Macro | Use |
|---|---|
| `#expect(a == b)` | Records a failure and continues; the failure message shows both sides |
| `try #require(x)` | Unwraps an optional or stops the test; replaces `XCTUnwrap` |
| `#expect(throws: ParseError.self) { … }` | Expects a specific error type; returns the error for further checks |
| `#expect(throws: Never.self) { … }` | Asserts nothing is thrown |
| `withKnownIssue { … }` | Marks a known failure without disabling the test |

Write the comparison directly (`#expect(items.count == 3)`), not a boolean computed earlier — the macro shows the operands only when it can see them.

## Parameterized tests

```swift
@Test(arguments: [
    ("Chapter 1", 1),
    ("Chapter 01: Prologue", 1),
    ("CHAPTER TWELVE", 12),
])
func parsesNumber(input: String, expected: Int) throws {
    #expect(try #require(ChapterParser().parse(input)).number == expected)
}

@Test(arguments: zip(inputs, expectations))  // pair two collections; two plain collections form a cartesian product
func pairs(input: String, expected: Int) { … }
```

Each argument runs as its own test case and can be re-run individually. Arguments must be `Sendable`.

## Traits

```swift
@Test(.tags(.media), .timeLimit(.minutes(2)))
func decodesLongBook() async throws { … }

@Test(.enabled(if: FileManager.default.fileExists(atPath: fixturePath)))
func readsRealFile() { … }

@Suite(.serialized)                      // this suite's tests run one at a time
struct KeychainTests { … }

extension Tag { @Tag static var media: Self }
```

Use tags to split a fast suite from slow or media tests rather than separate targets where possible. `.serialized` is for a resource that genuinely can't be shared — prefer giving each test its own resource.

## Async code and confirmations

```swift
@Test func reloadPublishesOnce() async throws {
    let model = LibraryModel(catalog: .stub([book]))
    await confirmation(expectedCount: 1) { reloaded in
        model.onReload = { reloaded() }
        try await model.reload()
    }
}
```

- `async` tests just `await`; no expectations or waits.
- `confirmation` replaces `XCTestExpectation` for events that must happen a given number of times (`expectedCount:` accepts a range in Swift 6.1+).
- Use a simulated clock (inject a `Clock`) instead of real sleeps. Never assert on real-time playback timing.

## Exit tests and attachments

Swift 6.2 added both:

```swift
@Test func trapsOnCorruptHeader() async {
    await #expect(processExitsWith: .failure) {
        _ = try? Decoder.decode(corruptHeader)   // runs in a child process
    }
}

@Test func renders() throws {
    let png = try renderSnapshot()
    Attachment.record(png, named: "snapshot.png")  // kept with the test result
}
```

## Test seams

Inject what the code reads from the world:

| Instead of | Inject |
|---|---|
| `UserDefaults.standard` | `UserDefaults(suiteName: UUID().uuidString)` per test, removed in teardown |
| `Date()`, `Task.sleep` | a `Clock` / `() -> Date` closure |
| `FileManager.default` paths, `~/Library`, App Group container | a root `URL` (per-test temp dir) |
| `URLSession.shared` | a protocol or a `URLProtocol` stub |
| environment variables | a configuration value passed in |

A test inside an app-hosted bundle runs *inside the app* — `.standard` there is the developer's live settings. Inject it.

Per-test temp directory:

```swift
@Test func writesSidecar() throws {
    let dir = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
    try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: dir) }
    …
}
```

## Rules that keep a suite trustworthy

- A failing test is evidence about the code first. Never weaken an assertion to pass.
- Don't assert exact strings from OS formatters (`Date.FormatStyle`, `Duration.UnitsFormatStyle`, `.relative`). Their output changes between OS releases — on macOS 27, a `.dateTime` style with weekday, month, day, hour and minute renders `Oct 26, Mon at 12:00 AM`. Test the value, or the properties of the string (contains the year, non-empty), or pin a fixed `Locale` *and* accept that an OS update may still change it.
- Real-file checks (media, large inputs) are a separate, tagged tier — not synthesized fixtures that weaken to "doesn't hang".
- Tests of deleted production code are cost, not coverage — delete them together.

## Running

```bash
swift test                                        # all
swift test --filter CoreTests.ChapterParserTests  # a suite
swift test --filter "ChapterParserTests/parsesNumber"
swift test --skip MediaTests                      # everything but a suite
xcodebuild test -scheme App -only-testing:AppTests
```

`xcodebuild build` does **not** compile test targets; a green build says nothing about the tests.

## Mixing with XCTest

Both frameworks can live in one target. Swift 6.4 (Xcode 27) adds interop: an `XCTAssert` failure inside a Swift Testing test is reported as an issue, and Swift Testing APIs work inside `XCTestCase`. These cross-framework issues are warnings by default; Xcode can promote them to failures. Migrate one file at a time:

| XCTest | Swift Testing |
|---|---|
| `XCTestCase` subclass | `struct` (optionally `@Suite`) |
| `setUp` / `tearDown` | `init` / `deinit` |
| `XCTAssertEqual(a, b)` | `#expect(a == b)` |
| `XCTUnwrap(x)` | `try #require(x)` |
| `XCTAssertThrowsError` | `#expect(throws:)` |
| `XCTestExpectation` + `wait` | `await confirmation { }` |
| `XCTSkip` | `.enabled(if:)` / `.disabled("reason")` |

## Command Line Tools only

On a Mac with only the Command Line Tools (no Xcode), measured on CLT 27.0 with Swift 6.4:

- `import Testing` works, but the `TestingMacros` plugin is not always found (2 of 5 clean runs failed with `plugin for module 'TestingMacros' not found`). Add its path to the test target, only when it exists:

```swift
import Foundation

let cltTestingPlugins = "/Library/Developer/CommandLineTools/usr/lib/swift/host/plugins/testing"
let testSettings: [SwiftSetting] =
    FileManager.default.fileExists(atPath: cltTestingPlugins)
    ? [.unsafeFlags(["-plugin-path", cltTestingPlugins])]
    : []
```

`unsafeFlags` makes a package unusable as a dependency of another package; keep it on test targets only. See [project_tooling.md](project_tooling.md#command-line-tools-only-builds) for the rest of the CLT constraints.
