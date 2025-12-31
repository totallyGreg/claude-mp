#!/usr/bin/env python3
"""
validate_hook.py - Validates marketplace-manager pre-commit hook installation

Usage:
    python3 validate_hook.py [--json]

Options:
    --json    Output results in JSON format for CI/CD

Exit codes:
    0  - All checks pass
    1  - Hook outdated or missing
    2  - Critical error (not in git repo, template missing, etc.)
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path


def find_repo_root():
    """Find git repository root."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return None


def extract_version(file_path, pattern):
    """Extract version from file using regex pattern."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None


def validate_hook(json_output=False):
    """Validate hook installation and return status."""
    results = {
        "installed": False,
        "executable": False,
        "up_to_date": False,
        "matches_template": False,
        "scripts_present": False,
        "installed_version": None,
        "template_version": None,
        "errors": [],
        "warnings": []
    }
    
    # Find repository root
    repo_root = find_repo_root()
    if not repo_root:
        results["errors"].append("Not in a git repository")
        return results, 2
    
    # Locate template
    script_dir = Path(__file__).parent
    template_path = script_dir / "pre-commit.template"
    
    if not template_path.exists():
        results["errors"].append(f"Template not found: {template_path}")
        return results, 2
    
    # Extract template version
    template_version = extract_version(
        template_path,
        r'^# marketplace-manager pre-commit hook v([\d.]+)'
    )
    results["template_version"] = template_version or "unknown"
    
    # Check hook installation
    hook_path = repo_root / ".git" / "hooks" / "pre-commit"
    
    if not hook_path.exists():
        results["warnings"].append("Hook not installed")
        return results, 1
    
    results["installed"] = True
    
    # Check if executable
    if os.access(hook_path, os.X_OK):
        results["executable"] = True
    else:
        results["warnings"].append("Hook not executable")
    
    # Extract installed version
    installed_version = extract_version(
        hook_path,
        r'^HOOK_VERSION="([\d.]+)"'
    )
    results["installed_version"] = installed_version or "unknown"
    
    # Compare versions
    if template_version and installed_version:
        if template_version == installed_version:
            results["up_to_date"] = True
        else:
            results["warnings"].append(
                f"Version mismatch: installed={installed_version}, "
                f"template={template_version}"
            )
    
    # Check if content matches template
    try:
        with open(template_path, 'r') as f1, open(hook_path, 'r') as f2:
            if f1.read() == f2.read():
                results["matches_template"] = True
    except Exception as e:
        results["warnings"].append(f"Could not compare files: {e}")
    
    # Check if required scripts exist
    sync_script = script_dir / "sync_marketplace_versions.py"
    detect_script = script_dir / "detect_version_changes.py"
    
    if sync_script.exists() and detect_script.exists():
        results["scripts_present"] = True
    else:
        missing = []
        if not sync_script.exists():
            missing.append("sync_marketplace_versions.py")
        if not detect_script.exists():
            missing.append("detect_version_changes.py")
        results["warnings"].append(f"Missing scripts: {', '.join(missing)}")
    
    # Determine exit code
    if results["warnings"]:
        exit_code = 1
    else:
        exit_code = 0
    
    return results, exit_code


def format_human_readable(results, exit_code):
    """Format results for human-readable output."""
    lines = []
    lines.append("🔍 marketplace-manager Hook Validation")
    lines.append("")
    
    # Status summary
    if exit_code == 0:
        lines.append("✅ All checks passed")
    elif exit_code == 1:
        lines.append("⚠️  Issues detected")
    else:
        lines.append("❌ Critical errors")
    
    lines.append("")
    
    # Installation status
    lines.append("Installation Status:")
    lines.append(f"  Installed:      {'✅' if results['installed'] else '❌'}")
    
    if results["installed"]:
        lines.append(f"  Executable:     {'✅' if results['executable'] else '❌'}")
        lines.append(f"  Up-to-date:     {'✅' if results['up_to_date'] else '⚠️ '}")
        lines.append(f"  Matches template: {'✅' if results['matches_template'] else '⚠️ '}")
    
    lines.append(f"  Scripts present: {'✅' if results['scripts_present'] else '❌'}")
    
    lines.append("")
    
    # Version info
    lines.append("Version Info:")
    lines.append(f"  Installed: {results['installed_version'] or 'N/A'}")
    lines.append(f"  Template:  {results['template_version']}")
    
    # Errors and warnings
    if results["errors"]:
        lines.append("")
        lines.append("❌ Errors:")
        for error in results["errors"]:
            lines.append(f"  - {error}")
    
    if results["warnings"]:
        lines.append("")
        lines.append("⚠️  Warnings:")
        for warning in results["warnings"]:
            lines.append(f"  - {warning}")
    
    # Recommendations
    if exit_code != 0:
        lines.append("")
        lines.append("💡 Recommended Action:")
        if not results["installed"]:
            lines.append("  bash skills/marketplace-manager/scripts/install_hook.sh")
        elif not results["up_to_date"] or not results["matches_template"]:
            lines.append("  bash skills/marketplace-manager/scripts/install_hook.sh --force")
        elif not results["executable"]:
            lines.append("  chmod +x .git/hooks/pre-commit")
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    json_output = "--json" in sys.argv
    
    results, exit_code = validate_hook(json_output)
    
    if json_output:
        output = {
            "status": "pass" if exit_code == 0 else ("warning" if exit_code == 1 else "error"),
            "exit_code": exit_code,
            "results": results
        }
        print(json.dumps(output, indent=2))
    else:
        print(format_human_readable(results, exit_code))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
