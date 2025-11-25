# Objective-C to Swift 6 Migration Guide

Comprehensive guide for migrating legacy Objective-C patterns to modern Swift 6, focusing on concurrency, data flow, error handling, and API design.

## Overview

Swift 6 introduces significant improvements over legacy Objective-C patterns, particularly in concurrency safety, type safety, and API design. This guide provides practical before-and-after examples for common migration scenarios.

**Key Swift 6 Features:**
- Structured concurrency with complete data-race safety checking
- Actors for automatic isolation and thread safety
- @Observable macro for reactive state management
- Typed throws for precise error handling
- Sendable protocol for concurrency safety

---

## 1. Concurrency Migration

### 1.1 From GCD to Structured Concurrency

Grand Central Dispatch (GCD) requires manual queue management and leads to nested closures. Swift 6's structured concurrency provides a linear, safer approach.

#### Basic Background Work + UI Update

**Before (Objective-C):**
```objc
// Nested GCD pattern - common but error-prone
dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
    // Perform background work
    NSData *data = [self fetchDataFromNetwork];
    id result = [self processData:data];

    // Update UI on main queue
    dispatch_async(dispatch_get_main_queue(), ^{
        [self.delegate didReceiveResult:result];
        [self.progressView setHidden:YES];
    });
});
```

**After (Swift 6):**
```swift
// Structured concurrency - linear and type-safe
Task {
    // Background work happens automatically off main thread
    let data = await fetchDataFromNetwork()
    let result = await processData(data)

    // UI updates automatically on main thread
    await MainActor.run {
        delegate?.didReceive(result: result)
        progressView.isHidden = true
    }
}
```

**Benefits:**
- **Linear control flow**: No callback nesting, easier to read
- **Automatic error propagation**: Errors bubble up naturally with try/await
- **Cancellation support**: Task cancellation propagates automatically
- **Type safety**: Compiler ensures proper async/await usage

#### Multiple Concurrent Operations

**Before (Objective-C):**
```objc
// dispatch_group for coordinating multiple operations
dispatch_group_t group = dispatch_group_create();
NSMutableArray *results = [NSMutableArray array];

for (NSString *userID in userIDs) {
    dispatch_group_enter(group);
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        User *user = [self fetchUserWithID:userID];
        @synchronized(results) {
            [results addObject:user];
        }
        dispatch_group_leave(group);
    });
}

dispatch_group_notify(group, dispatch_get_main_queue(), ^{
    [self processUsers:results];
});
```

**After (Swift 6):**
```swift
// TaskGroup for structured parallelism
Task {
    let users = await withTaskGroup(of: User.self) { group in
        var results: [User] = []

        for userID in userIDs {
            group.addTask {
                await self.fetchUser(withID: userID)
            }
        }

        for await user in group {
            results.append(user)
        }

        return results
    }

    await processUsers(users)
}
```

**Benefits:**
- **Automatic synchronization**: No need for @synchronized
- **Error handling**: Use withThrowingTaskGroup for errors
- **Type safety**: Compiler verifies all tasks return same type
- **Structured lifetime**: All tasks complete before continuation

### 1.2 From NSOperationQueue to TaskGroup

NSOperationQueue provides operation dependencies but with complex setup. TaskGroup offers similar capabilities with clearer syntax.

**Before (Objective-C):**
```objc
NSOperationQueue *queue = [[NSOperationQueue alloc] init];
queue.maxConcurrentOperationCount = 3;

NSOperation *downloadOp = [NSBlockOperation blockOperationWithBlock:^{
    [self downloadImages];
}];

NSOperation *processOp = [NSBlockOperation blockOperationWithBlock:^{
    [self processImages];
}];

NSOperation *uploadOp = [NSBlockOperation blockOperationWithBlock:^{
    [self uploadResults];
}];

// Set up dependencies
[processOp addDependency:downloadOp];
[uploadOp addDependency:processOp];

[queue addOperations:@[downloadOp, processOp, uploadOp] waitUntilFinished:NO];
```

**After (Swift 6):**
```swift
// Sequential pipeline with async/await
Task {
    do {
        let images = try await downloadImages()
        let processed = try await processImages(images)
        try await uploadResults(processed)
    } catch {
        handleError(error)
    }
}

// Or with explicit task dependencies using TaskGroup
Task {
    try await withThrowingTaskGroup(of: Void.self) { group in
        // Download phase
        group.addTask {
            try await self.downloadImages()
        }
        try await group.waitForAll()

        // Process phase (depends on download)
        group.addTask {
            try await self.processImages()
        }
        try await group.waitForAll()

        // Upload phase (depends on process)
        group.addTask {
            try await self.uploadResults()
        }
        try await group.waitForAll()
    }
}
```

**Benefits:**
- **Clearer dependencies**: Sequential code expresses dependencies naturally
- **Better error handling**: try/await provides structured error flow
- **Simpler cancellation**: Task cancellation is built-in
- **Type-safe results**: Return values are type-checked

### 1.3 From Locks to Actors

Thread-safety mechanisms like @synchronized and NSLock are error-prone. Swift actors provide compiler-enforced isolation.

**Before (Objective-C):**
```objc
@interface UserCache : NSObject
@property (nonatomic, strong) NSMutableDictionary<NSString *, User *> *cache;
@property (nonatomic, strong) NSLock *lock;
@end

@implementation UserCache

- (instancetype)init {
    if (self = [super init]) {
        _cache = [NSMutableDictionary dictionary];
        _lock = [[NSLock alloc] init];
    }
    return self;
}

- (void)storeUser:(User *)user forID:(NSString *)userID {
    [self.lock lock];
    self.cache[userID] = user;
    [self.lock unlock];
}

- (User *)userForID:(NSString *)userID {
    [self.lock lock];
    User *user = self.cache[userID];
    [self.lock unlock];
    return user;
}

@end
```

**After (Swift 6):**
```swift
// Actor provides automatic isolation
actor UserCache {
    private var cache: [String: User] = [:]

    // No locks needed - actor ensures thread safety
    func store(_ user: User, for id: String) {
        cache[id] = user
    }

    func user(for id: String) -> User? {
        cache[id]
    }

    // Batch operations are atomic
    func storeUsers(_ users: [User]) {
        for user in users {
            cache[user.id] = user
        }
    }
}

// Usage
Task {
    await userCache.store(user, for: userID)
    let retrievedUser = await userCache.user(for: userID)
}
```

**Benefits:**
- **Compiler-enforced safety**: Data races caught at compile time
- **No manual locking**: Actor runtime manages synchronization
- **Deadlock prevention**: Actors can't create deadlocks
- **Sendable checking**: Swift 6 verifies safe data passing

#### Advanced Actor Pattern: Singleton with Cleanup

**Before (Objective-C with @synchronized):**
```objc
@implementation DataManager

+ (instancetype)sharedManager {
    static DataManager *instance = nil;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        instance = [[self alloc] init];
    });
    return instance;
}

- (void)updateData:(id)data forKey:(NSString *)key {
    @synchronized(self) {
        [self.dataStore setObject:data forKey:key];
        [self notifyObservers];
    }
}

@end
```

**After (Swift 6):**
```swift
actor DataManager {
    static let shared = DataManager()

    private var dataStore: [String: Any] = [:]
    private var observers: [DataObserver] = []

    private init() {}

    func updateData(_ data: Any, for key: String) {
        dataStore[key] = data
        notifyObservers()
    }

    private func notifyObservers() {
        // Automatically isolated - no synchronization needed
        observers.forEach { $0.dataDidUpdate() }
    }

    // Nonisolated for synchronous access to immutable data
    nonisolated var observerCount: Int {
        // Must be computed without accessing isolated state
        0 // In practice, use isolated async access
    }
}
```

---

## 2. Data Flow & State Management

### 2.1 From KVO to @Observable

Key-Value Observing requires manual setup/teardown and string-based key paths. Swift 6's @Observable macro provides type-safe reactive bindings.

**Before (Objective-C):**
```objc
// Model with KVO support
@interface UserProfile : NSObject
@property (nonatomic, strong) NSString *name;
@property (nonatomic, assign) NSInteger age;
@end

@implementation UserProfile

+ (NSSet *)keyPathsForValuesAffectingDisplayName {
    return [NSSet setWithObjects:@"name", @"age", nil];
}

- (NSString *)displayName {
    return [NSString stringWithFormat:@"%@ (%ld)", self.name, (long)self.age];
}

@end

// Observer setup
@interface ProfileViewController : UIViewController
@property (nonatomic, strong) UserProfile *profile;
@end

@implementation ProfileViewController

- (void)viewDidLoad {
    [super viewDidLoad];

    [self.profile addObserver:self
                   forKeyPath:@"name"
                      options:NSKeyValueObservingOptionNew
                      context:NULL];
}

- (void)observeValueForKeyPath:(NSString *)keyPath
                      ofObject:(id)object
                        change:(NSDictionary *)change
                       context:(void *)context {
    if ([keyPath isEqualToString:@"name"]) {
        dispatch_async(dispatch_get_main_queue(), ^{
            self.nameLabel.text = self.profile.name;
        });
    }
}

- (void)dealloc {
    [self.profile removeObserver:self forKeyPath:@"name"];
}

@end
```

**After (Swift 6):**
```swift
import Observation

// Model with @Observable macro (Swift 5.9+)
@Observable
class UserProfile {
    var name: String = ""
    var age: Int = 0

    var displayName: String {
        "\(name) (\(age))"
    }
}

// SwiftUI view (automatic observation)
struct ProfileView: View {
    @State private var profile = UserProfile()

    var body: some View {
        VStack {
            Text(profile.displayName)
                .font(.headline)

            TextField("Name", text: $profile.name)
            Stepper("Age: \(profile.age)", value: $profile.age)
        }
    }
}

// UIKit integration
class ProfileViewController: UIViewController {
    let profile = UserProfile()

    override func viewDidLoad() {
        super.viewDidLoad()

        // Observe changes with Combine (iOS 13+)
        withObservationTracking {
            _ = profile.name
        } onChange: {
            Task { @MainActor in
                nameLabel.text = profile.name
            }
        }
    }
}
```

**Benefits:**
- **Type safety**: No string-based key paths
- **Automatic cleanup**: No manual observer removal
- **Compiler support**: Unused observations warned
- **SwiftUI integration**: Seamless reactive updates

#### Alternative: Combine for iOS 13+ Compatibility

```swift
import Combine

class UserProfile: ObservableObject {
    @Published var name: String = ""
    @Published var age: Int = 0

    var displayName: String {
        "\(name) (\(age))"
    }
}

class ProfileViewController: UIViewController {
    let profile = UserProfile()
    private var cancellables = Set<AnyCancellable>()

    override func viewDidLoad() {
        super.viewDidLoad()

        profile.$name
            .receive(on: DispatchQueue.main)
            .sink { [weak self] newName in
                self?.nameLabel.text = newName
            }
            .store(in: &cancellables)
    }
}
```

### 2.2 From NSNotificationCenter to AsyncStream

NSNotificationCenter uses selector-based callbacks. AsyncStream provides modern iteration-based notification handling.

**Before (Objective-C):**
```objc
@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(keyboardWillShow:)
                                                 name:UIKeyboardWillShowNotification
                                               object:nil];

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(keyboardWillHide:)
                                                 name:UIKeyboardWillHideNotification
                                               object:nil];
}

- (void)keyboardWillShow:(NSNotification *)notification {
    NSDictionary *userInfo = notification.userInfo;
    CGRect keyboardFrame = [[userInfo objectForKey:UIKeyboardFrameEndUserInfoKey] CGRectValue];
    [self adjustLayoutForKeyboardHeight:keyboardFrame.size.height];
}

- (void)keyboardWillHide:(NSNotification *)notification {
    [self adjustLayoutForKeyboardHeight:0];
}

- (void)dealloc {
    [[NSNotificationCenter defaultCenter] removeObserver:self];
}

@end
```

**After (Swift 6):**
```swift
import UIKit

class ViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()

        // Modern async approach with AsyncStream
        Task {
            for await notification in NotificationCenter.default.notifications(named: UIResponder.keyboardWillShowNotification) {
                if let keyboardFrame = notification.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? CGRect {
                    await adjustLayout(for: keyboardFrame.height)
                }
            }
        }

        Task {
            for await _ in NotificationCenter.default.notifications(named: UIResponder.keyboardWillHideNotification) {
                await adjustLayout(for: 0)
            }
        }
    }

    @MainActor
    func adjustLayout(for keyboardHeight: CGFloat) {
        // UI updates automatically on main actor
        view.frame.origin.y = -keyboardHeight
    }
}

// Extension for AsyncStream convenience
extension NotificationCenter {
    func notifications(named name: Notification.Name) -> AsyncStream<Notification> {
        AsyncStream { continuation in
            let observer = addObserver(forName: name, object: nil, queue: nil) { notification in
                continuation.yield(notification)
            }

            continuation.onTermination = { @Sendable _ in
                removeObserver(observer)
            }
        }
    }
}
```

**Alternative: Combine Publishers**
```swift
import Combine

class ViewController: UIViewController {
    private var cancellables = Set<AnyCancellable>()

    override func viewDidLoad() {
        super.viewDidLoad()

        NotificationCenter.default
            .publisher(for: UIResponder.keyboardWillShowNotification)
            .compactMap { $0.userInfo?[UIResponder.keyboardFrameEndUserInfoKey] as? CGRect }
            .sink { [weak self] keyboardFrame in
                self?.adjustLayout(for: keyboardFrame.height)
            }
            .store(in: &cancellables)
    }
}
```

**Benefits:**
- **Automatic cleanup**: Task cancellation removes observers
- **Type-safe**: Generic AsyncStream typing
- **Modern control flow**: for await loops vs callbacks
- **Structured lifetime**: Observation tied to task lifetime

---

## 3. Error Handling Patterns

### 3.1 From NSError** to throws

Objective-C error handling uses out parameters. Swift's throws provides cleaner error propagation.

**Before (Objective-C):**
```objc
- (BOOL)saveData:(NSData *)data toFile:(NSString *)path error:(NSError **)error {
    NSFileManager *manager = [NSFileManager defaultManager];

    if (![manager fileExistsAtPath:[path stringByDeletingLastPathComponent]]) {
        if (error != NULL) {
            *error = [NSError errorWithDomain:@"com.example.app"
                                         code:404
                                     userInfo:@{NSLocalizedDescriptionKey: @"Directory not found"}];
        }
        return NO;
    }

    BOOL success = [data writeToFile:path atomically:YES];
    if (!success && error != NULL) {
        *error = [NSError errorWithDomain:@"com.example.app"
                                     code:500
                                 userInfo:@{NSLocalizedDescriptionKey: @"Failed to write file"}];
    }

    return success;
}

// Usage
NSError *error = nil;
BOOL success = [self saveData:data toFile:path error:&error];
if (!success) {
    NSLog(@"Error: %@", error.localizedDescription);
}
```

**After (Swift 6):**
```swift
enum FileError: Error {
    case directoryNotFound
    case writeFailed
    case permissionDenied
}

func saveData(_ data: Data, to path: String) throws {
    let fileManager = FileManager.default
    let directory = (path as NSString).deletingLastPathComponent

    guard fileManager.fileExists(atPath: directory) else {
        throw FileError.directoryNotFound
    }

    do {
        try data.write(to: URL(fileURLWithPath: path), options: .atomic)
    } catch {
        throw FileError.writeFailed
    }
}

// Usage
do {
    try saveData(data, to: path)
} catch FileError.directoryNotFound {
    print("Directory not found")
} catch FileError.writeFailed {
    print("Failed to write file")
} catch {
    print("Unexpected error: \(error)")
}
```

**Benefits:**
- **Cleaner syntax**: No error pointers or BOOL returns
- **Automatic propagation**: Errors bubble up with try
- **Type-safe errors**: Enum errors vs generic NSError
- **Compiler enforcement**: Must handle or propagate errors

### 3.2 Typed Throws (Swift 6)

Swift 6 introduces typed throws for even more precise error handling.

**Swift 5.x:**
```swift
func loadUser(id: String) throws -> User {
    // Can throw any Error type
    throw NSError(domain: "error", code: 1)
}
```

**Swift 6 with Typed Throws:**
```swift
enum UserError: Error {
    case notFound
    case invalidData
    case networkFailure
}

// Explicitly typed error
func loadUser(id: String) throws(UserError) -> User {
    guard let data = try fetchUserData(id) else {
        throw UserError.notFound
    }

    guard let user = try parseUser(data) else {
        throw UserError.invalidData
    }

    return user
}

// Usage with exhaustive error handling
do {
    let user = try loadUser(id: "123")
} catch UserError.notFound {
    // Specific handling
} catch UserError.invalidData {
    // Specific handling
} catch UserError.networkFailure {
    // Specific handling
}
// Compiler ensures all cases handled - no default needed
```

**Benefits:**
- **Compile-time error verification**: Know exact errors thrown
- **Exhaustive switching**: Compiler ensures all errors handled
- **Better API contracts**: Callers know what to expect
- **No unexpected errors**: Type system prevents error leakage

---

## 4. API Design Patterns

### 4.1 From Delegates to async/await

Delegate protocols create callback complexity. Async/await simplifies call sites.

**Before (Objective-C):**
```objc
// Delegate protocol
@protocol DataFetcherDelegate <NSObject>
- (void)dataFetcher:(DataFetcher *)fetcher didFetchData:(NSData *)data;
- (void)dataFetcher:(DataFetcher *)fetcher didFailWithError:(NSError *)error;
@end

@interface DataFetcher : NSObject
@property (nonatomic, weak) id<DataFetcherDelegate> delegate;
- (void)fetchDataFromURL:(NSURL *)url;
@end

@implementation DataFetcher

- (void)fetchDataFromURL:(NSURL *)url {
    NSURLSession *session = [NSURLSession sharedSession];
    NSURLSessionDataTask *task = [session dataTaskWithURL:url completionHandler:^(NSData *data, NSURLResponse *response, NSError *error) {
        if (error) {
            [self.delegate dataFetcher:self didFailWithError:error];
        } else {
            [self.delegate dataFetcher:self didFetchData:data];
        }
    }];
    [task resume];
}

@end

// Usage
@interface ViewController () <DataFetcherDelegate>
@property (nonatomic, strong) DataFetcher *fetcher;
@end

@implementation ViewController

- (void)loadData {
    self.fetcher.delegate = self;
    [self.fetcher fetchDataFromURL:url];
}

- (void)dataFetcher:(DataFetcher *)fetcher didFetchData:(NSData *)data {
    // Handle success
}

- (void)dataFetcher:(DataFetcher *)fetcher didFailWithError:(NSError *)error {
    // Handle error
}

@end
```

**After (Swift 6):**
```swift
class DataFetcher {
    func fetchData(from url: URL) async throws -> Data {
        let (data, _) = try await URLSession.shared.data(from: url)
        return data
    }
}

// Usage - dramatically simpler
class ViewController {
    let fetcher = DataFetcher()

    func loadData() async {
        do {
            let data = try await fetcher.fetchData(from: url)
            // Handle success - linear code flow
            await processData(data)
        } catch {
            // Handle error
            await showError(error)
        }
    }
}
```

**Benefits:**
- **Linear code flow**: No delegate callbacks
- **Clear ownership**: No weak delegate references
- **Better error handling**: try/catch vs delegate methods
- **Composable**: Easy to chain async operations

---

## 5. Common Swift 6 Patterns

### 5.1 MainActor for UI Code

Ensure UI updates happen on the main thread without manual dispatch.

**Before (Objective-C):**
```objc
- (void)updateUIWithData:(id)data {
    dispatch_async(dispatch_get_main_queue(), ^{
        self.label.text = data.description;
        [self.tableView reloadData];
    });
}
```

**After (Swift 6):**
```swift
@MainActor
func updateUI(with data: Any) {
    // Automatically runs on main thread
    label.text = data.description
    tableView.reloadData()
}

// Or for entire class
@MainActor
class ViewController: UIViewController {
    // All methods automatically on main actor
    func updateLabel(_ text: String) {
        label.text = text  // Safe - guaranteed main thread
    }
}
```

### 5.2 Sendable Conformance

Swift 6's complete concurrency checking requires Sendable for data crossing isolation boundaries.

```swift
// Value types are automatically Sendable
struct User: Sendable {
    let id: String
    let name: String
}

// Class must explicitly conform
final class UserCache: Sendable {
    // Must be let or actor-isolated
    let cache: [String: User]

    init(cache: [String: User]) {
        self.cache = cache
    }
}

// @unchecked Sendable for types with manual synchronization
class LegacyCache: @unchecked Sendable {
    private let lock = NSLock()
    private var data: [String: Any] = [:]

    func store(_ value: Any, for key: String) {
        lock.lock()
        data[key] = value
        lock.unlock()
    }
}
```

---

## 6. Migration Strategy

### Phase 1: Assessment
1. Run `scripts/migration_analyzer.py` on your codebase
2. Review high-priority modernization targets
3. Identify modules suitable for Swift 6 strict concurrency

### Phase 2: Foundation
1. Enable Swift 6 language mode in new files
2. Migrate model layer to value types (structs)
3. Add Sendable conformance to data models

### Phase 3: Concurrency Modernization
1. Convert GCD to Task-based structured concurrency
2. Replace @synchronized/NSLock with actors
3. Mark UI classes with @MainActor
4. Enable complete concurrency checking

### Phase 4: Reactive Patterns
1. Migrate KVO to @Observable (Swift 5.9+) or Combine
2. Replace NSNotificationCenter with AsyncStream
3. Update delegates to async/await where appropriate

### Phase 5: Polish
1. Apply typed throws for precise error handling
2. Audit Sendable conformance
3. Enable strict concurrency warnings
4. Run concurrency safety checks

---

## Resources

- [Swift Evolution: Concurrency](https://github.com/apple/swift-evolution/blob/main/proposals/0306-actors.md)
- [Observation Framework (WWDC 2023)](https://developer.apple.com/documentation/observation)
- [Swift Concurrency by Example](https://www.hackingwithswift.com/quick-start/concurrency)
- Migration analyzer: `scripts/migration_analyzer.py`
