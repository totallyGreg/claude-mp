/**
 * ofo-contract.d.ts — Pure ambient shared type contract.
 *
 * Single source of truth for types shared between ofo-core (plugin) and ofo-cli (CLI).
 * No import() expressions. No exports. Consumed by:
 *   - tsconfig.plugin.json (plugin compilation, no ESM)
 *   - tsconfig.cli.json (CLI compilation, ESM)
 *   - tsconfig.attache.json (Attache @ts-check, future)
 *
 * ofo-types.ts is a thin ESM re-export wrapper for Node consumers that need module imports.
 */

declare type OfoAction =
  | 'ofo-info'
  | 'ofo-complete'
  | 'ofo-create'
  | 'ofo-create-batch'
  | 'ofo-update'
  | 'ofo-search'
  | 'ofo-list'
  | 'ofo-tag'
  | 'ofo-tags'
  | 'ofo-perspective'
  | 'ofo-perspective-configure'
  | 'ofo-perspective-rules'
  | 'ofo-dump'
  | 'ofo-stats'
  | 'ofo-clarity'
  | 'ofo-stalled'
  | 'ofo-drop'
  | 'ofo-health';

declare interface OfoArgs {
  action: OfoAction;
  [key: string]: unknown;
}

declare interface OfoResult {
  success: boolean;
  error?: string;
  [key: string]: unknown;
}

declare interface OfoTask {
  id: string;
  name: string;
  project: string | null;
  tags: string[];
  flagged: boolean;
  completed: boolean;
  dueDate: Date | null;
  deferDate: Date | null;
  plannedDate: Date | null;
  completionDate: Date | null;
  estimatedMinutes: number | null;
  note: string | null;
  added: Date | null;
  modified: Date | null;
  repetitionRule: string | null;
  repetitionCatchUp: boolean | null;
  repetitionScheduleType: string | null;
  taskStatus: string;
}

declare interface OfoStats {
  inbox: number;
  overdue: number;
  flagged: number;
  dueToday: number;
  activeProjects: number;
  activeTasks: number;
  reviewOverdue: number;
  plannedToday: number;
  withEstimate: number;
}
