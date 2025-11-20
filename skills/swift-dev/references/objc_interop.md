# Objective-C Interoperability Reference

Guide to Swift and Objective-C interoperability, bridging, and migration strategies.

## Bridging Header

### Creating a Bridging Header

When adding Swift to an Objective-C project, Xcode creates `ProjectName-Bridging-Header.h`:

```objc
// MyApp-Bridging-Header.h
#import "LegacyManager.h"
#import "OldViewController.h"
#import <CommonCrypto/CommonCrypto.h>
```

### Manual Setup

1. Create header file: `ProjectName-Bridging-Header.h`
2. Add to Build Settings: `SWIFT_OBJC_BRIDGING_HEADER = ProjectName-Bridging-Header.h`
3. Import Objective-C headers in bridging header

## Exposing Swift to Objective-C

### Generated Interface Header

Xcode automatically generates `ProjectName-Swift.h` containing Swift declarations visible to Objective-C.

Import in Objective-C:
```objc
#import "ProductName-Swift.h"
```

### @objc Attribute

```swift
// Expose to Objective-C
@objc class SwiftManager: NSObject {
    @objc func doSomething() {
        // Implementation
    }

    @objc var name: String = ""

    // Private - not exposed
    private func helperMethod() {
        // Not visible to Objective-C
    }
}
```

### @objc Name Customization

```swift
@objc(CustomObjCName)
class SwiftClass: NSObject {
    @objc(performActionWithValue:)
    func perform(action value: Int) {
        // Called as [obj performActionWithValue:42]
    }
}
```

### @objcMembers

```swift
@objcMembers
class User: NSObject {
    var name: String = ""  // Automatically @objc
    var age: Int = 0       // Automatically @objc

    func greet() {         // Automatically @objc
        print("Hello")
    }
}
```

## Type Mapping

### Primitive Types

| Objective-C | Swift |
|-------------|-------|
| `BOOL` | `Bool` |
| `NSInteger` | `Int` |
| `NSUInteger` | `UInt` |
| `CGFloat` | `CGFloat` |
| `double` | `Double` |
| `float` | `Float` |

### Object Types

| Objective-C | Swift |
|-------------|-------|
| `NSString *` | `String` |
| `NSArray *` | `[Any]` |
| `NSDictionary *` | `[AnyHashable: Any]` |
| `NSNumber *` | `NSNumber` |
| `id` | `Any` |
| `NSError *` | `Error` |

### Collections

```swift
// Swift to Objective-C
let swiftArray: [String] = ["a", "b", "c"]
let objcArray = swiftArray as NSArray

let swiftDict: [String: Int] = ["a": 1, "b": 2]
let objcDict = swiftDict as NSDictionary

// Objective-C to Swift
let nsArray: NSArray = ["a", "b", "c"]
let swiftArray = nsArray as? [String]

let nsDict: NSDictionary = ["a": 1]
let swiftDict = nsDict as? [String: Int]
```

## Nullability

### Objective-C Nullability Annotations

```objc
@interface User : NSObject

// Nonnull (cannot be nil)
@property (nonatomic, strong, nonnull) NSString *firstName;
@property (nonatomic, strong) NSString * _Nonnull lastName;

// Nullable (can be nil)
@property (nonatomic, strong, nullable) NSString *middleName;
@property (nonatomic, strong) NSString * _Nullable nickname;

- (nonnull NSString *)fullName;
- (nullable User *)findUserWithID:(nonnull NSString *)userID;

@end
```

### Nullability Regions

```objc
NS_ASSUME_NONNULL_BEGIN

@interface User : NSObject

@property (nonatomic, strong) NSString *firstName;  // Nonnull by default
@property (nonatomic, strong, nullable) NSString *middleName;  // Explicitly nullable

@end

NS_ASSUME_NONNULL_END
```

### Swift Translation

```swift
// Nonnull -> Non-optional
var firstName: String

// Nullable -> Optional
var middleName: String?

func fullName() -> String
func findUser(withID userID: String) -> User?
```

## Error Handling

### Objective-C NSError Pattern

```objc
- (BOOL)saveData:(NSData *)data error:(NSError **)error {
    if (/* error condition */) {
        if (error != NULL) {
            *error = [NSError errorWithDomain:@"com.example.error"
                                         code:100
                                     userInfo:nil];
        }
        return NO;
    }
    return YES;
}
```

### Swift Translation

```swift
func saveData(_ data: Data) throws {
    if /* error condition */ {
        throw NSError(domain: "com.example.error", code: 100, userInfo: nil)
    }
}

// Usage
do {
    try saveData(data)
} catch {
    print("Error: \(error)")
}
```

### Calling from Objective-C

```objc
NSError *error = nil;
BOOL success = [obj saveData:data error:&error];
if (!success) {
    NSLog(@"Error: %@", error);
}
```

## Protocols

### Objective-C Protocol

```objc
@protocol DataSourceDelegate <NSObject>

@required
- (NSInteger)numberOfItems;
- (NSString *)itemAtIndex:(NSInteger)index;

@optional
- (void)didSelectItemAtIndex:(NSInteger)index;

@end
```

### Swift Conformance

```swift
class DataSource: NSObject, DataSourceDelegate {
    func numberOfItems() -> Int {
        return 10
    }

    func item(at index: Int) -> String {
        return "Item \(index)"
    }

    // Optional method
    func didSelectItem(at index: Int) {
        print("Selected: \(index)")
    }
}
```

### Swift Protocol for Objective-C

```swift
@objc protocol SwiftDelegate: AnyObject {
    func didUpdate(value: String)

    @objc optional func willUpdate()
}

// Objective-C conformance
@interface ObjCClass : NSObject <SwiftDelegate>
@end

@implementation ObjCClass

- (void)didUpdateWithValue:(NSString *)value {
    NSLog(@"Updated: %@", value);
}

// Optional method can be omitted

@end
```

## Blocks and Closures

### Objective-C Blocks

```objc
typedef void (^CompletionBlock)(NSString *result, NSError *error);

- (void)fetchDataWithCompletion:(CompletionBlock)completion {
    dispatch_async(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), ^{
        NSString *result = @"Success";
        dispatch_async(dispatch_get_main_queue(), ^{
            completion(result, nil);
        });
    });
}
```

### Swift Closures

```swift
typealias CompletionClosure = (String?, Error?) -> Void

func fetchData(completion: @escaping CompletionClosure) {
    DispatchQueue.global().async {
        let result = "Success"
        DispatchQueue.main.async {
            completion(result, nil)
        }
    }
}

// Modern approach with Result
func fetchData(completion: @escaping (Result<String, Error>) -> Void) {
    DispatchQueue.global().async {
        let result = "Success"
        DispatchQueue.main.async {
            completion(.success(result))
        }
    }
}
```

## Enums

### Objective-C Enum

```objc
typedef NS_ENUM(NSInteger, Direction) {
    DirectionNorth,
    DirectionSouth,
    DirectionEast,
    DirectionWest
};

typedef NS_OPTIONS(NSUInteger, Permissions) {
    PermissionsRead    = 1 << 0,
    PermissionsWrite   = 1 << 1,
    PermissionsExecute = 1 << 2
};
```

### Swift Translation

```swift
// NS_ENUM becomes Swift enum
enum Direction: Int {
    case north
    case south
    case east
    case west
}

// NS_OPTIONS becomes OptionSet
struct Permissions: OptionSet {
    let rawValue: UInt

    static let read    = Permissions(rawValue: 1 << 0)
    static let write   = Permissions(rawValue: 1 << 1)
    static let execute = Permissions(rawValue: 1 << 2)
}

// Usage
let permissions: Permissions = [.read, .write]
if permissions.contains(.read) {
    // Can read
}
```

## Class Extensions and Categories

### Objective-C Category

```objc
@interface NSString (Utilities)
- (NSString *)reversedString;
@end

@implementation NSString (Utilities)
- (NSString *)reversedString {
    // Implementation
}
@end
```

### Swift Extension

```swift
extension String {
    func reversed() -> String {
        return String(self.reversed())
    }
}

// Expose to Objective-C (only for NSObject subclasses)
extension NSString {
    @objc func swiftReversed() -> String {
        return String(self.reversed())
    }
}
```

## Subclassing

### Subclassing Objective-C from Swift

```swift
import UIKit

class CustomViewController: UIViewController {
    override func viewDidLoad() {
        super.viewDidLoad()
        // Swift customization
    }

    @objc func customMethod() {
        // Exposed to Objective-C
    }
}
```

### Subclassing Swift from Objective-C

```swift
// Swift base class
@objc open class SwiftBase: NSObject {
    @objc open func overridableMethod() {
        // Implementation
    }

    @objc public final func finalMethod() {
        // Cannot be overridden
    }
}
```

```objc
// Objective-C subclass
@interface ObjCSubclass : SwiftBase
@end

@implementation ObjCSubclass

- (void)overridableMethod {
    [super overridableMethod];
    // Custom implementation
}

@end
```

## Property Attributes

### Objective-C Properties

```objc
@property (nonatomic, strong) NSString *name;
@property (nonatomic, weak) id<Delegate> delegate;
@property (nonatomic, copy) NSString *title;
@property (nonatomic, assign) NSInteger count;
@property (nonatomic, readonly) NSString *identifier;
```

### Swift Equivalents

```swift
var name: String           // strong
weak var delegate: Delegate?    // weak
var title: String          // copy (automatic for value types)
var count: Int            // assign (for value types)
let identifier: String     // readonly
```

## Dynamic Features

### Dynamic Dispatch

```swift
@objc class DynamicClass: NSObject {
    // Dynamic dispatch (can be swizzled)
    @objc dynamic func dynamicMethod() {
        print("Original")
    }

    // Static dispatch (cannot be swizzled)
    @objc func staticMethod() {
        print("Static")
    }
}
```

### Method Swizzling

```swift
import ObjectiveC

extension DynamicClass {
    static func swizzle() {
        let original = class_getInstanceMethod(DynamicClass.self, #selector(dynamicMethod))!
        let swizzled = class_getInstanceMethod(DynamicClass.self, #selector(swizzledMethod))!

        method_exchangeImplementations(original, swizzled)
    }

    @objc func swizzledMethod() {
        print("Swizzled")
        swizzledMethod() // Calls original
    }
}
```

## Key-Value Coding (KVC)

### Objective-C KVC

```objc
[user setValue:@"John" forKey:@"name"];
NSString *name = [user valueForKey:@"name"];
```

### Swift KVC

```swift
@objc class User: NSObject {
    @objc dynamic var name: String = ""
}

let user = User()
user.setValue("John", forKey: "name")
let name = user.value(forKey: "name") as? String
```

## Key-Value Observing (KVO)

### Objective-C KVO

```objc
[object addObserver:self
         forKeyPath:@"property"
            options:NSKeyValueObservingOptionNew
            context:NULL];

- (void)observeValueForKeyPath:(NSString *)keyPath
                      ofObject:(id)object
                        change:(NSDictionary *)change
                       context:(void *)context {
    if ([keyPath isEqualToString:@"property"]) {
        // Handle change
    }
}
```

### Swift KVO

```swift
class Observer: NSObject {
    @objc dynamic var observedProperty: String = ""

    private var observation: NSKeyValueObservation?

    func startObserving(_ object: ObservableObject) {
        observation = object.observe(\.property, options: [.new]) { object, change in
            print("New value: \(change.newValue ?? "")")
        }
    }
}
```

## Migration Strategies

### Incremental Migration

1. **Start with Model Layer**
```swift
// Migrate data models first
struct User: Codable {
    let id: String
    let name: String
}
```

2. **Utilities and Helpers**
```swift
// Pure logic functions
class StringUtils {
    static func format(_ string: String) -> String {
        // Implementation
    }
}
```

3. **View Controllers**
```swift
// Migrate one screen at a time
class SwiftViewController: UIViewController {
    // Swift implementation
}
```

### Translation Patterns

**Properties:**
```objc
@property (nonatomic, strong) NSString *name;
```
```swift
var name: String
```

**Methods:**
```objc
- (void)setName:(NSString *)name age:(NSInteger)age;
```
```swift
func setName(_ name: String, age: Int)
```

**Initializers:**
```objc
- (instancetype)initWithName:(NSString *)name;
```
```swift
init(name: String)
```

### Best Practices

1. **Add Nullability Annotations**
   - Mark all Objective-C APIs with nonnull/nullable
   - Use NS_ASSUME_NONNULL_BEGIN/END

2. **Use Lightweight Generics**
```objc
@property (nonatomic, strong) NSArray<NSString *> *names;
@property (nonatomic, strong) NSDictionary<NSString *, NSNumber *> *scores;
```

3. **Prefer Swift Idioms**
   - Use guard, if let for optionals
   - Use Swift error handling (throws)
   - Use value types (struct, enum)

4. **Bridge Carefully**
   - Minimize bridging overhead
   - Use @objc only when necessary
   - Prefer Swift protocols over @objc protocols

5. **Test Thoroughly**
   - Test Objective-C calling Swift
   - Test Swift calling Objective-C
   - Verify memory management

## Common Pitfalls

### Retain Cycles

```swift
// ❌ Bad: Retain cycle
class ViewController: UIViewController {
    var closure: (() -> Void)?

    func setup() {
        closure = {
            self.view.backgroundColor = .white  // Captures self strongly
        }
    }
}

// ✅ Good: Weak self
closure = { [weak self] in
    self?.view.backgroundColor = .white
}
```

### Optional Bridging

```swift
// Objective-C returns id (Any in Swift)
let value = objcMethod()  // Any

// Need to cast
if let string = value as? String {
    print(string)
}
```

### Collection Bridging

```swift
// Objective-C NSArray -> Swift array needs casting
let nsArray: NSArray = objcArray()
let swiftArray = nsArray as? [String] ?? []
```

## Tools and Resources

### Xcode Features
- Swift Migrator (Edit > Convert > To Current Swift Syntax)
- Interface Builder with mixed Swift/Objective-C
- Bridging header auto-generation

### Command Line
```bash
# Generate Swift interface from Objective-C
swiftc -emit-objc-header MySwiftFile.swift

# Print generated interface
xcrun swift -frontend -emit-objc-header MySwiftFile.swift
```

### Documentation
- [Using Swift with Cocoa and Objective-C](https://developer.apple.com/documentation/swift/using-swift-with-cocoa-and-objective-c)
- [Swift Evolution Proposals](https://github.com/apple/swift-evolution)
