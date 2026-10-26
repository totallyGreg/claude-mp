# Project Tooling

Toolchain, build gates, linting, launching and releasing a Swift app on macOS 26/27. The patterns come from a production SwiftPM + Xcode macOS app; adapt names, keep the invariants.

## Contents

- [Pin the toolchain](#pin-the-toolchain)
- [Warnings are errors](#warnings-are-errors)
- [Task runner](#task-runner)
- [Build products outside iCloud](#build-products-outside-icloud)
- [swift format](#swift-format)
- [Ratchets](#ratchets)
- [Editor and agent diagnostics](#editor-and-agent-diagnostics)
- [Launch the binary you just built](#launch-the-binary-you-just-built)
- [Release: signing and notarization](#release-signing-and-notarization)
- [Command Line Tools only builds](#command-line-tools-only-builds)

## Pin the toolchain

Call `/usr/bin/swift` (the `xcrun` shim for the selected Xcode), never a bare `swift` that `PATH` might resolve to a stale Command Line Tools or a swiftly toolchain. A toolchain that doesn't match the SDK fails with module and SDK mismatch errors that look like code bugs.

```bash
xcode-select -p                 # which developer dir the shims use
xcrun --find swift              # which swift that resolves to
/usr/bin/swift --version
```

## Warnings are errors

In every build, including CI and the pre-merge gate:

```bash
/usr/bin/swift build -Xswiftc -warnings-as-errors
xcodebuild … SWIFT_TREAT_WARNINGS_AS_ERRORS=YES build
```

For finer control, SwiftPM 6.2 has `.treatAllWarnings(as: .error)` and `.treatWarning("DeprecatedDeclaration", as: .warning)` on `SwiftSetting`; Swift 6.4's `@diagnose` attribute scopes an exception to one declaration instead of the whole target. A single, documented exception beats a global downgrade.

## Task runner

Give every command one name so humans and agents run the same thing. A `mise.toml` example:

```toml
[env]
SWIFT = "/usr/bin/swift"
LATEST_MACOS = "27.0"          # bump when a new macOS ships
SCRATCH = "{{env.HOME}}/Library/Developer/MyApp/build/{{config_root | basename}}"

[tasks.build]
run = '$SWIFT build --scratch-path "$SCRATCH" -Xswiftc -warnings-as-errors'

[tasks.test]
depends = ["build"]
run = '$SWIFT test --scratch-path "$SCRATCH" -Xswiftc -warnings-as-errors'

[tasks."app:build"]
run = 'xcodebuild -scheme MyApp -configuration Debug SWIFT_TREAT_WARNINGS_AS_ERRORS=YES build'

[tasks."app:test"]
depends = ["app:build"]          # `build` alone never compiles the test bundle
run = 'xcodebuild test -scheme MyApp -only-testing:MyAppTests SWIFT_TREAT_WARNINGS_AS_ERRORS=YES'

[tasks."app:canary"]             # sees what the newest SDK deprecates
run = 'xcodebuild -scheme MyApp MACOSX_DEPLOYMENT_TARGET=$LATEST_MACOS SWIFT_TREAT_WARNINGS_AS_ERRORS=YES -derivedDataPath "$HOME/Library/Developer/Xcode/DerivedData/MyApp-canary" build'

[tasks.lint]
run = '$SWIFT format lint --strict --recursive Package.swift Sources Tests'

[tasks.gate]                     # the merge gate: all green or no merge
depends = ["lint", "test", "app:test", "app:canary"]
```

Notes:

- The canary gets its own derived data so it doesn't invalidate the normal build cache.
- Keep UI automation tests (they take over the screen) out of the gate; run them on demand.
- Give long test runs a hang limit that fails by test name, not a silent CI timeout.

## Build products outside iCloud

A repo in an iCloud-synced folder (`~/Documents`, `~/Desktop`) gets FinderInfo extended attributes added to build products mid-build, and `codesign` refuses them (`resource fork, Finder information, or similar detritus not allowed`). Symptoms are random test-bundle signing failures and "file modified during the build".

- Put SwiftPM's scratch path outside the synced tree: `--scratch-path ~/Library/Developer/<App>/build/<checkout>`. One per checkout or worktree, so parallel builds don't wait on each other's lock.
- Xcode's DerivedData is already outside; keep it that way.
- Mark the repo folder "Keep Downloaded" in Finder to stop eviction under it.

## swift format

`swift format` ships with the toolchain (Xcode and Command Line Tools). Check in a `.swift-format` and lint with `--strict` so lint findings fail the gate:

```json
{
  "version": 1,
  "lineLength": 120,
  "indentation": { "spaces": 4 },
  "rules": {
    "AlwaysUseLiteralForEmptyCollectionInit": true,
    "NeverForceUnwrap": true,
    "NeverUseForceTry": true,
    "NeverUseImplicitlyUnwrappedOptionals": true,
    "NoEmptyLinesOpeningClosingBraces": true,
    "OmitExplicitReturns": true,
    "UseEarlyExits": true,
    "UseWhereClausesInForLoops": true,
    "ValidateDocumentationComments": true
  }
}
```

- Hold tests to the same rules; if a test tree needs an exception (say, `!` on a fixture), keep a separate `.swift-format` in that tree and a check that the copies differ only by the named exceptions.
- Per-line exception: `// swift-format-ignore: NeverForceUnwrap` on the line above, with the reason.
- `swift format --in-place --recursive …` fixes layout; run it before committing.

## Ratchets

For costs you can count but can't remove today — `@unchecked Sendable`, `nonisolated(unsafe)`, `@preconcurrency` imports, files over N lines, app-hosted tests — keep the counts in a checked-in file and fail the build when any count grows. The number can only fall, and the failure names the file that grew it.

## Editor and agent diagnostics

- `sourcekit-lsp` ships with Xcode (`xcrun --find sourcekit-lsp`). A `.sourcekit-lsp/config.json` that turns on background indexing and passes `-warnings-as-errors` gives the same errors as the package build in seconds.
- It indexes SwiftPM targets from `Package.swift`. An `.xcodeproj` app target needs `xcode-build-server` to be indexed; otherwise use Xcode (or its MCP bridge's code-issue refresh) for app-target files and `xcodebuild` as the truth.
- Xcode 27 ships agent skills (SwiftUI, App Intents, accessibility, test modernization); link them into a project's `.claude/skills/` rather than copying, and re-link after an Xcode update.

## Launch the binary you just built

Guessing the app's path (`find DerivedData -name MyApp.app | head -1`) launches whatever build the filesystem lists first — on a machine with many DerivedData folders, often one weeks old. A run script should:

1. Resolve the product from the build system:
   ```bash
   products=$(xcodebuild -scheme MyApp -configuration Debug -showBuildSettings 2>/dev/null |
     awk -F' = ' '/ BUILT_PRODUCTS_DIR /{print $2; exit}')
   ```
2. Refuse a binary older than the newest tracked source file (or HEAD's commit time).
3. Quit other running copies first (Cmd-Q via AppleScript, then kill after a timeout) — otherwise `open` just activates the old one.

The same applies when reading a crash report: check `app_version` and the process path before debugging HEAD.

## Release: signing and notarization

Outside the App Store:

```bash
xcodebuild archive -scheme MyApp -configuration Release -archivePath build/MyApp.xcarchive
xcodebuild -exportArchive -archivePath build/MyApp.xcarchive \
  -exportOptionsPlist ExportOptions.plist -exportPath build/export   # method: developer-id

ditto -c -k --keepParent build/export/MyApp.app build/MyApp.zip
xcrun notarytool submit build/MyApp.zip --keychain-profile MyApp --wait
xcrun stapler staple build/export/MyApp.app

hdiutil create -volname MyApp -srcfolder build/export -ov -format UDZO build/MyApp.dmg
codesign --force --timestamp --sign "Developer ID Application: …" build/MyApp.dmg
xcrun notarytool submit build/MyApp.dmg --keychain-profile MyApp --wait
xcrun stapler staple build/MyApp.dmg

codesign --verify --strict build/export/MyApp.app
spctl -a -t open --context context:primary-signature -v build/MyApp.dmg
```

- One-time setup: a Developer ID Application certificate, and `xcrun notarytool store-credentials MyApp --apple-id … --team-id … --password <app-specific>`.
- Stamp the marketing version and bump the build number for every build handed to anyone; tag the release commit.
- Fail the release, not just warn, when signing or notarization fails. Ad-hoc signed builds can't be opened by double-click on another Mac since macOS 15 ([macos_apps.md](macos_apps.md#signing-and-gatekeeper)).
- Apps using CloudKit: deploy the schema to Production before shipping a model change; only additive optional fields are safe.

## Command Line Tools only builds

A teammate with only the Command Line Tools (no Xcode) can build packages, with limits. Verified on CLT 27.0 with Swift 6.4 (`DEVELOPER_DIR=/Library/Developer/CommandLineTools`):

| Works | Fails or flaky |
|---|---|
| `swift build`, `swift test` on SwiftPM packages | Any `.xcodeproj` / `xcodebuild` |
| `swift-tools-version: 6.2`, `.defaultIsolation(MainActor.self)`, `NonisolatedNonsendingByDefault`, `InferIsolatedConformances` | `@State` — the SwiftUI macro plugin isn't shipped: `external macro implementation type 'SwiftUIMacros.StateMacro' could not be found` |
| `@Observable` (Observation macros ship with CLT) | Swift Testing macros intermittently: `plugin for module 'TestingMacros' not found` — add the plugin path ([swift_testing.md](swift_testing.md#command-line-tools-only)) |
| `swift format` (`/Library/Developer/CommandLineTools/usr/bin/swift-format`) | Previews, asset catalogs, Icon Composer icons, signing with entitlements |

Design for it:

- Keep view state in `@Observable` models passed in, not `@State`, in any target that must build under CLT.
- Put logic in packages that don't need SwiftUI macros; keep the Xcode app target thin.
- Not verified: CLT 26. Check `pkgutil --pkg-info=com.apple.pkg.CLTools_Executables` for the installed version before assuming.
