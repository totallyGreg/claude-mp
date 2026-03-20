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

function runAction(action: string, args: Record<string, unknown>): void {
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
  let name = '', project = '', note = '', due = '', defer_ = '', tags = '', estimate = '';
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
  if (flagged) argObj.flagged = true;
  if (tags) argObj.tags = tags.split(',').map(t => t.trim());

  runAction('ofo-create', argObj);
}

function cmdUpdate(args: string[]): void {
  if (args.length < 1) die('Usage: ofo update <id> [--name N] [--due D] [--flagged] [--tags t1,t2]');
  const id = parseOmniFocusUrl(args[0]!);

  const argObj: Record<string, unknown> = { id };
  let i = 1;
  while (i < args.length) {
    switch (args[i]) {
      case '--name':     argObj.name = args[++i] || ''; break;
      case '--note':     argObj.note = args[++i] || ''; break;
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
  if (!['inbox', 'flagged', 'today', 'overdue'].includes(filter)) {
    die('Unknown filter: ' + filter + '. Use: inbox, flagged, today, overdue');
  }
  runAction('ofo-list', { filter });
}

function cmdPerspective(args: string[]): void {
  if (args.length < 1) die('Usage: ofo perspective <name> [--id ID]');

  if (args[0] === '--id') {
    runAction('ofo-perspective', { id: args[1] || '' });
  } else {
    runAction('ofo-perspective', { name: args.join(' ') });
  }
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

function cmdTags(): void {
  runAction('ofo-tags', {});
}

function cmdHelp(): void {
  process.stdout.write(`ofo -- OmniFocus CLI via plugin library

Usage: ofo <command> [arguments]

Commands:
  info <id|url>                     Get task or project details as JSON
  complete <id|url>                 Mark a task as complete
  create --name "..." [options]     Create a new task (also accepts stdin)
  update <id|url> [options]         Update task properties
  search <query>                    Search tasks by name or note
  list <filter>                     List tasks by filter
  tag <id|url> [options]            Add/remove tags on a task
  tags                              List all tags as JSON hierarchy
  perspective <name> [--id ID]      Query a custom perspective
  help                              Show this help

Filters for 'list':
  inbox       Inbox tasks
  flagged     Flagged active tasks
  today       Due today or flagged
  overdue     Past due date

Create options:
  --name "Task name"        Task name (required)
  --project "Project"       Target project
  --tags "tag1,tag2"        Comma-separated tags
  --due YYYY-MM-DD          Due date
  --defer YYYY-MM-DD        Defer date
  --note "Note text"        Task note
  --flagged                 Flag the task
  --estimate N              Estimated minutes

Update options:
  --name "New name"         Change task name
  --due YYYY-MM-DD|clear    Set or clear due date
  --defer YYYY-MM-DD|clear  Set or clear defer date
  --tags "tag1,tag2"        Replace all tags
  --flagged                 Flag the task
  --note "Note text"        Set task note
  --estimate N              Set estimated minutes

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
  case 'create':      cmdCreate(commandArgs); break;
  case 'update':      cmdUpdate(commandArgs); break;
  case 'search':      cmdSearch(commandArgs); break;
  case 'list':        cmdList(commandArgs); break;
  case 'tag':         cmdTag(commandArgs); break;
  case 'tags':        cmdTags(); break;
  case 'perspective': cmdPerspective(commandArgs); break;
  case 'help':
  case '--help':
  case '-h':          cmdHelp(); break;
  default:            die('Unknown command: ' + command + '. Run \'ofo help\' for usage.');
}
