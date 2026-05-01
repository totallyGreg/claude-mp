/**
 * ofo-types.ts — ESM re-export wrapper for the ofo CLI ↔ ofoCore type contract.
 *
 * The canonical declarations live in ofo-contract.d.ts (pure ambient, no imports).
 * This file re-exports them for Node consumers (ofo-cli.ts) that need module imports.
 *
 * When adding a new action:
 *   1. Add to OfoAction in ofo-contract.d.ts (consumed by plugin + @ts-check gate)
 *   2. The re-export here picks it up automatically via the ambient declaration.
 */

export type OfoAction =
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

export interface OfoArgs {
  action: OfoAction;
  [key: string]: unknown;
}

export interface OfoResult {
  success: boolean;
  error?: string;
  [key: string]: unknown;
}

export interface OfoTask {
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

export interface OfoStats {
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
