#!/usr/bin/env python3
"""
Terminal diagnostics tool to check terminal capabilities, environment, and locale settings.
"""

import os
import sys
import locale
import subprocess
import shutil
from pathlib import Path


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


def check_environment():
    """Check terminal-related environment variables."""
    print_section("Environment Variables")

    important_vars = [
        'TERM', 'TERM_PROGRAM', 'COLORTERM', 'SHELL',
        'LANG', 'LC_ALL', 'LC_CTYPE',
        'ZDOTDIR', 'FPATH', 'PATH'
    ]

    for var in important_vars:
        value = os.environ.get(var, '(not set)')
        print(f"{var:15} = {value}")


def check_locale():
    """Check locale settings."""
    print_section("Locale Settings")

    try:
        current_locale = locale.getlocale()
        print(f"Current locale: {current_locale}")
        print(f"Default locale: {locale.getdefaultlocale()}")
        print(f"Preferred encoding: {locale.getpreferredencoding()}")
    except Exception as e:
        print(f"Error checking locale: {e}")

    # Show locale command output
    locale_output = run_command("locale")
    if locale_output:
        print(f"\nlocale command output:\n{locale_output}")


def check_terminal_capabilities():
    """Check terminal capabilities via tput and terminfo."""
    print_section("Terminal Capabilities")

    term = os.environ.get('TERM', 'unknown')
    print(f"TERM type: {term}")

    # Check if terminfo entry exists
    terminfo_check = run_command(f"infocmp {term} >/dev/null 2>&1", capture=False)
    print(f"Terminfo entry exists: {'Yes' if terminfo_check else 'No'}")

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

    print("\nCapabilities:")
    for cap, description in capabilities.items():
        value = run_command(f"tput {cap} 2>/dev/null")
        if value is not None:
            # For control sequences, show hex
            if cap in ['smcup', 'rmcup', 'smso', 'bold', 'dim', 'sitm', 'smul']:
                hex_val = value.encode().hex() if value else '(empty)'
                print(f"  {cap:10} ({description:30}): {hex_val}")
            else:
                print(f"  {cap:10} ({description:30}): {value}")


def check_unicode_support():
    """Check Unicode and UTF-8 support."""
    print_section("Unicode/UTF-8 Support")

    # Check if locale supports UTF-8
    lang = os.environ.get('LANG', '')
    lc_all = os.environ.get('LC_ALL', '')
    lc_ctype = os.environ.get('LC_CTYPE', '')

    utf8_env = 'UTF-8' in lang or 'UTF-8' in lc_all or 'UTF-8' in lc_ctype
    print(f"UTF-8 in environment: {'Yes' if utf8_env else 'No'}")

    # Test Unicode rendering
    print("\nUnicode test characters:")
    test_chars = [
        ('Basic Latin', 'ABC abc 123'),
        ('Box Drawing', '┌─┐│└┘├┤┬┴┼'),
        ('Emoji', '😀 🎉 ✨ 🚀'),
        ('East Asian Width', '你好世界'),
        ('Combining', 'e\u0301 a\u0300'),  # é à with combining accents
        ('Zero Width', 'A\u200bB'),  # Zero-width space
    ]

    for name, chars in test_chars:
        print(f"  {name:20}: {chars}")

    # Check Python's Unicode support
    print(f"\nPython default encoding: {sys.getdefaultencoding()}")
    print(f"stdout encoding: {sys.stdout.encoding}")


def check_shell():
    """Check shell configuration."""
    print_section("Shell Configuration")

    shell = os.environ.get('SHELL', 'unknown')
    print(f"Current shell: {shell}")

    # Determine shell type
    shell_name = Path(shell).name
    print(f"Shell name: {shell_name}")

    if 'zsh' in shell_name:
        # Check Zsh-specific settings
        zdotdir = os.environ.get('ZDOTDIR', os.path.expanduser('~'))
        print(f"ZDOTDIR: {zdotdir}")

        zsh_configs = ['.zshenv', '.zprofile', '.zshrc', '.zlogin', '.zlogout']
        print(f"\nZsh configuration files:")
        for config in zsh_configs:
            config_path = Path(zdotdir) / config
            exists = '✓' if config_path.exists() else '✗'
            print(f"  {exists} {config_path}")

        # Check fpath
        fpath = os.environ.get('FPATH', '')
        if fpath:
            print(f"\nFPATH directories:")
            for path in fpath.split(':'):
                exists = '✓' if Path(path).exists() else '✗'
                print(f"  {exists} {path}")

    elif 'bash' in shell_name:
        # Check Bash-specific settings
        bash_configs = ['.bash_profile', '.bashrc', '.bash_login', '.profile']
        print(f"\nBash configuration files:")
        for config in bash_configs:
            config_path = Path.home() / config
            exists = '✓' if config_path.exists() else '✗'
            print(f"  {exists} {config_path}")


def check_tui_tools():
    """Check for common TUI tools."""
    print_section("TUI Tools")

    tools = [
        'tmux', 'screen', 'vim', 'nvim', 'emacs',
        'htop', 'less', 'more', 'fzf', 'ncurses'
    ]

    print("Installed TUI tools:")
    for tool in tools:
        path = shutil.which(tool)
        if path:
            version = run_command(f"{tool} --version 2>&1 | head -n1")
            print(f"  ✓ {tool:10} -> {path}")
            if version:
                print(f"    Version: {version[:60]}")
        else:
            print(f"  ✗ {tool:10} (not found)")


def main():
    """Run all diagnostics."""
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
