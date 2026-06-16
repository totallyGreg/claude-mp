# Validation Pipeline (D8 Layered Approach)

This doc is the **single source of truth** for how generator output is validated. The goal: catch every class of error in static analysis or pre-emit validation, so loading a built plugin into OmniFocus only to find egregious errors becomes vanishingly rare.

Supersedes the historical `code_generation_validation.md` (which is being absorbed into this doc + `foundation_models.md` + `iife_wrapper.md`).

## The Five Layers

Each layer catches a different class of error. Layers run in order; failure at any layer prevents progression.

```
   1. Pre-generation (in generator)
        ↓ valid spec
   2. Pre-emit (after TS source drafted)
        ↓ tsc clean + ESLint clean + antipatterns clean
   3. Post-emit (after JS written)
        ↓ manifest valid, resources coherent, .strings keys match, smoke loads
   4. Runtime contracts (built into the code by D8.5)
        ↓ library present, System Map current, selection guarded
   5. Documented deviations (api_gaps.md tracker)
```

## Layer 1 — Pre-Generation

Owned by `generate_plugin.ts`. Runs before any code is drafted.

- **Spec validation.** The generator's spec parser rejects malformed input (missing required fields, unknown format, invalid action shape).
- **Template selection.** Wrong template = wrong code shape; the format selector enforces `solitary` / `solitary-fm` / `bundle` / `solitary-library` per `plugin_format_selection.md`.
- **ofoCore check (STEP 1.5 — per D3).** Before generating ANY task/project/tag CRUD code, the generator inspects `ofo-core.ts` exports. If the operation already exists in `ofoCore`, the plugin must consume it via library — generating fresh CRUD code is refused. See `library_consumer_pattern.md`.

## Layer 2 — Pre-Emit (Static Analysis)

After the generator drafts TS source, three checks run in sequence. Failure at any check prevents JS emission.

### 2a. `tsc --noEmit` with strict flags

Three tsconfigs cover the generator's outputs (`tsconfig.plugin.json`, `tsconfig.cli.json`, `tsconfig.attache-libs.json`). All three have D8.1 strictness:

- `strict: true` (plugin + cli — attache-libs is the residual permissive config)
- `noImplicitAny`, `strictNullChecks`, `noImplicitReturns`, `noFallthroughCasesInSwitch`
- `noUncheckedIndexedAccess` (D8.1 addition) — `arr[0]` types as `T | undefined`; catches `selection.tasks[0]`, `byName(x)`, regex `m[1]` patterns without guards
- `exactOptionalPropertyTypes` (D8.1, plugin + cli) — distinguishes `{x?: T}` from `{x: T | undefined}`; catches drift between OmniFocus stubs and consumer code

**Deferred:** `noPropertyAccessFromIndexSignature` — would surface 116 errors on existing `OfoArgs` access (the type is `{action: OfoAction; [key: string]: unknown}`). Real audit finding tracked in issue #182.

If `tsc` reports any error, the generator emits NOTHING. The agent must fix the source.

### 2b. ESLint flat config

`plugins/attache/skills/omnifocus-core/eslint.config.js` runs against plugin code (NOT the Node CLI — that's validated by tsc).

- `no-undef: error` (D8.2) — catches typos like `flattenedTaks`. Requires every legitimate global (76 PlugIn API classes + bare functions like `folderNamed`/`projectNamed`/`taskNamed`) declared in the config's `globals` list. Cross-referenced against `../typescript/omnifocus.d.ts`.
- `no-unused-vars: warn` with `argsIgnorePattern: ^_`, `caughtErrorsIgnorePattern: ^_`, `varsIgnorePattern: ^_` — flags dead code but doesn't fail on the standard `(selection, sender) => {}` PlugIn.Action handler params or `try { } catch (_) {}` pattern.

### 2c. PlugIn-API antipatterns (`validate-jxa-patterns.js` + `jxa-antipatterns.json`)

Pattern matchers against the JS source. Errors at any of these block emission:

**Always-blocked** (security/runtime):
- `eval()`, `Function()` constructor — code injection vectors
- `$.NSTask`, `doShellScript`, `$.NSURLSession` — system-level / network APIs not available in plugin sandbox

**JXA misuse in plugin context:**
- `.addTag()`, `.clearTags()` — JXA-only methods
- `Document.defaultDocument` — JXA pattern; plugin context uses bare globals
- `.name() === "..."` — exact tag-name matching fails on Unicode/emoji

**PlugIn-API footguns (D8.3 additions):**
- `.byName(...).foo` — `byName` returns null; must assign + null-check
- `selection.tasks[0]` etc. — selection arrays may be empty; must check `.length`
- `PlugIn.find(...).library(...)` — `find` returns null when plugin missing; must assign + null-check
- `new LanguageModel.Schema(...)` — must use `LanguageModel.Schema.fromJSON({...})` factory

Each rule references the relevant capability doc for context.

## Layer 3 — Post-Emit (`validate-plugin.sh`)

Runs on the written `.omnifocusjs` bundle. Failure should cause the generator to delete the bundle (zero-tolerance — don't ship broken plugins).

### 3a. Manifest validity
- `manifest.json` exists at bundle root
- Valid JSON
- Required fields: `identifier`, `version`
- Recommended: `author`, `description`
- `Resources/` directory exists

### 3b. Action / library file existence
- For each declared action: `Resources/<identifier>.js` exists
- For each declared library: `Resources/<identifier>.js` exists

### 3c. Bundle coherence (D8.4 — TBD)
For each declared action / library, the corresponding `.js` file should contain the matching `new PlugIn.Action(...)` / `new PlugIn.Library(...)` constructor. Mismatches = silent load failures in OmniFocus.

Status: **planned**, not yet implemented. See plan D8.4.

### 3d. `.strings` key validation (D8.4 — TBD)
- Parse `Resources/<locale>.lproj/<bundle-id>.strings` files
- Every manifest-referenced key (action `label`, `description`, etc.) must exist in the default locale
- Warn on unused keys

Status: **planned**, not yet implemented.

### 3e. Pre-load smoke test (D8.6 — TBD)
A Node.js script (`smoke-load.js`) that:
1. Loads a minimal stub environment defining OmniFocus globals as no-ops
2. `require()`s each compiled `Resources/*.js`
3. Reports any thrown error (syntax error, top-level reference to an undefined identifier)

This doesn't run action logic — only confirms the bundle parses + evaluates at the top level against stubbed globals. Catches the class of error where a refactor renames a global and the action still references the old name.

Status: **planned**, not yet implemented.

## Layer 4 — Runtime Contracts (Emitted by Generator)

When the spec declares `requires: ["ofoCore"]` (D3) or `requires: ["systemMap"]` (D7.7), the generator auto-emits guard skeletons at the top of each action / library:

- **ofoCore presence check** — `PlugIn.find("com.totallytools.omnifocus.attache")` null-guard, then `attache.library("ofoCore")` null-guard with function presence check
- **System Map version check** — find the "Attache System Map" task, parse JSON, check `schemaVersion === EXPECTED_SCHEMA_VERSION`, with explicit error UX pointing to `ofo system-map --refresh`

See `library_consumer_pattern.md` and `system_map_dependency.md` for the full skeletons.

Generator skeleton emission per D8.5 is **planned**, not yet implemented.

## Layer 5 — Documented Deviations (`api_gaps.md`)

Known TS stub gaps and `@ts-expect-error #ISSUE` tracking. When a strict-mode flag surfaces a real-but-known-acceptable issue, add a `// @ts-expect-error #ISSUE-N` comment at the call site AND document in `api_gaps.md` with:
- The pattern
- The reason it's acceptable
- The tracking issue
- The expected fix path

Status: doc planned; first entries will track #182 (OfoArgs refactor, missing bare globals).

## What's NOT Statically Checkable

Some failure modes can only be caught at runtime — design your plugin to fail loud, not silent.

| Concern | Why not static | Mitigation |
|---|---|---|
| Foundation Models availability | Requires macOS 26+ Apple Silicon at runtime | Check `typeof LanguageModel !== "undefined"` at startup; emit clear error if absent |
| Attache plugin reload after deploy | Issue #135 — OmniFocus caches library code; `Attache.omnifocusjs` rebuilds don't reload automatically | Manual workaround: restart OmniFocus after running `build-attache.sh` (D6.6) |
| Version-gated OmniFocus APIs | Some methods only exist in OmniFocus 4.x+; old installs lack them | `typeof` check before use; document minimum OmniFocus version in plugin description |
| User database state | Tag/folder names referenced in generated code may not exist | Generated plugins should use the System Map (D7.7) for convention-dependent code, not hardcoded names |
| Selection state at action invocation | `selection.tasks` may be empty if user invoked the action with no selection | The `require-selection-guard` antipattern (D8.3) enforces `.length` check |
| OmniFocus permission to run scripts | "Automatically run" must be enabled in Automation Console once | Document in plugin install instructions; `ofo` CLI surfaces a timeout if disabled |

## Acceptance Test (D8.8 — TBD)

A regression suite of deliberately-broken plugin specs should be maintained, covering each layer's failure modes:

- **Spec error** (Layer 1): missing required field → spec validation rejects
- **TS error** (Layer 2a): missing null-check on `flattenedTags.byName(x)` → tsc surfaces TS error
- **Lint error** (Layer 2b): `flattenedTaks` typo → ESLint `no-undef` error
- **Antipattern** (Layer 2c): `.byName(x).foo` → `require-byname-null-check` blocks
- **Manifest mismatch** (Layer 3c): manifest declares action `foo` but `Resources/foo.js` has no `new PlugIn.Action(...)` → coherence check blocks
- **Strings drift** (Layer 3d): manifest references `foo.label` but `en.lproj/com.foo.strings` has no `foo.label` key → strings validation blocks
- **Bundle smoke** (Layer 3e): action calls undefined global → smoke loader throws

Status: regression suite **planned**, not yet implemented.

## Cross-References

- `library_consumer_pattern.md` — Layer 4 ofoCore consumer skeleton
- `system_map_dependency.md` — Layer 4 systemDiscovery consumer skeleton
- `iife_wrapper.md` — IIFE wrap done by `build-attache.sh`
- `api_gaps.md` — Layer 5 deviation tracker
- `../scripts/validate-plugin.sh` — current Layer 3 implementation
- `../scripts/jxa-antipatterns.json` — current Layer 2c rule data
- `../scripts/validate-jxa-patterns.js` — Layer 2c runner
- Plan: `../../../docs/plans/2026-06-15-001-attache-references-routing-plan.md` D8
