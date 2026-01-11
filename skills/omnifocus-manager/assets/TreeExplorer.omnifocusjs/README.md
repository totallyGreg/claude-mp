# Query-Simple Template

Simple plugin template for querying and displaying OmniFocus data.

## What This Template Provides

- Basic query structure using global variables (correct pattern)
- Alert display for showing results
- Error handling
- Validation function
- Comments showing common customization points

## Use This Template For

- Displaying filtered task lists
- Showing tasks by criteria (due today, flagged, by tag, etc.)
- Simple data queries with Alert display
- Learning correct OmniFocus plugin patterns

## Template Variables

- `TreeExplorer` - Display name for the plugin
- `com.totallytools.omnifocus.tree-explorer` - Reverse domain identifier (e.g., com.user.myplugin)
- `TotallyTools` - Plugin author name
- `Explore and export OmniFocus hierarchy as tree structures` - Plugin description
- `treeexplorer` - Action identifier (usually camelCase version of plugin name)
- `TreeExplorer` - Action label shown in menus
- `list.bullet` - SF Symbol icon name (e.g., list.bullet, flag, calendar)

## Customization Points

In `Resources/action.js`, customize these sections:

1. **Data Access** (line 11-12): Add more global variables as needed
   ```javascript
   const tags = flattenedTags;
   const folders = flattenedFolders;
   ```

2. **Query Logic** (line 14-15): Add your filtering/grouping logic
   ```javascript
   const flaggedTasks = tasks.filter(t => t.flagged && !t.completed);
   ```

3. **Display Format** (line 17-26): Format your output message
   ```javascript
   message += `Flagged: ${flaggedTasks.length}\n`;
   ```

## Example Usage

```bash
python3 scripts/generate_plugin.py \\
  --template query-simple \\
  --name "My Plugin" \\
  --identifier "com.mycompany.myplugin" \\
  --description "Shows my tasks"
```
