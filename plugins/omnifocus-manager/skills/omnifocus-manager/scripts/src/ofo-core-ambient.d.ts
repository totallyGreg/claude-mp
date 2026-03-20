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
