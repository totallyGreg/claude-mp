# Omnifocus Manager - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the omnifocus-manager skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2025-12-19 | Initial release |

## Completed Improvements

### v1.0.0 - Initial Release (2025-12-19)

**Initial Features:**

Comprehensive OmniFocus integration with hybrid approach:

1. **Database Queries (Python) - `scripts/query_omnifocus.py`**
   - Auto-detects OmniFocus 3 and 4 database locations
   - Read-only safe access to OmniFocus SQLite database
   - Multiple query types:
     - List tasks (with filtering: active/completed/dropped/all)
     - Search tasks by name or note
     - Tasks due soon (configurable days)
     - Today's tasks (due or deferred)
     - Flagged tasks
     - List projects (with folder filtering)
     - List tags with task counts
     - Custom SQL queries for advanced analysis
   - Output formats: human-readable and JSON
   - Full error handling and validation

2. **Task Management (JavaScript/JXA) - `scripts/manage_omnifocus.js`**
   - Direct access to OmniFocus AppleScript API
   - Complete CRUD operations:
     - **Create** tasks with full property support (name, note, project, tags, due date, defer date, estimate, flag)
     - **Update** existing tasks (modify any property, move between projects)
     - **Complete** tasks
     - **Delete** tasks
     - **Info** retrieval with full task details
   - Handles duplicate task names via ID-based operations
   - JSON output for all operations
   - Auto-creation of projects and tags (optional flags)
   - Proper date parsing (ISO 8601)
   - Time estimate parsing (30m, 2h, 1h30m formats)

3. **Reference Documentation - `references/omnifocus_url_scheme.md`**
   - Complete omnifocus:// URL scheme reference
   - All parameters and syntax documented
   - URL encoding guidelines
   - Date format specifications
   - Common patterns and examples
   - Troubleshooting guide
   - (Maintained for compatibility; JXA preferred for most use cases)

4. **Comprehensive Skill Documentation - `SKILL.md`**
   - Clear decision tree for choosing Python vs JXA
   - Detailed examples for all common use cases
   - Combined workflow examples (read + write operations)
   - Permission requirements documented
   - Important notes and limitations
   - Resource documentation

**Design Decisions:**

- **Hybrid approach:** Python for queries (powerful SQLite), JavaScript/JXA for modifications (full API access)
- **Read-only Python:** Ensures safe database access, no risk of corruption
- **Full JXA capabilities:** Enables operations impossible via URL scheme (update, delete, complete)
- **Auto-detection:** Both scripts auto-find OmniFocus installation
- **Flexible identification:** Support both name-based and ID-based task operations
- **JSON output:** Enables programmatic processing and integration with other tools

**Files Created:**
- `SKILL.md` - Comprehensive skill documentation with examples and workflows
- `scripts/query_omnifocus.py` - Database query tool (Python, 450+ lines)
- `scripts/manage_omnifocus.js` - Task management tool (JavaScript/JXA, 650+ lines)
- `references/omnifocus_url_scheme.md` - URL scheme reference documentation (550+ lines)
- `IMPROVEMENT_PLAN.md` - This improvement plan

## Planned Improvements

### High Priority

#### 1. Recurring Task Support
**Goal:** Enable creation and management of recurring tasks through JXA

**Current Limitation:**
- Cannot set repeat rules via URL scheme or current JXA script
- Users must manually configure recurrence in OmniFocus UI

**Proposed Solution:**
- Add `--repeat` parameter to `manage_omnifocus.js create` command
- Support common patterns: daily, weekly, monthly, yearly
- Allow custom repeat rules via OmniFocus repeat rule syntax
- Example: `--repeat "every Monday"` or `--repeat "daily"`

**Files to Modify:**
- `scripts/manage_omnifocus.js` - Add repetition rule handling

**Success Criteria:**
- Can create tasks with weekly, monthly, and custom repeat patterns
- Repeat rules persist correctly in OmniFocus

### Medium Priority

#### 2. Bulk Operations Support
**Goal:** Enable batch operations on multiple tasks at once

**Current Limitation:**
- Scripts operate on one task at a time
- No way to bulk complete, update, or tag tasks

**Proposed Solution:**
- Add batch mode to JXA script
- Accept JSON file with array of operations
- Example: Complete all tasks matching a criteria, bulk tag updates

**Example Usage:**
```bash
osascript -l JavaScript scripts/manage_omnifocus.js batch --operations operations.json
```

**Files to Modify:**
- `scripts/manage_omnifocus.js` - Add batch operation support

#### 3. Task Templates
**Goal:** Quick task creation from predefined templates

**Current Limitation:**
- No template system for frequently created task patterns

**Proposed Solution:**
- Add `assets/templates/` directory with JSON templates
- Template format includes all task properties
- New script or flag to create tasks from templates
- Example templates: weekly review, meeting prep, project kickoff

**Files to Create:**
- `assets/templates/` - Template directory
- Example templates: `weekly_review.json`, `meeting_prep.json`
- `scripts/create_from_template.js` - Template processor

#### 4. Report Generation
**Goal:** Generate formatted reports from OmniFocus data

**Current Limitation:**
- Query results are raw data, not formatted reports
- No built-in analytics or visualization

**Proposed Solution:**
- Add reporting script that generates markdown/HTML reports
- Report types:
  - Weekly summary (completed, overdue, upcoming)
  - Project status report
  - Tag analysis
  - Time estimates vs actual
- Output as markdown or HTML

**Files to Create:**
- `scripts/generate_report.py` - Report generation tool
- `assets/report_templates/` - Report templates

### Low Priority

#### 5. Integration with Calendar/Reminders
**Goal:** Sync OmniFocus tasks with macOS Calendar or Reminders

**Current Limitation:**
- No cross-app integration
- Duplicate entry required for calendar events that are also tasks

**Proposed Solution:**
- Script to export OmniFocus tasks to Calendar/Reminders
- Maintain sync state to avoid duplicates
- Bidirectional sync if feasible

**Challenges:**
- Sync state management complexity
- Handling conflicts
- May be better as separate tool

#### 6. Natural Language Date Parsing
**Goal:** Accept natural language dates instead of ISO 8601 only

**Current Limitation:**
- Requires strict ISO 8601 date format
- Users must format dates manually

**Proposed Solution:**
- Add date parser that accepts: "tomorrow", "next Monday", "in 3 days"
- Use JavaScript date libraries or Python `dateutil`
- Fallback to ISO 8601 if parsing fails

**Files to Modify:**
- `scripts/manage_omnifocus.js` - Add date parsing library/function

#### 7. Task Hierarchy Visualization
**Goal:** Visualize project and task hierarchies

**Current Limitation:**
- Query results are flat lists
- No visual representation of project structure

**Proposed Solution:**
- Add visualization script that outputs tree structure
- ASCII tree format or interactive HTML
- Show dependencies and relationships

**Files to Create:**
- `scripts/visualize_hierarchy.py` - Tree visualization tool

#### 8. Database Schema Documentation
**Goal:** Complete documentation of OmniFocus database schema

**Current Limitation:**
- Custom queries require trial-and-error to understand schema
- Key tables and relationships not fully documented

**Proposed Solution:**
- Create comprehensive schema reference
- Document all tables, columns, and relationships
- Include common query patterns
- Example queries for different use cases

**Files to Create:**
- `references/database_schema.md` - Complete schema documentation

## Enhancement Requests

*Track feature requests and suggestions from users here*

## Technical Debt

### Code Quality
- Add comprehensive error handling to edge cases in JXA script
- Add unit tests for Python query script (test with mock database)
- Add integration tests for JXA script (requires OmniFocus installation)
- Consider adding type hints to Python code for better maintainability
- Validate all user inputs more strictly in both scripts

### Documentation
- Add troubleshooting section to SKILL.md for common permission issues
- Create video or animated GIF demonstrating common workflows
- Document how to contribute custom templates or query patterns
- Add examples of integrating with other automation tools (Keyboard Maestro, Alfred, etc.)

## Contributing

To suggest improvements to this skill:

1. Add enhancement requests to the "Enhancement Requests" section
2. Discuss technical approaches in "Planned Improvements"
3. Track implementation progress
4. Update "Completed Improvements" when done

## Notes

- This improvement plan should be excluded from skill packaging (see .skillignore)
- Update version history when making significant changes
- Link to relevant issues/PRs in your repository if applicable
