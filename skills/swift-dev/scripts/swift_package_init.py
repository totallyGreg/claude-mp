#!/usr/bin/env python3
"""
Initialize a Swift Package Manager project with common configurations.

Usage:
    python3 swift_package_init.py <package-name> [--type library|executable] [--platforms ios,macos]
"""

import argparse
import subprocess
import sys
from pathlib import Path

def create_package(name: str, package_type: str, platforms: list):
    """Create and configure a Swift package."""
    # Create package directory
    package_path = Path(name)
    if package_path.exists():
        print(f"Error: Directory '{name}' already exists")
        sys.exit(1)

    # Initialize package
    print(f"Creating {package_type} package: {name}")
    result = subprocess.run(
        ["swift", "package", "init", "--type", package_type, "--name", name],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)

    print(f"✅ Package created: {name}")

    # Update Package.swift with platforms
    if platforms:
        update_package_platforms(package_path / "Package.swift", platforms)
        print(f"✅ Added platform requirements: {', '.join(platforms)}")

    # Create .gitignore
    create_gitignore(package_path)
    print("✅ Created .gitignore")

    # Create README
    create_readme(package_path, name, package_type)
    print("✅ Created README.md")

    print(f"\n✨ Package '{name}' is ready!")
    print(f"\nNext steps:")
    print(f"  cd {name}")
    print(f"  swift build")
    if package_type == "executable":
        print(f"  swift run")
    else:
        print(f"  swift test")

def update_package_platforms(package_file: Path, platforms: list):
    """Add platform requirements to Package.swift."""
    with open(package_file, 'r') as f:
        content = f.read()

    platform_map = {
        'ios': '.iOS(.v15)',
        'macos': '.macOS(.v12)',
        'watchos': '.watchOS(.v8)',
        'tvos': '.tvOS(.v15)',
        'visionos': '.visionOS(.v1)'
    }

    platform_strings = [platform_map.get(p.lower(), f'.{p}(.v1)') for p in platforms]
    platforms_line = f"    platforms: [{', '.join(platform_strings)}],\n"

    # Insert platforms after Package declaration
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'let package = Package(' in line:
            # Find the name line
            for j in range(i+1, len(lines)):
                if 'name:' in lines[j]:
                    lines.insert(j+1, platforms_line)
                    break
            break

    with open(package_file, 'w') as f:
        f.write('\n'.join(lines))

def create_gitignore(package_path: Path):
    """Create .gitignore file."""
    gitignore_content = """.DS_Store
/.build
/Packages
xcuserdata/
DerivedData/
.swiftpm/configuration/registries.json
.swiftpm/xcode/package.xcworkspace/contents.xcworkspacedata
.netrc
Package.resolved
*.xcodeproj
"""
    with open(package_path / ".gitignore", 'w') as f:
        f.write(gitignore_content)

def create_readme(package_path: Path, name: str, package_type: str):
    """Create README.md file."""
    readme_content = f"""# {name}

A Swift {package_type} package.

## Installation

Add this package to your `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/username/{name}.git", from: "1.0.0")
]
```

## Usage

```swift
import {name}

// Your usage example
```

## Development

Build the package:
```bash
swift build
```

Run tests:
```bash
swift test
```

{'Run the executable:\n```bash\nswift run\n```' if package_type == 'executable' else ''}

## License

MIT License
"""
    with open(package_path / "README.md", 'w') as f:
        f.write(readme_content)

def main():
    parser = argparse.ArgumentParser(description='Initialize a Swift Package Manager project')
    parser.add_argument('name', help='Package name')
    parser.add_argument('--type', choices=['library', 'executable'], default='library',
                        help='Package type (default: library)')
    parser.add_argument('--platforms', help='Comma-separated list of platforms (e.g., ios,macos)')

    args = parser.parse_args()

    platforms = []
    if args.platforms:
        platforms = [p.strip() for p in args.platforms.split(',')]

    create_package(args.name, args.type, platforms)

if __name__ == '__main__':
    main()
