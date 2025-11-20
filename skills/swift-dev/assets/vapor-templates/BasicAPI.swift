import Vapor
import Fluent

// MARK: - Model
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

    init() { }

    init(id: UUID? = nil, email: String, name: String) {
        self.id = id
        self.email = email
        self.name = name
    }
}

// MARK: - Migration
struct CreateUser: AsyncMigration {
    func prepare(on database: Database) async throws {
        try await database.schema("users")
            .id()
            .field("email", .string, .required)
            .unique(on: "email")
            .field("name", .string, .required)
            .field("created_at", .datetime)
            .create()
    }

    func revert(on database: Database) async throws {
        try await database.schema("users").delete()
    }
}

// MARK: - DTO
struct CreateUserRequest: Content, Validatable {
    let email: String
    let name: String

    static func validations(_ validations: inout Validations) {
        validations.add("email", as: String.self, is: .email)
        validations.add("name", as: String.self, is: !.empty)
    }
}

// MARK: - Routes
func routes(_ app: Application) throws {
    let users = app.grouped("api", "users")

    // GET /api/users
    users.get { req async throws -> [User] in
        try await User.query(on: req.db).all()
    }

    // GET /api/users/:id
    users.get(":id") { req async throws -> User in
        guard let user = try await User.find(req.parameters.get("id"), on: req.db) else {
            throw Abort(.notFound)
        }
        return user
    }

    // POST /api/users
    users.post { req async throws -> User in
        try CreateUserRequest.validate(content: req)
        let input = try req.content.decode(CreateUserRequest.self)

        let user = User(email: input.email, name: input.name)
        try await user.save(on: req.db)
        return user
    }

    // PUT /api/users/:id
    users.put(":id") { req async throws -> User in
        guard var user = try await User.find(req.parameters.get("id"), on: req.db) else {
            throw Abort(.notFound)
        }

        let input = try req.content.decode(CreateUserRequest.self)
        user.email = input.email
        user.name = input.name
        try await user.save(on: req.db)
        return user
    }

    // DELETE /api/users/:id
    users.delete(":id") { req async throws -> HTTPStatus in
        guard let user = try await User.find(req.parameters.get("id"), on: req.db) else {
            throw Abort(.notFound)
        }

        try await user.delete(on: req.db)
        return .noContent
    }
}

// MARK: - Configuration
func configure(_ app: Application) async throws {
    // Database
    app.databases.use(.postgres(
        hostname: Environment.get("DATABASE_HOST") ?? "localhost",
        username: Environment.get("DATABASE_USER") ?? "vapor",
        password: Environment.get("DATABASE_PASSWORD") ?? "password",
        database: Environment.get("DATABASE_NAME") ?? "vapor"
    ), as: .psql)

    // Migrations
    app.migrations.add(CreateUser())

    // Routes
    try routes(app)
}
