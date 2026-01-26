---
name: swift-dev
description: Expert guidance for Swift development including SwiftUI, iOS/macOS frameworks, Server-side Swift, and Objective-C to Swift 6 migration. Use when developing Swift applications, working with Apple frameworks, building server-side Swift apps, or modernizing legacy Objective-C codebases to Swift 6. Supports Swift 5.0-6.0 with version annotations and live documentation fetching.
metadata:
  version: "1.2.0"
  license: "MIT"
  compatibility: ">=5.0"
---

# Swift Development Expert

Expert guidance for modern Swift development across all Apple platforms and server-side applications. Leverage idiomatic Swift patterns, type safety, and modern concurrency for production-ready code.

## Quick Start

When to use this skill:
- **SwiftUI Development**: Building modern declarative UIs for Apple platforms
- **Language Features**: Using async/await, actors, generics, and modern Swift patterns
- **Frameworks**: Integrating with Combine, Core Data, CloudKit, StoreKit, URLSession
- **Server-Side**: Building backend APIs with Vapor, Fluent ORM, Swift NIO
- **Migration**: Modernizing legacy Objective-C to Swift 6

## Core Capabilities

### 1. SwiftUI Development

Declarative UI framework for all Apple platforms (iOS, macOS, watchOS, tvOS).

**Key Areas:**
- **State Management**: @State, @Binding, @StateObject, @EnvironmentObject, @Environment
- **Navigation**: NavigationStack, NavigationSplitView, TabView, modal presentations
- **Views**: Lists, Forms, Grids, ScrollView, custom modifiers
- **Animations & Transitions**: Interactive, spring-based, with async support
- **Gestures**: Tap, long-press, drag, combined gestures
- **Performance**: LazyVStack/LazyHStack, @ViewBuilder, EquatableView

**Deep Dive:** [→ SwiftUI Components Reference](references/swiftui_components.md)

**Key Patterns:**
- State management for responsive UIs: [→ State Management](references/swiftui_components.md#state-management)
- Navigation in iOS 16+: [→ Navigation Stack](references/swiftui_components.md#navigationstack-ios-16)
- Custom view modifiers: [→ View Modifiers](references/swiftui_components.md#view-modifiers)

---

### 2. Swift Language Features

Modern patterns and idioms for idiomatic, type-safe Swift code.

**Core Concepts:**
- **Concurrency** (Swift 5.5+): async/await, actors, structured concurrency, TaskGroups
  - [→ Complete Concurrency Guide](references/swift_concurrency.md)
- **Protocols**: Protocol-oriented programming, extensions, associated types
  - [→ Protocol Examples](references/swift_language_features.md#protocol-oriented-programming)
- **Generics**: Type parameters, constraints, conditional conformance
  - [→ Generics Deep Dive](references/swift_language_features.md#generics-and-associated-types)
- **Property Wrappers** (Swift 5.1+): Custom attribute behavior, projectedValue
  - [→ Property Wrapper Patterns](references/swift_language_features.md#property-wrappers)
- **Result Builders** (Swift 5.4+): DSL creation for view hierarchies
  - [→ Result Builder Guide](references/swift_language_features.md#result-builders)
- **Error Handling**: throws, Result, async/await, typed throws (Swift 6)
  - [→ Error Patterns](references/swift_language_features.md#error-handling-patterns)
- **Availability**: Platform and version annotations
  - [→ Platform Availability](references/swift_language_features.md#platform-availability)

**Version Timeline:**
- Swift 5.5: async/await, actors, structured concurrency
- Swift 5.7: Generics improvements, `if let` shorthand
- Swift 5.9: Macros, parameter packs, @Observable macro
- Swift 6.0: Complete concurrency checking, typed throws

[→ Full Swift Language Features Reference](references/swift_language_features.md)

---

### 3. iOS/macOS Frameworks

Essential Apple platform frameworks for native app development.

**Framework Overview:**

| Framework | Purpose | Use When |
|-----------|---------|----------|
| **Combine** | Reactive programming | Data binding, reactive flows |
| **Core Data** | Local data persistence | Structured data storage, querying |
| **CloudKit** | Cloud sync & sharing | Multi-device sync, collaboration |
| **StoreKit 2** | In-app purchases | Monetization, subscriptions |
| **URLSession** | Networking | API requests, async/await |

**Key Patterns:**

- **Core Data**: @FetchRequest in SwiftUI, background contexts, relationships
  - [→ Core Data Setup & Usage](references/ios_macos_frameworks.md#core-data)

- **CloudKit**: Database management, subscriptions, record sharing
  - [→ CloudKit Guide](references/ios_macos_frameworks.md#cloudkit)

- **StoreKit 2**: Product loading, purchase flows, transaction handling
  - [→ Modern In-App Purchases](references/ios_macos_frameworks.md#storekit-2)

- **URLSession**: Async/await networking, error handling
  - [→ Networking Patterns](references/ios_macos_frameworks.md#urlsession-and-networking)

- **Combine**: Publishers, operators, subscribers
  - [→ Combine Framework](references/combine_framework.md)

[→ Complete iOS/macOS Frameworks Guide](references/ios_macos_frameworks.md)

---

### 4. Server-Side Swift

Backend services with Vapor, Fluent ORM, and Swift NIO.

**Frameworks:**

- **Vapor**: Web framework with routing, middleware, async/await
  - REST API endpoints, middleware stack, authentication, validation
  - [→ Vapor Framework Guide](references/server_side_frameworks.md#vapor-framework)

- **Fluent ORM**: Type-safe database interaction
  - Model definitions, relationships, migrations, querying
  - [→ Fluent ORM Reference](references/server_side_frameworks.md#fluent-orm)

- **Swift NIO**: Low-level async networking
  - Custom protocols, EventLoopFuture, channel handlers
  - [→ Swift NIO Guide](references/server_side_frameworks.md#swift-nio)

**Databases:** PostgreSQL, MongoDB, Redis, SQLite
**Deployment:** Docker, Kubernetes, environment configuration

[→ Complete Server-Side Frameworks Guide](references/server_side_frameworks.md)

---

### 5. Objective-C Migration

Modernize legacy Objective-C to Swift 6.

**Migration Strategy (5 Phases):**

1. **Assessment** - Use `scripts/migration_analyzer.py` to identify opportunities
2. **Foundation** - Migrate models and utilities first
3. **Swift 6 Modernization** - GCD → Task, locks → actors, KVO → @Observable
4. **UI Layer** - Update views incrementally with MainActor
5. **Polish** - Enable complete concurrency checking

**Key Modernizations:**

- **Concurrency**: From GCD (dispatch_async, queues) to Task-based structured concurrency
  - [→ Concurrency Migration](references/objc_to_swift6_migration.md#concurrency-migration)

- **Data Flow**: From KVO to @Observable macro, NSNotificationCenter to AsyncStream
  - [→ Data Flow Migration](references/objc_to_swift6_migration.md#data-flow-state)

- **Interoperability**: Bridging headers, @objc exposure, nullability
  - [→ Objective-C Interop](references/objc_interop.md)

[→ Complete Migration Guide](references/objc_to_swift6_migration.md)
[→ Bridging & Interop Patterns](references/objc_interop.md)

---

## Response Guidelines

### Initial Assessment Questions

When helping with Swift development, clarify:
1. **Target platform(s)**: iOS, macOS, watchOS, tvOS, server
2. **Minimum Swift version**: Language features depend on Swift version
3. **Deployment target**: iOS 15+, macOS 12+, etc.
4. **Architecture**: SwiftUI vs UIKit/AppKit, MVVM vs other patterns

### Code Quality Standards

Follow these principles:
- **[Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)**: Naming, parameter labels, clarity
- **Access Control**: private, fileprivate, internal, public appropriately
- **Type Safety**: Leverage Swift's type system, avoid force unwrapping
- **Error Handling**: Use throws, Result, or optionals appropriately
  - [→ Error Handling Patterns](references/swift_language_features.md#error-handling-patterns)
- **Testability**: Dependency injection, modular design
  - [→ Design Patterns](references/design_patterns.md)

### Design Patterns

Proven architectural approaches for maintainable code:

- **MVVM**: Model-View-ViewModel for SwiftUI apps
  - [→ MVVM Pattern](references/design_patterns.md#mvvm-with-swiftui)

- **Dependency Injection**: Constructor, property, method injection
  - [→ DI Patterns](references/design_patterns.md#dependency-injection)

- **Repository Pattern**: Abstract data access, swap implementations
  - [→ Repository Pattern](references/design_patterns.md#repository-pattern)

- **Coordinator**: Navigation and flow management
  - [→ Coordinator Pattern](references/design_patterns.md#coordinator-pattern)

[→ Complete Design Patterns Guide](references/design_patterns.md)

### Testing Approach

- **Unit Tests**: Test business logic with XCTest
- **Async Tests**: `async throws` test functions
- **Test Doubles**: Mocks, stubs, fakes for dependencies
- **TDD**: Test-driven development workflows

[→ Testing Strategies](references/testing_strategies.md)

---

## Reference Library

Complete guides organized by category:

### Language & Patterns
- **[Swift Language Features](references/swift_language_features.md)** - Protocols, generics, property wrappers, error handling, version management
- **[Swift Concurrency](references/swift_concurrency.md)** - async/await, actors, TaskGroups, async sequences, structured concurrency
- **[Design Patterns](references/design_patterns.md)** - MVVM, DI, Repository, Coordinator, composition patterns

### Frameworks
- **[SwiftUI Components](references/swiftui_components.md)** - Views, modifiers, navigation, animations, gestures, state management
- **[iOS/macOS Frameworks](references/ios_macos_frameworks.md)** - Core Data, CloudKit, StoreKit 2, URLSession, framework overview
- **[Combine Framework](references/combine_framework.md)** - Publishers, operators, subscribers, reactive patterns

### Platform-Specific
- **[Server-Side Frameworks](references/server_side_frameworks.md)** - Vapor, Fluent ORM, Swift NIO, WebSockets, authentication
- **[Swift Package Manager](references/swift_package_manager.md)** - Package configuration, dependencies, multi-target projects
- **[Testing Strategies](references/testing_strategies.md)** - XCTest, mocking, async testing, TDD approaches

### Migration & Interop
- **[Objective-C to Swift 6 Migration](references/objc_to_swift6_migration.md)** - Comprehensive guide with concurrency, data flow, and pattern translations
- **[Objective-C Interop](references/objc_interop.md)** - Bridging headers, @objc exposure, nullability, blocks to closures

---

## Tools & Resources

### Scripts

- **`scripts/migration_analyzer.py`** - Analyze Objective-C code for Swift 6 opportunities
  - Detects legacy concurrency patterns, KVO usage, error handling patterns
  - Provides specific migration recommendations

- **`scripts/swift_package_init.py`** - Initialize Swift Package Manager projects
  - Sets up Package.swift, directory structure, git configuration

### Templates

- **SwiftUI app** - Complete app template with MVVM architecture
- **Vapor server** - REST API boilerplate with database integration
- **Package** - Swift Package Manager library template

---

## Accessing Official Documentation

Use WebFetch to retrieve current Swift documentation:

- **[Swift Language Guide](https://docs.swift.org/swift-book/)** - Official language reference
- **[Apple Frameworks](https://developer.apple.com/documentation/)** - Platform framework documentation
- **[Vapor Docs](https://docs.vapor.codes/)** - Server-side Swift framework
- **[Swift Evolution](https://github.com/apple/swift-evolution)** - Language proposals and changes

Use WebFetch when asking about latest API changes, feature availability, or official best practices.

---

**Development Philosophy:**
Write idiomatic Swift that leverages type safety, optionals, and protocol-oriented design. Prefer value types (struct, enum) over reference types unless reference semantics are needed. Use modern async/await concurrency, avoid legacy GCD patterns, and apply @MainActor for UI code.
