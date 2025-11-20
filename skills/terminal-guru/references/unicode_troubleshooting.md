# Unicode and UTF-8 Troubleshooting Guide

## Overview

Unicode support in terminals involves multiple layers: locale settings, terminal emulator capabilities, font support, and application handling. This guide covers common Unicode/UTF-8 issues and their solutions.

## Understanding Unicode in Terminals

### Character Encoding Hierarchy

1. **Locale** - System setting (e.g., `en_US.UTF-8`)
2. **Terminal Emulator** - Must support UTF-8
3. **Font** - Must contain the required glyphs
4. **Application** - Must be UTF-8 aware
5. **Shell** - Must handle multibyte characters

All layers must support UTF-8 for proper rendering.

## Locale Configuration

### Checking Current Locale

```bash
# Show all locale settings
locale

# Check specific variable
echo $LANG
echo $LC_ALL
echo $LC_CTYPE

# Show available locales
locale -a
```

### Setting UTF-8 Locale

```bash
# Temporary (current session)
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export LANG=en_US.UTF-8' >> ~/.zshrc
echo 'export LC_ALL=en_US.UTF-8' >> ~/.zshrc

# macOS specific
defaults write -g AppleLocale en_US.UTF-8
```

### Generating Locales (Linux)

```bash
# Debian/Ubuntu
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8

# Arch Linux
# Uncomment desired locale in /etc/locale.gen
sudo nano /etc/locale.gen
sudo locale-gen

# RHEL/CentOS
sudo localedef -i en_US -f UTF-8 en_US.UTF-8
```

## Character Width Issues

### Understanding Character Width

Unicode characters have different display widths:
- **Narrow (width 1)**: ASCII, most Latin characters
- **Wide (width 2)**: CJK (Chinese, Japanese, Korean) characters
- **Zero-width**: Combining characters, zero-width joiners
- **Ambiguous**: Characters that can be narrow or wide depending on context

### East Asian Width

```bash
# Check character width in shell
printf "A\n你\n" | while IFS= read -r char; do
    echo "Character: $char"
    # Zsh has built-in width calculation
    echo "Width: ${#${(%):-$char}}"
done
```

### Testing Character Width

```python
#!/usr/bin/env python3
import unicodedata

def char_width(char):
    """Get East Asian Width property"""
    return unicodedata.east_asian_width(char)

def display_width(text):
    """Calculate display width"""
    import wcwidth
    return wcwidth.wcswidth(text)

# Test characters
test_chars = ['A', '你', '🎉', 'é']
for char in test_chars:
    width_prop = char_width(char)
    print(f"{char}: East Asian Width={width_prop}")
```

### Common Width Problems

**Problem**: CJK characters misaligned in columns

**Diagnosis**:
```bash
# Test with known-width characters
printf "ASCII: %s\n" "Hello"
printf "CJK:   %s\n" "你好"
# If they don't align, there's a width calculation issue
```

**Solutions**:
1. Ensure font supports CJK characters
2. Set locale to UTF-8
3. Use `wcwidth`-aware applications
4. Configure terminal to handle ambiguous width

## Combining Characters

### What Are Combining Characters?

Combining characters modify the preceding character:
- Accents: `e` + `́` = `é` (e + combining acute accent)
- Diacritics: `a` + `̃` = `ã` (a + combining tilde)

### Issues with Combining Characters

```bash
# Precomposed vs composed
echo "café"  # precomposed é (U+00E9)
echo "café"  # e (U+0065) + combining acute (U+0301)

# They look the same but have different byte lengths
```

### Normalization

```python
#!/usr/bin/env python3
import unicodedata

text = "café"  # Could be composed or precomposed

# NFD - Canonical Decomposition
nfd = unicodedata.normalize('NFD', text)

# NFC - Canonical Decomposition + Canonical Composition
nfc = unicodedata.normalize('NFC', text)

# NFKD - Compatibility Decomposition
nfkd = unicodedata.normalize('NFKD', text)

# NFKC - Compatibility Decomposition + Canonical Composition
nfkc = unicodedata.normalize('NFKC', text)

print(f"Original: {len(text)} chars")
print(f"NFC: {len(nfc)} chars")
print(f"NFD: {len(nfd)} chars")
```

In the shell:
```bash
# Use iconv for normalization
echo "café" | iconv -f UTF-8 -t UTF-8-MAC  # macOS NFD
echo "café" | iconv -f UTF-8-MAC -t UTF-8  # Back to NFC
```

## Emoji and Special Characters

### Emoji Rendering

Emoji complexity:
- **Simple emoji**: Single codepoint (e.g., 😀 U+1F600)
- **Emoji with modifiers**: Base + modifier (e.g., 👍🏽 = 👍 + 🏽)
- **ZWJ sequences**: Multiple emoji joined with zero-width joiner (e.g., 👨‍👩‍👧 = 👨 + ZWJ + 👩 + ZWJ + 👧)

### Testing Emoji Support

```bash
# Simple emoji
echo "😀 🎉 ✨ 🚀"

# Emoji with skin tone modifiers
echo "👍 👍🏻 👍🏼 👍🏽 👍🏾 👍🏿"

# ZWJ sequences (may not render correctly)
echo "👨‍👩‍👧‍👦"  # Family

# Flags (regional indicators)
echo "🇺🇸 🇬🇧 🇯🇵"
```

### Emoji Width Issues

Emoji typically have width 2, but terminals may vary:

```bash
# Test emoji alignment
printf "ASCII:  %s\n" "Hi"
printf "Emoji:  %s\n" "😀"
printf "CJK:    %s\n" "你"
```

## Box Drawing and Line Characters

### Box Drawing Characters

```bash
# Single-line box
┌─┬─┐
│ │ │
├─┼─┤
│ │ │
└─┴─┘

# Double-line box
╔═╦═╗
║ ║ ║
╠═╬═╣
║ ║ ║
╚═╩═╝

# Block elements
█ ▓ ▒ ░
```

### Common Box Drawing Issues

**Issue**: Box characters appear as `q`, `x`, `m`, `j`, etc.

**Diagnosis**:
- Terminal using wrong character set
- Falling back to VT100 line drawing mode
- Locale not set to UTF-8

**Solution**:
```bash
# Ensure UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# For ncurses applications
export NCURSES_NO_UTF8_ACS=0

# If issue persists, might need to disable ACS
export NCURSES_NO_UTF8_ACS=1
```

### Alternative Character Sets (ACS)

Some terminals use special character sets for box drawing:
- **VT100 ACS**: Uses Shift-In/Shift-Out (SO/SI) codes
- **Unicode Box Drawing**: Uses U+2500–U+257F range

```bash
# Test box drawing
printf '\u2502\n'  # │ (Unicode)
printf '\016x\017\n'  # x with SO/SI (VT100)
```

## Zero-Width Characters

### Types of Zero-Width Characters

- **Zero Width Space (ZWSP)**: U+200B
- **Zero Width Non-Joiner (ZWNJ)**: U+200C
- **Zero Width Joiner (ZWJ)**: U+200D
- **Zero Width No-Break Space (BOM)**: U+FEFF

### Detecting Zero-Width Characters

```bash
# Create test string with zero-width space
test="A$(printf '\u200b')B"
echo "$test"  # Looks like "AB"
echo "${#test}"  # Length is 3 (not 2!)

# Visualize with hexdump
echo "$test" | hexdump -C

# Find zero-width characters in file
grep -P '\u200b' file.txt
```

### Removing Zero-Width Characters

```bash
# Remove ZWSP
echo "$text" | tr -d '\u200b'

# Remove all zero-width characters
echo "$text" | sed 's/[\u200B-\u200D\uFEFF]//g'

# Using iconv
echo "$text" | iconv -f UTF-8 -t ASCII//TRANSLIT
```

## Byte Order Mark (BOM)

### Understanding BOM

The UTF-8 BOM (U+FEFF, bytes: EF BB BF) indicates UTF-8 encoding but is not required and often causes issues in Unix.

### Detecting BOM

```bash
# Check for BOM at start of file
head -c 3 file.txt | xxd

# Check if file starts with BOM
[[ $(head -c 3 file.txt) == $'\xef\xbb\xbf' ]] && echo "Has BOM"
```

### Removing BOM

```bash
# Remove BOM from file
sed -i '1s/^\xEF\xBB\xBF//' file.txt

# Using tail
tail -c +4 file_with_bom.txt > file_without_bom.txt

# Using dos2unix (if available)
dos2unix -r file.txt

# Using vim
vim -c "set nobomb" -c "wq" file.txt
```

## Terminal Emulator Configuration

### Modern Terminal Emulators

**iTerm2 (macOS)**:
- Preferences → Profiles → Text → "Unicode normalization form: NFC"
- Preferences → Profiles → Text → "Treat ambiguous characters as double width"

**Alacritty**:
```yaml
# ~/.config/alacritty/alacritty.yml
font:
  use_thin_strokes: true  # macOS only

# Enable proper rendering
env:
  LANG: "en_US.UTF-8"
  LC_ALL: "en_US.UTF-8"
```

**Kitty**:
```conf
# ~/.config/kitty/kitty.conf
# Always use Unicode
allow_remote_control yes
```

**GNOME Terminal / Konsole**:
- Edit → Preferences → Character Encoding → UTF-8

### Font Selection

Ensure fonts support required characters:

**Good monospace fonts with wide Unicode support**:
- Nerd Fonts (patched with many glyphs)
- JetBrains Mono
- Fira Code
- Cascadia Code
- Source Code Pro
- DejaVu Sans Mono

**Check font coverage**:
```bash
# List available glyphs in font (requires fontconfig)
fc-list "Nerd Font" -v | grep charset
```

## Diagnostic Commands

### Quick Diagnostics

```bash
#!/bin/bash
# Unicode diagnostics script

echo "=== Locale ==="
locale | grep UTF-8

echo -e "\n=== Environment ==="
echo "LANG=$LANG"
echo "LC_ALL=$LC_ALL"
echo "LC_CTYPE=$LC_CTYPE"

echo -e "\n=== Terminal ==="
echo "TERM=$TERM"

echo -e "\n=== UTF-8 Test ==="
echo "ASCII: ABC 123"
echo "Latin: café naïve"
echo "Greek: α β γ δ"
echo "Cyrillic: Привет"
echo "CJK: 你好世界"
echo "Arabic: مرحبا"
echo "Emoji: 😀 🎉 ✨"
echo "Box: ┌─┐│└┘"

echo -e "\n=== Width Test ==="
printf "%-10s %s\n" "ASCII:" "Hello"
printf "%-10s %s\n" "CJK:" "你好"
printf "%-10s %s\n" "Emoji:" "😀😀"
```

## Common Problems and Solutions

### Problem: Garbled characters

**Symptoms**: Characters appear as �, boxes, or random symbols

**Diagnosis**:
```bash
# Check file encoding
file -i filename.txt

# Check for valid UTF-8
iconv -f UTF-8 -t UTF-8 filename.txt > /dev/null
```

**Solution**:
```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt

# Set correct locale
export LANG=en_US.UTF-8
```

### Problem: String length incorrect

**Symptoms**: `${#string}` returns wrong length

**Diagnosis**: String contains multi-byte characters

**Solution** (Zsh):
```bash
# Zsh: Use ${(m)#string} for character count
text="你好"
echo ${#text}      # Byte count (6)
echo ${(m)#text}   # Character count (2)
```

**Solution** (Bash):
```bash
# Bash: Use wc
text="你好"
echo -n "$text" | wc -m  # Character count
```

### Problem: Cursor misalignment

**Symptoms**: Cursor doesn't align with characters

**Causes**:
- Terminal width calculation wrong
- Font doesn't match character widths
- Ambiguous width characters

**Solution**:
```bash
# For ambiguous width, configure terminal
# iTerm2: Treat ambiguous as double-width
# Or set in application if supported

# Test cursor alignment
printf "%-20s|\n" "ASCII text"
printf "%-20s|\n" "你好 text"
```

### Problem: Text editor displays wrong

**Symptoms**: Vim/Emacs displays characters incorrectly

**Solution** (Vim):
```vim
" In ~/.vimrc
set encoding=utf-8
set fileencoding=utf-8
set termencoding=utf-8
```

**Solution** (Emacs):
```elisp
; In ~/.emacs
(prefer-coding-system 'utf-8)
(set-default-coding-systems 'utf-8)
(set-terminal-coding-system 'utf-8)
(set-keyboard-coding-system 'utf-8)
```

## Testing Unicode Support

### Comprehensive Test

```bash
#!/bin/bash
# Save as unicode_test.sh

cat << 'EOF'
=== Unicode Rendering Test ===

1. ASCII (width 1):
   ABCDEFGHIJKLMNOPQRSTUVWXYZ
   abcdefghijklmnopqrstuvwxyz
   0123456789

2. Latin Extended (width 1):
   àáâãäåæçèéêë
   ÀÁÂÃÄÅÆÇÈÉÊË

3. Greek (width 1):
   αβγδεζηθικλμνξοπρστυφχψω
   ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ

4. Cyrillic (width 1):
   абвгдеёжзийклмнопрстуфхцчшщъыьэюя
   АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ

5. CJK (width 2):
   Chinese: 你好世界
   Japanese: こんにちは 日本語
   Korean: 안녕하세요

6. Box Drawing (width 1):
   ┌─┬─┐  ╔═╦═╗
   │ │ │  ║ ║ ║
   ├─┼─┤  ╠═╬═╣
   │ │ │  ║ ║ ║
   └─┴─┘  ╚═╩═╝

7. Block Elements (width 1):
   █▓▒░ ▀▄ ▌▐

8. Symbols (mostly width 1):
   ← ↑ → ↓ ↔ ↕
   ✓ ✗ ★ ☆ ♠ ♣ ♥ ♦
   ©®™ ℃℉ № ⁰¹²³

9. Emoji (width 2):
   😀 😃 😄 😁 😅
   🎉 🎊 🎈 🎁 🎀
   🚀 🚁 🚂 🚃 🚄
   ❤️ 💛 💚 💙 💜

10. Math (width 1):
    ∀∂∃∅∈∉∋∏∑
    ∫∮∞∧∨∩∪⊂⊃

EOF
```

## Resources

- Unicode Standard: https://unicode.org/standard/standard.html
- Unicode Character Database: https://unicode.org/ucd/
- `man locale`
- `man iconv`
- `man utf-8` (on some systems)
- Python `unicodedata` module documentation
