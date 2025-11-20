import SwiftUI

// MARK: - Model
struct Item: Identifiable {
    let id: UUID
    var title: String
    var isCompleted: Bool
}

// MARK: - ViewModel
@MainActor
class ItemListViewModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var isLoading = false
    @Published var error: Error?

    private let repository: ItemRepository

    init(repository: ItemRepository = ItemRepositoryImpl()) {
        self.repository = repository
    }

    func loadItems() async {
        isLoading = true
        defer { isLoading = false }

        do {
            items = try await repository.fetchItems()
        } catch {
            self.error = error
        }
    }

    func toggleItem(_ item: Item) async {
        guard let index = items.firstIndex(where: { $0.id == item.id }) else { return }
        items[index].isCompleted.toggle()

        do {
            try await repository.updateItem(items[index])
        } catch {
            self.error = error
            items[index].isCompleted.toggle() // Revert on error
        }
    }
}

// MARK: - View
struct ItemListView: View {
    @StateObject private var viewModel = ItemListViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading {
                    ProgressView()
                } else if viewModel.items.isEmpty {
                    ContentUnavailableView("No Items", systemImage: "list.bullet")
                } else {
                    itemList
                }
            }
            .navigationTitle("Items")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("Add", systemImage: "plus") {
                        // Add new item
                    }
                }
            }
            .task {
                await viewModel.loadItems()
            }
        }
    }

    private var itemList: some View {
        List {
            ForEach(viewModel.items) { item in
                ItemRow(item: item) {
                    Task {
                        await viewModel.toggleItem(item)
                    }
                }
            }
        }
    }
}

struct ItemRow: View {
    let item: Item
    let onToggle: () -> Void

    var body: some View {
        HStack {
            Image(systemName: item.isCompleted ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(item.isCompleted ? .green : .gray)

            Text(item.title)
                .strikethrough(item.isCompleted)

            Spacer()
        }
        .contentShape(Rectangle())
        .onTapGesture(perform: onToggle)
    }
}

// MARK: - Repository Protocol
protocol ItemRepository {
    func fetchItems() async throws -> [Item]
    func updateItem(_ item: Item) async throws
}

// MARK: - Repository Implementation
class ItemRepositoryImpl: ItemRepository {
    func fetchItems() async throws -> [Item] {
        // Implement actual data fetching
        []
    }

    func updateItem(_ item: Item) async throws {
        // Implement actual data update
    }
}

// MARK: - Preview
#Preview {
    ItemListView()
}
