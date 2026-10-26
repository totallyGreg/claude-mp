# macOS 26 and 27 Apps

Platform guidance for Mac apps that support macOS 26 (Tahoe) and macOS 27. When Xcode's own skills are installed (`swiftui-specialist`, `swiftui-whats-new-27`, `app-intents-*`), they are the authority on SwiftUI and App Intents API detail; this file covers the app-level practice around them.

## Contents

- [Supporting two releases](#supporting-two-releases)
- [Liquid Glass](#liquid-glass)
- [What macOS 27 changes for SwiftUI](#what-macos-27-changes-for-swiftui)
- [App icon](#app-icon)
- [Menu bar apps](#menu-bar-apps)
- [Login items](#login-items)
- [Activation and windows](#activation-and-windows)
- [Running other processes](#running-other-processes)
- [Signing and Gatekeeper](#signing-and-gatekeeper)
- [Crash and hang diagnostics](#crash-and-hang-diagnostics)

## Supporting two releases

- Deployment target = the older release (`.macOS(.v26)` / `MACOSX_DEPLOYMENT_TARGET = 26.0`). Build with the newest Xcode.
- Gate 27-only API with `if #available(macOS 27, *)` / `@available(macOS 27, *)`. Most new SwiftUI API in the 27 SDK does not back-deploy.
- Build a **canary** at deployment target 27 in CI or the merge gate: deprecation warnings only fire at the target you build for, so a build at 26 can't see what 27 deprecates.
- Swift 6.4's `@available(anyAppleOS 27, *)` replaces a list of same-numbered platforms; use it only once the floor compiler is 6.4.

## Liquid Glass

macOS 26 introduced Liquid Glass; macOS 27 refreshes its materials and typography. Apps built with the current SDK pick both up automatically through standard controls — toolbars, sidebars, sheets, menus, buttons, tab and navigation bars.

Do:

- Use standard containers (`NavigationSplitView`, `.toolbar`, `.inspector`, sheets) and let the system draw them.
- Let content extend under the sidebar and toolbar; use `.backgroundExtensionEffect()` for imagery that should continue beneath the sidebar.
- For custom floating controls, use `.glassEffect()` (optionally `.glassEffect(.regular.interactive(), in: .capsule)`), group neighbours in a `GlassEffectContainer` so they blend and morph, and use `.buttonStyle(.glass)` / `.buttonStyle(.glassProminent)` for buttons.
- Use `ToolbarSpacer` to split toolbar items into groups rather than custom backgrounds.

Don't:

- Paint `.background(.thickMaterial)`, `.ultraThinMaterial`, a solid color, or a custom `NSVisualEffectView` behind toolbars, sidebars or the window chrome — it covers the system glass and looks wrong on both 26 and 27.
- Put glass on glass (a glass button inside a glass panel); one layer of glass per element.
- Hard-code colors for text on glass; use semantic styles (`.primary`, `.secondary`, `.tint`) so vibrancy and the inactive-window appearance work.

Check appearance with Xcode Previews (rendered, not read) in light, dark, and an inactive window.

## What macOS 27 changes for SwiftUI

From Apple's WWDC26 material; confirm exact API in the SDK or Xcode's `swiftui-whats-new-27` skill before use:

- `@State` is now a macro; a class stored in `@State` is initialized lazily. Code that relied on the initializer running eagerly changes behavior. This is also why `@State` fails to build with only the Command Line Tools ([project_tooling.md](project_tooling.md#command-line-tools-only-builds)).
- Faster builds from a reworked view builder (`ContentBuilder`).
- A new document API with direct disk access; reorderable containers beyond `List`; toolbar item visibility priorities; swipe actions in any `ScrollView`; `AsyncImage` HTTP caching by default.
- Xcode 27 runs only on Apple silicon.

## App icon

Use an Icon Composer `.icon` file (Xcode 26+) instead of an `AppIcon` image set: layered artwork that the system renders in default, dark, tinted and clear appearances. Add the `.icon` file to the target and set the app icon name (`ASSETCATALOG_COMPILER_APPICON_NAME`) to its name. Keep a 1024 px master for DMG `.icns` and marketing.

## Menu bar apps

```swift
@main
struct BudgetApp: App {
    @State private var model = BudgetModel()

    var body: some Scene {
        MenuBarExtra("Budget", systemImage: "chart.pie") {
            BudgetPanel(model: model)
        }
        .menuBarExtraStyle(.window)       // a panel; `.menu` (default) renders a plain menu

        Settings { SettingsView(model: model) }
    }
}
```

- Menu-bar-only app: set `LSUIElement` (Application is agent) to `YES` — no Dock icon or main menu.
- `MenuBarExtra(isInserted:)` controls whether the item is in the menu bar, not whether its panel is open; SwiftUI has no API to open or close the panel programmatically. If you need that, use an `NSStatusItem` with an `NSPopover`/`NSPanel` instead.
- An agent app is not active when its panel opens. Before opening a window or settings from the panel, call `NSApp.activate()`, otherwise the window appears behind other apps. Open settings with `@Environment(\.openSettings)`.
- In `.window` style, panel size follows the content's ideal size; give the root view an explicit `.frame(width:)` to stop it resizing as content changes.
- Keep the panel's work light; refresh data on a timer or `Observations` in the model, not in `body`.

## Login items

```swift
import ServiceManagement

func setLaunchAtLogin(_ enabled: Bool) throws {
    let service = SMAppService.mainApp
    if enabled {
        try service.register()
    } else {
        try service.unregister()
    }
}

// Reflect the real state, not a stored preference: the user can change it in System Settings.
var launchAtLoginStatus: SMAppService.Status { SMAppService.mainApp.status }
```

- `.requiresApproval` means the user must allow it: call `SMAppService.openSystemSettingsLoginItems()`.
- Read `status` when the settings view appears; don't cache it in `UserDefaults`.
- Helpers and agents use `SMAppService.loginItem(identifier:)` / `.agent(plistName:)`. The old `SMLoginItemSetEnabled` and LaunchAgents written into `~/Library` are legacy.

## Activation and windows

- `NSApp.activate()` (macOS 14+) replaces the deprecated `NSApp.activate(ignoringOtherApps:)`. Activation is now cooperative: the system may decline if the user is working elsewhere.
- Open windows with `@Environment(\.openWindow)` and `WindowGroup(id:)` / `Window(_:id:)`; use `Window` for a single-instance utility window.
- Respect state restoration; give scenes stable IDs.

## Running other processes

Prefer the `Subprocess` package (swift-subprocess) for new code — it is async-native. With `Foundation.Process`:

- Never call `waitUntilExit()` from async code; it blocks a cooperative-pool thread. Await `terminationHandler` through a continuation.
- Read pipes on a GCD queue or with `readabilityHandler`, not from a concurrency-pool task, and start the readers only after `run()` succeeds.
- Read stdout and stderr concurrently, or a full pipe buffer deadlocks the child.
- On timeout, kill the whole process group, not just the child.
- An app launched from Finder gets a minimal `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`). Resolve tools to absolute paths; never assume Homebrew is on `PATH`.

## Signing and Gatekeeper

- Distribution outside the App Store: Developer ID Application certificate, hardened runtime, notarize with `notarytool`, staple. See [project_tooling.md](project_tooling.md#release-signing-and-notarization).
- Since macOS 15, a downloaded app that is ad-hoc signed or not notarized can no longer be opened with Control-click → Open; the user must allow it in System Settings → Privacy & Security → Open Anyway. Notarize anything you hand to someone else.
- Entitlements that need a provisioning profile (iCloud/CloudKit, App Groups, some keychain sharing) require an Apple Development or Developer ID certificate; ad-hoc signing silently drops them.

## Crash and hang diagnostics

- `~/Library/Logs/DiagnosticReports/<App>-<date>.ips` holds crash reports; the first line is JSON metadata, the rest a JSON body (`exception`, `threads[].triggered`, `usedImages`).
- Check `app_version` and `procPath` before debugging: a crash from an old copy of the app (an earlier install, a stale DerivedData build) is not a crash in HEAD.
- MetricKit delivers crash and hang payloads to the app on its next launch; persist them to an app-specific diagnostics folder.
- Under the Xcode debugger, a Swift runtime trap *pauses* the process rather than crashing it; an app that "stops responding" during a debug run is often a trap — `sample <pid>` shows where.
