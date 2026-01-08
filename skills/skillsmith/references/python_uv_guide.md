# Python Scripts in Skills: uv + PEP 723 Guide

This guide covers best practices for Python scripts in AgentSkills using `uv` and PEP 723 inline metadata.

## Why uv for Agent Workflows?

When an agent executes a Python script, `uv` provides critical advantages:

| Aspect | Traditional `pip` + `venv` | `uv` + PEP 723 |
|--------|---------------------------|----------------|
| **Execution Speed** | 5-60 seconds (pip install) | <100ms (cached) |
| **Token Cost** | 200-500 tokens (install logs) | 0 tokens |
| **Setup Complexity** | Multiple commands | Single command: `uv run` |
| **Isolation** | Manual venv management | Automatic ephemeral envs |
| **Portability** | Separate requirements.txt | Self-contained script |

**Bottom line**: `uv` makes scripts faster, cleaner, and more agent-friendly.

## Installing uv

One-time system setup:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip (if you must)
pip install uv
```

Verify installation:
```bash
uv --version
```

## PEP 723: Inline Script Metadata

PEP 723 allows embedding dependency declarations directly in Python files using a special comment block.

### Basic Structure

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0",
#   "pyyaml>=6.0",
# ]
# ///

import requests
import yaml

# ... script code
```

### The Metadata Block

The block **must** follow this exact format:

1. Starts with `# /// script` (note: three slashes)
2. Contains `dependencies = [...]` as a TOML array
3. Ends with `# ///`
4. Must appear before any import statements

### Version Pinning Best Practices

**For libraries (most dependencies):**
```python
# dependencies = [
#   "requests>=2.31.0,<3.0.0",  # Allow minor/patch updates
#   "pyyaml>=6.0,<7.0",          # Allow patch updates
# ]
```

**For critical dependencies where exact version matters:**
```python
# dependencies = [
#   "pandas==2.1.4",             # Exact version
#   "numpy==1.26.2",             # Exact version
# ]
```

**For pre-release or development versions:**
```python
# dependencies = [
#   "some-lib>=1.0.0a1",         # Allow alpha/beta
# ]
```

## Execution Patterns

### Standard Execution

```bash
uv run scripts/my_script.py
```

This automatically:
1. Reads the PEP 723 metadata block
2. Creates an ephemeral environment
3. Installs dependencies (or uses cache)
4. Executes the script
5. Cleans up (environment persists in cache for reuse)

### Quiet Mode (Recommended for Agent Workflows)

```bash
uv run --quiet scripts/my_script.py
```

Suppresses dependency resolution output, keeping agent context clean.

### With Arguments

```bash
uv run scripts/process_data.py --input data.csv --output result.json
```

Arguments after the script name are passed through normally.

## Complete Example

Here's a production-ready script following all best practices:

```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0,<3.0.0",
#   "pyyaml>=6.0.1",
#   "click>=8.1.0,<9.0.0",
# ]
# ///
"""
Data Fetcher Script

Fetches data from an API and saves to YAML format.

Usage:
    uv run scripts/fetch_data.py --url <api_url> --output <file.yaml>

Example:
    uv run scripts/fetch_data.py --url https://api.example.com/data --output result.yaml
"""

import sys
from pathlib import Path

import click
import requests
import yaml


@click.command()
@click.option('--url', required=True, help='API URL to fetch from')
@click.option('--output', required=True, type=click.Path(), help='Output YAML file')
def main(url: str, output: str):
    """Fetch data from API and save as YAML."""
    try:
        # Fetch data
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Save to YAML
        output_path = Path(output)
        with output_path.open('w') as f:
            yaml.dump(data, f, default_flow_style=False)

        print(f"✓ Data saved to {output}")

    except requests.RequestException as e:
        print(f"✗ HTTP error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Development Workflow

### During Active Development

When rapidly iterating on a script, creating a persistent environment can be faster:

```bash
# Create a virtual environment once
uv venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies manually
uv pip install requests pyyaml

# Run script directly
python scripts/my_script.py
```

**However**: Once development is complete, switch to `uv run` for production use.

### For Production Use

Always use `uv run` in:
- SKILL.md documentation
- Agent instructions
- CI/CD pipelines
- End-user examples

## Troubleshooting

### Dependency Resolution Fails

Remove `--quiet` to see full output:
```bash
uv run scripts/my_script.py
```

Common issues:
- **Version conflict**: Adjust version constraints
- **Package not found**: Check package name spelling (PyPI vs import name)
- **Platform incompatibility**: Some packages don't support all platforms

### Cache Issues

Clear the uv cache:
```bash
uv cache clean
```

Cache location: `~/.cache/uv/` (Linux/macOS) or `%LOCALAPPDATA%\uv\cache\` (Windows)

### Script Works with python3 but Fails with uv run

Check that:
1. PEP 723 block syntax is exactly correct (three slashes: `# ///`)
2. Block appears before all imports
3. Dependencies list is valid TOML array format
4. No system-level dependencies are missing (uv only handles Python packages)

## Converting Existing Scripts

To convert a script from traditional to PEP 723 format:

**Before:**
```python
#!/usr/bin/env python3
# requirements.txt needed separately

import requests
import yaml
```

**After:**
```python
#!/usr/bin/env python3
# /// script
# dependencies = [
#   "requests>=2.31.0,<3.0.0",
#   "pyyaml>=6.0.1",
# ]
# ///

import requests
import yaml
```

**Steps:**
1. Read existing `requirements.txt` (if present)
2. Add PEP 723 block before imports
3. Convert each requirement to TOML array format
4. Add version constraints if missing
5. Update SKILL.md to use `uv run` instead of `python3`
6. Delete `requirements.txt` (no longer needed)
7. Test with `uv run scripts/script_name.py`

## Documentation in SKILL.md

When referencing script execution in SKILL.md, use this format:

```markdown
## Using the Data Processor

To process data:

```bash
uv run scripts/process_data.py --input data.csv --output results.json
```

The script will:
1. Load and validate the CSV
2. Transform the data
3. Export to JSON format
```

**Do NOT include**:
- pip install instructions
- venv creation steps
- Requirements file references

The `uv run` command handles everything.

## FAQ

**Q: What if uv isn't installed?**
A: Skills requiring Python scripts should list `uv` in the compatibility field. Users must install it.

**Q: Can I use uv with Python 2?**
A: No. uv requires Python 3.8+. All modern skills should use Python 3.

**Q: Does this work on Windows?**
A: Yes. uv supports Windows, macOS, and Linux.

**Q: What about scripts with no dependencies?**
A: Still use PEP 723 with an empty dependencies array:
```python
# /// script
# dependencies = []
# ///
```

**Q: Can I use requirements.txt alongside PEP 723?**
A: Technically yes, but don't. Choose one approach. For skills, PEP 723 is preferred.

## Summary Checklist

When creating or updating Python scripts in skills:

- [ ] PEP 723 metadata block at top of script
- [ ] Dependencies with version constraints
- [ ] Shebang line: `#!/usr/bin/env python3`
- [ ] Docstring with usage example showing `uv run`
- [ ] SKILL.md uses `uv run` in examples
- [ ] Tested with `uv run scripts/script_name.py`
- [ ] No requirements.txt file (dependencies in script)
- [ ] Compatibility field mentions `uv` requirement
