# XCode and SPM Integration Issues

Comprehensive guide for troubleshooting and preventing common XCode/Swift Package Manager integration problems.

## Overview

Hybrid XCode + SPM projects introduce complexity due to two independent build systems:
- **XCode Projects** (`.xcodeproj`): Traditional IDE projects with UI-based configuration
- **Swift Package Manager** (`Package.swift`): Declarative, CLI-based package definition

When mixed, they can conflict on build schemes, entry points, package resolution, and file indexing.

---

## Common Issues and Solutions

### 1. Package Recognition Issues

**Problem:** New files added to SPM targets aren't recognized in XCode, even though `swift build` works fine.

**Root Cause:** XCode's IDE indexing is separate from the actual build process. Package changes aren't reflected in the IDE's file navigator or autocomplete.

**Solutions (in order of effectiveness):**

1. **Clear XCode's Derived Data** (Most effective ~90%)
   ```bash
   rm -rf ~/Library/Developer/Xcode/DerivedData/*ProjectName*
   ```
   Close and reopen the workspace after clearing.

2. **Reset SPM Package Caches**
   - In XCode: `File > Packages > Reset Package Caches`
   - Command line: `rm -rf .swiftpm/xcode`

3. **Regenerate Package Resolution**
   ```bash
   rm -rf .swiftpm
   swift package resolve
   ```

4. **Full Workspace Regeneration** (Nuclear option)
   ```bash
   rm -rf .swiftpm/xcode AudiobookOCD.xcodeproj
   swift package generate-xcodeproj
   ```

**Prevention:**
- Use `swift build` to verify changes work before expecting IDE recognition
- After adding new files, always clear derived data
- Keep `Package.swift` as the source of truth for file organization

---

### 2. Multiple @main Entry Point Conflicts

**Problem:** Building fails with `'main' attribute cannot be used in a module that contains top-level code` when mixing app and CLI targets.

**Root Cause:** You have two executable entry points (`@main` declarations) but they're being compiled into the same build scheme:
- App target: `@main struct MyApp: App` (SwiftUI)
- CLI target: `@main struct MyCLI: ParsableCommand` (ArgumentParser)

When XCode builds the app scheme, it tries to include the CLI as a library module (not executable), causing the error.

**Example:**
```
AudiobookOCD/
  AudiobookOCDApp.swift      // @main for app
Sources/
  AudiobookCLI/
    main.swift               // @main for CLI executable
```

**Solutions:**

1. **Remove CLI from App's Linked Libraries** (Recommended)
   - In XCode: Select app target → Build Phases → Link Binary With Libraries
   - Remove the CLI executable, keep only library targets
   - The CLI builds separately with `swift build`

2. **Use Separate Schemes**
   - App scheme: builds only the UI app + library dependencies
   - CLI scheme: builds only the CLI executable
   - Both can coexist in the same Package.swift

3. **Create Wrapper CLI in XCode** (if you need single build)
   - Remove `@main` from SPM's main.swift, make it a library
   - Add a CLI target to the XCode project with its own `@main`
   - Have the XCode CLI import the SPM CLI library

**Prevention:**
- Keep app and CLI targets separate and never link them
- Only link library targets to the app
- Use distinct schemes for app vs CLI builds

---

### 3. Hybrid XCode + SPM Package Dependency Conflicts

**Problem:** Adding a local SPM package to an XCode project creates duplicate build definitions that confuse XCode's build system.

**Structure Issues:**
```
Project/
  Package.swift                    # SPM package definition
  AudiobookOCD.xcodeproj/         # XCode project (separate)
  Sources/                         # SPM targets
    AudiobookCore/
    AudiobookCLI/
  AudiobookOCD/                    # XCode app folder
    AudiobookOCDApp.swift
```

**Root Cause:** Two build systems trying to manage the same files:
- `Package.swift` defines targets, dependencies, products
- `.xcodeproj` defines build settings, schemes, linked libraries
- When XCode adds the SPM package, it creates a new scheme for each SPM product

**Solutions:**

1. **Keep Schemes Separate**
   ```
   Schemes:
   - AudiobookOCD      (app only - links to Core, Playback, Persistence)
   - abctl             (CLI only - links to Core, Playback)
   - AudiobookCore     (library development)
   ```
   Don't link the CLI into the app scheme.

2. **Archive Strategy**
   - `File > Add Packages` → Select the Package.swift root directory
   - Select ONLY library targets for the app scheme
   - Don't add executable targets as linked libraries

3. **Use Build Script Phases** (for embedding CLI in app)
   ```bash
   # Add as Build Phase in app target
   cd "${SRCROOT}"
   swift build -c release --product abctl

   mkdir -p "${BUILT_PRODUCTS_DIR}/${EXECUTABLE_FOLDER_PATH}"
   cp ".build/release/abctl" "${BUILT_PRODUCTS_DIR}/${EXECUTABLE_FOLDER_PATH}/"
   ```

**Prevention:**
- When adding SPM packages via "Add Packages", carefully select which products to link
- Never link executable targets to app targets
- Use `swift build` at the command line for executables

---

### 4. Greyed-Out Package Options in XCode

**Problem:** All options under `File > Packages` are greyed out.

**Root Cause:** XCode doesn't recognize the project as an SPM-integrated workspace. This happens when:
- The workspace was created before SPM integration
- The project references a `.xcodeproj` but not the SPM package itself
- The workspace configuration is out of sync

**Solutions:**

1. **Close All XCode Windows**
   ```bash
   # Completely close XCode
   killall Xcode
   ```

2. **Remove and Regenerate Workspace**
   ```bash
   rm -rf AudiobookOCD.xcworkspace
   swift package generate-xcodeproj
   ```

3. **Open the Generated Workspace**
   The new workspace should recognize the SPM integration.

4. **Or: Manually Add Package to Workspace**
   - In workspace settings, add the `Package.swift` path
   - Reopen the workspace

**Prevention:**
- When creating hybrid projects, generate XCode integration from SPM first:
  ```bash
  swift package generate-xcodeproj
  ```
- Then open the generated `.xcworkspace` rather than the `.xcodeproj`

---

### 5. @main Attribute Parsing Errors

**Problem:** Swift compiler error about `@main` being used in a module with top-level code, even though the file structure looks correct.

**Root Cause:** The file is being compiled as a library module instead of as an executable. This happens when:
- The target is configured as a library in XCode
- The file is included in a framework target
- The build system is treating an executable target as a library

**Example Error:**
```
'main' attribute cannot be used in a module that contains top-level code
@main
^
top-level code defined in this source file
import Foundation
^
pass '-parse-as-library' to compiler invocation if this is intentional
```

**Solutions:**

1. **Verify Target Type**
   - Check `Package.swift`: Is it `.executableTarget` or `.target`?
   - `.executableTarget` → can have `@main`
   - `.target` → cannot have `@main`

2. **Check XCode Build Scheme**
   - Make sure the executable isn't linked into another target
   - Remove from "Frameworks, Libraries, and Embedded Content"

3. **Rebuild from Scratch**
   ```bash
   rm -rf .build ~/Library/Developer/Xcode/DerivedData/*ProjectName*
   swift build
   ```

**Prevention:**
- Always use `.executableTarget()` in Package.swift for CLI tools
- Only `@main` one entry point per executable target
- Never link executable targets as dependencies

---

## Build Integration Best Practices

### Project Structure

**Recommended layout for hybrid projects:**
```
Project/
├── Package.swift                 # Source of truth for libraries and CLI
├── Sources/
│   ├── AppCore/                  # Shared library
│   ├── AppUI/                    # Another library (if needed)
│   └── AppCLI/                   # CLI executable
├── Tests/
├── AudiobookOCD.xcodeproj/       # XCode app project (generated/separate)
│   └── AudiobookOCD/             # macOS/iOS app target
├── AudiobookOCD.xcworkspace/     # Generated workspace
└── Documentation/
```

**Key principles:**
- `Package.swift` defines all targets and dependencies
- XCode project manages UI-specific build settings
- Never duplicate target definitions
- SPM handles libraries and executables
- XCode handles UI app and distribution

### File Organization

**Inside Package.swift targets:**
```swift
.target(
    name: "AppCore",
    dependencies: [],
    path: "Sources/AppCore"           // Explicit path
)

.executableTarget(
    name: "AppCLI",
    dependencies: ["AppCore"],
    path: "Sources/AppCLI"
)
```

**Always use explicit `path` parameters** to avoid ambiguity.

### Linking Strategy

**For app targets:**
```swift
// Package.swift - define library products
products: [
    .library(name: "AppCore", targets: ["AppCore"]),
]

// XCode - link to libraries only
// File > Add Packages > select Package.swift
// Select only library products
// Frameworks, Libraries, and Embedded Content:
//   - Add "AppCore"
//   - Do NOT add any executables
```

**For CLI tools:**
```swift
// Package.swift - define executable product
products: [
    .executable(name: "app-cli", targets: ["AppCLI"]),
]

// Build CLI separately
// swift build -c release --product app-cli
// Result: .build/release/app-cli
```

### Scheme Configuration

**Create explicit schemes for clarity:**

1. **App Scheme**
   - Builds: AudiobookOCD app target only
   - Links: Core, Playback, Persistence libraries
   - Output: AudiobookOCD.app

2. **CLI Scheme**
   - Builds: abctl executable
   - Links: Core, Playback, Persistence libraries
   - Output: .build/release/abctl

3. **All Scheme** (optional)
   - Builds: App + CLI sequentially
   - Useful for CI/CD

### Build Script Integration

**For embedding CLI in macOS app:**

Add as "New Run Script Build Phase" in XCode:

```bash
# Build the CLI
cd "${SRCROOT}"
SWIFT_BUILD_DIR="${SRCROOT}/.build/release"
swift build -c release --product abctl

# Create target directory
mkdir -p "${BUILT_PRODUCTS_DIR}/${EXECUTABLE_FOLDER_PATH}"

# Copy binary
CLI_BINARY="${SWIFT_BUILD_DIR}/abctl"
cp "${CLI_BINARY}" "${BUILT_PRODUCTS_DIR}/${EXECUTABLE_FOLDER_PATH}/"

echo "✅ Embedded CLI at: ${BUILT_PRODUCTS_DIR}/${EXECUTABLE_FOLDER_PATH}/abctl"
```

**Placement:** Build Phases → add before "Compile Sources"

---

## Troubleshooting Checklist

When builds fail:

- [ ] Run `swift build` from command line - does it work?
  - Yes: XCode indexing issue, clear derived data
  - No: Actual code issue, fix the error

- [ ] Check for multiple `@main` declarations
  - grep -r "@main" Sources/
  - Should be exactly one per executable target

- [ ] Verify target types in Package.swift
  - Libraries: `.target()`
  - Executables: `.executableTarget()`

- [ ] Check app target's linked libraries
  - Remove any executable targets
  - Keep only library targets

- [ ] Clear all caches
  ```bash
  rm -rf .swiftpm ~/Library/Developer/Xcode/DerivedData/*
  ```

- [ ] Rebuild from scratch
  ```bash
  swift package resolve
  swift build
  ```

- [ ] Close and reopen XCode
  - Sometimes necessary for indexing to catch up

---

## Prevention Strategies

### During Project Setup

1. Generate XCode integration from SPM:
   ```bash
   swift package init --type library
   swift package generate-xcodeproj
   ```

2. Separate app and CLI concerns early
   - Never mix UI and command-line code
   - Create distinct targets for each

3. Use `.xcworkspace` as your XCode entry point
   - Not `.xcodeproj`
   - Workspace knows about SPM integration

### During Development

1. **Always verify with command line first**
   ```bash
   swift build
   swift test
   ```
   Before expecting XCode to work.

2. **Keep Package.swift as source of truth**
   - Don't rely on XCode GUI for target configuration
   - Use explicit `path` parameters

3. **Maintain discipline with linking**
   - Never link executables to app targets
   - Only link libraries

4. **Use version control**
   - Commit `Package.swift` and `*.xcodeproj/` structure
   - This helps track what changed

### CI/CD Integration

Use command line builds for automation:

```bash
# Build libraries
swift build -c release

# Build CLI
swift build -c release --product app-cli

# Build app (if you have XCode automation)
xcodebuild build -scheme AudiobookOCD -configuration Release
```

This avoids XCode-specific quirks in CI environments.

---

## References

- [Swift Package Manager Documentation](https://swift.org/package-manager/)
- [Xcode Build System Documentation](https://developer.apple.com/documentation/xcode)
- [Swift Language Guide - @main](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/attributes#main)
- [SPM Executable Target Configuration](https://developer.apple.com/documentation/packagedescription/target/init(name:dependencies:path:publicheaderspath:sources:resources:publicHeadersPath:linkerSettings:swiftSettings:plugins:))
