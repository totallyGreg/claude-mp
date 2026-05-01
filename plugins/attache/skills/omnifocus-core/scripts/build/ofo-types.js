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
export {};
