#!/usr/bin/env bash
#
# Terminal Color Display Script
# Shows all available colors in your terminal
#

# Print script header
echo "════════════════════════════════════════════════════════════════"
echo "  Terminal Color Capability Display"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Display terminal info
echo "Terminal: $TERM"
echo "Colors supported: $(tput colors 2>/dev/null || echo 'unknown')"
echo ""

# Function to print colored text
print_color() {
    local code=$1
    local text=$2
    printf "\033[${code}m${text}\033[0m"
}

# Display 16 basic ANSI colors
echo "════════════════════════════════════════════════════════════════"
echo "  16 Basic ANSI Colors"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Standard colors:"
for code in {30..37}; do
    print_color "$code" "  ██  "
    printf " \033[${code}m%-6s\033[0m" "\\033[${code}m"
done
echo ""

echo ""
echo "Bright colors:"
for code in {90..97}; do
    print_color "$code" "  ██  "
    printf " \033[${code}m%-6s\033[0m" "\\033[${code}m"
done
echo ""

echo ""
echo "Background colors:"
for code in {40..47}; do
    print_color "$code" "  ██  "
    printf " %-6s" "\\033[${code}m"
done
echo ""

echo ""
echo "Bright backgrounds:"
for code in {100..107}; do
    print_color "$code" "  ██  "
    printf " %-6s" "\\033[${code}m"
done
echo ""
echo ""

# Display 256 colors
if [[ $(tput colors 2>/dev/null) -ge 256 ]]; then
    echo "════════════════════════════════════════════════════════════════"
    echo "  256 Color Palette"
    echo "════════════════════════════════════════════════════════════════"
    echo ""

    echo "System colors (0-15):"
    for i in {0..15}; do
        printf "\033[48;5;${i}m  %3s  \033[0m" "$i"
        if (( (i + 1) % 8 == 0 )); then
            echo ""
        fi
    done
    echo ""

    echo "Color cube (16-231):"
    echo "6x6x6 color cube (R-G-B):"
    for r in {0..5}; do
        for g in {0..5}; do
            for b in {0..5}; do
                color=$((16 + 36*r + 6*g + b))
                printf "\033[48;5;${color}m %3s \033[0m" "$color"
            done
            printf "  "
        done
        echo ""
    done
    echo ""

    echo "Grayscale ramp (232-255):"
    for i in {232..255}; do
        printf "\033[48;5;${i}m %3s \033[0m" "$i"
        if (( (i - 232 + 1) % 12 == 0 )); then
            echo ""
        fi
    done
    echo ""
fi

# Test true color (24-bit) support
echo "════════════════════════════════════════════════════════════════"
echo "  True Color (24-bit) Test"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "RGB gradient test:"
for r in {0..255..8}; do
    printf "\033[48;2;${r};0;0m \033[0m"
done
echo " Red gradient"

for g in {0..255..8}; do
    printf "\033[48;2;0;${g};0m \033[0m"
done
echo " Green gradient"

for b in {0..255..8}; do
    printf "\033[48;2;0;0;${b}m \033[0m"
done
echo " Blue gradient"

echo ""
echo "Rainbow spectrum:"
for i in {0..255..2}; do
    # Create rainbow using HSV to RGB conversion approximation
    if (( i < 43 )); then
        r=255; g=$((i * 6)); b=0
    elif (( i < 85 )); then
        r=$((255 - (i - 43) * 6)); g=255; b=0
    elif (( i < 128 )); then
        r=0; g=255; b=$(((i - 85) * 6))
    elif (( i < 170 )); then
        r=0; g=$((255 - (i - 128) * 6)); b=255
    elif (( i < 213 )); then
        r=$(((i - 170) * 6)); g=0; b=255
    else
        r=255; g=0; b=$((255 - (i - 213) * 6))
    fi
    printf "\033[48;2;${r};${g};${b}m \033[0m"
done
echo ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Text Style Attributes"
echo "════════════════════════════════════════════════════════════════"
echo ""

styles=(
    "0:Normal"
    "1:Bold"
    "2:Dim"
    "3:Italic"
    "4:Underline"
    "5:Blink"
    "7:Reverse"
    "8:Hidden"
    "9:Strikethrough"
)

for style in "${styles[@]}"; do
    code="${style%%:*}"
    name="${style##*:}"
    printf "\033[${code}m%-20s\033[0m \\033[${code}m\n" "$name"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Usage Examples"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Basic ANSI colors (16 colors):"
echo "  printf '\\033[31mRed text\\033[0m\\n'"
echo "  printf '\\033[1;34mBold blue\\033[0m\\n'"
echo ""

echo "256 colors (requires 256-color terminal):"
echo "  printf '\\033[38;5;196mBright red text\\033[0m\\n'"
echo "  printf '\\033[48;5;21mBlue background\\033[0m\\n'"
echo ""

echo "True color / 24-bit (requires true color support):"
echo "  printf '\\033[38;2;255;100;0mOrange text\\033[0m\\n'"
echo "  printf '\\033[48;2;0;100;200mCustom blue bg\\033[0m\\n'"
echo ""

echo "Combined attributes:"
echo "  printf '\\033[1;4;38;5;214mBold underline orange\\033[0m\\n'"
echo ""

echo "Reset to default:"
echo "  printf '\\033[0m' or use tput sgr0"
echo ""
