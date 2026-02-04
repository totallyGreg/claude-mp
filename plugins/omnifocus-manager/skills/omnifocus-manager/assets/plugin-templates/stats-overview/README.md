# Stats-Overview Template

Comprehensive statistics dashboard template for OmniFocus database overview.

## What This Template Provides

- Complete statistics counting for tasks, projects, folders, tags, inbox
- Status breakdowns (active, completed, dropped) with percentages
- Helper functions for formatting numbers and percentages
- Well-structured, readable output
- Production-ready code following OmniFocus best practices

## Use This Template For

- Database overview plugins
- Statistics dashboards
- Summary reports
- Understanding your OmniFocus database state
- Learning comprehensive data access patterns

## Features

- **Task Statistics**: Total, Active, Completed, Dropped with percentages
- **Project Statistics**: Total, Active, On Hold, Completed, Dropped with percentages
- **Organization**: Folder count, Tag count, Inbox count
- **Additional Stats**: Flagged count, Overdue count
- **Number Formatting**: Thousand separators for large numbers
- **Percentage Calculations**: Context-aware percentages

## Template Variables

- `{{PLUGIN_NAME}}` - Display name
- `{{IDENTIFIER}}` - Reverse domain identifier
- `{{AUTHOR}}` - Plugin author
- `{{DESCRIPTION}}` - Plugin description

## Customization Points

1. **Add More Statistics** (lines 67-69):
   ```javascript
   message += `  Due Today: ${formatNumber(stats.dueToday)}\n`;
   ```

2. **Add New Sections**:
   ```javascript
   message += 'ESTIMATES\n';
   message += `  Total Minutes: ${stats.totalMinutes}\n\n`;
   ```

3. **Change Display Format**: Modify `buildOverviewMessage()` function

## Example Usage

```bash
python3 scripts/generate_plugin.py \\
  --template stats-overview \\
  --name "Database Stats" \\
  --identifier "com.mycompany.dbstats"
```
