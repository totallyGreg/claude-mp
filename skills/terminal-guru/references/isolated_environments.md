# Isolated Test Environments Guide

## Overview

Isolated test environments allow testing and modifying zsh configurations without affecting the user's working shell. This guide explains how to create, use, and manage isolated shell environments using the ZDOTDIR mechanism.

## The ZDOTDIR Mechanism

### How It Works

Zsh uses the `ZDOTDIR` environment variable to determine where to look for startup files. By setting a custom ZDOTDIR, we can create completely isolated zsh instances.

**Standard zsh startup:**
```bash
# Looks in $HOME for:
~/.zshenv
~/.zprofile
~/.zshrc
~/.zlogin
```

**Isolated zsh startup:**
```bash
# Set custom ZDOTDIR
export ZDOTDIR=/path/to/test/environment

# Zsh now looks in ZDOTDIR:
/path/to/test/environment/.zshenv
/path/to/test/environment/.zprofile
/path/to/test/environment/.zshrc
/path/to/test/environment/.zlogin
```

### Benefits of Isolation

1. **Safety** - Changes don't affect your working shell configuration
2. **Repeatability** - Create consistent test environments on demand
3. **Comparison** - Test different configurations side-by-side
4. **Experimentation** - Try changes without risk
5. **Debugging** - Isolate problems without breaking your shell

## Creating Isolated Environments

### Using environment_builder.py

The easiest way to create isolated environments is using the built-in script:

```bash
# Create a new test environment
python3 scripts/environment_builder.py --create my-test

# Create from specific source
python3 scripts/environment_builder.py --create my-test --source /path/to/config

# List all test environments
python3 scripts/environment_builder.py --list

# Remove a test environment
python3 scripts/environment_builder.py --cleanup /path/to/env
```

### Manual Creation

To manually create an isolated environment:

```bash
# 1. Create directory structure
TEST_DIR="/tmp/zsh-test-$$"
mkdir -p "$TEST_DIR"

# 2. Copy user's config files
cp ~/.zshenv "$TEST_DIR/.zshenv" 2>/dev/null || true
cp ~/.zshrc "$TEST_DIR/.zshrc" 2>/dev/null || true
cp ~/.zprofile "$TEST_DIR/.zprofile" 2>/dev/null || true
cp ~/.zlogin "$TEST_DIR/.zlogin" 2>/dev/null || true

# 3. Copy functions directory if it exists
if [ -d ~/.zsh/functions ]; then
    mkdir -p "$TEST_DIR/functions"
    cp -r ~/.zsh/functions/* "$TEST_DIR/functions/"
fi

# 4. Launch isolated zsh
ZDOTDIR="$TEST_DIR" zsh

# Changes made in this shell only affect TEST_DIR
# User's real ~/.zshrc is untouched
```

## Using Isolated Environments

### Running Commands in Isolation

Execute commands without entering the shell:

```bash
# Run single command
ZDOTDIR=/path/to/test zsh -c "echo \$COLUMNS"

# Run command and exit
ZDOTDIR=/path/to/test zsh -i -c "source ~/.zshrc; some_command"

# Profile startup time
time ZDOTDIR=/path/to/test zsh -i -c exit
```

### Interactive Testing

Enter an interactive isolated shell:

```bash
# Launch isolated shell
ZDOTDIR=/path/to/test zsh

# Now you're in an isolated environment
# Any changes only affect $ZDOTDIR files
```

### Testing Configuration Changes

Safe workflow for testing changes:

```bash
# 1. Create test environment
python3 scripts/environment_builder.py --create config-test

# 2. Edit the isolated config
vim ~/.terminal-guru/test-environments/config-test-*/zdotdir/.zshrc

# 3. Test in isolation
ZDOTDIR=~/.terminal-guru/test-environments/config-test-*/zdotdir zsh

# 4. If it works, apply to real config
# If it doesn't work, just delete the test environment
```

## Directory Structure

The environment builder creates this structure:

```
~/.terminal-guru/test-environments/
└── test-20251120-143022/
    ├── zdotdir/                    # Isolated ZDOTDIR
    │   ├── .zshenv
    │   ├── .zshrc
    │   ├── .zprofile
    │   ├── .zlogin
    │   └── functions/
    ├── plugins/                    # Plugin copies
    │   ├── zsh-autosuggestions/
    │   └── zsh-syntax-highlighting/
    ├── logs/                       # Test execution logs
    │   ├── display_test.log
    │   ├── performance_test.log
    │   └── compatibility_test.log
    ├── results/                    # Test results (JSON)
    │   ├── display_results.json
    │   ├── performance_results.json
    │   └── compatibility_results.json
    ├── diffs/                      # Configuration diffs
    │   ├── iteration-1.diff
    │   └── iteration-2.diff
    └── metadata.json               # Environment metadata
```

## Common Use Cases

### Testing Plugin Changes

Test a new plugin without affecting your shell:

```bash
# Create environment
python3 scripts/environment_builder.py --create plugin-test

# Edit isolated .zshrc to add plugin
ZDOTDIR=~/.terminal-guru/test-environments/plugin-test-*/zdotdir
echo "source ~/.zsh/plugins/new-plugin/new-plugin.zsh" >> $ZDOTDIR/.zshrc

# Test it
ZDOTDIR=$ZDOTDIR zsh

# If it works, add to real ~/.zshrc
# If it breaks, just delete the test environment
```

### Comparing Configurations

Compare oh-my-zsh vs zinit:

```bash
# Test current config (oh-my-zsh)
python3 scripts/terminal_test_runner.py --name omz-baseline

# Create second environment for zinit
python3 scripts/environment_builder.py --create zinit-test

# Convert to zinit in isolated environment
# Edit ~/.terminal-guru/test-environments/zinit-test-*/zdotdir/.zshrc

# Run tests on both
python3 scripts/terminal_test_runner.py --name zinit-test

# Compare results
python3 scripts/terminal_test_runner.py --compare \
    ~/.terminal-guru/test-environments/omz-baseline-*/results/all_results.json \
    ~/.terminal-guru/test-environments/zinit-test-*/results/all_results.json
```

### Debugging Startup Issues

Isolate startup problems:

```bash
# Create clean environment
python3 scripts/environment_builder.py --create debug-startup

# Add debug output to isolated .zshrc
ZDOTDIR=~/.terminal-guru/test-environments/debug-startup-*/zdotdir
cat >> $ZDOTDIR/.zshrc << 'EOF'
# Enable debug output
zmodload zsh/zprof

# ... rest of config ...

# Show profiling at end
zprof
EOF

# Run and see where time is spent
ZDOTDIR=$ZDOTDIR zsh -i -c exit
```

### Testing Performance Optimizations

Before and after performance testing:

```bash
# Baseline
python3 scripts/terminal_test_runner.py --name baseline --suite performance

# Modify config in test environment
# Add lazy loading, defer plugins, etc.

# Test optimizations
python3 scripts/terminal_test_runner.py --name optimized --suite performance

# Compare
python3 scripts/terminal_test_runner.py --compare \
    baseline-results.json \
    optimized-results.json
```

## Environment Variables

### Important Variables for Isolation

When using ZDOTDIR, these variables affect behavior:

```bash
# Primary isolation variable
ZDOTDIR=/path/to/test/env

# Plugin paths may need adjustment
FPATH=/path/to/test/env/functions:$FPATH

# Plugin manager directories
ZSH=$ZDOTDIR/.oh-my-zsh        # oh-my-zsh
ZINIT_HOME=$ZDOTDIR/.zinit      # zinit
ANTIGEN_HOME=$ZDOTDIR/.antigen  # antigen
```

### Preserving User Environment

To test while preserving some user settings:

```bash
# Preserve PATH but isolate zsh config
env -i \
    HOME="$HOME" \
    PATH="$PATH" \
    TERM="$TERM" \
    ZDOTDIR="/path/to/test" \
    zsh
```

## Best Practices

### DO:
- ✓ Always use isolated environments for testing changes
- ✓ Create descriptive environment names
- ✓ Preserve environments for comparison
- ✓ Document changes in test environments
- ✓ Run tests before applying to real config

### DON'T:
- ✗ Test directly in production shell
- ✗ Reuse test environments for multiple purposes
- ✗ Forget to clean up old test environments
- ✗ Mix isolated and non-isolated testing
- ✗ Assume isolation is complete (some environment variables leak)

## Advanced Techniques

### Complete Isolation with Container-Like Behavior

For maximum isolation:

```bash
# Clear most environment variables
env -i \
    HOME="$HOME" \
    USER="$USER" \
    PATH="/usr/local/bin:/usr/bin:/bin" \
    TERM="xterm-256color" \
    LANG="en_US.UTF-8" \
    ZDOTDIR="/path/to/test" \
    SHELL="/bin/zsh" \
    zsh -d  # -d flag ignores global rc files
```

### Testing Multiple Versions

Test zsh updates before upgrading:

```bash
# Test with specific zsh binary
/usr/local/bin/zsh-5.9 \
    ZDOTDIR=/path/to/test \
    -i -c "echo \$ZSH_VERSION"

# Compare different versions
for zsh in /bin/zsh /usr/local/bin/zsh-5.9; do
    echo "Testing with: $zsh"
    ZDOTDIR=/path/to/test $zsh -i -c exit
done
```

### Automated Testing

Use in CI/CD or automated testing:

```bash
#!/bin/bash
# automated_zsh_test.sh

# Create isolated environment
python3 scripts/environment_builder.py --create ci-test

# Run tests
python3 scripts/terminal_test_runner.py --name ci-test --suite all

# Check exit code
if [ $? -eq 0 ]; then
    echo "Tests passed"
else
    echo "Tests failed"
    exit 1
fi

# Cleanup
python3 scripts/environment_builder.py --cleanup ci-test
```

## Troubleshooting

### Environment Not Truly Isolated

**Problem:** Changes still affect main shell

**Solution:** Check these variables:
```bash
# Verify ZDOTDIR is set
echo $ZDOTDIR

# Check which files are being sourced
zsh -x  # Trace execution

# Ensure .zshenv doesn't override
cat ~/.zshenv | grep ZDOTDIR
```

### Plugins Not Loading

**Problem:** Plugins fail in isolated environment

**Solution:** Copy plugin directories:
```bash
# Copy oh-my-zsh
cp -r ~/.oh-my-zsh $ZDOTDIR/.oh-my-zsh

# Or adjust ZSH variable
export ZSH=$ZDOTDIR/.oh-my-zsh
```

### Performance Differences

**Problem:** Isolated environment faster/slower than production

**Solution:** Check for missing/extra plugins:
```bash
# Compare loaded plugins
diff <(zsh -c 'echo $plugins') \
     <(ZDOTDIR=/path/to/test zsh -c 'echo $plugins')
```

## Related Tools

- `terminal_test_runner.py` - Automated testing in isolated environments
- `environment_builder.py` - Create and manage test environments
- `terminal_diagnostics.py` - Diagnose environment issues

## References

- Zsh Manual: [Startup/Shutdown Files](http://zsh.sourceforge.net/Doc/Release/Files.html)
- ZDOTDIR documentation in zsh(1)
- `zsh_configuration.md` - Comprehensive zsh configuration guide
