/**
 * Argument Parser for OmniFocus JXA CLI
 *
 * Parses command-line arguments for JXA scripts.
 *
 * Usage (load in JXA script):
 *   ObjC.import('Foundation');
 *   const argParser = eval($.NSString.alloc.initWithContentsOfFileEncodingError(
 *       'libraries/jxa/argParser.js', $.NSUTF8StringEncoding, null
 *   ).js);
 *
 *   function run(argv) {
 *       const args = argParser.parseArgs(argv);
 *       // ... use args
 *   }
 */

(() => {
    const argParser = {};

    /**
     * Parse command-line arguments
     * @param {Array<string>} argv - Command-line arguments
     * @returns {Object} Parsed arguments object
     */
    argParser.parseArgs = function(argv) {
        const args = {
            action: argv[0] || 'help'
        };

        for (let i = 1; i < argv.length; i++) {
            const arg = argv[i];

            if (arg.startsWith('--')) {
                const key = arg.substring(2);

                // Boolean flags
                if (key === 'flagged' || key === 'completed' || key === 'help') {
                    args[key] = true;
                } else {
                    // Value arguments
                    i++;
                    if (i < argv.length) {
                        args[key] = argv[i];
                    }
                }
            }
        }

        return args;
    };

    /**
     * Parse option value (for custom parsing)
     * @param {string} key - Option key
     * @param {string} value - Option value
     * @returns {*} Parsed value
     */
    argParser.parseOption = function(key, value) {
        // Handle special option types
        if (key === 'days' || key === 'estimate') {
            return parseInt(value);
        }

        if (key === 'flagged' || key === 'completed' || key === 'create-project' || key === 'create-tags') {
            return true;
        }

        return value;
    };

    /**
     * Print help information for OmniFocus CLI
     * @returns {string} Help text
     */
    argParser.printHelp = function() {
        const help = `
OmniFocus Task Manager (JXA)

Usage:
    osascript -l JavaScript omnifocus.js <action> [options]

Actions:
    Task Management:
      create     Create a new task
      update     Update an existing task
      complete   Mark a task as complete
      delete     Delete a task
      info       Get task information

    Query Tasks:
      list       List tasks with optional filters
      today      Show tasks due or deferred to today
      due-soon   Show tasks due within N days (default: 7)
      flagged    Show all flagged tasks
      search     Search for tasks by name or note

    Other:
      help       Show this help message

Common Options:
    --name <name>          Task name
    --id <id>              Task ID (persistent identifier)
    --note <note>          Task note/description
    --project <project>    Project name
    --tags <tags>          Comma-separated tag names
    --due <date>           Due date (ISO 8601: YYYY-MM-DD)
    --defer <date>         Defer/start date (ISO 8601: YYYY-MM-DD)
    --estimate <time>      Time estimate (e.g., 30m, 2h, 1h30m)
    --flagged              Flag the task (for create/update)

Create-specific Options:
    --create-project       Create project if it doesn't exist
    --create-tags          Create tags if they don't exist

Update-specific Options:
    --new-name <name>      New task name
    --due clear            Clear due date
    --defer clear          Clear defer date

Examples:
    # Create a simple task
    osascript -l JavaScript omnifocus.js create --name "Call dentist"

    # Create task with all options
    osascript -l JavaScript omnifocus.js create \\
        --name "Important meeting" \\
        --project "Work" \\
        --tags "urgent,meeting" \\
        --due "2025-12-25T14:00:00" \\
        --defer "2025-12-20" \\
        --estimate "1h30m" \\
        --note "Prepare slides and agenda" \\
        --flagged \\
        --create-project \\
        --create-tags

    # Update a task
    osascript -l JavaScript omnifocus.js update \\
        --name "Old task name" \\
        --new-name "New task name" \\
        --due "2025-12-30"

    # Complete a task
    osascript -l JavaScript omnifocus.js complete --name "Task to complete"

    # List today's tasks
    osascript -l JavaScript omnifocus.js today

    # Show tasks due soon
    osascript -l JavaScript omnifocus.js due-soon --days 7

Query Options:
    --filter <status>      Filter tasks: active, completed, dropped, all (for list)
    --days <N>             Number of days to look ahead (for due-soon, default: 7)
    --query <text>         Search term (for search)
`;

        return help;
    };

    return argParser;
})();
