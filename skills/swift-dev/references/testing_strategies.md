# Swift Testing Strategies Reference

Comprehensive guide to testing Swift applications using XCTest, test doubles, and modern testing practices.

## XCTest Basics

### Test Class Structure

```swift
import XCTest
@testable import MyApp

final class UserServiceTests: XCTestCase {
    var sut: UserService!  // System Under Test
    var mockRepository: MockUserRepository!

    // Run before each test
    override func setUp() {
        super.setUp()
        mockRepository = MockUserRepository()
        sut = UserService(repository: mockRepository)
    }

    // Run after each test
    override func tearDown() {
        sut = nil
        mockRepository = nil
        super.tearDown()
    }

    // Class-level setup (runs once)
    override class func setUp() {
        super.setUp()
        // One-time setup
    }

    // Class-level teardown (runs once)
    override class func tearDown() {
        // One-time cleanup
        super.tearDown()
    }
}
```

### Assertions

```swift
// Equality
XCTAssertEqual(result, expected)
XCTAssertNotEqual(result, unexpected)

// Identity
XCTAssertIdentical(object1, object2)
XCTAssertNotIdentical(object1, object2)

// Boolean
XCTAssertTrue(condition)
XCTAssertFalse(condition)

// Nil checking
XCTAssertNil(optional)
XCTAssertNotNil(optional)

// Errors
XCTAssertThrowsError(try throwingFunction())
XCTAssertNoThrow(try nonThrowingFunction())

// Floating point
XCTAssertEqual(value, expected, accuracy: 0.001)

// Failure
XCTFail("Test failed")

// Custom messages
XCTAssertEqual(result, expected, "Values should match")
```

## Async Testing

### Testing Async/Await

```swift
func testAsyncFunction() async throws {
    let result = try await fetchData()
    XCTAssertEqual(result.count, 10)
}

func testAsyncError() async {
    do {
        _ = try await failingFunction()
        XCTFail("Should have thrown error")
    } catch {
        XCTAssertTrue(error is NetworkError)
    }
}
```

### Testing with Expectations

```swift
func testWithExpectation() {
    let expectation = XCTestExpectation(description: "Data loaded")

    dataService.loadData { result in
        switch result {
        case .success(let data):
            XCTAssertFalse(data.isEmpty)
            expectation.fulfill()
        case .failure:
            XCTFail("Should not fail")
        }
    }

    wait(for: [expectation], timeout: 5.0)
}

// Multiple expectations
func testMultipleExpectations() {
    let exp1 = XCTestExpectation(description: "First")
    let exp2 = XCTestExpectation(description: "Second")

    doAsync {
        exp1.fulfill()
    }

    doAnotherAsync {
        exp2.fulfill()
    }

    wait(for: [exp1, exp2], timeout: 5.0)
}
```

## Test Doubles

### Mocks

```swift
class MockUserRepository: UserRepository {
    var users: [User] = []
    var fetchCalled = false
    var fetchCallCount = 0

    func fetchUsers() async throws -> [User] {
        fetchCalled = true
        fetchCallCount += 1
        return users
    }

    func save(_ user: User) async throws {
        users.append(user)
    }
}

// Test with mock
func testLoadUsers() async throws {
    // Given
    let expectedUsers = [User(id: "1", name: "John")]
    mockRepository.users = expectedUsers

    // When
    let users = try await sut.loadUsers()

    // Then
    XCTAssertTrue(mockRepository.fetchCalled)
    XCTAssertEqual(mockRepository.fetchCallCount, 1)
    XCTAssertEqual(users, expectedUsers)
}
```

### Stubs

```swift
class StubNetworkService: NetworkService {
    var stubData: Data?
    var stubError: Error?

    func fetch(from url: URL) async throws -> Data {
        if let error = stubError {
            throw error
        }
        return stubData ?? Data()
    }
}

// Test with stub
func testWithStub() async throws {
    // Given
    let expectedData = "test".data(using: .utf8)!
    stubService.stubData = expectedData

    // When
    let data = try await sut.fetchData()

    // Then
    XCTAssertEqual(data, expectedData)
}
```

### Spies

```swift
class SpyAnalytics: AnalyticsService {
    var loggedEvents: [(name: String, properties: [String: Any])] = []

    func log(event: String, properties: [String: Any] = [:]) {
        loggedEvents.append((event, properties))
    }
}

// Test with spy
func testAnalytics() {
    // Given
    let spy = SpyAnalytics()
    let sut = ViewController(analytics: spy)

    // When
    sut.buttonTapped()

    // Then
    XCTAssertEqual(spy.loggedEvents.count, 1)
    XCTAssertEqual(spy.loggedEvents[0].name, "button_tap")
}
```

### Fakes

```swift
class FakeDatabase: Database {
    private var storage: [String: Any] = [:]

    func save<T>(_ object: T, for key: String) {
        storage[key] = object
    }

    func load<T>(for key: String) -> T? {
        storage[key] as? T
    }

    func delete(for key: String) {
        storage.removeValue(forKey: key)
    }
}

// Test with fake
func testPersistence() {
    // Given
    let fake = FakeDatabase()
    let sut = UserManager(database: fake)
    let user = User(id: "1", name: "John")

    // When
    sut.save(user)
    let loaded: User? = fake.load(for: "1")

    // Then
    XCTAssertEqual(loaded, user)
}
```

## Dependency Injection

### Protocol-Based Injection

```swift
protocol UserRepository {
    func fetchUsers() async throws -> [User]
}

class RealUserRepository: UserRepository {
    func fetchUsers() async throws -> [User] {
        // Real implementation
    }
}

class UserService {
    private let repository: UserRepository

    init(repository: UserRepository) {
        self.repository = repository
    }

    func loadUsers() async throws -> [User] {
        try await repository.fetchUsers()
    }
}

// Test
func testUserService() async throws {
    let mock = MockUserRepository()
    let sut = UserService(repository: mock)
    // Test...
}
```

## Testing Patterns

### AAA Pattern (Arrange-Act-Assert)

```swift
func testUserLogin() async throws {
    // Arrange (Given)
    let email = "test@example.com"
    let password = "password"
    mockAuth.stubUser = User(email: email)

    // Act (When)
    let user = try await sut.login(email: email, password: password)

    // Assert (Then)
    XCTAssertEqual(user.email, email)
    XCTAssertTrue(mockAuth.loginCalled)
}
```

### Given-When-Then

```swift
func testUserRegistration() async throws {
    // Given
    let email = "new@example.com"
    mockRepository.users = []

    // When
    let user = try await sut.register(email: email)

    // Then
    XCTAssertEqual(mockRepository.users.count, 1)
    XCTAssertEqual(mockRepository.users[0].email, email)
}
```

## SwiftUI Testing

### Preview Testing

```swift
import SwiftUI

struct ContentView_Previews: PreviewProvider {
    static var previews: some View {
        Group {
            ContentView()
                .preferredColorScheme(.light)
                .previewDisplayName("Light")

            ContentView()
                .preferredColorScheme(.dark)
                .previewDisplayName("Dark")

            ContentView()
                .previewDevice("iPhone SE (3rd generation)")
                .previewDisplayName("Small Screen")
        }
    }
}
```

### ViewInspector

```swift
import ViewInspector
import SwiftUI

extension ContentView: Inspectable { }

func testContentView() throws {
    let view = ContentView()
    let text = try view.inspect().find(text: "Hello, World!")
    XCTAssertEqual(try text.string(), "Hello, World!")
}

func testButton() throws {
    var tapped = false
    let view = Button("Tap") { tapped = true }

    try view.inspect().button().tap()
    XCTAssertTrue(tapped)
}
```

## UI Testing

### XCUITest

```swift
import XCTest

final class AppUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    func testLoginFlow() {
        // Enter email
        let emailField = app.textFields["Email"]
        emailField.tap()
        emailField.typeText("test@example.com")

        // Enter password
        let passwordField = app.secureTextFields["Password"]
        passwordField.tap()
        passwordField.typeText("password123")

        // Tap login button
        app.buttons["Login"].tap()

        // Verify navigation
        XCTAssertTrue(app.staticTexts["Welcome"].exists)
    }

    func testNavigationFlow() {
        let tabBar = app.tabBars.firstMatch
        tabBar.buttons["Profile"].tap()

        XCTAssertTrue(app.navigationBars["Profile"].exists)
    }
}
```

### Accessibility Identifiers

```swift
// SwiftUI
Button("Login") {
    login()
}
.accessibilityIdentifier("loginButton")

// UIKit
button.accessibilityIdentifier = "loginButton"

// Test
let button = app.buttons["loginButton"]
XCTAssertTrue(button.exists)
```

## Performance Testing

### Measure Block

```swift
func testPerformance() {
    measure {
        // Code to measure
        _ = heavyComputation()
    }
}

// Metrics
func testPerformanceMetrics() {
    let metrics: [XCTMetric] = [
        XCTClockMetric(),
        XCTCPUMetric(),
        XCTMemoryMetric(),
        XCTStorageMetric()
    ]

    let options = XCTMeasureOptions()
    options.iterationCount = 10

    measure(metrics: metrics, options: options) {
        performOperation()
    }
}
```

## Test Organization

### Test Suites

```swift
// Group related tests
class UserTests: XCTestCase {
    // User-related tests
}

class AuthTests: XCTestCase {
    // Auth-related tests
}

// Create suite
class AllTests {
    static func allTests() -> XCTestSuite {
        let suite = XCTestSuite(name: "All Tests")
        suite.addTest(UserTests.defaultTestSuite())
        suite.addTest(AuthTests.defaultTestSuite())
        return suite
    }
}
```

### Tags and Filtering

```bash
# Run specific test
swift test --filter UserServiceTests.testLoadUsers

# Run test class
swift test --filter UserServiceTests

# Skip slow tests
swift test --filter '.*' --skip-slow-tests
```

## Code Coverage

```bash
# Enable code coverage
swift test --enable-code-coverage

# Generate coverage report
xcrun llvm-cov show \
    .build/debug/MyAppPackageTests.xctest/Contents/MacOS/MyAppPackageTests \
    -instr-profile .build/debug/codecov/default.profdata \
    -use-color \
    > coverage.txt
```

## Snapshot Testing

```swift
import SnapshotTesting

func testViewSnapshot() {
    let view = ContentView()
    assertSnapshot(matching: view, as: .image)
}

func testLayoutOnDifferentDevices() {
    let view = ContentView()

    assertSnapshot(matching: view, as: .image(on: .iPhone13))
    assertSnapshot(matching: view, as: .image(on: .iPhoneSe))
    assertSnapshot(matching: view, as: .image(on: .iPadPro12_9))
}
```

## Testing Best Practices

### 1. Test Naming

```swift
// ✅ Good: Descriptive names
func testLoadUsers_WhenNetworkFails_ThrowsError()
func testLogin_WithValidCredentials_ReturnsUser()
func testSave_WhenDatabaseUnavailable_ReturnsFalse()

// ❌ Bad: Vague names
func testUser()
func test1()
func testSomething()
```

### 2. One Assertion Per Test (When Possible)

```swift
// ✅ Good: Focused test
func testUserName() {
    XCTAssertEqual(user.name, "John")
}

func testUserEmail() {
    XCTAssertEqual(user.email, "john@example.com")
}

// ❌ Bad: Multiple unrelated assertions
func testUser() {
    XCTAssertEqual(user.name, "John")
    XCTAssertEqual(user.email, "john@example.com")
    XCTAssertEqual(user.age, 30)
}
```

### 3. Test Independence

```swift
// ✅ Good: Independent tests
class UserTests: XCTestCase {
    override func setUp() {
        database.clear()  // Clean state for each test
    }

    func testSaveUser() {
        let user = User(name: "John")
        sut.save(user)
        XCTAssertEqual(database.count, 1)
    }

    func testDeleteUser() {
        let user = User(name: "John")
        sut.save(user)
        sut.delete(user)
        XCTAssertEqual(database.count, 0)
    }
}

// ❌ Bad: Dependent tests
var savedUser: User!

func test1_SaveUser() {
    savedUser = User(name: "John")
    sut.save(savedUser)
}

func test2_DeleteUser() {
    sut.delete(savedUser)  // Depends on test1
}
```

### 4. Test Data Builders

```swift
class UserBuilder {
    private var id = "default-id"
    private var name = "Default Name"
    private var email = "default@example.com"

    func withId(_ id: String) -> UserBuilder {
        self.id = id
        return self
    }

    func withName(_ name: String) -> UserBuilder {
        self.name = name
        return self
    }

    func build() -> User {
        User(id: id, name: name, email: email)
    }
}

// Usage
func testUser() {
    let user = UserBuilder()
        .withName("John")
        .withEmail("john@example.com")
        .build()

    // Test with user
}
```

### 5. Test Fixtures

```swift
extension User {
    static func fixture(
        id: String = "test-id",
        name: String = "Test User",
        email: String = "test@example.com"
    ) -> User {
        User(id: id, name: name, email: email)
    }
}

// Usage
func testUserService() {
    let user = User.fixture(name: "Custom Name")
    // Test with user
}
```

## TDD Workflow

### Red-Green-Refactor

```swift
// 1. RED: Write failing test
func testUserFullName() {
    let user = User(firstName: "John", lastName: "Doe")
    XCTAssertEqual(user.fullName, "John Doe")  // Fails: fullName doesn't exist
}

// 2. GREEN: Make it pass
struct User {
    let firstName: String
    let lastName: String

    var fullName: String {
        "\(firstName) \(lastName)"
    }
}

// 3. REFACTOR: Improve code quality
struct User {
    let firstName: String
    let lastName: String

    var fullName: String {
        [firstName, lastName]
            .filter { !$0.isEmpty }
            .joined(separator: " ")
    }
}
```

## Common Testing Patterns

### Testing Errors

```swift
func testThrowsSpecificError() {
    XCTAssertThrowsError(try throwingFunction()) { error in
        XCTAssertTrue(error is NetworkError)
        XCTAssertEqual(error as? NetworkError, .timeout)
    }
}
```

### Testing Collections

```swift
func testCollection() {
    let items = sut.loadItems()

    XCTAssertEqual(items.count, 3)
    XCTAssertTrue(items.contains { $0.name == "Item 1" })
    XCTAssertFalse(items.isEmpty)
}
```

### Testing Optionals

```swift
func testOptional() throws {
    let result = sut.findUser(id: "123")

    let user = try XCTUnwrap(result)  // Fails if nil
    XCTAssertEqual(user.id, "123")
}
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest

    steps:
    - uses: actions/checkout@v3

    - name: Run tests
      run: swift test --enable-code-coverage

    - name: Generate coverage
      run: |
        xcrun llvm-cov export -format="lcov" \
          .build/debug/MyAppPackageTests.xctest/Contents/MacOS/MyAppPackageTests \
          -instr-profile .build/debug/codecov/default.profdata \
          > coverage.lcov

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.lcov
```

## Resources

- [XCTest Documentation](https://developer.apple.com/documentation/xctest)
- [Testing Swift Code](https://www.swift.org/getting-started/#testing)
- [ViewInspector](https://github.com/nalexn/ViewInspector)
- [SnapshotTesting](https://github.com/pointfreeco/swift-snapshot-testing)
