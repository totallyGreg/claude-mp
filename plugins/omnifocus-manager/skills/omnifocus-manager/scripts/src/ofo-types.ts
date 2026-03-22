/**
 * ofo-types.ts — Shared type contract for the ofo CLI ↔ ofoCore plugin interface.
 *
 * Importable by ofo-cli.ts (Node.js/ESM compilation).
 *
 * IMPORTANT: Keep in sync with the ambient declarations at the bottom of
 * ofo-core-ambient.d.ts, which provide the same types for the plugin
 * compilation (tsconfig.plugin.json) where imports are not available.
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
  | 'ofo-perspective-rules';

export interface OfoArgs {
  action: OfoAction;
  [key: string]: unknown;
}

export interface OfoResult {
  success: boolean;
  error?: string;
  [key: string]: unknown;
}
