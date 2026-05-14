# Design Patterns for Swift Applications

Common architectural patterns and design approaches for building maintainable, testable Swift applications. This reference covers MVVM, Dependency Injection, Repository patterns, and other proven strategies.

## Table of Contents

- [MVVM with SwiftUI](#mvvm-with-swiftui)
- [Dependency Injection](#dependency-injection)
- [Repository Pattern](#repository-pattern)
- [Coordinator Pattern](#coordinator-pattern)
- [View Composition](#view-composition)
- [Singleton Pattern](#singleton-pattern)
- [Observer Pattern](#observer-pattern)
- [Best Practices](#best-practices)

---

## MVVM with SwiftUI

Model-View-ViewModel (MVVM) separates UI logic from business logic, making code testable and reusable.

### Complete Example: Todo App

**Model:**
```swift
import Foundation

struct Todo: Identifiable, Codable {
    let id: UUID
    var title: String
    var description: String
    var isCompleted: Bool
    var dueDate: Date?
}
```

**ViewModel:**
```swift
import Combine

@MainActor
class TodoListViewModel: ObservableObject {
    @Published var todos: [Todo] = []
    @Published var newTodoTitle: String = ""
    @Published var isLoading = false
    @Published var error: String?

    private let repository: TodoRepository

    init(repository: TodoRepository = TodoRepository()) {
        self.repository = repository
        Task {
            await loadTodos()
        }
    }

    func loadTodos() async {
        isLoading = true
        defer { isLoading = false }

        do {
            todos = try await repository.fetchTodos()
        } catch {
            self.error = error.localizedDescription
        }
    }

    func addTodo(title: String) async {
        guard !title.trimmingCharacters(in: .whitespaces).isEmpty else { return }

        let todo = Todo(
            id: UUID(),
            title: title,
            description: "",
            isCompleted: false
        )

        do {
            try await repository.save(todo)
            todos.append(todo)
            newTodoTitle = ""
        } catch {
            self.error = error.localizedDescription
        }
    }

    func toggleTodo(_ todo: Todo) async {
        var updated = todo
        updated.isCompleted.toggle()

        do {
            try await repository.update(updated)
            if let index = todos.firstIndex(where: { $0.id == todo.id }) {
                todos[index] = updated
            }
        } catch {
            self.error = error.localizedDescription
        }
    }

    func deleteTodo(_ todo: Todo) async {
        do {
            try await repository.delete(todo)
            todos.removeAll { $0.id == todo.id }
        } catch {
            self.error = error.localizedDescription
        }
    }

    func clearError() {
        error = nil
    }
}
```

**Repository:**
```swift
protocol TodoRepository {
    func fetchTodos() async throws -> [Todo]
    func save(_ todo: Todo) async throws
    func update(_ todo: Todo) async throws
    func delete(_ todo: Todo) async throws
}

class DefaultTodoRepository: TodoRepository {
    private let persistenceController: PersistenceController

    init(persistence: PersistenceController = PersistenceController.shared) {
        self.persistenceController = persistence
    }

    func fetchTodos() async throws -> [Todo] {
        // Fetch from Core Data, CloudKit, or API
        // For this example, returning mock data
        return [
            Todo(id: UUID(), title: "Learn MVVM", description: "", isCompleted: false),
            Todo(id: UUID(), title: "Build app", description: "", isCompleted: true)
        ]
    }

    func save(_ todo: Todo) async throws {
        // Save to persistence layer
    }

    func update(_ todo: Todo) async throws {
        // Update in persistence layer
    }

    func delete(_ todo: Todo) async throws {
        // Delete from persistence layer
    }
}
```

**View:**
```swift
struct TodoListView: View {
    @StateObject private var viewModel = TodoListViewModel()
    @State private var showAddTodo = false

    var body: some View {
        ZStack {
            List {
                ForEach(viewModel.todos) { todo in
                    TodoRow(todo: todo) {
                        Task {
                            await viewModel.toggleTodo(todo)
                        }
                    }
                    .onDelete { indexSet in
                        Task {
                            for index in indexSet {
                                await viewModel.deleteTodo(viewModel.todos[index])
                            }
                        }
                    }
                }
            }
            .navigationTitle("Todos")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Add") {
                        showAddTodo = true
                    }
                }
            }
            .sheet(isPresented: $showAddTodo) {
                AddTodoView { title in
                    Task {
                        await viewModel.addTodo(title: title)
                    }
                    showAddTodo = false
                }
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK") {
                    viewModel.clearError()
                }
            } message: {
                Text(viewModel.error ?? "Unknown error")
            }

            if viewModel.isLoading {
                ProgressView()
            }
        }
    }
}

struct TodoRow: View {
    let todo: Todo
    let onToggle: () -> Void

    var body: some View {
        HStack {
            Button(action: onToggle) {
                Image(systemName: todo.isCompleted ? "checkmark.circle.fill" : "circle")
                    .foregroundColor(todo.isCompleted ? .green : .gray)
            }

            VStack(alignment: .leading) {
                Text(todo.title)
                    .strikethrough(todo.isCompleted)

                if !todo.description.isEmpty {
                    Text(todo.description)
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
            }

            Spacer()

            if let dueDate = todo.dueDate {
                Text(dueDate.formatted(date: .abbreviated, time: .omitted))
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}

struct AddTodoView: View {
    @State private var title = ""
    let onSave: (String) -> Void

    var body: some View {
        NavigationView {
            Form {
                TextField("Todo title", text: $title)
            }
            .navigationTitle("New Todo")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Save") {
                        onSave(title)
                    }
                    .disabled(title.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}
```

### MVVM Benefits

1. **Testability**: ViewModels can be tested without UI
2. **Reusability**: Same ViewModel can work with different Views
3. **Separation of Concerns**: UI logic separated from business logic
4. **State Management**: Clear data flow through @Published properties

**See also:**
- [Swift Concurrency](swift_concurrency.md) - Async/await in ViewModels
- [Testing Strategies](testing_strategies.md) - Testing ViewModels

---

## Dependency Injection

Dependency Injection (DI) makes code testable by inverting control—dependencies are provided to objects rather than being created internally.

### Constructor Injection

```swift
// Protocol defines the dependency contract
protocol DataService {
    func fetchUsers() async throws -> [User]
}

// Concrete implementation
class APIDataService: DataService {
    func fetchUsers() async throws -> [User] {
        // Fetch from API
        []
    }
}

// Mock for testing
class MockDataService: DataService {
    var mockUsers: [User] = []

    func fetchUsers() async throws -> [User] {
        mockUsers
    }
}

// Class receives dependency via constructor
class UserRepository {
    private let dataService: DataService

    init(dataService: DataService) {
        self.dataService = dataService
    }

    func getUsers() async throws -> [User] {
        try await dataService.fetchUsers()
    }
}

// Production
let productionRepo = UserRepository(dataService: APIDataService())

// Testing
let testService = MockDataService()
testService.mockUsers = [User(id: "1", name: "Test")]
let testRepo = UserRepository(dataService: testService)
```

### Property Injection

```swift
class ViewController: UIViewController {
    var repository: UserRepository?

    override func viewDidLoad() {
        super.viewDidLoad()
        // repository should be set before viewDidLoad
        repository?.loadUsers()
    }
}

// Setup
let vc = ViewController()
vc.repository = UserRepository(dataService: APIDataService())
```

### Method Injection

```swift
class DataProcessor {
    func process(_ data: [User], using service: DataService) async throws {
        let enriched = try await service.fetchUsers()
        // Process enriched data
    }
}

// Caller injects the dependency
let processor = DataProcessor()
try await processor.process(users, using: mockService)
```

### Service Locator Pattern (Use Sparingly)

```swift
class ServiceLocator {
    static let shared = ServiceLocator()

    private var services: [String: Any] = [:]

    func register<T>(_ type: T.Type, factory: @escaping () -> T) {
        let key = String(describing: T.self)
        services[key] = factory
    }

    func resolve<T>(_ type: T.Type) -> T {
        let key = String(describing: T.self)
        guard let factory = services[key] as? () -> T else {
            fatalError("Service not registered: \(key)")
        }
        return factory()
    }
}

// Setup
ServiceLocator.shared.register(DataService.self) {
    APIDataService()
}

// Usage (less testable than constructor injection)
let service: DataService = ServiceLocator.shared.resolve(DataService.self)
```

### DI Container Pattern

```swift
class DIContainer {
    // MARK: - Services
    lazy var dataService: DataService = APIDataService()
    lazy var userRepository: UserRepository = UserRepository(dataService: dataService)
    lazy var userViewModel: UserViewModel = UserViewModel(repository: userRepository)

    // MARK: - For Testing
    init(dataService: DataService? = nil) {
        if let dataService {
            self.dataService = dataService
        }
    }
}

// Production
let container = DIContainer()
let viewModel = container.userViewModel

// Testing
let mockService = MockDataService()
let testContainer = DIContainer(dataService: mockService)
let testViewModel = testContainer.userViewModel
```

**See also:**
- [Protocol-Oriented Programming](swift_language_features.md#protocol-oriented-programming) - DI uses protocols
- [Testing Strategies](testing_strategies.md) - Injecting mocks for testing

---

## Repository Pattern

The Repository pattern abstracts the data access layer, providing a clean API for fetching and persisting data regardless of source (API, Core Data, file system).

```swift
protocol UserRepository {
    func fetchUsers() async throws -> [User]
    func fetchUser(id: String) async throws -> User
    func saveUser(_ user: User) async throws
    func deleteUser(id: String) async throws
}

class DefaultUserRepository: UserRepository {
    private let apiService: APIService
    private let cacheService: CacheService

    init(apiService: APIService, cacheService: CacheService) {
        self.apiService = apiService
        self.cacheService = cacheService
    }

    func fetchUsers() async throws -> [User] {
        // Try cache first
        if let cached = try await cacheService.getUsers() {
            return cached
        }

        // Fall back to API
        let users = try await apiService.fetchUsers()

        // Update cache
        try await cacheService.saveUsers(users)

        return users
    }

    func fetchUser(id: String) async throws -> User {
        // Try cache
        if let cached = try await cacheService.getUser(id: id) {
            return cached
        }

        // Fetch from API
        let user = try await apiService.fetchUser(id: id)

        // Cache it
        try await cacheService.saveUser(user)

        return user
    }

    func saveUser(_ user: User) async throws {
        // Save to API
        try await apiService.saveUser(user)

        // Update cache
        try await cacheService.saveUser(user)
    }

    func deleteUser(id: String) async throws {
        // Delete from API
        try await apiService.deleteUser(id: id)

        // Remove from cache
        try await cacheService.deleteUser(id: id)
    }
}

// Multi-source example
class CloudKitUserRepository: UserRepository {
    private let cloudKit = CloudKitManager.shared
    private let coreData = PersistenceController.shared

    func fetchUsers() async throws -> [User] {
        // Try CloudKit first (online-first)
        do {
            let records = try await cloudKit.fetchRecords(ofType: "User")
            let users = records.compactMap { User(from: $0) }
            try await coreData.saveUsers(users)  // Cache locally
            return users
        } catch {
            // Fall back to Core Data
            return try await coreData.fetchUsers()
        }
    }
}
```

**Benefits:**
- Decouples data source details from business logic
- Easy to swap implementations (API, database, cache)
- Simplifies testing with mock repositories
- Centralizes data access logic

---

## Coordinator Pattern

The Coordinator pattern manages navigation and orchestrates transitions between view controllers, keeping individual controllers free of navigation logic.

### Basic Coordinator

```swift
protocol Coordinator: AnyObject {
    associatedtype ViewController

    func start() -> ViewController
}

class AppCoordinator: Coordinator {
    var navigationController: UINavigationController

    init(navigationController: UINavigationController) {
        self.navigationController = navigationController
    }

    func start() -> UINavigationController {
        let viewModel = TodoListViewModel()
        let todoListVC = TodoListViewController(viewModel: viewModel)
        todoListVC.coordinator = self

        navigationController.viewControllers = [todoListVC]
        return navigationController
    }

    func showTodoDetail(_ todo: Todo) {
        let detailViewModel = TodoDetailViewModel(todo: todo)
        let detailVC = TodoDetailViewController(viewModel: detailViewModel)
        navigationController.pushViewController(detailVC, animated: true)
    }

    func showSettings() {
        let settingsVC = SettingsViewController()
        let settingsNav = UINavigationController(rootViewController: settingsVC)
        navigationController.present(settingsNav, animated: true)
    }
}

// View Controller uses coordinator for navigation
class TodoListViewController: UIViewController {
    weak var coordinator: AppCoordinator?
    let viewModel: TodoListViewModel

    init(viewModel: TodoListViewModel) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) not supported")
    }

    override func viewDidLoad() {
        super.viewDidLoad()

        navigationItem.rightBarButtonItem = UIBarButtonItem(
            image: UIImage(systemName: "gear"),
            style: .plain,
            target: self,
            action: #selector(didTapSettings)
        )
    }

    func tableView(_ UITableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        let todo = viewModel.todos[indexPath.row]
        coordinator?.showTodoDetail(todo)
    }

    @objc
    func didTapSettings() {
        coordinator?.showSettings()
    }
}
```

### Coordinator with Child Coordinators

```swift
protocol Coordinator: AnyObject {
    var children: [Coordinator] { get set }
    var parent: Coordinator? { get set }

    func start()
}

class AppCoordinator: Coordinator {
    var children: [Coordinator] = []
    var parent: Coordinator?

    func start() {
        showTodoList()
    }

    private func showTodoList() {
        let coordinator = TodoListCoordinator(navigationController: navigationController)
        coordinator.parent = self
        children.append(coordinator)
        coordinator.start()
    }
}

class TodoListCoordinator: Coordinator {
    var children: [Coordinator] = []
    var parent: Coordinator?
    let navigationController: UINavigationController

    init(navigationController: UINavigationController) {
        self.navigationController = navigationController
    }

    func start() {
        let vc = TodoListViewController()
        vc.coordinator = self
        navigationController.pushViewController(vc, animated: true)
    }

    func showDetail(_ todo: Todo) {
        let coordinator = TodoDetailCoordinator(
            navigationController: navigationController,
            todo: todo
        )
        coordinator.parent = self
        children.append(coordinator)
        coordinator.start()
    }
}
```

---

## View Composition

Building complex UIs by composing smaller, reusable view components.

```swift
// Small, focused components
struct UserAvatarView: View {
    let user: User
    let size: CGFloat = 50

    var body: some View {
        AsyncImage(url: user.avatarURL) { phase in
            switch phase {
            case .empty:
                ProgressView()
            case .success(let image):
                image
                    .resizable()
                    .scaledToFill()
            case .failure:
                Image(systemName: "person.crop.circle")
            @unknown default:
                Image(systemName: "person.crop.circle")
            }
        }
        .frame(width: size, height: size)
        .clipShape(Circle())
    }
}

struct UserHeaderView: View {
    let user: User

    var body: some View {
        VStack(spacing: 12) {
            UserAvatarView(user: user, size: 60)

            VStack(spacing: 4) {
                Text(user.name)
                    .font(.headline)
                Text(user.bio)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding()
    }
}

struct UserProfileView: View {
    let user: User

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                UserHeaderView(user: user)

                VStack(spacing: 12) {
                    ForEach(user.posts) { post in
                        PostCardView(post: post)
                    }
                }
                .padding()
            }
        }
    }
}
```

**Benefits:**
- Reusable, testable components
- Easier to maintain
- Clear responsibility for each view
- Easy to preview in Xcode

---

## Singleton Pattern

A class that should have only one instance. Use sparingly—dependency injection is usually preferable.

### Thread-Safe Singleton

```swift
class AppState {
    static let shared = AppState()

    private var data: [String: Any] = [:]
    private let lock = NSLock()

    private init() {}

    func set(_ value: Any, forKey key: String) {
        lock.withLock {
            data[key] = value
        }
    }

    func get(forKey key: String) -> Any? {
        lock.withLock {
            data[key]
        }
    }
}

// Usage
AppState.shared.set("darkMode", forKey: "theme")
let theme = AppState.shared.get(forKey: "theme")
```

### When to Use Singletons

✓ Application-wide state
✓ Configuration managers
✓ Analytics/Logging services
✓ Network client
✓ Database connection

✗ Data repositories (inject instead)
✗ Service dependencies (inject instead)
✗ State that changes frequently (use @State/@Published)

---

## Observer Pattern

Objects can observe state changes and react accordingly.

### Using Combine Publishers

```swift
class UserViewModel: ObservableObject {
    @Published var isLoggedIn = false
    @Published var userName: String = ""

    private var cancellables = Set<AnyCancellable>()

    func setupObservers() {
        // Observer pattern using Combine
        $isLoggedIn
            .dropFirst()
            .sink { isLoggedIn in
                print("Login state changed: \(isLoggedIn)")
                if isLoggedIn {
                    self.loadUserProfile()
                }
            }
            .store(in: &cancellables)
    }

    func loadUserProfile() {
        // Load user profile
    }
}
```

### Using Swift 5.9 @Observable

```swift
import Observation

@Observable
class UserViewModel {
    var isLoggedIn = false
    var userName: String = ""

    func login() {
        isLoggedIn = true
        // Changes automatically observed by Views
    }
}

struct UserView: View {
    @State var viewModel = UserViewModel()

    var body: some View {
        if viewModel.isLoggedIn {
            Text("Welcome, \(viewModel.userName)")
        } else {
            Button("Login") {
                viewModel.login()
            }
        }
    }
}
```

---

## Best Practices

### 1. Separation of Concerns

```swift
// ❌ Bad: Mixed concerns
class UserViewModel {
    var users: [User] = []

    func fetchUsers() {
        // Network request
        // Database update
        // UI state management
        // Error handling
    }
}

// ✅ Good: Separated concerns
class UserRepository {
    func fetchUsers() async throws -> [User] { /* Data fetching */ }
}

@MainActor
class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    private let repository: UserRepository

    func loadUsers() async {
        do {
            users = try await repository.fetchUsers()
        } catch {
            handleError(error)
        }
    }
}
```

### 2. Dependency Direction

```swift
// ✅ Good: Dependency flows downward
// AppCoordinator → ViewController → ViewModel → Repository → Service

// ❌ Bad: Circular dependencies
// ViewController ↔ ViewModel
// Repository ↔ Service
```

### 3. Protocol-Driven Design

```swift
// ✅ Good: Depend on protocols
class UserViewModel {
    private let repository: UserRepository  // Protocol

    init(repository: UserRepository) {
        self.repository = repository
    }
}

// ❌ Bad: Depend on concrete types
class UserViewModel {
    private let repository = DefaultUserRepository()  // Concrete class
}
```

### 4. Testability First

```swift
// ✅ Good: Easy to test with mock
protocol DataService {
    func fetch() async throws -> Data
}

class ViewModel {
    init(service: DataService) {
        self.service = service
    }
}

let mockService = MockDataService()
let viewModel = ViewModel(service: mockService)

// ❌ Bad: Hard to test
class ViewModel {
    private let service = APIService()  // Can't mock
}
```

---

**See also:**
- [Swift Language Features](swift_language_features.md) - Protocols and generics
- [Testing Strategies](testing_strategies.md) - Testing these patterns
- [iOS/macOS Frameworks](ios_macos_frameworks.md) - Repository pattern with Core Data/CloudKit
