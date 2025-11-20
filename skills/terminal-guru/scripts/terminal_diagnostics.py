#!/usr/bin/env python3
"""
Terminal diagnostics tool to check terminal capabilities, environment, and locale settings.

Supports both human-readable output and JSON format for programmatic analysis.
"""

import os
import sys
import locale
import subprocess
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, Any


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def run_command(cmd, capture=True):
    """Run a shell command and return output."""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.stdout.strip() if result.returncode == 0 else None
        else:
            subprocess.run(cmd, shell=True, timeout=5)
            return True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return None


def check_environment(json_mode=False):
    """Check terminal-related environment variables."""
    important_vars = [
        'TERM', 'TERM_PROGRAM', 'COLORTERM', 'SHELL',
        'LANG', 'LC_ALL', 'LC_CTYPE',
        'ZDOTDIR', 'FPATH', 'PATH'
    ]

    env_data = {}
    for var in important_vars:
        env_data[var] = os.environ.get(var, None)

    if not json_mode:
        print_section("Environment Variables")
        for var in important_vars:
            value = env_data[var] if env_data[var] else '(not set)'
            print(f"{var:15} = {value}")

    return env_data


def check_locale(json_mode=False):
    """Check locale settings."""
    locale_data = {}

    try:
        current_locale = locale.getlocale()
        locale_data['current_locale'] = str(current_locale)
        locale_data['default_locale'] = str(locale.getdefaultlocale())
        locale_data['preferred_encoding'] = locale.getpreferredencoding()
    except Exception as e:
        locale_data['error'] = str(e)

    # Get locale command output
    locale_output = run_command("locale")
    if locale_output:
        locale_data['locale_command'] = locale_output

    if not json_mode:
        print_section("Locale Settings")
        print(f"Current locale: {locale_data.get('current_locale', 'N/A')}")
        print(f"Default locale: {locale_data.get('default_locale', 'N/A')}")
        print(f"Preferred encoding: {locale_data.get('preferred_encoding', 'N/A')}")
        if 'error' in locale_data:
            print(f"Error checking locale: {locale_data['error']}")
        if 'locale_command' in locale_data:
            print(f"\nlocale command output:\n{locale_data['locale_command']}")

    return locale_data


def check_terminal_capabilities(json_mode=False):
    """Check terminal capabilities via tput and terminfo."""
    term = os.environ.get('TERM', 'unknown')
    cap_data = {'term': term}

    # Check if terminfo entry exists
    terminfo_check = run_command(f"infocmp {term} >/dev/null 2>&1", capture=False)
    cap_data['terminfo_exists'] = bool(terminfo_check)

    # Check common capabilities
    capabilities = {
        'colors': 'Number of colors',
        'lines': 'Terminal lines',
        'cols': 'Terminal columns',
        'smcup': 'Enter alternate screen',
        'rmcup': 'Exit alternate screen',
        'smso': 'Enter standout mode',
        'bold': 'Bold text',
        'dim': 'Dim text',
        'sitm': 'Enter italics',
        'smul': 'Start underline',
    }

    cap_data['capabilities'] = {}
    for cap, description in capabilities.items():
        value = run_command(f"tput {cap} 2>/dev/null")
        if value is not None:
            # For control sequences, store hex
            if cap in ['smcup', 'rmcup', 'smso', 'bold', 'dim', 'sitm', 'smul']:
                cap_data['capabilities'][cap] = {
                    'description': description,
                    'value': value.encode().hex() if value else ''
                }
            else:
                cap_data['capabilities'][cap] = {
                    'description': description,
                    'value': value
                }

    if not json_mode:
        print_section("Terminal Capabilities")
        print(f"TERM type: {term}")
        print(f"Terminfo entry exists: {'Yes' if cap_data['terminfo_exists'] else 'No'}")
        print("\nCapabilities:")
        for cap, data in cap_data['capabilities'].items():
            print(f"  {cap:10} ({data['description']:30}): {data['value']}")

    return cap_data


def check_unicode_support(json_mode=False):
    """Check Unicode and UTF-8 support."""
    unicode_data = {}

    # Check if locale supports UTF-8
    lang = os.environ.get('LANG', '')
    lc_all = os.environ.get('LC_ALL', '')
    lc_ctype = os.environ.get('LC_CTYPE', '')

    utf8_env = 'UTF-8' in lang or 'UTF-8' in lc_all or 'UTF-8' in lc_ctype
    unicode_data['utf8_in_env'] = utf8_env

    # Test Unicode rendering
    test_chars = [
        ('Basic Latin', 'ABC abc 123'),
        ('Box Drawing', '┌─┐│└┘├┤┬┴┼'),
        ('Emoji', '😀 🎉 ✨ 🚀'),
        ('East Asian Width', '你好世界'),
        ('Combining', 'e\u0301 a\u0300'),  # é à with combining accents
        ('Zero Width', 'A\u200bB'),  # Zero-width space
    ]

    unicode_data['test_chars'] = {name: chars for name, chars in test_chars}

    # Check Python's Unicode support
    unicode_data['python_default_encoding'] = sys.getdefaultencoding()
    unicode_data['stdout_encoding'] = sys.stdout.encoding

    if not json_mode:
        print_section("Unicode/UTF-8 Support")
        print(f"UTF-8 in environment: {'Yes' if utf8_env else 'No'}")
        print("\nUnicode test characters:")
        for name, chars in test_chars:
            print(f"  {name:20}: {chars}")
        print(f"\nPython default encoding: {unicode_data['python_default_encoding']}")
        print(f"stdout encoding: {unicode_data['stdout_encoding']}")

    return unicode_data


def check_shell(json_mode=False):
    """Check shell configuration."""
    shell = os.environ.get('SHELL', 'unknown')
    shell_name = Path(shell).name
    shell_data = {
        'shell': shell,
        'shell_name': shell_name
    }

    if 'zsh' in shell_name:
        # Check Zsh-specific settings
        zdotdir = os.environ.get('ZDOTDIR', os.path.expanduser('~'))
        shell_data['zdotdir'] = zdotdir

        zsh_configs = ['.zshenv', '.zprofile', '.zshrc', '.zlogin', '.zlogout']
        shell_data['config_files'] = {}
        for config in zsh_configs:
            config_path = Path(zdotdir) / config
            shell_data['config_files'][config] = {
                'path': str(config_path),
                'exists': config_path.exists()
            }

        # Check fpath
        fpath = os.environ.get('FPATH', '')
        if fpath:
            shell_data['fpath'] = []
            for path in fpath.split(':'):
                shell_data['fpath'].append({
                    'path': path,
                    'exists': Path(path).exists()
                })

    elif 'bash' in shell_name:
        # Check Bash-specific settings
        bash_configs = ['.bash_profile', '.bashrc', '.bash_login', '.profile']
        shell_data['config_files'] = {}
        for config in bash_configs:
            config_path = Path.home() / config
            shell_data['config_files'][config] = {
                'path': str(config_path),
                'exists': config_path.exists()
            }

    if not json_mode:
        print_section("Shell Configuration")
        print(f"Current shell: {shell}")
        print(f"Shell name: {shell_name}")

        if 'zsh' in shell_name:
            print(f"ZDOTDIR: {shell_data['zdotdir']}")
            print("\nZsh configuration files:")
            for config, data in shell_data['config_files'].items():
                exists = '✓' if data['exists'] else '✗'
                print(f"  {exists} {data['path']}")

            if 'fpath' in shell_data:
                print("\nFPATH directories:")
                for fpath_data in shell_data['fpath']:
                    exists = '✓' if fpath_data['exists'] else '✗'
                    print(f"  {exists} {fpath_data['path']}")

        elif 'bash' in shell_name:
            print("\nBash configuration files:")
            for config, data in shell_data['config_files'].items():
                exists = '✓' if data['exists'] else '✗'
                print(f"  {exists} {data['path']}")

    return shell_data


def check_tui_tools(json_mode=False):
    """Check for common TUI tools."""
    tools = [
        'tmux', 'screen', 'vim', 'nvim', 'emacs',
        'htop', 'less', 'more', 'fzf', 'ncurses'
    ]

    tools_data = {}
    for tool in tools:
        path = shutil.which(tool)
        if path:
            version = run_command(f"{tool} --version 2>&1 | head -n1")
            tools_data[tool] = {
                'installed': True,
                'path': path,
                'version': version if version else 'unknown'
            }
        else:
            tools_data[tool] = {
                'installed': False
            }

    if not json_mode:
        print_section("TUI Tools")
        print("Installed TUI tools:")
        for tool, data in tools_data.items():
            if data['installed']:
                print(f"  ✓ {tool:10} -> {data['path']}")
                if data.get('version') and data['version'] != 'unknown':
                    print(f"    Version: {data['version'][:60]}")
            else:
                print(f"  ✗ {tool:10} (not found)")

    return tools_data


def collect_diagnostics_data() -> Dict[str, Any]:
    """Collect all diagnostic data in JSON-compatible format."""
    return {
        'environment': check_environment(json_mode=True),
        'locale': check_locale(json_mode=True),
        'terminal_capabilities': check_terminal_capabilities(json_mode=True),
        'unicode_support': check_unicode_support(json_mode=True),
        'shell': check_shell(json_mode=True),
        'tui_tools': check_tui_tools(json_mode=True)
    }


def main():
    """Run all diagnostics."""
    parser = argparse.ArgumentParser(
        description='Terminal diagnostics tool'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Write output to file'
    )

    args = parser.parse_args()

    if args.json:
        # JSON output mode
        data = collect_diagnostics_data()
        output = json.dumps(data, indent=2)

        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"Diagnostics written to {args.output}")
        else:
            print(output)
    else:
        # Human-readable output mode
        print("=" * 60)
        print("  TERMINAL DIAGNOSTICS")
        print("=" * 60)

        check_environment()
        check_locale()
        check_terminal_capabilities()
        check_unicode_support()
        check_shell()
        check_tui_tools()

        print("\n" + "=" * 60)
        print("  Diagnostics complete")
        print("=" * 60)


if __name__ == '__main__':
    main()
