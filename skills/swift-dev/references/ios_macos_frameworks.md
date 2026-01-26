# iOS/macOS Frameworks

Essential Apple platform frameworks for building native iOS, iPadOS, and macOS applications. This reference covers frameworks for data persistence, in-app purchases, networking, and cloud synchronization.

## Table of Contents

- [Core Data](#core-data)
- [CloudKit](#cloudkit)
- [StoreKit 2](#storekit-2)
- [URLSession and Networking](#urlsession-and-networking)
- [Framework Overview](#framework-overview)
- [Best Practices](#best-practices)
- [Documentation Access](#documentation-access)

---

## Core Data

Core Data is an object-graph management framework for persistent storage, providing a layer above SQLite with memory management, change tracking, and relationship handling.

### Basic Setup with SwiftUI

```swift
import CoreData

// MARK: - Data Model
@Entity
@Model
final class Item {
    #Timestamp var timestamp: Date?
    var title: String = ""
    var isCompleted: Bool = false

    init(title: String = "") {
        self.title = title
    }
}

// MARK: - Fetch in SwiftUI
struct ContentView: View {
    @Query(sort: \Item.timestamp) private var items: [Item]
    @Environment(\.modelContext) var modelContext

    var body: some View {
        List {
            ForEach(items) { item in
                HStack {
                    Text(item.title)
                    Spacer()
                    if item.isCompleted {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    }
                }
            }
            .onDelete(perform: deleteItems)
        }
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Add Item") {
                    let newItem = Item(title: "New Item")
                    modelContext.insert(newItem)
                }
            }
        }
    }

    private func deleteItems(offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(items[index])
        }
    }
}
```

### Background Context Operations

```swift
import CoreData

class PersistenceController {
    static let shared = PersistenceController()

    let container: NSPersistentContainer

    init() {
        container = NSPersistentContainer(name: "Model")
        container.loadPersistentStores { _, error in
            if let error {
                fatalError("Core Data load failed: \(error)")
            }
        }
    }

    func performBackgroundTask(_ block: @escaping (NSManagedObjectContext) -> Void) {
        let backgroundContext = container.newBackgroundContext()
        backgroundContext.perform {
            block(backgroundContext)
        }
    }

    func saveBackground() {
        let backgroundContext = container.newBackgroundContext()
        backgroundContext.perform {
            do {
                try backgroundContext.save()
            } catch {
                print("Background save failed: \(error)")
            }
        }
    }
}

// Usage
PersistenceController.shared.performBackgroundTask { context in
    let newItem = NSEntityDescription.insertNewObject(forEntityName: "Item", into: context)
    newItem.setValue("Test Item", forKey: "title")

    do {
        try context.save()
    } catch {
        print("Error saving: \(error)")
    }
}
```

### Fetch Requests with Predicates

```swift
// Traditional NSFetchRequest approach
func fetchUsers(olderThan age: Int, in context: NSManagedObjectContext) throws -> [User] {
    let fetchRequest: NSFetchRequest<User> = User.fetchRequest()
    fetchRequest.predicate = NSPredicate(format: "age > %d", age)
    fetchRequest.sortDescriptors = [NSSortDescriptor(keyPath: \User.name, ascending: true)]

    return try context.fetch(fetchRequest)
}
```

### Relationships and Cascading Deletes

```swift
@Entity
@Model
final class Author {
    var name: String = ""

    @Relationship(deleteRule: .cascade, inverse: \Book.author)
    var books: [Book] = []

    init(name: String) {
        self.name = name
    }
}

@Entity
@Model
final class Book {
    var title: String = ""
    var author: Author?

    init(title: String, author: Author? = nil) {
        self.title = title
        self.author = author
    }
}
```

### Common Pitfalls

**Memory management:**
```swift
// ❌ Avoid keeping contexts alive longer than needed
func badApproach() {
    let context = container.newBackgroundContext()
    // Long running operation holding context reference
    // This prevents memory from being freed
}

// ✅ Good approach
func goodApproach() {
    container.performBackgroundTask { context in
        // Work within context
        // Context is released when block completes
    }
}
```

**Thread safety:**
```swift
// ❌ Accessing main thread context from background
DispatchQueue.global().async {
    let items = try mainContext.fetch(NSFetchRequest<Item>(entityName: "Item"))
    // Main context can only be accessed from main thread!
}

// ✅ Use background context
container.performBackgroundTask { context in
    let items = try context.fetch(NSFetchRequest<Item>(entityName: "Item"))
    // Safe from background thread
}
```

**See also:**
- [SwiftUI Components](swiftui_components.md) - @Query for fetching
- [Design Patterns](design_patterns.md) - Repository pattern with Core Data

---

## CloudKit

CloudKit enables synchronization and sharing of data across user devices through iCloud. It provides both public and private databases.

### Database Types

**Private Database:**
- Accessible only to the app's owner
- Encrypted in transit and at rest
- Good for user's personal data (notes, preferences, etc.)

**Public Database:**
- Accessible to all app users
- Good for shared content (stories, comments, etc.)
- Read access usually public, write requires authentication

**Shared Database:**
- Accessible via sharing invitations
- Enables collaboration

### Basic CloudKit Setup

```swift
import CloudKit

class CloudKitManager {
    static let shared = CloudKitManager()

    let container = CKContainer.default()

    var privateDatabase: CKDatabase {
        container.privateCloudDatabase
    }

    var publicDatabase: CKDatabase {
        container.publicCloudDatabase
    }

    // Save a record
    func saveRecord(_ record: CKRecord) async throws {
        try await privateDatabase.save(record)
    }

    // Fetch a record
    func fetchRecord(withID recordID: CKRecord.ID) async throws -> CKRecord {
        try await privateDatabase.record(for: recordID)
    }

    // Query records
    func queryRecords(ofType type: String) async throws -> [CKRecord] {
        let query = CKQuery(recordType: type, predicate: NSPredicate(value: true))
        let (records, _) = try await privateDatabase.records(matching: query)
        return records.compactMap { $0.1.get() }
    }
}

// Usage
Task {
    do {
        let record = CKRecord(recordType: "Article")
        record["title"] = "My Article"
        record["content"] = "Article content"

        try await CloudKitManager.shared.saveRecord(record)
        print("Record saved successfully")
    } catch {
        print("Save failed: \(error)")
    }
}
```

### Subscriptions for Push Notifications

```swift
func subscribeToChanges() async throws {
    let subscription = CKQuerySubscription(
        recordType: "Article",
        predicate: NSPredicate(value: true),
        subscriptionID: "all-articles"
    )

    let notification = CKSubscription.NotificationInfo()
    notification.shouldSendContentAvailable = true
    subscription.notificationInfo = notification

    try await CloudKitManager.shared.privateDatabase.save(subscription)
}
```

### Sharing Records

```swift
// Create a share for a record
func shareRecord(_ record: CKRecord) async throws -> CKShare {
    let share = CKShare(baseRecord: record)
    share[CKShare.SystemFieldKey.title] = "Shared Article"
    share[CKShare.SystemFieldKey.subtitle] = "Check this out!"

    try await CloudKitManager.shared.privateDatabase.save(share)
    return share
}

// Accept a share
@main
struct MyApp: App {
    @Environment(\.scenePhase) var scenePhase

    var body: some Scene {
        WindowGroup {
            ContentView()
                .onContinueUserActivity(CKShareUserActivity.typeIdentifier) { userActivity in
                    if let share = CKShare(from: userActivity) {
                        handleShare(share)
                    }
                }
        }
    }

    private func handleShare(_ share: CKShare) {
        // Process the shared record
    }
}
```

---

## StoreKit 2

StoreKit 2 (Swift 5.5+) provides modern, async/await-based APIs for in-app purchases, subscriptions, and managing transactions.

### Product Loading and Display

```swift
import StoreKit

@MainActor
class StoreManager: ObservableObject {
    @Published var products: [Product] = []
    @Published var purchasedProductIDs: Set<String> = []

    func loadProducts() async {
        do {
            // Load product IDs from App Store Connect
            let productIDs = ["com.example.premium", "com.example.subscription"]
            products = try await Product.products(for: productIDs)
        } catch {
            print("Failed to load products: \(error)")
        }
    }
}

// Display products in UI
struct StoreView: View {
    @StateObject private var store = StoreManager()

    var body: some View {
        List {
            ForEach(store.products) { product in
                Button(action: {
                    Task {
                        await purchase(product)
                    }
                }) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(product.displayName)
                                .font(.headline)
                            Text(product.description)
                                .font(.caption)
                        }

                        Spacer()

                        Text(product.displayPrice)
                            .font(.title3)
                            .fontWeight(.bold)
                    }
                }
            }
        }
        .task {
            await store.loadProducts()
        }
    }

    private func purchase(_ product: Product) async {
        // Implementation below
    }
}
```

### Purchase and Transaction Handling

```swift
@MainActor
class StoreManager: ObservableObject {
    func purchase(_ product: Product) async throws -> Transaction? {
        let result = try await product.purchase()

        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            await transaction.finish()
            return transaction

        case .userCancelled:
            print("Purchase cancelled by user")
            return nil

        case .pending:
            print("Purchase pending (parental controls?)")
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
}

enum StoreError: Error {
    case failedVerification
}
```

### Transaction Listener

```swift
@MainActor
class TransactionListener {
    var transactionListener: Task<Void, Never>?

    func startListening() {
        transactionListener = Task.detached { [weak self] in
            for await result in Transaction.updates {
                if case .verified(let transaction) = result {
                    await self?.handleTransaction(transaction)
                    await transaction.finish()
                }
            }
        }
    }

    func stopListening() {
        transactionListener?.cancel()
    }

    private func handleTransaction(_ transaction: Transaction) {
        switch transaction.productType {
        case .consumable:
            // Handle consumable (one-time purchase)
            print("Consumable purchased: \(transaction.productID)")

        case .nonConsumable:
            // Handle non-consumable (permanent purchase)
            print("Non-consumable purchased: \(transaction.productID)")

        case .autoRenewable:
            // Handle subscription
            print("Subscription: \(transaction.productID)")

        case .nonRenewable:
            // Handle non-renewable subscription
            print("Non-renewable subscription: \(transaction.productID)")

        @unknown default:
            break
        }
    }
}
```

### Checking Purchase Status

```swift
@MainActor
func checkPurchaseStatus() async {
    for await result in Transaction.currentEntitlements {
        if case .verified(let transaction) = result {
            switch transaction.productType {
            case .nonConsumable:
                if transaction.productID == "com.example.premium" {
                    print("User has premium access")
                }

            case .autoRenewable:
                if transaction.isUpgraded {
                    print("Subscription was upgraded")
                } else {
                    print("Active subscription")
                }

            default:
                break
            }
        }
    }
}
```

---

## URLSession and Networking

URLSession provides a high-level API for making HTTP requests with modern async/await support.

### Basic Async/Await Request

```swift
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

enum NetworkError: Error {
    case invalidResponse
    case decodingError
}

// Usage
struct User: Decodable {
    let id: String
    let name: String
}

let service = NetworkService()
Task {
    do {
        let user: User = try await service.fetch(User.self, from: url)
        print("Fetched user: \(user.name)")
    } catch {
        print("Network error: \(error)")
    }
}
```

### POST Request with JSON

```swift
func createUser(name: String) async throws -> User {
    let url = URL(string: "https://api.example.com/users")!

    struct CreateUserRequest: Encodable {
        let name: String
    }

    let request = CreateUserRequest(name: name)
    var urlRequest = URLRequest(url: url)
    urlRequest.httpMethod = "POST"
    urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
    urlRequest.httpBody = try JSONEncoder().encode(request)

    let (data, _) = try await URLSession.shared.data(for: urlRequest)
    return try JSONDecoder().decode(User.self, from: data)
}
```

### Uploading Files

```swift
func uploadFile(url: URL, to endpoint: URL) async throws {
    var request = URLRequest(url: endpoint)
    request.httpMethod = "POST"

    let (data, _) = try await URLSession.shared.upload(for: request, fromFile: url)

    let response = try JSONDecoder().decode(UploadResponse.self, from: data)
    return response
}

struct UploadResponse: Decodable {
    let success: Bool
    let message: String
}
```

### Custom Headers and Configuration

```swift
let config = URLSessionConfiguration.default
config.httpAdditionalHeaders = [
    "Authorization": "Bearer token123",
    "User-Agent": "MyApp/1.0"
]
config.timeoutIntervalForRequest = 30
config.timeoutIntervalForResource = 300

let session = URLSession(configuration: config)

let (data, _) = try await session.data(from: url)
```

### Download with Progress

```swift
func downloadFile(from url: URL) async throws {
    let downloadTask = URLSession.shared.downloadTask(with: url)

    // URLSession.shared doesn't support async download directly
    // Use delegate-based approach or third-party library for progress

    // For simple downloads without progress:
    let (tempFileURL, _) = try await URLSession.shared.download(from: url)
    let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    let fileURL = documentsURL.appendingPathComponent(url.lastPathComponent)

    try FileManager.default.moveItem(at: tempFileURL, to: fileURL)
}
```

**See also:**
- [Swift Concurrency](swift_concurrency.md) - Async/await for network requests
- [Error Handling](swift_language_features.md#error-handling-patterns) - Network error handling

---

## Framework Overview

Choosing the right framework for your use case:

| Framework | Purpose | When to Use |
|-----------|---------|------------|
| **Core Data** | Local persistent storage | Storing user data locally with querying and relationships |
| **CloudKit** | Cloud sync and sharing | Syncing data across devices, sharing with other users |
| **StoreKit 2** | In-app purchases | Selling content, subscriptions, premium features |
| **URLSession** | Network requests | Fetching data from APIs, uploading files |
| **Combine** | Reactive programming | Responding to data changes, chaining operations |
| **SwiftUI** | UI building | Creating user interfaces (see [SwiftUI Components](swiftui_components.md)) |

---

## Best Practices

### Data Persistence Strategy

```swift
// Tier 1: UserDefaults for simple settings
@AppStorage("isDarkMode") var isDarkMode = false

// Tier 2: Core Data for structured data
@Query(sort: \Item.timestamp) var items: [Item]

// Tier 3: CloudKit for cloud sync
Task {
    try await CloudKitManager.shared.saveRecord(record)
}

// Tier 4: File system for large files (documents, images)
let documentsURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
let fileURL = documentsURL.appendingPathComponent("document.pdf")
```

### Error Handling with Networking

```swift
@MainActor
class DataRepository {
    @Published var isLoading = false
    @Published var error: String?

    func fetchData() async {
        isLoading = true
        error = nil

        do {
            let data = try await fetchFromNetwork()
            // Update UI
        } catch URLError.notConnectedToInternet {
            error = "No internet connection"
        } catch URLError.timedOut {
            error = "Request timed out"
        } catch DecodingError.dataCorrupted {
            error = "Invalid response format"
        } catch {
            error = "Unknown error: \(error.localizedDescription)"
        }

        isLoading = false
    }
}
```

### Testing Framework Integration

```swift
import CoreData
import XCTest

class CoreDataTests: XCTestCase {
    var container: NSPersistentContainer!

    override func setUp() {
        super.setUp()

        // Create in-memory Core Data store for testing
        container = NSPersistentContainer(name: "Model")
        let description = NSPersistentStoreDescription()
        description.type = NSInMemoryStoreType
        container.persistentStoreDescriptions = [description]

        container.loadPersistentStores { _, error in
            if let error {
                fatalError("Failed to load: \(error)")
            }
        }
    }

    func testFetchingItems() async throws {
        // Create test data
        let context = container.viewContext
        let item = NSEntityDescription.insertNewObject(forEntityName: "Item", into: context)
        item.setValue("Test", forKey: "title")
        try context.save()

        // Verify fetch works
        let fetchRequest = NSFetchRequest<NSFetchRequestResult>(entityName: "Item")
        let results = try context.fetch(fetchRequest)
        XCTAssertEqual(results.count, 1)
    }
}
```

---

## Documentation Access

Use WebFetch to retrieve current Apple framework documentation:

```
WebFetch("https://developer.apple.com/documentation/coredata",
         "Explain Core Data setup, contexts, and fetch requests")

WebFetch("https://developer.apple.com/documentation/cloudkit",
         "Describe CloudKit public and private databases")

WebFetch("https://developer.apple.com/documentation/storekit",
         "Explain StoreKit 2 product loading and purchase flow")

WebFetch("https://developer.apple.com/documentation/foundation/urlsession",
         "Document URLSession async/await API usage")
```

---

**See also:**
- [SwiftUI Components](swiftui_components.md) - Building UI for framework data
- [Design Patterns](design_patterns.md) - Repository pattern with these frameworks
- [Testing Strategies](testing_strategies.md) - Testing code using these frameworks
- [Error Handling](swift_language_features.md#error-handling-patterns) - Proper error handling with frameworks
