
# Skills

Agent Skills extend Claude's capabilities with specialized knowledge and workflows.

## Available Skills

### terminal-guru
**v2.0** - Terminal diagnostics, configuration, testing, and optimization expert. Provides comprehensive diagnostics (terminfo, Unicode, locale), Python-based testing framework with isolated environments (ZDOTDIR), performance profiling, and plugin compatibility validation. Safely test and optimize zsh configurations without affecting your working shell.

**Installation:**
```bash
claude skill install totally-tools/terminal-guru
```

### helm-chart-developer
Expert guide for Helm chart development, testing, security, and OCI registries. Includes Helm 4 migration guidance and best practices.

**Installation:**
```bash
claude skill install totally-tools/helm-chart-developer
```

### skill-creator
Comprehensive guide for creating effective Claude skills with marketplace integration.

**Installation:**
```bash
claude skill install totally-tools/skill-creator
```

### swift-dev
**v1.0.0** - Expert guidance for Swift development including SwiftUI, iOS/macOS frameworks, Server-side Swift, and Objective-C migration. Supports Swift 5.0+ with version annotations and live documentation fetching via WebFetch.

**Features:**
- SwiftUI development patterns (state management, navigation, animations)
- Modern Swift language features (async/await, actors, protocols, generics)
- iOS/macOS frameworks (Combine, Core Data, CloudKit, StoreKit)
- Server-side Swift (Vapor, Swift NIO, Fluent ORM)
- Objective-C migration strategies and interoperability
- Swift Package Manager configuration and best practices
- Comprehensive testing strategies (XCTest, UI testing, TDD)

**Includes:**
- 7 detailed reference documents covering all aspects of Swift development
- Python scripts for migration analysis and package initialization
- SwiftUI and Vapor code templates
- Live documentation fetching from Swift.org and Apple Developer

**Installation:**
```bash
claude skill install totally-tools/swift-dev
```

## Creating Your Own Skills

See the [skill-creator](./skill-creator/) skill for detailed guidance on creating custom skills.
