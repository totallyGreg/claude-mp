// Ambient declarations for OmniFocus properties not in the 2021 type definitions.
// These exist at runtime in OmniFocus 4 and are used by ofo-core.ts.

interface Task {
  effectivelyCompleted: boolean;
  effectivelyDropped: boolean;
  clearTags(): void;
  markComplete(date?: Date | null): Task;
}

interface Project {
  modified: Date | null;
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
