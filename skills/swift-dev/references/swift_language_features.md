# Swift Language Features

Comprehensive guide to modern Swift patterns, idioms, and language features across Swift 5.0-6.0. This reference covers advanced language capabilities that enable idiomatic, type-safe, and maintainable Swift code.

## Table of Contents

- [Protocol-Oriented Programming](#protocol-oriented-programming)
- [Generics and Associated Types](#generics-and-associated-types)
- [Property Wrappers](#property-wrappers)
- [Result Builders](#result-builders)
- [Error Handling Patterns](#error-handling-patterns)
- [Platform Availability](#platform-availability)
- [Swift Version Timeline](#swift-version-timeline)
- [Documentation Access](#documentation-access)

---

## Protocol-Oriented Programming

Protocol-Oriented Programming (POP) emphasizes protocols and extensions over inheritance, leveraging Swift's powerful protocol system to write flexible, reusable code.

### Basic Protocol Definition with Extensions

```swift
protocol Drawable {
    func draw()
}

extension Drawable where Self: Shape {
    func draw() {
        print("Drawing shape with area: \(area)")
    }
}

protocol Shape {
    var area: Double { get }
}

struct Circle: Shape, Drawable {
    let radius: Double

    var area: Double {
        .pi * radius * radius
    }
}
```

### When to Use POP

- **Code reuse**: Share behavior across unrelated types
- **Composition**: Combine multiple protocols for flexible designs
- **Avoiding inheritance hierarchies**: Flatten complex class hierarchies
- **Default implementations**: Provide defaults that types can override

### Benefits

1. **Multiple protocol conformance**: A type can conform to many protocols (vs. single inheritance)
2. **Retroactive modeling**: Add protocol conformance to existing types via extensions
3. **Protocol composition**: Combine protocols with `&` operator
4. **Default implementations**: Provide concrete implementations in protocol extensions

```swift
// Protocol composition
func describe(_ item: Drawable & CustomStringConvertible) {
    print(item.description)
    item.draw()
}

// Protocol extension with default
protocol Identifiable {
    var id: UUID { get }
}

extension Identifiable {
    // Default implementation can be overridden
    var description: String {
        "Item with id: \(id)"
    }
}
```

### Common Patterns

**Capability-based design:**
```swift
protocol Saveable {
    func save() throws
}

protocol Loadable {
    static func load() throws -> Self
}

// Types declare only the capabilities they support
class Document: Saveable, Loadable {
    func save() throws { /* ... */ }
    static func load() throws -> Document { /* ... */ }
}
```

**Witness pattern for non-type-bound behavior:**
```swift
protocol Comparable {
    func isLessThan(_ other: Self) -> Bool
}

struct Person: Comparable {
    let name: String
    let age: Int

    func isLessThan(_ other: Person) -> Bool {
        self.age < other.age
    }
}
```

**See also:**
- [Combine Framework](combine_framework.md) - Protocol-based reactive programming
- [Design Patterns](design_patterns.md) - Dependency injection uses protocols

---

## Generics and Associated Types

Generics enable writing flexible, type-safe code that works with multiple types while maintaining compile-time type checking.

### Generic Types and Functions

```swift
// Generic function
func findIndex<T: Equatable>(of value: T, in array: [T]) -> Int? {
    for (index, element) in array.enumerated() {
        if element == value {
            return index
        }
    }
    return nil
}

// Generic type
struct Stack<Element> {
    private var elements: [Element] = []

    mutating func push(_ element: Element) {
        elements.append(element)
    }

    mutating func pop() -> Element? {
        elements.popLast()
    }
}

// Usage
var intStack = Stack<Int>()
intStack.push(42)
let value = intStack.pop()  // Type: Int?
```

### Associated Types

Associated types define a placeholder for a type that a protocol can use. They allow protocols to work with generic types without specifying the concrete type upfront.

```swift
protocol Container {
    associatedtype Item

    var count: Int { get }
    subscript(i: Int) -> Item { get }
    mutating func append(_ item: Item)
}

struct Stack<Element>: Container {
    private var elements: [Element] = []

    typealias Item = Element  // Explicitly specify if needed

    var count: Int {
        elements.count
    }

    subscript(i: Int) -> Element {
        elements[i]
    }

    mutating func append(_ item: Element) {
        elements.append(item)
    }
}
```

### Generic Constraints

```swift
// Type constraints
func compare<T: Comparable>(_ a: T, _ b: T) -> Bool {
    a < b
}

// Protocol constraints
func describe<T: CustomStringConvertible>(_ value: T) {
    print(value.description)
}

// Multiple constraints (conjunctions)
func process<T: Equatable & Comparable>(_ values: [T]) {
    let sorted = values.sorted()
}

// Constrained associated types (Swift 5.7+)
protocol DataRepository {
    associatedtype Item: Codable
    func fetch() async throws -> [Item]
}
```

### Conditional Conformance

```swift
// Conform to Equatable only if the element is Equatable
extension Stack: Equatable where Element: Equatable {
    static func == (lhs: Stack, rhs: Stack) -> Bool {
        lhs.elements == rhs.elements
    }
}

// Default implementations based on constraints
extension Container where Self: Equatable {
    func contains(_ item: Item) -> Bool where Item: Equatable {
        false  // Simplified for example
    }
}
```

### Advanced Generic Patterns

**Opaque Result Types (Swift 5.1+):**
```swift
func makeRect() -> some Shape {
    Rectangle()
}

// Caller sees `some Shape`, not the concrete type
// Useful for API stability and hiding implementation
```

**Type-erased wrappers:**
```swift
struct AnyContainer<Item> {
    private let _count: () -> Int
    private let _subscript: (Int) -> Item

    init<C: Container>(_ container: C) where C.Item == Item {
        self._count = { container.count }
        self._subscript = { container[$0] }
    }

    var count: Int { _count() }
    subscript(_ index: Int) -> Item { _subscript(index) }
}
```

**See also:**
- [Swift Concurrency](swift_concurrency.md) - Generic async functions
- [Combine Framework](combine_framework.md) - Generic publishers and operators

---

## Property Wrappers

Property wrappers provide a reusable way to add behavior to property storage through composition rather than inheritance.

### Basic Property Wrapper

```swift
@propertyWrapper
struct Clamped<Value: Comparable> {
    private var value: Value
    private let range: ClosedRange<Value>

    var wrappedValue: Value {
        get { value }
        set { value = min(max(newValue, range.lowerBound), range.upperBound) }
    }

    init(wrappedValue: Value, _ range: ClosedRange<Value>) {
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
        self.range = range
    }
}

struct Settings {
    @Clamped(0...100) var volume: Int = 50
    @Clamped(0...1) var brightness: Double = 0.8
}

// Usage
var settings = Settings()
settings.volume = 150  // Automatically clamped to 100
print(settings.volume)  // 100
```

### Property Wrapper Components

```swift
@propertyWrapper
struct Validated<Value> {
    private var value: Value
    private let validator: (Value) -> Bool

    var wrappedValue: Value {
        get { value }
        set {
            guard validator(newValue) else {
                fatalError("Validation failed")
            }
            value = newValue
        }
    }

    // projectedValue provides access to the wrapper itself
    var projectedValue: Validated<Value> {
        self
    }

    init(wrappedValue: Value, validator: @escaping (Value) -> Bool) {
        guard validator(wrappedValue) else {
            fatalError("Initial value failed validation")
        }
        self.value = wrappedValue
        self.validator = validator
    }

    func isValid(_ candidate: Value) -> Bool {
        validator(candidate)
    }
}

class User {
    @Validated(validator: { $0.count > 0 })
    var email: String

    init(email: String) {
        self.email = email
    }
}

// Access the wrapper via $ syntax
let user = User(email: "test@example.com")
if user.$email.isValid("new@example.com") {
    user.email = "new@example.com"
}
```

### Common Property Wrappers

**Thread-safe storage:**
```swift
@propertyWrapper
struct ThreadSafe<Value> {
    private let lock = NSLock()
    private var value: Value

    var wrappedValue: Value {
        get {
            lock.withLock { value }
        }
        set {
            lock.withLock { value = newValue }
        }
    }

    init(wrappedValue: Value) {
        self.value = wrappedValue
    }
}

class Counter {
    @ThreadSafe var count = 0
}
```

**Lazy initialization:**
```swift
@propertyWrapper
struct Lazy<Value> {
    private var value: Value?
    private let initializer: () -> Value

    var wrappedValue: Value {
        mutating get {
            if let value = value {
                return value
            }
            let newValue = initializer()
            self.value = newValue
            return newValue
        }
    }

    init(wrappedValue initializer: @escaping @autoclosure () -> Value) {
        self.initializer = initializer
    }
}
```

**See also:**
- [SwiftUI Components](swiftui_components.md) - @State, @Binding, @Published are property wrappers
- [Design Patterns](design_patterns.md) - Property wrappers in architectural patterns

---

## Result Builders

Result builders provide a DSL-like syntax for constructing complex data structures. They're used in SwiftUI, property declarations, and custom APIs.

### Basic Result Builder

```swift
@resultBuilder
struct HTMLBuilder {
    static func buildBlock(_ components: String...) -> String {
        components.joined()
    }
}

@HTMLBuilder
func buildHTML() -> String {
    "<html>"
    "<head><title>Page</title></head>"
    "<body>"
    "<h1>Hello, World!</h1>"
    "</body>"
    "</html>"
}

let html = buildHTML()
```

### Result Builder Protocol

```swift
@resultBuilder
struct ArrayBuilder<Element> {
    // Required: buildBlock for comma-separated statements
    static func buildBlock(_ components: Element...) -> [Element] {
        components
    }

    // Optional: buildOptional for if without else
    static func buildOptional(_ component: [Element]?) -> [Element] {
        component ?? []
    }

    // Optional: buildEither for if-else
    static func buildEither(first component: [Element]) -> [Element] {
        component
    }

    static func buildEither(second component: [Element]) -> [Element] {
        component
    }

    // Optional: buildArray for loops
    static func buildArray(_ components: [[Element]]) -> [Element] {
        components.flatMap { $0 }
    }
}

func makeArray<Element>(@ArrayBuilder<Element> builder: () -> [Element]) -> [Element] {
    builder()
}

let numbers = makeArray {
    1
    2
    3
    for i in 4...6 {
        i
    }
    if true {
        7
    }
}
// Result: [1, 2, 3, 4, 5, 6, 7]
```

### Custom DSL Example

```swift
@resultBuilder
struct QueryBuilder {
    static func buildBlock(_ conditions: String...) -> String {
        conditions.joined(separator: " AND ")
    }

    static func buildOptional(_ condition: String?) -> String {
        condition ?? ""
    }
}

func query(@QueryBuilder builder: () -> String) -> String {
    "SELECT * FROM users WHERE " + builder()
}

let sqlQuery = query {
    "age > 18"
    "status = 'active'"
    if true {
        "verified = true"
    }
}
// Result: "SELECT * FROM users WHERE age > 18 AND status = 'active' AND verified = true"
```

### Common Use Cases

**Building UI hierarchies (SwiftUI):**
```swift
var body: some View {
    VStack {
        Text("Title")

        if showDetails {
            DetailView()
        }

        ForEach(items, id: \.id) { item in
            ItemRow(item: item)
        }
    }
}
```

**Building configuration objects:**
```swift
@resultBuilder
struct ConfigBuilder {
    static func buildBlock(_ components: (String, Any)...) -> [String: Any] {
        Dictionary(uniqueKeysWithValues: components)
    }
}

func config(@ConfigBuilder builder: () -> [String: Any]) -> [String: Any] {
    builder()
}

let appConfig = config {
    ("apiURL", "https://api.example.com")
    ("timeout", 30)
    ("retries", 3)
}
```

**See also:**
- [SwiftUI Components](swiftui_components.md) - Result builders in view construction
- [Design Patterns](design_patterns.md) - DSL patterns in app architecture

---

## Error Handling Patterns

Swift provides multiple error handling patterns for different scenarios and async models.

### Throwing Functions and throws

Use `throws` for synchronous operations where errors are expected:

```swift
enum DatabaseError: Error {
    case userNotFound
    case invalidData
    case connectionFailed
}

func loadUser(id: String) throws -> User {
    guard let user = database.user(id: id) else {
        throw DatabaseError.userNotFound
    }
    return user
}

// Caller must handle error
do {
    let user = try loadUser(id: "123")
    print(user)
} catch DatabaseError.userNotFound {
    print("User not found")
} catch {
    print("Error: \(error)")
}
```

### Result Type for Async Callbacks

Use `Result` for asynchronous callbacks (pre-async/await pattern):

```swift
func fetchUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
    DispatchQueue.global().asyncAfter(deadline: .now() + 1) {
        let user = User(id: id, name: "Test User")
        completion(.success(user))
    }
}

// Usage
fetchUser(id: "123") { result in
    switch result {
    case .success(let user):
        print("User: \(user)")
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

### Async/Await Error Handling

Modern async/await combines the benefits of both patterns:

```swift
func fetchUser(id: String) async throws -> User {
    let url = URL(string: "https://api.example.com/users/\(id)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Clean, try-catch like syntax
Task {
    do {
        let user = try await fetchUser(id: "123")
        print("User: \(user)")
    } catch DecodingError.dataCorrupted {
        print("Invalid user data")
    } catch {
        print("Error: \(error)")
    }
}
```

### Typed Throws (Swift 6.0+)

Swift 6 introduces typed throws for more precise error handling:

```swift
enum FetchError: Error {
    case invalidURL
    case networkFailure
    case decodingError
}

func fetchUser(id: String) async throws(FetchError) -> User {
    guard URL(string: "https://api.example.com/users/\(id)") != nil else {
        throw FetchError.invalidURL
    }

    // Implementation
}

// Error type is known at compile time
Task {
    do {
        let user = try await fetchUser(id: "123")
        print(user)
    } catch {
        // `error` is FetchError, not generic Error
        switch error {
        case .invalidURL:
            print("Invalid URL")
        case .networkFailure:
            print("Network error")
        case .decodingError:
            print("Decoding error")
        }
    }
}
```

### Optionals for Missing Values

Use optionals when a value being absent is not an error:

```swift
// Returns nil if not found, not an error
func findUser(email: String) -> User? {
    database.users.first { $0.email == email }
}

// Usage
if let user = findUser(email: "test@example.com") {
    print("Found user: \(user)")
} else {
    print("User not found")
}
```

### Error Recovery Patterns

**Fallback values:**
```swift
func fetchImageWithFallback(url: URL) async -> UIImage {
    do {
        return try await fetchImage(url: url)
    } catch {
        return UIImage(systemName: "photo")!  // Fallback
    }
}
```

**Retry logic:**
```swift
func fetchWithRetry<T>(
    maxAttempts: Int = 3,
    operation: () async throws -> T
) async throws -> T {
    var lastError: Error?

    for attempt in 1...maxAttempts {
        do {
            return try await operation()
        } catch {
            lastError = error
            if attempt < maxAttempts {
                try await Task.sleep(nanoseconds: UInt64(pow(2.0, Double(attempt)) * 1_000_000_000))
            }
        }
    }

    throw lastError ?? NSError(domain: "Unknown error", code: -1)
}

// Usage
let data = try await fetchWithRetry {
    try await fetchData()
}
```

**Error wrapping:**
```swift
enum APIError: Error {
    case networkError(Error)
    case invalidResponse
    case decodingError(Error)
}

func fetchData() async throws -> Data {
    do {
        let url = URL(string: "https://api.example.com/data")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return data
    } catch {
        throw APIError.networkError(error)
    }
}
```

**See also:**
- [Swift Concurrency](swift_concurrency.md) - Error handling with async sequences
- [Testing Strategies](testing_strategies.md) - Testing error conditions

---

## Platform Availability

Mark APIs with version constraints to ensure compatibility across different platforms and Swift versions.

### Availability Annotation

```swift
@available(iOS 16.0, macOS 13.0, *)
struct NewView: View {
    var body: some View {
        Text("Available on iOS 16+, macOS 13+")
    }
}

// Version-specific method
@available(iOS 15.0, *)
func useNewAPI() {
    // iOS 15+ only
}
```

### Runtime Availability Checks

```swift
func useFeature() {
    if #available(iOS 16.0, macOS 13.0, *) {
        // Use new API
        NavigationStack {
            // iOS 16+ only code
        }
    } else {
        // Fallback for older versions
        NavigationView {
            // iOS 14 compatible code
        }
    }
}
```

### Deprecated APIs

```swift
@available(*, deprecated, renamed: "newFunction()")
func oldFunction() {
    // Old implementation
}

@available(iOS, deprecated: 15.0, message: "Use NavigationStack instead")
struct OldNavigationView: View {
    var body: some View {
        Text("Deprecated")
    }
}
```

### Common Availability Patterns

**iOS minimum versions:**
```swift
@available(iOS 15.0, *)
var supportedOnFrontrunner: some View {
    EmptyView()
}

@available(iOS 14.0, *)
var supportedOnPreiOS15: some View {
    EmptyView()
}
```

**Platform-specific code:**
```swift
#if os(iOS)
import UIKit
#elseif os(macOS)
import AppKit
#endif

func getPlatformSpecificView() -> some View {
    #if os(iOS)
    return MobileView()
    #else
    return DesktopView()
    #endif
}
```

---

## Swift Version Timeline

Understanding Swift version capabilities is crucial for choosing appropriate patterns and APIs.

| Version | Release | Key Features |
|---------|---------|--------------|
| **Swift 5.0** | Mar 2019 | Stable ABI, fixed-size SIMD types |
| **Swift 5.1** | Sep 2019 | Opaque return types (`some`), property wrappers, function builders |
| **Swift 5.2** | Mar 2020 | Key path expressions as functions, subscript improvements |
| **Swift 5.3** | Sep 2020 | Multi-pattern catch, multiple trailing closures |
| **Swift 5.4** | Apr 2021 | Result builders, implicit member expressions |
| **Swift 5.5** | Sep 2021 | Async/await, actors, structured concurrency |
| **Swift 5.6** | Mar 2022 | Existential `any`, unavailability conditions |
| **Swift 5.7** | Sep 2022 | Generics improvements, `if let` shorthand, regex literals |
| **Swift 5.8** | Mar 2023 | Result builder inference, more improvements |
| **Swift 5.9** | Sep 2023 | Macros, parameter packs, @Observable macro |
| **Swift 6.0** | Sep 2024 | Complete concurrency checking, typed throws |

### Feature Availability by Version

```swift
// Swift 5.1+: Opaque return types
func makeView() -> some View {
    Text("Hello")
}

// Swift 5.5+: Async/await
func fetchData() async throws -> Data {
    try await URLSession.shared.data(from: url).0
}

// Swift 5.9+: @Observable macro
@Observable
class ViewModel {
    var value: String = ""
}

// Swift 6.0+: Typed throws
func operation() throws(CustomError) {
    // Implementation
}
```

---

## Documentation Access

Use WebFetch to retrieve current official documentation for Swift language features.

### Swift Language Guide

Retrieve information about specific language concepts:

```
WebFetch("https://docs.swift.org/swift-book/LanguageGuide/Protocols.html",
         "Explain protocol-oriented programming with examples")

WebFetch("https://docs.swift.org/swift-book/LanguageGuide/Generics.html",
         "Describe generic types and generic functions")

WebFetch("https://docs.swift.org/swift-book/LanguageGuide/OpaqueTypes.html",
         "Explain opaque types and when to use them")
```

### Swift Standard Library

Look up specific types and their methods:

```
WebFetch("https://developer.apple.com/documentation/swift",
         "List all types and protocols available in the Swift standard library")

WebFetch("https://developer.apple.com/documentation/swift/array",
         "Show Array methods for filtering, mapping, and reducing")
```

### Swift Evolution Proposals

Review accepted proposals for language changes:

```
WebFetch("https://github.com/apple/swift-evolution/blob/main/proposals/0296-async-await.md",
         "Summarize the async/await proposal and its rationale")

WebFetch("https://github.com/apple/swift-evolution/blob/main/proposals/0384-importing-opaque-types.md",
         "Explain opaque type parameter improvements")
```

**Use WebFetch when:**
- Learning new language features
- Verifying version availability
- Checking for improvements in newer Swift versions
- Exploring evolution proposals for upcoming features

---

**See also:**
- [Swift Concurrency](swift_concurrency.md) - Async/await, actors, TaskGroups
- [Design Patterns](design_patterns.md) - How these features enable common patterns
- [Testing Strategies](testing_strategies.md) - Testing code using these patterns
