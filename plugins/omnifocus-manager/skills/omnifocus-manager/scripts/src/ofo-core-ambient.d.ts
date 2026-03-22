// Ambient declarations for OmniFocus properties not in the 2021 type definitions.
// These exist at runtime in OmniFocus 4 and are used by ofo-core.ts.

interface Task {
  effectivelyCompleted: boolean;
  effectivelyDropped: boolean;
  plannedDate: Date | null;  // OF4 only; throws on unmigrated databases
  clearTags(): void;
  markComplete(date?: Date | null): Task;
}

interface Project {
  modified: Date | null;
  plannedDate: Date | null;  // OF4 only; throws on unmigrated databases
}

declare namespace Perspective {
  interface Custom {
    archivedFilterRules: any[];
    archivedTopLevelFilterAggregation: any;
  }
}

// Top-level OmniFocus document for tag hierarchy access
declare namespace Tag {
  const enum Status {
    Active = 0,
    OnHold = 1,
    Dropped = 2
  }
}

interface Tag {
  status: Tag.Status;
  children: Tag[];
  remainingTasks: Task[];
  removeTag(tag: Tag): void;
}

// Top-level tag hierarchy (from Database global)
declare const tags: Tag[];

// --- Shared ofo action contract ---
// Single source of truth: ofo-types.ts (used by ofo-cli.ts via ESM import).
// This file re-declares the same types as ambient for the plugin compilation
// (tsconfig.plugin.json) where ESM imports are not available.
// When adding a new action, update ofo-types.ts first, then mirror here.

type OfoAction = import('./ofo-types.js').OfoAction;
type OfoArgs = import('./ofo-types.js').OfoArgs;
type OfoResult = import('./ofo-types.js').OfoResult;
