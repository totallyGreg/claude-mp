# Swift Package Manager Reference

Comprehensive guide to Swift Package Manager (SPM) for dependency management and package creation.

## Package.swift Structure

### Basic Package

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyLibrary",
    platforms: [
        .iOS(.v15),
        .macOS(.v12),
        .watchOS(.v8),
        .tvOS(.v15)
    ],
    products: [
        .library(
            name: "MyLibrary",
            targets: ["MyLibrary"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),
    ],
    targets: [
        .target(
            name: "MyLibrary",
            dependencies: ["Alamofire"]
        ),
        .testTarget(
            name: "MyLibraryTests",
            dependencies: ["MyLibrary"]
        ),
    ]
)
```

### Package Components

**Platforms**: Specify minimum deployment targets
```swift
platforms: [
    .iOS(.v15),
    .macOS(.v12),
    .watchOS(.v8),
    .tvOS(.v15),
    .visionOS(.v1) // Swift 5.9+
]
```

**Products**: What the package exposes
```swift
products: [
    // Library (static or dynamic)
    .library(
        name: "MyLibrary",
        type: .static, // or .dynamic
        targets: ["MyLibrary"]
    ),

    // Executable
    .executable(
        name: "MyTool",
        targets: ["MyTool"]
    ),

    // Plugin (Swift 5.6+)
    .plugin(
        name: "MyPlugin",
        targets: ["MyPlugin"]
    )
]
```

**Dependencies**: External packages
```swift
dependencies: [
    // Version-based
    .package(url: "https://github.com/user/Package.git", from: "1.0.0"),
    .package(url: "https://github.com/user/Package.git", .upToNextMajor(from: "1.0.0")),
    .package(url: "https://github.com/user/Package.git", .upToNextMinor(from: "1.0.0")),
    .package(url: "https://github.com/user/Package.git", exact: "1.0.0"),
    .package(url: "https://github.com/user/Package.git", "1.0.0"..<"2.0.0"),

    // Branch-based
    .package(url: "https://github.com/user/Package.git", branch: "main"),

    // Revision-based
    .package(url: "https://github.com/user/Package.git", revision: "abc123"),

    // Local path
    .package(path: "../LocalPackage")
]
```

**Targets**: Build units
```swift
targets: [
    // Regular target
    .target(
        name: "MyLibrary",
        dependencies: [
            "Alamofire",
            .product(name: "SwiftProtobuf", package: "swift-protobuf")
        ],
        path: "Sources/MyLibrary",
        exclude: ["README.md"],
        sources: nil, // All Swift files in path
        resources: [
            .process("Resources"),
            .copy("config.json")
        ],
        publicHeadersPath: nil,
        cSettings: [
            .headerSearchPath("include")
        ],
        cxxSettings: [],
        swiftSettings: [
            .define("DEBUG", .when(configuration: .debug))
        ],
        linkerSettings: [
            .linkedFramework("CoreData")
        ]
    ),

    // Test target
    .testTarget(
        name: "MyLibraryTests",
        dependencies: ["MyLibrary"]
    ),

    // Executable target
    .executableTarget(
        name: "MyTool",
        dependencies: ["MyLibrary"]
    ),

    // Plugin target (Swift 5.6+)
    .plugin(
        name: "MyPlugin",
        capability: .buildTool()
    )
]
```

## Directory Structure

```
MyPackage/
├── Package.swift
├── README.md
├── LICENSE
├── Sources/
│   ├── MyLibrary/
│   │   ├── MyLibrary.swift
│   │   └── Models/
│   │       └── User.swift
│   └── MyTool/
│       └── main.swift
├── Tests/
│   └── MyLibraryTests/
│       └── MyLibraryTests.swift
└── Resources/
    └── config.json
```

## Creating a Package

### Initialize New Package

```bash
# Library package
swift package init --type library

# Executable package
swift package init --type executable

# Empty package
swift package init --type empty

# Plugin package (Swift 5.6+)
swift package init --type build-tool-plugin
```

### Package Commands

```bash
# Build package
swift build

# Build for release
swift build -c release

# Run executable
swift run

# Run tests
swift test

# Update dependencies
swift package update

# Resolve dependencies
swift package resolve

# Reset package
swift package reset

# Show dependencies
swift package show-dependencies

# Generate Xcode project (deprecated in favor of direct SPM support)
swift package generate-xcodeproj

# Clean build artifacts
swift package clean

# Archive for distribution
swift build -c release --arch arm64 --arch x86_64

# Describe package
swift package describe --type json
```

## Resources

### Adding Resources (Swift 5.3+)

```swift
.target(
    name: "MyTarget",
    resources: [
        // Process: Optimize and localize
        .process("Assets"),

        // Copy: Copy as-is
        .copy("config.json"),
        .copy("Scripts/setup.sh")
    ]
)
```

### Accessing Resources

```swift
import Foundation

// Bundle for module
let bundle = Bundle.module

// Load resource
if let url = bundle.url(forResource: "config", withExtension: "json") {
    let data = try Data(contentsOf: url)
}

// Image resource
#if canImport(UIKit)
import UIKit
let image = UIImage(named: "logo", in: .module, compatibleWith: nil)
#elseif canImport(AppKit)
import AppKit
let image = Bundle.module.image(forResource: "logo")
#endif
```

## Swift Settings

### Compiler Flags

```swift
.target(
    name: "MyTarget",
    swiftSettings: [
        // Define compile-time flag
        .define("DEBUG", .when(configuration: .debug)),
        .define("RELEASE", .when(configuration: .release)),

        // Define for specific platforms
        .define("IOS_ONLY", .when(platforms: [.iOS])),

        // Unsafe flags
        .unsafeFlags(["-warnings-as-errors"])
    ]
)
```

### Using Compile-Time Flags

```swift
#if DEBUG
print("Debug mode")
#endif

#if RELEASE
print("Release mode")
#endif

#if IOS_ONLY
import UIKit
#endif
```

## Plugins (Swift 5.6+)

### Build Tool Plugin

```swift
// Package.swift
.plugin(
    name: "MyBuildPlugin",
    capability: .buildTool(),
    dependencies: ["MyTool"]
)

// Plugins/MyBuildPlugin/plugin.swift
import PackagePlugin

@main
struct MyBuildPlugin: BuildToolPlugin {
    func createBuildCommands(context: PluginContext, target: Target) async throws -> [Command] {
        guard let target = target as? SourceModuleTarget else {
            return []
        }

        return try target.sourceFiles.map { file in
            let outputPath = context.pluginWorkDirectory
                .appending(file.path.stem + ".generated.swift")

            return .buildCommand(
                displayName: "Generating code for \(file.path.lastComponent)",
                executable: try context.tool(named: "MyTool").path,
                arguments: [file.path, outputPath],
                inputFiles: [file.path],
                outputFiles: [outputPath]
            )
        }
    }
}
```

### Command Plugin

```swift
.plugin(
    name: "FormatCode",
    capability: .command(
        intent: .sourceCodeFormatting(),
        permissions: [
            .writeToPackageDirectory(reason: "Format source files")
        ]
    )
)

// Plugins/FormatCode/plugin.swift
import PackagePlugin

@main
struct FormatCodePlugin: CommandPlugin {
    func performCommand(context: PluginContext, arguments: [String]) async throws {
        let process = Process()
        process.executableURL = try context.tool(named: "swiftformat").path.url
        process.arguments = [context.package.directory.string]

        try process.run()
        process.waitUntilExit()
    }
}
```

## Binary Targets

### XCFramework Distribution

```swift
.binaryTarget(
    name: "MyFramework",
    url: "https://example.com/MyFramework.xcframework.zip",
    checksum: "abc123..."
)

// Or local path
.binaryTarget(
    name: "MyFramework",
    path: "Frameworks/MyFramework.xcframework"
)
```

### Creating XCFramework

```bash
# Build for iOS
xcodebuild archive \
    -scheme MyFramework \
    -archivePath ./build/ios.xcarchive \
    -sdk iphoneos \
    SKIP_INSTALL=NO \
    BUILD_LIBRARY_FOR_DISTRIBUTION=YES

# Build for iOS Simulator
xcodebuild archive \
    -scheme MyFramework \
    -archivePath ./build/ios-simulator.xcarchive \
    -sdk iphonesimulator \
    SKIP_INSTALL=NO \
    BUILD_LIBRARY_FOR_DISTRIBUTION=YES

# Create XCFramework
xcodebuild -create-xcframework \
    -framework ./build/ios.xcarchive/Products/Library/Frameworks/MyFramework.framework \
    -framework ./build/ios-simulator.xcarchive/Products/Library/Frameworks/MyFramework.framework \
    -output ./MyFramework.xcframework

# Zip for distribution
zip -r MyFramework.xcframework.zip MyFramework.xcframework

# Generate checksum
swift package compute-checksum MyFramework.xcframework.zip
```

## Conditional Dependencies

### Platform-Specific Dependencies

```swift
.target(
    name: "MyTarget",
    dependencies: [
        .product(
            name: "AppKit",
            package: "AppKit",
            condition: .when(platforms: [.macOS])
        ),
        .product(
            name: "UIKit",
            package: "UIKit",
            condition: .when(platforms: [.iOS, .tvOS, .watchOS])
        )
    ]
)
```

## Versioning

### Semantic Versioning

```
MAJOR.MINOR.PATCH

Examples:
1.0.0 - Initial release
1.0.1 - Patch (bug fix)
1.1.0 - Minor (new feature, backward compatible)
2.0.0 - Major (breaking change)
```

### Git Tags

```bash
# Create version tag
git tag 1.0.0

# Push tag
git push origin 1.0.0

# List tags
git tag -l

# Delete tag
git tag -d 1.0.0
git push origin :refs/tags/1.0.0
```

## Testing

### Test Dependencies

```swift
.testTarget(
    name: "MyTests",
    dependencies: [
        "MyLibrary",
        .product(name: "XCTVapor", package: "vapor"),
    ]
)
```

### Running Tests

```bash
# Run all tests
swift test

# Run specific test
swift test --filter MyTests.testExample

# Parallel testing
swift test --parallel

# Generate code coverage
swift test --enable-code-coverage

# List tests
swift test --list-tests
```

## Publishing

### Preparing for Release

1. Update version in git tag
2. Update CHANGELOG.md
3. Ensure tests pass
4. Build for release
5. Create GitHub release

```bash
# Validate package
swift build
swift test

# Tag version
git tag 1.0.0
git push origin 1.0.0

# Create release on GitHub
gh release create 1.0.0 --notes "Release notes"
```

### Package Registry (Swift 5.9+)

```bash
# Login to registry
swift package-registry login https://registry.example.com

# Publish package
swift package-registry publish 1.0.0
```

## Advanced Features

### Macro Targets (Swift 5.9+)

```swift
.macro(
    name: "MyMacros",
    dependencies: [
        .product(name: "SwiftSyntaxMacros", package: "swift-syntax"),
        .product(name: "SwiftCompilerPlugin", package: "swift-syntax")
    ]
)

.target(
    name: "MyLibrary",
    dependencies: ["MyMacros"]
)
```

### Conditional Compilation

```swift
#if canImport(UIKit)
import UIKit
#elseif canImport(AppKit)
import AppKit
#endif

#if os(iOS)
// iOS-specific code
#elseif os(macOS)
// macOS-specific code
#endif
```

## Best Practices

1. **Versioning**
   - Use semantic versioning
   - Tag releases properly
   - Maintain CHANGELOG.md

2. **Dependencies**
   - Prefer version ranges over exact versions
   - Regularly update dependencies
   - Use `swift package update` carefully

3. **Testing**
   - Write tests for public APIs
   - Test on all supported platforms
   - Use continuous integration

4. **Documentation**
   - Maintain comprehensive README.md
   - Document public APIs
   - Include usage examples

5. **Structure**
   - Follow standard directory layout
   - Separate concerns into modules
   - Use appropriate access control

6. **Platform Support**
   - Specify minimum platform versions
   - Test on all target platforms
   - Use conditional compilation when needed

7. **Resources**
   - Use .process for localizable resources
   - Use .copy for files that shouldn't be processed
   - Access via Bundle.module

8. **Plugins**
   - Use for code generation
   - Keep plugins simple and focused
   - Document plugin usage

## Common Issues

### Dependency Resolution

```bash
# Reset package resolved file
rm Package.resolved
swift package resolve

# Update specific dependency
swift package update PackageName

# Clear build cache
rm -rf .build
swift package clean
```

### Xcode Integration

```bash
# Open in Xcode
open Package.swift

# Reset Xcode packages
rm -rf ~/Library/Developer/Xcode/DerivedData
```

### Platform Compatibility

```swift
// Check minimum version
@available(iOS 15.0, *)
func modernFeature() {
    // iOS 15+ only
}

// Runtime check
if #available(iOS 15.0, *) {
    modernFeature()
} else {
    legacyFeature()
}
```

## Migration Guide

### From CocoaPods

1. Remove Podfile and Pods directory
2. Create Package.swift
3. Add dependencies
4. Update imports
5. Test thoroughly

### From Carthage

1. Remove Cartfile
2. Create Package.swift
3. Convert dependencies to SPM format
4. Update project settings
5. Test build

## Example Packages

### CLI Tool

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyCLI",
    platforms: [.macOS(.v12)],
    products: [
        .executable(name: "mycli", targets: ["MyCLI"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.2.0"),
    ],
    targets: [
        .executableTarget(
            name: "MyCLI",
            dependencies: [
                .product(name: "ArgumentParser", package: "swift-argument-parser"),
            ]
        ),
    ]
)
```

### Multi-Target Library

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyApp",
    platforms: [.iOS(.v15)],
    products: [
        .library(name: "Core", targets: ["Core"]),
        .library(name: "UI", targets: ["UI"]),
        .library(name: "Networking", targets: ["Networking"]),
    ],
    dependencies: [
        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),
    ],
    targets: [
        .target(
            name: "Core",
            dependencies: []
        ),
        .target(
            name: "UI",
            dependencies: ["Core"]
        ),
        .target(
            name: "Networking",
            dependencies: [
                "Core",
                "Alamofire"
            ]
        ),
        .testTarget(
            name: "CoreTests",
            dependencies: ["Core"]
        ),
        .testTarget(
            name: "NetworkingTests",
            dependencies: ["Networking"]
        ),
    ]
)
```
