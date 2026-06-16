#!/usr/bin/env node
/**
 * ofo-cli.ts — OmniFocus CLI via plugin library + omnijs-run URL.
 *
 * Replaces the bash+python3 ofo wrapper. Parses arguments, constructs
 * the omnijs-run URL with the stable stub script, and polls pasteboard
 * for the JSON result.
 */

import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import type { OfoAction } from './ofo-types.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const VERSION = '2.0.0';

// --- Helpers ---

function die(message: string): never {
  process.stderr.write(JSON.stringify({ success: false, error: message }) + '\n');
  process.exit(1);
}

function checkOmniFocus(): void {
  try {
    execSync('pgrep -x OmniFocus', { stdio: 'ignore' });
  } catch {
    die('OmniFocus is not running');
  }
}

function parseOmniFocusUrl(input: string): string {
  if (input.startsWith('omnifocus:///')) {
    const path = input.slice('omnifocus:///'.length);
    const slashIndex = path.indexOf('/');
    return slashIndex >= 0 ? path.slice(slashIndex + 1) : path;
  }
  return input;
}

function detectTypeFromUrl(input: string): string {
  if (input.startsWith('omnifocus:///project/')) return 'project';
  if (input.startsWith('omnifocus:///tag/')) return 'tag';
  return 'task';
}

function urlEncode(text: string): string {
  return encodeURIComponent(text);
}

function pbcopy(text: string): void {
  execSync('pbcopy', { input: text, stdio: ['pipe', 'ignore', 'ignore'] });
}

function pbpaste(): string {
  return execSync('pbpaste', { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'ignore'] });
}

function runAction(action: OfoAction, args: Record<string, unknown>): void {
  const stubPath = join(__dirname, 'ofo-stub.js');
  let stub: string;
  try {
    stub = readFileSync(stubPath, 'utf-8');
  } catch {
    die('Stub script not found: ' + stubPath);
  }

  const argJson = JSON.stringify({ action, ...args });
  const encodedScript = urlEncode(stub);
  const encodedArg = urlEncode(argJson);

  // Set sentinel so we can detect when OmniFocus writes the result
  pbcopy('__ofo_pending__');

  execSync(`open "omnifocus://localhost/omnijs-run?script=${encodedScript}&arg=${encodedArg}"`, {
    stdio: 'ignore'
  });

  // Poll until pasteboard changes from sentinel
  const maxAttempts = 50; // 50 * 0.2s = 10 second timeout
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    execSync('sleep 0.2');
    const result = pbpaste();
    if (result !== '__ofo_pending__') {
      process.stdout.write(result);
      return;
    }
  }

  process.stdout.write('{"success":false,"error":"Timeout waiting for OmniFocus response. Is external script execution enabled?"}');
  process.exit(1);
}

// --- Commands ---

function cmdInfo(args: string[]): void {
  if (args.length < 1) die('Usage: ofo info <id|omnifocus-url>');
  const id = parseOmniFocusUrl(args[0]!);
  const type = detectTypeFromUrl(args[0]!);
  runAction('ofo-info', { id, type });
}

function cmdComplete(args: string[]): void {
  if (args.length < 1) die('Usage: ofo complete <id|omnifocus-url>');
  const id = parseOmniFocusUrl(args[0]!);
  runAction('ofo-complete', { id });
}

function cmdDrop(args: string[]): void {
  if (args.length < 1) die('Usage: ofo drop <id|omnifocus-url> [--all]');
  const id = parseOmniFocusUrl(args[0]!);
  let allOccurrences = false;
  for (let i = 1; i < args.length; i++) {
    if (args[i] === '--all') allOccurrences = true;
  }
  runAction('ofo-drop', { id, allOccurrences });
}

// --- Stdin Helpers ---

function readStdin(): string | null {
  if (process.stdin.isTTY) return null;
  try {
    const data = readFileSync(0, 'utf-8').trim();
    return data || null;
  } catch {
    return null;
  }
}

function parseStdinInput(raw: string): Record<string, unknown> | Record<string, unknown>[] {
  // Try JSON first
  try {
    return JSON.parse(raw);
  } catch {
    // Plain text: first line = name, rest = note
    const lines = raw.split('\n');
    const name = lines[0]!.trim();
    const note = lines.slice(1).join('\n').trim();
    if (!name) die('No input received from stdin');
    const result: Record<string, unknown> = { name };
    if (note) result.note = note;
    return result;
  }
}

function cmdCreate(args: string[]): void {
  // Parse CLI flags
  let name = '', project = '', note = '', due = '', defer_ = '', tags = '', estimate = '', plannedDate = '';
  let flagged = false;

  let i = 0;
  while (i < args.length) {
    switch (args[i]) {
      case '--name':    name = args[++i] || ''; break;
      case '--project': project = args[++i] || ''; break;
      case '--note':    note = args[++i] || ''; break;
      case '--due':     due = args[++i] || ''; break;
      case '--defer':   defer_ = args[++i] || ''; break;
      case '--tags':    tags = args[++i] || ''; break;
      case '--flagged': flagged = true; break;
      case '--estimate': estimate = args[++i] || ''; break;
      case '--planned-date': plannedDate = args[++i] || ''; break;
      default: die('Unknown option: ' + args[i]);
    }
    i++;
  }

  // Check for stdin input
  const stdinData = readStdin();

  if (stdinData) {
    const parsed = parseStdinInput(stdinData);

    // JSON array: batch create
    if (Array.isArray(parsed)) {
      // Merge CLI flags into each item
      const items = parsed.map(item => {
        const merged = { ...item };
        if (project && !merged.project) merged.project = project;
        if (tags && !merged.tags) merged.tags = tags.split(',').map(t => t.trim());
        if (due && !merged.due) merged.due = due;
        if (defer_ && !merged.defer) merged.defer = defer_;
        if (flagged && !merged.flagged) merged.flagged = true;
        if (estimate && !merged.estimate) merged.estimate = parseInt(estimate, 10);
        if (plannedDate && !merged.plannedDate) merged.plannedDate = plannedDate;
        return merged;
      });
      runAction('ofo-create-batch', { items });
      return;
    }

    // JSON object or plain text: single task
    const stdinObj = parsed as Record<string, unknown>;

    // --name overrides stdin name; stdin text becomes note
    if (name) {
      if (!stdinObj.note && stdinObj.name) {
        stdinObj.note = stdinObj.name;
      }
      stdinObj.name = name;
    }

    // CLI flags override stdin fields
    if (project) stdinObj.project = project;
    if (note) stdinObj.note = note;
    if (due) stdinObj.due = due;
    if (defer_) stdinObj.defer = defer_;
    if (flagged) stdinObj.flagged = true;
    if (estimate) stdinObj.estimate = parseInt(estimate, 10);
    if (plannedDate) stdinObj.plannedDate = plannedDate;
    if (tags) stdinObj.tags = tags.split(',').map(t => t.trim());

    runAction('ofo-create', stdinObj);
    return;
  }

  // No stdin: require --name
  if (!name) die('Usage: ofo create --name "Task name" [--project P] [--tags t1,t2] [--due YYYY-MM-DD]');

  const argObj: Record<string, unknown> = { name };
  if (project) argObj.project = project;
  if (note) argObj.note = note;
  if (due) argObj.due = due;
  if (defer_) argObj.defer = defer_;
  if (estimate) argObj.estimate = parseInt(estimate, 10);
  if (plannedDate) argObj.plannedDate = plannedDate;
  if (flagged) argObj.flagged = true;
  if (tags) argObj.tags = tags.split(',').map(t => t.trim());

  runAction('ofo-create', argObj);
}

function cmdUpdate(args: string[]): void {
  if (args.length < 1) die('Usage: ofo update <id> [--name N] [--due D] [--flagged] [--tags t1,t2] [--project P]');
  const id = parseOmniFocusUrl(args[0]!);

  const argObj: Record<string, unknown> = { id };
  let i = 1;
  while (i < args.length) {
    switch (args[i]) {
      case '--name':     argObj.name = args[++i] || ''; break;
      case '--note':        argObj.note = args[++i] || ''; break;
      case '--note-append': argObj.noteAppend = args[++i] || ''; break;
      case '--due': {
        const val = args[++i] || '';
        argObj.due = val === 'clear' ? null : val;
        break;
      }
      case '--defer': {
        const val = args[++i] || '';
        argObj.defer = val === 'clear' ? null : val;
        break;
      }
      case '--tags':     argObj.tags = (args[++i] || '').split(',').map(t => t.trim()); break;
      case '--flagged':  argObj.flagged = true; break;
      case '--estimate': argObj.estimate = parseInt(args[++i] || '0', 10); break;
      case '--project': argObj.project = args[++i] || ''; break;
      case '--planned-date': {
        const val = args[++i] || '';
        argObj.plannedDate = val === 'clear' ? null : val;
        break;
      }
      default: die('Unknown option: ' + args[i]);
    }
    i++;
  }

  runAction('ofo-update', argObj);
}

function cmdSearch(args: string[]): void {
  if (args.length < 1) die('Usage: ofo search <query>');
  const query = args.join(' ');
  runAction('ofo-search', { query });
}

function cmdList(args: string[]): void {
  const filter = args[0] || 'inbox';
  if (!['inbox', 'flagged', 'today', 'overdue', 'due-soon', 'waiting-for', 'someday-maybe'].includes(filter)) {
    die('Unknown filter: ' + filter + '. Use: inbox, flagged, today, overdue, due-soon [N], waiting-for, someday-maybe');
  }
  if (filter === 'due-soon') {
    const days = args[1] ? parseInt(args[1], 10) : 7;
    if (isNaN(days) || days < 1) die('due-soon requires a positive number of days (e.g. ofo list due-soon 3)');
    runAction('ofo-list', { filter, days });
    return;
  }
  // D6.3 + D7.5 — waiting-for and someday-maybe need conventions from explicit flag → System Map
  if (filter === 'waiting-for') {
    let tag: string | null = null;
    let ageThresholdDays = 0;
    for (let i = 1; i < args.length; i++) {
      if (args[i] === '--tag') tag = args[++i] || null;
      else if (args[i] === '--days') ageThresholdDays = parseInt(args[++i] || '0', 10);
    }
    if (!tag) {
      tag = resolveSystemMapConvention('waitingTag');
      if (!tag) die('No --tag provided and SystemMap.conventions.waitingTag is not set. Run: ofo system-map --refresh');
    }
    runAction('ofo-list-waiting-for', { tag, ageThresholdDays });
    return;
  }
  if (filter === 'someday-maybe') {
    let tag: string | null = null;
    let folder: string | null = null;
    for (let i = 1; i < args.length; i++) {
      if (args[i] === '--tag') tag = args[++i] || null;
      else if (args[i] === '--folder') folder = args[++i] || null;
    }
    if (!tag && !folder) {
      tag = resolveSystemMapConvention('somedayTag');
      folder = resolveSystemMapConvention('somedayFolder');
      if (!tag && !folder) die('No --tag or --folder provided and SystemMap.conventions.{somedayTag, somedayFolder} are not set. Run: ofo system-map --refresh');
    }
    const payload: Record<string, unknown> = {};
    if (tag) payload['tag'] = tag;
    if (folder) payload['folder'] = folder;
    runAction('ofo-list-someday-maybe', payload);
    return;
  }
  runAction('ofo-list', { filter });
}

/**
 * D7.5 — read a convention field from the cached System Map task note.
 * Returns null on missing/corrupt map or missing field; caller decides error UX.
 */
function resolveSystemMapConvention(field: string): string | null {
  const script = `(() => {
  const tasks = flattenedTasks.filter(t => t.name === ${JSON.stringify(SYSTEM_MAP_TASK_NAME)});
  if (tasks.length === 0) { Pasteboard.general.string = JSON.stringify({success:false, error:"missing"}); return; }
  Pasteboard.general.string = JSON.stringify({success:true, note: tasks[0].note || "{}"});
})()`;
  const raw = runInlineScript(script);
  try {
    const wrap = JSON.parse(raw);
    if (!wrap.success) return null;
    const map = JSON.parse(wrap.note);
    return map.conventions?.[field] ?? null;
  } catch {
    return null;
  }
}

function cmdPerspective(args: string[]): void {
  if (args.length < 1) die('Usage: ofo perspective <name> [--id ID]');

  if (args[0] === '--id') {
    runAction('ofo-perspective', { id: args[1] || '' });
  } else {
    runAction('ofo-perspective', { name: args.join(' ') });
  }
}

function cmdPerspectiveRules(args: string[]): void {
  const name = args.join(' ') || null;
  runAction('ofo-perspective-rules', name ? { name } : {});
}

// --- Tag Commands ---

const CAPTURE_MAP: Record<string, string> = {
  question:    'Question❓',
  discontent:  'Discontent⁉️',
  decide:      'Decide😤',
  routine:     'Routine🔁',
  evening:     'Evening🕕',
};

function cmdTag(args: string[]): void {
  if (args.length < 1) die('Usage: ofo tag <id> --add "Tag" --remove "Tag" --capture <shortcut>');
  const id = parseOmniFocusUrl(args[0]!);

  const addTags: string[] = [];
  const removeTags: string[] = [];
  let i = 1;
  while (i < args.length) {
    switch (args[i]) {
      case '--add':     addTags.push(args[++i] || ''); break;
      case '--remove':  removeTags.push(args[++i] || ''); break;
      case '--capture': {
        const shortcut = (args[++i] || '').toLowerCase();
        const mapped = CAPTURE_MAP[shortcut];
        if (!mapped) die(`Unknown capture shortcut: ${shortcut}. Available: ${Object.keys(CAPTURE_MAP).join(', ')}`);
        addTags.push(mapped);
        break;
      }
      default: die('Unknown option: ' + args[i]);
    }
    i++;
  }

  if (addTags.length === 0 && removeTags.length === 0) {
    die('At least one --add, --remove, or --capture flag is required');
  }

  runAction('ofo-tag', { id, add: addTags, remove: removeTags });
}

function cmdPerspectiveConfigure(args: string[]): void {
  let name = '', id = '', rules = '', aggregation = '';

  let i = 0;
  while (i < args.length) {
    switch (args[i]) {
      case '--name': name = args[++i] || ''; break;
      case '--id':   id = args[++i] || ''; break;
      case '--rules': rules = args[++i] || ''; break;
      case '--aggregation': aggregation = args[++i] || ''; break;
      default: die('Unknown option: ' + args[i]);
    }
    i++;
  }

  if (!name && !id) die('Usage: ofo perspective-configure --name "Name" --rules \'[...]\'');
  if (!rules && !aggregation) die('At least one of --rules or --aggregation is required');

  const argObj: Record<string, unknown> = {};
  if (name) argObj.name = name;
  if (id) argObj.id = id;
  if (rules) {
    try {
      argObj.rules = JSON.parse(rules);
    } catch {
      die('Invalid JSON for --rules: ' + rules);
    }
  }
  if (aggregation) argObj.aggregation = aggregation;

  runAction('ofo-perspective-configure', argObj);
}

function cmdCompletedToday(args: string[]): void {
  let markdown = false;
  for (const arg of args) {
    if (arg === '--markdown') markdown = true;
    else die('Unknown option: ' + arg);
  }

  // Use a synchronous approach: call runAction which writes to stdout,
  // but we need to intercept the result for post-processing.
  // Override stdout to capture the perspective result.
  const perspectiveName = 'Completed Today';
  const stubPath = join(__dirname, 'ofo-stub.js');
  let stub: string;
  try {
    stub = readFileSync(stubPath, 'utf-8');
  } catch {
    die('Stub script not found: ' + stubPath);
  }

  const argJson = JSON.stringify({ action: 'ofo-perspective', name: perspectiveName });
  const encodedScript = urlEncode(stub);
  const encodedArg = urlEncode(argJson);

  pbcopy('__ofo_pending__');

  execSync(`open "omnifocus://localhost/omnijs-run?script=${encodedScript}&arg=${encodedArg}"`, {
    stdio: 'ignore'
  });

  const maxAttempts = 50;
  let rawResult = '';
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    execSync('sleep 0.2');
    const result = pbpaste();
    if (result !== '__ofo_pending__') {
      rawResult = result;
      break;
    }
  }

  if (!rawResult) {
    process.stdout.write('{"success":false,"error":"Timeout waiting for OmniFocus response"}');
    process.exit(1);
  }

  let data: any;
  try {
    data = JSON.parse(rawResult);
  } catch {
    process.stdout.write(rawResult);
    return;
  }

  if (!data.success) {
    process.stdout.write(rawResult);
    return;
  }

  const items: any[] = data.items || [];

  // Filter out Routine🔁 tagged tasks
  const filtered = items.filter((t: any) =>
    !t.tags || !t.tags.includes('Routine🔁')
  );

  // Categorize by capture tags
  const questions: any[] = [];
  const discontents: any[] = [];
  const decisions: any[] = [];
  const tasks: any[] = [];

  for (const t of filtered) {
    const tagList: string[] = t.tags || [];
    if (tagList.includes('Question❓')) questions.push(t);
    else if (tagList.includes('Discontent⁉️')) discontents.push(t);
    else if (tagList.includes('Decide😤')) decisions.push(t);
    else tasks.push(t);
  }

  if (markdown) {
    const lines: string[] = [];

    if (filtered.length === 0) {
      lines.push('No completions logged today.');
    } else {
      lines.push('## Completed Today');
      lines.push('');

      if (tasks.length > 0) {
        lines.push('### Tasks');
        for (const t of tasks) {
          const proj = t.project ? ` (${t.project})` : '';
          lines.push(`- ${t.name}${proj}`);
        }
        lines.push('');
      }

      if (questions.length > 0) {
        lines.push('### Questions Answered');
        for (const t of questions) {
          const proj = t.project ? ` (${t.project})` : '';
          lines.push(`- ${t.name}${proj}`);
        }
        lines.push('');
      }

      if (discontents.length > 0) {
        lines.push('### Discontents Resolved');
        for (const t of discontents) {
          const proj = t.project ? ` (${t.project})` : '';
          lines.push(`- ${t.name}${proj}`);
        }
        lines.push('');
      }

      if (decisions.length > 0) {
        lines.push('### Decisions Made');
        for (const t of decisions) {
          const proj = t.project ? ` (${t.project})` : '';
          lines.push(`- ${t.name}${proj}`);
        }
        lines.push('');
      }
    }

    process.stdout.write(lines.join('\n'));
  } else {
    process.stdout.write(JSON.stringify({
      success: true,
      date: new Date().toISOString().slice(0, 10),
      totalCompleted: filtered.length,
      tasks,
      questions,
      discontents,
      decisions
    }));
  }
}

function cmdTags(): void {
  runAction('ofo-tags', {});
}

function cmdDump(): void {
  runAction('ofo-dump', {});
}

function cmdStats(): void {
  runAction('ofo-stats', {});
}

function cmdClarity(args: string[]): void {
  let limit = '10';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--limit') limit = args[++i] || '10';
  }
  runAction('ofo-clarity', { limit });
}

function cmdStalled(args: string[]): void {
  let days = '14';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--days') days = args[++i] || '14';
  }
  runAction('ofo-stalled', { days });
}

function cmdHealth(): void {
  runAction('ofo-health', {});
}

function cmdHelp(): void {
  process.stdout.write(`ofo -- OmniFocus CLI via plugin library

Usage: ofo <command> [arguments]

Commands:
  info <id|url>                     Get task or project details as JSON
  complete <id|url>                 Mark a task as complete
  drop <id|url> [--all]            Drop single occurrence (--all stops repeating)
  create --name "..." [options]     Create a new task (also accepts stdin)
  update <id|url> [options]         Update task properties
  search <query>                    Search tasks by name or note
  list <filter>                     List tasks by filter
  tag <id|url> [options]            Add/remove tags on a task
  tags                              List all tags as JSON hierarchy
  perspective <name> [--id ID]      Query a custom perspective
  perspective-configure [options]   Set filter rules on a perspective
  completed-today [--markdown]      Today's completions categorized by tag
  dump                              Full database snapshot (active tasks, projects, perspectives) as JSON
  stats                             Counts: inbox, flagged, overdue, projects, tasks, reviewOverdue, plannedToday, withEstimate
  clarity [--limit N]               Tasks with lowest clarity score (no estimate/tags/project); default limit 10
  stalled [--days N]                Active projects with no available next action or not modified in N days (default 14)
  health                            System health: inbox, overdue (with Catch Up metadata), flagged — single call
  completed --since <date> [--by-tag]   Tasks completed since date; optional grouping by tag (gtd-coach "what did you accomplish?")
  folders [--with-projects]         Folder hierarchy as tree; optionally include projects under each folder
  projects neglected [--days N]     Active projects not modified in N days (default 30)
  projects review [--before <ISO>]  Active/onHold projects whose nextReviewDate ≤ before date (default now)
  project review <id> [--date <ISO>]    Mark project as reviewed (sets lastReviewDate; advances nextReviewDate)
  project create --name "..." [--folder NAME] [--sequential|--parallel] [--note] [--due] [--defer] [--review-every N <unit>]
  project update <id> [--name|--note|--status|--folder|--due|--defer|--sequential|--parallel|--flagged|--unflag]
                                    Status values: active | onHold | completed | dropped
  system-map [flags]                Inspect or refresh the Attache System Map (per D7.2 schema v1).
                                    Flags: --show (human summary), --json (raw JSON, default),
                                           --refresh [--depth quick|full] (re-discover + write to task note),
                                           --drift-check (returns {stale, reasons, ageDays}),
                                           --validate (check against schema v1 required fields).
                                    Env: ATTACHE_MAP_MAX_AGE_DAYS (default 30) — drift-check age threshold.
  help                              Show this help

Filters for 'list':
  inbox                      Inbox tasks
  flagged                    Flagged active tasks
  today                      Due today, flagged, or planned today
  overdue                    Past due date
  due-soon [N]               Due in next N days (default 7)
  waiting-for [--tag NAME] [--days N]  Tasks tagged as Waiting For. If --tag omitted,
                             resolves from SystemMap.conventions.waitingTag (D7.5).
  someday-maybe [--tag NAME] [--folder NAME]  Tasks in Someday/Maybe tag or folder.
                             If both omitted, resolves from SystemMap.conventions.{somedayTag,somedayFolder}.

Create options:
  --name "Task name"        Task name (required)
  --project "Project"       Target project
  --tags "tag1,tag2"        Comma-separated tags
  --due YYYY-MM-DD          Due date
  --defer YYYY-MM-DD        Defer date
  --note "Note text"        Task note
  --flagged                 Flag the task
  --estimate N              Estimated minutes
  --planned-date YYYY-MM-DD Planned date (Forecast scheduling)

Update options:
  --name "New name"         Change task name
  --due YYYY-MM-DD|clear    Set or clear due date
  --defer YYYY-MM-DD|clear  Set or clear defer date
  --tags "tag1,tag2"        Replace all tags
  --flagged                 Flag the task
  --note "Note text"        Set task note
  --estimate N              Set estimated minutes
  --planned-date YYYY-MM-DD|clear  Set or clear planned date

Tag options:
  --add "TagName"           Add a tag (repeatable)
  --remove "TagName"        Remove a tag (repeatable)
  --capture <shortcut>      Add a capture pipeline tag
    Shortcuts: question, discontent, decide, routine, evening

Stdin support (create):
  echo "Task name" | ofo create              Plain text: first line = name, rest = note
  echo '{"name":"X"}' | ofo create           JSON object with task fields
  echo '[{"name":"A"},...]' | ofo create     JSON array for batch creation
  Flags (--project, --tags) merge with stdin; --name overrides stdin name

Perspective-configure options:
  --name "Name"             Perspective to configure (by name)
  --id "ID"                 Perspective to configure (by ID)
  --rules '[...]'           JSON array of filter rule objects
  --aggregation all|any|none  Filter aggregation mode

Completed-today options:
  --markdown                Output as markdown (default: JSON)
  Queries "Completed Today" perspective, excludes Routine🔁,
  categorizes by Question❓, Discontent⁉️, Decide😤 tags.
  Pipe to obsidian-cli: ofo completed-today --markdown | obsidian append "path"

URL handling:
  All commands accept omnifocus:// URLs:
    ofo info omnifocus:///task/abc123
    ofo complete omnifocus:///project/def456

Prerequisites:
  - OmniFocus must be running
  - ofo-core plugin must be installed in OmniFocus
  - First command triggers a one-time approval dialog
`);
}

// --- Main ---

// --- D7.3 — System Map CLI ---

const ATTACHE_PLUGIN_ID = 'com.totallytools.omnifocus.attache';
const SYSTEM_MAP_TASK_NAME = 'Attache System Map';
const EXPECTED_SCHEMA_VERSION = 1;
const DEFAULT_MAX_AGE_DAYS = 30;

/**
 * Run an inline omnijs-run script and return its pasteboard output.
 * Same polling pattern as runAction() but takes the script body inline
 * (not the ofo-stub.js). Used for system-map operations that cross
 * libraries (ofoCore + systemDiscovery).
 */
function runInlineScript(scriptBody: string): string {
  pbcopy('__ofo_pending__');
  const encoded = urlEncode(scriptBody);
  execSync(`open "omnifocus://localhost/omnijs-run?script=${encoded}"`, { stdio: 'ignore' });
  for (let attempt = 0; attempt < 50; attempt++) {
    execSync('sleep 0.2');
    const result = pbpaste();
    if (result !== '__ofo_pending__') return result;
  }
  die('Timeout waiting for OmniFocus response (system-map). Is external script execution enabled?');
  return ''; // unreachable
}

function cmdSystemMap(args: string[]): void {
  let mode: 'show' | 'refresh' | 'drift-check' | 'validate' | 'json' = 'json';
  let depth: 'quick' | 'full' = 'full';

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--show':        mode = 'show'; break;
      case '--refresh':     mode = 'refresh'; break;
      case '--drift-check': mode = 'drift-check'; break;
      case '--validate':    mode = 'validate'; break;
      case '--json':        mode = 'json'; break;
      case '--depth':       depth = (args[++i] as 'quick' | 'full') || 'full'; break;
      default:              die('Unknown flag: ' + args[i] + '. Usage: ofo system-map [--show|--refresh|--drift-check|--validate|--json] [--depth quick|full]');
    }
  }

  if (mode === 'refresh') {
    // Inline script: invoke systemDiscovery, write to task note, return JSON.
    const script = `(() => {
  const p = PlugIn.find(${JSON.stringify(ATTACHE_PLUGIN_ID)});
  if (!p) { Pasteboard.general.string = JSON.stringify({success:false, error:"Attache plugin not installed"}); return; }
  const lib = p.library("systemDiscovery");
  if (!lib) { Pasteboard.general.string = JSON.stringify({success:false, error:"systemDiscovery library not found in Attache plugin (rebuild required?)"}); return; }
  let map;
  try { map = lib.discoverSystem({depth: ${JSON.stringify(depth)}}); }
  catch (e) { Pasteboard.general.string = JSON.stringify({success:false, error:"discoverSystem threw: " + String(e)}); return; }
  const mapJson = JSON.stringify(map);
  // Find or create the Attache System Map task at inbox root
  const existing = flattenedTasks.filter(t => t.name === ${JSON.stringify(SYSTEM_MAP_TASK_NAME)});
  let task;
  if (existing.length > 0) { task = existing[0]; task.note = mapJson; }
  else { task = new Task(${JSON.stringify(SYSTEM_MAP_TASK_NAME)}, inbox.ending); task.note = mapJson; }
  Pasteboard.general.string = JSON.stringify({success:true, refreshed:true, taskId: task.id.primaryKey, schemaVersion: map.schemaVersion, generatedAt: map.generatedAt, discoveryMode: map.discoveryMode, conventions: map.conventions, durationModel: map.durationModel});
})()`;
    const result = runInlineScript(script);
    process.stdout.write(result);
    return;
  }

  // For show/drift-check/validate/json: first read the map from the task note.
  const readScript = `(() => {
  const tasks = flattenedTasks.filter(t => t.name === ${JSON.stringify(SYSTEM_MAP_TASK_NAME)});
  if (tasks.length === 0) { Pasteboard.general.string = JSON.stringify({success:false, error:"System Map not found. Run: ofo system-map --refresh"}); return; }
  const task = tasks[0];
  const note = task.note || "{}";
  // Also collect live counts for drift detection
  const liveTagCount = flattenedTags.length;
  const liveTopLevelFolderCount = folders.length;
  Pasteboard.general.string = JSON.stringify({success:true, note: note, liveTagCount: liveTagCount, liveTopLevelFolderCount: liveTopLevelFolderCount, taskId: task.id.primaryKey});
})()`;
  const readResult = runInlineScript(readScript);
  let readData: any;
  try { readData = JSON.parse(readResult); }
  catch { die('Failed to parse OmniFocus response: ' + readResult.slice(0, 200)); }
  if (!readData.success) {
    process.stdout.write(readResult);
    process.exit(1);
  }

  let map: any;
  try { map = JSON.parse(readData.note); }
  catch {
    process.stdout.write(JSON.stringify({ success: false, error: 'System Map task note is not valid JSON. Run: ofo system-map --refresh' }));
    process.exit(1);
  }

  if (mode === 'json' || mode === 'show') {
    if (mode === 'json') {
      process.stdout.write(JSON.stringify(map, null, 2));
      return;
    }
    // Human-readable summary
    const ageDays = map.generatedAt
      ? Math.floor((Date.parse(new Date().toISOString()) - Date.parse(map.generatedAt)) / 86400000)
      : '?';
    const lines = [
      'Attache System Map',
      '==================',
      `Schema version:    ${map.schemaVersion ?? '(legacy, pre-D7.2)'}`,
      `Attache version:   ${map.attacheVersion ?? '?'}`,
      `Generated at:      ${map.generatedAt ?? map.discoveredAt ?? '?'} (${ageDays} days ago)`,
      `Discovery mode:    ${map.discoveryMode ?? '?'} (depth: ${map.discoveryDepth ?? map.discoveryMode ?? '?'})`,
      `Duration model:    ${map.durationModel ?? '?'}`,
      '',
      'Conventions:',
      `  waitingTag:        ${map.conventions?.waitingTag ?? '(none)'}`,
      `  somedayTag:        ${map.conventions?.somedayTag ?? '(none)'}`,
      `  somedayFolder:     ${map.conventions?.somedayFolder ?? '(none)'}`,
      `  waitingForFolder:  ${map.conventions?.waitingForFolder ?? '(none)'}`,
      `  defaultContextTag: ${map.conventions?.defaultContextTag ?? '(none)'}`,
      '',
      `Folders: ${map.structure?.totalFolders ?? '?'} total, ${map.structure?.topLevelFolders?.length ?? '?'} top-level`,
      `Projects: ${map.projects?.total ?? '?'} (${map.projects?.active ?? '?'} active, ${map.projects?.stalled ?? '?'} stalled)`,
      map.tasks ? `Tasks: ${map.tasks.active ?? '?'} active (${map.tasks.inInbox ?? '?'} in inbox)` : 'Tasks: (quick mode, no task data)',
      `Tags: ${map.tags?.totalTags ?? '?'} total (${map.tags?.taxonomyStyle ?? '?'})`,
    ];
    process.stdout.write(lines.join('\n') + '\n');
    return;
  }

  if (mode === 'validate') {
    const errors: string[] = [];
    if (map.schemaVersion !== EXPECTED_SCHEMA_VERSION) {
      errors.push(`schemaVersion: expected ${EXPECTED_SCHEMA_VERSION}, got ${map.schemaVersion}`);
    }
    const requiredTopLevel = ['attacheVersion', 'generatedAt', 'discoveryMode', 'discoveryDepth', 'conventions', 'tags', 'structure', 'projects'];
    for (const field of requiredTopLevel) {
      if (!(field in map)) errors.push(`missing required field: ${field}`);
    }
    if (map.conventions) {
      const reqConventions = ['waitingTag', 'somedayTag', 'somedayFolder', 'waitingForFolder', 'defaultContextTag'];
      for (const c of reqConventions) {
        if (!(c in map.conventions)) errors.push(`missing required field: conventions.${c}`);
      }
    }
    if (errors.length === 0) {
      process.stdout.write(JSON.stringify({ valid: true, schemaVersion: map.schemaVersion }) + '\n');
      return;
    }
    process.stdout.write(JSON.stringify({ valid: false, errors }) + '\n');
    process.exit(1);
  }

  if (mode === 'drift-check') {
    const maxAgeDays = parseInt(process.env['ATTACHE_MAP_MAX_AGE_DAYS'] || String(DEFAULT_MAX_AGE_DAYS), 10);
    const reasons: string[] = [];

    if (map.schemaVersion !== EXPECTED_SCHEMA_VERSION) {
      reasons.push(`schema-stale: map v${map.schemaVersion}, current schema v${EXPECTED_SCHEMA_VERSION}`);
    }

    const generatedAt = map.generatedAt || map.discoveredAt;
    let ageDays = 0;
    if (generatedAt) {
      ageDays = Math.floor((Date.parse(new Date().toISOString()) - Date.parse(generatedAt)) / 86400000);
      if (ageDays > maxAgeDays) reasons.push(`age-stale: refreshed ${ageDays} days ago (threshold ${maxAgeDays}d)`);
    }

    // Tag-count delta: sum of all tags.categories.* arrays vs current flattenedTags.length
    let mapTagCount = 0;
    if (map.tags?.categories) {
      for (const cat of Object.values(map.tags.categories) as any[]) {
        if (Array.isArray(cat)) mapTagCount += cat.length;
      }
    }
    const tagDelta = Math.abs(readData.liveTagCount - mapTagCount);
    const tagDeltaPct = mapTagCount > 0 ? (tagDelta / mapTagCount) * 100 : 0;
    if (tagDeltaPct > 10) {
      reasons.push(`tag-drift: ${tagDelta} tags difference (${tagDeltaPct.toFixed(1)}% drift)`);
    }

    // Folder-count delta
    const mapFolderCount = map.structure?.topLevelFolders?.length ?? 0;
    const folderDelta = Math.abs(readData.liveTopLevelFolderCount - mapFolderCount);
    const folderDeltaPct = mapFolderCount > 0 ? (folderDelta / mapFolderCount) * 100 : 0;
    if (folderDeltaPct > 10) {
      reasons.push(`folder-drift: top-level folder count changed (${folderDelta} difference)`);
    }

    // Broken convention check (rough — checks if convention tag/folder name still exists)
    // Note: full check requires another roundtrip; the live counts already give a strong signal.

    process.stdout.write(JSON.stringify({
      stale: reasons.length > 0,
      reasons,
      lastRefresh: generatedAt,
      ageDays,
    }, null, 2) + '\n');
    return;
  }
}

// --- D6.3 — Projects, project, completed, folders ---

function cmdProjects(args: string[]): void {
  const sub = args[0];
  if (!sub) die('Usage: ofo projects <subcommand> — try: neglected, review');
  if (sub === 'neglected') {
    let days = 30;
    for (let i = 1; i < args.length; i++) {
      if (args[i] === '--days') days = parseInt(args[++i] || '30', 10);
    }
    runAction('ofo-list-neglected-projects', { daysSinceModified: days });
    return;
  }
  if (sub === 'review') {
    let before: string | null = null;
    for (let i = 1; i < args.length; i++) {
      if (args[i] === '--before') before = args[++i] || null;
    }
    const payload: Record<string, unknown> = {};
    if (before) payload['beforeDate'] = before;
    runAction('ofo-list-projects-for-review', payload);
    return;
  }
  die('Unknown projects subcommand: ' + sub + ' (try: neglected, review)');
}

function cmdProject(args: string[]): void {
  const sub = args[0];
  if (!sub) die('Usage: ofo project <subcommand> [args] — try: review <id>, create, update <id>');

  if (sub === 'review') {
    const id = args[1];
    if (!id) die('Usage: ofo project review <id> [--date <ISO>]');
    let date: string | null = null;
    for (let i = 2; i < args.length; i++) {
      if (args[i] === '--date') date = args[++i] || null;
    }
    const payload: Record<string, unknown> = { id: parseOmniFocusUrl(id) };
    if (date) payload['reviewDate'] = date;
    runAction('ofo-mark-project-reviewed', payload);
    return;
  }

  if (sub === 'create') {
    let name = '', folder = '', note = '', due = '', defer_ = '';
    let sequential: boolean | undefined;
    let flagged = false;
    let reviewIntervalSteps = 0;
    let reviewIntervalUnit = 'weeks';
    for (let i = 1; i < args.length; i++) {
      switch (args[i]) {
        case '--name':       name = args[++i] || ''; break;
        case '--folder':     folder = args[++i] || ''; break;
        case '--note':       note = args[++i] || ''; break;
        case '--due':        due = args[++i] || ''; break;
        case '--defer':      defer_ = args[++i] || ''; break;
        case '--sequential': sequential = true; break;
        case '--parallel':   sequential = false; break;
        case '--flagged':    flagged = true; break;
        case '--review-every': {
          // Format: "--review-every 1 week" or "--review-every 7 days"
          reviewIntervalSteps = parseInt(args[++i] || '0', 10);
          reviewIntervalUnit = args[++i] || 'weeks';
          break;
        }
        default: die('Unknown flag: ' + args[i]);
      }
    }
    if (!name) die('--name is required');
    const payload: Record<string, unknown> = { name };
    if (folder) payload['folder'] = folder;
    if (note) payload['note'] = note;
    if (due) payload['due'] = due;
    if (defer_) payload['defer'] = defer_;
    if (sequential !== undefined) payload['sequential'] = sequential;
    if (flagged) payload['flagged'] = true;
    if (reviewIntervalSteps > 0) payload['reviewInterval'] = { steps: reviewIntervalSteps, unit: reviewIntervalUnit };
    runAction('ofo-create-project', payload);
    return;
  }

  if (sub === 'update') {
    const id = args[1];
    if (!id) die('Usage: ofo project update <id> [flags]');
    const payload: Record<string, unknown> = { id: parseOmniFocusUrl(id) };
    for (let i = 2; i < args.length; i++) {
      switch (args[i]) {
        case '--name':       payload['name'] = args[++i] || ''; break;
        case '--note':       payload['note'] = args[++i] || ''; break;
        case '--status':     payload['status'] = args[++i] || ''; break;
        case '--folder':     payload['folder'] = args[++i] || ''; break;
        case '--due':        payload['due'] = args[++i] === 'clear' ? null : args[i]; break;
        case '--defer':      payload['defer'] = args[++i] === 'clear' ? null : args[i]; break;
        case '--sequential': payload['sequential'] = true; break;
        case '--parallel':   payload['sequential'] = false; break;
        case '--flagged':    payload['flagged'] = true; break;
        case '--unflag':     payload['flagged'] = false; break;
        default: die('Unknown flag: ' + args[i]);
      }
    }
    runAction('ofo-update-project', payload);
    return;
  }

  die('Unknown project subcommand: ' + sub + ' (try: review, create, update)');
}

function cmdCompleted(args: string[]): void {
  let since: string | null = null;
  let byTag = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--since') since = args[++i] || null;
    else if (args[i] === '--by-tag') byTag = true;
  }
  const payload: Record<string, unknown> = {};
  if (since) payload['sinceDate'] = since;
  if (byTag) payload['groupByTag'] = true;
  runAction('ofo-list-recently-completed', payload);
}

function cmdFolders(args: string[]): void {
  let withProjects = false;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--with-projects') withProjects = true;
  }
  runAction('ofo-list-folders', withProjects ? { includeProjects: true } : {});
}

const argv = process.argv.slice(2);
const command = argv[0] || 'help';
const commandArgs = argv.slice(1);

if (command === '--version' || command === '-V') {
  process.stdout.write(`ofo ${VERSION} (TypeScript plugin library architecture)\n`);
  process.exit(0);
}

if (command !== 'help' && command !== '--help' && command !== '-h') {
  checkOmniFocus();
}

switch (command) {
  case 'info':        cmdInfo(commandArgs); break;
  case 'complete':    cmdComplete(commandArgs); break;
  case 'drop':        cmdDrop(commandArgs); break;
  case 'create':      cmdCreate(commandArgs); break;
  case 'update':      cmdUpdate(commandArgs); break;
  case 'search':      cmdSearch(commandArgs); break;
  case 'list':        cmdList(commandArgs); break;
  case 'tag':                   cmdTag(commandArgs); break;
  case 'tags':                  cmdTags(); break;
  case 'perspective':           cmdPerspective(commandArgs); break;
  case 'perspective-configure': cmdPerspectiveConfigure(commandArgs); break;
  case 'perspective-rules':     cmdPerspectiveRules(commandArgs); break;
  case 'completed-today':       cmdCompletedToday(commandArgs); break;
  case 'dump':                  cmdDump(); break;
  case 'stats':                 cmdStats(); break;
  case 'clarity':               cmdClarity(commandArgs); break;
  case 'stalled':               cmdStalled(commandArgs); break;
  case 'health':                cmdHealth(); break;
  // D6.3 — GTD-essential commands
  case 'projects':              cmdProjects(commandArgs); break;
  case 'project':               cmdProject(commandArgs); break;
  case 'completed':             cmdCompleted(commandArgs); break;
  case 'folders':               cmdFolders(commandArgs); break;
  case 'system-map':            cmdSystemMap(commandArgs); break;
  case 'help':
  case '--help':
  case '-h':          cmdHelp(); break;
  default:            die('Unknown command: ' + command + '. Run \'ofo help\' for usage.');
}
