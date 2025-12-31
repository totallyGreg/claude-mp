# Omnifocus Manager - Improvement Plan

## Overview

This document tracks improvements, enhancements, and future development plans for the omnifocus-manager skill.

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.3.6 | 2025-12-28 | Added PlugIn API reference with validation checklist and fixed AITaskAnalyzer manifest |
| 1.3.5 | 2025-12-28 | Added PlugIn.Library API reference for creating shared plugin modules |
| 1.3.4 | 2025-12-28 | Enhanced plugin documentation with .omnijs extension and consolidated references |
| 1.3.3 | 2025-12-28 | Added automation best practices reference from Omni Automation documentation |
| 1.3.2 | 2025-12-27 | Added comprehensive plugin bundle structure documentation |
| 1.3.1 | 2025-12-24 | Reorganized skill structure for AgentSkills compliance |
| 1.1.0 | 2025-12-21 | Major quality improvements, new references, and task templates |
| 1.0.0 | 2025-12-19 | Initial release |

## Completed Improvements

### v1.3.6 - PlugIn API Reference and Plugin Validation (2025-12-28)

**Problem Addressed:**
- AITaskAnalyzer.omnifocusjs plugin failing with errors due to invalid manifest identifier
- No comprehensive PlugIn class API documentation in skill references
- Missing plugin validation checklist for manifest and structure validation
- Unclear distinction between PlugIn API (PlugIn.find, PlugIn.Action) and OmniFocus API (Task, Project)
- No guidance on common plugin errors and troubleshooting

**Root Cause:**
- manifest.json had `"identifier": "Analyze Tasks"` which is INVALID (contains spaces, not reverse-domain notation)
- Valid identifiers must use reverse-domain format: "com.company.app.feature"
- Invalid identifier prevents plugin from registering/loading in OmniFocus

**Changes Made:**

1. **Fixed AITaskAnalyzer.omnifocusjs manifest.json:**
   - Changed `"identifier": "Analyze Tasks"` → `"identifier": "com.totallytools.omnifocus.ai-task-analyzer"`
   - Now follows required reverse-domain notation
   - Version remains 2.2.2 (user-modified)

2. **Added `references/plugin_api.md`:**
   - Complete PlugIn class documentation (PlugIn.find(), PlugIn.all)
   - PlugIn.Action and PlugIn.Library constructors and usage
   - Instance properties: identifier, version, actions, libraries, plugIn
   - Resource access methods: library(), resourceNamed()
   - Version class documentation
   - Complete manifest.json field specifications with validation rules
   - **Plugin Validation Checklist** (critical addition):
     - Manifest validation (identifier format, required fields, version format)
     - Structure validation (bundle directory, Resources/, file matching)
     - API usage validation (properties vs methods, common pitfalls)
     - Common properties reference (doc.flattenedTasks, task.name, etc.)
     - Common methods reference (task.markComplete(), doc.newInboxTask(), etc.)
   - Troubleshooting guide for 4 most common plugin errors:
     - "Plugin not found" → invalid identifier
     - "undefined is not an object" → property/method confusion
     - "Action file not found" → identifier mismatch
     - "Library not found" → missing PlugIn.Library return
   - Best practices for identifier naming, version management, action organization
   - Clear examples of valid vs invalid identifiers

3. **Updated SKILL.md:**
   - Added "Validating plugins?" decision tree entry (line 43)
   - Added "PlugIn class API?" decision tree entry (line 45)
   - Separated PlugIn API from JavaScript API for clarity
   - Added references section 3b with complete plugin_api.md documentation
   - Emphasized validation checklist availability

**Benefits:**
- AITaskAnalyzer plugin can now load correctly with valid identifier
- Clear validation checklist prevents common manifest errors
- Developers can validate plugins before distribution
- Distinction between PlugIn API (plugin infrastructure) and OmniFocus API (task/project manipulation)
- Troubleshooting guide reduces debugging time
- Best practices prevent identifier conflicts and version issues
- Comprehensive reference for all plugin-related development

**Source:** https://omni-automation.com/plugins/api.html

**Impact:**
This is a CRITICAL fix for the AITaskAnalyzer plugin and significantly improves the skill's ability to generate and validate plugins correctly.

### v1.3.5 - PlugIn.Library API Reference (2025-12-28)

**Problem Addressed:**
- No documentation for creating shared libraries within plugins
- Module reuse patterns not documented
- Library access methods unclear (from same plugin vs external plugins)
- Best practices for library creation not covered

**Changes Made:**

1. **Added `references/plugin_library_api.md`:**
   - Complete PlugIn.Library constructor and properties documentation
   - How to access libraries from actions and other plugins
   - Single-file and bundle library patterns
   - Best practices (info() function, IIFE pattern, versioning)
   - Common patterns (utilities, data collection, export libraries)
   - Troubleshooting guide for common library issues
   - Integration examples for AITaskAnalyzer plugin structure

2. **Updated SKILL.md:**
   - Added library reference to plugin decision tree (line 46)
   - Links to `plugin_library_api.md` for shared modules

**Benefits:**
- Enables proper creation of lib/taskMetrics.js and lib/exportUtils.js as PlugIn.Library instances
- Documents correct library call patterns (this.plugIn.library("name"))
- Provides reusable module architecture for plugin development
- Ensures correct library structure and exports

**Source:** https://omni-automation.com/plugins/library.html

### v1.3.4 - Plugin Documentation Enhancement (2025-12-28)

**Problem Addressed:**
- Generic `.omnijs` extension not documented (works across all Omni apps)
- Installation procedures incomplete compared to official omni-automation.com documentation
- Content duplication between `plugin_installation.md` and `omnifocus_plugin_structure.md`
- Uninstallation procedures not comprehensive
- Unclear separation between installing vs creating plugins

**Changes Made:**

1. **Enhanced `references/plugin_installation.md`:**
   - **NEW: Extension Types section**
     - Documents generic `.omnijs` extension (cross-app plugins)
     - Documents app-specific extensions (`.omnifocusjs`, `.omniplanjs`, etc.)
     - Explains when to use each type
     - Installation differences between generic and app-specific
   - **Expanded Installation Methods:**
     - macOS: Double-click, drag-to-Automation-Configuration, manual installation
     - iOS/iPadOS: Tap to install, Files app method, share sheet
     - Complete procedures for both `.omnijs` and `.omnifocusjs`
   - **NEW: Installation Dialog section**
     - Dialog components (name, description, storage options)
     - Storage location details (local vs iCloud)
   - **Enhanced Uninstallation:**
     - macOS: Via Automation Configuration (recommended), manual deletion
     - iOS/iPadOS: Swipe to delete (recommended), Files app method
     - Complete step-by-step procedures
   - **Streamlined Creating Plugins section:**
     - Removed duplicate content (templates, detailed creation steps)
     - Clear cross-reference to `omnifocus_plugin_structure.md` for development
     - Kept focus on installation and usage

2. **Streamlined `references/omnifocus_plugin_structure.md`:**
   - **Added clear statement at top:** "This is a development reference"
   - **NEW: Quick Navigation section** at top
     - Installing plugins? → See plugin_installation.md
     - Creating/modifying plugins? → Continue reading
     - Extension types? → See plugin_installation.md
   - **Updated Plugin Installation & Testing section:**
     - Clear cross-reference to plugin_installation.md
     - Simplified to focus on development/testing workflow
     - Removed duplicate installation procedures
   - **Enhanced Related Documentation:**
     - Clear separation: installation vs development
     - Better organization of API references

3. **Updated `SKILL.md`:**
   - **Enhanced Quick Decision Tree (#1):**
     - Clear distinction: Installing vs Creating plugins
     - Added `.omnijs` mention
     - Added quick tip: `open <path-to-plugin>` after creation
     - Better navigation to appropriate references
   - **Updated Reference Documentation section:**
     - Added `plugin_installation.md` as reference #9 with ⭐
     - Clear description of what it covers
     - "Use this for: Installing and using plugins"
     - Renumbered subsequent references (10, 11)
   - **Version bumped:** 1.3.3 → 1.3.4

**Source:**
- Guidance from https://omni-automation.com/plugins/installation.html
- Official Omni Automation documentation

**Impact:**
- Complete plugin installation coverage (all methods, all platforms)
- Generic `.omnijs` cross-app plugins now documented
- Clear separation of concerns: installation vs development
- No content duplication between references
- Better progressive disclosure (users find what they need faster)
- Claude will correctly distinguish between installing and creating plugins
- Comprehensive uninstallation procedures for users

**Quality Metrics:**
- Enhanced 2 reference documents (~150 lines added to plugin_installation.md)
- Updated SKILL.md decision tree and references
- Total documentation: 18 references (10,550+ lines)
- Progressive disclosure maintained
- Spec compliance: Maintained

### v1.3.3 - Automation Best Practices (2025-12-28)

**Problem Addressed:**
- Automation scripting best practices were scattered across multiple reference files
- Key patterns from official Omni Automation documentation weren't explicitly documented
- Users lacked a consolidated guide for writing efficient OmniFocus scripts
- Important distinctions (apply vs forEach, flattened collections, etc.) not prominently featured

**New Documentation:**

1. **`references/automation_best_practices.md`** (NEW)
   - Comprehensive 600+ line best practices reference
   - **Core Principles:**
     - Database-centric architecture pattern
     - Hierarchical traversal: apply() vs forEach() distinction
     - Flattened collections for efficient searching
     - Selection-based operations
     - Create-if-missing pattern (`itemNamed() || new Item()`)
     - Smart matching functions (tagsMatching, projectsMatching)
     - Positional insertion patterns
     - Data persistence pattern (always save after modifications)
     - Error handling best practices
     - Perspective management
   - **Advanced Patterns:**
     - Conditional task processing by status
     - Bulk operations on multiple items
     - Comprehensive hierarchical search with byName()
     - Performance optimization techniques
   - **Object Model:**
     - Containment hierarchy explained
     - Terminology alignment (Actions vs Tasks)
     - Context awareness patterns
   - **Script Organization:**
     - Immediate invocation pattern (IIFE)
     - Helper functions structure
     - Common script template
   - **Integration:**
     - Apple Intelligence integration overview
     - Reference to foundation_models_integration.md
   - Based on official Omni Automation documentation from omni-automation.com

2. **SKILL.md Updates:**
   - Added automation_best_practices.md as #1 primary reference (prominent position)
   - Renumbered all subsequent references (1-10)
   - Updated .omnifocusjs note to clarify it can be single file OR directory bundle
   - Updated version to 1.3.3

**Impact:**
- Claude will now reference consolidated best practices when writing automation scripts
- Users get clear guidance on efficient scripting patterns
- Key distinctions (apply vs forEach, flattened vs hierarchical) prominently documented
- Performance patterns emphasized (batch saves, use flattened collections)
- Common script template provides starting point for new automations
- All patterns sourced from official Omni Automation documentation

**Quality Metrics:**
- Added 1 new reference document (600+ lines)
- Updated SKILL.md with new reference ordering
- Total documentation: 17 references (10,865+ lines)
- Progressive disclosure maintained (new reference loaded only when needed)

### v1.3.2 - Plugin Bundle Documentation (2025-12-27)

**Problem Addressed:**
- Claude struggled to work with .omnifocusjs plugin bundles
- Tried to Read .omnifocusjs paths directly, failing because they're directories not files
- Lacked knowledge about bundle structure and how to navigate them
- No comprehensive documentation existed for manifest.json schema

**New Documentation:**

1. **`references/omnifocus_plugin_structure.md`** (NEW)
   - Comprehensive 700+ line reference document
   - **Bundle Fundamentals:**
     - Explains .omnifocusjs are directory bundles, not single files
     - Distinction between Finder behavior (appears as file) vs Terminal (is a directory)
     - Why Read tool fails on bundle paths
     - Correct patterns for reading files within bundles
   - **Complete Structure Documentation:**
     - Required vs optional files
     - Directory layout standards
     - Naming conventions and best practices
   - **manifest.json Complete Schema:**
     - All available fields documented
     - Required vs optional fields
     - Field descriptions and examples
     - Multiple example configurations (minimal, full-featured, multi-action)
   - **Working with Bundles:**
     - How to detect plugin bundles
     - Reading files from bundles (correct patterns)
     - Common Glob patterns for finding plugins
     - Common Grep patterns for searching within plugins
     - Exploring bundle contents with ls and Glob
   - **Creating Plugins:**
     - Step-by-step creation process
     - Adding multiple actions
     - Best practices for organization
     - Version management
   - **Action Script Structure:**
     - Complete templates
     - Plugin.Action wrapper pattern
     - Validation functions
     - Error handling patterns
     - Common API usage examples
   - **Installation & Testing:**
     - Installation locations on macOS
     - Testing procedures during development
     - Troubleshooting common issues
   - **Modifying Existing Plugins:**
     - Reading plugin contents
     - Making changes safely
     - Version update guidelines

2. **SKILL.md Updates:**
   - Added omnifocus_plugin_structure.md to primary references (position #2)
   - Added **CRITICAL** note that .omnifocusjs is a directory bundle
   - Updated decision tree with plugin creation/modification as first option
   - Added cross-references to all related documentation
   - Renumbered references section (now has 9 primary references)

3. **`references/plugin_installation.md` Updates:**
   - Added comprehensive "Understanding .omnifocusjs Bundles" section at beginning
   - Explains bundle vs file distinction
   - Shows correct vs incorrect approaches for reading bundles
   - Provides bundle structure overview
   - Documents how to navigate bundles in terminal
   - Added cross-reference to omnifocus_plugin_structure.md

4. **`references/omnifocus_automation.md` Updates:**
   - Added prominent cross-reference at Plug-In Development section
   - Notes that .omnifocusjs is a directory bundle
   - Updated "As Plug-Ins" section with reference
   - Links to omnifocus_plugin_structure.md for complete details

**Impact:**
- Claude will now correctly recognize .omnifocusjs as directory bundles
- Will use Read with full paths like `Plugin.omnifocusjs/manifest.json`
- Will use Bash ls or Glob to explore bundle contents
- Has complete templates and structure documentation
- Understands all available manifest.json fields
- Knows how to create, read, and modify plugin bundles correctly

**Quality Metrics:**
- Added 1 new reference document (700+ lines)
- Updated 3 existing documentation files
- Total documentation: 16 references (10,265 lines)
- Spec compliance: ✓ PASS (90/100)
- Overall score: 75/100 (maintained)

## Completed Improvements

### v1.1.0 - Quality Improvements (2025-12-21)

**Major Refactoring:**

1. **SKILL.md Restructuring**
   - Reduced from 654 lines to 312 lines (52% reduction)
   - Extracted detailed content to dedicated reference files
   - Improved conciseness score from 17/100 to estimated 70+/100
   - Added proper frontmatter metadata (version, author, license, compatibility)
   - Fixed spec compliance warnings (score improved from 65/100 to 100/100)

2. **New Reference Documentation**
   - **`references/jxa_commands.md`** - Complete JXA command reference
     - All query commands with examples
     - All task management commands
     - Output formats and error handling
     - 600+ lines of comprehensive command documentation

   - **`references/workflows.md`** - Common workflow patterns
     - Daily planning routines
     - Weekly/monthly review workflows
     - Project management patterns
     - Batch operations and automation examples
     - Integration patterns (Keyboard Maestro, Alfred, shell scripts)
     - 500+ lines of practical workflows

   - **`references/troubleshooting.md`** - Complete troubleshooting guide
     - Permission setup (step-by-step for all macOS versions)
     - Common errors and solutions
     - Performance optimization
     - Debugging techniques
     - Version compatibility notes
     - 400+ lines of troubleshooting content

   - **`references/applescript_api.md`** - AppleScript API documentation
     - Complete object model (Application, Document, Task, Project, Tag, Folder)
     - All properties and methods
     - Creating and querying objects
     - Best practices and common patterns
     - Comparison with Omni Automation
     - 600+ lines of API reference

   - **`references/database_schema.md`** - SQLite schema documentation
     - Complete table structures (Task, Tag, Folder, TaskTag)
     - Common query patterns
     - Analytics queries (completion rates, productivity metrics)
     - Advanced patterns (recursive queries, age distribution)
     - Best practices for database access
     - 600+ lines of schema documentation

   - **`references/gtd_methodology.md`** - GTD best practices
     - The five GTD steps (Capture, Clarify, Organize, Reflect, Engage)
     - GTD organization in OmniFocus (folders, projects, tags)
     - Review workflows (daily, weekly, monthly)
     - GTD horizons of focus
     - Automation templates for GTD workflows
     - Common pitfalls and solutions
     - 700+ lines of methodology guidance

3. **Task Templates System**
   - **`assets/templates/task_templates.json`** - 15 pre-built templates
     - Weekly/monthly review templates
     - Meeting preparation
     - Project kickoff and review
     - Inbox processing
     - Daily planning
     - Deep work sessions
     - Learning plans
     - Financial reviews
     - Health checkups
     - Variable substitution support ({{VARIABLE}} placeholders)

   - **`scripts/create_from_template.js`** - Template processor
     - JXA script to create tasks from templates
     - Variable substitution engine
     - Auto-create projects and tags
     - List available templates
     - Full error handling
     - 200+ lines of template processing logic

**Quality Metrics Improvements:**
- Conciseness: 17/100 → ~70+/100 (52% reduction in SKILL.md size)
- Spec Compliance: 65/100 → 100/100 (all frontmatter fields added)
- Progressive Disclosure: 100/100 (maintained, now with more references)
- Overall Score: 56/100 → ~80+/100 (estimated)

**Benefits:**
- SKILL.md is now lean and navigable
- Detailed content is discoverable but not loaded by default
- Better separation of concerns (commands vs workflows vs troubleshooting)
- Task templates enable quick, consistent task creation
- GTD guidance bridges automation with methodology
- Complete API and schema references enable advanced usage

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
