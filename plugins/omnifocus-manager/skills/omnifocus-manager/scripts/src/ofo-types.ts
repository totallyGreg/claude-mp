/**
 * ofo-types.ts — Single source of truth for the ofo CLI ↔ ofoCore plugin type contract.
 *
 * Consumed by:
 *   - ofo-cli.ts via `import type { OfoAction } from './ofo-types.js'`
 *   - ofo-core-ambient.d.ts via `type OfoAction = import('./ofo-types.js').OfoAction`
 *
 * When adding a new action, update this file — both consumers pick it up automatically.
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
  | 'ofo-stats';

export interface OfoArgs {
  action: OfoAction;
  [key: string]: unknown;
}

export interface OfoResult {
  success: boolean;
  error?: string;
  [key: string]: unknown;
}
