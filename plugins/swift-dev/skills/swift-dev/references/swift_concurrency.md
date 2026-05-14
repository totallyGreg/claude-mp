# Swift Concurrency Reference

Comprehensive guide to Swift's modern concurrency features including async/await, actors, and structured concurrency (Swift 5.5+).

## Async/Await Basics

### Async Functions

```swift
// Basic async function
func fetchData() async throws -> Data {
    let url = URL(string: "https://api.example.com/data")!
    let (data, _) = try await URLSession.shared.data(from: url)
    return data
}

// Calling async function
Task {
    do {
        let data = try await fetchData()
        print("Received \(data.count) bytes")
    } catch {
        print("Error: \(error)")
    }
}
```

### Async Properties

```swift
struct UserProfile {
    var avatarImage: UIImage {
        get async throws {
            let url = URL(string: imageURL)!
            let (data, _) = try await URLSession.shared.data(from: url)
            return UIImage(data: data)!
        }
    }
}

// Usage
Task {
    let image = try await profile.avatarImage
}
```

### Async Sequences

```swift
func fetchLines(from url: URL) async throws -> [String] {
    var lines: [String] = []

    for try await line in url.lines {
        lines.append(line)
    }

    return lines
}

// Custom async sequence
struct Counter: AsyncSequence {
    typealias Element = Int
    let limit: Int

    struct AsyncIterator: AsyncIteratorProtocol {
        let limit: Int
        var current = 0

        mutating func next() async -> Int? {
            guard current < limit else { return nil }

            current += 1
            try? await Task.sleep(nanoseconds: 1_000_000_000)
            return current
        }
    }

    func makeAsyncIterator() -> AsyncIterator {
        AsyncIterator(limit: limit)
    }
}

// Usage
for await number in Counter(limit: 5) {
    print(number)
}
```

## Tasks

### Creating Tasks

```swift
// Detached task
Task.detached {
    await performBackgroundWork()
}

// Regular task (inherits priority and context)
Task {
    await doSomething()
}

// Task with priority
Task(priority: .high) {
    await urgentWork()
}
```

### Task Cancellation

```swift
let task = Task {
    for i in 1...10 {
        // Check for cancellation
        try Task.checkCancellation()

        // Or use Task.isCancelled
        if Task.isCancelled {
            print("Task cancelled")
            return
        }

        await performStep(i)
    }
}

// Cancel the task
task.cancel()
```

### Task Values

```swift
let task = Task {
    await fetchData()
}

// Wait for task to complete and get value
let data = await task.value

// Task with error handling
let task = Task<String, Error> {
    try await fetchUserName()
}

do {
    let name = try await task.value
    print("Name: \(name)")
} catch {
    print("Error: \(error)")
}
```

### Task Priority

```swift
Task(priority: .high) {
    // High priority work
}

Task(priority: .low) {
    // Low priority work
}

// Available priorities:
// .high, .medium, .low, .background, .userInitiated, .utility
```

### Task Sleep

```swift
// Sleep for duration
try await Task.sleep(nanoseconds: 1_000_000_000) // 1 second
try await Task.sleep(for: .seconds(1))            // Swift 5.7+

// Until deadline
try await Task.sleep(until: .now + .seconds(5), clock: .continuous)
```

## Task Groups

### Structured Concurrency with Task Groups

```swift
func fetchMultipleUsers(ids: [String]) async throws -> [User] {
    try await withThrowingTaskGroup(of: User.self) { group in
        var users: [User] = []

        // Add tasks to group
        for id in ids {
            group.addTask {
                try await fetchUser(id: id)
            }
        }

        // Collect results
        for try await user in group {
            users.append(user)
        }

        return users
    }
}
```

### Non-Throwing Task Groups

```swift
func loadImages(urls: [URL]) async -> [UIImage] {
    await withTaskGroup(of: UIImage?.self) { group in
        var images: [UIImage] = []

        for url in urls {
            group.addTask {
                try? await loadImage(from: url)
            }
        }

        for await image in group {
            if let image = image {
                images.append(image)
            }
        }

        return images
    }
}
```

### Task Group with Early Exit

```swift
func findFirst(matching condition: @escaping (Item) -> Bool) async -> Item? {
    await withTaskGroup(of: Item?.self) { group in
        for item in items {
            group.addTask {
                if condition(item) {
                    return item
                }
                return nil
            }
        }

        for await result in group {
            if let found = result {
                group.cancelAll() // Cancel remaining tasks
                return found
            }
        }

        return nil
    }
}
```

### Collecting Task Group Results

```swift
func processInParallel(_ items: [Item]) async throws -> [Result] {
    try await withThrowingTaskGroup(of: Result.self) { group in
        for item in items {
            group.addTask {
                try await process(item)
            }
        }

        // Reduce pattern
        return try await group.reduce(into: []) { results, result in
            results.append(result)
        }
    }
}
```

## Actors

### Basic Actor

```swift
actor Counter {
    private var value = 0

    func increment() {
        value += 1
    }

    func getValue() -> Int {
        value
    }
}

// Usage
let counter = Counter()

Task {
    await counter.increment()
    let value = await counter.getValue()
    print("Count: \(value)")
}
```

### Actor Isolation

```swift
actor BankAccount {
    private var balance: Decimal = 0

    // Isolated to actor (safe)
    func deposit(_ amount: Decimal) {
        balance += amount
    }

    // Isolated to actor (safe)
    func withdraw(_ amount: Decimal) throws {
        guard balance >= amount else {
            throw BankError.insufficientFunds
        }
        balance -= amount
    }

    // Nonisolated method (can be called synchronously)
    nonisolated func getAccountInfo() -> AccountInfo {
        AccountInfo(accountNumber: accountNumber)
    }
}
```

### Actor Reentrancy

```swift
actor ImageDownloader {
    private var cache: [URL: UIImage] = [:]

    func image(from url: URL) async throws -> UIImage {
        // Check cache
        if let cached = cache[url] {
            return cached
        }

        // Download (suspension point - actor can be reentered here)
        let (data, _) = try await URLSession.shared.data(from: url)

        // After await, state might have changed!
        // Check cache again
        if let cached = cache[url] {
            return cached
        }

        let image = UIImage(data: data)!
        cache[url] = image
        return image
    }
}
```

### Global Actor

```swift
@globalActor
actor DatabaseActor {
    static let shared = DatabaseActor()
}

// Mark function to run on global actor
@DatabaseActor
func saveToDatabase(_ data: Data) {
    // This runs isolated to DatabaseActor
}

// Mark type to run on global actor
@DatabaseActor
class DatabaseManager {
    // All methods isolated to DatabaseActor
    func save(_ item: Item) {
        // ...
    }
}
```

### MainActor

```swift
// Run on main thread
@MainActor
func updateUI() {
    // UI updates here
}

// Mark class for main thread
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [Item] = []

    func loadItems() async {
        let items = await fetchItems()
        // Already on MainActor
        self.items = items
    }
}

// Explicitly run on main actor
await MainActor.run {
    updateUI()
}
```

## Sendable

### Sendable Protocol

```swift
// Value types are automatically Sendable if all properties are Sendable
struct User: Sendable {
    let id: String
    let name: String
}

// Explicitly conform
class ImmutableUser: Sendable {
    let id: String
    let name: String

    init(id: String, name: String) {
        self.id = id
        self.name = name
    }
}
```

### @unchecked Sendable

```swift
// When you know it's safe but compiler can't verify
class ThreadSafeCache: @unchecked Sendable {
    private let lock = NSLock()
    private var storage: [String: Any] = [:]

    func get(_ key: String) -> Any? {
        lock.lock()
        defer { lock.unlock() }
        return storage[key]
    }

    func set(_ key: String, value: Any) {
        lock.lock()
        defer { lock.unlock() }
        storage[key] = value
    }
}
```

### Sendable Closures

```swift
func performAsync(_ operation: @Sendable @escaping () -> Void) {
    Task.detached {
        operation()
    }
}

// Sendable closure cannot capture mutable variables
var counter = 0

// Error: mutable capture
performAsync {
    counter += 1
}

// OK: immutable capture
let value = 42
performAsync {
    print(value)
}
```

## AsyncStream

### Creating AsyncStream

```swift
func countdown(from: Int) -> AsyncStream<Int> {
    AsyncStream { continuation in
        Task {
            for i in (1...from).reversed() {
                continuation.yield(i)
                try? await Task.sleep(nanoseconds: 1_000_000_000)
            }
            continuation.finish()
        }
    }
}

// Usage
for await number in countdown(from: 5) {
    print(number)
}
```

### AsyncThrowingStream

```swift
func watchFile(at url: URL) -> AsyncThrowingStream<String, Error> {
    AsyncThrowingStream { continuation in
        let monitor = FileMonitor(url: url) { line in
            continuation.yield(line)
        } onError: { error in
            continuation.finish(throwing: error)
        }

        continuation.onTermination = { _ in
            monitor.stop()
        }

        monitor.start()
    }
}

// Usage
do {
    for try await line in watchFile(at: logURL) {
        print(line)
    }
} catch {
    print("Error: \(error)")
}
```

### Buffering Strategy

```swift
// Buffer unlimited
AsyncStream(Int.self, bufferingPolicy: .unbounded) { continuation in
    // ...
}

// Buffer with limit
AsyncStream(Int.self, bufferingPolicy: .bufferingOldest(10)) { continuation in
    // Drops oldest values when buffer is full
}

// Buffer newest
AsyncStream(Int.self, bufferingPolicy: .bufferingNewest(10)) { continuation in
    // Drops newest values when buffer is full
}
```

## Continuation

### Async Continuation

```swift
func legacyAPI(completion: @escaping (Result<Data, Error>) -> Void) {
    // Old callback-based API
}

func modernAPI() async throws -> Data {
    try await withCheckedThrowingContinuation { continuation in
        legacyAPI { result in
            continuation.resume(with: result)
        }
    }
}
```

### Non-Throwing Continuation

```swift
func loadData() async -> Data? {
    await withCheckedContinuation { continuation in
        loadDataCallback { data in
            continuation.resume(returning: data)
        }
    }
}
```

### Unsafe Continuation

```swift
// When you need better performance and can guarantee safety
func unsafeModernAPI() async throws -> Data {
    try await withUnsafeThrowingContinuation { continuation in
        legacyAPI { result in
            continuation.resume(with: result)
        }
    }
}

// MUST call resume exactly once!
```

## TaskLocal

### Defining Task Local Values

```swift
enum RequestID {
    @TaskLocal static var current: UUID?
}

func processRequest() async {
    RequestID.$current.withValue(UUID()) {
        await handleRequest()
    }
}

func handleRequest() async {
    if let id = RequestID.current {
        print("Processing request: \(id)")
    }
}
```

### Nested Task Local Values

```swift
enum Logger {
    @TaskLocal static var context: [String: String] = [:]
}

func outerOperation() async {
    Logger.$context.withValue(["user": "john"]) {
        await innerOperation()
    }
}

func innerOperation() async {
    Logger.$context.withValue(
        Logger.context.merging(["operation": "fetch"], uniquingKeysWith: { $1 })
    ) {
        print(Logger.context) // ["user": "john", "operation": "fetch"]
    }
}
```

## Async Let

### Concurrent Binding

```swift
func loadData() async throws -> (User, [Post], [Comment]) {
    async let user = fetchUser()
    async let posts = fetchPosts()
    async let comments = fetchComments()

    return try await (user, posts, comments)
}

// All three fetch operations run concurrently
```

### Error Handling with Async Let

```swift
func complexOperation() async throws -> Result {
    async let part1 = try fetchPart1()
    async let part2 = try fetchPart2()

    // If either throws, both are cancelled
    let (p1, p2) = try await (part1, part2)

    return combine(p1, p2)
}
```

## Best Practices

### 1. Prefer Structured Concurrency

```swift
// ✅ Good: Structured with task group
func loadAll() async throws -> [Item] {
    try await withThrowingTaskGroup(of: Item.self) { group in
        for id in itemIDs {
            group.addTask { try await fetch(id) }
        }
        return try await group.reduce(into: []) { $0.append($1) }
    }
}

// ❌ Bad: Unstructured tasks
func loadAll() async throws -> [Item] {
    var items: [Item] = []
    for id in itemIDs {
        Task {
            let item = try await fetch(id)
            items.append(item) // Race condition!
        }
    }
    return items // Might not be complete!
}
```

### 2. Handle Cancellation

```swift
func longRunningTask() async throws {
    for i in 1...1000 {
        // Check periodically
        try Task.checkCancellation()

        await processItem(i)
    }
}

// With cleanup
func taskWithCleanup() async throws {
    defer {
        // Cleanup runs even if cancelled
        cleanup()
    }

    try Task.checkCancellation()
    await doWork()
}
```

### 3. Actor Design

```swift
// ✅ Good: Minimize time in actor
actor GoodCache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key] // Fast, synchronous
    }

    func set(_ key: String, data: Data) {
        storage[key] = data // Fast, synchronous
    }
}

// ❌ Bad: Long async operations in actor
actor BadCache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) async -> Data {
        if let cached = storage[key] {
            return cached
        }

        // Bad: Long network call while holding actor
        let data = await fetchFromNetwork(key)
        storage[key] = data
        return data
    }
}

// ✅ Better: Do async work outside actor
actor BetterCache {
    private var storage: [String: Data] = [:]

    func get(_ key: String) -> Data? {
        storage[key]
    }

    func set(_ key: String, data: Data) {
        storage[key] = data
    }
}

func getData(key: String, cache: BetterCache) async -> Data {
    if let cached = await cache.get(key) {
        return cached
    }

    let data = await fetchFromNetwork(key)
    await cache.set(key, data: data)
    return data
}
```

### 4. MainActor Usage

```swift
// ✅ Good: Mark view model for main thread
@MainActor
class ViewModel: ObservableObject {
    @Published var items: [Item] = []

    func loadItems() async {
        // Do background work
        let items = await fetchItems()

        // Update UI - already on main thread
        self.items = items
    }
}

// ✅ Good: Switch to main thread only for UI updates
class ViewModel: ObservableObject {
    @Published var items: [Item] = []

    func loadItems() async {
        let items = await fetchItems()

        await MainActor.run {
            self.items = items
        }
    }
}
```

### 5. Avoid Data Races

```swift
// ❌ Bad: Shared mutable state
var counter = 0

Task {
    counter += 1 // Race condition
}

Task {
    counter += 1 // Race condition
}

// ✅ Good: Use actor
actor Counter {
    var value = 0

    func increment() {
        value += 1
    }
}

let counter = Counter()
Task { await counter.increment() }
Task { await counter.increment() }
```

### 6. Task Lifetime Management

```swift
class ViewController: UIViewController {
    private var loadTask: Task<Void, Never>?

    override func viewDidLoad() {
        super.viewDidLoad()

        loadTask = Task {
            await loadData()
        }
    }

    override func viewDidDisappear(_ animated: Bool) {
        super.viewDidDisappear(animated)

        // Cancel when view disappears
        loadTask?.cancel()
        loadTask = nil
    }
}
```

### 7. Error Propagation

```swift
// ✅ Good: Proper error handling
func loadData() async throws -> Data {
    let url = URL(string: "https://api.example.com/data")!

    do {
        let (data, response) = try await URLSession.shared.data(from: url)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NetworkError.invalidResponse
        }

        return data
    } catch {
        // Log error, perform cleanup
        print("Failed to load data: \(error)")
        throw error
    }
}
```

## Common Patterns

### Retry with Exponential Backoff

```swift
func retryWithBackoff<T>(
    maxAttempts: Int = 3,
    operation: @Sendable () async throws -> T
) async throws -> T {
    var attempt = 0

    while true {
        attempt += 1

        do {
            return try await operation()
        } catch {
            if attempt >= maxAttempts {
                throw error
            }

            let delay = UInt64(pow(2.0, Double(attempt)) * 1_000_000_000)
            try await Task.sleep(nanoseconds: delay)
        }
    }
}

// Usage
let data = try await retryWithBackoff {
    try await fetchData()
}
```

### Timeout

```swift
func withTimeout<T>(
    seconds: TimeInterval,
    operation: @escaping @Sendable () async throws -> T
) async throws -> T {
    try await withThrowingTaskGroup(of: T.self) { group in
        group.addTask {
            try await operation()
        }

        group.addTask {
            try await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
            throw TimeoutError()
        }

        let result = try await group.next()!
        group.cancelAll()
        return result
    }
}

// Usage
let data = try await withTimeout(seconds: 5) {
    try await fetchData()
}
```

### Debounce

```swift
actor Debouncer {
    private var task: Task<Void, Never>?

    func debounce(for duration: Duration, operation: @Sendable @escaping () async -> Void) {
        task?.cancel()

        task = Task {
            try? await Task.sleep(for: duration)

            if !Task.isCancelled {
                await operation()
            }
        }
    }
}

// Usage
let debouncer = Debouncer()

func searchTextChanged(_ text: String) async {
    await debouncer.debounce(for: .milliseconds(300)) {
        await performSearch(text)
    }
}
```

### Rate Limiting

```swift
actor RateLimiter {
    private var lastExecutionTime: ContinuousClock.Instant?
    private let minimumInterval: Duration

    init(minimumInterval: Duration) {
        self.minimumInterval = minimumInterval
    }

    func execute<T>(_ operation: @Sendable () async throws -> T) async throws -> T {
        if let lastTime = lastExecutionTime {
            let elapsed = ContinuousClock.now.duration(to: lastTime)
            if elapsed < minimumInterval {
                try await Task.sleep(for: minimumInterval - elapsed)
            }
        }

        lastExecutionTime = .now
        return try await operation()
    }
}

// Usage
let limiter = RateLimiter(minimumInterval: .seconds(1))

for request in requests {
    try await limiter.execute {
        try await sendRequest(request)
    }
}
```

## Migration from Completion Handlers

### Before (Completion Handler)

```swift
func fetchUser(id: String, completion: @escaping (Result<User, Error>) -> Void) {
    URLSession.shared.dataTask(with: url) { data, response, error in
        if let error = error {
            completion(.failure(error))
            return
        }

        guard let data = data else {
            completion(.failure(NetworkError.noData))
            return
        }

        do {
            let user = try JSONDecoder().decode(User.self, from: data)
            completion(.success(user))
        } catch {
            completion(.failure(error))
        }
    }.resume()
}
```

### After (Async/Await)

```swift
func fetchUser(id: String) async throws -> User {
    let (data, _) = try await URLSession.shared.data(from: url)
    return try JSONDecoder().decode(User.self, from: data)
}
```

## Performance Considerations

1. **Task Overhead**: Creating tasks has overhead; don't create thousands of tiny tasks
2. **Actor Contention**: Minimize time spent in actors; do heavy work outside
3. **Suspension Points**: Each `await` is a potential suspension; cache values if needed
4. **Task Priority**: Use appropriate priorities to avoid priority inversion
5. **Cancellation Checking**: Check cancellation frequently in long-running operations

## Swift 6 Concurrency Changes

### Complete Concurrency Checking

Swift 6 enables strict concurrency checking by default:

```swift
// Swift 6: Must be Sendable
func process(_ data: Data) async {
    Task {
        // data must be Sendable
        await upload(data)
    }
}

// Swift 6: Data races detected at compile time
class ViewModel {
    var items: [Item] = [] // Error: shared mutable state

    func update() {
        Task {
            items.append(newItem) // Compile error
        }
    }
}
```

### Typed Throws (Swift 6)

```swift
func fetchData() async throws(NetworkError) -> Data {
    // Can only throw NetworkError
}

do {
    let data = try await fetchData()
} catch {
    // error is NetworkError, not general Error
    switch error {
    case .timeout:
        // handle timeout
    case .serverError(let code):
        // handle server error
    }
}
```
