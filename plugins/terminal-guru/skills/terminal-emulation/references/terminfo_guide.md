# Terminfo Database Guide

## Overview

The terminfo database is a comprehensive collection of terminal capability descriptions used by Unix-like systems to control terminal behavior. Understanding terminfo is essential for diagnosing terminal issues, optimizing TUI applications, and configuring terminal emulators.

## Key Concepts

### Terminal Type (TERM)

The `TERM` environment variable specifies which terminfo entry to use. Common values:
- `xterm-256color` - xterm with 256 color support
- `screen-256color` - GNU screen with 256 colors
- `tmux-256color` - tmux with 256 colors
- `xterm` - basic xterm
- `dumb` - minimal terminal with no special capabilities

### Terminfo Database Locations

Terminfo entries are stored in compiled binary format at:
- `/usr/share/terminfo/` - System-wide database (standard location)
- `/lib/terminfo/` - Alternative system location
- `~/.terminfo/` - User-specific overrides
- `$TERMINFO` - Custom location (if set)

Files are organized by first letter: `/usr/share/terminfo/x/xterm-256color`

## Essential Commands

### infocmp - Compare and decompile terminfo entries

```bash
# Display current terminal's terminfo entry
infocmp

# Display specific terminal type
infocmp xterm-256color

# Compare two terminal types
infocmp xterm-256color xterm

# Show only differences
infocmp -d xterm-256color xterm

# Output in termcap format (legacy)
infocmp -C
```

### tic - Compile terminfo descriptions

```bash
# Compile a terminfo source file
tic myterminal.ti

# Install to user directory
tic -o ~/.terminfo myterminal.ti

# Verbose output
tic -v myterminal.ti
```

### tput - Query and set terminal capabilities

```bash
# Get number of colors
tput colors

# Get terminal dimensions
tput cols
tput lines

# Move cursor to row 5, column 10
tput cup 5 10

# Clear screen
tput clear

# Set bold text
tput bold

# Reset attributes
tput sgr0

# Enter standout mode (reverse video)
tput smso

# Exit standout mode
tput rmso
```

### toe - List available terminal types

```bash
# List all terminfo entries
toe

# List with descriptions
toe -a

# Search for specific terminals
toe | grep xterm
```

## Important Capabilities

### Display Capabilities

| Capability | Name | Description |
|------------|------|-------------|
| `colors` | max_colors | Maximum number of colors |
| `cols` | columns | Number of columns |
| `lines` | lines | Number of lines |
| `it` | init_tabs | Tab stops initially every # spaces |

### Cursor Movement

| Capability | Name | Description |
|------------|------|-------------|
| `cup` | cursor_address | Move cursor to row #1, col #2 |
| `home` | cursor_home | Home cursor |
| `cuu1` | cursor_up | Move cursor up one line |
| `cud1` | cursor_down | Move cursor down one line |
| `cuf1` | cursor_right | Move cursor right one space |
| `cub1` | cursor_left | Move cursor left one space |

### Text Attributes

| Capability | Name | Description |
|------------|------|-------------|
| `bold` | enter_bold_mode | Turn on bold |
| `dim` | enter_dim_mode | Turn on half-bright mode |
| `smul` | enter_underline_mode | Begin underline |
| `rmul` | exit_underline_mode | End underline |
| `smso` | enter_standout_mode | Begin standout mode |
| `rmso` | exit_standout_mode | End standout mode |
| `sitm` | enter_italics_mode | Enter italic mode |
| `ritm` | exit_italics_mode | Exit italic mode |
| `sgr0` | exit_attribute_mode | Turn off all attributes |

### Color Capabilities

| Capability | Name | Description |
|------------|------|-------------|
| `setaf` | set_a_foreground | Set ANSI foreground color |
| `setab` | set_a_background | Set ANSI background color |
| `setf` | set_foreground | Set foreground color (non-ANSI) |
| `setb` | set_background | Set background color (non-ANSI) |
| `op` | orig_pair | Set default color pair |

### Screen Management

| Capability | Name | Description |
|------------|------|-------------|
| `clear` | clear_screen | Clear screen and home cursor |
| `el` | clr_eol | Clear to end of line |
| `ed` | clr_eos | Clear to end of screen |
| `smcup` | enter_ca_mode | Enter alternate screen |
| `rmcup` | exit_ca_mode | Exit alternate screen |

## Common Issues and Solutions

### Issue: Wrong TERM value

**Symptoms:**
- Garbled output
- Function keys don't work
- Colors appear wrong or missing
- Box drawing characters broken

**Diagnosis:**
```bash
echo $TERM
infocmp $TERM  # Check if entry exists
```

**Solution:**
```bash
# Try xterm-256color for modern terminals
export TERM=xterm-256color

# For tmux/screen
export TERM=tmux-256color  # or screen-256color

# Add to shell config to persist
echo 'export TERM=xterm-256color' >> ~/.zshrc
```

### Issue: Missing terminfo entry

**Symptoms:**
- Error: "unknown terminal type"
- Terminal behaves like 'dumb'

**Diagnosis:**
```bash
infocmp $TERM 2>&1 | grep -q "unknown" && echo "Missing"
```

**Solution:**
```bash
# Option 1: Use a compatible TERM
export TERM=xterm-256color

# Option 2: Copy terminfo from another system
infocmp xterm-256color > /tmp/xterm-256color.ti
# Transfer file to target system
tic /tmp/xterm-256color.ti

# Option 3: Install ncurses-term package (Debian/Ubuntu)
sudo apt-get install ncurses-term
```

### Issue: Colors not working

**Diagnosis:**
```bash
# Check color support
tput colors

# Test colors
for i in {0..255}; do
    tput setaf $i
    printf "█"
done
tput sgr0
echo
```

**Solution:**
```bash
# Ensure TERM supports colors
export TERM=xterm-256color

# Check COLORTERM variable
export COLORTERM=truecolor  # For true color support
```

### Issue: Box drawing characters broken

**Symptoms:**
- Lines appear as 'q', 'x', 'm', etc.
- TUI apps look corrupted

**Diagnosis:**
- Often related to locale/charset issues
- Check with: `locale | grep UTF`

**Solution:**
```bash
# Ensure UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Some terminals need this
export NCURSES_NO_UTF8_ACS=1
```

## Custom Terminfo Entries

### Creating a custom entry

```bash
# Start with existing entry
infocmp xterm-256color > custom.ti

# Edit the file
# Change the terminal name in first line
# Modify capabilities as needed

# Compile and install
tic -o ~/.terminfo custom.ti
```

### Example: Extending an entry

```terminfo
# File: xterm-custom.ti
xterm-custom|xterm with custom settings,
    use=xterm-256color,
    # Add or override capabilities here
    kf13=\E[25~,    # Define F13 key
    kf14=\E[26~,    # Define F14 key
```

Compile with:
```bash
tic -o ~/.terminfo xterm-custom.ti
export TERM=xterm-custom
```

## Testing Terminal Capabilities

### Color test script

```bash
#!/bin/bash
# Test 256 colors
for i in {0..255}; do
    printf "\e[38;5;${i}m%03d\e[0m " "$i"
    [ $((($i + 1) % 16)) -eq 0 ] && echo
done
```

### Attribute test

```bash
# Test various text attributes
tput bold; echo "Bold"; tput sgr0
tput dim; echo "Dim"; tput sgr0
tput smul; echo "Underline"; tput rmul
tput smso; echo "Standout"; tput rmso
tput sitm; echo "Italic"; tput ritm
```

### Alternate screen test

```bash
# Enter alternate screen
tput smcup
echo "This is in alternate screen buffer"
sleep 2
# Exit alternate screen
tput rmcup
echo "Back to main screen"
```

## Advanced Topics

### Terminfo Capability Types

1. **Boolean capabilities**: Simple flags (e.g., `am` = auto margins)
2. **Numeric capabilities**: Integer values (e.g., `colors#256`)
3. **String capabilities**: Escape sequences (e.g., `bold=\E[1m`)

### Parameter Substitution

String capabilities can use parameters:
- `%p1` - first parameter
- `%p2` - second parameter
- `%d` - output as decimal
- `%02d` - output as decimal, padded to 2 digits
- `%+` - add parameters
- `%'char'` - push character constant

Example: `cup=\E[%p1%d;%p2%dH` (move cursor)

### Delays and Padding

Some capabilities include padding information:
- `$<10>` - 10 millisecond delay
- `$<10*>` - 10ms times affected lines
- `$<10/>` - 10ms mandatory delay

Modern terminals usually ignore padding.

## Troubleshooting Workflow

1. **Verify TERM is set**: `echo $TERM`
2. **Check entry exists**: `infocmp $TERM`
3. **Test basic capabilities**: `tput colors`, `tput cols`
4. **Check locale**: `locale`
5. **Test rendering**: Run color/attribute tests
6. **Compare with working terminal**: `infocmp -d $TERM1 $TERM2`
7. **Try alternative TERM**: `TERM=xterm-256color bash`

## Resources

- `man terminfo` - Complete terminfo reference
- `man infocmp` - infocmp command details
- `man tic` - tic compiler documentation
- `man tput` - tput command reference
- `/usr/share/terminfo/` - Browse existing entries
