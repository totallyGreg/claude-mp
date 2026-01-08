#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
CoSAI Schema Fetcher

Downloads and caches the latest CoSAI Risk Map schemas from the GitHub repository.
Provides local access to YAML data files and JSON schemas for validation and analysis.

Usage:
    uv run scripts/fetch_cosai_schemas.py [--force] [--cache-dir PATH]

Options:
    --force         Force re-download even if cache exists
    --cache-dir     Custom cache directory (default: ~/.cosai-cache)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# CoSAI GitHub repository URLs
COSAI_REPO = "https://raw.githubusercontent.com/cosai-oasis/secure-ai-tooling/main/risk-map"

# Files to download
YAML_FILES = [
    "components.yaml",
    "controls.yaml",
    "personas.yaml",
    "risks.yaml",
    "self-assessment.yaml",
]

SCHEMA_FILES = [
    "components.schema.json",
    "controls.schema.json",
    "personas.schema.json",
    "risks.schema.json",
    "self-assessment.schema.json",
]


class CoSAIFetcher:
    """Fetches and caches CoSAI Risk Map schemas"""

    def __init__(self, cache_dir: Optional[Path] = None, force: bool = False):
        """
        Initialize the fetcher.

        Args:
            cache_dir: Custom cache directory (default: ~/.cosai-cache)
            force: Force re-download even if cache exists
        """
        self.cache_dir = cache_dir or Path.home() / ".cosai-cache"
        self.force = force
        self.yaml_dir = self.cache_dir / "yaml"
        self.schema_dir = self.cache_dir / "schemas"

    def setup_cache(self) -> None:
        """Create cache directories if they don't exist"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.yaml_dir.mkdir(exist_ok=True)
        self.schema_dir.mkdir(exist_ok=True)
        print(f"✓ Cache directory: {self.cache_dir}")

    def download_file(self, url: str, destination: Path) -> bool:
        """
        Download a file from URL to destination.

        Args:
            url: Source URL
            destination: Local file path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Skip if file exists and not forcing
            if destination.exists() and not self.force:
                print(f"  ✓ {destination.name} (cached)")
                return True

            # Download with User-Agent header
            req = Request(url, headers={'User-Agent': 'CoSAI-Risk-Mapper/1.0'})
            with urlopen(req, timeout=30) as response:
                content = response.read()

            # Write to destination
            destination.write_bytes(content)
            print(f"  ✓ {destination.name} (downloaded)")
            return True

        except HTTPError as e:
            print(f"  ✗ {destination.name} - HTTP {e.code}: {e.reason}", file=sys.stderr)
            return False
        except URLError as e:
            print(f"  ✗ {destination.name} - Network error: {e.reason}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"  ✗ {destination.name} - Error: {e}", file=sys.stderr)
            return False

    def fetch_yaml_files(self) -> List[Path]:
        """
        Fetch all YAML data files.

        Returns:
            List of successfully downloaded file paths
        """
        print("\n📥 Fetching YAML data files...")
        downloaded = []

        for filename in YAML_FILES:
            url = f"{COSAI_REPO}/yaml/{filename}"
            destination = self.yaml_dir / filename

            if self.download_file(url, destination):
                downloaded.append(destination)

        return downloaded

    def fetch_schema_files(self) -> List[Path]:
        """
        Fetch all JSON schema files.

        Returns:
            List of successfully downloaded file paths
        """
        print("\n📥 Fetching JSON schema files...")
        downloaded = []

        for filename in SCHEMA_FILES:
            url = f"{COSAI_REPO}/schemas/{filename}"
            destination = self.schema_dir / filename

            if self.download_file(url, destination):
                downloaded.append(destination)

        return downloaded

    def validate_json_schemas(self) -> bool:
        """
        Validate that downloaded JSON schemas are valid JSON.

        Returns:
            True if all schemas are valid, False otherwise
        """
        print("\n🔍 Validating JSON schemas...")
        all_valid = True

        for schema_file in self.schema_dir.glob("*.schema.json"):
            try:
                with open(schema_file) as f:
                    json.load(f)
                print(f"  ✓ {schema_file.name} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"  ✗ {schema_file.name} - Invalid JSON: {e}", file=sys.stderr)
                all_valid = False

        return all_valid

    def generate_manifest(self, yaml_files: List[Path], schema_files: List[Path]) -> None:
        """
        Generate a manifest file listing all cached files.

        Args:
            yaml_files: List of downloaded YAML file paths
            schema_files: List of downloaded schema file paths
        """
        manifest = {
            "cache_dir": str(self.cache_dir),
            "yaml_files": [f.name for f in yaml_files],
            "schema_files": [f.name for f in schema_files],
            "total_files": len(yaml_files) + len(schema_files),
        }

        manifest_path = self.cache_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n✓ Manifest written to {manifest_path}")

    def get_cache_stats(self) -> Dict[str, any]:
        """
        Get statistics about the cache.

        Returns:
            Dictionary with cache statistics
        """
        yaml_count = len(list(self.yaml_dir.glob("*.yaml")))
        schema_count = len(list(self.schema_dir.glob("*.schema.json")))

        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.rglob("*")
            if f.is_file()
        )

        return {
            "cache_dir": str(self.cache_dir),
            "yaml_files": yaml_count,
            "schema_files": schema_count,
            "total_files": yaml_count + schema_count,
            "total_size_bytes": total_size,
            "total_size_kb": round(total_size / 1024, 2),
        }

    def run(self) -> bool:
        """
        Run the complete fetch operation.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.setup_cache()

            yaml_files = self.fetch_yaml_files()
            schema_files = self.fetch_schema_files()

            if not yaml_files or not schema_files:
                print("\n✗ Failed to download all required files", file=sys.stderr)
                return False

            if not self.validate_json_schemas():
                print("\n✗ Some JSON schemas are invalid", file=sys.stderr)
                return False

            self.generate_manifest(yaml_files, schema_files)

            # Print summary
            stats = self.get_cache_stats()
            print("\n" + "="*60)
            print("📊 Cache Summary")
            print("="*60)
            print(f"  Location:     {stats['cache_dir']}")
            print(f"  YAML files:   {stats['yaml_files']}")
            print(f"  Schema files: {stats['schema_files']}")
            print(f"  Total size:   {stats['total_size_kb']} KB")
            print("="*60)

            return True

        except Exception as e:
            print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fetch and cache CoSAI Risk Map schemas"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if cache exists"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Custom cache directory (default: ~/.cosai-cache)"
    )

    args = parser.parse_args()

    fetcher = CoSAIFetcher(cache_dir=args.cache_dir, force=args.force)
    success = fetcher.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
