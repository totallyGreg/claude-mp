//
// ActorSingleton.swift
// Modern thread-safe singleton pattern using Swift actors
//
// Replaces Objective-C patterns using @synchronized, NSLock, or dispatch queues
// for thread-safe singleton access.
//
// Swift 5.5+ (iOS 13+, macOS 10.15+)

import Foundation

// MARK: - Basic Actor Singleton Pattern

/// Thread-safe service locator using Swift actor isolation
///
/// This pattern replaces common Objective-C singleton implementations that use
/// manual synchronization mechanisms.
///
/// **Objective-C Pattern (Before):**
/// ```objc
/// @implementation ServiceManager
///
/// + (instancetype)sharedInstance {
///     static ServiceManager *instance = nil;
///     static dispatch_once_t onceToken;
///     dispatch_once(&onceToken, ^{
///         instance = [[self alloc] init];
///     });
///     return instance;
/// }
///
/// - (void)registerService:(id)service forKey:(NSString *)key {
///     @synchronized(self) {
///         [self.services setObject:service forKey:key];
///     }
/// }
///
/// - (id)serviceForKey:(NSString *)key {
///     @synchronized(self) {
///         return [self.services objectForKey:key];
///     }
/// }
///
/// @end
/// ```
///
/// **Swift 6 Pattern (After):**
/// ```swift
/// actor ServiceManager {
///     static let shared = ServiceManager()
///     private init() {}
///
///     func register(_ service: any Service, for key: String) {
///         // Automatically thread-safe - no @synchronized needed
///     }
/// }
/// ```
actor ServiceLocator {
    // MARK: - Singleton Instance

    /// Shared instance - thread-safe initialization guaranteed by Swift
    static let shared = ServiceLocator()

    // MARK: - State

    /// Isolated state - automatically protected by actor isolation
    /// No manual locks or @synchronized blocks needed
    private var services: [String: any Service] = [:]

    /// Usage statistics (isolated)
    private var accessCount: Int = 0

    // MARK: - Initialization

    /// Private initializer prevents external instantiation
    /// Ensures singleton pattern is maintained
    private init() {
        // Perform any initialization here
        // This runs exactly once when shared instance is first accessed
    }

    // MARK: - Public Interface

    /// Register a service with a key
    /// - Parameters:
    ///   - service: Service instance conforming to Service protocol
    ///   - key: Unique identifier for the service
    ///
    /// Automatically thread-safe - actor isolation ensures no data races
    func register<T: Service>(_ service: T, for key: String) {
        services[key] = service
        accessCount += 1
    }

    /// Retrieve a service by key
    /// - Parameter key: Service identifier
    /// - Returns: Service instance if found, nil otherwise
    func service<T: Service>(for key: String) -> T? {
        accessCount += 1
        return services[key] as? T
    }

    /// Remove a service
    /// - Parameter key: Service identifier to remove
    func removeService(for key: String) {
        services.removeValue(forKey: key)
    }

    /// Remove all registered services
    func removeAllServices() {
        services.removeAll()
    }

    /// Get all registered service keys
    /// - Returns: Array of service identifiers
    func allServiceKeys() -> [String] {
        Array(services.keys)
    }

    // MARK: - Statistics

    /// Get access count
    /// - Returns: Number of times services were accessed
    func getAccessCount() -> Int {
        accessCount
    }

    /// Reset statistics
    func resetStatistics() {
        accessCount = 0
    }

    // MARK: - Nonisolated Members

    /// Service count - can be called synchronously
    ///
    /// Note: For true count, you'd need to call an isolated method.
    /// This demonstrates nonisolated usage for documentation purposes.
    nonisolated var description: String {
        "ServiceLocator (actor-isolated)"
    }
}

// MARK: - Service Protocol

/// Protocol that all services must conform to
protocol Service: Sendable {
    /// Unique identifier for the service
    var identifier: String { get }

    /// Optional initialization method
    func initialize() async throws
}

// MARK: - Example Services

/// Network service implementation
struct NetworkService: Service {
    let identifier = "network"
    let baseURL: URL

    func initialize() async throws {
        // Perform any async initialization
        print("NetworkService initialized with base URL: \(baseURL)")
    }

    func fetchData(from endpoint: String) async throws -> Data {
        let url = baseURL.appendingPathComponent(endpoint)
        let (data, _) = try await URLSession.shared.data(from: url)
        return data
    }
}

/// Cache service implementation
actor CacheService: Service {
    let identifier = "cache"
    private var cache: [String: Data] = [:]

    func initialize() async throws {
        print("CacheService initialized")
    }

    func store(_ data: Data, for key: String) {
        cache[key] = data
    }

    func retrieve(for key: String) -> Data? {
        cache[key]
    }

    func clear() {
        cache.removeAll()
    }
}

/// Analytics service implementation
final class AnalyticsService: Service, @unchecked Sendable {
    let identifier = "analytics"
    private let queue = DispatchQueue(label: "com.example.analytics")
    private var events: [String] = []

    func initialize() async throws {
        print("AnalyticsService initialized")
    }

    func trackEvent(_ event: String) {
        queue.async {
            self.events.append(event)
        }
    }

    func getEventCount() -> Int {
        queue.sync {
            events.count
        }
    }
}

// MARK: - Usage Examples

/// Example usage of the actor singleton pattern
func demonstrateUsage() async throws {
    print("=== Actor Singleton Pattern Demo ===\n")

    // MARK: Example 1: Register and retrieve services

    print("1. Registering services...")

    let networkService = NetworkService(
        baseURL: URL(string: "https://api.example.com")!
    )
    await ServiceLocator.shared.register(networkService, for: "network")

    let cacheService = CacheService()
    await ServiceLocator.shared.register(cacheService, for: "cache")

    print("   ✓ Services registered\n")

    // MARK: Example 2: Retrieve and use services

    print("2. Retrieving and using services...")

    if let network: NetworkService = await ServiceLocator.shared.service(for: "network") {
        print("   ✓ Network service retrieved")
        // Use the service
        // let data = try await network.fetchData(from: "/users")
    }

    if let cache: CacheService = await ServiceLocator.shared.service(for: "cache") {
        print("   ✓ Cache service retrieved")
        await cache.store(Data(), for: "test")
    }

    print()

    // MARK: Example 3: List all services

    print("3. Listing all registered services...")
    let keys = await ServiceLocator.shared.allServiceKeys()
    for key in keys {
        print("   • \(key)")
    }
    print()

    // MARK: Example 4: Statistics

    print("4. Access statistics...")
    let count = await ServiceLocator.shared.getAccessCount()
    print("   Total access count: \(count)\n")

    // MARK: Example 5: Cleanup

    print("5. Cleanup...")
    await ServiceLocator.shared.removeService(for: "cache")
    print("   ✓ Cache service removed")

    let remainingKeys = await ServiceLocator.shared.allServiceKeys()
    print("   Remaining services: \(remainingKeys.joined(separator: ", "))")
}

// MARK: - Advanced Pattern: Async Initialization

/// Actor singleton with async initialization
actor DatabaseManager {
    static let shared = DatabaseManager()

    private var connection: DatabaseConnection?
    private var isInitialized = false

    private init() {}

    /// Initialize database connection (call once)
    func initialize() async throws {
        guard !isInitialized else { return }

        connection = try await DatabaseConnection.create()
        isInitialized = true
    }

    /// Execute query (ensures initialization)
    func executeQuery(_ sql: String) async throws -> [Row] {
        guard isInitialized, let connection = connection else {
            throw DatabaseError.notInitialized
        }

        return try await connection.execute(sql)
    }
}

// Supporting types for example
struct DatabaseConnection {
    static func create() async throws -> DatabaseConnection {
        // Simulate async initialization
        DatabaseConnection()
    }

    func execute(_ sql: String) async throws -> [Row] {
        []
    }
}

struct Row {}

enum DatabaseError: Error {
    case notInitialized
}

// MARK: - Benefits Documentation

/*
 ## Benefits of Actor-Based Singleton over Objective-C Patterns

 ### 1. Compiler-Enforced Thread Safety
 - **Objective-C**: Manual @synchronized blocks, NSLock, or dispatch queues
   - Easy to forget synchronization
   - Risk of deadlocks with nested locks
   - Runtime errors if locks are misused

 - **Swift Actor**: Automatic isolation
   - Compiler ensures all access is safe
   - No manual synchronization needed
   - Impossible to forget thread safety

 ### 2. Cleaner, More Readable Code
 - **Objective-C**:
   ```objc
   - (void)updateData:(id)data {
       [self.lock lock];
       [self.dataStore setObject:data forKey:@"key"];
       [self.lock unlock];
   }
   ```

 - **Swift**:
   ```swift
   func updateData(_ data: Data) {
       dataStore["key"] = data  // Automatically safe
   }
   ```

 ### 3. Better Performance
 - Actors use cooperative thread pool
 - Efficient scheduling compared to traditional locks
 - No over-synchronization
 - Reduced context switching

 ### 4. Sendable Checking (Swift 6)
 - Compile-time verification of data safety
 - Ensures data passed to actors is thread-safe
 - Prevents entire categories of concurrency bugs
 - Full data-race safety with Swift 6 strict mode

 ### 5. Structured Concurrency Integration
 - Works seamlessly with async/await
 - Natural integration with Task and TaskGroup
 - Automatic cancellation support
 - Better error propagation

 ## When to Use This Pattern

 ✅ **Good Use Cases:**
 - Service locators and dependency injection
 - Shared resource managers (cache, database, network)
 - Configuration managers
 - Analytics/logging services
 - Thread-safe state coordination

 ❌ **Consider Alternatives:**
 - Simple value type singletons → Use `static let`
 - UI state → Use @Observable or SwiftUI @State
 - Performance-critical sync access → Measure first
 - iOS < 13 / macOS < 10.15 → Use traditional patterns

 ## Migration Checklist

 When migrating from Objective-C singleton:

 1. ✅ Replace `static dispatch_once_t` with `static let shared`
 2. ✅ Make init private to enforce singleton
 3. ✅ Change class to actor
 4. ✅ Remove all @synchronized blocks
 5. ✅ Remove NSLock/NSRecursiveLock properties
 6. ✅ Remove dispatch_queue properties for synchronization
 7. ✅ Add await to all method calls
 8. ✅ Ensure stored properties are Sendable
 9. ✅ Test with Swift 6 strict concurrency mode

 ## Performance Considerations

 - Actor calls have overhead due to isolation
 - For high-frequency access, measure performance
 - Consider batching operations
 - Use nonisolated for immutable computed properties
 - Profile with Instruments before optimizing

 ## Swift 6 Complete Concurrency

 Enable complete concurrency checking in your target:
 - Build Settings → Swift Compiler → Complete Concurrency Checking → Enable
 - Ensures all data races are caught at compile time
 - Required for future Swift versions

 */
