#!/usr/bin/env node
/**
 * smoke-load.js — D8.6 pre-load smoke test for OmniFocus plugin bundles.
 *
 * Catches the class of error where a Resources/*.js file references an
 * identifier that doesn't exist at the top level (typo'd global, missing
 * import, wrong constructor name) — the kind of error that would crash
 * OmniFocus the moment it loads the file.
 *
 * Loads each Resources/*.js in a Node vm sandbox with stubbed OmniFocus
 * globals. The stubs are no-ops, just enough to satisfy top-level
 * evaluation (IIFE invocations, `new PlugIn.Library(...)`, `new PlugIn.Action(...)`).
 * Action LOGIC is NOT executed — we only care that the file parses + evaluates
 * its top-level statements without throwing.
 *
 * Usage:
 *   node smoke-load.js <path-to-plugin.omnifocusjs>
 *
 * Exits 0 if all Resources/*.js files load cleanly, 1 otherwise.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const pluginPath = process.argv[2];
if (!pluginPath) {
  console.error('Usage: smoke-load.js <path-to-plugin.omnifocusjs>');
  process.exit(2);
}

const resourcesDir = path.join(pluginPath, 'Resources');
if (!fs.existsSync(resourcesDir)) {
  console.error('Resources/ not found in: ' + pluginPath);
  process.exit(2);
}

// ─────────────────────────────────────────────────────────────────────────────
// Stub environment — OmniFocus PlugIn API as no-ops.
// Stubs are intentionally permissive: any property access returns a callable
// no-op, so files that reference deeply-nested APIs don't crash on load.
// ─────────────────────────────────────────────────────────────────────────────

function makeNoop(name) {
  const fn = function () { return makeNoop(name + '()'); };
  fn._stubName = name;
  return new Proxy(fn, {
    get(target, prop) {
      if (prop === 'then' || typeof prop === 'symbol') return undefined;
      if (prop in target) return target[prop];
      return makeNoop(name + '.' + String(prop));
    },
    construct() { return makeNoop('new ' + name); },
  });
}

function makeStubClass(name) {
  // A class-like stub that supports both `new X(...)` and `X.staticMethod(...)`.
  function Stub() { return makeNoop('instance of ' + name); }
  return new Proxy(Stub, {
    get(target, prop) {
      if (prop === 'prototype') return target.prototype;
      if (prop === 'then' || typeof prop === 'symbol') return undefined;
      return makeNoop(name + '.' + String(prop));
    },
    construct() { return makeNoop('new ' + name); },
  });
}

const stubGlobals = {
  // ─── PlugIn API classes ───
  PlugIn: (() => {
    const PI = makeStubClass('PlugIn');
    PI.Library = makeStubClass('PlugIn.Library');
    PI.Action = makeStubClass('PlugIn.Action');
    PI.find = () => null; // Resources usually null-check this
    return PI;
  })(),
  Version: makeStubClass('Version'),
  Alert: makeStubClass('Alert'),
  Form: (() => {
    const F = makeStubClass('Form');
    F.Field = makeStubClass('Form.Field');
    F.Field.Checkbox = makeStubClass('Form.Field.Checkbox');
    F.Field.String = makeStubClass('Form.Field.String');
    F.Field.Date = makeStubClass('Form.Field.Date');
    F.Field.Option = makeStubClass('Form.Field.Option');
    F.Field.MultipleOptions = makeStubClass('Form.Field.MultipleOptions');
    return F;
  })(),
  FileWrapper: makeStubClass('FileWrapper'),
  FileSaver: makeStubClass('FileSaver'),
  FilePicker: makeStubClass('FilePicker'),
  FileType: makeStubClass('FileType'),
  Data: makeStubClass('Data'),
  Pasteboard: (() => {
    const P = makeStubClass('Pasteboard');
    P.general = { string: '' };
    return P;
  })(),

  // ─── Database classes ───
  Task: (() => {
    const T = makeStubClass('Task');
    T.Status = { Available: 'Available', Completed: 'Completed', Dropped: 'Dropped', Blocked: 'Blocked', DueSoon: 'DueSoon', Overdue: 'Overdue', Next: 'Next' };
    T.byIdentifier = () => null;
    return T;
  })(),
  Project: (() => {
    const P = makeStubClass('Project');
    P.Status = { Active: 'Active', OnHold: 'OnHold', Done: 'Done', Dropped: 'Dropped' };
    P.byIdentifier = () => null;
    return P;
  })(),
  Folder: (() => {
    const F = makeStubClass('Folder');
    F.Status = { Active: 'Active', Dropped: 'Dropped' };
    F.byIdentifier = () => null;
    return F;
  })(),
  Tag: (() => {
    const T = makeStubClass('Tag');
    T.Status = { Active: 'Active', Dropped: 'Dropped', OnHold: 'OnHold' };
    T.byIdentifier = () => null;
    T.forecastTag = null;
    return T;
  })(),
  Perspective: (() => {
    const P = makeStubClass('Perspective');
    P.Custom = makeStubClass('Perspective.Custom');
    P.Custom.all = [];
    P.Custom.byIdentifier = () => null;
    P.Custom.byName = () => null;
    return P;
  })(),
  LanguageModel: (() => {
    const L = makeStubClass('LanguageModel');
    L.Session = makeStubClass('LanguageModel.Session');
    L.Schema = makeStubClass('LanguageModel.Schema');
    L.Schema.fromJSON = () => makeNoop('LanguageModel.Schema instance');
    L.GenerationOptions = makeStubClass('LanguageModel.GenerationOptions');
    return L;
  })(),
  // Other classes the antipattern docs reference
  Calendar: makeStubClass('Calendar'),
  Formatter: makeStubClass('Formatter'),
  DateComponents: makeStubClass('DateComponents'),
  Document: makeStubClass('Document'),
  DocumentWindow: makeStubClass('DocumentWindow'),
  Window: makeStubClass('Window'),
  Selection: makeStubClass('Selection'),
  Settings: makeStubClass('Settings'),
  Preferences: makeStubClass('Preferences'),
  ForecastDay: makeStubClass('ForecastDay'),
  Tree: makeStubClass('Tree'),
  TreeNode: makeStubClass('TreeNode'),
  URL: makeStubClass('URL'),
  Email: makeStubClass('Email'),
  Application: makeStubClass('Application'),

  // ─── Database globals ───
  flattenedTasks: Object.assign([], { byName: () => null }),
  flattenedProjects: Object.assign([], { byName: () => null }),
  flattenedFolders: Object.assign([], { byName: () => null }),
  flattenedTags: Object.assign([], { byName: () => null }),
  folders: Object.assign([], { byName: () => null }),
  projects: Object.assign([], { byName: () => null }),
  tags: Object.assign([], { byName: () => null }),
  inbox: Object.assign([], { ending: makeNoop('inbox.ending') }),
  library: makeStubClass('library'),

  // ─── Bare function globals ───
  moveTasks: () => {},
  moveSections: () => {},
  deleteObject: () => {},
  duplicateTasks: () => {},
  duplicateSections: () => {},
  folderNamed: () => null,
  projectNamed: () => null,
  taskNamed: () => null,
  tagNamed: () => null,
  app: makeNoop('app'),
  document: makeNoop('document'),
  database: (() => {
    const d = makeNoop('database');
    d.tags = Object.assign([], { ending: makeNoop('database.tags.ending') });
    return d;
  })(),

  // ─── Standard JS globals (forwarded; vm sandbox by default doesn't have these) ───
  console: console,
  setTimeout: setTimeout,
  setInterval: setInterval,
  clearTimeout: clearTimeout,
  clearInterval: clearInterval,
  JSON: JSON,
  Date: Date,
  Math: Math,
  Object: Object,
  Array: Array,
  String: String,
  Number: Number,
  Boolean: Boolean,
  Promise: Promise,
  Set: Set,
  Map: Map,
  Error: Error,
  TypeError: TypeError,
  RangeError: RangeError,
  parseInt: parseInt,
  parseFloat: parseFloat,
  isNaN: isNaN,
  isFinite: isFinite,
  Symbol: Symbol,
};

// ─────────────────────────────────────────────────────────────────────────────
// Run each Resources/*.js in a fresh sandbox.
// ─────────────────────────────────────────────────────────────────────────────

const jsFiles = fs.readdirSync(resourcesDir)
  .filter((f) => f.endsWith('.js'))
  .sort();

if (jsFiles.length === 0) {
  console.log('No .js files in Resources/ — nothing to smoke-load.');
  process.exit(0);
}

let failures = 0;
const failureDetails = [];

for (const file of jsFiles) {
  const filePath = path.join(resourcesDir, file);
  const source = fs.readFileSync(filePath, 'utf-8');
  // Fresh sandbox per file (avoids cross-file state pollution)
  const sandbox = vm.createContext({ ...stubGlobals });
  try {
    vm.runInContext(source, sandbox, { filename: file, timeout: 2000 });
    process.stdout.write('  ✅ ' + file + '\n');
  } catch (e) {
    failures++;
    failureDetails.push({ file, error: e.message, stack: e.stack });
    process.stdout.write('  ❌ ' + file + ' — ' + e.message + '\n');
  }
}

if (failures > 0) {
  process.stdout.write('\nSmoke load failed for ' + failures + ' / ' + jsFiles.length + ' file(s).\n');
  process.exit(1);
}

process.stdout.write('\nAll ' + jsFiles.length + ' file(s) loaded cleanly in the smoke sandbox.\n');
process.exit(0);
