# Combine Framework Reference

Comprehensive guide to Apple's Combine framework for reactive programming in Swift.

## Core Concepts

### Publishers

Publishers emit sequences of values over time.

```swift
import Combine

// Just: Emits a single value then completes
let publisher = Just(42)

// Future: Async operation that emits one value
let future = Future<Int, Error> { promise in
    DispatchQueue.global().async {
        promise(.success(100))
    }
}

// Empty: Completes immediately without emitting
let empty = Empty<Int, Never>()

// Fail: Fails immediately with error
let fail = Fail<Int, NetworkError>(error: .timeout)
```

### Subscribers

Subscribers receive values from publishers.

```swift
// Sink: Most common subscriber
cancellable = publisher
    .sink(
        receiveCompletion: { completion in
            switch completion {
            case .finished:
                print("Completed")
            case .failure(let error):
                print("Error: \(error)")
            }
        },
        receiveValue: { value in
            print("Received: \(value)")
        }
    )

// Assign: Assigns values to property
cancellable = publisher
    .assign(to: \.text, on: label)

// Assign to Published (SwiftUI)
publisher
    .assign(to: &$propertyName)
```

### Subjects

Subjects are both publishers and allow manual value injection.

```swift
// PassthroughSubject: Doesn't hold state
let subject = PassthroughSubject<String, Never>()

subject.sink { value in
    print(value)
}.store(in: &cancellables)

subject.send("Hello")
subject.send("World")
subject.send(completion: .finished)

// CurrentValueSubject: Holds current value
let currentSubject = CurrentValueSubject<Int, Never>(0)

print(currentSubject.value) // 0

currentSubject.send(1)
currentSubject.send(2)

print(currentSubject.value) // 2
```

## Publisher Operators

### Transforming

```swift
// Map: Transform values
publisher
    .map { $0 * 2 }
    .sink { print($0) }

// TryMap: Transform with error throwing
publisher
    .tryMap { value throws -> Int in
        guard value > 0 else {
            throw ValidationError.negative
        }
        return value
    }

// FlatMap: Transform to another publisher
publisher
    .flatMap { id in
        fetchUser(id: id)
    }

// Scan: Accumulator pattern
publisher
    .scan(0) { accumulator, value in
        accumulator + value
    }

// ReplaceNil: Replace nil with default
optionalPublisher
    .replaceNil(with: "Default")

// ReplaceEmpty: Provide value if publisher completes without emitting
publisher
    .replaceEmpty(with: 0)
```

### Filtering

```swift
// Filter: Only emit matching values
publisher
    .filter { $0 > 10 }

// CompactMap: Filter nil values and transform
publisher
    .compactMap { $0 as? String }

// RemoveDuplicates: Remove consecutive duplicates
publisher
    .removeDuplicates()

// First: Emit only first value
publisher
    .first()

// Last: Emit only last value
publisher
    .last()

// DropFirst: Skip first N values
publisher
    .dropFirst(2)

// Drop while: Skip while condition is true
publisher
    .drop(while: { $0 < 5 })

// Prefix: Take first N values
publisher
    .prefix(3)

// Prefix while: Take while condition is true
publisher
    .prefix(while: { $0 < 10 })
```

### Combining

```swift
// Merge: Combine multiple publishers of same type
let publisher1 = PassthroughSubject<Int, Never>()
let publisher2 = PassthroughSubject<Int, Never>()

publisher1.merge(with: publisher2)
    .sink { print($0) }

// CombineLatest: Emit when any publisher emits
publisher1.combineLatest(publisher2)
    .sink { value1, value2 in
        print("\(value1), \(value2)")
    }

// Zip: Emit when both publishers emit
publisher1.zip(publisher2)
    .sink { value1, value2 in
        print("\(value1), \(value2)")
    }

// SwitchToLatest: Switch to latest publisher
publisherOfPublishers
    .switchToLatest()
    .sink { print($0) }

// Append: Append publisher after first completes
publisher1.append(publisher2)

// Prepend: Prepend values or publisher
publisher.prepend(1, 2, 3)
publisher.prepend(otherPublisher)
```

### Timing

```swift
// Debounce: Emit after pause in emissions
searchQuery
    .debounce(for: .milliseconds(300), scheduler: DispatchQueue.main)
    .sink { query in
        performSearch(query)
    }

// Throttle: Emit at most once per interval
publisher
    .throttle(for: .seconds(1), scheduler: DispatchQueue.main, latest: true)

// Delay: Delay emissions
publisher
    .delay(for: .seconds(2), scheduler: DispatchQueue.main)

// Timeout: Fail if no emission within timeout
publisher
    .timeout(.seconds(5), scheduler: DispatchQueue.main)
```

### Sequence Operators

```swift
// Collect: Collect all values into array
publisher
    .collect()
    .sink { values in
        print(values) // Array of all values
    }

// Collect with count: Buffer values
publisher
    .collect(3)
    .sink { values in
        print(values) // Arrays of 3 values
    }

// Reduce: Reduce to single value
publisher
    .reduce(0, +)
    .sink { sum in
        print(sum)
    }
```

### Error Handling

```swift
// Catch: Recover from error with another publisher
publisher
    .catch { error -> AnyPublisher<String, Never> in
        Just("Default").eraseToAnyPublisher()
    }

// TryCatch: Catch with error throwing
publisher
    .tryCatch { error throws -> AnyPublisher<String, Error> in
        if shouldRetry(error) {
            return retryPublisher().eraseToAnyPublisher()
        }
        throw error
    }

// Retry: Retry on failure
publisher
    .retry(3)

// ReplaceError: Replace error with value
publisher
    .replaceError(with: "Error occurred")

// SetFailureType: Change Never to specific error type
neverFailPublisher
    .setFailureType(to: MyError.self)

// MapError: Transform error type
publisher
    .mapError { error in
        NetworkError.from(error)
    }
```

### Scheduling

```swift
// Receive on: Specify scheduler for downstream
publisher
    .receive(on: DispatchQueue.main)
    .sink { value in
        // Update UI on main thread
        updateUI(value)
    }

// Subscribe on: Specify scheduler for subscription
publisher
    .subscribe(on: DispatchQueue.global())
    .receive(on: DispatchQueue.main)
    .sink { value in
        print(value)
    }
```

## Common Patterns

### Search with Debounce

```swift
class SearchViewModel: ObservableObject {
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
        URLSession.shared.dataTaskPublisher(for: searchURL(query))
            .map(\.data)
            .decode(type: [Result].self, decoder: JSONDecoder())
            .eraseToAnyPublisher()
    }
}
```

### Form Validation

```swift
class FormViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var confirmPassword = ""

    @Published var isValid = false

    private var cancellables = Set<AnyCancellable>()

    init() {
        // Email validation
        let emailValid = $email
            .map { $0.contains("@") && $0.contains(".") }

        // Password validation
        let passwordValid = $password
            .map { $0.count >= 8 }

        // Confirm password validation
        let passwordsMatch = Publishers.CombineLatest($password, $confirmPassword)
            .map { $0 == $1 && !$0.isEmpty }

        // Combine all validations
        Publishers.CombineLatest3(emailValid, passwordValid, passwordsMatch)
            .map { $0 && $1 && $2 }
            .assign(to: &$isValid)
    }
}
```

### Network Request with Retry

```swift
func fetchData<T: Decodable>(from url: URL) -> AnyPublisher<T, Error> {
    URLSession.shared.dataTaskPublisher(for: url)
        .tryMap { data, response -> Data in
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                throw NetworkError.invalidResponse
            }
            return data
        }
        .decode(type: T.self, decoder: JSONDecoder())
        .retry(3)
        .receive(on: DispatchQueue.main)
        .eraseToAnyPublisher()
}
```

### Multiple Parallel Requests

```swift
func loadAll() -> AnyPublisher<(User, [Post], [Comment]), Error> {
    let userPublisher = fetchUser()
    let postsPublisher = fetchPosts()
    let commentsPublisher = fetchComments()

    return Publishers.Zip3(userPublisher, postsPublisher, commentsPublisher)
        .eraseToAnyPublisher()
}
```

### Chaining Dependent Requests

```swift
func loadUserProfile(id: String) -> AnyPublisher<Profile, Error> {
    fetchUser(id: id)
        .flatMap { user in
            fetchPosts(userId: user.id)
                .map { posts in
                    Profile(user: user, posts: posts)
                }
        }
        .eraseToAnyPublisher()
}
```

### Polling

```swift
func poll<T>(
    interval: TimeInterval,
    publisher: @escaping () -> AnyPublisher<T, Error>
) -> AnyPublisher<T, Error> {
    Timer.publish(every: interval, on: .main, in: .common)
        .autoconnect()
        .flatMap { _ in
            publisher()
                .catch { _ in Empty<T, Error>() }
        }
        .eraseToAnyPublisher()
}

// Usage
poll(interval: 5.0) {
    fetchStatus()
}
.sink { status in
    updateStatus(status)
}
.store(in: &cancellables)
```

## SwiftUI Integration

### @Published Property Wrapper

```swift
class ViewModel: ObservableObject {
    @Published var text = ""
    @Published var count = 0

    // SwiftUI automatically updates when these change
}
```

### ObservableObject

```swift
class UserViewModel: ObservableObject {
    @Published var user: User?
    @Published var isLoading = false
    @Published var error: Error?

    private var cancellables = Set<AnyCancellable>()

    func loadUser(id: String) {
        isLoading = true

        userService.fetchUser(id: id)
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    if case .failure(let error) = completion {
                        self?.error = error
                    }
                },
                receiveValue: { [weak self] user in
                    self?.user = user
                }
            )
            .store(in: &cancellables)
    }
}
```

### Custom Publisher for SwiftUI

```swift
extension Publishers {
    struct ViewDidAppear: Publisher {
        typealias Output = Void
        typealias Failure = Never

        func receive<S>(subscriber: S) where S: Subscriber, Failure == S.Failure, Output == S.Input {
            let subscription = ViewDidAppearSubscription(subscriber: subscriber)
            subscriber.receive(subscription: subscription)
        }
    }
}

class ViewDidAppearSubscription<S: Subscriber>: Subscription where S.Input == Void, S.Failure == Never {
    private var subscriber: S?

    init(subscriber: S) {
        self.subscriber = subscriber
    }

    func request(_ demand: Subscribers.Demand) {
        _ = subscriber?.receive(())
    }

    func cancel() {
        subscriber = nil
    }
}
```

## Memory Management

### Storing Cancellables

```swift
class ViewModel {
    // Option 1: Set of AnyCancellable
    private var cancellables = Set<AnyCancellable>()

    func setup() {
        publisher
            .sink { value in
                print(value)
            }
            .store(in: &cancellables)
    }

    // Option 2: Individual cancellables
    private var userCancellable: AnyCancellable?
    private var postsCancellable: AnyCancellable?

    // Option 3: Array
    private var cancellables: [AnyCancellable] = []

    func setupArray() {
        let c1 = publisher1.sink { _ in }
        let c2 = publisher2.sink { _ in }
        cancellables.append(contentsOf: [c1, c2])
    }
}
```

### Weak Self Pattern

```swift
class ViewModel {
    private var cancellables = Set<AnyCancellable>()

    func loadData() {
        publisher
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.handleCompletion(completion)
                },
                receiveValue: { [weak self] value in
                    self?.handleValue(value)
                }
            )
            .store(in: &cancellables)
    }
}
```

## Custom Publishers

### Simple Custom Publisher

```swift
struct CountdownPublisher: Publisher {
    typealias Output = Int
    typealias Failure = Never

    let start: Int

    func receive<S>(subscriber: S) where S: Subscriber, Failure == S.Failure, Output == S.Input {
        let subscription = CountdownSubscription(subscriber: subscriber, start: start)
        subscriber.receive(subscription: subscription)
    }
}

class CountdownSubscription<S: Subscriber>: Subscription where S.Input == Int, S.Failure == Never {
    private var subscriber: S?
    private var count: Int

    init(subscriber: S, start: Int) {
        self.subscriber = subscriber
        self.count = start
    }

    func request(_ demand: Subscribers.Demand) {
        var demand = demand

        while demand > 0 && count > 0 {
            demand -= 1
            demand += subscriber?.receive(count) ?? .none
            count -= 1
        }

        if count == 0 {
            subscriber?.receive(completion: .finished)
        }
    }

    func cancel() {
        subscriber = nil
    }
}

// Usage
CountdownPublisher(start: 5)
    .sink { value in
        print(value)
    }
```

### Extension Publisher

```swift
extension Publishers {
    struct Validate<Upstream: Publisher>: Publisher where Upstream.Output == String {
        typealias Output = Bool
        typealias Failure = Upstream.Failure

        let upstream: Upstream
        let validator: (String) -> Bool

        init(upstream: Upstream, validator: @escaping (String) -> Bool) {
            self.upstream = upstream
            self.validator = validator
        }

        func receive<S>(subscriber: S) where S: Subscriber, Failure == S.Failure, Output == S.Input {
            upstream
                .map(validator)
                .receive(subscriber: subscriber)
        }
    }
}

extension Publisher where Output == String {
    func validate(_ validator: @escaping (String) -> Bool) -> Publishers.Validate<Self> {
        Publishers.Validate(upstream: self, validator: validator)
    }
}

// Usage
$email
    .validate { $0.contains("@") }
    .sink { isValid in
        print("Email valid: \(isValid)")
    }
```

## Testing

### Testing Publishers

```swift
import XCTest
import Combine

class PublisherTests: XCTestCase {
    var cancellables = Set<AnyCancellable>()

    func testPublisher() {
        let expectation = XCTestExpectation(description: "Publisher emits value")

        Just(42)
            .sink { value in
                XCTAssertEqual(value, 42)
                expectation.fulfill()
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: 1.0)
    }

    func testAsyncPublisher() throws {
        let values = try awaitPublisher(
            Just([1, 2, 3])
                .delay(for: 0.1, scheduler: DispatchQueue.main)
        )

        XCTAssertEqual(values, [1, 2, 3])
    }

    func awaitPublisher<P: Publisher>(
        _ publisher: P,
        timeout: TimeInterval = 1.0
    ) throws -> P.Output where P.Failure == Never {
        var result: P.Output?
        let expectation = XCTestExpectation(description: "Awaiting publisher")

        publisher
            .sink { value in
                result = value
                expectation.fulfill()
            }
            .store(in: &cancellables)

        wait(for: [expectation], timeout: timeout)

        return try XCTUnwrap(result)
    }
}
```

### Mock Subscribers

```swift
class MockSubscriber<Input, Failure: Error>: Subscriber {
    var receivedValues: [Input] = []
    var receivedCompletion: Subscribers.Completion<Failure>?

    func receive(subscription: Subscription) {
        subscription.request(.unlimited)
    }

    func receive(_ input: Input) -> Subscribers.Demand {
        receivedValues.append(input)
        return .none
    }

    func receive(completion: Subscribers.Completion<Failure>) {
        receivedCompletion = completion
    }
}

// Usage in tests
func testCustomPublisher() {
    let subscriber = MockSubscriber<Int, Never>()

    CountdownPublisher(start: 3)
        .subscribe(subscriber)

    XCTAssertEqual(subscriber.receivedValues, [3, 2, 1])
}
```

## Performance Tips

1. **Use `share()` for expensive publishers**
```swift
let expensivePublisher = fetchData()
    .share() // Share single subscription

expensivePublisher.sink { _ in }
expensivePublisher.sink { _ in }
// Only one network request
```

2. **Avoid unnecessary type erasure**
```swift
// ❌ Unnecessary type erasure
func simple() -> AnyPublisher<Int, Never> {
    Just(42).eraseToAnyPublisher()
}

// ✅ Better: Use opaque type
func simple() -> some Publisher<Int, Never> {
    Just(42)
}
```

3. **Use `compactMap` instead of `filter` + `map`**
```swift
// ❌ Less efficient
publisher
    .filter { $0 != nil }
    .map { $0! }

// ✅ Better
publisher
    .compactMap { $0 }
```

4. **Cancel subscriptions properly**
```swift
// Always store or cancel immediately
cancellable = publisher.sink { _ in }

// Or use store
publisher.sink { _ in }.store(in: &cancellables)
```

## Migration to Async/Await

### Before (Combine)

```swift
func fetchUser() -> AnyPublisher<User, Error> {
    URLSession.shared.dataTaskPublisher(for: url)
        .map(\.data)
        .decode(type: User.self, decoder: JSONDecoder())
        .eraseToAnyPublisher()
}

cancellable = fetchUser()
    .sink(
        receiveCompletion: { completion in
            // Handle completion
        },
        receiveValue: { user in
            // Handle user
        }
    )
```

### After (Async/Await)

```swift
func fetchUser() async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}

Task {
    do {
        let user = try await fetchUser()
        // Handle user
    } catch {
        // Handle error
    }
}
```

### Bridging Combine to Async/Await

```swift
extension Publisher {
    func async() async throws -> Output where Failure == Error {
        try await withCheckedThrowingContinuation { continuation in
            var cancellable: AnyCancellable?

            cancellable = first()
                .sink(
                    receiveCompletion: { completion in
                        switch completion {
                        case .finished:
                            break
                        case .failure(let error):
                            continuation.resume(throwing: error)
                        }
                    },
                    receiveValue: { value in
                        continuation.resume(returning: value)
                    }
                )
        }
    }
}

// Usage
let value = try await publisher.async()
```

## Best Practices

1. **Store cancellables properly to avoid memory leaks**
2. **Use `weak self` in closures when needed**
3. **Prefer simple operators over complex custom publishers**
4. **Use type erasure sparingly (performance cost)**
5. **Consider async/await for simple async operations**
6. **Use Combine for reactive streams and complex transformations**
7. **Always handle errors appropriately**
8. **Use appropriate schedulers (main for UI updates)**
9. **Cancel subscriptions when no longer needed**
10. **Test publishers thoroughly with expectations**
