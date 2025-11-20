# Server-Side Swift Frameworks Reference

Guide to building backend services with Swift using Vapor, Swift NIO, and related frameworks.

## Vapor Framework

### Setup and Installation

```bash
# Install Vapor toolbox (macOS)
brew install vapor

# Create new project
vapor new MyProject

# Or use Swift Package Manager
swift package init --type executable
```

### Basic Vapor Application

```swift
import Vapor

@main
struct Application {
    static func main() async throws {
        var env = try Environment.detect()
        try LoggingSystem.bootstrap(from: &env)

        let app = Vapor.Application(env)
        defer { app.shutdown() }

        try await configure(app)
        try await app.execute()
    }
}

func configure(_ app: Application) async throws {
    // Register routes
    try routes(app)
}

func routes(_ app: Application) throws {
    app.get("hello") { req async -> String in
        "Hello, world!"
    }
}
```

### Routing

```swift
func routes(_ app: Application) throws {
    // GET request
    app.get("users") { req async throws -> [User] in
        try await User.query(on: req.db).all()
    }

    // POST request
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

    // PUT request
    app.put("users", ":userID") { req async throws -> User in
        guard var user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }

        let input = try req.content.decode(UserInput.self)
        user.name = input.name
        try await user.save(on: req.db)
        return user
    }

    // DELETE request
    app.delete("users", ":userID") { req async throws -> HTTPStatus in
        guard let user = try await User.find(req.parameters.get("userID"), on: req.db) else {
            throw Abort(.notFound)
        }

        try await user.delete(on: req.db)
        return .noContent
    }

    // Route groups
    let api = app.grouped("api", "v1")
    api.get("status") { req in
        ["status": "ok"]
    }
}
```

### Fluent ORM

#### Model Definition

```swift
import Fluent
import Vapor

final class User: Model, Content {
    static let schema = "users"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "email")
    var email: String

    @Field(key: "name")
    var name: String

    @Timestamp(key: "created_at", on: .create)
    var createdAt: Date?

    @Timestamp(key: "updated_at", on: .update)
    var updatedAt: Date?

    // Relationships
    @Children(for: \.$user)
    var posts: [Post]

    @OptionalParent(key: "company_id")
    var company: Company?

    init() { }

    init(id: UUID? = nil, email: String, name: String) {
        self.id = id
        self.email = email
        self.name = name
    }
}

final class Post: Model, Content {
    static let schema = "posts"

    @ID(key: .id)
    var id: UUID?

    @Field(key: "title")
    var title: String

    @Field(key: "content")
    var content: String

    @Parent(key: "user_id")
    var user: User

    init() { }
}
```

#### Migrations

```swift
struct CreateUser: AsyncMigration {
    func prepare(on database: Database) async throws {
        try await database.schema("users")
            .id()
            .field("email", .string, .required)
            .unique(on: "email")
            .field("name", .string, .required)
            .field("created_at", .datetime)
            .field("updated_at", .datetime)
            .create()
    }

    func revert(on database: Database) async throws {
        try await database.schema("users").delete()
    }
}

// Register migration
app.migrations.add(CreateUser())
try await app.autoMigrate()
```

#### Querying

```swift
// Find all
let users = try await User.query(on: db).all()

// Filter
let admins = try await User.query(on: db)
    .filter(\.$role == "admin")
    .all()

// Sort
let sorted = try await User.query(on: db)
    .sort(\.$name, .ascending)
    .all()

// Pagination
let page = try await User.query(on: db)
    .paginate(PageRequest(page: 1, per: 20))

// Eager loading
let users = try await User.query(on: db)
    .with(\.$posts)
    .all()

// Joins
let result = try await User.query(on: db)
    .join(Post.self, on: \User.$id == \Post.$user.$id)
    .all()
```

### Middleware

```swift
struct LogMiddleware: AsyncMiddleware {
    func respond(to request: Request, chainingTo next: AsyncResponder) async throws -> Response {
        print("Incoming request: \(request.method) \(request.url.path)")

        let start = Date()
        let response = try await next.respond(to: request)
        let duration = Date().timeIntervalSince(start)

        print("Response: \(response.status.code) (\(duration)s)")

        return response
    }
}

// Register middleware
app.middleware.use(LogMiddleware())

// Built-in middleware
app.middleware.use(FileMiddleware(publicDirectory: app.directory.publicDirectory))
app.middleware.use(ErrorMiddleware.default(environment: app.environment))
```

### Authentication

```swift
import JWT

struct UserToken: Content, Authenticatable, JWTPayload {
    var subject: SubjectClaim
    var expiration: ExpirationClaim

    func verify(using signer: JWTSigner) throws {
        try expiration.verifyNotExpired()
    }
}

// Protected routes
let protected = app.grouped(UserToken.authenticator(), UserToken.guardMiddleware())

protected.get("profile") { req async throws -> User in
    let token = try req.auth.require(UserToken.self)
    guard let user = try await User.find(UUID(uuidString: token.subject.value), on: req.db) else {
        throw Abort(.notFound)
    }
    return user
}

// Login
app.post("login") { req async throws -> String in
    let credentials = try req.content.decode(LoginRequest.self)

    guard let user = try await User.query(on: req.db)
        .filter(\.$email == credentials.email)
        .first() else {
        throw Abort(.unauthorized)
    }

    // Verify password (use Bcrypt in production)
    guard try req.password.verify(credentials.password, created: user.passwordHash) else {
        throw Abort(.unauthorized)
    }

    let payload = UserToken(
        subject: SubjectClaim(value: user.id!.uuidString),
        expiration: ExpirationClaim(value: Date().addingTimeInterval(3600))
    )

    return try req.jwt.sign(payload)
}
```

### Validation

```swift
struct CreateUserRequest: Content, Validatable {
    let email: String
    let name: String
    let age: Int

    static func validations(_ validations: inout Validations) {
        validations.add("email", as: String.self, is: .email)
        validations.add("name", as: String.self, is: !.empty)
        validations.add("age", as: Int.self, is: .range(13...))
    }
}

app.post("users") { req async throws -> User in
    try CreateUserRequest.validate(content: req)
    let input = try req.content.decode(CreateUserRequest.self)
    // Process...
}
```

### WebSockets

```swift
app.webSocket("chat") { req, ws in
    ws.onText { ws, text in
        // Echo message back
        ws.send(text)
    }

    ws.onBinary { ws, buffer in
        // Handle binary data
    }

    ws.onClose.whenComplete { result in
        print("WebSocket closed")
    }
}
```

## Swift NIO

### Basic HTTP Server

```swift
import NIO
import NIOHTTP1

final class HTTPHandler: ChannelInboundHandler {
    typealias InboundIn = HTTPServerRequestPart
    typealias OutboundOut = HTTPServerResponsePart

    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        let reqPart = unwrapInboundIn(data)

        switch reqPart {
        case .head(let request):
            let response = HTTPResponseHead(
                version: request.version,
                status: .ok,
                headers: ["Content-Type": "text/plain"]
            )
            context.write(wrapOutboundOut(.head(response)), promise: nil)

            var buffer = context.channel.allocator.buffer(capacity: 12)
            buffer.writeString("Hello, World!")
            context.write(wrapOutboundOut(.body(.byteBuffer(buffer))), promise: nil)
            context.writeAndFlush(wrapOutboundOut(.end(nil)), promise: nil)

        case .body, .end:
            break
        }
    }
}

// Create server
let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
defer { try! group.syncShutdownGracefully() }

let bootstrap = ServerBootstrap(group: group)
    .serverChannelOption(ChannelOptions.backlog, value: 256)
    .childChannelInitializer { channel in
        channel.pipeline.configureHTTPServerPipeline().flatMap {
            channel.pipeline.addHandler(HTTPHandler())
        }
    }

let channel = try bootstrap.bind(host: "127.0.0.1", port: 8080).wait()
try channel.closeFuture.wait()
```

### EventLoopFuture

```swift
func fetchUser(id: String, on eventLoop: EventLoop) -> EventLoopFuture<User> {
    let promise = eventLoop.makePromise(of: User.self)

    DispatchQueue.global().async {
        do {
            let user = try loadUser(id: id)
            promise.succeed(user)
        } catch {
            promise.fail(error)
        }
    }

    return promise.futureResult
}

// Chain futures
fetchUser(id: "123", on: eventLoop)
    .flatMap { user in
        fetchPosts(for: user, on: eventLoop)
    }
    .whenComplete { result in
        switch result {
        case .success(let posts):
            print("Posts: \(posts)")
        case .failure(let error):
            print("Error: \(error)")
        }
    }
```

## Database Drivers

### PostgreSQL (Fluent)

```swift
import FluentPostgresDriver

// Configure
app.databases.use(.postgres(
    hostname: "localhost",
    username: "vapor",
    password: "password",
    database: "vapor"
), as: .psql)
```

### MongoDB (MongoKitten)

```swift
import MongoKitten

let db = try await MongoDatabase.connect(to: "mongodb://localhost/mydb")

struct User: Codable {
    let _id: ObjectId
    let name: String
    let email: String
}

// Insert
let user = User(_id: ObjectId(), name: "John", email: "john@example.com")
try await db["users"].insert(user)

// Find
let users = try await db["users"].find().decode(User.self).allResults()

// Update
try await db["users"].updateOne(
    where: "_id" == user._id,
    to: ["$set": ["name": "Jane"]]
)

// Delete
try await db["users"].deleteOne(where: "_id" == user._id)
```

### Redis

```swift
import Redis

let redis = try await RedisConnection.make(
    configuration: try .init(hostname: "localhost"),
    boundEventLoop: app.eventLoopGroup.next()
).get()

// Set
try await redis.set("key", to: "value").get()

// Get
let value = try await redis.get("key", as: String.self).get()

// Expire
try await redis.expire("key", after: .seconds(3600)).get()
```

## Deployment

### Docker

```dockerfile
# Dockerfile
FROM swift:5.9 as build
WORKDIR /app
COPY . .
RUN swift build -c release

FROM swift:5.9-slim
WORKDIR /app
COPY --from=build /app/.build/release/MyApp .
EXPOSE 8080
CMD ["./MyApp", "serve", "--hostname", "0.0.0.0", "--port", "8080"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    depends_on:
      - db
    environment:
      DATABASE_HOST: db
      DATABASE_NAME: vapor

  db:
    image: postgres:15
    environment:
      POSTGRES_USER: vapor
      POSTGRES_PASSWORD: password
      POSTGRES_DB: vapor
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
```

### Environment Configuration

```swift
import Vapor

extension Application {
    var config: Config {
        Config(app: self)
    }

    struct Config {
        let app: Application

        var databaseURL: String {
            Environment.get("DATABASE_URL") ?? "postgres://localhost/vapor"
        }

        var jwtSecret: String {
            Environment.get("JWT_SECRET") ?? "secret"
        }

        var port: Int {
            Int(Environment.get("PORT") ?? "8080")!
        }
    }
}
```

## Testing

```swift
@testable import App
import XCTVapor

final class AppTests: XCTestCase {
    var app: Application!

    override func setUp() async throws {
        app = Application(.testing)
        try await configure(app)
    }

    override func tearDown() async throws {
        app.shutdown()
    }

    func testHello() async throws {
        try app.test(.GET, "hello") { res in
            XCTAssertEqual(res.status, .ok)
            XCTAssertEqual(res.body.string, "Hello, world!")
        }
    }

    func testCreateUser() async throws {
        let user = CreateUserRequest(email: "test@example.com", name: "Test")

        try app.test(.POST, "users", beforeRequest: { req in
            try req.content.encode(user)
        }, afterResponse: { res in
            XCTAssertEqual(res.status, .ok)
            let created = try res.content.decode(User.self)
            XCTAssertEqual(created.email, user.email)
        })
    }
}
```

## Best Practices

1. **Error Handling**: Use Abort for HTTP errors
2. **Async/Await**: Prefer async/await over EventLoopFuture
3. **Database**: Use migrations for schema management
4. **Security**: Always hash passwords, use HTTPS in production
5. **Validation**: Validate all user input
6. **Testing**: Write integration tests for routes
7. **Logging**: Use structured logging
8. **Environment**: Use environment variables for configuration
9. **Database Connections**: Use connection pooling
10. **Performance**: Profile and optimize hot paths
