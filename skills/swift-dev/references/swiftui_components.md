# SwiftUI Components Reference

Comprehensive reference for SwiftUI views, modifiers, and patterns.

## Layout Containers

### VStack, HStack, ZStack

**VStack** - Vertical stack:
```swift
VStack(alignment: .leading, spacing: 10) {
    Text("Title")
    Text("Subtitle")
}
```

**HStack** - Horizontal stack:
```swift
HStack(alignment: .top, spacing: 20) {
    Image(systemName: "star")
    Text("Favorite")
}
```

**ZStack** - Depth stack (overlaying):
```swift
ZStack(alignment: .bottomTrailing) {
    Image("background")
    Text("Overlay")
        .padding()
}
```

### LazyVStack, LazyHStack

Lazy loading for performance with large datasets:
```swift
ScrollView {
    LazyVStack(spacing: 10) {
        ForEach(1...1000, id: \.self) { index in
            RowView(index: index)
        }
    }
}
```

### Grid (iOS 16+)

```swift
Grid(alignment: .leading, horizontalSpacing: 10, verticalSpacing: 10) {
    GridRow {
        Text("Name:")
        Text("John Doe")
    }
    GridRow {
        Text("Age:")
        Text("30")
    }
}
```

### LazyVGrid, LazyHGrid

Grid layouts with lazy loading:
```swift
let columns = [
    GridItem(.adaptive(minimum: 100))
]

ScrollView {
    LazyVGrid(columns: columns, spacing: 20) {
        ForEach(items) { item in
            ItemView(item: item)
        }
    }
}
```

## Lists and Collections

### List

```swift
// Basic list
List(items) { item in
    Text(item.name)
}

// With sections
List {
    Section("Section 1") {
        Text("Item 1")
        Text("Item 2")
    }
    Section("Section 2") {
        Text("Item 3")
    }
}

// With delete and move
List {
    ForEach(items) { item in
        Text(item.name)
    }
    .onDelete(perform: delete)
    .onMove(perform: move)
}
```

### ForEach

```swift
ForEach(items) { item in
    ItemRow(item: item)
}

// With index
ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
    Text("\(index): \(item.name)")
}
```

### ScrollView

```swift
ScrollView(.vertical, showsIndicators: true) {
    VStack(spacing: 20) {
        ForEach(items) { item in
            ItemView(item: item)
        }
    }
}

// Horizontal scroll
ScrollView(.horizontal) {
    HStack(spacing: 15) {
        ForEach(items) { item in
            ItemCard(item: item)
        }
    }
}
```

## Navigation

### NavigationStack (iOS 16+)

```swift
NavigationStack {
    List(items) { item in
        NavigationLink(value: item) {
            ItemRow(item: item)
        }
    }
    .navigationDestination(for: Item.self) { item in
        DetailView(item: item)
    }
    .navigationTitle("Items")
}
```

### NavigationSplitView (iOS 16+)

```swift
NavigationSplitView {
    List(categories, selection: $selectedCategory) { category in
        Text(category.name)
    }
} content: {
    if let category = selectedCategory {
        List(category.items, selection: $selectedItem) { item in
            Text(item.name)
        }
    }
} detail: {
    if let item = selectedItem {
        DetailView(item: item)
    } else {
        Text("Select an item")
    }
}
```

### NavigationLink (Legacy)

```swift
// Pre-iOS 16
NavigationView {
    List(items) { item in
        NavigationLink(destination: DetailView(item: item)) {
            ItemRow(item: item)
        }
    }
    .navigationTitle("Items")
}
```

### TabView

```swift
TabView {
    HomeView()
        .tabItem {
            Label("Home", systemImage: "house")
        }

    ProfileView()
        .tabItem {
            Label("Profile", systemImage: "person")
        }
}
```

## Forms and Input

### Form

```swift
Form {
    Section("Personal Information") {
        TextField("Name", text: $name)
        DatePicker("Birthday", selection: $birthday, displayedComponents: .date)
    }

    Section("Preferences") {
        Toggle("Enable notifications", isOn: $notificationsEnabled)
        Picker("Theme", selection: $selectedTheme) {
            ForEach(themes) { theme in
                Text(theme.name).tag(theme)
            }
        }
    }
}
```

### TextField

```swift
// Basic text field
TextField("Enter text", text: $text)

// With placeholder and styling
TextField("Email", text: $email)
    .textInputAutocapitalization(.never)
    .keyboardType(.emailAddress)
    .autocorrectionDisabled()

// Secure field for passwords
SecureField("Password", text: $password)

// With submit action
TextField("Search", text: $searchQuery)
    .onSubmit {
        performSearch()
    }
```

### TextEditor

```swift
TextEditor(text: $notes)
    .frame(height: 200)
    .border(Color.gray)
```

### Toggle

```swift
Toggle("Enable feature", isOn: $isEnabled)

// Custom style
Toggle("Dark mode", isOn: $isDarkMode)
    .toggleStyle(.switch)
```

### Picker

```swift
// Menu style
Picker("Category", selection: $selectedCategory) {
    ForEach(categories) { category in
        Text(category.name).tag(category)
    }
}
.pickerStyle(.menu)

// Segmented style
Picker("View", selection: $viewMode) {
    Text("List").tag(ViewMode.list)
    Text("Grid").tag(ViewMode.grid)
}
.pickerStyle(.segmented)

// Wheel style
Picker("Age", selection: $age) {
    ForEach(1...100, id: \.self) { age in
        Text("\(age)").tag(age)
    }
}
.pickerStyle(.wheel)
```

### Slider

```swift
Slider(value: $volume, in: 0...100, step: 1)

// With label and value label
Slider(value: $brightness, in: 0...1) {
    Text("Brightness")
} minimumValueLabel: {
    Image(systemName: "sun.min")
} maximumValueLabel: {
    Image(systemName: "sun.max")
}
```

### Stepper

```swift
Stepper("Quantity: \(quantity)", value: $quantity, in: 1...10)

// With custom step
Stepper(value: $price, in: 0...1000, step: 10) {
    Text("Price: $\(price, specifier: "%.2f")")
}
```

### DatePicker

```swift
// Date only
DatePicker("Select date", selection: $date, displayedComponents: .date)

// Date and time
DatePicker("Appointment", selection: $appointmentDate)

// With range
DatePicker("Birthday", selection: $birthday, in: ...Date(), displayedComponents: .date)
```

### ColorPicker (iOS 14+)

```swift
ColorPicker("Choose color", selection: $selectedColor)
```

## Presentation Modifiers

### Sheet

```swift
.sheet(isPresented: $showingSheet) {
    SheetView()
}

// With item binding (iOS 16+)
.sheet(item: $selectedItem) { item in
    DetailSheet(item: item)
}
```

### FullScreenCover

```swift
.fullScreenCover(isPresented: $showingFullScreen) {
    FullScreenView()
}
```

### Alert

```swift
// Simple alert
.alert("Title", isPresented: $showingAlert) {
    Button("OK") { }
}

// With message
.alert("Error", isPresented: $showingError) {
    Button("Cancel", role: .cancel) { }
    Button("Retry") {
        retryAction()
    }
} message: {
    Text("An error occurred")
}

// iOS 15+ with item
.alert("Delete Item?", isPresented: $showingDeleteAlert, presenting: itemToDelete) { item in
    Button("Delete", role: .destructive) {
        delete(item)
    }
    Button("Cancel", role: .cancel) { }
}
```

### ConfirmationDialog

```swift
.confirmationDialog("Choose option", isPresented: $showingOptions) {
    Button("Option 1") { selectOption(1) }
    Button("Option 2") { selectOption(2) }
    Button("Cancel", role: .cancel) { }
}
```

### Popover

```swift
.popover(isPresented: $showingPopover) {
    PopoverContent()
        .presentationCompactAdaptation(.popover)
}
```

## Text and Typography

### Text

```swift
// Basic text
Text("Hello, World!")

// Styled text
Text("Bold text")
    .bold()
    .font(.title)
    .foregroundColor(.blue)

// Multi-line with alignment
Text("This is a long text that will wrap to multiple lines")
    .lineLimit(3)
    .multilineTextAlignment(.center)

// Combining text
Text("Hello, ")
    + Text("World").bold()
    + Text("!")

// String interpolation with formatting
Text("Price: \(price, specifier: "%.2f")")
Text("Date: \(date, style: .date)")
```

### Label

```swift
Label("Home", systemImage: "house")

// Custom style
Label {
    Text("Custom")
} icon: {
    Image(systemName: "star")
        .foregroundColor(.yellow)
}
```

### Link

```swift
Link("Visit website", destination: URL(string: "https://example.com")!)
```

## Images

### Image

```swift
// System image (SF Symbols)
Image(systemName: "heart.fill")
    .foregroundColor(.red)
    .imageScale(.large)

// Asset catalog image
Image("photo")
    .resizable()
    .aspectRatio(contentMode: .fit)
    .frame(width: 200, height: 200)

// With rendering mode
Image("logo")
    .renderingMode(.template)
    .foregroundColor(.blue)
```

### AsyncImage (iOS 15+)

```swift
AsyncImage(url: URL(string: "https://example.com/image.jpg")) { image in
    image
        .resizable()
        .aspectRatio(contentMode: .fit)
} placeholder: {
    ProgressView()
}
.frame(width: 300, height: 300)

// With phase handling
AsyncImage(url: imageURL) { phase in
    switch phase {
    case .empty:
        ProgressView()
    case .success(let image):
        image
            .resizable()
            .aspectRatio(contentMode: .fill)
    case .failure:
        Image(systemName: "photo")
            .foregroundColor(.gray)
    @unknown default:
        EmptyView()
    }
}
```

## Shapes and Graphics

### Basic Shapes

```swift
// Rectangle
Rectangle()
    .fill(Color.blue)
    .frame(width: 100, height: 100)

// RoundedRectangle
RoundedRectangle(cornerRadius: 10)
    .stroke(Color.red, lineWidth: 2)
    .frame(width: 100, height: 100)

// Circle
Circle()
    .fill(Color.green)
    .frame(width: 50, height: 50)

// Capsule
Capsule()
    .fill(Color.purple)
    .frame(width: 100, height: 40)
```

### Path

```swift
Path { path in
    path.move(to: CGPoint(x: 50, y: 50))
    path.addLine(to: CGPoint(x: 150, y: 50))
    path.addLine(to: CGPoint(x: 100, y: 150))
    path.closeSubpath()
}
.stroke(Color.blue, lineWidth: 2)
```

### Canvas (iOS 15+)

```swift
Canvas { context, size in
    context.fill(
        Path(ellipseIn: CGRect(origin: .zero, size: size)),
        with: .color(.blue)
    )

    context.stroke(
        Path { path in
            path.move(to: CGPoint(x: 0, y: size.height / 2))
            path.addLine(to: CGPoint(x: size.width, y: size.height / 2))
        },
        with: .color(.red),
        lineWidth: 2
    )
}
.frame(width: 200, height: 200)
```

## View Modifiers

### Common Modifiers

```swift
// Padding
.padding()
.padding(.horizontal, 20)
.padding(.top, 10)

// Frame
.frame(width: 100, height: 50)
.frame(maxWidth: .infinity)
.frame(idealWidth: 200, maxHeight: 300)

// Background
.background(Color.blue)
.background {
    RoundedRectangle(cornerRadius: 10)
        .fill(Color.gray)
}

// Overlay
.overlay {
    Text("NEW")
        .font(.caption)
        .padding(4)
        .background(Color.red)
        .foregroundColor(.white)
        .cornerRadius(4)
}

// Border
.border(Color.gray, width: 1)

// Corner radius
.cornerRadius(10)

// Clip shape
.clipShape(RoundedRectangle(cornerRadius: 15))

// Shadow
.shadow(color: .black.opacity(0.2), radius: 5, x: 0, y: 2)

// Opacity
.opacity(0.5)

// Blur
.blur(radius: 3)
```

### Conditional Modifiers

```swift
// Using if
if condition {
    view.modifier1()
} else {
    view.modifier2()
}

// Using ternary
view
    .foregroundColor(isSelected ? .blue : .gray)
    .font(isLarge ? .title : .body)
```

### Custom View Modifier

```swift
struct CardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .background(Color.white)
            .cornerRadius(10)
            .shadow(radius: 5)
    }
}

extension View {
    func cardStyle() -> some View {
        modifier(CardModifier())
    }
}

// Usage
Text("Card content")
    .cardStyle()
```

## Animations

### Basic Animations

```swift
@State private var isExpanded = false

Circle()
    .fill(isExpanded ? Color.red : Color.blue)
    .frame(width: isExpanded ? 100 : 50, height: isExpanded ? 100 : 50)
    .animation(.default, value: isExpanded)
    .onTapGesture {
        isExpanded.toggle()
    }
```

### Animation Types

```swift
// Linear
.animation(.linear(duration: 1), value: scale)

// Easing
.animation(.easeIn(duration: 0.5), value: offset)
.animation(.easeOut(duration: 0.5), value: offset)
.animation(.easeInOut(duration: 0.5), value: offset)

// Spring
.animation(.spring(response: 0.5, dampingFraction: 0.6), value: position)

// With delay
.animation(.default.delay(0.5), value: opacity)

// Repeating
.animation(.default.repeatCount(3, autoreverses: true), value: scale)
.animation(.default.repeatForever(autoreverses: true), value: rotation)
```

### Transitions

```swift
if showView {
    ContentView()
        .transition(.slide)
}

// Custom transitions
.transition(.opacity)
.transition(.scale)
.transition(.move(edge: .bottom))

// Asymmetric transition
.transition(.asymmetric(
    insertion: .scale,
    removal: .opacity
))

// Combined transition
.transition(.opacity.combined(with: .scale))
```

### WithAnimation

```swift
Button("Animate") {
    withAnimation(.spring()) {
        isExpanded.toggle()
    }
}
```

## Gestures

### TapGesture

```swift
Text("Tap me")
    .onTapGesture {
        print("Tapped")
    }

// Double tap
.onTapGesture(count: 2) {
    print("Double tapped")
}
```

### LongPressGesture

```swift
.onLongPressGesture(minimumDuration: 1.0) {
    print("Long pressed")
}
```

### DragGesture

```swift
@State private var offset = CGSize.zero

Circle()
    .offset(offset)
    .gesture(
        DragGesture()
            .onChanged { gesture in
                offset = gesture.translation
            }
            .onEnded { _ in
                withAnimation {
                    offset = .zero
                }
            }
    )
```

### Combined Gestures

```swift
let tap = TapGesture()
    .onEnded { _ in
        print("Tapped")
    }

let longPress = LongPressGesture()
    .onEnded { _ in
        print("Long pressed")
    }

view.gesture(tap.exclusively(before: longPress))
view.gesture(tap.simultaneously(with: longPress))
```

## State Management

### @State

```swift
@State private var count = 0

Button("Increment") {
    count += 1
}
```

### @Binding

```swift
struct ChildView: View {
    @Binding var text: String

    var body: some View {
        TextField("Enter text", text: $text)
    }
}

// Parent
@State private var inputText = ""

ChildView(text: $inputText)
```

### @StateObject

```swift
@StateObject private var viewModel = ViewModel()

// ViewModel owns the ObservableObject
```

### @ObservedObject

```swift
@ObservedObject var viewModel: ViewModel

// ViewModel is passed from parent
```

### @EnvironmentObject

```swift
class AppState: ObservableObject {
    @Published var user: User?
}

// Inject at root
ContentView()
    .environmentObject(AppState())

// Access in child views
struct ChildView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        Text(appState.user?.name ?? "Guest")
    }
}
```

### @Environment

```swift
@Environment(\.colorScheme) var colorScheme
@Environment(\.dismiss) var dismiss

if colorScheme == .dark {
    // Dark mode UI
}

Button("Close") {
    dismiss()
}
```

## Best Practices

1. **Performance**
   - Use `LazyVStack`/`LazyHStack` for large lists
   - Avoid expensive operations in view body
   - Use `@State` for local state, `@StateObject` for owned objects
   - Profile with Instruments to identify bottlenecks

2. **Code Organization**
   - Extract complex views into smaller components
   - Use view extensions for reusable modifiers
   - Separate business logic into view models

3. **Accessibility**
   - Always provide accessibility labels
   - Test with VoiceOver enabled
   - Use semantic colors for dark mode support

4. **Responsive Design**
   - Use `GeometryReader` for adaptive layouts
   - Test on different device sizes
   - Leverage `@Environment(\.horizontalSizeClass)` for layout decisions

5. **Animation**
   - Use explicit animations with `.animation(_, value:)` in iOS 15+
   - Prefer `withAnimation` for transaction-based animations
   - Keep animations subtle and purposeful
