# OmniFocus Automation Troubleshooting

Complete troubleshooting guide for OmniFocus automation issues, permissions, and common problems.

## Permissions Setup

### Automation Permission (Required for JXA)

**First time running JXA scripts will prompt for automation permission.**

#### macOS Ventura and later:
1. Open **System Settings**
2. Go to **Privacy & Security**
3. Scroll to **Automation**
4. Find your terminal app (Terminal, iTerm2, etc.)
5. Enable **OmniFocus**

#### macOS Monterey and earlier:
1. Open **System Preferences**
2. Go to **Security & Privacy** → **Privacy**
3. Select **Automation** from the left sidebar
4. Find your terminal app
5. Check the box next to **OmniFocus**

**If you don't see Automation in the list:**
- Run a JXA command first to trigger the permission prompt
- The Automation category will appear after the first attempt

### Full Disk Access (Required for Python Database Queries)

**Only needed if using `query_omnifocus.py` for database access.**

#### macOS Ventura and later:
1. Open **System Settings**
2. Go to **Privacy & Security**
3. Scroll to **Full Disk Access**
4. Click the **+** button
5. Navigate to `/Applications/Utilities/Terminal.app` (or your terminal app)
6. Add it to the list

#### macOS Monterey and earlier:
1. Open **System Preferences**
2. Go to **Security & Privacy** → **Privacy**
3. Select **Full Disk Access** from the left sidebar
4. Click the lock icon to make changes
5. Click the **+** button
6. Add your terminal app

**Important:** You must completely quit and restart your terminal app after granting permissions.

```bash
# Quit Terminal completely
killall Terminal

# Or for iTerm2
killall iTerm2
```

## Common Issues

### JXA Script Issues

#### "execution error: Not authorized to send Apple events"

**Cause:** Missing automation permission for OmniFocus.

**Solution:**
1. Grant automation permission (see above)
2. Completely quit and restart Terminal
3. Try the command again

#### "Error: Application isn't running"

**Cause:** OmniFocus is not running.

**Solution:**
```bash
# Launch OmniFocus
open -a OmniFocus

# Wait a few seconds, then run your command
sleep 3
osascript -l JavaScript scripts/manage_omnifocus.js today
```

#### "Error: Can't get object"

**Cause:**
- Task/project/tag name doesn't exist
- Case-sensitivity mismatch
- Special characters in names

**Solution:**
```bash
# Verify exact name
osascript -l JavaScript scripts/manage_omnifocus.js list --filter all | \
  jq -r '.tasks[] | .name' | grep -i "partial-name"

# Use exact name with proper casing
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Exact Task Name" \
  --due "2025-12-31"
```

#### "Multiple tasks found" error

**Cause:** Multiple tasks have the same name.

**Solution:** Use task ID instead of name:

```bash
# Get task IDs
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Duplicate Name"

# Output shows all matches with IDs
{
  "success": false,
  "error": "Multiple tasks found",
  "tasks": [
    { "id": "abc123", "name": "Duplicate Name", "project": "Work" },
    { "id": "def456", "name": "Duplicate Name", "project": "Personal" }
  ]
}

# Use specific ID
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --id "abc123" \
  --due "2025-12-31"
```

### Python Database Query Issues

#### "Permission denied" when accessing database

**Cause:** Missing Full Disk Access permission.

**Solution:**
1. Grant Full Disk Access (see above)
2. Completely quit and restart Terminal
3. Verify permission is granted:

```bash
# Test database access
python3 scripts/query_omnifocus.py --list
```

#### "Database file not found"

**Cause:** Auto-detection failed to find OmniFocus database.

**Solution 1 - Verify OmniFocus version:**
```bash
# Check if OmniFocus is installed
ls -la ~/Library/Group\ Containers/*/com.omnigroup.OmniFocus/

# OmniFocus 3
ls -la ~/Library/Group\ Containers/34YW5XSRB7.com.omnigroup.OmniFocus3/

# OmniFocus 4
ls -la ~/Library/Group\ Containers/34YW5XSRB7.com.omnigroup.OmniFocus/
```

**Solution 2 - Manually specify database path:**
```bash
# Edit query_omnifocus.py and set DB_PATH directly
DB_PATH = "/Users/YOUR_USERNAME/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/Data/OmniFocus.ofocus/OmniFocus.sqlite"
```

#### "SQLite database is locked"

**Cause:** OmniFocus has the database open and locked.

**Solution:**
- The Python script uses read-only mode, so this shouldn't happen
- If it does, quit OmniFocus and try again
- Wait a few seconds for OmniFocus to release locks

### URL Scheme Issues

#### URL doesn't open in OmniFocus

**Cause:**
- Improper URL encoding
- OmniFocus not installed
- Invalid parameter

**Solution:**
```bash
# Test basic URL first
open "omnifocus:///add?name=Test"

# If that works, check URL encoding
# Spaces must be %20 or +
# & must be %26
# = must be %3D

# Use Python for proper encoding
python3 -c "import urllib.parse; print('omnifocus:///add?name=' + urllib.parse.quote('Test Task'))"
```

#### Task created but in wrong location

**Cause:**
- Project/folder name doesn't match exactly
- Case sensitivity issue

**Solution:**
```bash
# Verify exact project name
osascript -l JavaScript scripts/manage_omnifocus.js list --filter all | \
  jq -r '.tasks[].project' | sort -u

# Use exact name in URL
```

#### autosave=true not working

**Cause:** Parameter might not be supported in your OmniFocus version.

**Solution:**
- Test without autosave to see the preview dialog
- Update OmniFocus to latest version
- Use JXA for fully automated task creation instead

### Date and Time Issues

#### Dates in wrong timezone

**Cause:** ISO 8601 dates without timezone are interpreted in local time.

**Solution:**
```bash
# Include timezone explicitly
--due "2025-12-25T14:00:00-08:00"  # PST
--due "2025-12-25T14:00:00-05:00"  # EST

# Or use date only (no timezone issues)
--due "2025-12-25"
```

#### "Invalid date format" error

**Cause:** Date not in ISO 8601 format.

**Solution:**
```bash
# Correct formats
--due "2025-12-25"              # Date only
--due "2025-12-25T14:30:00"     # Date and time
--due "2025-12-25T14:30:00-08:00"  # With timezone

# Incorrect formats (will fail)
--due "12/25/2025"              # US format
--due "25-12-2025"              # European format
--due "Dec 25, 2025"            # Natural language
```

#### Task not appearing today even with today's date

**Cause:** Task might have a defer date in the future.

**Solution:**
```bash
# Check task details
osascript -l JavaScript scripts/manage_omnifocus.js info --name "Task Name"

# Update defer date if needed
osascript -l JavaScript scripts/manage_omnifocus.js update \
  --name "Task Name" \
  --defer "2025-12-21"  # Today
```

### Performance Issues

#### Script is very slow

**Cause:** Large OmniFocus database with thousands of tasks.

**Solution:**
```bash
# Use filters to reduce result set
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active

# Use search instead of listing all
osascript -l JavaScript scripts/manage_omnifocus.js search --query "specific-term"

# For database queries, add WHERE clauses
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT * FROM Task WHERE dateDue IS NOT NULL LIMIT 100"
```

#### Database query returns too many results

**Cause:** No filtering in query.

**Solution:**
```bash
# Limit results
python3 scripts/query_omnifocus.py --list --json | jq '.tasks[:10]'

# Or add LIMIT in custom query
python3 scripts/query_omnifocus.py --custom-query \
  "SELECT * FROM Task WHERE dateCompleted IS NULL LIMIT 50"
```

## Debugging

### Enable verbose output

**For JXA scripts:**
```bash
# Add console.log statements in the script
# Output will appear in Console.app

# Or redirect to file
osascript -l JavaScript scripts/manage_omnifocus.js today 2>&1 | tee output.log
```

**For Python scripts:**
```bash
# Add print statements
# Or use Python debugger
python3 -m pdb scripts/query_omnifocus.py --list
```

### Check JSON output

```bash
# Verify JSON is valid
osascript -l JavaScript scripts/manage_omnifocus.js today | jq .

# Pretty print
osascript -l JavaScript scripts/manage_omnifocus.js today | jq '.'

# Check for errors
osascript -l JavaScript scripts/manage_omnifocus.js today | jq '.success'
```

### Test minimal command first

```bash
# Start with simplest command
osascript -l JavaScript scripts/manage_omnifocus.js help

# Then try basic query
osascript -l JavaScript scripts/manage_omnifocus.js list --filter active

# Then try creation
osascript -l JavaScript scripts/manage_omnifocus.js create --name "Test"
```

## Version Compatibility

### OmniFocus 3 vs OmniFocus 4

**Both versions are supported, but database paths differ:**

- **OmniFocus 3:** `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus3/`
- **OmniFocus 4:** `~/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/`

**Scripts auto-detect version:**
- JXA: Works with both (uses AppleScript API)
- Python: Auto-detects database location
- URL Scheme: Works with both

**If you have both versions installed:**
- Scripts will use OmniFocus 4 by default
- To force OmniFocus 3, modify the script's database path

### macOS Version Compatibility

- **macOS 10.15 (Catalina) and later:** Full support
- **macOS 10.14 (Mojave) and earlier:** May have permission dialog differences

### Terminal App Compatibility

- **Terminal.app:** Full support
- **iTerm2:** Full support
- **Other terminals:** Should work, grant permissions as needed

## Getting Help

### Built-in Help

```bash
# JXA help
osascript -l JavaScript scripts/manage_omnifocus.js help

# Python help
python3 scripts/query_omnifocus.py --help
```

### Check OmniFocus Logs

1. Open **Console.app**
2. Filter for "OmniFocus"
3. Run your command
4. Check for error messages

### Verify OmniFocus is working

```bash
# Can you open OmniFocus normally?
open -a OmniFocus

# Can you create tasks in the UI?
# Try manually creating a task to verify OmniFocus itself is working
```

### Reset Permissions

If all else fails, reset permissions:

1. Remove your terminal from automation permissions
2. Remove from Full Disk Access
3. Restart your Mac
4. Run commands again to trigger fresh permission prompts

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Not authorized to send Apple events" | Missing automation permission | Grant automation permission, restart terminal |
| "Application isn't running" | OmniFocus not open | Launch OmniFocus first |
| "Can't get object" | Invalid name/ID | Verify exact name, check case sensitivity |
| "Multiple tasks found" | Duplicate names | Use task ID instead of name |
| "Permission denied" | Missing Full Disk Access | Grant Full Disk Access for database queries |
| "Database file not found" | Wrong database path | Check OmniFocus version, verify path |
| "Invalid date format" | Non-ISO date | Use YYYY-MM-DD format |
| "execution error" | Various JXA issues | Check Console.app for details |

## Still Having Issues?

1. **Check OmniFocus version:** Ensure you're running OmniFocus 3 or 4
2. **Update macOS:** Some features require recent macOS versions
3. **Check script version:** Ensure you have the latest version of the scripts
4. **Simplify:** Remove optional parameters and test with minimal command
5. **Review permissions:** Double-check both automation and Full Disk Access
6. **Test manually:** Try the operation in OmniFocus UI to verify it's possible
7. **Check logs:** Console.app often has helpful error messages
