#!/usr/bin/env node
/**
 * diff-task-shapes.js — Verify getTask, searchTasks, and listTasks return identical field sets.
 *
 * Reads the built ofoCore.js, stubs the OmniFocus globals, calls each function with
 * a synthetic task, and diffs the returned field sets. Exits 1 if any divergence is found.
 *
 * Run after build-plugin.sh as a regression check.
 */

import { readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';

const __dirname = dirname(fileURLToPath(import.meta.url));
const BUILT_JS = join(__dirname, 'build/ofo-core.omnifocusjs/Resources/ofoCore.js');

if (!existsSync(BUILT_JS)) {
  console.error(`ERROR: Built plugin not found at ${BUILT_JS}. Run build-plugin.sh first.`);
  process.exit(1);
}

// ── Stub OmniFocus globals ────────────────────────────────────────────────────

const STUB_TASK = {
  id: { primaryKey: 'task-abc' },
  name: 'Test Task',
  note: 'note text',
  flagged: false,
  completed: false,
  dropped: false,
  effectivelyCompleted: false,
  effectivelyDropped: false,
  taskStatus: 'available',
  dueDate: null,
  deferDate: null,
  plannedDate: null,
  estimatedMinutes: 30,
  containingProject: { name: 'Test Project', id: { primaryKey: 'proj-xyz' } },
  tags: [{ name: 'work' }],
};

globalThis.Task = { Status: { Available: 'available', Completed: 'completed', Dropped: 'dropped', Blocked: 'blocked' }, byIdentifier: (_id) => STUB_TASK };
globalThis.Project = { Status: { Active: 'active', Done: 'done', Dropped: 'dropped', OnHold: 'onhold' }, byIdentifier: (_id) => null };
globalThis.Tag = { Status: { Active: 0, OnHold: 1, Dropped: 2 }, byIdentifier: (_id) => null };
globalThis.Folder = { byIdentifier: (_id) => null };
globalThis.Perspective = { Custom: { all: [], byIdentifier: (_id) => null } };
globalThis.Version = function(v) { this.version = v; };
globalThis.PlugIn = { Library: function(v) { this.version = v; } };
globalThis.Alert = function() {};
globalThis.Pasteboard = { general: { string: '' } };
globalThis.flattenedTasks = [STUB_TASK];
globalThis.flattenedProjects = [];
globalThis.inbox = [STUB_TASK];
globalThis.tags = [];
globalThis.document = { flattenedTasks: [STUB_TASK], flattenedProjects: [], tags: [] };

// ── Load the built plugin via Function() to respect globalThis stubs ──────────

let lib;
try {
  const raw = readFileSync(BUILT_JS, 'utf8');
  // Strip IIFE wrapper, capture return value as lib
  const inner = raw
    .replace(/^\(\(\) => \{/, '')
    .replace(/\}\)\(\);[\s]*$/, '\nreturn lib;');
  lib = new Function(inner)(); // eslint-disable-line no-new-func
} catch (err) {
  console.error('ERROR: Failed to load ofoCore.js:', err.message);
  process.exit(1);
}

// ── Call each function and collect field sets ─────────────────────────────────

function fieldSet(result, key) {
  const items = result?.[key];
  if (Array.isArray(items) && items.length > 0) return new Set(Object.keys(items[0]));
  if (result?.task && typeof result.task === 'object') return new Set(Object.keys(result.task));
  return new Set();
}

let failed = false;

try {
  const infoResult = lib.getTask({ action: 'ofo-info', id: 'task-abc' });
  const searchResult = lib.searchTasks({ action: 'ofo-search', query: 'Test' });
  const listResult = lib.listTasks({ action: 'ofo-list', filter: 'inbox' });

  const infoFields = fieldSet(infoResult, 'task');
  const searchFields = fieldSet(searchResult, 'tasks');
  const listFields = fieldSet(listResult, 'tasks');

  console.log('getTask fields:    ', [...infoFields].sort().join(', '));
  console.log('searchTasks fields:', [...searchFields].sort().join(', '));
  console.log('listTasks fields:  ', [...listFields].sort().join(', '));

  const allFields = new Set([...infoFields, ...searchFields, ...listFields]);
  const divergences = [];
  for (const f of allFields) {
    const present = [
      infoFields.has(f) ? 'getTask' : null,
      searchFields.has(f) ? 'searchTasks' : null,
      listFields.has(f) ? 'listTasks' : null,
    ].filter(Boolean);
    if (present.length < 3) {
      divergences.push(`  '${f}' only in: ${present.join(', ')}`);
    }
  }

  if (divergences.length > 0) {
    console.error('\nFIELD SET DIVERGENCE:');
    divergences.forEach(d => console.error(d));
    failed = true;
  } else {
    console.log('\nAll three functions return identical field sets. ✓');
  }
} catch (err) {
  console.error('ERROR calling ofoCore functions:', err.message);
  failed = true;
}

process.exit(failed ? 1 : 0);
