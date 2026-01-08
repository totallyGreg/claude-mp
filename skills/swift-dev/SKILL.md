---
name: swift-dev
description: Expert guidance for Swift development including SwiftUI, iOS/macOS frameworks, Server-side Swift, and Objective-C to Swift 6 migration. Use when developing Swift applications, working with Apple frameworks, building server-side Swift apps, or modernizing legacy Objective-C codebases to Swift 6. Supports Swift 5.0-6.0 with version annotations and live documentation fetching.
metadata:
  version: "1.1.0"
---

# Swift Development Expert

Expert guidance for modern Swift development across all Apple platforms and server-side applications. Provide production-ready, idiomatic Swift code with appropriate error handling, testing approaches, and references to official documentation.

## Core Capabilities

### 1. SwiftUI Development

Design declarative user interfaces with modern SwiftUI patterns:

**State Management:**
- `@State`: Local view state for simple values
- `@Binding`: Two-way connections to parent state
- `@StateObject`: Observable object ownership
- `@ObservedObject`: Observable object observation
- `@EnvironmentObject`: Shared app-wide state
- `@Environment`: System environment values

**Navigation:**
```swift
// NavigationStack (iOS 16+, Swift 5.7+)
NavigationStack {
    List(items) { item in
        NavigationLink(value: item) {
            ItemRow(item: item)
        }
    }
    .navigationDestination(for: Item.self) { item in
        DetailView(item: item)
    }
}

// NavigationSplitView for iPad/Mac
NavigationSplitView {
    SidebarView()
} detail: {
    DetailView()
}
```

**Common View Patterns:**
- Lists with custom rows and sections
- Forms for data entry
- Sheets, popovers, and alerts
- Animations and transitions
- Custom view modifiers
- GeometryReader for responsive layouts
- ViewBuilder for conditional views

**Performance Considerations:**
- Avoid expensive computations in body
- Use `@ViewBuilder` for conditional content
- Leverage `EquatableView` for optimization
- Profile with Instruments when needed

### 2. Swift Language Features

Implement modern Swift patterns and idioms (Swift 5.0+):

**Concurrency (Swift 5.5+):**
```swift
// Async/await
func fetchUser(id: String) async throws -> User {
    let url = URL(string: "https://api.example.com/users/\(id)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

// Actors for thread-safe state
actor UserCache {
    private var cache: [String: User] = [:]

    func user(for id: String) -> User? {
        cache[id]
    }

    func store(_ user: User, for id: String) {
        cache[id] = user
    }
}

// Task groups for parallel execution
await withTaskGroup(of: User.self) { group in
    for id in userIDs {
        group.addTask {
            try await fetchUser(id: id)
        }
    }

    for await user in group {
        users.append(user)
    }
}
```

**Protocol-Oriented Programming:**
```swift
protocol Drawable {
    func draw()
}

extension Drawable where Self: Shape {
    func draw() {
        print("Drawing shape with area: \(area)")
    }
}
```

**Property Wrappers (Swift 5.1+):**
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
        self.range = range
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
    }
}

struct Settings {
    @Clamped(0...100) var volume: Int = 50
}
```

**Generics and Associated Types:**
```swift
protocol Container {
    associatedtype Item
    var items: [Item] { get }
    mutating func add(_ item: Item)
}

struct Stack<Element>: Container {
    private var elements: [Element] = []

    var items: [Element] { elements }

    mutating func add(_ item: Element) {
        elements.append(item)
    }
}
```

**Result Builders (Swift 5.4+):**
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
    "<body>"
    "<h1>Hello, World!</h1>"
    "</body>"
    "</html>"
}
```

### 3. iOS/macOS Frameworks

Integrate with essential Apple frameworks:

**Combine Framework:**
```swift
import Combine

class ViewModel: ObservableObject {
    @Published var searchText = ""
    @Published var results: [Result] = []
    private var cancellables = Set<AnyCancellable>()

    init() {
        $searchText
            .debounce(for: 0.5, scheduler: DispatchQueue.main)
            .removeDuplicates()
            .compactMap { $0.isEmpty ? nil : $0 }
            .flatMap { query in
                self.search(query: query)
                    .catch { _ in Just([]) }
            }
            .receive(on: DispatchQueue.main)
            .assign(to: &$results)
    }

    func search(query: String) -> AnyPublisher<[Result], Error> {
        // Implement search logic
        Just([]).setFailureType(to: Error.self).eraseToAnyPublisher()
    }
}
```

**Core Data:**
```swift
// SwiftUI integration
@FetchRequest(
    sortDescriptors: [NSSortDescriptor(keyPath: \Item.timestamp, ascending: true)],
    animation: .default
)
private var items: FetchedResults<Item>

// Background context operations
func performBackgroundTask() {
    persistenceController.container.performBackgroundTask { context in
        let newItem = Item(context: context)
        newItem.timestamp = Date()

        do {
            try context.save()
        } catch {
            print("Error saving: \(error)")
        }
    }
}
```

**CloudKit:**
- Private and public databases
- Record types and fields
- Subscriptions for push notifications
- Sharing and collaboration

**StoreKit 2 (Swift 5.5+):**
```swift
import StoreKit

func purchase(_ product: Product) async throws -> Transaction? {
    let result = try await product.purchase()

    switch result {
    case .success(let verification):
        let transaction = try checkVerified(verification)
        await transaction.finish()
        return transaction
    case .userCancelled, .pending:
        return nil
    @unknown default:
        return nil
    }
}

func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
    switch result {
    case .unverified:
        throw StoreError.failedVerification
    case .verified(let safe):
        return safe
    }
}
```

**URLSession and Networking:**
```swift
// Modern async/await approach
struct NetworkService {
    func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T {
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }

        return try JSONDecoder().decode(T.self, from: data)
    }
}
```

### 4. Server-Side Swift

Build backend services with Swift frameworks:

**Vapor Framework:**
```swift
import Vapor

func routes(_ app: Application) throws {
    // Basic route
    app.get("hello") { req async -> String in
        "Hello, world!"
    }

    // JSON endpoint
    app.post("users") { req async throws -> User in
        let user = try req.content.decode(User.self)
        try await user.save(on: req.db)
        return user
    }

    // Route parameters
    app.get("users", ":userID") { req async throws -> User in
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }
        return user
    }
}

// Middleware
struct AuthMiddleware: AsyncMiddleware {
    func respond(to request: Request, chainingTo next: AsyncResponder) async throws -> Response {
        guard request.headers.bearerAuthorization != nil else {
            throw Abort(.unauthorized)
        }
        return try await next.respond(to: request)
    }
}
```

**Fluent ORM:**
```swift
final class User: Model {
    static let schema = "users"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "email")
    var email: String

    @Field(key: "name")
    var name: String

    @Children(for: \.$user)
    var posts: [Post]

    init() { }

    init(id: UUID? = nil, email: String, name: String) {
        self.id = id
        self.email = email
        self.name = name
    }
}
```

**Swift NIO for Custom Networking:**
```swift
import NIO

let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
let bootstrap = ServerBootstrap(group: group)
    .serverChannelOption(ChannelOptions.backlog, value: 256)
    .childChannelInitializer { channel in
        channel.pipeline.addHandler(HTTPServerHandler())
    }

let channel = try bootstrap.bind(host: "localhost", port: 8080).wait()
try channel.closeFuture.wait()
```

**Authentication & Authorization:**
- JWT token generation and validation
- OAuth 2.0 integration
- Session management
- Password hashing with Bcrypt

**Database Integration:**
- PostgreSQL with Fluent
- MongoDB with MongoKitten
- Redis for caching
- SQLite for development

### 5. Objective-C Migration

Migrate legacy Objective-C code to Swift:

**Interoperability Basics:**
```swift
// Bridging header (ProjectName-Bridging-Header.h)
#import "LegacyManager.h"
#import "OldViewController.h"

// Using Objective-C from Swift
let manager = LegacyManager()
manager.performAction()

// Exposing Swift to Objective-C
@objc class SwiftManager: NSObject {
    @objc func newMethod() {
        // Implementation
    }
}
```

**Common Translation Patterns:**
```objc
// Objective-C
@interface User : NSObject
@property (nonatomic, strong) NSString *name;
@property (nonatomic, assign) NSInteger age;
- (void)greetWithMessage:(NSString *)message;
@end
```

```swift
// Swift equivalent
class User: NSObject {
    var name: String
    var age: Int

    init(name: String, age: Int) {
        self.name = name
        self.age = age
        super.init()
    }

    func greet(message: String) {
        print("\(message), \(name)")
    }
}
```

**Swift 6 Modernization:**

Modern Swift 6 provides significant improvements over legacy Objective-C patterns. The migration goes beyond syntax translation to architectural improvements:

**From GCD to Structured Concurrency:**
```objc
// Objective-C: Nested GCD for background work + UI update
dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
    id result = [self performWork];
    dispatch_async(dispatch_get_main_queue(), ^{
        [self.ui updateWithResult:result];
    });
});
```

```swift
// Swift 6: Structured concurrency with Task and MainActor
Task {
    let result = await performWork()
    await MainActor.run {
        self.ui.update(with: result)
    }
}
```

**From thread locks to actors:**
```objc
// Objective-C: Manual synchronization
@synchronized(self) {
    [self.cache setObject:user forKey:userID];
}
```

```swift
// Swift 6: Actor provides automatic isolation
actor UserCache {
    private var cache: [String: User] = [:]

    func store(_ user: User, for id: String) {
        cache[id] = user  // Automatically thread-safe
    }
}
```

**From KVO to @Observable:**
```objc
// Objective-C: KVO setup
[self.model addObserver:self forKeyPath:@"value" options:NSKeyValueObservingOptionNew context:NULL];
```

```swift
// Swift 6: @Observable macro (Swift 5.9+)
@Observable
class Model {
    var value: String = ""  // Automatically observable
}
```

For comprehensive Swift 6 migration patterns with detailed before/after examples, see `objc_to_swift6_migration.md`.

**Nullability and Optionals:**
```objc
// Objective-C with nullability annotations
@property (nonatomic, strong, nullable) NSString *middleName;
@property (nonatomic, strong, nonnull) NSString *lastName;
```

```swift
// Swift automatically translates these
var middleName: String?  // nullable
var lastName: String     // nonnull
```

**Blocks to Closures:**
```objc
// Objective-C
typedef void (^CompletionHandler)(NSString *result, NSError *error);

- (void)fetchDataWithCompletion:(CompletionHandler)completion {
    // Implementation
}
```

```swift
// Swift
typealias CompletionHandler = (String?, Error?) -> Void

func fetchData(completion: @escaping CompletionHandler) {
    // Implementation
}

// Or using Result type (preferred)
func fetchData(completion: @escaping (Result<String, Error>) -> Void) {
    // Implementation
}
```

**Migration Strategy:**

**Phase 1: Assessment**
- Run `scripts/migration_analyzer.py` on your codebase to identify migration opportunities
- Identify high-priority modernization targets (concurrency patterns, KVO, NSNotificationCenter)
- Add nullability annotations to remaining Objective-C headers

**Phase 2: Foundation**
- Migrate model layer first (data structures, pure logic)
- Convert utilities and helper functions to Swift
- Establish Swift coding patterns and style guide

**Phase 3: Swift 6 Modernization**
- Convert GCD patterns to Task-based structured concurrency
- Replace @synchronized/NSLock with actors for thread safety
- Migrate KVO to @Observable macro (Swift 5.9+) or Combine
- Replace NSNotificationCenter with AsyncStream or Combine publishers

**Phase 4: UI Layer**
- Update view controllers incrementally
- Apply MainActor to UI classes
- Leverage SwiftUI where appropriate
- Refactor delegate patterns to async/await where beneficial

**Phase 5: Polish**
- Apply Swift idioms (guard, if let, protocol-oriented design)
- Enable complete concurrency checking (Swift 6)
- Add Sendable conformance where needed
- Comprehensive testing with strict concurrency mode

For detailed migration patterns and code examples, see `objc_to_swift6_migration.md`.

## Response Guidelines

### When Helping with Swift Development

**Initial Assessment:**
1. Ask about target platform (iOS, macOS, watchOS, tvOS, server)
2. Identify minimum Swift version required
3. Understand deployment target (iOS 15+, macOS 12+, etc.)
4. Clarify whether SwiftUI or UIKit/AppKit is preferred

**Code Quality Standards:**
- Follow [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/)
- Use meaningful, descriptive names (verbs for functions, nouns for types)
- Implement proper access control (private, fileprivate, internal, public)
- Add documentation comments for public APIs
- Handle errors appropriately (throws, Result, optional)
- Write testable, modular code

**Error Handling Approach:**
```swift
// Use throws for expected failures
func loadUser(id: String) throws -> User {
    guard let user = database.user(id: id) else {
        throw DatabaseError.userNotFound
    }
    return user
}

// Use Result for async callbacks
func fetchUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
    // Implementation
}

// Use async/await for modern async code
func fetchUser(id: String) async throws -> User {
    // Implementation
}

// Use optionals for absence of value (not errors)
func findUser(email: String) -> User? {
    // Returns nil if not found
}
```

**Testing Recommendations:**
```swift
import XCTest
@testable import MyApp

class UserServiceTests: XCTestCase {
    var sut: UserService!
    var mockDatabase: MockDatabase!

    override func setUp() {
        super.setUp()
        mockDatabase = MockDatabase()
        sut = UserService(database: mockDatabase)
    }

    override func tearDown() {
        sut = nil
        mockDatabase = nil
        super.tearDown()
    }

    func testFetchUser_ValidID_ReturnsUser() async throws {
        // Given
        let expectedUser = User(id: "123", name: "Test")
        mockDatabase.users = [expectedUser]

        // When
        let user = try await sut.fetchUser(id: "123")

        // Then
        XCTAssertEqual(user.id, expectedUser.id)
        XCTAssertEqual(user.name, expectedUser.name)
    }
}
```

### Version Annotations

When features are version-specific, annotate clearly:

**Swift Language Versions:**
- **Swift 5.0**: Basic features, opaque result types removed
- **Swift 5.1**: Opaque return types (`some View`), property wrappers, function builders
- **Swift 5.2**: Key path expressions as functions
- **Swift 5.3**: Multi-pattern catch clauses, multiple trailing closures
- **Swift 5.4**: Result builders, implicit member expressions
- **Swift 5.5**: Async/await, actors, structured concurrency
- **Swift 5.6**: Existential any, unavailability condition
- **Swift 5.7**: Generics improvements, if let shorthand
- **Swift 5.8**: Result builder inference
- **Swift 5.9**: Macros, parameter packs
- **Swift 6.0**: Complete concurrency checking, typed throws

**Platform Availability:**
```swift
@available(iOS 16.0, macOS 13.0, *)
func useNavigationStack() {
    NavigationStack {
        // iOS 16+ only
    }
}

if #available(iOS 16.0, *) {
    // Use new API
} else {
    // Fallback for older versions
}
```

## Accessing Official Documentation

To retrieve current Swift documentation, use WebFetch with these official sources:

**Swift Language Guide:**
```
WebFetch("https://docs.swift.org/swift-book/LanguageGuide/TheBasics.html",
         "Extract information about [specific topic like optionals, closures, protocols]")
```

**Swift Standard Library:**
```
WebFetch("https://developer.apple.com/documentation/swift/array",
         "Explain methods and usage patterns for Array type")
```

**SwiftUI Documentation:**
```
WebFetch("https://developer.apple.com/documentation/swiftui/view",
         "Summarize View protocol and common modifiers")
```

**Framework Documentation:**
```
WebFetch("https://developer.apple.com/documentation/combine",
         "Explain Combine publishers and operators")

WebFetch("https://developer.apple.com/documentation/coredata",
         "Describe Core Data stack setup and usage")
```

**Server-Side Swift:**
```
WebFetch("https://docs.vapor.codes/",
         "Find information about [Vapor feature]")
```

**Swift Evolution Proposals:**
```
WebFetch("https://github.com/apple/swift-evolution/blob/main/proposals/XXXX-proposal-name.md",
         "Summarize the Swift evolution proposal and its implementation")
```

Use WebFetch when:
- User asks about latest API changes
- Clarification needed on framework behavior
- Checking availability of features across versions
- Verifying best practices from official sources

## Common Patterns and Snippets

### SwiftUI MVVM Pattern
```swift
// Model
struct Todo: Identifiable, Codable {
    let id: UUID
    var title: String
    var isCompleted: Bool
}

// ViewModel
@MainActor
class TodoListViewModel: ObservableObject {
    @Published var todos: [Todo] = []
    private let repository: TodoRepository

    init(repository: TodoRepository = TodoRepository()) {
        self.repository = repository
        Task {
            await loadTodos()
        }
    }

    func loadTodos() async {
        do {
            todos = try await repository.fetchTodos()
        } catch {
            print("Error loading todos: \(error)")
        }
    }

    func addTodo(title: String) async {
        let todo = Todo(id: UUID(), title: title, isCompleted: false)
        do {
            try await repository.save(todo)
            await loadTodos()
        } catch {
            print("Error saving todo: \(error)")
        }
    }

    func toggleTodo(_ todo: Todo) async {
        var updated = todo
        updated.isCompleted.toggle()
        do {
            try await repository.update(updated)
            await loadTodos()
        } catch {
            print("Error updating todo: \(error)")
        }
    }
}

// View
struct TodoListView: View {
    @StateObject private var viewModel = TodoListViewModel()
    @State private var newTodoTitle = ""

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.todos) { todo in
                    TodoRow(todo: todo) {
                        Task {
                            await viewModel.toggleTodo(todo)
                        }
                    }
                }
            }
            .navigationTitle("Todos")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Add") {
                        Task {
                            await viewModel.addTodo(title: newTodoTitle)
                            newTodoTitle = ""
                        }
                    }
                }
            }
        }
    }
}
```

### Dependency Injection
```swift
protocol NetworkService {
    func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T
}

class DefaultNetworkService: NetworkService {
    func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T {
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode(T.self, from: data)
    }
}

// Dependency injection via initializer
class UserRepository {
    private let networkService: NetworkService

    init(networkService: NetworkService = DefaultNetworkService()) {
        self.networkService = networkService
    }

    func fetchUsers() async throws -> [User] {
        let url = URL(string: "https://api.example.com/users")!
        return try await networkService.fetch([User].self, from: url)
    }
}
```

### Swift Package Manager Setup
```swift
// Package.swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MyLibrary",
    platforms: [
        .iOS(.v15),
        .macOS(.v12)
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

## Progressive Disclosure

For detailed technical information, reference these documentation files in the `references/` directory:

- **swiftui_components.md**: Comprehensive SwiftUI component reference with examples
- **swift_concurrency.md**: Deep dive into async/await, actors, and structured concurrency
- **combine_framework.md**: Complete Combine guide with publishers, operators, and subscribers
- **swift_package_manager.md**: SPM configuration, dependencies, and best practices
- **objc_interop.md**: Objective-C bridging, migration strategies, and interoperability
- **objc_to_swift6_migration.md**: Comprehensive guide for migrating legacy Objective-C patterns to Swift 6, including concurrency (GCD to Task, locks to actors), data flow (KVO to @Observable, NSNotificationCenter to AsyncStream), error handling, and API design patterns with detailed before/after examples
- **server_side_frameworks.md**: Vapor, Swift NIO, and backend development guides
- **testing_strategies.md**: XCTest, test doubles, UI testing, and TDD approaches

## Resources

### scripts/
- **migration_analyzer.py**: Analyze Objective-C code for Swift 6 migration opportunities. Detects legacy concurrency patterns (GCD, locks, NSOperation), data flow patterns (KVO, NSNotificationCenter), error handling (NSError**), and provides specific Swift 6 replacement recommendations
- **swift_package_init.py**: Initialize Swift Package Manager projects

### references/
Detailed Swift language and framework documentation, server-side guides, and migration strategies.

### assets/
SwiftUI templates, Vapor server boilerplate, and Package.swift examples for quick project starts.

---

**Remember**: Always write idiomatic Swift code that leverages the language's type safety, optionals, and protocol-oriented features. Prefer value types (struct, enum) over reference types (class) unless reference semantics are needed. Use modern concurrency with async/await for asynchronous operations.
